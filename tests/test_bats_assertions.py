"""Bats assertions must be able to fail (L-045).

Bats fails a test through bash's errexit, which ignores a command negated with `!`:
`! grep -q x f` on any line but a test's last never fails it. Write `run ! cmd`
(bats >= 1.5, `bats_require_minimum_version 1.5.0`) or a positive `[[ … != … ]]`.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BARE_NEGATION_RE = re.compile(r"^\s*!\s")


def bare_negations(text: str) -> list[int]:
    return [
        n for n, line in enumerate(text.splitlines(), 1) if BARE_NEGATION_RE.match(line)
    ]


def test_no_bare_negation_in_bats_files() -> None:
    hits = [
        f"{p.relative_to(REPO_ROOT)}:{n}"
        for p in sorted((REPO_ROOT / "tests").rglob("*.bats"))
        for n in bare_negations(p.read_text(encoding="utf-8"))
    ]
    assert not hits, (
        "bare `! cmd` never fails a bats test; use `run ! cmd`: " + ", ".join(hits)
    )


def test_bare_negation_detector() -> None:
    assert bare_negations("@test x {\n  ! grep -q a f\n  true\n}\n") == [2]
    assert (
        bare_negations(
            "  run ! grep -q a f\n  if ! true; then false; fi\n  [[ a != b ]]\n"
        )
        == []
    )
