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
