from __future__ import annotations

import torch
from PIL import Image

from ml.data.augmentation import augment_training_sample


def sample() -> tuple[Image.Image, dict[str, object]]:
    image = Image.new("RGB", (20, 10), "white")
    mask = torch.zeros((1, 10, 20), dtype=torch.uint8)
    mask[:, 2:6, 3:9] = 1
    target = {
        "boxes": torch.tensor([[3.0, 2.0, 9.0, 6.0]]),
        "labels": torch.tensor([1]),
        "masks": mask,
        "image_id": "sample",
    }
    return image, target


def test_geometric_augmentation_keeps_box_and_mask_aligned() -> None:
    image, target = sample()
    augmented_image, augmented = augment_training_sample(
        image,
        target,
        {"horizontal_flip_probability": 1.0, "rotation_degrees": 8},
        seed=42,
    )
    assert augmented_image.size == image.size
    mask = augmented["masks"][0]
    ys, xs = torch.where(mask.bool())
    expected = torch.tensor(
        [float(xs.min()), float(ys.min()), float(xs.max() + 1), float(ys.max() + 1)]
    )
    assert torch.equal(augmented["boxes"][0], expected)


def test_augmentation_is_deterministic_and_preserves_metadata() -> None:
    image, target = sample()
    config = {
        "horizontal_flip_probability": 0.5,
        "rotation_degrees": 10,
        "brightness": 0.15,
        "contrast": 0.15,
        "gaussian_noise_probability": 1.0,
        "gaussian_noise_std": 0.015,
        "salt_pepper_probability": 1.0,
        "salt_pepper_fraction": 0.002,
    }
    first_image, first_target = augment_training_sample(image, target, config, seed=7)
    second_image, second_target = augment_training_sample(image, target, config, seed=7)
    assert torch.equal(
        torch.from_numpy(__import__("numpy").array(first_image)),
        torch.from_numpy(__import__("numpy").array(second_image)),
    )
    assert torch.equal(first_target["masks"], second_target["masks"])
    assert first_target["image_id"] == "sample"


def test_negative_image_remains_negative() -> None:
    image = Image.new("RGB", (20, 10), "white")
    target = {
        "boxes": torch.zeros((0, 4)),
        "labels": torch.zeros((0,), dtype=torch.int64),
        "masks": torch.zeros((0, 10, 20), dtype=torch.uint8),
    }
    _, augmented = augment_training_sample(
        image,
        target,
        {"horizontal_flip_probability": 1.0, "rotation_degrees": 10},
        seed=9,
    )
    assert augmented["boxes"].shape == (0, 4)
    assert augmented["masks"].shape == (0, 10, 20)
