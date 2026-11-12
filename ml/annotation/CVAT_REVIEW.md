# Local CVAT Review Procedure

Docker Desktop was repaired and verified on 2026-09-24: client/engine 29.8.0, Compose 5.5.1, Apple `aarch64`. The app now runs from `/Applications/Docker.app`, and normal `docker` commands resolve through `~/.local/bin/docker`. Docker is an external system prerequisite, not a Python dependency, so it is intentionally not managed through pip or Conda.

Official references:

- CVAT Community installation: <https://docs.cvat.ai/docs/administration/community/basics/installation/>
- COCO import/export behavior: <https://docs.cvat.ai/docs/manual/advanced/formats/format-coco/>

## Prepared local package

- CVAT ZIP: `ml/cvat/hook_sinskey_pilot_candidates.zip`
- Expanded dataset: `ml/annotation/local/hook_sinskey_pilot/cvat_dataset/`
- Visual overlays: `ml/annotation/local/hook_sinskey_pilot/overlays/`
- Review queue: `ml/annotation/local/hook_sinskey_pilot/review_queue.json`
- Tracked summary and hashes: `ml/annotation/candidate_summary.json`

The ZIP follows CVAT's COCO structure:

```text
images/default/<20 image files>
annotations/instances_default.json
```

## Review steps

1. Install and start Docker Desktop for macOS, then install/start local CVAT Community using the official instructions.
2. Create or import a task containing one label, `defect`.
3. Import `ml/cvat/hook_sinskey_pilot_candidates.zip` as COCO 1.0 instance segmentation.
4. Review all 20 images against `ANNOTATION_POLICY.md`:
   - Correct or reject every one of the 15 generated masks on 14 defective images.
   - Confirm all 6 healthy images as reviewed negatives with no mask.
   - Record ambiguity flags and notes for uncertain cases.
5. Export reviewed annotations as COCO 1.0 into a new local-only `reviewed/` directory. Do not overwrite the candidate package.
6. Update `review_queue.json` with reviewer, date, state, flags, and notes.
7. Run the reviewed-package validator before requesting the Milestone 2 gate.

The overlays use red for the SAM2 candidate mask and yellow for the inherited YOLO prompt box. SAM2 scores are prioritization metadata only and must not substitute for human review.
