"""Cross-file edge resolution (M1 Task 1.6).

Ports the four-strategy Python import resolver from
``~/.claude-code-project-index/scripts/index_utils.py``
(``build_import_map`` + ``resolve_cross_file_edges``). Given the in-memory
``ParseResult`` list produced by the indexer and the SQLite symbols table,
it upgrades each file's ``unresolved_edges`` into proper edge rows — with
``dst_symbol_id`` set when a match is found, or ``dst_unresolved`` populated
when nothing matches.

Resolution strategies (tried in order for each imported module name):

1. Direct match — ``import_map[imp]`` hits.
2. Relative to source file's directory — ``<source_dir>.<imp>``.
3. Common package prefixes — ``src.``, ``scripts.``, ``lib.``, ``app.``.
4. Suffix match — any dotted entry ending in ``.<imp>``.

Once a target file is resolved, each unresolved callee name is looked up
against that target file's symbol names; one edge is emitted per match.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable


__all__ = ["build_import_map", "resolve_cross_file_edges"]


_PACKAGE_PREFIXES: tuple[str, ...] = ("src.", "scripts.", "lib.", "app.")


def build_import_map(file_paths: Iterable[str]) -> dict[str, str]:
    """Dotted-module-name → file-path map for Python files.

    ``src/utils/helpers.py`` → ``src.utils.helpers``.
    ``src/pkg/__init__.py`` → both ``src.pkg.__init__`` AND ``src.pkg``.
    Non-Python paths are ignored.
    """
    import_map: dict[str, str] = {}
    for path in file_paths:
        if not path.endswith(".py"):
            continue
        dotted = path.replace("/", ".").removesuffix(".py")
        import_map[dotted] = path
        if path.endswith("__init__.py"):
            pkg = dotted.removesuffix(".__init__").removesuffix("__init__").rstrip(".")
            if pkg:
                import_map[pkg] = path
    return import_map


def _resolve_import(
    source_path: str,
    imp: str,
    import_map: dict[str, str],
    known_files: set[str],
) -> str | None:
    """Return the target file path for ``imp`` imported by ``source_path``,
    or ``None`` when no strategy resolves."""
    # Strategy 1 — direct
    target = import_map.get(imp)
    if target and target in known_files and target != source_path:
        return target

    # Strategy 2 — relative to source dir
    source_dir = Path(source_path).parent.as_posix()
    if source_dir and source_dir not in (".", ""):
        relative_dotted = f"{source_dir.replace('/', '.')}.{imp}"
        target = import_map.get(relative_dotted)
        if target and target in known_files and target != source_path:
            return target

    # Strategy 3 — common package prefixes
    for prefix in _PACKAGE_PREFIXES:
        target = import_map.get(f"{prefix}{imp}")
        if target and target in known_files and target != source_path:
            return target

    # Strategy 4 — suffix match
    suffix = f".{imp}"
    for dotted, mapped in import_map.items():
        if (
            dotted.endswith(suffix)
            and mapped in known_files
            and mapped != source_path
        ):
            return mapped

    return None


def resolve_cross_file_edges(
    conn: sqlite3.Connection,
    *,
    parses: list,  # list[codemem.indexer._FileParse]; typed loosely to avoid circular import
) -> dict[str, int]:
    """Emit edges for each file's ``unresolved_edges`` by resolving
    callees against imported target files. Returns stats:
    ``{"resolved": N, "unresolved": N}``.
    """
    all_paths: set[str] = {fp.rel_to_repo for fp in parses}
    import_map = build_import_map(all_paths)

    # target_file → {symbol_name: [symbol_id, ...]}
    target_lookup: dict[str, dict[str, list[int]]] = {}
    rows = conn.execute(
        """
        SELECT f.path, s.name, s.id
        FROM symbols s JOIN files f ON s.file_id = f.id
        """
    ).fetchall()
    for path, name, sid in rows:
        target_lookup.setdefault(path, {}).setdefault(name, []).append(sid)

    # src_scip_id → symbol_id (for edge FK)
    src_scip_to_id: dict[str, int] = dict(
        conn.execute("SELECT scip_id, id FROM symbols").fetchall()
    )

    edge_rows: list[tuple[int, int | None, str | None, str]] = []
    resolved = 0
    unresolved = 0

    for fp in parses:
        source_path = fp.rel_to_repo

        resolved_targets: set[str] = set()
        for imp in fp.result.imports:
            target = _resolve_import(source_path, imp, import_map, all_paths)
            if target is not None:
                resolved_targets.add(target)

        for ue in fp.result.unresolved_edges:
            src_id = src_scip_to_id.get(ue.src_scip_id)
            if src_id is None:
                continue
            callee = ue.dst_unresolved
            if callee is None:
                continue

            matched_sids: list[int] = []
            for target_path in resolved_targets:
                matched_sids.extend(target_lookup.get(target_path, {}).get(callee, []))

            if matched_sids:
                for sid in matched_sids:
                    edge_rows.append((src_id, sid, None, ue.kind))
                    resolved += 1
            else:
                edge_rows.append((src_id, None, callee, ue.kind))
                unresolved += 1

    if edge_rows:
        conn.executemany(
            """
            INSERT OR IGNORE INTO edges
                (src_symbol_id, dst_symbol_id, dst_unresolved, kind)
            VALUES (?, ?, ?, ?)
            """,
            edge_rows,
        )

    return {"resolved": resolved, "unresolved": unresolved}
