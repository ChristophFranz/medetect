# MEDetect ML Benchmark

This workspace compares the inherited Hook Sinskey YOLO defect detector with DETR detection, DETR segmentation, and Mask R-CNN segmentation. The application UI and tray detector are out of scope.

## Current boundary

Milestone 5 controlled benchmarking is complete and awaiting human review. Each model was evaluated once on the frozen test split after validation-only threshold selection. See `BENCHMARK_REPORT.md` and the local error gallery under `ml/runs/benchmark/error_gallery/index.html`.

## Environment

All Python packages are managed by Conda. Pip, pipx, and uv are not permitted.

```sh
conda env create -f ml/environment.yml
conda run -n medetect-ml python ml/scripts/context_snapshot.py
conda run -n medetect-ml python ml/scripts/context_check.py
```

The exact `osx-arm64` environment export is recorded in `conda-explicit.txt` after successful creation. Recreate that exact solve with `conda create -n medetect-ml --file ml/conda-explicit.txt` on a compatible Mac.

PyTorch uses MPS when it is available and otherwise falls back to CPU. The agent filesystem sandbox may hide Metal; the host-side probe is authoritative. The inherited YOLO path requires `PYTORCH_ENABLE_MPS_FALLBACK=1` because Torchvision NMS has no native MPS kernel in the pinned environment.

## Predictions and presentation material

See `PRESENTATION_GUIDE.md` for the exact commands to run the trained models on new
images, a map of checkpoint and implementation locations, and reproducible benchmark
figures. The ad-hoc prediction command is separate from the one-time frozen-test
evaluator.

## Local-only assets

- `ml/data/local/hook_sinskey/yolov8_v4/`: copied Roboflow YOLOv8 export.
- `ml/artifacts/legacy/hook_sinskey/yolov8n_best.pt`: copied inherited checkpoint.
- `ml/data/local/hook_sinskey/coco_segmentation_v1/`: frozen reviewed COCO dataset.
- `ml/runs/smoke/`: smoke checkpoints and full local run records.
- `ml/runs/prediction_review/`: local Milestone 4 HTML review package.

These assets are intentionally ignored by Git. Their provenance, sizes, and SHA-256 hashes are tracked in `data/manifest.json`.

## Human gates

Each gate must be recorded in `PROJECT_STATE.md`. Generated annotations and benchmark results are not authoritative until their corresponding gate is approved.
