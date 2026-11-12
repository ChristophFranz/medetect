"""Focused tests for deterministic inventory and context-integrity checks."""

from __future__ import annotations

import os

from ml.scripts import context_check
from ml.scripts.build_manifest import inventory
from ml.scripts.context_check import sha256, validate_tree


def test_inventory_is_deterministic(tmp_path) -> None:
    (tmp_path / "b.txt").write_text("second\n")
    (tmp_path / "a.txt").write_text("first\n")

    first_records, first_digest = inventory(tmp_path)
    second_records, second_digest = inventory(tmp_path)

    assert first_records == second_records
    assert first_digest == second_digest
    assert [record["path"] for record in first_records] == ["a.txt", "b.txt"]


def test_validate_tree_detects_content_hash_mismatch(tmp_path) -> None:
    asset = tmp_path / "asset.txt"
    asset.write_text("original\n")
    records = [
        {
            "path": "asset.txt",
            "bytes": asset.stat().st_size,
            "sha256": sha256(asset),
        }
    ]
    _, expected_digest = inventory(tmp_path)
    errors: list[str] = []
    validate_tree(tmp_path, records, expected_digest, "fixture", errors)
    assert errors == []

    asset.write_text("modified\n")
    validate_tree(tmp_path, records, expected_digest, "fixture", errors)
    assert any("hash mismatch" in error for error in errors)


def test_snapshot_freshness_detects_stale_state(tmp_path, monkeypatch) -> None:
    snapshot = tmp_path / "CONTEXT_SNAPSHOT.md"
    state = tmp_path / "PROJECT_STATE.md"
    snapshot.write_text("old snapshot\n")
    state.write_text("new state\n")
    os.utime(snapshot, ns=(1, 1))
    os.utime(state, ns=(2, 2))
    monkeypatch.setattr(context_check, "ML_ROOT", tmp_path)
    monkeypatch.setattr(context_check, "SNAPSHOT_INPUTS", [state])

    errors: list[str] = []
    context_check.validate_snapshot_freshness(errors)

    assert errors == [
        "CONTEXT_SNAPSHOT.md is stale; regenerate it with context_snapshot.py"
    ]
