"""Validate the human-reviewed redesigned-tray COCO detection export."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CLASS_NAMES = ("chop phaco", "forceps macpherson", "forceps utrata", "hook sinskey")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def exported_name(source: dict) -> str:
    relative = Path(source["source_relative_path"])
    parent = relative.parent.as_posix().replace("/", "__")
    return f"{source['split']}__{parent}__{relative.name}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--reviewed-zip",
        type=Path,
        default=REPO_ROOT / "ml/cvat/new_tray_detection_reviewed.zip",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=REPO_ROOT / "ml/annotation/new_tray_manifest.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "ml/annotation/new_tray_detection_review_validation.json",
    )
    parser.add_argument("--reviewer", default="Christoph")
    parser.add_argument(
        "--normalized-coco",
        type=Path,
        default=REPO_ROOT
        / "ml/annotation/local/new_tray_detection_reviewed/annotations/instances_default.json",
    )
    args = parser.parse_args()
    reviewed_zip = args.reviewed_zip.resolve()
    manifest = json.loads(args.manifest.read_text())
    expected = {exported_name(source): source for source in manifest["sources"]}
    errors: list[str] = []
    warnings: list[str] = []

    with zipfile.ZipFile(reviewed_zip) as archive:
        candidates = [name for name in archive.namelist() if name.endswith(".json")]
        if len(candidates) != 1:
            raise SystemExit(f"expected one COCO JSON in archive, found {candidates}")
        coco = json.loads(archive.read(candidates[0]))

    category_names = tuple(item["name"] for item in sorted(coco["categories"], key=lambda x: x["id"]))
    if category_names != CLASS_NAMES:
        errors.append(f"category order mismatch: {category_names}")
    hook_ids = {item["id"] for item in coco["categories"] if item["name"] == "hook sinskey"}
    if len(hook_ids) != 1:
        errors.append(f"expected exactly one hook sinskey category, found {sorted(hook_ids)}")
    hook_id = next(iter(hook_ids), None)

    images = {item["id"]: item for item in coco["images"]}
    filenames = [item["file_name"] for item in coco["images"]]
    if len(images) != 151 or len(set(filenames)) != 151:
        errors.append(f"expected 151 unique images, found {len(images)} IDs / {len(set(filenames))} names")
    missing = sorted(set(expected) - set(filenames))
    extra = sorted(set(filenames) - set(expected))
    if missing or extra:
        errors.append(f"image inventory mismatch: missing={len(missing)}, extra={len(extra)}")

    by_image: dict[int, list[dict]] = defaultdict(list)
    invalid_boxes = []
    wrong_categories = []
    for annotation in coco["annotations"]:
        image = images.get(annotation["image_id"])
        if image is None:
            errors.append(f"annotation {annotation['id']} references missing image {annotation['image_id']}")
            continue
        by_image[annotation["image_id"]].append(annotation)
        if annotation["category_id"] != hook_id:
            wrong_categories.append(annotation["id"])
        x, y, width, height = annotation["bbox"]
        if (
            width <= 0
            or height <= 0
            or x < 0
            or y < 0
            or x + width > image["width"] + 1e-6
            or y + height > image["height"] + 1e-6
        ):
            invalid_boxes.append(annotation["id"])
    if wrong_categories:
        errors.append(f"non-Hook categories used by {len(wrong_categories)} annotations")
    if invalid_boxes:
        errors.append(f"invalid/out-of-bounds boxes: {invalid_boxes}")

    mismatches = []
    split_counts: Counter[str] = Counter()
    for image in coco["images"]:
        source = expected.get(image["file_name"])
        if source is None:
            continue
        actual_count = len(by_image[image["id"]])
        expected_count = int(source["tool_count"])
        split_counts[f"{source['split']}_images"] += 1
        split_counts[f"{source['split']}_boxes"] += actual_count
        if actual_count != expected_count:
            mismatches.append(
                {
                    "file_name": image["file_name"],
                    "source_relative_path": source["source_relative_path"],
                    "expected_boxes": expected_count,
                    "actual_boxes": actual_count,
                }
            )
    if mismatches:
        errors.append(f"{len(mismatches)} images have an unexpected box count")
    expected_box_total = sum(int(source["tool_count"]) for source in manifest["sources"])
    if len(coco["annotations"]) != expected_box_total:
        errors.append(
            f"expected {expected_box_total} total boxes, found {len(coco['annotations'])}"
        )

    if not errors and any(annotation.get("segmentation") for annotation in coco["annotations"]):
        warnings.append("COCO annotations contain segmentation fields; only bbox values will be used")
    normalized_path = None
    if not errors:
        normalized = json.loads(json.dumps(coco))
        normalized_images = {item["id"]: item for item in normalized["images"]}
        normalized_annotations: dict[int, list[dict]] = defaultdict(list)
        for annotation in normalized["annotations"]:
            normalized_annotations[annotation["image_id"]].append(annotation)
        for image in normalized["images"]:
            source = expected[image["file_name"]]
            image.update(
                {
                    "split": source["split"],
                    "capture_group": source["capture_group"],
                    "source_relative_path": source["source_relative_path"],
                    "review_state": "human_reviewed",
                }
            )
            ordered = sorted(
                normalized_annotations[image["id"]],
                key=lambda item: item["bbox"][1] + item["bbox"][3] / 2,
            )
            for instance_index, annotation in enumerate(ordered, start=1):
                annotation["source_instance_index"] = instance_index
                annotation["review_state"] = "human_reviewed"
        args.normalized_coco.parent.mkdir(parents=True, exist_ok=True)
        args.normalized_coco.write_text(json.dumps(normalized, indent=2) + "\n")
        normalized_path = args.normalized_coco.relative_to(REPO_ROOT).as_posix()
    report = {
        "schema_version": 1,
        "reviewer": args.reviewer,
        "reviewed_on": date.today().isoformat(),
        "reviewed_zip": reviewed_zip.relative_to(REPO_ROOT).as_posix(),
        "reviewed_zip_sha256": sha256(reviewed_zip),
        "images": len(coco["images"]),
        "boxes": len(coco["annotations"]),
        "split_counts": dict(sorted(split_counts.items())),
        "box_count_mismatches": mismatches,
        "errors": errors,
        "warnings": warnings,
        "normalized_coco": normalized_path,
        "status": "validated" if not errors else "correction_required",
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
