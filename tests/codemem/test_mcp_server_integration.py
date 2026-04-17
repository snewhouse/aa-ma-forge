"""Integration tests for the FastMCP server — M3.5 Task 3.5.2.

Unit tests in ``test_mcp_server.py`` verify that the 12 canonical tools
(plus aliases) are *registered* on ``build_server()``. This module
verifies they are *callable end-to-end* — i.e. an MCP client looking up
each tool via ``server.get_tool(name)`` and invoking ``tool.run(args)``
gets back a non-error ``structured_content`` dict.

This is the integration tier that M3's HARD gate missed: the public
surface (FastMCP registration + dispatch) is exercised against a
populated fixture DB for every tool.

One test file, one fixture, parameterised over all 14 reachable names.
Synchronous tests wrap async FastMCP calls via ``asyncio.run`` —
avoids a new ``pytest-asyncio`` dev dep.
"""

from __future__ import annotations

import asyncio
import importlib.util
import subprocess
import time
from pathlib import Path
from typing import Any

import pytest

from codemem.storage import apply_schema, connect, migrate, transaction


# --------------------------------------------------------------------- helpers


def _load_server_module():
    """Load the plugin-surface server from disk (it lives outside the
    ``packages/codemem-mcp/src/codemem/`` tree, so an import-by-path is
    required — same pattern as ``test_mcp_server.py``)."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    server_path = repo_root / "claude-code" / "codemem" / "mcp" / "server.py"
    spec = importlib.util.spec_from_file_location("codemem_mcp_server", server_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_tool(server, name: str, kwargs: dict[str, Any]) -> dict:
    """Look up a tool by name on the FastMCP server and invoke it.

    Returns the tool's ``structured_content`` dict (the JSON our tools
    actually emit). Wraps FastMCP's async API via ``asyncio.run`` so the
    test stays sync."""
    async def _call() -> dict:
        tool = await server.get_tool(name)
        result = await tool.run(kwargs)
        return result.structured_content
    return asyncio.run(_call())


# --------------------------------------------------------------------- fixture


@pytest.fixture(scope="module")
def server_mod():
    return _load_server_module()


@pytest.fixture
def populated_env(tmp_path: Path, monkeypatch) -> Path:
    """Seed a v2 SQLite DB + a minimal git repo + an AA-MA task dir.

    Returns the repo root. ``CODEMEM_DB`` + ``CODEMEM_REPO_ROOT`` env
    vars are wired so the server picks up this fixture through its
    existing ``_default_*`` factories."""
    repo_root = tmp_path
    db_path = repo_root / ".codemem" / "index.db"
    db_path.parent.mkdir(parents=True)

    # --- SQLite fixture: 2 files, 2 symbols, 1 intra-graph call edge,
    #     1 commit covering both files, 1 ownership row.
    conn = connect(db_path)
    apply_schema(conn)
    migrate(conn)
    now = int(time.time())
    with transaction(conn):
        conn.execute(
            "INSERT INTO files(id, path, lang, last_indexed) "
            "VALUES (1, 'a.py', 'python', ?), (2, 'b.py', 'python', ?)",
            (now, now),
        )
        conn.execute(
            "INSERT INTO symbols(id, file_id, scip_id, name, kind, line) "
            "VALUES (1, 1, 'codemem . /a.py#foo', 'foo', 'function', 1), "
            "       (2, 2, 'codemem . /b.py#bar', 'bar', 'function', 1)"
        )
        conn.execute(
            "INSERT INTO edges(src_symbol_id, dst_symbol_id, kind) VALUES (1, 2, 'call')"
        )
        conn.execute(
            "INSERT INTO commits(sha, author_email, author_time, message) "
            "VALUES ('abc123', 't@t.dev', ?, 'seed')",
            (now,),
        )
        conn.execute(
            "INSERT INTO commit_files(commit_sha, file_path) VALUES ('abc123','a.py'), ('abc123','b.py')"
        )
        conn.execute(
            "INSERT INTO ownership(file_path, author_email, line_count, percentage, computed_at) "
            "VALUES ('a.py','t@t.dev', 10, 100.0, ?)",
            (now,),
        )
    conn.close()

    # --- Real git repo: symbol_history shells out to `git log -L` and
    #     needs a valid working tree. Empty result is fine for the
    #     reachability contract.
    (repo_root / "a.py").write_text("def foo():\n    pass\n")
    (repo_root / "b.py").write_text("def bar():\n    pass\n")
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t.dev", "-c", "user.name=t",
         "add", "a.py", "b.py"], cwd=repo_root, check=True,
    )
    subprocess.run(
        ["git", "-c", "user.email=t@t.dev", "-c", "user.name=t",
         "commit", "-q", "-m", "seed"],
        cwd=repo_root, check=True,
    )

    # --- AA-MA task dir for aa_ma_context. Adversarial-safe mentions:
    #     a.py exists on disk; "foo" exists in the symbols table.
    task_dir = repo_root / ".claude" / "dev" / "active" / "demo"
    task_dir.mkdir(parents=True)
    (task_dir / "demo-tasks.md").write_text("# demo\n\n`a.py` — work here on `foo`.\n")
    (task_dir / "demo-reference.md").write_text("# ref\n\nThe `foo` function is the anchor.\n")

    # --- Wire env vars — the server's _default_db_path + _default_repo_root
    #     honour these.
    monkeypatch.setenv("CODEMEM_DB", str(db_path))
    monkeypatch.setenv("CODEMEM_REPO_ROOT", str(repo_root))

    return repo_root


# --------------------------------------------------------------------- tests


# Tool name → args for a one-shot, non-error invocation. Each entry is the
# minimal keyword set needed to return a valid payload against the fixture.
_TOOL_CASES: list[tuple[str, dict[str, Any]]] = [
    # M1 — ported from /index
    ("who_calls",        {"name": "bar"}),
    ("blast_radius",     {"name": "foo"}),
    ("dead_code",        {}),
    ("dependency_chain", {"source": "foo", "target": "bar"}),
    ("search_symbols",   {"query": "foo"}),
    ("file_summary",     {"path": "a.py"}),
    # M3 — git mining (wired in Task 3.5.1)
    ("hot_spots",        {}),
    ("co_changes",       {"file_path": "a.py", "threshold": 1}),
    ("owners",           {"path": "a.py"}),
    ("symbol_history",   {"name": "foo", "file_path": "a.py"}),
    ("layers",           {}),
    # M3 — AA-MA-native moat
    ("aa_ma_context",    {"task_name": "demo"}),
    # Aliases (same handler wired under an alternate discoverability name)
    ("find_references",  {"name": "bar"}),   # → who_calls
    ("find_dead_code",   {}),                # → dead_code
]


class TestAllToolsCallableViaFastMCP:
    @pytest.mark.parametrize("tool_name,kwargs", _TOOL_CASES,
                             ids=[t[0] for t in _TOOL_CASES])
    def test_tool_returns_non_error_dict(self, server_mod, populated_env, tool_name, kwargs):
        server = server_mod.build_server()
        payload = _run_tool(server, tool_name, kwargs)

        assert isinstance(payload, dict), (
            f"{tool_name} did not return a dict (got {type(payload).__name__})"
        )
        # Tools embed errors as `{"error": "<reason>", ...}` rather than
        # raising. The reachability contract is "no error surface leaks
        # out of the server layer" — missing-key and empty-string are
        # both 'no error'. Schema mismatches at the MCP boundary would
        # surface here as exceptions and fail the test naturally.
        err = payload.get("error")
        assert err in (None, ""), (
            f"{tool_name} returned error: {err!r} (payload keys: {list(payload)})"
        )


class TestCanonicalSurfaceCoverage:
    """Guards against silent drift — every name in ``CANONICAL_TOOL_NAMES``
    plus every declared alias must appear in the parametrised test list.
    If this fails after adding a new tool, add the corresponding
    ``_TOOL_CASES`` entry."""

    def test_every_canonical_tool_has_a_case(self, server_mod):
        covered = {name for name, _ in _TOOL_CASES}
        missing = set(server_mod.CANONICAL_TOOL_NAMES) - covered
        assert not missing, f"Integration test missing entries for: {sorted(missing)}"

    def test_every_alias_has_a_case(self, server_mod):
        covered = {name for name, _ in _TOOL_CASES}
        aliases = {a for lst in server_mod.ALIASES.values() for a in lst}
        missing = aliases - covered
        assert not missing, f"Integration test missing alias entries for: {sorted(missing)}"
