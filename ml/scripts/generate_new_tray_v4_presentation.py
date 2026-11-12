"""Build a clearly labelled presentation bundle for the new-tray v4 benchmark."""

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
CROP_RESULTS = REPO_ROOT / "ml/experiments/new_tray_v4_defect_benchmark_results.json"
CONNECTED_RESULTS = REPO_ROOT / "ml/experiments/new_tray_v4_connected_results.json"
STAGE_RESULTS = REPO_ROOT / "ml/experiments/new_tray_v4_stage_consistent_metrics.json"
OUTPUT = REPO_ROOT / "ml/exports/hook_sinskey_current/NEW_TRAY_V4_RESULTS"
NAMES = {
    "yolo_detection": "YOLO defect detection",
    "detr_detection": "DETR defect detection",
    "detr_segmentation": "DETR segmentation",
    "mask_rcnn": "Mask R-CNN segmentation",
}
COLORS = ["#2563eb", "#7c3aed", "#ea580c", "#059669"]


def percent(value: float | None) -> str:
    return "—" if value is None else f"{100 * value:.1f}%"


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def grouped_chart(path: Path, title: str, models: list[str], series: dict[str, list[float]], ylabel: str = "Percent") -> None:
    figure, axis = plt.subplots(figsize=(12, 6.75), constrained_layout=True)
    x = np.arange(len(models))
    width = 0.8 / len(series)
    for index, (label, values) in enumerate(series.items()):
        positions = x - 0.4 + width / 2 + index * width
        bars = axis.bar(positions, np.asarray(values) * 100, width, label=label, color=COLORS[index])
        axis.bar_label(bars, fmt="%.1f", fontsize=8, padding=2)
    axis.set_title(title, fontsize=16, weight="bold")
    axis.set_ylabel(ylabel)
    axis.set_xticks(x, models, rotation=12, ha="right")
    axis.set_ylim(0, 110)
    axis.grid(axis="y", alpha=0.25)
    axis.legend(ncols=min(4, len(series)), loc="upper center", bbox_to_anchor=(0.5, -0.19))
    figure.savefig(path, dpi=180)
    plt.close(figure)


def main() -> None:
    if not CROP_RESULTS.is_file() or not CONNECTED_RESULTS.is_file() or not STAGE_RESULTS.is_file():
        raise FileNotFoundError("run both v4 evaluators and the stage-consistent audit before generating the presentation bundle")
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    (OUTPUT / "01_OFFLINE_FIXED_CROP_REFERENCE").mkdir(parents=True)
    (OUTPUT / "02_COMPLETE_PIPELINE").mkdir(parents=True)
    (OUTPUT / "03_VISUAL_OUTPUTS").mkdir(parents=True)
    crop = json.loads(CROP_RESULTS.read_text())
    connected = json.loads(CONNECTED_RESULTS.read_text())
    stage = json.loads(STAGE_RESULTS.read_text())

    crop_rows = []
    for result in crop["models"]:
        classification = result["classification"]
        localization = result["localization"]
        crop_rows.append({
            "model": NAMES[result["model"]],
            "model_type": localization["type"],
            "accuracy": classification["accuracy"],
            "precision": classification["precision"],
            "sensitivity": classification["sensitivity"],
            "specificity": classification["specificity"],
            "f1": classification["f1"],
            "pr_auc": classification["pr_auc"],
            "roc_auc": classification["roc_auc"],
            "ap50": localization["ap50"],
            "ap75": localization["ap75"],
            "map50_95": localization["map50_95"],
            "mean_iou": localization.get("iou", ""),
            "mean_dice": localization.get("dice", ""),
            "score_threshold": result["score_threshold"],
            "minimum_mask_area": result["minimum_mask_area"] or "",
            "median_latency_ms": result["operational"]["median_latency_ms"],
            "p95_latency_ms": result["operational"]["p95_latency_ms"],
        })
    write_csv(OUTPUT / "01_OFFLINE_FIXED_CROP_REFERENCE/metrics.csv", crop_rows)
    grouped_chart(
        OUTPUT / "01_OFFLINE_FIXED_CROP_REFERENCE/classification_comparison.png",
        "Offline reference — 24 fixed reviewed tip crops",
        [row["model"] for row in crop_rows],
        {
            "Accuracy": [row["accuracy"] for row in crop_rows],
            "Sensitivity": [row["sensitivity"] for row in crop_rows],
            "Specificity": [row["specificity"] for row in crop_rows],
            "F1": [row["f1"] for row in crop_rows],
        },
    )
    grouped_chart(
        OUTPUT / "01_OFFLINE_FIXED_CROP_REFERENCE/localization_comparison.png",
        "Offline fixed-crop localization — boxes for detectors, masks for segmenters",
        [row["model"] for row in crop_rows],
        {
            "AP50": [row["ap50"] for row in crop_rows],
            "AP75": [row["ap75"] for row in crop_rows],
            "mAP50–95": [row["map50_95"] for row in crop_rows],
        },
    )

    connected_by_model = {item["model"]: item for item in connected["models"]}
    connected_rows = []
    for result in stage["models"]:
        conditional = result["conditional_on_delivered_generated_crops"]
        strict = result["strict_connected_pipeline"]
        raw_connected = connected_by_model[result["model"]]
        end_to_end = raw_connected["end_to_end"]
        connected_rows.append({
            "downstream_model": NAMES[result["model"]],
            "localization_type": end_to_end["localization_type"],
            "delivered_generated_crops": conditional["delivered_crops"],
            "generated_crop_accuracy": conditional["accuracy"],
            "generated_crop_defective_recall": conditional["defective_recall"],
            "generated_crop_false_negative_rate": conditional["false_negative_rate"],
            "strict_pipeline_correct": strict["strict_correct"],
            "strict_pipeline_expected": strict["expected_tools"],
            "strict_pipeline_accuracy": strict["strict_accuracy"],
            "strict_pipeline_defective_recall": strict["defective_recall"],
            "strict_pipeline_false_negative_rate": strict["false_negative_rate"],
            "localized_pipeline_success_rate": strict["localized_success_rate"],
            "defective_localized_recall": strict["defective_localized_recall"],
            "defective_mean_localization_iou": end_to_end["defective_mean_localization_iou"],
            "defective_mean_mask_dice": end_to_end["defective_mean_mask_dice"] if end_to_end["defective_mean_mask_dice"] is not None else "",
            "alarm_precision_including_false_tool_detections": raw_connected["alarm_accounting"]["alarm_precision_including_unmatched_detections"],
            "median_tray_latency_ms": result["per_tray_latency_ms"]["median_tray_to_outputs_ms"],
            "p95_tray_latency_ms": result["per_tray_latency_ms"]["p95_tray_to_outputs_ms"],
        })
    write_csv(OUTPUT / "02_COMPLETE_PIPELINE/metrics.csv", connected_rows)
    grouped_chart(
        OUTPUT / "02_COMPLETE_PIPELINE/end_to_end_comparison.png",
        "Complete pipeline — tray YOLO → tip crop → defect model",
        [row["downstream_model"] for row in connected_rows],
        {
            "Model accuracy on 20 delivered crops": [row["generated_crop_accuracy"] for row in connected_rows],
            "Strict pipeline accuracy on 24 expected tools": [row["strict_pipeline_accuracy"] for row in connected_rows],
            "Localized pipeline success": [row["localized_pipeline_success_rate"] for row in connected_rows],
        },
    )
    tool = connected["tool_detection_common_to_all_models"]
    endpoint = connected["endpoint_selection_common_to_all_models"]
    component_rows = [
        {"component": "Tray YOLO", "metric": "precision", "value": tool["precision"]},
        {"component": "Tray YOLO", "metric": "recall", "value": tool["recall"]},
        {"component": "Tray YOLO", "metric": "AP50", "value": tool["ap50"]},
        {"component": "Tray YOLO", "metric": "mAP50-95", "value": tool["map50_95"]},
        {"component": "Endpoint cropper", "metric": "tip-side accuracy", "value": endpoint["accuracy"]},
    ]
    write_csv(OUTPUT / "02_COMPLETE_PIPELINE/shared_components.csv", component_rows)

    for result in crop["models"]:
        destination = OUTPUT / "03_VISUAL_OUTPUTS" / f"CROP_{result['model']}"
        shutil.copytree(
            REPO_ROOT / result["structured_outputs"] / "overlays",
            destination / "OVERLAYS",
        )
        mask_source = REPO_ROOT / result["structured_outputs"] / "masks"
        if mask_source.is_dir() and any(mask_source.iterdir()):
            shutil.copytree(mask_source, destination / "MASKS")
    for result in connected["models"]:
        destination = OUTPUT / "03_VISUAL_OUTPUTS" / f"FULL_TRAY_{result['model']}"
        shutil.copytree(
            REPO_ROOT / result["overlay_directory"], destination / "OVERLAYS"
        )
        mask_source = (REPO_ROOT / result["overlay_directory"]).parent / "masks"
        if mask_source.is_dir() and any(mask_source.iterdir()):
            shutil.copytree(mask_source, destination / "MASKS")

    lines = [
        "# Hook Sinskey new-tray v4 results",
        "",
        "> Confirmatory benchmark: these 24 crop / 16 tray captures were exposed during earlier project work. No test-informed threshold tuning was performed.",
        "",
        "## 1. Offline fixed-crop reference (separate experiment)",
        "",
        "These 24 fixed reviewed crops are not the crops generated by the connected pipeline. Do not use this table as the upstream stage of the connected table.",
        "",
        "| Model | Accuracy | Sensitivity | Specificity | F1 | AP50 | mAP50–95 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in crop_rows:
        lines.append(f"| {row['model']} | {percent(row['accuracy'])} | {percent(row['sensitivity'])} | {percent(row['specificity'])} | {percent(row['f1'])} | {percent(row['ap50'])} | {percent(row['map50_95'])} |")
    lines += [
        "",
        "## 2. Complete pipeline (16 tray photos, 24 expected tools)",
        "",
        f"Shared tray YOLO: precision {percent(tool['precision'])}, recall {percent(tool['recall'])}, AP50 {percent(tool['ap50'])}, mAP50–95 {percent(tool['map50_95'])}. Shared tip-side selector accuracy: {percent(endpoint['accuracy'])}.",
        "",
        "The tray detector delivered 20 generated crops from 24 expected tools. Conditional model performance and strict pipeline performance below come from the same connected run.",
        "",
        "| Downstream model | Accuracy on 20 delivered crops | Defective recall | Strict pipeline accuracy (all 24) | FNR | Localized success |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in connected_rows:
        lines.append(f"| {row['downstream_model']} | {percent(row['generated_crop_accuracy'])} | {percent(row['strict_pipeline_defective_recall'])} | {percent(row['strict_pipeline_accuracy'])} | {percent(row['strict_pipeline_false_negative_rate'])} | {percent(row['localized_pipeline_success_rate'])} |")
    lines += [
        "",
        "Definitions: delivered-crop accuracy evaluates only the exact generated crops received by the downstream model. Strict pipeline accuracy counts every missed expected tool as wrong. Localized success additionally requires IoU ≥ 0.50 for a defect box or mask.",
        "",
        "See the CSV files for all metrics, thresholds, and latency. `03_VISUAL_OUTPUTS` contains model-by-model crop and full-tray overlays.",
    ]
    (OUTPUT / "README.md").write_text("\n".join(lines) + "\n")
    shutil.copy2(CROP_RESULTS, OUTPUT / "01_OFFLINE_FIXED_CROP_REFERENCE/results.json")
    shutil.copy2(CONNECTED_RESULTS, OUTPUT / "02_COMPLETE_PIPELINE/results.json")
    shutil.copy2(STAGE_RESULTS, OUTPUT / "02_COMPLETE_PIPELINE/stage_consistent_metrics.json")
    print(OUTPUT.relative_to(REPO_ROOT))


if __name__ == "__main__":
    main()
