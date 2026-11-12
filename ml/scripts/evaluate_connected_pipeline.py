"""Run the confirmatory full-tray to defect-mask Hook Sinskey pipeline."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import torch
import yaml
from PIL import Image, ImageDraw, ImageOps
from pycocotools import mask as mask_utils
from ultralytics import YOLO

from ml.benchmark.metrics import (
    bootstrap_intervals,
    classification_metrics,
    decode_mask,
)
from ml.models.endpoint_selector import EndpointSelector
from ml.models.factory import build_adapter

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_MANIFEST = REPO_ROOT / "ml/annotation/new_tray_manifest.json"
CROP_MANIFEST = REPO_ROOT / "ml/annotation/new_tray_model_cropped_manifest.json"
REVIEWED_BOXES = (
    REPO_ROOT
    / "ml/annotation/local/new_tray_detection_reviewed/annotations/instances_default.json"
)
REVIEWED_DEFECTS = (
    REPO_ROOT
    / "ml/data/local/hook_sinskey/combined_reviewed_v3/annotations/instances_test.json"
)
ENDPOINT_CONFIG = REPO_ROOT / "ml/configs/endpoint_selector.yaml"
ENDPOINT_POLICY = REPO_ROOT / "ml/experiments/endpoint_selector_v1_policy.json"
DEFECT_THRESHOLDS = REPO_ROOT / "ml/experiments/combined_reviewed_v3_thresholds.json"
TRAY_CHECKPOINT = (
    REPO_ROOT / "ml/runs/tray_yolo/combined_provisional_presentation_20e/weights/best.pt"
)
MASK_CHECKPOINT = REPO_ROOT / "ml/runs/combined_reviewed_v3/mask_rcnn/best.pt"
RUN_ROOT = REPO_ROOT / "ml/runs/connected_pipeline_confirmatory"
RESULT_PATH = REPO_ROOT / "ml/experiments/connected_pipeline_confirmatory_results.json"
TRAY_THRESHOLD = 0.10
MATCH_IOU = 0.50
LOCALIZATION_IOU = 0.50


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def box_iou(first: list[float], second: list[float]) -> float:
    ax1, ay1, ax2, ay2 = first
    bx1, by1, bx2, by2 = second
    intersection = max(0.0, min(ax2, bx2) - max(ax1, bx1)) * max(
        0.0, min(ay2, by2) - max(ay1, by1)
    )
    first_area = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    second_area = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = first_area + second_area - intersection
    return intersection / union if union else 0.0


def greedy_matches(
    predictions: list[list[float]],
    ground_truth: list[list[float]],
    minimum_iou: float,
) -> list[tuple[int, int, float]]:
    candidates = sorted(
        (
            (box_iou(prediction, truth), prediction_index, truth_index)
            for prediction_index, prediction in enumerate(predictions)
            for truth_index, truth in enumerate(ground_truth)
        ),
        reverse=True,
    )
    matches = []
    used_predictions: set[int] = set()
    used_truth: set[int] = set()
    for iou, prediction_index, truth_index in candidates:
        if iou < minimum_iou:
            break
        if prediction_index in used_predictions or truth_index in used_truth:
            continue
        matches.append((prediction_index, truth_index, iou))
        used_predictions.add(prediction_index)
        used_truth.add(truth_index)
    return matches


def decode_coco_mask(segmentation: dict[str, Any]) -> np.ndarray:
    if isinstance(segmentation["counts"], list):
        encoded = mask_utils.frPyObjects(
            segmentation,
            int(segmentation["size"][0]),
            int(segmentation["size"][1]),
        )
    else:
        encoded = {
            "size": segmentation["size"],
            "counts": str(segmentation["counts"]).encode("ascii"),
        }
    return mask_utils.decode(encoded).astype(bool)


def project_crop_mask(
    mask: np.ndarray,
    crop_box: list[int],
    full_shape: tuple[int, int],
    mirrored: bool,
) -> np.ndarray:
    if mirrored:
        mask = np.fliplr(mask)
    left, top, right, bottom = crop_box
    expected_width = right - left
    expected_height = bottom - top
    if mask.shape != (expected_height, expected_width):
        mask = np.asarray(
            Image.fromarray(mask.astype(np.uint8)).resize(
                (expected_width, expected_height), Image.Resampling.NEAREST
            )
        ).astype(bool)
    projected = np.zeros(full_shape, dtype=bool)
    projected[top:bottom, left:right] = mask
    return projected


def union_prediction_masks(record: dict[str, Any]) -> np.ndarray | None:
    masks = [decode_mask(encoded) for encoded in record["masks"]]
    return np.any(masks, axis=0) if masks else None


def mask_iou(prediction: np.ndarray | None, truth: np.ndarray) -> float:
    if prediction is None:
        return 0.0
    intersection = int(np.logical_and(prediction, truth).sum())
    union = int(np.logical_or(prediction, truth).sum())
    return intersection / union if union else 0.0


def mask_dice(prediction: np.ndarray | None, truth: np.ndarray) -> float:
    if prediction is None:
        return 0.0
    intersection = int(np.logical_and(prediction, truth).sum())
    denominator = int(prediction.sum()) + int(truth.sum())
    return 2 * intersection / denominator if denominator else 0.0


def tint(image: Image.Image, mask: np.ndarray, color: tuple[int, int, int]) -> None:
    values = np.asarray(image).copy().astype(np.float32)
    values[mask] = 0.58 * values[mask] + 0.42 * np.asarray(color, dtype=np.float32)
    image.paste(Image.fromarray(np.clip(values, 0, 255).astype(np.uint8)))


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(record) + "\n" for record in records))


def load_ground_truth() -> tuple[dict[str, list[dict]], dict[str, np.ndarray]]:
    source_manifest = json.loads(SOURCE_MANIFEST.read_text())
    boxes = json.loads(REVIEWED_BOXES.read_text())
    defects = json.loads(REVIEWED_DEFECTS.read_text())

    status_by_key = {
        (item["source_relative_path"], int(item["source_instance_index"])): item
        for item in source_manifest["images"]
    }
    images_by_number = {int(item["id"]): item for item in boxes["images"]}
    truth_by_source: dict[str, list[dict]] = defaultdict(list)
    for annotation in boxes["annotations"]:
        image = images_by_number[int(annotation["image_id"])]
        if image["split"] != "test":
            continue
        relative = image["source_relative_path"]
        instance_index = int(annotation["source_instance_index"])
        x, y, width, height = map(float, annotation["bbox"])
        source_record = status_by_key[(relative, instance_index)]
        truth_by_source[relative].append(
            {
                "image_id": source_record["image_id"],
                "source_instance_index": instance_index,
                "status": source_record["status"],
                "box": [x, y, x + width, y + height],
            }
        )
    for records in truth_by_source.values():
        records.sort(key=lambda item: item["source_instance_index"])

    defect_images = {
        int(item["id"]): item
        for item in defects["images"]
        if item.get("source_domain") == "reviewed_new_tray"
    }
    annotations_by_image: dict[int, list[dict]] = defaultdict(list)
    for annotation in defects["annotations"]:
        if int(annotation["image_id"]) in defect_images:
            annotations_by_image[int(annotation["image_id"])].append(annotation)
    masks: dict[str, np.ndarray] = {}
    for image_number, image in defect_images.items():
        image_id = str(image["medetect_image_id"]).removeprefix("new__")
        height = int(image["height"])
        width = int(image["width"])
        crop_union = np.zeros((height, width), dtype=bool)
        for annotation in annotations_by_image[image_number]:
            crop_union |= decode_coco_mask(annotation["segmentation"])
        masks[image_id] = crop_union
    return dict(truth_by_source), masks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", choices=("cpu", "mps"), default="cpu")
    args = parser.parse_args()
    if RUN_ROOT.exists():
        shutil.rmtree(RUN_ROOT)
    (RUN_ROOT / "overlays").mkdir(parents=True)
    (RUN_ROOT / "masks").mkdir(parents=True)

    source_manifest = json.loads(SOURCE_MANIFEST.read_text())
    crop_manifest = json.loads(CROP_MANIFEST.read_text())
    endpoint_policy = json.loads(ENDPOINT_POLICY.read_text())
    endpoint_config = yaml.safe_load(ENDPOINT_CONFIG.read_text())
    thresholds = json.loads(DEFECT_THRESHOLDS.read_text())
    threshold_by_model = {
        item["model"]: item for item in thresholds["operating_points"]
    }
    mask_threshold = threshold_by_model["mask_rcnn"]
    yolo_threshold = threshold_by_model["legacy_yolo"]
    review_margin = float(endpoint_policy["review_policy"]["score_margin_threshold"])

    endpoint = EndpointSelector.from_checkpoint(
        REPO_ROOT / endpoint_policy["checkpoint"],
        int(endpoint_config["image_size"]),
        torch.device(args.device),
    )
    mask_adapter = build_adapter("mask_rcnn", device=args.device)
    mask_adapter.load_checkpoint(MASK_CHECKPOINT)
    mask_adapter.score_threshold = float(mask_threshold["score_threshold"])
    mask_adapter.minimum_mask_area = int(mask_threshold["minimum_mask_area"])
    yolo_adapter = build_adapter("legacy_yolo", device=args.device)
    yolo_adapter.confidence_threshold = float(yolo_threshold["score_threshold"])
    tray_model = YOLO(TRAY_CHECKPOINT)

    truth_by_source, ground_truth_crop_masks = load_ground_truth()
    crop_by_id = {item["image_id"]: item for item in crop_manifest["images"]}
    raw_root = REPO_ROOT / source_manifest["local_root"] / "raw"
    source_records = {
        item["source_relative_path"]: item
        for item in source_manifest["sources"]
        if item["split"] == "test"
    }

    instance_records: list[dict[str, Any]] = []
    extra_prediction_records: list[dict[str, Any]] = []
    tray_records: list[dict[str, Any]] = []
    total_predictions = 0
    total_matches = 0
    endpoint_correct = 0
    endpoint_evaluated = 0
    tray_latencies = []
    for tray_index, relative in enumerate(sorted(source_records), start=1):
        with Image.open(raw_root / relative) as handle:
            image = ImageOps.exif_transpose(handle).convert("RGB")
        start = time.perf_counter()
        tray_start = time.perf_counter()
        result = tray_model.predict(
            image,
            imgsz=640,
            conf=TRAY_THRESHOLD,
            device=args.device,
            verbose=False,
        )[0]
        tray_detection_ms = (time.perf_counter() - tray_start) * 1000
        predictions = []
        if result.boxes is not None:
            for box, score, class_id in zip(
                result.boxes.xyxy.cpu().tolist(),
                result.boxes.conf.cpu().tolist(),
                result.boxes.cls.cpu().tolist(),
                strict=True,
            ):
                if int(class_id) == 3:
                    predictions.append({"box": box, "score": float(score)})
        predicted_outputs = []
        for prediction_index, prediction in enumerate(predictions):
            endpoint_start = time.perf_counter()
            crop, selection = endpoint.select_from_box(
                image,
                prediction["box"],
                review_margin_threshold=review_margin,
            )
            endpoint_ms = (time.perf_counter() - endpoint_start) * 1000
            output_id = f"tray_{tray_index:02d}_prediction_{prediction_index + 1}"
            mask_prediction = mask_adapter.predict(output_id, crop).to_dict()
            yolo_prediction = yolo_adapter.predict(output_id, crop).to_dict()
            predicted_outputs.append(
                {
                    **prediction,
                    "endpoint": selection,
                    "endpoint_latency_ms": endpoint_ms,
                    "crop": crop,
                    "mask_prediction": mask_prediction,
                    "yolo_prediction": yolo_prediction,
                }
            )

        truths = truth_by_source[relative]
        matches = greedy_matches(
            [item["box"] for item in predictions],
            [item["box"] for item in truths],
            MATCH_IOU,
        )
        prediction_to_match = {
            prediction_index: (truth_index, iou)
            for prediction_index, truth_index, iou in matches
        }
        truth_to_match = {
            truth_index: (prediction_index, iou)
            for prediction_index, truth_index, iou in matches
        }
        total_predictions += len(predictions)
        total_matches += len(matches)

        overlay = image.copy()
        draw = ImageDraw.Draw(overlay)
        for truth in truths:
            draw.rectangle(truth["box"], outline=(40, 130, 255), width=10)
        for prediction_index, output in enumerate(predicted_outputs):
            color = (0, 210, 80) if prediction_index in prediction_to_match else (255, 170, 0)
            draw.rectangle(output["box"], outline=color, width=10)
            if prediction_index not in prediction_to_match:
                continue
            truth_index, _ = prediction_to_match[prediction_index]
            truth = truths[truth_index]
            crop_box = output["endpoint"]["source_crop_xyxy"]
            crop_mask = union_prediction_masks(output["mask_prediction"])
            predicted_full_mask = (
                project_crop_mask(
                    crop_mask,
                    crop_box,
                    (image.height, image.width),
                    bool(output["endpoint"]["canonicalized_by_horizontal_flip"]),
                )
                if crop_mask is not None
                else None
            )
            if predicted_full_mask is not None:
                tint(overlay, predicted_full_mask, (245, 30, 80))

            crop_record = crop_by_id[truth["image_id"]]
            truth_crop_mask = ground_truth_crop_masks[truth["image_id"]]
            truth_full_mask = project_crop_mask(
                truth_crop_mask,
                [int(value) for value in crop_record["source_crop_xyxy"]],
                (image.height, image.width),
                bool(crop_record["canonicalized_by_horizontal_flip"]),
            )
            if truth["status"] == "defective":
                tint(overlay, truth_full_mask, (0, 210, 80))

        for truth_index, truth in enumerate(truths):
            matched = truth_index in truth_to_match
            if matched:
                prediction_index, detection_iou = truth_to_match[truth_index]
                output = predicted_outputs[prediction_index]
                selected_side = output["endpoint"]["selected_side"]
                expected_side = crop_by_id[truth["image_id"]]["source_tip_side"]
                selected_correctly = selected_side == expected_side
                endpoint_correct += int(selected_correctly)
                endpoint_evaluated += 1
                crop_mask = union_prediction_masks(output["mask_prediction"])
                predicted_full_mask = (
                    project_crop_mask(
                        crop_mask,
                        output["endpoint"]["source_crop_xyxy"],
                        (image.height, image.width),
                        bool(output["endpoint"]["canonicalized_by_horizontal_flip"]),
                    )
                    if crop_mask is not None
                    else None
                )
                crop_record = crop_by_id[truth["image_id"]]
                truth_full_mask = project_crop_mask(
                    ground_truth_crop_masks[truth["image_id"]],
                    [int(value) for value in crop_record["source_crop_xyxy"]],
                    (image.height, image.width),
                    bool(crop_record["canonicalized_by_horizontal_flip"]),
                )
                iou = mask_iou(predicted_full_mask, truth_full_mask)
                dice = mask_dice(predicted_full_mask, truth_full_mask)
                mask_decision = bool(output["mask_prediction"]["defective"])
                yolo_decision = bool(output["yolo_prediction"]["defective"])
                mask_score = float(output["mask_prediction"]["confidence"])
                endpoint_review = bool(output["endpoint"]["review_required"])
                disagreement = mask_decision != yolo_decision
                hybrid_review = endpoint_review or disagreement
                endpoint_record = output["endpoint"]
                endpoint_latency = float(output["endpoint_latency_ms"])
                mask_latency = float(output["mask_prediction"]["latency_ms"])
                yolo_latency = float(output["yolo_prediction"]["latency_ms"])
            else:
                detection_iou = 0.0
                selected_side = None
                expected_side = crop_by_id[truth["image_id"]]["source_tip_side"]
                selected_correctly = False
                iou = 0.0
                dice = 0.0
                mask_decision = False
                yolo_decision = False
                mask_score = 0.0
                endpoint_review = False
                disagreement = False
                hybrid_review = True
                endpoint_record = None
                endpoint_latency = 0.0
                mask_latency = 0.0
                yolo_latency = 0.0

            defective = truth["status"] == "defective"
            decision_correct = mask_decision == defective
            decision_success = matched and selected_correctly and decision_correct
            localized_success = decision_success and (
                (not defective) or iou >= LOCALIZATION_IOU
            )
            instance_records.append(
                {
                    "image_id": truth["image_id"],
                    "source_relative_path": relative,
                    "source_instance_index": truth["source_instance_index"],
                    "truth": truth["status"],
                    "detected": matched,
                    "detection_iou": detection_iou,
                    "endpoint": endpoint_record,
                    "expected_tip_side": expected_side,
                    "endpoint_correct": selected_correctly,
                    "mask_rcnn": {
                        "defective": mask_decision,
                        "confidence": mask_score,
                        "decision_correct": decision_correct,
                        "mask_iou_full_tray": iou,
                        "mask_dice_full_tray": dice,
                    },
                    "yolo_verifier": {
                        "defective": yolo_decision,
                        "decision_agrees_with_mask_rcnn": not disagreement,
                    },
                    "hybrid_review_required": hybrid_review,
                    "end_to_end_decision_success": decision_success,
                    "localized_end_to_end_success": localized_success,
                    "latency_ms": {
                        "endpoint": endpoint_latency,
                        "mask_rcnn": mask_latency,
                        "yolo_verifier": yolo_latency,
                    },
                }
            )

        for prediction_index, output in enumerate(predicted_outputs):
            if prediction_index in prediction_to_match:
                continue
            mask_decision = bool(output["mask_prediction"]["defective"])
            yolo_decision = bool(output["yolo_prediction"]["defective"])
            disagreement = mask_decision != yolo_decision
            endpoint_review = bool(output["endpoint"]["review_required"])
            extra_prediction_records.append(
                {
                    "source_relative_path": relative,
                    "tray_score": output["score"],
                    "box": output["box"],
                    "endpoint": output["endpoint"],
                    "mask_rcnn_defective": mask_decision,
                    "mask_rcnn_confidence": float(
                        output["mask_prediction"]["confidence"]
                    ),
                    "yolo_verifier_defective": yolo_decision,
                    "model_disagreement": disagreement,
                    "hybrid_review_required": endpoint_review or disagreement,
                }
            )

        tray_elapsed = (time.perf_counter() - start) * 1000
        tray_latencies.append(tray_elapsed)
        overlay_name = Path(relative).stem.lower() + ".jpg"
        overlay.save(RUN_ROOT / "overlays" / overlay_name, quality=90)
        tray_records.append(
            {
                "source_relative_path": relative,
                "expected_hook_instances": len(truths),
                "predicted_hook_instances": len(predictions),
                "matched_hook_instances": len(matches),
                "tray_detection_latency_ms": tray_detection_ms,
                "total_pipeline_latency_ms": tray_elapsed,
                "overlay": (RUN_ROOT / "overlays" / overlay_name)
                .relative_to(REPO_ROOT)
                .as_posix(),
            }
        )
        print(
            json.dumps(
                {
                    "tray": tray_index,
                    "total": len(source_records),
                    "expected": len(truths),
                    "matched": len(matches),
                }
            ),
            flush=True,
        )

    labels = [item["truth"] == "defective" for item in instance_records]
    scores = [float(item["mask_rcnn"]["confidence"]) for item in instance_records]
    classification = classification_metrics(
        labels, scores, float(mask_threshold["score_threshold"])
    )
    intervals = bootstrap_intervals(
        labels,
        scores,
        float(mask_threshold["score_threshold"]),
        resamples=2000,
        confidence_level=0.95,
        seed=42,
    )
    detected_records = [item for item in instance_records if item["detected"]]
    conditional_labels = [item["truth"] == "defective" for item in detected_records]
    conditional_scores = [float(item["mask_rcnn"]["confidence"]) for item in detected_records]
    conditional = classification_metrics(
        conditional_labels,
        conditional_scores,
        float(mask_threshold["score_threshold"]),
    )
    positives = [item for item in instance_records if item["truth"] == "defective"]
    localized_positives = [
        item for item in positives if item["localized_end_to_end_success"]
    ]
    positive_ious = [float(item["mask_rcnn"]["mask_iou_full_tray"]) for item in positives]
    positive_dices = [float(item["mask_rcnn"]["mask_dice_full_tray"]) for item in positives]
    automatic = [item for item in instance_records if not item["hybrid_review_required"]]
    review = [item for item in instance_records if item["hybrid_review_required"]]
    endpoint_reviews = [
        item
        for item in detected_records
        if item["endpoint"] and item["endpoint"]["review_required"]
    ]
    disagreements = [
        item
        for item in detected_records
        if not item["yolo_verifier"]["decision_agrees_with_mask_rcnn"]
    ]
    extra_automatic = [
        item
        for item in extra_prediction_records
        if not item["hybrid_review_required"]
    ]
    extra_review = [
        item for item in extra_prediction_records if item["hybrid_review_required"]
    ]
    correct_defect_alarms = int(classification["confusion_matrix"]["tp"])
    expected_false_defect_alarms = int(classification["confusion_matrix"]["fp"])
    extra_false_defect_alarms = sum(
        item["mask_rcnn_defective"] for item in extra_prediction_records
    )
    all_defect_alarms = (
        correct_defect_alarms
        + expected_false_defect_alarms
        + extra_false_defect_alarms
    )
    result = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "status": "confirmatory_awaiting_human_review",
        "evaluation_design": {
            "cohort": "previously exposed redesigned-tray test captures",
            "test_status": "confirmatory_not_untouched_external_test",
            "test_tray_images": len(source_records),
            "expected_hook_instances": len(instance_records),
            "defective_instances": sum(labels),
            "healthy_instances": len(labels) - sum(labels),
            "test_informed_tuning": False,
        },
        "frozen_policy": {
            "tray_checkpoint": TRAY_CHECKPOINT.relative_to(REPO_ROOT).as_posix(),
            "tray_checkpoint_sha256": sha256(TRAY_CHECKPOINT),
            "tray_score_threshold": TRAY_THRESHOLD,
            "tool_match_iou": MATCH_IOU,
            "endpoint_checkpoint": endpoint_policy["checkpoint"],
            "endpoint_checkpoint_sha256": endpoint_policy["checkpoint_sha256"],
            "endpoint_review_margin": review_margin,
            "mask_checkpoint": MASK_CHECKPOINT.relative_to(REPO_ROOT).as_posix(),
            "mask_checkpoint_sha256": sha256(MASK_CHECKPOINT),
            "mask_score_threshold": float(mask_threshold["score_threshold"]),
            "minimum_mask_area": int(mask_threshold["minimum_mask_area"]),
            "localization_success_iou": LOCALIZATION_IOU,
            "hybrid_review_rule": "review tool misses, low endpoint margins, or Mask R-CNN/YOLO decision disagreement",
        },
        "tool_detection": {
            "predictions": total_predictions,
            "matched": total_matches,
            "false_positives": total_predictions - total_matches,
            "missed": len(instance_records) - total_matches,
            "precision": total_matches / total_predictions if total_predictions else 0.0,
            "recall": total_matches / len(instance_records),
            "mean_matched_iou": float(
                np.mean([item["detection_iou"] for item in instance_records if item["detected"]])
            )
            if total_matches
            else 0.0,
            "unmatched_prediction_downstream": {
                "mask_rcnn_defect_alarms": sum(
                    item["mask_rcnn_defective"] for item in extra_prediction_records
                ),
                "automatic_outputs": len(extra_automatic),
                "automatic_defect_alarms": sum(
                    item["mask_rcnn_defective"] for item in extra_automatic
                ),
                "review_outputs": len(extra_review),
            },
        },
        "endpoint_selection": {
            "evaluated": endpoint_evaluated,
            "correct": endpoint_correct,
            "accuracy": endpoint_correct / endpoint_evaluated if endpoint_evaluated else 0.0,
            "low_margin_review_count": len(endpoint_reviews),
        },
        "mask_rcnn_classification_all_expected_instances": classification,
        "mask_rcnn_bootstrap_95_ci": intervals,
        "mask_rcnn_classification_detected_instances": conditional,
        "end_to_end": {
            "decision_successes": sum(
                item["end_to_end_decision_success"] for item in instance_records
            ),
            "decision_success_rate": float(
                np.mean([item["end_to_end_decision_success"] for item in instance_records])
            ),
            "localized_successes": sum(
                item["localized_end_to_end_success"] for item in instance_records
            ),
            "localized_success_rate": float(
                np.mean([item["localized_end_to_end_success"] for item in instance_records])
            ),
            "defective_localized_successes": len(localized_positives),
            "defective_localized_success_rate": len(localized_positives) / len(positives),
            "defective_mean_full_tray_iou": float(np.mean(positive_ious)),
            "defective_mean_full_tray_dice": float(np.mean(positive_dices)),
            "defect_alarm_accounting": {
                "correct_defect_alarms": correct_defect_alarms,
                "false_alarms_on_healthy_tools": expected_false_defect_alarms,
                "false_alarms_from_unmatched_tool_detections": extra_false_defect_alarms,
                "alarm_precision_including_unmatched_detections": (
                    correct_defect_alarms / all_defect_alarms
                    if all_defect_alarms
                    else 0.0
                ),
                "false_defect_alarms_per_tray": (
                    (expected_false_defect_alarms + extra_false_defect_alarms)
                    / len(source_records)
                ),
            },
        },
        "hybrid_review_policy": {
            "automatic_instances": len(automatic),
            "automatic_coverage": len(automatic) / len(instance_records),
            "automatic_correct": sum(
                item["mask_rcnn"]["decision_correct"] for item in automatic
            ),
            "automatic_accuracy": (
                float(np.mean([item["mask_rcnn"]["decision_correct"] for item in automatic]))
                if automatic
                else 0.0
            ),
            "review_instances": len(review),
            "review_rate": len(review) / len(instance_records),
            "model_disagreements": len(disagreements),
            "low_endpoint_margins": len(endpoint_reviews),
            "tool_misses": len(instance_records) - total_matches,
            "review_outcomes_assumed": False,
            "additional_false_tool_review_events": len(extra_review),
            "additional_false_tool_automatic_outputs": len(extra_automatic),
            "automatic_output_validity_including_false_tools": (
                sum(item["mask_rcnn"]["decision_correct"] for item in automatic)
                / (len(automatic) + len(extra_automatic))
                if automatic or extra_automatic
                else 0.0
            ),
            "total_review_events": len(review) + len(extra_review),
            "review_events_per_tray": (len(review) + len(extra_review))
            / len(source_records),
        },
        "latency": {
            "median_tray_to_outputs_ms": float(np.median(tray_latencies)),
            "p95_tray_to_outputs_ms": float(np.quantile(tray_latencies, 0.95)),
            "note": "includes all predicted Hook crops and both Mask R-CNN and YOLO verifier",
        },
        "instance_records": (RUN_ROOT / "instance_records.jsonl")
        .relative_to(REPO_ROOT)
        .as_posix(),
        "tray_records": (RUN_ROOT / "tray_records.jsonl")
        .relative_to(REPO_ROOT)
        .as_posix(),
        "overlay_directory": (RUN_ROOT / "overlays").relative_to(REPO_ROOT).as_posix(),
        "extra_prediction_records": (RUN_ROOT / "extra_prediction_records.jsonl")
        .relative_to(REPO_ROOT)
        .as_posix(),
    }
    write_jsonl(RUN_ROOT / "instance_records.jsonl", instance_records)
    write_jsonl(RUN_ROOT / "tray_records.jsonl", tray_records)
    write_jsonl(
        RUN_ROOT / "extra_prediction_records.jsonl", extra_prediction_records
    )
    RESULT_PATH.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
