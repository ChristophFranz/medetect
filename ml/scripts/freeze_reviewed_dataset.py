"""Freeze the approved reviewed export as deterministic COCO segmentation data."""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
from pycocotools import mask as mask_utils

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "ml/annotation/full_dataset_manifest.json"
REVIEW_SUMMARY_PATH = REPO_ROOT / "ml/annotation/reviewed_summary.json"
OUTPUT_ROOT = REPO_ROOT / "ml/data/local/hook_sinskey/coco_segmentation_v1"
FREEZE_RECORD = REPO_ROOT / "ml/data/frozen_hook_sinskey_v1.json"
SPLITS = ("train", "valid", "test")


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


def encode_mask(mask: np.ndarray) -> dict[str, object]:
    encoded = mask_utils.encode(np.asfortranarray(mask.astype(np.uint8)))
    encoded["counts"] = encoded["counts"].decode("ascii")
    return encoded


def mask_to_bbox(mask: np.ndarray) -> list[float]:
    rows, columns = np.where(mask)
    x1, y1 = int(columns.min()), int(rows.min())
    x2, y2 = int(columns.max()) + 1, int(rows.max()) + 1
    return [float(x1), float(y1), float(x2 - x1), float(y2 - y1)]


def cvat_filename(record: dict[str, object]) -> str:
    return f"{record['split']}__{Path(str(record['image_path'])).name}"


def write_coco(path: Path, images: list[dict], annotations: list[dict]) -> str:
    payload = {
        "info": {
            "description": "Frozen reviewed Hook Sinskey defect segmentation benchmark",
            "version": "1",
        },
        "licenses": [],
        "categories": [{"id": 1, "name": "defect", "supercategory": "defect"}],
        "images": images,
        "annotations": annotations,
    }
    contents = (json.dumps(payload, indent=2) + "\n").encode()
    path.write_bytes(contents)
    return sha256_bytes(contents)


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text())
    review = json.loads(REVIEW_SUMMARY_PATH.read_text())
    reviewed_zip = REPO_ROOT / review["reviewed_export"]
    if sha256_file(reviewed_zip) != review["reviewed_zip_sha256"]:
        raise SystemExit("reviewed ZIP hash does not match the approved validation record")
    with zipfile.ZipFile(reviewed_zip) as archive:
        reviewed_bytes = archive.read("annotations/instances_default.json")
    if sha256_bytes(reviewed_bytes) != review["reviewed_coco_sha256"]:
        raise SystemExit("reviewed COCO hash does not match the approved validation record")
    reviewed = json.loads(reviewed_bytes)

    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    annotation_dir = OUTPUT_ROOT / "annotations"
    annotation_dir.mkdir(parents=True)
    for split in SPLITS:
        (OUTPUT_ROOT / "images" / split).mkdir(parents=True)

    records = sorted(manifest["images"], key=lambda item: cvat_filename(item))
    records_by_name = {cvat_filename(record): record for record in records}
    reviewed_images = {int(image["id"]): image for image in reviewed["images"]}
    reviewed_annotations: dict[str, list[dict]] = {
        name: [] for name in records_by_name
    }
    for annotation in reviewed["annotations"]:
        image = reviewed_images[int(annotation["image_id"])]
        reviewed_annotations[str(image["file_name"])].append(annotation)

    canonical_images: list[dict] = []
    canonical_annotations: list[dict] = []
    split_counts: dict[str, Counter] = {split: Counter() for split in SPLITS}
    for image_id, record in enumerate(records, start=1):
        name = cvat_filename(record)
        split = str(record["split"])
        source = REPO_ROOT / str(record["image_path"])
        target = OUTPUT_ROOT / "images" / split / source.name
        shutil.copy2(source, target)
        canonical_images.append(
            {
                "id": image_id,
                "file_name": f"images/{split}/{source.name}",
                "width": int(record["width"]),
                "height": int(record["height"]),
                "medetect_image_id": record["image_id"],
                "split": split,
                "status": record["status"],
                "source_image_sha256": record["image_sha256"],
            }
        )
        split_counts[split]["images"] += 1
        split_counts[split][str(record["status"])] += 1
        for annotation in sorted(reviewed_annotations[name], key=lambda item: item["id"]):
            mask = decode_mask(
                annotation["segmentation"], int(record["height"]), int(record["width"])
            )
            canonical_annotations.append(
                {
                    "id": len(canonical_annotations) + 1,
                    "image_id": image_id,
                    "category_id": 1,
                    "segmentation": encode_mask(mask),
                    "area": float(mask.sum()),
                    "bbox": mask_to_bbox(mask),
                    "iscrowd": 0,
                }
            )
            split_counts[split]["instances"] += 1

    hashes = {
        "all": write_coco(
            annotation_dir / "instances_all.json",
            canonical_images,
            canonical_annotations,
        )
    }
    for split in SPLITS:
        split_image_ids = {
            int(image["id"]) for image in canonical_images if image["split"] == split
        }
        hashes[split] = write_coco(
            annotation_dir / f"instances_{split}.json",
            [image for image in canonical_images if int(image["id"]) in split_image_ids],
            [
                annotation
                for annotation in canonical_annotations
                if int(annotation["image_id"]) in split_image_ids
            ],
        )

    combined = hashlib.sha256()
    files = []
    for path in sorted(item for item in OUTPUT_ROOT.rglob("*") if item.is_file()):
        relative = path.relative_to(OUTPUT_ROOT).as_posix()
        digest = sha256_file(path)
        size = path.stat().st_size
        combined.update(f"{relative}\0{size}\0{digest}\n".encode())
        files.append({"path": relative, "bytes": size, "sha256": digest})

    freeze_record = {
        "schema_version": 1,
        "dataset_version": "hook_sinskey_segmentation_v1",
        "approved_by": "Christoph",
        "approved_on": "2026-09-24",
        "source_dataset_sha256": manifest["dataset_sha256"],
        "reviewed_zip_sha256": review["reviewed_zip_sha256"],
        "reviewed_coco_sha256": review["reviewed_coco_sha256"],
        "canonical_local_path": OUTPUT_ROOT.relative_to(REPO_ROOT).as_posix(),
        "canonical_tree_sha256": combined.hexdigest(),
        "annotation_sha256": hashes,
        "counts": {split: dict(split_counts[split]) for split in SPLITS},
        "images": len(canonical_images),
        "instances": len(canonical_annotations),
        "test_split_frozen": True,
        "files": files,
    }
    FREEZE_RECORD.write_text(json.dumps(freeze_record, indent=2) + "\n")
    print(f"Wrote {FREEZE_RECORD.relative_to(REPO_ROOT)}")
    print(f"Canonical tree SHA-256: {freeze_record['canonical_tree_sha256']}")
    print(json.dumps(freeze_record["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
