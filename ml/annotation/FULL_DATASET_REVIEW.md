# Full Hook Sinskey Review in CVAT

CVAT Community 2.76.0 is running locally at <http://localhost:8080>. Its state is stored in local Docker volumes and is not committed to Git.

## Files

- Import archive: `ml/cvat/hook_sinskey_full_candidates.zip`
- Expanded images: `ml/annotation/local/hook_sinskey_full/cvat_dataset/images/default/`
- Overlays: `ml/annotation/local/hook_sinskey_full/overlays/`
- Local queue: `ml/annotation/local/hook_sinskey_full/review_queue.json`
- Tracked manifest: `ml/annotation/full_dataset_manifest.json`
- Tracked summary: `ml/annotation/full_candidate_summary.json`

## First-time setup

1. Open <http://localhost:8080> and create a local account, or sign in if one already exists.
2. Create a task named `Hook Sinskey — full segmentation review` with one label: `defect`.
3. Add all 240 files from the expanded `images/default/` directory as task data.
4. After task processing finishes, choose **Actions → Upload annotations**, select **COCO 1.0**, and upload `hook_sinskey_full_candidates.zip`.
5. Confirm that the task shows 240 images and 199 candidate masks before editing.

If CVAT offers direct dataset import for your account/version, the same ZIP may be imported as a COCO 1.0 dataset. Verify the 240/199 counts either way.

## Required review

- Inspect and correct every mask on all 179 defective images.
- Confirm all 61 healthy images contain no `defect` annotation.
- Apply `ANNOTATION_POLICY.md`; record ambiguity notes rather than guessing.
- Start with the lowest-confidence candidate: `valid/6-4_20260214_170937487...` (SAM2 score 0.4351), but review every item regardless of score.
- Do not change inherited split membership.

## Finish and handoff

1. Export the reviewed task as COCO 1.0 into a new local-only reviewed package; do not overwrite the candidate ZIP.
2. Tell the agent the reviewer name and that review is complete.
3. The agent will validate masks, negatives, derived boxes, IDs, split leakage, counts, and hashes before asking for Milestone 3 approval.

Useful local commands from `ml/cvat/runtime`:

```sh
docker compose up -d
docker compose ps
docker compose stop
```
