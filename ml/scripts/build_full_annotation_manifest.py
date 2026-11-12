"""Build the deterministic Hook Sinskey full-dataset annotation manifest."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from select_annotation_sample import inventory_split, preserve_workflow_state

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET = REPO_ROOT / "ml/data/local/hook_sinskey/yolov8_v4"
DATA_MANIFEST = REPO_ROOT / "ml/data/manifest.json"
OUTPUT = REPO_ROOT / "ml/annotation/full_dataset_manifest.json"


def build_full_manifest() -> dict[str, object]:
    data_manifest = json.loads(DATA_MANIFEST.read_text())
    hashes = {
        record["path"]: record["sha256"]
        for record in data_manifest["dataset"]["files"]
    }
    images: list[dict[str, object]] = []
    counts: dict[str, dict[str, int]] = {}
    source_splits: dict[str, set[str]] = defaultdict(set)
    hash_splits: dict[str, set[str]] = defaultdict(set)

    for split in ("train", "valid", "test"):
        split_records = inventory_split(DATASET, split)
        split_counts = Counter(record["status"] for record in split_records)
        counts[split] = {
            "images": len(split_records),
            "defective": split_counts["defective"],
            "healthy": split_counts["healthy"],
            "defect_instances": sum(
                int(record["legacy_defect_instance_count"])
                for record in split_records
            ),
        }
        for record in split_records:
            relative_image = Path(str(record["image_path"])).relative_to(
                "ml/data/local/hook_sinskey/yolov8_v4"
            ).as_posix()
            image_hash = hashes[relative_image]
            source_capture_id = Path(str(record["image_path"])).stem.split(".rf.")[0]
            record["image_sha256"] = image_hash
            record["source_capture_id"] = source_capture_id
            source_splits[source_capture_id].add(split)
            hash_splits[image_hash].add(split)
            images.append(record)

    images.sort(key=lambda record: str(record["image_id"]))
    source_leakage = {
        key: sorted(value) for key, value in source_splits.items() if len(value) > 1
    }
    exact_hash_leakage = {
        key: sorted(value) for key, value in hash_splits.items() if len(value) > 1
    }
    return {
        "schema_version": 1,
        "package_name": "hook_sinskey_full_dataset_candidates",
        "tool": "hook_sinskey",
        "canonical_class": "defect",
        "dataset_sha256": data_manifest["dataset"]["dataset_sha256"],
        "seed": 42,
        "included_splits": ["train", "valid", "test"],
        "excluded_splits": [],
        "selection": "all_images_in_frozen_inherited_splits",
        "counts": counts,
        "sample_size": len(images),
        "images": images,
        "leakage_audit": {
            "source_capture_ids_in_multiple_splits": source_leakage,
            "exact_image_hashes_in_multiple_splits": exact_hash_leakage,
            "passed": not source_leakage and not exact_hash_leakage,
        },
        "candidate_generation": {"status": "not_started"},
        "review": {
            "all_masks": "pending",
            "all_negative_images": "pending",
            "test_split_frozen": False,
            "reviewer": None,
            "reviewed_on": None,
        },
    }


def main() -> None:
    result = build_full_manifest()
    if OUTPUT.exists():
        result = preserve_workflow_state(result, json.loads(OUTPUT.read_text()))
    if result["sample_size"] != 240:
        raise SystemExit(f"expected 240 images, got {result['sample_size']}")
    if not result["leakage_audit"]["passed"]:
        raise SystemExit("cross-split leakage detected; inspect full dataset manifest")
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Wrote {OUTPUT.relative_to(REPO_ROOT)}")
    print(json.dumps(result["counts"], sort_keys=True))
    print("Cross-split source/hash leakage: none")


if __name__ == "__main__":
    main()
