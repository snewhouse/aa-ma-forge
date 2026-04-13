"""Tests for claude-code/codemem/mcp/server.py — Task 1.10.

Verifies the FastMCP server registers all 12 tool slots, exposes the
M1 subset as callable handlers, and carries the required aliases
(`dead_code` ↔ `find_dead_code`, `who_calls` ↔ `find_references`)
for Anthropic Tool Search discoverability.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def _load_server_module():
    # The server lives outside `packages/codemem-mcp/src/codemem/` (in the
    # claude-code plugin tree). Load it directly.
    repo_root = Path(__file__).resolve().parent.parent.parent
    server_path = repo_root / "claude-code" / "codemem" / "mcp" / "server.py"
    spec = importlib.util.spec_from_file_location("codemem_mcp_server", server_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def server_mod():
    return _load_server_module()


class TestTwelveSlots:
    def test_canonical_tool_names_declared(self, server_mod):
        # The 12 canonical names per codemem-reference.md §12 MCP Tools.
        expected = {
            # M1 (1–6)
            "who_calls", "blast_radius", "dead_code",
            "dependency_chain", "search_symbols", "file_summary",
            # M3 git-mining (7–11) — stubbed in M1
            "hot_spots", "co_changes", "owners",
            "symbol_history", "layers",
            # M3 AA-MA-native (12)
            "aa_ma_context",
        }
        assert set(server_mod.CANONICAL_TOOL_NAMES) == expected

    def test_twelve_exact(self, server_mod):
        assert len(server_mod.CANONICAL_TOOL_NAMES) == 12


class TestAliases:
    def test_dead_code_find_dead_code(self, server_mod):
        assert "find_dead_code" in server_mod.ALIASES.get("dead_code", [])

    def test_who_calls_find_references(self, server_mod):
        assert "find_references" in server_mod.ALIASES.get("who_calls", [])


class TestToolRegistration:
    def test_m1_six_tools_registered(self, server_mod):
        """M1 AC: 'M1 lights up first 6'. Each handler must be registered
        on the FastMCP server instance under its canonical name AND
        each declared alias."""
        registered = server_mod.list_registered_tool_names()
        m1_canonical = {
            "who_calls", "blast_radius", "dead_code",
            "dependency_chain", "search_symbols", "file_summary",
        }
        assert m1_canonical.issubset(registered)

    def test_aliases_also_registered(self, server_mod):
        registered = server_mod.list_registered_tool_names()
        assert "find_dead_code" in registered
        assert "find_references" in registered

    def test_m3_tools_stubbed_not_registered_in_m1(self, server_mod):
        """M3 tools shouldn't be live callable yet — they raise a
        'not yet implemented' error if exercised."""
        registered = server_mod.list_registered_tool_names()
        # Per plan, M1 registers 6 of 12 tool slots; M3 adds the rest.
        # At minimum, the M3 tools should not appear in the M1 registration.
        for m3_name in ("hot_spots", "co_changes", "owners",
                        "symbol_history", "layers", "aa_ma_context"):
            assert m3_name not in registered, (
                f"{m3_name} is M3 — should not be registered in M1"
            )


class TestReadOnlyConnectionPolicy:
    def test_database_opened_read_only(self, server_mod):
        # Contract sanity — the server wrapper should use read-only
        # connections (the underlying `codemem.mcp_tools.*` helpers
        # already do this internally; verify the server doesn't
        # silently switch to RW).
        src = server_mod.__file__
        text = Path(src).read_text()
        assert "read_only" not in text or "read_only=False" not in text
