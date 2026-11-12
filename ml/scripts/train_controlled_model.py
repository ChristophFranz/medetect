"""Train one frozen-configuration Milestone 5 model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ml.benchmark.training import CONFIG_PATH, TRAINABLE_MODELS, train_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("model", choices=TRAINABLE_MODELS)
    parser.add_argument("--device", choices=("auto", "mps", "cpu"), default="auto")
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--max-epochs", type=int)
    parser.add_argument("--limit-train", type=int)
    parser.add_argument("--limit-valid", type=int)
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--dataset-root", type=Path)
    parser.add_argument("--dataset-record", type=Path)
    parser.add_argument("--initial-checkpoint", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = train_model(
        args.model,
        device=args.device,
        config_path=args.config.resolve(),
        output_root=args.output_root.resolve() if args.output_root else None,
        max_epochs_override=args.max_epochs,
        limit_train=args.limit_train,
        limit_valid=args.limit_valid,
        resume=not args.no_resume,
        dataset_root=args.dataset_root.resolve() if args.dataset_root else None,
        dataset_record=args.dataset_record.resolve() if args.dataset_record else None,
        initial_checkpoint=(
            args.initial_checkpoint.resolve() if args.initial_checkpoint else None
        ),
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
