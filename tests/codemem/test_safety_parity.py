"""codemem.safety and its aa_ma twin (render.graph) must refuse exactly the same dirs.

aa_ma never imports codemem (ADR-0014), so the §13 diagram fence carries its own
copy of the rule. A test may import both: this one pins them together, so a rule
added to one and not the other fails here (M15 §6.8 re-run 2).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from aa_ma.render.graph import _unsafe_reason
from codemem.safety import UnsafeDbPath, check_db_path
from codemem.storage import db


def _built(d: Path) -> Path:
    d.mkdir(parents=True)
    db.connect(d / "index.db").close()  # created by codemem → stamped
    return d


def _graph_at(d: Path):
    """open_graph on the index in ``d``: since M16 that dir is chosen by CODEMEM_DB."""
    from aa_ma.render.graph import open_graph

    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("CODEMEM_DB", str(d / "index.db"))
        return open_graph(d.parent)


def _case(name: str, tmp: Path) -> Path:
    d = tmp / "r" / ".codemem"
    victim = tmp / "victim"
    victim.write_text("x\n")
    if name == "absent":
        return d
    if name == "built here":
        return _built(d)
    if name == "dir is a link":
        (tmp / "elsewhere").mkdir()
        d.parent.mkdir(parents=True)
        d.symlink_to(tmp / "elsewhere")
        return d
    if name == "holds a link":
        _built(d)
        (d / "anything").symlink_to(victim)
        return d
    if name == "regular file":
        d.parent.mkdir(parents=True)
        d.write_text("not a dir\n")
        return d
    raise AssertionError(name)


@pytest.mark.parametrize(
    "name", ["absent", "built here", "dir is a link", "holds a link", "regular file"]
)
def test_twin_refuses_iff_codemem_refuses(tmp_path, name):
    d = _case(name, tmp_path)
    try:
        check_db_path(d / "index.db")
        codemem_refuses = False
    except UnsafeDbPath:
        codemem_refuses = True
    assert (_unsafe_reason(d) is not None) == codemem_refuses, name


def test_twin_trust_matches_codemem_trust(tmp_path):
    """Built here → both read it; plain sqlite → both refuse."""

    here = _built(tmp_path / "a" / ".codemem")
    db.connect(here / "index.db", read_only=True).close()
    assert "not built" not in (_graph_at(here).reason or "")

    foreign = tmp_path / "c" / ".codemem"
    foreign.mkdir(parents=True)
    (foreign / "index.db").write_bytes(
        (here / "index.db").read_bytes()
    )  # another dir's stamp
    with pytest.raises(db.UntrustedIndex):
        db.connect(foreign / "index.db", read_only=True)
    assert "not built" in _graph_at(foreign).reason

    plain = tmp_path / "b" / ".codemem"
    plain.mkdir(parents=True)
    sqlite3.connect(plain / "index.db").close()
    with pytest.raises(db.UntrustedIndex):
        db.connect(plain / "index.db", read_only=True)
    assert "codemem build" in _graph_at(plain).reason


def test_twins_agree_a_non_ascii_stamp_is_untrusted(tmp_path):

    d = _built(tmp_path / "n" / ".codemem")
    conn = sqlite3.connect(d / "index.db")
    conn.execute("UPDATE meta SET value = 'é' WHERE key = 'trust_nonce'")
    conn.commit()
    conn.close()
    assert db.index_trusted(d / "index.db") is False
    assert "not built" in _graph_at(d).reason


def test_twins_name_a_broken_trust_store_not_a_hostile_index(tmp_path, monkeypatch):
    """SECURITY.md: a trust-store fault is reported as such, never as 'not built here'.

    The store is broken by pointing XDG_STATE_HOME at a file (chmod 0 does not stop root).
    """
    from codemem.safety import TrustStoreError

    d = _built(tmp_path / "s" / ".codemem")
    blocker = tmp_path / "state-is-a-file"
    blocker.write_text("x\n")
    monkeypatch.setenv("XDG_STATE_HOME", str(blocker))
    with pytest.raises(TrustStoreError):
        db.connect(d / "index.db", read_only=True)
    reason = _graph_at(d).reason
    assert "trust store" in reason and "not built" not in reason


@pytest.mark.parametrize("fault", ["non-utf8 record", "shared trust dir"])
def test_twins_agree_on_store_faults(tmp_path, fault):
    import os

    from codemem.safety import TrustStoreError, trust_record

    d = _built(tmp_path / "f" / ".codemem")
    rec = trust_record(d)
    if fault == "non-utf8 record":
        rec.write_bytes(b"\xff\xfe")
    else:
        os.chmod(rec.parent, 0o777)  # noqa: S103  # why: plants the unsafe mode the code must refuse
    try:
        with pytest.raises(TrustStoreError):
            db.connect(d / "index.db", read_only=True)
        reason = _graph_at(d).reason
    finally:
        os.chmod(rec.parent, 0o700)
    assert "trust store" in reason and "not built" not in reason


# --- the index location (M16): codemem, aa_ma.render.graph and the shell agree ---

_FORGE = Path(__file__).resolve().parents[2]


def _shell_dir(root: Path, env: dict[str, str]) -> str:
    import subprocess

    r = subprocess.run(
        [
            "bash",
            "-c",
            '. "$1/claude-code/hooks/lib/aa-ma-parse.sh"; aa_ma_codemem_dir "$2"',
            "_",
            str(_FORGE),
            str(root),
        ],
        capture_output=True,
        text=True,
        env=env,
        cwd=root,
    )
    assert r.returncode == 0, r.stderr
    return r.stdout


@pytest.mark.parametrize(
    "case",
    [
        "plain",
        "with spaces",
        "symlinked root",
        "CODEMEM_DB",
        "CODEMEM_DB at /",
        "CODEMEM_DB trailing slash",
        "relative XDG",
        "XDG trailing slash",
    ],
)
def test_every_twin_resolves_the_same_index_dir(tmp_path, monkeypatch, case):
    import os

    from aa_ma.render.graph import _resolve_db_path
    from codemem.paths import resolve_db_path

    real = tmp_path / ("my repo" if case == "with spaces" else "repo")
    real.mkdir()
    root = real
    if case == "symlinked root":
        root = tmp_path / "link"
        root.symlink_to(real)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    xdg = {"relative XDG": "rel", "XDG trailing slash": f"{tmp_path / 'cache'}/"}
    monkeypatch.setenv("XDG_CACHE_HOME", xdg.get(case, str(tmp_path / "cache")))
    monkeypatch.delenv("CODEMEM_DB", raising=False)
    if case == "CODEMEM_DB":
        monkeypatch.setenv("CODEMEM_DB", str(tmp_path / "explicit" / "index.db"))
    if case == "CODEMEM_DB trailing slash":
        monkeypatch.setenv("CODEMEM_DB", f"{tmp_path / 'explicit'}/")
    if case == "CODEMEM_DB at /":
        monkeypatch.setenv("CODEMEM_DB", "/index.db")  # never opened: names only
    monkeypatch.chdir(root)

    py = resolve_db_path(root).parent
    assert _resolve_db_path(root).parent == py
    assert _shell_dir(root, dict(os.environ)) == str(py)
    if not case.startswith("CODEMEM_DB"):
        assert py.parent.name == "codemem" and real not in py.parents
