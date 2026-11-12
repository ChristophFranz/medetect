"""Audit why the small frozen test split may overstate generalization."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.stats import beta

REPO_ROOT = Path(__file__).resolve().parents[2]
ML_ROOT = REPO_ROOT / "ml"
DATA_ROOT = ML_ROOT / "data/local/hook_sinskey/coco_segmentation_v1/images"
TIMESTAMP = re.compile(r"^(6-[34])_(\d{8})_(\d{9})")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ML_ROOT / "experiments/test_metric_audit.json",
    )
    return parser.parse_args()


def exact_interval(successes: int, total: int, confidence: float = 0.95) -> list[float]:
    alpha = 1 - confidence
    lower = 0.0 if successes == 0 else float(beta.ppf(alpha / 2, successes, total - successes + 1))
    upper = 1.0 if successes == total else float(beta.ppf(1 - alpha / 2, successes + 1, total - successes))
    return [lower, upper]


def image_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def difference_hash(path: Path) -> int:
    with Image.open(path) as image:
        values = np.asarray(image.convert("L").resize((9, 8), Image.Resampling.LANCZOS))
    bits = values[:, 1:] > values[:, :-1]
    packed = np.packbits(bits.reshape(-1))
    return int.from_bytes(packed.tobytes(), byteorder="big")


def hamming(left: int, right: int) -> int:
    return (left ^ right).bit_count()


def capture_time(path: Path) -> tuple[str, datetime]:
    match = TIMESTAMP.match(path.name)
    if match is None:
        raise ValueError(f"cannot parse acquisition timestamp: {path.name}")
    group, date, clock = match.groups()
    parsed = datetime.strptime(date + clock, "%Y%m%d%H%M%S%f").replace(tzinfo=UTC)
    return group, parsed


def image_paths(split: str) -> list[Path]:
    return sorted(path for path in (DATA_ROOT / split).iterdir() if path.is_file())


def main() -> None:
    args = parse_args()
    benchmark = json.loads((ML_ROOT / "experiments/benchmark_results.json").read_text())
    train = image_paths("train")
    valid = image_paths("valid")
    test = image_paths("test")
    all_paths = train + valid + test

    sha_to_splits: dict[str, set[str]] = {}
    split_for = {path: path.parent.name for path in all_paths}
    for path in all_paths:
        sha_to_splits.setdefault(image_sha256(path), set()).add(split_for[path])
    exact_cross_split_duplicates = sum(
        1 for splits in sha_to_splits.values() if len(splits) > 1
    )

    train_hashes = {path: difference_hash(path) for path in train}
    nearest_visual = []
    for test_path in test:
        test_hash = difference_hash(test_path)
        nearest_path, distance = min(
            ((path, hamming(test_hash, value)) for path, value in train_hashes.items()),
            key=lambda item: item[1],
        )
        nearest_visual.append(
            {
                "test": test_path.name,
                "train": nearest_path.name,
                "dhash_hamming_64": distance,
            }
        )

    train_times: dict[str, list[tuple[Path, datetime]]] = {"6-3": [], "6-4": []}
    for path in train:
        group, timestamp = capture_time(path)
        train_times[group].append((path, timestamp))
    temporal_gaps = []
    for test_path in test:
        group, timestamp = capture_time(test_path)
        nearest_path, nearest_timestamp = min(
            train_times[group], key=lambda item: abs((timestamp - item[1]).total_seconds())
        )
        temporal_gaps.append(
            {
                "test": test_path.name,
                "train": nearest_path.name,
                "seconds": abs((timestamp - nearest_timestamp).total_seconds()),
            }
        )

    model_audits = []
    for model in benchmark["models"]:
        cm = model["classification"]["confusion_matrix"]
        correct = int(cm["tn"] + cm["tp"])
        model_audits.append(
            {
                "model": model["model"],
                "correct": correct,
                "total": benchmark["test_images"],
                "accuracy": model["classification"]["accuracy"],
                "accuracy_exact_95_ci": exact_interval(correct, benchmark["test_images"]),
                "healthy_correct": int(cm["tn"]),
                "healthy_total": int(cm["tn"] + cm["fp"]),
                "specificity_exact_95_ci": exact_interval(
                    int(cm["tn"]), int(cm["tn"] + cm["fp"])
                ),
            }
        )

    distances = [item["dhash_hamming_64"] for item in nearest_visual]
    gaps = [item["seconds"] for item in temporal_gaps]
    output = {
        "schema_version": 1,
        "purpose": "risk audit only; no model selection or test retuning",
        "test_images": len(test),
        "test_class_counts": {"defective": 18, "healthy": 6},
        "accuracy_step_per_image": 1 / len(test),
        "always_defective_baseline": {"correct": 18, "accuracy": 18 / len(test)},
        "acquisition_group_rule": {
            "rule": "6-4 => defective; 6-3 => healthy",
            "correct": len(all_paths),
            "total": len(all_paths),
            "accuracy": 1.0,
            "warning": "filenames are not model inputs, but group-correlated visual cues may be",
        },
        "model_uncertainty": model_audits,
        "split_similarity": {
            "exact_cross_split_duplicate_hashes": exact_cross_split_duplicates,
            "dhash_note": "64-bit perceptual-hash distance is a screening heuristic, not proof of duplication",
            "nearest_test_to_train_dhash": {
                "minimum": min(distances),
                "median": float(np.median(distances)),
                "maximum": max(distances),
                "at_or_below_5": sum(distance <= 5 for distance in distances),
                "at_or_below_10": sum(distance <= 10 for distance in distances),
            },
            "nearest_pairs": sorted(nearest_visual, key=lambda item: item["dhash_hamming_64"])[:10],
        },
        "temporal_proximity": {
            "note": "nearest same-acquisition-group training capture based on filename timestamp",
            "minimum_seconds": min(gaps),
            "median_seconds": float(np.median(gaps)),
            "maximum_seconds": max(gaps),
            "within_30_seconds": sum(gap <= 30 for gap in gaps),
            "within_120_seconds": sum(gap <= 120 for gap in gaps),
            "nearest_pairs": sorted(temporal_gaps, key=lambda item: item["seconds"])[:10],
        },
    }
    destination = args.output.expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
