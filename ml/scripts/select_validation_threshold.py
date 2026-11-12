"""Freeze one model's operating point from validation candidates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ml.benchmark.thresholds import select_thresholds
from ml.benchmark.training import TRAINABLE_MODELS

REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("model", choices=TRAINABLE_MODELS)
    args = parser.parse_args()
    candidates = (
        REPO_ROOT
        / "ml/runs/benchmark"
        / args.model
        / "validation_candidates.jsonl"
    )
    result = select_thresholds(args.model, candidates)
    output = REPO_ROOT / "ml/runs/benchmark" / args.model / "threshold.json"
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
