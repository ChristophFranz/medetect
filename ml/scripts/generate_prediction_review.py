"""Create the deterministic Milestone 4 validation prediction review package."""

from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from pycocotools import mask as mask_utils

from ml.data.coco_dataset import FrozenCocoDataset
from ml.models.device import seed_everything
from ml.models.factory import build_adapter

REPO_ROOT = Path(__file__).resolve().parents[2]
ML_ROOT = REPO_ROOT / "ml"
OUTPUT_ROOT = ML_ROOT / "runs/prediction_review"
MODELS = ("legacy_yolo", "detr_detection", "detr_segmentation", "mask_rcnn")
CHECKPOINTS = {
    model: ML_ROOT / "runs/smoke" / model / "checkpoint.pt"
    for model in MODELS
    if model != "legacy_yolo"
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def select_review_sample(dataset: FrozenCocoDataset) -> list[int]:
    selected = []
    for status in ("defective", "healthy"):
        matching = [
            index
            for index in range(len(dataset))
            if dataset[index][1]["status"] == status
        ]
        if len(matching) < 5:
            raise RuntimeError(f"validation split has fewer than five {status} images")
        selected.extend(matching[:5])
    return selected


def decode_prediction_mask(encoded: dict[str, object]) -> np.ndarray:
    rle = {"size": encoded["size"], "counts": encoded["counts"].encode("ascii")}
    return mask_utils.decode(rle).astype(bool)


def tint(image: Image.Image, mask: np.ndarray, color: tuple[int, int, int], alpha: float) -> None:
    array = np.asarray(image).copy()
    array[mask] = ((1 - alpha) * array[mask] + alpha * np.asarray(color)).astype(
        np.uint8
    )
    image.paste(Image.fromarray(array))


def render_overlay(
    image: Image.Image,
    target: dict[str, object],
    prediction: dict[str, object],
    destination: Path,
) -> None:
    rendered = image.copy()
    segmentation_model = prediction["model"] in {"detr_segmentation", "mask_rcnn"}
    if segmentation_model:
        for mask in target["masks"]:
            tint(rendered, mask.numpy().astype(bool), (0, 210, 80), 0.48)
        for encoded in prediction["masks"]:
            tint(rendered, decode_prediction_mask(encoded), (235, 30, 120), 0.55)
    else:
        draw = ImageDraw.Draw(rendered)
        for box in target["boxes"].tolist():
            draw.rectangle(box, outline=(0, 210, 80), width=5)
        for box in prediction["boxes"]:
            draw.rectangle(box, outline=(235, 30, 80), width=5)

    banner_height = 72
    canvas = Image.new("RGB", (rendered.width, rendered.height + banner_height), "black")
    canvas.paste(rendered, (0, banner_height))
    draw = ImageDraw.Draw(canvas)
    model_prediction = "DEFECTIVE" if prediction["defective"] else "NONE (HEALTHY)"
    summary = (
        f"MODEL: {prediction['model']} | REVIEWED LABEL: {str(target['status']).upper()} "
        f"| MODEL PREDICTION: {model_prediction} | CONFIDENCE: {prediction['confidence']:.3f}"
    )
    if segmentation_model:
        legend = (
            f"GREEN MASK = REVIEWED GROUND TRUTH ({len(target['masks'])})   |   "
            f"PINK MASK = MODEL PREDICTION ({len(prediction['masks'])})   |   "
            "NO BOXES ARE DISPLAYED"
        )
    else:
        legend = (
            f"GREEN BOX = REVIEWED GROUND TRUTH ({len(target['boxes'])})   |   "
            f"RED BOX = MODEL PREDICTION ({len(prediction['boxes'])})   |   "
            "NO MASKS ARE DISPLAYED"
        )
    draw.text((10, 12), summary, fill=(255, 255, 255))
    draw.text((10, 42), legend, fill=(255, 255, 255))
    destination.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(destination, quality=90)


def write_html(rows: list[dict[str, object]]) -> None:
    cards = []
    for row in rows:
        cards.append(
            "<article>"
            f"<h3>{html.escape(str(row['model']))} — {html.escape(str(row['status']))}</h3>"
            f"<img src=\"{html.escape(str(row['overlay']))}\" loading=\"lazy\">"
            f"<p><code>{html.escape(str(row['image_id']))}</code><br>"
            f"Prediction: {html.escape(str(row['prediction']))}; "
            f"confidence {float(row['confidence']):.3f}</p>"
            "</article>"
        )
    document = f"""<!doctype html>
<meta charset="utf-8">
<title>Hook Sinskey Milestone 4 Prediction Review</title>
<style>
body {{ font: 15px system-ui; margin: 24px; background: #f5f5f5; color: #171717; }}
.notice {{ max-width: 1000px; padding: 14px; background: #fff3cd; border: 1px solid #e0bb4d; }}
.legend {{ color: #444; }}
main {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 18px; }}
article {{ background: white; padding: 12px; border-radius: 8px; box-shadow: 0 1px 5px #bbb; }}
img {{ display: block; max-width: 100%; height: auto; }}
code {{ overflow-wrap: anywhere; }}
</style>
<h1>Hook Sinskey Milestone 4 Prediction Review</h1>
<p class="notice"><strong>Mechanical smoke-check outputs only.</strong> These models were run for five epochs on two training images. Do not interpret these predictions as benchmark performance.</p>
<p class="legend">Detection: green boxes are reviewed ground truth and red boxes are model predictions. Segmentation: green masks are reviewed ground truth and pink masks are model predictions; segmentation boxes are deliberately hidden. Review five defective and five healthy validation images for each model.</p>
<main>{''.join(cards)}</main>
"""
    (OUTPUT_ROOT / "index.html").write_text(document)


def main() -> None:
    seed_everything(42)
    dataset = FrozenCocoDataset("valid")
    indices = select_review_sample(dataset)
    sample = [dataset[index] for index in indices]
    sample_record = {
        "schema_version": 1,
        "split": "valid",
        "selection": "first five by stable COCO image ID for each status",
        "seed": 42,
        "test_split_accessed": False,
        "images": [
            {"image_id": target["image_id"], "status": target["status"]}
            for _, target in sample
        ],
    }
    (ML_ROOT / "experiments/milestone4_review_sample.json").write_text(
        json.dumps(sample_record, indent=2) + "\n"
    )

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    rows = []
    model_records = []
    for model_name in MODELS:
        adapter = build_adapter(model_name, device="auto")
        checkpoint = CHECKPOINTS.get(model_name)
        if checkpoint is not None:
            if not checkpoint.is_file():
                raise RuntimeError(f"missing smoke checkpoint: {checkpoint}")
            adapter.load_checkpoint(checkpoint)

        predictions = []
        for position, (image, target) in enumerate(sample, start=1):
            prediction = adapter.predict(str(target["image_id"]), image).to_dict()
            predictions.append(prediction)
            overlay = Path("overlays") / model_name / f"{position:02d}.jpg"
            render_overlay(image, target, prediction, OUTPUT_ROOT / overlay)
            rows.append(
                {
                    "model": model_name,
                    "image_id": target["image_id"],
                    "status": target["status"],
                    "prediction": "defective" if prediction["defective"] else "healthy",
                    "confidence": prediction["confidence"],
                    "overlay": overlay.as_posix(),
                }
            )
        prediction_path = OUTPUT_ROOT / f"{model_name}.jsonl"
        prediction_path.write_text(
            "\n".join(json.dumps(item, separators=(",", ":")) for item in predictions)
            + "\n"
        )
        model_records.append(
            {
                "model": model_name,
                "checkpoint": (
                    checkpoint.relative_to(REPO_ROOT).as_posix()
                    if checkpoint is not None
                    else "ml/artifacts/legacy/hook_sinskey/yolov8n_best.pt"
                ),
                "checkpoint_sha256": sha256(
                    checkpoint
                    if checkpoint is not None
                    else REPO_ROOT
                    / "ml/artifacts/legacy/hook_sinskey/yolov8n_best.pt"
                ),
                "predictions": prediction_path.relative_to(REPO_ROOT).as_posix(),
                "predictions_sha256": sha256(prediction_path),
                "images": 10,
            }
        )

    write_html(rows)
    manifest = {
        "schema_version": 1,
        "event": "milestone_4_prediction_review",
        "date": "2026-09-24",
        "tool": "hook_sinskey",
        "split": "valid",
        "defective_images": 5,
        "healthy_images": 5,
        "models": model_records,
        "test_split_accessed": False,
        "purpose": "human review of mechanics; smoke checkpoints are not performance evidence",
        "local_index": "ml/runs/prediction_review/index.html",
        "reviewer": None,
        "review_status": "awaiting_human_review",
    }
    output = ML_ROOT / "experiments/prediction_review_manifest.json"
    output.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wrote {output.relative_to(REPO_ROOT)}")
    print(f"Open {manifest['local_index']}")


if __name__ == "__main__":
    main()
