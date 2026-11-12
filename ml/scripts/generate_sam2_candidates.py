"""Generate SAM2 masks and a local COCO/CVAT package from an image manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

import cv2
import numpy as np
import torch
import yaml
from PIL import Image, ImageDraw
from pycocotools import mask as mask_utils
from transformers import Sam2Model, Sam2Processor

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SAMPLE = REPO_ROOT / "ml/annotation/pilot_sample.json"
DEFAULT_CONFIG = REPO_ROOT / "ml/annotation/sample_config.yaml"
DEFAULT_OUTPUT = REPO_ROOT / "ml/annotation/local/hook_sinskey_pilot"
DEFAULT_SUMMARY = REPO_ROOT / "ml/annotation/candidate_summary.json"
DEFAULT_CVAT_ZIP = REPO_ROOT / "ml/cvat/hook_sinskey_pilot_candidates.zip"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def choose_device(preferences: list[str]) -> torch.device:
    for preference in preferences:
        if preference == "mps" and torch.backends.mps.is_available():
            return torch.device("mps")
        if preference == "cpu":
            return torch.device("cpu")
    return torch.device("cpu")


def mask_to_bbox(binary_mask: np.ndarray) -> list[float]:
    rows, columns = np.where(binary_mask)
    if not len(columns):
        raise ValueError("cannot derive a box from an empty mask")
    x1 = int(columns.min())
    y1 = int(rows.min())
    x2 = int(columns.max()) + 1
    y2 = int(rows.max()) + 1
    return [float(x1), float(y1), float(x2 - x1), float(y2 - y1)]


def encode_rle(binary_mask: np.ndarray) -> dict[str, object]:
    encoded = mask_utils.encode(np.asfortranarray(binary_mask.astype(np.uint8)))
    encoded["counts"] = encoded["counts"].decode("ascii")
    return encoded


def render_overlay(
    image: Image.Image, masks: list[np.ndarray], boxes: list[list[float]]
) -> Image.Image:
    rgb = np.asarray(image.convert("RGB"), dtype=np.float32)
    union = np.zeros(rgb.shape[:2], dtype=bool)
    for binary_mask in masks:
        union |= binary_mask
    if union.any():
        red = np.zeros_like(rgb)
        red[..., 0] = 255
        rgb[union] = 0.55 * rgb[union] + 0.45 * red[union]
    overlay = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
    draw = ImageDraw.Draw(overlay)
    for box in boxes:
        draw.rectangle(box, outline=(255, 220, 0), width=3)
    return overlay


def select_masks(
    processed_masks: torch.Tensor,
    iou_scores: torch.Tensor,
    prompt_points: list[list[int]] | None = None,
    prompt_labels: list[int] | None = None,
) -> tuple[list[np.ndarray], list[float]]:
    masks = processed_masks
    scores = iou_scores
    if masks.ndim == 3:
        masks = masks.unsqueeze(1)
    if scores.ndim == 1:
        scores = scores.unsqueeze(1)
    if masks.shape[:2] != scores.shape[:2]:
        raise ValueError(
            f"mask/score shape mismatch: masks={tuple(masks.shape)}, scores={tuple(scores.shape)}"
        )
    chosen_masks: list[np.ndarray] = []
    chosen_scores: list[float] = []
    for object_index in range(masks.shape[0]):
        if prompt_points and prompt_labels:
            ranked = []
            for candidate_index in range(masks.shape[1]):
                candidate = masks[object_index, candidate_index].detach().cpu().numpy().astype(bool)
                positive_hits = sum(
                    bool(candidate[min(candidate.shape[0] - 1, y), min(candidate.shape[1] - 1, x)])
                    for (x, y), label in zip(prompt_points, prompt_labels, strict=True)
                    if label == 1
                )
                negative_hits = sum(
                    bool(candidate[min(candidate.shape[0] - 1, y), min(candidate.shape[1] - 1, x)])
                    for (x, y), label in zip(prompt_points, prompt_labels, strict=True)
                    if label == 0
                )
                ranked.append(
                    (
                        positive_hits,
                        -negative_hits,
                        -int(candidate.sum()),
                        float(scores[object_index, candidate_index].item()),
                        candidate_index,
                    )
                )
            candidate_index = max(ranked)[-1]
        else:
            candidate_index = int(torch.argmax(scores[object_index]).item())
        mask = masks[object_index, candidate_index].detach().cpu().numpy().astype(bool)
        if prompt_points and prompt_labels:
            _, components = cv2.connectedComponents(mask.astype(np.uint8), connectivity=8)
            retained_ids = {
                int(components[min(mask.shape[0] - 1, y), min(mask.shape[1] - 1, x)])
                for (x, y), label in zip(prompt_points, prompt_labels, strict=True)
                if label == 1
                and components[min(mask.shape[0] - 1, y), min(mask.shape[1] - 1, x)] > 0
            }
            if retained_ids:
                mask = np.isin(components, list(retained_ids))
        if not mask.any():
            raise ValueError(f"SAM2 returned an empty mask for object {object_index}")
        chosen_masks.append(mask)
        chosen_scores.append(float(scores[object_index, candidate_index].item()))
    return chosen_masks, chosen_scores


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=Path, default=DEFAULT_SAMPLE)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--cvat-zip", type=Path, default=DEFAULT_CVAT_ZIP)
    parser.add_argument("--cache-dir", type=Path, default=REPO_ROOT / "ml/artifacts/huggingface")
    parser.add_argument("--device", choices=("auto", "mps", "cpu"), default="auto")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    for path_argument in ("sample", "config", "output", "summary", "cvat_zip", "cache_dir"):
        setattr(args, path_argument, getattr(args, path_argument).resolve())
    sample = json.loads(args.sample.read_text())
    config = yaml.safe_load(args.config.read_text())
    model_config = config["sam2"]
    preferences = (
        model_config["device_preference"] if args.device == "auto" else [args.device]
    )
    device = choose_device(preferences)
    torch.manual_seed(int(config["seed"]))

    processor = Sam2Processor.from_pretrained(
        model_config["model_id"],
        revision=model_config["revision"],
        cache_dir=args.cache_dir,
        local_files_only=True,
    )
    model = Sam2Model.from_pretrained(
        model_config["model_id"],
        revision=model_config["revision"],
        cache_dir=args.cache_dir,
        use_safetensors=True,
        local_files_only=True,
    ).to(device)
    model.eval()

    if args.output.exists():
        shutil.rmtree(args.output)
    cvat_dataset = args.output / "cvat_dataset"
    image_output = cvat_dataset / "images/default"
    overlay_output = args.output / "overlays"
    annotation_output = cvat_dataset / "annotations"
    for directory in (image_output, overlay_output, annotation_output):
        directory.mkdir(parents=True, exist_ok=True)

    coco: dict[str, object] = {
        "info": {
            "description": f"Unreviewed Hook Sinskey SAM2 candidates: {sample.get('package_name', 'pilot')}",
            "version": "milestone-3-candidates",
            "date_created": datetime.now(UTC).isoformat(timespec="seconds"),
        },
        "licenses": [],
        "categories": [{"id": 1, "name": "defect", "supercategory": "defect"}],
        "images": [],
        "annotations": [],
    }
    review_queue: list[dict[str, object]] = []
    summary_images: list[dict[str, object]] = []
    annotation_id = 1

    for image_index, record in enumerate(sample["images"], start=1):
        source = REPO_ROOT / record["image_path"]
        target_name = f"{record['split']}__{source.name}"
        target = image_output / target_name
        shutil.copy2(source, target)
        image = Image.open(source).convert("RGB")
        coco["images"].append(
            {
                "id": image_index,
                "file_name": target_name,
                "width": record["width"],
                "height": record["height"],
                "medetect_image_id": record["image_id"],
                "split": record["split"],
                "review_state": "candidate_unreviewed",
            }
        )

        masks: list[np.ndarray] = []
        scores: list[float] = []
        boxes = record["legacy_defect_boxes_xyxy"]
        current_annotation_ids: list[int] = []
        if record["status"] == "defective":
            processor_inputs = {"images": image, "input_boxes": [boxes], "return_tensors": "pt"}
            if record.get("sam2_prompt_points"):
                processor_inputs["input_points"] = [[record["sam2_prompt_points"]]]
                processor_inputs["input_labels"] = [[record["sam2_prompt_point_labels"]]]
            inputs = processor(**processor_inputs)
            original_sizes = inputs["original_sizes"].clone()
            model_inputs = {key: value.to(device) for key, value in inputs.items()}
            with torch.inference_mode():
                outputs = model(
                    **model_inputs,
                    multimask_output=bool(model_config["multimask_output"]),
                )
            processed = processor.post_process_masks(
                outputs.pred_masks.detach().cpu(),
                original_sizes,
                mask_threshold=float(model_config["mask_threshold"]),
            )[0]
            masks, scores = select_masks(
                processed,
                outputs.iou_scores.detach().cpu()[0],
                record.get("sam2_prompt_points"),
                record.get("sam2_prompt_point_labels"),
            )
            for prompt_index, (binary_mask, score, prompt_box) in enumerate(
                zip(masks, scores, boxes, strict=True)
            ):
                rle = encode_rle(binary_mask)
                area = float(mask_utils.area(rle))
                bbox = mask_to_bbox(binary_mask)
                coco["annotations"].append(
                    {
                        "id": annotation_id,
                        "image_id": image_index,
                        "category_id": 1,
                        "segmentation": rle,
                        "area": area,
                        "bbox": bbox,
                        "iscrowd": 0,
                        "review_state": "candidate_unreviewed",
                        "sam2_predicted_iou": score,
                        "legacy_prompt_box_xyxy": prompt_box,
                        "prompt_index": prompt_index,
                    }
                )
                current_annotation_ids.append(annotation_id)
                annotation_id += 1

        overlay = render_overlay(image, masks, boxes)
        overlay.save(overlay_output / f"{Path(target_name).stem}__overlay.jpg", quality=92)
        review_queue.append(
            {
                "image_id": record["image_id"],
                "cvat_file_name": target_name,
                "legacy_status": record["status"],
                "annotation_ids": current_annotation_ids,
                "review_state": "candidate_unreviewed",
                "ambiguity_flags": [],
                "reviewer": None,
                "reviewed_on": None,
                "notes": "",
            }
        )
        summary_images.append(
            {
                "image_id": record["image_id"],
                "status": record["status"],
                "candidate_masks": len(masks),
                "sam2_predicted_iou": [round(score, 6) for score in scores],
            }
        )
        print(
            f"[{image_index:02d}/{sample['sample_size']}] "
            f"{record['image_id']} masks={len(masks)}"
        )

    coco_path = annotation_output / "instances_default.json"
    queue_path = args.output / "review_queue.json"
    coco_path.write_text(json.dumps(coco, indent=2) + "\n")
    queue_path.write_text(json.dumps(review_queue, indent=2) + "\n")
    args.cvat_zip.parent.mkdir(parents=True, exist_ok=True)
    archive_path = Path(
        shutil.make_archive(
            str(args.cvat_zip.with_suffix("")), "zip", root_dir=cvat_dataset
        )
    )
    try:
        sample_manifest_record = args.sample.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        sample_manifest_record = args.sample.as_posix()
    summary = {
        "schema_version": 1,
        "generated_on": datetime.now(UTC).date().isoformat(),
        "tool": sample["tool"],
        "dataset_sha256": sample["dataset_sha256"],
        "sample_manifest": sample_manifest_record,
        "model_id": model_config["model_id"],
        "model_revision": model_config["revision"],
        "license": "Apache-2.0",
        "device": str(device),
        "image_count": len(coco["images"]),
        "defective_image_count": sum(
            record["status"] == "defective" for record in summary_images
        ),
        "healthy_image_count": sum(
            record["status"] == "healthy" for record in summary_images
        ),
        "candidate_mask_count": len(coco["annotations"]),
        "coco_sha256": sha256(coco_path),
        "review_queue_sha256": sha256(queue_path),
        "cvat_zip": archive_path.relative_to(REPO_ROOT).as_posix(),
        "cvat_zip_sha256": sha256(archive_path),
        "local_package": args.output.relative_to(REPO_ROOT).as_posix(),
        "review_status": "pending",
        "images": summary_images,
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2) + "\n")
    sample["candidate_generation"] = {
        "status": "complete",
        "model_id": model_config["model_id"],
        "model_revision": model_config["revision"],
        "device": str(device),
        "candidate_mask_count": len(coco["annotations"]),
        "summary": args.summary.relative_to(REPO_ROOT).as_posix(),
        "local_package": args.output.relative_to(REPO_ROOT).as_posix(),
    }
    args.sample.write_text(json.dumps(sample, indent=2) + "\n")
    print(f"Wrote {args.summary.relative_to(REPO_ROOT)}")
    print(f"COCO candidate masks: {len(coco['annotations'])}")


if __name__ == "__main__":
    main()
