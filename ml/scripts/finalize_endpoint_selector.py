"""Freeze a validation-derived endpoint review policy and materialize selected tips."""

from __future__ import annotations

import hashlib
import json
import shutil
from collections import defaultdict
from pathlib import Path

import numpy as np
import yaml
from PIL import Image

from ml.models.device import select_device
from ml.models.endpoint_selector import EndpointSelector

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = REPO_ROOT / "ml/data/endpoint_selector_v1.json"
CONFIG = REPO_ROOT / "ml/configs/endpoint_selector.yaml"
CHECKPOINT = REPO_ROOT / "ml/runs/endpoint_selector/v1/best.pt"
OUTPUT_ROOT = REPO_ROOT / "ml/runs/endpoint_selector/v1/selected_tips"
OUTPUT_SUMMARY = REPO_ROOT / "ml/experiments/endpoint_selector_v1_policy.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def grouped(records: list[dict[str, object]], split: str) -> dict[str, list[dict[str, object]]]:
    result: dict[str, list[dict[str, object]]] = defaultdict(list)
    for record in records:
        if record["split"] == split:
            result[str(record["source_image_id"])].append(record)
    if any(len(candidates) != 2 for candidates in result.values()):
        raise ValueError(f"{split} does not contain exactly two endpoints per tool")
    return result


def evaluate_pairs(
    selector: EndpointSelector,
    pairs: dict[str, list[dict[str, object]]],
    review_threshold: float | None,
    output: Path | None,
) -> tuple[list[dict[str, object]], list[float]]:
    results = []
    margins = []
    if output is not None:
        output.mkdir(parents=True, exist_ok=True)
    for source_id, candidates in sorted(pairs.items()):
        ordered = sorted(candidates, key=lambda item: str(item["candidate_side"]))
        images = [Image.open(REPO_ROOT / str(item["image_path"])).convert("RGB") for item in ordered]
        scores = selector.score_images(images)
        selected_index = int(np.argmax(scores))
        selected = ordered[selected_index]
        margin = float(abs(scores[0] - scores[1]))
        margins.append(margin)
        review_required = review_threshold is not None and margin < review_threshold
        record = {
            "source_image_id": source_id,
            "selected_candidate_id": selected["candidate_id"],
            "selected_side": selected["candidate_side"],
            "actual_tip_side": next(item["candidate_side"] for item in ordered if item["label"] == "tip"),
            "correct": selected["label"] == "tip",
            "tip_scores": {str(item["candidate_side"]): score for item, score in zip(ordered, scores, strict=True)},
            "score_margin": margin,
            "review_required": review_required,
            "review_reason": "low_endpoint_score_margin" if review_required else None,
        }
        if output is not None:
            target = output / f"{source_id}.jpg"
            images[selected_index].save(target, quality=95, subsampling=0)
            record["selected_tip_path"] = target.relative_to(REPO_ROOT).as_posix()
        results.append(record)
    return results, margins


def summarize(results: list[dict[str, object]]) -> dict[str, object]:
    accepted = [item for item in results if not item["review_required"]]
    return {
        "source_instruments": len(results),
        "correct": sum(bool(item["correct"]) for item in results),
        "selection_accuracy": sum(bool(item["correct"]) for item in results) / len(results),
        "review_required": sum(bool(item["review_required"]) for item in results),
        "automatic_accepts": len(accepted),
        "automatic_accept_accuracy": (
            sum(bool(item["correct"]) for item in accepted) / len(accepted) if accepted else None
        ),
        "errors": [item["source_image_id"] for item in results if not item["correct"]],
        "review_queue": [item["source_image_id"] for item in results if item["review_required"]],
    }


def main() -> None:
    manifest = json.loads(MANIFEST.read_text())
    config = yaml.safe_load(CONFIG.read_text())
    device = select_device("auto")
    selector = EndpointSelector.from_checkpoint(CHECKPOINT, int(config["image_size"]), device)
    validation_pairs = grouped(manifest["records"], "valid")
    validation_results, validation_margins = evaluate_pairs(selector, validation_pairs, None, None)
    review_quantile = 0.10
    review_threshold = float(np.quantile(validation_margins, review_quantile, method="higher"))
    validation_results, _ = evaluate_pairs(selector, validation_pairs, review_threshold, None)

    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    test_results, test_margins = evaluate_pairs(
        selector,
        grouped(manifest["records"], "test"),
        review_threshold,
        OUTPUT_ROOT / "test",
    )
    predictions = OUTPUT_ROOT / "test_selections.jsonl"
    predictions.write_text("".join(json.dumps(item) + "\n" for item in test_results))
    summary = {
        "schema_version": 1,
        "status": "awaiting_human_gallery_review",
        "dataset_sha256": manifest["dataset_sha256"],
        "checkpoint": CHECKPOINT.relative_to(REPO_ROOT).as_posix(),
        "checkpoint_sha256": sha256(CHECKPOINT),
        "device": str(device),
        "selection_rule": "choose the higher tip score within each left/right endpoint pair",
        "review_policy": {
            "method": "10th percentile of validation pair-score margins",
            "quantile": review_quantile,
            "score_margin_threshold": review_threshold,
            "comparison": "review when margin is below threshold",
        },
        "validation": summarize(validation_results),
        "validation_margin": {
            "minimum": min(validation_margins),
            "median": float(np.median(validation_margins)),
            "maximum": max(validation_margins),
        },
        "test": summarize(test_results),
        "test_margin": {
            "minimum": min(test_margins),
            "median": float(np.median(test_margins)),
            "maximum": max(test_margins),
        },
        "test_predictions": predictions.relative_to(REPO_ROOT).as_posix(),
        "test_predictions_sha256": sha256(predictions),
        "selected_tip_directory": (OUTPUT_ROOT / "test").relative_to(REPO_ROOT).as_posix(),
    }
    OUTPUT_SUMMARY.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
