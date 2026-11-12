"""Export redesigned-tray overlays and Hook crops with provisional status labels."""

from __future__ import annotations

import argparse
import json
import shutil
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageOps
from ultralytics import YOLO

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = REPO_ROOT / "ml/annotation/new_tray_manifest.json"
DEFAULT_COCO = (
    REPO_ROOT
    / "ml/annotation/local/new_tray_detection_candidates/cvat_dataset/annotations/instances_default.json"
)


def safe_stem(relative: str) -> str:
    path = Path(relative)
    return "__".join((*path.parent.parts, path.stem))


def box_iou(first: list[float], second: list[float]) -> float:
    x1 = max(first[0], second[0])
    y1 = max(first[1], second[1])
    x2 = min(first[2], second[2])
    y2 = min(first[3], second[3])
    intersection = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    first_area = max(0.0, first[2] - first[0]) * max(0.0, first[3] - first[1])
    second_area = max(0.0, second[2] - second[0]) * max(0.0, second[3] - second[1])
    union = first_area + second_area - intersection
    return intersection / union if union else 0.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--candidate-coco", type=Path, default=DEFAULT_COCO)
    parser.add_argument(
        "--output", type=Path,
        default=REPO_ROOT / "ml/runs/tray_yolo/presentation_predictions",
    )
    parser.add_argument("--confidence", type=float, default=0.10)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    coco = json.loads(args.candidate_coco.read_text())
    local_root = REPO_ROOT / manifest["local_root"] / "raw"
    output = args.output.resolve()
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    instances: dict[str, list[dict]] = defaultdict(list)
    for record in manifest["images"]:
        instances[record["source_relative_path"]].append(record)
    coco_images = {item["id"]: item for item in coco["images"]}
    candidate_boxes: dict[str, list[dict]] = defaultdict(list)
    for annotation in coco["annotations"]:
        image_record = coco_images[annotation["image_id"]]
        x, y, width, height = annotation["bbox"]
        candidate_boxes[image_record["source_relative_path"]].append(
            {
                "source_instance_index": annotation["source_instance_index"],
                "box": [x, y, x + width, y + height],
            }
        )
    model = YOLO(args.checkpoint.resolve())
    prediction_records = []
    for source_record in manifest["sources"]:
        relative = source_record["source_relative_path"]
        source = local_root / relative
        split = source_record["split"]
        stem = safe_stem(relative)
        overlay_dir = output / split / "overlays"
        crop_dir = output / split / "crops"
        overlay_dir.mkdir(parents=True, exist_ok=True)
        crop_dir.mkdir(parents=True, exist_ok=True)
        with Image.open(source) as handle:
            upright = ImageOps.exif_transpose(handle).convert("RGB")
        result = model.predict(upright, imgsz=640, conf=args.confidence, device="cpu", verbose=False)[0]
        candidates = []
        if result.boxes is not None:
            for box, confidence, class_id in zip(
                result.boxes.xyxy.cpu().tolist(),
                result.boxes.conf.cpu().tolist(),
                result.boxes.cls.cpu().tolist(),
                strict=True,
            ):
                if int(class_id) == 3:
                    candidates.append({"box": box, "confidence": float(confidence)})
        expected = sorted(instances[relative], key=lambda item: int(item["source_instance_index"]))
        candidates = sorted(candidates, key=lambda item: item["confidence"], reverse=True)[: len(expected)]
        references = candidate_boxes[relative]
        possible_pairs = sorted(
            (
                (box_iou(candidate["box"], reference["box"]), pred_index, ref_index)
                for pred_index, candidate in enumerate(candidates)
                for ref_index, reference in enumerate(references)
            ),
            reverse=True,
        )
        assignments = []
        used_predictions: set[int] = set()
        used_references: set[int] = set()
        for iou, pred_index, ref_index in possible_pairs:
            if pred_index in used_predictions or ref_index in used_references:
                continue
            assignments.append((references[ref_index]["source_instance_index"], candidates[pred_index], iou))
            used_predictions.add(pred_index)
            used_references.add(ref_index)
        assignments.sort(key=lambda item: int(item[0]))
        overlay = Image.fromarray(result.plot()[..., ::-1])
        overlay.save(overlay_dir / f"{stem}.jpg", quality=90)
        matched = []
        expected_by_index = {int(item["source_instance_index"]): item for item in expected}
        for instance_index, candidate, assignment_iou in assignments:
            ground_record = expected_by_index[int(instance_index)]
            x1, y1, x2, y2 = candidate["box"]
            crop = upright.crop((max(0, x1), max(0, y1), min(upright.width, x2), min(upright.height, y2)))
            status = ground_record["status"]
            index = ground_record["source_instance_index"]
            crop_name = f"{stem}__instance_{index}__{status}.jpg"
            crop.save(crop_dir / crop_name, quality=95, subsampling=0)
            matched.append(
                {
                    "source_instance_index": index,
                    "status": status,
                    "confidence": candidate["confidence"],
                    "box_xyxy": candidate["box"],
                    "candidate_box_iou": assignment_iou,
                    "crop": (crop_dir / crop_name).relative_to(REPO_ROOT).as_posix(),
                }
            )
        prediction_records.append(
            {
                "source_relative_path": relative,
                "split": split,
                "expected_instances": len(expected),
                "predicted_hook_instances": len(candidates),
                "matched_instances": matched,
                "overlay": (overlay_dir / f"{stem}.jpg").relative_to(REPO_ROOT).as_posix(),
            }
        )
    prediction_path = output / "predictions.jsonl"
    prediction_path.write_text("".join(json.dumps(item) + "\n" for item in prediction_records))
    summary = {
        "images": len(prediction_records),
        "expected_instances": sum(item["expected_instances"] for item in prediction_records),
        "predicted_instances": sum(item["predicted_hook_instances"] for item in prediction_records),
        "matched_instances": sum(len(item["matched_instances"]) for item in prediction_records),
        "confidence_threshold": args.confidence,
        "status": "provisional_unreviewed_new_tray_boxes",
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
