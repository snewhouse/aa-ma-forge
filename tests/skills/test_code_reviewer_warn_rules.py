"""code-reviewer carries the comment-substance WARN rules (code-conventions-impact M6, T8).

The rules are advisory: each is a WARNING, never a CRITICAL, so review substance never
blocks the §7.3 approval. The style-nit ban stays, so naming and comment *style* are
still out of scope; what a comment says is not style.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

AGENT = (
    Path(__file__).resolve().parents[2] / "claude-code" / "agents" / "code-reviewer.md"
)
SECTION = "## Comment and docstring substance (WARNING only)"


def _section() -> str:
    text = AGENT.read_text(encoding="utf-8")
    assert SECTION in text
    return text.split(SECTION, 1)[1].split("\n## ", 1)[0]


@pytest.mark.parametrize(
    "rule",
    [
        "what-comment",
        "missing why",
        "docstring claim",
        "unjustified suppression",
        "unexplained imperative",
    ],
)
def test_warn_rule_present(rule: str) -> None:
    assert f"WARNING [{rule}]" in _section()


def test_section_never_raises_critical() -> None:
    assert "CRITICAL" not in _section().replace("never CRITICAL", "")


def test_magic_constants_warn_at_any_count() -> None:
    text = AGENT.read_text(encoding="utf-8")
    assert "3+ occurrences" not in text
    assert re.search(r"any count", text)


def test_style_nit_ban_kept() -> None:
    assert (
        "Stylistic preferences without empirical impact (variable naming, comment style)"
        in AGENT.read_text(encoding="utf-8")
    )


def test_magic_constants_reported_once() -> None:
    # why: pattern 5 owns them; a second bullet double-counts one literal in SUMMARY.
    assert "WARNING [magic constant]" not in _section()


def test_low_budget_keeps_the_substance_section() -> None:
    text = AGENT.read_text(encoding="utf-8")
    low = next(line for line in text.splitlines() if "AA_MA_AUDIT_BUDGET=low" in line)
    assert "Comment and docstring substance" in low
