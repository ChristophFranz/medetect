"""Tip-versus-handle endpoint selection for a reviewed full-tool box."""

from __future__ import annotations

from pathlib import Path

import torch
from PIL import Image, ImageOps
from torch import nn
from torchvision import models, transforms

from ml.scripts.build_endpoint_selector_dataset import endpoint_crop_box


class ResizePad:
    def __init__(self, size: int) -> None:
        self.size = size

    def __call__(self, image: Image.Image) -> Image.Image:
        image = image.copy()
        image.thumbnail((self.size, self.size), Image.Resampling.BILINEAR)
        canvas = Image.new("RGB", (self.size, self.size), (124, 116, 104))
        canvas.paste(image, ((self.size - image.width) // 2, (self.size - image.height) // 2))
        return canvas


def endpoint_architecture() -> nn.Module:
    model = models.resnet50(weights=None)
    model.fc = nn.Linear(model.fc.in_features, 2)
    return model


def initialize_from_mask_rcnn(checkpoint: Path) -> nn.Module:
    model = models.resnet50(weights=None)
    state = torch.load(checkpoint, map_location="cpu", weights_only=True)
    backbone = {
        key.removeprefix("backbone.body."): value
        for key, value in state.items()
        if key.startswith("backbone.body.")
    }
    incompatible = model.load_state_dict(backbone, strict=False)
    if set(incompatible.missing_keys) != {"fc.weight", "fc.bias"} or incompatible.unexpected_keys:
        raise RuntimeError(f"unexpected backbone keys: {incompatible}")
    for parameter in model.parameters():
        parameter.requires_grad = False
    model.fc = nn.Linear(model.fc.in_features, 2)
    return model


class EndpointSelector:
    def __init__(self, model: nn.Module, image_size: int, device: torch.device) -> None:
        self.model = model.to(device).eval()
        self.device = device
        self.transform = transforms.Compose(
            [
                ResizePad(image_size),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ]
        )

    @classmethod
    def from_checkpoint(
        cls, checkpoint: Path, image_size: int, device: torch.device
    ) -> EndpointSelector:
        payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
        model = endpoint_architecture()
        model.load_state_dict(payload["model"])
        return cls(model, image_size, device)

    def score_images(self, images: list[Image.Image]) -> list[float]:
        batch = torch.stack([self.transform(image.convert("RGB")) for image in images]).to(self.device)
        with torch.inference_mode():
            scores = self.model(batch).softmax(dim=1)[:, 1].cpu().tolist()
        return [float(score) for score in scores]

    def select_from_box(
        self,
        image: Image.Image,
        box_xyxy: list[float],
        *,
        review_margin_threshold: float,
    ) -> tuple[Image.Image, dict[str, object]]:
        candidates: dict[str, Image.Image] = {}
        crop_boxes: dict[str, list[int]] = {}
        for side in ("left", "right"):
            crop_box = endpoint_crop_box(box_xyxy, image.size, side)
            crop = image.crop(crop_box)
            if side == "left":
                crop = ImageOps.mirror(crop)
            candidates[side] = crop
            crop_boxes[side] = list(crop_box)
        scores = self.score_images([candidates["left"], candidates["right"]])
        selected_side = "left" if scores[0] >= scores[1] else "right"
        margin = abs(scores[0] - scores[1])
        record = {
            "selected_side": selected_side,
            "tip_scores": {"left": scores[0], "right": scores[1]},
            "score_margin": margin,
            "review_required": margin < review_margin_threshold,
            "review_reason": "low_endpoint_score_margin" if margin < review_margin_threshold else None,
            "source_crop_xyxy": crop_boxes[selected_side],
            "canonicalized_by_horizontal_flip": selected_side == "left",
        }
        return candidates[selected_side], record
