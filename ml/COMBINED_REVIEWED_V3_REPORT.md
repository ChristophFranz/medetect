# Hook Sinskey Combined Reviewed-v3 Benchmark

Status: awaiting human review.

All new models were full-backbone trained with seed 42 on the frozen combined
reviewed-v3 train split. Operating thresholds were selected on the 76-image
validation split before each model was evaluated once on the frozen 48-image
test split.

## Test results

| Model | Accuracy | Precision | Sensitivity | Specificity | F1 | AP50 | mAP50–95 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Inherited YOLO | 0.854 | 0.846 | 0.971 | 0.571 | 0.904 | 0.536 box | 0.230 box |
| DETR detection | 0.708 | 0.727 | 0.941 | 0.143 | 0.821 | 0.028 box | 0.011 box |
| DETR segmentation | 0.708 | 0.717 | 0.971 | 0.071 | 0.825 | 0.100 mask | 0.036 mask |
| Mask R-CNN | 0.792 | 0.800 | 0.941 | 0.429 | 0.865 | 0.633 mask | 0.287 mask |

Mask R-CNN is the strongest segmentation model. Its mean union-mask IoU is
0.651 and Dice is 0.759. On the redesigned-tray half of the test set it reaches
0.917 accuracy and 0.941 F1, compared with 0.833 accuracy and 0.882 F1 for the
inherited YOLO baseline.

Inherited YOLO remains the strongest overall image-level classifier at the
unchanged 0.1 threshold. DETR detection and DETR segmentation remain weak at
rejecting healthy images. DETR segmentation also retains many duplicate query
masks at its validation-selected operating point, producing 1,022 test mask
instances and poor COCO AP despite moderate union-mask overlap.

## Augmentation accounting

Augmentation does not add files or change split membership. The physical
training set remains 342 images. A deterministic transformed view is generated
when each training sample is loaded during an epoch; validation and test images
are never augmented.

| Model | Epochs completed | Image presentations | Additional transformed views over one pass |
|---|---:|---:|---:|
| DETR detection | 19 | 6,498 | 6,156 |
| DETR segmentation | 23 | 7,866 | 7,524 |
| Mask R-CNN | 14 | 4,788 | 4,446 |

The longest run therefore received 23 times as many image presentations as one
static pass, but this must not be described as 7,866 independent captured
images. The underlying biological and acquisition diversity remains 342
training images.

## Frozen operating points

| Model | Score threshold | Minimum mask area |
|---|---:|---:|
| Inherited YOLO | 0.1000 | not applicable |
| DETR detection | 0.0990 | not applicable |
| DETR segmentation | 0.1533 | 1 pixel |
| Mask R-CNN | 0.6978 | 1 pixel |

## Outputs

- Metrics: `ml/experiments/combined_reviewed_v3_benchmark_results.json`
- Frozen thresholds: `ml/experiments/combined_reviewed_v3_thresholds.json`
- Presentation figures: `ml/presentation/figures/combined_reviewed_v3/`
- Error gallery: `ml/runs/combined_reviewed_v3/error_gallery/index.html`
- Model overlays and masks: `ml/runs/combined_reviewed_v3/<model>/test_outputs/`
- Final unified prediction records:
  `ml/runs/combined_reviewed_v3/<model>/test_predictions.jsonl`

## Interpretation boundary

The 48-image test set contains 34 defective and 14 healthy crops, so accuracy
can be dominated by sensitivity. Specificity and the confusion matrices must be
presented alongside accuracy. Metrics describe internal performance on the
frozen reviewed dataset and do not by themselves establish deployment
generalization to unseen instruments, sites, cameras, or acquisition sessions.

## Human gate

- Reviewer: pending
- Decision: pending
- Next action: inspect the figures, error gallery, and representative output
  masks before accepting the benchmark or authorizing further tuning.
