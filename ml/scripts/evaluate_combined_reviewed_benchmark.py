"""Evaluate the authoritative combined reviewed-v3 Hook Sinskey benchmark."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import torch
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
DATA_ROOT = REPO_ROOT / "ml/data/local/hook_sinskey/combined_reviewed_v3"
DATA_RECORD = REPO_ROOT / "ml/data/combined_hook_sinskey_reviewed_v3.json"
RUN_ROOT = REPO_ROOT / "ml/runs/combined_reviewed_v3"
RESULT_PATH = REPO_ROOT / "ml/experiments/combined_reviewed_v3_benchmark_results.json"
THRESHOLD_PATH = REPO_ROOT / "ml/experiments/combined_reviewed_v3_thresholds.json"
MODELS = {
    "legacy_yolo": REPO_ROOT / "ml/artifacts/legacy/hook_sinskey/yolov8n_best.pt",
    "detr_detection": RUN_ROOT / "detr_detection/best.pt",
    "detr_segmentation": RUN_ROOT / "detr_segmentation/best.pt",
    "mask_rcnn": RUN_ROOT / "mask_rcnn/best.pt",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(record, separators=(",", ":")) + "\n" for record in records)
    )


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def build_loaded_adapter(model_name: str, checkpoint: Path, device: str):
    adapter = build_adapter(model_name, device=device)
    if model_name != "legacy_yolo":
        adapter.load_checkpoint(checkpoint)
        adapter.score_threshold = 0.05
        if hasattr(adapter, "minimum_mask_area"):
            adapter.minimum_mask_area = 1
    return adapter


def predict_split(adapter, split: str) -> tuple[list[dict], list[dict]]:
    dataset = FrozenCocoDataset(split, root=DATA_ROOT, allow_test=split == "test")
    records = []
    targets = []
    for index in range(len(dataset)):
        image, target = dataset[index]
        records.append(adapter.predict(str(target["image_id"]), image).to_dict())
        targets.append(target)
        print(
            json.dumps(
                {
                    "model": adapter.name,
                    "split": split,
                    "image": index + 1,
                    "total": len(dataset),
                }
            ),
            flush=True,
        )
    return records, targets


def qualifying_indices(
    record: dict[str, Any], threshold: float, minimum_area: int | None
) -> list[int]:
    indices = []
    for index, score in enumerate(record["instance_scores"]):
        if float(score) < threshold:
            continue
        if minimum_area is not None and mask_area(record["masks"][index]) < minimum_area:
            continue
        indices.append(index)
    return indices


def finalize_record(
    record: dict[str, Any], threshold: float, minimum_area: int | None
) -> dict[str, Any]:
    indices = qualifying_indices(record, threshold, minimum_area)
    scores = [float(record["instance_scores"][index]) for index in indices]
    return {
        **record,
        "defective": bool(indices),
        "confidence": max(scores, default=0.0),
        "boxes": [record["boxes"][index] for index in indices],
        "masks": [record["masks"][index] for index in indices] if record["masks"] else [],
        "instance_scores": scores,
    }


def safe_name(image_id: str) -> str:
    return image_id.replace("/", "__").replace("\\", "__")


def tint(image: Image.Image, mask: np.ndarray, color: tuple[int, int, int]) -> None:
    array = np.asarray(image).copy().astype(np.float32)
    color_array = np.asarray(color, dtype=np.float32)
    array[mask] = 0.55 * array[mask] + 0.45 * color_array
    image.paste(Image.fromarray(np.clip(array, 0, 255).astype(np.uint8)))


def export_outputs(
    model_name: str,
    raw_records: list[dict],
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
    for index, (record, _target) in enumerate(zip(raw_records, targets, strict=True)):
        image, _ = dataset[index]
        overlay = image.convert("RGB")
        draw = ImageDraw.Draw(overlay)
        union = np.zeros((image.height, image.width), dtype=bool)
        filename = safe_name(record["image_id"])
        for instance_index in qualifying_indices(record, threshold, minimum_area):
            score = float(record["instance_scores"][instance_index])
            encoded = record["masks"][instance_index] if record["masks"] else None
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
            tint(overlay, union, (255, 0, 0))
            Image.fromarray(union.astype(np.uint8) * 255).save(
                mask_dir / f"{filename}__union.png"
            )
        overlay.save(overlay_dir / f"{filename}.jpg", quality=92)
    return output.relative_to(REPO_ROOT).as_posix()


def parameter_count(adapter) -> int:
    model = adapter.model.model if adapter.name == "legacy_yolo" else adapter.model
    return sum(parameter.numel() for parameter in model.parameters())


def render_error_gallery(
    models: list[dict[str, Any]], targets: list[dict[str, Any]]
) -> tuple[str, int]:
    gallery = RUN_ROOT / "error_gallery"
    if gallery.exists():
        shutil.rmtree(gallery)
    gallery.mkdir(parents=True)
    dataset = FrozenCocoDataset("test", root=DATA_ROOT, allow_test=True)
    images = {dataset[index][1]["image_id"]: dataset[index][0] for index in range(len(dataset))}
    target_by_id = {target["image_id"]: target for target in targets}
    cards = []
    error_count = 0
    for model in models:
        for record in read_jsonl(REPO_ROOT / model["prediction_records"]):
            target = target_by_id[record["image_id"]]
            truth = target["status"] == "defective"
            if bool(record["defective"]) == truth:
                continue
            error_count += 1
            rendered = images[record["image_id"]].copy()
            draw = ImageDraw.Draw(rendered)
            if model["model"] in {"detr_segmentation", "mask_rcnn"}:
                for mask in target["masks"]:
                    tint(rendered, mask.numpy().astype(bool), (0, 210, 80))
                for encoded in record["masks"]:
                    tint(rendered, decode_mask(encoded), (235, 30, 120))
            else:
                for box in target["boxes"].tolist():
                    draw.rectangle(box, outline=(0, 210, 80), width=5)
                for box in record["boxes"]:
                    draw.rectangle(box, outline=(235, 30, 80), width=5)
            filename = f"{model['model']}_{error_count:03d}.jpg"
            rendered.save(gallery / filename, quality=92)
            cards.append(
                "<article>"
                f"<h3>{html.escape(model['model'])}: {html.escape(str(target['status']))} → "
                f"{'defective' if record['defective'] else 'healthy'}</h3>"
                f"<img src='{filename}' loading='lazy'>"
                f"<p><code>{html.escape(record['image_id'])}</code></p></article>"
            )
    (gallery / "index.html").write_text(
        "<!doctype html><meta charset='utf-8'><title>Combined v3 errors</title>"
        "<style>body{font:15px system-ui;margin:24px;background:#eee}main{display:grid;"
        "grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:16px}article{background:"
        "white;padding:12px}img{max-width:100%;height:auto}code{overflow-wrap:anywhere}</style>"
        "<h1>Combined reviewed-v3 frozen-test errors</h1><main>"
        + "".join(cards)
        + "</main>"
    )
    return (gallery / "index.html").relative_to(REPO_ROOT).as_posix(), error_count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", choices=("cpu", "mps"), default="cpu")
    args = parser.parse_args()
    dataset_record = json.loads(DATA_RECORD.read_text())

    operating_points = []
    for model_name, checkpoint in MODELS.items():
        run_dir = RUN_ROOT / model_name
        run_dir.mkdir(parents=True, exist_ok=True)
        validation_path = run_dir / "validation_candidates.jsonl"
        if not validation_path.is_file():
            adapter = build_loaded_adapter(model_name, checkpoint, args.device)
            validation_records, _ = predict_split(adapter, "valid")
            write_jsonl(validation_path, validation_records)
            del adapter
            if torch.backends.mps.is_available():
                torch.mps.empty_cache()
        if model_name == "legacy_yolo":
            operating_point = {
                "model": model_name,
                "score_threshold": 0.1,
                "minimum_mask_area": None,
                "selection": "inherited operating point; unchanged",
                "test_split_accessed": False,
            }
        else:
            operating_point = select_thresholds(
                model_name,
                validation_path,
                config_path=REPO_ROOT / "ml/configs/combined_reviewed_v3.yaml",
                dataset_root=DATA_ROOT,
            )
        operating_points.append(operating_point)

    threshold_payload = {
        "schema_version": 1,
        "frozen_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "dataset_version": dataset_record["dataset_version"],
        "dataset_sha256": dataset_record["tree_sha256"],
        "selection_split": "valid",
        "test_split_accessed": False,
        "operating_points": operating_points,
    }
    THRESHOLD_PATH.write_text(json.dumps(threshold_payload, indent=2) + "\n")

    test_dataset = FrozenCocoDataset("test", root=DATA_ROOT, allow_test=True)
    test_targets = [test_dataset[index][1] for index in range(len(test_dataset))]
    labels = [target["status"] == "defective" for target in test_targets]
    annotation_path = DATA_ROOT / "annotations/instances_test.json"
    results = []
    for operating_point in operating_points:
        model_name = operating_point["model"]
        checkpoint = MODELS[model_name]
        run_dir = RUN_ROOT / model_name
        candidates_path = run_dir / "test_candidates.jsonl"
        adapter = build_loaded_adapter(model_name, checkpoint, args.device)
        parameters = parameter_count(adapter)
        if candidates_path.is_file():
            raw_records = read_jsonl(candidates_path)
        else:
            raw_records, _ = predict_split(adapter, "test")
            write_jsonl(candidates_path, raw_records)
        del adapter
        if torch.backends.mps.is_available():
            torch.mps.empty_cache()

        threshold = float(operating_point["score_threshold"])
        minimum_area = operating_point["minimum_mask_area"]
        scores = [score_for_area(record, minimum_area) for record in raw_records]
        classification = classification_metrics(labels, scores, threshold)
        intervals = bootstrap_intervals(
            labels, scores, threshold, resamples=2000, confidence_level=0.95, seed=42
        )
        domains = {}
        for domain in ("old", "new"):
            indices = [
                index
                for index, record in enumerate(raw_records)
                if record["image_id"].startswith(f"{domain}__")
            ]
            domains[domain] = classification_metrics(
                [labels[index] for index in indices],
                [scores[index] for index in indices],
                threshold,
            )

        if model_name in {"legacy_yolo", "detr_detection"}:
            def include_box(
                score: float,
                _mask: dict | None,
                frozen_threshold: float = threshold,
            ) -> bool:
                return score >= frozen_threshold

            localization = {
                "detection": coco_metrics(
                    annotation_path, raw_records, iou_type="bbox", include=include_box
                )
            }
        else:
            area_threshold = int(minimum_area)

            def include_mask(
                score: float,
                mask: dict | None,
                frozen_threshold: float = threshold,
                frozen_area: int = area_threshold,
            ) -> bool:
                return (
                    score >= frozen_threshold
                    and mask is not None
                    and mask_area(mask) >= frozen_area
                )

            predicted_masks = [
                [
                    decode_mask(mask)
                    for score, mask in zip(
                        record["instance_scores"], record["masks"], strict=True
                    )
                    if include_mask(float(score), mask)
                ]
                for record in raw_records
            ]
            truth_masks = [target["masks"].numpy().astype(bool) for target in test_targets]
            positives = [index for index, label in enumerate(labels) if label]
            localization = {
                "segmentation": {
                    **coco_metrics(
                        annotation_path,
                        raw_records,
                        iou_type="segm",
                        include=include_mask,
                    ),
                    **segmentation_overlap(
                        [truth_masks[index] for index in positives],
                        [predicted_masks[index] for index in positives],
                    ),
                }
            }

        final_records = [
            finalize_record(record, threshold, minimum_area) for record in raw_records
        ]
        prediction_path = run_dir / "test_predictions.jsonl"
        write_jsonl(prediction_path, final_records)
        output_dir = export_outputs(
            model_name, raw_records, test_targets, threshold, minimum_area
        )
        latencies = np.asarray([record["latency_ms"] for record in raw_records])
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
                "operational": {
                    "median_latency_ms": float(np.median(latencies)),
                    "p95_latency_ms": float(np.quantile(latencies, 0.95)),
                    "model_size_bytes": checkpoint.stat().st_size,
                    "parameter_count": parameters,
                },
                "candidate_records": candidates_path.relative_to(REPO_ROOT).as_posix(),
                "prediction_records": prediction_path.relative_to(REPO_ROOT).as_posix(),
                "structured_outputs": output_dir,
            }
        )

    gallery_path, error_count = render_error_gallery(results, test_targets)
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "status": "awaiting_human_review",
        "dataset": DATA_RECORD.relative_to(REPO_ROOT).as_posix(),
        "dataset_version": dataset_record["dataset_version"],
        "dataset_sha256": dataset_record["tree_sha256"],
        "threshold_freeze": THRESHOLD_PATH.relative_to(REPO_ROOT).as_posix(),
        "threshold_freeze_sha256": sha256(THRESHOLD_PATH),
        "test_images": len(test_targets),
        "test_evaluations_per_model": 1,
        "models": results,
        "error_gallery": gallery_path,
        "error_count": error_count,
    }
    RESULT_PATH.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
