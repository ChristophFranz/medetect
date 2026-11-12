"""Create presentation figures for the provisional combined defect benchmark."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
MODEL_LABELS = {
    "legacy_yolo": "Inherited YOLO",
    "detr_detection": "DETR detection",
    "mask_rcnn": "Mask R-CNN",
}
COLORS = ("#657786", "#E67E22", "#1976D2")
NOTE = "Provisional: new masks unreviewed; DETR and Mask R-CNN received one CPU adaptation epoch"


def save(fig: plt.Figure, output: Path, name: str) -> None:
    fig.text(0.5, 0.012, NOTE, ha="center", fontsize=8.5, color="#444444")
    fig.tight_layout(rect=(0, 0.055, 1, 0.94))
    for suffix in ("png", "svg"):
        fig.savefig(output / f"{name}.{suffix}", dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--results",
        type=Path,
        default=REPO_ROOT / "ml/experiments/combined_provisional_benchmark_results.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "ml/presentation/figures/combined_provisional",
    )
    args = parser.parse_args()
    results = json.loads(args.results.read_text())
    models = results["models"]
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid")

    # Classification outcomes at the frozen validation-selected thresholds.
    metric_keys = ("accuracy", "precision", "sensitivity", "specificity", "f1")
    metric_labels = ("Accuracy", "Precision", "Sensitivity", "Specificity", "F1")
    x = np.arange(len(metric_keys))
    width = 0.25
    fig, axis = plt.subplots(figsize=(11.5, 5.4))
    for index, (model, color) in enumerate(zip(models, COLORS, strict=True)):
        values = [model["classification"][key] for key in metric_keys]
        bars = axis.bar(
            x + (index - 1) * width,
            values,
            width,
            label=MODEL_LABELS[model["model"]],
            color=color,
        )
        axis.bar_label(bars, fmt="%.2f", padding=2, fontsize=8)
    axis.set_xticks(x, metric_labels)
    axis.set_ylim(0, 1.12)
    axis.set_ylabel("Score")
    axis.set_title("Hook Sinskey defect classification on the combined test set")
    axis.legend(loc="upper right", ncols=3)
    save(fig, output, "classification_comparison")

    # Localization metrics are task-specific, so detection and segmentation are separated.
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.0), sharey=True)
    detection_models = models[:2]
    detection_values = np.array(
        [[item["detection"]["ap50"], item["detection"]["map50_95"]] for item in detection_models]
    )
    for index, (item, color) in enumerate(zip(detection_models, COLORS[:2], strict=True)):
        bars = axes[0].bar(
            np.arange(2) + (index - 0.5) * 0.36,
            detection_values[index],
            0.36,
            label=MODEL_LABELS[item["model"]],
            color=color,
        )
        axes[0].bar_label(bars, fmt="%.3f", padding=3, fontsize=9)
    axes[0].set_xticks(np.arange(2), ("AP50", "mAP50–95"))
    axes[0].set_title("Box detection")
    axes[0].set_ylabel("COCO score")
    axes[0].legend()

    mask = models[2]["segmentation"]
    mask_keys = ("ap50", "ap75", "map50_95", "iou", "dice")
    bars = axes[1].bar(
        np.arange(len(mask_keys)),
        [mask[key] for key in mask_keys],
        color="#1976D2",
    )
    axes[1].bar_label(bars, fmt="%.3f", padding=3, fontsize=9)
    axes[1].set_xticks(np.arange(len(mask_keys)), ("AP50", "AP75", "mAP50–95", "IoU", "Dice"))
    axes[1].set_title("Mask R-CNN segmentation")
    axes[1].set_ylim(0, 0.8)
    fig.suptitle("Defect localization performance")
    save(fig, output, "localization_comparison")

    # Domain split highlights transfer from the inherited acquisition setup to the new tray.
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.0), sharey=True)
    domains = (("old", "Original\nimages"), ("new", "Redesigned-tray\nimages"))
    for axis, metric, title in zip(axes, ("accuracy", "f1"), ("Accuracy", "F1"), strict=True):
        domain_x = np.arange(2)
        for index, (model, color) in enumerate(zip(models, COLORS, strict=True)):
            values = [model["classification_by_domain"][key][metric] for key, _ in domains]
            bars = axis.bar(
                domain_x + (index - 1) * width,
                values,
                width,
                label=MODEL_LABELS[model["model"]],
                color=color,
            )
            axis.bar_label(bars, fmt="%.2f", padding=2, fontsize=8)
        axis.set_xticks(domain_x, [label for _, label in domains])
        axis.set_ylim(0, 1.12)
        axis.set_title(title)
    axes[0].set_ylabel("Score")
    axes[1].legend(loc="upper right", fontsize=9)
    fig.suptitle("Classification performance by acquisition domain")
    save(fig, output, "domain_comparison")

    fig, axes = plt.subplots(1, 3, figsize=(11.5, 4.2))
    for axis, model in zip(axes, models, strict=True):
        matrix = model["classification"]["confusion_matrix"]
        values = np.array([[matrix["tn"], matrix["fp"]], [matrix["fn"], matrix["tp"]]])
        axis.imshow(values, cmap="Blues", vmin=0, vmax=max(1, values.max()))
        for row in range(2):
            for column in range(2):
                axis.text(
                    column,
                    row,
                    str(values[row, column]),
                    ha="center",
                    va="center",
                    fontsize=14,
                    color="white" if values[row, column] > values.max() / 2 else "#222222",
                )
        axis.set_xticks((0, 1), ("Healthy", "Defective"))
        axis.set_yticks((0, 1), ("Healthy", "Defective"))
        axis.set_xlabel("Predicted")
        axis.set_ylabel("Actual")
        axis.set_title(MODEL_LABELS[model["model"]])
    fig.suptitle("Test-set confusion matrices (46 images)")
    save(fig, output, "confusion_matrices")
    print(output)


if __name__ == "__main__":
    main()
