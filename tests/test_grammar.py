"""Grammar tests for AA-MA milestone/step headings.

RED-first for milestone-grammar-ssot M1. Cases are derived from the real
corpus census in `.claude/dev/active/milestone-grammar-ssot/milestone-grammar-ssot-reference.md`,
not invented: 4 milestone styles + a letter-suffixed variant, 3 step keywords
(`Step` 151 headings, `Task` 128, `Sub-step` 72) and 7 number shapes.

Negatives assert against `split_milestones()` / `split_steps()` rather than the
raw regexes. A flat `re.MULTILINE` pattern cannot see fenced code blocks, so
the fenced case is only satisfiable at function level.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from aa_ma.grammar import (
    MILESTONE_RE,
    STEP_RE,
    split_milestones,
    split_steps,
    strip_fenced_blocks,
)

FENCE = "```"

# --- 15 positive cases -------------------------------------------------------
# (heading, expected_number, expected_title, kind)
POSITIVE_CASES: list[tuple[str, str, str, str]] = [
    # 5 milestone variants
    ("## Milestone 1: Foundation", "1", "Foundation", "milestone"),
    ("## Milestone M1: Foundation", "1", "Foundation", "milestone"),
    ("## M1: Foundation", "1", "Foundation", "milestone"),
    ("## Milestone 1 — Pre-flight checks", "1", "Pre-flight checks", "milestone"),
    ("## Milestone 2a: Fair 3-way re-run", "2a", "Fair 3-way re-run", "milestone"),
    # 3 step keywords
    ("### Step 1.1: Create skeleton", "1.1", "Create skeleton", "step"),
    ("### Task 1.1: Copy command", "1.1", "Copy command", "step"),
    ("### Sub-step 1.1: Cut the branch", "1.1", "Cut the branch", "step"),
    # 7 step number shapes
    ("### Step 3.5.1: Wire six tools", "3.5.1", "Wire six tools", "step"),
    ("### Step 1.11: Eleventh step", "1.11", "Eleventh step", "step"),
    ("### Step 2.7b: Refactor helper", "2.7b", "Refactor helper", "step"),
    ("### Step 1.1.bis: Fixture self-test", "1.1.bis", "Fixture self-test", "step"),
    ("### Step M2.1: Probe adapter", "M2.1", "Probe adapter", "step"),
    ("### Step M2a.1: Add dev dep", "M2a.1", "Add dev dep", "step"),
    ("### Task 1.2b: SCIP symbol grammar", "1.2b", "SCIP symbol grammar", "step"),
]

# --- 9 negative cases --------------------------------------------------------
NEGATIVE_CASES: list[tuple[str, str]] = [
    ("## Summary Counts", "no number"),
    ("## Notes", "no number"),
    ("## Milestone Gate Types", "keyword but no number"),
    ("## 2024 — Retro", "bare digits, no Milestone/M prefix"),
    ("### Result Log", "not a step keyword"),
    ("### Step: no number", "keyword with no number"),
    ("#### Step 1.1: too deep", "H4, not H3"),
    (f"{FENCE}\n## Milestone 1: inside fence\n{FENCE}", "inside a fenced block"),
    ("### Step 1.1-alpha: hyphen suffix", "bare hyphen is not a separator"),
    # §6.8 review found these three: flat regex fence-pairing emitted phantoms.
    (
        f"{FENCE}`md\n## Milestone 9: outer\n{FENCE}\n## Milestone 8: nested\n"
        f"{FENCE}\n## Milestone 7: outer\n{FENCE}`\n",
        "nested fences — inner ``` is content, not a close",
    ),
    (f"~~~\n## Milestone 5: tilde fence\n~~~", "tilde fences are fences too"),
    ("<!--\n## Milestone 9: commented out\n-->", "inside an HTML comment"),
]


@pytest.mark.parametrize(
    ("heading", "number", "title", "kind"),
    POSITIVE_CASES,
    ids=[c[0][:38] for c in POSITIVE_CASES],
)
def test_positive_headings_parse(heading: str, number: str, title: str, kind: str) -> None:
    """Every style observed in the real corpus parses to (number, title)."""
    regex = MILESTONE_RE if kind == "milestone" else STEP_RE
    match = regex.search(heading)
    assert match is not None, f"{heading!r} did not match {kind} grammar"
    assert match.group("number") == number
    assert match.group("title") == title


@pytest.mark.parametrize(
    ("text", "reason"),
    NEGATIVE_CASES,
    ids=[c[1].replace(" ", "-") for c in NEGATIVE_CASES],
)
def test_negative_headings_rejected(text: str, reason: str) -> None:
    """Non-headings yield no blocks. Asserted through the splitters, because
    fence-awareness lives there and not in the regexes."""
    assert split_milestones(text) == [], f"{text!r} parsed as a milestone ({reason})"
    assert split_steps(text) == [], f"{text!r} parsed as a step ({reason})"


def test_match_does_not_span_lines() -> None:
    """`[ \\t]*$` not `\\s*$` — `\\s` eats newlines and makes group(0) run on."""
    match = MILESTONE_RE.search("## Milestone 1: Title   \n\n- Status: PENDING\n")
    assert match is not None
    assert "\n" not in match.group(0)


def test_discover_tasks_does_not_crash_on_real_corpus() -> None:
    """`Milestone 2a` and `Milestone 3.5` exist in the corpus. If
    `Milestone.number` is still `int`, `int("2a")` raises ValueError — which is
    not ParseError, so discover_tasks lets it escape and aa-ma-tui hard-crashes.
    """
    from aa_ma.tui.parser import discover_tasks

    root = Path(__file__).resolve().parents[1]
    tasks = discover_tasks(
        [root / ".claude" / "dev" / "active", root / ".claude" / "dev" / "completed"]
    )
    assert tasks, "expected the repo corpus to yield tasks"


def test_case_counts_are_pinned() -> None:
    """Guards against silently dropping a case to make the suite pass."""
    # `>=` not `==`: this guards against silently DROPPING a case. Pinning
    # equality would also punish legitimately adding one, forcing an unrelated
    # magic-number edit on the next contributor.
    assert len(POSITIVE_CASES) >= 15
    assert len(NEGATIVE_CASES) >= 12


def test_strip_fenced_blocks_removes_fenced_headings() -> None:
    cleaned = strip_fenced_blocks(f"## Milestone 1: real\n{FENCE}\n## Milestone 2: fake\n{FENCE}\n")
    assert "## Milestone 1: real" in cleaned
    assert "## Milestone 2: fake" not in cleaned


def test_split_milestones_returns_number_title_block() -> None:
    text = "preamble\n## Milestone 1: One\nbody one\n## Milestone 2: Two\nbody two\n"
    blocks = split_milestones(text)
    assert [(n, t) for n, t, _ in blocks] == [("1", "One"), ("2", "Two")]
    assert "preamble" not in blocks[0][2]
    assert "body one" in blocks[0][2]
    assert "body two" in blocks[1][2]


def test_split_steps_scoped_to_its_milestone_block() -> None:
    block = "## Milestone 1: One\n### Step 1.1: A\nx\n### Sub-step 1.2: B\ny\n"
    assert [(n, t) for n, t, _ in split_steps(block)] == [("1.1", "A"), ("1.2", "B")]


def test_unterminated_fence_swallows_to_eof() -> None:
    """CommonMark: an unterminated fence runs to end of input."""
    assert split_milestones(f"{FENCE}\n## Milestone 5: unterminated\n") == []


def test_fence_stripping_is_linear_not_quadratic() -> None:
    """Regression guard for the O(n^2) fence scan found in §6.8 security review.

    A language-tagged opener (```python) could open a fence but never close one,
    so the old DOTALL regex drove a scan to EOF from every opener. 78 KiB took
    5.15s through parse_task_dir. Doubling the input must not quadruple the time.
    """
    import time

    def elapsed(reps: int) -> float:
        text = f"{FENCE}python\n" * reps
        start = time.perf_counter()
        strip_fenced_blocks(text)
        return time.perf_counter() - start

    small = elapsed(2000)
    large = elapsed(8000)
    # 4x the input. Quadratic would be ~16x; allow generous headroom for noise.
    assert large < max(small * 8, 0.5), f"superlinear: {small:.4f}s -> {large:.4f}s"
