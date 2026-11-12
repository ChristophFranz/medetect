"""Build a simple, numbered, local-only results directory for human review."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = REPO_ROOT / "ml/exports/hook_sinskey_current"


def copy_tree(source: Path, target: Path) -> int:
    if not source.exists():
        return 0
    count = 0
    for path in source.rglob("*"):
        if not path.is_file():
            continue
        destination = target / path.relative_to(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--update", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() and not args.update:
        raise SystemExit(f"refusing to overwrite existing results bundle: {output}")
    if output.exists() and args.update:
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)

    sources = [
        (REPO_ROOT / "ml/data/local/hook_sinskey/new_tray_reviewed_v4_augmented_50_50/review_gallery", output / "01_DATASET_AUGMENTATION_PREVIEW"),
        (REPO_ROOT / "ml/runs/connected_pipeline_confirmatory/overlays", output / "02_FULL_TRAY_PIPELINE_OVERLAYS"),
        (REPO_ROOT / "ml/runs/combined_reviewed_v3/error_gallery", output / "04_DEFECT_MODEL_ERROR_GALLERY"),
        (REPO_ROOT / "ml/presentation/figures/combined_reviewed_v3", output / "05_DEFECT_MODEL_FIGURES"),
        (REPO_ROOT / "ml/presentation/figures/connected_pipeline_confirmatory", output / "06_END_TO_END_FIGURES"),
    ]
    copied = {target.name: copy_tree(source, target) for source, target in sources}
    training_source = (
        REPO_ROOT
        / "ml/data/local/hook_sinskey/new_tray_reviewed_v4_augmented_50_50/images/train"
    )
    preview_root = output / "01_DATASET_AUGMENTATION_PREVIEW"
    for name, pattern in (
        ("ORIGINALS_ONLY", "*.jpg"),
        ("AUGMENTED_ONLY", "*__aug01.jpg"),
    ):
        target = preview_root / name
        target.mkdir(parents=True, exist_ok=True)
        selected = sorted(training_source.glob(pattern))
        if name == "ORIGINALS_ONLY":
            selected = [path for path in selected if not path.name.endswith("__aug01.jpg")]
        for path in selected:
            shutil.copy2(path, target / path.name)
        copied[f"01_DATASET_AUGMENTATION_PREVIEW/{name}"] = len(selected)
    defect_outputs = output / "03_DEFECT_MODEL_OUTPUTS"
    for model in ("legacy_yolo", "detr_detection", "detr_segmentation", "mask_rcnn"):
        copied[f"03_DEFECT_MODEL_OUTPUTS/{model}"] = copy_tree(
            REPO_ROOT / "ml/runs/combined_reviewed_v3" / model / "test_outputs",
            defect_outputs / model,
        )
    metrics = output / "07_METRICS_AND_REPORTS"
    metrics.mkdir(exist_ok=True)
    for relative in (
        "ml/COMBINED_REVIEWED_V3_REPORT.md",
        "ml/CONNECTED_PIPELINE_CONFIRMATORY_REPORT.md",
        "ml/experiments/combined_reviewed_v3_benchmark_results.json",
        "ml/experiments/connected_pipeline_confirmatory_results.json",
        "ml/experiments/combined_reviewed_v3_thresholds.json",
    ):
        source = REPO_ROOT / relative
        if source.exists():
            shutil.copy2(source, metrics / source.name)

    readme = """# Hook Sinskey Results — Start Here

Open folders in numeric order:

1. `01_DATASET_AUGMENTATION_PREVIEW` — original/augmented pairs awaiting review.
   Open `ORIGINALS_ONLY` or `AUGMENTED_ONLY` to browse the 161 source and 161
   generated training images separately.
2. `02_FULL_TRAY_PIPELINE_OVERLAYS` — full photos with tray detections and final outputs.
3. `03_DEFECT_MODEL_OUTPUTS` — per-model overlays and lossless binary masks.
4. `04_DEFECT_MODEL_ERROR_GALLERY` — examples each defect model got wrong.
5. `05_DEFECT_MODEL_FIGURES` — 48-crop model benchmark charts.
6. `06_END_TO_END_FIGURES` — 16-tray/24-tool connected-pipeline charts.
7. `07_METRICS_AND_REPORTS` — exact JSON metrics and readable reports.

Pink/filled regions are segmentation masks. Rectangles are detection boxes.
The existing figures are reviewed-v3/confirmatory results; they are not results
from the prepared v4 augmentation dataset, because v4 training is gated.
"""
    (output / "00_READ_ME_FIRST.md").write_text(readme)
    print(f"Created {output}")
    for name, count in copied.items():
        print(f"{name}: {count} files")


if __name__ == "__main__":
    main()
