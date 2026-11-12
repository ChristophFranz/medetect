"""Generate presentation-ready plots from recorded benchmark results."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ML_ROOT = REPO_ROOT / "ml"
os.environ.setdefault("MPLCONFIGDIR", str(ML_ROOT / "runs/.matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(ML_ROOT / "runs/.cache"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

MODEL_LABELS = {
    "legacy_yolo": "Legacy YOLO",
    "detr_detection": "DETR detection",
    "detr_segmentation": "DETR segmentation",
    "mask_rcnn": "Mask R-CNN",
}
COLORS = ["#4C78A8", "#F58518", "#E45756", "#54A24B"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=ML_ROOT / "presentation/figures"
    )
    return parser.parse_args()


def save(fig: plt.Figure, output: Path, name: str) -> None:
    fig.savefig(output / f"{name}.png", dpi=220, bbox_inches="tight")
    fig.savefig(output / f"{name}.svg", bbox_inches="tight")
    plt.close(fig)


def annotate_bars(ax: plt.Axes, bars, digits: int = 2) -> None:
    for bar in bars:
        value = bar.get_height()
        ax.annotate(
            f"{value:.{digits}f}",
            (bar.get_x() + bar.get_width() / 2, value),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
        )


def plot_classification(models: list[dict], output: Path) -> None:
    metrics = ["accuracy", "precision", "sensitivity", "specificity", "f1"]
    labels = ["Accuracy", "Precision", "Sensitivity", "Specificity", "F1"]
    x = np.arange(len(metrics))
    width = 0.19
    fig, ax = plt.subplots(figsize=(12, 6.4))
    for offset, (model, color) in enumerate(zip(models, COLORS, strict=True)):
        values = [model["classification"][metric] for metric in metrics]
        bars = ax.bar(
            x + (offset - 1.5) * width,
            values,
            width,
            label=MODEL_LABELS[model["model"]],
            color=color,
        )
        annotate_bars(ax, bars)
    ax.set_title("Hook Sinskey defect classification — frozen test split (n=24)")
    ax.set_ylabel("Score")
    ax.set_xticks(x, labels)
    ax.set_ylim(0, 1.12)
    ax.legend(ncols=2, frameon=False)
    ax.grid(axis="y", alpha=0.25)
    fig.text(
        0.5,
        0.01,
        "Thresholds selected on validation data. Higher is better.",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.035, 1, 1))
    save(fig, output, "classification-comparison")


def plot_localization(models: list[dict], output: Path) -> None:
    x = np.arange(len(models))
    width = 0.25
    values = {"AP50": [], "AP75": [], "mAP50–95": []}
    task_labels = []
    for model in models:
        task = model.get("detection") or model.get("segmentation")
        values["AP50"].append(task["ap50"])
        values["AP75"].append(task["ap75"])
        values["mAP50–95"].append(task["map50_95"])
        task_labels.append(
            f"{MODEL_LABELS[model['model']]}\n({'box AP' if 'detection' in model else 'mask AP'})"
        )
    fig, ax = plt.subplots(figsize=(11, 6.4))
    for index, (metric, color) in enumerate(zip(values, COLORS[:3], strict=True)):
        bars = ax.bar(x + (index - 1) * width, values[metric], width, label=metric, color=color)
        annotate_bars(ax, bars)
    ax.set_title("Localization performance — frozen test split")
    ax.set_ylabel("Average precision")
    ax.set_xticks(x, task_labels)
    ax.set_ylim(0, 0.82)
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.25)
    fig.text(
        0.5,
        0.01,
        "Detection models use bounding-box AP; segmentation models use mask AP. Higher is better.",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    save(fig, output, "localization-comparison")


def plot_confusion_matrices(models: list[dict], output: Path) -> None:
    fig, axes = plt.subplots(1, 4, figsize=(13, 3.8), constrained_layout=True)
    maximum = max(
        max(model["classification"]["confusion_matrix"].values()) for model in models
    )
    for ax, model in zip(axes, models, strict=True):
        cm = model["classification"]["confusion_matrix"]
        matrix = np.asarray([[cm["tn"], cm["fp"]], [cm["fn"], cm["tp"]]])
        image = ax.imshow(matrix, cmap="Blues", vmin=0, vmax=maximum)
        for row in range(2):
            for column in range(2):
                ax.text(
                    column,
                    row,
                    str(matrix[row, column]),
                    ha="center",
                    va="center",
                    color="white" if matrix[row, column] > maximum / 2 else "black",
                    fontsize=15,
                )
        ax.set_title(MODEL_LABELS[model["model"]], fontsize=10)
        ax.set_xticks([0, 1], ["Healthy", "Defective"])
        ax.set_yticks([0, 1], ["Healthy", "Defective"])
        ax.set_xlabel("Predicted")
        if ax is axes[0]:
            ax.set_ylabel("Reviewed label")
    fig.colorbar(image, ax=axes, shrink=0.72, label="Images")
    fig.suptitle("Confusion matrices — frozen test split (18 defective, 6 healthy)")
    save(fig, output, "confusion-matrices")


def plot_efficiency(models: list[dict], output: Path) -> None:
    labels = [MODEL_LABELS[model["model"]] for model in models]
    x = np.arange(len(models))
    medians = [model["operational"]["median_latency_ms"] for model in models]
    p95s = [model["operational"]["p95_latency_ms"] for model in models]
    sizes = [model["operational"]["model_size_bytes"] / 1_000_000 for model in models]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2))
    width = 0.36
    bars1 = axes[0].bar(x - width / 2, medians, width, label="Median", color=COLORS[0])
    bars2 = axes[0].bar(x + width / 2, p95s, width, label="p95", color=COLORS[1])
    annotate_bars(axes[0], bars1, 0)
    annotate_bars(axes[0], bars2, 0)
    axes[0].set_title("Inference latency on Apple MPS")
    axes[0].set_ylabel("Milliseconds per image")
    axes[0].set_xticks(x, labels, rotation=18, ha="right")
    axes[0].legend(frameon=False)
    axes[0].grid(axis="y", alpha=0.25)
    bars3 = axes[1].bar(x, sizes, color=COLORS)
    annotate_bars(axes[1], bars3, 0)
    axes[1].set_title("Checkpoint size")
    axes[1].set_ylabel("MB (decimal)")
    axes[1].set_xticks(x, labels, rotation=18, ha="right")
    axes[1].grid(axis="y", alpha=0.25)
    fig.tight_layout()
    save(fig, output, "operational-comparison")


def plot_training(output: Path) -> None:
    model_names = ("detr_detection", "detr_segmentation", "mask_rcnn")
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.5))
    for ax, model_name in zip(axes, model_names, strict=True):
        path = ML_ROOT / "runs/benchmark" / model_name / "training_summary.json"
        summary = json.loads(path.read_text())
        epochs = [item["epoch"] for item in summary["history"]]
        train = [item["train_loss"] for item in summary["history"]]
        valid = [item["validation_loss"] for item in summary["history"]]
        ax.plot(epochs, train, label="Train", color=COLORS[0], linewidth=2)
        ax.plot(epochs, valid, label="Validation", color=COLORS[1], linewidth=2)
        ax.axvline(
            summary["best_epoch"], color=COLORS[3], linestyle="--", linewidth=1.5, label="Best epoch"
        )
        ax.set_title(MODEL_LABELS[model_name])
        ax.set_xlabel("Epoch")
        ax.set_ylabel("Model training loss")
        ax.grid(alpha=0.25)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.suptitle("Controlled-training curves (loss scales are model-specific)", y=0.98)
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.925),
        ncols=3,
        frameon=False,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.84))
    save(fig, output, "training-curves")


def main() -> None:
    args = parse_args()
    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    benchmark = json.loads((ML_ROOT / "experiments/benchmark_results.json").read_text())
    models = benchmark["models"]
    plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False})
    plot_classification(models, output)
    plot_localization(models, output)
    plot_confusion_matrices(models, output)
    plot_efficiency(models, output)
    plot_training(output)
    print(f"Wrote 5 PNG and 5 SVG figures to {output}")


if __name__ == "__main__":
    main()
