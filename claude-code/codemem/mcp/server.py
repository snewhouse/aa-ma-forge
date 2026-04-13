"""codemem MCP server (M1 Task 1.10).

Registers 12 canonical tool slots on a FastMCP instance. M1 lights up
the first six (``who_calls``, ``blast_radius``, ``dead_code``,
``dependency_chain``, ``search_symbols``, ``file_summary``); M3 fills
in the remaining six (``hot_spots``, ``co_changes``, ``owners``,
``symbol_history``, ``layers``, ``aa_ma_context``).

The server is a thin adapter: every handler delegates straight to the
matching function in :mod:`codemem.mcp_tools`, which is where the
sanitization and SQL logic actually lives. Keeping the MCP wrapper
dumb means the same tools can be exercised from the CLI, from unit
tests, and from subprocess harnesses without spinning up a server.

Aliases are registered for Anthropic Tool Search discoverability —
agents searching for ``find_references`` hit ``who_calls``; searches
for ``find_dead_code`` hit ``dead_code``.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

from fastmcp import FastMCP

from codemem import mcp_tools


__all__ = [
    "CANONICAL_TOOL_NAMES",
    "ALIASES",
    "build_server",
    "list_registered_tool_names",
]


# 12 canonical slots — see codemem-reference.md §MCP Tools.
CANONICAL_TOOL_NAMES: tuple[str, ...] = (
    # M1 — ported from /index
    "who_calls",
    "blast_radius",
    "dead_code",
    "dependency_chain",
    "search_symbols",
    "file_summary",
    # M3 — git mining
    "hot_spots",
    "co_changes",
    "owners",
    "symbol_history",
    "layers",
    # M3 — AA-MA-native moat
    "aa_ma_context",
)


# Alias map: canonical → list of aliases registered against the same handler.
# Picked for Anthropic Tool Search discoverability (competing tools use
# these names — we register both so agents find us either way).
ALIASES: dict[str, list[str]] = {
    "who_calls": ["find_references"],
    "dead_code": ["find_dead_code"],
}


# Module-level registry tracking every name we've registered — canonical
# + aliases + any test-time insertions. Consulted by
# :func:`list_registered_tool_names` for the AC test.
_registered_names: list[str] = []


def _default_db_path() -> Path:
    """Default codemem DB location. Override via ``CODEMEM_DB`` env var."""
    env = os.environ.get("CODEMEM_DB")
    if env:
        return Path(env)
    return Path.cwd() / ".codemem" / "index.db"


def _default_repo_root() -> Path:
    env = os.environ.get("CODEMEM_REPO_ROOT")
    if env:
        return Path(env)
    return Path.cwd()


def build_server() -> FastMCP:
    """Construct a FastMCP server with the M1 tools + aliases registered."""
    server = FastMCP(name="codemem")
    _registered_names.clear()

    db_path_factory = _default_db_path
    repo_root_factory = _default_repo_root

    # ------------------------------------------------------------------
    # M1 tool handlers — each a thin wrapper over codemem.mcp_tools.*
    # ------------------------------------------------------------------

    def who_calls(name: str, max_depth: int = 3, budget: int = 8_000) -> dict:
        """Return callers of a symbol (upstream traversal)."""
        return mcp_tools.who_calls(
            db_path_factory(), name, max_depth=max_depth, budget=budget
        )

    def blast_radius(name: str, max_depth: int = 3, budget: int = 8_000) -> dict:
        """Return everything a symbol reaches (downstream transitive)."""
        return mcp_tools.blast_radius(
            db_path_factory(), name, max_depth=max_depth, budget=budget
        )

    def dead_code(budget: int = 8_000) -> dict:
        """Return function/method symbols with zero incoming call edges."""
        return mcp_tools.dead_code(db_path_factory(), budget=budget)

    def dependency_chain(
        source: str, target: str, max_depth: int = 5, budget: int = 8_000
    ) -> dict:
        """Shortest call-graph path from ``source`` to ``target``."""
        return mcp_tools.dependency_chain(
            db_path_factory(), source, target, max_depth=max_depth, budget=budget
        )

    def search_symbols(query: str, budget: int = 8_000) -> dict:
        """Substring name search (exact > prefix > contains ranking)."""
        return mcp_tools.search_symbols(
            db_path_factory(), query, budget=budget
        )

    def file_summary(path: str, budget: int = 8_000) -> dict:
        """List symbols in a file, ordered by source line."""
        return mcp_tools.file_summary(
            db_path_factory(),
            path,
            budget=budget,
            repo_root=repo_root_factory(),
        )

    # ------------------------------------------------------------------
    # Register handlers under canonical names AND their aliases.
    # ------------------------------------------------------------------
    m1_handlers: dict[str, Callable[..., dict]] = {
        "who_calls": who_calls,
        "blast_radius": blast_radius,
        "dead_code": dead_code,
        "dependency_chain": dependency_chain,
        "search_symbols": search_symbols,
        "file_summary": file_summary,
    }

    for canonical, handler in m1_handlers.items():
        server.tool(handler, name=canonical)
        _registered_names.append(canonical)
        for alias in ALIASES.get(canonical, []):
            server.tool(handler, name=alias)
            _registered_names.append(alias)

    # M3 tools (hot_spots, co_changes, owners, symbol_history, layers,
    # aa_ma_context) are intentionally NOT registered here — Task 3.2+
    # add them with git-mining logic. Listing them in
    # CANONICAL_TOOL_NAMES preserves the "12 tool slots" contract while
    # keeping the surface honest: if an agent calls one now, FastMCP
    # returns a proper "tool not found" — not a stub that returns
    # empty data.

    return server


def list_registered_tool_names() -> set[str]:
    """Return the set of names the server registered on its last build.

    Exposed for the Task 1.10 AC test; not part of the runtime MCP
    protocol surface.
    """
    # Build lazily so tests can inspect without running a server.
    if not _registered_names:
        build_server()
    return set(_registered_names)


if __name__ == "__main__":
    # Ensure `_registered_names` reflects the *running* server on
    # stdio-transport startup; no separate build step required.
    build_server().run(transport="stdio")
