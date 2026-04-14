"""Tests for codemem.diff.symbol_diff — Task 2.1.

Covers: exact-name-match classification (added / removed / modified /
unchanged), rename detection via signature Jaccard with line-proximity
tiebreak, same-kind hard filter, demoted-match logging,
detect_renames=False escape hatch, and mass-refactor determinism.
"""

from __future__ import annotations

import pytest

from codemem.diff.symbol_diff import (
    ChangeKind,
    DiffResult,
    diff_symbols,
)
from codemem.parser.python_ast import Symbol


def _sym(name: str, *, kind: str = "function", line: int = 1,
         signature: str | None = "()", parent: str | None = None) -> Symbol:
    """Small helper for building Symbol fixtures."""
    return Symbol(
        scip_id=f"codemem . /x.py#{name}",
        name=name,
        kind=kind,
        line=line,
        signature=signature,
        signature_hash=None,
        docstring=None,
        parent_scip_id=parent,
    )


# ---------------------------------------------------------------------
# Direct-match classification (name+kind exact)
# ---------------------------------------------------------------------

class TestExactMatch:
    def test_same_name_same_signature_unchanged(self):
        old = [_sym("foo", signature="(x)")]
        new = [_sym("foo", signature="(x)")]
        r = diff_symbols(old, new)
        kinds = [c.kind for c in r.changes]
        assert kinds == [ChangeKind.UNCHANGED]

    def test_same_name_diff_signature_modified(self):
        old = [_sym("foo", signature="(x)")]
        new = [_sym("foo", signature="(x, y)")]
        r = diff_symbols(old, new)
        assert len(r.changes) == 1
        assert r.changes[0].kind == ChangeKind.MODIFIED
        assert r.changes[0].old.signature == "(x)"
        assert r.changes[0].new.signature == "(x, y)"

    def test_only_in_old_is_removed(self):
        old = [_sym("foo")]
        new = []
        r = diff_symbols(old, new, detect_renames=False)
        assert [c.kind for c in r.changes] == [ChangeKind.REMOVED]

    def test_only_in_new_is_added(self):
        old = []
        new = [_sym("bar")]
        r = diff_symbols(old, new, detect_renames=False)
        assert [c.kind for c in r.changes] == [ChangeKind.ADDED]

    def test_kind_difference_not_same_symbol(self):
        # Function and class sharing a name are DIFFERENT symbols.
        old = [_sym("Foo", kind="function")]
        new = [_sym("Foo", kind="class")]
        r = diff_symbols(old, new, detect_renames=False)
        kinds = {c.kind for c in r.changes}
        assert kinds == {ChangeKind.ADDED, ChangeKind.REMOVED}


# ---------------------------------------------------------------------
# Rename detection via signature Jaccard (AC-required)
# ---------------------------------------------------------------------

class TestRenameDetection:
    def test_same_signature_different_name_above_threshold_renamed(self):
        old = [_sym("get_user", signature="(user_id: int) -> User")]
        new = [_sym("fetch_user", signature="(user_id: int) -> User")]
        r = diff_symbols(old, new)
        assert len(r.changes) == 1
        assert r.changes[0].kind == ChangeKind.RENAMED
        assert r.changes[0].old.name == "get_user"
        assert r.changes[0].new.name == "fetch_user"
        assert r.changes[0].score is not None
        assert r.changes[0].score >= 0.7

    def test_identical_signatures_score_one(self):
        old = [_sym("a", signature="(x, y)")]
        new = [_sym("b", signature="(x, y)")]
        r = diff_symbols(old, new)
        assert r.changes[0].kind == ChangeKind.RENAMED
        assert r.changes[0].score == pytest.approx(1.0)

    def test_below_threshold_not_renamed_demoted_logged(self):
        old = [_sym("foo", signature="(a)")]
        new = [_sym("bar", signature="(x: int, y: str, z: float) -> Dict")]
        r = diff_symbols(old, new)
        kinds = {c.kind for c in r.changes}
        assert kinds == {ChangeKind.ADDED, ChangeKind.REMOVED}
        # The low-similarity pair should appear in the demoted log.
        assert r.demoted, "below-threshold pair must be logged to demoted"
        names = {(old_s.name, new_s.name) for old_s, new_s, _ in r.demoted}
        assert ("foo", "bar") in names

    def test_same_kind_hard_filter(self):
        # Even with identical signatures, different kinds can't rename.
        old = [_sym("Foo", kind="class", signature=None)]
        new = [_sym("Bar", kind="function", signature="()")]
        r = diff_symbols(old, new)
        kinds = {c.kind for c in r.changes}
        assert kinds == {ChangeKind.ADDED, ChangeKind.REMOVED}

    def test_line_proximity_tiebreak(self):
        # Two equally-good candidates — the one closer in line wins.
        old = [_sym("helper", signature="(x)", line=10)]
        new = [
            _sym("helper_v1", signature="(x)", line=100),
            _sym("helper_v2", signature="(x)", line=12),
        ]
        r = diff_symbols(old, new)
        renames = [c for c in r.changes if c.kind == ChangeKind.RENAMED]
        assert len(renames) == 1
        assert renames[0].new.name == "helper_v2"  # closer line wins

    def test_mass_refactor_deterministic(self):
        # Every symbol rename preserves the 1:1 mapping.
        old = [_sym(f"old_{i}", signature=f"(arg{i})", line=i) for i in range(5)]
        new = [_sym(f"new_{i}", signature=f"(arg{i})", line=i) for i in range(5)]
        r = diff_symbols(old, new)
        renames = [c for c in r.changes if c.kind == ChangeKind.RENAMED]
        assert len(renames) == 5
        pairs = {(c.old.name, c.new.name) for c in renames}
        assert pairs == {(f"old_{i}", f"new_{i}") for i in range(5)}


# ---------------------------------------------------------------------
# detect_renames=False escape hatch
# ---------------------------------------------------------------------

class TestNoRenameDetection:
    def test_disabled_treats_everything_as_added_removed(self):
        old = [_sym("x", signature="(a)")]
        new = [_sym("y", signature="(a)")]
        r = diff_symbols(old, new, detect_renames=False)
        kinds = {c.kind for c in r.changes}
        assert kinds == {ChangeKind.ADDED, ChangeKind.REMOVED}
        assert r.demoted == []  # nothing logged when disabled


# ---------------------------------------------------------------------
# Data-class contract
# ---------------------------------------------------------------------

class TestDataTypes:
    def test_changekind_values(self):
        assert ChangeKind.ADDED == "added"
        assert ChangeKind.REMOVED == "removed"
        assert ChangeKind.MODIFIED == "modified"
        assert ChangeKind.RENAMED == "renamed"
        assert ChangeKind.UNCHANGED == "unchanged"

    def test_diff_result_exposes_changes_and_demoted(self):
        r = DiffResult(changes=[], demoted=[])
        assert r.changes == []
        assert r.demoted == []
