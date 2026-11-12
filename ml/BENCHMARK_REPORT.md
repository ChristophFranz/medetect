# Hook Sinskey Controlled Benchmark

Status: awaiting Milestone 5 human review.

All operating thresholds were selected on validation data and frozen before each model was evaluated once on the 24-image test split.

| Model | Accuracy | Sensitivity | Specificity | F1 | AP50 | mAP50–95 | Median ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| legacy_yolo | 0.875 | 1.000 | 0.500 | 0.923 | 0.605 | 0.258 | 17.7 |
| detr_detection | 0.708 | 0.944 | 0.000 | 0.829 | 0.140 | 0.045 | 43.3 |
| detr_segmentation | 0.750 | 1.000 | 0.000 | 0.857 | 0.308 | 0.128 | 430.4 |
| mask_rcnn | 0.875 | 1.000 | 0.500 | 0.923 | 0.730 | 0.362 | 185.9 |

## Main finding

Mask R-CNN matched the inherited YOLO baseline on image-level accuracy (0.875), sensitivity (1.000), specificity (0.500), and F1 (0.923), while providing the requested tip-defect segmentation. Its test segmentation AP50 was 0.730, mAP50–95 was 0.362, mean IoU was 0.616, and Dice was 0.752.

DETR detection and heads-only DETR segmentation classified every healthy test image as defective at their validation-selected operating points. Their specificities were therefore 0.000. DETR segmentation's full-parameter fine-tune was infeasible on the available 24 GB Apple system, so only its classifier, box predictor, mask head, and box-attention layers were trained; this materially limits a direct architecture comparison.

## Baseline interpretation

The inherited historical YOLO validation references were mAP50 0.8982, mAP50–95 0.5712, precision 0.7625, and recall 0.8518. They are not directly comparable to the authoritative frozen-test results. Standardized test YOLO achieved AP50 0.6051 and mAP50–95 0.2583.

## Important limitation

Defect label remains perfectly confounded with acquisition group: `6-4` images are defective and `6-3` images are healthy. Results describe this internal dataset and cannot establish cross-session, cross-device, or deployment generalization.

A post-benchmark risk audit also found that 23 of 24 test images were captured within
30 seconds of a same-group training image. See `ml/TEST_METRIC_AUDIT.md`. This does
not change the frozen measurements, but it further limits their external validity.

## Review material

- Full metrics and bootstrap intervals: `ml/experiments/benchmark_results.json`
- Local error gallery: `ml/runs/benchmark/error_gallery/index.html`
- Green is reviewed ground truth; red/pink is the model prediction.

## Human gate

- Reviewer: pending
- Decision: pending
- Next action: review the report and all failure overlays, then approve expansion, request relabeling/tuning, or stop.
