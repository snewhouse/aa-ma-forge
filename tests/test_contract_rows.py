"""aa_ma.contract_rows — one milestone's Contract rows as (verb, path), the gate's predicted set.

code-conventions-impact 11.2. Every row verb, nothing exempt (a test or doc the Contract names
is predicted), sliced to one milestone. The row grammar is shared with
``aa_ma.render.coverage`` (Angle 6 check 8), which keeps its Create/Modify-only reader: both
regexes are built from :data:`aa_ma.contract_rows.ROW_VERBS`.
"""

from __future__ import annotations

import ast
from pathlib import Path

from aa_ma import contract_rows
from aa_ma.contract_rows import (
    ROW_VERBS,
    covers,
    plan_created,
    milestone_contract_lines,
    milestone_contract_rows,
    row_re,
)
from aa_ma.render import coverage

PLAN = """\
# Plan

### Milestone 1 — First
#### Contract
```
Files:
  Create  src/one.py
```

### Milestone 2 — Second
#### Contract
```
Audit-Profile: full
Files:
  Modify  src/two.py            # a comment: not/a/path.py
            helper(x) -> int    # a signature line, not a row
  Modify  claude-code/skills/{alpha,beta}/SKILL.md
  Create  scripts/new.sh
  Test    tests/test_two.py (fixture repos: a, b)
  Modify  docs/spec/x.md, README.md
  Delete  old/gone.py
  Move    old/name.py → new/name.py   (git mv)
  Merge   a/one.md -> a/two.md
  Modify  src/two.py
```
Steps: prose naming `src/prose.py` is not a row.

### Milestone 3 — Template grammar
#### Contract
```python
# file: src/three.py
def f(): ...
```
"""


def test_row_verbs_are_the_contract_grammar() -> None:
    assert ROW_VERBS == ("Create", "Modify", "Test", "Move", "Merge", "Delete")


def test_one_milestone_every_verb_in_order_deduped() -> None:
    assert milestone_contract_rows(PLAN, "2") == [
        ("Modify", "src/two.py"),
        ("Modify", "claude-code/skills/alpha/SKILL.md"),
        ("Modify", "claude-code/skills/beta/SKILL.md"),
        ("Create", "scripts/new.sh"),
        ("Test", "tests/test_two.py"),
        ("Modify", "docs/spec/x.md"),
        ("Modify", "README.md"),
        ("Delete", "old/gone.py"),
        ("Move", "old/name.py"),
        ("Move", "new/name.py"),
        ("Merge", "a/one.md"),
        ("Merge", "a/two.md"),
    ]


def test_template_file_line_reads_as_modify() -> None:
    assert milestone_contract_rows(PLAN, "3") == [("Modify", "src/three.py")]


def test_absent_milestone_no_contract_or_unterminated_fence_is_empty() -> None:
    assert milestone_contract_rows(PLAN, "9") == []
    assert milestone_contract_rows("### Milestone 4 — x\nprose\n", "4") == []
    assert milestone_contract_rows(PLAN + "```\n", "2") == []


def test_coverage_builds_its_row_regex_from_the_verb_tuple() -> None:
    """Angle 6 check 8 reads Create/Modify only; both readers share :func:`row_re`."""
    assert coverage._ROW_RE.pattern == row_re(ROW_VERBS[:2]).pattern
    assert ROW_VERBS[:2] == ("Create", "Modify")


def test_milestone_contract_paths_is_the_rows_paths() -> None:
    assert coverage.milestone_contract_paths(PLAN, "2") == list(
        dict.fromkeys(p for _, p in milestone_contract_rows(PLAN, "2"))
    )


def test_module_imports_only_the_grammar_from_aa_ma() -> None:
    """Direct imports only (lint-imports pins it too): grammar -> plan_parsers is why this module exists."""
    tree = ast.parse(Path(contract_rows.__file__).read_text(encoding="utf-8"))
    from_aa_ma = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("aa_ma")
    } | {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
        if alias.name.startswith("aa_ma")
    }
    assert from_aa_ma == {"aa_ma.grammar"}


def test_contract_lines_are_the_raw_fence_lines_of_one_milestone() -> None:
    """Non-row Contract lines (`API-Break:`, field lines) for fence 4's own readers."""
    lines = milestone_contract_lines(PLAN, "3")
    assert lines == ["# file: src/three.py", "def f(): ..."]
    assert "Audit-Profile: full" in milestone_contract_lines(PLAN, "2")
    assert milestone_contract_lines(PLAN, "9") == []


def test_plan_created_reads_the_front_matter_outside_fences() -> None:
    assert (
        plan_created("# P\nCreated: 2026-10-08\n\n## One\nCreated: 2027-01-01\n")
        == "2026-10-08"
    )
    assert plan_created("# P\n**Created:** 2026-10-08\n") == "2026-10-08"
    assert plan_created("# P\n```\nCreated: 2026-10-08\n```\n## One\n") is None
    assert plan_created("# P\n## One\nCreated: 2026-10-08\n") is None


def test_covers_is_exact_or_beneath_a_directory_row() -> None:
    assert (
        covers("src/a.py", "src/a.py")
        and covers("src/", "src/a.py")
        and covers("src", "src/a.py")
    )
    assert not covers("src/a", "src/ab.py") and not covers("src/a.py", "src/a.py.orig")


def test_coverage_uses_the_shared_created_reader_and_covers() -> None:
    assert coverage.plan_created is plan_created and coverage.covers is covers
