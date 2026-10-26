"""codemem MCP server (M1 Task 1.10).

Registers 14 canonical tool slots on a FastMCP instance. M1 lights up
the first six (``who_calls``, ``blast_radius``, ``dead_code``,
``dependency_chain``, ``search_symbols``, ``file_summary``); M3 adds
six more (``hot_spots``, ``co_changes``, ``owners``, ``symbol_history``,
``layers``, ``aa_ma_context``); diagram-generation M13 adds ``diagram``;
code-conventions-impact M10.2 adds ``callees``, and ``blast_radius``
becomes its deprecated alias (removed after v0.18.x).

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

import functools
import logging
import os
from pathlib import Path
from typing import Any, Callable

from fastmcp import FastMCP

from codemem import mcp_tools
from codemem.paths import resolve_db_path

logger = logging.getLogger(__name__)


__all__ = [
    "CANONICAL_TOOL_NAMES",
    "ALIASES",
    "build_server",
    "list_registered_tool_names",
]


# 14 canonical slots — see codemem-reference.md §MCP Tools (+ diagram, M13; + callees, M10.2).
CANONICAL_TOOL_NAMES: tuple[str, ...] = (
    # M1 — ported from /index
    "who_calls",
    "blast_radius",
    "dead_code",
    "dependency_chain",
    "search_symbols",
    "file_summary",
    # code-conventions-impact M10.2 — blast_radius under its honest name
    "callees",
    # M3 — git mining
    "hot_spots",
    "co_changes",
    "owners",
    "symbol_history",
    "layers",
    # M3 — AA-MA-native moat
    "aa_ma_context",
    # diagram-generation M13 — the MCP door onto `codemem draw`
    "diagram",
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
    """``CODEMEM_DB``, else the repo root's dir in the XDG cache (M16); always absolute."""
    return resolve_db_path(_default_repo_root())


def _default_repo_root() -> Path:
    """``CODEMEM_REPO_ROOT``, else cwd; always absolute (the refresh runs elsewhere)."""
    return Path(os.environ.get("CODEMEM_REPO_ROOT") or Path.cwd()).absolute()


def build_server() -> FastMCP:  # noqa: C901  # why: pre-existing (21 before M15.3); refactor tracked in TODOS.md (M8.2 D8 pay-down)
    """Construct a FastMCP server with the M1 tools + aliases registered."""
    server = FastMCP(name="codemem")
    _registered_names.clear()

    db_path_factory = _default_db_path
    repo_root_factory = _default_repo_root

    # ------------------------------------------------------------------
    # Build-if-missing + bounded refresh before every query (M3.5 Task
    # 3.5.3; M15.2-15.3). The logic lives in
    # :func:`codemem.mcp_tools.ensure_fresh` so the plugin surface stays on
    # the mcp_tools-only layering contract. Its freshness fields are added
    # to every response (X2); with no DB to serve, the error dict is
    # returned with them.
    # ------------------------------------------------------------------

    def _ensure_fresh() -> dict:
        return mcp_tools.ensure_fresh(db_path_factory(), repo_root_factory())

    # ------------------------------------------------------------------
    # M1 tool handlers — each a thin wrapper over codemem.mcp_tools.*
    # ------------------------------------------------------------------

    def who_calls(
        name: str, max_depth: int = 3, budget: int = mcp_tools._DEFAULT_BUDGET
    ) -> dict:
        """Return callers of a symbol (upstream traversal).

        ``name`` may also be a plugin node (skill/command/agent/rule/hook stem, or
        ``<kind>:<stem>``). Code callers come first as ``{name, kind, file, line}``;
        plugin callers follow with ``via: "plugin_edges"``, ``file`` = the caller's
        node id (e.g. ``skill:gamma``) and ``line: null``.
        """
        return mcp_tools.who_calls(
            db_path_factory(), name, max_depth=max_depth, budget=budget
        )

    def callees(
        name: str, max_depth: int = 3, budget: int = mcp_tools._DEFAULT_BUDGET
    ) -> dict:
        """Return the symbols a symbol calls, transitively (downstream)."""
        return mcp_tools.callees(
            db_path_factory(), name, max_depth=max_depth, budget=budget
        )

    def blast_radius(
        name: str, max_depth: int = 3, budget: int = mcp_tools._DEFAULT_BUDGET
    ) -> dict:
        """Deprecated: use callees; removed after v0.18.x. Same payload, plus ``downstream``."""
        return mcp_tools.blast_radius(
            db_path_factory(), name, max_depth=max_depth, budget=budget
        )

    def dead_code(budget: int = mcp_tools._DEFAULT_BUDGET) -> dict:
        """Return function/method symbols with zero incoming call edges."""
        return mcp_tools.dead_code(db_path_factory(), budget=budget)

    def dependency_chain(
        source: str,
        target: str,
        max_depth: int = 5,
        budget: int = mcp_tools._DEFAULT_BUDGET,
    ) -> dict:
        """Shortest call-graph path from ``source`` to ``target``."""
        return mcp_tools.dependency_chain(
            db_path_factory(), source, target, max_depth=max_depth, budget=budget
        )

    def search_symbols(query: str, budget: int = mcp_tools._DEFAULT_BUDGET) -> dict:
        """Substring name search (exact > prefix > contains ranking)."""
        return mcp_tools.search_symbols(db_path_factory(), query, budget=budget)

    def file_summary(path: str, budget: int = mcp_tools._DEFAULT_BUDGET) -> dict:
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
        window_days: int = 90, top_n: int = 10, budget: int = mcp_tools._DEFAULT_BUDGET
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
        budget: int = mcp_tools._DEFAULT_BUDGET,
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
        budget: int = mcp_tools._DEFAULT_BUDGET,
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
        budget: int = mcp_tools._DEFAULT_BUDGET,
    ) -> dict:
        """``git log -L:<name>:<file>`` summary per file containing ``name``."""
        return mcp_tools.symbol_history(
            db_path_factory(),
            name,
            file_path=file_path,
            repo_root=repo_root_factory(),
            budget=budget,
        )

    def layers(budget: int = mcp_tools._DEFAULT_BUDGET) -> dict:
        """Bucket files into core/middle/periphery by in-degree; render onion."""
        return mcp_tools.layers(db_path_factory(), budget=budget)

    def aa_ma_context(
        task_name: str, write: bool = False, budget: int = mcp_tools._DEFAULT_BUDGET
    ) -> dict:
        """Validate an AA-MA task; assemble a code-intel context pack."""
        return mcp_tools.aa_ma_context(
            db_path_factory(),
            task_name,
            repo_root=repo_root_factory(),
            write=write,
            budget=budget,
        )

    def diagram(
        level: str = "L2",
        scope: str | None = None,
        hops: int = 1,
        budget: int = mcp_tools._DEFAULT_BUDGET,
    ) -> dict:
        """Mermaid flowchart of the code graph at L0-L3, sized to ``budget`` tokens.

        Over budget it collapses to a coarser level (``collapsed_from``) while that
        level still has edges, else truncates; ``dropped`` counts edges not drawn.
        """
        return mcp_tools.diagram(
            db_path_factory(), level=level, scope=scope, hops=hops, budget=budget
        )

    # ------------------------------------------------------------------
    # Register handlers under canonical names AND their aliases.
    # ------------------------------------------------------------------
    m1_handlers: dict[str, Callable[..., dict]] = {
        "who_calls": who_calls,
        "blast_radius": blast_radius,
        "callees": callees,
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
        "diagram": diagram,
    }

    def _with_autobuild(handler: Callable[..., dict]) -> Callable[..., dict]:
        """Decorator: run ``_ensure_fresh`` first, then add its X2 fields.

        Every response gains ``index_sha``, ``head_sha``, ``stale``
        (true|false|"unknown") and ``stale_reason`` (report 03 X2).
        ``functools.wraps`` propagates the original signature via
        ``__wrapped__`` so FastMCP's introspection (which uses
        ``inspect.signature``) still sees the tool's real parameter list
        — the ``**kwargs`` in the wrapper is the runtime dispatch surface.
        """

        @functools.wraps(handler)
        def wrapper(**kwargs: Any) -> dict:
            fresh = _ensure_fresh()
            if "error" in fresh:
                return fresh
            try:
                result = handler(**kwargs)
            except Exception as exc:  # noqa: BLE001  # why: tool-surface contract — an error dict, never a raise (e.g. a corrupt index)
                logger.warning("codemem tool failed: %s", type(exc).__name__)
                result = {"error": f"query failed: {exc.__class__.__name__}: {exc}"}
            return {**result, **fresh}

        return wrapper

    for handlers in (m1_handlers, m3_handlers):
        for canonical, handler in handlers.items():
            wrapped = _with_autobuild(handler)
            server.tool(wrapped, name=canonical)
            _registered_names.append(canonical)
            for alias in ALIASES.get(canonical, []):
                server.tool(wrapped, name=alias)
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
