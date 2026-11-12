"""Deterministic, segmentation-safe training augmentation."""

from __future__ import annotations

import random
from typing import Any

import torch
from PIL import Image
from torchvision.transforms import functional as tvf


def _boxes_from_masks(masks: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    boxes = []
    keep = []
    for index, mask in enumerate(masks):
        ys, xs = torch.where(mask.bool())
        if not xs.numel():
            continue
        boxes.append(
            [
                float(xs.min()),
                float(ys.min()),
                float(xs.max() + 1),
                float(ys.max() + 1),
            ]
        )
        keep.append(index)
    return (
        torch.tensor(boxes, dtype=torch.float32).reshape(-1, 4),
        torch.tensor(keep, dtype=torch.int64),
    )


def augment_training_sample(
    image: Image.Image,
    target: dict[str, object],
    config: dict[str, Any],
    *,
    seed: int,
) -> tuple[Image.Image, dict[str, object]]:
    """Apply approved transforms while keeping masks, boxes, and labels aligned."""
    rng = random.Random(seed)
    result = image.convert("RGB")
    masks = target["masks"].clone().to(torch.uint8)
    labels = target["labels"].clone().to(torch.int64)

    if rng.random() < float(config.get("horizontal_flip_probability", 0.0)):
        result = tvf.hflip(result)
        masks = torch.flip(masks, dims=(-1,))

    rotation = float(config.get("rotation_degrees", 0.0))
    if rotation:
        angle = rng.uniform(-rotation, rotation)
        result = tvf.rotate(
            result,
            angle,
            interpolation=tvf.InterpolationMode.BILINEAR,
            fill=0,
        )
        if masks.shape[0]:
            masks = tvf.rotate(
                masks,
                angle,
                interpolation=tvf.InterpolationMode.NEAREST,
                fill=0,
            ).to(torch.uint8)

    brightness = float(config.get("brightness", 0.0))
    if brightness:
        result = tvf.adjust_brightness(
            result, rng.uniform(1.0 - brightness, 1.0 + brightness)
        )
    contrast = float(config.get("contrast", 0.0))
    if contrast:
        result = tvf.adjust_contrast(
            result, rng.uniform(1.0 - contrast, 1.0 + contrast)
        )
    if rng.random() < float(config.get("gaussian_blur_probability", 0.0)):
        result = tvf.gaussian_blur(result, kernel_size=[3, 3], sigma=[0.1, 1.0])
    if rng.random() < float(config.get("sharpness_probability", 0.0)):
        result = tvf.adjust_sharpness(result, sharpness_factor=1.5)

    image_tensor = tvf.pil_to_tensor(result).float().div(255.0)
    generator = torch.Generator().manual_seed(seed)
    if rng.random() < float(config.get("gaussian_noise_probability", 0.0)):
        standard_deviation = float(config.get("gaussian_noise_std", 0.0))
        noise = torch.randn(
            image_tensor.shape, generator=generator, dtype=image_tensor.dtype
        )
        image_tensor = image_tensor.add(noise * standard_deviation).clamp(0.0, 1.0)
    if rng.random() < float(config.get("salt_pepper_probability", 0.0)):
        fraction = float(config.get("salt_pepper_fraction", 0.0))
        draw = torch.rand(image_tensor.shape[1:], generator=generator)
        image_tensor[:, draw < fraction / 2] = 0.0
        image_tensor[:, draw > 1.0 - fraction / 2] = 1.0
    result = tvf.to_pil_image(image_tensor)

    if masks.shape[0]:
        boxes, keep = _boxes_from_masks(masks)
        masks = masks[keep]
        labels = labels[keep]
    else:
        boxes = torch.zeros((0, 4), dtype=torch.float32)

    augmented_target = dict(target)
    augmented_target.update({"boxes": boxes, "labels": labels, "masks": masks})
    return result, augmented_target
