"""Tests for deterministic annotation-sample selection helpers."""

import pytest

from ml.scripts.select_annotation_sample import (
    evenly_spaced,
    preserve_workflow_state,
    yolo_box_to_xyxy,
)


def test_evenly_spaced_is_deterministic_and_keeps_endpoints() -> None:
    records = [{"index": index} for index in range(10)]
    selected = evenly_spaced(records, 4)
    assert [record["index"] for record in selected] == [0, 3, 6, 9]


def test_evenly_spaced_rejects_impossible_quota() -> None:
    with pytest.raises(ValueError):
        evenly_spaced([{"index": 0}], 2)


def test_yolo_box_conversion_clamps_to_image() -> None:
    box = yolo_box_to_xyxy(["0", "0.0", "0.0", "0.4", "0.4"], 100, 200)
    assert box == [0.0, 0.0, 20.0, 40.0]


def test_rerun_preserves_review_and_generation_state() -> None:
    selected = {
        "dataset_sha256": "same",
        "images": [{"image_id": "train/example", "review_state": "candidate_unreviewed"}],
        "candidate_generation": {"status": "not_started"},
        "review": {"policy": "pending"},
    }
    previous = {
        "dataset_sha256": "same",
        "images": [{"image_id": "train/example", "review_state": "corrected"}],
        "candidate_generation": {"status": "complete"},
        "review": {"policy": "approved"},
    }
    preserved = preserve_workflow_state(selected, previous)
    assert preserved["candidate_generation"]["status"] == "complete"
    assert preserved["review"]["policy"] == "approved"
    assert preserved["images"][0]["review_state"] == "corrected"
