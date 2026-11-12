"""Freeze validation-selected thresholds before any test inference."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from ml.benchmark.training import TRAINABLE_MODELS

REPO_ROOT = Path(__file__).resolve().parents[2]
ML_ROOT = REPO_ROOT / "ml"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    frozen_dataset = json.loads((ML_ROOT / "data/frozen_hook_sinskey_v1.json").read_text())
    models = [
        {
            "model": "legacy_yolo",
            "score_threshold": 0.1,
            "minimum_mask_area": None,
            "threshold_source": "inherited operating point; unchanged",
            "checkpoint": "ml/artifacts/legacy/hook_sinskey/yolov8n_best.pt",
            "checkpoint_sha256": "016d6b46669ca9d2888d9411e80107df7748192c6df3076c217a1f1230db963b",
        }
    ]
    for model in TRAINABLE_MODELS:
        run_dir = ML_ROOT / "runs/benchmark" / model
        threshold_path = run_dir / "threshold.json"
        training_path = run_dir / "training_summary.json"
        if not threshold_path.is_file() or not training_path.is_file():
            raise SystemExit(f"training/threshold selection incomplete: {model}")
        threshold = json.loads(threshold_path.read_text())
        training = json.loads(training_path.read_text())
        if threshold["test_split_accessed"] or training["test_split_accessed"]:
            raise SystemExit(f"pre-freeze test access reported: {model}")
        checkpoint = REPO_ROOT / training["best_checkpoint"]
        if sha256(checkpoint) != training["best_checkpoint_sha256"]:
            raise SystemExit(f"best checkpoint hash mismatch: {model}")
        models.append(
            {
                **threshold,
                "threshold_source": "validation-only grid search",
                "training_summary": training_path.relative_to(REPO_ROOT).as_posix(),
                "training_summary_sha256": sha256(training_path),
                "checkpoint": training["best_checkpoint"],
                "checkpoint_sha256": training["best_checkpoint_sha256"],
            }
        )
    payload = {
        "schema_version": 1,
        "event": "validation_threshold_freeze",
        "frozen_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "dataset_version": frozen_dataset["dataset_version"],
        "dataset_sha256": frozen_dataset["canonical_tree_sha256"],
        "selection_split": "valid",
        "test_split_accessed": False,
        "models": models,
        "status": "frozen_before_test",
    }
    output = ML_ROOT / "experiments/frozen_thresholds.json"
    output.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"Wrote {output.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
