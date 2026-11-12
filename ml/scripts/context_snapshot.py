"""Regenerate a compact, repository-backed handoff snapshot."""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ML_ROOT = REPO_ROOT / "ml"
OUTPUT = ML_ROOT / "CONTEXT_SNAPSHOT.md"


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def main() -> None:
    manifest = json.loads((ML_ROOT / "data/manifest.json").read_text())
    state = (ML_ROOT / "PROJECT_STATE.md").read_text().strip()
    metrics = manifest["historical_best_validation_metrics"]
    annotation_section = ""
    sample_path = ML_ROOT / "annotation/pilot_sample.json"
    summary_path = ML_ROOT / "annotation/candidate_summary.json"
    if sample_path.exists() and summary_path.exists():
        sample = json.loads(sample_path.read_text())
        summary = json.loads(summary_path.read_text())
        annotation_section = f"""
## Annotation pilot

- Sample images: {sample['sample_size']} ({summary['defective_image_count']} defective, {summary['healthy_image_count']} healthy)
- Candidate masks: {summary['candidate_mask_count']}
- Test images used: 0
- SAM2 checkpoint: `{summary['model_id']}@{summary['model_revision']}`
- Device: `{summary['device']}`
- Review status: `{summary['review_status']}`
- Docker command available: {str(shutil.which('docker') is not None).lower()}
- Data warning: class is perfectly confounded with acquisition groups `6-4` (defective) and `6-3` (healthy).
"""
    full_annotation_section = ""
    full_manifest_path = ML_ROOT / "annotation/full_dataset_manifest.json"
    full_summary_path = ML_ROOT / "annotation/full_candidate_summary.json"
    if full_manifest_path.exists() and full_summary_path.exists():
        full_manifest = json.loads(full_manifest_path.read_text())
        full_summary = json.loads(full_summary_path.read_text())
        full_annotation_section = f"""
## Full-dataset annotation

- Images: {full_summary['image_count']} ({full_summary['defective_image_count']} defective, {full_summary['healthy_image_count']} healthy)
- Candidate masks: {full_summary['candidate_mask_count']}
- Candidate COCO SHA-256: `{full_summary['coco_sha256']}`
- Candidate CVAT ZIP SHA-256: `{full_summary['cvat_zip_sha256']}`
- Cross-split source/hash leakage: {str(not full_manifest['leakage_audit']['passed']).lower()}
- Review status: `{full_summary['review_status']}`
- Local CVAT URL: `http://localhost:8080`
"""
    reviewed_section = ""
    reviewed_summary_path = ML_ROOT / "annotation/reviewed_summary.json"
    if reviewed_summary_path.exists():
        reviewed = json.loads(reviewed_summary_path.read_text())
        reviewed_section = f"""
## Reviewed ground truth

- Reviewer/date: {reviewed['reviewer']} / {reviewed['reviewed_on']}
- Images/masks: {reviewed['images']} / {reviewed['masks']}
- Healthy images with masks: {reviewed['healthy_images_with_masks']}
- Reviewed ZIP SHA-256: `{reviewed['reviewed_zip_sha256']}`
- Reviewed COCO SHA-256: `{reviewed['reviewed_coco_sha256']}`
- Status: `{reviewed['review_status']}`
"""
    frozen_section = ""
    frozen_path = ML_ROOT / "data/frozen_hook_sinskey_v1.json"
    if frozen_path.exists():
        frozen = json.loads(frozen_path.read_text())
        frozen_section = f"""
## Frozen benchmark dataset

- Version: `{frozen['dataset_version']}`
- Canonical tree SHA-256: `{frozen['canonical_tree_sha256']}`
- Train/validation/test images: {frozen['counts']['train']['images']} / {frozen['counts']['valid']['images']} / {frozen['counts']['test']['images']}
- Test split frozen: {str(frozen['test_split_frozen']).lower()}
"""
    model_section = ""
    smoke_path = ML_ROOT / "experiments/smoke_results.json"
    review_path = ML_ROOT / "experiments/prediction_review_manifest.json"
    if smoke_path.exists() and review_path.exists():
        smoke = json.loads(smoke_path.read_text())
        review = json.loads(review_path.read_text())
        model_section = f"""
## Milestone 4 model checks

- Adapter smoke status: `{smoke['status']}`
- Models passed: {len(smoke['models'])}
- Device: `{smoke['models'][0]['device']}`
- Frozen test split accessed: {str(smoke['test_split_accessed']).lower()}
- Prediction review: `{review['review_status']}`
- Review scope: {review['defective_images']} defective + {review['healthy_images']} healthy validation images per model
- Local review index: `{review['local_index']}`
"""
    benchmark_section = ""
    benchmark_path = ML_ROOT / "experiments/benchmark_results.json"
    if benchmark_path.exists():
        benchmark = json.loads(benchmark_path.read_text())
        model_lines = "\n".join(
            f"- {item['model']}: accuracy {item['classification']['accuracy']:.3f}, "
            f"sensitivity {item['classification']['sensitivity']:.3f}, "
            f"specificity {item['classification']['specificity']:.3f}, "
            f"F1 {item['classification']['f1']:.3f}"
            for item in benchmark["models"]
        )
        benchmark_section = f"""
## Milestone 5 controlled benchmark

- Status: `{benchmark['status']}`
- Frozen test images: {benchmark['test_images']}
- Evaluations per model: {benchmark['test_evaluations_per_model']}
- Error overlays: {benchmark['error_count']}
{model_lines}
- Report: `ml/BENCHMARK_REPORT.md`
- Local error gallery: `{benchmark['error_gallery']}`
"""
    new_tray_section = ""
    new_tray_path = ML_ROOT / "annotation/new_tray_detection_summary.json"
    if new_tray_path.exists():
        new_tray = json.loads(new_tray_path.read_text())
        new_tray_section = f"""
## Redesigned-tray detector expansion

- Source dataset SHA-256: `{new_tray['source_dataset_sha256']}`
- Images / Hook Sinskey instances: {new_tray['images']} / {new_tray['hook_sinskey_instances']}
- Train/validation/test images: {new_tray['counts']['train_images']} / {new_tray['counts']['valid_images']} / {new_tray['counts']['test_images']}
- Candidate method: {new_tray['candidate_method']}
- Review status: `{new_tray['review_status']}`
- Candidate ZIP SHA-256: `{new_tray['cvat_zip_sha256']}`
- Local CVAT URL: `http://localhost:8080`
- Human gate: `ml/annotation/NEW_TRAY_DETECTION_REVIEW.md`
"""
    reviewed_tray_section = ""
    reviewed_tray_path = ML_ROOT / "annotation/new_tray_detection_review_validation.json"
    regenerated_mask_path = ML_ROOT / "annotation/new_tray_defect_model_cropped_summary.json"
    if reviewed_tray_path.exists() and regenerated_mask_path.exists():
        reviewed_tray = json.loads(reviewed_tray_path.read_text())
        regenerated_masks = json.loads(regenerated_mask_path.read_text())
        reviewed_tray_section = f"""
## Human-reviewed redesigned-tray boxes

- Reviewer/date: {reviewed_tray['reviewer']} / {reviewed_tray['reviewed_on']}
- Validation status: `{reviewed_tray['status']}`
- Images / reviewed boxes: {reviewed_tray['images']} / {reviewed_tray['boxes']}
- Reviewed ZIP SHA-256: `{reviewed_tray['reviewed_zip_sha256']}`
- Regenerated crops / SAM2 masks: {regenerated_masks['image_count']} / {regenerated_masks['candidate_mask_count']}
- Healthy negative crops: {regenerated_masks['healthy_image_count']}
- Mask-review procedure: `ml/annotation/NEW_TRAY_DEFECT_MASK_REVIEW.md`
"""
    reviewed_masks_section = ""
    reviewed_masks_path = ML_ROOT / "annotation/new_tray_defect_masks_reviewed_summary.json"
    combined_reviewed_path = ML_ROOT / "data/combined_hook_sinskey_reviewed_v3.json"
    if reviewed_masks_path.exists() and combined_reviewed_path.exists():
        reviewed_masks = json.loads(reviewed_masks_path.read_text())
        combined_reviewed = json.loads(combined_reviewed_path.read_text())
        counts = combined_reviewed["counts"]
        reviewed_masks_section = f"""
## Frozen redesigned-tray masks and combined dataset

- Reviewer/date: {reviewed_masks['reviewer']} / {reviewed_masks['reviewed_on']}
- Redesigned-tray images / masks: {reviewed_masks['images']} / {reviewed_masks['masks']}
- Defective / healthy: {reviewed_masks['defective_images']} / {reviewed_masks['healthy_images']}
- Candidate masks changed by reviewer: {reviewed_masks['candidate_comparison']['images_with_changed_mask_pixels']}
- Combined dataset status: `{combined_reviewed['status']}`
- Combined train/validation/test images: {counts['train_images']} / {counts['valid_images']} / {counts['test_images']}
- Combined instances: {sum(counts[f'{split}_instances'] for split in ('train', 'valid', 'test'))}
- Combined tree SHA-256: `{combined_reviewed['tree_sha256']}`
- Next action: review the completed authoritative benchmark, figures, and error gallery.
"""
    endpoint_section = ""
    endpoint_manifest_path = ML_ROOT / "data/endpoint_selector_v1.json"
    endpoint_result_path = ML_ROOT / "experiments/endpoint_selector_v1_results.json"
    endpoint_policy_path = ML_ROOT / "experiments/endpoint_selector_v1_policy.json"
    if all(path.exists() for path in (endpoint_manifest_path, endpoint_result_path, endpoint_policy_path)):
        endpoint_manifest = json.loads(endpoint_manifest_path.read_text())
        endpoint_result = json.loads(endpoint_result_path.read_text())
        endpoint_policy = json.loads(endpoint_policy_path.read_text())
        endpoint_section = f"""
## Endpoint selector

- Dataset samples / source instruments: {endpoint_manifest['sample_count']} / {endpoint_manifest['source_instrument_count']}
- Dataset SHA-256: `{endpoint_manifest['dataset_sha256']}`
- Validation/test pair accuracy: {endpoint_result['validation_pair_selection']['accuracy']:.3f} / {endpoint_result['test_pair_selection']['accuracy']:.3f}
- Validation-derived review margin: {endpoint_policy['review_policy']['score_margin_threshold']:.6f}
- Test automatic accepts / review queue: {endpoint_policy['test']['automatic_accepts']} / {endpoint_policy['test']['review_required']}
- Human gate: `ml/ENDPOINT_SELECTOR_REVIEW.md`
- Gallery: `{endpoint_result['gallery']}`
"""
    authoritative_section = ""
    authoritative_path = ML_ROOT / "experiments/combined_reviewed_v3_benchmark_results.json"
    threshold_path = ML_ROOT / "experiments/combined_reviewed_v3_thresholds.json"
    if authoritative_path.exists() and threshold_path.exists():
        authoritative = json.loads(authoritative_path.read_text())
        threshold_freeze = json.loads(threshold_path.read_text())
        authoritative_lines = "\n".join(
            f"- {item['model']}: accuracy {item['classification']['accuracy']:.3f}, "
            f"specificity {item['classification']['specificity']:.3f}, "
            f"F1 {item['classification']['f1']:.3f}"
            for item in authoritative["models"]
        )
        authoritative_section = f"""
## Authoritative combined reviewed-v3 benchmark

- Status: `{authoritative['status']}`
- Dataset SHA-256: `{authoritative['dataset_sha256']}`
- Frozen test images / evaluations per model: {authoritative['test_images']} / {authoritative['test_evaluations_per_model']}
- Threshold selection split: `{threshold_freeze['selection_split']}`
{authoritative_lines}
- Physical training images: 342; transforms were generated on-the-fly.
- Maximum training exposure: 7,866 image presentations (23 epochs x 342), not 7,866 independent images.
- Report: `ml/COMBINED_REVIEWED_V3_REPORT.md`
- Figures: `ml/presentation/figures/combined_reviewed_v3/`
- Local error gallery: `{authoritative['error_gallery']}`
"""
    connected_section = ""
    connected_path = ML_ROOT / "experiments/connected_pipeline_confirmatory_results.json"
    if connected_path.exists():
        connected = json.loads(connected_path.read_text())
        connected_section = f"""
## Connected tray-to-mask confirmatory benchmark

- Status: `{connected['status']}`
- Cohort: {connected['evaluation_design']['test_tray_images']} trays / {connected['evaluation_design']['expected_hook_instances']} expected Hook Sinskey instances
- Tool precision / recall: {connected['tool_detection']['precision']:.3f} / {connected['tool_detection']['recall']:.3f}
- Endpoint accuracy: {connected['endpoint_selection']['accuracy']:.3f}
- End-to-end decision / localized success: {connected['end_to_end']['decision_success_rate']:.3f} / {connected['end_to_end']['localized_success_rate']:.3f}
- Full-tray mask IoU / Dice: {connected['end_to_end']['defective_mean_full_tray_iou']:.3f} / {connected['end_to_end']['defective_mean_full_tray_dice']:.3f}
- False Hook outputs / false-tool defect alarms: {connected['tool_detection']['false_positives']} / {connected['end_to_end']['defect_alarm_accounting']['false_alarms_from_unmatched_tool_detections']}
- Report: `ml/CONNECTED_PIPELINE_CONFIRMATORY_REPORT.md`
- Figures: `ml/presentation/figures/connected_pipeline_confirmatory/`
- Full-tray overlays: `{connected['overlay_directory']}`
"""
    augmented_section = ""
    augmented_path = ML_ROOT / "data/hook_sinskey_new_tray_reviewed_v4_augmented_50_50.json"
    if augmented_path.exists():
        augmented = json.loads(augmented_path.read_text())
        augmented_section = f"""
## Prepared v4 50/50 augmentation dataset

- Status: `{augmented['status']}`
- Training images: {augmented['train_images']} ({augmented['original_augmented_ratio']} original:augmented)
- Validation/test images: {augmented['validation_images']} / {augmented['test_images']}
- Validation/test augmented: {str(augmented['validation_and_test_augmented']).lower()}
- Dataset tree SHA-256: `{augmented['tree_sha256']}`
- Review gallery: `{augmented['review_gallery']}`
- Human review: `{augmented['review_status']}`
- Fine-tuning started: false
"""
    combined_section = ""
    combined_data_path = ML_ROOT / "data/combined_hook_sinskey_provisional_v2.json"
    combined_results_path = ML_ROOT / "experiments/combined_provisional_benchmark_results.json"
    if combined_data_path.exists() and combined_results_path.exists():
        combined_data = json.loads(combined_data_path.read_text())
        combined_results = json.loads(combined_results_path.read_text())
        combined_lines = "\n".join(
            f"- {item['model']}: accuracy {item['classification']['accuracy']:.3f}, "
            f"specificity {item['classification']['specificity']:.3f}, "
            f"F1 {item['classification']['f1']:.3f}"
            for item in combined_results["models"]
        )
        combined_section = f"""
## Provisional redesigned-tray benchmark

- Status: `{combined_results['status']}`
- Dataset tree SHA-256: `{combined_data['tree_sha256']}`
- Train/validation/test images: {combined_data['counts']['train_images']} / {combined_data['counts']['valid_images']} / {combined_data['counts']['test_images']}
- Quarantined generated masks: {len(combined_data['quarantined'])}
- Test images: {combined_results['test_images']}
{combined_lines}
- Report: `ml/COMBINED_PROVISIONAL_REPORT.md`
- Deferred gate: review all redesigned-tray boxes and masks before authoritative HPC retraining.
"""
    cascade_section = ""
    cascade_path = ML_ROOT / "experiments/end_to_end_provisional_results.json"
    if cascade_path.exists():
        cascade = json.loads(cascade_path.read_text())
        cascade_lines = "\n".join(
            f"- {item['model']}: defect decision {item['defect_decision_accuracy']:.3f}, "
            f"localized end-to-end {item['localized_end_to_end_rate']:.3f}"
            for item in cascade["models"]
        )
        cascade_section = f"""
## Linked end-to-end cascade

- Status: `{cascade['status']}`
- QC-eligible linked instances: {cascade['cohort']['eligible_instances']}
- Tool identification / crop generation: {cascade['tool_identification']['rate']:.3f} / {cascade['crop_generation']['rate']:.3f}
- Quarantined before cohort: {cascade['cohort']['quarantined_before_evaluation']}
{cascade_lines}
- Figures: `ml/presentation/figures/end_to_end_provisional/`
"""
    status_lines = git("status", "--short").splitlines()
    ml_changes = [line for line in status_lines if " ml/" in line or line.endswith(" AGENTS.md")]
    non_ml_changes = [line for line in status_lines if line not in ml_changes]
    text = f"""# ML Context Snapshot

Generated: {datetime.now(UTC).astimezone().isoformat(timespec='seconds')}

## Repository

- Branch: `{git('branch', '--show-current')}`
- Commit: `{git('rev-parse', 'HEAD')}`
- ML-related working-tree entries: {len(ml_changes)}
- Preserved non-ML working-tree entries: {len(non_ml_changes)}
- Remote push performed: no

## Pilot inventory

- Tool: Hook Sinskey
- Dataset status: `{manifest['dataset']['status']}`
- Dataset files: {manifest['dataset']['file_count']}
- Dataset bytes: {manifest['dataset']['total_bytes']}
- Dataset SHA-256: `{manifest['dataset']['dataset_sha256']}`
- Source copy verified: {str(manifest['dataset']['copy_verified']).lower()}
- Legacy checkpoint SHA-256: `{manifest['legacy_checkpoint']['sha256']}`
- Checkpoint copy verified: {str(manifest['legacy_checkpoint']['copy_verified']).lower()}

## Historical YOLO reference

- Best epoch: {metrics['epoch']}
- Precision: {metrics['precision']:.4f}
- Recall: {metrics['recall']:.4f}
- mAP50: {metrics['map50']:.4f}
- mAP50-95: {metrics['map50_95']:.4f}

{annotation_section}
{full_annotation_section}
{reviewed_section}
{frozen_section}
{model_section}
{benchmark_section}
{new_tray_section}
{reviewed_tray_section}
{reviewed_masks_section}
{endpoint_section}
{authoritative_section}
{connected_section}
{augmented_section}
{combined_section}
{cascade_section}

## Current project state

{state}

## Required next-agent action

Run `conda run -n medetect-ml python ml/scripts/context_check.py`, then obey the pending human gate in `ml/PROJECT_STATE.md`.
"""
    OUTPUT.write_text(text)
    print(f"Wrote {OUTPUT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
