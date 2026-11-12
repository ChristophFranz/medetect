"""Build reviewable YOLO/CVAT Hook Sinskey boxes for the redesigned tray."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageOps

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = REPO_ROOT / "ml/annotation/new_tray_manifest.json"
DEFAULT_OUTPUT = REPO_ROOT / "ml/annotation/local/new_tray_detection_candidates"
DEFAULT_SUMMARY = REPO_ROOT / "ml/annotation/new_tray_detection_summary.json"
DEFAULT_CVAT_ZIP = REPO_ROOT / "ml/cvat/new_tray_detection_candidates.zip"
CLASS_NAMES = (
    "chop phaco",
    "forceps macpherson",
    "forceps utrata",
    "hook sinskey",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def detector_boxes(image: Image.Image, tool_count: int) -> tuple[list[list[float]], str]:
    """Locate low-saturation horizontal instrument edges and expand them to boxes."""
    rgb = np.asarray(image.convert("RGB"))
    height, width = rgb.shape[:2]
    analysis_width = 1200
    analysis_height = max(1, round(height * analysis_width / width))
    resized = cv2.resize(rgb, (analysis_width, analysis_height), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(resized, cv2.COLOR_RGB2HSV)
    edges = cv2.Canny(cv2.cvtColor(resized, cv2.COLOR_RGB2GRAY), 60, 160)
    lines = cv2.HoughLinesP(
        edges,
        1,
        np.pi / 360,
        50,
        minLineLength=round(0.21 * analysis_width),
        maxLineGap=round(0.067 * analysis_width),
    )
    candidates: list[dict[str, float]] = []
    if lines is not None:
        for x1, y1, x2, y2 in lines[:, 0]:
            angle = math.degrees(math.atan2(float(y2 - y1), float(x2 - x1)))
            length = math.hypot(float(x2 - x1), float(y2 - y1))
            normalized_y = ((float(y1) + float(y2)) / 2) / analysis_height
            if abs(angle) > 15 or length < 0.25 * analysis_width:
                continue
            samples = np.linspace(0, 1, 100)
            sample_x = np.clip(
                (x1 + (x2 - x1) * samples).astype(int), 0, analysis_width - 1
            )
            sample_y = np.clip(
                (y1 + (y2 - y1) * samples).astype(int), 0, analysis_height - 1
            )
            low_saturation_fraction = float((hsv[sample_y, sample_x, 1] < 65).mean())
            if low_saturation_fraction < 0.5:
                continue
            candidates.append(
                {
                    "x1": float(x1),
                    "y1": float(y1),
                    "x2": float(x2),
                    "y2": float(y2),
                    "normalized_y": normalized_y,
                    "score": length * (0.5 + low_saturation_fraction),
                }
            )

    bands = [(0.40, 0.64), (0.62, 0.84)] if tool_count == 2 else [(0.43, 0.76)]
    fallback_rows = [0.51, 0.72] if tool_count == 2 else [0.63]
    boxes: list[list[float]] = []
    methods = []
    x_scale = width / analysis_width
    y_scale = height / analysis_height
    for (lower, upper), fallback_row in zip(bands, fallback_rows, strict=True):
        in_band = [item for item in candidates if lower <= item["normalized_y"] <= upper]
        if in_band:
            best = max(in_band, key=lambda item: item["score"])
            line_x1, line_x2 = sorted((best["x1"], best["x2"]))
            line_y1, line_y2 = sorted((best["y1"], best["y2"]))
            x1 = max(0.0, (line_x1 - 0.035 * analysis_width) * x_scale)
            x2 = min(float(width), (line_x2 + 0.055 * analysis_width) * x_scale)
            y1 = max(0.0, (line_y1 - 0.035 * analysis_height) * y_scale)
            y2 = min(float(height), (line_y2 + 0.035 * analysis_height) * y_scale)
            boxes.append([x1, y1, x2, y2])
            methods.append("metal_hough")
        else:
            center_y = fallback_row * height
            boxes.append(
                [0.09 * width, center_y - 0.06 * height, 0.83 * width, center_y + 0.06 * height]
            )
            methods.append("fallback")
    return boxes, "+".join(methods)


def xyxy_to_yolo(box: list[float], width: int, height: int) -> str:
    x1, y1, x2, y2 = box
    center_x = (x1 + x2) / (2 * width)
    center_y = (y1 + y2) / (2 * height)
    box_width = (x2 - x1) / width
    box_height = (y2 - y1) / height
    return f"3 {center_x:.8f} {center_y:.8f} {box_width:.8f} {box_height:.8f}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--cvat-zip", type=Path, default=DEFAULT_CVAT_ZIP)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest_path = args.manifest.resolve()
    output = args.output.resolve()
    summary_path = args.summary.resolve()
    cvat_zip = args.cvat_zip.resolve()
    manifest = json.loads(manifest_path.read_text())
    local_root = REPO_ROOT / manifest["local_root"]
    raw_root = local_root / "raw"
    records_by_source: dict[str, list[dict]] = defaultdict(list)
    for record in manifest["images"]:
        records_by_source[record["source_relative_path"]].append(record)

    if output.exists():
        shutil.rmtree(output)
    cvat_root = output / "cvat_dataset"
    image_root = cvat_root / "images/default"
    annotation_root = cvat_root / "annotations"
    overlay_root = output / "overlays"
    yolo_root = output / "yolo"
    for directory in (image_root, annotation_root, overlay_root):
        directory.mkdir(parents=True, exist_ok=True)
    for split in ("train", "valid", "test"):
        (yolo_root / split / "images").mkdir(parents=True, exist_ok=True)
        (yolo_root / split / "labels").mkdir(parents=True, exist_ok=True)

    coco = {
        "info": {
            "description": "Unreviewed redesigned-tray Hook Sinskey detection candidates",
            "version": "new-tray-detection-candidates-v1",
            "date_created": datetime.now(UTC).isoformat(timespec="seconds"),
        },
        "licenses": [],
        "categories": [
            {"id": index + 1, "name": name, "supercategory": "tool"}
            for index, name in enumerate(CLASS_NAMES)
        ],
        "images": [],
        "annotations": [],
    }
    queue = []
    counts: Counter[str] = Counter()
    annotation_id = 1
    for image_id, source_record in enumerate(manifest["sources"], start=1):
        relative = Path(source_record["source_relative_path"])
        source = raw_root / relative
        if not source.is_file():
            raise SystemExit(f"missing copied source image: {source}")
        if sha256_file(source) != source_record["sha256"]:
            raise SystemExit(f"copied source hash mismatch: {source}")
        with Image.open(source) as handle:
            image = ImageOps.exif_transpose(handle).convert("RGB")
        width, height = image.size
        split = source_record["split"]
        target_name = f"{split}__{relative.parent.as_posix().replace('/', '__')}__{relative.name}"
        cvat_target = image_root / target_name
        yolo_target = yolo_root / split / "images" / target_name
        # Persist pixels in their upright orientation.  The row-localization
        # coordinates in the source manifest are defined after EXIF transpose.
        image.save(cvat_target, quality=95, subsampling=0)
        image.save(yolo_target, quality=95, subsampling=0)
        coco["images"].append(
            {
                "id": image_id,
                "file_name": target_name,
                "width": width,
                "height": height,
                "split": split,
                "capture_group": source_record["capture_group"],
                "source_relative_path": relative.as_posix(),
                "review_state": "candidate_unreviewed",
            }
        )
        source_instances = sorted(
            records_by_source[relative.as_posix()],
            key=lambda item: int(item["source_instance_index"]),
        )
        boxes, box_method = detector_boxes(image, len(source_instances))
        label_lines = []
        for record, box in zip(source_instances, boxes, strict=True):
            x1, y1, x2, y2 = box
            coco["annotations"].append(
                {
                    "id": annotation_id,
                    "image_id": image_id,
                    "category_id": 4,
                    "bbox": [x1, y1, x2 - x1, y2 - y1],
                    "area": (x2 - x1) * (y2 - y1),
                    "iscrowd": 0,
                    "source_instance_index": record["source_instance_index"],
                    "review_state": "candidate_unreviewed",
                }
            )
            label_lines.append(xyxy_to_yolo(box, width, height))
            annotation_id += 1
        (yolo_root / split / "labels" / f"{Path(target_name).stem}.txt").write_text(
            "\n".join(label_lines) + "\n"
        )
        overlay = image.copy()
        draw = ImageDraw.Draw(overlay)
        for position, box in enumerate(boxes, start=1):
            draw.rectangle(box, outline=(255, 40, 40), width=12)
            draw.text((box[0] + 12, box[1] + 12), f"hook sinskey {position}", fill=(255, 255, 0))
        overlay.save(overlay_root / f"{Path(target_name).stem}__boxes.jpg", quality=90)
        queue.append(
            {
                "image_id": image_id,
                "file_name": target_name,
                "source_relative_path": relative.as_posix(),
                "expected_instances": len(boxes),
                "candidate_method": box_method,
                "review_state": "candidate_unreviewed",
                "reviewer": None,
                "reviewed_on": None,
                "notes": "",
            }
        )
        counts[f"{split}_images"] += 1
        counts[f"{split}_instances"] += len(boxes)

    coco_path = annotation_root / "instances_default.json"
    queue_path = output / "review_queue.json"
    coco_path.write_text(json.dumps(coco, indent=2) + "\n")
    queue_path.write_text(json.dumps(queue, indent=2) + "\n")
    data_yaml = (
        "path: .\n"
        "train: train/images\n"
        "val: valid/images\n"
        "test: test/images\n\n"
        "names:\n"
        + "".join(f"  {index}: {name}\n" for index, name in enumerate(CLASS_NAMES))
    )
    (yolo_root / "data.yaml").write_text(data_yaml)
    cvat_zip.parent.mkdir(parents=True, exist_ok=True)
    archive = Path(shutil.make_archive(str(cvat_zip.with_suffix("")), "zip", cvat_root))
    summary = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "source_manifest": manifest_path.relative_to(REPO_ROOT).as_posix(),
        "source_dataset_sha256": manifest["source_dataset_sha256"],
        "images": len(coco["images"]),
        "hook_sinskey_instances": len(coco["annotations"]),
        "counts": dict(sorted(counts.items())),
        "class_mapping": {str(index): name for index, name in enumerate(CLASS_NAMES)},
        "candidate_method": "low-saturation horizontal-line localization with deterministic fallback",
        "coco_sha256": sha256_file(coco_path),
        "review_queue_sha256": sha256_file(queue_path),
        "cvat_zip": archive.relative_to(REPO_ROOT).as_posix(),
        "cvat_zip_sha256": sha256_file(archive),
        "local_output": output.relative_to(REPO_ROOT).as_posix(),
        "review_status": "pending",
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"Wrote {summary_path.relative_to(REPO_ROOT)}")
    print(json.dumps(summary["counts"], sort_keys=True))
    print(f"Review ZIP: {archive}")


if __name__ == "__main__":
    main()
