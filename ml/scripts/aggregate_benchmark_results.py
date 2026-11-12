"""Aggregate frozen-test results and generate the Milestone 5 error gallery."""

from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw

from ml.benchmark.metrics import decode_mask
from ml.benchmark.thresholds import mask_area, score_for_area
from ml.data.coco_dataset import FrozenCocoDataset

REPO_ROOT = Path(__file__).resolve().parents[2]
ML_ROOT = REPO_ROOT / "ml"
MODELS = ("legacy_yolo", "detr_detection", "detr_segmentation", "mask_rcnn")
GALLERY = ML_ROOT / "runs/benchmark/error_gallery"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tint(image: Image.Image, mask: np.ndarray, color: tuple[int, int, int], alpha: float) -> None:
    array = np.asarray(image).copy()
    array[mask] = ((1 - alpha) * array[mask] + alpha * np.asarray(color)).astype(
        np.uint8
    )
    image.paste(Image.fromarray(array))


def render_error(
    model: str,
    image: Image.Image,
    target: dict[str, Any],
    record: dict[str, Any],
    threshold: float,
    minimum_area: int | None,
    destination: Path,
) -> None:
    rendered = image.copy()
    segmentation = model in {"detr_segmentation", "mask_rcnn"}
    if segmentation:
        for mask in target["masks"]:
            tint(rendered, mask.numpy().astype(bool), (0, 210, 80), 0.48)
        for score, encoded in zip(
            record["instance_scores"], record["masks"], strict=True
        ):
            if float(score) >= threshold and mask_area(encoded) >= int(minimum_area):
                tint(rendered, decode_mask(encoded), (235, 30, 120), 0.55)
        legend = "GREEN MASK = GROUND TRUTH | PINK MASK = PREDICTION"
    else:
        draw = ImageDraw.Draw(rendered)
        for box in target["boxes"].tolist():
            draw.rectangle(box, outline=(0, 210, 80), width=5)
        for score, box in zip(
            record["instance_scores"], record["boxes"], strict=True
        ):
            if float(score) >= threshold:
                draw.rectangle(box, outline=(235, 30, 80), width=5)
        legend = "GREEN BOX = GROUND TRUTH | RED BOX = PREDICTION"
    score = score_for_area(record, minimum_area)
    prediction = score >= threshold
    canvas = Image.new("RGB", (rendered.width, rendered.height + 72), "black")
    canvas.paste(rendered, (0, 72))
    draw = ImageDraw.Draw(canvas)
    draw.text(
        (10, 12),
        f"MODEL: {model} | LABEL: {str(target['status']).upper()} | "
        f"PREDICTION: {'DEFECTIVE' if prediction else 'HEALTHY'} | SCORE: {score:.3f}",
        fill="white",
    )
    draw.text((10, 42), legend, fill="white")
    destination.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(destination, quality=90)


def report_markdown(results: dict[str, Any]) -> str:
    rows = []
    for model in results["models"]:
        classification = model["classification"]
        task = model.get("detection", model.get("segmentation", {}))
        rows.append(
            f"| {model['model']} | {classification['accuracy']:.3f} | "
            f"{classification['sensitivity']:.3f} | {classification['specificity']:.3f} | "
            f"{classification['f1']:.3f} | {task.get('ap50', float('nan')):.3f} | "
            f"{task.get('map50_95', float('nan')):.3f} | "
            f"{model['operational']['median_latency_ms']:.1f} |"
        )
    return f"""# Hook Sinskey Controlled Benchmark

Status: awaiting Milestone 5 human review.

All operating thresholds were selected on validation data and frozen before each model was evaluated once on the 24-image test split.

| Model | Accuracy | Sensitivity | Specificity | F1 | AP50 | mAP50–95 | Median ms |
|---|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

## Main finding

Mask R-CNN matched the inherited YOLO baseline on image-level accuracy (0.875), sensitivity (1.000), specificity (0.500), and F1 (0.923), while providing the requested tip-defect segmentation. Its test segmentation AP50 was 0.730, mAP50–95 was 0.362, mean IoU was 0.616, and Dice was 0.752.

DETR detection and heads-only DETR segmentation classified every healthy test image as defective at their validation-selected operating points. Their specificities were therefore 0.000. DETR segmentation's full-parameter fine-tune was infeasible on the available 24 GB Apple system, so only its classifier, box predictor, mask head, and box-attention layers were trained; this materially limits a direct architecture comparison.

## Baseline interpretation

The inherited historical YOLO validation references were mAP50 0.8982, mAP50–95 0.5712, precision 0.7625, and recall 0.8518. They are not directly comparable to the authoritative frozen-test results. Standardized test YOLO achieved AP50 0.6051 and mAP50–95 0.2583.

## Important limitation

Defect label remains perfectly confounded with acquisition group: `6-4` images are defective and `6-3` images are healthy. Results describe this internal dataset and cannot establish cross-session, cross-device, or deployment generalization.

## Review material

- Full metrics and bootstrap intervals: `ml/experiments/benchmark_results.json`
- Local error gallery: `ml/runs/benchmark/error_gallery/index.html`
- Green is reviewed ground truth; red/pink is the model prediction.

## Human gate

- Reviewer: pending
- Decision: pending
- Next action: review the report and all failure overlays, then approve expansion, request relabeling/tuning, or stop.
"""


def main() -> None:
    freeze_path = ML_ROOT / "experiments/frozen_thresholds.json"
    freeze = json.loads(freeze_path.read_text())
    dataset = FrozenCocoDataset("test", allow_test=True)
    items = [dataset[index] for index in range(len(dataset))]
    by_id = {target["image_id"]: (image, target) for image, target in items}
    models = []
    gallery_rows = []
    for model in MODELS:
        run_dir = ML_ROOT / "runs/benchmark" / model
        summary_path = run_dir / "test_summary.json"
        predictions_path = run_dir / "test_predictions.jsonl"
        summary = json.loads(summary_path.read_text())
        records = [json.loads(line) for line in predictions_path.read_text().splitlines()]
        if summary["status"] != "complete" or not summary["test_split_accessed_once"]:
            raise SystemExit(f"test evaluation incomplete: {model}")
        if len(records) != 24:
            raise SystemExit(f"unexpected test prediction count: {model}")
        summary["test_summary_sha256"] = sha256(summary_path)
        summary["test_predictions_sha256"] = sha256(predictions_path)
        models.append(summary)
        threshold = float(summary["score_threshold"])
        minimum_area = summary["minimum_mask_area"]
        for record in records:
            image, target = by_id[record["image_id"]]
            truth = target["status"] == "defective"
            score = score_for_area(record, minimum_area)
            predicted = score >= threshold
            if truth == predicted:
                continue
            filename = f"{model}_{len(gallery_rows) + 1:02d}.jpg"
            render_error(
                model,
                image,
                target,
                record,
                threshold,
                minimum_area,
                GALLERY / filename,
            )
            gallery_rows.append(
                {
                    "model": model,
                    "image_id": record["image_id"],
                    "truth": "defective" if truth else "healthy",
                    "prediction": "defective" if predicted else "healthy",
                    "score": score,
                    "image": filename,
                }
            )

    cards = "".join(
        "<article>"
        f"<h3>{html.escape(row['model'])}: {html.escape(row['truth'])} → "
        f"{html.escape(row['prediction'])}</h3>"
        f"<img src=\"{html.escape(row['image'])}\" loading=\"lazy\">"
        f"<p><code>{html.escape(row['image_id'])}</code>; score {row['score']:.3f}</p>"
        "</article>"
        for row in gallery_rows
    )
    GALLERY.mkdir(parents=True, exist_ok=True)
    (GALLERY / "index.html").write_text(
        "<!doctype html><meta charset='utf-8'><title>Benchmark errors</title>"
        "<style>body{font:15px system-ui;margin:24px;background:#eee}main{display:grid;"
        "grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:16px}article{background:"
        "white;padding:12px}img{max-width:100%;height:auto}code{overflow-wrap:anywhere}</style>"
        "<h1>Hook Sinskey frozen-test errors</h1><p>Every false positive and false "
        "negative at the validation-frozen operating points.</p><main>"
        + cards
        + "</main>"
    )
    result = {
        "schema_version": 1,
        "event": "controlled_benchmark",
        "date": "2026-09-25",
        "tool": "hook_sinskey",
        "dataset_version": freeze["dataset_version"],
        "dataset_sha256": freeze["dataset_sha256"],
        "threshold_freeze": freeze_path.relative_to(REPO_ROOT).as_posix(),
        "threshold_freeze_sha256": sha256(freeze_path),
        "test_images": 24,
        "test_evaluations_per_model": 1,
        "models": models,
        "error_gallery": "ml/runs/benchmark/error_gallery/index.html",
        "error_count": len(gallery_rows),
        "status": "awaiting_human_review",
    }
    output = ML_ROOT / "experiments/benchmark_results.json"
    output.write_text(json.dumps(result, indent=2) + "\n")
    (ML_ROOT / "BENCHMARK_REPORT.md").write_text(report_markdown(result))
    print(f"Wrote {output.relative_to(REPO_ROOT)}")
    print(f"Errors rendered: {len(gallery_rows)}")


if __name__ == "__main__":
    main()
