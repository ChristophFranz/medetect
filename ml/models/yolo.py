"""Read-only inherited Hook Sinskey YOLO adapter."""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from ultralytics import YOLO

from .base import ModelAdapter
from .device import select_device
from .prediction import PredictionRecord
from .preprocessing import prepare_sample, restore_boxes


class LegacyYoloAdapter(ModelAdapter):
    name = "legacy_yolo"
    supports_training = False

    def __init__(
        self,
        checkpoint: Path,
        *,
        confidence_threshold: float = 0.1,
        device: str = "auto",
        maximum_edge: int = 640,
    ) -> None:
        self.device = select_device(device)
        self.confidence_threshold = confidence_threshold
        self.maximum_edge = maximum_edge
        self.model = YOLO(checkpoint)

    def predict(self, image_id: str, image: Image.Image) -> PredictionRecord:
        target = {
            "boxes": torch.zeros((0, 4)),
            "labels": torch.zeros((0,), dtype=torch.int64),
            "masks": torch.zeros((0, image.height, image.width), dtype=torch.uint8),
        }
        sample = prepare_sample(image, target, self.maximum_edge)
        source = np.transpose(sample.image.mul(255).byte().numpy(), (1, 2, 0))
        start = time.perf_counter()
        result = self.model.predict(
            source=source,
            imgsz=self.maximum_edge,
            conf=self.confidence_threshold,
            device=str(self.device),
            verbose=False,
        )[0]
        classes = result.boxes.cls.detach().cpu().to(torch.int64)
        keep = classes == 0
        scores = result.boxes.conf.detach().cpu()[keep]
        boxes = restore_boxes(result.boxes.xyxy.detach().cpu()[keep], sample.info)
        return PredictionRecord(
            image_id=image_id,
            tool="hook_sinskey",
            model=self.name,
            defective=bool(scores.numel()),
            confidence=float(scores.max()) if scores.numel() else 0.0,
            boxes=boxes.tolist(),
            masks=[],
            instance_scores=scores.tolist(),
            latency_ms=(time.perf_counter() - start) * 1000,
        )

    def training_loss(self, images, targets) -> torch.Tensor:
        raise NotImplementedError("the inherited YOLO checkpoint remains unchanged")

    def save_checkpoint(self, path: Path) -> None:
        raise NotImplementedError("the inherited YOLO checkpoint remains unchanged")

    def load_checkpoint(self, path: Path) -> None:
        raise NotImplementedError("the inherited YOLO checkpoint remains unchanged")
