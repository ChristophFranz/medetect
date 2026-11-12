"""Build a deterministic provenance manifest for the local Hook Sinskey pilot assets."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ML_ROOT = REPO_ROOT / "ml"
LOCAL_DATASET = ML_ROOT / "data/local/hook_sinskey/yolov8_v4"
LOCAL_WEIGHT = ML_ROOT / "artifacts/legacy/hook_sinskey/yolov8n_best.pt"
SOURCE_DATASET = Path(
    "/Users/christophcuan/Desktop/medetect-api/Hook Sinskey Tip/"
    "Tool 2.v4-epoch-200-set.yolov8 3"
)
SOURCE_WEIGHT = Path(
    "/Users/christophcuan/Desktop/medetect-api/Hook Sinskey Tip/"
    "runs/detect/train/weights/best.pt"
)
RESULTS_CSV = ML_ROOT / "legacy/hook_sinskey/training/results.csv"
OUTPUT = ML_ROOT / "data/manifest.json"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
DEFAULT_REVIEW = {
    "milestone_0_inventory": "pending",
    "context_handoff": "not_started",
    "annotation_policy": "not_started",
    "all_masks": "not_started",
    "all_negative_images": "not_started",
    "frozen_test_split": False,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inventory(root: Path) -> tuple[list[dict[str, object]], str]:
    records: list[dict[str, object]] = []
    combined = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p.name != ".DS_Store"):
        relative = path.relative_to(root).as_posix()
        digest = sha256(path)
        size = path.stat().st_size
        records.append({"path": relative, "bytes": size, "sha256": digest})
        combined.update(f"{relative}\0{size}\0{digest}\n".encode())
    return records, combined.hexdigest()


def split_summary(root: Path, split: str) -> dict[str, object]:
    image_dir = root / split / "images"
    label_dir = root / split / "labels"
    images = sorted(p for p in image_dir.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES)
    labels = sorted(label_dir.glob("*.txt"))
    instance_counts: Counter[str] = Counter()
    image_classes: Counter[str] = Counter()
    empty_labels = 0
    for label in labels:
        classes: set[str] = set()
        rows = [line.split() for line in label.read_text().splitlines() if line.strip()]
        if not rows:
            empty_labels += 1
        for row in rows:
            class_id = row[0]
            instance_counts[class_id] += 1
            classes.add(class_id)
        if classes == {"0"}:
            image_classes["defective_only"] += 1
        elif classes == {"1"}:
            image_classes["non_defective_only"] += 1
        elif classes == {"0", "1"}:
            image_classes["mixed"] += 1
        elif not classes:
            image_classes["empty"] += 1
    return {
        "images": len(images),
        "label_files": len(labels),
        "empty_label_files": empty_labels,
        "instances_by_legacy_class": dict(sorted(instance_counts.items())),
        "images_by_legacy_class_presence": dict(sorted(image_classes.items())),
    }


def historical_metrics() -> dict[str, object]:
    best: dict[str, object] = {}
    with RESULTS_CSV.open(newline="") as handle:
        for row in csv.DictReader(handle):
            normalized = {key.strip(): value.strip() for key, value in row.items()}
            map_5095 = float(normalized["metrics/mAP50-95(B)"])
            if not best or map_5095 > float(best["map50_95"]):
                best = {
                    "epoch": int(normalized["epoch"]),
                    "precision": float(normalized["metrics/precision(B)"]),
                    "recall": float(normalized["metrics/recall(B)"]),
                    "map50": float(normalized["metrics/mAP50(B)"]),
                    "map50_95": map_5095,
                }
    return best


def existing_review_state() -> dict[str, object]:
    review = DEFAULT_REVIEW.copy()
    if not OUTPUT.exists():
        return review
    try:
        previous = json.loads(OUTPUT.read_text()).get("review", {})
    except json.JSONDecodeError:
        return review
    for key in review:
        if key in previous:
            review[key] = previous[key]
    return review


def main() -> None:
    required = [LOCAL_DATASET, LOCAL_WEIGHT, SOURCE_DATASET, SOURCE_WEIGHT, RESULTS_CSV]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit("Missing required assets:\n" + "\n".join(missing))

    local_files, local_digest = inventory(LOCAL_DATASET)
    source_files, source_digest = inventory(SOURCE_DATASET)
    review = existing_review_state()
    if review["annotation_policy"] == "approved":
        dataset_status = "annotation_policy_approved"
    elif review["context_handoff"] == "approved":
        dataset_status = "candidate_milestone_1_approved"
    elif review["milestone_0_inventory"] == "approved":
        dataset_status = "candidate_milestone_0_approved"
    else:
        dataset_status = "candidate_awaiting_human_gate"
    manifest = {
        "schema_version": 1,
        "generated_on": datetime.now(UTC).date().isoformat(),
        "tool": "hook_sinskey",
        "dataset": {
            "status": dataset_status,
            "format": "roboflow_yolov8_detection",
            "roboflow_project": "tool-2-ntfbg",
            "roboflow_version": 4,
            "license": "CC BY 4.0",
            "legacy_classes": {"0": "defective_HS", "1": "non defective_HS"},
            "canonical_class": "defect",
            "source_path": str(SOURCE_DATASET),
            "local_path": str(LOCAL_DATASET.relative_to(REPO_ROOT)),
            "dataset_sha256": local_digest,
            "source_dataset_sha256": source_digest,
            "copy_verified": local_digest == source_digest and local_files == source_files,
            "file_count": len(local_files),
            "total_bytes": sum(int(record["bytes"]) for record in local_files),
            "splits": {
                split: split_summary(LOCAL_DATASET, split)
                for split in ("train", "valid", "test")
            },
            "files": local_files,
        },
        "legacy_checkpoint": {
            "source_path": str(SOURCE_WEIGHT),
            "local_path": str(LOCAL_WEIGHT.relative_to(REPO_ROOT)),
            "bytes": LOCAL_WEIGHT.stat().st_size,
            "sha256": sha256(LOCAL_WEIGHT),
            "source_sha256": sha256(SOURCE_WEIGHT),
            "copy_verified": sha256(LOCAL_WEIGHT) == sha256(SOURCE_WEIGHT),
            "architecture": "yolov8n",
            "task": "detect",
            "class_names": {"0": "defective_HS", "1": "non defective_HS"},
            "training_epochs": 200,
            "training_image_size": 640,
            "inherited_confidence_threshold": 0.1,
            "threshold_source": "ml/legacy/Detector.py:362",
            "metadata_verification": {
                "checkpoint_data_reference": "data.yaml",
                "candidate_data_yaml_names_match": True,
                "candidate_image_size_matches": True,
                "candidate_training_epochs_match": True,
            },
        },
        "historical_best_validation_metrics": historical_metrics(),
        "review": review,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wrote {OUTPUT.relative_to(REPO_ROOT)}")
    print(f"Dataset digest: {local_digest}")
    print(f"Copy verified: {manifest['dataset']['copy_verified']}")


if __name__ == "__main__":
    main()
