# Connected Hook Sinskey Pipeline — Confirmatory Results

## Scope

This run executes the proposed sequence rather than combining independent
stage metrics:

`full tray -> tray YOLO -> endpoint selector -> Mask R-CNN -> YOLO verifier / review rule`

The cohort contains 16 redesigned-tray photographs with 24 human-reviewed Hook
Sinskey instances: 16 defective and 8 healthy. These captures appeared in the
earlier provisional cascade, so this is a **confirmatory benchmark**, not an
untouched external test. No thresholds or checkpoints were changed from these
test results.

## Frozen policy

- Tray YOLO confidence threshold: `0.10`.
- A tray prediction matches a reviewed tool at IoU >= `0.50`.
- Endpoint review margin: `0.0331498086`, selected previously from validation.
- Mask R-CNN score threshold: `0.6978445053`, selected previously from validation.
- Defect localization succeeds at full-tray mask IoU >= `0.50`.
- Route tool misses, low endpoint margins, and Mask R-CNN/YOLO decision
  disagreements to human review.

## Presentation headline

| Measure | Result |
|---|---:|
| Tool-detection recall | 91.7% (22/24) |
| Tool-detection precision | 75.9% (22/29) |
| Endpoint accuracy on detected tools | 100.0% (22/22) |
| Mask R-CNN accuracy on detected tools | 95.5% (21/22) |
| End-to-end decision success | **87.5% (21/24)** |
| Localized end-to-end success | **87.5% (21/24)** |
| Defective tools localized at IoU >= 0.50 | 100.0% (16/16) |
| Mean full-tray mask IoU / Dice, defective tools | 72.3% / 83.7% |
| Median / p95 CPU latency per tray | 3.66 s / 5.37 s |

The previous provisional linked Mask R-CNN cascade reported 50.0% localized
success on 22 unreviewed eligible instances. The new 87.5% result uses reviewed
ground truth and the current fully trained Mask R-CNN, so it should be described
as an updated confirmatory result rather than a controlled percentage-point
improvement on an identical experiment.

## Expected-instance defect decisions

Across all 24 reviewed instruments, a missed tool produces no defect alarm:

| Metric | Result |
|---|---:|
| Accuracy | 95.8% |
| Precision | 94.1% |
| Sensitivity | 100.0% |
| Specificity | 87.5% |
| F1 | 97.0% |
| Confusion matrix | TN 7, FP 1, FN 0, TP 16 |

This classification table must be shown beside tool-detection coverage. Both
missed tools happened to be healthy and therefore appear as negative defect
outputs, but they remain inspection failures in the 87.5% end-to-end measure.

## False-tool alarm accounting

Tray YOLO emitted 29 Hook predictions: 22 matched reviewed tools and 7 were
unmatched. Mask R-CNN raised defect alarms on five of those unmatched outputs.
Including these outputs:

- Correct defect alarms: 16.
- False alarms on real healthy tools: 1.
- False alarms from unmatched tool detections: 5.
- Defect-alarm precision including unmatched detections: **72.7%**.
- False defect alarms per tray: **0.375**.

This is the clearest remaining bottleneck. Crop-level Mask R-CNN performance is
strong, but false Hook detections create avoidable downstream alarms.

## Hybrid human-review policy

- 14/24 expected instances were automatically accepted and all 14 decisions
  were correct.
- 10/24 expected instances entered review: two tool misses, four low endpoint
  margins, and five model disagreements, with overlap between reasons.
- Seven false tool outputs produced five automatic outputs and two review
  events. Four of the automatic false-tool outputs raised defect alarms.
- Total review workload was 12 events across 16 trays, or 0.75 events per tray.
- No reviewed outcomes are assumed; the report does not claim 100% assisted
  accuracy.

## Interpretation

The connected experiment supports Mask R-CNN as the leading segmentation model
for the redesigned tray. Every defective tool was detected and localized above
the predefined IoU requirement. Overall system success is lower because the
tray detector missed two healthy instruments and generated seven false Hook
detections. The next optimization target should therefore be the tray detector,
especially precision and count consistency, before further defect-model tuning.

## Outputs

- Exact metrics: `ml/experiments/connected_pipeline_confirmatory_results.json`
- Presentation figures: `ml/presentation/figures/connected_pipeline_confirmatory/`
- Full-tray overlays: `ml/runs/connected_pipeline_confirmatory/overlays/`
- Per-instance records: `ml/runs/connected_pipeline_confirmatory/instance_records.jsonl`
- False-tool records: `ml/runs/connected_pipeline_confirmatory/extra_prediction_records.jsonl`
