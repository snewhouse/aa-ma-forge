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


def _package_dir(
    source_path: str,
    module: str | None,
    level: int,
    import_map: dict[str, str],
    known_files: set[str],
) -> str | None:
    """The directory whose modules ``from <module> import <name>`` can name (M8).

    Derived from the module's OWN resolution, never an independent search: ``from
    typing import Any`` can reach an in-repo ``Any.py`` only if ``typing`` itself
    resolved to an in-repo package. ``from . import x`` is the importer's directory;
    each further dot climbs one level.
    """
    if module is None:
        parts = Path(source_path).parent.parts
        if level < 1 or level - 1 > len(parts):
            return None
        return "/".join(parts[: len(parts) - (level - 1)])
    target = _resolve_import(source_path, module, import_map, known_files)
    if target is None or not target.endswith("__init__.py"):
        return None
    return Path(target).parent.as_posix()


def _submodule(pkg_dir: str, name: str, known_files: set[str]) -> str | None:
    prefix = f"{pkg_dir}/" if pkg_dir not in ("", ".") else ""
    return next(
        (p for p in (f"{prefix}{name}.py", f"{prefix}{name}/__init__.py") if p in known_files), None
    )


def _lookup_name(callee: str, qualified_heads: set[str]) -> str | None:
    """Symbol name to match for ``callee``, or ``None`` if it is too
    ambiguous to resolve. ``helper`` and ``mod.helper`` match ``helper``
    (single-Name receiver, as before dotted callees were kept); a deeper
    chain matches only when its receiver is an imported module
    (``os.path.join``), so ``self.conn.execute`` never binds to an
    unrelated ``execute``."""
    head, dot, name = callee.rpartition(".")
    if not dot or "." not in head or head in qualified_heads:
        return name
    return None


def _persist_import_edges(
    conn: sqlite3.Connection, parses: list
) -> tuple[dict[str, set[str]], dict[str, dict[str, str]]]:
    """Replace each parsed file's ``file_edges`` import rows; return
    ``{source_path: {resolved target paths}}`` and ``{source_path: {local name:
    submodule path}}`` for call-edge resolution.

    Resolves against EVERY indexed path, not just ``parses``: an
    incremental refresh passes only the dirty files, and an import of an
    unchanged file must still resolve. The explicit DELETE is what keeps
    an edit-in-place idempotent — the ``files`` row survives an edit, so
    ON DELETE CASCADE never fires.
    """
    path_to_fid: dict[str, int] = dict(conn.execute("SELECT path, id FROM files"))
    import_map = build_import_map(path_to_fid)
    known = set(path_to_fid)
    rows: list[tuple[int, int | None, str | None]] = []
    targets: dict[str, set[str]] = {}
    submodules: dict[str, dict[str, str]] = {}
    src_fids: list[tuple[int]] = []
    for fp in parses:
        src = fp.rel_to_repo
        resolved = targets.setdefault(src, set())
        src_fid = path_to_fid.get(src)
        if src_fid is not None:
            src_fids.append((src_fid,))
        for imp in fp.result.imports:
            target = _resolve_import(src, imp, import_map, known)
            if target is not None:
                resolved.add(target)
            if src_fid is None:
                continue
            if target is None:
                rows.append((src_fid, None, imp))
            else:
                rows.append((src_fid, path_to_fid[target], None))
        # `imports` carries only `pkg` for `from pkg import sub`; an imported name that is
        # a module gets its own edge (and its local name binds calls to it alone). A name
        # that is not a module (a function) adds nothing — `pkg` is already recorded.
        local_to_module = submodules.setdefault(src, {})
        for module, level, names in fp.result.from_imports:
            pkg_dir = _package_dir(src, module, level, import_map, known)
            if pkg_dir is None:
                continue
            for name, local in names:
                target = _submodule(pkg_dir, name, known)
                if target is None or target == src:
                    continue
                resolved.add(target)
                local_to_module[local] = target
                if src_fid is not None:
                    rows.append((src_fid, path_to_fid[target], None))
    conn.executemany("DELETE FROM file_edges WHERE src_file_id = ?", src_fids)
    conn.executemany(
        """
        INSERT OR IGNORE INTO file_edges
            (src_file_id, dst_file_id, dst_unresolved, kind)
        VALUES (?, ?, ?, 'import')
        """,
        rows,
    )
    return targets, submodules


def resolve_cross_file_edges(
    conn: sqlite3.Connection,
    *,
    parses: list,  # list[codemem.indexer._FileParse]; typed loosely to avoid circular import
) -> dict[str, int]:
    """Emit edges for each file's ``unresolved_edges`` by resolving
    callees against imported target files. Returns stats:
    ``{"resolved": N, "unresolved": N}``.
    """
    targets_by_file, submodules_by_file = _persist_import_edges(conn, parses)

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
        resolved_targets = targets_by_file[fp.rel_to_repo]
        submodules = submodules_by_file.get(fp.rel_to_repo, {})
        qualified_heads = set(fp.result.imports) | set(fp.result.import_aliases.values())
        for ue in fp.result.unresolved_edges:
            src_id = src_scip_to_id.get(ue.src_scip_id)
            if src_id is None:
                continue
            callee = ue.dst_unresolved
            if callee is None:
                continue

            head, dot, rest = callee.partition(".")
            if dot and head in submodules:  # `y.run()`, y a submodule: bind in y alone
                search: Iterable[str] = (submodules[head],)
                lookup_name = rest.rpartition(".")[2]
            else:
                search = resolved_targets
                lookup_name = _lookup_name(callee, qualified_heads)
            matched_sids: list[int] = []
            if lookup_name is not None:
                for target_path in search:
                    matched_sids.extend(
                        target_lookup.get(target_path, {}).get(lookup_name, [])
                    )

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
