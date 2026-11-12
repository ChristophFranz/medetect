"""Validate local smoke outputs and write tracked Milestone 4 provenance."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ML_ROOT = REPO_ROOT / "ml"
MODELS = ("legacy_yolo", "detr_detection", "detr_segmentation", "mask_rcnn")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    results = []
    for model in MODELS:
        path = ML_ROOT / "runs/smoke" / model / "summary.json"
        if not path.is_file():
            raise SystemExit(f"missing smoke result: {path.relative_to(REPO_ROOT)}")
        result = json.loads(path.read_text())
        if result["status"] != "passed":
            raise SystemExit(f"smoke test did not pass: {model}")
        if result["test_split_accessed"]:
            raise SystemExit(f"smoke test accessed frozen test data: {model}")
        if not result["checkpoint_reload_ok"]:
            raise SystemExit(f"checkpoint reload failed: {model}")
        results.append(result)

    frozen = json.loads((ML_ROOT / "data/frozen_hook_sinskey_v1.json").read_text())
    config = ML_ROOT / "configs/models.yaml"
    payload = {
        "schema_version": 1,
        "event": "milestone_4_smoke_tests",
        "date": "2026-09-24",
        "tool": "hook_sinskey",
        "git_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip(),
        "dataset_version": frozen["dataset_version"],
        "dataset_sha256": frozen["canonical_tree_sha256"],
        "config": config.relative_to(REPO_ROOT).as_posix(),
        "config_sha256": sha256(config),
        "seed": 42,
        "maximum_edge": 640,
        "test_split_accessed": False,
        "purpose": "mechanical validation only; not performance evidence",
        "models": results,
        "status": "passed_awaiting_prediction_review",
    }
    output = ML_ROOT / "experiments/smoke_results.json"
    output.write_text(json.dumps(payload, indent=2) + "\n")

    registry = ML_ROOT / "experiments/registry.jsonl"
    event = {
        "event": payload["event"],
        "date": payload["date"],
        "milestone": 4,
        "tool": payload["tool"],
        "dataset_version": payload["dataset_version"],
        "dataset_sha256": payload["dataset_sha256"],
        "config_sha256": payload["config_sha256"],
        "models": list(MODELS),
        "device": "mps",
        "test_split_accessed": False,
        "summary": output.relative_to(REPO_ROOT).as_posix(),
        "status": payload["status"],
    }
    lines = registry.read_text().splitlines()
    lines = [
        line
        for line in lines
        if json.loads(line).get("event") != "milestone_4_smoke_tests"
    ]
    lines.append(json.dumps(event, separators=(",", ":")))
    registry.write_text("\n".join(lines) + "\n")
    print(f"Wrote {output.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
