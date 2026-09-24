"""aa_ma.deps — the `Dependencies:` grammar, resolver, Milestone graph and advisory
(diagram-generation M7, map Tickets 7 and 16).

The hazard is the resolver, not the data: two resolvers written during charting reported
30–36 failures on correct data because `MILESTONE_RE` strips a leading `M` while step
numbers keep it (`### Step M2a.1:`). The fixtures below are those shapes; `_naive_strip_m`
is the mutant that proves they are actually covered.

Decisions (context-log 2026-09-24, Ste): the corpus yields ZERO findings — the plan's
"tiktoken" case is `- Dependencies table: …`, not a `Dependencies:` field — and the
surfaces are `python -m aa_ma.deps {graph,check,advisory}`.
"""

from __future__ import annotations

import dataclasses
import glob
import subprocess
import sys
from pathlib import Path

import pytest

from aa_ma import deps
from aa_ma.deps import DepRef, advisory, check, milestone_graph, parse_dependencies, resolve
from aa_ma.grammar import CANONICAL_DEPENDENCY_RE, split_milestones, split_steps
from aa_ma.render.mermaid_lint import lint_text

REPO = Path(__file__).resolve().parents[1]
FIXTURE = (REPO / "tests/fixtures/deps-hazards.md").read_text(encoding="utf-8")
CROSS_PLAN = "Milestone 1; `milestone-grammar-ssot` M5 merged (grammar.split_milestones trailing-H2 fix)"

# The four hazard values (Ticket 16), each exactly as it appears in the fixture.
EXPECTED: dict[str, list[DepRef]] = {
    "Step M1.0": [DepRef("Step M1.0", "step", "M1.0", None)],
    "Step M2a.1": [DepRef("Step M2a.1", "step", "M2a.1", None)],
    "Milestone 2a": [DepRef("Milestone 2a", "milestone", "2a", None)],
    CROSS_PLAN: [
        DepRef("Milestone 1", "milestone", "1", None),
        DepRef("`milestone-grammar-ssot` M5", "cross-plan", "5", "milestone-grammar-ssot"),
    ],
}


def _naive_strip_m(value: str) -> list[DepRef]:
    """The charting-time mutant: normalise every number by stripping `M`."""
    return [
        dataclasses.replace(r, number=r.number.lstrip("M")) if r.number else r
        for r in parse_dependencies(value)
    ]


def _heading_numbers(text: str) -> tuple[set[str], set[str]]:
    blocks = split_milestones(text)
    return {b.number for b in blocks}, {s.number for b in blocks for s in split_steps(b.text)}


# ---------------------------------------------------------------------
# AC1 — hazard fixtures + the naive mutant
# ---------------------------------------------------------------------

@pytest.mark.parametrize("value", list(EXPECTED))
def test_hazard_values_parse_exactly(value: str) -> None:
    assert parse_dependencies(value) == EXPECTED[value]


@pytest.mark.parametrize("value", list(EXPECTED))
def test_hazard_values_resolve_against_the_fixture(value: str) -> None:
    assert resolve(parse_dependencies(value), FIXTURE) == []


def test_expected_numbers_are_the_fixtures_real_heading_numbers() -> None:
    """Ties EXPECTED to the headings, so the mutant's `1.0` is provably not a heading."""
    milestones, steps = _heading_numbers(FIXTURE)
    for refs in EXPECTED.values():
        for r in refs:
            if r.kind == "milestone":
                assert r.number in milestones
            elif r.kind == "step":
                assert r.number in steps


def test_the_naive_mutant_is_caught() -> None:
    wrong = [v for v in EXPECTED if _naive_strip_m(v) != EXPECTED[v]]
    assert wrong, "no hazard fixture distinguishes the naive M-stripping resolver"
    _, steps = _heading_numbers(FIXTURE)
    assert any(r.number not in steps for v in wrong for r in _naive_strip_m(v) if r.kind == "step")


def test_unresolvable_references_are_returned() -> None:
    refs = parse_dependencies("Milestone 9, Step M9.9, Milestone 2")
    assert [(r.kind, r.number) for r in resolve(refs, FIXTURE)] == [("milestone", "9"), ("step", "M9.9")]


# ---------------------------------------------------------------------
# Lenient read of every legacy form (Ticket 7)
# ---------------------------------------------------------------------

@pytest.mark.parametrize(("value", "expected"), [
    ("None", [("none", None)]),
    ("None (can parallelize with 1.1)", [("none", None)]),
    ("None (pre-M4 `[ad-hoc]` housekeeping commit must land first)", [("none", None)]),
    ("Milestone 2", [("milestone", "2")]),
    ("Milestone M2", [("milestone", "2")]),
    ("M2", [("milestone", "2")]),
    ("M2a", [("milestone", "2a")]),
    ("M2 complete, Task 1.1", [("milestone", "2"), ("step", "1.1")]),
    ("M1.1 complete", [("step", "M1.1")]),
    ("Milestones 1, 2, 3", [("milestone", "1"), ("milestone", "2"), ("milestone", "3")]),
    ("Milestones 1-3", [("milestone", "1"), ("milestone", "2"), ("milestone", "3")]),
    ("Steps 1.1–1.3", [("step", "1.1"), ("step", "1.2"), ("step", "1.3")]),
    ("Steps 1.1, 1.2", [("step", "1.1"), ("step", "1.2")]),
    ("Tasks 1.1.1, 1.1.2", [("step", "1.1.1"), ("step", "1.1.2")]),
    ("Task 1.2b", [("step", "1.2b")]),
    ("Sub-step 1.1", [("step", "1.1")]),
    ("Milestone 2, Milestone 3", [("milestone", "2"), ("milestone", "3")]),
    ("Milestone 2 (Milestone 1 recommended, not required)", [("milestone", "2")]),
    ("Task 2.2.1 live verification (which surfaced the defect)", [("step", "2.2.1")]),
    ("Step 1.1 (flag-only leg); Step 1.2 (docs leg)", [("step", "1.1"), ("step", "1.2")]),
    ("Milestone 1; milestone-grammar-ssot M5 merged", [("milestone", "1"), ("cross-plan", "5")]),
    ("Milestone 1, milestone-grammar-ssot Milestone 5", [("milestone", "1"), ("cross-plan", "5")]),
    ("table: tiktoken `latest from PyPI` → `>=0.7`", []),
])
def test_legacy_forms_read_leniently(value: str, expected: list[tuple[str, str | None]]) -> None:
    assert [(r.kind, r.number) for r in parse_dependencies(value)] == expected


# ---------------------------------------------------------------------
# AC2 / AC3 — the corpus: zero findings, identity not ratio
# ---------------------------------------------------------------------

def _corpus() -> list[Path]:
    pats = (".claude/dev/**/*tasks.md", "examples/**/*tasks.md")
    return sorted({Path(p) for pat in pats for p in glob.glob(str(REPO / pat), recursive=True)})


def test_the_corpus_has_no_unresolved_dependency() -> None:
    findings = {str(p.relative_to(REPO)): check(p.read_text(encoding="utf-8")) for p in _corpus()}
    assert {p: f for p, f in findings.items() if f} == {}


def test_the_cross_plan_reference_is_exempt_not_flagged() -> None:
    p = REPO / ".claude/dev/completed/plan-architecture-views/plan-architecture-views-tasks.md"
    text = p.read_text(encoding="utf-8")
    assert "milestone-grammar-ssot M5 merged" in text
    assert check(text) == []
    assert ("cross-plan", "5") in [(r.kind, r.number) for r in parse_dependencies(
        "Milestone 1; milestone-grammar-ssot M5 merged (grammar.split_milestones trailing-H2 fix)")]


def test_dependencies_table_prose_is_not_a_field() -> None:
    """The plan's 'tiktoken' case: a Result Log sub-bullet, not a `Dependencies:` field."""
    as_prose = "## Milestone 1: x\n- Status: PENDING\n  - Dependencies table: tiktoken `latest from PyPI`\n"
    as_field = "## Milestone 1: x\n- Status: PENDING\n- Dependencies: table: tiktoken `latest from PyPI`\n"
    assert check(as_prose) == []
    assert check(as_field) == ["UNRESOLVED_DEPENDENCY Milestone 1: no reference in 'table: tiktoken `latest from PyPI`'"]


def test_check_names_the_owner_and_the_reference() -> None:
    text = FIXTURE.replace("- Dependencies: Step M2.1", "- Dependencies: Step M7.7")
    assert check(text) == ["UNRESOLVED_DEPENDENCY Sub-step M2a.1: Step M7.7"]


@pytest.mark.parametrize("line", [
    "- Dependencies: Milestone 9", "- **Dependencies:** Milestone 9", "**Dependencies**: Milestone 9",
])
def test_check_reads_bold_and_plain_fields(line: str) -> None:
    assert check(f"## Milestone 1: x\n{line}\n") == ["UNRESOLVED_DEPENDENCY Milestone 1: Milestone 9"]


def test_fields_inside_fences_are_not_read() -> None:
    assert check("## Milestone 1: x\n```\n- Dependencies: Milestone 9\n```\n") == []


# ---------------------------------------------------------------------
# Canonical write form (grammar.CANONICAL_DEPENDENCY_RE)
# ---------------------------------------------------------------------

@pytest.mark.parametrize("value", [
    "None", "Milestone 2", "Milestone 2, Milestone 3", "Sub-step 1.1", "Milestone 2, Sub-step 1.1",
    "Milestone 1, milestone-grammar-ssot Milestone 5",
])
def test_canonical_form_accepts(value: str) -> None:
    assert CANONICAL_DEPENDENCY_RE.match(value)


@pytest.mark.parametrize("value", [
    "Step 1.1", "M2", "Milestones 1, 2", "Task 1.1", "milestone 2", "Milestone 2,Milestone 3",
    "None (later)", "Milestone 2a", "", "Milestone 2, ", "milestone-grammar-ssot M5", "grammar Milestone 5",
])
def test_canonical_form_refuses(value: str) -> None:
    assert not CANONICAL_DEPENDENCY_RE.match(value)


# ---------------------------------------------------------------------
# AC4 — Milestone graph, generated into plan §13
# ---------------------------------------------------------------------

GRAPH = """flowchart LR
  M1("Milestone 1: Foundations")
  M2("Milestone 2: Core")
  M2a("Milestone 2a: Core, lettered")
  M3("Milestone 3: Integration")
  M1 --> M2
  M1 --> M2a
  M2 --> M3
  M2a --> M3
"""


def test_milestone_graph_of_the_fixture() -> None:
    assert milestone_graph(FIXTURE) == GRAPH


def test_a_step_reference_at_milestone_level_draws_from_its_milestone() -> None:
    text = "## Milestone 1: A\n### Sub-step 1.1: s\n## Milestone 2: B\n- Dependencies: Sub-step 1.1\n"
    assert "  M1 --> M2\n" in milestone_graph(text)


def test_graph_labels_are_quoted_and_escaped() -> None:
    graph = milestone_graph('## Milestone 1: say "hi" `now`\n- Dependencies: None\n')
    assert '  M1("Milestone 1: say #quot;hi#quot; `now`")\n' in graph


def test_graph_in_section_13_lints_clean(capsys: pytest.CaptureFixture) -> None:
    fixture = REPO / "tests/fixtures/deps-hazards.md"
    assert deps.main(["graph", str(fixture)]) == 0
    view = capsys.readouterr().out
    assert view.startswith("### Milestone graph\n\n```mermaid\nflowchart LR\n")
    plan = (
        "# P\n\n## 13. Architecture View\n\n### Component view\n\n"
        '```mermaid\nflowchart LR\n  A["src/aa_ma/grammar.py"] --> B["src/aa_ma/deps.py"]\n```\n\n'
        f"{view}"
    )
    report = lint_text(plan, REPO)
    assert report.findings == ()
    assert report.render_status != "FAIL"


# ---------------------------------------------------------------------
# AC6 — the advisory (never blocking)
# ---------------------------------------------------------------------

def test_advisory_for_the_fixture() -> None:
    assert advisory(FIXTURE) == "Milestone 3 is ACTIVE but Milestone 2 (Dependencies) is PENDING"


def test_advisory_is_empty_when_dependencies_are_complete() -> None:
    assert advisory(FIXTURE.replace("## Milestone 2: Core\n- Status: PENDING", "## Milestone 2: Core\n- Status: COMPLETE")) == ""


def test_advisory_is_empty_without_an_active_milestone() -> None:
    assert advisory(FIXTURE.replace("- Status: ACTIVE", "- Status: PENDING")) == ""


# ---------------------------------------------------------------------
# python -m aa_ma.deps {graph,check,advisory}
# ---------------------------------------------------------------------

def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "-m", "aa_ma.deps", *args], capture_output=True, text=True, cwd=REPO)


def test_cli_check_exits_1_on_findings(tmp_path: Path) -> None:
    bad = tmp_path / "t-tasks.md"
    bad.write_text("## Milestone 1: x\n- Dependencies: Milestone 9\n")
    r = _run("check", str(bad))
    assert (r.returncode, r.stdout) == (1, "UNRESOLVED_DEPENDENCY Milestone 1: Milestone 9\n")
    assert _run("check", "tests/fixtures/deps-hazards.md").returncode == 0


def test_cli_advisory_always_exits_0() -> None:
    r = _run("advisory", "tests/fixtures/deps-hazards.md")
    assert (r.returncode, r.stdout) == (0, "Milestone 3 is ACTIVE but Milestone 2 (Dependencies) is PENDING\n")


@pytest.mark.parametrize("args", [(), ("graph",), ("nope", "x"), ("graph", "/no/such/tasks.md")])
def test_cli_usage_errors_exit_2(args: tuple[str, ...]) -> None:
    assert _run(*args).returncode == 2


# ---------------------------------------------------------------------
# §6.8 M7 review fixes (Ste: CRITICAL accepted, "Fix all now")
# ---------------------------------------------------------------------

import time  # noqa: E402

from aa_ma import grammar  # noqa: E402

_PAD = 50_000


@pytest.mark.parametrize("line", [
    " " * _PAD + "x",
    "- Dependencies: x" + " " * _PAD + "y",
    "- Status: ACTIVE" + " " * _PAD,
])
def test_field_reads_are_linear_on_padded_lines(line: str) -> None:
    """security-auditor: `[ \\t]*-?[ \\t]*` + lazy value was quadratic (14 s at 50k)."""
    text = f"## Milestone 1: x\n{line}\n## Milestone 2: y\n- Status: ACTIVE\n- Dependencies: Milestone 1\n"
    start = time.perf_counter()
    check(text)
    advisory(text)
    assert time.perf_counter() - start < 0.5


def test_a_huge_range_is_not_expanded() -> None:
    start = time.perf_counter()
    refs = parse_dependencies("Milestones 1-99999999")
    assert time.perf_counter() - start < 0.5
    assert [r.number for r in refs] == ["1", "99999999"]
    assert check("## Milestone 1: x\n- Dependencies: Milestones 1-99999999\n") == [
        "UNRESOLVED_DEPENDENCY Milestone 1: 99999999"
    ]


def test_a_range_within_the_cap_still_expands() -> None:
    assert len(parse_dependencies(f"Milestones 1-{deps.MAX_SPAN + 1}")) == deps.MAX_SPAN + 1


def test_cli_check_caps_its_output(tmp_path: Path) -> None:
    bad = tmp_path / "t-tasks.md"
    many = ", ".join(f"Milestone {n}" for n in range(100, 100 + deps.MAX_FINDINGS + 7))
    bad.write_text(f"## Milestone 1: x\n- Dependencies: {many}\n")
    r = _run("check", str(bad))
    lines = r.stdout.splitlines()
    assert r.returncode == 1 and len(lines) == deps.MAX_FINDINGS + 1
    assert lines[-1] == "… 7 more UNRESOLVED_DEPENDENCY findings"


@pytest.mark.parametrize(("value", "expected"), [
    ("see docs/M2.md", []),
    ("Milestone 2, and 3", [("milestone", "2"), ("milestone", "3")]),
])
def test_parser_edge_shapes(value: str, expected: list[tuple[str, str]]) -> None:
    assert [(r.kind, r.number) for r in parse_dependencies(value)] == expected


@pytest.mark.parametrize("line", ["- Status: ACTIVE", "  -  **Status:** ACTIVE  ", "**Status**: ACTIVE\r", "-Status: ACTIVE"])
def test_shared_field_pattern_reads_every_bullet_and_bold_form(line: str) -> None:
    m = grammar.field_pattern("Status").search(line)
    assert m and m.group(1) == "ACTIVE"


def test_tui_and_deps_share_one_field_pattern() -> None:
    from aa_ma.tui import parser as tui_parser

    assert not hasattr(tui_parser, "_field_pattern")
    assert not hasattr(deps, "_field_re")


def test_own_text_is_one_helper_for_gate_and_deps() -> None:
    from aa_ma import gate

    [b] = [b for b in split_milestones(FIXTURE) if b.number == "2"]
    assert grammar.own_text(b) == b.text[: b.text.index("### Step M2.1")]
    assert not hasattr(gate, "_own_text") and not hasattr(deps, "_head")


def test_graph_labels_escape_angle_brackets() -> None:
    assert '  M1("Milestone 1: a #lt;b#gt; c")\n' in milestone_graph("## Milestone 1: a <b> c\n")
