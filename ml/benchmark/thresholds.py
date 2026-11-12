"""Validation-only operating-threshold selection."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from pycocotools import mask as mask_utils

from ml.data.coco_dataset import DEFAULT_ROOT, FrozenCocoDataset

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "ml/configs/controlled_benchmark.yaml"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def mask_area(encoded: dict[str, Any]) -> int:
    rle = {
        "size": encoded["size"],
        "counts": encoded["counts"].encode("ascii"),
    }
    return int(mask_utils.area(rle))


def confusion(labels: list[bool], predictions: list[bool]) -> dict[str, int | float]:
    tp = sum(label and prediction for label, prediction in zip(labels, predictions, strict=True))
    tn = sum(
        not label and not prediction
        for label, prediction in zip(labels, predictions, strict=True)
    )
    fp = sum(
        not label and prediction
        for label, prediction in zip(labels, predictions, strict=True)
    )
    fn = sum(
        label and not prediction
        for label, prediction in zip(labels, predictions, strict=True)
    )
    precision = tp / (tp + fp) if tp + fp else 0.0
    sensitivity = tp / (tp + fn) if tp + fn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    f1 = 2 * precision * sensitivity / (precision + sensitivity) if precision + sensitivity else 0.0
    return {
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "sensitivity": sensitivity,
        "specificity": specificity,
        "f1": f1,
    }


def score_for_area(record: dict[str, Any], minimum_mask_area: int | None) -> float:
    scores = [float(score) for score in record["instance_scores"]]
    if minimum_mask_area is None:
        return max(scores, default=0.0)
    eligible = [
        score
        for score, mask in zip(scores, record["masks"], strict=True)
        if mask_area(mask) >= minimum_mask_area
    ]
    return max(eligible, default=0.0)


def threshold_grid(config: dict[str, Any]) -> list[float]:
    values = config["threshold_selection"]["score_grid"]
    return [
        round(float(value), 10)
        for value in np.arange(
            float(values["start"]),
            float(values["stop"]) + float(values["step"]) / 2,
            float(values["step"]),
        )
    ]


def select_thresholds(
    model_name: str,
    prediction_path: Path,
    *,
    config_path: Path = CONFIG_PATH,
    dataset_root: Path | None = None,
) -> dict[str, Any]:
    config = yaml.safe_load(config_path.read_text())
    records = [json.loads(line) for line in prediction_path.read_text().splitlines()]
    dataset = FrozenCocoDataset("valid", root=dataset_root or DEFAULT_ROOT)
    labels_by_id = {
        target["image_id"]: target["status"] == "defective"
        for _, target in (dataset[index] for index in range(len(dataset)))
    }
    if {record["image_id"] for record in records} != set(labels_by_id):
        raise ValueError("candidate predictions do not exactly match the validation split")
    records.sort(key=lambda item: item["image_id"])
    labels = [labels_by_id[record["image_id"]] for record in records]
    areas: list[int | None]
    if model_name in {"detr_segmentation", "mask_rcnn"}:
        areas = [int(value) for value in config["threshold_selection"]["minimum_mask_area_grid"]]
    else:
        areas = [None]

    candidates = []
    for area in areas:
        image_scores = [score_for_area(record, area) for record in records]
        observed_thresholds = [score for score in image_scores if score > 0]
        thresholds = sorted(set(threshold_grid(config) + observed_thresholds))
        for threshold in thresholds:
            metrics = confusion(labels, [score >= threshold for score in image_scores])
            candidates.append(
                {
                    "score_threshold": threshold,
                    "minimum_mask_area": area,
                    "metrics": metrics,
                }
            )
    objective = config["threshold_selection"].get("objective", "image_level_f1")
    if objective == "image_level_f1":
        best = max(
            candidates,
            key=lambda item: (
                item["metrics"]["f1"],
                item["metrics"]["sensitivity"],
                item["metrics"]["specificity"],
                item["score_threshold"],
                -(item["minimum_mask_area"] or 0),
            ),
        )
    elif objective == "balanced_accuracy":
        minimum_sensitivity = float(
            config["threshold_selection"].get("minimum_sensitivity", 0.0)
        )
        eligible = [
            item
            for item in candidates
            if item["metrics"]["sensitivity"] >= minimum_sensitivity
        ]
        if not eligible:
            raise ValueError(
                "no threshold satisfies the configured minimum sensitivity"
            )
        best = max(
            eligible,
            key=lambda item: (
                (
                    item["metrics"]["sensitivity"]
                    + item["metrics"]["specificity"]
                )
                / 2,
                item["metrics"]["specificity"],
                item["metrics"]["f1"],
                item["score_threshold"],
                -(item["minimum_mask_area"] or 0),
            ),
        )
    else:
        raise ValueError(f"unsupported threshold objective: {objective}")
    return {
        "model": model_name,
        "score_threshold": best["score_threshold"],
        "minimum_mask_area": best["minimum_mask_area"],
        "validation_metrics": best["metrics"],
        "validation_images": len(records),
        "candidate_predictions": prediction_path.relative_to(REPO_ROOT).as_posix(),
        "candidate_predictions_sha256": sha256(prediction_path),
        "test_split_accessed": False,
        "selection_objective": objective,
    }
