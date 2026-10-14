"""X2 staleness envelope on every codemem MCP response (code-conventions-impact M15.3).

Report 03 X2: ``index_sha``, ``head_sha``, ``stale`` (true|false|unknown) and
``stale_reason`` are added once, in the server's ``_with_autobuild`` wrapper.
The 15.2 stale paths are asserted here through the real FastMCP dispatch.
"""

from __future__ import annotations

import asyncio
import importlib.util
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from codemem.indexer import build_index

REPO_ROOT = Path(__file__).resolve().parents[2]
FIELDS = {"index_sha", "head_sha", "stale", "stale_reason"}


@pytest.fixture(scope="module")
def server_mod():
    path = REPO_ROOT / "claude-code" / "codemem" / "mcp" / "server.py"
    spec = importlib.util.spec_from_file_location("codemem_mcp_server_x2", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run(server, name: str, kwargs: dict) -> dict:
    async def call() -> dict:
        tool = await server.get_tool(name)
        return (await tool.run(kwargs)).structured_content

    return asyncio.run(call())


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def _commit(root: Path) -> str:
    _git(root, "add", "-A")
    _git(root, "-c", "user.email=t@x", "-c", "user.name=T", "commit", "-qm", "c")
    return _git(root, "rev-parse", "HEAD")


@pytest.fixture
def env(tmp_path: Path, monkeypatch) -> tuple[Path, Path]:
    root = tmp_path / "r"
    root.mkdir()
    (root / ".gitignore").write_text(".codemem/\n")
    (root / "a.py").write_text("def helper():\n    return 1\n")
    _git(root, "init", "-q", "-b", "main")
    _commit(root)
    db_path = root / ".codemem" / "index.db"
    build_index(root, db_path)
    monkeypatch.setenv("CODEMEM_DB", str(db_path))
    monkeypatch.setenv("CODEMEM_REPO_ROOT", str(root))
    return root, db_path


def _hold_lock(lock: Path) -> subprocess.Popen:
    code = textwrap.dedent(
        """
        import sys, time
        from pathlib import Path
        from codemem.journal.lock import acquire_writer_lock
        with acquire_writer_lock(Path(sys.argv[1])) as got:
            print("HELD" if got else "BUSY", flush=True)
            time.sleep(30)
        """
    )
    p = subprocess.Popen(
        [sys.executable, "-c", code, str(lock)], stdout=subprocess.PIPE, text=True
    )
    assert p.stdout is not None and p.stdout.readline().strip() == "HELD"
    return p


def test_fresh_response_carries_the_fields(server_mod, env):
    root, _ = env
    r = _run(server_mod.build_server(), "search_symbols", {"query": "helper"})
    assert FIELDS <= set(r)
    head = _git(root, "rev-parse", "HEAD")
    assert (r["stale"], r["stale_reason"], r["index_sha"], r["head_sha"]) == (
        False,
        None,
        head,
        head,
    )
    assert any(m["name"] == "helper" for m in r["matches"])


def test_c_locked_index_is_served_stale(server_mod, env):
    root, db_path = env
    (root / "b.py").write_text("def b():\n    pass\n")
    head = _commit(root)
    holder = _hold_lock(db_path.parent / "db.lock")
    try:
        r = _run(server_mod.build_server(), "search_symbols", {"query": "helper"})
    finally:
        holder.kill()
        holder.wait()
    assert (r["stale"], r["stale_reason"], r["head_sha"]) == (True, "locked", head)
    assert r["index_sha"] != head
    assert any(m["name"] == "helper" for m in r["matches"])  # results still served


def test_d_refresh_error_is_served_stale_error(server_mod, env):
    root, db_path = env
    (root / "b.py").write_text("def b():\n    pass\n")
    _commit(root)
    db_path.write_bytes(b"garbage" * 64)
    r = _run(server_mod.build_server(), "who_calls", {"name": "helper"})
    assert (r["stale"], r["stale_reason"]) == (True, "error")


def test_dirty_tree_is_refreshed_and_fresh(server_mod, env):
    root, _ = env
    (root / "a.py").write_text("def edited_live():\n    return 2\n")
    r = _run(server_mod.build_server(), "search_symbols", {"query": "edited_live"})
    assert (r["stale"], r["stale_reason"]) == (False, None)
    assert any(m["name"] == "edited_live" for m in r["matches"])


def test_no_git_is_unknown(server_mod, tmp_path, monkeypatch):
    (tmp_path / "a.py").write_text("def nogit():\n    pass\n")
    monkeypatch.setenv("CODEMEM_DB", str(tmp_path / ".codemem" / "index.db"))
    monkeypatch.setenv("CODEMEM_REPO_ROOT", str(tmp_path))
    r = _run(server_mod.build_server(), "search_symbols", {"query": "nogit"})
    assert (r["stale"], r["stale_reason"], r["head_sha"]) == ("unknown", "no_git", None)


def test_build_failure_still_carries_the_fields(server_mod, tmp_path, monkeypatch):
    phony = tmp_path / "not-a-repo"
    phony.write_text("a file, not a directory")
    monkeypatch.setenv("CODEMEM_DB", str(tmp_path / ".codemem" / "index.db"))
    monkeypatch.setenv("CODEMEM_REPO_ROOT", str(phony))
    r = _run(server_mod.build_server(), "search_symbols", {"query": "x"})
    assert r["error"].startswith("build failed:")
    assert (r["stale"], r["stale_reason"], r["index_sha"]) == (
        "unknown",
        "no_index",
        None,
    )
