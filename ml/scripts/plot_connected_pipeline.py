"""Create presentation figures for the connected confirmatory pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULT_PATH = REPO_ROOT / "ml/experiments/connected_pipeline_confirmatory_results.json"
OUTPUT = REPO_ROOT / "ml/presentation/figures/connected_pipeline_confirmatory"
BLUE = "#1976D2"
GREEN = "#2E7D32"
ORANGE = "#E67E22"
RED = "#C62828"
GRAY = "#657786"
NOTE = "Confirmatory redesigned-tray cohort: 16 trays, 24 expected Hook Sinskey instances"


def save(fig: plt.Figure, name: str) -> None:
    fig.text(0.5, 0.015, NOTE, ha="center", fontsize=8.5, color="#444444")
    fig.tight_layout(rect=(0, 0.055, 1, 0.96))
    fig.savefig(OUTPUT / f"{name}.png", dpi=180, bbox_inches="tight")
    fig.savefig(OUTPUT / f"{name}.svg", bbox_inches="tight")
    plt.close(fig)


def label_bars(axis: plt.Axes, bars, *, percentage: bool = True) -> None:
    for bar in bars:
        value = bar.get_height()
        label = f"{100 * value:.1f}%" if percentage else f"{value:.2f}"
        axis.text(
            bar.get_x() + bar.get_width() / 2,
            value + (0.025 if percentage else 0.04),
            label,
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )


def main() -> None:
    result = json.loads(RESULT_PATH.read_text())
    OUTPUT.mkdir(parents=True, exist_ok=True)

    stage_labels = [
        "Tool detection\nrecall",
        "Endpoint\naccuracy",
        "Defect accuracy\nwhen detected",
        "End-to-end\ndecision success",
        "Localized\nend-to-end success",
    ]
    stage_values = [
        result["tool_detection"]["recall"],
        result["endpoint_selection"]["accuracy"],
        result["mask_rcnn_classification_detected_instances"]["accuracy"],
        result["end_to_end"]["decision_success_rate"],
        result["end_to_end"]["localized_success_rate"],
    ]
    fig, axis = plt.subplots(figsize=(11, 5.8))
    bars = axis.bar(stage_labels, stage_values, color=[BLUE, GREEN, ORANGE, RED, GRAY])
    axis.set_ylim(0, 1.12)
    axis.set_ylabel("Rate")
    axis.set_title("Connected tray-to-defect pipeline performance", fontweight="bold")
    axis.grid(axis="y", alpha=0.25)
    label_bars(axis, bars)
    save(fig, "pipeline_stage_performance")

    expected = result["evaluation_design"]["expected_hook_instances"]
    attrition_labels = [
        "Expected\ninstruments",
        "Tool\ndetected",
        "Correct\nendpoint",
        "Correct defect\ndecision",
        "Localized\nsuccess",
    ]
    attrition_values = [
        expected,
        result["tool_detection"]["matched"],
        result["endpoint_selection"]["correct"],
        result["end_to_end"]["decision_successes"],
        result["end_to_end"]["localized_successes"],
    ]
    fig, axis = plt.subplots(figsize=(10.5, 5.8))
    bars = axis.bar(attrition_labels, attrition_values, color=[GRAY, BLUE, GREEN, ORANGE, RED])
    axis.set_ylim(0, expected + 4)
    axis.set_ylabel("Hook Sinskey instances")
    axis.set_title("Pipeline attrition", fontweight="bold")
    axis.grid(axis="y", alpha=0.25)
    for bar, value in zip(bars, attrition_values, strict=True):
        axis.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.45,
            f"{value}/{expected}",
            ha="center",
            fontweight="bold",
        )
    save(fig, "pipeline_attrition")

    matrix = result["mask_rcnn_classification_all_expected_instances"]["confusion_matrix"]
    values = np.array([[matrix["tn"], matrix["fp"]], [matrix["fn"], matrix["tp"]]])
    fig, axis = plt.subplots(figsize=(6.8, 5.8))
    image = axis.imshow(values, cmap="Blues", vmin=0, vmax=max(1, values.max()))
    for row in range(2):
        for column in range(2):
            axis.text(
                column,
                row,
                str(values[row, column]),
                ha="center",
                va="center",
                fontsize=18,
                fontweight="bold",
            )
    axis.set_xticks([0, 1], ["Predicted healthy", "Predicted defective"])
    axis.set_yticks([0, 1], ["Actually healthy", "Actually defective"])
    axis.set_title("Mask R-CNN decisions after the connected front end", fontweight="bold")
    fig.colorbar(image, ax=axis, fraction=0.046, pad=0.04)
    save(fig, "connected_confusion_matrix")

    localization_labels = ["Mean full-tray IoU", "Mean full-tray Dice", "Defects localized ≥0.50 IoU"]
    localization_values = [
        result["end_to_end"]["defective_mean_full_tray_iou"],
        result["end_to_end"]["defective_mean_full_tray_dice"],
        result["end_to_end"]["defective_localized_success_rate"],
    ]
    fig, axis = plt.subplots(figsize=(9, 5.8))
    bars = axis.bar(localization_labels, localization_values, color=[BLUE, GREEN, ORANGE])
    axis.set_ylim(0, 1.12)
    axis.set_ylabel("Rate")
    axis.set_title("Full-tray defect-mask localization", fontweight="bold")
    axis.grid(axis="y", alpha=0.25)
    label_bars(axis, bars)
    save(fig, "full_tray_localization")

    review = result["hybrid_review_policy"]
    categories = ["Expected instruments", "False tool outputs"]
    automatic = [review["automatic_instances"], review["additional_false_tool_automatic_outputs"]]
    reviewed = [review["review_instances"], review["additional_false_tool_review_events"]]
    positions = np.arange(2)
    fig, axis = plt.subplots(figsize=(8.5, 5.8))
    first = axis.bar(positions, automatic, color=GREEN, label="Automatic")
    second = axis.bar(positions, reviewed, bottom=automatic, color=ORANGE, label="Human review")
    axis.set_xticks(positions, categories)
    axis.set_ylabel("Output events")
    axis.set_title("Hybrid automation and review workload", fontweight="bold")
    axis.legend()
    axis.grid(axis="y", alpha=0.25)
    for bars in (first, second):
        for bar in bars:
            if bar.get_height():
                axis.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_y() + bar.get_height() / 2,
                    str(int(bar.get_height())),
                    ha="center",
                    va="center",
                    color="white",
                    fontweight="bold",
                )
    save(fig, "hybrid_review_workload")

    alarm = result["end_to_end"]["defect_alarm_accounting"]
    alarm_labels = ["Correct defect\nalarms", "Healthy-tool\nfalse alarms", "False-tool\nfalse alarms"]
    alarm_values = [
        alarm["correct_defect_alarms"],
        alarm["false_alarms_on_healthy_tools"],
        alarm["false_alarms_from_unmatched_tool_detections"],
    ]
    fig, axis = plt.subplots(figsize=(8.5, 5.8))
    bars = axis.bar(alarm_labels, alarm_values, color=[GREEN, ORANGE, RED])
    axis.set_ylabel("Defect alarms")
    axis.set_title("Where defect alarms came from", fontweight="bold")
    axis.grid(axis="y", alpha=0.25)
    for bar, value in zip(bars, alarm_values, strict=True):
        axis.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.25,
            str(value),
            ha="center",
            fontweight="bold",
        )
    axis.text(
        0.98,
        0.93,
        f"Alarm precision: {100 * alarm['alarm_precision_including_unmatched_detections']:.1f}%",
        transform=axis.transAxes,
        ha="right",
        va="top",
        bbox={"facecolor": "white", "edgecolor": "#cccccc", "boxstyle": "round,pad=0.4"},
    )
    save(fig, "defect_alarm_accounting")

    latency = result["latency"]
    fig, axis = plt.subplots(figsize=(7.5, 5.8))
    latency_values = [
        latency["median_tray_to_outputs_ms"] / 1000,
        latency["p95_tray_to_outputs_ms"] / 1000,
    ]
    bars = axis.bar(["Median", "95th percentile"], latency_values, color=[BLUE, GRAY])
    axis.set_ylabel("Seconds per tray")
    axis.set_title("Connected pipeline latency on laptop CPU", fontweight="bold")
    axis.grid(axis="y", alpha=0.25)
    label_bars(axis, bars, percentage=False)
    save(fig, "connected_latency")

    print(f"Wrote {len(list(OUTPUT.glob('*.png')))} PNG figures to {OUTPUT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
