import json
from pathlib import Path

import pytest

from ml.benchmark.metrics import classification_metrics, coco_metrics


def test_classification_metrics_include_requested_outcomes() -> None:
    metrics = classification_metrics(
        [True, True, False, False], [0.9, 0.2, 0.8, 0.1], 0.5
    )
    assert metrics["accuracy"] == 0.5
    assert metrics["precision"] == 0.5
    assert metrics["sensitivity"] == 0.5
    assert metrics["specificity"] == 0.5
    assert metrics["f1"] == 0.5
    assert metrics["confusion_matrix"] == {"tn": 1, "fp": 1, "fn": 1, "tp": 1}


def test_coco_metrics_can_normalize_reviewed_cvat_crowd_metadata(
    tmp_path: Path,
) -> None:
    annotation_path = tmp_path / "instances.json"
    annotation_path.write_text(
        json.dumps(
            {
                "images": [
                    {"id": 1, "width": 10, "height": 10, "medetect_image_id": "one"}
                ],
                "annotations": [
                    {
                        "id": 1,
                        "image_id": 1,
                        "category_id": 1,
                        "bbox": [2, 2, 4, 4],
                        "area": 16,
                        "iscrowd": 1,
                    }
                ],
                "categories": [{"id": 1, "name": "defect"}],
            }
        )
    )
    records = [
        {
            "image_id": "one",
            "boxes": [[2, 2, 6, 6]],
            "masks": [],
            "instance_scores": [0.9],
        }
    ]

    metrics = coco_metrics(
        annotation_path,
        records,
        iou_type="bbox",
        include=lambda score, _mask: score >= 0.5,
        normalize_crowd=True,
    )

    assert metrics["ap50"] == pytest.approx(1.0)
    assert metrics["map50_95"] == pytest.approx(1.0)
