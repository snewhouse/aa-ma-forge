"""aa_ma.render.coverage.milestone_contract_paths — the predicted set of §6.3 predicted-vs-actual.

code-conventions-impact 10.7. Unlike ``contract_paths`` (Angle 6 check 8), it reads ONE
milestone's Contract, every row verb (a Test row predicts its test file), and exempts
nothing: a test or doc a Contract names is predicted, so it must not read as unpredicted.
"""

from __future__ import annotations

from aa_ma.render.coverage import contract_paths, milestone_contract_paths
from aa_ma.grammar import scan_fences

PLAN = """\
# Plan

### Milestone 1 — First
#### Contract
```
Files:
  Create  src/one.py
```

### Milestone 2 — Second (the one asked for)
#### Contract
```
Audit-Profile: full
Files:
  Modify  src/two.py            # a comment: not/a/path.py
            helper(x) -> int    # a signature line, not a row
  Modify  claude-code/skills/{alpha,beta}/SKILL.md
  Create  scripts/new.sh
  Test    tests/test_two.py
  Modify  docs/spec/x.md, README.md
  Delete  old/gone.py
```
Steps: prose naming `src/prose.py` is not a row.

```
  Modify  src/example_fence_after_prose.py
```

#### Verification amendments (v1, binding)
- prose

### Milestone 2a — Lettered sibling
#### Contract
```
  Modify  src/two_a.py
```

### Milestone 20 — Not milestone 2
#### Contract
```
  Modify  src/twenty.py
```
"""


def test_reads_only_the_named_milestone_every_verb_no_exemptions() -> None:
    assert milestone_contract_paths(PLAN, "2") == [
        "src/two.py",
        "claude-code/skills/alpha/SKILL.md",
        "claude-code/skills/beta/SKILL.md",
        "scripts/new.sh",
        "tests/test_two.py",
        "docs/spec/x.md",
        "README.md",
        "old/gone.py",
    ]


def test_milestone_ids_match_exactly() -> None:
    assert milestone_contract_paths(PLAN, "1") == ["src/one.py"]
    assert milestone_contract_paths(PLAN, "2a") == ["src/two_a.py"]
    assert milestone_contract_paths(PLAN, "20") == ["src/twenty.py"]


def test_absent_milestone_or_contract_is_empty() -> None:
    assert milestone_contract_paths(PLAN, "9") == []
    assert milestone_contract_paths("### Milestone 3 — no contract\nprose\n", "3") == []


def test_unterminated_fence_is_empty() -> None:
    assert (
        milestone_contract_paths(
            "### Milestone 1 — x\n#### Contract\n```\n  Modify a.py\n", "1"
        )
        == []
    )


def test_duplicates_are_dropped_in_order() -> None:
    plan = "### Milestone 1 — x\n#### Contract\n```\n  Modify a.py\n  Test a.py\n  Modify b.py\n```\n"
    assert milestone_contract_paths(plan, "1") == ["a.py", "b.py"]


def test_angle6_contract_paths_unchanged() -> None:
    """--coverage keeps reading Create/Modify only, every milestone, exemptions applied."""
    got = [p for _, p in contract_paths(PLAN, scan_fences(PLAN).stripped)]
    assert "tests/test_two.py" not in got and "docs/spec/x.md" not in got
    assert "old/gone.py" not in got  # Delete is not a Create/Modify row
    assert {"src/one.py", "src/two.py", "src/twenty.py", "scripts/new.sh"} <= set(got)


def test_headings_the_grammar_ssot_accepts_are_read() -> None:
    """§6.6 W3: the heading grammar is aa_ma.grammar's, at any level ``##``-``####``.

    The old private regex took ``Milestone <n>`` only, so ``### M10: …`` and
    ``## Milestone M10 — …`` (both accepted by the gate's grammar) read as no Contract.
    """
    for heading in ("### M10: Short form", "## Milestone M10 — Prefixed"):
        plan = f"{heading}\n#### Contract\n```\n  Modify src/ten.py\n```\n"
        assert milestone_contract_paths(plan, "10") == ["src/ten.py"], heading


def test_a_prose_heading_is_not_a_milestone() -> None:
    plan = "### Milestone graph\n#### Contract\n```\n  Modify src/x.py\n```\n"
    assert milestone_contract_paths(plan, "1") == []
