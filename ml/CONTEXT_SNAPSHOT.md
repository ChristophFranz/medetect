# ML Context Snapshot

Generated: 2026-11-13T19:28:21+08:00

## Repository

- Branch: `ml/hook-sinskey-benchmark-pilot`
- Commit: `94dd30b8a4d67952aa006777f400b3ab9004cd14`
- ML-related working-tree entries: 0
- Preserved non-ML working-tree entries: 119
- Remote push performed: yes — `personal/ml/hook-sinskey-benchmark-pilot` on 2026-11-13

## Pilot inventory

- Tool: Hook Sinskey
- Dataset status: `frozen_milestone_3_approved`
- Dataset files: 483
- Dataset bytes: 33675498
- Dataset SHA-256: `aab031079814138d9f4137b007c3eeebcac3291e94ab7fbcfddfa5e2e2370ad2`
- Source copy verified: true
- Legacy checkpoint SHA-256: `016d6b46669ca9d2888d9411e80107df7748192c6df3076c217a1f1230db963b`
- Checkpoint copy verified: true

## Historical YOLO reference

- Best epoch: 181
- Precision: 0.7625
- Recall: 0.8518
- mAP50: 0.8982
- mAP50-95: 0.5712


## Annotation pilot

- Sample images: 20 (14 defective, 6 healthy)
- Candidate masks: 15
- Test images used: 0
- SAM2 checkpoint: `facebook/sam2.1-hiera-tiny@de431c4043854a71d8101e17995dfe596bf101a5`
- Device: `mps`
- Review status: `approved`
- Docker command available: true
- Data warning: class is perfectly confounded with acquisition groups `6-4` (defective) and `6-3` (healthy).


## Full-dataset annotation

- Images: 240 (179 defective, 61 healthy)
- Candidate masks: 199
- Candidate COCO SHA-256: `4500fd7cc8d07324bf50cf4381ddc40eb3df7f6424bc0089421630b3e7666b37`
- Candidate CVAT ZIP SHA-256: `550731b169205b58f59b74274fd9f39508c8fe27beede4ad236c0f73f477115f`
- Cross-split source/hash leakage: false
- Review status: `pending`
- Local CVAT URL: `http://localhost:8080`


## Reviewed ground truth

- Reviewer/date: Christoph / 2026-09-24
- Images/masks: 240 / 199
- Healthy images with masks: 0
- Reviewed ZIP SHA-256: `da7381a24fdf71e60f61c73177b10ca8b49da6e9bd87927dd53ae13c79ab2269`
- Reviewed COCO SHA-256: `a25df42862b39b3f159a2f73e788cab6bb5135bad86aa642b877ee542195b290`
- Status: `approved_and_frozen`


## Frozen benchmark dataset

- Version: `hook_sinskey_segmentation_v1`
- Canonical tree SHA-256: `771a2e13e818ac6c6d70a06c9b9973b5fd701a415373f0dc265b20e37c1eb74e`
- Train/validation/test images: 181 / 35 / 24
- Test split frozen: true


## Milestone 4 model checks

- Adapter smoke status: `passed_awaiting_prediction_review`
- Models passed: 4
- Device: `mps`
- Frozen test split accessed: false
- Prediction review: `approved`
- Review scope: 5 defective + 5 healthy validation images per model
- Local review index: `ml/runs/prediction_review/index.html`


## Milestone 5 controlled benchmark

- Status: `awaiting_human_review`
- Frozen test images: 24
- Evaluations per model: 1
- Error overlays: 19
- legacy_yolo: accuracy 0.875, sensitivity 1.000, specificity 0.500, F1 0.923
- detr_detection: accuracy 0.708, sensitivity 0.944, specificity 0.000, F1 0.829
- detr_segmentation: accuracy 0.750, sensitivity 1.000, specificity 0.000, F1 0.857
- mask_rcnn: accuracy 0.875, sensitivity 1.000, specificity 0.500, F1 0.923
- Report: `ml/BENCHMARK_REPORT.md`
- Local error gallery: `ml/runs/benchmark/error_gallery/index.html`


## Redesigned-tray detector expansion

- Source dataset SHA-256: `02e7ddb403bdec8f7e9258c8957432e171af3bb3c2f869264f420aa677603b76`
- Images / Hook Sinskey instances: 151 / 223
- Train/validation/test images: 109 / 26 / 16
- Candidate method: low-saturation horizontal-line localization with deterministic fallback
- Review status: `pending`
- Candidate ZIP SHA-256: `f29d23be9c0f0913bbb5d4a27648bcaa8e158c6249f4ff0055992050eaf9e577`
- Local CVAT URL: `http://localhost:8080`
- Human gate: `ml/annotation/NEW_TRAY_DETECTION_REVIEW.md`


## Human-reviewed redesigned-tray boxes

- Reviewer/date: Christoph / 2026-10-20
- Validation status: `validated`
- Images / reviewed boxes: 151 / 226
- Reviewed ZIP SHA-256: `13d9841f2184a80a5535cac8bed4cc15301174a02de673e47c82fb1e0e09c63d`
- Regenerated crops / SAM2 masks: 226 / 154
- Healthy negative crops: 72
- Mask-review procedure: `ml/annotation/NEW_TRAY_DEFECT_MASK_REVIEW.md`


## Frozen redesigned-tray masks and combined dataset

- Reviewer/date: Christoph / 2026-10-21
- Redesigned-tray images / masks: 226 / 154
- Defective / healthy: 154 / 72
- Candidate masks changed by reviewer: 21
- Combined dataset status: `human_reviewed_frozen`
- Combined train/validation/test images: 342 / 76 / 48
- Combined instances: 353
- Combined tree SHA-256: `f3d2e02f34c3f910dcdb12c902bb1bed8fd4ff78043a6fb846353c089bb17e8c`
- Next action: review the completed authoritative benchmark, figures, and error gallery.


## Endpoint selector

- Dataset samples / source instruments: 452 / 226
- Dataset SHA-256: `ea91d8ff682c34d875e63bed0c1aeb0fd042cbe33d9a7addc7911e7807cb2f27`
- Validation/test pair accuracy: 1.000 / 1.000
- Validation-derived review margin: 0.033150
- Test automatic accepts / review queue: 20 / 4
- Human gate: `ml/ENDPOINT_SELECTOR_REVIEW.md`
- Gallery: `ml/runs/endpoint_selector/v1/gallery/index.html`


## Authoritative combined reviewed-v3 benchmark

- Status: `human_approved`
- Dataset SHA-256: `f3d2e02f34c3f910dcdb12c902bb1bed8fd4ff78043a6fb846353c089bb17e8c`
- Frozen test images / evaluations per model: 48 / 1
- Threshold selection split: `valid`
- legacy_yolo: accuracy 0.854, specificity 0.571, F1 0.904
- detr_detection: accuracy 0.708, specificity 0.143, F1 0.821
- detr_segmentation: accuracy 0.708, specificity 0.071, F1 0.825
- mask_rcnn: accuracy 0.792, specificity 0.429, F1 0.865
- Physical training images: 342; transforms were generated on-the-fly.
- Maximum training exposure: 7,866 image presentations (23 epochs x 342), not 7,866 independent images.
- Report: `ml/COMBINED_REVIEWED_V3_REPORT.md`
- Figures: `ml/presentation/figures/combined_reviewed_v3/`
- Local error gallery: `ml/runs/combined_reviewed_v3/error_gallery/index.html`


## Connected tray-to-mask confirmatory benchmark

- Status: `confirmatory_awaiting_human_review`
- Cohort: 16 trays / 24 expected Hook Sinskey instances
- Tool precision / recall: 0.759 / 0.917
- Endpoint accuracy: 1.000
- End-to-end decision / localized success: 0.875 / 0.875
- Full-tray mask IoU / Dice: 0.723 / 0.837
- False Hook outputs / false-tool defect alarms: 7 / 5
- Report: `ml/CONNECTED_PIPELINE_CONFIRMATORY_REPORT.md`
- Figures: `ml/presentation/figures/connected_pipeline_confirmatory/`
- Full-tray overlays: `ml/runs/connected_pipeline_confirmatory/overlays`


## Prepared v4 50/50 augmentation dataset

- Status: `human_approved_frozen_for_fine_tuning`
- Training images: 322 (161:161 original:augmented)
- Validation/test images: 41 / 24
- Validation/test augmented: false
- Dataset tree SHA-256: `f334b1e6d3ce3786456b92f56d5dd3654402712194fa43569b8e31a56724bffc`
- Review gallery: `ml/data/local/hook_sinskey/new_tray_reviewed_v4_augmented_50_50/review_gallery/index.html`
- Human review: `approved`
- Fine-tuning started: false


## Provisional redesigned-tray benchmark

- Status: `provisional_unreviewed_new_tray_masks_one_epoch_adaptation`
- Dataset tree SHA-256: `dde541ea8ff82126b1034f266d3281f04e54318115e402fe15b617faeea8a6b2`
- Train/validation/test images: 332 / 72 / 46
- Quarantined generated masks: 13
- Test images: 46
- legacy_yolo: accuracy 0.848, specificity 0.571, F1 0.899
- detr_detection: accuracy 0.696, specificity 0.000, F1 0.821
- mask_rcnn: accuracy 0.717, specificity 0.071, F1 0.831
- Report: `ml/COMBINED_PROVISIONAL_REPORT.md`
- Deferred gate: review all redesigned-tray boxes and masks before authoritative HPC retraining.


## Linked end-to-end cascade

- Status: `provisional_unreviewed_linked_new_tray_test`
- QC-eligible linked instances: 22
- Tool identification / crop generation: 1.000 / 1.000
- Quarantined before cohort: 2
- legacy_yolo: defect decision 0.818, localized end-to-end 0.273
- detr_detection: defect decision 0.636, localized end-to-end 0.000
- mask_rcnn: defect decision 0.636, localized end-to-end 0.500
- Figures: `ml/presentation/figures/end_to_end_provisional/`


## Current project state

# Project State

- Current milestone: 5 — Controlled benchmark
- Status: new-tray-only v4 confirmatory benchmark complete; awaiting human review
- Branch: `ml/hook-sinskey-benchmark-pilot`
- Pilot tool: Hook Sinskey
- Canonical target: defect affected-tip segment; healthy images have no mask
- Last verified date: 2026-10-29
- Last verified action: generated stage-consistent metrics from the frozen connected records, separating the offline fixed-crop reference, conditional performance on 20 delivered generated crops, and strict performance on all 24 expected tools
- Active experiment: paired new-tray v4 crop-level and connected-pipeline comparison across defect YOLO, DETR detection, DETR segmentation, and Mask R-CNN
- Active experiment status: complete; Mask R-CNN leads at crop level and in the connected pipeline
- Augmentation gate: approved by Christoph on 2026-10-21; validation and test remain unaugmented
- Next action: human review of `ml/NEW_TRAY_V4_REPORT.md`, `ml/NEW_TRAY_V4_METRIC_AUDIT.md`, `ml/NEW_TRAY_V4_SUBGROUP_REPORT.md`, presentation figures, and model-by-model masks/overlays; then pre-register any tray-threshold or human-review policy before collecting an untouched external test cohort

## Human gate record

| Milestone | Reviewer | Date | Decision | Next action |
|---|---|---|---|---|
| 0 | Christoph | 2026-09-23 | Approved | Verify the Milestone 1 context handoff |
| 1 | Christoph | 2026-09-24 | Approved | Begin the Milestone 2 annotation-policy sample |
| 2 | Christoph | 2026-09-24 | Approved — policy and all 20 pilot labels via visual overlays | Begin full-dataset assisted annotation and human review |
| 3 | Christoph | 2026-09-24 | Approved — reviewed Hook Sinskey dataset frozen | Begin Milestone 4 model adapters and smoke tests |
| 4 | Christoph | 2026-09-24 | Approved — all four ten-image prediction galleries reviewed | Begin controlled benchmark implementation |
| 5 | Christoph | 2026-10-23 | Approved — combined reviewed-v3 metrics, figures, masks, and error-gallery benchmark accepted | Run a confirmatory connected tray-to-mask evaluation and report system-level metrics |
| Redesigned tray labels | Christoph | 2026-10-21 | Completed — boxes, masks, and healthy negatives reviewed; combined dataset frozen | Begin full-training benchmark on combined reviewed v3 |
| Endpoint selector | Christoph | 2026-10-21 | Approved — all selected test images contain valid working tips and proposed augmentation strengths preserve labels | Begin combined reviewed v3 defect-model retraining |
| Connected pipeline | Christoph | 2026-10-23 | Approved for the next modelling iteration | Retrain tray YOLO and compare all downstream defect models in the connected pipeline |
| V4 augmentation | Christoph | 2026-10-23 | Approved — redesigned-tray-only, 161 originals + 161 augmentations, horizontal flipping retained | Begin controlled fine-tuning and validation-only threshold selection |
| V4 training pause | Christoph | 2026-10-23 | Paused after DETR detection; preserve completed checkpoints and stop DETR segmentation | Await explicit resume instruction |

## New-tray v4 fine-tuning checkpoint (paused 2026-10-23)

- Tray YOLO completed, best epoch 8: validation precision 0.994, recall 1.000,
  mAP50 0.995, and mAP50-95 0.704.
- Defect YOLO completed, best epoch 18: validation precision 0.901, recall
  0.900, mAP50 0.960, and mAP50-95 0.682.
- DETR detection completed 20 epochs; best epoch 18 with validation loss
  0.7362329406. The test split was not accessed.
- DETR segmentation was stopped before its first v4 epoch completed. No v4
  DETR-segmentation resume state exists, so resume from the combined-reviewed-v3
  checkpoint using `--no-resume`.
- MPS DETR segmentation reserved about 10 GB and left under 0.4 GB free, so it
  was stopped to prevent another desktop failure. CPU training with activation
  checkpointing and four threads remained responsive (roughly 2-5.5 GB free)
  but was slow. On resume, use a bounded six-to-eight-thread CPU run as the
  initial reasonable high-throughput setting and monitor memory.
- Crop-level, connected-pipeline, and presentation-bundle scripts are prepared;
  all 42 ML tests pass. Do not evaluate the test cohort until both remaining
  model checkpoints exist and validation-only thresholds have been frozen.

## New-tray v4 confirmatory result (completed 2026-10-23)

- DETR segmentation resumed with bounded MPS and activation checkpointing,
  early-stopped after 14 epochs, and retained epoch 9 (validation loss
  0.5724069221).
- Mask R-CNN early-stopped after 11 epochs and retained epoch 6 (validation
  loss 0.1020418732).
- Thresholds were frozen from 41 validation crops before opening the 24-crop
  test cohort.
- Crop-level accuracy: YOLO 0.833, DETR detection 0.542, DETR segmentation
  0.792, and Mask R-CNN 0.958.
- Connected localized success on 24 expected tools: YOLO 0.583, DETR detection
  0.458, DETR segmentation 0.667, and Mask R-CNN 0.833.
- Shared tray YOLO: AP50 0.995, mAP50-95 0.617, operating precision 0.909,
  and operating recall 0.833 at the validation-selected threshold 0.90.
- Treat Mask R-CNN as the leading model for the redesigned-tray cohort. Do not
  claim deployment performance: the cohort is confirmatory and only 24 tools.
- Report: `ml/NEW_TRAY_V4_REPORT.md`.
- Presentation bundle: `ml/exports/hook_sinskey_current/NEW_TRAY_V4_RESULTS/`.

## Preservation notes

- Original files under `/Users/christophcuan/Desktop/medetect-api` were copied, not moved or deleted.
- Existing staged application files were preserved and excluded from ML staging.
- No UI, Supabase, or tray-detector files were intentionally modified by this pilot.
- Desktop dataset and checkpoint hashes still match the local copies.
- The 151 redesigned-tray Desktop originals were copied into ignored local storage; originals were not moved, renamed, or deleted.
- The frozen v1 Hook Sinskey benchmark remains unchanged while the redesigned-tray experiment is gated.

## Required next-agent action

Run `conda run -n medetect-ml python ml/scripts/context_check.py`, then obey the pending human gate in `ml/PROJECT_STATE.md`.
