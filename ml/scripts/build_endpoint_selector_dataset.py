"""Build paired tip/handle endpoint crops from reviewed full-tool boxes."""

from __future__ import annotations

import hashlib
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, ImageOps

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_MANIFEST = REPO_ROOT / "ml/annotation/new_tray_model_cropped_manifest.json"
REVIEWED_BOXES = (
    REPO_ROOT
    / "ml/annotation/local/new_tray_detection_reviewed/annotations/instances_default.json"
)
ORIENTATIONS = REPO_ROOT / "ml/annotation/new_tray_tip_orientations.json"
OUTPUT_ROOT = REPO_ROOT / "ml/data/local/hook_sinskey/endpoint_selector_v1"
OUTPUT_MANIFEST = REPO_ROOT / "ml/data/endpoint_selector_v1.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def endpoint_crop_box(
    box_xyxy: list[float], image_size: tuple[int, int], side: str
) -> tuple[int, int, int, int]:
    """Return the distal 62% crop for one side of a full-instrument box."""
    if side not in {"left", "right"}:
        raise ValueError(f"invalid endpoint side: {side}")
    image_width, image_height = image_size
    x1, y1, x2, y2 = box_xyxy
    box_width = x2 - x1
    box_height = y2 - y1
    if side == "right":
        left = max(0, round(x1 + 0.38 * box_width))
        right = min(image_width, round(x2 + 0.03 * image_width))
    else:
        left = max(0, round(x1 - 0.03 * image_width))
        right = min(image_width, round(x2 - 0.38 * box_width))
    top = max(0, round(y1 - 0.10 * box_height))
    bottom = min(image_height, round(y2 + 0.10 * box_height))
    if right <= left or bottom <= top:
        raise ValueError(f"empty {side} endpoint crop for box {box_xyxy}")
    return left, top, right, bottom


def main() -> None:
    manifest = json.loads(SOURCE_MANIFEST.read_text())
    coco = json.loads(REVIEWED_BOXES.read_text())
    orientations = json.loads(ORIENTATIONS.read_text())
    default_side = orientations["default_tip_side"]
    overrides = orientations.get("overrides", {})

    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    for split in ("train", "valid", "test"):
        for label in ("handle", "tip"):
            (OUTPUT_ROOT / split / label).mkdir(parents=True, exist_ok=True)

    images = {int(item["id"]): item for item in coco["images"]}
    annotations_by_key: dict[tuple[str, int], list[float]] = {}
    for annotation in coco["annotations"]:
        image = images[int(annotation["image_id"])]
        x, y, width, height = map(float, annotation["bbox"])
        key = (str(image["source_relative_path"]), int(annotation["source_instance_index"]))
        annotations_by_key[key] = [x, y, x + width, y + height]

    raw_root = REPO_ROOT / manifest["local_root"] / "raw"
    records: list[dict[str, object]] = []
    counts: Counter[str] = Counter()
    group_splits: dict[str, set[str]] = defaultdict(set)
    for source_record in manifest["images"]:
        image_id = source_record["image_id"]
        tip_side = overrides.get(image_id, default_side)
        relative = source_record["source_relative_path"]
        instance_index = int(source_record["source_instance_index"])
        box = annotations_by_key[(relative, instance_index)]
        with Image.open(raw_root / relative) as handle:
            image = ImageOps.exif_transpose(handle).convert("RGB")
        split = source_record["split"]
        group_splits[source_record["capture_group"]].add(split)
        for candidate_side in ("left", "right"):
            crop_box = endpoint_crop_box(box, image.size, candidate_side)
            crop = image.crop(crop_box)
            mirrored = candidate_side == "left"
            if mirrored:
                crop = ImageOps.mirror(crop)
            label = "tip" if candidate_side == tip_side else "handle"
            name = f"{image_id}__{candidate_side}.jpg"
            target = OUTPUT_ROOT / split / label / name
            crop.save(target, quality=95, subsampling=0)
            record = {
                "candidate_id": target.stem,
                "source_image_id": image_id,
                "source_relative_path": relative,
                "source_instance_index": instance_index,
                "capture_group": source_record["capture_group"],
                "split": split,
                "label": label,
                "label_id": 1 if label == "tip" else 0,
                "candidate_side": candidate_side,
                "reviewed_tip_side": tip_side,
                "canonicalized_by_horizontal_flip": mirrored,
                "source_tool_box_xyxy": box,
                "source_crop_xyxy": list(crop_box),
                "image_path": target.relative_to(REPO_ROOT).as_posix(),
                "width": crop.width,
                "height": crop.height,
                "sha256": sha256(target),
            }
            records.append(record)
            counts[f"{split}_{label}"] += 1

    leaking_groups = sorted(group for group, splits in group_splits.items() if len(splits) > 1)
    if leaking_groups:
        raise ValueError(f"capture groups cross splits: {leaking_groups}")
    digest = hashlib.sha256()
    for record in sorted(records, key=lambda item: str(item["candidate_id"])):
        digest.update(
            f"{record['candidate_id']}\0{record['split']}\0{record['label']}\0{record['sha256']}\n".encode()
        )
    output = {
        "schema_version": 1,
        "dataset_version": "hook_sinskey_endpoint_selector_v1",
        "status": "labels_derived_from_human_reviewed_boxes_and_tip_orientations",
        "seed": 42,
        "classes": {"0": "handle", "1": "tip"},
        "local_root": OUTPUT_ROOT.relative_to(REPO_ROOT).as_posix(),
        "source_manifest": SOURCE_MANIFEST.relative_to(REPO_ROOT).as_posix(),
        "reviewed_boxes": REVIEWED_BOXES.relative_to(REPO_ROOT).as_posix(),
        "tip_orientations": ORIENTATIONS.relative_to(REPO_ROOT).as_posix(),
        "normalization": "left endpoint mirrored; candidate endpoint appears on right",
        "sample_count": len(records),
        "source_instrument_count": len(manifest["images"]),
        "counts": dict(sorted(counts.items())),
        "capture_group_leakage": leaking_groups,
        "dataset_sha256": digest.hexdigest(),
        "records": records,
    }
    OUTPUT_MANIFEST.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({"samples": len(records), "counts": output["counts"], "sha256": output["dataset_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
