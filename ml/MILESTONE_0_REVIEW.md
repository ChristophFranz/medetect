# Milestone 0 Review — Safe Migration and Environment

Status: approved by Christoph on 2026-09-23.

## Authoritative candidate

- Desktop source: `/Users/christophcuan/Desktop/medetect-api/Hook Sinskey Tip/Tool 2.v4-epoch-200-set.yolov8 3`
- Local copy: `ml/data/local/hook_sinskey/yolov8_v4`
- Roboflow project/version: `tool-2-ntfbg`, version 4, YOLOv8 detection export
- Dataset inventory: 483 files, 33,675,498 bytes
- Dataset SHA-256: `aab031079814138d9f4137b007c3eeebcac3291e94ab7fbcfddfa5e2e2370ad2`
- Source/copy result: exact inventory, size, and per-file hash match

The candidate matches the inherited training artifacts: both declare classes `defective_HS` and `non defective_HS`; the checkpoint records `data.yaml` and image size 640; `args.yaml` records 200 epochs; and the results history corresponds to that run. The copied checkpoint loads as a YOLOv8 detection model with the same two class names.

## Split inventory

| Split | Images | Defective images | Healthy images | Defect boxes | Healthy-class boxes |
|---|---:|---:|---:|---:|---:|
| Train | 181 | 135 | 46 | 151 | 46 |
| Validation | 35 | 26 | 9 | 27 | 9 |
| Test | 24 | 18 | 6 | 21 | 6 |
| Total | 240 | 179 | 61 | 199 | 61 |

The inherited export has no empty label files. Healthy images are currently represented by class-1 tool boxes. Milestone 2 must convert reviewed healthy images to COCO negatives with empty annotation lists; it must not carry those class-1 boxes into the canonical one-class `defect` dataset.

## Legacy checkpoint and baseline

- Desktop source: `/Users/christophcuan/Desktop/medetect-api/Hook Sinskey Tip/runs/detect/train/weights/best.pt`
- Local copy: `ml/artifacts/legacy/hook_sinskey/yolov8n_best.pt`
- Size: 6,255,786 bytes
- SHA-256: `016d6b46669ca9d2888d9411e80107df7748192c6df3076c217a1f1230db963b`
- Source/copy result: exact hash match
- Inherited confidence threshold: 0.1 (`ml/legacy/Detector.py`, Hook Sinskey inference call)

Historical best validation reference, at epoch 181:

| Precision | Recall | mAP50 | mAP50–95 |
|---:|---:|---:|---:|
| 0.7625 | 0.8518 | 0.8982 | 0.5712 |

These are historical validation figures, not the future benchmark result.

## Conda environment

- Environment: `medetect-ml`
- Policy: Conda only; no pip subsection or pip/uv installation command
- Python 3.12.14
- PyTorch 2.9.1
- Torchvision 0.24.1
- Transformers 5.16.1
- Ultralytics 8.4.156
- OpenCV 4.13.0
- Exact platform export: `ml/conda-explicit.txt`
- JPEG decode smoke test: passed on a migrated image
- Host hardware probe: MPS built, available, one device
- Inherited YOLO MPS smoke test: passed on one training image at threshold 0.1
- Runtime caveat: Torchvision NMS uses CPU through `PYTORCH_ENABLE_MPS_FALLBACK=1`; the remaining prediction path reported `mps:0`
- Sandbox behavior: full CPU fallback works when Metal is hidden

## Safety confirmation

- Branch: `ml/hook-sinskey-benchmark-pilot`
- The 119 pre-existing staged application files remain staged and were not edited by this work.
- ML additions are staged only by explicit path.
- Raw images and weights are ignored by Git; only provenance, code, metadata, and summarized results are trackable.
- Desktop originals were not moved, renamed, overwritten, or deleted.
- No UI, Supabase, tray-detector, remote-push, annotation, or training action was performed.

## Human gate

Christoph approved the candidate dataset, split inventory, copied checkpoint, inherited threshold, and Conda environment on 2026-09-23. Milestone 1 handoff verification is the recorded next action.
