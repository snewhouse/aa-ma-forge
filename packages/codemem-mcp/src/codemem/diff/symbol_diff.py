"""Symbol-set diff algorithm (M2 Task 2.1).

Classifies ``(old_symbols, new_symbols)`` per file into five buckets:
``UNCHANGED`` / ``MODIFIED`` / ``ADDED`` / ``REMOVED`` / ``RENAMED``.
``RENAMED`` is a RefactoringMiner-style heuristic — signature Jaccard
similarity with same-kind hard filter and line-proximity tiebreak,
threshold 0.7 by default.

Rename candidates scoring below the threshold are NOT emitted as
``RENAMED`` but are recorded in :attr:`DiffResult.demoted` for audit.
This "conservative demotion" keeps us from fabricating a rename
relationship when the signal is weak.

Consumers: the incremental refresh driver (Task 2.2) uses this to
decide which DB rows to insert/update/delete; the M2 WAL journal
(Task 2.3) uses the change set to build idempotent intent entries.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

from ..parser.python_ast import Symbol


__all__ = [
    "ChangeKind",
    "SymbolChange",
    "DiffResult",
    "diff_symbols",
]


DEFAULT_RENAME_THRESHOLD = 0.7


class ChangeKind(str, Enum):
    ADDED     = "added"
    REMOVED   = "removed"
    MODIFIED  = "modified"   # same (kind, name), different signature
    RENAMED   = "renamed"    # different name, similar signature (above threshold)
    UNCHANGED = "unchanged"  # identical (kind, name, signature)


@dataclass
class SymbolChange:
    kind: ChangeKind
    old: Symbol | None
    new: Symbol | None
    score: float | None = None  # populated for RENAMED only


@dataclass
class DiffResult:
    changes: list[SymbolChange] = field(default_factory=list)
    # Pairs (old, new, score) whose Jaccard similarity is above 0 but
    # below the rename threshold. Logged for audit; NOT emitted as
    # RENAMED changes.
    demoted: list[tuple[Symbol, Symbol, float]] = field(default_factory=list)


# ---------------------------------------------------------------------
# Algorithm
# ---------------------------------------------------------------------

# Tokenize on any non-alphanumeric boundary — Jaccard is defined over a
# set of tokens, and identifier tokens (``int``, ``user_id``) matter
# more than punctuation.
_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


def _signature_tokens(sig: str | None) -> frozenset[str]:
    if not sig:
        return frozenset()
    return frozenset(_TOKEN_RE.findall(sig))


def _jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def diff_symbols(
    old: list[Symbol],
    new: list[Symbol],
    *,
    rename_threshold: float = DEFAULT_RENAME_THRESHOLD,
    detect_renames: bool = True,
) -> DiffResult:
    """Compute the change set for a file's before/after symbol lists.

    Two-phase algorithm:

    1. **Exact-name pass** — pair symbols by ``(kind, name)``. Identical
       signatures → UNCHANGED; different → MODIFIED. Unmatched rows on
       either side fall through to phase 2.
    2. **Rename detection** (optional) — for every remaining
       (old, new) pair of the same kind, compute signature Jaccard.
       For each old, pick the new with the highest score, using line
       proximity as a tiebreak. If score ≥ ``rename_threshold``, emit
       RENAMED; otherwise log to ``demoted`` and treat both as
       ADDED/REMOVED.

    Deterministic: symbols sorted by ``(line, name)`` before matching
    so the output order is stable across runs.
    """
    old_sorted = sorted(old, key=lambda s: (s.line, s.name))
    new_sorted = sorted(new, key=lambda s: (s.line, s.name))

    result = DiffResult()

    # ---- Phase 1: exact (kind, name) matching ------------------------
    new_by_key: dict[tuple[str, str], Symbol] = {
        (s.kind, s.name): s for s in new_sorted
    }
    old_by_key: dict[tuple[str, str], Symbol] = {
        (s.kind, s.name): s for s in old_sorted
    }

    matched_old_keys: set[tuple[str, str]] = set()
    matched_new_keys: set[tuple[str, str]] = set()

    for key, old_sym in old_by_key.items():
        new_sym = new_by_key.get(key)
        if new_sym is None:
            continue
        matched_old_keys.add(key)
        matched_new_keys.add(key)
        if old_sym.signature == new_sym.signature:
            result.changes.append(
                SymbolChange(kind=ChangeKind.UNCHANGED, old=old_sym, new=new_sym)
            )
        else:
            result.changes.append(
                SymbolChange(kind=ChangeKind.MODIFIED, old=old_sym, new=new_sym)
            )

    remaining_old = [s for s in old_sorted if (s.kind, s.name) not in matched_old_keys]
    remaining_new = [s for s in new_sorted if (s.kind, s.name) not in matched_new_keys]

    # ---- Phase 2: rename detection ----------------------------------
    if detect_renames and remaining_old and remaining_new:
        used_new_ids: set[int] = set()  # id() of already-paired new symbols

        for old_sym in remaining_old:
            old_tokens = _signature_tokens(old_sym.signature)

            best_new: Symbol | None = None
            best_score: float = -1.0
            best_distance: int = 10**9

            for new_sym in remaining_new:
                if id(new_sym) in used_new_ids:
                    continue
                if new_sym.kind != old_sym.kind:
                    continue  # same-kind hard filter
                score = _jaccard(old_tokens, _signature_tokens(new_sym.signature))
                distance = abs(old_sym.line - new_sym.line)
                # Prefer higher score; break ties with closer line.
                if (score > best_score) or (
                    score == best_score and distance < best_distance
                ):
                    best_score = score
                    best_distance = distance
                    best_new = new_sym

            if best_new is None or best_score < 0:
                continue
            if best_score >= rename_threshold:
                result.changes.append(
                    SymbolChange(
                        kind=ChangeKind.RENAMED,
                        old=old_sym,
                        new=best_new,
                        score=best_score,
                    )
                )
                used_new_ids.add(id(best_new))
            else:
                # Same-kind candidate existed but scored below threshold.
                # Log for audit — conservative demotion keeps us from
                # fabricating renames on weak signal.
                result.demoted.append((old_sym, best_new, best_score))

        # Any old/new unpaired after phase 2 → REMOVED / ADDED
        still_old = [s for s in remaining_old
                     if not any(c.old is s for c in result.changes
                                if c.kind == ChangeKind.RENAMED)]
        still_new = [s for s in remaining_new if id(s) not in used_new_ids]
    else:
        still_old = remaining_old
        still_new = remaining_new

    for s in still_old:
        result.changes.append(
            SymbolChange(kind=ChangeKind.REMOVED, old=s, new=None)
        )
    for s in still_new:
        result.changes.append(
            SymbolChange(kind=ChangeKind.ADDED, old=None, new=s)
        )

    return result
