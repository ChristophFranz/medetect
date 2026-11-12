# Milestone 1 Review — Persistent Context Management

Status: approved by Christoph on 2026-09-24.

## Two-file recovery contract

A fresh person or agent starts with only:

1. `AGENTS.md`
2. `ml/CONTEXT_SNAPSHOT.md`

Together they identify the active branch, current milestone and gate, preserved user changes, project invariants, source locations, dataset/checkpoint hashes, historical YOLO baseline, and the exact next command:

```sh
conda run -n medetect-ml python ml/scripts/context_check.py
```

The snapshot embeds the full current project state, so chat history is not required to discover the blocker or next action. `AGENTS.md` then routes deeper work to the append-only decisions, manifest, and project-state files.

## Persistent records

- `AGENTS.md`: mandatory startup sequence and invariants.
- `ml/PROJECT_STATE.md`: active milestone, blocker, last verified work, next action, and all human gates.
- `ml/DECISIONS.md`: append-only technical and governance decisions.
- `ml/data/manifest.json`: source paths, complete per-file hashes, split membership/counts, checkpoint provenance, and review state.
- `ml/experiments/registry.jsonl`: machine-readable lifecycle and future experiment records.
- `ml/CONTEXT_SNAPSHOT.md`: generated compact handoff.

## Commands and checks

- Snapshot regeneration: `conda run -n medetect-ml python ml/scripts/context_snapshot.py`
- Integrity validation: `conda run -n medetect-ml python ml/scripts/context_check.py`

The integrity command checks:

- Required handoff files and local-only artifacts exist.
- Dataset and checkpoint hashes still match both the manifest and Desktop originals.
- Dataset file inventories have no missing or unexpected files.
- The Conda-only policy remains intact.
- The recorded branch and state date are current.
- The context snapshot is newer than its source records.
- Experiment-registry lines are valid JSON.
- Raw images and weights have not entered Git.
- The active human gate is explicitly reported when incomplete.

Automated tests cover deterministic inventory generation, changed-content hash detection, stale-snapshot detection, and the two-file recovery contract.

## Current boundary

Milestone 0 is approved. Milestone 1 is the active pending gate. No SAM2/CVAT annotation work, mask generation, model training, test-set evaluation, UI integration, or remote push has started.

## Human gate

Christoph approved the two-file recovery contract on 2026-09-24. The recorded next action is the Milestone 2 annotation-policy sample.
