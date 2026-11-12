"""Measure and plot the provisional tray-to-defect cascade on linked new-tray data."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from pycocotools import mask as mask_utils

REPO_ROOT = Path(__file__).resolve().parents[2]
COCO_PATH = REPO_ROOT / "ml/data/local/hook_sinskey/combined_provisional_v2/annotations/instances_test.json"
TRAY_PREDICTIONS = REPO_ROOT / "ml/runs/tray_yolo/presentation_predictions/predictions.jsonl"
RUN_ROOT = REPO_ROOT / "ml/runs/combined_provisional"
RESULT_PATH = REPO_ROOT / "ml/experiments/end_to_end_provisional_results.json"
OUTPUT = REPO_ROOT / "ml/presentation/figures/end_to_end_provisional"
MODELS = (
    ("legacy_yolo", "Inherited YOLO", "box"),
    ("detr_detection", "DETR detection", "box"),
    ("mask_rcnn", "Mask R-CNN", "mask"),
)
COLORS = ("#657786", "#E67E22", "#1976D2")
NOTE = "Provisional linked new-tray test cohort; generated boxes and masks have not been human-reviewed"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def decode_rle(encoded: dict) -> np.ndarray:
    return mask_utils.decode(
        {"size": encoded["size"], "counts": str(encoded["counts"]).encode("ascii")}
    ).astype(bool)


def box_iou(first: list[float], second: list[float]) -> float:
    ax1, ay1, ax2, ay2 = first
    bx1, by1, bx2, by2 = second
    intersection = max(0.0, min(ax2, bx2) - max(ax1, bx1)) * max(
        0.0, min(ay2, by2) - max(ay1, by1)
    )
    union = (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - intersection
    return intersection / union if union > 0 else 0.0


def mask_iou(first: np.ndarray, second: np.ndarray) -> float:
    intersection = np.logical_and(first, second).sum()
    union = np.logical_or(first, second).sum()
    return float(intersection / union) if union else 0.0


def save(fig: plt.Figure, name: str, *, svg: bool = True) -> None:
    fig.text(0.5, 0.01, NOTE, ha="center", fontsize=8.5, color="#444444")
    fig.tight_layout(rect=(0, 0.055, 1, 0.94))
    fig.savefig(OUTPUT / f"{name}.png", dpi=180, bbox_inches="tight")
    if svg:
        fig.savefig(OUTPUT / f"{name}.svg", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    coco = json.loads(COCO_PATH.read_text())
    new_images = {
        item["medetect_image_id"]: item
        for item in coco["images"]
        if item.get("source_domain") == "provisional_new_tray"
    }
    image_number_to_id = {item["id"]: item["medetect_image_id"] for item in coco["images"]}
    annotations: dict[str, list[dict]] = defaultdict(list)
    for annotation in coco["annotations"]:
        image_id = image_number_to_id[annotation["image_id"]]
        if image_id in new_images:
            annotations[image_id].append(annotation)

    identified: set[str] = set()
    cropped: set[str] = set()
    for record in read_jsonl(TRAY_PREDICTIONS):
        if record["split"] != "test":
            continue
        match = re.search(r"(IMG_\d+)", record["source_relative_path"], flags=re.IGNORECASE)
        if not match:
            continue
        source_stem = match.group(1).lower()
        for instance in record["matched_instances"]:
            linked_id = f"new__newtray_{source_stem}_tool{instance['source_instance_index']}"
            identified.add(linked_id)
            crop_path = REPO_ROOT / instance["crop"]
            if crop_path.is_file():
                cropped.add(linked_id)

    cohort_ids = sorted(new_images)
    model_results = []
    for model_name, label, localization_type in MODELS:
        predictions = {
            item["image_id"]: item
            for item in read_jsonl(RUN_ROOT / model_name / "test_predictions.jsonl")
            if item["image_id"] in new_images
        }
        correct_decisions = 0
        localized_successes = 0
        per_image = []
        for image_id in cohort_ids:
            truth_defective = new_images[image_id]["status"] == "defective"
            prediction = predictions[image_id]
            decision_correct = bool(prediction["defective"]) == truth_defective
            correct_decisions += int(decision_correct)
            best_iou = 0.0
            if not truth_defective:
                localized_success = decision_correct
            elif localization_type == "box":
                truth_boxes = []
                for annotation in annotations[image_id]:
                    x, y, width, height = annotation["bbox"]
                    truth_boxes.append([x, y, x + width, y + height])
                best_iou = max(
                    (box_iou(predicted, truth) for predicted in prediction["boxes"] for truth in truth_boxes),
                    default=0.0,
                )
                localized_success = decision_correct and best_iou >= 0.5
            else:
                truth_masks = [decode_rle(annotation["segmentation"]) for annotation in annotations[image_id]]
                predicted_masks = [decode_rle(encoded) for encoded in prediction["masks"]]
                best_iou = max(
                    (mask_iou(predicted, truth) for predicted in predicted_masks for truth in truth_masks),
                    default=0.0,
                )
                localized_success = decision_correct and best_iou >= 0.5
            localized_successes += int(localized_success)
            per_image.append(
                {
                    "image_id": image_id,
                    "truth": "defective" if truth_defective else "healthy",
                    "decision_correct": decision_correct,
                    "best_localization_iou": best_iou,
                    "localized_success": localized_success,
                }
            )
        model_results.append(
            {
                "model": model_name,
                "label": label,
                "localization_type": localization_type,
                "correct_defect_decisions": correct_decisions,
                "defect_decision_accuracy": correct_decisions / len(cohort_ids),
                "localized_end_to_end_successes": localized_successes,
                "localized_end_to_end_rate": localized_successes / len(cohort_ids),
                "per_image": per_image,
            }
        )

    identified_count = len(set(cohort_ids) & identified)
    cropped_count = len(set(cohort_ids) & cropped)
    result = {
        "schema_version": 1,
        "status": "provisional_unreviewed_linked_new_tray_test",
        "cohort": {
            "eligible_instances": len(cohort_ids),
            "defective": sum(item["status"] == "defective" for item in new_images.values()),
            "healthy": sum(item["status"] == "healthy" for item in new_images.values()),
            "quarantined_before_evaluation": 2,
        },
        "tool_identification": {
            "identified": identified_count,
            "rate": identified_count / len(cohort_ids),
        },
        "crop_generation": {
            "generated": cropped_count,
            "rate": cropped_count / len(cohort_ids),
        },
        "models": model_results,
        "definition": (
            "Localized end-to-end success requires a matched tray detection and exported crop; "
            "healthy cases require a correct no-defect decision; defective cases require a correct "
            "defect decision and at least one predicted box/mask with IoU >= 0.50."
        ),
        "limitations": [
            "New-tray detector boxes and SAM2 reference masks are unreviewed.",
            "Two defective test instances were quarantined before this 22-instance cohort was formed.",
            "YOLO and DETR localization is box-based; only Mask R-CNN localization is mask-based.",
        ],
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2) + "\n")

    plt.style.use("seaborn-v0_8-whitegrid")
    stages = ("Tool identified", "Crop generated", "Defect decision correct", "Localized output correct")
    x = np.arange(len(stages))
    width = 0.25
    fig, axis = plt.subplots(figsize=(12, 5.5))
    for index, (model, color) in enumerate(zip(model_results, COLORS, strict=True)):
        values = [
            identified_count / len(cohort_ids),
            cropped_count / len(cohort_ids),
            model["defect_decision_accuracy"],
            model["localized_end_to_end_rate"],
        ]
        bars = axis.bar(x + (index - 1) * width, values, width, color=color, label=model["label"])
        axis.bar_label(bars, labels=[f"{value:.1%}" for value in values], padding=3, fontsize=8)
    axis.set_xticks(x, ("Tool\nidentified", "Crop\ngenerated", "Defect decision\ncorrect", "Localized output\ncorrect"))
    axis.set_ylim(0, 1.16)
    axis.set_ylabel("Share of linked test instances")
    axis.set_title("End-to-end Hook Sinskey pipeline performance")
    axis.legend(loc="upper right", ncols=3)
    save(fig, "stage_performance")

    # Senior-report-style comparison between prerequisite presence detection and inspection.
    fig, axis = plt.subplots(figsize=(10.5, 5.4))
    categories = ("Tool identification", "Defect identification", "Localization-aware end-to-end")
    for index, (model, color) in enumerate(zip(model_results, COLORS, strict=True)):
        values = [
            identified_count / len(cohort_ids),
            model["defect_decision_accuracy"],
            model["localized_end_to_end_rate"],
        ]
        bars = axis.bar(np.arange(3) + (index - 1) * width, values, width, color=color, label=model["label"])
        axis.bar_label(bars, labels=[f"{value:.1%}" for value in values], padding=3, fontsize=8)
    axis.set_xticks(np.arange(3), categories)
    axis.set_ylim(0, 1.16)
    axis.set_ylabel("Success rate")
    axis.set_title("Presence detection versus downstream defect performance")
    axis.legend(loc="upper right", ncols=3)
    save(fig, "presence_vs_defect")

    mask_result = next(item for item in model_results if item["model"] == "mask_rcnn")
    funnel_counts = [
        len(cohort_ids),
        identified_count,
        cropped_count,
        mask_result["correct_defect_decisions"],
        mask_result["localized_end_to_end_successes"],
    ]
    funnel_labels = (
        "QC-eligible tools",
        "Tool identified",
        "Crop generated",
        "Correct defect decision",
        "Correct mask / no-mask outcome",
    )
    fig, axis = plt.subplots(figsize=(10.5, 5.7))
    y = np.arange(len(funnel_labels))
    bars = axis.barh(y, funnel_counts, color=("#9AA5B1", "#7F8C9A", "#657786", "#4994D4", "#1976D2"))
    axis.bar_label(
        bars,
        labels=[f"{count}/22 ({count / len(cohort_ids):.1%})" for count in funnel_counts],
        padding=5,
        fontsize=9,
    )
    axis.set_yticks(y, funnel_labels)
    axis.invert_yaxis()
    axis.set_xlim(0, 25.5)
    axis.set_xlabel("Linked test instances")
    axis.set_title("Mask R-CNN cascade attrition")
    save(fig, "mask_rcnn_pipeline_attrition")

    # Concrete example: full tray detection, detector-derived tip crop, final predicted mask.
    tray_overlay = RUN_ROOT.parent / "tray_yolo/presentation_predictions/test/overlays/Two Tools Dry__Non-Defect + Defect__IMG_1561.jpg"
    crop_record = new_images["new__newtray_img_1561_tool1"]
    crop_image = REPO_ROOT / "ml/data/local/hook_sinskey/combined_provisional_v2" / crop_record["file_name"]
    mask_overlay = RUN_ROOT / "mask_rcnn/test_outputs/overlays/new__newtray_img_1561_tool1.jpg"
    images = [Image.open(path).convert("RGB") for path in (tray_overlay, crop_image, mask_overlay)]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.8))
    for axis, image, title in zip(
        axes,
        images,
        ("1. Tool identification", "2. Detector-derived tip crop", "3. Mask R-CNN output"),
        strict=True,
    ):
        axis.imshow(image)
        axis.set_title(title)
        axis.axis("off")
    fig.suptitle("Example end-to-end prediction path: IMG_1561, defective instance")
    save(fig, "pipeline_example", svg=False)
    print(json.dumps({"results": str(RESULT_PATH), "figures": str(OUTPUT)}, indent=2))


if __name__ == "__main__":
    main()
