# Hook Sinskey New-Tray V4 Subgroup Analysis

**Generated:** 28 October 2026  
**Status:** Post-hoc descriptive analysis of frozen predictions; no model, split, or threshold changes.

## Scope

This analysis reuses the 24 expected-tool records from the frozen new-tray v4
connected benchmark. It does not rerun inference or tune any operating point.
The subgroups are taken from reviewed source metadata:

These are connected-pipeline results on dynamically generated crops. They
should not be compared as a monotonic extension of the fixed reviewed-crop
benchmark; see `ml/NEW_TRAY_V4_METRIC_AUDIT.md`.

| Subgroup | Expected tools | Defective | Healthy |
|---|---:|---:|---:|
| One-tool trays | 8 | 8 | 0 |
| Two-tool trays | 16 | 8 | 8 |
| Dry trays | 12 | 8 | 4 |
| Wet trays | 12 | 8 | 4 |

The test cohort is factorial at tray level: four one-tool dry trays, four
two-tool dry trays, four one-tool wet trays, and four two-tool wet trays.

## Important comparability limitation

One-tool and two-tool accuracy must not be interpreted as a clean controlled
comparison. Every one-tool test instance is defective, whereas two-tool trays
contain both defective and healthy instruments. Defective-tool recall is the
more comparable model metric because each tool-count subgroup contains eight
defective instruments.

Wet and dry groups have matching image-level class counts, but the cohort is
still very small and contains only the same four physical instruments used in
the project. These results are exploratory rather than evidence of general
wet-condition robustness.

## Shared upstream tray detector

| Subgroup | Tool-detection recall |
|---|---:|
| One-tool | 100.0% (8/8) |
| Two-tool | 75.0% (12/16) |
| Dry | 100.0% (12/12) |
| Wet | 66.7% (8/12) |

All four misses were healthy second instruments in wet two-tool trays. The
observed shortfall therefore cannot be attributed to wetness alone: wetness,
second-tool position, health status, and physical-instrument identity are
confounded in these four cases.

## Defect classification by tool count

These metrics use all expected tools. Strict pipeline accuracy requires
successful tray detection, correct endpoint selection, and the correct defect
decision. Every missed tool is wrong, including a missed healthy tool.
False-negative rate is `1 - defective recall`.

| Model | Group | Strict pipeline accuracy | Defective recall | False-negative rate | Localized success |
|---|---|---:|---:|---:|---:|
| YOLO detection | One-tool | 75.0% | 75.0% | 25.0% | 50.0% |
| YOLO detection | Two-tool | 68.8% | 100.0% | 0.0% | 62.5% |
| DETR detection | One-tool | 37.5% | 37.5% | 62.5% | 12.5% |
| DETR detection | Two-tool | 68.8% | 100.0% | 0.0% | 62.5% |
| DETR segmentation | One-tool | 87.5% | 87.5% | 12.5% | 87.5% |
| DETR segmentation | Two-tool | 56.2% | 100.0% | 0.0% | 56.2% |
| **Mask R-CNN** | **One-tool** | **100.0%** | **100.0%** | **0.0%** | **100.0%** |
| **Mask R-CNN** | **Two-tool** | **75.0%** | **100.0%** | **0.0%** | **75.0%** |

Mask R-CNN made the correct defect decision for every expected instrument in
both groups. Its two-tool end-to-end result is lower only because the upstream
tray detector missed four instruments.

## Defect classification by wet/dry condition

| Model | Group | Strict pipeline accuracy | Defective recall | False-negative rate | Localized success |
|---|---|---:|---:|---:|---:|
| YOLO detection | Dry | 83.3% | 87.5% | 12.5% | 83.3% |
| YOLO detection | Wet | 58.3% | 87.5% | 12.5% | 33.3% |
| DETR detection | Dry | 66.7% | 62.5% | 37.5% | 58.3% |
| DETR detection | Wet | 50.0% | 75.0% | 25.0% | 33.3% |
| DETR segmentation | Dry | 75.0% | 100.0% | 0.0% | 75.0% |
| DETR segmentation | Wet | 58.3% | 87.5% | 12.5% | 58.3% |
| **Mask R-CNN** | **Dry** | **100.0%** | **100.0%** | **0.0%** | **100.0%** |
| **Mask R-CNN** | **Wet** | **66.7%** | **100.0%** | **0.0%** | **66.7%** |

The wet pipeline results explicitly count the four missed healthy tools as
errors. They were not inspected and therefore cannot be treated as successful
healthy decisions.

## Interpretation and next test design

- Mask R-CNN remains the strongest downstream defect model in every subgroup.
- The principal subgroup failure is upstream localization of the second tool in
  wet two-tool trays.
- The current 4-tray-per-cell cohort is too small for statistical conclusions.
- A stronger external test should collect every combination of wet/dry,
  one/two tools, healthy/defective status, physical instrument, orientation,
  and tray position.
- Each condition should include independent capture sessions and should be
  frozen before predictions are viewed.
- Until that collection exists, report the present figures as exploratory
  subgroup results and do not tune thresholds from them.

## Sources

- Overall crop benchmark: `ml/experiments/new_tray_v4_defect_benchmark_results.json`
- Connected benchmark: `ml/experiments/new_tray_v4_connected_results.json`
- Per-model instance records: `ml/runs/new_tray_v4/connected_pipeline/*/instance_records.jsonl`
- Source metadata: `ml/annotation/new_tray_manifest.json`

