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
from aa_ma.contract_rows import ROW_VERBS, milestone_contract_rows, row_re
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


def test_coverage_builds_both_row_regexes_from_the_one_verb_tuple() -> None:
    assert coverage._ROW_RE.pattern == row_re(("Create", "Modify")).pattern
    assert coverage._ANY_ROW_RE.pattern == row_re(ROW_VERBS).pattern


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
