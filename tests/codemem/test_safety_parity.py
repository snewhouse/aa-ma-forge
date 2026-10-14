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
    assert (
        open_graph(here.parent).reason is None
        or "not built" not in open_graph(here.parent).reason
    )

    plain = tmp_path / "b" / ".codemem"
    plain.mkdir(parents=True)
    sqlite3.connect(plain / "index.db").close()
    with pytest.raises(db.UntrustedIndex):
        db.connect(plain / "index.db", read_only=True)
    assert "codemem build" in open_graph(plain.parent).reason
