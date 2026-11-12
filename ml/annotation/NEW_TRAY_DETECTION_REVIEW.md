# Redesigned-Tray Detection Review

This gate reviews full-instrument Hook Sinskey boxes before retraining the
four-class tray detector. The candidates are machine-generated starting
points, not ground truth.

## Open the task

1. Open local CVAT at <http://localhost:8080>.
2. Create a task named `Hook Sinskey — redesigned tray detection review`.
3. Define these labels in this exact order:
   - `chop phaco`
   - `forceps macpherson`
   - `forceps utrata`
   - `hook sinskey`
4. Upload all 151 images from
   `ml/annotation/local/new_tray_detection_candidates/cvat_dataset/images/default/`.
5. Continue to the annotation job, then use **Actions → Upload annotations →
   COCO 1.0** and select `ml/cvat/new_tray_detection_candidates.zip`.
6. Confirm that CVAT reports 151 images and 223 boxes.

If the CVAT version offers a direct **Create from backup/dataset** route, the
same ZIP may be imported as a COCO 1.0 dataset instead. Do not overwrite or
rename the candidate ZIP.

## Box policy

- Every box must use the `hook sinskey` class.
- Draw one box per physical Hook Sinskey instrument: one-tool images have one
  box and two-tool images have two boxes.
- Enclose the entire visible instrument, including handle, shaft, and distal
  tip. Keep the box tight while including every visible part.
- Exclude tray walls, holders, labels, reflections, and unrelated background
  as far as a rectangular box permits.
- A defect label is deliberately **not** part of this task. These boxes train
  tray-level tool localization; defect/healthy labels are applied after crops
  are produced.
- Correct, resize, or replace every candidate box. Do not approve boxes solely
  because they look plausible at fit-to-window zoom.

Give extra attention to the ten fallback-localized images:

- `One Tool Dry/Defect/IMG_1527.jpeg`
- `One Tool Dry/Defect/IMG_1528.jpeg`
- `One Tool Dry/Defect/IMG_1535.jpeg`
- `One Tool Dry/Defect/IMG_1542.jpeg`
- `One Tool Dry/Defect/IMG_1544.jpeg`
- `One Tool Dry/Defect/IMG_1552.jpeg`
- `One Tool Dry/Defect/IMG_1554.jpeg`
- `One Tool Dry/Non-Defect/IMG_1519.jpeg`
- `One Tool Dry/Non-Defect/IMG_1520.jpeg`
- `One Tool Dry/Non-Defect/IMG_1521.jpeg`

## Complete the gate

1. Review all 151 images at useful zoom and mark the CVAT job complete.
2. Export the task as **COCO 1.0**.
3. Save the export as `ml/cvat/new_tray_detection_reviewed.zip`.
4. Tell the agent who reviewed it and that the redesigned-tray detection review
   is complete.

The agent will then validate the export, build the combined old-plus-new
four-class YOLO dataset, retrain from the inherited tray checkpoint, compare
old-tray and redesigned-tray performance, and only then generate model-based
tool crops for defect-model work.
