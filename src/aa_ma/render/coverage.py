"""Angle 6 check 8: every path a milestone's Contract creates or modifies is drawn in §13.

diagram-generation M10. Planning-time only: ``aa-ma-lint-views --coverage`` runs it for
``Skill(plan-verification)``; the milestone gate never passes ``--coverage`` (ADR-0009).

Rows read (both grammars in use, Ste 2026-09-25): ``Create``/``Modify`` rows and template
``# file: <path>`` lines, inside the fences under a ``#### Contract`` heading. Fail closed
(§6.8): every token of a row is a path — only ``# comments`` and ``(parentheticals)`` are
dropped, backticks and ``:12-40`` line ranges stripped — because a dropped path would pass
silently. ``{a,b}`` lists expand, bounded: past ``MAX_EXPANSIONS`` the token stays whole. Exempt: ``Test``/``Verify`` rows, ``tests/`` and ``docs/``, root docs, and
dependency manifests / lockfiles. A node covers its own path and — when it names a
directory — everything beneath it; a ``(new)`` node covers the path it plans.

``milestone_contract_paths`` is the other reader (code-conventions-impact 10.7): the
predicted set of ``/execute-aa-ma-milestone`` §6.3 predicted-vs-actual, ONE milestone's
Contract, every row verb, nothing exempt (a test the Contract names is predicted). The row
grammar itself lives in :mod:`aa_ma.contract_rows` (11.2), shared with ``aa_ma.impact``.
"""

from __future__ import annotations


from aa_ma.contract_rows import (
    MAX_EXPANSIONS,
    contract_rows,
    covers,
    milestone_contract_rows,
    plan_created,
    row_re,
)
from aa_ma.grammar import scan_fences
from aa_ma.render.mermaid_lint import (
    NEW_RE,
    Finding,
    mermaid_fences,
    node_labels,
    section_13,
)

__all__ = [
    "COVERAGE_CUTOVER",
    "EXEMPT_DIRS",
    "MANIFESTS",
    "MAX_EXPANSIONS",
    "ROOT_DOCS",
    "contract_paths",
    "coverage_findings",
    "drawn_paths",
    "milestone_contract_paths",
]

COVERAGE_CUTOVER = "2026-09-11"  # spec §XI item 13's cutover; a literal date, not a tag
_ROW_RE = row_re(("Create", "Modify"))
EXEMPT_DIRS = ("tests/", "docs/")
ROOT_DOCS = frozenset({"README.md", "CHANGELOG.md", "SECURITY.md", "CONTEXT.md"})
MANIFESTS = frozenset({"pyproject.toml", "package.json"})  # and every *.lock


def coverage_findings(plan_text: str) -> list[Finding]:
    """One ``UNDRAWN_PATH`` per Contract path no §13 node covers; ``[]`` when not applicable.

    Not applicable: ``Created:`` absent or before the cutover, an unterminated fence (the
    lint reports it), or no §13 (check 6's ``NO_SECTION``).
    """
    scan = scan_fences(plan_text)
    if scan.unterminated or not _in_force(plan_text):
        return []
    drawn = drawn_paths(plan_text, scan.stripped)
    if drawn is None:
        return []
    return [
        Finding(
            "UNDRAWN_PATH",
            line,
            f"{path}: named by a Contract but drawn by no §13 node "
            "(draw it, a directory node above it, or `(new)` if planned)",
        )
        for line, path in contract_paths(plan_text, scan.stripped)
        if not any(covers(n, path) for n in drawn)
    ]


def contract_paths(plan_text: str, stripped: str) -> list[tuple[int, str]]:
    """(1-based line, path) per non-exempt Create/Modify/``# file:`` path, in order."""
    return [
        (n, p)
        for n, _, p in contract_rows(
            plan_text.split("\n"), stripped.split("\n"), _ROW_RE
        )
        if not _exempt(p)
    ]


def milestone_contract_paths(plan_text: str, milestone: str) -> list[str]:
    """Every path Milestone ``milestone``'s Contract names: all row verbs, none exempt, deduped.

    The milestone slice and the row grammar are :func:`aa_ma.contract_rows.milestone_contract_rows`'s.
    """
    return list(
        dict.fromkeys(p for _, p in milestone_contract_rows(plan_text, milestone))
    )


def drawn_paths(plan_text: str, stripped: str) -> set[str] | None:
    """Paths the §13 node labels name (``(new)`` included, trailing ``/`` dropped); None: no §13."""
    sec = section_13(plan_text, stripped)
    if sec is None:
        return None
    body = "\n".join(sec[1])
    # Every label token counts (`.importlinter`, `Makefile` are paths too); a prose word can
    # only ever cover a Contract path that literally is, or starts with, that word.
    return {
        tok.rstrip("/")
        for _, src in mermaid_fences(body)
        for label in node_labels(src).values()
        for tok in NEW_RE.sub("", label).split()
        if tok.rstrip("/")
    }


def _in_force(plan_text: str) -> bool:
    created = plan_created(plan_text)
    return created is not None and created >= COVERAGE_CUTOVER


def _exempt(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    return (
        path.startswith(EXEMPT_DIRS)
        or path in ROOT_DOCS
        or name in MANIFESTS
        or name.endswith(".lock")
    )
