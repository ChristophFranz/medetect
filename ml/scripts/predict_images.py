"""Run one or more frozen benchmark models on arbitrary local images.

This command is deliberately separate from the frozen-test evaluator. It loads the
approved validation-selected operating points but never opens a benchmark split.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from pycocotools import mask as mask_utils

from ml.models.device import seed_everything
from ml.models.factory import build_adapter

REPO_ROOT = Path(__file__).resolve().parents[2]
ML_ROOT = REPO_ROOT / "ml"
MODELS = ("legacy_yolo", "detr_detection", "detr_segmentation", "mask_rcnn")
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Predict Hook Sinskey tip defects in arbitrary local images."
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        help="Image files or directories (directories are searched recursively).",
    )
    parser.add_argument(
        "--model",
        action="append",
        choices=MODELS,
        dest="models",
        help="Model to run; repeat for several. Defaults to mask_rcnn.",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", choices=("auto", "mps", "cpu"), default="auto")
    return parser.parse_args()


def discover_images(inputs: list[Path]) -> list[Path]:
    images: set[Path] = set()
    for supplied in inputs:
        path = supplied.expanduser().resolve()
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
            images.add(path)
        elif path.is_dir():
            images.update(
                candidate.resolve()
                for candidate in path.rglob("*")
                if candidate.is_file() and candidate.suffix.lower() in IMAGE_SUFFIXES
            )
        else:
            raise ValueError(f"not a supported image or directory: {supplied}")
    if not images:
        raise ValueError("no supported images found")
    return sorted(images)


def load_operating_points() -> dict[str, dict[str, object]]:
    path = ML_ROOT / "experiments/frozen_thresholds.json"
    payload = json.loads(path.read_text())
    if payload.get("status") != "frozen_before_test":
        raise RuntimeError(f"invalid frozen operating-point record: {path}")
    return {str(item["model"]): item for item in payload["models"]}


def build_frozen_adapter(model_name: str, device: str, operating_point: dict[str, object]):
    checkpoint = REPO_ROOT / str(operating_point["checkpoint"])
    if not checkpoint.is_file():
        raise FileNotFoundError(f"checkpoint missing: {checkpoint}")
    adapter = build_adapter(model_name, device=device)
    threshold = float(operating_point["score_threshold"])
    if model_name == "legacy_yolo":
        adapter.confidence_threshold = threshold
    else:
        adapter.load_checkpoint(checkpoint)
        adapter.score_threshold = threshold
    minimum_area = operating_point.get("minimum_mask_area")
    if minimum_area is not None and hasattr(adapter, "minimum_mask_area"):
        adapter.minimum_mask_area = int(minimum_area)
    return adapter


def decode_mask(encoded: dict[str, object]) -> np.ndarray:
    rle = {"size": encoded["size"], "counts": str(encoded["counts"]).encode("ascii")}
    return mask_utils.decode(rle).astype(bool)


def safe_stem(path: Path) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", path.stem).strip("-.")
    return cleaned or "image"


def render_prediction(
    image: Image.Image, prediction: dict[str, object], destination: Path
) -> None:
    rendered = image.convert("RGB")
    segmentation = prediction["model"] in {"detr_segmentation", "mask_rcnn"}
    if segmentation:
        array = np.asarray(rendered).copy()
        for encoded in prediction["masks"]:
            mask = decode_mask(encoded)
            color = np.asarray((235, 30, 120))
            array[mask] = (0.45 * array[mask] + 0.55 * color).astype(np.uint8)
        rendered = Image.fromarray(array)
    else:
        draw = ImageDraw.Draw(rendered)
        for box, score in zip(
            prediction["boxes"], prediction["instance_scores"], strict=True
        ):
            draw.rectangle(box, outline=(235, 30, 80), width=5)
            draw.text((box[0] + 4, max(2, box[1] - 14)), f"{score:.3f}", fill=(235, 30, 80))

    banner_height = 54
    canvas = Image.new("RGB", (rendered.width, rendered.height + banner_height), "black")
    canvas.paste(rendered, (0, banner_height))
    label = "DEFECTIVE" if prediction["defective"] else "HEALTHY / NO DEFECT"
    legend = "pink mask" if segmentation else "red box"
    ImageDraw.Draw(canvas).text(
        (10, 10),
        f"{prediction['model']} | {label} | confidence {prediction['confidence']:.3f} | {legend} = prediction",
        fill=(255, 255, 255),
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(destination, quality=92)


def write_raw_masks(
    prediction: dict[str, object], destination: Path, image_size: tuple[int, int]
) -> dict[str, object] | None:
    if prediction["model"] not in {"detr_segmentation", "mask_rcnn"}:
        return None
    destination.mkdir(parents=True, exist_ok=True)
    decoded = [decode_mask(encoded) for encoded in prediction["masks"]]
    if decoded:
        union = np.logical_or.reduce(decoded)
    else:
        union = np.zeros((image_size[1], image_size[0]), dtype=bool)
    instance_paths = []
    for index, mask in enumerate(decoded, start=1):
        path = destination / f"instance_{index:03d}.png"
        Image.fromarray(mask.astype(np.uint8) * 255, mode="L").save(path)
        instance_paths.append(str(path))
    union_path = destination / "union.png"
    Image.fromarray(union.astype(np.uint8) * 255, mode="L").save(union_path)
    return {"union": str(union_path), "instances": instance_paths}


def main() -> None:
    args = parse_args()
    seed_everything(42)
    images = discover_images(args.inputs)
    models = args.models or ["mask_rcnn"]
    output_root = args.output.expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    operating_points = load_operating_points()

    manifest_models = []
    for model_name in models:
        adapter = build_frozen_adapter(model_name, args.device, operating_points[model_name])
        records = []
        model_dir = output_root / model_name
        model_dir.mkdir(parents=True, exist_ok=True)
        for index, path in enumerate(images, start=1):
            with Image.open(path) as opened:
                image = opened.convert("RGB")
            record = adapter.predict(path.name, image).to_dict()
            record["source_path"] = str(path)
            records.append(record)
            output_stem = f"{index:04d}_{safe_stem(path)}"
            overlay = model_dir / "overlays" / f"{output_stem}.jpg"
            render_prediction(image, record, overlay)
            mask_outputs = write_raw_masks(
                record, model_dir / "masks" / output_stem, image.size
            )
            if mask_outputs is not None:
                record["mask_outputs"] = mask_outputs
            print(
                json.dumps(
                    {
                        "model": model_name,
                        "image": index,
                        "total": len(images),
                        "prediction": "defective" if record["defective"] else "healthy",
                        "confidence": round(float(record["confidence"]), 4),
                    }
                ),
                flush=True,
            )
        predictions = model_dir / "predictions.jsonl"
        predictions.write_text(
            "\n".join(json.dumps(record, separators=(",", ":")) for record in records)
            + "\n"
        )
        manifest_models.append(
            {
                "model": model_name,
                "checkpoint": operating_points[model_name]["checkpoint"],
                "score_threshold": operating_points[model_name]["score_threshold"],
                "minimum_mask_area": operating_points[model_name]["minimum_mask_area"],
                "predictions": str(predictions),
                "overlays": str(model_dir / "overlays"),
                "raw_masks": (
                    str(model_dir / "masks")
                    if model_name in {"detr_segmentation", "mask_rcnn"}
                    else None
                ),
            }
        )

    manifest = {
        "schema_version": 1,
        "purpose": "ad-hoc inference; not benchmark evaluation",
        "images": [str(path) for path in images],
        "models": manifest_models,
    }
    (output_root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Results: {output_root}")


if __name__ == "__main__":
    main()
