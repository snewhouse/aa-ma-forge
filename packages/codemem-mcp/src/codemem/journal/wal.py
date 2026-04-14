"""Write-ahead log for crash-safe incremental refresh (M2 Task 2.3).

Implements the three-phase ordering pinned in
``codemem-reference.md §WAL JSONL Replay State Diagram``:

    1. append_intent()  — JSON line describing what we're about to do
    2. SQLite txn commit — apply the mutation (caller's responsibility)
    3. append_ack()     — JSON line marking the intent applied

Each line is written with ``O_APPEND`` so concurrent writers don't
interleave within a single write() — and each JSON line is small
(< 4KB) so POSIX guarantees atomicity per-line.

Replay walks the log in order and reconciles:

    branch 1 — entry.id in acked_ids            → skip (already applied)
    branch 2 — DB state already matches target  → idempotent skip + ack
                                                    (crash after commit,
                                                     before ack)
    branch 3 — entry.prev_user_version != DB's  → ReplayConflict
    branch 4 — apply op, commit, append ack     → forward-progress

Idempotency key: ``(op, prev_user_version, content_sha)``. For
``op="file_upsert"``, ``content_sha`` equals ``content_hash_after`` —
we check the live ``files.content_hash`` against it to decide
branch 2.
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from ..storage import db


__all__ = [
    "ENTRY_SCHEMA_VERSION",
    "WALEntry",
    "ReplayConflict",
    "append_intent",
    "append_ack",
    "read_entries",
    "read_acked_ids",
    "replay_wal",
]


ENTRY_SCHEMA_VERSION = 1


@dataclass
class WALEntry:
    id: str
    ts: str
    op: str
    args: dict[str, Any]
    prev_user_version: int
    content_sha: str
    schema_version: int = ENTRY_SCHEMA_VERSION


class ReplayConflict(RuntimeError):
    """Raised when an entry's ``prev_user_version`` doesn't match the
    current DB schema version. Signals a non-recoverable replay state."""


# ---------------------------------------------------------------------
# Append primitives — O_APPEND-safe JSON-line writes
# ---------------------------------------------------------------------

def _append_line(path: Path, payload: dict) -> None:
    """Append one JSON line atomically via O_APPEND. Creates parent
    dirs and the file itself if missing."""
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n"
    encoded = line.encode("utf-8")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        os.write(fd, encoded)
        os.fsync(fd)  # durability: ensure the line hits disk before we proceed
    finally:
        os.close(fd)


def append_intent(
    wal_path: Path,
    *,
    op: str,
    args: dict[str, Any],
    prev_user_version: int,
    content_sha: str,
) -> str:
    """Append an intent line and return its UUID.

    Caller should then perform the SQLite mutation in a transaction
    and follow up with :func:`append_ack(wal_path, entry_id)` on
    successful commit.
    """
    entry_id = uuid.uuid4().hex
    payload = {
        "id": entry_id,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime()),
        "op": op,
        "args": args,
        "prev_user_version": prev_user_version,
        "content_sha": content_sha,
        "schema_version": ENTRY_SCHEMA_VERSION,
    }
    _append_line(wal_path, payload)
    return entry_id


def append_ack(wal_path: Path, entry_id: str) -> None:
    """Append the post-commit ack for an intent."""
    _append_line(wal_path, {"ack": True, "id": entry_id})


# ---------------------------------------------------------------------
# Read helpers
# ---------------------------------------------------------------------

def _iter_lines(wal_path: Path) -> Iterator[dict]:
    if not wal_path.exists():
        return
    with wal_path.open("r", encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            try:
                yield json.loads(raw)
            except json.JSONDecodeError:
                # Truncated last line after a crash — stop rather than
                # propagate; replay will rebuild safely.
                continue


def read_entries(wal_path: Path) -> Iterator[dict]:
    """Yield every INTENT entry (ack lines filtered out)."""
    for obj in _iter_lines(wal_path):
        if obj.get("ack") is True:
            continue
        yield obj


def read_acked_ids(wal_path: Path) -> set[str]:
    """Set of entry IDs that have been acked."""
    return {
        obj["id"]
        for obj in _iter_lines(wal_path)
        if obj.get("ack") is True and "id" in obj
    }


# ---------------------------------------------------------------------
# Replay — the state diagram
# ---------------------------------------------------------------------

def replay_wal(wal_path: Path, db_path: Path) -> dict[str, int]:
    """Apply any intent that lacks an ack. Returns stats::

        {
            "total": N,
            "applied": N,                 # mutation actually executed
            "skipped_already_acked": N,   # branch 1
            "skipped_idempotent": N,      # branch 2
        }

    Raises :class:`ReplayConflict` if any unacked entry's
    ``prev_user_version`` mismatches the DB's current schema version.
    """
    acked = read_acked_ids(wal_path)
    stats = {
        "total": 0,
        "applied": 0,
        "skipped_already_acked": 0,
        "skipped_idempotent": 0,
    }

    conn = db.connect(db_path, read_only=False)
    try:
        db.apply_schema(conn)
        current_uv = conn.execute("PRAGMA user_version").fetchone()[0]

        for obj in read_entries(wal_path):
            stats["total"] += 1
            entry_id = obj.get("id", "")

            # State-first semantics (required by Task 2.4 round-trip):
            # the DB is the source of truth, not the ack log. If DB
            # state already matches the entry's target, no work is
            # needed — just verify an ack exists (appending one if not).
            if _is_idempotent(conn, obj):
                if entry_id in acked:
                    stats["skipped_already_acked"] += 1
                else:
                    # Branch 2: crash after commit, before ack append.
                    append_ack(wal_path, entry_id)
                    stats["skipped_idempotent"] += 1
                continue

            # State diverged from target. Before applying, sanity-check
            # that the entry was written against a compatible schema.
            expected_uv = obj.get("prev_user_version", -1)
            if expected_uv != current_uv:
                raise ReplayConflict(
                    f"entry {entry_id}: prev_user_version={expected_uv} "
                    f"but DB is at {current_uv}"
                )

            _apply_op(conn, obj)
            if entry_id not in acked:
                append_ack(wal_path, entry_id)
            stats["applied"] += 1
    finally:
        conn.close()
    return stats


# ---------------------------------------------------------------------
# Op dispatch
# ---------------------------------------------------------------------

def _is_idempotent(conn: sqlite3.Connection, entry: dict) -> bool:
    """Check whether the current DB state already matches the entry's
    target state. Used to detect the crash-after-commit-before-ack window.
    """
    op = entry.get("op")
    args = entry.get("args", {})
    if op == "file_upsert":
        path = args.get("path")
        target_hash = args.get("content_hash_after")
        row = conn.execute(
            "SELECT content_hash FROM files WHERE path = ?", (path,)
        ).fetchone()
        return row is not None and row[0] == target_hash
    if op == "file_delete":
        path = args.get("path")
        row = conn.execute(
            "SELECT 1 FROM files WHERE path = ?", (path,)
        ).fetchone()
        return row is None
    return False


def _apply_op(conn: sqlite3.Connection, entry: dict) -> None:
    """Apply a single WAL entry's op to the DB inside a transaction."""
    op = entry.get("op")
    args = entry.get("args", {})
    with db.transaction(conn):
        if op == "file_upsert":
            _apply_file_upsert(conn, args)
        elif op == "file_delete":
            conn.execute(
                "DELETE FROM files WHERE path = ?", (args.get("path"),)
            )
        else:
            raise ReplayConflict(f"unknown op: {op!r}")


def _apply_file_upsert(conn: sqlite3.Connection, args: dict) -> None:
    """Restore a file row + its symbols + its intra-file edges from the
    WAL entry. Replay is file-atomic: we delete any prior rows for
    this path (CASCADE cleans symbols+edges) and re-insert from the
    serialised ``parse_result``.
    """
    now = int(time.time())
    path = args.get("path")

    # Delete-then-insert keeps replay deterministic: regardless of
    # whether the file row exists or not, the end state is exactly
    # the WAL entry's payload.
    conn.execute("DELETE FROM files WHERE path = ?", (path,))
    conn.execute(
        """
        INSERT INTO files (path, lang, mtime, size, content_hash, last_indexed)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            path,
            args.get("lang", "unknown"),
            args.get("mtime", 0),
            args.get("size", 0),
            args.get("content_hash_after"),
            now,
        ),
    )
    file_id = conn.execute(
        "SELECT id FROM files WHERE path = ?", (path,)
    ).fetchone()[0]

    parse_result = args.get("parse_result") or {}
    symbols = parse_result.get("symbols", [])
    edges = parse_result.get("edges", [])

    scip_to_id: dict[str, int] = {}

    # Insert symbols; parent resolution is a second pass (parent may
    # appear later in the source file — we don't assume order).
    for sym in symbols:
        conn.execute(
            """
            INSERT OR REPLACE INTO symbols
                (file_id, scip_id, name, kind, line, signature,
                 signature_hash, docstring, parent_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL)
            """,
            (
                file_id,
                sym["scip_id"],
                sym["name"],
                sym["kind"],
                sym.get("line"),
                sym.get("signature"),
                sym.get("signature_hash"),
                sym.get("docstring"),
            ),
        )
        scip_to_id[sym["scip_id"]] = conn.execute(
            "SELECT id FROM symbols WHERE file_id = ? AND scip_id = ?",
            (file_id, sym["scip_id"]),
        ).fetchone()[0]

    # Resolve parent_id for symbols whose parent is in the same file.
    for sym in symbols:
        parent_scip = sym.get("parent_scip_id")
        if not parent_scip or parent_scip not in scip_to_id:
            continue
        conn.execute(
            "UPDATE symbols SET parent_id = ? WHERE id = ?",
            (scip_to_id[parent_scip], scip_to_id[sym["scip_id"]]),
        )

    # Insert intra-file edges — cross-file edges are the resolver's
    # job and get written when the ``resolve_cross_file_edges`` op
    # runs (see below). For replay-from-scratch the caller should
    # run the resolver op last, after all file_upserts.
    for edge in edges:
        src_id = scip_to_id.get(edge["src_scip_id"])
        if src_id is None:
            continue
        dst_id = scip_to_id.get(edge.get("dst_scip_id"))
        dst_unresolved = edge.get("dst_unresolved")
        if dst_id is None and dst_unresolved is None:
            continue
        conn.execute(
            """
            INSERT OR IGNORE INTO edges
                (src_symbol_id, dst_symbol_id, dst_unresolved, kind)
            VALUES (?, ?, ?, ?)
            """,
            (src_id, dst_id, dst_unresolved, edge.get("kind", "call")),
        )
