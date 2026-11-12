"""Tests for the shared prediction record."""

from ml.models.prediction import PredictionRecord


def test_detr_query_masks_preserve_thin_instances() -> None:
    import torch

    from ml.models.detr import query_instance_masks

    logits = torch.tensor([[3.0, 0.0], [-3.0, 3.0]])
    masks = torch.full((2, 4, 4), -10.0)
    masks[0, :, 1] = 10.0
    scores, selected = query_instance_masks(
        logits,
        masks,
        score_threshold=0.5,
        mask_threshold=0.5,
        output_size=8,
    )
    assert scores.shape == (1,)
    assert selected.shape == (1, 8, 8)
    assert selected[0].any()


def test_prediction_record_matches_contract() -> None:
    result = PredictionRecord(
        image_id="valid/example",
        tool="hook_sinskey",
        model="example",
        defective=False,
        confidence=0,
    ).to_dict()
    assert result == {
        "image_id": "valid/example",
        "tool": "hook_sinskey",
        "model": "example",
        "defective": False,
        "confidence": 0.0,
        "boxes": [],
        "masks": [],
        "instance_scores": [],
        "latency_ms": 0.0,
    }
