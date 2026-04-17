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
    # M3 tool handlers (wired in M3.5 Task 3.5.1, 2026-04-17).
    # ------------------------------------------------------------------

    def hot_spots(
        window_days: int = 90, top_n: int = 10, budget: int = 8_000
    ) -> dict:
        """Top-N files by (commits in window) × (function_count)."""
        return mcp_tools.hot_spots(
            db_path_factory(),
            window_days=window_days,
            top_n=top_n,
            budget=budget,
        )

    def co_changes(
        file_path: str,
        threshold: int = 3,
        top_n: int = 50,
        budget: int = 8_000,
    ) -> dict:
        """Files co-changing with ``file_path`` that lack an import edge."""
        return mcp_tools.co_changes(
            db_path_factory(),
            file_path,
            threshold=threshold,
            top_n=top_n,
            budget=budget,
        )

    def owners(
        path: str,
        refresh: bool = False,
        skip: bool = False,
        budget: int = 8_000,
    ) -> dict:
        """Per-author line-count percentages for a file or directory."""
        return mcp_tools.owners(
            db_path_factory(),
            path,
            repo_root=repo_root_factory(),
            refresh=refresh,
            skip=skip,
            budget=budget,
        )

    def symbol_history(
        name: str,
        file_path: str | None = None,
        budget: int = 8_000,
    ) -> dict:
        """``git log -L:<name>:<file>`` summary per file containing ``name``."""
        return mcp_tools.symbol_history(
            db_path_factory(),
            name,
            file_path=file_path,
            repo_root=repo_root_factory(),
            budget=budget,
        )

    def layers(budget: int = 8_000) -> dict:
        """Bucket files into core/middle/periphery by in-degree; render onion."""
        return mcp_tools.layers(db_path_factory(), budget=budget)

    def aa_ma_context(
        task_name: str, write: bool = False, budget: int = 8_000
    ) -> dict:
        """Validate an AA-MA task; assemble a code-intel context pack."""
        return mcp_tools.aa_ma_context(
            db_path_factory(),
            task_name,
            repo_root=repo_root_factory(),
            write=write,
            budget=budget,
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

    m3_handlers: dict[str, Callable[..., dict]] = {
        "hot_spots": hot_spots,
        "co_changes": co_changes,
        "owners": owners,
        "symbol_history": symbol_history,
        "layers": layers,
        "aa_ma_context": aa_ma_context,
    }

    for handlers in (m1_handlers, m3_handlers):
        for canonical, handler in handlers.items():
            server.tool(handler, name=canonical)
            _registered_names.append(canonical)
            for alias in ALIASES.get(canonical, []):
                server.tool(handler, name=alias)
                _registered_names.append(alias)

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
