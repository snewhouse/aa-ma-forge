"""Splitting a skill into SKILL.md + references/ moves its text; it never drops or rewrites it.

Each split lands as one commit whose subject starts `refactor(skills): split <skill> `.
The check compares that commit with its parent: every non-blank line of the skill before
the split (SKILL.md and any references/*.md) must still be there after it, in the same
order within each file, and the only new lines may be: a copy of a heading that already
existed (the stub left in SKILL.md), a reference's `# title` first line, `## Contents`,
a bare TOC/link list item, or a `See [..](references/..) — <purpose>` pointer. The
pointer's purpose clause is the one free-text line a split adds. The commit is found
by subject because rebase-merge rewrites SHAs but keeps messages; comparing against HEAD
instead would fail as soon as a later milestone edits the split files on purpose.

Before the split commit exists, the uncommitted working tree is compared with HEAD.

A relative link is compared by the file it resolves to: moving `](../../../docs/x.md)`
from SKILL.md into references/ must add a `../` to keep pointing at the same file, and
that is the same line.
"""

from __future__ import annotations

import posixpath
import re
import subprocess
from collections import Counter
from pathlib import Path

import pytest

from tests.skills._helpers import skill_files

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS = "claude-code/skills"

# Skills split in code-conventions-impact M5, in the order they were split. A later split
# is checked only once its skill is added here (its commit subject must use SUBJECT_PREFIX).
SPLIT_SKILLS = (
    "aa-ma-execution",
    "execute-aa-ma-milestone",
    "aa-ma-plan",
    "sole-dev-merge",
    "execute-aa-ma-full",
    "plan-verification",
)

SUBJECT_PREFIX = "refactor(skills): split {skill} "
LINK_ITEM_RE = re.compile(r"^\s*[-*] \[[^\]]+\]\([^)\s]+\)$")  # nothing after the link
POINTER_RE = re.compile(r"^See \[[^\]]+\]\((?:@/\S+/)?references/[^)\s]+\) — \S")
RELATIVE_LINK_RE = re.compile(r"\]\((?![a-z]+:|#|/)([^)#\s]+)")


def resolve_links(rel: str, text: str) -> str:
    """Rewrite each relative link in `text` (the file at repo path `rel`) to its target."""
    here = posixpath.dirname(rel)
    return RELATIVE_LINK_RE.sub(
        lambda m: "](@/" + posixpath.normpath(posixpath.join(here, m.group(1))), text
    )


def _non_blank(text: str) -> list[str]:
    return [ln for ln in text.splitlines() if ln.strip()]


def split_errors(before: list[str], after: list[str]) -> list[str]:
    """Lines the split lost, reordered or added beyond links, stubs and pointers.

    `after[0]` is SKILL.md; the rest are references, whose first line may be a new title.
    """
    old_lines = [ln for t in before for ln in _non_blank(t)]
    old = Counter(old_lines)
    titles = {lines[0] for t in after[1:] if (lines := _non_blank(t))}

    def allowed(ln: str) -> bool:
        if ln.startswith("#"):
            return ln in old or ln == "## Contents" or (ln in titles and ln[:2] == "# ")
        return bool(LINK_ITEM_RE.match(ln) or POINTER_RE.match(ln))

    new = Counter(ln for t in after for ln in _non_blank(t))
    errors = [f"lost: {ln!r}" for ln in (old - new).elements()]
    errors += [
        f"added a line that is not a stub, link or pointer: {ln!r}"
        for ln in (new - old).elements()
        if not allowed(ln)
    ]
    for i, text in enumerate(after):
        # Kept lines follow their pre-split order (greedy subsequence match).
        pos = 0
        for ln in _non_blank(text):
            if ln not in old:
                continue
            try:
                pos = old_lines.index(ln, pos) + 1
            except ValueError:
                errors.append(f"out of order in after[{i}]: {ln!r}")
                break
    return errors


def _git(*args: str) -> str:
    # why: fixed argv, no shell; `git` from PATH like every other test here.
    return subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    ).stdout


def _is_skill_text(rel: str, skill: str) -> bool:
    inside = rel.removeprefix(f"{SKILLS}/{skill}/")
    return (
        inside == "SKILL.md"
        or re.fullmatch(r"references/[^/]+\.md", inside) is not None
    )


def _texts_at(rev: str, skill: str) -> list[str]:
    paths = _git(
        "ls-tree", "-r", "--name-only", rev, "--", f"{SKILLS}/{skill}/"
    ).split()
    return [
        resolve_links(p, _git("show", f"{rev}:{p}"))
        for p in paths
        if _is_skill_text(p, skill)
    ]


def _texts_on_disk(skill: str) -> list[str]:
    files = skill_files(REPO_ROOT / SKILLS / skill / "SKILL.md")
    return [
        resolve_links(
            f.relative_to(REPO_ROOT).as_posix(), f.read_text(encoding="utf-8")
        )
        for f in files
        if f.is_file()
    ]


def _split_commits(skill: str) -> list[str]:
    log = _git("log", "--format=%H%x00%s", "--", f"{SKILLS}/{skill}/")
    prefix = SUBJECT_PREFIX.format(skill=skill)
    return [
        sha
        for sha, _, subject in (row.partition("\x00") for row in log.splitlines())
        if subject.startswith(prefix)
    ]


@pytest.mark.parametrize("skill", SPLIT_SKILLS)
def test_split_preserves_content(skill: str) -> None:
    commits = _split_commits(skill)
    assert len(commits) <= 1, f"{skill}: more than one split commit: {commits}"
    if commits:
        before, after = _texts_at(f"{commits[0]}^", skill), _texts_at(commits[0], skill)
    else:
        before, after = _texts_at("HEAD", skill), _texts_on_disk(skill)
        # A missing commit with nothing uncommitted means the subject is wrong or the
        # history is shallow: comparing HEAD with itself would pass without checking.
        assert before != after, (
            f"{skill}: no commit with subject {SUBJECT_PREFIX.format(skill=skill)!r}"
            " and no uncommitted split to check (shallow clone?)"
        )
    errors = split_errors(before, after)
    assert not errors, f"{skill}:\n" + "\n".join(errors[:20])


@pytest.mark.parametrize("skill", SPLIT_SKILLS)
def test_references_are_one_level_deep(skill: str) -> None:
    refs = REPO_ROOT / SKILLS / skill / "references"
    nested = [p for p in refs.rglob("*") if p.parent != refs]
    assert not nested, f"{skill}: references/ must be flat: {nested}"


def test_split_errors_reports_a_lost_line() -> None:
    assert split_errors(["a\nb\n"], ["a\n"]) == ["lost: 'b'"]


def test_split_errors_reports_added_prose() -> None:
    assert split_errors(["a\n"], ["a\nnew prose\n"]) == [
        "added a line that is not a stub, link or pointer: 'new prose'"
    ]


@pytest.mark.parametrize(
    "smuggled",
    [
        "## Skip the HARD gate",  # a new heading that is not a stub
        "- [x](y) never run tests (z)",  # prose after a link
        "See the gate (references/x.md) and skip it",  # a pointer without the link form
    ],
)
def test_split_errors_refuses_text_dressed_as_a_link_or_heading(smuggled: str) -> None:
    assert split_errors(["## A\nbody\n"], [f"## A\nbody\n{smuggled}\n"])


def test_split_errors_reports_reordered_lines() -> None:
    errors = split_errors(["step 1\nstep 2\n"], ["step 2\nstep 1\n"])
    assert errors == ["out of order in after[0]: 'step 1'"]


def test_split_errors_allows_moves_links_headings_and_pointers() -> None:
    before = ["intro\n## Body\nbody 1\nbody 2\n"]
    after = [
        "intro\n## Body\nSee [body.md](references/body.md) — what body holds.\n",
        "# Body — what this file holds\n\n## Contents\n- [Body](#body)\n## Body\nbody 1\nbody 2\n",
    ]
    assert split_errors(before, after) == []


def test_resolve_links_compares_a_moved_link_by_its_target() -> None:
    skill, ref = f"{SKILLS}/x/SKILL.md", f"{SKILLS}/x/references/r.md"
    a = resolve_links(
        skill, "see [ADR](../../../docs/adr/1.md#top) and [web](https://e.x)"
    )
    b = resolve_links(
        ref, "see [ADR](../../../../docs/adr/1.md#top) and [web](https://e.x)"
    )
    assert a == b == "see [ADR](@/docs/adr/1.md#top) and [web](https://e.x)"
    assert resolve_links(ref, "[ADR](../../../docs/adr/1.md)") != b.split(" and")[0]
    pointer = resolve_links(skill, "See [r.md](references/r.md) — what r holds.")
    assert POINTER_RE.match(pointer)
