"""`aa-ma-render --explorer` (diagram-generation M12, map Ticket 11, ADR-0010/0014).

The explorer embeds the codemem graph as JSON and derives each level in the browser, so
its mermaid generator is JavaScript while `codemem draw`'s is Python. The shared fixture
`draw-node-ids.json` pins the two surfaces that must agree — node-id derivation and the
directory-collapse rule — here (Python) and in `explorer_contract.test.mjs` (JS).
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
from pathlib import Path

import pytest

from aa_ma.render import explorer, html
from aa_ma.render.cli import render_main
from codemem.draw.cut import MAX_EDGES, Level, collapse, is_test_path
from codemem.draw.mermaid import escape_label
from codemem.indexer import build_index

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "tests/fixtures/draw-node-ids.json"
RULES = REPO / "tests/fixtures/draw-label-rules.json"
GEN = REPO / "tests/fixtures/draw-node-ids.gen.mjs"
# The element-id scheme explorer.js's nodeIdOf parses was proven against the real SVG of this
# mermaid version (M12.1 prototype). A bump must re-run that check before changing this.
NODE_ID_SCHEME_PROVEN_ON = "11.17.2"
CONTRACT = REPO / "tests/render/explorer_contract.test.mjs"
EXPLORER_JS = REPO / "src/aa_ma/render/explorer.js"


def _rows() -> list[dict]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------
# The shared fixture — Python side (AC5, AC6)
# ---------------------------------------------------------------------

def test_fixture_pins_the_collapse_rule() -> None:
    rows = [r for r in _rows() if "collapse" in r]
    assert rows and all(r["level"] == 2 for r in rows)
    assert any("/" not in r["name"] for r in rows)  # a top-level file stays itself
    for r in rows:
        assert r["collapse"] == [collapse(r["name"], Level.L0), collapse(r["name"], Level.L1)], r


def test_label_rules_are_codemems() -> None:
    """The sibling fixture's expected values ARE codemem's; the JS suite asserts the same rows."""
    rules = json.loads(RULES.read_text(encoding="utf-8"))
    assert [[s, escape_label(s)] for s, _ in rules["escape"]] == rules["escape"]
    assert [[p, is_test_path(p)] for p, _ in rules["is_test"]] == rules["is_test"]


def test_the_generator_reproduces_the_fixture(tmp_path: Path) -> None:
    """§6.8: regenerating draw-node-ids.json must keep the collapse pins, byte for byte."""
    node = shutil.which("node")
    if node is None:
        pytest.skip("node not installed — the explorer-contract CI job runs the JS side")
    keys = json.dumps([[r["level"], r["name"]] for r in _rows()], ensure_ascii=False)
    run = subprocess.run([node, str(GEN)], input=keys, capture_output=True, text=True, timeout=60)
    assert run.returncode == 0, run.stderr
    assert run.stdout == FIXTURE.read_text(encoding="utf-8")


def test_a_mermaid_bump_re_proves_the_node_element_scheme() -> None:
    assert html.MERMAID_VERSION == NODE_ID_SCHEME_PROVEN_ON, (
        "MERMAID_VERSION moved: re-run the M12.1 SVG check (prototype/diagram-generation-explorer "
        "drive.py) — explorer.js nodeIdOf parses `<renderId>-flowchart-<nid>-<i>` — then update "
        "NODE_ID_SCHEME_PROVEN_ON."
    )


def test_explorer_edge_cap_is_codemems() -> None:
    """aa_ma may not import codemem (import contract), so the cap is restated — pinned here."""
    assert explorer.MAX_EDGES == MAX_EDGES


# ---------------------------------------------------------------------
# An indexed throwaway repo
# ---------------------------------------------------------------------

def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", *args],
                   check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "r"
    (root / "src/app").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / ".gitignore").write_text(".codemem/\nbuild/\n")
    (root / "src/app/__init__.py").write_text("")
    (root / "src/app/a.py").write_text("from app.b import helper\n\ndef run():\n    return helper()\n")
    (root / "src/app/b.py").write_text("def helper():\n    return 1\n")
    (root / "tests/test_a.py").write_text("from app.a import run\n\ndef test_run():\n    run()\n")
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "init")
    build_index(root, root / ".codemem/index.db", package=".")
    return root


def _island(page: str) -> dict:
    m = re.search(r'<script type="application/json" id="graph">(.*?)</script>', page, re.S)
    assert m, "no graph island"
    return json.loads(m.group(1))


def _sha(text: str) -> str:
    return base64.b64encode(hashlib.sha256(text.encode()).digest()).decode()


# ---------------------------------------------------------------------
# The page (AC1, AC2a, AC3, AC8)
# ---------------------------------------------------------------------

def test_the_page_embeds_import_and_call_edges(repo: Path) -> None:
    page, stale = explorer.build_explorer(repo)
    assert stale is None
    g = _island(page)
    assert ["src/app/a.py", "src/app/b.py", "import"] in g["edges"]
    assert ["src/app/a.py", "src/app/b.py", "call"] in g["edges"]
    assert g["maxEdges"] == MAX_EDGES and g["stale"] is None


def test_the_page_reuses_html_py_security_unchanged(repo: Path) -> None:
    """AC3 + AC8: strict and the CDN/SRI pin come from html.py; the CSP is COMPOSED by
    html.csp() from the page's own inline-script hash, and html._CSP is untouched."""
    page, _ = explorer.build_explorer(repo)
    assert html._CSP == html.csp(html._INIT_SHA)
    inline = re.findall(r"<script>(.*?)</script>", page, re.S)
    assert len(inline) == 1
    assert f'content="{html.csp(_sha(inline[0]))}"' in page
    assert f"mermaid@{html.MERMAID_VERSION}/dist/mermaid.min.js" in page
    assert f'integrity="{html.MERMAID_SRI}"' in page
    assert 'securityLevel: "strict"' in html._INIT_JS and 'securityLevel: "strict"' in inline[0]
    assert "click " not in inline[0].split("function")[0]  # no mermaid `click` lines


def test_a_hostile_file_name_cannot_end_the_island(repo: Path) -> None:
    (repo / "src/app/x<").mkdir()  # a path segment cannot hold '/': the dir supplies `</`
    (repo / "src/app/x</script><!--.py").write_text("from app.b import helper\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "hostile")
    build_index(repo, repo / ".codemem/index.db", package=".")
    page, _ = explorer.build_explorer(repo)
    assert page.count("</script>") == page.count("<script")
    assert any("x</script><!--.py" in e[0] for e in _island(page)["edges"])


def test_mermaid_version_is_defined_once_and_never_in_the_js() -> None:
    """AC4."""
    hits = [ln for p in (REPO / "src").rglob("*.py") for ln in p.read_text().splitlines()
            if ln.startswith("MERMAID_VERSION =")]
    assert len(hits) == 1
    assert not re.search(rf"MERMAID_VERSION|{re.escape(html.MERMAID_VERSION)}", EXPLORER_JS.read_text())
    assert "MERMAID_VERSION" in (REPO / "src/aa_ma/render/explorer.py").read_text()


# ---------------------------------------------------------------------
# Index state (Ste 2026-09-26): refuse missing/too-old; banner when stale
# ---------------------------------------------------------------------

def test_no_index_refuses_naming_the_remedy(repo: Path, capsys, monkeypatch) -> None:
    shutil.rmtree(repo / ".codemem")
    monkeypatch.chdir(repo)
    assert render_main(["--explorer"]) == 2
    assert "codemem build" in capsys.readouterr().err
    assert not (repo / "build").exists()


def test_a_too_old_index_refuses(repo: Path, capsys) -> None:
    conn = sqlite3.connect(repo / ".codemem/index.db")
    conn.execute("PRAGMA user_version = 2")
    conn.commit()
    conn.close()
    assert render_main(["--explorer", "--repo-root", str(repo), "--out", str(repo / "out")]) == 2
    assert "codemem build" in capsys.readouterr().err
    assert not (repo / "out").exists()


def test_an_unreadable_index_refuses_not_a_traceback(repo: Path, capsys) -> None:
    """§6.8: a schema-v3 file missing tables is 'unreadable' — exit 2, nothing written."""
    db = repo / ".codemem/index.db"
    db.unlink()
    conn = sqlite3.connect(db)
    conn.executescript("CREATE TABLE files(id INTEGER PRIMARY KEY, path TEXT, mtime INTEGER, lang TEXT); PRAGMA user_version = 3;")
    conn.close()
    assert render_main(["--explorer", "--repo-root", str(repo), "--out", str(repo / "out")]) == 2
    assert "codemem build" in capsys.readouterr().err
    assert not (repo / "out").exists()


def test_the_lint_never_depends_on_the_explorer() -> None:
    """§6.8: cli.py hosts aa-ma-lint-views (read by the §6.7 HARD item); a broken explorer
    must not break it, so explorer.py is imported only when --explorer runs."""
    code = "import sys; sys.modules['aa_ma.render.explorer'] = None; from aa_ma.render.cli import lint_main"
    run = subprocess.run(["uv", "run", "--quiet", "python", "-c", code], cwd=REPO, capture_output=True, text=True)
    assert run.returncode == 0, run.stderr


def test_a_write_error_is_printable(repo: Path, tmp_path: Path, capsys) -> None:
    blocker = tmp_path / "f"
    blocker.write_text("")
    assert render_main(["--explorer", "--repo-root", str(repo), "--out", str(blocker / "x\x1b[2Jy")]) == 2
    err = capsys.readouterr().err
    assert "\x1b" not in err and "aa-ma-render:" in err


def test_a_stale_index_writes_a_banner_and_warns(repo: Path, capsys) -> None:
    os.utime(repo / "src/app/b.py", (4_000_000_000, 4_000_000_000))
    assert render_main(["--explorer", "--repo-root", str(repo), "--out", str(repo / "out")]) == 0
    page = (repo / "out/explorer.html").read_text()
    assert "changed since indexing" in _island(page)["stale"]
    assert "codemem build" in capsys.readouterr().err


# ---------------------------------------------------------------------
# CLI (AC1, AC7)
# ---------------------------------------------------------------------

def test_explorer_writes_build_explorer_html_by_default(repo: Path, capsys, monkeypatch) -> None:
    monkeypatch.chdir(repo)
    assert render_main(["--explorer"]) == 0
    assert (repo / "build/explorer.html").is_file()
    assert "build/explorer.html" in capsys.readouterr().out


def test_explorer_and_markdown_sources_are_exclusive() -> None:
    assert render_main(["--explorer", str(REPO / "README.md")]) == 2


def test_build_is_never_committed() -> None:
    """AC7: build/ stays untracked — git ignores the explorer's default output."""
    rc = subprocess.run(["git", "-C", str(REPO), "check-ignore", "-q", "build/explorer.html"]).returncode
    assert rc == 0


# ---------------------------------------------------------------------
# The JS contract suite, run from pytest when node is present (the CI node job always runs it)
# ---------------------------------------------------------------------

def test_the_js_contract_suite_passes(repo: Path, tmp_path: Path) -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node not installed — the explorer-contract CI job runs this suite")
    page = tmp_path / "explorer.html"
    page.write_text(explorer.build_explorer(repo)[0], encoding="utf-8")
    run = subprocess.run([node, "--test", str(CONTRACT)], capture_output=True, text=True,
                         env={**os.environ, "EXPLORER_HTML": str(page)}, timeout=120)
    assert run.returncode == 0, run.stdout + run.stderr
