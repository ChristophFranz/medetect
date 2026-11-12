"""Create defect-tip inputs from retrained tray-detector predictions."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

REPO_ROOT = Path(__file__).resolve().parents[2]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def metallic_point(crop: Image.Image, x_fraction: float) -> list[int]:
    """Find the locally brightest low-saturation row at a distal x position."""
    rgb = np.asarray(crop.convert("RGB"))
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    height, width = hsv.shape[:2]
    x = min(width - 1, max(0, round(x_fraction * width)))
    start = round(0.42 * height)
    stop = round(0.76 * height)
    half_window = max(2, round(0.004 * width))
    left = max(0, x - half_window)
    right = min(width, x + half_window + 1)
    scores = (
        hsv[start:stop, left:right, 2].astype(np.float32).mean(axis=1)
        - hsv[start:stop, left:right, 1].astype(np.float32).mean(axis=1)
    )
    y = start + int(np.argmax(scores))
    return [x, y]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-manifest", type=Path,
        default=REPO_ROOT / "ml/annotation/new_tray_manifest.json",
    )
    parser.add_argument(
        "--predictions", type=Path,
        default=REPO_ROOT / "ml/runs/tray_yolo/presentation_predictions/predictions.jsonl",
    )
    parser.add_argument(
        "--candidate-coco", type=Path,
        default=REPO_ROOT / "ml/annotation/local/new_tray_detection_candidates/cvat_dataset/annotations/instances_default.json",
    )
    parser.add_argument(
        "--output-root", type=Path,
        default=REPO_ROOT / "ml/data/local/hook_sinskey/new_tray_v2/model_tip_crops",
    )
    parser.add_argument(
        "--output-manifest", type=Path,
        default=REPO_ROOT / "ml/annotation/new_tray_model_cropped_manifest.json",
    )
    parser.add_argument(
        "--tip-orientations",
        type=Path,
        default=REPO_ROOT / "ml/annotation/new_tray_tip_orientations.json",
        help="Per-instance tip-side decisions. Left-facing tips are mirrored to canonical tip-right crops.",
    )
    parser.add_argument(
        "--prefer-coco-boxes",
        action="store_true",
        help="Use the supplied COCO boxes as authoritative instead of tray-model predictions.",
    )
    args = parser.parse_args()
    source_manifest = json.loads(args.source_manifest.read_text())
    orientation_config = json.loads(args.tip_orientations.read_text())
    default_tip_side = orientation_config["default_tip_side"]
    tip_side_overrides = orientation_config.get("overrides", {})
    if default_tip_side not in {"left", "right"}:
        raise ValueError(f"invalid default_tip_side: {default_tip_side}")
    predictions = [json.loads(line) for line in args.predictions.read_text().splitlines() if line]
    coco = json.loads(args.candidate_coco.read_text())
    predicted_by_key = {}
    for image_prediction in predictions:
        for instance in image_prediction["matched_instances"]:
            predicted_by_key[(image_prediction["source_relative_path"], int(instance["source_instance_index"]))] = instance
    coco_images = {item["id"]: item for item in coco["images"]}
    fallback_by_key = {}
    for annotation in coco["annotations"]:
        image = coco_images[annotation["image_id"]]
        x, y, width, height = annotation["bbox"]
        fallback_by_key[(image["source_relative_path"], int(annotation["source_instance_index"]))] = [
            x, y, x + width, y + height
        ]

    output_root = args.output_root.resolve()
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True)
    raw_root = REPO_ROOT / source_manifest["local_root"] / "raw"
    records_by_source: dict[str, list[dict]] = defaultdict(list)
    for record in source_manifest["images"]:
        records_by_source[record["source_relative_path"]].append(record)
    output_records = []
    counts: Counter[str] = Counter()
    for relative, records in sorted(records_by_source.items()):
        with Image.open(raw_root / relative) as handle:
            image = ImageOps.exif_transpose(handle).convert("RGB")
        for record in sorted(records, key=lambda item: int(item["source_instance_index"])):
            key = (relative, int(record["source_instance_index"]))
            prediction = predicted_by_key.get(key)
            if prediction and not args.prefer_coco_boxes:
                box = prediction["box_xyxy"]
                method = "retrained_yolo_prediction"
                confidence = prediction["confidence"]
            else:
                box = fallback_by_key[key]
                method = (
                    "human_reviewed_coco_box"
                    if args.prefer_coco_boxes
                    else "candidate_box_fallback_after_missed_detection"
                )
                confidence = None
            x1, y1, x2, y2 = box
            box_width = x2 - x1
            box_height = y2 - y1
            tip_side = tip_side_overrides.get(record["image_id"], default_tip_side)
            if tip_side not in {"left", "right"}:
                raise ValueError(f"invalid tip side for {record['image_id']}: {tip_side}")
            # Keep the distal 62% with modest context. Left-facing tools are
            # mirrored after cropping so downstream inputs remain tip-right.
            if tip_side == "right":
                left = max(0, round(x1 + 0.38 * box_width))
                right = min(image.width, round(x2 + 0.03 * image.width))
            else:
                left = max(0, round(x1 - 0.03 * image.width))
                right = min(image.width, round(x2 - 0.38 * box_width))
            top = max(0, round(y1 - 0.10 * box_height))
            bottom = min(image.height, round(y2 + 0.10 * box_height))
            crop = image.crop((left, top, right, bottom))
            canonicalized_by_flip = tip_side == "left"
            if canonicalized_by_flip:
                crop = ImageOps.mirror(crop)
            target = output_root / f"{record['image_id']}.jpg"
            crop.save(target, quality=95, subsampling=0)
            # Keep positive prompts on the cone/shaft before the defect. A
            # severely bent tip may leave the frame's right-side scan rows.
            positive_points = [metallic_point(crop, fraction) for fraction in (0.60, 0.65)]
            point_rows = [point[1] for point in positive_points]
            prompt = [
                round(0.58 * crop.width),
                max(0, min(point_rows) - round(0.36 * crop.height)),
                round(0.98 * crop.width),
                min(crop.height - 1, max(point_rows) + round(0.36 * crop.height)),
            ]
            middle_y = round(sum(point_rows) / len(point_rows))
            prompt_points = positive_points + [
                [round(0.76 * crop.width), max(0, middle_y - round(0.40 * crop.height))],
                [round(0.76 * crop.width), min(crop.height - 1, middle_y + round(0.40 * crop.height))],
            ]
            updated = dict(record)
            updated.update(
                {
                    "image_path": target.relative_to(REPO_ROOT).as_posix(),
                    "image_sha256": sha256(target),
                    "width": crop.width,
                    "height": crop.height,
                    "legacy_defect_boxes_xyxy": [prompt] if record["status"] == "defective" else [],
                    "sam2_prompt_points": prompt_points if record["status"] == "defective" else [],
                    "sam2_prompt_point_labels": [1, 1, 0, 0] if record["status"] == "defective" else [],
                    "legacy_defect_instance_count": 1 if record["status"] == "defective" else 0,
                    "max_normalized_defect_box_area": (
                        ((prompt[2] - prompt[0]) * (prompt[3] - prompt[1])) / (crop.width * crop.height)
                        if record["status"] == "defective" else 0.0
                    ),
                    "source_crop_xyxy": [left, top, right, bottom],
                    "source_tip_side": tip_side,
                    "canonicalized_by_horizontal_flip": canonicalized_by_flip,
                    "tip_orientation_manifest": args.tip_orientations.relative_to(REPO_ROOT).as_posix(),
                    "localization_method": method,
                    "tray_detection_confidence": confidence,
                    "review_state": (
                        "box_human_reviewed_mask_pending"
                        if args.prefer_coco_boxes
                        else "provisional_unreviewed"
                    ),
                }
            )
            output_records.append(updated)
            counts[method] += 1
            counts[f"{record['split']}_{record['status']}"] += 1
    manifest = dict(source_manifest)
    manifest.update(
        {
            "package_name": (
                "hook_sinskey_model_cropped_new_tray_v3_reviewed_boxes"
                if args.prefer_coco_boxes
                else "hook_sinskey_model_cropped_new_tray_v2_provisional"
            ),
            "images": output_records,
            "review_status": (
                "tray_boxes_human_reviewed_defect_masks_pending"
                if args.prefer_coco_boxes
                else "provisional_unreviewed_review_bypassed_for_presentation"
            ),
            "crop_pipeline": (
                "human-reviewed tray COCO box -> orientation-aware distal 62% tip crop "
                "-> canonical tip-right normalization -> SAM2 prompt"
                if args.prefer_coco_boxes
                else "retrained tray YOLO -> distal 62% tip crop -> SAM2 prompt"
            ),
            "crop_counts": dict(sorted(counts.items())),
        }
    )
    args.output_manifest.resolve().write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest["crop_counts"], indent=2))


if __name__ == "__main__":
    main()
