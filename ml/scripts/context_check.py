"""Validate the persistent ML handoff and local pilot inventory."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ML_ROOT = REPO_ROOT / "ml"
REQUIRED = [
    REPO_ROOT / "AGENTS.md",
    ML_ROOT / "README.md",
    ML_ROOT / "PROJECT_STATE.md",
    ML_ROOT / "DECISIONS.md",
    ML_ROOT / "CONTEXT_SNAPSHOT.md",
    ML_ROOT / "environment.yml",
    ML_ROOT / "conda-explicit.txt",
    ML_ROOT / "data/manifest.json",
    ML_ROOT / "data/frozen_hook_sinskey_v1.json",
    ML_ROOT / "experiments/registry.jsonl",
    ML_ROOT / "annotation/ANNOTATION_POLICY.md",
    ML_ROOT / "annotation/sample_config.yaml",
    ML_ROOT / "annotation/pilot_sample.json",
    ML_ROOT / "annotation/candidate_summary.json",
    ML_ROOT / "annotation/full_dataset_manifest.json",
    ML_ROOT / "annotation/full_candidate_summary.json",
    ML_ROOT / "annotation/reviewed_summary.json",
    ML_ROOT / "MILESTONE_2_REVIEW.md",
    ML_ROOT / "MILESTONE_3_REVIEW.md",
    ML_ROOT / "MILESTONE_4_REVIEW.md",
    ML_ROOT / "annotation/FULL_DATASET_REVIEW.md",
    ML_ROOT / "configs/models.yaml",
    ML_ROOT / "experiments/smoke_results.json",
    ML_ROOT / "experiments/milestone4_review_sample.json",
    ML_ROOT / "experiments/prediction_review_manifest.json",
    ML_ROOT / "experiments/frozen_thresholds.json",
    ML_ROOT / "experiments/benchmark_results.json",
    ML_ROOT / "BENCHMARK_REPORT.md",
    ML_ROOT / "annotation/new_tray_manifest.json",
    ML_ROOT / "annotation/new_tray_detection_summary.json",
    ML_ROOT / "annotation/NEW_TRAY_DETECTION_REVIEW.md",
    ML_ROOT / "annotation/NEW_TRAY_DEFECT_MASK_REVIEW.md",
    ML_ROOT / "annotation/new_tray_detection_review_validation.json",
    ML_ROOT / "annotation/new_tray_defect_masks_reviewed_summary.json",
    ML_ROOT / "annotation/new_tray_tip_orientations.json",
    ML_ROOT / "data/combined_hook_sinskey_reviewed_v3.json",
    ML_ROOT / "data/hook_sinskey_new_tray_reviewed_v4_augmented_50_50.json",
    ML_ROOT / "configs/augmentation_v4_50_50.yaml",
    ML_ROOT / "configs/fine_tune_v4_50_50.yaml",
    ML_ROOT / "WORKSPACE_GUIDE.md",
    ML_ROOT / "configs/combined_reviewed_v3_detr_segmentation_safe.yaml",
    ML_ROOT / "experiments/combined_reviewed_v3_thresholds.json",
    ML_ROOT / "experiments/combined_reviewed_v3_benchmark_results.json",
    ML_ROOT / "COMBINED_REVIEWED_V3_REPORT.md",
    ML_ROOT / "experiments/connected_pipeline_confirmatory_results.json",
    ML_ROOT / "CONNECTED_PIPELINE_CONFIRMATORY_REPORT.md",
    ML_ROOT / "data/endpoint_selector_v1.json",
    ML_ROOT / "configs/endpoint_selector.yaml",
    ML_ROOT / "experiments/endpoint_selector_v1_results.json",
    ML_ROOT / "experiments/endpoint_selector_v1_policy.json",
    ML_ROOT / "ENDPOINT_SELECTOR_REVIEW.md",
    ML_ROOT / "data/combined_hook_sinskey_provisional_v2.json",
    ML_ROOT / "experiments/combined_provisional_benchmark_results.json",
    ML_ROOT / "COMBINED_PROVISIONAL_REPORT.md",
    ML_ROOT / "experiments/end_to_end_provisional_results.json",
]
SNAPSHOT_INPUTS = [
    REPO_ROOT / "AGENTS.md",
    ML_ROOT / "PROJECT_STATE.md",
    ML_ROOT / "DECISIONS.md",
    ML_ROOT / "environment.yml",
    ML_ROOT / "conda-explicit.txt",
    ML_ROOT / "data/manifest.json",
    ML_ROOT / "data/frozen_hook_sinskey_v1.json",
    ML_ROOT / "experiments/registry.jsonl",
    ML_ROOT / "annotation/ANNOTATION_POLICY.md",
    ML_ROOT / "annotation/sample_config.yaml",
    ML_ROOT / "annotation/pilot_sample.json",
    ML_ROOT / "annotation/candidate_summary.json",
    ML_ROOT / "annotation/full_dataset_manifest.json",
    ML_ROOT / "annotation/full_candidate_summary.json",
    ML_ROOT / "annotation/reviewed_summary.json",
    ML_ROOT / "MILESTONE_2_REVIEW.md",
    ML_ROOT / "MILESTONE_3_REVIEW.md",
    ML_ROOT / "MILESTONE_4_REVIEW.md",
    ML_ROOT / "annotation/FULL_DATASET_REVIEW.md",
    ML_ROOT / "configs/models.yaml",
    ML_ROOT / "experiments/smoke_results.json",
    ML_ROOT / "experiments/milestone4_review_sample.json",
    ML_ROOT / "experiments/prediction_review_manifest.json",
    ML_ROOT / "experiments/frozen_thresholds.json",
    ML_ROOT / "experiments/benchmark_results.json",
    ML_ROOT / "BENCHMARK_REPORT.md",
    ML_ROOT / "annotation/new_tray_manifest.json",
    ML_ROOT / "annotation/new_tray_detection_summary.json",
    ML_ROOT / "annotation/NEW_TRAY_DETECTION_REVIEW.md",
    ML_ROOT / "annotation/NEW_TRAY_DEFECT_MASK_REVIEW.md",
    ML_ROOT / "annotation/new_tray_detection_review_validation.json",
    ML_ROOT / "annotation/new_tray_defect_masks_reviewed_summary.json",
    ML_ROOT / "annotation/new_tray_tip_orientations.json",
    ML_ROOT / "data/combined_hook_sinskey_reviewed_v3.json",
    ML_ROOT / "data/hook_sinskey_new_tray_reviewed_v4_augmented_50_50.json",
    ML_ROOT / "configs/augmentation_v4_50_50.yaml",
    ML_ROOT / "configs/fine_tune_v4_50_50.yaml",
    ML_ROOT / "WORKSPACE_GUIDE.md",
    ML_ROOT / "configs/combined_reviewed_v3_detr_segmentation_safe.yaml",
    ML_ROOT / "experiments/combined_reviewed_v3_thresholds.json",
    ML_ROOT / "experiments/combined_reviewed_v3_benchmark_results.json",
    ML_ROOT / "COMBINED_REVIEWED_V3_REPORT.md",
    ML_ROOT / "experiments/connected_pipeline_confirmatory_results.json",
    ML_ROOT / "CONNECTED_PIPELINE_CONFIRMATORY_REPORT.md",
    ML_ROOT / "data/endpoint_selector_v1.json",
    ML_ROOT / "configs/endpoint_selector.yaml",
    ML_ROOT / "experiments/endpoint_selector_v1_results.json",
    ML_ROOT / "experiments/endpoint_selector_v1_policy.json",
    ML_ROOT / "ENDPOINT_SELECTOR_REVIEW.md",
    ML_ROOT / "data/combined_hook_sinskey_provisional_v2.json",
    ML_ROOT / "experiments/combined_provisional_benchmark_results.json",
    ML_ROOT / "COMBINED_PROVISIONAL_REPORT.md",
    ML_ROOT / "experiments/end_to_end_provisional_results.json",
]
CURRENT_GATE_KEYS = {
    "0": "milestone_0_inventory",
    "1": "context_handoff",
    "2": "annotation_policy",
    "3": "all_masks",
    "4": "model_smoke_tests",
    "5": "benchmark_review",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_tree(
    root: Path,
    records: list[dict[str, object]],
    expected_digest: str,
    label: str,
    errors: list[str],
) -> None:
    if not root.is_dir():
        errors.append(f"{label} missing: {root}")
        return

    actual_paths = sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.name != ".DS_Store"
    )
    expected_paths = sorted(str(record["path"]) for record in records)
    if actual_paths != expected_paths:
        missing = sorted(set(expected_paths) - set(actual_paths))
        extra = sorted(set(actual_paths) - set(expected_paths))
        errors.append(
            f"{label} file inventory mismatch "
            f"(missing={len(missing)}, extra={len(extra)})"
        )
        return


    combined = hashlib.sha256()
    records_by_path = {str(record["path"]): record for record in records}
    for relative in actual_paths:
        path = root / relative
        record = records_by_path[relative]
        size = path.stat().st_size
        digest = sha256(path)
        if size != int(record["bytes"]) or digest != record["sha256"]:
            errors.append(f"{label} hash mismatch: {relative}")
        combined.update(f"{relative}\0{size}\0{digest}\n".encode())

    if combined.hexdigest() != expected_digest:
        errors.append(f"{label} aggregate hash mismatch")


def validate_environment(errors: list[str]) -> None:
    environment = ML_ROOT / "environment.yml"
    if not environment.exists():
        return
    contents = environment.read_text().lower()
    forbidden = ("- pip", "pip:", "pip install", "pipx", "uv ")
    if any(token in contents for token in forbidden):
        errors.append("environment.yml violates the Conda-only dependency policy")
    if "conda-forge" not in contents:
        errors.append("environment.yml does not declare a Conda channel")


def validate_manifest(errors: list[str]) -> dict[str, object] | None:
    manifest_path = ML_ROOT / "data/manifest.json"
    if not manifest_path.exists():
        return None
    try:
        manifest = json.loads(manifest_path.read_text())
        dataset = manifest["dataset"]
        checkpoint = manifest["legacy_checkpoint"]
        records = dataset["files"]
        validate_tree(
            REPO_ROOT / str(dataset["local_path"]),
            records,
            str(dataset["dataset_sha256"]),
            "local dataset",
            errors,
        )
        validate_tree(
            Path(str(dataset["source_path"])),
            records,
            str(dataset["source_dataset_sha256"]),
            "Desktop source dataset",
            errors,
        )

        local_weight = REPO_ROOT / str(checkpoint["local_path"])
        source_weight = Path(str(checkpoint["source_path"]))
        for path, expected, label in (
            (local_weight, checkpoint["sha256"], "local checkpoint"),
            (source_weight, checkpoint["source_sha256"], "Desktop source checkpoint"),
        ):
            if not path.is_file():
                errors.append(f"{label} missing: {path}")
            elif sha256(path) != expected:
                errors.append(f"{label} hash mismatch: {path}")
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        errors.append(f"invalid dataset manifest: {exc}")
        return None
    return manifest


def validate_registry(errors: list[str]) -> None:
    registry = ML_ROOT / "experiments/registry.jsonl"
    if not registry.exists():
        return
    for number, line in enumerate(registry.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"invalid registry JSON on line {number}: {exc}")


def validate_annotation_pilot(errors: list[str]) -> None:
    sample_path = ML_ROOT / "annotation/pilot_sample.json"
    summary_path = ML_ROOT / "annotation/candidate_summary.json"
    if not sample_path.exists() or not summary_path.exists():
        return
    try:
        sample = json.loads(sample_path.read_text())
        summary = json.loads(summary_path.read_text())
        if sample["sample_size"] != 20:
            errors.append("annotation pilot does not contain exactly 20 images")
        if "test" not in sample["excluded_splits"] or any(
            record["split"] == "test" for record in sample["images"]
        ):
            errors.append("annotation pilot does not fully exclude the test split")
        if sample["candidate_generation"].get("status") != "complete":
            errors.append("SAM2 candidate generation is incomplete")
            return
        if summary["candidate_mask_count"] != 15:
            errors.append("unexpected SAM2 candidate-mask count")

        local_package = REPO_ROOT / summary["local_package"]
        coco = local_package / "cvat_dataset/annotations/instances_default.json"
        cvat_zip = REPO_ROOT / summary["cvat_zip"]
        for path, expected_hash, label in (
            (coco, summary["coco_sha256"], "candidate COCO"),
            (cvat_zip, summary["cvat_zip_sha256"], "CVAT import ZIP"),
        ):
            if not path.is_file():
                errors.append(f"{label} missing: {path}")
            elif sha256(path) != expected_hash:
                errors.append(f"{label} hash mismatch: {path}")
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        errors.append(f"invalid annotation pilot metadata: {exc}")


def validate_full_annotation_candidates(errors: list[str]) -> None:
    manifest_path = ML_ROOT / "annotation/full_dataset_manifest.json"
    summary_path = ML_ROOT / "annotation/full_candidate_summary.json"
    if not manifest_path.exists() or not summary_path.exists():
        return
    try:
        manifest = json.loads(manifest_path.read_text())
        summary = json.loads(summary_path.read_text())
        if manifest["sample_size"] != 240 or summary["image_count"] != 240:
            errors.append("full annotation package does not contain 240 images")
        if summary["defective_image_count"] != 179:
            errors.append("full annotation package does not contain 179 defective images")
        if summary["healthy_image_count"] != 61:
            errors.append("full annotation package does not contain 61 healthy images")
        if summary["candidate_mask_count"] != 199:
            errors.append("full annotation package does not contain 199 masks")
        if manifest["candidate_generation"].get("status") != "complete":
            errors.append("full SAM2 candidate generation is incomplete")
        if not manifest["leakage_audit"].get("passed"):
            errors.append("full annotation manifest reports cross-split leakage")

        local_package = REPO_ROOT / summary["local_package"]
        coco = local_package / "cvat_dataset/annotations/instances_default.json"
        cvat_zip = REPO_ROOT / summary["cvat_zip"]
        for path, expected_hash, label in (
            (coco, summary["coco_sha256"], "full candidate COCO"),
            (cvat_zip, summary["cvat_zip_sha256"], "full CVAT import ZIP"),
        ):
            if not path.is_file():
                errors.append(f"{label} missing: {path}")
            elif sha256(path) != expected_hash:
                errors.append(f"{label} hash mismatch: {path}")
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        errors.append(f"invalid full annotation metadata: {exc}")


def validate_reviewed_annotation_export(errors: list[str]) -> None:
    summary_path = ML_ROOT / "annotation/reviewed_summary.json"
    if not summary_path.exists():
        return
    try:
        summary = json.loads(summary_path.read_text())
        reviewed_zip = REPO_ROOT / summary["reviewed_export"]
        if not reviewed_zip.is_file():
            errors.append(f"reviewed export missing: {reviewed_zip}")
            return
        if sha256(reviewed_zip) != summary["reviewed_zip_sha256"]:
            errors.append("reviewed export ZIP hash mismatch")
        if summary["images"] != 240 or summary["masks"] != 199:
            errors.append("reviewed export summary has unexpected image/mask counts")
        if summary["healthy_images_with_masks"] != 0:
            errors.append("reviewed export summary reports annotated healthy images")
        if not all(summary["checks"].values()):
            errors.append("reviewed export summary contains a failed check")
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        errors.append(f"invalid reviewed export metadata: {exc}")


def validate_frozen_dataset(errors: list[str]) -> None:
    record_path = ML_ROOT / "data/frozen_hook_sinskey_v1.json"
    if not record_path.exists():
        return
    try:
        record = json.loads(record_path.read_text())
        if not record.get("test_split_frozen"):
            errors.append("canonical Hook Sinskey test split is not frozen")
        if record["images"] != 240 or record["instances"] != 199:
            errors.append("canonical dataset has unexpected image/instance counts")
        validate_tree(
            REPO_ROOT / record["canonical_local_path"],
            record["files"],
            record["canonical_tree_sha256"],
            "frozen canonical dataset",
            errors,
        )
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        errors.append(f"invalid frozen dataset record: {exc}")


def validate_model_smoke_tests(errors: list[str]) -> None:
    summary_path = ML_ROOT / "experiments/smoke_results.json"
    review_path = ML_ROOT / "experiments/prediction_review_manifest.json"
    try:
        summary = json.loads(summary_path.read_text())
        if summary["status"] != "passed_awaiting_prediction_review":
            errors.append("model smoke-test summary is not awaiting prediction review")
        if summary["test_split_accessed"]:
            errors.append("model smoke tests report frozen test-split access")
        models = summary["models"]
        expected = {
            "legacy_yolo",
            "detr_detection",
            "detr_segmentation",
            "mask_rcnn",
        }
        if {item["model"] for item in models} != expected:
            errors.append("model smoke-test summary does not contain all four adapters")
        for item in models:
            if item["status"] != "passed" or not item["checkpoint_reload_ok"]:
                errors.append(f"smoke test is incomplete: {item['model']}")
            if item["test_split_accessed"] or item["split"] != "train":
                errors.append(f"invalid smoke-test split usage: {item['model']}")

        review = json.loads(review_path.read_text())
        if review["split"] != "valid" or review["test_split_accessed"]:
            errors.append("prediction review did not remain validation-only")
        if review["defective_images"] != 5 or review["healthy_images"] != 5:
            errors.append("prediction review does not use five images per status")
        if {item["model"] for item in review["models"]} != expected:
            errors.append("prediction review does not contain all four adapters")
        for item in review["models"]:
            prediction_path = REPO_ROOT / item["predictions"]
            if not prediction_path.is_file():
                errors.append(f"prediction review output missing: {item['model']}")
            elif sha256(prediction_path) != item["predictions_sha256"]:
                errors.append(f"prediction review hash mismatch: {item['model']}")
            elif len(prediction_path.read_text().splitlines()) != 10:
                errors.append(f"prediction review count mismatch: {item['model']}")
        index = REPO_ROOT / review["local_index"]
        if not index.is_file():
            errors.append("prediction review HTML index is missing")
        overlays = list((index.parent / "overlays").rglob("*.jpg"))
        if len(overlays) != 40:
            errors.append("prediction review does not contain 40 overlays")
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        errors.append(f"invalid model smoke-test metadata: {exc}")


def validate_benchmark(errors: list[str]) -> None:
    freeze_path = ML_ROOT / "experiments/frozen_thresholds.json"
    result_path = ML_ROOT / "experiments/benchmark_results.json"
    try:
        freeze = json.loads(freeze_path.read_text())
        result = json.loads(result_path.read_text())
        expected = {
            "legacy_yolo",
            "detr_detection",
            "detr_segmentation",
            "mask_rcnn",
        }
        if freeze["status"] != "frozen_before_test" or freeze["test_split_accessed"]:
            errors.append("validation thresholds were not frozen before test access")
        if {item["model"] for item in freeze["models"]} != expected:
            errors.append("threshold freeze does not contain all four models")
        if result["status"] != "awaiting_human_review":
            errors.append("benchmark result is not awaiting human review")
        if result["test_images"] != 24 or result["test_evaluations_per_model"] != 1:
            errors.append("benchmark test access count is invalid")
        if {item["model"] for item in result["models"]} != expected:
            errors.append("benchmark result does not contain all four models")
        for item in result["models"]:
            model = item["model"]
            run_dir = ML_ROOT / "runs/benchmark" / model
            summary = run_dir / "test_summary.json"
            predictions = run_dir / "test_predictions.jsonl"
            if not summary.is_file() or sha256(summary) != item["test_summary_sha256"]:
                errors.append(f"test summary missing or changed: {model}")
            if (
                not predictions.is_file()
                or sha256(predictions) != item["test_predictions_sha256"]
            ):
                errors.append(f"test predictions missing or changed: {model}")
        gallery = REPO_ROOT / result["error_gallery"]
        if not gallery.is_file():
            errors.append("benchmark error gallery index is missing")
        elif len(list(gallery.parent.glob("*.jpg"))) != result["error_count"]:
            errors.append("benchmark error-gallery count mismatch")
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        errors.append(f"invalid benchmark metadata: {exc}")


def validate_new_tray_candidates(errors: list[str]) -> None:
    summary_path = ML_ROOT / "annotation/new_tray_detection_summary.json"
    if not summary_path.exists():
        return
    try:
        summary = json.loads(summary_path.read_text())
        if summary["images"] != 151 or summary["hook_sinskey_instances"] != 223:
            errors.append("redesigned-tray candidate package has unexpected counts")
        if summary["review_status"] not in {"pending", "approved"}:
            errors.append("redesigned-tray candidate package has invalid review status")
        if summary["class_mapping"] != {
            "0": "chop phaco",
            "1": "forceps macpherson",
            "2": "forceps utrata",
            "3": "hook sinskey",
        }:
            errors.append("redesigned-tray class mapping differs from inherited detector")
        local_output = REPO_ROOT / summary["local_output"]
        coco = local_output / "cvat_dataset/annotations/instances_default.json"
        queue = local_output / "review_queue.json"
        cvat_zip = REPO_ROOT / summary["cvat_zip"]
        for path, expected_hash, label in (
            (coco, summary["coco_sha256"], "redesigned-tray candidate COCO"),
            (queue, summary["review_queue_sha256"], "redesigned-tray review queue"),
            (cvat_zip, summary["cvat_zip_sha256"], "redesigned-tray CVAT ZIP"),
        ):
            if not path.is_file():
                errors.append(f"{label} missing: {path}")
            elif sha256(path) != expected_hash:
                errors.append(f"{label} hash mismatch: {path}")
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        errors.append(f"invalid redesigned-tray candidate metadata: {exc}")


def validate_new_tray_reviewed_dataset(errors: list[str]) -> None:
    review_path = ML_ROOT / "annotation/new_tray_defect_masks_reviewed_summary.json"
    combined_path = ML_ROOT / "data/combined_hook_sinskey_reviewed_v3.json"
    if not review_path.exists() or not combined_path.exists():
        return
    try:
        review = json.loads(review_path.read_text())
        reviewed_zip = REPO_ROOT / review["reviewed_export"]
        if not reviewed_zip.is_file() or sha256(reviewed_zip) != review["reviewed_zip_sha256"]:
            errors.append("redesigned-tray reviewed mask ZIP is missing or changed")
        if (
            review["images"] != 226
            or review["masks"] != 154
            or review["defective_images"] != 154
            or review["healthy_images"] != 72
            or review["healthy_images_with_masks"] != 0
        ):
            errors.append("redesigned-tray reviewed masks have unexpected counts")
        if not all(review["checks"].values()):
            errors.append("redesigned-tray reviewed mask summary contains a failed check")

        combined = json.loads(combined_path.read_text())
        if combined["status"] != "human_reviewed_frozen" or not combined["test_split_frozen"]:
            errors.append("combined reviewed v3 dataset is not frozen")
        counts = combined["counts"]
        if (
            counts["train_images"] != 342
            or counts["valid_images"] != 76
            or counts["test_images"] != 48
            or sum(counts[f"{split}_instances"] for split in ("train", "valid", "test")) != 353
        ):
            errors.append("combined reviewed v3 dataset has unexpected counts")
        validate_tree(
            REPO_ROOT / combined["local_path"],
            combined["files"],
            combined["tree_sha256"],
            "combined reviewed v3 dataset",
            errors,
        )
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        errors.append(f"invalid redesigned-tray reviewed dataset metadata: {exc}")


def validate_endpoint_selector(errors: list[str]) -> None:
    manifest_path = ML_ROOT / "data/endpoint_selector_v1.json"
    result_path = ML_ROOT / "experiments/endpoint_selector_v1_results.json"
    policy_path = ML_ROOT / "experiments/endpoint_selector_v1_policy.json"
    if not all(path.exists() for path in (manifest_path, result_path, policy_path)):
        return
    try:
        manifest = json.loads(manifest_path.read_text())
        if manifest["sample_count"] != 452 or manifest["source_instrument_count"] != 226:
            errors.append("endpoint selector dataset has unexpected counts")
        if manifest["capture_group_leakage"]:
            errors.append("endpoint selector dataset has capture-group leakage")
        expected_counts = {
            "train_handle": 161,
            "train_tip": 161,
            "valid_handle": 41,
            "valid_tip": 41,
            "test_handle": 24,
            "test_tip": 24,
        }
        if manifest["counts"] != expected_counts:
            errors.append("endpoint selector split counts changed")
        for record in manifest["records"]:
            image = REPO_ROOT / record["image_path"]
            if not image.is_file() or sha256(image) != record["sha256"]:
                errors.append(f"endpoint crop missing or changed: {record['candidate_id']}")
                break

        result = json.loads(result_path.read_text())
        checkpoint = REPO_ROOT / result["checkpoint"]
        predictions = REPO_ROOT / result["test_predictions"]
        if not checkpoint.is_file() or sha256(checkpoint) != result["checkpoint_sha256"]:
            errors.append("endpoint selector checkpoint is missing or changed")
        if not predictions.is_file() or sha256(predictions) != result["test_predictions_sha256"]:
            errors.append("endpoint selector test predictions are missing or changed")
        if result["validation_pair_selection"]["accuracy"] != 1.0:
            errors.append("endpoint selector validation pair accuracy changed")
        if result["test_pair_selection"]["accuracy"] != 1.0:
            errors.append("endpoint selector test pair accuracy changed")

        policy = json.loads(policy_path.read_text())
        policy_predictions = REPO_ROOT / policy["test_predictions"]
        if not policy_predictions.is_file() or sha256(policy_predictions) != policy["test_predictions_sha256"]:
            errors.append("endpoint selector policy predictions are missing or changed")
        if policy["test"]["selection_accuracy"] != 1.0 or policy["test"]["review_required"] != 4:
            errors.append("endpoint selector frozen test policy changed")
        selected = REPO_ROOT / policy["selected_tip_directory"]
        if not selected.is_dir() or len(list(selected.glob("*.jpg"))) != 24:
            errors.append("endpoint selector selected-tip outputs are incomplete")
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        errors.append(f"invalid endpoint selector metadata: {exc}")


def validate_combined_reviewed_benchmark(errors: list[str]) -> None:
    dataset_path = ML_ROOT / "data/combined_hook_sinskey_reviewed_v3.json"
    freeze_path = ML_ROOT / "experiments/combined_reviewed_v3_thresholds.json"
    result_path = ML_ROOT / "experiments/combined_reviewed_v3_benchmark_results.json"
    if not all(path.exists() for path in (dataset_path, freeze_path, result_path)):
        return
    try:
        dataset = json.loads(dataset_path.read_text())
        freeze = json.loads(freeze_path.read_text())
        result = json.loads(result_path.read_text())
        expected = {
            "legacy_yolo",
            "detr_detection",
            "detr_segmentation",
            "mask_rcnn",
        }
        if freeze["dataset_sha256"] != dataset["tree_sha256"]:
            errors.append("combined reviewed-v3 threshold dataset hash changed")
        if freeze["selection_split"] != "valid" or freeze["test_split_accessed"]:
            errors.append("combined reviewed-v3 thresholds were not validation-only")
        if {item["model"] for item in freeze["operating_points"]} != expected:
            errors.append("combined reviewed-v3 threshold freeze is incomplete")
        if result["dataset_sha256"] != dataset["tree_sha256"]:
            errors.append("combined reviewed-v3 result dataset hash changed")
        if result["status"] != "human_approved":
            errors.append("combined reviewed-v3 benchmark approval is not recorded")
        if result["test_images"] != 48 or result["test_evaluations_per_model"] != 1:
            errors.append("combined reviewed-v3 test access count is invalid")
        if {item["model"] for item in result["models"]} != expected:
            errors.append("combined reviewed-v3 benchmark does not contain four models")
        if sha256(freeze_path) != result["threshold_freeze_sha256"]:
            errors.append("combined reviewed-v3 threshold freeze hash changed")

        for item in result["models"]:
            model = item["model"]
            checkpoint = REPO_ROOT / item["checkpoint"]
            predictions = REPO_ROOT / item["prediction_records"]
            outputs = REPO_ROOT / item["structured_outputs"]
            if not checkpoint.is_file() or sha256(checkpoint) != item["checkpoint_sha256"]:
                errors.append(f"combined reviewed-v3 checkpoint missing or changed: {model}")
            if not predictions.is_file() or len(predictions.read_text().splitlines()) != 48:
                errors.append(f"combined reviewed-v3 prediction count changed: {model}")
            overlays = outputs / "overlays"
            if not overlays.is_dir() or len(list(overlays.glob("*.jpg"))) != 48:
                errors.append(f"combined reviewed-v3 overlay count changed: {model}")

        gallery = REPO_ROOT / result["error_gallery"]
        if not gallery.is_file():
            errors.append("combined reviewed-v3 error gallery is missing")
        figure_dir = ML_ROOT / "presentation/figures/combined_reviewed_v3"
        if len(list(figure_dir.glob("*.png"))) != 7:
            errors.append("combined reviewed-v3 presentation figure set is incomplete")
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        errors.append(f"invalid combined reviewed-v3 benchmark metadata: {exc}")


def validate_connected_pipeline(errors: list[str]) -> None:
    result_path = ML_ROOT / "experiments/connected_pipeline_confirmatory_results.json"
    if not result_path.exists():
        return
    try:
        result = json.loads(result_path.read_text())
        design = result["evaluation_design"]
        if result["status"] != "confirmatory_awaiting_human_review":
            errors.append("connected pipeline is not awaiting confirmatory review")
        if (
            design["test_tray_images"] != 16
            or design["expected_hook_instances"] != 24
            or design["test_informed_tuning"]
        ):
            errors.append("connected pipeline evaluation design changed")
        policy = result["frozen_policy"]
        for key in ("tray_checkpoint", "endpoint_checkpoint", "mask_checkpoint"):
            checkpoint = REPO_ROOT / policy[key]
            expected_hash = policy[f"{key}_sha256"]
            if not checkpoint.is_file() or sha256(checkpoint) != expected_hash:
                errors.append(f"connected pipeline checkpoint missing or changed: {key}")
        if result["tool_detection"]["matched"] != 22:
            errors.append("connected pipeline matched-tool count changed")
        if result["end_to_end"]["localized_successes"] != 21:
            errors.append("connected pipeline localized-success count changed")
        expected_records = {
            "instance_records": 24,
            "tray_records": 16,
            "extra_prediction_records": 7,
        }
        for key, expected_count in expected_records.items():
            path = REPO_ROOT / result[key]
            if not path.is_file() or len(path.read_text().splitlines()) != expected_count:
                errors.append(f"connected pipeline record count changed: {key}")
        overlay_dir = REPO_ROOT / result["overlay_directory"]
        if not overlay_dir.is_dir() or len(list(overlay_dir.glob("*.jpg"))) != 16:
            errors.append("connected pipeline overlay set is incomplete")
        figure_dir = ML_ROOT / "presentation/figures/connected_pipeline_confirmatory"
        if len(list(figure_dir.glob("*.png"))) != 7:
            errors.append("connected pipeline presentation figure set is incomplete")
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        errors.append(f"invalid connected pipeline metadata: {exc}")


def validate_augmented_v4(errors: list[str]) -> None:
    record_path = ML_ROOT / "data/hook_sinskey_new_tray_reviewed_v4_augmented_50_50.json"
    if not record_path.exists():
        return
    try:
        record = json.loads(record_path.read_text())
        root = REPO_ROOT / record["local_path"]
        if not root.is_dir():
            errors.append("v4 augmented dataset directory is missing")
            return
        if (
            record["train_images"] != 322
            or record["validation_images"] != 41
            or record["test_images"] != 24
            or record["original_augmented_ratio"] != "161:161"
            or record["source_domain_filter"] != "reviewed_new_tray"
        ):
            errors.append("v4 augmented dataset split counts changed")
        if record["validation_and_test_augmented"] or not record["test_split_frozen"]:
            errors.append("v4 augmented dataset violates frozen evaluation splits")
        if record["review_status"] not in {"pending", "approved"}:
            errors.append("v4 augmented dataset has an invalid review state")
        gallery = REPO_ROOT / record["review_gallery"]
        if not gallery.is_file():
            errors.append("v4 augmentation review gallery is missing")
        for item in record["files"]:
            path = root / item["path"]
            if (
                not path.is_file()
                or path.stat().st_size != item["bytes"]
                or sha256(path) != item["sha256"]
            ):
                errors.append(f"v4 augmented file missing or changed: {item['path']}")
                break
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        errors.append(f"invalid v4 augmented dataset metadata: {exc}")


def validate_state(
    manifest: dict[str, object] | None, errors: list[str], notices: list[str]
) -> None:
    state_path = ML_ROOT / "PROJECT_STATE.md"
    if not state_path.exists():
        return
    contents = state_path.read_text()
    for required_text in (
        "Current milestone:",
        "Status:",
        "Last verified date:",
        "Next action",
        "Human gate record",
    ):
        if required_text not in contents:
            errors.append(f"PROJECT_STATE.md missing field: {required_text}")

    branch_match = re.search(r"^- Branch: `([^`]+)`", contents, re.MULTILINE)
    if branch_match:
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        if branch != branch_match.group(1):
            errors.append(
                f"PROJECT_STATE.md branch is stale: records {branch_match.group(1)}, actual {branch}"
            )

    date_match = re.search(
        r"^- Last verified date: (\d{4}-\d{2}-\d{2})", contents, re.MULTILINE
    )
    if date_match and manifest:
        verified = date.fromisoformat(date_match.group(1))
        generated = date.fromisoformat(str(manifest["generated_on"]))
        if verified < generated:
            errors.append("PROJECT_STATE.md predates the current dataset manifest")

    milestone_match = re.search(r"^- Current milestone: (\d+)", contents, re.MULTILINE)
    if milestone_match and manifest:
        gate_key = CURRENT_GATE_KEYS.get(milestone_match.group(1))
        if gate_key:
            decision = str(manifest["review"].get(gate_key, "missing"))
            if decision != "approved":
                notices.append(f"current human gate is incomplete: {gate_key}={decision}")


def validate_snapshot_freshness(errors: list[str]) -> None:
    snapshot = ML_ROOT / "CONTEXT_SNAPSHOT.md"
    if not snapshot.exists():
        return
    newest_input = max(path.stat().st_mtime_ns for path in SNAPSHOT_INPUTS if path.exists())
    if snapshot.stat().st_mtime_ns < newest_input:
        errors.append(
            "CONTEXT_SNAPSHOT.md is stale; regenerate it with context_snapshot.py"
        )


def validate_local_artifact_policy(errors: list[str]) -> None:
    result = subprocess.run(
        [
            "git",
            "ls-files",
            "ml/data/local",
            "ml/artifacts",
            "ml/annotation/local",
            "ml/cvat",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    if result.stdout.strip():
        errors.append("raw data or model artifacts are tracked by Git")


def main() -> None:
    errors: list[str] = []
    notices: list[str] = []
    for path in REQUIRED:
        if not path.is_file():
            errors.append(f"missing required file: {path.relative_to(REPO_ROOT)}")

    validate_environment(errors)
    manifest = validate_manifest(errors)
    validate_registry(errors)
    validate_annotation_pilot(errors)
    validate_full_annotation_candidates(errors)
    validate_reviewed_annotation_export(errors)
    validate_frozen_dataset(errors)
    validate_model_smoke_tests(errors)
    validate_benchmark(errors)
    validate_new_tray_candidates(errors)
    validate_new_tray_reviewed_dataset(errors)
    validate_endpoint_selector(errors)
    validate_combined_reviewed_benchmark(errors)
    validate_connected_pipeline(errors)
    validate_augmented_v4(errors)
    validate_state(manifest, errors, notices)
    validate_snapshot_freshness(errors)
    validate_local_artifact_policy(errors)

    if errors:
        print("Context check failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print("Context check passed.")
    for notice in notices:
        print(f"Review notice: {notice}")


if __name__ == "__main__":
    main()
