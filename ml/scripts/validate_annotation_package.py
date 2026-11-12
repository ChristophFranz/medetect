"""Validate a Hook Sinskey COCO/CVAT candidate package."""

from __future__ import annotations

import argparse
import json
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from pycocotools import mask as mask_utils

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SAMPLE = REPO_ROOT / "ml/annotation/pilot_sample.json"
DEFAULT_COCO = (
    REPO_ROOT
    / "ml/annotation/local/hook_sinskey_pilot/cvat_dataset/annotations/instances_default.json"
)
DEFAULT_ZIP = REPO_ROOT / "ml/cvat/hook_sinskey_pilot_candidates.zip"


def mask_to_bbox(binary_mask: np.ndarray) -> list[float]:
    rows, columns = np.where(binary_mask)
    if not len(columns):
        raise ValueError("cannot derive a box from an empty mask")
    x1 = int(columns.min())
    y1 = int(rows.min())
    x2 = int(columns.max()) + 1
    y2 = int(rows.max()) + 1
    return [float(x1), float(y1), float(x2 - x1), float(y2 - y1)]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=Path, default=DEFAULT_SAMPLE)
    parser.add_argument("--coco", type=Path, default=DEFAULT_COCO)
    parser.add_argument("--cvat-zip", type=Path, default=DEFAULT_ZIP)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sample = json.loads(args.sample.read_text())
    coco = json.loads(args.coco.read_text())
    errors: list[str] = []

    expected_size = int(sample["sample_size"])
    test_is_excluded = "test" in sample.get("excluded_splits", [])
    if test_is_excluded and any(
        record["split"] == "test" for record in sample["images"]
    ):
        errors.append("test image found despite being explicitly excluded")
    if coco["categories"] != [
        {"id": 1, "name": "defect", "supercategory": "defect"}
    ]:
        errors.append("COCO categories are not the canonical one-class policy")

    sample_by_id = {record["image_id"]: record for record in sample["images"]}
    coco_by_id = {image["id"]: image for image in coco["images"]}
    if len(coco_by_id) != expected_size:
        errors.append(
            f"COCO image count is {len(coco_by_id)}, expected {expected_size}"
        )
    if {image["medetect_image_id"] for image in coco["images"]} != set(sample_by_id):
        errors.append("COCO/sample image identifiers differ")

    annotations_by_image: dict[int, list[dict[str, object]]] = defaultdict(list)
    for annotation in coco["annotations"]:
        annotations_by_image[int(annotation["image_id"])].append(annotation)
        image_record = coco_by_id.get(annotation["image_id"])
        if image_record is None:
            errors.append(f"annotation {annotation['id']} references a missing image")
            continue
        if annotation["category_id"] != 1:
            errors.append(f"annotation {annotation['id']} has a non-defect category")
        binary_mask = mask_utils.decode(annotation["segmentation"]).astype(bool)
        expected_shape = (image_record["height"], image_record["width"])
        if binary_mask.shape != expected_shape:
            errors.append(
                f"annotation {annotation['id']} shape {binary_mask.shape} != {expected_shape}"
            )
            continue
        if not binary_mask.any():
            errors.append(f"annotation {annotation['id']} is empty")
            continue
        derived_box = mask_to_bbox(binary_mask)
        if not np.allclose(derived_box, annotation["bbox"], atol=1e-6):
            errors.append(f"annotation {annotation['id']} box does not enclose its mask")
        if not np.isclose(float(binary_mask.sum()), float(annotation["area"])):
            errors.append(f"annotation {annotation['id']} area does not match its mask")

    status_counts: Counter[str] = Counter()
    for coco_image_id, image_record in coco_by_id.items():
        sample_record = sample_by_id[image_record["medetect_image_id"]]
        status = sample_record["status"]
        status_counts[status] += 1
        annotation_count = len(annotations_by_image[coco_image_id])
        if status == "healthy" and annotation_count:
            errors.append(f"healthy image has {annotation_count} annotations")
        expected = int(sample_record["legacy_defect_instance_count"])
        if status == "defective" and annotation_count != expected:
            errors.append(
                f"defective image {sample_record['image_id']} has {annotation_count} masks, "
                f"expected {expected} prompts"
            )

    if not args.cvat_zip.is_file():
        errors.append(f"CVAT ZIP missing: {args.cvat_zip}")
    else:
        with zipfile.ZipFile(args.cvat_zip) as archive:
            names = set(archive.namelist())
        if "annotations/instances_default.json" not in names:
            errors.append("CVAT ZIP lacks annotations/instances_default.json")
        zipped_images = [
            name
            for name in names
            if name.startswith("images/default/") and not name.endswith("/")
        ]
        if len(zipped_images) != expected_size:
            errors.append(
                f"CVAT ZIP has {len(zipped_images)} images, expected {expected_size}"
            )

    if errors:
        print("Annotation package validation failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print("Annotation package validation passed.")
    print(f"Images: {len(coco_by_id)} ({dict(status_counts)})")
    print(f"Candidate masks: {len(coco['annotations'])}")
    print(
        "Test images: "
        f"{sum(record['split'] == 'test' for record in sample['images'])}"
    )


if __name__ == "__main__":
    main()
