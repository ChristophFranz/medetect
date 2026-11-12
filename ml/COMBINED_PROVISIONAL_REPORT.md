# Provisional Redesigned-Tray Benchmark

## Executive result

The urgent presentation run is complete. It adds a redesigned-tray localization stage, detector-derived Hook Sinskey crops, a combined old/new defect dataset, one adaptation epoch for DETR detection and Mask R-CNN, frozen validation-selected thresholds, one test evaluation, structured prediction outputs, and presentation figures.

This run is **provisional**. The new tray boxes and SAM2 masks were not human-reviewed, and 13 implausible SAM2 masks were quarantined. These results are suitable for an internal progress presentation, not model selection, publication, or deployment.

## Pipeline evaluated stage by stage

```text
Full tray image
  -> four-class retrained YOLO tray detector
  -> Hook Sinskey crop / distal-tip crop
  -> defect model (inherited YOLO, DETR detection, or Mask R-CNN)
  -> healthy/defective decision + box or mask output
```

The inherited YOLO defect checkpoint and threshold (`0.1`) were unchanged. DETR and Mask R-CNN started from the previously trained Hook Sinskey checkpoints and received one CPU adaptation epoch on the combined dataset. This was deliberately shortened for the presentation deadline.

The tray and defect stages were evaluated separately because the inherited full-tray dataset has tool boxes but no tray-image-level defect labels linking each Hook Sinskey instance to defect ground truth. Consequently, the numbers below are **not** a single cascaded end-to-end accuracy. The exported redesigned-tray crops and downstream defect outputs demonstrate the executable cascade; a defensible end-to-end metric requires linked instance labels.

## Tray detector

| Checkpoint | Original tray mAP50 | Original tray mAP50–95 | Redesigned tray mAP50 | Redesigned tray mAP50–95 |
|---|---:|---:|---:|---:|
| Inherited YOLO | 0.961 | 0.656 | 0.000 | 0.000 |
| Retrained YOLO | 0.947 | 0.579 | 0.659 | 0.193 |

The retrained detector recovered substantial redesigned-tray performance while largely preserving original-tray AP50. At confidence `0.1`, it matched 220 of 223 expected Hook Sinskey instances. Three missed instances used the provisional candidate box as a fallback so the presentation dataset remained complete.

Checkpoint: `ml/runs/tray_yolo/combined_provisional_presentation_20e/weights/best.pt`

## Combined defect benchmark

The combined test set contains 46 crops: 24 original-domain and 22 redesigned-tray crops; 32 are defective and 14 healthy. Thresholds were selected on the 72-image validation split only.

| Model | Accuracy | Precision | Sensitivity | Specificity | F1 | PR-AUC | ROC-AUC |
|---|---:|---:|---:|---:|---:|---:|---:|
| Inherited YOLO | **0.848** | **0.838** | 0.969 | **0.571** | **0.899** | **0.926** | **0.862** |
| DETR detection | 0.696 | 0.696 | **1.000** | 0.000 | 0.821 | 0.752 | 0.547 |
| Mask R-CNN | 0.717 | 0.711 | **1.000** | 0.071 | 0.831 | 0.908 | 0.788 |

The inherited YOLO is currently the strongest image-level defect classifier. DETR and Mask R-CNN detect every defective test image at their validation-selected thresholds, but classify almost every healthy image as defective. Their high sensitivity therefore must not be presented as overall superiority.

### Localization

| Model/task | AP50 | AP75 | mAP50–95 | IoU | Dice |
|---|---:|---:|---:|---:|---:|
| Inherited YOLO boxes | 0.320 | 0.130 | 0.141 | — | — |
| DETR boxes | 0.002 | 0.001 | 0.001 | — | — |
| Mask R-CNN masks | **0.503** | 0.121 | **0.222** | 0.558 | 0.696 |

Mask R-CNN provides the most promising preliminary segmentation result, but its operating threshold and healthy-image behavior require further training and tuning. DETR localization did not adapt successfully in one epoch.

## Linked end-to-end cascade

A separate cascade analysis links each QC-eligible redesigned-tray test instance through tool identification, crop generation, defect classification, and localization. This is the closest current comparison to the senior report's presence-detection-versus-defect-identification charts.

| Model | Tool identified | Crop generated | Correct defect decision | Localization-aware end-to-end success |
|---|---:|---:|---:|---:|
| Inherited YOLO | 22/22 (100.0%) | 22/22 (100.0%) | 18/22 (81.8%) | 6/22 (27.3%, box) |
| DETR detection | 22/22 (100.0%) | 22/22 (100.0%) | 14/22 (63.6%) | 0/22 (0.0%, box) |
| Mask R-CNN | 22/22 (100.0%) | 22/22 (100.0%) | 14/22 (63.6%) | **11/22 (50.0%, mask)** |

“Localization-aware end-to-end success” requires tray detection and an exported crop. A healthy case must produce the correct no-defect decision. A defective case must produce the correct defect decision and at least one box or mask with IoU ≥ 0.50 against the provisional reference.

This 22-instance analysis excludes two defective test instances quarantined for implausible generated reference-mask area. The 100% tool-identification result applies only to this linked new-tray test cohort and must not be generalized to the full dataset. The reference boxes and masks remain unreviewed.

## Dataset and quality boundary

| Split | Images | Defective | Healthy | Original | New tray |
|---|---:|---:|---:|---:|---:|
| Train | 332 | 236 | 96 | 181 | 151 |
| Validation | 72 | 52 | 20 | 35 | 37 |
| Test | 46 | 32 | 14 | 24 | 22 |

- Combined dataset tree SHA-256: `dde541ea8ff82126b1034f266d3281f04e54318115e402fe15b617faeea8a6b2`.
- Thirteen defective new-tray crops with masks outside the provisional area bounds `[0.001, 0.10]` were quarantined.
- Capture bursts and multi-tool photographs remain grouped within a split.
- The original reviewed and frozen Hook Sinskey dataset was not changed.

## Presentation assets

- Defect comparison charts: `ml/presentation/figures/combined_provisional/`
- Tray-detector charts: `ml/presentation/figures/tray_detector_provisional/`
- Linked end-to-end charts and example: `ml/presentation/figures/end_to_end_provisional/`
- Exact benchmark metrics: `ml/experiments/combined_provisional_benchmark_results.json`
- Exact linked cascade metrics: `ml/experiments/end_to_end_provisional_results.json`
- Combined dataset record: `ml/data/combined_hook_sinskey_provisional_v2.json`
- Tray overlays/crops: `ml/runs/tray_yolo/presentation_predictions/`
- Defect overlays and Mask R-CNN PNG masks:
  - `ml/runs/combined_provisional/legacy_yolo/test_outputs/`
  - `ml/runs/combined_provisional/detr_detection/test_outputs/`
  - `ml/runs/combined_provisional/mask_rcnn/test_outputs/`

## Recommended presentation wording

“The inherited tray detector failed on the redesigned tray, confirming domain shift. A short mixed-domain retraining recovered redesigned-tray mAP50 to 0.659 while retaining 0.947 on the original tray. On provisional combined defect data, inherited YOLO remains the strongest classifier at 84.8% accuracy. Mask R-CNN is promising for localization, reaching 0.696 Dice, but currently over-calls healthy tools. Human annotation review and full HPC training are the next required steps.”

## Required follow-up

1. Review all redesigned-tray boxes and masks in CVAT; resolve the 13 quarantined cases.
2. Rebuild and freeze an authoritative combined dataset, preserving capture-group splits.
3. Train DETR and Mask R-CNN fully on the HPC with early stopping and validation-only hyperparameter selection.
4. Tune score and minimum-mask-area thresholds for the desired safety trade-off.
5. Re-evaluate each final model once on a newly frozen test split and regenerate the report.
