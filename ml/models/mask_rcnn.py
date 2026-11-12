"""Torchvision Mask R-CNN adapter."""

from __future__ import annotations

import time
from pathlib import Path

import torch
from PIL import Image
from torchvision.models.detection import (
    MaskRCNN_ResNet50_FPN_V2_Weights,
    maskrcnn_resnet50_fpn_v2,
)
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torchvision.models.detection.mask_rcnn import MaskRCNNPredictor

from .base import ModelAdapter
from .device import select_device
from .mask_encoding import encode_prediction_mask
from .prediction import PredictionRecord
from .preprocessing import prepare_sample, restore_boxes, restore_masks


class MaskRcnnAdapter(ModelAdapter):
    name = "mask_rcnn"

    def __init__(
        self,
        *,
        score_threshold: float,
        mask_threshold: float,
        minimum_mask_area: int,
        device: str = "auto",
        maximum_edge: int = 640,
    ) -> None:
        self.device = select_device(device)
        self.score_threshold = score_threshold
        self.mask_threshold = mask_threshold
        self.minimum_mask_area = minimum_mask_area
        self.maximum_edge = maximum_edge
        self.model = maskrcnn_resnet50_fpn_v2(
            weights=MaskRCNN_ResNet50_FPN_V2_Weights.COCO_V1,
            min_size=maximum_edge,
            max_size=maximum_edge,
        )
        box_features = self.model.roi_heads.box_predictor.cls_score.in_features
        self.model.roi_heads.box_predictor = FastRCNNPredictor(box_features, 2)
        mask_features = self.model.roi_heads.mask_predictor.conv5_mask.in_channels
        mask_hidden = self.model.roi_heads.mask_predictor.conv5_mask.out_channels
        self.model.roi_heads.mask_predictor = MaskRCNNPredictor(
            mask_features, mask_hidden, 2
        )
        self.model.to(self.device)

    def training_loss(
        self, images: list[Image.Image], targets: list[dict[str, object]]
    ) -> torch.Tensor:
        samples = [
            prepare_sample(image, target, self.maximum_edge)
            for image, target in zip(images, targets, strict=True)
        ]
        model_targets = [
            {
                "boxes": sample.boxes.to(self.device),
                "labels": sample.labels.to(self.device),
                "masks": sample.masks.to(self.device),
            }
            for sample in samples
        ]
        self.model.train()
        losses = self.model(
            [sample.image.to(self.device) for sample in samples], model_targets
        )
        return sum(losses.values())

    def predict(self, image_id: str, image: Image.Image) -> PredictionRecord:
        target = {
            "boxes": torch.zeros((0, 4)),
            "labels": torch.zeros((0,), dtype=torch.int64),
            "masks": torch.zeros((0, image.height, image.width), dtype=torch.uint8),
        }
        sample = prepare_sample(image, target, self.maximum_edge)
        start = time.perf_counter()
        self.model.eval()
        with torch.inference_mode():
            output = self.model([sample.image.to(self.device)])[0]
        keep = (output["labels"] == 1) & (output["scores"] >= self.score_threshold)
        scores = output["scores"][keep].detach().cpu()
        boxes = restore_boxes(output["boxes"][keep].detach().cpu(), sample.info)
        masks = output["masks"][keep, 0].detach().cpu() >= self.mask_threshold
        restored_masks = restore_masks(masks, sample.info)
        area_keep = torch.tensor(
            [int(mask.sum()) >= self.minimum_mask_area for mask in restored_masks],
            dtype=torch.bool,
        )
        scores = scores[area_keep]
        boxes = boxes[area_keep]
        restored_masks = restored_masks[area_keep]
        return PredictionRecord(
            image_id=image_id,
            tool="hook_sinskey",
            model=self.name,
            defective=bool(scores.numel()),
            confidence=float(scores.max()) if scores.numel() else 0.0,
            boxes=boxes.tolist(),
            masks=[encode_prediction_mask(mask) for mask in restored_masks],
            instance_scores=scores.tolist(),
            latency_ms=(time.perf_counter() - start) * 1000,
        )

    def save_checkpoint(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(self.model.state_dict(), path)

    def load_checkpoint(self, path: Path) -> None:
        state = torch.load(path, map_location=self.device, weights_only=True)
        self.model.load_state_dict(state)
