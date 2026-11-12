# Hook Sinskey New-Tray V4 Confirmatory Benchmark

## Scope

This benchmark uses only reviewed images captured with the redesigned tray for
fine-tuning and evaluation. The materialized training split contains 161
original and 161 augmented tip crops. Validation contains 41 unaugmented crops;
the confirmatory test cohort contains 24 unaugmented crops from 16 tray photos
(16 defective tools and 8 healthy tools).

These captures were viewed in earlier project work, so this is a confirmatory
benchmark rather than an untouched external test. All model and tray thresholds
were selected using validation data only. No threshold was changed after test
results were observed.

## 1. Offline reference on fixed reviewed tip crops

This is a separate standardized model benchmark. These fixed crop pixels are
not the generated crops used by the connected pipeline, so this table must not
be treated as the downstream stage of Section 2.

| Model | Accuracy | Precision | Sensitivity | Specificity | F1 | AP50 | mAP50-95 | IoU | Dice |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| YOLO detection | 83.3% | 92.9% | 81.2% | 87.5% | 86.7% | 60.3% | 35.1% | — | — |
| DETR detection | 54.2% | 66.7% | 62.5% | 37.5% | 64.5% | 14.7% | 4.6% | — | — |
| DETR segmentation | 79.2% | 78.9% | 93.8% | 50.0% | 85.7% | 60.1% | 34.0% | 72.1% | 81.4% |
| Mask R-CNN segmentation | **95.8%** | **100.0%** | 93.8% | **100.0%** | **96.8%** | **93.1%** | **51.3%** | 71.9% | 81.2% |

Mask R-CNN is the strongest crop-level model. Its 95% bootstrap confidence
interval for accuracy is 87.5%-100.0%; the wide interval reflects the small
24-image cohort. DETR segmentation produces useful masks and high sensitivity,
but its 50.0% specificity and duplicate-query output make it less suitable than
Mask R-CNN at the frozen operating point. DETR detection remains the weakest
variant.

Median per-crop latency on Apple MPS was 30.5 ms for YOLO, 61.5 ms for DETR
detection, 342.7 ms for DETR segmentation, and 197.2 ms for Mask R-CNN.

## 2. Complete connected pipeline

The connected evaluation executes the actual sequence rather than multiplying
independent stage metrics:

`redesigned tray photo -> fine-tuned tray YOLO -> endpoint selector/tip crop -> defect model`

The same tray detector, score threshold, matches, crops, and endpoint selector
are used for all downstream models.

This is not a monotonic extension of the standalone crop benchmark. The
standalone benchmark uses fixed reviewed crops, whereas this connected run
regenerates tip crops from predicted tray boxes. The changed crop pixels can
correct or introduce downstream errors. Compare models within each evaluation,
but do not interpret the numerical difference between the two tables as pure
pipeline-stage attrition.

Shared upstream results:

- Tray YOLO AP50: 99.5%; mAP50-95: 61.7%.
- Validation-selected tray score threshold: 0.90.
- Operating-point tool precision: 90.9% (20 matches from 22 predictions).
- Operating-point tool recall: 83.3% (20/24 expected tools).
- Endpoint side accuracy: 100.0% on all 20 matched tools.

Conditional downstream performance on the exact 20 generated crops delivered
by that connected run:

| Downstream model | Correct decisions | Accuracy | Defective recall | False-negative rate |
|---|---:|---:|---:|---:|
| YOLO detection | 17/20 | 85.0% | 87.5% | 12.5% |
| DETR detection | 14/20 | 70.0% | 68.8% | 31.2% |
| DETR segmentation | 16/20 | 80.0% | 93.8% | 6.2% |
| Mask R-CNN segmentation | **20/20** | **100.0%** | **100.0%** | **0.0%** |

Strict system performance on all 24 expected tools:

| Downstream model | Strict pipeline accuracy | Defective recall | False-negative rate | Localized pipeline success |
|---|---:|---:|---:|---:|
| YOLO detection | 70.8% | 87.5% | 12.5% | 58.3% |
| DETR detection | 58.3% | 68.8% | 31.2% | 45.8% |
| DETR segmentation | 66.7% | 93.8% | 6.2% | 66.7% |
| Mask R-CNN segmentation | **83.3%** | **100.0%** | **0.0%** | **83.3%** |

Strict pipeline accuracy requires successful tool detection, correct endpoint
selection, and the correct defect decision. Every missed expected tool is an
error, including a missed healthy tool, because it was never inspected.
Localized success additionally requires a defect box or mask IoU of at least
0.50 for defective tools. The machine-readable results retain a separate
defect-label-agreement field for diagnostic use; that field must not be called
pipeline accuracy because a missed healthy tool can appear label-correct.

Raw connected counts provide the clearest audit:

| Downstream model | Strict decisions correct | Defective decisions correct | Final localized successes |
|---|---:|---:|---:|
| YOLO detection | 17/24 | 14/16 | 14/24 |
| DETR detection | 14/24 | 11/16 | 11/24 |
| DETR segmentation | 16/24 | 15/16 | 16/24 |
| Mask R-CNN segmentation | **20/24** | **16/16** | **20/24** |

Mask R-CNN missed `IMG_1541` on its fixed reviewed crop but detected it on the
newly generated connected crop. This explains why its connected defective
recall is 16/16 even though standalone defective recall is 15/16. See
`ml/NEW_TRAY_V4_METRIC_AUDIT.md` for the full reconciliation.

Mask R-CNN is the leading complete pipeline. Its mean full-tray defect-mask IoU
is 76.3% and Dice is 86.3%. Its 83.3% ceiling is caused by four tray-detector
misses, not downstream mask failures. Tray-YOLO ranking quality is high, but the
validation-selected 0.90 threshold is conservative; this threshold must not be
changed using the current test results. A future threshold-policy comparison
should be specified first and evaluated on new, untouched tray captures.

## Metric handling and limitations

- CVAT exported the reviewed brush masks with `iscrowd=1`. COCOeval excludes
  crowd annotations and initially returned `-1` AP. The evaluator explicitly
  normalizes those reviewed single-defect instances to non-crowd in memory for
  AP calculation; frozen labels and training data are unchanged.
- DETR segmentation emitted 174 retained instance/union mask PNGs for 24 test
  crops, indicating persistent duplicate-query behavior. The union masks can
  still localize defects, but the duplicate instances are an operational
  failure mode.
- The 24-crop/16-tray cohort is too small for deployment claims and is not an
  untouched test set.
- The next authoritative evaluation should use a newly collected external tray
  cohort after tray-threshold and human-review policies are frozen in advance.

## Outputs

- Presentation bundle: `ml/exports/hook_sinskey_current/NEW_TRAY_V4_RESULTS/`
- Crop-level results: `ml/experiments/new_tray_v4_defect_benchmark_results.json`
- Connected results: `ml/experiments/new_tray_v4_connected_results.json`
- Stage-consistent derived metrics: `ml/experiments/new_tray_v4_stage_consistent_metrics.json`
- Frozen thresholds: `ml/experiments/new_tray_v4_thresholds.json`
- Standalone crop/full-tray masks and overlays are under the presentation
  bundle's `03_VISUAL_OUTPUTS` directory.
