"""Read the frozen Hook Sinskey COCO instance-segmentation dataset."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import torch
from PIL import Image
from pycocotools import mask as mask_utils
from torch.utils.data import Dataset

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROOT = REPO_ROOT / "ml/data/local/hook_sinskey/coco_segmentation_v1"


def decode_segmentation(
    segmentation: dict[str, object], height: int, width: int
) -> torch.Tensor:
    rle = segmentation
    if isinstance(rle.get("counts"), list):
        rle = mask_utils.frPyObjects(rle, height, width)
    decoded = mask_utils.decode(rle)
    if decoded.ndim == 3:
        decoded = decoded[..., 0]
    return torch.from_numpy(decoded.copy()).to(torch.uint8)


class FrozenCocoDataset(Dataset):
    def __init__(
        self,
        split: str,
        root: Path = DEFAULT_ROOT,
        *,
        allow_test: bool = False,
    ) -> None:
        if split not in {"train", "valid", "test"}:
            raise ValueError(f"unsupported split: {split}")
        if split == "test" and not allow_test:
            raise PermissionError(
                "the frozen test split requires allow_test=True and is prohibited "
                "during training, early stopping, and threshold selection"
            )
        self.root = root
        self.split = split
        payload = json.loads(
            (root / "annotations" / f"instances_{split}.json").read_text()
        )
        self.images = sorted(payload["images"], key=lambda item: int(item["id"]))
        self.annotations: dict[int, list[dict]] = defaultdict(list)
        for annotation in payload["annotations"]:
            self.annotations[int(annotation["image_id"])].append(annotation)

    def __len__(self) -> int:
        return len(self.images)

    def __getitem__(self, index: int) -> tuple[Image.Image, dict[str, object]]:
        record = self.images[index]
        image = Image.open(self.root / record["file_name"]).convert("RGB")
        annotations = self.annotations[int(record["id"])]
        boxes = []
        labels = []
        masks = []
        for annotation in annotations:
            x, y, width, height = map(float, annotation["bbox"])
            boxes.append([x, y, x + width, y + height])
            labels.append(1)
            masks.append(
                decode_segmentation(
                    annotation["segmentation"],
                    int(record["height"]),
                    int(record["width"]),
                )
            )
        target: dict[str, object] = {
            "boxes": torch.tensor(boxes, dtype=torch.float32).reshape(-1, 4),
            "labels": torch.tensor(labels, dtype=torch.int64),
            "masks": (
                torch.stack(masks)
                if masks
                else torch.zeros(
                    (0, int(record["height"]), int(record["width"])),
                    dtype=torch.uint8,
                )
            ),
            "image_id": str(record["medetect_image_id"]),
            "numeric_image_id": int(record["id"]),
            "status": str(record["status"]),
            "split": self.split,
        }
        return image, target


def collate_raw(batch: list[tuple[Image.Image, dict]]) -> tuple[list[Image.Image], list[dict]]:
    images, targets = zip(*batch, strict=True)
    return list(images), list(targets)
