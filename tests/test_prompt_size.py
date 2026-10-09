"""Prompt files stay small enough to load whole: a size cap with a ratchet, plus TOCs.

The Agent Skills spec (https://agentskills.io/specification, "Progressive disclosure")
says to keep a SKILL.md under 500 lines and move detail into reference files, which the
agent reads on demand. Six skills predate the cap; they are held at their size on
2026-10-09 in ALLOWLIST and split in M5, after which ALLOWLIST is empty. A ceiling may
only fall: raising one is a visible diff in this file.

Lines are counted for the whole file, frontmatter included — the figures the plan
measured (reference.md "Oversized prompt files").

A reference file over 100 lines needs a table of contents, so a reader that previews
the top of the file sees what it holds. The rule binds only files that are new or
modified against the merge-base with origin/main; the ones that predate it sit in
TOC_ALLOWLIST until something touches them.
"""

from __future__ import annotations

import re
import subprocess
import warnings
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN = REPO_ROOT / "claude-code"

MAX_LINES = 500  # Agent Skills spec: "Keep your main SKILL.md under 500 lines"
TOC_THRESHOLD = 100  # lines; a longer reference file needs a table of contents

# path relative to claude-code/ -> ceiling (lines on 2026-10-09). May only fall.
ALLOWLIST = {
    "skills/aa-ma-execution/SKILL.md": 1295,
    "skills/execute-aa-ma-milestone/SKILL.md": 1244,
    "skills/aa-ma-plan/SKILL.md": 1154,
    "skills/sole-dev-merge/SKILL.md": 1057,
    "skills/execute-aa-ma-full/SKILL.md": 758,
    "skills/plan-verification/SKILL.md": 608,
}

# references/*.md over TOC_THRESHOLD lines with no TOC on 2026-10-09 (24).
TOC_ALLOWLIST = frozenset(
    {
        "skills/aa-ma-plan-workflow/references/COMPLEXITY_ROUTING.md",
        "skills/aa-ma-plan-workflow/references/PHASE_0_OPERATIONAL_READINESS.md",
        "skills/aa-ma-plan-workflow/references/PHASE_2_BRAINSTORM.md",
        "skills/aa-ma-plan-workflow/references/PHASE_3_RESEARCH.md",
        "skills/aa-ma-plan-workflow/references/PHASE_4_PLAN_GENERATION.md",
        "skills/aa-ma-plan-workflow/references/PHASE_5_ARTIFACT_CREATION.md",
        "skills/aa-ma-plan-workflow/references/SKILL_INTEGRATION.md",
        "skills/aa-ma-plan-workflow/references/SYNC_PROTOCOL.md",
        "skills/aa-ma-plan-workflow/references/VALIDATION_GATES.md",
        "skills/agent-teams/references/AA_MA_INTEGRATION.md",
        "skills/agent-teams/references/ERROR_RECOVERY.md",
        "skills/agent-teams/references/QUALITY_GATES.md",
        "skills/agent-teams/references/ROLE_TEMPLATES.md",
        "skills/agent-teams/references/SHUTDOWN_PROTOCOL.md",
        "skills/agent-teams/references/TEAM_PATTERNS.md",
        "skills/logging-and-comments/references/python.md",
        "skills/retro/references/output-format.md",
        "skills/understand-codebase/references/AGENTS-MD-TEMPLATE.md",
        "skills/understand-codebase/references/ANALYSIS-CONTRACT.md",
        "skills/understand-codebase/references/DEEPDIVE-TEMPLATES.md",
        "skills/understand-codebase/references/DIMENSIONS.md",
        "skills/understand-codebase/references/ONBOARDING-TEMPLATE.md",
        "skills/understand-codebase/references/REUSE-MAP.md",
        "skills/understand-codebase/references/RULES-FILES.md",
    }
)

PROMPT_GLOBS = ("skills/*/SKILL.md", "agents/*.md")
TOC_HEADING_RE = re.compile(r"^#{1,3} +(table of )?contents\b", re.IGNORECASE | re.M)
ANCHOR_LINK_RE = re.compile(r"\]\(#[^)\s]+\)")
MIN_ANCHOR_LINKS = 3  # a list of 3+ in-file anchor links counts as a TOC


def line_count(text: str) -> int:
    return len(text.splitlines())


def size_error(rel: str, text: str) -> str | None:
    """Return why `text` (the file at claude-code/<rel>) is too long, else None."""
    lines = line_count(text)
    ceiling = ALLOWLIST.get(rel, MAX_LINES)
    if lines > ceiling:
        kind = "ALLOWLIST ceiling" if rel in ALLOWLIST else "cap"
        return f"{rel}: {lines} lines > {kind} {ceiling}; move detail into references/"
    return None


def has_toc(text: str) -> bool:
    return bool(TOC_HEADING_RE.search(text)) or (
        len(ANCHOR_LINK_RE.findall(text)) >= MIN_ANCHOR_LINKS
    )


def _rel(path: Path) -> str:
    return path.relative_to(PLUGIN).as_posix()


def _prompt_files() -> list[Path]:
    return sorted(p for g in PROMPT_GLOBS for p in PLUGIN.glob(g))


def _touched_since_merge_base() -> set[str] | None:
    """claude-code/-relative paths changed vs origin/main's merge-base (None if unknown)."""

    def git(*args: str) -> str:
        # why: fixed argv, no shell; `git` from PATH like every other test here.
        return subprocess.run(
            ["git", "-C", str(REPO_ROOT), *args],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        ).stdout

    try:
        base = git("merge-base", "origin/main", "HEAD").strip()
        names = git("diff", "--name-only", base, "--", "claude-code/").split()
        names += git(
            "ls-files", "--others", "--exclude-standard", "claude-code/"
        ).split()
    except (subprocess.SubprocessError, OSError) as exc:
        warnings.warn(f"TOC touched-check skipped, no merge-base: {exc}", stacklevel=2)
        return None
    return {n.removeprefix("claude-code/") for n in names}


@pytest.mark.parametrize("path", _prompt_files(), ids=_rel)
def test_prompt_file_within_cap(path: Path) -> None:
    error = size_error(_rel(path), path.read_text(encoding="utf-8"))
    assert error is None, error


@pytest.mark.parametrize("rel", sorted(ALLOWLIST))
def test_allowlist_ceilings_track_the_file(rel: str) -> None:
    """A ceiling equals the file's size, so a shrink must lower it in the same diff.

    Without this a file that drops from 1154 to 700 lines could silently regrow to 1154.
    """
    path = PLUGIN / rel
    assert path.is_file(), f"{rel} no longer exists"
    lines = line_count(path.read_text(encoding="utf-8"))
    assert lines > MAX_LINES, (
        f"{rel} is within the {MAX_LINES}-line cap; remove it from ALLOWLIST"
    )
    assert lines == ALLOWLIST[rel], (
        f"{rel} is {lines} lines; set its ALLOWLIST ceiling to {lines}"
    )


def test_one_added_line_breaks_an_allowlisted_ceiling() -> None:
    """Negative control: the ratchet bites at ceiling + 1."""
    rel = "skills/execute-aa-ma-milestone/SKILL.md"
    text = (PLUGIN / rel).read_text(encoding="utf-8")
    padded = "x\n" * (ALLOWLIST[rel] - line_count(text) + 1)
    assert size_error(rel, text + padded) is not None
    assert size_error(rel, text) is None


def test_cap_applies_to_a_file_not_on_the_allowlist() -> None:
    assert size_error("skills/new-skill/SKILL.md", "x\n" * (MAX_LINES + 1))
    assert size_error("skills/new-skill/SKILL.md", "x\n" * MAX_LINES) is None


def test_references_over_threshold_have_a_toc() -> None:
    touched = _touched_since_merge_base()
    missing = []
    for path in sorted(PLUGIN.glob("skills/*/references/*.md")):
        rel, text = _rel(path), path.read_text(encoding="utf-8")
        if line_count(text) <= TOC_THRESHOLD or has_toc(text):
            continue
        if rel not in TOC_ALLOWLIST or (touched is not None and rel in touched):
            missing.append(rel)
    assert not missing, "add a table of contents to: " + ", ".join(missing)


def test_toc_allowlist_entries_still_need_it() -> None:
    for rel in sorted(TOC_ALLOWLIST):
        path = PLUGIN / rel
        assert path.is_file(), f"{rel} no longer exists"
        text = path.read_text(encoding="utf-8")
        assert line_count(text) > TOC_THRESHOLD and not has_toc(text), (
            f"{rel} no longer needs an exemption; remove it from TOC_ALLOWLIST"
        )


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("# Title\n\n## Contents\n- a\n", True),
        ("# Title\n\n## Table of Contents\n", True),
        ("- [A](#a)\n- [B](#b)\n- [C](#c)\n", True),
        ("- [A](#a)\n- [B](#b)\n", False),
        ("# Title\n\nprose only\n", False),
    ],
)
def test_has_toc(text: str, expected: bool) -> None:
    assert has_toc(text) is expected
