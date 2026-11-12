# Milestone 2 Review — Annotation Policy and SAM2 Pilot

Status: approved by Christoph on 2026-09-24.

## Policy

`ml/annotation/ANNOTATION_POLICY.md` defines one canonical class, `defect`. Defective images receive masks over visibly affected distal segments; approved healthy images receive no annotation. It includes rules for bends, breaks, missing material, partial visibility, reflection, blur, multiple defects, conservative boundaries, and domain-review escalation.

## Deterministic sample

- Sample size: 20 images
- Train: 10 defective, 4 healthy
- Validation: 4 defective, 2 healthy
- Test: 0 images
- Defect prompts: 15 inherited class-0 YOLO boxes across 14 defective images
- Sample manifest SHA-256: `eda0df7f168a23372b151c6939ad77ed4c41e6e0f7d6fa02c2766e96e55f0c48`
- Selection rerun reproduced the same manifest hash while preserving workflow state.

## SAM2 candidates

- Hugging Face model: `facebook/sam2.1-hiera-tiny`
- Immutable revision: `de431c4043854a71d8101e17995dfe596bf101a5`
- License: Apache-2.0
- Device: Apple MPS
- Candidate masks: 15
- Predicted-IoU range: 0.7012–0.8507; mean 0.7841
- Healthy candidates: 6 images with zero masks
- COCO SHA-256: `ece888db5454b2b622f06204c21292e0ad30f6c502f9e2cbfdf7c755b9405a6b`
- CVAT ZIP SHA-256: `3256594814eb68770e9c92df40772580ba9be5e6445ae61a56ce3fbbb21fdaa6`

The official checkpoint advertises both image and video use. Transformers identifies its configuration as `sam2_video`; the generator intentionally loads the compatible image subset with `Sam2Model`. All 20 images completed, and the resulting image masks passed shape, non-empty area, boundary, box-enclosure, class, negative-image, and package-structure validation.

Four initial visual spot checks covered a small prompt, a large bent segment, a two-instance image, and a healthy negative. Christoph subsequently reviewed the pilot overlays and approved all 20 pilot decisions and the annotation policy.

## Data-risk finding

Class is perfectly confounded with filename acquisition group: all 179 defective images are `6-4`, while all 61 healthy images are `6-3`. Background/session shortcuts may therefore inflate both historical and future internal metrics. See `ml/annotation/DATA_RISK.md`.

## Local review package

- Import ZIP: `ml/cvat/hook_sinskey_pilot_candidates.zip`
- Expanded local dataset and overlays: `ml/annotation/local/hook_sinskey_pilot/`
- Instructions: `ml/annotation/CVAT_REVIEW.md`
- Tracked summary: `ml/annotation/candidate_summary.json`

Raw images, masks, overlays, downloaded weights, and the import ZIP remain local and ignored by Git.

## Human gate result

- Reviewer: Christoph
- Date: 2026-09-24
- Decision: approved
- Scope: annotation policy, 15 candidate masks, and 6 healthy-negative decisions across all 20 pilot images
- Review method: generated visual overlays, not an edited CVAT export
- Corrections requested: none
- Next action: begin Milestone 3 full-dataset assisted annotation and human review

Docker Desktop was subsequently repaired and verified with engine 29.8.0 and Compose 5.5.1. CVAT remains the review system for the full dataset. Do not freeze the benchmark dataset or begin model training until the Milestone 3 gate is approved.
