"""Collect low-threshold validation candidates from one trained model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ml.benchmark.training import TRAINABLE_MODELS
from ml.data.coco_dataset import FrozenCocoDataset
from ml.models.device import seed_everything
from ml.models.factory import build_adapter

REPO_ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("model", choices=TRAINABLE_MODELS)
    parser.add_argument("--device", choices=("auto", "mps", "cpu"), default="auto")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    seed_everything(42)
    checkpoint = REPO_ROOT / "ml/runs/benchmark" / args.model / "best.pt"
    if not checkpoint.is_file():
        raise SystemExit(f"trained checkpoint missing: {checkpoint}")
    adapter = build_adapter(args.model, device=args.device)
    adapter.load_checkpoint(checkpoint)
    adapter.score_threshold = 0.05
    if hasattr(adapter, "minimum_mask_area"):
        adapter.minimum_mask_area = 1
    dataset = FrozenCocoDataset("valid")
    output = REPO_ROOT / "ml/runs/benchmark" / args.model / "validation_candidates.jsonl"
    with output.open("w") as handle:
        for index in range(len(dataset)):
            image, target = dataset[index]
            record = adapter.predict(str(target["image_id"]), image).to_dict()
            handle.write(json.dumps(record, separators=(",", ":")) + "\n")
            print(
                json.dumps(
                    {
                        "model": args.model,
                        "validation_image": index + 1,
                        "total": len(dataset),
                    }
                ),
                flush=True,
            )
    print(output.relative_to(REPO_ROOT))


if __name__ == "__main__":
    main()
