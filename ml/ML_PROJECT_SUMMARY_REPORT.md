# MEDetect ML Project Summary

**Project focus:** Hook Sinskey tool and defect detection  
**Report generated:** 26 October 2026  
**Current status:** Redesigned-tray pilot trained and evaluated; Mask R-CNN is the leading defect-model candidate, subject to external validation.

## 1. Executive Summary

This project developed and evaluated a two-stage computer-vision pipeline for detecting defects on Hook Sinskey ophthalmic instruments in full medical-tool tray photographs:

1. A YOLO tray detector locates each Hook Sinskey instrument in a full-tray image.
2. An endpoint-selection step identifies the tip end and produces a standardized tip crop.
3. A tool-specific model determines whether the tip is defective and, for segmentation models, identifies the affected tip region.

The inherited YOLO defect detector was retained as a baseline. Three alternatives were added: DETR detection, DETR segmentation, and Mask R-CNN segmentation. The data and training workflow were subsequently updated for a redesigned tray, including human-reviewed tool boxes, human-reviewed defect masks, deterministic data splitting, controlled augmentation, model fine-tuning, and validation-only operating-threshold selection.

On the final redesigned-tray crop-level test set of 24 Hook Sinskey instances, Mask R-CNN achieved the best defect-classification result: **95.8% accuracy, 100% precision, 93.8% sensitivity, 100% specificity, and 96.8% F1**. Its segmentation mAP50–95 was **51.3%**. In the connected full pipeline, Mask R-CNN correctly completed detection, cropping, defect classification, and defect localization for **20 of 24 expected tools (83.3%)**. The four failures at this stage were caused by upstream tray-detector misses rather than the Mask R-CNN defect classifier.

These results are promising but should be treated as a confirmatory pilot rather than a final deployment claim. The evaluation cohort is small, contains only four physical Hook Sinskey instruments, and includes captures that were encountered during earlier development. A new, untouched external collection is required to estimate real-world generalization reliably.

## 2. Project Objectives and Scope

The ML work had the following objectives:

- Preserve the existing full-tray detection architecture while improving tool-specific defect detection.
- Focus initially on Hook Sinskey instruments.
- Compare an inherited YOLO detector against DETR detection, DETR segmentation, and Mask R-CNN segmentation.
- Treat a healthy image as having no defect annotation or prediction.
- For a defective image, localize the visibly affected tip segment using a box or mask.
- Establish a reproducible workflow for data migration, annotation, training, evaluation, and handoff.
- Avoid modifying the React UI, Supabase integration, or production API during the ML pilot.

The present work does not yet implement human-in-the-loop review in the application UI, deploy a production model, or cover the other instrument families.

## 3. Inherited System and Baseline

The inherited project used YOLO models for both tray-level tool detection and tool-specific defect detection. The original Hook Sinskey defect checkpoint was preserved unchanged as the historical baseline.

The training metadata associated with that checkpoint reported:

| Historical YOLO metric | Value |
|---|---:|
| Precision | 76.25% |
| Recall | 85.18% |
| mAP50 | 89.82% |
| mAP50–95 | 57.12% |

These historical values are useful references but are not directly interchangeable with the new results because the annotation policy, evaluation implementation, test composition, tray design, and pipeline stage differ. The standardized evaluations created during this project are the preferred basis for model comparison.

## 4. Reproducible ML Workspace

A dedicated `ml/` workspace was created inside the GitHub-connected repository. Desktop source files were copied rather than moved, and the original source was left unchanged.

Reproducibility and handoff mechanisms include:

- `AGENTS.md` for mandatory startup instructions and project invariants.
- `ml/PROJECT_STATE.md` for current milestone, human gates, blockers, and next actions.
- `ml/DECISIONS.md` as an append-only technical decision log.
- `ml/CONTEXT_SNAPSHOT.md` as a concise restart and handoff document.
- Dataset manifests containing source records, hashes, split membership, class counts, and review state.
- An experiment registry containing model configurations, dataset identities, metrics, and artifact locations.
- Context-check and context-snapshot scripts.
- A Conda-only environment and lock/export files; no pip, pipx, or uv workflow was introduced.
- Deterministic seed `42`, frozen data splits, and validation-only operating-threshold selection.

Raw photographs, model weights, generated checkpoints, CVAT state, and large run outputs remain local and ignored by Git. Code, configurations, manifests, checksums, summary metrics, and reports are tracked.

## 5. Original Hook Sinskey Dataset

The original frozen dataset contained 240 images:

| Split | Images |
|---|---:|
| Training | 181 |
| Validation | 35 |
| Test | 24 |
| **Total** | **240** |

At image level, it contained 179 defective and 61 healthy examples. Existing YOLO boxes were used as prompts to generate initial SAM2 mask candidates. A 20-image stratified pilot was reviewed first to establish the mask policy before assisted annotation was expanded to the full dataset.

The final annotation policy was:

- Use one canonical class: `defect`.
- Mark the visibly affected Hook Sinskey tip segment.
- Allow multiple defect instances when multiple affected tips are visible.
- Give healthy images an empty annotation list.
- Derive detection boxes from reviewed segmentation masks.

All generated masks and all healthy-negative decisions were reviewed in CVAT. The frozen dataset contained 199 reviewed defect masks and retained healthy images with no annotations.

### Original-data limitation

The inherited data contained an acquisition confound: defective examples came from source group `6-4`, while healthy examples came from source group `6-3`. A model could therefore learn capture or background differences correlated with the label instead of only learning the defect. This motivated the redesigned-tray collection and the need for stronger external validation.

## 6. Initial Model Benchmark

Shared model adapters were implemented for:

- Inherited Hook Sinskey YOLO detection.
- DETR defect-box detection.
- DETR segmentation.
- Torchvision Mask R-CNN segmentation.

All adapters used a common prediction record, aspect-preserving resize to a 640-pixel maximum edge, consistent padding, deterministic behavior, Apple MPS acceleration where safe, and a documented CPU fallback.

On the original frozen 24-image test split, image-level defect classification was:

| Model | Accuracy | Sensitivity | Specificity | F1 |
|---|---:|---:|---:|---:|
| Inherited YOLO | 87.5% | 100.0% | 50.0% | 92.3% |
| DETR detection | 70.8% | 94.4% | 0.0% | 82.9% |
| DETR segmentation | 75.0% | 100.0% | 0.0% | 85.7% |
| Mask R-CNN | 87.5% | 100.0% | 50.0% | 92.3% |

This initial benchmark showed that the segmentation approaches could run end to end and that Mask R-CNN was the strongest segmentation candidate. It also showed that the small number of healthy cases made specificity unstable.

## 7. Redesigned-Tray Data Collection and Review

A new tray was introduced, requiring the upstream tray detector and crop-generation workflow to be adapted. The redesigned-tray collection contained 151 full-tray images. Human review in CVAT produced:

- 226 reviewed Hook Sinskey tool boxes.
- 154 defective tool instances.
- 72 healthy tool instances.

Three tray photographs contained two instruments: one defective upper instrument and one healthy lower instrument. These were handled as separate tool instances rather than assigning one label to the entire photograph.

Some automatically generated crops initially selected the handle end instead of the tip. An endpoint selector was therefore trained to choose the correct end. The selector used mirrored pairs and achieved 100% pair accuracy on both validation and test data. All downstream crops were then standardized into a canonical tip-right orientation.

SAM2 was used again to propose tip-defect masks. Every defective mask and every healthy negative was reviewed in CVAT. Reviewer corrections changed 21 proposed masks before the redesigned-tray segmentation dataset was accepted.

## 8. Final New-Tray-Only Dataset and Augmentation

For the final benchmark, the user elected to train only on redesigned-tray data. The physical tools were the same instrument set, but the tray background and collection conditions matched the intended future setup.

The final split was:

| Split | Total | Defective | Healthy | Augmented images |
|---|---:|---:|---:|---:|
| Training | 322 | 216* | 106* | 161 |
| Validation | 41 | 30 | 11 | 0 |
| Test | 24 | 16 | 8 | 0 |

\*The training class counts are doubled by creating one augmented partner for each of the 161 original training images. The original training set contained 108 defective and 53 healthy images.

The training set was deliberately materialized as a 50/50 composition:

- 161 original training images.
- 161 augmented training images.

Validation and test images remained unaugmented. Loader-time augmentation was disabled so the exact 50/50 composition stayed constant from epoch to epoch.

The approved augmentation policy was intentionally moderate:

| Augmentation | Setting |
|---|---:|
| Horizontal flip | Probability 0.50 |
| Rotation | Up to ±10° |
| Brightness jitter | 0.15 |
| Contrast jitter | 0.15 |
| Blur | Probability 0.10 |
| Sharpening | Probability 0.10 |
| Gaussian noise | Probability 0.15; standard deviation 0.015 |
| Salt-and-pepper noise | Probability 0.05; affected fraction 0.002 |

Geometric transformations were applied consistently to images, boxes, and masks. Augmentation increased appearance variation but did not create new physical tools, new defect mechanisms, or independent biological samples.

## 9. Final Model Training

### 9.1 Tray-level YOLO detector

The one-class Hook Sinskey tray detector was initialized from the previous tray checkpoint and fine-tuned on the human-reviewed redesigned-tray boxes. Its best validation checkpoint occurred at epoch 8.

| Validation metric | Result |
|---|---:|
| Precision | 99.4% |
| Recall | 100.0% |
| mAP50 | 99.5% |
| mAP50–95 | 70.4% |

### 9.2 Tool-specific defect models

| Model | Initialization and training outcome |
|---|---|
| YOLO detection | Initialized from the inherited Hook Sinskey checkpoint; early stopped after 24 epochs; best epoch 18. |
| DETR detection | Full-model fine-tuning for 20 epochs; best epoch 18. |
| DETR segmentation | Full-model fine-tuning with activation checkpointing and bounded MPS memory; early stopped after 14 epochs; best epoch 9. |
| Mask R-CNN | Full-model fine-tuning; early stopped after 11 epochs; best epoch 6. |

DETR segmentation required explicit MPS memory controls. Unrestricted MPS execution was not safe on the available laptop, while CPU training was impractically slow. Bounded MPS execution with activation checkpointing allowed training to finish while retaining normal laptop usability.

## 10. Threshold Selection and Test Discipline

Operating thresholds were selected using only the 41-image validation set. Balanced accuracy was optimized subject to a minimum sensitivity requirement of 90%. The selected defect thresholds were:

| Model | Score threshold | Minimum mask area |
|---|---:|---:|
| YOLO detection | 0.001625 | Not applicable |
| DETR detection | 0.130762 | Not applicable |
| DETR segmentation | 0.257079 | 1 pixel |
| Mask R-CNN | 0.946180 | 1 pixel |

The connected tray detector used a validation-selected confidence threshold of 0.90. No threshold was modified after test evaluation.

CVAT brush masks were exported with `iscrowd=1`. Because standard COCO evaluation excludes crowd annotations from ordinary instance AP, the evaluator normalizes each individually reviewed defect instance to `iscrowd=0` in memory. This affects evaluation only; the frozen labels and training data remain unchanged.

## 11. Final Crop-Level Defect Results

The final test set contained 24 manually reviewed Hook Sinskey tip crops: 16 defective and 8 healthy.

| Model | Accuracy | Precision | Sensitivity | Specificity | F1 | AP50 | mAP50–95 |
|---|---:|---:|---:|---:|---:|---:|---:|
| YOLO detection | 83.3% | 92.9% | 81.2% | 87.5% | 86.7% | 60.3% | 35.1% |
| DETR detection | 54.2% | 66.7% | 62.5% | 37.5% | 64.5% | 14.7% | 4.6% |
| DETR segmentation | 79.2% | 78.9% | 93.8% | 50.0% | 85.7% | 60.1% | 34.0% |
| **Mask R-CNN** | **95.8%** | **100.0%** | **93.8%** | **100.0%** | **96.8%** | **93.1%** | **51.3%** |

Segmentation and operational results were:

| Model | Mean IoU | Mean Dice | Median latency per crop |
|---|---:|---:|---:|
| YOLO detection | Not applicable | Not applicable | 30.5 ms |
| DETR detection | Not applicable | Not applicable | 61.5 ms |
| DETR segmentation | 72.1% | 81.4% | 342.7 ms |
| Mask R-CNN | 71.9% | 81.2% | 197.2 ms |

Mask R-CNN classified 23 of 24 test crops correctly. The bootstrap 95% confidence interval for its accuracy was approximately 87.5% to 100%, illustrating the uncertainty caused by the small test sample.

Although DETR segmentation obtained reasonable overlap when it found the defect, it retained 174 masks for 24 test crops. This duplicate-query behavior requires stronger deduplication or query-level post-processing before DETR segmentation would be suitable for deployment.

## 12. Connected End-to-End Pipeline Results

The final connected evaluation executed the actual sequence:

`full tray photograph → YOLO tool detection → endpoint selection and tip crop → defect model → defect box or mask`

The set contained 16 tray photographs and 24 expected Hook Sinskey tools.
The connected run regenerates crops from predicted tray boxes, whereas the
standalone benchmark uses fixed reviewed crops. The two tables therefore use
different pixel inputs and must not be interpreted as a monotonic stage
ablation; the raw-count reconciliation is documented in
`ml/NEW_TRAY_V4_METRIC_AUDIT.md`.

### 12.1 Shared upstream performance

At the frozen 0.90 operating threshold, the tray detector produced:

| Upstream metric | Result |
|---|---:|
| Expected tools | 24 |
| Predicted tools | 22 |
| Correctly matched tools | 20 |
| False-positive tool detections | 2 |
| Missed tools | 4 |
| Operating precision | 90.9% |
| Operating recall | 83.3% |
| Mean matched tool-box IoU | 80.9% |
| Endpoint selection accuracy on matched tools | 100.0% |

The tray detector's COCO-style performance on this evaluation was 99.5% AP50 and 61.7% mAP50–95. The lower operating recall at a fixed confidence of 0.90 shows why summary AP and actual pipeline performance should both be reported.

### 12.2 End-to-end comparison

| Defect model after shared YOLO cropper | Accuracy on 20 delivered generated crops | Strict pipeline accuracy on 24 expected tools | Correct defect localization | Localization on defective tools |
|---|---:|---:|---:|---:|
| YOLO detection | 85.0% | 70.8% | 58.3% | 68.8% |
| DETR detection | 70.0% | 58.3% | 45.8% | 50.0% |
| DETR segmentation | 80.0% | 66.7% | 66.7% | 93.8% |
| **Mask R-CNN** | **100.0%** | **83.3%** | **83.3%** | **100.0%** |

The first column evaluates only the exact crops generated and delivered by the
connected run. Strict pipeline accuracy uses all 24 expected tools and counts
every missed expected tool as an error.

For Mask R-CNN, the correctly localized full-tray defects achieved a mean IoU of 76.3% and mean Dice of 86.3%. Its final 83.3% ceiling was determined by the four upstream tool misses: all 20 tools delivered correctly to the defect stage were handled successfully in this evaluation.

## 13. Interpretation of the Results

### Why the final figures are higher than early provisional results

An earlier provisional end-to-end exercise reported approximately 27.3% for YOLO, 0% for DETR detection, and 50.0% for Mask R-CNN. Those figures came from unreviewed crops, provisional labels, very limited adaptation, and a different set of only 22 quality-control-eligible tools. They are not directly comparable with the final benchmark.

The final workflow improved performance through:

- Human review of tray-level tool boxes.
- Correction of tool-end selection so crops consistently contain the tip.
- Human review of all defect masks and healthy negatives.
- Training on the redesigned tray domain.
- Controlled 50/50 original-to-augmented training composition.
- Full-model fine-tuning and early stopping.
- Validation-only threshold selection.
- Evaluation of the actual connected pipeline using frozen settings.

### Why Mask R-CNN outperformed the YOLO baseline

Mask R-CNN benefits from direct pixel-level supervision over the affected tip segment. For small, irregular defects, this can provide a more informative learning signal than box-only supervision. Its region-proposal and mask heads also align well with the task of finding a localized defect within an already cropped instrument tip.

This result does not establish that Mask R-CNN will always outperform YOLO. The dataset is small and model rankings can change on a genuinely independent cohort.

### Why DETR underperformed

DETR detection was weak on this small, specialized dataset. Transformer detectors often require more data or careful optimization to learn stable object queries. DETR segmentation additionally produced multiple overlapping query predictions for the same defect. Better query filtering, deduplication, class weighting, longer tuning, and a larger independent dataset may improve it, but it is currently not the preferred model family.

## 14. Limitations and Threats to Validity

The principal limitations are:

1. **Small test set.** The final test set contains only 24 tools, so a single error changes accuracy by 4.17 percentage points.
2. **Limited physical diversity.** The redesigned-tray data were collected from one healthy and three defective physical Hook Sinskey instruments.
3. **Development exposure.** The final tray captures appeared during earlier provisional evaluation and visual review. Exact split leakage was prevented, and thresholds were not tuned on test outcomes, but capture-session and near-duplicate correlations may make the final result optimistic.
4. **Augmentation is not new specimen data.** Rotation, flipping, illumination changes, blur, sharpening, and noise improve robustness but do not replace new instruments, defects, trays, cameras, or collection sessions.
5. **Upstream bottleneck.** Four of 24 tools were missed by the tray detector at the chosen operating point, limiting all downstream models.
6. **Specificity uncertainty.** Only eight healthy tools were present in the final crop-level test set.
7. **Legacy acquisition confound.** The original data correlated source groups with defect status.
8. **No production human-in-the-loop UI yet.** Low-confidence review is planned but not implemented in the current pilot.

The final figures should therefore be described as promising internal or confirmatory results, not as proof of clinical or production-level performance.

## 15. Visual and Machine-Readable Outputs

The project produces structured local outputs for inspection and presentation, including:

- Crop-level prediction overlays for all four defect models.
- Segmentation masks and masked overlays for DETR segmentation and Mask R-CNN.
- Full-tray connected-pipeline overlays showing detected tools and projected defect localization.
- Confusion matrices and model-comparison charts.
- CSV and JSON metric summaries.
- Threshold-selection records.
- Per-image prediction records and latency measurements.
- Error galleries and presentation-ready result folders.

Key tracked reports include:

- `ml/NEW_TRAY_V4_REPORT.md` — final new-tray-only crop benchmark.
- `ml/CONNECTED_PIPELINE_CONFIRMATORY_REPORT.md` — connected full-pipeline evaluation.
- `ml/COMBINED_REVIEWED_V3_REPORT.md` — preceding combined old/new reviewed benchmark.
- `ml/PROJECT_STATE.md` and `ml/CONTEXT_SNAPSHOT.md` — current status and exact artifact locations.

Large output images, weights, and runs are intentionally retained locally rather than committed to Git.

## 16. Recommended Next Steps

The recommended order of work is:

1. **Collect an untouched external test cohort.** Use new capture sessions and, if possible, additional physical healthy and defective instruments. Freeze it before viewing model predictions.
2. **Split by physical instrument and capture session.** Ensure that near-duplicate views of the same tool cannot appear across training and test sets.
3. **Audit near duplicates.** Use perceptual hashing or embedding similarity to detect highly similar photographs across splits.
4. **Improve tray-detector recall.** Evaluate a slightly lower confidence threshold on validation data, collect hard negatives, and add examples of currently missed tool poses without tuning on the frozen test set.
5. **Retain Mask R-CNN as the leading candidate.** Confirm its advantage on the external cohort before integration.
6. **Improve DETR only if strategically useful.** Test query deduplication, class weighting, additional pretraining, and broader hyperparameter search on validation data.
7. **Introduce human-in-the-loop review.** Route low-confidence tool detections, ambiguous endpoint selections, and low-confidence defect predictions to an operator.
8. **Test robustness deliberately.** Evaluate lighting, rotation, blur, noise, occlusion, reflections, partial visibility, camera distance, background variation, and future wet-tool conditions as separate test factors.
9. **Repeat the audited process for other tools only after approval.** Maintain separate manifests, masks, thresholds, and model reports for each instrument family.
10. **Integrate with the API and UI only after model and threshold approval.** Preserve visual overlays and confidence values for traceability.

## 17. Conclusion

The project converted a fragmented inherited YOLO workflow into a reproducible, human-reviewed benchmark for Hook Sinskey defect detection. It established a complete path from full-tray detection through tip cropping to defect classification and segmentation, while preserving data provenance and test discipline.

Among the evaluated defect models, Mask R-CNN is the strongest current candidate. It achieved 95.8% crop-level accuracy and 83.3% complete-pipeline localization success on the final redesigned-tray cohort. The remaining end-to-end errors were dominated by missed upstream tool detections. The result supports continued development of the two-stage YOLO-plus-Mask-R-CNN pipeline, but an untouched, instrument-grouped external test set is essential before making deployment or generalization claims.

