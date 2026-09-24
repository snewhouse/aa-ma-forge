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
    assert f"{plan}:{_line_of(plan.read_text(), 'A -->|\"@import\"| N')}: UNKNOWN: " in out


# ---------------------------------------------------------------------
# AC5 — every completed plan without a sigil: zero new findings
# ---------------------------------------------------------------------

def _completed_plans() -> list[Path]:
    return sorted(Path(p) for p in glob.glob(str(REPO / ".claude/dev/completed/**/*-plan.md"), recursive=True))


def test_there_are_completed_plans_to_check() -> None:
    assert _completed_plans()


@pytest.mark.parametrize("plan", _completed_plans(), ids=lambda p: p.parent.name)
def test_sigil_free_completed_plans_get_no_sigil_findings(plan: Path) -> None:
    text = plan.read_text(encoding="utf-8")
    if mermaid_lint.SIGIL_LABEL_RE.search(text):
        pytest.skip("carries a sigil — AC5 covers sigil-free plans only")
    report = lint_text(text, REPO)
    assert not {"PHANTOM_EDGE", "LABEL_UNKNOWN"} & set(_codes(report))
    assert not report.unknowns
