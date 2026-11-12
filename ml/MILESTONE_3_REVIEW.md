# Milestone 3 Review — Frozen Hook Sinskey Ground Truth

Status: approved by Christoph on 2026-09-24; canonical dataset frozen.

## Candidate package

- SAM2 model: `facebook/sam2.1-hiera-tiny@de431c4043854a71d8101e17995dfe596bf101a5`
- Device: Apple MPS
- Images: 240 (179 defective, 61 healthy)
- Candidate masks: 199
- Predicted-IoU range: 0.4351–0.8970; mean 0.7838
- COCO SHA-256: `4500fd7cc8d07324bf50cf4381ddc40eb3df7f6424bc0089421630b3e7666b37`
- CVAT ZIP SHA-256: `550731b169205b58f59b74274fd9f39508c8fe27beede4ad236c0f73f477115f`
- Package validation: passed
- Exact-image/source-capture cross-split leakage: none
- CVAT: Community 2.76.0 running locally at `http://localhost:8080`

## Required review scope

- 240 images in the inherited splits: 181 train, 35 validation, 24 test.
- 179 defective images with 199 inherited defect-box prompts.
- 61 healthy images that must remain annotation-free.
- One canonical class: `defect`.
- Every generated mask and every healthy-negative decision requires human review.

## Freeze checks

- Stable unique image IDs and original train/validation/test membership.
- No exact-image or source-capture leakage across splits.
- Valid in-bounds masks for every approved defective instance.
- Empty annotation lists for approved healthy images.
- Boxes derived from masks and enclosing them exactly.
- Counts and hashes recorded after the reviewed CVAT export.
- Test split frozen only after approval; no test data may inform training, early stopping, or threshold selection.

## Reviewed export

- Reviewer: Christoph
- Review date: 2026-09-24
- CVAT task/job state: completed
- Reviewed ZIP SHA-256: `da7381a24fdf71e60f61c73177b10ca8b49da6e9bd87927dd53ae13c79ab2269`
- Reviewed COCO SHA-256: `a25df42862b39b3f159a2f73e788cab6bb5135bad86aa642b877ee542195b290`
- Images: 240 (181 train, 35 validation, 24 test)
- Masks: 199 across all 179 defective images
- Healthy negatives: all 61 contain zero masks
- Mask, area, boundary, category, filename, ID, box-enclosure, and split checks: passed
- Images with mask pixels changed versus the original SAM2 candidate: 31
- Canonical validation record: `ml/annotation/reviewed_summary.json`

## Known limitation

Defect status remains perfectly confounded with acquisition group (`6-4` defective, `6-3` healthy). Approval freezes an internal benchmark, not evidence of deployment generalization.

## Human gate

- Reviewer: Christoph
- Date: 2026-09-24
- Decision: approved and frozen
- Canonical dataset version: `hook_sinskey_segmentation_v1`
- Canonical tree SHA-256: `771a2e13e818ac6c6d70a06c9b9973b5fd701a415373f0dc265b20e37c1eb74e`
- Next action: begin Milestone 4 model adapters and smoke tests
