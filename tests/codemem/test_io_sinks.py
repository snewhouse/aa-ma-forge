"""The I/O-boundary view (diagram-generation M9).

Decisions (context-log 2026-09-25, M9 prototype verdict REVISE, Ste):
* arrows per FILE when that fits the dense band (``DENSE_BAND``), else per L1 folder;
* two tiers — ``qualified`` (a catalogued ``mod.func``) and ``bare`` (a catalogued
  method name on an untyped receiver) — drawn as edge ids in ``class … qualified`` /
  ``class … bare`` lines (mermaid has no ``:::class`` on edges);
* ``open`` stays in ``_CALL_EXCLUDE``; filesystem edges on this fixture tree <= N = 5,
  one per v1 language, and ``opener.py`` (whose only I/O is ``open()``) adds none;
* the ``IO_DENSE_BAND`` line records the FILE-level count.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

from codemem.draw import io_sinks, views
from codemem.draw.cut import Level
from codemem.draw.mermaid import CATEGORY_LABEL, io_to_mermaid
from codemem.indexer import build_index
from codemem.parser import ast_grep
from codemem.parser.python_ast import _CALL_EXCLUDE, extract_python_signatures
from codemem.storage.db import connect

REPO = Path(__file__).resolve().parents[2]
V1_LANGS = {"python", "typescript", "tsx", "javascript", "go"}
FS_EDGE_CAP = len(io_sinks.LANGS)  # N = 5, pinned by the M9 prototype verdict: one fs edge per v1 language

needs_sg = pytest.mark.skipif(shutil.which("sg") is None, reason="ast-grep binary not on PATH")

FIXTURE = {
    "app/store.py": 'import sqlite3\n\ndef save():\n    conn = sqlite3.connect("x.db")\n    conn.execute("select 1")\n',
    "app/shell.py": 'from subprocess import run\n\ndef go():\n    run(["ls"])\n',
    "app/files.py": 'import shutil\n\ndef cp():\n    shutil.copy("a", "b")\n',
    "app/opener.py": 'def read():\n    return open("x").read()\n',
    "app/cfg.py": 'import os\n\ndef env():\n    return os.getenv("X")\n',
    "app/repo.py": 'class Repo:\n    def q(self):\n        return self.db.execute("select 1")\n',
    "web/client.ts": (
        'import fs from "fs";\n'
        "export function load(): string {\n"
        '  return fs.readFileSync("x", "utf8");\n'
        "}\n"
        "export function get() {\n"
        '  return fetch("https://example.invalid");\n'
        "}\n"
    ),
    "web/view.tsx": (
        'import fs from "fs";\n'
        "export function View() {\n"
        '  fs.writeFileSync("x", "y");\n'
        "  return <div />;\n"
        "}\n"
    ),
    "web/legacy.js": 'const fs = require("fs");\nfunction save() {\n  fs.writeFileSync("x", "y");\n}\n',
    "svc/main.go": 'package main\n\nimport "os"\n\nfunc Load() ([]byte, error) {\n\treturn os.ReadFile("x")\n}\n',
    "tests/test_x.py": 'import subprocess\n\ndef test_x():\n    subprocess.run(["x"])\n',
}


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True).stdout


def _commit(root: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text)
    _git(root, "init", "-q")
    _git(root, "add", ".")
    _git(root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init")


@pytest.fixture
def io_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "r"
    root.mkdir()
    _commit(root, FIXTURE)
    build_index(root, root / ".codemem/index.db", package=".")
    monkeypatch.chdir(root)
    return root


@pytest.fixture
def edges(io_repo: Path) -> list[io_sinks.IoEdge]:
    conn = connect(io_repo / ".codemem/index.db", read_only=True)
    try:
        return io_sinks.io_edges(conn, io_sinks.load_catalogue())
    finally:
        conn.close()


def _by(edges, **want):
    return [e for e in edges if all(getattr(e, k) == v for k, v in want.items())]


# --- the catalogue ---------------------------------------------------------------------


def test_catalogue_loads_and_covers_every_v1_language_and_category():
    cat = io_sinks.load_catalogue()
    assert {s.lang for s in cat.sinks} == V1_LANGS
    assert {s.category for s in cat.sinks} == set(io_sinks.CATEGORIES)
    assert {s.tier for s in cat.sinks} == {"qualified", "bare"}
    assert all(s.source.startswith("https://") for s in cat.sinks)


@pytest.mark.parametrize(
    ("row", "why"),
    [
        ("- {lang: cobol, category: db, symbol: x.y, tier: qualified, source: 'https://a'}", "lang"),
        ("- {lang: python, category: gpu, symbol: x.y, tier: qualified, source: 'https://a'}", "category"),
        ("- {lang: python, category: db, symbol: x.y, tier: fuzzy, source: 'https://a'}", "tier"),
        ("- {lang: python, category: db, symbol: on, tier: bare, source: 'https://a'}", "symbol"),  # YAML 1.1 bool
        ("- {lang: python, category: db, symbol: x.y, tier: qualified}", "source"),
        ("- {lang: python, category: db, symbol: x.y, tier: qualified, source: 'http://a'}", "source"),
        ("{lang: python}", "list"),
    ],
    ids=["lang", "category", "tier", "yaml-bool", "no-source", "http-source", "not-a-list"],
)
def test_catalogue_refuses_a_malformed_row(tmp_path: Path, row: str, why: str):
    p = tmp_path / "sinks.yaml"
    p.write_text(row + "\n")
    with pytest.raises(ValueError, match=why):
        io_sinks.load_catalogue(p)


def test_catalogue_names_an_unexpected_key(tmp_path: Path):
    p = tmp_path / "sinks.yaml"
    p.write_text("- {lang: python, category: db, symbol: x.y, tier: qualified, source: 'https://a', extra: 1}\n")
    with pytest.raises(ValueError, match="unexpected.*extra"):
        io_sinks.load_catalogue(p)


def test_catalogue_refuses_a_duplicate_symbol(tmp_path: Path):
    row = "- {lang: python, category: db, symbol: x.y, tier: qualified, source: 'https://a'}\n"
    p = tmp_path / "sinks.yaml"
    p.write_text(row * 2)
    with pytest.raises(ValueError, match="duplicate"):
        io_sinks.load_catalogue(p)


@pytest.mark.parametrize(
    ("lang", "callee", "want"),
    [
        ("python", "sqlite3.connect", ("db", "qualified")),
        ("python", "conn.execute", ("db", "bare")),
        ("python", "self.db.execute", ("db", "bare")),
        ("python", "execute", None),  # no receiver: a local helper, not a sink
        ("python", "json.loads", None),
        ("javascript", "fetch", ("http", "qualified")),
        ("go", "os.ReadFile", ("fs", "qualified")),
        ("go", "sqlite3.connect", None),  # a python symbol does not match in go
    ],
)
def test_classify(lang, callee, want):
    assert io_sinks.classify(lang, callee, io_sinks.load_catalogue()) == want


# --- the parser changes ------------------------------------------------------------------


def test_open_stays_excluded():
    assert "open" in _CALL_EXCLUDE


def test_imported_bare_name_is_qualified_through_the_alias_map():
    r = extract_python_signatures(
        "from subprocess import run as r\nfrom os import getenv\n\ndef go():\n    r(['ls'])\n    getenv('X')\n",
        package=".", file_rel="a.py",
    )
    assert {e.dst_unresolved for e in r.unresolved_edges} == {"subprocess.run", "os.getenv"}


@needs_sg
def test_ast_grep_emits_unresolved_calls_from_the_enclosing_function(tmp_path: Path):
    from codemem.parser.ast_grep import extract_with_ast_grep

    f = tmp_path / "a.ts"
    f.write_text(
        'fs.readFileSync("top-level, no enclosing function");\n'
        "function outer() {\n"
        '  fs.readFileSync("x");\n'
        "  fetch(url).then(r => r);\n"
        "}\n"
    )
    r = extract_with_ast_grep([f], package=".", repo_root=tmp_path)[f]
    got = {(e.src_scip_id.rsplit("#", 1)[1], e.dst_unresolved) for e in r.unresolved_edges}
    # A callee chained through a call (`fetch(url).then`) is dropped, as in python_ast;
    # the inner `fetch` is its own call expression and is kept.
    assert got == {("outer", "fs.readFileSync"), ("outer", "fetch")}


# --- the edges --------------------------------------------------------------------------------


@needs_sg
def test_every_v1_language_contributes_a_qualified_edge(edges):  # AC2
    assert {e.lang for e in edges if e.tier == "qualified"} == V1_LANGS


@needs_sg
def test_filesystem_edges_are_capped_and_open_adds_none(edges):  # AC5
    fs = _by(edges, category="fs")
    assert len(fs) <= FS_EDGE_CAP
    assert not _by(edges, src="app/opener.py")


@needs_sg
def test_tiers_merge_per_edge_and_tests_are_excluded(edges):
    assert [e.tier for e in _by(edges, src="app/store.py", category="db")] == ["qualified"]
    assert [e.tier for e in _by(edges, src="app/repo.py", category="db")] == ["bare"]
    assert _by(edges, src="app/shell.py", category="subprocess")
    assert not [e for e in edges if e.src.startswith("tests/")]


def test_level_is_file_when_it_fits_else_l1():
    es = [io_sinks.IoEdge(f"pkg/sub/m{i}.py", "python", "fs", "qualified", 1) for i in range(3)]
    level, kept = io_sinks.choose_level(es, threshold=3)
    assert level is Level.L2 and len(kept) == 3
    level, kept = io_sinks.choose_level(es, threshold=2)
    assert level is Level.L1
    assert kept == [io_sinks.IoEdge("pkg/sub", "python", "fs", "qualified", 3)]


def test_l1_collapse_keeps_qualified_when_any_member_is():
    es = [
        io_sinks.IoEdge("pkg/sub/a.py", "python", "db", "bare", 1),
        io_sinks.IoEdge("pkg/sub/b.py", "python", "db", "qualified", 2),
    ]
    _, kept = io_sinks.choose_level(es, threshold=1)
    assert kept == [io_sinks.IoEdge("pkg/sub", "python", "db", "qualified", 3)]


# --- the mermaid ------------------------------------------------------------------------------

_EDGE = re.compile(r"^\s+\S+ (e\d+)@-->\|\"\d+\"\| \S+$")


def _mmd(edges) -> str:
    level, kept = io_sinks.choose_level(edges)
    return io_to_mermaid(kept, level)


@needs_sg
def test_exactly_two_classdefs_qualified_and_bare_differing_in_dasharray(edges):  # AC1, AC4
    lines = _mmd(edges).splitlines()
    defs = {ln.split()[1]: ln for ln in lines if ln.strip().startswith("classDef ")}
    assert set(defs) == {"qualified", "bare"}
    dash = {k: re.search(r"stroke-dasharray:([^;,]*)", v) for k, v in defs.items()}
    assert (dash["qualified"] and dash["qualified"][1]) != (dash["bare"] and dash["bare"][1])


@needs_sg
def test_every_edge_id_is_in_exactly_one_tier_class_line(edges):  # AC4
    lines = _mmd(edges).splitlines()
    ids = [m[1] for ln in lines if (m := _EDGE.match(ln))]
    assert len(ids) == len(edges)
    classes = {ln.split()[2]: set(ln.split()[1].split(",")) for ln in lines if ln.strip().startswith("class ")}
    assert set(classes) == {"qualified", "bare"}
    assert classes["qualified"].isdisjoint(classes["bare"])
    assert classes["qualified"] | classes["bare"] == set(ids)


@needs_sg
def test_languages_are_subgraphs(edges):
    text = _mmd(edges)
    for lang in V1_LANGS:
        assert re.search(rf'^\s+subgraph \S+\["{lang}"\]$', text, re.M), lang


def test_mermaid_is_deterministic_and_escapes_paths():
    es = [io_sinks.IoEdge('a/"x".py', "python", "fs", "qualified", 1)]
    assert io_to_mermaid(es, Level.L2) == io_to_mermaid(list(es), Level.L2)
    assert '"x"' not in io_to_mermaid(es, Level.L2)


def test_no_sinks_is_a_valid_empty_flowchart():
    assert io_to_mermaid([], Level.L2).startswith("flowchart LR\n")


# --- the living doc -----------------------------------------------------------------------------


def test_io_view_is_registered():  # AC3
    assert views.VIEWS["io"].output_path == "docs/architecture/io.md"


@needs_sg
def test_check_covers_io_md(io_repo: Path):  # AC3
    conn = connect(io_repo / ".codemem/index.db", read_only=True)
    try:
        views.write_views(io_repo, conn)
        io_md = io_repo / "docs/architecture/io.md"
        assert io_md.is_file()
        assert views.check_views(io_repo, conn) == []
        io_md.write_text(io_md.read_text().replace("filesystem", "files"))
        assert "DRIFT docs/architecture/io.md: differs from the code" in views.check_views(io_repo, conn)
    finally:
        conn.close()


# --- the band line ------------------------------------------------------------------------------

BAND = re.compile(
    rf"^IO_DENSE_BAND repo=\S+ sha=[0-9a-f]{{40}} edges=\d+ threshold={io_sinks.DENSE_BAND} verdict=(UNDER|OVER)$"
)


def test_dense_band_is_ticket_3s():
    assert io_sinks.DENSE_BAND == 120


@pytest.mark.parametrize(("n", "verdict"), [(io_sinks.DENSE_BAND, "UNDER"), (io_sinks.DENSE_BAND + 1, "OVER")])
def test_band_line(n, verdict):
    line = io_sinks.band_line("r", "a" * 40, n)
    assert BAND.match(line)
    assert line.endswith(f"edges={n} threshold={io_sinks.DENSE_BAND} verdict={verdict}")


def test_band_line_cannot_break_its_own_format_or_the_terminal():
    line = io_sinks.band_line("my repo\x1b[31m", "a" * 40, 1)
    assert BAND.match(line) and "\x1b" not in line


def _outside_the_venv() -> dict[str, str]:
    """The caller's shell, not pytest's: no active venv, so the script must find its own project."""
    venv = os.environ.get("VIRTUAL_ENV", str(REPO / ".venv"))
    env = {k: v for k, v in os.environ.items() if k not in ("VIRTUAL_ENV", "UV_PROJECT", "PYTHONPATH")}
    env["PATH"] = os.pathsep.join(p for p in env["PATH"].split(os.pathsep) if not p.startswith(venv))
    return env


@needs_sg
def test_measure_script_regenerates_the_line_byte_identically(io_repo: Path):  # AC6
    sha = _git(io_repo, "rev-parse", "HEAD").strip()
    before = _git(io_repo, "status", "--porcelain", "--ignored")
    run = lambda: subprocess.run(  # noqa: E731
        ["bash", str(REPO / "scripts/measure_io_band.sh"), str(io_repo), sha],
        cwd=io_repo.parent, env=_outside_the_venv(), check=True, capture_output=True, text=True,
    ).stdout
    first = run()
    assert BAND.match(first.strip()), first
    assert f"repo=r sha={sha} " in first
    assert first == run()
    assert _git(io_repo, "status", "--porcelain", "--ignored") == before  # read-only on the measured repo


# --- §6.8 follow-ups ------------------------------------------------------------------------------


def test_every_category_has_a_label():
    assert set(CATEGORY_LABEL) == set(io_sinks.CATEGORIES)


def test_the_generic_renderer_does_not_load_yaml():
    code = "import sys, codemem.draw.mermaid; sys.exit('yaml' in sys.modules)"
    assert subprocess.run([sys.executable, "-c", code]).returncode == 0


def _sg(rule: str, line: int, col: int, end_line: int, end_col: int, **kw) -> ast_grep._SgMatch:
    return ast_grep._SgMatch(Path("a.ts"), rule, kw.get("name"), line, end_line, "", kw.get("callee"), col, end_col)


def test_enclosing_function_is_column_precise():
    # `function a(){} function b(){ fs.readFileSync() }` — one line, two functions.
    ms = [
        _sg("ts-function-def", 1, 0, 1, 14, name="a"),
        _sg("ts-function-def", 1, 15, 1, 48, name="b"),
        _sg("ts-call", 1, 28, 1, 46, callee="fs.readFileSync"),
    ]
    r = ast_grep._build_parse_result(Path("a.ts"), ms, package=".", repo_root=Path("."))
    assert [(e.src_scip_id.rsplit("#", 1)[1], e.dst_unresolved) for e in r.unresolved_edges] == [("b", "fs.readFileSync")]


def test_enclosing_function_lookup_is_linear():
    n = 5000  # quadratic took ~2.4 s at 3000 functions (§6.8); linear is milliseconds
    ms = [m for i in range(n) for m in (
        _sg("ts-function-def", 3 * i + 1, 0, 3 * i + 3, 1, name=f"f{i}"),
        _sg("ts-call", 3 * i + 2, 2, 3 * i + 2, 20, callee="fs.readFileSync"),
        _sg("ts-call", 3 * i + 2, 22, 3 * i + 2, 30, callee="fetch"),
    )]
    start = time.perf_counter()
    r = ast_grep._build_parse_result(Path("a.ts"), ms, package=".", repo_root=Path("."))
    assert time.perf_counter() - start < 1.0
    assert len(r.unresolved_edges) == 2 * n
