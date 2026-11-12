"""JSON-safe COCO RLE helpers for unified predictions."""

from __future__ import annotations

from typing import Any

import numpy as np
import torch
from pycocotools import mask as mask_utils


def encode_prediction_mask(mask: torch.Tensor) -> dict[str, Any]:
    array = mask.detach().cpu().numpy().astype(np.uint8)
    encoded = mask_utils.encode(np.asfortranarray(array))
    encoded["counts"] = encoded["counts"].decode("ascii")
    return {"size": list(encoded["size"]), "counts": encoded["counts"]}


def mask_box(mask: torch.Tensor) -> list[float]:
    rows, columns = torch.where(mask)
    if not columns.numel():
        raise ValueError("cannot derive a box from an empty mask")
    x1, y1 = int(columns.min()), int(rows.min())
    x2, y2 = int(columns.max()) + 1, int(rows.max()) + 1
    return [float(x1), float(y1), float(x2), float(y2)]
