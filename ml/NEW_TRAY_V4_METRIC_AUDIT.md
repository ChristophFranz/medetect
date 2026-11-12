# New-Tray V4 Metric Audit

**Audited:** 29 October 2026  
**Source:** Frozen crop predictions and frozen connected-pipeline instance records  
**Changes to models, thresholds, or predictions:** None

## Finding

The reported counts are reproducible from the raw records, but the previous
presentation made two different evaluations look like a monotonic cascade:

1. The standalone defect benchmark uses fixed, reviewed tip crops.
2. The connected benchmark creates new tip crops from tray-YOLO predictions.

Because the pixel inputs differ, the connected defect model can correct or
introduce errors relative to the fixed-crop benchmark. Its model-level recall
is therefore not mathematically required to be less than the standalone recall.
The strict connected success rate is still capped by upstream coverage: only 20
of 24 expected tools were detected and inspected.

## Raw standalone crop counts

| Model | Correct / 24 | Defective found / 16 | Healthy correct / 8 |
|---|---:|---:|---:|
| YOLO detection | 20 | 13 | 7 |
| DETR detection | 13 | 10 | 3 |
| DETR segmentation | 19 | 15 | 4 |
| Mask R-CNN | 23 | 15 | 8 |

## Raw connected-pipeline counts

Every missed expected tool is counted as incorrect. “Decision correct” requires
tool detection, correct endpoint selection, and the correct defect decision.
“Localized correct” additionally requires valid localization for a defective
tool.

| Model | Decision correct / 24 | Defective decision recall | Localized correct / 24 | Defective localized / 16 |
|---|---:|---:|---:|---:|
| YOLO detection | 17 | 14/16 | 14 | 11/16 |
| DETR detection | 14 | 11/16 | 11 | 8/16 |
| DETR segmentation | 16 | 15/16 | 16 | 15/16 |
| Mask R-CNN | 20 | 16/16 | 20 | 16/16 |

The common upstream tray detector found 20/24 expected tools. All four misses
were healthy second tools in wet two-tool trays; all 16 defective tools were
found by the tray detector.

## Why some connected model values increased

The newly generated connected crops were not pixel-identical to the fixed
reviewed crops. For example, Mask R-CNN missed defective `IMG_1541` on the fixed
crop but detected and localized it from the connected pipeline's generated
crop. Its defective count therefore changed from 15/16 to 16/16. The four
upstream misses still reduce strict overall success to 20/24.

DETR detection similarly corrected enough decisions on the generated crops for
its strict connected count to be 14/24 versus 13/24 on fixed crops. This is not
a one-stage arithmetic improvement; it is performance on a different image
representation.

## Correct reporting policy

- Report standalone crop performance as downstream-model performance under
  standardized reviewed crops.
- Report strict connected decision success as system classification
  performance; every missed tool is wrong.
- Report localized connected success as the final tray-to-defect-output metric.
- Do not describe the difference between standalone and connected figures as
  stage attrition or improvement because the crops differ.
- If a monotonic stage-ablation table is needed, run a separate controlled
  analysis using identical crop pixels at every comparison point.

The stage-consistent connected table is generated programmatically by
`ml/scripts/audit_new_tray_v4_stage_metrics.py` and stored in
`ml/experiments/new_tray_v4_stage_consistent_metrics.json`.

## Authoritative sources

- Crop records: `ml/runs/new_tray_v4/*/test_predictions.jsonl`
- Connected records: `ml/runs/new_tray_v4/connected_pipeline/*/instance_records.jsonl`
- Crop summary: `ml/experiments/new_tray_v4_defect_benchmark_results.json`
- Connected summary: `ml/experiments/new_tray_v4_connected_results.json`
- Stage-consistent summary: `ml/experiments/new_tray_v4_stage_consistent_metrics.json`

