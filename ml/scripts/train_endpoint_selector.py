"""Train and evaluate a tip-versus-handle endpoint selector locally."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

import torch
import yaml
from PIL import Image, ImageDraw
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

from ml.benchmark.metrics import classification_metrics
from ml.models.device import seed_everything, select_device
from ml.models.endpoint_selector import ResizePad, initialize_from_mask_rcnn

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = REPO_ROOT / "ml/data/endpoint_selector_v1.json"
DEFAULT_CONFIG = REPO_ROOT / "ml/configs/endpoint_selector.yaml"
DEFAULT_RUN = REPO_ROOT / "ml/runs/endpoint_selector/v1"
DEFAULT_SUMMARY = REPO_ROOT / "ml/experiments/endpoint_selector_v1_results.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class TensorNoise:
    def __init__(self, gaussian_p: float, gaussian_std: float, sp_p: float, sp_fraction: float) -> None:
        self.gaussian_p = gaussian_p
        self.gaussian_std = gaussian_std
        self.sp_p = sp_p
        self.sp_fraction = sp_fraction

    def __call__(self, tensor: torch.Tensor) -> torch.Tensor:
        if torch.rand(()) < self.gaussian_p:
            tensor = (tensor + torch.randn_like(tensor) * self.gaussian_std).clamp(0, 1)
        if torch.rand(()) < self.sp_p:
            count = max(1, round(tensor.shape[1] * tensor.shape[2] * self.sp_fraction))
            rows = torch.randint(0, tensor.shape[1], (count,))
            cols = torch.randint(0, tensor.shape[2], (count,))
            values = torch.randint(0, 2, (count,), dtype=tensor.dtype)
            tensor[:, rows, cols] = values
        return tensor


class EndpointDataset(Dataset):
    def __init__(self, records: list[dict[str, object]], transform: object) -> None:
        self.records = records
        self.transform = transform

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, int, int]:
        record = self.records[index]
        image = Image.open(REPO_ROOT / str(record["image_path"])).convert("RGB")
        return self.transform(image), int(record["label_id"]), index


def make_transforms(config: dict[str, object], training: bool) -> transforms.Compose:
    size = int(config["image_size"])
    augmentation = config["augmentation"]
    operations: list[object] = [ResizePad(size)]
    if training:
        operations.extend(
            [
                transforms.RandomHorizontalFlip(float(augmentation["horizontal_flip_probability"])),
                transforms.RandomRotation(float(augmentation["rotation_degrees"]), fill=(124, 116, 104)),
                transforms.ColorJitter(
                    brightness=float(augmentation["brightness"]),
                    contrast=float(augmentation["contrast"]),
                ),
                transforms.RandomApply(
                    [transforms.GaussianBlur(kernel_size=3, sigma=(0.1, 1.0))],
                    p=float(augmentation["gaussian_blur_probability"]),
                ),
                transforms.RandomAdjustSharpness(
                    sharpness_factor=1.5,
                    p=float(augmentation["sharpness_probability"]),
                ),
            ]
        )
    operations.append(transforms.ToTensor())
    if training:
        operations.append(
            TensorNoise(
                float(augmentation["gaussian_noise_probability"]),
                float(augmentation["gaussian_noise_std"]),
                float(augmentation["salt_pepper_probability"]),
                float(augmentation["salt_pepper_fraction"]),
            )
        )
    operations.append(transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]))
    return transforms.Compose(operations)


def infer(model: nn.Module, loader: DataLoader, device: torch.device) -> tuple[list[int], list[float], list[int]]:
    model.eval()
    labels: list[int] = []
    scores: list[float] = []
    indices: list[int] = []
    with torch.inference_mode():
        for images, batch_labels, batch_indices in loader:
            probabilities = model(images.to(device)).softmax(dim=1)[:, 1].cpu()
            labels.extend(batch_labels.tolist())
            scores.extend(probabilities.tolist())
            indices.extend(batch_indices.tolist())
    return labels, scores, indices


def select_threshold(labels: list[int], scores: list[float]) -> float:
    candidates = sorted({0.0, 1.0, *scores})
    ranked = []
    for threshold in candidates:
        result = classification_metrics([bool(x) for x in labels], scores, threshold)
        ranked.append((result["f1"], result["accuracy"], -abs(threshold - 0.5), threshold))
    return float(max(ranked)[-1])


def pair_metrics(records: list[dict[str, object]], scores: list[float], indices: list[int]) -> dict[str, object]:
    by_source: dict[str, list[tuple[dict[str, object], float]]] = defaultdict(list)
    for score, index in zip(scores, indices, strict=True):
        record = records[index]
        by_source[str(record["source_image_id"])].append((record, score))
    errors = []
    selections = []
    for source_id, candidates in sorted(by_source.items()):
        if len(candidates) != 2:
            raise ValueError(f"expected two endpoint candidates for {source_id}")
        selected, selected_score = max(candidates, key=lambda item: item[1])
        correct = selected["label"] == "tip"
        selection = {
            "source_image_id": source_id,
            "selected_candidate_id": selected["candidate_id"],
            "selected_side": selected["candidate_side"],
            "tip_score": selected_score,
            "correct": correct,
            "candidates": [
                {"candidate_id": record["candidate_id"], "label": record["label"], "tip_score": score}
                for record, score in candidates
            ],
        }
        selections.append(selection)
        if not correct:
            errors.append(selection)
    return {
        "source_instruments": len(selections),
        "correct": len(selections) - len(errors),
        "accuracy": (len(selections) - len(errors)) / len(selections),
        "errors": errors,
        "selections": selections,
    }


def render_gallery(
    records: list[dict[str, object]], pair_result: dict[str, object], output: Path
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    record_by_id = {str(record["candidate_id"]): record for record in records}
    cards = []
    for selection in pair_result["selections"]:
        candidates = selection["candidates"]
        canvas = Image.new("RGB", (1000, 330), "white")
        draw = ImageDraw.Draw(canvas)
        for column, candidate in enumerate(candidates):
            record = record_by_id[candidate["candidate_id"]]
            image = Image.open(REPO_ROOT / str(record["image_path"])).convert("RGB")
            image.thumbnail((490, 270), Image.Resampling.LANCZOS)
            x = column * 500 + (500 - image.width) // 2
            canvas.paste(image, (x, 48))
            selected = candidate["candidate_id"] == selection["selected_candidate_id"]
            color = "green" if (selected and candidate["label"] == "tip") else ("red" if selected else "black")
            draw.text(
                (column * 500 + 8, 8),
                f"{candidate['label']} | p(tip)={candidate['tip_score']:.3f} | selected={selected}",
                fill=color,
            )
        name = f"{selection['source_image_id']}.jpg"
        canvas.save(output / name, quality=92)
        cards.append((name, selection["correct"]))
    html = ["<!doctype html><meta charset='utf-8'><title>Endpoint selector review</title>", "<h1>Endpoint selector test review</h1>"]
    for name, correct in cards:
        html.append(f"<h2>{name} — {'correct' if correct else 'ERROR'}</h2><img src='{name}' style='max-width:100%'>")
    (output / "index.html").write_text("\n".join(html) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--device", choices=("auto", "mps", "cpu"), default=None)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text())
    seed_everything(int(config["seed"]))
    device = select_device(args.device or str(config["device"]))
    manifest = json.loads(args.manifest.read_text())
    records_by_split = {
        split: [record for record in manifest["records"] if record["split"] == split]
        for split in ("train", "valid", "test")
    }
    loaders = {
        split: DataLoader(
            EndpointDataset(records, make_transforms(config, split == "train")),
            batch_size=int(config["batch_size"]),
            shuffle=split == "train",
            num_workers=0,
        )
        for split, records in records_by_split.items()
    }
    checkpoint_source = Path(config["model"]["local_checkpoint"])
    model = initialize_from_mask_rcnn(checkpoint_source).to(device)
    optimizer = torch.optim.AdamW(
        model.fc.parameters(),
        lr=float(config["learning_rate"]),
        weight_decay=float(config["weight_decay"]),
    )
    criterion = nn.CrossEntropyLoss()
    args.run_dir.mkdir(parents=True, exist_ok=True)
    best_path = args.run_dir / "best.pt"
    history = []
    best_accuracy = -1.0
    stale = 0
    started = time.perf_counter()
    for epoch in range(1, int(config["epochs"]) + 1):
        model.eval()
        model.fc.train()
        loss_total = 0.0
        seen = 0
        for images, labels, _ in loaders["train"]:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(model(images), labels)
            loss.backward()
            optimizer.step()
            loss_total += float(loss.detach().cpu()) * len(labels)
            seen += len(labels)
        val_labels, val_scores, _ = infer(model, loaders["valid"], device)
        threshold = select_threshold(val_labels, val_scores)
        metrics = classification_metrics([bool(x) for x in val_labels], val_scores, threshold)
        item = {"epoch": epoch, "train_loss": loss_total / seen, "validation_threshold": threshold, **metrics}
        history.append(item)
        print(f"epoch={epoch:02d} loss={item['train_loss']:.4f} val_acc={metrics['accuracy']:.4f} val_f1={metrics['f1']:.4f}")
        if metrics["accuracy"] > best_accuracy:
            best_accuracy = float(metrics["accuracy"])
            stale = 0
            torch.save({"model": model.state_dict(), "epoch": epoch, "config": config}, best_path)
        else:
            stale += 1
        if stale >= int(config["patience"]):
            break

    saved = torch.load(best_path, map_location="cpu", weights_only=False)
    model.load_state_dict(saved["model"])
    model.to(device)
    val_labels, val_scores, val_indices = infer(model, loaders["valid"], device)
    threshold = select_threshold(val_labels, val_scores)
    validation_metrics = classification_metrics([bool(x) for x in val_labels], val_scores, threshold)
    test_labels, test_scores, test_indices = infer(model, loaders["test"], device)
    test_metrics = classification_metrics([bool(x) for x in test_labels], test_scores, threshold)
    validation_pairs = pair_metrics(records_by_split["valid"], val_scores, val_indices)
    test_pairs = pair_metrics(records_by_split["test"], test_scores, test_indices)

    predictions = []
    for score, label, index in zip(test_scores, test_labels, test_indices, strict=True):
        record = records_by_split["test"][index]
        predictions.append({**record, "tip_score": score, "predicted_tip": score >= threshold, "correct": (score >= threshold) == bool(label)})
    prediction_path = args.run_dir / "test_predictions.jsonl"
    prediction_path.write_text("".join(json.dumps(item) + "\n" for item in predictions))
    pair_path = args.run_dir / "test_pair_selections.json"
    pair_path.write_text(json.dumps(test_pairs, indent=2) + "\n")
    gallery = args.run_dir / "gallery"
    render_gallery(records_by_split["test"], test_pairs, gallery)

    result = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "status": "awaiting_human_gallery_review",
        "model": config["model"],
        "device": str(device),
        "seed": config["seed"],
        "dataset_sha256": manifest["dataset_sha256"],
        "config": args.config.relative_to(REPO_ROOT).as_posix(),
        "config_sha256": sha256(args.config),
        "source_checkpoint_sha256": sha256(checkpoint_source),
        "best_epoch": saved["epoch"],
        "threshold_selected_on_validation": threshold,
        "validation": validation_metrics,
        "validation_pair_selection": {key: value for key, value in validation_pairs.items() if key != "selections"},
        "test": test_metrics,
        "test_pair_selection": {key: value for key, value in test_pairs.items() if key != "selections"},
        "history": history,
        "elapsed_seconds": time.perf_counter() - started,
        "trainable_parameters": sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad),
        "total_parameters": sum(parameter.numel() for parameter in model.parameters()),
        "checkpoint": best_path.relative_to(REPO_ROOT).as_posix(),
        "checkpoint_sha256": sha256(best_path),
        "test_predictions": prediction_path.relative_to(REPO_ROOT).as_posix(),
        "test_predictions_sha256": sha256(prediction_path),
        "test_pair_selections": pair_path.relative_to(REPO_ROOT).as_posix(),
        "gallery": (gallery / "index.html").relative_to(REPO_ROOT).as_posix(),
    }
    args.summary.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"best_epoch": result["best_epoch"], "threshold": threshold, "validation": validation_metrics, "test": test_metrics, "test_pair_selection": result["test_pair_selection"]}, indent=2))


if __name__ == "__main__":
    main()
