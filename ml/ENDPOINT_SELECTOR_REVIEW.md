# Endpoint Selector Human Gate

## Review record

- Reviewer: Christoph
- Date: 2026-10-21
- Endpoint decision: approved
- Confirmation: all selected test images contain the working tip and remain
  visually valid.
- Augmentation-strength decision: approved by Christoph on 2026-10-21.

## What was built

- Two orientation-normalized endpoint candidates per reviewed instrument.
- 226 `tip` and 226 `handle` examples with capture-group-preserving splits.
- A frozen COCO-pretrained ResNet-50 backbone with a trained two-class head.
- Pairwise inference that retains the endpoint with the higher tip score.
- A validation-derived review flag for the lowest-margin 10% of endpoint pairs.

## Results to review

- Validation pair selection: 41/41 correct.
- Test pair selection: 24/24 correct.
- Test pairs sent to review by the frozen margin rule: 4/24.
- Test candidate classification: 47/48 correct. The one threshold miss was still
  correctly selected by pairwise ranking.

Open the complete test gallery at:

`ml/runs/endpoint_selector/v1/gallery/index.html`

Open the augmentation sheet at:

`ml/runs/endpoint_selector/v1/augmentation_review.jpg`

Confirm that:

1. The selected candidate contains the fine working tip, not the handle end.
2. Mirrored left-side candidates remain anatomically interpretable.
3. The proposed rotation, flip, brightness/contrast, blur, sharpening, Gaussian
   noise, and salt-and-pepper examples preserve the tip/handle label.
4. No alteration obscures the fine wire enough to change the ground truth.

Both the endpoint-selection and augmentation-strength portions of this gate are
approved. Authoritative combined-dataset defect-model retraining may proceed.
