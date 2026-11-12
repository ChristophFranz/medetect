"""Deterministic, resumable training loop for the controlled benchmark."""

from __future__ import annotations

import hashlib
import json
import math
import random
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import torch
import yaml

from ml.data.augmentation import augment_training_sample
from ml.data.coco_dataset import DEFAULT_ROOT, FrozenCocoDataset
from ml.models.device import seed_everything
from ml.models.factory import build_adapter

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "ml/configs/controlled_benchmark.yaml"
FROZEN_RECORD = REPO_ROOT / "ml/data/frozen_hook_sinskey_v1.json"
TRAINABLE_MODELS = ("detr_detection", "detr_segmentation", "mask_rcnn")


def apply_trainable_scope(adapter, scope: str) -> int:
    if scope == "all":
        for parameter in adapter.model.parameters():
            parameter.requires_grad = True
    elif scope == "detr_segmentation_heads":
        prefixes = (
            "detr.class_labels_classifier",
            "detr.bbox_predictor",
            "mask_head",
            "bbox_attention",
        )
        for name, parameter in adapter.model.named_parameters():
            parameter.requires_grad = name.startswith(prefixes)
    else:
        raise ValueError(f"unsupported trainable scope: {scope}")
    count = sum(
        parameter.numel()
        for parameter in adapter.model.parameters()
        if parameter.requires_grad
    )
    if not count:
        raise RuntimeError("trainable scope selected zero parameters")
    return count


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def load_training_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    return yaml.safe_load(path.read_text())


def batches(indices: list[int], batch_size: int) -> list[list[int]]:
    return [indices[start : start + batch_size] for start in range(0, len(indices), batch_size)]


def limited_indices(dataset: FrozenCocoDataset, limit: int | None) -> list[int]:
    indices = list(range(len(dataset)))
    if limit is None or limit >= len(indices):
        return indices
    if limit < 2:
        return indices[:limit]
    positives = [index for index in indices if dataset[index][1]["status"] == "defective"]
    negatives = [index for index in indices if dataset[index][1]["status"] == "healthy"]
    positive_count = min(len(positives), (limit + 1) // 2)
    negative_count = min(len(negatives), limit - positive_count)
    if positive_count + negative_count < limit:
        positive_count = min(len(positives), limit - negative_count)
    return sorted(positives[:positive_count] + negatives[:negative_count])


def positive_safe_batches(
    dataset: FrozenCocoDataset,
    indices: list[int],
    batch_size: int,
    seed: int,
) -> list[list[int]]:
    if batch_size < 2:
        raise ValueError("positive-safe batching requires batch_size >= 2")
    positives = [index for index in indices if dataset[index][1]["status"] == "defective"]
    negatives = [index for index in indices if dataset[index][1]["status"] == "healthy"]
    rng = random.Random(seed)
    rng.shuffle(positives)
    rng.shuffle(negatives)
    if len(positives) < math.ceil(len(negatives) / (batch_size - 1)):
        raise ValueError("not enough positive images for positive-safe batching")
    result = []
    while negatives:
        batch = [positives.pop()]
        while negatives and len(batch) < batch_size:
            batch.append(negatives.pop())
        result.append(batch)
    result.extend(batches(positives, batch_size))
    rng.shuffle(result)
    return result


def mean_loss(adapter, dataset: FrozenCocoDataset, indices: list[int], batch_size: int) -> float:
    losses = []
    with torch.no_grad():
        for batch_indices in batches(indices, batch_size):
            items = [dataset[index] for index in batch_indices]
            images = [item[0] for item in items]
            targets = [item[1] for item in items]
            loss = adapter.training_loss(images, targets)
            if not torch.isfinite(loss):
                raise RuntimeError("non-finite validation loss")
            losses.append(float(loss.detach().cpu()))
    return sum(losses) / len(losses)


def training_item(
    dataset: FrozenCocoDataset,
    index: int,
    augmentation: dict[str, Any] | None,
    *,
    seed: int,
) -> tuple[Any, dict[str, object]]:
    image, target = dataset[index]
    if augmentation:
        image, target = augment_training_sample(image, target, augmentation, seed=seed)
    return image, target


def train_model(
    model_name: str,
    *,
    device: str = "auto",
    config_path: Path = CONFIG_PATH,
    output_root: Path | None = None,
    max_epochs_override: int | None = None,
    limit_train: int | None = None,
    limit_valid: int | None = None,
    resume: bool = True,
    dataset_root: Path | None = None,
    dataset_record: Path | None = None,
    initial_checkpoint: Path | None = None,
) -> dict[str, Any]:
    if model_name not in TRAINABLE_MODELS:
        raise ValueError(f"not a trainable benchmark model: {model_name}")
    config = load_training_config(config_path)
    seed = int(config["seed"])
    seed_everything(seed)
    model_config = config["models"][model_name]
    augmentation = config.get("augmentation")
    if augmentation == "none":
        augmentation = None
    if augmentation is not None and not isinstance(augmentation, dict):
        raise ValueError("augmentation must be 'none' or a mapping")
    batch_size = int(model_config["batch_size"])
    validation_batch_size = int(model_config.get("validation_batch_size", batch_size))
    gradient_accumulation_steps = int(
        model_config.get("gradient_accumulation_steps", 1)
    )
    if gradient_accumulation_steps < 1:
        raise ValueError("gradient_accumulation_steps must be at least 1")
    maximum_epochs = int(max_epochs_override or config["max_epochs"])
    patience = int(config["early_stopping"]["patience"])
    minimum_delta = float(config["early_stopping"]["minimum_delta"])
    output_dir = output_root or REPO_ROOT / "ml/runs/benchmark" / model_name
    output_dir.mkdir(parents=True, exist_ok=True)
    best_checkpoint = output_dir / "best.pt"
    last_checkpoint = output_dir / "last.pt"
    state_path = output_dir / "training_state.pt"
    summary_path = output_dir / "training_summary.json"

    selected_dataset_root = dataset_root or DEFAULT_ROOT
    train_dataset = FrozenCocoDataset("train", root=selected_dataset_root)
    valid_dataset = FrozenCocoDataset("valid", root=selected_dataset_root)
    train_indices = limited_indices(train_dataset, limit_train)
    valid_indices = limited_indices(valid_dataset, limit_valid)
    if not train_indices or not valid_indices:
        raise ValueError("training and validation subsets must be non-empty")

    adapter = build_adapter(model_name, device=device)
    initialized_from = None
    if initial_checkpoint and not (resume and state_path.is_file()):
        adapter.load_checkpoint(initial_checkpoint)
        initialized_from = initial_checkpoint
    trainable_scope = str(model_config.get("trainable_scope", "all"))
    trainable_parameter_count = apply_trainable_scope(adapter, trainable_scope)
    activation_checkpointing = bool(
        model_config.get("activation_checkpointing", False)
    )
    if activation_checkpointing:
        if not getattr(adapter.model, "supports_gradient_checkpointing", False):
            raise ValueError(
                f"{model_name} does not support requested activation checkpointing"
            )
        adapter.model.gradient_checkpointing_enable()
    optimizer = torch.optim.AdamW(
        [parameter for parameter in adapter.model.parameters() if parameter.requires_grad],
        lr=float(model_config["learning_rate"]),
        weight_decay=float(config["weight_decay"]),
    )
    start_epoch = 1
    best_loss = math.inf
    best_epoch = 0
    epochs_without_improvement = 0
    history: list[dict[str, float | int]] = []
    resumed = False
    resumed_from_epoch = None
    if resume and state_path.is_file():
        state = torch.load(state_path, map_location=adapter.device, weights_only=False)
        if state["model"] != model_name or state["seed"] != seed:
            raise RuntimeError("resume state does not match the frozen run configuration")
        adapter.model.load_state_dict(state["model_state"])
        optimizer.load_state_dict(state["optimizer_state"])
        start_epoch = int(state["epoch"]) + 1
        best_loss = float(state["best_loss"])
        best_epoch = int(state["best_epoch"])
        epochs_without_improvement = int(state["epochs_without_improvement"])
        history = list(state["history"])
        resumed = True
        resumed_from_epoch = int(state["epoch"])

    started_at = datetime.now(UTC).isoformat(timespec="seconds")
    wall_start = time.perf_counter()
    status = "maximum_epochs_reached"
    for epoch in range(start_epoch, maximum_epochs + 1):
        shuffled = train_indices.copy()
        random.Random(seed + epoch).shuffle(shuffled)
        if model_config.get("batching") == "ensure_positive_per_batch":
            epoch_batches = positive_safe_batches(
                train_dataset, train_indices, batch_size, seed + epoch
            )
        else:
            epoch_batches = batches(shuffled, batch_size)
        epoch_losses = []
        epoch_start = time.perf_counter()
        optimizer.zero_grad(set_to_none=True)
        for batch_number, batch_indices in enumerate(epoch_batches):
            items = [
                training_item(
                    train_dataset,
                    index,
                    augmentation,
                    seed=seed * 1_000_000 + epoch * len(train_dataset) + index,
                )
                for index in batch_indices
            ]
            images = [item[0] for item in items]
            targets = [item[1] for item in items]
            loss = adapter.training_loss(images, targets)
            if not torch.isfinite(loss):
                raise RuntimeError(f"non-finite training loss at epoch {epoch}")
            accumulation_window_start = (
                batch_number // gradient_accumulation_steps
            ) * gradient_accumulation_steps
            accumulation_window_size = min(
                gradient_accumulation_steps,
                len(epoch_batches) - accumulation_window_start,
            )
            (loss / accumulation_window_size).backward()
            accumulation_boundary = (
                (batch_number + 1) % gradient_accumulation_steps == 0
                or batch_number + 1 == len(epoch_batches)
            )
            if accumulation_boundary:
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)
            epoch_losses.append(float(loss.detach().cpu()))

        train_loss = sum(epoch_losses) / len(epoch_losses)
        validation_loss = mean_loss(
            adapter, valid_dataset, valid_indices, validation_batch_size
        )
        duration = time.perf_counter() - epoch_start
        history.append(
            {
                "epoch": epoch,
                "train_loss": train_loss,
                "validation_loss": validation_loss,
                "duration_seconds": duration,
            }
        )
        improved = validation_loss < best_loss - minimum_delta
        if improved:
            best_loss = validation_loss
            best_epoch = epoch
            epochs_without_improvement = 0
            adapter.save_checkpoint(best_checkpoint)
        else:
            epochs_without_improvement += 1
        adapter.save_checkpoint(last_checkpoint)
        torch.save(
            {
                "model": model_name,
                "seed": seed,
                "epoch": epoch,
                "best_loss": best_loss,
                "best_epoch": best_epoch,
                "epochs_without_improvement": epochs_without_improvement,
                "history": history,
                "batch_size": batch_size,
                "validation_batch_size": validation_batch_size,
                "gradient_accumulation_steps": gradient_accumulation_steps,
                "model_state": adapter.model.state_dict(),
                "optimizer_state": optimizer.state_dict(),
            },
            state_path,
        )
        print(
            json.dumps(
                {
                    "model": model_name,
                    "epoch": epoch,
                    "train_loss": round(train_loss, 6),
                    "validation_loss": round(validation_loss, 6),
                    "best_epoch": best_epoch,
                    "patience_used": epochs_without_improvement,
                    "duration_seconds": round(duration, 2),
                }
            ),
            flush=True,
        )
        if adapter.device.type == "mps":
            torch.mps.empty_cache()
        if epochs_without_improvement >= patience:
            status = "early_stopped"
            break

    if not best_checkpoint.is_file():
        raise RuntimeError("training finished without a best checkpoint")
    adapter.load_checkpoint(best_checkpoint)
    parameter_count = sum(parameter.numel() for parameter in adapter.model.parameters())
    selected_record = dataset_record or FROZEN_RECORD
    frozen = json.loads(selected_record.read_text())
    dataset_version = frozen.get("dataset_version", "unknown")
    dataset_sha256 = frozen.get("canonical_tree_sha256", frozen.get("tree_sha256", "unknown"))
    summary = {
        "schema_version": 1,
        "event": "controlled_training",
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "started_at": started_at,
        "model": model_name,
        "seed": seed,
        "device": str(adapter.device),
        "dataset_version": dataset_version,
        "dataset_sha256": dataset_sha256,
        "dataset_root": display_path(selected_dataset_root),
        "initialized_from": (
            display_path(initialized_from) if initialized_from else None
        ),
        "config": display_path(config_path),
        "config_sha256": sha256(config_path),
        "train_images": len(train_indices),
        "validation_images": len(valid_indices),
        "test_split_accessed": False,
        "batch_size": batch_size,
        "effective_batch_size": batch_size * gradient_accumulation_steps,
        "validation_batch_size": validation_batch_size,
        "gradient_accumulation_steps": gradient_accumulation_steps,
        "batching": model_config.get("batching", "seeded_shuffle"),
        "learning_rate": float(model_config["learning_rate"]),
        "weight_decay": float(config["weight_decay"]),
        "augmentation": augmentation or "none",
        "maximum_epochs": maximum_epochs,
        "epochs_completed": len(history),
        "best_epoch": best_epoch,
        "best_validation_loss": best_loss,
        "early_stopping_status": status,
        "resumed": resumed,
        "resumed_from_epoch": resumed_from_epoch,
        "history": history,
        "parameter_count": parameter_count,
        "trainable_scope": trainable_scope,
        "trainable_parameter_count": trainable_parameter_count,
        "activation_checkpointing": activation_checkpointing,
        "best_checkpoint": display_path(best_checkpoint),
        "best_checkpoint_sha256": sha256(best_checkpoint),
        "best_checkpoint_bytes": best_checkpoint.stat().st_size,
        "total_duration_seconds": time.perf_counter() - wall_start,
        "status": "complete",
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    return summary
