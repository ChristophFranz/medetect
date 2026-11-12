"""Tests for the frozen COCO loader and shared preprocessing contract."""

import pytest
import torch

from ml.data.coco_dataset import FrozenCocoDataset
from ml.models.detr import normalized_cxcywh
from ml.models.preprocessing import prepare_sample, restore_boxes, restore_masks


def test_frozen_split_counts_and_test_guard() -> None:
    assert len(FrozenCocoDataset("train")) == 181
    assert len(FrozenCocoDataset("valid")) == 35
    with pytest.raises(PermissionError):
        FrozenCocoDataset("test")
    assert len(FrozenCocoDataset("test", allow_test=True)) == 24


def test_healthy_item_has_empty_instances() -> None:
    dataset = FrozenCocoDataset("train")
    image, target = next(
        (image, target)
        for image, target in (dataset[index] for index in range(len(dataset)))
        if target["status"] == "healthy"
    )
    assert image.size == (1440, 1072)
    assert target["boxes"].shape == (0, 4)
    assert target["labels"].shape == (0,)
    assert target["masks"].shape == (0, 1072, 1440)


def test_resize_pad_and_restore_round_trip() -> None:
    dataset = FrozenCocoDataset("train")
    image, target = next(
        (image, target)
        for image, target in (dataset[index] for index in range(len(dataset)))
        if target["status"] == "defective"
    )
    prepared = prepare_sample(image, target, maximum_edge=640)
    assert prepared.image.shape == (3, 640, 640)
    assert prepared.info.resized_width == 640
    assert prepared.info.resized_height < 640
    assert prepared.valid_pixels.sum() == (
        prepared.info.resized_height * prepared.info.resized_width
    )
    assert torch.allclose(
        restore_boxes(prepared.boxes, prepared.info), target["boxes"], atol=1e-3
    )
    restored_masks = restore_masks(prepared.masks.bool(), prepared.info)
    assert restored_masks.shape == target["masks"].shape


def test_detr_box_conversion_is_normalized() -> None:
    boxes = torch.tensor([[0.0, 0.0, 640.0, 320.0]])
    assert torch.allclose(
        normalized_cxcywh(boxes, 640),
        torch.tensor([[0.5, 0.25, 1.0, 0.5]]),
    )


def test_restore_boxes_clamps_padding() -> None:
    dataset = FrozenCocoDataset("train")
    image, target = dataset[0]
    prepared = prepare_sample(image, target, maximum_edge=640)
    restored = restore_boxes(
        torch.tensor([[0.0, 0.0, 640.0, 640.0]]), prepared.info
    )
    assert restored.tolist() == [[0.0, 0.0, 1440.0, 1072.0]]
