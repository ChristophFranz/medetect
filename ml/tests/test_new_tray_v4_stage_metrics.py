import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SUMMARY = REPO_ROOT / "ml/experiments/new_tray_v4_stage_consistent_metrics.json"
RUN_ROOT = REPO_ROOT / "ml/runs/new_tray_v4/connected_pipeline"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def test_stage_consistent_metrics_penalize_every_missed_tool() -> None:
    summary = json.loads(SUMMARY.read_text())
    shared = summary["shared_upstream"]
    assert shared["expected_tools"] == 24
    assert shared["detected_tools"] == 20

    for model in summary["models"]:
        conditional = model["conditional_on_delivered_generated_crops"]
        strict = model["strict_connected_pipeline"]
        records = read_jsonl(RUN_ROOT / model["model"] / "instance_records.jsonl")

        assert conditional["delivered_crops"] == shared["detected_tools"]
        assert strict["expected_tools"] == shared["expected_tools"]
        assert strict["strict_correct"] == conditional["correct"]
        assert strict["strict_accuracy"] <= conditional["accuracy"]
        assert all(
            not record["end_to_end_decision_success"]
            for record in records
            if not record["detected"]
        )


def test_connected_defective_recall_uses_the_same_delivered_crops() -> None:
    summary = json.loads(SUMMARY.read_text())
    assert summary["shared_upstream"]["detected_defective_tools"] == 16
    assert summary["shared_upstream"]["defective_tools"] == 16

    for model in summary["models"]:
        conditional = model["conditional_on_delivered_generated_crops"]
        strict = model["strict_connected_pipeline"]
        assert strict["defective_recall"] == conditional["defective_recall"]
        assert strict["false_negative_rate"] == conditional["false_negative_rate"]
