"""Create presentation figures for the provisional tray-detector comparison."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inherited", type=Path, required=True)
    parser.add_argument("--retrained", type=Path, required=True)
    parser.add_argument("--training-csv", type=Path, required=True)
    parser.add_argument(
        "--output", type=Path,
        default=REPO_ROOT / "ml/presentation/figures/tray_detector_provisional",
    )
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    inherited = json.loads(args.inherited.read_text())
    retrained = json.loads(args.retrained.read_text())
    by_model = {
        "Inherited YOLO": {item["domain"]: item for item in inherited["evaluations"]},
        "Retrained YOLO": {item["domain"]: item for item in retrained["evaluations"]},
    }

    plt.style.use("seaborn-v0_8-whitegrid")
    metrics = (("map50", "mAP50"), ("map50_95", "mAP50–95"))
    domains = (("inherited_tray", "Original tray"), ("redesigned_tray", "Redesigned tray"))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), sharey=True)
    x = np.arange(len(domains))
    width = 0.36
    colors = ("#9AA5B1", "#1976D2")
    for axis, (metric, title) in zip(axes, metrics, strict=True):
        for offset, ((model_name, results), color) in enumerate(zip(by_model.items(), colors, strict=True)):
            values = [results[key][metric] for key, _ in domains]
            bars = axis.bar(x + (offset - 0.5) * width, values, width, label=model_name, color=color)
            axis.bar_label(bars, fmt="%.3f", padding=3, fontsize=9)
        axis.set_title(title)
        axis.set_xticks(x, [label for _, label in domains])
        axis.set_ylim(0, 1.08)
    axes[0].set_ylabel("Score")
    axes[1].legend(loc="upper left")
    fig.suptitle("Tray detector performance by acquisition domain")
    fig.text(0.5, 0.01, "Provisional: redesigned-tray boxes are machine-generated and unreviewed", ha="center", fontsize=9)
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    for suffix in ("png", "svg"):
        fig.savefig(output / f"domain_comparison.{suffix}", dpi=180, bbox_inches="tight")
    plt.close(fig)

    frame = pd.read_csv(args.training_csv)
    frame.columns = [column.strip() for column in frame.columns]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    axes[0].plot(frame["epoch"], frame["train/box_loss"], label="Train box loss", linewidth=2)
    axes[0].plot(frame["epoch"], frame["val/box_loss"], label="Validation box loss", linewidth=2)
    axes[0].set(title="Localization loss", xlabel="Epoch", ylabel="Loss")
    axes[0].legend()
    axes[1].plot(frame["epoch"], frame["metrics/mAP50(B)"], label="mAP50", linewidth=2)
    axes[1].plot(frame["epoch"], frame["metrics/mAP50-95(B)"], label="mAP50–95", linewidth=2)
    axes[1].set(title="Mixed-domain validation performance", xlabel="Epoch", ylabel="Score", ylim=(0, 1))
    axes[1].legend()
    fig.suptitle("Provisional redesigned-tray YOLO fine-tuning")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    for suffix in ("png", "svg"):
        fig.savefig(output / f"training_curves.{suffix}", dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(output)


if __name__ == "__main__":
    main()
