from pathlib import Path

from ml.benchmark.training import (
    apply_trainable_scope,
    batches,
    limited_indices,
    load_training_config,
    positive_safe_batches,
)


class TinyAdapter:
    def __init__(self) -> None:
        import torch

        self.model = torch.nn.Module()
        self.model.detr = torch.nn.Module()
        self.model.detr.class_labels_classifier = torch.nn.Linear(2, 2)
        self.model.detr.backbone = torch.nn.Linear(2, 2)
        self.model.mask_head = torch.nn.Linear(2, 2)
        self.model.bbox_attention = torch.nn.Linear(2, 2)


def test_controlled_config_prohibits_test_selection() -> None:
    config = load_training_config()
    assert config["seed"] == 42
    assert config["augmentation"] == "none"
    assert config["selection_split"] == "valid"
    assert config["test_access_during_training"] == "prohibited"
    assert set(config["models"]) == {
        "detr_detection",
        "detr_segmentation",
        "mask_rcnn",
    }


def test_batch_partition_is_stable() -> None:
    assert batches([0, 1, 2, 3, 4], 2) == [[0, 1], [2, 3], [4]]


def test_no_pip_dependencies_in_controlled_config() -> None:
    contents = Path("ml/configs/controlled_benchmark.yaml").read_text().lower()
    assert "pip" not in contents


def test_segmentation_head_scope_freezes_backbone() -> None:
    adapter = TinyAdapter()
    count = apply_trainable_scope(adapter, "detr_segmentation_heads")
    assert count > 0
    parameters = dict(adapter.model.named_parameters())
    assert parameters["detr.class_labels_classifier.weight"].requires_grad
    assert parameters["mask_head.weight"].requires_grad
    assert parameters["bbox_attention.weight"].requires_grad
    assert not parameters["detr.backbone.weight"].requires_grad


def test_positive_safe_batches_use_every_index_once() -> None:
    class StatusDataset:
        def __getitem__(self, index):
            status = "defective" if index < 4 else "healthy"
            return None, {"status": status}

    result = positive_safe_batches(StatusDataset(), list(range(7)), 2, 42)
    assert sorted(index for batch in result for index in batch) == list(range(7))
    assert all(any(index < 4 for index in batch) for batch in result)


def test_limited_indices_are_stratified() -> None:
    class StatusDataset:
        def __len__(self):
            return 10

        def __getitem__(self, index):
            status = "healthy" if index < 5 else "defective"
            return None, {"status": status}

    dataset = StatusDataset()
    selected = limited_indices(dataset, 4)
    assert [dataset[index][1]["status"] for index in selected] == [
        "healthy",
        "healthy",
        "defective",
        "defective",
    ]


def test_safe_detr_segmentation_config_preserves_effective_batch() -> None:
    config = load_training_config(
        Path("ml/configs/combined_reviewed_v3_detr_segmentation_safe.yaml")
    )
    model = config["models"]["detr_segmentation"]
    assert model["batch_size"] == 1
    assert model["gradient_accumulation_steps"] == 2
    assert model["batch_size"] * model["gradient_accumulation_steps"] == 2
    assert model["validation_batch_size"] == 2
    assert model["trainable_scope"] == "all"
    assert config["maximum_edge"] == 640
    assert config["test_access_during_training"] == "prohibited"
