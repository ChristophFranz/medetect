"""Benchmark classification, COCO, and segmentation metrics."""

from __future__ import annotations

import contextlib
import io
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
from pycocotools import mask as mask_utils
from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def classification_metrics(
    labels: list[bool], scores: list[float], threshold: float
) -> dict[str, Any]:
    truth = np.asarray(labels, dtype=bool)
    probabilities = np.asarray(scores, dtype=float)
    predicted = probabilities >= threshold
    tp = int(np.sum(truth & predicted))
    tn = int(np.sum(~truth & ~predicted))
    fp = int(np.sum(~truth & predicted))
    fn = int(np.sum(truth & ~predicted))
    return {
        "accuracy": float(accuracy_score(truth, predicted)),
        "precision": float(precision_score(truth, predicted, zero_division=0)),
        "sensitivity": float(recall_score(truth, predicted, zero_division=0)),
        "specificity": tn / (tn + fp) if tn + fp else 0.0,
        "f1": float(f1_score(truth, predicted, zero_division=0)),
        "pr_auc": float(average_precision_score(truth, probabilities)),
        "roc_auc": float(roc_auc_score(truth, probabilities)),
        "confusion_matrix": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
    }


def bootstrap_intervals(
    labels: list[bool],
    scores: list[float],
    threshold: float,
    *,
    resamples: int,
    confidence_level: float,
    seed: int,
) -> dict[str, list[float]]:
    truth = np.asarray(labels, dtype=bool)
    probabilities = np.asarray(scores, dtype=float)
    positive = np.flatnonzero(truth)
    negative = np.flatnonzero(~truth)
    if not len(positive) or not len(negative):
        raise ValueError("stratified bootstrap requires both classes")
    rng = np.random.default_rng(seed)
    names = (
        "accuracy",
        "precision",
        "sensitivity",
        "specificity",
        "f1",
        "pr_auc",
        "roc_auc",
    )
    values = {name: [] for name in names}
    for _ in range(resamples):
        indices = np.concatenate(
            (
                rng.choice(positive, size=len(positive), replace=True),
                rng.choice(negative, size=len(negative), replace=True),
            )
        )
        result = classification_metrics(
            truth[indices].tolist(), probabilities[indices].tolist(), threshold
        )
        for name in names:
            values[name].append(float(result[name]))
    tail = (1 - confidence_level) / 2
    return {
        name: [
            float(np.quantile(samples, tail)),
            float(np.quantile(samples, 1 - tail)),
        ]
        for name, samples in values.items()
    }


def coco_metrics(
    annotation_path: Path,
    records: list[dict[str, Any]],
    *,
    iou_type: str,
    include: Callable[[float, dict[str, Any] | None], bool],
    normalize_crowd: bool = False,
) -> dict[str, float]:
    payload = json.loads(annotation_path.read_text())
    image_ids = {item["medetect_image_id"]: int(item["id"]) for item in payload["images"]}
    detections = []
    for record in records:
        image_id = image_ids[record["image_id"]]
        for index, score in enumerate(record["instance_scores"]):
            mask = record["masks"][index] if iou_type == "segm" else None
            if not include(float(score), mask):
                continue
            detection: dict[str, Any] = {
                "image_id": image_id,
                "category_id": 1,
                "score": float(score),
            }
            if iou_type == "bbox":
                x1, y1, x2, y2 = record["boxes"][index]
                detection["bbox"] = [x1, y1, x2 - x1, y2 - y1]
            else:
                detection["segmentation"] = mask
            detections.append(detection)
    if not detections:
        return {"map50_95": 0.0, "ap50": 0.0, "ap75": 0.0}
    with contextlib.redirect_stdout(io.StringIO()):
        if normalize_crowd:
            # CVAT represents brush masks as RLE "crowd" regions even when
            # each mask is a reviewed, individual defect instance. COCOeval
            # excludes crowd regions from AP, producing -1 for this cohort.
            # Normalize only in the evaluator; do not alter frozen labels.
            payload = {
                **payload,
                "annotations": [
                    {**annotation, "iscrowd": 0}
                    for annotation in payload["annotations"]
                ],
            }
            ground_truth = COCO()
            ground_truth.dataset = payload
            ground_truth.createIndex()
        else:
            ground_truth = COCO(str(annotation_path))
        predictions = ground_truth.loadRes(detections)
        evaluator = COCOeval(ground_truth, predictions, iou_type)
        evaluator.evaluate()
        evaluator.accumulate()
        evaluator.summarize()
    return {
        "map50_95": float(evaluator.stats[0]),
        "ap50": float(evaluator.stats[1]),
        "ap75": float(evaluator.stats[2]),
    }


def decode_mask(encoded: dict[str, Any]) -> np.ndarray:
    rle = {
        "size": encoded["size"],
        "counts": encoded["counts"].encode("ascii"),
    }
    return mask_utils.decode(rle).astype(bool)


def segmentation_overlap(
    ground_truth_masks: list[np.ndarray], predicted_masks: list[np.ndarray]
) -> dict[str, float]:
    ious = []
    dices = []
    for truth_masks, prediction_masks in zip(
        ground_truth_masks, predicted_masks, strict=True
    ):
        truth = np.any(truth_masks, axis=0)
        prediction = (
            np.any(prediction_masks, axis=0)
            if len(prediction_masks)
            else np.zeros_like(truth)
        )
        intersection = int(np.logical_and(truth, prediction).sum())
        union = int(np.logical_or(truth, prediction).sum())
        truth_area = int(truth.sum())
        prediction_area = int(prediction.sum())
        ious.append(intersection / union if union else 1.0)
        denominator = truth_area + prediction_area
        dices.append(2 * intersection / denominator if denominator else 1.0)
    return {"iou": float(np.mean(ious)), "dice": float(np.mean(dices))}
