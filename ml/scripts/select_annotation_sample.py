"""Select the deterministic 20-image Hook Sinskey annotation-policy sample."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATASET = REPO_ROOT / "ml/data/local/hook_sinskey/yolov8_v4"
DEFAULT_CONFIG = REPO_ROOT / "ml/annotation/sample_config.yaml"
DEFAULT_OUTPUT = REPO_ROOT / "ml/annotation/pilot_sample.json"
IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png")


def evenly_spaced(records: list[dict[str, object]], count: int) -> list[dict[str, object]]:
    if count < 0 or count > len(records):
        raise ValueError(f"cannot select {count} records from {len(records)}")
    if count == 0:
        return []
    if count == 1:
        return [records[(len(records) - 1) // 2]]
    indices = [round(index * (len(records) - 1) / (count - 1)) for index in range(count)]
    if len(set(indices)) != count:
        raise ValueError("evenly-spaced selection produced duplicate indices")
    return [records[index] for index in indices]


def image_for_label(label: Path, image_dir: Path) -> Path:
    for suffix in IMAGE_SUFFIXES:
        candidate = image_dir / f"{label.stem}{suffix}"
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"no image for {label}")


def yolo_box_to_xyxy(
    row: list[str], image_width: int, image_height: int
) -> list[float]:
    center_x, center_y, width, height = map(float, row[1:5])
    x1 = max(0.0, (center_x - width / 2) * image_width)
    y1 = max(0.0, (center_y - height / 2) * image_height)
    x2 = min(float(image_width), (center_x + width / 2) * image_width)
    y2 = min(float(image_height), (center_y + height / 2) * image_height)
    if x2 <= x1 or y2 <= y1:
        raise ValueError(f"invalid YOLO box: {row}")
    return [round(value, 4) for value in (x1, y1, x2, y2)]


def inventory_split(dataset: Path, split: str) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    label_dir = dataset / split / "labels"
    image_dir = dataset / split / "images"
    for label in sorted(label_dir.glob("*.txt")):
        image = image_for_label(label, image_dir)
        rows = [line.split() for line in label.read_text().splitlines() if line.strip()]
        if any(len(row) < 5 for row in rows):
            raise ValueError(f"invalid YOLO row in {label}")
        with Image.open(image) as opened:
            width, height = opened.size
        defect_rows = [row for row in rows if row[0] == "0"]
        healthy_rows = [row for row in rows if row[0] == "1"]
        if defect_rows and healthy_rows:
            raise ValueError(f"mixed defective/healthy labels are not supported: {label}")
        if not defect_rows and not healthy_rows:
            raise ValueError(f"empty legacy label: {label}")
        status = "defective" if defect_rows else "healthy"
        boxes = [yolo_box_to_xyxy(row, width, height) for row in defect_rows]
        normalized_areas = [float(row[3]) * float(row[4]) for row in defect_rows]
        records.append(
            {
                "image_id": f"{split}/{label.stem}",
                "split": split,
                "status": status,
                "image_path": image.relative_to(REPO_ROOT).as_posix(),
                "label_path": label.relative_to(REPO_ROOT).as_posix(),
                "width": width,
                "height": height,
                "legacy_defect_boxes_xyxy": boxes,
                "legacy_defect_instance_count": len(defect_rows),
                "legacy_healthy_box_count": len(healthy_rows),
                "max_normalized_defect_box_area": max(normalized_areas, default=0.0),
                "review_state": "candidate_unreviewed",
                "ambiguity_flags": [],
            }
        )
    return records


def select_sample(
    dataset: Path, config: dict[str, object], dataset_hash: str
) -> dict[str, object]:
    selected: list[dict[str, object]] = []
    available_counts: dict[str, dict[str, int]] = {}
    for split, split_quotas in config["quotas"].items():
        records = inventory_split(dataset, split)
        available_counts[split] = {}
        for status, quota in split_quotas.items():
            candidates = [record for record in records if record["status"] == status]
            available_counts[split][status] = len(candidates)
            if status == "defective":
                candidates.sort(
                    key=lambda record: (
                        record["max_normalized_defect_box_area"],
                        record["image_id"],
                    )
                )
            else:
                candidates.sort(key=lambda record: record["image_id"])
            chosen = evenly_spaced(candidates, int(quota))
            for rank, record in enumerate(chosen):
                record["stratum"] = f"{split}_{status}"
                record["selection_rank"] = rank
                selected.append(record)

    selected.sort(key=lambda record: record["image_id"])
    return {
        "schema_version": 1,
        "tool": config["tool"],
        "canonical_class": config["canonical_class"],
        "dataset_sha256": dataset_hash,
        "seed": config["seed"],
        "excluded_splits": config["excluded_splits"],
        "selection": config["selection"],
        "quotas": config["quotas"],
        "available_counts": available_counts,
        "sample_size": len(selected),
        "images": selected,
        "candidate_generation": {
            "status": "not_started",
            "model": config["sam2"],
        },
        "review": {
            "policy": "pending",
            "all_sample_annotations": "pending",
            "reviewer": None,
            "reviewed_on": None,
        },
    }


def preserve_workflow_state(
    selected: dict[str, object], previous: dict[str, object]
) -> dict[str, object]:
    selected_ids = [record["image_id"] for record in selected["images"]]
    previous_ids = [record["image_id"] for record in previous.get("images", [])]
    if (
        selected["dataset_sha256"] != previous.get("dataset_sha256")
        or selected_ids != previous_ids
    ):
        return selected

    selected["candidate_generation"] = previous.get(
        "candidate_generation", selected["candidate_generation"]
    )
    selected["review"] = previous.get("review", selected["review"])
    previous_by_id = {record["image_id"]: record for record in previous["images"]}
    for record in selected["images"]:
        old_record = previous_by_id[record["image_id"]]
        for key in ("review_state", "ambiguity_flags", "reviewer", "reviewed_on", "notes"):
            if key in old_record:
                record[key] = old_record[key]
    return selected


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = yaml.safe_load(args.config.read_text())
    manifest = json.loads((REPO_ROOT / "ml/data/manifest.json").read_text())
    sample = select_sample(args.dataset, config, manifest["dataset"]["dataset_sha256"])
    if args.output.exists():
        sample = preserve_workflow_state(sample, json.loads(args.output.read_text()))
    if sample["sample_size"] != 20:
        raise SystemExit(f"expected a 20-image sample, got {sample['sample_size']}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(sample, indent=2) + "\n")
    print(f"Wrote {args.output.relative_to(REPO_ROOT)}")
    print(f"Selected {sample['sample_size']} images; excluded splits: {sample['excluded_splits']}")


if __name__ == "__main__":
    main()
