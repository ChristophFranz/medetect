# Redesigned-Tray Hook Sinskey Defect-Mask Review

The 226 crops in this package were regenerated directly from Christoph's
human-reviewed full-instrument boxes. A full-box orientation audit found 19
left-facing instruments and 207 right-facing instruments. Left-facing distal
tip crops are horizontally mirrored so every review image presents the tip on
the right. The decisions are recorded in `new_tray_tip_orientations.json` and
are not inferred from defect status or folder name. SAM2 masks remain
machine-generated and must not be treated as ground truth until this review is
completed.

## Create the CVAT task

1. Open local CVAT at <http://localhost:8080>.
2. Create a task named `Hook Sinskey — redesigned tray defect-mask review`.
3. Create exactly one label: `defect`.
4. Upload all images from
   `ml/annotation/local/new_tray_defect_model_cropped_candidates/cvat_dataset/images/default/`.
5. Confirm that CVAT reports **226 images**.
6. Open **Actions → Upload annotations**, choose **COCO 1.0**, and select
   `ml/cvat/new_tray_defect_model_cropped_candidates.zip`.
7. Confirm that CVAT reports **154 masks**. The other 72 images are healthy
   negatives and should initially contain no annotations.

## Review policy

- A defective crop receives one `defect` mask over the visibly affected distal
  tip segment.
- A healthy crop must contain no mask.
- Correct masks that include tray, holders, reflections, shadows, or an
  unaffected portion of the instrument beyond the agreed tip segment.
- Delete a mask and redraw it if editing would be less reliable.
- Verify the entire tip remains inside the crop. Record any crop that still
  excludes the relevant tip rather than inventing a mask.
- Every crop should show the distal tool tip on the right. Stop and report the
  filename if a crop instead shows the handle end; do not annotate it.
- The three corrected two-tool exceptions use the established top-to-bottom
  convention: upper tool defective, lower tool healthy for `IMG_1667`,
  `IMG_1668`, and `IMG_1670`.

## Finish and handoff

1. Review every mask and every healthy negative.
2. Mark the CVAT job complete.
3. Export as **COCO 1.0**.
4. Save the ZIP as `ml/cvat/new_tray_defect_masks_reviewed.zip`.
5. Tell the agent that the redesigned-tray defect-mask review is complete and
   identify the reviewer.

The agent will validate mask geometry, empty healthy annotations, image IDs,
counts, split grouping, and hashes before rebuilding the combined dataset.
