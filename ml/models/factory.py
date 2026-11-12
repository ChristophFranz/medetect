"""Configuration-driven construction of benchmark adapters."""

from __future__ import annotations

from pathlib import Path

import yaml

from .base import ModelAdapter
from .detr import DetrDetectionAdapter, DetrSegmentationAdapter
from .mask_rcnn import MaskRcnnAdapter
from .yolo import LegacyYoloAdapter

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO_ROOT / "ml/configs/models.yaml"


def load_model_config(path: Path = DEFAULT_CONFIG) -> dict:
    return yaml.safe_load(path.read_text())


def build_adapter(
    name: str, *, device: str | None = None, config_path: Path = DEFAULT_CONFIG
) -> ModelAdapter:
    config = load_model_config(config_path)
    selected_device = device or str(config["device"])
    maximum_edge = int(config["maximum_edge"])
    if name == "legacy_yolo":
        values = config[name]
        return LegacyYoloAdapter(
            REPO_ROOT / values["checkpoint"],
            confidence_threshold=float(values["confidence_threshold"]),
            device=selected_device,
            maximum_edge=maximum_edge,
        )
    if name == "detr_detection":
        values = config[name]
        return DetrDetectionAdapter(
            model_id=values["model_id"],
            revision=values["revision"],
            use_safetensors=bool(values["use_safetensors"]),
            cache_dir=REPO_ROOT / "ml/artifacts/huggingface",
            score_threshold=float(values["score_threshold"]),
            device=selected_device,
            maximum_edge=maximum_edge,
        )
    if name == "detr_segmentation":
        values = config[name]
        return DetrSegmentationAdapter(
            model_id=values["model_id"],
            revision=values["revision"],
            use_safetensors=bool(values["use_safetensors"]),
            cache_dir=REPO_ROOT / "ml/artifacts/huggingface",
            score_threshold=float(values["score_threshold"]),
            mask_threshold=float(values["mask_threshold"]),
            minimum_mask_area=int(values["minimum_mask_area"]),
            device=selected_device,
            maximum_edge=maximum_edge,
        )
    if name == "mask_rcnn":
        values = config[name]
        return MaskRcnnAdapter(
            score_threshold=float(values["score_threshold"]),
            mask_threshold=float(values["mask_threshold"]),
            minimum_mask_area=int(values["minimum_mask_area"]),
            device=selected_device,
            maximum_edge=maximum_edge,
        )
    raise ValueError(f"unknown model adapter: {name}")
