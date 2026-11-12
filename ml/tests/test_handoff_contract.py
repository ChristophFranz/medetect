"""Contract test for recovery using only the two designated entry-point files."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_two_file_handoff_identifies_state_and_next_command() -> None:
    agents = (REPO_ROOT / "AGENTS.md").read_text()
    snapshot = (REPO_ROOT / "ml/CONTEXT_SNAPSHOT.md").read_text()
    handoff = agents + "\n" + snapshot

    required_facts = (
        "ml/hook-sinskey-benchmark-pilot",
        "Current milestone: 5",
        "Status: new-tray-only v4 confirmatory benchmark complete; awaiting human review",
        "conda run -n medetect-ml python ml/scripts/context_check.py",
        "Do not modify the React UI",
        "Never tune against the test split",
        "aab031079814138d9f4137b007c3eeebcac3291e94ab7fbcfddfa5e2e2370ad2",
        "771a2e13e818ac6c6d70a06c9b9973b5fd701a415373f0dc265b20e37c1eb74e",
    )
    for fact in required_facts:
        assert fact in handoff
