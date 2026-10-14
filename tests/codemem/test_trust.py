"""codemem serves only an index it built here (M15 §6.8 re-run 2, Ste: trust-token redesign).

A repo controls ``.codemem/``: it can commit a whole index (or ship one in a zip)
whose rows do not match the code. Git-based detection was bypassed four ways
(dubious ownership, an embedded repo, a case alias, a relative GIT_DIR). Instead,
a DB file codemem creates carries this user's nonce for its directory, kept
outside the repo (``$XDG_STATE_HOME/codemem/trust``); readers refuse a DB whose
stamp does not match, and a refresh rebuilds it.
"""

from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from codemem import mcp_tools
from codemem.incremental import refresh_index
from codemem.indexer import build_index
from codemem.storage import db


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@t",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "r"
    root.mkdir()
    (root / ".gitignore").write_text(".codemem/\n")
    (root / "a.py").write_text("def evil():\n    pass\n")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "init")
    db_path = root / ".codemem" / "index.db"
    build_index(root, db_path)
    return root, db_path


def _plant_phantom(db_path: Path) -> None:
    """Rows the code does not hold, written behind codemem's back."""
    conn = sqlite3.connect(db_path)
    fid = conn.execute("SELECT id FROM files WHERE path = 'a.py'").fetchone()[0]
    conn.execute(
        "INSERT INTO symbols (file_id, name, kind, line, scip_id) VALUES (?, 'phantom', 'function', 1, 'x phantom')",
        (fid,),
    )
    conn.commit()
    conn.close()


def _other_machine(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "other-machine-state"))


def test_a_db_codemem_built_here_is_trusted(repo):
    _, db_path = repo
    with db.connect(db_path, read_only=True) as conn:
        assert conn.execute("SELECT COUNT(*) FROM files").fetchone()[0] == 1


def test_a_db_built_elsewhere_is_refused_by_every_reader(repo, monkeypatch, tmp_path):
    _, db_path = repo
    _other_machine(monkeypatch, tmp_path)
    with pytest.raises(db.UntrustedIndex):
        db.connect(db_path, read_only=True)
    assert issubclass(db.UntrustedIndex, db.UnsafeDbPath)


def test_a_db_made_with_plain_sqlite_is_untrusted(tmp_path):
    p = tmp_path / ".codemem" / "index.db"
    p.parent.mkdir()
    sqlite3.connect(p).close()
    with pytest.raises(db.UntrustedIndex):
        db.connect(p, read_only=True)


def test_a_copied_stamp_from_another_dir_is_untrusted(repo, tmp_path):
    _, db_path = repo
    other = tmp_path / "copy" / ".codemem"
    other.mkdir(parents=True)
    (other / "index.db").write_bytes(db_path.read_bytes())
    with pytest.raises(db.UntrustedIndex):
        db.connect(other / "index.db", read_only=True)


def test_ensure_fresh_rebuilds_an_untrusted_index_and_never_serves_its_rows(
    repo, monkeypatch, tmp_path
):
    root, db_path = repo
    _plant_phantom(db_path)
    _other_machine(monkeypatch, tmp_path)
    r = mcp_tools.ensure_fresh(db_path, root, cap=60)
    assert r["stale"] is False, r
    assert mcp_tools.search_symbols(db_path, "phantom")["matches"] == []


def test_an_untrusted_index_whose_rebuild_does_not_finish_is_not_served(
    repo, monkeypatch, tmp_path
):
    root, db_path = repo
    _other_machine(monkeypatch, tmp_path)
    monkeypatch.setattr(mcp_tools, "_capped_refresh", lambda *a, **k: "timeout")
    r = mcp_tools.ensure_fresh(db_path, root)
    assert "error" in r and r["stale_reason"] == "untrusted"


def test_refresh_rebuilds_an_untrusted_index(repo, monkeypatch, tmp_path):
    root, db_path = repo
    _plant_phantom(db_path)
    _other_machine(monkeypatch, tmp_path)
    assert refresh_index(root, db_path).full_rebuild is True
    with db.connect(db_path, read_only=True) as conn:
        assert (
            conn.execute(
                "SELECT COUNT(*) FROM symbols WHERE name = 'phantom'"
            ).fetchone()[0]
            == 0
        )


def test_build_over_an_untrusted_db_keeps_none_of_its_rows(repo, monkeypatch, tmp_path):
    """build_index leaves git-mining tables alone, so an untrusted DB is replaced, not reused."""
    root, db_path = repo
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO commits (sha, author_email, author_time, message) VALUES ('f'||hex(randomblob(19)), 'x', 0, 'planted')"
    )
    conn.commit()
    conn.close()
    _other_machine(monkeypatch, tmp_path)
    build_index(root, db_path)
    with db.connect(db_path, read_only=True) as c:
        assert (
            c.execute(
                "SELECT COUNT(*) FROM commits WHERE message = 'planted'"
            ).fetchone()[0]
            == 0
        )


def test_a_committed_index_is_rebuilt_not_refused(repo, monkeypatch, tmp_path):
    """The git ls-files check is gone: a tracked .codemem is rebuilt like any untrusted one."""
    root, db_path = repo
    _git(root, "add", "-f", ".codemem/index.db", ".codemem/last_sha")
    _git(root, "commit", "-qm", "ship an index")
    _plant_phantom(db_path)
    _other_machine(monkeypatch, tmp_path)
    r = mcp_tools.ensure_fresh(db_path, root, cap=60)
    assert r.get("stale_reason") != "unsafe_db_path", r
    assert mcp_tools.search_symbols(db_path, "phantom")["matches"] == []


def test_the_trust_record_lives_outside_the_repo_and_is_private(repo):
    import os
    import stat

    from codemem.safety import trust_record

    _, db_path = repo
    rec = trust_record(db_path.parent)
    assert not rec.is_relative_to(db_path.parent.parent)
    assert stat.S_IMODE(rec.stat().st_mode) == 0o600
    assert rec.parent.is_relative_to(Path(os.environ["XDG_STATE_HOME"]))


def test_cli_status_on_an_untrusted_index_refuses_and_names_the_remedy(
    repo, monkeypatch, tmp_path
):
    root, db_path = repo
    _other_machine(monkeypatch, tmp_path)
    r = subprocess.run(
        [sys.executable, "-m", "codemem.cli", "--db", str(db_path), "status"],
        capture_output=True,
        text=True,
        cwd=root,
    )
    assert r.returncode == 1 and "refused" in r.stderr and "codemem build" in r.stderr


def test_a_corrupt_index_is_rebuilt_not_served(repo):
    root, db_path = repo
    db_path.write_bytes(b"not a sqlite database at all" * 10)
    r = mcp_tools.ensure_fresh(db_path, root, cap=60)
    assert r["stale"] is False, r


def test_a_planted_wal_is_never_absorbed_into_a_new_stamped_db(tmp_path):
    """SQLite replays an existing -wal into a newly created DB; codemem would then stamp it."""
    import shutil

    src = tmp_path / "attacker" / "index.db"
    src.parent.mkdir()
    keep = sqlite3.connect(src)
    keep.execute("PRAGMA journal_mode=WAL")
    keep.execute("PRAGMA wal_autocheckpoint=0")
    keep.execute(
        "CREATE TABLE commits (sha TEXT PRIMARY KEY, author_email TEXT, author_time INTEGER, message TEXT)"
    )
    keep.execute("INSERT INTO commits VALUES ('f00d', 'x', 0, 'planted')")
    keep.commit()
    target = tmp_path / "victim-repo" / ".codemem"
    target.mkdir(parents=True)
    shutil.copy(src.with_name("index.db-wal"), target / "index.db-wal")
    keep.close()
    conn = db.connect(target / "index.db")
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master")}
    conn.close()
    assert "commits" not in tables


def test_a_planted_rollback_journal_is_never_absorbed_either(tmp_path):
    """Characterisation (SQLite 3.4x): a hot -journal with no main file is ignored."""
    target = tmp_path / "victim-repo" / ".codemem"
    target.mkdir(parents=True)
    (target / "index.db-journal").write_bytes(
        b"\xd9\xd5\x05\xf9\x20\xa1\x63\xd7" + b"\x00" * 504
    )
    conn = db.connect(target / "index.db")
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master")}
    conn.close()
    assert tables == {"meta"}
