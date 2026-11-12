# MEDetect ML Workspace Map

Start here when looking for data, models, visual results, or the next command.

## Current authoritative inputs

| Purpose | Location | Notes |
|---|---|---|
| Full-tray photographs | `ml/data/local/hook_sinskey/new_tray_v2/raw/` | Original redesigned-tray captures; local only |
| Reviewed defect crops | `ml/data/local/hook_sinskey/combined_reviewed_v3/` | 342 train, 76 validation, 48 test |
| Defect dataset record | `ml/data/combined_hook_sinskey_reviewed_v3.json` | Tracked counts, hashes, and provenance |
| Reviewed tray boxes | `ml/annotation/local/new_tray_detection_reviewed/` | Human-reviewed local CVAT material |
| Current tray dataset | `ml/data/local/tray_detection/combined_provisional_v1/` | Still provisional; do not call authoritative |

Within a COCO defect dataset:

```text
annotations/instances_train.json   masks, boxes, labels, and image records
images/train/                      actual training crop photographs
images/valid/                      validation crops; never augmented
images/test/                       frozen test crops; never used for tuning
yolo/                              equivalent box-only export for YOLO
```

## Prepared next dataset

`ml/data/local/hook_sinskey/new_tray_reviewed_v4_augmented_50_50/` contains only
human-reviewed crops originating from the redesigned tray:

- 161 reviewed original training crops;
- 161 deterministic augmented training crops;
- the unchanged 41-image redesigned-tray validation subset;
- the unchanged 24-image redesigned-tray test subset;
- `review_gallery/index.html` for visual approval.

This dataset is prepared but must not be used for training until its human gate
is approved. The tracked record is
`ml/data/hook_sinskey_new_tray_reviewed_v4_augmented_50_50.json`.

## Models and runs

| Stage | Current location |
|---|---|
| Tray-level YOLO | `ml/runs/tray_yolo/` |
| Endpoint selector | `ml/runs/endpoint_selector/v1/` |
| Reviewed-v3 defect models | `ml/runs/combined_reviewed_v3/<model>/best.pt` |
| Connected tray-to-mask run | `ml/runs/connected_pipeline_confirmatory/` |

`runs/` contains local checkpoints and detailed machine-readable outputs. It is
not the recommended place for presentation browsing.

## Human-readable results

Run `build_results_bundle.py` to create one browsable export under
`ml/exports/hook_sinskey_current/`. Its numbered folders separate dataset
previews, full-tray predictions, defect-model outputs, figures, and metrics.

## Pipeline vocabulary

```text
full tray
  -> YOLO tray detector
  -> endpoint selector and tip crop
  -> defect model comparison
       legacy YOLO (box baseline)
       DETR detection (box)
       DETR segmentation (mask)
       Mask R-CNN (mask)
```

The word “YOLO” must always be qualified as either **tray YOLO** or **defect
YOLO** because they are different models with different inputs and tasks.

