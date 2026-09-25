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
"""

from __future__ import annotations

import re

from aa_ma.grammar import H2_RE, scan_fences
from aa_ma.render.mermaid_lint import (
    NEW_RE,
    Finding,
    mermaid_fences,
    node_labels,
    section_13,
)

__all__ = [
    "COVERAGE_CUTOVER", "EXEMPT_DIRS", "MANIFESTS", "MAX_EXPANSIONS", "ROOT_DOCS",
    "contract_paths", "coverage_findings", "drawn_paths",
]

COVERAGE_CUTOVER = "2026-09-11"  # spec §XI item 13's cutover; a literal date, not a tag
_CREATED_RE = re.compile(r"^(?:\*\*Created:\*\*|Created:)[ \t]*(\d{4}-\d{2}-\d{2})", re.M)
_CONTRACT_RE = re.compile(r"^#### Contract[ \t]*$")
_ROW_RE = re.compile(r"^[ \t]*(?:[-*|][ \t]*)?(?:Create|Modify)[ \t]*:?[ \t|]+([^#]*)")
_FILE_RE = re.compile(r"^[ \t]*#[ \t]*file:[ \t]*(\S+)")
_PAREN_RE = re.compile(r"\([^()]*\)")
_LINES_RE = re.compile(r":\d+(?:-\d+)?$")
_BRACES_RE = re.compile(r"\{([^{}]*)\}")  # innermost group
MAX_EXPANSIONS = 256  # `{a,b}` x 25 is 2**25 paths; past this the token is kept whole
EXEMPT_DIRS = ("tests/", "docs/")
ROOT_DOCS = frozenset({"README.md", "CHANGELOG.md", "SECURITY.md", "CONTEXT.md"})
MANIFESTS = frozenset({"pyproject.toml", "package.json"})  # and every *.lock


def coverage_findings(plan_text: str) -> list[Finding]:
    """One ``UNDRAWN_PATH`` per Contract path no §13 node covers; ``[]`` when not applicable.

    Not applicable: ``Created:`` absent or before the cutover, an unterminated fence (the
    lint reports it), or no §13 (check 6's ``NO_SECTION``).
    """
    scan = scan_fences(plan_text)
    if scan.unterminated or not _in_force(scan.stripped):
        return []
    drawn = drawn_paths(plan_text, scan.stripped)
    if drawn is None:
        return []
    return [
        Finding(
            "UNDRAWN_PATH", line,
            f"{path}: named by a Contract but drawn by no §13 node "
            "(draw it, a directory node above it, or `(new)` if planned)",
        )
        for line, path in contract_paths(plan_text, scan.stripped)
        if not any(path == n or path.startswith(n + "/") for n in drawn)
    ]


def contract_paths(plan_text: str, stripped: str) -> list[tuple[int, str]]:
    """(1-based line, path) per non-exempt Create/Modify/``# file:`` path, in order."""
    lines, bare = plan_text.split("\n"), stripped.split("\n")
    out: list[tuple[int, str]] = []
    k = 0
    while k < len(bare):
        if not _CONTRACT_RE.match(bare[k]):
            k += 1
            continue
        k += 1
        # The Contract is the fences right under the heading: stop at the first line outside
        # a fence (prose or a heading), so a later example fence is never read as one.
        while k < len(bare) and not bare[k].strip():
            if lines[k].strip():  # blank in `stripped` but not in the text: inside a fence
                out += [(k + 1, p) for p in _row_paths(lines[k]) if not _exempt(p)]
            k += 1
    return out


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


def _in_force(stripped: str) -> bool:
    first_h2 = H2_RE.search(stripped)
    m = _CREATED_RE.search(stripped[: first_h2.start()] if first_h2 else stripped)
    return m is not None and m.group(1) >= COVERAGE_CUTOVER


def _row_paths(line: str) -> list[str]:
    if m := _FILE_RE.match(line):
        tokens = [m.group(1)]
    elif m := _ROW_RE.match(line):
        tokens = _split(_PAREN_RE.sub(" ", m.group(1)).replace("|", " "))
    else:
        return []
    paths = (_LINES_RE.sub("", tok.strip("`")) for tok in tokens)
    return [p for path in paths if path for p in _expand(path)]


def _split(text: str) -> list[str]:
    """Whitespace/comma separated, except inside `{...}` (a brace list is one token)."""
    out, cur, depth = [], [], 0
    for ch in text:
        depth += (ch == "{") - (ch == "}" and depth > 0)
        if depth == 0 and (ch.isspace() or ch == ","):
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    return [t for t in (*out, "".join(cur)) if t]


def _expand(token: str) -> list[str]:
    """`a/{b,c}.py` -> both paths; iterative (no recursion depth) and capped at MAX_EXPANSIONS."""
    done, todo, steps = [], [token], 0
    while todo:
        cur = todo.pop()
        m = _BRACES_RE.search(cur)
        if m is None:
            done.append(cur)
            continue
        steps += 1
        alts = m.group(1).split(",")
        if steps > MAX_EXPANSIONS or len(done) + len(todo) + len(alts) > MAX_EXPANSIONS:
            return [token]  # unreadable as a path list: flag the token itself (fail closed)
        todo += [cur[: m.start()] + a.strip() + cur[m.end():] for a in reversed(alts)]
    return done



def _exempt(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    return path.startswith(EXEMPT_DIRS) or path in ROOT_DOCS or name in MANIFESTS or name.endswith(".lock")
