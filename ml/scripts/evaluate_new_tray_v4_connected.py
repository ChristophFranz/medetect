"""Evaluate the connected new-tray pipeline with each fine-tuned defect model.

Pipeline: tray YOLO -> endpoint selector/crop -> one of four defect models.
The tool detector and cropper are held constant so downstream comparisons are
paired on the same 16 tray captures and 24 expected Hook Sinskey instances.
"""

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

from ml.benchmark.metrics import bootstrap_intervals, classification_metrics, decode_mask
from ml.models.endpoint_selector import EndpointSelector
from ml.scripts.evaluate_new_tray_v4 import MODELS, build_loaded_adapter, sha256

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_MANIFEST = REPO_ROOT / "ml/annotation/new_tray_manifest.json"
CROP_MANIFEST = REPO_ROOT / "ml/annotation/new_tray_model_cropped_manifest.json"
REVIEWED_BOXES = REPO_ROOT / "ml/annotation/local/new_tray_detection_reviewed/annotations/instances_default.json"
REVIEWED_DEFECTS = REPO_ROOT / "ml/data/local/hook_sinskey/new_tray_reviewed_v4_augmented_50_50/annotations/instances_test.json"
ENDPOINT_CONFIG = REPO_ROOT / "ml/configs/endpoint_selector.yaml"
ENDPOINT_POLICY = REPO_ROOT / "ml/experiments/endpoint_selector_v1_policy.json"
DEFECT_THRESHOLDS = REPO_ROOT / "ml/experiments/new_tray_v4_thresholds.json"
TRAY_CHECKPOINT = REPO_ROOT / "ml/runs/new_tray_v4/tray_yolo/fine_tuned/weights/best.pt"
RUN_ROOT = REPO_ROOT / "ml/runs/new_tray_v4/connected_pipeline"
RESULT_PATH = REPO_ROOT / "ml/experiments/new_tray_v4_connected_results.json"
MATCH_IOU = 0.50
LOCALIZATION_IOU = 0.50
MODEL_NAMES = tuple(MODELS)


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, separators=(",", ":")) + "\n" for record in records))


def box_iou(first: list[float], second: list[float]) -> float:
    ax1, ay1, ax2, ay2 = first
    bx1, by1, bx2, by2 = second
    intersection = max(0.0, min(ax2, bx2) - max(ax1, bx1)) * max(0.0, min(ay2, by2) - max(ay1, by1))
    first_area = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    second_area = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = first_area + second_area - intersection
    return intersection / union if union else 0.0


def greedy_matches(predictions: list[list[float]], truths: list[list[float]], minimum_iou: float) -> list[tuple[int, int, float]]:
    candidates = sorted(
        ((box_iou(prediction, truth), pi, ti) for pi, prediction in enumerate(predictions) for ti, truth in enumerate(truths)),
        reverse=True,
    )
    matches: list[tuple[int, int, float]] = []
    used_predictions: set[int] = set()
    used_truths: set[int] = set()
    for iou, pi, ti in candidates:
        if iou < minimum_iou:
            break
        if pi in used_predictions or ti in used_truths:
            continue
        matches.append((pi, ti, iou))
        used_predictions.add(pi)
        used_truths.add(ti)
    return matches


def decode_coco_mask(segmentation: dict[str, Any]) -> np.ndarray:
    if isinstance(segmentation["counts"], list):
        encoded = mask_utils.frPyObjects(segmentation, int(segmentation["size"][0]), int(segmentation["size"][1]))
    else:
        encoded = {"size": segmentation["size"], "counts": str(segmentation["counts"]).encode("ascii")}
    return mask_utils.decode(encoded).astype(bool)


def project_crop_mask(mask: np.ndarray, crop_box: list[int], full_shape: tuple[int, int], mirrored: bool) -> np.ndarray:
    if mirrored:
        mask = np.fliplr(mask)
    left, top, right, bottom = crop_box
    width, height = right - left, bottom - top
    if mask.shape != (height, width):
        mask = np.asarray(Image.fromarray(mask.astype(np.uint8)).resize((width, height), Image.Resampling.NEAREST)).astype(bool)
    projected = np.zeros(full_shape, dtype=bool)
    projected[top:bottom, left:right] = mask
    return projected


def project_crop_box(box: list[float], crop_box: list[int], mirrored: bool) -> list[float]:
    left, top, right, _ = crop_box
    x1, y1, x2, y2 = box
    if mirrored:
        width = right - left
        x1, x2 = width - x2, width - x1
    return [left + x1, top + y1, left + x2, top + y2]


def mask_box(mask: np.ndarray) -> list[float]:
    ys, xs = np.where(mask)
    if not len(xs):
        return [0.0, 0.0, 0.0, 0.0]
    return [float(xs.min()), float(ys.min()), float(xs.max() + 1), float(ys.max() + 1)]


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
    pixels = np.asarray(image).copy().astype(np.float32)
    pixels[mask] = 0.58 * pixels[mask] + 0.42 * np.asarray(color, dtype=np.float32)
    image.paste(Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8)))


def load_ground_truth() -> tuple[dict[str, list[dict]], dict[str, dict]]:
    source_manifest = json.loads(SOURCE_MANIFEST.read_text())
    crop_manifest = json.loads(CROP_MANIFEST.read_text())
    boxes = json.loads(REVIEWED_BOXES.read_text())
    defects = json.loads(REVIEWED_DEFECTS.read_text())
    status_by_key = {
        (item["source_relative_path"], int(item["source_instance_index"])): item
        for item in source_manifest["images"]
    }
    crop_by_id = {item["image_id"]: item for item in crop_manifest["images"]}
    images_by_number = {int(item["id"]): item for item in boxes["images"]}
    truth_by_source: dict[str, list[dict]] = defaultdict(list)
    for annotation in boxes["annotations"]:
        image = images_by_number[int(annotation["image_id"])]
        if image["split"] != "test":
            continue
        relative = image["source_relative_path"]
        instance_index = int(annotation["source_instance_index"])
        source = status_by_key[(relative, instance_index)]
        x, y, width, height = map(float, annotation["bbox"])
        truth_by_source[relative].append({
            "image_id": source["image_id"],
            "source_instance_index": instance_index,
            "status": source["status"],
            "box": [x, y, x + width, y + height],
        })
    for records in truth_by_source.values():
        records.sort(key=lambda item: item["source_instance_index"])

    annotations_by_image: dict[int, list[dict]] = defaultdict(list)
    for annotation in defects["annotations"]:
        annotations_by_image[int(annotation["image_id"])].append(annotation)
    defect_by_id: dict[str, dict] = {}
    for image in defects["images"]:
        image_id = str(image["medetect_image_id"]).removeprefix("new__")
        union = np.zeros((int(image["height"]), int(image["width"])), dtype=bool)
        for annotation in annotations_by_image[int(image["id"])]:
            union |= decode_coco_mask(annotation["segmentation"])
        defect_by_id[image_id] = {
            "mask": union,
            "box": mask_box(union),
            "crop": crop_by_id[image_id],
        }
    return dict(truth_by_source), defect_by_id


def raw_tray_predictions(model: YOLO, image: Image.Image, device: str) -> list[dict]:
    result = model.predict(image, imgsz=640, conf=0.001, device=device, verbose=False)[0]
    if result.boxes is None:
        return []
    return [
        {"box": list(map(float, box)), "score": float(score)}
        for box, score, class_id in zip(result.boxes.xyxy.cpu().tolist(), result.boxes.conf.cpu().tolist(), result.boxes.cls.cpu().tolist(), strict=True)
        if int(class_id) == 0
    ]


def select_tray_threshold(model: YOLO, raw_root: Path, device: str) -> tuple[float, dict]:
    reviewed = json.loads(REVIEWED_BOXES.read_text())
    images = [item for item in reviewed["images"] if item["split"] == "valid"]
    image_by_id = {int(item["id"]): item for item in images}
    truths: dict[int, list[list[float]]] = defaultdict(list)
    for annotation in reviewed["annotations"]:
        image_id = int(annotation["image_id"])
        if image_id not in image_by_id:
            continue
        x, y, width, height = map(float, annotation["bbox"])
        truths[image_id].append([x, y, x + width, y + height])
    predictions: dict[int, list[dict]] = {}
    for index, image_record in enumerate(images, start=1):
        with Image.open(raw_root / image_record["source_relative_path"]) as handle:
            image = ImageOps.exif_transpose(handle).convert("RGB")
        predictions[int(image_record["id"])] = raw_tray_predictions(model, image, device)
        print(json.dumps({"tray_threshold_validation": index, "total": len(images)}), flush=True)
    candidates = []
    for threshold in np.arange(0.05, 0.951, 0.05):
        tp = fp = fn = 0
        for image_id, expected in truths.items():
            selected = [item["box"] for item in predictions[image_id] if item["score"] >= threshold]
            matches = greedy_matches(selected, expected, MATCH_IOU)
            tp += len(matches)
            fp += len(selected) - len(matches)
            fn += len(expected) - len(matches)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        candidates.append({"threshold": float(round(threshold, 2)), "tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1})
    best = max(candidates, key=lambda item: (item["f1"], item["recall"], item["threshold"]))
    return float(best["threshold"]), best


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", choices=("cpu", "mps"), default="cpu")
    args = parser.parse_args()
    if not DEFECT_THRESHOLDS.is_file():
        raise FileNotFoundError("run evaluate_new_tray_v4.py first to freeze defect thresholds")
    if RUN_ROOT.exists():
        shutil.rmtree(RUN_ROOT)
    for model_name in MODEL_NAMES:
        (RUN_ROOT / model_name / "overlays").mkdir(parents=True)
        (RUN_ROOT / model_name / "masks").mkdir(parents=True)

    source_manifest = json.loads(SOURCE_MANIFEST.read_text())
    endpoint_policy = json.loads(ENDPOINT_POLICY.read_text())
    endpoint_config = yaml.safe_load(ENDPOINT_CONFIG.read_text())
    thresholds = json.loads(DEFECT_THRESHOLDS.read_text())
    threshold_by_model = {item["model"]: item for item in thresholds["operating_points"]}
    endpoint = EndpointSelector.from_checkpoint(
        REPO_ROOT / endpoint_policy["checkpoint"],
        int(endpoint_config["image_size"]),
        torch.device(args.device),
    )
    adapters = {}
    for model_name, checkpoint in MODELS.items():
        adapter = build_loaded_adapter(model_name, checkpoint, args.device)
        point = threshold_by_model[model_name]
        if model_name == "yolo_detection":
            adapter.confidence_threshold = float(point["score_threshold"])
        else:
            adapter.score_threshold = float(point["score_threshold"])
        if hasattr(adapter, "minimum_mask_area"):
            adapter.minimum_mask_area = int(point["minimum_mask_area"])
        adapters[model_name] = adapter

    truth_by_source, defect_truth = load_ground_truth()
    raw_root = REPO_ROOT / source_manifest["local_root"] / "raw"
    source_records = {item["source_relative_path"]: item for item in source_manifest["sources"] if item["split"] == "test"}
    tray_model = YOLO(TRAY_CHECKPOINT)
    tray_threshold, tray_validation = select_tray_threshold(tray_model, raw_root, args.device)
    tray_test_metrics = tray_model.val(
        data=str(REPO_ROOT / "ml/data/local/tray_detection/new_tray_reviewed_v2/data.yaml"),
        split="test",
        imgsz=640,
        conf=0.001,
        device=args.device,
        plots=False,
        save_json=False,
        project=str(RUN_ROOT),
        name="tray_yolo_test_metrics",
        verbose=False,
    )
    review_margin = float(endpoint_policy["review_policy"]["score_margin_threshold"])

    instance_records: dict[str, list[dict]] = {name: [] for name in MODEL_NAMES}
    extra_records: dict[str, list[dict]] = {name: [] for name in MODEL_NAMES}
    tray_records: list[dict] = []
    total_predictions = total_matches = endpoint_correct = endpoint_evaluated = 0
    tray_latencies: dict[str, list[float]] = {name: [] for name in MODEL_NAMES}
    matched_ious: list[float] = []
    for tray_index, relative in enumerate(sorted(source_records), start=1):
        with Image.open(raw_root / relative) as handle:
            image = ImageOps.exif_transpose(handle).convert("RGB")
        tray_start = time.perf_counter()
        raw_predictions = raw_tray_predictions(tray_model, image, args.device)
        detection_ms = (time.perf_counter() - tray_start) * 1000
        predictions = [item for item in raw_predictions if item["score"] >= tray_threshold]
        outputs = []
        for prediction_index, prediction in enumerate(predictions):
            endpoint_start = time.perf_counter()
            crop, selection = endpoint.select_from_box(image, prediction["box"], review_margin_threshold=review_margin)
            endpoint_ms = (time.perf_counter() - endpoint_start) * 1000
            model_outputs = {
                name: adapter.predict(f"tray_{tray_index:02d}_prediction_{prediction_index + 1}", crop).to_dict()
                for name, adapter in adapters.items()
            }
            outputs.append({**prediction, "endpoint": selection, "endpoint_latency_ms": endpoint_ms, "models": model_outputs})

        truths = truth_by_source[relative]
        matches = greedy_matches([item["box"] for item in predictions], [item["box"] for item in truths], MATCH_IOU)
        prediction_to_match = {pi: (ti, iou) for pi, ti, iou in matches}
        truth_to_match = {ti: (pi, iou) for pi, ti, iou in matches}
        total_predictions += len(predictions)
        total_matches += len(matches)
        matched_ious.extend(iou for _, _, iou in matches)

        overlays = {name: image.copy() for name in MODEL_NAMES}
        draws = {name: ImageDraw.Draw(overlay) for name, overlay in overlays.items()}
        predicted_mask_unions = {
            name: np.zeros((image.height, image.width), dtype=bool)
            for name in ("detr_segmentation", "mask_rcnn")
        }
        for name in MODEL_NAMES:
            for truth in truths:
                draws[name].rectangle(truth["box"], outline=(40, 130, 255), width=10)
            for pi, output in enumerate(outputs):
                color = (0, 210, 80) if pi in prediction_to_match else (255, 170, 0)
                draws[name].rectangle(output["box"], outline=color, width=10)

        for truth_index, truth in enumerate(truths):
            matched = truth_index in truth_to_match
            expected_side = defect_truth[truth["image_id"]]["crop"]["source_tip_side"]
            if matched:
                prediction_index, detection_iou = truth_to_match[truth_index]
                output = outputs[prediction_index]
                selected_correctly = output["endpoint"]["selected_side"] == expected_side
                endpoint_correct += int(selected_correctly)
                endpoint_evaluated += 1
            else:
                detection_iou = 0.0
                output = None
                selected_correctly = False
            defective = truth["status"] == "defective"
            truth_crop = defect_truth[truth["image_id"]]
            truth_full_mask = project_crop_mask(
                truth_crop["mask"],
                [int(value) for value in truth_crop["crop"]["source_crop_xyxy"]],
                (image.height, image.width),
                bool(truth_crop["crop"]["canonicalized_by_horizontal_flip"]),
            )
            truth_full_box = mask_box(truth_full_mask)
            for model_name in MODEL_NAMES:
                if output is None:
                    record = {"defective": False, "confidence": 0.0, "boxes": [], "masks": [], "latency_ms": 0.0}
                    endpoint_latency = 0.0
                    endpoint_review = True
                    predicted_mask = None
                    localization_iou = localization_dice = 0.0
                else:
                    record = output["models"][model_name]
                    endpoint_latency = float(output["endpoint_latency_ms"])
                    endpoint_review = bool(output["endpoint"]["review_required"])
                    crop_box = [int(value) for value in output["endpoint"]["source_crop_xyxy"]]
                    mirrored = bool(output["endpoint"]["canonicalized_by_horizontal_flip"])
                    if record["masks"]:
                        crop_masks = [decode_mask(encoded) for encoded in record["masks"]]
                        union = np.any(crop_masks, axis=0)
                        predicted_mask = project_crop_mask(union, crop_box, (image.height, image.width), mirrored)
                        localization_iou = mask_iou(predicted_mask, truth_full_mask) if defective else 0.0
                        localization_dice = mask_dice(predicted_mask, truth_full_mask) if defective else 0.0
                        if predicted_mask.any():
                            tint(overlays[model_name], predicted_mask, (245, 30, 80))
                            predicted_mask_unions[model_name] |= predicted_mask
                    else:
                        predicted_mask = None
                        full_boxes = [project_crop_box(box, crop_box, mirrored) for box in record["boxes"]]
                        localization_iou = max((box_iou(box, truth_full_box) for box in full_boxes), default=0.0) if defective else 0.0
                        localization_dice = 0.0
                        for box in full_boxes:
                            draws[model_name].rectangle(box, outline=(245, 30, 80), width=8)
                decision = bool(record["defective"])
                decision_correct = decision == defective
                decision_success = matched and selected_correctly and decision_correct
                localized_success = decision_success and (not defective or localization_iou >= LOCALIZATION_IOU)
                instance_records[model_name].append({
                    "image_id": truth["image_id"],
                    "source_relative_path": relative,
                    "truth": truth["status"],
                    "detected": matched,
                    "tool_detection_iou": detection_iou,
                    "endpoint_correct": selected_correctly,
                    "endpoint_review_required": endpoint_review,
                    "defective": decision,
                    "confidence": float(record["confidence"]),
                    "decision_correct": decision_correct,
                    "localization_type": "mask" if model_name in {"detr_segmentation", "mask_rcnn"} else "box",
                    "localization_iou_full_tray": localization_iou,
                    "mask_dice_full_tray": localization_dice,
                    "end_to_end_decision_success": decision_success,
                    "localized_end_to_end_success": localized_success,
                    "latency_ms": endpoint_latency + float(record["latency_ms"]),
                })

        for prediction_index, output in enumerate(outputs):
            if prediction_index in prediction_to_match:
                continue
            for model_name in MODEL_NAMES:
                record = output["models"][model_name]
                extra_records[model_name].append({
                    "source_relative_path": relative,
                    "tray_score": output["score"],
                    "defective": bool(record["defective"]),
                    "confidence": float(record["confidence"]),
                    "endpoint_review_required": bool(output["endpoint"]["review_required"]),
                })

        for model_name, overlay in overlays.items():
            filename = Path(relative).stem.lower() + ".jpg"
            overlay.save(RUN_ROOT / model_name / "overlays" / filename, quality=90)
            if model_name in predicted_mask_unions:
                Image.fromarray(
                    predicted_mask_unions[model_name].astype(np.uint8) * 255
                ).save(RUN_ROOT / model_name / "masks" / f"{Path(relative).stem.lower()}.png")
            model_pipeline_ms = detection_ms + sum(float(output["endpoint_latency_ms"]) + float(output["models"][model_name]["latency_ms"]) for output in outputs)
            tray_latencies[model_name].append(model_pipeline_ms)
        tray_records.append({
            "source_relative_path": relative,
            "expected_hook_instances": len(truths),
            "predicted_hook_instances": len(predictions),
            "matched_hook_instances": len(matches),
            "tray_detection_latency_ms": detection_ms,
        })
        print(json.dumps({"connected_tray": tray_index, "total": len(source_records), "expected": len(truths), "matched": len(matches)}), flush=True)

    model_results = []
    for model_name in MODEL_NAMES:
        records = instance_records[model_name]
        labels = [item["truth"] == "defective" for item in records]
        scores = [float(item["confidence"]) for item in records]
        threshold = float(threshold_by_model[model_name]["score_threshold"])
        classification = classification_metrics(labels, scores, threshold)
        intervals = bootstrap_intervals(labels, scores, threshold, resamples=2000, confidence_level=0.95, seed=42)
        positives = [item for item in records if item["truth"] == "defective"]
        extras = extra_records[model_name]
        false_extra_alarms = sum(item["defective"] for item in extras)
        tp = int(classification["confusion_matrix"]["tp"])
        fp = int(classification["confusion_matrix"]["fp"])
        all_alarms = tp + fp + false_extra_alarms
        output_path = RUN_ROOT / model_name / "instance_records.jsonl"
        write_jsonl(output_path, records)
        write_jsonl(RUN_ROOT / model_name / "extra_predictions.jsonl", extras)
        model_results.append({
            "model": model_name,
            "classification_all_expected_instances": classification,
            "bootstrap_95_ci": intervals,
            "end_to_end": {
                "decision_successes": sum(item["end_to_end_decision_success"] for item in records),
                "decision_success_rate": float(np.mean([item["end_to_end_decision_success"] for item in records])),
                "localized_successes": sum(item["localized_end_to_end_success"] for item in records),
                "localized_success_rate": float(np.mean([item["localized_end_to_end_success"] for item in records])),
                "defective_localized_successes": sum(item["localized_end_to_end_success"] for item in positives),
                "defective_localized_success_rate": float(np.mean([item["localized_end_to_end_success"] for item in positives])),
                "defective_mean_localization_iou": float(np.mean([item["localization_iou_full_tray"] for item in positives])),
                "defective_mean_mask_dice": float(np.mean([item["mask_dice_full_tray"] for item in positives])) if model_name in {"detr_segmentation", "mask_rcnn"} else None,
                "localization_type": "mask" if model_name in {"detr_segmentation", "mask_rcnn"} else "box",
            },
            "alarm_accounting": {
                "false_alarms_on_expected_healthy_tools": fp,
                "false_alarms_from_unmatched_tool_detections": false_extra_alarms,
                "alarm_precision_including_unmatched_detections": tp / all_alarms if all_alarms else 0.0,
            },
            "review_rate": float(np.mean([item["endpoint_review_required"] for item in records])),
            "latency": {
                "median_tray_to_outputs_ms": float(np.median(tray_latencies[model_name])),
                "p95_tray_to_outputs_ms": float(np.quantile(tray_latencies[model_name], 0.95)),
            },
            "instance_records": output_path.relative_to(REPO_ROOT).as_posix(),
            "overlay_directory": (RUN_ROOT / model_name / "overlays").relative_to(REPO_ROOT).as_posix(),
        })

    write_jsonl(RUN_ROOT / "tray_records.jsonl", tray_records)
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "status": "confirmatory_awaiting_human_review",
        "evaluation_level": "connected_tray_yolo_to_endpoint_crop_to_defect_model",
        "cohort_note": "Previously exposed 16 redesigned-tray captures containing 24 expected tools; not an untouched external test.",
        "evaluation_design": {
            "test_tray_images": len(source_records),
            "expected_hook_instances": sum(len(items) for items in truth_by_source.values()),
            "defective_instances": sum(item["truth"] == "defective" for item in next(iter(instance_records.values()))),
            "healthy_instances": sum(item["truth"] == "healthy" for item in next(iter(instance_records.values()))),
            "paired_downstream_comparison": True,
        },
        "frozen_policy": {
            "tray_checkpoint": TRAY_CHECKPOINT.relative_to(REPO_ROOT).as_posix(),
            "tray_checkpoint_sha256": sha256(TRAY_CHECKPOINT),
            "tray_score_threshold": tray_threshold,
            "tray_threshold_validation_metrics": tray_validation,
            "tool_match_iou": MATCH_IOU,
            "endpoint_checkpoint": endpoint_policy["checkpoint"],
            "endpoint_review_margin": review_margin,
            "defect_thresholds": DEFECT_THRESHOLDS.relative_to(REPO_ROOT).as_posix(),
            "localization_success_iou": LOCALIZATION_IOU,
        },
        "tool_detection_common_to_all_models": {
            "predictions": total_predictions,
            "matched": total_matches,
            "false_positives": total_predictions - total_matches,
            "missed": sum(len(items) for items in truth_by_source.values()) - total_matches,
            "precision": total_matches / total_predictions if total_predictions else 0.0,
            "recall": total_matches / sum(len(items) for items in truth_by_source.values()),
            "mean_matched_iou": float(np.mean(matched_ious)) if matched_ious else 0.0,
            "ap50": float(tray_test_metrics.box.map50),
            "map50_95": float(tray_test_metrics.box.map),
        },
        "endpoint_selection_common_to_all_models": {
            "evaluated": endpoint_evaluated,
            "correct": endpoint_correct,
            "accuracy": endpoint_correct / endpoint_evaluated if endpoint_evaluated else 0.0,
        },
        "models": model_results,
        "tray_records": (RUN_ROOT / "tray_records.jsonl").relative_to(REPO_ROOT).as_posix(),
    }
    RESULT_PATH.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
