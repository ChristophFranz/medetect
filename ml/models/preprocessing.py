"""Shared aspect-preserving resize and bottom/right padding contract."""

from __future__ import annotations

from dataclasses import dataclass

import torch
from PIL import Image
from torchvision.transforms import functional as tvf


@dataclass(slots=True, frozen=True)
class TransformInfo:
    original_height: int
    original_width: int
    resized_height: int
    resized_width: int
    padded_size: int
    scale_x: float
    scale_y: float


@dataclass(slots=True)
class PreparedSample:
    image: torch.Tensor
    boxes: torch.Tensor
    labels: torch.Tensor
    masks: torch.Tensor
    valid_pixels: torch.Tensor
    info: TransformInfo


def prepare_sample(
    image: Image.Image,
    target: dict[str, torch.Tensor],
    maximum_edge: int = 640,
) -> PreparedSample:
    rgb = image.convert("RGB")
    original_width, original_height = rgb.size
    minimum_scale = maximum_edge / max(original_width, original_height)
    resized_width = max(1, round(original_width * minimum_scale))
    resized_height = max(1, round(original_height * minimum_scale))
    resized = tvf.resize(
        rgb,
        [resized_height, resized_width],
        interpolation=tvf.InterpolationMode.BILINEAR,
        antialias=True,
    )
    image_tensor = tvf.pil_to_tensor(resized).float().div(255.0)
    padded = torch.zeros((3, maximum_edge, maximum_edge), dtype=torch.float32)
    padded[:, :resized_height, :resized_width] = image_tensor
    valid_pixels = torch.zeros((maximum_edge, maximum_edge), dtype=torch.bool)
    valid_pixels[:resized_height, :resized_width] = True

    boxes = target["boxes"].clone().to(torch.float32)
    if boxes.numel():
        boxes[:, [0, 2]] *= resized_width / original_width
        boxes[:, [1, 3]] *= resized_height / original_height
    labels = target["labels"].clone().to(torch.int64)
    source_masks = target["masks"].to(torch.float32)
    if source_masks.shape[0]:
        resized_masks = torch.nn.functional.interpolate(
            source_masks[:, None],
            size=(resized_height, resized_width),
            mode="nearest",
        )[:, 0].to(torch.uint8)
        masks = torch.zeros(
            (source_masks.shape[0], maximum_edge, maximum_edge), dtype=torch.uint8
        )
        masks[:, :resized_height, :resized_width] = resized_masks
    else:
        masks = torch.zeros((0, maximum_edge, maximum_edge), dtype=torch.uint8)

    return PreparedSample(
        image=padded,
        boxes=boxes,
        labels=labels,
        masks=masks,
        valid_pixels=valid_pixels,
        info=TransformInfo(
            original_height=original_height,
            original_width=original_width,
            resized_height=resized_height,
            resized_width=resized_width,
            padded_size=maximum_edge,
            scale_x=resized_width / original_width,
            scale_y=resized_height / original_height,
        ),
    )


def restore_boxes(boxes: torch.Tensor, info: TransformInfo) -> torch.Tensor:
    restored = boxes.clone().to(torch.float32)
    if restored.numel():
        restored[:, [0, 2]] = restored[:, [0, 2]].clamp(0, info.resized_width)
        restored[:, [1, 3]] = restored[:, [1, 3]].clamp(0, info.resized_height)
        restored[:, [0, 2]] /= info.scale_x
        restored[:, [1, 3]] /= info.scale_y
        restored[:, [0, 2]] = restored[:, [0, 2]].clamp(0, info.original_width)
        restored[:, [1, 3]] = restored[:, [1, 3]].clamp(0, info.original_height)
    return restored


def restore_masks(masks: torch.Tensor, info: TransformInfo) -> torch.Tensor:
    if not masks.shape[0]:
        return torch.zeros(
            (0, info.original_height, info.original_width), dtype=torch.bool
        )
    cropped = masks[:, : info.resized_height, : info.resized_width].float()
    restored = torch.nn.functional.interpolate(
        cropped[:, None],
        size=(info.original_height, info.original_width),
        mode="nearest",
    )[:, 0]
    return restored.bool()
