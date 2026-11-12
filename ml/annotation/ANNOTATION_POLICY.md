# Hook Sinskey Defect-Mask Policy

Status: draft for Milestone 2 human review.

## Canonical label

- Use exactly one category: `defect` (`category_id: 1`).
- A defective image receives one instance mask for each separately visible affected tip segment.
- A healthy image receives no annotation. Its COCO `annotations` list is empty.
- Existing YOLO boxes are prompts for assisted labeling only. They are not segmentation ground truth.
- Final detection boxes are derived from approved masks and must not be copied from prompt boxes.

## Inclusion boundary

Mask only visible Hook Sinskey pixels that form the affected distal segment. Begin at the first visually supportable transition from normal shaft geometry or surface to the affected region and continue to the visible distal end. Exclude normal shaft, handle, background, shadows, labels, and unrelated instruments.

The goal is a clinically interpretable affected segment, not a tight outline around an image artifact and not a mask of the entire tool.

## Case rules

### Bend or deformation

- Include the continuous segment from the onset of abnormal curvature through the distal tip.
- Do not include an otherwise normal proximal shaft merely because it lies inside the prompt box.
- If the onset is ambiguous, choose the shortest defensible affected segment and mark `boundary_uncertain`.

### Break, chip, or missing tip

- Mask the visible damaged remnant and visibly affected adjacent material.
- Do not mask empty background where material is missing.
- If only absence is inferable and no affected material is visible, mark `domain_review_required`; do not invent a mask.

### Partial visibility or occlusion

- Mask only the visible affected pixels.
- Accept the instance only when the defect remains assessable from visible evidence.
- If the defect state or proximal boundary cannot be supported, mark `domain_review_required`.

### Reflection and glare

- Reflections alone are not defects.
- Exclude specular highlights unless underlying deformation or damage is independently visible.
- Mark `reflection_interference` when glare materially obscures the boundary.

### Blur or poor focus

- Use a conservative boundary around pixels that remain visibly attributable to the affected segment.
- Mark `blurred_boundary` when exact edges are uncertain.
- If a defect cannot be verified, do not force a positive mask; mark `domain_review_required`.

### Multiple affected regions

- Use separate instances for spatially separate defects.
- Keep one instance for a continuous bent, broken, or damaged segment.

## Healthy-image review

Every healthy image must receive an explicit reviewer decision even though it has no instance annotation. Confirm that:

- The Hook Sinskey tip is sufficiently visible to assess.
- No bend, break, chip, deformation, or other intended defect is visible.
- Blur, glare, occlusion, or crop boundaries do not prevent a reliable negative decision.

If any condition fails, mark `domain_review_required`; do not silently treat the image as a confirmed negative.

## Review states

Each sample image has one of:

- `candidate_unreviewed`
- `approved`
- `corrected`
- `rejected`
- `domain_review_required`

Optional ambiguity flags are `boundary_uncertain`, `reflection_interference`, `blurred_boundary`, `partial_visibility`, and `multiple_defects`.

## Acceptance rules

- Masks stay inside image boundaries and contain at least one pixel.
- Derived boxes tightly enclose their masks.
- Defective images have at least one approved mask unless escalated for domain review.
- Approved healthy images have zero masks.
- Prompt boxes and SAM2 scores remain provenance metadata only.
- Train/validation/test membership never changes during annotation.
- The Milestone 2 pilot uses train and validation images only; the test split remains unopened for policy tuning.
