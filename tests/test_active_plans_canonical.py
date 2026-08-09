"""Strict-writer lint: new plans must use the single canonical heading form.

The reader (`aa_ma.grammar`) is deliberately tolerant — the archived corpus
accumulated four milestone styles and three step keywords before it existed, and
those archives are frozen. The writer is not tolerant: anything under
`.claude/dev/active/` is being authored now and must use one form.

Candidate selection matters. A heading is a *candidate* only if the tolerant
grammar recognises it; a candidate is a *violation* only if it is not also
canonical. Without that rule a plain `## Summary Counts` heading would be
flagged and this plan's own tasks.md would fail.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from aa_ma.grammar import find_non_canonical, iter_fenced_blocks, split_milestones

REPO_ROOT = Path(__file__).resolve().parents[1]
ACTIVE_DIR = REPO_ROOT / ".claude" / "dev" / "active"
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "canonical" / "malformed-task"


def _active_tasks_files() -> list[Path]:
    """Every tasks.md under .claude/dev/active/, excluding git worktrees."""
    if not ACTIVE_DIR.exists():
        return []
    return sorted(p for p in ACTIVE_DIR.glob("*/*-tasks.md") if ".worktrees" not in p.parts)


@pytest.mark.parametrize(
    "tasks_file", _active_tasks_files(), ids=lambda p: p.parent.name
)
def test_active_plans_use_canonical_headings(tasks_file: Path) -> None:
    """Active plans use `## Milestone N: Title` / `### Sub-step N.N: Title`."""
    text = tasks_file.read_text(encoding="utf-8")
    # Anti-vacuity: a tasks.md whose headings the tolerant reader cannot see at
    # all yields zero violations while being invisible to the TUI and to the
    # HARD-gate scans. Zero violations must mean "canonical", not "unparsed".
    milestones = split_milestones(text)
    assert milestones, (
        f"{tasks_file} parsed to ZERO milestones — the lint would pass it "
        "vacuously while aa-ma-tui shows nothing."
    )
    violations = find_non_canonical(text)
    assert not violations, (
        f"{tasks_file} has non-canonical headings:\n  "
        + "\n  ".join(violations)
        + "\n\nCompleted plans are grandfathered; active ones are not."
    )


def test_lint_rejects_the_malformed_fixture() -> None:
    """Meta-test: the lint must actually catch what it claims to.

    A test that passes on an empty `active/` proves nothing — this is what
    proves the lint works. Separate test rather than a failing one, because a
    test that fails cannot live in the suite.
    """
    text = (FIXTURE / "malformed-task-tasks.md").read_text(encoding="utf-8")
    violations = find_non_canonical(text)
    assert len(violations) == 4, f"expected 4 violations, got {len(violations)}: {violations}"
    assert any("## M1:" in v for v in violations)
    assert any("## Milestone M2:" in v for v in violations)
    assert any("Em-dash" in v for v in violations)
    assert any("### Task 1.1:" in v for v in violations)
    # Canonical headings and non-headings must NOT be flagged.
    assert not any("Milestone 4" in v for v in violations)
    assert not any("Sub-step 4.1" in v for v in violations)
    assert not any("Summary Counts" in v for v in violations)


# Every shipped file that TEACHES or EMITS a tasks.md heading. Derived list kept
# explicit so a new writer fails loudly (see test_writer_list_is_complete).
WRITER_TEMPLATES = [
    "docs/templates/tasks-template.md",
    "docs/spec/aa-ma-team-guide.md",
    "docs/spec/aa-ma-specification.md",
    "claude-code/agents/aa-ma-scribe.md",
    "claude-code/commands/aa-ma-plan.md",
    "claude-code/commands/execute-aa-ma-milestone.md",
    "claude-code/skills/aa-ma-plan-workflow/references/PHASE_5_ARTIFACT_CREATION.md",
    "claude-code/skills/aa-ma-execution/SKILL.md",
    "claude-code/rules/aa-ma.md",
    "README.md",
]

_PLACEHOLDER_RE = re.compile(r"^(#{2,3} (?:Milestone|Sub-step|Step|Task)) N(?:\.[MN0-9])?:", re.MULTILINE)


def _normalise_placeholders(text: str) -> str:
    """Turn `N` / `N.M` placeholders into real digits so the regexes can judge shape."""
    text = _PLACEHOLDER_RE.sub(lambda m: f"{m.group(1)} 1.1:", text)
    return text.replace("## Milestone 1.1:", "## Milestone 1:")


def _violations_everywhere(text: str) -> list[str]:
    """Lint the tasks.md templates a writer file contains.

    Two rules, both learned the hard way:

    * **Lint inside the fences.** These files hold their templates in
      ```markdown blocks, which `sanitize()` strips — so linting the sanitized
      text checks nothing. The §6.8 review mutation-tested the first version of
      this helper and found 4 of 5 writer checks inert.
    * **Lint ONLY inside the fences** when fences exist. A documentation file's
      own section headings (`### Step 3: Dispatch agents`) are prose, not
      tasks.md content, and the tolerant reader cannot tell them apart. Files
      with no fences (a bare template like `tasks-template.md`) are templates in
      their entirety, so lint the whole thing.
    """
    normalised = _normalise_placeholders(text)
    blocks = iter_fenced_blocks(normalised)
    if not blocks:
        return find_non_canonical(normalised)
    found: list[str] = []
    for block in blocks:
        found += find_non_canonical(block)
    return found


@pytest.mark.parametrize("rel_path", WRITER_TEMPLATES)
def test_shipped_writers_emit_canonical_headings(rel_path: str) -> None:
    """Every writer of tasks.md emits the form the lint accepts."""
    text = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
    violations = _violations_everywhere(text)
    assert not violations, (
        f"{rel_path} writes non-canonical headings the lint rejects:\n  " + "\n  ".join(violations)
    )


@pytest.mark.parametrize("rel_path", WRITER_TEMPLATES)
def test_writer_check_is_not_vacuous(rel_path: str) -> None:
    """Mutation guard: corrupting the file MUST produce a violation.

    Without this, a writer whose headings are invisible to the checker passes
    green forever and nobody notices the guard stopped guarding.
    """
    text = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
    corrupted = text.replace("### Sub-step ", "### Task ").replace("## Milestone ", "## M")
    assert _violations_everywhere(corrupted), (
        f"{rel_path}: corrupting every heading produced NO violation — "
        "this file contributes zero coverage and the guard is inert."
    )


def test_active_dir_scan_is_not_vacuous() -> None:
    """The parametrized lint above silently skips when `active/` is empty.

    Mirrors `tests/codemem/test_corpus_grandfathering.py::test_corpus_is_non_empty`.
    Without it, archiving the last plan turns the whole lint into a green no-op
    and nobody notices until a new plan lands.
    """
    if not _active_tasks_files():
        pytest.skip(
            "No active plans — lint is inert until one exists. This skip is the "
            "signal; the parametrized test above would show nothing at all."
        )
    assert _active_tasks_files()
