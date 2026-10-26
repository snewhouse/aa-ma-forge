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
Contract, every row verb, nothing exempt (a test the Contract names is predicted).
M11's ``aa_ma.contract_rows`` takes it over (plan, Milestone 11 Contract).
"""

from __future__ import annotations

import re

from aa_ma.grammar import H2_RE, PLAN_MILESTONE_RE, scan_fences
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
_CREATED_RE = re.compile(
    r"^(?:\*\*Created:\*\*|Created:)[ \t]*(\d{4}-\d{2}-\d{2})", re.M
)
_CONTRACT_RE = re.compile(r"^#### Contract[ \t]*$")
_ROW_RE = re.compile(r"^[ \t]*(?:[-*|][ \t]*)?(?:Create|Modify)[ \t]*:?[ \t|]+([^#]*)")
_ANY_ROW_RE = re.compile(
    r"^[ \t]*(?:[-*|][ \t]*)?(?:Create|Modify|Test|Move|Merge|Delete)[ \t]*:?[ \t|]+([^#]*)"
)
_HEADING_RE = re.compile(r"^(#{1,6})[ \t]")
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
            "UNDRAWN_PATH",
            line,
            f"{path}: named by a Contract but drawn by no §13 node "
            "(draw it, a directory node above it, or `(new)` if planned)",
        )
        for line, path in contract_paths(plan_text, scan.stripped)
        if not any(path == n or path.startswith(n + "/") for n in drawn)
    ]


def contract_paths(plan_text: str, stripped: str) -> list[tuple[int, str]]:
    """(1-based line, path) per non-exempt Create/Modify/``# file:`` path, in order."""
    return [
        (n, p)
        for n, p in _contract_rows(plan_text.split("\n"), stripped.split("\n"), _ROW_RE)
        if not _exempt(p)
    ]


def milestone_contract_paths(plan_text: str, milestone: str) -> list[str]:
    """Every path Milestone ``milestone``'s Contract names: all row verbs, none exempt, deduped.

    The milestone is the ``##``-``####`` heading :data:`aa_ma.grammar.PLAN_MILESTONE_RE`
    reads as ``milestone`` (the gate's number + separator grammar) up to the next heading of
    the same or a higher level; ``[]`` when it is absent, has no Contract, or the plan has an
    unterminated fence.
    """
    scan = scan_fences(plan_text)
    if scan.unterminated:
        return []
    lines, bare = plan_text.split("\n"), scan.stripped.split("\n")
    start = end = None
    for i, line in enumerate(bare):
        if start is None:
            m = PLAN_MILESTONE_RE.match(line)
            if m and m.group("number") == milestone:
                start, level = i, len(m.group("hashes"))
        elif (h := _HEADING_RE.match(line)) and len(h.group(1)) <= level:
            end = i
            break
    if start is None:
        return []
    rows = _contract_rows(lines[start:end], bare[start:end], _ANY_ROW_RE)
    return list(dict.fromkeys(p for _, p in rows))


def _contract_rows(
    lines: list[str], bare: list[str], row_re: re.Pattern[str]
) -> list[tuple[int, str]]:
    """(1-based line, path) per row path in the fences right under each ``#### Contract``."""
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
            # Blank in `stripped` but not in the text: inside a fence.
            if lines[k].strip():
                out += [(k + 1, p) for p in _row_paths(lines[k], row_re)]
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


def _row_paths(line: str, row_re: re.Pattern[str] = _ROW_RE) -> list[str]:
    if m := _FILE_RE.match(line):
        tokens = [m.group(1)]
    elif m := row_re.match(line):
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
            # Unreadable as a path list: flag the token itself (fail closed).
            return [token]
        todo += [cur[: m.start()] + a.strip() + cur[m.end() :] for a in reversed(alts)]
    return done


def _exempt(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    return (
        path.startswith(EXEMPT_DIRS)
        or path in ROOT_DOCS
        or name in MANIFESTS
        or name.endswith(".lock")
    )
