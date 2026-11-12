# Hook Sinskey Model Presentation Guide

## What was compared

The inherited YOLO defect detector was compared with DETR detection, DETR instance
segmentation, and Mask R-CNN instance segmentation. All four models used the same
frozen 24-image test split and validation-selected operating thresholds. The test
split contains 18 defective and 6 healthy images.

The strongest segmentation result was Mask R-CNN. It matched legacy YOLO on
image-level accuracy (0.875), sensitivity (1.000), specificity (0.500), and F1
(0.923), while adding a defect-tip mask. Its mask AP50 was 0.730, mAP50–95 was
0.362, mean IoU was 0.616, and Dice was 0.752.

Do not present the historical YOLO validation mAP50 of 0.8982 as directly comparable
to the new frozen-test AP values. The standardized frozen-test YOLO baseline is AP50
0.605 and mAP50–95 0.258.

## Run predictions on new images

From the repository root, run the recommended Mask R-CNN model:

```sh
conda run -n medetect-ml python -m ml.scripts.predict_images \
  /absolute/path/to/image-or-folder \
  --model mask_rcnn \
  --output ml/runs/demo-predictions
```

Run all four models on the same images:

```sh
PYTORCH_ENABLE_MPS_FALLBACK=1 conda run -n medetect-ml \
  python -m ml.scripts.predict_images \
  /absolute/path/to/image-or-folder \
  --model legacy_yolo \
  --model detr_detection \
  --model detr_segmentation \
  --model mask_rcnn \
  --output ml/runs/demo-predictions
```

Each model gets a subdirectory containing annotated JPEGs under `overlays/` and a
`predictions.jsonl` file. Segmentation predictions are shown as pink masks; detection
predictions are shown as red boxes. Segmentation runs also write lossless binary masks under `masks/`: one
`instance_NNN.png` per predicted instance and a combined `union.png` per image.
The command automatically uses the frozen validation-selected thresholds.
These ad-hoc predictions do not read or modify the benchmark test split.

## Where the models are

| Purpose | Location |
|---|---|
| Legacy YOLO checkpoint | `ml/artifacts/legacy/hook_sinskey/yolov8n_best.pt` |
| Trained DETR detection checkpoint | `ml/runs/benchmark/detr_detection/best.pt` |
| Trained DETR segmentation checkpoint | `ml/runs/benchmark/detr_segmentation/best.pt` |
| Trained Mask R-CNN checkpoint | `ml/runs/benchmark/mask_rcnn/best.pt` |
| Frozen operating thresholds/checkpoint map | `ml/experiments/frozen_thresholds.json` |
| Model construction and pretrained IDs | `ml/configs/models.yaml` |
| Adapter selection | `ml/models/factory.py` |
| DETR implementation | `ml/models/detr.py` |
| Mask R-CNN implementation | `ml/models/mask_rcnn.py` |
| Legacy YOLO wrapper | `ml/models/yolo.py` |

Weights and generated runs are intentionally ignored by Git. Code, configurations,
hashes, and summarized metrics are tracked. `best.pt` is the checkpoint selected by
validation loss; `last.pt` is the final training epoch and should not be used for the
reported benchmark.

## Recreate the presentation graphs

```sh
conda run -n medetect-ml python -m ml.scripts.plot_benchmark_results
```

The command reads the recorded JSON results and training summaries; it does not rerun
inference. It writes both PNG and editable SVG versions under
`ml/presentation/figures/`:

- `classification-comparison`: accuracy, precision, sensitivity, specificity, F1.
- `localization-comparison`: AP50, AP75, and mAP50–95, with box and mask AP labelled.
- `confusion-matrices`: exact healthy/defective outcomes for each model.
- `operational-comparison`: median/p95 latency and checkpoint size.
- `training-curves`: train/validation loss and selected best epoch.

## Essential caveats for the presentation

- The dataset is small, so uncertainty is wide; the report contains bootstrap 95% CIs.
- Healthy images all came from acquisition group `6-3`, while defective images all
  came from `6-4`. The model may partly learn session/background cues.
- DETR segmentation was heads-only because full fine-tuning was impractical on the
  available 24 GB Apple machine. This limits the architecture comparison.
- DETR detection and DETR segmentation had zero specificity at their frozen operating
  points: every healthy test image was called defective.
- The existing test set has now been evaluated and viewed. Any tuned follow-up should
  use a newly collected, untouched, deconfounded test set.
