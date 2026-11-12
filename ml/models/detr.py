"""Hugging Face DETR detection and instance-segmentation adapters."""

from __future__ import annotations

import time
from pathlib import Path

import torch
from PIL import Image
from transformers import DetrForObjectDetection, DetrForSegmentation, DetrImageProcessor

from .base import ModelAdapter
from .device import select_device
from .mask_encoding import encode_prediction_mask, mask_box
from .prediction import PredictionRecord
from .preprocessing import PreparedSample, prepare_sample, restore_boxes, restore_masks


def normalized_cxcywh(boxes: torch.Tensor, size: int) -> torch.Tensor:
    if not boxes.numel():
        return torch.zeros((0, 4), dtype=torch.float32, device=boxes.device)
    x1, y1, x2, y2 = boxes.unbind(dim=1)
    return torch.stack(
        ((x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1), dim=1
    ).div(float(size))


def query_instance_masks(
    logits: torch.Tensor,
    pred_masks: torch.Tensor,
    *,
    score_threshold: float,
    mask_threshold: float,
    output_size: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    scores = logits.softmax(dim=-1)[..., 0]
    keep = scores >= score_threshold
    selected_scores = scores[keep]
    selected_masks = pred_masks[keep]
    if not selected_masks.shape[0]:
        return selected_scores, torch.zeros(
            (0, output_size, output_size), dtype=torch.bool, device=logits.device
        )
    upsampled = torch.nn.functional.interpolate(
        selected_masks[:, None],
        size=(output_size, output_size),
        mode="bilinear",
        align_corners=False,
    )[:, 0]
    return selected_scores, upsampled.sigmoid() >= mask_threshold


class _DetrBase(ModelAdapter):
    model_class: type[torch.nn.Module]

    def __init__(
        self,
        *,
        model_id: str,
        revision: str,
        cache_dir: Path,
        score_threshold: float,
        use_safetensors: bool | None = None,
        device: str = "auto",
        maximum_edge: int = 640,
    ) -> None:
        self.model_id = model_id
        self.revision = revision
        self.maximum_edge = maximum_edge
        self.score_threshold = score_threshold
        self.device = select_device(device)
        self.processor = DetrImageProcessor.from_pretrained(
            model_id, revision=revision, cache_dir=cache_dir, local_files_only=True
        )
        self.model = self.model_class.from_pretrained(
            model_id,
            revision=revision,
            cache_dir=cache_dir,
            num_labels=1,
            id2label={0: "defect"},
            label2id={"defect": 0},
            ignore_mismatched_sizes=True,
            use_safetensors=use_safetensors,
            local_files_only=True,
        ).to(self.device)

    def _prepare(
        self, images: list[Image.Image], targets: list[dict[str, object]]
    ) -> tuple[torch.Tensor, torch.Tensor, list[dict[str, torch.Tensor]], list[PreparedSample]]:
        samples = [
            prepare_sample(image, target, self.maximum_edge)
            for image, target in zip(images, targets, strict=True)
        ]
        batch = self.processor(
            images=[sample.image for sample in samples],
            do_resize=False,
            do_rescale=False,
            do_pad=False,
            return_tensors="pt",
        )
        pixel_values = batch["pixel_values"].to(self.device)
        pixel_mask = torch.stack([sample.valid_pixels for sample in samples]).to(
            self.device
        )
        labels = []
        for sample in samples:
            labels.append(
                {
                    "class_labels": torch.zeros(
                        sample.labels.shape, dtype=torch.int64, device=self.device
                    ),
                    "boxes": normalized_cxcywh(
                        sample.boxes.to(self.device), self.maximum_edge
                    ),
                    "masks": sample.masks.to(self.device, dtype=torch.float32),
                }
            )
        return pixel_values, pixel_mask, labels, samples

    def training_loss(
        self, images: list[Image.Image], targets: list[dict[str, object]]
    ) -> torch.Tensor:
        self.model.train()
        pixel_values, pixel_mask, labels, _ = self._prepare(images, targets)
        outputs = self.model(
            pixel_values=pixel_values, pixel_mask=pixel_mask, labels=labels
        )
        return outputs.loss

    def save_checkpoint(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(self.model.state_dict(), path)

    def load_checkpoint(self, path: Path) -> None:
        state = torch.load(path, map_location=self.device, weights_only=True)
        self.model.load_state_dict(state)


class DetrDetectionAdapter(_DetrBase):
    name = "detr_detection"
    model_class = DetrForObjectDetection

    def predict(self, image_id: str, image: Image.Image) -> PredictionRecord:
        empty_target = {
            "boxes": torch.zeros((0, 4)),
            "labels": torch.zeros((0,), dtype=torch.int64),
            "masks": torch.zeros((0, image.height, image.width), dtype=torch.uint8),
        }
        start = time.perf_counter()
        pixel_values, pixel_mask, _, samples = self._prepare([image], [empty_target])
        self.model.eval()
        with torch.inference_mode():
            outputs = self.model(pixel_values=pixel_values, pixel_mask=pixel_mask)
        processed = self.processor.post_process_object_detection(
            outputs,
            threshold=self.score_threshold,
            target_sizes=torch.tensor(
                [[self.maximum_edge, self.maximum_edge]], device=self.device
            ),
        )[0]
        keep = processed["labels"] == 0
        scores = processed["scores"][keep].detach().cpu()
        boxes = restore_boxes(processed["boxes"][keep].detach().cpu(), samples[0].info)
        return PredictionRecord(
            image_id=image_id,
            tool="hook_sinskey",
            model=self.name,
            defective=bool(scores.numel()),
            confidence=float(scores.max()) if scores.numel() else 0.0,
            boxes=boxes.tolist(),
            masks=[],
            instance_scores=scores.tolist(),
            latency_ms=(time.perf_counter() - start) * 1000,
        )


class DetrSegmentationAdapter(_DetrBase):
    name = "detr_segmentation"
    model_class = DetrForSegmentation

    def __init__(
        self,
        *,
        mask_threshold: float,
        minimum_mask_area: int,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.mask_threshold = mask_threshold
        self.minimum_mask_area = minimum_mask_area

    def predict(self, image_id: str, image: Image.Image) -> PredictionRecord:
        empty_target = {
            "boxes": torch.zeros((0, 4)),
            "labels": torch.zeros((0,), dtype=torch.int64),
            "masks": torch.zeros((0, image.height, image.width), dtype=torch.uint8),
        }
        start = time.perf_counter()
        pixel_values, pixel_mask, _, samples = self._prepare([image], [empty_target])
        self.model.eval()
        with torch.inference_mode():
            outputs = self.model(pixel_values=pixel_values, pixel_mask=pixel_mask)
        candidate_scores, candidate_masks = query_instance_masks(
            outputs.logits[0],
            outputs.pred_masks[0],
            score_threshold=self.score_threshold,
            mask_threshold=self.mask_threshold,
            output_size=self.maximum_edge,
        )
        masks = []
        scores = []
        for score, mask in zip(candidate_scores, candidate_masks, strict=True):
            restored = restore_masks(mask.detach().cpu()[None], samples[0].info)[0]
            if int(restored.sum()) < self.minimum_mask_area:
                continue
            masks.append(restored)
            scores.append(float(score.detach().cpu()))
        return PredictionRecord(
            image_id=image_id,
            tool="hook_sinskey",
            model=self.name,
            defective=bool(masks),
            confidence=max(scores, default=0.0),
            boxes=[mask_box(mask) for mask in masks],
            masks=[encode_prediction_mask(mask) for mask in masks],
            instance_scores=scores,
            latency_ms=(time.perf_counter() - start) * 1000,
        )
