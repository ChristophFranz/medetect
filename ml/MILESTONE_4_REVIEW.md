# Milestone 4 Review — Model Adapters and Smoke Tests

Status: approved by Christoph on 2026-09-24.

## Mechanical checks

- Models: inherited YOLO, DETR detection, DETR segmentation, and Mask R-CNN.
- Device: Apple MPS with documented CPU fallback for Torchvision NMS.
- Shared input: preserve aspect ratio, resize to a 640-pixel maximum edge, and pad bottom/right to 640 × 640.
- Seed: 42.
- Frozen test split accessed: no.
- Inference and checkpoint reload: passed for all four models.
- Backward propagation and five-epoch two-image subset run: passed for all three trainable models.
- Summary: `ml/experiments/smoke_results.json`.

## Important interpretation limit

The three new checkpoints were trained for only five epochs on one defective and one healthy training image. The review images validate loading, coordinate restoration, rendering, and the unified prediction schema. They are not evidence of model quality. Obvious prediction errors are expected and do not by themselves fail this gate.

## Human review instructions

1. Open `ml/runs/prediction_review/index.html` in a browser.
2. Inspect all 40 overlays: five defective and five healthy validation images for each model.
3. Confirm that images are correctly oriented and that boxes/masks line up spatially with the displayed image.
4. Confirm the status banner, confidence, box count, and mask count are readable and plausible representations of what is drawn.
5. For segmentation models, green masks are reviewed ground truth and pink masks are model predictions; no boxes are displayed. For detection models, green boxes are ground truth and red boxes are predictions; no masks are displayed.
6. Report any shifted, clipped, mirrored, or incorrectly scaled overlays. Prediction accuracy itself is not the acceptance criterion for these two-image smoke checkpoints.

## Human gate

- Reviewer: Christoph
- Date: 2026-09-24
- Decision: approved after reviewing all four ten-image galleries with the clarified model-specific legends
- Required approval wording: `Christoph Approve Milestone 4 prediction review and proceed to the controlled benchmark.`
- Next action: implement the controlled training/evaluation pipeline, train each new model once with seed 42, select thresholds on validation only, then evaluate once on the frozen test split.
