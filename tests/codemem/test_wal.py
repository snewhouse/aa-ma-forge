"""Tests for codemem.journal.wal — Task 2.3.

Covers: entry schema validation, O_APPEND atomicity, intent→commit→ack
ordering, idempotency keys, replay state diagram (acked skip /
already-applied skip / apply path / ReplayConflict), crash-injection
between intent and commit.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from codemem.journal.wal import (
    ENTRY_SCHEMA_VERSION,
    ReplayConflict,
    WALEntry,
    append_ack,
    append_intent,
    read_acked_ids,
    read_entries,
    replay_wal,
)
from codemem.storage import db


# ---------------------------------------------------------------------
# Entry schema + append contract
# ---------------------------------------------------------------------

class TestEntrySchema:
    def test_append_intent_returns_uuid(self, tmp_path: Path):
        wal = tmp_path / "wal.jsonl"
        entry_id = append_intent(
            wal,
            op="file_upsert",
            args={"path": "a.py", "content_hash_after": "deadbeef"},
            prev_user_version=1,
            content_sha="deadbeef",
        )
        assert isinstance(entry_id, str)
        assert len(entry_id) >= 32  # uuid4 hex is 32 chars

    def test_entry_has_required_fields(self, tmp_path: Path):
        wal = tmp_path / "wal.jsonl"
        append_intent(
            wal,
            op="file_upsert",
            args={"path": "a.py"},
            prev_user_version=1,
            content_sha="abc",
        )
        entries = list(read_entries(wal))
        assert len(entries) == 1
        entry = entries[0]
        for field in ("id", "ts", "op", "args", "prev_user_version",
                      "content_sha", "schema_version"):
            assert field in entry, f"entry missing field: {field}"
        assert entry["schema_version"] == ENTRY_SCHEMA_VERSION

    def test_append_ack_writes_ack_line(self, tmp_path: Path):
        wal = tmp_path / "wal.jsonl"
        eid = append_intent(
            wal, op="file_upsert", args={}, prev_user_version=1, content_sha="x"
        )
        append_ack(wal, eid)
        acked = read_acked_ids(wal)
        assert eid in acked

    def test_multiple_appends_all_persisted(self, tmp_path: Path):
        wal = tmp_path / "wal.jsonl"
        ids = [
            append_intent(
                wal, op="file_upsert", args={"i": i},
                prev_user_version=1, content_sha=f"h{i}",
            )
            for i in range(5)
        ]
        entries = list(read_entries(wal))
        assert [e["id"] for e in entries] == ids


# ---------------------------------------------------------------------
# Ordering: intent → commit → ack
# ---------------------------------------------------------------------

class TestOrdering:
    def test_ack_follows_intent_in_file(self, tmp_path: Path):
        wal = tmp_path / "wal.jsonl"
        eid = append_intent(
            wal, op="file_upsert", args={}, prev_user_version=1, content_sha="x",
        )
        append_ack(wal, eid)
        # The file should have TWO lines: intent then ack.
        lines = wal.read_text().splitlines()
        assert len(lines) == 2
        j0 = json.loads(lines[0])
        j1 = json.loads(lines[1])
        assert "ack" not in j0  # first line is the intent
        assert j1.get("ack") is True  # second is the ack
        assert j1["id"] == eid


# ---------------------------------------------------------------------
# Read helpers
# ---------------------------------------------------------------------

class TestReadHelpers:
    def test_read_entries_ignores_acks(self, tmp_path: Path):
        wal = tmp_path / "wal.jsonl"
        eid_a = append_intent(wal, op="o", args={}, prev_user_version=1, content_sha="a")
        eid_b = append_intent(wal, op="o", args={}, prev_user_version=1, content_sha="b")
        append_ack(wal, eid_a)
        entries = list(read_entries(wal))
        assert [e["id"] for e in entries] == [eid_a, eid_b]  # both intents returned

    def test_read_acked_ids(self, tmp_path: Path):
        wal = tmp_path / "wal.jsonl"
        eid_a = append_intent(wal, op="o", args={}, prev_user_version=1, content_sha="a")
        append_intent(wal, op="o", args={}, prev_user_version=1, content_sha="b")
        append_ack(wal, eid_a)
        assert read_acked_ids(wal) == {eid_a}

    def test_empty_wal_yields_nothing(self, tmp_path: Path):
        wal = tmp_path / "missing.jsonl"
        assert list(read_entries(wal)) == []
        assert read_acked_ids(wal) == set()


# ---------------------------------------------------------------------
# Replay state diagram
# ---------------------------------------------------------------------

def _fresh_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "index.db"
    with db.connect(db_path, read_only=False) as conn:
        db.apply_schema(conn)
    return db_path


class TestReplayStateDiagram:
    def test_already_acked_entry_with_matching_state_skipped(self, tmp_path: Path):
        """State-first branch: DB matches target AND entry is acked →
        skipped_already_acked. This is the normal steady-state replay
        after a clean shutdown."""
        wal = tmp_path / "wal.jsonl"
        db_path = _fresh_db(tmp_path)

        # Pre-populate DB to match the WAL's target state. In real use
        # this is the result of build_index (which writes the row) then
        # append_ack (which records the success).
        with db.connect(db_path, read_only=False) as conn:
            conn.execute(
                "INSERT INTO files (path, lang, mtime, size, content_hash, last_indexed) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                ("a.py", "python", 0, 0, "h1", 0),
            )
            conn.commit()

        eid = append_intent(
            wal,
            op="file_upsert",
            args={"path": "a.py", "lang": "python",
                  "content_hash_before": None, "content_hash_after": "h1",
                  "parse_result": {"symbols": [], "edges": [], "imports": []}},
            prev_user_version=1,
            content_sha="h1",
        )
        append_ack(wal, eid)

        stats = replay_wal(wal, db_path)
        assert stats["applied"] == 0
        assert stats["skipped_already_acked"] == 1

    def test_unacked_entry_applied_and_acked(self, tmp_path: Path):
        """State machine branch 3: apply + append_ack."""
        wal = tmp_path / "wal.jsonl"
        db_path = _fresh_db(tmp_path)

        append_intent(
            wal,
            op="file_upsert",
            args={
                "path": "a.py",
                "lang": "python",
                "content_hash_before": None,
                "content_hash_after": "h1",
                "mtime": 0, "size": 10,
                "parse_result": {"symbols": [], "edges": [], "imports": []},
            },
            # _fresh_db now lands at CURRENT_SCHEMA_VERSION (v2+) via
            # ensure_schema — WAL entry must match or replay raises
            # ReplayConflict (L-253).
            prev_user_version=db.CURRENT_SCHEMA_VERSION,
            content_sha="h1",
        )

        stats = replay_wal(wal, db_path)
        assert stats["applied"] == 1
        assert stats["skipped_already_acked"] == 0

        # After replay, the ack must have been appended.
        acked = read_acked_ids(wal)
        assert len(acked) == 1

        with db.connect(db_path, read_only=True) as conn:
            paths = {p for (p,) in conn.execute("SELECT path FROM files")}
            assert "a.py" in paths

    def test_already_applied_unacked_idempotent_skip(self, tmp_path: Path):
        """State machine branch 2: crash AFTER commit BEFORE ack.
        Current state already matches target — skip + ack."""
        wal = tmp_path / "wal.jsonl"
        db_path = _fresh_db(tmp_path)

        # Simulate a crash scenario: insert the file row manually (as
        # if the SQLite commit had happened), then write the WAL
        # intent WITHOUT an ack.
        with db.connect(db_path, read_only=False) as conn:
            conn.execute(
                """
                INSERT INTO files (path, lang, mtime, size, content_hash, last_indexed)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                ("a.py", "python", 0, 10, "h1", 0),
            )
            conn.commit()

        append_intent(
            wal,
            op="file_upsert",
            args={
                "path": "a.py",
                "lang": "python",
                "content_hash_before": None,
                "content_hash_after": "h1",
                "mtime": 0, "size": 10,
                "parse_result": {"symbols": [], "edges": [], "imports": []},
            },
            prev_user_version=1,
            content_sha="h1",
        )

        stats = replay_wal(wal, db_path)
        assert stats["skipped_idempotent"] == 1
        assert stats["applied"] == 0
        # And the ack should have been appended post-skip
        assert len(read_acked_ids(wal)) == 1


# ---------------------------------------------------------------------
# Crash injection — kill between intent append and commit
# ---------------------------------------------------------------------

class TestCrashInjection:
    def test_kill_between_intent_and_commit_replay_recovers(self, tmp_path: Path):
        """AC: kill indexer between WAL append and SQLite commit →
        next refresh completes correctly without double-applying."""
        wal = tmp_path / "wal.jsonl"
        db_path = _fresh_db(tmp_path)

        # Simulate: intent was appended but SQLite never committed.
        # (No direct DB write before the intent.)
        append_intent(
            wal,
            op="file_upsert",
            args={
                "path": "crashed.py",
                "lang": "python",
                "content_hash_before": None,
                "content_hash_after": "h_crash",
                "mtime": 0, "size": 5,
                "parse_result": {"symbols": [], "edges": [], "imports": []},
            },
            # Match the DB's actual user_version after ensure_schema (L-253).
            prev_user_version=db.CURRENT_SCHEMA_VERSION,
            content_sha="h_crash",
        )

        # Pre-replay: DB has no crashed.py row
        with db.connect(db_path, read_only=True) as conn:
            assert conn.execute(
                "SELECT COUNT(*) FROM files WHERE path = 'crashed.py'"
            ).fetchone()[0] == 0

        # Replay recovers
        stats = replay_wal(wal, db_path)
        assert stats["applied"] == 1

        with db.connect(db_path, read_only=True) as conn:
            row = conn.execute(
                "SELECT content_hash FROM files WHERE path = 'crashed.py'"
            ).fetchone()
            assert row[0] == "h_crash"

        # Second replay: entry already acked → no double apply
        stats2 = replay_wal(wal, db_path)
        assert stats2["applied"] == 0
        assert stats2["skipped_already_acked"] == 1


# ---------------------------------------------------------------------
# ReplayConflict — prev_user_version mismatch
# ---------------------------------------------------------------------

class TestReplayConflict:
    def test_schema_version_mismatch_raises(self, tmp_path: Path):
        wal = tmp_path / "wal.jsonl"
        db_path = _fresh_db(tmp_path)

        # Entry expects user_version 999; DB is at 1.
        append_intent(
            wal,
            op="file_upsert",
            args={
                "path": "x.py", "lang": "python",
                "content_hash_before": None, "content_hash_after": "h",
                "mtime": 0, "size": 0,
                "parse_result": {"symbols": [], "edges": [], "imports": []},
            },
            prev_user_version=999,
            content_sha="h",
        )

        with pytest.raises(ReplayConflict):
            replay_wal(wal, db_path)


# ---------------------------------------------------------------------
# WALEntry dataclass contract
# ---------------------------------------------------------------------

class TestWALEntry:
    def test_wal_entry_fields(self):
        e = WALEntry(
            id="abc", ts="2026-04-14T12:00:00", op="file_upsert", args={},
            prev_user_version=1, content_sha="h", schema_version=1,
        )
        assert e.id == "abc"
        assert e.op == "file_upsert"
