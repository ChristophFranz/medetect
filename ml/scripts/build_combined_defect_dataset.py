"""Combine reviewed legacy masks with reviewed redesigned-tray masks."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OLD_ROOT = REPO_ROOT / "ml/data/local/hook_sinskey/coco_segmentation_v1"
NEW_ROOT = REPO_ROOT / "ml/annotation/local/new_tray_defect_model_cropped_candidates/cvat_dataset"
NEW_MANIFEST = REPO_ROOT / "ml/annotation/new_tray_model_cropped_manifest.json"
NEW_REVIEWED_ZIP = REPO_ROOT / "ml/cvat/new_tray_defect_masks_reviewed.zip"
NEW_REVIEW_SUMMARY = REPO_ROOT / "ml/annotation/new_tray_defect_masks_reviewed_summary.json"
OUTPUT_ROOT = REPO_ROOT / "ml/data/local/hook_sinskey/combined_reviewed_v3"
SUMMARY = REPO_ROOT / "ml/data/combined_hook_sinskey_reviewed_v3.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--minimum-area-ratio", type=float, default=0.001)
    parser.add_argument("--maximum-area-ratio", type=float, default=0.10)
    args = parser.parse_args()
    output = OUTPUT_ROOT
    if output.exists():
        shutil.rmtree(output)
    (output / "annotations").mkdir(parents=True)
    for split in ("train", "valid", "test"):
        (output / "images" / split).mkdir(parents=True)
        (output / "yolo" / split / "images").mkdir(parents=True)
        (output / "yolo" / split / "labels").mkdir(parents=True)

    with zipfile.ZipFile(NEW_REVIEWED_ZIP) as archive:
        new_coco = json.loads(archive.read("annotations/instances_default.json"))
    new_manifest = json.loads(NEW_MANIFEST.read_text())
    review_summary = json.loads(NEW_REVIEW_SUMMARY.read_text())
    new_records = {
        f"{item['split']}__{Path(item['image_path']).name}": item
        for item in new_manifest["images"]
    }
    new_annotations: dict[int, list[dict]] = defaultdict(list)
    for annotation in new_coco["annotations"]:
        new_annotations[int(annotation["image_id"])].append(annotation)
    area_qc_warnings = []
    for image in new_coco["images"]:
        annotations = new_annotations[int(image["id"])]
        for annotation in annotations:
            ratio = annotation["area"] / (image["width"] * image["height"])
            if ratio < args.minimum_area_ratio or ratio > args.maximum_area_ratio:
                area_qc_warnings.append(
                    {
                        "image_id": new_records[image["file_name"]]["image_id"],
                        "split": new_records[image["file_name"]]["split"],
                        "mask_area_ratio": ratio,
                        "reason": "human-reviewed mask area outside advisory QC bounds",
                    }
                )
    counts: Counter[str] = Counter()
    split_payloads = {}
    next_image_id = 1
    next_annotation_id = 1
    for split in ("train", "valid", "test"):
        payload = {
            "info": {
                "description": "Combined Hook Sinskey defect segmentation; reviewed legacy + reviewed new tray",
                "version": "combined-reviewed-v3",
                "date_created": review_summary["reviewed_on"],
            },
            "licenses": [],
            "categories": [{"id": 1, "name": "defect", "supercategory": "defect"}],
            "images": [],
            "annotations": [],
        }
        old = json.loads((OLD_ROOT / "annotations" / f"instances_{split}.json").read_text())
        old_annotations: dict[int, list[dict]] = defaultdict(list)
        for annotation in old["annotations"]:
            old_annotations[int(annotation["image_id"])].append(annotation)
        sources = []
        for image in old["images"]:
            sources.append(("old", image, old_annotations[int(image["id"])], OLD_ROOT / image["file_name"]))
        for image in new_coco["images"]:
            record = new_records[image["file_name"]]
            if record["split"] != split:
                continue
            sources.append(
                (
                    "new",
                    {
                        **image,
                        "status": record["status"],
                        "split": record["split"],
                        "capture_group": record["capture_group"],
                        "medetect_image_id": record["image_id"],
                    },
                    new_annotations[int(image["id"])],
                    NEW_ROOT / "images/default" / image["file_name"],
                )
            )
        for domain, image, annotations, source in sources:
            target_name = f"{domain}__{Path(image['file_name']).name}"
            target = output / "images" / split / target_name
            shutil.copy2(source, target)
            yolo_target = output / "yolo" / split / "images" / target_name
            shutil.copy2(source, yolo_target)
            status = image.get("status", "defective" if annotations else "healthy")
            image_record = dict(image)
            image_record.update(
                {
                    "id": next_image_id,
                    "file_name": f"images/{split}/{target_name}",
                    "medetect_image_id": f"{domain}__{image['medetect_image_id']}",
                    "status": status,
                    "source_domain": "reviewed_legacy" if domain == "old" else "reviewed_new_tray",
                }
            )
            payload["images"].append(image_record)
            label_lines = []
            for annotation in annotations:
                converted = dict(annotation)
                converted.update({"id": next_annotation_id, "image_id": next_image_id, "category_id": 1})
                payload["annotations"].append(converted)
                x, y, width, height = map(float, annotation["bbox"])
                label_lines.append(
                    f"0 {(x + width / 2) / image['width']:.8f} "
                    f"{(y + height / 2) / image['height']:.8f} "
                    f"{width / image['width']:.8f} {height / image['height']:.8f}"
                )
                next_annotation_id += 1
            (output / "yolo" / split / "labels" / f"{Path(target_name).stem}.txt").write_text(
                "\n".join(label_lines) + ("\n" if label_lines else "")
            )
            counts[f"{split}_images"] += 1
            counts[f"{split}_{status}"] += 1
            counts[f"{split}_instances"] += len(annotations)
            counts[f"{split}_{domain}"] += 1
            next_image_id += 1
        annotation_path = output / "annotations" / f"instances_{split}.json"
        annotation_path.write_text(json.dumps(payload, indent=2) + "\n")
        split_payloads[split] = payload
    all_payload = {
        "info": {
            "description": "Combined reviewed Hook Sinskey dataset",
            "version": "combined-reviewed-v3",
            "date_created": review_summary["reviewed_on"],
        },
        "licenses": [],
        "categories": [{"id": 1, "name": "defect", "supercategory": "defect"}],
        "images": [image for split in split_payloads.values() for image in split["images"]],
        "annotations": [annotation for split in split_payloads.values() for annotation in split["annotations"]],
    }
    (output / "annotations/instances_all.json").write_text(json.dumps(all_payload, indent=2) + "\n")
    (output / "yolo/data.yaml").write_text(
        f"path: {(output / 'yolo').as_posix()}\ntrain: train/images\nval: valid/images\ntest: test/images\n\nnames:\n  0: defect\n"
    )
    digest = hashlib.sha256()
    files = []
    for path in sorted(item for item in output.rglob("*") if item.is_file()):
        relative = path.relative_to(output).as_posix()
        file_digest = sha256(path)
        size = path.stat().st_size
        digest.update(f"{relative}\0{size}\0{file_digest}\n".encode())
        files.append({"path": relative, "bytes": size, "sha256": file_digest})
    summary = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "dataset_version": "hook_sinskey_combined_reviewed_v3",
        "status": "human_reviewed_frozen",
        "reviewer": review_summary["reviewer"],
        "reviewed_on": review_summary["reviewed_on"],
        "new_tray_reviewed_zip_sha256": review_summary["reviewed_zip_sha256"],
        "new_tray_reviewed_coco_sha256": review_summary["reviewed_coco_sha256"],
        "local_path": output.relative_to(REPO_ROOT).as_posix(),
        "counts": dict(sorted(counts.items())),
        "mask_area_qc": {"minimum": args.minimum_area_ratio, "maximum": args.maximum_area_ratio},
        "area_qc_warnings": area_qc_warnings,
        "test_split_frozen": True,
        "tree_sha256": digest.hexdigest(),
        "files": files,
    }
    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n")
    print(
        json.dumps(
            {"counts": summary["counts"], "area_qc_warnings": len(area_qc_warnings)},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
