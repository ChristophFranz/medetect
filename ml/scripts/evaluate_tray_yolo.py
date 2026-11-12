"""Evaluate a tray YOLO checkpoint on combined, old, and redesigned-tray tests."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from ultralytics import YOLO

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = REPO_ROOT / "ml/data/local/tray_detection/combined_provisional_v1"


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument(
        "--output", type=Path, default=REPO_ROOT / "ml/experiments/tray_yolo_provisional_results.json"
    )
    args = parser.parse_args()
    checkpoint = args.checkpoint.resolve()
    model = YOLO(checkpoint)
    evaluations = []
    domains = {
        "combined": DATA_ROOT / "data.yaml",
        "inherited_tray": DATA_ROOT / "old_test.yaml",
        "redesigned_tray": DATA_ROOT / "new_test.yaml",
    }
    for domain, data in domains.items():
        metrics = model.val(
            data=str(data), split="test", imgsz=640, batch=16, device="cpu",
            workers=0, plots=False, project=str(REPO_ROOT / "ml/runs/tray_yolo/evaluation"),
            name=domain, exist_ok=True, verbose=False,
        )
        evaluations.append(
            {
                "domain": domain,
                "precision": float(metrics.box.mp),
                "recall": float(metrics.box.mr),
                "map50": float(metrics.box.map50),
                "map50_95": float(metrics.box.map),
                "map50_95_by_class": {
                    model.names[index]: float(value)
                    for index, value in enumerate(metrics.box.maps)
                },
                "speed_ms_per_image": {key: float(value) for key, value in metrics.speed.items()},
            }
        )
    try:
        checkpoint_record = checkpoint.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        checkpoint_record = checkpoint.as_posix()
    result = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "status": "provisional_unreviewed_new_tray_boxes",
        "checkpoint": checkpoint_record,
        "checkpoint_sha256": file_hash(checkpoint),
        "test_split_used_for_tuning": False,
        "evaluations": evaluations,
    }
    args.output.resolve().write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
