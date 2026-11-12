"""Train the provisional combined tray detector from the inherited checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml
from ultralytics import YOLO

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO_ROOT / "ml/configs/tray_yolo_provisional.yaml"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--epochs", type=int)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text())
    model_path = config.pop("model")
    if args.epochs is not None:
        config["epochs"] = args.epochs
    for key in ("data", "project"):
        path = Path(config[key])
        if not path.is_absolute():
            config[key] = str((REPO_ROOT / path).resolve())
    model = YOLO(model_path)
    model.train(**config)


if __name__ == "__main__":
    main()
