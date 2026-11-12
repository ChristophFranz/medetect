#!/usr/bin/env python3
"""Derive stage-consistent new-tray v4 metrics from frozen instance records."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_ROOT = REPO_ROOT / "ml/runs/new_tray_v4/connected_pipeline"
CONNECTED_RESULTS = REPO_ROOT / "ml/experiments/new_tray_v4_connected_results.json"
OUTPUT = REPO_ROOT / "ml/experiments/new_tray_v4_stage_consistent_metrics.json"
MODEL_NAMES = (
    "yolo_detection",
    "detr_detection",
    "detr_segmentation",
    "mask_rcnn",
)


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def condition(record: dict, group: str) -> bool:
    source = record["source_relative_path"]
    if group == "one_tool":
        return source.startswith("One Tool")
    if group == "two_tool":
        return source.startswith("Two Tools")
    if group == "dry":
        return " Dry/" in source
    if group == "wet":
        return " Wet/" in source
    raise ValueError(f"unknown subgroup: {group}")


def strict_metrics(records: list[dict]) -> dict:
    defective = [item for item in records if item["truth"] == "defective"]
    healthy = [item for item in records if item["truth"] == "healthy"]
    correct = sum(bool(item["end_to_end_decision_success"]) for item in records)
    defective_correct = sum(
        bool(item["end_to_end_decision_success"]) for item in defective
    )
    localized = sum(bool(item["localized_end_to_end_success"]) for item in records)
    defective_localized = sum(
        bool(item["localized_end_to_end_success"]) for item in defective
    )
    recall = ratio(defective_correct, len(defective))
    return {
        "expected_tools": len(records),
        "defective_tools": len(defective),
        "healthy_tools": len(healthy),
        "strict_correct": correct,
        "strict_accuracy": ratio(correct, len(records)),
        "defective_correct": defective_correct,
        "defective_recall": recall,
        "false_negative_rate": 1.0 - recall,
        "localized_correct": localized,
        "localized_success_rate": ratio(localized, len(records)),
        "defective_localized": defective_localized,
        "defective_localized_recall": ratio(defective_localized, len(defective)),
    }


def conditional_metrics(records: list[dict]) -> dict:
    delivered = [item for item in records if item["detected"]]
    defective = [item for item in delivered if item["truth"] == "defective"]
    healthy = [item for item in delivered if item["truth"] == "healthy"]
    correct = sum(bool(item["decision_correct"]) for item in delivered)
    defective_correct = sum(bool(item["decision_correct"]) for item in defective)
    healthy_correct = sum(bool(item["decision_correct"]) for item in healthy)
    recall = ratio(defective_correct, len(defective))
    latencies = np.asarray([float(item["latency_ms"]) for item in delivered])
    return {
        "delivered_crops": len(delivered),
        "delivered_defective": len(defective),
        "delivered_healthy": len(healthy),
        "correct": correct,
        "accuracy": ratio(correct, len(delivered)),
        "defective_correct": defective_correct,
        "defective_recall": recall,
        "false_negative_rate": 1.0 - recall,
        "healthy_correct": healthy_correct,
        "specificity": ratio(healthy_correct, len(healthy)),
        "median_endpoint_plus_model_latency_ms": float(np.median(latencies)),
        "p95_endpoint_plus_model_latency_ms": float(np.quantile(latencies, 0.95)),
    }


def main() -> None:
    connected = json.loads(CONNECTED_RESULTS.read_text())
    latency_by_model = {
        item["model"]: item["latency"] for item in connected["models"]
    }
    records_by_model = {
        model: read_jsonl(RUN_ROOT / model / "instance_records.jsonl")
        for model in MODEL_NAMES
    }

    reference = records_by_model[MODEL_NAMES[0]]
    reference_identity = [
        (item["image_id"], item["truth"], item["detected"]) for item in reference
    ]
    for model, records in records_by_model.items():
        identity = [(item["image_id"], item["truth"], item["detected"]) for item in records]
        if identity != reference_identity:
            raise RuntimeError(f"cohort or upstream detections differ for {model}")

    expected = len(reference)
    detected = sum(bool(item["detected"]) for item in reference)
    defective = [item for item in reference if item["truth"] == "defective"]
    healthy = [item for item in reference if item["truth"] == "healthy"]
    payload = {
        "schema_version": 1,
        "source_connected_results": CONNECTED_RESULTS.relative_to(REPO_ROOT).as_posix(),
        "metric_policy": {
            "conditional_stage": "evaluate model decisions only on the exact generated crops delivered by the connected pipeline",
            "strict_pipeline": "require tool detection, correct endpoint, and correct defect decision; every missed expected tool is wrong",
            "localized_pipeline": "strict pipeline success plus valid localization for defective tools",
            "comparison_warning": "fixed reviewed-crop benchmark is a separate experiment and is not a monotonic upstream stage of this connected run",
        },
        "shared_upstream": {
            "expected_tools": expected,
            "detected_tools": detected,
            "tool_detection_recall": ratio(detected, expected),
            "defective_tools": len(defective),
            "detected_defective_tools": sum(bool(item["detected"]) for item in defective),
            "healthy_tools": len(healthy),
            "detected_healthy_tools": sum(bool(item["detected"]) for item in healthy),
        },
        "models": [],
    }

    for model in MODEL_NAMES:
        records = records_by_model[model]
        subgroups = {}
        for group in ("one_tool", "two_tool", "dry", "wet"):
            subgroups[group] = strict_metrics(
                [item for item in records if condition(item, group)]
            )
        payload["models"].append(
            {
                "model": model,
                "conditional_on_delivered_generated_crops": conditional_metrics(records),
                "strict_connected_pipeline": strict_metrics(records),
                "per_tray_latency_ms": latency_by_model[model],
                "strict_connected_subgroups": subgroups,
            }
        )

    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"Wrote {OUTPUT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
