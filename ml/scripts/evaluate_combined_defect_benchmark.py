"""Validation-select and evaluate the provisional combined defect benchmark."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from ml.benchmark.metrics import (
    bootstrap_intervals,
    classification_metrics,
    coco_metrics,
    decode_mask,
    segmentation_overlap,
)
from ml.benchmark.thresholds import mask_area, score_for_area, select_thresholds
from ml.data.coco_dataset import FrozenCocoDataset
from ml.models.factory import build_adapter

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = REPO_ROOT / "ml/data/local/hook_sinskey/combined_provisional_v2"
RUN_ROOT = REPO_ROOT / "ml/runs/combined_provisional"
RESULT_PATH = REPO_ROOT / "ml/experiments/combined_provisional_benchmark_results.json"
MODELS = {
    "legacy_yolo": REPO_ROOT / "ml/artifacts/legacy/hook_sinskey/yolov8n_best.pt",
    "detr_detection": RUN_ROOT / "detr_detection/best.pt",
    "mask_rcnn": RUN_ROOT / "mask_rcnn/best.pt",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def predict_split(model_name: str, adapter, split: str) -> tuple[list[dict], list[dict]]:
    dataset = FrozenCocoDataset(split, root=DATA_ROOT, allow_test=split == "test")
    records = []
    targets = []
    for index in range(len(dataset)):
        image, target = dataset[index]
        records.append(adapter.predict(str(target["image_id"]), image).to_dict())
        targets.append(target)
        print(json.dumps({"model": model_name, "split": split, "image": index + 1, "total": len(dataset)}), flush=True)
    return records, targets


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text("".join(json.dumps(record, separators=(",", ":")) + "\n" for record in records))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def safe_name(image_id: str) -> str:
    return image_id.replace("/", "__").replace("\\", "__")


def export_outputs(
    model_name: str,
    records: list[dict],
    targets: list[dict],
    threshold: float,
    minimum_area: int | None,
) -> str:
    output = RUN_ROOT / model_name / "test_outputs"
    if output.exists():
        shutil.rmtree(output)
    overlay_dir = output / "overlays"
    mask_dir = output / "masks"
    overlay_dir.mkdir(parents=True)
    mask_dir.mkdir(parents=True)
    dataset = FrozenCocoDataset("test", root=DATA_ROOT, allow_test=True)
    for index, (record, target) in enumerate(zip(records, targets, strict=True)):
        image, _ = dataset[index]
        overlay = image.convert("RGB")
        draw = ImageDraw.Draw(overlay)
        union = np.zeros((image.height, image.width), dtype=bool)
        filename = safe_name(record["image_id"])
        for instance_index, score in enumerate(record["instance_scores"]):
            encoded = record["masks"][instance_index] if record["masks"] else None
            if score < threshold or (encoded is not None and minimum_area is not None and mask_area(encoded) < minimum_area):
                continue
            if encoded is not None:
                binary = decode_mask(encoded)
                union |= binary
                Image.fromarray(binary.astype(np.uint8) * 255).save(
                    mask_dir / f"{filename}__instance_{instance_index + 1}.png"
                )
            x1, y1, x2, y2 = record["boxes"][instance_index]
            draw.rectangle((x1, y1, x2, y2), outline=(0, 255, 80), width=4)
            draw.text((x1 + 4, y1 + 4), f"{score:.2f}", fill=(0, 255, 80))
        if union.any():
            array = np.asarray(overlay).copy().astype(np.float32)
            red = np.zeros_like(array)
            red[..., 0] = 255
            array[union] = 0.55 * array[union] + 0.45 * red[union]
            overlay = Image.fromarray(np.clip(array, 0, 255).astype(np.uint8))
            Image.fromarray(union.astype(np.uint8) * 255).save(mask_dir / f"{filename}__union.png")
        overlay.save(overlay_dir / f"{filename}.jpg", quality=92)
    return output.relative_to(REPO_ROOT).as_posix()


def main() -> None:
    results = []
    thresholds = []
    for model_name, checkpoint in MODELS.items():
        adapter = build_adapter(model_name, device="cpu")
        if model_name != "legacy_yolo":
            adapter.load_checkpoint(checkpoint)
            adapter.score_threshold = 0.05
            if hasattr(adapter, "minimum_mask_area"):
                adapter.minimum_mask_area = 1
        run_dir = RUN_ROOT / model_name
        run_dir.mkdir(parents=True, exist_ok=True)
        validation_path = run_dir / "validation_candidates.jsonl"
        if validation_path.is_file():
            validation_records = read_jsonl(validation_path)
        else:
            validation_records, _ = predict_split(model_name, adapter, "valid")
            write_jsonl(validation_path, validation_records)
        if model_name == "legacy_yolo":
            operating_point = {"model": model_name, "score_threshold": 0.1, "minimum_mask_area": None}
        else:
            operating_point = select_thresholds(model_name, validation_path, dataset_root=DATA_ROOT)
        thresholds.append(operating_point)

        prediction_path = run_dir / "test_predictions.jsonl"
        test_dataset = FrozenCocoDataset("test", root=DATA_ROOT, allow_test=True)
        test_targets = [test_dataset[index][1] for index in range(len(test_dataset))]
        if prediction_path.is_file():
            test_records = read_jsonl(prediction_path)
        else:
            test_records, test_targets = predict_split(model_name, adapter, "test")
            write_jsonl(prediction_path, test_records)
        labels = [target["status"] == "defective" for target in test_targets]
        minimum_area = operating_point["minimum_mask_area"]
        threshold = float(operating_point["score_threshold"])
        scores = [score_for_area(record, minimum_area) for record in test_records]
        classification = classification_metrics(labels, scores, threshold)
        intervals = bootstrap_intervals(labels, scores, threshold, resamples=1000, confidence_level=0.95, seed=42)
        domains = {}
        for domain in ("old", "new"):
            indices = [index for index, record in enumerate(test_records) if record["image_id"].startswith(f"{domain}__")]
            domains[domain] = classification_metrics(
                [labels[index] for index in indices], [scores[index] for index in indices], threshold
            )
        annotation_path = DATA_ROOT / "annotations/instances_test.json"
        if model_name in {"legacy_yolo", "detr_detection"}:
            localization = {
                "detection": coco_metrics(
                    annotation_path,
                    test_records,
                    iou_type="bbox",
                    include=lambda score, _: score >= threshold,
                )
            }
        else:
            area_threshold = int(minimum_area)
            include = lambda score, mask: score >= threshold and mask_area(mask) >= area_threshold
            predicted_masks = [
                [decode_mask(mask) for score, mask in zip(record["instance_scores"], record["masks"], strict=True) if include(float(score), mask)]
                for record in test_records
            ]
            truth_masks = [target["masks"].numpy().astype(bool) for target in test_targets]
            positives = [index for index, label in enumerate(labels) if label]
            localization = {
                "segmentation": {
                    **coco_metrics(annotation_path, test_records, iou_type="segm", include=include),
                    **segmentation_overlap(
                        [truth_masks[index] for index in positives],
                        [predicted_masks[index] for index in positives],
                    ),
                }
            }
        output_dir = export_outputs(model_name, test_records, test_targets, threshold, minimum_area)
        results.append(
            {
                "model": model_name,
                "checkpoint": checkpoint.relative_to(REPO_ROOT).as_posix(),
                "checkpoint_sha256": sha256(checkpoint),
                "score_threshold": threshold,
                "minimum_mask_area": minimum_area,
                "classification": classification,
                "bootstrap_95_ci": intervals,
                "classification_by_domain": domains,
                **localization,
                "prediction_records": prediction_path.relative_to(REPO_ROOT).as_posix(),
                "structured_outputs": output_dir,
            }
        )
    payload = {
        "schema_version": 1,
        "status": "provisional_unreviewed_new_tray_masks_one_epoch_adaptation",
        "dataset": "ml/data/combined_hook_sinskey_provisional_v2.json",
        "validation_selected_thresholds": thresholds,
        "test_images": 46,
        "test_evaluations_per_model": 1,
        "models": results,
    }
    RESULT_PATH.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
