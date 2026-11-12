# Decision Log

## 2026-10-29 — Separate fixed-crop and connected-crop metric interpretations

- Audit all final values directly from frozen per-image and per-instance
  prediction records after Christoph flagged apparently increasing connected
  accuracy and recall.
- Record that standalone evaluation uses fixed reviewed crops while connected
  evaluation regenerates crops from tray-YOLO predictions. These are different
  model inputs, so their figures are not a monotonic stage-ablation sequence.
- Preserve strict connected accounting: every missed expected tool is wrong.
- Report raw numerator/denominator counts and do not describe changes between
  standalone and connected tables as improvement or stage attrition.
- A future monotonic ablation, if required, must use identical crop pixels at
  each comparison point.

## 2026-10-28 — Count every missed expected tool as a pipeline error

- At Christoph's clarification, use strict pipeline accuracy as the primary
  connected classification metric: successful tool detection, correct endpoint
  selection, and the correct defect decision are all required.
- Count a missed expected tool as incorrect even when its ground-truth label is
  healthy. A missing output is an uninspected tool, not evidence of health.
- Retain the existing all-expected defect-label-agreement values only as
  diagnostics and never call them end-to-end or pipeline accuracy.
- Update the overall and subgroup reports accordingly. Mask R-CNN's corrected
  connected-pipeline accuracy is 83.3%, not 100.0%.

## 2026-10-28 — Post-hoc one/two-tool and wet/dry subgroup analysis

- Reuse the frozen new-tray v4 connected-pipeline instance records; do not
  rerun training, change checkpoints, or tune thresholds from subgroup results.
- Report subgroup results as exploratory because the cohort contains only four
  trays per tool-count/wetness cell and the same limited physical instruments.
- Do not compare one-tool and two-tool accuracy as if class composition were
  controlled: all one-tool test instances are defective, while two-tool trays
  contain both healthy and defective instruments.
- Record that all four tray-detector misses are healthy second instruments in
  wet two-tool trays. Wetness, tool position, health status, and instrument
  identity are therefore confounded and require a newly collected external
  factorial cohort to separate.

## 2026-10-23 — Authorize new-tray-only fine-tuning and two-level reporting

- Reviewer: Christoph.
- Approve the new-tray-only v4 augmentation set and retain horizontal flipping.
- Fine-tune using redesigned-tray data only. Existing checkpoints may initialize
  training, but no legacy-tray images enter the new training split.
- Use one reviewed new-tray YOLO detector for every connected pipeline variant.
- Compare downstream defect models at two explicitly separated levels:
  crop-level defect detection/segmentation and the complete tray-to-defect
  pipeline. Never substitute multiplied stage metrics for connected execution.
- Report the already exposed 24-crop/16-tray test cohort as confirmatory.

## 2026-10-23 — Prepare 50/50 materialized augmentation dataset

- At Christoph's clarified request, use only reviewed crops originating from
  the redesigned tray and materialize exactly one deterministic augmentation
  for each training original. The physical tools are unchanged across tray
  domains, but the target deployment domain is the redesigned tray.
- The resulting training composition is 161 original and 161 augmented images.
  Preserve the 41 validation and 24 test images byte-for-byte and do not
  augment either split.
- Retain the approved 50% horizontal-flip probability alongside conservative
  rotation, brightness, contrast, blur, sharpening, and noise transforms.
- Disable loader-time augmentation for this fine-tuning run so each epoch
  remains exactly 50% original and 50% materialized augmentation.
- Continue using tray YOLO upstream and compare legacy defect YOLO, DETR
  detection, DETR segmentation, and Mask R-CNN downstream.
- Do not start fine-tuning until both the pending connected-pipeline gate and
  the new augmentation-gallery review are explicitly approved and recorded.

## 2026-10-23 — Connected confirmatory pipeline result

- Execute 16 full redesigned-tray photographs containing 24 reviewed Hook
  Sinskey instances through tray YOLO, endpoint selection, Mask R-CNN, and the
  YOLO disagreement verifier with all policies frozen before the run.
- Label the result confirmatory because these captures appeared in the earlier
  provisional cascade; no test-informed tuning was performed in this run.
- Record 22/24 matched tools, 22/22 correct endpoints, and 21/24 end-to-end
  decision-plus-localization successes. All 16 defective tools exceeded full-
  tray mask IoU 0.50; mean IoU and Dice were 0.723 and 0.837.
- Do not headline crop classification alone. Tray YOLO produced seven unmatched
  Hook outputs, five of which became Mask R-CNN defect alarms, reducing alarm
  precision including false-tool outputs to 0.727.
- Treat tray-detector precision and count consistency as the next modelling
  bottleneck. Await review before retraining or tuning that detector.

## 2026-10-23 — Approve combined benchmark and authorize connected evaluation

- Reviewer: Christoph.
- Approve the combined reviewed-v3 crop-model benchmark and advance the
  Milestone 5 human gate.
- Execute the redesigned-tray Hook Sinskey pipeline as an actual connected
  sequence rather than multiplying independently measured stage metrics.
- Freeze all stage checkpoints, thresholds, endpoint policy, and any fusion
  rule before computing outcomes; do not tune from connected test results.
- Label the result `confirmatory`, because the redesigned-tray test captures
  were included in the earlier provisional cascade and are no longer an
  untouched external test cohort.
- Produce presentation metrics for stage attrition, final defect decisions,
  localization-aware success, review rate, latency, and failure attribution.

## 2026-10-21 — Approve endpoint selector visual gate

- Christoph confirmed that every selected test image contains the working tip
  rather than the handle end and remains visually valid.
- Keep the validation-derived low-margin review rule active despite 24/24
  correct test selections.
- Treat augmentation strength as a separate pending human gate; endpoint
  approval alone does not authorize authoritative defect-model retraining.

## 2026-10-21 — Use paired endpoint selection before defect modelling

- Generate both left and right endpoint candidates from every reviewed
  full-tool box and mirror left candidates into a consistent representation.
- Derive `tip` and `handle` labels from the reviewed orientation manifest;
  never infer them from defect status or folder names.
- Select the higher-scoring endpoint within each pair. Train with handle ends as
  explicit negatives so the downstream defect stage is protected from an
  endpoint-selection failure.
- Fit only a two-class head on a locally available COCO-pretrained ResNet-50
  backbone for the pilot. MPS was unavailable in the execution session, so the
  documented CPU fallback was used; HPC training remains deferred.
- Freeze a human-review trigger at the 10th percentile of validation pair-score
  margins. This selected all 24 test tips correctly and flagged four as low
  margin rather than silently accepting them.

## 2026-10-21 — Freeze reviewed redesigned-tray masks and combined v3

- Accept Christoph's reviewed COCO export after structural and semantic
  validation of 226 images, 154 defective masks, and 72 empty healthy images.
- Build `hook_sinskey_combined_reviewed_v3` exclusively from the previously
  frozen legacy dataset and the reviewed redesigned-tray export; provisional
  SAM2 masks are not authoritative inputs.
- Preserve all reviewed samples and treat mask-area bounds as advisory checks,
  not automatic exclusion criteria. No reviewed masks triggered those bounds.
- Freeze the resulting train/validation/test membership and tree hash before
  full-training or hyperparameter experiments.

## 2026-10-21 — Make redesigned-tray tip orientation explicit

- The redesigned-tray collection contains both left-facing and right-facing
  instruments, so a global handle-left/tip-right assumption is invalid.
- Store orientation overrides in
  `ml/annotation/new_tray_tip_orientations.json` rather than encoding image
  identifiers in crop logic or inferring orientation from defect labels.
- Crop the distal 62% from the recorded side and mirror left-facing crops to a
  canonical tip-right representation before SAM2 annotation and downstream
  modelling.
- Status: agent-audited across all 226 full-tool boxes; pending confirmation
  during Christoph's complete mask/negative review.

## 2026-09-23 — Pilot scope

- Use Hook Sinskey as the first tool-specific pilot.
- Keep the tray-level YOLO detector unchanged.
- Compare inherited YOLO, DETR detection, DETR segmentation, and Mask R-CNN.
- Treat the affected tip segment as the defect mask; healthy images receive no mask.

## 2026-09-23 — Model sources

- Use Hugging Face for DETR detection and segmentation checkpoints.
- Use Torchvision for Mask R-CNN.
- Preserve the inherited YOLO checkpoint and operating point as the baseline.

## 2026-09-23 — Data and dependency policy

- Keep raw datasets, weights, checkpoints, and generated runs local and out of Git.
- Track manifests, checksums, configurations, code, and summarized results.
- Use Conda exclusively for Python dependency installation. Pip, pipx, and uv are prohibited.

## 2026-09-23 — Repository safety

- Preserve the pre-existing staged application changes.
- Stage and commit ML additions using explicit paths only.
- Copy legacy files; never move or delete the originals during migration.

## 2026-09-23 — Resolved Conda environment

- Use conda-forge builds of PyTorch 2.9.1 and Torchvision 0.24.1 on `osx-arm64`.
- This matched pair replaces the initial mixed-channel solve, which exposed a missing JPEG runtime and an older PyTorch build.
- Host-side MPS is available; CPU is the required fallback where Metal is hidden or unsupported.
- Set `PYTORCH_ENABLE_MPS_FALLBACK=1` for inherited YOLO execution because Torchvision NMS falls back to CPU while the rest of the tested prediction remains on `mps:0`.

## 2026-09-23 — Inherited YOLO operating point

- Preserve confidence threshold `0.1`, as used by the Hook Sinskey call in the inherited `Detector.py`.
- Treat the historical training metrics as reference values only; the later frozen-test evaluation is authoritative.

## 2026-09-23 — Milestone 0 human gate

- Reviewer: Christoph.
- Decision: approved.
- Next action: verify that a fresh person or agent can recover project state and the next command from `AGENTS.md` and `ml/CONTEXT_SNAPSHOT.md`, then request Milestone 1 approval.

## 2026-09-24 — Milestone 1 human gate

- Reviewer: Christoph.
- Decision: approved.
- Next action: define the Hook Sinskey mask policy and generate a deterministic, stratified 20-image SAM2/CVAT review sample without using the test split.

## 2026-09-24 — Milestone 2 pilot sample

- Use 20 train/validation images: 14 defective and 6 healthy; keep the test split entirely outside policy development.
- Select defective examples evenly across inherited normalized defect-box area and healthy examples by stable image ID.
- Use `facebook/sam2.1-hiera-tiny` at immutable revision `de431c4043854a71d8101e17995dfe596bf101a5` with inherited class-0 YOLO boxes as prompts.
- Treat all 15 generated masks as unreviewed candidates regardless of SAM2 score.
- Require explicit human decisions for all 6 mask-free healthy images.

## 2026-09-24 — Acquisition confound

- Every defective image belongs to filename capture group `6-4`; every healthy image belongs to `6-3` across train, validation, and test.
- Report future metrics as internal-dataset performance and do not claim deployment generalization without cross-session, cross-instrument data.

## 2026-09-24 — Milestone 2 human gate

- Reviewer: Christoph.
- Decision: approved the annotation policy and all 20 pilot decisions after inspecting the generated overlays.
- No pilot corrections were requested. Record the review method as `visual_overlays`; it was not an edited CVAT export.
- Begin Milestone 3 full-dataset candidate generation and review. Do not freeze the dataset or train benchmark models until every full-dataset mask and healthy-negative decision is reviewed and the Milestone 3 gate is approved.

## 2026-09-24 — Docker Desktop repair

- The initial backend was running from the read-only `/Volumes/Docker` installer image, and CLI links targeted that mount.
- Relaunched the installed `/Applications/Docker.app` copy and repointed `~/.local/bin/docker` and `~/.docker/bin/docker` to its CLI.
- Verified Docker client/engine 29.8.0, Compose 5.5.1, Docker Desktop on Apple `aarch64`.

## 2026-09-24 — Milestone 3 candidate package

- Include all 240 images in the inherited train/validation/test splits for annotation; this labels ground truth but does not permit test use for training or tuning.
- Generated 199 SAM2 candidates for 179 defective images and preserved 61 healthy images with empty annotation lists.
- The full manifest found no exact-image or source-capture ID crossing split boundaries.
- Pin local CVAT Community to v2.76.0 (`b78c39f7a5de6450567e77c9e1ffc8f0c428cea7`) under ignored `ml/cvat/runtime`.
- Full human review remains mandatory; SAM2 confidence is only a review-priority hint.

## 2026-09-24 — Milestone 3 reviewed export

- Christoph reviewed all 240 images in local CVAT and completed the task/job.
- The reviewed export validates with 199 masks on all 179 defective images and no masks on all 61 healthy images.
- Thirty-one images contain mask-pixel changes versus the original SAM2 candidates; treat the human-reviewed CVAT export as authoritative.
- Keep the reviewed ZIP local and track only its hashes, validation summary, and reproducibility code.
- Await explicit Milestone 3 approval before marking the test split frozen or starting Milestone 4.

## 2026-09-24 — Milestone 3 human gate and dataset freeze

- Reviewer: Christoph.
- Decision: approved Milestone 3 and froze the reviewed Hook Sinskey dataset.
- Canonical dataset version: `hook_sinskey_segmentation_v1`.
- Canonical tree SHA-256: `771a2e13e818ac6c6d70a06c9b9973b5fd701a415373f0dc265b20e37c1eb74e`.
- Preserve 181 train, 35 validation, and 24 test images. The test split may be used only for the single final evaluation after Milestone 5 thresholds are frozen.
- Begin Milestone 4 adapters and smoke tests; do not begin the controlled benchmark until its prediction-review gate is approved.

## 2026-09-24 — Milestone 4 smoke-test boundary

- Use a common 640-pixel maximum-edge, aspect-preserving transform with bottom/right padding and exact realized horizontal/vertical scales for coordinate restoration.
- All four adapters passed one-batch inference and checkpoint reload on Apple MPS. DETR detection, DETR segmentation, and Mask R-CNN passed backward propagation and a five-epoch run on one defective and one healthy training image.
- The inherited YOLO checkpoint remains byte-identical and was not trained. Torchvision NMS falls back to CPU for YOLO and Mask R-CNN in this environment.
- The two-image smoke checkpoints validate mechanics only. Their predictions are explicitly not benchmark performance and may contain obvious false positives or false negatives.
- Use a deterministic validation review set containing five defective and five healthy images per model. Do not access the frozen test split or start Milestone 5 until Christoph approves the prediction-review gate.

## 2026-09-24 — Milestone 4 human gate

- Reviewer: Christoph.
- Decision: approved after reviewing all four model galleries with detection boxes and segmentation masks displayed separately.
- Begin Milestone 5 controlled benchmark implementation. Keep the frozen test split inaccessible until training, early stopping, and validation-only threshold selection are complete and recorded.

## 2026-09-24 — Benchmark prediction provenance

- Preserve every required unified prediction field and add `instance_scores`, aligned one-to-one with boxes and masks.
- The additional field is necessary for validation-only threshold selection and standard COCO AP calculation; the single `confidence` field remains the maximum retained instance score for image-level decisions.
- Select score thresholds from the union of the predeclared regular grid and observed validation scores. This avoids coarse-grid artifacts while remaining deterministic and validation-only.

## 2026-09-25 — DETR segmentation memory boundary

- A full-parameter DETR segmentation attempt was stopped before epoch 1 and before any checkpoint after more than 28 minutes under severe unified-memory pressure. It is not counted as a trained benchmark model and did not access test data.
- Keep the common 640-pixel input and frozen splits, but fine-tune only the pretrained segmentation model's defect classifier, box predictor, mask head, and box-attention layers.
- Record this heads-only scope as an important comparison limitation; use a dedicated immutable configuration file so the completed DETR detection configuration hash remains reproducible.

## 2026-09-25 — DETR thin-instance postprocessing

- Do not use the panoptic pixel-assignment postprocessor for the defect-tip benchmark: it discarded every validation mask despite non-empty high-logit per-query masks.
- Treat each retained defect query as an instance, bilinearly upsample its mask logits to the common padded size, threshold the sigmoid mask, restore it to original coordinates, and derive its box from that mask.

## 2026-09-25 — Mask R-CNN empty-batch MPS workaround

- The initial Mask R-CNN attempt failed before checkpointing because PyTorch 2.9.1 MPS cannot backpropagate an all-negative batch with empty detection tensors.
- Use every training image exactly once per epoch, but deterministically pair healthy images with defective images so every Mask R-CNN batch has at least one instance. Do not create annotations for healthy images or remove them from training.

## 2026-09-25 — Controlled benchmark result

- Freeze all operating points before test access and evaluate each model exactly once on the 24-image frozen test split.
- Mask R-CNN matches inherited YOLO image-level accuracy, sensitivity, specificity, and F1 while providing the requested segmentation; treat it as the leading pilot model.
- Do not treat DETR segmentation as a full architecture comparison because hardware constraints required heads-only fine-tuning.
- Do not claim deployment generalization because acquisition group remains perfectly confounded with defect label.
- Await Milestone 5 human review before any expansion, tuning, relabeling, or application integration.

## 2026-10-15 — Redesigned-tray detector before defect modelling

- The new collection contains 151 full redesigned-tray photographs rather than pre-cropped tool-tip images. Retrain tray-level localization before building the combined defect dataset.
- Preserve the inherited detector's four-class mapping: `chop phaco`, `forceps macpherson`, `forceps utrata`, and `hook sinskey`.
- Combine inherited four-tool tray data with reviewed new-tray Hook Sinskey boxes. Do not train only on the new Hook photographs, because that would encourage catastrophic forgetting of the other three classes.
- Start fine-tuning from the inherited tray YOLO checkpoint and report performance separately for the inherited tray domain and redesigned-tray domain.
- Keep contiguous capture bursts and every tool from a multi-tool photograph in one split. Do not randomly split near-duplicate frames at image or crop level.
- The inherited tray checkpoint detected zero tools in a 36-image sample of the new collection at confidence 0.1, confirming material tray/capture domain shift.
- Candidate boxes were generated for all 151 images (223 Hook Sinskey instances). Human review and a validated COCO export are mandatory before tray-model training or model-based cropping.
- This experiment is explicitly authorized by the user while the prior Milestone 5 benchmark-review record remains preserved.

## 2026-10-15 — Presentation-only annotation-review bypass

- Christoph explicitly authorized bypassing the redesigned-tray box-review gate because the presentation is urgent.
- Preserve `review_status: pending`; machine-generated boxes do not become reviewed ground truth through this bypass.
- Mark the combined dataset, tray checkpoint, metrics, crops, and downstream results as `provisional_unreviewed_new_tray_boxes`.
- Use the inherited four-class checkpoint and a shortened 20-epoch, 640-pixel YOLOv8n fine-tune for the presentation run. Keep the best validation checkpoint.
- Return to full box review and authoritative retraining before deployment, publication, or final model selection.

## 2026-10-16 — Provisional redesigned-tray benchmark result

- Stop the shortened tray fine-tune after epoch 11 because validation performance had recovered and the presentation deadline did not justify further local CPU time.
- The retrained tray detector recovers redesigned-tray mAP50 from 0.000 to 0.659 while retaining original-tray mAP50 of 0.947; use candidate-box fallback for the three unmatched instances only in this provisional dataset.
- Quarantine 13 new defective crops whose SAM2 mask area falls outside `[0.001, 0.10]`; do not silently convert them to healthy or use implausible masks as ground truth.
- Adapt DETR detection and Mask R-CNN for one epoch from the prior reviewed-dataset checkpoints. This is a presentation-time domain adaptation run, not the planned full HPC comparison.
- The inherited YOLO remains the best combined-test classifier at 0.848 accuracy and 0.899 F1. DETR and Mask R-CNN have 0.000 and 0.071 specificity, respectively, and therefore are not deployment candidates at the current thresholds.
- Mask R-CNN's 0.696 Dice is promising for segmentation, but the unreviewed labels, one-epoch training, and 46-image test set prohibit a final model-family decision.
- Preserve human review as the next gate. The urgent bypass does not approve the generated labels or supersede the frozen reviewed v1 benchmark.

## 2026-10-16 — Linked cascade reporting definition

- Report a senior-report-style linked cascade only on the 22 QC-eligible redesigned-tray test instances for which tray detection, detector-derived crop, defect ground truth, and downstream predictions can be joined deterministically.
- Do not multiply independent aggregate metrics or call the 46-image defect benchmark an end-to-end tray result.
- Define localization-aware success as: tool detected and crop exported; healthy cases receive a correct no-defect decision; defective cases receive a correct defect decision and at least one predicted box or mask with IoU ≥ 0.50.
- Keep box localization for inherited YOLO and DETR distinct from Mask R-CNN mask localization. The resulting rates are 27.3%, 0.0%, and 50.0%, respectively.
- State prominently that two generated-mask outliers were quarantined before cohort formation and that the 22 linked reference annotations remain unreviewed.

## 2026-10-20 — Redesigned-tray box review and source-label exceptions

- Reviewer: Christoph.
- The reviewed COCO export contains 151 images and 226 valid Hook Sinskey boxes.
- Human review revealed that `IMG_1667`, `IMG_1668`, and `IMG_1670` each contain two instruments despite residing in `One Tool Dry/Defect`.
- Record these as explicit, reproducible source exceptions: upper tool defective and lower tool healthy. Do not rename or move Desktop originals.
- Treat the human-reviewed boxes as authoritative for crop regeneration; do not use provisional detector predictions or fallback boxes for the mask-review package.
- Regenerate 226 crops and 154 SAM2 masks. Keep 72 healthy crops annotation-free and require full human mask/negative review before rebuilding the authoritative combined dataset.
## 2026-10-21 — Endpoint augmentation strengths approved

- Reviewer: Christoph.
- Approve the proposed training-only horizontal flip, rotation, brightness and
  contrast jitter, mild blur, sharpening, Gaussian noise, and salt-and-pepper
  examples.
- Apply geometry jointly to images and masks, then derive boxes from the
  transformed masks so all targets remain aligned.
- Do not augment validation or frozen test data.
- Proceed with local combined reviewed v3 defect-model retraining; HPC work
  remains deferred.

## 2026-10-22 — Resume DETR segmentation with bounded MPS memory

- A computer restart interrupted full-backbone DETR-segmentation training after
  epoch 6. The resumable state and model checkpoints loaded successfully;
  epoch 6 remains the best checkpoint with validation loss 1.4872729214.
- Apple Metal reports a recommended maximum working set of 19,069,665,280
  bytes on this machine.
- Resume from epoch 7 without changing the frozen data, 640-pixel preprocessing,
  batch size, optimizer state, augmentation policy, or test-access prohibition.
- Set `PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.9` and
  `PYTORCH_MPS_LOW_WATERMARK_RATIO=0.8` so an allocation failure occurs before
  PyTorch consumes enough unified memory to destabilize the desktop.

## 2026-10-22 — Use micro-batches for safe full-backbone DETR segmentation

- The first bounded-memory resume stopped safely before epoch 7 with an MPS
  out-of-memory error; the epoch-6 state remained intact and macOS stayed
  responsive.
- From epoch 7 onward, use one image per training micro-batch and accumulate
  gradients for two steps. This preserves the effective batch size of 2 and
  the existing AdamW optimizer state while reducing peak activation memory.
- Keep validation at batch size 2 because it does not retain backward-pass
  activations. Keep the 640-pixel input, full trainable backbone, learning rate,
  augmentation policy, splits, and early-stopping history unchanged.
- Continue using MPS high/low watermarks 0.9/0.8. A two-train-image,
  two-validation-image Metal smoke test passed under these limits before the
  authoritative epoch-6 state was resumed.

## 2026-10-22 — Combined reviewed-v3 benchmark result

- DETR segmentation resumed safely and early-stopped at epoch 23, retaining
  epoch 18 as best with validation loss 0.9250394101.
- Freeze all four operating points from validation before test access, then
  evaluate each model once on the 48-image frozen test split.
- Inherited YOLO remains the strongest image-level classifier at 0.854 accuracy
  and 0.904 F1. Mask R-CNN is the strongest segmentation model at 0.792
  accuracy, 0.651 IoU, 0.759 Dice, and 0.633 mask AP50.
- Treat DETR segmentation's 1,022 retained test masks as a duplicate-query
  failure mode. Do not hide this with test-informed NMS or threshold changes.
- Record augmentation as on-the-fly training views, not new captured images:
  the physical train split remains 342 images and the longest run processed
  7,866 transformed presentations across 23 epochs.
- Await human review of the report, figures, masks, and error gallery before
  tuning or advancing the benchmark gate.

## 2026-10-23 — Pause new-tray v4 training after DETR detection

- Christoph explicitly paused DETR training and will provide a separate resume
  instruction.
- Preserve the completed tray-YOLO, defect-YOLO, and DETR-detection checkpoints.
- The attempted v4 DETR-segmentation runs did not complete epoch 1 and created
  no resumable training state. Restart from the combined-reviewed-v3 best
  checkpoint when authorized.
- Do not use unrestricted MPS for DETR segmentation on this Mac: observed
  unified-memory pressure left less than 0.4 GB free and risked repeating the
  earlier desktop instability.
- Activation-checkpointed CPU training was stable but slow. At resume, increase
  from four to six or eight CPU threads, monitor free memory and responsiveness,
  and keep full-model training, 640-pixel preprocessing, and the frozen data
  policy unchanged.

## 2026-10-23 — New-tray v4 confirmatory benchmark result

- Resume full-model DETR segmentation using activation checkpointing and
  bounded MPS watermarks after an eight-thread CPU attempt proved impractical.
  Early-stop at epoch 14 and retain epoch 9.
- Early-stop Mask R-CNN at epoch 11 and retain epoch 6.
- Freeze every defect-model operating point from validation before opening the
  confirmatory test cohort. Select the common tray-YOLO threshold from reviewed
  validation trays only; do not lower its 0.90 value after observing four test
  misses.
- Normalize CVAT `iscrowd=1` brush-mask metadata to non-crowd only inside
  COCOeval because each reviewed mask is an individual defect instance. Do not
  modify frozen annotations or retrain models for this metadata correction.
- Select Mask R-CNN as the leading redesigned-tray candidate: crop accuracy
  0.958, mask AP50 0.931, and connected localized success 0.833.
- Keep DETR segmentation as a research comparison rather than the deployment
  candidate. It retains useful union-mask overlap but continues to emit many
  duplicate instance queries.
- Label all current results confirmatory. Require a newly collected untouched
  tray cohort before claiming generalization or changing deployment thresholds.
