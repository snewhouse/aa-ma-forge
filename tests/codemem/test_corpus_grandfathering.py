"""Corpus test: parser must not false-positive against existing completed plans.

This test reads every completed AA-MA plan's `-tasks.md` file in
`.claude/dev/completed/` and runs both parsers across each milestone block.
All completed plans are pre-v0.8.0 (no `Audit-Profile:` field exists), so
the parser must report `(None, True, None)` — absence = valid (handled by
grandfathering in plan-verification Angle 6).

Any pre-existing `TDD-Waiver:` values (unlikely in pre-v0.8.0 corpus but
possible) must already be canonical, since check #5 fires regardless of
`Created:` date.

This guards against parser regressions that would falsely flag historical
plans during the v0.8.0 cutover transition.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from aa_ma.plan_parsers import parse_audit_profile, parse_tdd_waiver

PROJECT_ROOT = Path(__file__).resolve().parents[2]
COMPLETED_DIR = PROJECT_ROOT / ".claude" / "dev" / "completed"


def _list_completed_tasks_files() -> list[Path]:
    """Return every `*-tasks.md` file in `.claude/dev/completed/`."""
    if not COMPLETED_DIR.exists():
        return []
    return sorted(COMPLETED_DIR.glob("*/*-tasks.md"))


def _split_milestones(tasks_md_text: str) -> list[str]:
    """Split a tasks.md file into individual milestone blocks.

    Accepts both heading conventions seen in the corpus:
      - Long form: `## Milestone 1: Title`
      - Short form: `## M1: Title`
    """
    blocks: list[str] = []
    matches = list(
        re.finditer(
            r"^## (?:Milestone\s+)?M?\d+(?:\.\d+)?:.+?$",
            tasks_md_text,
            re.MULTILINE,
        )
    )
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(tasks_md_text)
        blocks.append(tasks_md_text[start:end])
    return blocks


@pytest.mark.parametrize("tasks_file", _list_completed_tasks_files(), ids=lambda p: p.parent.name)
def test_audit_profile_absence_is_valid_for_pre_v080_corpus(tasks_file: Path) -> None:
    """For every milestone in every completed plan, `Audit-Profile:` is absent → (None, True, None)."""
    text = tasks_file.read_text(encoding="utf-8")
    milestones = _split_milestones(text)
    assert milestones, f"No milestones found in {tasks_file} — possible parser issue"
    for i, block in enumerate(milestones, start=1):
        value, is_valid, error = parse_audit_profile(block)
        # Pre-v0.8.0 plans have NO Audit-Profile field; parser should report None+valid.
        # If a future plan adds it pre-cutover (unexpected), the value must still be canonical.
        if value is None:
            assert is_valid is True, f"{tasks_file}:M{i} absent field flagged invalid: {error}"
        else:
            assert is_valid is True, (
                f"{tasks_file}:M{i} has non-canonical Audit-Profile={value!r}: {error}"
            )


@pytest.mark.parametrize("tasks_file", _list_completed_tasks_files(), ids=lambda p: p.parent.name)
def test_tdd_waiver_canonical_or_absent_for_corpus(tasks_file: Path) -> None:
    """For every milestone in every completed plan, `TDD-Waiver:` is absent OR canonical."""
    text = tasks_file.read_text(encoding="utf-8")
    milestones = _split_milestones(text)
    for i, block in enumerate(milestones, start=1):
        value, is_valid, error = parse_tdd_waiver(block)
        # Field absence is always valid; presence must be canonical.
        assert is_valid is True, (
            f"{tasks_file}:M{i} has non-canonical TDD-Waiver={value!r}: {error}"
        )


def test_corpus_is_non_empty() -> None:
    """Sanity check: the corpus exists and has at least one completed plan."""
    files = _list_completed_tasks_files()
    assert len(files) > 0, (
        "No completed plans found in .claude/dev/completed/ — "
        "this test only makes sense after at least one plan has shipped"
    )
