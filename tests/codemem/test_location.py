"""The default codemem index lives outside the repo (code-conventions-impact M16).

``.codemem/`` was repo-controlled: a clone could commit a WAL, a rollback journal
or a stamped index beside the real one and have SQLite replay it (M15 §6.8 re-run 3,
double-check F1, pre-merge HIGH). The default is now
``${XDG_CACHE_HOME:-~/.cache}/codemem/<sha256(realpath root)>/index.db``; nothing in
the repo is read or written unless ``CODEMEM_DB`` points there.
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from codemem import mcp_tools, paths
from codemem.incremental import _db_files
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


def _plant_phantom(db_path: Path) -> None:
    """Rows the code does not hold, written behind codemem's back (as test_trust)."""
    conn = sqlite3.connect(db_path)
    fid = conn.execute("SELECT id FROM files WHERE path = 'a.py'").fetchone()[0]
    conn.execute(
        "INSERT INTO symbols (file_id, name, kind, line, scip_id) VALUES (?, 'phantom', 'function', 1, 'x phantom')",
        (fid,),
    )
    conn.commit()
    conn.close()


def _key(root: Path) -> str:
    return hashlib.sha256(os.fsencode(os.path.realpath(root))).hexdigest()


@pytest.fixture
def cache(tmp_path, monkeypatch) -> Path:
    c = tmp_path / "cache"
    monkeypatch.setenv("XDG_CACHE_HOME", str(c))
    monkeypatch.delenv("CODEMEM_DB", raising=False)
    return c


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "r"
    root.mkdir()
    (root / "a.py").write_text("def real():\n    pass\n")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "init")
    return root


def test_default_is_the_cache_dir_keyed_by_realpath(cache, repo, tmp_path):
    expected = cache / "codemem" / _key(repo) / "index.db"
    assert paths.default_db_path(repo) == expected
    link = tmp_path / "link"
    link.symlink_to(repo)
    assert paths.default_db_path(link) == expected


def test_a_relative_xdg_cache_home_is_ignored(monkeypatch, tmp_path, repo):
    # XDG Base Directory spec: a relative path in an XDG_* variable is invalid.
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("XDG_CACHE_HOME", "rel/cache")
    assert paths.default_db_path(repo) == (
        tmp_path / "home" / ".cache" / "codemem" / _key(repo) / "index.db"
    )


def test_cli_build_writes_nothing_into_the_repo(cache, repo):
    r = subprocess.run(
        [sys.executable, "-I", "-m", "codemem.cli", "build"],
        cwd=repo,
        capture_output=True,
        text=True,
        env={**os.environ, "XDG_CACHE_HOME": str(cache)},
    )
    assert r.returncode == 0, r.stderr
    assert not (repo / ".codemem").exists()
    built = cache / "codemem" / _key(repo)
    assert {"index.db", "last_sha", "tree_sig"} <= {p.name for p in built.iterdir()}


def test_cli_repo_root_flag_picks_that_repos_dir(cache, repo, tmp_path):
    r = subprocess.run(
        [sys.executable, "-I", "-m", "codemem.cli", "build", "--repo-root", str(repo)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env={**os.environ, "XDG_CACHE_HOME": str(cache)},
    )
    assert r.returncode == 0, r.stderr
    assert (cache / "codemem" / _key(repo) / "index.db").exists()


def _server():
    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location(
        "codemem_mcp_server_loc", root / "claude-code" / "codemem" / "mcp" / "server.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_server_defaults_to_the_cache_dir_of_its_repo_root(cache, repo, monkeypatch):
    monkeypatch.setenv("CODEMEM_REPO_ROOT", str(repo))
    srv = _server()
    assert srv._default_db_path() == paths.default_db_path(repo)


def test_server_makes_relative_env_paths_absolute(cache, repo, monkeypatch):
    monkeypatch.chdir(repo.parent)
    monkeypatch.setenv("CODEMEM_DB", "elsewhere/index.db")
    monkeypatch.setenv("CODEMEM_REPO_ROOT", repo.name)
    srv = _server()
    assert srv._default_db_path() == repo.parent / "elsewhere" / "index.db"
    assert srv._default_repo_root() == repo


def test_capped_refresh_gets_absolute_paths(cache, repo, monkeypatch):
    """The refresh runs with cwd = the DB dir; a relative path there means another file."""
    monkeypatch.chdir(repo.parent)
    rel_db = Path("idx") / "index.db"
    rel_root = Path(repo.name)
    build_index(rel_root, rel_db)
    (repo / "b.py").write_text("def new():\n    pass\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "b")
    assert mcp_tools._capped_refresh(rel_db, rel_root, cap=60) == "ok"
    head = _git(repo, "rev-parse", "HEAD")
    assert (repo.parent / "idx" / "last_sha").read_text().strip() == head
    assert not (repo.parent / "idx" / "idx").exists()


# --- repo-controlled .codemem/ never reaches the default index --------------


def _forged_wal(tmp_path: Path, target: Path) -> None:
    src = tmp_path / "attacker" / "index.db"
    src.parent.mkdir()
    keep = sqlite3.connect(src)
    keep.execute("PRAGMA journal_mode=WAL")
    keep.execute("PRAGMA wal_autocheckpoint=0")
    keep.execute("CREATE TABLE planted (x TEXT)")
    keep.execute("INSERT INTO planted VALUES ('forged')")
    keep.commit()
    shutil.copy(src.with_name("index.db-wal"), target / "index.db-wal")
    keep.close()


def _forged_journal(tmp_path: Path, target: Path) -> None:
    src = tmp_path / "attacker" / "index.db"
    src.parent.mkdir()
    keep = sqlite3.connect(src, isolation_level=None)
    keep.execute("PRAGMA journal_mode=DELETE")
    keep.execute("CREATE TABLE planted (x TEXT)")
    keep.execute("BEGIN")
    keep.executemany("INSERT INTO planted VALUES (?)", [("forged",)] * 2000)
    shutil.copy(src.with_name("index.db-journal"), target / "index.db-journal")
    keep.execute("ROLLBACK")
    keep.close()


@pytest.mark.parametrize("plant", ["wal", "journal", "own-stamped-index"])
def test_a_committed_codemem_dir_is_never_read_by_default(cache, repo, tmp_path, plant):
    """Re-run 3 planted WAL, pre-merge HIGH rollback journal, double-check F1 nonce leak."""
    planted = repo / ".codemem"
    # The victim's own stamped index, as if committed and then forged upstream
    # with the stamp kept (F1): worst case, the nonce matches this machine.
    build_index(repo, planted / "index.db")
    _plant_phantom(planted / "index.db")
    if plant == "wal":
        _forged_wal(tmp_path, planted)
    elif plant == "journal":
        _forged_journal(tmp_path, planted)
    _git(repo, "add", "-f", ".codemem")
    _git(repo, "commit", "-qm", "plant")

    default = paths.default_db_path(repo)
    r = mcp_tools.ensure_fresh(default, repo, cap=60)
    assert r["stale"] is False, r
    served = mcp_tools.search_symbols(default, "phantom")
    assert "phantom" not in str(served)
    conn = sqlite3.connect(default)
    tables = {t for (t,) in conn.execute("SELECT name FROM sqlite_master")}
    conn.close()
    assert "planted" not in tables


# --- one list of SQLite sidecars --------------------------------------------


def test_every_cleanup_uses_one_suffix_list_with_journal():
    assert db.SQLITE_SUFFIXES == ("", "-wal", "-shm", "-journal")
    p = Path("/x/index.db")
    assert _db_files(p) == [p.with_name("index.db" + s) for s in db.SQLITE_SUFFIXES]


def test_a_build_over_an_untrusted_db_removes_its_journal(
    cache, repo, tmp_path, monkeypatch
):
    target = paths.default_db_path(repo)
    build_index(repo, target)
    target.with_name("index.db-journal").write_bytes(b"stale")
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "other-machine-state"))
    build_index(repo, target)
    assert not target.with_name("index.db-journal").exists()
