"""Evaluate fine-tuned defect models on the reviewed new-tray crop cohort.

Operating thresholds are selected from validation predictions before the test
split is opened.  The 24-image test cohort is confirmatory because it has been
viewed during earlier project work.
"""

from __future__ import annotations

import argparse
import hashlib
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
from ml.models.yolo import LegacyYoloAdapter

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = REPO_ROOT / "ml/data/local/hook_sinskey/new_tray_reviewed_v4_augmented_50_50"
DATA_RECORD = REPO_ROOT / "ml/data/hook_sinskey_new_tray_reviewed_v4_augmented_50_50.json"
CONFIG = REPO_ROOT / "ml/configs/fine_tune_v4_50_50.yaml"
RUN_ROOT = REPO_ROOT / "ml/runs/new_tray_v4"
RESULT_PATH = REPO_ROOT / "ml/experiments/new_tray_v4_defect_benchmark_results.json"
THRESHOLD_PATH = REPO_ROOT / "ml/experiments/new_tray_v4_thresholds.json"
MODELS = {
    "yolo_detection": RUN_ROOT / "defect_yolo/fine_tuned/weights/best.pt",
    "detr_detection": RUN_ROOT / "detr_detection/best.pt",
    "detr_segmentation": RUN_ROOT / "detr_segmentation/best.pt",
    "mask_rcnn": RUN_ROOT / "mask_rcnn/best.pt",
}
SEGMENTATION_MODELS = {"detr_segmentation", "mask_rcnn"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(item, separators=(",", ":")) + "\n" for item in records))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def build_loaded_adapter(model_name: str, checkpoint: Path, device: str):
    if model_name == "yolo_detection":
        adapter = LegacyYoloAdapter(
            checkpoint, confidence_threshold=0.001, device=device, maximum_edge=640
        )
        adapter.name = model_name
        return adapter
    adapter = build_adapter(model_name, device=device)
    adapter.load_checkpoint(checkpoint)
    adapter.score_threshold = 0.001
    if hasattr(adapter, "minimum_mask_area"):
        adapter.minimum_mask_area = 1
    return adapter


def predict_split(adapter, split: str) -> tuple[list[dict], list[dict]]:
    dataset = FrozenCocoDataset(split, root=DATA_ROOT, allow_test=split == "test")
    records: list[dict] = []
    targets: list[dict] = []
    for index in range(len(dataset)):
        image, target = dataset[index]
        record = adapter.predict(str(target["image_id"]), image).to_dict()
        record["model"] = adapter.name
        records.append(record)
        targets.append(target)
        print(json.dumps({"model": adapter.name, "split": split, "image": index + 1, "total": len(dataset)}), flush=True)
    return records, targets


def qualifying_indices(record: dict[str, Any], threshold: float, minimum_area: int | None) -> list[int]:
    selected = []
    for index, score in enumerate(record["instance_scores"]):
        if float(score) < threshold:
            continue
        if minimum_area is not None and mask_area(record["masks"][index]) < minimum_area:
            continue
        selected.append(index)
    return selected


def final_record(record: dict[str, Any], threshold: float, minimum_area: int | None) -> dict[str, Any]:
    selected = qualifying_indices(record, threshold, minimum_area)
    scores = [float(record["instance_scores"][index]) for index in selected]
    return {
        **record,
        "defective": bool(selected),
        "confidence": max(scores, default=0.0),
        "boxes": [record["boxes"][index] for index in selected],
        "masks": [record["masks"][index] for index in selected] if record["masks"] else [],
        "instance_scores": scores,
    }


def tint(image: Image.Image, mask: np.ndarray, color: tuple[int, int, int]) -> None:
    pixels = np.asarray(image).copy().astype(np.float32)
    pixels[mask] = 0.55 * pixels[mask] + 0.45 * np.asarray(color, dtype=np.float32)
    image.paste(Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8)))


def export_outputs(model_name: str, records: list[dict], threshold: float, minimum_area: int | None) -> str:
    output = RUN_ROOT / model_name / "test_outputs"
    if output.exists():
        shutil.rmtree(output)
    overlays = output / "overlays"
    masks = output / "masks"
    overlays.mkdir(parents=True)
    masks.mkdir(parents=True)
    dataset = FrozenCocoDataset("test", root=DATA_ROOT, allow_test=True)
    for index, record in enumerate(records):
        image, _ = dataset[index]
        overlay = image.convert("RGB")
        draw = ImageDraw.Draw(overlay)
        union = np.zeros((image.height, image.width), dtype=bool)
        safe = str(record["image_id"]).replace("/", "__")
        for instance_index in qualifying_indices(record, threshold, minimum_area):
            score = float(record["instance_scores"][instance_index])
            if record["masks"]:
                binary = decode_mask(record["masks"][instance_index])
                union |= binary
                Image.fromarray(binary.astype(np.uint8) * 255).save(masks / f"{safe}__instance_{instance_index + 1}.png")
            x1, y1, x2, y2 = record["boxes"][instance_index]
            draw.rectangle((x1, y1, x2, y2), outline=(0, 255, 80), width=4)
            draw.text((x1 + 4, y1 + 4), f"{score:.2f}", fill=(0, 255, 80))
        if union.any():
            tint(overlay, union, (255, 0, 0))
            Image.fromarray(union.astype(np.uint8) * 255).save(masks / f"{safe}__union.png")
        overlay.save(overlays / f"{safe}.jpg", quality=92)
    return output.relative_to(REPO_ROOT).as_posix()


def parameter_count(adapter) -> int:
    model = adapter.model.model if isinstance(adapter, LegacyYoloAdapter) else adapter.model
    return sum(parameter.numel() for parameter in model.parameters())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", choices=("cpu", "mps"), default="cpu")
    args = parser.parse_args()
    missing = [str(path) for path in MODELS.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("training is incomplete; missing checkpoints: " + ", ".join(missing))
    dataset_record = json.loads(DATA_RECORD.read_text())

    operating_points = []
    for model_name, checkpoint in MODELS.items():
        run_dir = RUN_ROOT / model_name
        validation_path = run_dir / "validation_candidates.jsonl"
        if not validation_path.is_file():
            adapter = build_loaded_adapter(model_name, checkpoint, args.device)
            records, _ = predict_split(adapter, "valid")
            write_jsonl(validation_path, records)
            del adapter
            if torch.backends.mps.is_available():
                torch.mps.empty_cache()
        operating_points.append(
            select_thresholds(
                model_name,
                validation_path,
                config_path=CONFIG,
                dataset_root=DATA_ROOT,
            )
        )

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
    targets = [test_dataset[index][1] for index in range(len(test_dataset))]
    labels = [target["status"] == "defective" for target in targets]
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
        intervals = bootstrap_intervals(labels, scores, threshold, resamples=2000, confidence_level=0.95, seed=42)
        if model_name in SEGMENTATION_MODELS:
            area = int(minimum_area)

            def include(score: float, mask: dict | None) -> bool:
                return score >= threshold and mask is not None and mask_area(mask) >= area

            predicted_masks = [
                [decode_mask(mask) for score, mask in zip(record["instance_scores"], record["masks"], strict=True) if include(float(score), mask)]
                for record in raw_records
            ]
            positives = [index for index, label in enumerate(labels) if label]
            localization = {
                "type": "segmentation",
                **coco_metrics(
                    annotation_path,
                    raw_records,
                    iou_type="segm",
                    include=include,
                    normalize_crowd=True,
                ),
                **segmentation_overlap(
                    [targets[index]["masks"].numpy().astype(bool) for index in positives],
                    [predicted_masks[index] for index in positives],
                ),
            }
        else:

            def include(score: float, _mask: dict | None) -> bool:
                return score >= threshold

            localization = {
                "type": "detection",
                **coco_metrics(
                    annotation_path,
                    raw_records,
                    iou_type="bbox",
                    include=include,
                    normalize_crowd=True,
                ),
            }
        finalized = [final_record(record, threshold, minimum_area) for record in raw_records]
        prediction_path = run_dir / "test_predictions.jsonl"
        write_jsonl(prediction_path, finalized)
        output_dir = export_outputs(model_name, raw_records, threshold, minimum_area)
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
                "localization": localization,
                "operational": {
                    "median_latency_ms": float(np.median(latencies)),
                    "p95_latency_ms": float(np.quantile(latencies, 0.95)),
                    "model_size_bytes": checkpoint.stat().st_size,
                    "parameter_count": parameters,
                },
                "prediction_records": prediction_path.relative_to(REPO_ROOT).as_posix(),
                "structured_outputs": output_dir,
            }
        )

    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "status": "confirmatory_awaiting_human_review",
        "evaluation_level": "defect_model_on_reviewed_tip_crops",
        "cohort_note": "Previously exposed 24-crop redesigned-tray test cohort; not an untouched external test.",
        "dataset": DATA_RECORD.relative_to(REPO_ROOT).as_posix(),
        "dataset_version": dataset_record["dataset_version"],
        "threshold_freeze": THRESHOLD_PATH.relative_to(REPO_ROOT).as_posix(),
        "test_images": len(targets),
        "defective_images": sum(labels),
        "healthy_images": len(labels) - sum(labels),
        "models": results,
    }
    RESULT_PATH.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
