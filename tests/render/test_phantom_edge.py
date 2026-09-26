"""`PHANTOM_EDGE` — opt-in sigil edges checked against the derived graph (diagram-generation M8).

Ticket 5: an edge is checked ONLY when its label carries a reserved sigil
(`-->|"@import"|`). Unlabelled and prose-labelled edges are never checked and never
reported. Anything unevaluable is `UNKNOWN` + a reason and never changes the exit code
(L-012: UNKNOWN is never PASS). Plugin sigils are recognised but UNKNOWN until the index
carries plugin-surface edges (Ste 2026-09-24).
"""

from __future__ import annotations

import glob
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from aa_ma.render import cli, mermaid_lint
from aa_ma.render.mermaid_lint import lint_text
from codemem.indexer import build_index

REPO = Path(__file__).resolve().parents[2]
_LINEAR_BUDGET_S = 1.0  # generous: the quadratic forms measured 15 s at the same sizes
FIXTURE = (REPO / "tests/fixtures/sigil-edges.md").read_text(encoding="utf-8")


@pytest.fixture(autouse=True)
def _no_render(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mermaid_lint, "render_check", lambda sources, **kw: "UNKNOWN")


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def _build(root: Path) -> None:
    build_index(root, root / ".codemem/index.db", package=".")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "r"
    (root / "src/app").mkdir(parents=True)
    (root / "scripts").mkdir()
    (root / "claude-code/skills/x").mkdir(parents=True)
    (root / ".gitignore").write_text(".codemem/\n")
    (root / "src/app/__init__.py").write_text("")
    (root / "src/app/a.py").write_text("from app.b import helper\n\ndef run():\n    return helper()\n")
    (root / "src/app/b.py").write_text("def helper():\n    return 1\n")
    # A second importer: deleting a.py's import must not leave Python with no edges at all.
    (root / "src/app/c.py").write_text("from app.b import helper\n\ndef go():\n    return helper()\n")
    (root / "scripts/run.sh").write_text("#!/bin/sh\n")
    (root / "claude-code/skills/x/SKILL.md").write_text("# x\n")
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    _git(root, "-c", "user.name=t", "-c", "user.email=t@t", "add", "-A")
    _git(root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init")
    _build(root)
    return root


def _codes(report) -> list[str]:
    return [f.code for f in report.findings]


def _line_of(text: str, needle: str) -> int:
    return next(i for i, line in enumerate(text.split("\n"), 1) if needle in line)


# ---------------------------------------------------------------------
# AC1-AC4 — the fixture
# ---------------------------------------------------------------------

def test_true_sigil_edges_yield_no_finding(repo: Path) -> None:
    report = lint_text(FIXTURE, repo)
    assert "PHANTOM_EDGE" not in _codes(report)


def test_deleting_the_import_yields_exactly_one_phantom_edge(repo: Path) -> None:
    (repo / "src/app/a.py").write_text("def run():\n    return 1\n")
    _build(repo)
    report = lint_text(FIXTURE, repo)
    phantoms = [f for f in report.findings if f.code == "PHANTOM_EDGE"]
    assert len(phantoms) == 2  # the @import AND the @call claim are both now false
    assert [f.line for f in phantoms] == [
        _line_of(FIXTURE, 'A -->|"@import"| B'), _line_of(FIXTURE, 'A -->|"@call"| B'),
    ]
    assert "src/app/a.py" in phantoms[0].message and "src/app/b.py" in phantoms[0].message


def test_only_the_import_claim_when_only_the_import_is_claimed(repo: Path) -> None:
    (repo / "src/app/a.py").write_text("def run():\n    return 1\n")
    _build(repo)
    text = FIXTURE.replace('    A -->|"@call"| B\n', "")
    assert _codes(lint_text(text, repo)).count("PHANTOM_EDGE") == 1


def test_a_typo_sigil_is_label_unknown(repo: Path) -> None:
    [f] = [f for f in lint_text(FIXTURE, repo).findings if f.code == "LABEL_UNKNOWN"]
    assert f.line == _line_of(FIXTURE, "@improt")
    assert "@improt" in f.message


@pytest.mark.parametrize("state", ["built", "deleted-import", "no-index"])
def test_unlabelled_and_prose_edges_are_never_reported(repo: Path, state: str) -> None:
    if state == "deleted-import":
        (repo / "src/app/a.py").write_text("def run():\n    return 1\n")
        _build(repo)
    elif state == "no-index":
        shutil.rmtree(repo / ".codemem")
    report = lint_text(FIXTURE, repo)
    lines = {_line_of(FIXTURE, "A -->|fork| B"), _line_of(FIXTURE, "    A --> B")}
    assert not [f for f in (*report.findings, *report.unknowns) if f.line in lines]


# ---------------------------------------------------------------------
# UNKNOWN — every unevaluable claim, with its reason; never a finding
# ---------------------------------------------------------------------

def _unknown(report, needle: str) -> str:
    [f] = [f for f in report.unknowns if f.line == _line_of(FIXTURE, needle)]
    assert f.code == "UNKNOWN"
    return f.message


def test_unevaluable_claims_are_unknown_with_a_reason(repo: Path) -> None:
    report = lint_text(FIXTURE, repo)
    assert "planned" in _unknown(report, 'A -->|"@import"| N')
    assert "not in the codemem graph" in _unknown(report, 'A -->|"@import"| SH')
    assert "plugin-surface edges are not in the codemem index" in _unknown(report, 'A -->|"@skill"| K')
    assert "no repo path" in _unknown(report, 'G -->|"@import"| B')
    assert not [f for f in report.findings if f.code == "UNKNOWN"]


def test_no_index_makes_every_sigil_edge_unknown_with_the_remedy(repo: Path) -> None:
    """AC6: exit is decided by the other tiers alone."""
    shutil.rmtree(repo / ".codemem")
    report = lint_text(FIXTURE, repo)
    assert not {"PHANTOM_EDGE"} & set(_codes(report))
    checked = [f for f in report.unknowns if f.line == _line_of(FIXTURE, 'A -->|"@import"| B')]
    assert checked and "codemem build" in checked[0].message
    assert _codes(report) == ["LABEL_UNKNOWN"]  # the typo is still loud without a graph


def test_a_stale_graph_is_unknown_not_phantom(repo: Path) -> None:
    (repo / "src/app/a.py").write_text("def run():\n    return 1\n")  # edited after indexing
    os.utime(repo / "src/app/a.py", (4_000_000_000, 4_000_000_000))
    report = lint_text(FIXTURE, repo)
    assert "PHANTOM_EDGE" not in _codes(report)
    assert any("changed since indexing" in f.message for f in report.unknowns)


def test_node_ids_are_scoped_per_fence(repo: Path) -> None:
    """The Flow view's `A` is b.py; it must not leak into the Component view's A."""
    report = lint_text(FIXTURE, repo)
    assert "PHANTOM_EDGE" not in _codes(report)
    assert not [f for f in report.unknowns if f.line == _line_of(FIXTURE, "-->|runs|")]


def test_classdef_and_class_lines_are_not_edges(repo: Path) -> None:
    report = lint_text(FIXTURE, repo)
    lines = {_line_of(FIXTURE, "classDef start"), _line_of(FIXTURE, "class A start")}
    assert not [f for f in (*report.findings, *report.unknowns) if f.line in lines]


def test_unquoted_sigil_is_still_read(repo: Path) -> None:
    text = FIXTURE.replace('A -->|"@improt"| B', "A -->|@improt| B")
    assert "LABEL_UNKNOWN" in _codes(lint_text(text, repo))


def test_inline_node_declarations_on_an_edge_line(repo: Path) -> None:
    (repo / "src/app/a.py").write_text("def run():\n    return 1\n")
    _build(repo)
    text = FIXTURE.replace(
        '    A -->|"@import"| B\n', '    X["src/app/a.py"] -->|"@import"| Y["src/app/b.py"]\n'
    )
    assert "PHANTOM_EDGE" in _codes(lint_text(text, repo))


# ---------------------------------------------------------------------
# CLI — UNKNOWN lines never change the exit code
# ---------------------------------------------------------------------

def test_cli_prints_unknowns_and_exits_on_findings_only(
    repo: Path, tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    plan = tmp_path / "p-plan.md"
    plan.write_text(FIXTURE.replace('    A -->|"@improt"| B\n', ""))
    assert cli.lint_main([str(plan), "--repo-root", str(repo)]) == 0
    out = capsys.readouterr().out
    planned = _line_of(plan.read_text(), 'A -->|"@import"| N')
    assert f"{plan}:{planned}: UNKNOWN: " in out


# ---------------------------------------------------------------------
# AC5 — every completed plan without a sigil: zero new findings
# ---------------------------------------------------------------------

def _completed_plans() -> list[Path]:
    return sorted(Path(p) for p in glob.glob(str(REPO / ".claude/dev/completed/**/*-plan.md"), recursive=True))


def test_there_are_completed_plans_to_check() -> None:
    assert _completed_plans()


@pytest.mark.parametrize("plan", _completed_plans(), ids=lambda p: p.parent.name)
def test_completed_plans_get_no_sigil_findings(plan: Path) -> None:
    """No skip: a completed plan with a stray `|"@..."|` prose label is exactly the one that
    could newly go red (code-reviewer §6.8). Today none carries a sigil at all."""
    report = lint_text(plan.read_text(encoding="utf-8"), REPO)
    assert not {"PHANTOM_EDGE", "LABEL_UNKNOWN"} & set(_codes(report))
    assert not report.unknowns


@pytest.mark.parametrize("line", [
    "A" + "[" * 50_000, "A -->|" + "x" * 50_000, "A" * 50_000 + " --> ", "A[" * 25_000,
    "A" + " " * 50_000 + '-->|"@import"| B',
    "a[" * 100_000 + "]",  # security-auditor: node flood (unbounded `]` search per match)
    'N["' + "(" * 100_000 + "x" + ")" * 100_000 + '"]',  # security-auditor: `_unwrap` re-slicing
], ids=["brackets", "pipe", "ids", "decls", "spaces", "node-flood", "paren-label"])
def test_edge_parsing_is_linear_on_hostile_lines(repo: Path, line: str) -> None:
    import time

    text = FIXTURE.replace("    A --> B\n", f"    {line}\n")
    start = time.perf_counter()
    lint_text(text, repo)
    assert time.perf_counter() - start < _LINEAR_BUDGET_S


def test_an_isolated_python_file_is_still_evaluable(repo: Path) -> None:
    """Evaluability is by language, from the graph's own data: lonely.py has no edges
    at all, but Python has import edges, so a false claim on it is PHANTOM, not UNKNOWN."""
    (repo / "src/app/lonely.py").write_text("X = 1\n")
    _git(repo, "add", "-A")  # codemem indexes `git ls-files`
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "lonely")
    _build(repo)
    text = FIXTURE.replace('    N["src/app/new.py (new)"]\n', '    N["src/app/lonely.py"]\n')
    report = lint_text(text, repo)
    assert [f.line for f in report.findings if f.code == "PHANTOM_EDGE"] == [_line_of(text, 'A -->|"@import"| N')]


# ---------------------------------------------------------------------
# §6.8 M8 fixes (Ste: CRITICALs accepted, "fix all now")
# ---------------------------------------------------------------------

@pytest.mark.parametrize("edge", [
    'A --> B -->|"@import"| N',
    'A & B -->|"@import"| N',
    'A -- "@import" --> N',
    'A --->|"@import"| N',
    'A <-->|"@import"| N',
    'A --o|"@import"| N',
    'A -->|"@import"| B & N',
    'A -->|"@import"| B -->|"@import"| N',
])
def test_an_unparsed_sigil_edge_is_unknown_never_silent(repo: Path, edge: str) -> None:
    """code-reviewer CRITICAL: these forms produced no finding and no UNKNOWN — a silent PASS."""
    text = FIXTURE.replace("    A --> B\n", f"    {edge}\n")
    report = lint_text(text, repo)
    line = _line_of(text, edge)
    assert [f.message for f in report.unknowns if f.line == line] == ["unparsed sigil edge form"]
    assert not [f for f in report.findings if f.line == line]


def test_a_sigil_in_a_mermaid_comment_is_not_a_claim(repo: Path) -> None:
    text = FIXTURE.replace("    A --> B\n", '    %% A -->|"@import"| N\n')
    report = lint_text(text, repo)
    assert not [f for f in (*report.findings, *report.unknowns) if f.line == _line_of(text, "%%")]


def test_a_pipe_inside_a_quoted_label_is_part_of_the_label(repo: Path) -> None:
    text = FIXTURE.replace("    A --> B\n", '    A -->|"@import | x"| B\n')
    [f] = [f for f in lint_text(text, repo).findings if f.line == _line_of(text, "@import | x")]
    assert f.code == "LABEL_UNKNOWN"


def test_the_last_node_declaration_wins(repo: Path) -> None:
    """Mermaid relabels a node on redeclaration; B becomes c.py, which a.py never imports."""
    text = FIXTURE.replace('    A -->|"@call"| B\n', '    B["src/app/c.py"]\n    A -->|"@call"| B\n')
    phantoms = [f for f in lint_text(text, repo).findings if f.code == "PHANTOM_EDGE"]
    assert phantoms and "src/app/c.py" in phantoms[0].message


@pytest.mark.parametrize("exists", [True, False])
def test_an_endpoint_outside_the_repo_is_never_probed(repo: Path, tmp_path: Path, exists: bool) -> None:
    """security-auditor + code-reviewer: `../x` leaked host-file existence via two reasons."""
    if exists:
        (tmp_path / "secret.py").write_text("S = 1\n")
    text = FIXTURE.replace('    N["src/app/new.py (new)"]\n', '    N["../secret.py"]\n')
    [f] = [f for f in lint_text(text, repo).unknowns if f.line == _line_of(text, 'A -->|"@import"| N')]
    assert f.message == "endpoint outside the repo: ../secret.py"


def test_terminal_escapes_never_reach_the_cli_output(repo: Path, tmp_path: Path, capsys) -> None:
    plan = tmp_path / "p-plan.md"
    plan.write_text(FIXTURE.replace('"src/app/new.py (new)"', '"\x1b[2Jfake src/app/new.py (new)"'))
    cli.lint_main([str(plan), "--repo-root", str(repo)])
    assert "\x1b" not in capsys.readouterr().out


def test_a_partial_index_is_unknown_not_a_crash(repo: Path) -> None:
    import sqlite3

    db = repo / ".codemem/index.db"
    db.unlink()
    conn = sqlite3.connect(db)
    conn.executescript("CREATE TABLE files(id INTEGER PRIMARY KEY, path TEXT, mtime INTEGER); PRAGMA user_version = 3;")
    conn.close()
    report = lint_text(FIXTURE, repo)
    [f] = [f for f in report.unknowns if f.line == _line_of(FIXTURE, 'A -->|"@import"| B')]
    assert "codemem build" in f.message


def test_the_lint_knows_every_sigil_the_emitter_writes() -> None:
    """future-proofing: two packages that may not import each other each spell the vocabulary."""
    from codemem.draw.cut import KINDS
    from codemem.draw.plugin_surface import NodeKind

    emitted = {f"@{k}" for k in KINDS if k != "both"} | {f"@{k}" for k in NodeKind if k is not NodeKind.RULE}
    assert emitted <= set(mermaid_lint.SIGILS)


def test_the_generated_architecture_docs_lint_with_no_label_unknown() -> None:
    for page in sorted((REPO / "docs/architecture").glob("*.md")):
        text = "## 13. Architecture View\n\n### Component view\n\n" + page.read_text(encoding="utf-8")
        assert "LABEL_UNKNOWN" not in _codes(lint_text(text, REPO)), page


# ---------------------------------------------------------------------
# M11 — the `sigils:` summary line the §6.7 HARD item reads (ADR-0015)
# ---------------------------------------------------------------------

def _summary(repo: Path, tmp_path: Path, capsys: pytest.CaptureFixture) -> str:
    plan = tmp_path / "s-plan.md"
    plan.write_text(FIXTURE)
    cli.lint_main([str(plan), "--repo-root", str(repo)])
    out = capsys.readouterr().out.splitlines()
    [line] = [ln for ln in out if ln.startswith("sigils: ")]
    assert out[-2:] == [line, out[-1]] and out[-1].startswith("render: ")  # just before render:
    return line


def test_summary_counts_every_sigil_claim(repo: Path, tmp_path: Path, capsys) -> None:
    # 7 claims: 2 checked, @improt (LABEL_UNKNOWN counts as phantom), 4 per-claim UNKNOWN of
    # which the path-less `G` label is an authoring error (invalid).
    assert _summary(repo, tmp_path, capsys) == "sigils: edges=7 checked=2 phantom=1 unknown=4 invalid=1 index-unknown=0"


def test_summary_counts_phantoms(repo: Path, tmp_path: Path, capsys) -> None:
    (repo / "src/app/a.py").write_text("def run():\n    return 1\n")
    _build(repo)
    assert _summary(repo, tmp_path, capsys) == "sigils: edges=7 checked=2 phantom=3 unknown=4 invalid=1 index-unknown=0"


def test_summary_without_an_index_counts_index_unknowns(repo: Path, tmp_path: Path, capsys) -> None:
    """Only claims that reach the graph are index-unknown; `(new)`/plugin/path-less stay per-claim."""
    shutil.rmtree(repo / ".codemem")
    assert _summary(repo, tmp_path, capsys) == "sigils: edges=7 checked=0 phantom=1 unknown=6 invalid=1 index-unknown=3"


def test_summary_counts_a_stale_index_as_index_unknown(repo: Path, tmp_path: Path, capsys) -> None:
    os.utime(repo / "src/app/b.py", (4_000_000_000, 4_000_000_000))
    assert _summary(repo, tmp_path, capsys) == "sigils: edges=7 checked=0 phantom=1 unknown=6 invalid=1 index-unknown=3"


def test_summary_counts_a_partial_index_as_index_unknown(repo: Path, tmp_path: Path, capsys) -> None:
    import sqlite3

    db = repo / ".codemem/index.db"
    db.unlink()
    conn = sqlite3.connect(db)
    conn.executescript("CREATE TABLE files(id INTEGER PRIMARY KEY, path TEXT, mtime INTEGER); PRAGMA user_version = 3;")
    conn.close()
    assert _summary(repo, tmp_path, capsys).endswith("index-unknown=3")


def _one_edge(repo: Path, edge: str, *decls: str) -> str:
    """Lint a one-edge §13 over the fixture's nodes; return the `sigils:` payload."""
    text = FIXTURE.split("```mermaid")[0] + "```mermaid\ngraph TD\n" + "".join(
        f"    {d}\n" for d in ('A["src/app/a.py"]', 'B["src/app/b.py"]', *decls)
    ) + f"    {edge}\n```\n"
    return cli._sigil_summary(lint_text(text, repo))


@pytest.mark.parametrize(
    ("edge", "decls"),
    [
        ('A -->|"@import"| M', ('M["src/app/missing.py"]',)),  # endpoint missing, not (new)
        ('A -->|"@import"| S', ('S["src/app/b.py (new)"]',)),  # stale (new): the file exists
        ('A -->|"@import"| G', ('G["group of things"]',)),  # no repo path in the label
        ('A -->|"@import"| B & C', ()),  # unparsed sigil edge form
        ('A -->|"@import"| O', ('O["/etc/passwd.py"]',)),  # endpoint outside the repo
    ],
)
def test_authoring_errors_are_invalid(repo: Path, edge: str, decls: tuple[str, ...]) -> None:
    """§6.8 M11 (Ste): a claim the diagram's author can fix now is refused, not passed as UNKNOWN."""
    assert _one_edge(repo, edge, *decls) == "edges=1 checked=0 phantom=0 unknown=1 invalid=1 index-unknown=0"


@pytest.mark.parametrize(
    ("edge", "decls"),
    [
        ('A -->|"@import"| N', ('N["src/app/new.py (new)"]',)),  # genuinely planned
        ('A -->|"@skill"| K', ('K["claude-code/skills/x/SKILL.md"]',)),  # plugin sigil (M13)
        ('A -->|"@import"| SH', ('SH["scripts/run.sh"]',)),  # a language the graph does not model
    ],
)
def test_claims_that_cannot_be_checked_yet_are_not_invalid(repo: Path, edge: str, decls: tuple[str, ...]) -> None:
    assert _one_edge(repo, edge, *decls) == "edges=1 checked=0 phantom=0 unknown=1 invalid=0 index-unknown=0"


def test_a_true_edge_is_checked(repo: Path) -> None:
    assert _one_edge(repo, 'A -->|"@import"| B') == "edges=1 checked=1 phantom=0 unknown=0 invalid=0 index-unknown=0"


def test_every_sigil_finding_code_is_counted_as_phantom(repo: Path) -> None:
    """future-proofing: a new sigil finding the summary did not count would pass the §6.7 item."""
    (repo / "src/app/a.py").write_text("def run():\n    return 1\n")
    _build(repo)
    codes = {f.code for f in lint_text(FIXTURE, repo).findings} - {"STALE_PATH"}
    assert codes and codes <= set(mermaid_lint.SIGIL_FINDINGS)
