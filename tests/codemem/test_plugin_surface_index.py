"""plugin_edges: the plugin surface indexed into codemem (code-conventions-impact M10.3).

``codemem build`` fills ``plugin_edges`` from :func:`codemem.draw.plugin_surface.extract`
so ``who_calls`` and ``file_impact`` see ``Skill(x)`` / ``/x`` / ``subagent_type``
references as callers. ``.md`` files stay out of ``files``.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from codemem import mcp_tools
from codemem.draw.plugin_surface import extract
from codemem.draw.surface_allowlist import HOOK_TABLE
from codemem.incremental import refresh_index
from codemem.indexer import build_index
from codemem.storage import db

_INSTALL = 'AA_MA_HOOKS=(\n    "SessionStart||h-start.sh|5|"\n)\n'

# Same shape as test_plugin_surface.BASE, plus an agent, a hook and a code file.
_TREE = {
    HOOK_TABLE: _INSTALL,
    "claude-code/hooks/h-start.sh": "echo hi\n",
    "claude-code/skills/alpha/SKILL.md": "<!-- fork -->\n---\nname: Not Alpha\n---\n",
    "claude-code/skills/alpha/refs/notes.md": "detail\n",
    "claude-code/skills/gamma/SKILL.md": "Use Skill(alpha) here.\n",
    "claude-code/commands/run.md": "Skill(alpha) then Skill(gamma); run h-start.sh\n",
    "claude-code/agents/checker.md": "",
    "claude-code/rules/house.md": "subagent_type: checker\n",
    "src/app.py": "def main():\n    return 1\n",
}


def _write(root: Path, files: dict[str, str]) -> Path:
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    return root


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def _rows(db_path: Path) -> set[tuple[str, str, str, str]]:
    with db.connect(db_path, read_only=True) as conn:
        return set(conn.execute("SELECT src, dst, kind, ref_class FROM plugin_edges"))


def _has_table(conn, name: str) -> bool:
    return bool(
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
        ).fetchone()
    )


@pytest.fixture
def built(tmp_path: Path) -> tuple[Path, Path]:
    root = _write(tmp_path / "repo", _TREE)
    db_path = tmp_path / "idx" / "index.db"
    build_index(root, db_path)
    return root, db_path


# ---------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------


def test_schema_version_is_4() -> None:
    assert db.CURRENT_SCHEMA_VERSION == 4


def test_fresh_build_creates_plugin_edges_at_v4(built) -> None:
    _, db_path = built
    with db.connect(db_path, read_only=True) as conn:
        assert _has_table(conn, "plugin_edges")
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 4


def test_v3_db_migrates_to_v4(tmp_path: Path) -> None:
    conn = db.connect(tmp_path / "t.db")
    db.apply_schema(conn)
    for target, sql in db.MIGRATIONS:
        if target <= 3:
            with conn:
                conn.executescript(sql)
                conn.execute(f"PRAGMA user_version = {target}")
    assert not _has_table(conn, "plugin_edges")
    assert db.ensure_schema(conn) == 4
    assert _has_table(conn, "plugin_edges")
    conn.close()


# ---------------------------------------------------------------------
# Build-time fill
# ---------------------------------------------------------------------


def test_rows_match_extract(built) -> None:
    root, db_path = built
    want = {
        (e.src, e.dst, e.kind.value, e.ref_class.value) for e in extract(root).edges
    }
    assert want  # the fixture has references
    assert _rows(db_path) == want


def test_repo_without_claude_code_builds_with_empty_table(tmp_path: Path) -> None:
    root = _write(tmp_path / "repo", {"src/app.py": "def main():\n    return 1\n"})
    db_path = tmp_path / "idx" / "index.db"
    stats = build_index(root, db_path)
    assert stats.files_indexed == 1
    assert _rows(db_path) == set()


def test_markdown_is_not_indexed_into_files(built) -> None:
    _, db_path = built
    with db.connect(db_path, read_only=True) as conn:
        paths = {p for (p,) in conn.execute("SELECT path FROM files")}
    assert "src/app.py" in paths
    assert not any(p.endswith(".md") for p in paths)


def test_refresh_rewrites_plugin_edges_after_a_markdown_only_commit(
    tmp_path: Path,
) -> None:
    root = _write(tmp_path / "repo", {**_TREE, ".gitignore": ".codemem/\n"})
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "t@x")
    _git(root, "config", "user.name", "T")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "i")
    db_path = root / ".codemem" / "index.db"
    build_index(root, db_path)
    assert ("skill:gamma", "skill:alpha", "skill", "ON_DISK") in _rows(db_path)

    (root / "claude-code/skills/gamma/SKILL.md").write_text("No references now.\n")
    _git(root, "commit", "-qam", "drop ref")
    stats = refresh_index(root, db_path)

    assert not stats.full_rebuild  # the incremental path, not a rebuild
    assert ("skill:gamma", "skill:alpha", "skill", "ON_DISK") not in _rows(db_path)
    want = {
        (e.src, e.dst, e.kind.value, e.ref_class.value) for e in extract(root).edges
    }
    assert _rows(db_path) == want


# ---------------------------------------------------------------------
# Ownership: one rule, shared with plugin_surface
# ---------------------------------------------------------------------


@pytest.mark.parametrize(
    ("path", "owner"),
    [
        ("claude-code/skills/alpha/SKILL.md", "skill:alpha"),
        ("claude-code/skills/alpha/refs/notes.md", "skill:alpha"),
        ("claude-code/agents/checker.md", "agent:checker"),
        ("claude-code/commands/run.md", "command:run"),
        ("claude-code/rules/house.md", "rule:house"),
        ("claude-code/hooks/h-start.sh", "hook:h-start.sh"),
        ("claude-code/hooks/lib/h-lib.sh", "hook:h-lib.sh"),
        ("claude-code/skills/alpha.md", None),
        ("claude-code/agents/x/deep.md", None),
        ("claude-code/codemem/x.md", None),
        ("src/app.py", None),
    ],
)
def test_owner_of(path: str, owner: str | None) -> None:
    from codemem.draw.plugin_surface import owner_of  # RED: not yet public

    assert owner_of(path) == owner


# ---------------------------------------------------------------------
# who_calls
# ---------------------------------------------------------------------


def _plugin(callers: list[dict]) -> set[tuple[str, str]]:
    return {(c["name"], c["kind"]) for c in callers if c.get("via") == "plugin_edges"}


@pytest.mark.parametrize("target", ["alpha", "skill:alpha"])
def test_who_calls_lists_plugin_callers(built, target: str) -> None:
    _, db_path = built
    r = mcp_tools.who_calls(db_path, target)
    assert r["error"] is None
    assert _plugin(r["callers"]) == {("gamma", "skill"), ("run", "command")}
    for c in r["callers"]:
        assert c["via"] == "plugin_edges"
        assert c["file"] in {"skill:gamma", "command:run"}


def test_who_calls_agent_and_hook(built) -> None:
    _, db_path = built
    assert _plugin(mcp_tools.who_calls(db_path, "checker")["callers"]) == {
        ("house", "rule")
    }
    assert _plugin(mcp_tools.who_calls(db_path, "h-start.sh")["callers"]) == {
        ("run", "command")
    }


def test_who_calls_code_symbols_keep_their_shape(built) -> None:
    _, db_path = built
    r = mcp_tools.who_calls(db_path, "main")
    assert r["error"] is None
    assert all("via" not in c for c in r["callers"])


@pytest.mark.parametrize("bad", ["skill:al;pha", "nokind:alpha", "skill:", "a b"])
def test_who_calls_rejects_unsanitary_names(built, bad: str) -> None:
    _, db_path = built
    r = mcp_tools.who_calls(db_path, bad)
    assert r["error"]
    assert r["callers"] == []


# ---------------------------------------------------------------------
# file_impact
# ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    ["claude-code/skills/alpha/SKILL.md", "claude-code/skills/alpha/refs/notes.md"],
)
def test_file_impact_reports_plugin_callers(built, path: str) -> None:
    _, db_path = built
    r = mcp_tools.file_impact(db_path, path)
    assert r["error"] is None
    assert {(c["file"], c["name"]) for c in r["external_callers"]} == {
        ("command:run", "run"),
        ("skill:gamma", "gamma"),
    }


def test_file_impact_on_an_agent(built) -> None:
    _, db_path = built
    r = mcp_tools.file_impact(db_path, "claude-code/agents/checker.md")
    assert r["external_callers"] == [
        {"file": "rule:house", "name": "house", "via": "plugin_edges"}
    ]


def test_file_impact_tags_plugin_callers_like_who_calls(built) -> None:
    """§6.6 INFO b: a plugin caller says so (``via``), as ``who_calls`` does."""
    _, db_path = built
    r = mcp_tools.file_impact(db_path, "claude-code/skills/alpha/SKILL.md")
    assert {c.get("via") for c in r["external_callers"]} == {"plugin_edges"}


def test_file_impact_on_code_is_unchanged(built) -> None:
    _, db_path = built
    r = mcp_tools.file_impact(db_path, "src/app.py")
    assert r["error"] is None
    assert r["external_callers"] == []


def test_who_calls_plugin_callers_carry_a_null_line(built) -> None:
    """§6.8 W1: a plugin caller has every key a code caller has; ``line`` is None."""
    _, db_path = built
    r = mcp_tools.who_calls(db_path, "alpha")
    plugin = [c for c in r["callers"] if c.get("via") == "plugin_edges"]
    assert plugin
    for c in plugin:
        assert list(c) == ["name", "kind", "file", "line", "via"]
        assert c["line"] is None


def test_who_calls_callers_sort_by_file_and_line(built) -> None:
    """§6.8 W1: a consumer sorting by ``(file, line or 0)`` must not raise KeyError."""
    _, db_path = built
    for target in ("alpha", "main"):
        callers = mcp_tools.who_calls(db_path, target)["callers"]
        sorted(callers, key=lambda c: (c["file"], c["line"] or 0))
