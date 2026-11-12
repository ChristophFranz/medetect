# Hook Sinskey Test-Metric Risk Audit

This audit explains why the frozen-test accuracy should not be interpreted as an
estimate of deployment performance. It did not retrain, retune, or rerun any model.
The machine-readable evidence is in `ml/experiments/test_metric_audit.json`.

Regenerate the audit with:

```sh
conda run -n medetect-ml python -m ml.scripts.audit_test_metric_risk
```

## What 0.875 accuracy means here

- The test split has 24 images: 18 defective and 6 healthy.
- Accuracy changes by 0.0417 for every image.
- Legacy YOLO and Mask R-CNN each classified 21 of 24 images correctly: 0.875.
- A classifier that calls every image defective gets 18 of 24 correct: 0.750.
- The apparent improvement over that trivial rule is three correctly rejected healthy
  images.
- The exact binomial 95% confidence interval for 21/24 is 0.676–0.973.
- Specificity is based on only six images. Three of six were correct, giving 0.500
  specificity with an exact 95% interval of 0.118–0.882.

Therefore 0.875 is the observed score, but it is not a precise estimate. It is also
essentially the same as a previously reported accuracy of 0.88 after rounding. The
historical YOLO value of 0.8982 recorded in this repository is **mAP50**, not accuracy,
and must not be compared directly with 0.875 accuracy.

## Split dependence and acquisition leakage

There are no byte-identical image files shared across train, validation, and test.
However, the images were split at image level from rapid capture sequences:

- The median test image is 8.135 seconds from the nearest same-group training capture.
- 23 of 24 test images are within 30 seconds of a training capture.
- All 24 are within 36 seconds of a training capture.
- A 64-bit difference-hash screen found 6 of 24 test images within Hamming distance 5
  of a training image and 13 of 24 within distance 10. This is a heuristic indication
  of visual similarity, not proof of duplication.

The label is also perfectly associated with acquisition group across all 240 images:

- Every `6-4` image is defective.
- Every `6-3` image is healthy.

Filenames are not passed to the models, but lighting, background, camera position,
instrument placement, and other group-specific visual cues may reveal the same
association. A rule based only on acquisition group labels all 240 images correctly.

## Interpretation

The current frozen test result measures performance on held-out frames from the same
two acquisition streams. It is useful for checking that the model pipeline works and
for making a controlled internal comparison, but it likely overstates performance on
new instruments, sessions, cameras, operators, and backgrounds.

The strongest defensible conclusion remains: Mask R-CNN matched inherited YOLO on
this internal split while adding a defect mask. It has not yet demonstrated external
or deployment generalization.

## Correct follow-up design

Collect healthy and defective examples in the same sessions and under the same
backgrounds, then split by physical instrument and acquisition session rather than by
individual image. Keep the resulting test sessions entirely untouched. The next test
set also needs substantially more than six healthy images so specificity can be
estimated with useful precision.
