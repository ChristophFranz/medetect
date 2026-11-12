# MEDetect Agent Handoff

## Required startup sequence

1. Read `ml/CONTEXT_SNAPSHOT.md`.
2. Read `ml/PROJECT_STATE.md` and stop at any pending human gate.
3. Read `ml/DECISIONS.md` before changing data, labels, models, or metrics.
4. Run `conda run -n medetect-ml python ml/scripts/context_check.py`.
5. Regenerate the snapshot after material work with `conda run -n medetect-ml python ml/scripts/context_snapshot.py`.

## Project invariants

- Do not modify the React UI, Supabase code, tray-level YOLO detector, or legacy Desktop source during the ML pilot.
- The ML pilot targets Hook Sinskey defects only until the benchmark human gate approves expansion.
- Raw images, weights, checkpoints, CVAT state, and generated runs remain local and untracked.
- Install Python dependencies with Conda only. Do not use pip, pipx, or uv.
- Preserve the frozen train/validation/test split. Never tune against the test split.
- A healthy image has no defect annotation. A defective image mask covers the affected tip segment.
- Never advance past a human gate until reviewer, date, decision, and next action are recorded in `ml/PROJECT_STATE.md`.
- The pre-existing staged files are user-owned and must not be staged or committed as part of ML work. Stage ML paths explicitly.

## Source locations

- GitHub-connected workspace: `/Users/christophcuan/Desktop/medetect-api/medetect`
- Read-only legacy source: `/Users/christophcuan/Desktop/medetect-api`
- Authoritative pilot dataset candidate: `Hook Sinskey Tip/Tool 2.v4-epoch-200-set.yolov8 3`
- Legacy checkpoint: `Hook Sinskey Tip/runs/detect/train/weights/best.pt`
