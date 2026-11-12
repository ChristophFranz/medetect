"""Inventory redesigned-tray photos and create Hook Sinskey tip crops.

The source folders provide image/instance labels.  They do not provide pixel
coordinates, so this script uses the standardized horizontal tray layout to
find one or two instrument rows and makes reviewable tip crops.  It never
modifies the Desktop source collection.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageOps

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = Path("/Users/christophcuan/Desktop/New Hook Sinksey Training Photos")
DEFAULT_LOCAL_ROOT = REPO_ROOT / "ml/data/local/hook_sinskey/new_tray_v2"
DEFAULT_MANIFEST = REPO_ROOT / "ml/annotation/new_tray_manifest.json"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
TWO_TOOL_SOURCE_EXCEPTIONS = {
    "One Tool Dry/Defect/IMG_1667.jpeg": ["defective", "healthy"],
    "One Tool Dry/Defect/IMG_1668.jpeg": ["defective", "healthy"],
    "One Tool Dry/Defect/IMG_1670.jpeg": ["defective", "healthy"],
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_fraction(value: str) -> float:
    integer = int(hashlib.sha256(value.encode()).hexdigest()[:16], 16)
    return integer / float(0xFFFFFFFFFFFFFFFF)


def parse_number(path: Path) -> int:
    match = re.search(r"(\d+)$", path.stem)
    if not match:
        raise ValueError(f"image name has no numeric suffix: {path.name}")
    return int(match.group(1))


def folder_rule(path: Path, source: Path) -> tuple[int, list[str]]:
    relative = path.relative_to(source)
    exception = TWO_TOOL_SOURCE_EXCEPTIONS.get(relative.as_posix())
    if exception is not None:
        return 2, exception
    condition, label = relative.parts[:2]
    tool_count = 2 if condition.startswith("Two Tools") else 1
    if tool_count == 1:
        statuses = ["healthy" if label == "Non-Defect" else "defective"]
    elif label == "Non-Defect + Defect":
        # The collection convention places the defective instrument on top.
        statuses = ["defective", "healthy"]
    elif label == "Defect2":
        statuses = ["defective", "defective"]
    else:
        raise ValueError(f"unsupported source label folder: {relative.parent}")
    return tool_count, statuses


def horizontal_line_rows(image: Image.Image, tool_count: int) -> tuple[list[float], str]:
    """Return normalized y coordinates for horizontal instrument rows."""
    rgb = np.asarray(image.convert("RGB"))
    height, width = rgb.shape[:2]
    analysis_width = 1200
    resized = cv2.resize(
        rgb,
        (analysis_width, max(1, round(height * analysis_width / width))),
        interpolation=cv2.INTER_AREA,
    )
    gray = cv2.cvtColor(resized, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 60, 160)
    lines = cv2.HoughLinesP(
        edges,
        1,
        np.pi / 180,
        80,
        minLineLength=round(0.23 * analysis_width),
        maxLineGap=round(0.06 * analysis_width),
    )
    candidates: list[tuple[float, float]] = []
    analysis_height = resized.shape[0]
    if lines is not None:
        for x1, y1, x2, y2 in lines[:, 0]:
            angle = abs(math.degrees(math.atan2(float(y2 - y1), float(x2 - x1))))
            normalized_y = ((float(y1) + float(y2)) / 2) / analysis_height
            length = math.hypot(float(x2 - x1), float(y2 - y1))
            if angle > 15:
                continue
            if min(x1, x2) >= 0.42 * analysis_width:
                continue
            if max(x1, x2) <= 0.58 * analysis_width:
                continue
            candidates.append((normalized_y, length))

    bands = [(0.43, 0.61), (0.64, 0.81)] if tool_count == 2 else [(0.48, 0.74)]
    fallbacks = [0.51, 0.72] if tool_count == 2 else [0.63]
    rows = []
    methods = []
    for (lower, upper), fallback in zip(bands, fallbacks, strict=True):
        band_candidates = [(y, weight) for y, weight in candidates if lower <= y <= upper]
        if not band_candidates:
            rows.append(fallback)
            methods.append("fallback")
            continue
        bin_width = 0.02
        bins: dict[int, float] = defaultdict(float)
        for y, weight in band_candidates:
            bins[int((y - lower) / bin_width)] += weight
        best_bin = max(bins, key=bins.get)
        selected = [
            (y, weight)
            for y, weight in band_candidates
            if int((y - lower) / bin_width) == best_bin
        ]
        row = sum(y * weight for y, weight in selected) / sum(
            weight for _, weight in selected
        )
        rows.append(row)
        methods.append("hough")
    return rows, "+".join(methods)


def clamp(value: int, lower: int, upper: int) -> int:
    return max(lower, min(value, upper))


def crop_geometry(image: Image.Image, row: float) -> tuple[tuple[int, int, int, int], list[float]]:
    width, height = image.size
    left = round(0.43 * width)
    right = round(0.88 * width)
    center_y = round(row * height)
    half_height = round(0.10 * height)
    top = clamp(center_y - half_height, 0, height - 2)
    bottom = clamp(center_y + half_height, top + 1, height)
    crop_width = right - left
    crop_height = bottom - top
    # Prompt only the distal wire/tip, not the normal handle or background.
    prompt = [
        float(round(0.40 * crop_width)),
        float(round(0.23 * crop_height)),
        float(round(0.96 * crop_width)),
        float(round(0.77 * crop_height)),
    ]
    return (left, top, right, bottom), prompt


def assign_splits(paths: list[Path], source: Path, burst_size: int) -> dict[str, str]:
    """Assign whole contiguous capture bursts to deterministic T/V/T splits."""
    groups: dict[str, list[Path]] = defaultdict(list)
    by_folder: dict[str, list[Path]] = defaultdict(list)
    for path in paths:
        folder = path.parent.relative_to(source).as_posix()
        by_folder[folder].append(path)
    for folder, members in by_folder.items():
        ordered = sorted(members, key=parse_number)
        for position, path in enumerate(ordered):
            group = f"{folder}/burst-{position // burst_size:02d}"
            groups[group].append(path)

    group_splits: dict[str, str] = {}
    for folder in sorted(by_folder):
        folder_groups = sorted(group for group in groups if group.startswith(f"{folder}/"))
        # Stable ranking avoids adjacent bursts systematically falling into the same split.
        ranked = sorted(folder_groups, key=stable_fraction)
        count = len(ranked)
        test_count = 1 if count >= 3 else 0
        valid_count = 1 if count >= 2 else 0
        for index, group in enumerate(ranked):
            if index < test_count:
                group_splits[group] = "test"
            elif index < test_count + valid_count:
                group_splits[group] = "valid"
            else:
                group_splits[group] = "train"

    result = {}
    for group, members in groups.items():
        for path in members:
            result[path.as_posix()] = group_splits[group]
    return result


def burst_id(path: Path, source: Path, burst_size: int, paths: list[Path]) -> str:
    folder = path.parent.relative_to(source).as_posix()
    ordered = sorted((item for item in paths if item.parent == path.parent), key=parse_number)
    position = ordered.index(path)
    return f"{folder}/burst-{position // burst_size:02d}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--local-root", type=Path, default=DEFAULT_LOCAL_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--burst-size", type=int, default=4)
    parser.add_argument("--no-copy-raw", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = args.source.expanduser().resolve()
    local_root = args.local_root.resolve()
    manifest_path = args.manifest.resolve()
    if not source.is_dir():
        raise SystemExit(f"source collection not found: {source}")
    paths = sorted(
        path
        for path in source.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )
    if not paths:
        raise SystemExit("source collection contains no supported images")
    if args.burst_size < 1:
        raise SystemExit("--burst-size must be positive")

    raw_root = local_root / "raw"
    crop_root = local_root / "tip_crops"
    audit_root = local_root / "crop_audit"
    if crop_root.exists():
        shutil.rmtree(crop_root)
    if audit_root.exists():
        shutil.rmtree(audit_root)
    crop_root.mkdir(parents=True)
    audit_root.mkdir(parents=True)
    split_by_path = assign_splits(paths, source, args.burst_size)

    records = []
    source_records = []
    counts: Counter[str] = Counter()
    dataset_digest = hashlib.sha256()
    for source_index, path in enumerate(paths, start=1):
        relative = path.relative_to(source)
        source_hash = sha256_file(path)
        source_size = path.stat().st_size
        dataset_digest.update(f"{relative.as_posix()}\0{source_size}\0{source_hash}\n".encode())
        if not args.no_copy_raw:
            raw_target = raw_root / relative
            raw_target.parent.mkdir(parents=True, exist_ok=True)
            if not raw_target.is_file() or sha256_file(raw_target) != source_hash:
                shutil.copy2(path, raw_target)
        image = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
        tool_count, statuses = folder_rule(path, source)
        rows, localization_method = horizontal_line_rows(image, tool_count)
        split = split_by_path[path.as_posix()]
        group = burst_id(path, source, args.burst_size, paths)
        audit = image.copy()
        draw = ImageDraw.Draw(audit)
        source_crop_ids = []
        for instance_index, (row, status) in enumerate(zip(rows, statuses, strict=True), start=1):
            crop_box, prompt = crop_geometry(image, row)
            crop = image.crop(crop_box)
            crop_id = f"newtray_{path.stem.lower()}_tool{instance_index}"
            crop_name = f"{crop_id}.jpg"
            crop_path = crop_root / crop_name
            crop.save(crop_path, quality=95, subsampling=0)
            crop_hash = sha256_file(crop_path)
            source_crop_ids.append(crop_id)
            counts[f"{split}_images"] += 1
            counts[f"{split}_{status}"] += 1
            counts[status] += 1
            draw.rectangle(crop_box, outline=(255, 220, 0), width=12)
            draw.text((crop_box[0] + 12, crop_box[1] + 12), f"{instance_index}: {status}", fill=(255, 0, 0))
            records.append(
                {
                    "image_id": crop_id,
                    "image_path": crop_path.relative_to(REPO_ROOT).as_posix(),
                    "image_sha256": crop_hash,
                    "width": crop.width,
                    "height": crop.height,
                    "split": split,
                    "status": status,
                    "legacy_defect_boxes_xyxy": [prompt] if status == "defective" else [],
                    "legacy_defect_instance_count": 1 if status == "defective" else 0,
                    "max_normalized_defect_box_area": (
                        ((prompt[2] - prompt[0]) * (prompt[3] - prompt[1]))
                        / (crop.width * crop.height)
                        if status == "defective"
                        else 0.0
                    ),
                    "source_collection": "new_hook_sinksey_training_photos",
                    "source_relative_path": relative.as_posix(),
                    "source_image_sha256": source_hash,
                    "source_instance_index": instance_index,
                    "source_tool_count": tool_count,
                    "source_folder_label": relative.parent.as_posix(),
                    "source_crop_xyxy": list(crop_box),
                    "capture_group": group,
                    "localization_method": localization_method,
                    "review_state": "candidate_unreviewed",
                }
            )
        audit_name = f"{source_index:03d}__{path.stem}__audit.jpg"
        audit.save(audit_root / audit_name, quality=90)
        source_records.append(
            {
                "source_relative_path": relative.as_posix(),
                "sha256": source_hash,
                "bytes": source_size,
                "split": split,
                "capture_group": group,
                "tool_count": tool_count,
                "crop_ids": source_crop_ids,
                "localization_method": localization_method,
            }
        )

    manifest = {
        "schema_version": 1,
        "package_name": "hook_sinskey_new_tray_v2_candidates",
        "tool": "hook_sinskey",
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "source_path": str(source),
        "source_file_count": len(paths),
        "source_dataset_sha256": dataset_digest.hexdigest(),
        "dataset_sha256": dataset_digest.hexdigest(),
        "sample_size": len(records),
        "burst_size": args.burst_size,
        "split_policy": "folder-stratified contiguous capture bursts; source image instances remain together",
        "label_policy": {
            "one_tool/Defect": ["defective"],
            "one_tool/Non-Defect": ["healthy"],
            "two_tools/Non-Defect + Defect": ["defective", "healthy"],
            "two_tools/Defect2": ["defective", "defective"],
            "source_exceptions": TWO_TOOL_SOURCE_EXCEPTIONS,
            "two_tool_order": "top_to_bottom",
        },
        "counts": dict(sorted(counts.items())),
        "local_root": local_root.relative_to(REPO_ROOT).as_posix(),
        "review_status": "pending_crop_and_mask_review",
        "sources": source_records,
        "images": records,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wrote {manifest_path.relative_to(REPO_ROOT)}")
    print(json.dumps(manifest["counts"], sort_keys=True))
    print(f"Crop audit: {audit_root}")


if __name__ == "__main__":
    main()
