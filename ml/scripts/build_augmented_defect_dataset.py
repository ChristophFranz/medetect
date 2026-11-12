"""Materialize a deterministic 50/50 original/augmented defect dataset."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from PIL import Image, ImageDraw
from pycocotools import mask as mask_utils

from ml.data.augmentation import augment_training_sample
from ml.data.coco_dataset import FrozenCocoDataset

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO_ROOT / "ml/configs/augmentation_v4_50_50.yaml"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_seed(base_seed: int, image_id: str) -> int:
    value = hashlib.sha256(f"{base_seed}:{image_id}:aug01".encode()).digest()
    return int.from_bytes(value[:8], "big") % (2**31)


def encode_mask(mask: np.ndarray) -> dict[str, Any]:
    encoded = mask_utils.encode(np.asfortranarray(mask.astype(np.uint8)))
    return {
        "size": [int(value) for value in encoded["size"]],
        "counts": encoded["counts"].decode("ascii"),
    }


def relative_config_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def write_yolo_label(path: Path, annotations: list[dict[str, Any]], width: int, height: int) -> None:
    lines = []
    for annotation in annotations:
        x, y, box_width, box_height = map(float, annotation["bbox"])
        lines.append(
            f"0 {(x + box_width / 2) / width:.8f} {(y + box_height / 2) / height:.8f} "
            f"{box_width / width:.8f} {box_height / height:.8f}"
        )
    path.write_text("\n".join(lines) + ("\n" if lines else ""))


def draw_masks(image: Image.Image, masks: np.ndarray) -> Image.Image:
    base = image.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    pixels = np.zeros((base.height, base.width, 4), dtype=np.uint8)
    if len(masks):
        union = masks.astype(bool).any(axis=0)
        pixels[union] = (255, 0, 120, 105)
    overlay = Image.fromarray(pixels, mode="RGBA")
    result = Image.alpha_composite(base, overlay)
    draw = ImageDraw.Draw(result)
    draw.rectangle((0, 0, result.width - 1, result.height - 1), outline=(25, 120, 220, 255), width=3)
    return result.convert("RGB")


def build_gallery(output: Path, pairs: list[dict[str, Any]]) -> None:
    gallery = output / "review_gallery"
    gallery.mkdir(parents=True)
    dataset = FrozenCocoDataset("train", root=output)
    index_by_id = {
        str(item["medetect_image_id"]): index
        for index, item in enumerate(dataset.images)
    }
    cards = []
    for index, pair in enumerate(pairs, start=1):
        original, original_target = dataset[index_by_id[pair["image_id"]]]
        augmented, augmented_target = dataset[
            index_by_id[f"{pair['image_id']}__aug01"]
        ]
        original = draw_masks(original, original_target["masks"].numpy())
        augmented = draw_masks(augmented, augmented_target["masks"].numpy())
        original.thumbnail((520, 360))
        augmented.thumbnail((520, 360))
        canvas = Image.new("RGB", (1040, 400), "white")
        canvas.paste(original, (0, 40))
        canvas.paste(augmented, (520, 40))
        draw = ImageDraw.Draw(canvas)
        draw.text((10, 10), "ORIGINAL", fill="black")
        draw.text((530, 10), "AUGMENTED", fill="black")
        filename = f"pair_{index:03d}_{pair['image_id']}.jpg".replace("/", "_")
        canvas.save(gallery / filename, quality=92)
        cards.append(
            f'<figure><img src="{filename}" loading="lazy"><figcaption>{pair["image_id"]} — '
            f'{pair["status"]}</figcaption></figure>'
        )
    (gallery / "index.html").write_text(
        "<!doctype html><meta charset='utf-8'><title>Augmentation review</title>"
        "<style>body{font-family:system-ui;margin:24px;background:#f5f7fa}"
        "figure{background:white;padding:12px;border-radius:8px;box-shadow:0 1px 4px #bbb}"
        "img{width:100%;height:auto}figcaption{padding:8px 2px}</style>"
        "<h1>Hook Sinskey 50/50 augmentation review</h1>"
        "<p>Left: reviewed original. Right: deterministic training-only augmentation. "
        "Validation and test are not augmented.</p>" + "".join(cards)
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text())
    source = relative_config_path(config["source_dataset"])
    source_domain_filter = config.get("source_domain_filter")
    output = relative_config_path(config["output_dataset"])
    record_path = relative_config_path(config["output_record"])
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing dataset: {output}")

    for split in ("train", "valid", "test"):
        (output / "images" / split).mkdir(parents=True)
        (output / "yolo" / split / "images").mkdir(parents=True)
        (output / "yolo" / split / "labels").mkdir(parents=True)
    (output / "annotations").mkdir(parents=True)

    base_seed = int(config["seed"])
    transforms = dict(config["transforms"])
    counts: Counter[str] = Counter()
    gallery_candidates = []
    split_payloads = {}
    train_source_dataset = FrozenCocoDataset("train", root=source)
    next_image_id = 1
    next_annotation_id = 1

    for split in ("train", "valid", "test"):
        source_payload = json.loads(
            (source / "annotations" / f"instances_{split}.json").read_text()
        )
        annotations_by_image: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for annotation in source_payload["annotations"]:
            annotations_by_image[int(annotation["image_id"])].append(annotation)
        payload = {
            "info": {
                "description": "Hook Sinskey reviewed-v3 with one deterministic augmentation per training image",
                "version": "new-tray-reviewed-v4-augmented-50-50",
                "date_created": datetime.now(UTC).date().isoformat(),
            },
            "licenses": source_payload.get("licenses", []),
            "categories": source_payload["categories"],
            "images": [],
            "annotations": [],
        }
        selected_images = [
            image
            for image in source_payload["images"]
            if source_domain_filter is None
            or image.get("source_domain") == source_domain_filter
        ]
        for source_image in selected_images:
            source_annotations = annotations_by_image[int(source_image["id"])]
            source_path = source / source_image["file_name"]
            original_name = Path(source_image["file_name"]).name
            original_rel = Path("images") / split / original_name
            shutil.copy2(source_path, output / original_rel)
            shutil.copy2(source_path, output / "yolo" / split / "images" / original_name)
            original_record = {
                **source_image,
                "id": next_image_id,
                "file_name": original_rel.as_posix(),
                "sample_kind": "original",
                "parent_medetect_image_id": source_image["medetect_image_id"],
                "augmentation_id": None,
            }
            payload["images"].append(original_record)
            converted_originals = []
            for annotation in source_annotations:
                converted = {
                    **annotation,
                    "id": next_annotation_id,
                    "image_id": next_image_id,
                }
                payload["annotations"].append(converted)
                converted_originals.append(converted)
                next_annotation_id += 1
            write_yolo_label(
                output / "yolo" / split / "labels" / f"{Path(original_name).stem}.txt",
                converted_originals,
                int(source_image["width"]),
                int(source_image["height"]),
            )
            counts[f"{split}_original"] += 1
            counts[f"{split}_{source_image['status']}"] += 1
            counts[f"{split}_instances"] += len(source_annotations)
            next_image_id += 1

            if split != "train":
                continue
            dataset = train_source_dataset
            # IDs are sorted in FrozenCocoDataset, so locate the matching source record explicitly.
            dataset_index = next(
                index
                for index, item in enumerate(dataset.images)
                if int(item["id"]) == int(source_image["id"])
            )
            image, target = dataset[dataset_index]
            augmentation_seed = stable_seed(base_seed, str(source_image["medetect_image_id"]))
            augmented_image, augmented_target = augment_training_sample(
                image, target, transforms, seed=augmentation_seed
            )
            augmented_name = f"{Path(original_name).stem}__aug01.jpg"
            augmented_rel = Path("images/train") / augmented_name
            augmented_image.save(output / augmented_rel, quality=95, subsampling=0)
            shutil.copy2(output / augmented_rel, output / "yolo/train/images" / augmented_name)
            augmented_record = {
                **source_image,
                "id": next_image_id,
                "file_name": augmented_rel.as_posix(),
                "medetect_image_id": f"{source_image['medetect_image_id']}__aug01",
                "sample_kind": "augmented",
                "parent_medetect_image_id": source_image["medetect_image_id"],
                "augmentation_id": "aug01",
                "augmentation_seed": augmentation_seed,
            }
            payload["images"].append(augmented_record)
            augmented_annotations = []
            masks = augmented_target["masks"].cpu().numpy()
            boxes = augmented_target["boxes"].cpu().numpy()
            for mask, box in zip(masks, boxes, strict=True):
                x1, y1, x2, y2 = map(float, box)
                annotation = {
                    "id": next_annotation_id,
                    "image_id": next_image_id,
                    "category_id": 1,
                    "segmentation": encode_mask(mask),
                    "area": int(mask.sum()),
                    "bbox": [x1, y1, x2 - x1, y2 - y1],
                    "iscrowd": 0,
                }
                payload["annotations"].append(annotation)
                augmented_annotations.append(annotation)
                next_annotation_id += 1
            write_yolo_label(
                output / "yolo/train/labels" / f"{Path(augmented_name).stem}.txt",
                augmented_annotations,
                int(source_image["width"]),
                int(source_image["height"]),
            )
            counts["train_augmented"] += 1
            counts[f"train_augmented_{source_image['status']}"] += 1
            counts["train_augmented_instances"] += len(augmented_annotations)
            gallery_candidates.append(
                {
                    "image_id": str(source_image["medetect_image_id"]),
                    "status": str(source_image["status"]),
                }
            )
            next_image_id += 1

        annotation_path = output / "annotations" / f"instances_{split}.json"
        annotation_path.write_text(json.dumps(payload, indent=2) + "\n")
        split_payloads[split] = payload

    all_payload = {
        "info": split_payloads["train"]["info"],
        "licenses": [],
        "categories": split_payloads["train"]["categories"],
        "images": [item for split in split_payloads.values() for item in split["images"]],
        "annotations": [item for split in split_payloads.values() for item in split["annotations"]],
    }
    (output / "annotations/instances_all.json").write_text(json.dumps(all_payload, indent=2) + "\n")
    (output / "yolo/data.yaml").write_text(
        f"path: {(output / 'yolo').as_posix()}\ntrain: train/images\nval: valid/images\n"
        "test: test/images\n\nnames:\n  0: defect\n"
    )

    requested_gallery = int(config["review"]["gallery_pairs"])
    ordered_gallery = sorted(
        gallery_candidates,
        key=lambda item: hashlib.sha256(item["image_id"].encode()).hexdigest(),
    )[:requested_gallery]
    build_gallery(output, ordered_gallery)

    digest = hashlib.sha256()
    files = []
    for path in sorted(item for item in output.rglob("*") if item.is_file()):
        relative = path.relative_to(output).as_posix()
        file_hash = sha256(path)
        size = path.stat().st_size
        digest.update(f"{relative}\0{size}\0{file_hash}\n".encode())
        files.append({"path": relative, "bytes": size, "sha256": file_hash})
    original_count = int(counts["train_original"])
    augmented_count = int(counts["train_augmented"])
    summary = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "dataset_version": "hook_sinskey_new_tray_reviewed_v4_augmented_50_50",
        "status": "generated_awaiting_augmentation_review",
        "source_dataset": source.relative_to(REPO_ROOT).as_posix(),
        "source_domain_filter": source_domain_filter,
        "source_dataset_record": "ml/data/combined_hook_sinskey_reviewed_v3.json",
        "local_path": output.relative_to(REPO_ROOT).as_posix(),
        "seed": base_seed,
        "transforms": transforms,
        "counts": dict(sorted(counts.items())),
        "train_images": len(split_payloads["train"]["images"]),
        "validation_images": len(split_payloads["valid"]["images"]),
        "test_images": len(split_payloads["test"]["images"]),
        "original_augmented_ratio": f"{original_count}:{augmented_count}",
        "validation_and_test_augmented": False,
        "test_split_frozen": True,
        "review_gallery": (output / "review_gallery/index.html").relative_to(REPO_ROOT).as_posix(),
        "review_status": "pending",
        "tree_sha256": digest.hexdigest(),
        "files": files,
    }
    record_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({key: summary[key] for key in ("dataset_version", "train_images", "validation_images", "test_images", "original_augmented_ratio", "tree_sha256")}, indent=2))


if __name__ == "__main__":
    main()

