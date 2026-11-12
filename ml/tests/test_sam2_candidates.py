"""Unit tests for SAM2 candidate post-processing utilities."""

import numpy as np
import pytest
import torch
from pycocotools import mask as mask_utils

from ml.scripts.generate_sam2_candidates import (
    encode_rle,
    mask_to_bbox,
    select_masks,
)


def test_mask_to_bbox_tightly_encloses_mask() -> None:
    mask = np.zeros((8, 10), dtype=bool)
    mask[2:6, 3:9] = True
    assert mask_to_bbox(mask) == [3.0, 2.0, 6.0, 4.0]


def test_rle_round_trip() -> None:
    mask = np.zeros((5, 7), dtype=bool)
    mask[1:4, 2:6] = True
    encoded = encode_rle(mask)
    decoded = mask_utils.decode(encoded).astype(bool)
    assert np.array_equal(decoded, mask)


def test_select_masks_uses_highest_iou_per_prompt() -> None:
    masks = torch.zeros((2, 3, 4, 4), dtype=torch.bool)
    masks[0, 1, 0:2, 0:2] = True
    masks[1, 2, 2:4, 2:4] = True
    scores = torch.tensor([[0.1, 0.9, 0.2], [0.2, 0.3, 0.8]])
    selected, selected_scores = select_masks(masks, scores)
    assert [int(mask.sum()) for mask in selected] == [4, 4]
    assert selected_scores == pytest.approx([0.9, 0.8])
