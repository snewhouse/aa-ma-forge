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
    from aa_ma.render.graph import open_graph

    here = _built(tmp_path / "a" / ".codemem")
    db.connect(here / "index.db", read_only=True).close()
    assert "not built" not in (open_graph(here.parent).reason or "")

    foreign = tmp_path / "c" / ".codemem"
    foreign.mkdir(parents=True)
    (foreign / "index.db").write_bytes(
        (here / "index.db").read_bytes()
    )  # another dir's stamp
    with pytest.raises(db.UntrustedIndex):
        db.connect(foreign / "index.db", read_only=True)
    assert "not built" in open_graph(foreign.parent).reason

    plain = tmp_path / "b" / ".codemem"
    plain.mkdir(parents=True)
    sqlite3.connect(plain / "index.db").close()
    with pytest.raises(db.UntrustedIndex):
        db.connect(plain / "index.db", read_only=True)
    assert "codemem build" in open_graph(plain.parent).reason


def test_twins_agree_a_non_ascii_stamp_is_untrusted(tmp_path):
    from aa_ma.render.graph import open_graph

    d = _built(tmp_path / "n" / ".codemem")
    conn = sqlite3.connect(d / "index.db")
    conn.execute("UPDATE meta SET value = 'é' WHERE key = 'trust_nonce'")
    conn.commit()
    conn.close()
    assert db.index_trusted(d / "index.db") is False
    assert "not built" in open_graph(d.parent).reason


def test_twins_name_a_broken_trust_store_not_a_hostile_index(tmp_path, monkeypatch):
    """SECURITY.md: a trust-store fault is reported as such, never as 'not built here'.

    The store is broken by pointing XDG_STATE_HOME at a file (chmod 0 does not stop root).
    """
    from aa_ma.render.graph import open_graph
    from codemem.safety import TrustStoreError

    d = _built(tmp_path / "s" / ".codemem")
    blocker = tmp_path / "state-is-a-file"
    blocker.write_text("x\n")
    monkeypatch.setenv("XDG_STATE_HOME", str(blocker))
    with pytest.raises(TrustStoreError):
        db.connect(d / "index.db", read_only=True)
    reason = open_graph(d.parent).reason
    assert "trust store" in reason and "not built" not in reason


@pytest.mark.parametrize("fault", ["non-utf8 record", "shared trust dir"])
def test_twins_agree_on_store_faults(tmp_path, fault):
    import os

    from aa_ma.render.graph import open_graph
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
        reason = open_graph(d.parent).reason
    finally:
        os.chmod(rec.parent, 0o700)
    assert "trust store" in reason and "not built" not in reason
