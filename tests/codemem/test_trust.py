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
    """Characterisation (SQLite 3.4x): a real hot -journal with no main file is ignored."""
    import shutil

    src = tmp_path / "attacker" / "index.db"
    src.parent.mkdir()
    keep = sqlite3.connect(src, isolation_level=None)
    keep.execute("PRAGMA journal_mode=DELETE")
    keep.execute("CREATE TABLE commits (message TEXT)")
    keep.execute("BEGIN")
    keep.executemany("INSERT INTO commits VALUES (?)", [("planted",)] * 2000)
    target = tmp_path / "victim-repo" / ".codemem"
    target.mkdir(parents=True)
    shutil.copy(
        src.with_name("index.db-journal"), target / "index.db-journal"
    )  # hot, mid-transaction
    keep.execute("ROLLBACK")
    keep.close()
    conn = db.connect(target / "index.db")
    tables = {
        r[0]
        for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }
    conn.close()
    assert tables == {"meta"}


def _set_stamp(db_path: Path, value: str) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute("UPDATE meta SET value = ? WHERE key = 'trust_nonce'", (value,))
    conn.commit()
    conn.close()


def test_a_non_ascii_stamp_is_untrusted_and_build_recovers(repo):
    """hmac.compare_digest raised TypeError on a non-ASCII str: even `codemem build` crashed."""
    from codemem.storage.db import index_trusted

    root, db_path = repo
    _set_stamp(db_path, "é")
    assert index_trusted(db_path) is False
    build_index(root, db_path)
    assert index_trusted(db_path) is True


def test_an_unreadable_trust_store_is_a_named_error_not_untrusted(
    repo, monkeypatch, tmp_path
):
    """A broken state dir must not look like a hostile index (that loops rebuilds silently)."""
    from codemem.safety import TrustStoreError

    root, db_path = repo
    blocker = tmp_path / "state-is-a-file"
    blocker.write_text("x\n")
    monkeypatch.setenv("XDG_STATE_HOME", str(blocker))
    with pytest.raises(TrustStoreError):
        db.connect(db_path, read_only=True)
    r = mcp_tools.ensure_fresh(db_path, root)
    assert r["stale_reason"] == "trust_store" and "trust store" in r["error"]
    assert not (db_path.parent / "index.db.rebuild").exists()


def test_a_db_that_cannot_be_stamped_is_not_left_behind(tmp_path, monkeypatch):
    from codemem.safety import TrustStoreError

    blocker = tmp_path / "state-is-a-file"
    blocker.write_text("x\n")
    monkeypatch.setenv("XDG_STATE_HOME", str(blocker))
    d = tmp_path / "r" / ".codemem"
    d.mkdir(parents=True)
    with pytest.raises(TrustStoreError):
        db.connect(d / "index.db")
    assert list(d.iterdir()) == []


def test_an_untrusted_rebuild_that_failed_says_so(repo, monkeypatch, tmp_path):
    """Caller must tell 'still rebuilding, retry' from 'rebuild failed'."""
    root, db_path = repo
    _other_machine(monkeypatch, tmp_path)
    monkeypatch.setattr(mcp_tools, "_capped_refresh", lambda *a, **k: "error")
    r = mcp_tools.ensure_fresh(db_path, root)
    assert r["stale_reason"] == "untrusted" and "failed" in r["error"]
    log = (db_path.parent / "refresh.log").read_text()
    assert "not served" in log and "serving a stale index" not in log.splitlines()[-1]


# --- §6.8 re-run 4 (fold-ins) -------------------------------------------------


def _broken_store(monkeypatch, tmp_path) -> None:
    blocker = tmp_path / "state-is-a-file"
    blocker.write_text("x\n")
    monkeypatch.setenv("XDG_STATE_HOME", str(blocker))


def test_connect_never_deletes_an_index_it_did_not_create(repo, monkeypatch, tmp_path):
    """TOCTOU: a file that appears after an exists() check must not be cleaned up as ours."""
    from codemem.safety import TrustStoreError

    _, db_path = repo
    _broken_store(monkeypatch, tmp_path)
    real_exists = Path.exists
    monkeypatch.setattr(
        Path, "exists", lambda p: False if p == db_path else real_exists(p)
    )
    try:
        db.connect(db_path).close()  # an existing file: neither stamped nor cleaned up
    except TrustStoreError:
        pass
    monkeypatch.setattr(Path, "exists", real_exists)
    assert db_path.exists()


def test_an_empty_trust_record_heals_on_the_next_build(repo):
    from codemem.safety import trust_record
    from codemem.storage.db import index_trusted

    root, db_path = repo
    trust_record(db_path.parent).write_text("")
    build_index(root, db_path)
    assert index_trusted(db_path) is True
    assert trust_record(db_path.parent).read_text().strip()


def test_a_record_created_concurrently_is_used_and_no_temp_is_left(
    tmp_path, monkeypatch
):
    import os

    import codemem.safety as safety

    d = tmp_path / "r" / ".codemem"
    d.mkdir(parents=True)
    rec = safety.trust_record(d)
    real_link = safety.os.link

    def racing_link(src, dst, *, src_dir_fd=None, dst_dir_fd=None):
        fd = os.open(dst, os.O_WRONLY | os.O_CREAT, 0o600, dir_fd=dst_dir_fd)
        os.write(fd, b"their-nonce\n")  # another process won
        os.close(fd)
        return real_link(src, dst, src_dir_fd=src_dir_fd, dst_dir_fd=dst_dir_fd)

    monkeypatch.setattr(safety.os, "link", racing_link)
    assert safety._nonce(d, create=True) == "their-nonce"
    assert not list(
        rec.parent.glob(f".{rec.name}.*")
    )  # the store is shared by the session: look for ours


def test_a_store_without_hard_links_still_records(tmp_path, monkeypatch):
    import errno

    import codemem.safety as safety

    def no_links(src, dst, **_):
        raise OSError(errno.EPERM, "Operation not permitted")

    monkeypatch.setattr(safety.os, "link", no_links)
    d = tmp_path / "r" / ".codemem"
    d.mkdir(parents=True)
    assert safety._nonce(d, create=True)


def test_a_non_utf8_record_is_a_trust_store_error(repo):
    from codemem.safety import TrustStoreError, trust_record

    _, db_path = repo
    trust_record(db_path.parent).write_bytes(b"\xff\xfe\x00bad")
    with pytest.raises(TrustStoreError):
        db.connect(db_path, read_only=True)


def test_a_trust_dir_another_user_could_write_is_refused(repo):
    import os

    from codemem.safety import TrustStoreError, trust_record

    _, db_path = repo
    store = trust_record(db_path.parent).parent
    os.chmod(store, 0o777)  # noqa: S103  # why: plants the unsafe mode the code must refuse
    try:
        with pytest.raises(TrustStoreError):
            db.connect(db_path, read_only=True)
    finally:
        os.chmod(store, 0o700)


def test_a_broken_store_has_its_own_stale_reason(repo, monkeypatch, tmp_path):
    root, db_path = repo
    _broken_store(monkeypatch, tmp_path)
    r = mcp_tools.ensure_fresh(db_path, root)
    assert r["stale_reason"] == "trust_store" and "trust store" in r["error"]


def test_cli_names_a_broken_store(repo, monkeypatch, tmp_path):
    root, db_path = repo
    _broken_store(monkeypatch, tmp_path)
    r = subprocess.run(
        [sys.executable, "-m", "codemem.cli", "--db", str(db_path), "status"],
        capture_output=True,
        text=True,
        cwd=root,
    )
    assert r.returncode == 1 and "trust store error" in r.stderr


def test_draw_check_on_a_broken_store_is_unknown_not_drift(
    repo, monkeypatch, tmp_path, capsys
):
    from codemem import cli

    _, db_path = repo
    _broken_store(monkeypatch, tmp_path)
    assert cli.main(["--db", str(db_path), "draw", "--check"]) == 0
    out = capsys.readouterr().out
    assert "UNKNOWN" in out and "codemem build" not in out


def test_untrusted_error_names_the_real_log(repo, monkeypatch, tmp_path):
    root, db_path = repo
    _other_machine(monkeypatch, tmp_path)
    monkeypatch.setattr(mcp_tools, "_capped_refresh", lambda *a, **k: "error")
    r = mcp_tools.ensure_fresh(db_path, root)
    assert str(db_path.parent / "refresh.log") in r["error"]


def test_every_refresh_outcome_has_an_untrusted_message():
    import typing

    assert set(mcp_tools._UNTRUSTED_ERROR) == set(
        typing.get_args(mcp_tools.RefreshOutcome)
    )


def test_a_trust_dir_swapped_after_its_check_is_never_read(repo, monkeypatch, tmp_path):
    """TOCTOU: checks and reads go through one directory fd, not the path twice."""
    import os

    import codemem.safety as safety

    _, db_path = repo
    _other_machine(monkeypatch, tmp_path)  # its own store: this test moves it
    safety._nonce(db_path.parent, create=True)
    rec = safety.trust_record(db_path.parent)
    store = rec.parent
    planted = tmp_path / "planted-store"
    planted.mkdir(mode=0o700)
    (planted / rec.name).write_text("attacker-known-nonce\n")
    real_open = os.open
    swapped = []

    def open_then_swap(path, flags, *a, **k):
        fd = real_open(path, flags, *a, **k)
        if (
            Path(os.fsdecode(path)) == store and not swapped
        ):  # the dir is open: now swap the path
            store.rename(tmp_path / "moved-store")
            store.symlink_to(planted)
            swapped.append(True)
        return fd

    monkeypatch.setattr(safety.os, "open", open_then_swap)
    assert safety._nonce(db_path.parent, create=False) != "attacker-known-nonce"
    assert swapped, "the store directory was never opened by path"
