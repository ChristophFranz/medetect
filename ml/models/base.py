"""Common adapter interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import torch
from PIL import Image

from .prediction import PredictionRecord


class ModelAdapter(ABC):
    name: str
    supports_training: bool = True

    @abstractmethod
    def predict(self, image_id: str, image: Image.Image) -> PredictionRecord:
        raise NotImplementedError

    @abstractmethod
    def training_loss(
        self, images: list[Image.Image], targets: list[dict[str, object]]
    ) -> torch.Tensor:
        raise NotImplementedError

    @abstractmethod
    def save_checkpoint(self, path: Path) -> None:
        raise NotImplementedError

    @abstractmethod
    def load_checkpoint(self, path: Path) -> None:
        raise NotImplementedError
