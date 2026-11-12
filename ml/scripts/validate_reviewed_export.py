"""Validate a human-reviewed CVAT COCO export and write a tracked summary."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from pycocotools import mask as mask_utils

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXPORT = (
    REPO_ROOT
    / "ml/annotation/local/hook_sinskey_full/reviewed/"
    "hook_sinskey_reviewed_christoph.zip"
)
DEFAULT_MANIFEST = REPO_ROOT / "ml/annotation/full_dataset_manifest.json"
DEFAULT_CANDIDATE = (
    REPO_ROOT
    / "ml/annotation/local/hook_sinskey_full/"
    "cvat_dataset/annotations/instances_default.json"
)
DEFAULT_SUMMARY = REPO_ROOT / "ml/annotation/reviewed_summary.json"


def sha256_bytes(contents: bytes) -> str:
    return hashlib.sha256(contents).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def decode_mask(segmentation: dict[str, object], height: int, width: int) -> np.ndarray:
    rle = segmentation
    if isinstance(rle.get("counts"), list):
        rle = mask_utils.frPyObjects(rle, height, width)
    decoded = mask_utils.decode(rle)
    if decoded.ndim == 3:
        decoded = decoded[..., 0]
    return decoded.astype(bool)


def mask_to_bbox(mask: np.ndarray) -> list[float]:
    rows, columns = np.where(mask)
    if not len(columns):
        raise ValueError("cannot derive a box from an empty mask")
    x1, y1 = int(columns.min()), int(rows.min())
    x2, y2 = int(columns.max()) + 1, int(rows.max()) + 1
    return [float(x1), float(y1), float(x2 - x1), float(y2 - y1)]


def expected_filename(record: dict[str, object]) -> str:
    return f"{record['split']}__{Path(str(record['image_path'])).name}"


def unions_by_filename(coco: dict[str, object]) -> dict[str, np.ndarray]:
    images = {int(image["id"]): image for image in coco["images"]}
    unions = {
        str(image["file_name"]): np.zeros(
            (int(image["height"]), int(image["width"])), dtype=bool
        )
        for image in coco["images"]
    }
    for annotation in coco["annotations"]:
        image = images[int(annotation["image_id"])]
        unions[str(image["file_name"])] |= decode_mask(
            annotation["segmentation"], int(image["height"]), int(image["width"])
        )
    return unions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", type=Path, default=DEFAULT_EXPORT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--candidate", type=Path, default=DEFAULT_CANDIDATE)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--reviewer", default="Christoph")
    parser.add_argument("--reviewed-on", default="2026-09-24")
    parser.add_argument(
        "--expected-masks",
        type=int,
        default=199,
        help="Expected instance count; set from the reviewed dataset policy.",
    )
    parser.add_argument(
        "--review-status",
        default="validated_awaiting_milestone_3_approval",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    export = args.export.resolve()
    manifest = json.loads(args.manifest.resolve().read_text())
    candidate = json.loads(args.candidate.resolve().read_text())
    errors: list[str] = []

    with zipfile.ZipFile(export) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        if names != ["annotations/instances_default.json"]:
            errors.append(f"unexpected reviewed ZIP contents: {names}")
        coco_bytes = archive.read("annotations/instances_default.json")
    coco = json.loads(coco_bytes)

    categories = coco.get("categories", [])
    if len(categories) != 1 or categories[0].get("name") != "defect":
        errors.append("reviewed export does not have exactly one defect category")

    expected = {expected_filename(record): record for record in manifest["images"]}
    image_list = coco.get("images", [])
    images_by_id = {int(image["id"]): image for image in image_list}
    actual_names = {str(image["file_name"]) for image in images_by_id.values()}
    expected_image_count = len(expected)
    if len(images_by_id) != len(image_list):
        errors.append("reviewed export contains duplicate image IDs")
    if len(images_by_id) != expected_image_count or len(actual_names) != expected_image_count:
        errors.append(
            f"reviewed export does not contain {expected_image_count} unique images"
        )
    if actual_names != set(expected):
        errors.append("reviewed image filenames do not match the frozen manifest")
    for image in images_by_id.values():
        record = expected.get(str(image["file_name"]))
        if record is None:
            continue
        if int(image["width"]) != int(record["width"]) or int(image["height"]) != int(record["height"]):
            errors.append(f"reviewed image dimensions changed: {image['file_name']}")

    annotations_by_name: dict[str, list[dict[str, object]]] = defaultdict(list)
    seen_annotation_ids: set[int] = set()
    for annotation in coco.get("annotations", []):
        annotation_id = int(annotation["id"])
        if annotation_id in seen_annotation_ids:
            errors.append(f"duplicate annotation ID: {annotation_id}")
        seen_annotation_ids.add(annotation_id)
        image = images_by_id.get(int(annotation["image_id"]))
        if image is None:
            errors.append(f"annotation {annotation_id} references a missing image")
            continue
        if int(annotation["category_id"]) != int(categories[0]["id"]):
            errors.append(f"annotation {annotation_id} has the wrong category")
        name = str(image["file_name"])
        height, width = int(image["height"]), int(image["width"])
        mask = decode_mask(annotation["segmentation"], height, width)
        if mask.shape != (height, width) or not mask.any():
            errors.append(f"annotation {annotation_id} has an invalid or empty mask")
            continue
        derived_box = mask_to_bbox(mask)
        if not np.allclose(derived_box, annotation["bbox"], atol=1e-6):
            errors.append(f"annotation {annotation_id} bbox does not enclose its mask")
        if not np.isclose(float(mask.sum()), float(annotation["area"])):
            errors.append(f"annotation {annotation_id} area does not match its mask")
        annotations_by_name[name].append(annotation)

    status_counts: Counter[str] = Counter()
    split_counts: Counter[str] = Counter()
    annotated_defective = 0
    capture_group_splits: dict[str, set[str]] = defaultdict(set)
    for name, record in expected.items():
        status, split = str(record["status"]), str(record["split"])
        status_counts[status] += 1
        split_counts[split] += 1
        capture_group_splits[str(record["capture_group"])].add(split)
        count = len(annotations_by_name[name])
        if status == "healthy" and count:
            errors.append(f"healthy image has {count} masks: {name}")
        if status == "defective":
            if not count:
                errors.append(f"defective image has no mask: {name}")
            else:
                annotated_defective += 1
    leaking_groups = sorted(
        group for group, splits in capture_group_splits.items() if len(splits) > 1
    )
    if leaking_groups:
        errors.append(f"capture groups cross splits: {leaking_groups}")

    reviewed_unions = unions_by_filename(coco)
    candidate_unions = unions_by_filename(candidate)
    changed: list[dict[str, object]] = []
    for name in sorted(expected):
        reviewed_mask, candidate_mask = reviewed_unions[name], candidate_unions[name]
        intersection = int(np.logical_and(reviewed_mask, candidate_mask).sum())
        union = int(np.logical_or(reviewed_mask, candidate_mask).sum())
        iou = intersection / union if union else 1.0
        changed_pixels = int(np.logical_xor(reviewed_mask, candidate_mask).sum())
        if changed_pixels:
            changed.append(
                {
                    "file_name": name,
                    "union_iou_vs_candidate": round(iou, 6),
                    "changed_pixels": changed_pixels,
                }
            )

    if len(coco.get("annotations", [])) != args.expected_masks:
        errors.append(
            f"reviewed export does not contain {args.expected_masks} masks"
        )
    expected_defective = status_counts["defective"]
    if annotated_defective != expected_defective:
        errors.append(
            f"reviewed export does not annotate all {expected_defective} defective images"
        )
    if errors:
        print("Reviewed export validation failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    summary = {
        "schema_version": 1,
        "tool": "hook_sinskey",
        "reviewer": args.reviewer,
        "reviewed_on": args.reviewed_on,
        "review_status": args.review_status,
        "dataset_sha256": manifest["dataset_sha256"],
        "reviewed_export": export.relative_to(REPO_ROOT).as_posix(),
        "reviewed_zip_sha256": sha256_file(export),
        "reviewed_coco_sha256": sha256_bytes(coco_bytes),
        "images": len(images_by_id),
        "masks": len(coco["annotations"]),
        "defective_images": status_counts["defective"],
        "healthy_images": status_counts["healthy"],
        "annotated_defective_images": annotated_defective,
        "healthy_images_with_masks": 0,
        "split_images": dict(sorted(split_counts.items())),
        "candidate_comparison": {
            "images_with_changed_mask_pixels": len(changed),
            "unchanged_images": len(expected) - len(changed),
            "total_changed_pixels": sum(int(item["changed_pixels"]) for item in changed),
            "minimum_union_iou": min(
                (float(item["union_iou_vs_candidate"]) for item in changed),
                default=1.0,
            ),
            "changed_images": changed,
        },
        "checks": {
            "single_defect_category": True,
            "stable_unique_image_ids": True,
            "frozen_split_membership": True,
            "valid_in_bounds_nonempty_masks": True,
            "derived_boxes_enclose_masks": True,
            "healthy_images_empty": True,
            "no_cross_split_leakage": True,
        },
    }
    args.summary.resolve().write_text(json.dumps(summary, indent=2) + "\n")
    print("Reviewed export validation passed.")
    print(f"Images: {summary['images']} ({dict(status_counts)})")
    print(f"Masks: {summary['masks']} on {annotated_defective} defective images")
    print(f"Healthy images with masks: {summary['healthy_images_with_masks']}")
    print(f"Images changed vs candidate: {len(changed)}")
    print(f"Wrote {args.summary.resolve().relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
