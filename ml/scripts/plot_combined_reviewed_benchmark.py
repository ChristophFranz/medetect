"""Create presentation figures for the authoritative combined reviewed-v3 benchmark."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS = REPO_ROOT / "ml/experiments/combined_reviewed_v3_benchmark_results.json"
OUTPUT = REPO_ROOT / "ml/presentation/figures/combined_reviewed_v3"
RUN_ROOT = REPO_ROOT / "ml/runs/combined_reviewed_v3"
LABELS = {
    "legacy_yolo": "Inherited YOLO",
    "detr_detection": "DETR detection",
    "detr_segmentation": "DETR segmentation",
    "mask_rcnn": "Mask R-CNN",
}
COLORS = {
    "legacy_yolo": "#657786",
    "detr_detection": "#E67E22",
    "detr_segmentation": "#7B61A8",
    "mask_rcnn": "#1976D2",
}
NOTE = "Combined reviewed-v3 frozen test (48 images); thresholds selected on validation only"


def save(fig: plt.Figure, name: str, *, note: str = NOTE) -> None:
    fig.text(0.5, 0.012, note, ha="center", fontsize=8.5, color="#444444")
    fig.tight_layout(rect=(0, 0.055, 1, 0.94))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT / f"{name}.png", dpi=200, bbox_inches="tight")
    fig.savefig(OUTPUT / f"{name}.svg", bbox_inches="tight")
    plt.close(fig)


def classification_figure(models: list[dict]) -> None:
    keys = ("accuracy", "precision", "sensitivity", "specificity", "f1")
    labels = ("Accuracy", "Precision", "Sensitivity", "Specificity", "F1")
    x = np.arange(len(keys))
    width = 0.19
    fig, axis = plt.subplots(figsize=(12.5, 5.8))
    for index, model in enumerate(models):
        values = [model["classification"][key] for key in keys]
        bars = axis.bar(
            x + (index - 1.5) * width,
            values,
            width,
            label=LABELS[model["model"]],
            color=COLORS[model["model"]],
        )
        axis.bar_label(bars, fmt="%.2f", padding=2, fontsize=7.5, rotation=90)
    axis.set_xticks(x, labels)
    axis.set_ylim(0, 1.17)
    axis.set_ylabel("Score")
    axis.set_title("Hook Sinskey defect classification")
    axis.legend(loc="upper right", ncols=2)
    save(fig, "classification_comparison")


def localization_figure(models: list[dict]) -> None:
    by_name = {model["model"]: model for model in models}
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    detection_names = ("legacy_yolo", "detr_detection")
    detection_keys = ("ap50", "ap75", "map50_95")
    x = np.arange(len(detection_keys))
    for index, name in enumerate(detection_names):
        values = [by_name[name]["detection"][key] for key in detection_keys]
        bars = axes[0].bar(
            x + (index - 0.5) * 0.36,
            values,
            0.36,
            label=LABELS[name],
            color=COLORS[name],
        )
        axes[0].bar_label(bars, fmt="%.3f", padding=3, fontsize=8)
    axes[0].set_xticks(x, ("AP50", "AP75", "mAP50–95"))
    axes[0].set_ylim(0, 0.75)
    axes[0].set_ylabel("Score")
    axes[0].set_title("Box detection")
    axes[0].legend()

    segmentation_names = ("detr_segmentation", "mask_rcnn")
    segmentation_keys = ("ap50", "ap75", "map50_95", "iou", "dice")
    x = np.arange(len(segmentation_keys))
    for index, name in enumerate(segmentation_names):
        values = [by_name[name]["segmentation"][key] for key in segmentation_keys]
        bars = axes[1].bar(
            x + (index - 0.5) * 0.36,
            values,
            0.36,
            label=LABELS[name],
            color=COLORS[name],
        )
        axes[1].bar_label(bars, fmt="%.3f", padding=3, fontsize=8, rotation=90)
    axes[1].set_xticks(x, ("AP50", "AP75", "mAP50–95", "IoU", "Dice"))
    axes[1].set_ylim(0, 0.9)
    axes[1].set_title("Instance segmentation")
    axes[1].legend()
    fig.suptitle("Defect localization performance")
    save(fig, "localization_comparison")


def domain_figure(models: list[dict]) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.4), sharey=True)
    domains = (("old", "Original images"), ("new", "Redesigned tray"))
    width = 0.19
    for axis, metric, title in zip(
        axes, ("accuracy", "f1"), ("Accuracy", "F1"), strict=True
    ):
        x = np.arange(2)
        for index, model in enumerate(models):
            values = [
                model["classification_by_domain"][domain][metric]
                for domain, _label in domains
            ]
            bars = axis.bar(
                x + (index - 1.5) * width,
                values,
                width,
                label=LABELS[model["model"]],
                color=COLORS[model["model"]],
            )
            axis.bar_label(bars, fmt="%.2f", padding=2, fontsize=7.5, rotation=90)
        axis.set_xticks(x, [label for _domain, label in domains])
        axis.set_ylim(0, 1.16)
        axis.set_title(title)
    axes[0].set_ylabel("Score")
    axes[1].legend(loc="upper right", ncols=2, fontsize=8.5)
    fig.suptitle("Performance by acquisition domain")
    save(fig, "domain_comparison")


def confusion_figure(models: list[dict]) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(9.5, 8.5))
    for axis, model in zip(axes.flat, models, strict=True):
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
                    fontsize=16,
                    color="white" if values[row, column] > values.max() / 2 else "#222222",
                )
        axis.set_xticks((0, 1), ("Healthy", "Defective"))
        axis.set_yticks((0, 1), ("Healthy", "Defective"))
        axis.set_xlabel("Predicted")
        axis.set_ylabel("Actual")
        axis.set_title(LABELS[model["model"]])
    fig.suptitle("Frozen-test confusion matrices")
    save(fig, "confusion_matrices")


def training_curves() -> dict[str, int]:
    names = ("detr_detection", "detr_segmentation", "mask_rcnn")
    summaries = {
        name: json.loads((RUN_ROOT / name / "training_summary.json").read_text())
        for name in names
    }
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.7))
    for axis, name in zip(axes, names, strict=True):
        history = summaries[name]["history"]
        epochs = [item["epoch"] for item in history]
        axis.plot(epochs, [item["train_loss"] for item in history], label="Train", linewidth=2)
        axis.plot(
            epochs,
            [item["validation_loss"] for item in history],
            label="Validation",
            linewidth=2,
        )
        axis.axvline(
            summaries[name]["best_epoch"],
            color="#C62828",
            linestyle="--",
            label=f"Best: {summaries[name]['best_epoch']}",
        )
        axis.set_xlabel("Epoch")
        axis.set_ylabel("Loss")
        axis.set_title(LABELS[name])
        axis.legend(fontsize=8)
    fig.suptitle("Full-backbone training and validation loss")
    save(fig, "training_curves")
    return {name: int(summary["epochs_completed"]) for name, summary in summaries.items()}


def augmentation_figure(epochs: dict[str, int]) -> None:
    training_images = 342
    names = tuple(epochs)
    exposures = [training_images * epochs[name] for name in names]
    additional = [value - training_images for value in exposures]
    fig, axis = plt.subplots(figsize=(10.5, 5.5))
    x = np.arange(len(names))
    bars = axis.bar(x, exposures, color=[COLORS[name] for name in names])
    axis.axhline(
        training_images,
        color="#333333",
        linestyle="--",
        label="Static training images: 342",
    )
    axis.bar_label(
        bars,
        labels=[
            f"{value:,} views\n(+{extra:,})"
            for value, extra in zip(exposures, additional, strict=True)
        ],
        padding=4,
        fontsize=9,
    )
    axis.set_xticks(x, [LABELS[name] for name in names])
    axis.set_ylim(0, max(exposures) * 1.16)
    axis.set_ylabel("Training-image presentations")
    axis.set_title("On-the-fly augmentation exposure")
    axis.legend()
    save(
        fig,
        "augmentation_exposure",
        note=(
            "342 files remain on disk; transforms are generated during training and do not "
            "alter validation or test images"
        ),
    )


def operational_figure(models: list[dict]) -> None:
    names = [model["model"] for model in models]
    latency = [model["operational"]["median_latency_ms"] for model in models]
    size = [model["operational"]["model_size_bytes"] / (1024 * 1024) for model in models]
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.1))
    bars = axes[0].bar(names, latency, color=[COLORS[name] for name in names])
    axes[0].bar_label(bars, fmt="%.1f ms", padding=3, fontsize=8)
    axes[0].set_xticks(range(len(names)), [LABELS[name] for name in names], rotation=15)
    axes[0].set_ylabel("Median latency (ms/image)")
    axes[0].set_title("Apple MPS inference latency")
    bars = axes[1].bar(names, size, color=[COLORS[name] for name in names])
    axes[1].bar_label(bars, fmt="%.1f MB", padding=3, fontsize=8)
    axes[1].set_xticks(range(len(names)), [LABELS[name] for name in names], rotation=15)
    axes[1].set_ylabel("Checkpoint size (MiB)")
    axes[1].set_title("Model size")
    save(fig, "operational_comparison")


def main() -> None:
    results = json.loads(RESULTS.read_text())
    models = results["models"]
    plt.style.use("seaborn-v0_8-whitegrid")
    classification_figure(models)
    localization_figure(models)
    domain_figure(models)
    confusion_figure(models)
    epochs = training_curves()
    augmentation_figure(epochs)
    operational_figure(models)
    print(OUTPUT)


if __name__ == "__main__":
    main()
