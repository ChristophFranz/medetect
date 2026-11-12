"""Run the single authorized frozen-test evaluation for one model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from ml.benchmark.metrics import (
    bootstrap_intervals,
    classification_metrics,
    coco_metrics,
    decode_mask,
    segmentation_overlap,
)
from ml.benchmark.thresholds import mask_area, score_for_area
from ml.data.coco_dataset import FrozenCocoDataset
from ml.models.device import seed_everything
from ml.models.factory import build_adapter

REPO_ROOT = Path(__file__).resolve().parents[2]
ML_ROOT = REPO_ROOT / "ml"
MODELS = ("legacy_yolo", "detr_detection", "detr_segmentation", "mask_rcnn")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("model", choices=MODELS)
    parser.add_argument("--device", choices=("auto", "mps", "cpu"), default="auto")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    freeze_path = ML_ROOT / "experiments/frozen_thresholds.json"
    if not freeze_path.is_file():
        raise SystemExit("test evaluation prohibited: frozen thresholds are missing")
    freeze = json.loads(freeze_path.read_text())
    if freeze["status"] != "frozen_before_test" or freeze["test_split_accessed"]:
        raise SystemExit("test evaluation prohibited: invalid threshold freeze state")
    operating_point = next(
        item for item in freeze["models"] if item["model"] == args.model
    )
    output_dir = ML_ROOT / "runs/benchmark" / args.model
    output_dir.mkdir(parents=True, exist_ok=True)
    prediction_path = output_dir / "test_predictions.jsonl"
    temporary_prediction_path = output_dir / "test_predictions.in_progress.jsonl"
    summary_path = output_dir / "test_summary.json"
    if prediction_path.exists() or summary_path.exists():
        raise SystemExit(f"refusing to repeat frozen-test evaluation: {args.model}")

    seed_everything(42)
    adapter = build_adapter(args.model, device=args.device)
    if args.model != "legacy_yolo":
        adapter.load_checkpoint(REPO_ROOT / operating_point["checkpoint"])
        adapter.score_threshold = 0.05
        if hasattr(adapter, "minimum_mask_area"):
            adapter.minimum_mask_area = 1
    dataset = FrozenCocoDataset("test", allow_test=True)
    records = []
    labels = []
    ground_truth_masks = []
    peak_memory = 0
    for index in range(len(dataset)):
        image, target = dataset[index]
        record = adapter.predict(str(target["image_id"]), image).to_dict()
        records.append(record)
        labels.append(target["status"] == "defective")
        if target["masks"].shape[0]:
            ground_truth_masks.append(target["masks"].numpy().astype(bool))
        else:
            ground_truth_masks.append(
                np.zeros((0, image.height, image.width), dtype=bool)
            )
        if adapter.device.type == "mps":
            peak_memory = max(peak_memory, int(torch.mps.driver_allocated_memory()))
        print(
            json.dumps(
                {"model": args.model, "test_image": index + 1, "total": len(dataset)}
            ),
            flush=True,
        )
    temporary_prediction_path.write_text(
        "\n".join(json.dumps(record, separators=(",", ":")) for record in records)
        + "\n"
    )
    threshold = float(operating_point["score_threshold"])
    minimum_area = operating_point["minimum_mask_area"]
    scores = [score_for_area(record, minimum_area) for record in records]
    metrics = classification_metrics(labels, scores, threshold)
    intervals = bootstrap_intervals(
        labels,
        scores,
        threshold,
        resamples=2000,
        confidence_level=0.95,
        seed=42,
    )
    annotation_path = (
        ML_ROOT
        / "data/local/hook_sinskey/coco_segmentation_v1/annotations/instances_test.json"
    )
    task_metrics: dict[str, object]
    if args.model in {"legacy_yolo", "detr_detection"}:
        task_metrics = {
            "detection": coco_metrics(
                annotation_path,
                records,
                iou_type="bbox",
                include=lambda score, _: score >= threshold,
            )
        }
    else:
        area_threshold = int(minimum_area)
        include = lambda score, mask: score >= threshold and mask_area(mask) >= area_threshold
        predicted_masks = [
            [
                decode_mask(mask)
                for score, mask in zip(
                    record["instance_scores"], record["masks"], strict=True
                )
                if include(float(score), mask)
            ]
            for record in records
        ]
        positive_indices = [index for index, label in enumerate(labels) if label]
        overlap = segmentation_overlap(
            [ground_truth_masks[index] for index in positive_indices],
            [predicted_masks[index] for index in positive_indices],
        )
        task_metrics = {
            "segmentation": {
                **coco_metrics(
                    annotation_path,
                    records,
                    iou_type="segm",
                    include=include,
                ),
                **overlap,
                "overlap_scope": "defective test images; union of instances per image",
            }
        }
    latencies = np.asarray([record["latency_ms"] for record in records])
    underlying = adapter.model if hasattr(adapter.model, "parameters") else adapter.model.model
    parameter_count = sum(parameter.numel() for parameter in underlying.parameters())
    checkpoint_path = REPO_ROOT / operating_point["checkpoint"]
    summary = {
        "schema_version": 1,
        "event": "frozen_test_evaluation",
        "model": args.model,
        "test_images": len(dataset),
        "score_threshold": threshold,
        "minimum_mask_area": minimum_area,
        "classification": metrics,
        "bootstrap_95_ci": intervals,
        **task_metrics,
        "operational": {
            "median_latency_ms": float(np.median(latencies)),
            "p95_latency_ms": float(np.quantile(latencies, 0.95)),
            "model_size_bytes": checkpoint_path.stat().st_size,
            "parameter_count": parameter_count,
            "peak_driver_memory_bytes": peak_memory or None,
            "device": str(adapter.device),
        },
        "prediction_records": prediction_path.relative_to(REPO_ROOT).as_posix(),
        "test_split_accessed_once": True,
        "status": "complete",
    }
    temporary_prediction_path.replace(prediction_path)
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
