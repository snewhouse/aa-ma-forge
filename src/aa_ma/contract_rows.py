"""Contract rows: the paths a milestone's ``#### Contract`` names, with their verbs.

code-conventions-impact 11.2. The row grammar shared by ``aa_ma.render.coverage`` (Angle 6
check 8, planning time) and ``aa_ma.impact`` (§6.7 fence 4, gate time). Its own module,
not ``plan_parsers``: ``aa_ma.grammar`` imports ``plan_parsers``, so fence scanning there
would cycle; not ``render/``: ``render-is-leaf`` (ADR-0010) forbids aa_ma importing it.

Rows: ``<Verb> <path>…`` lines (verbs :data:`ROW_VERBS`, optional bullet, ``|``, or ``:``)
and template ``# file: <path>`` lines (read as ``Modify``), inside the fences right under
a ``#### Contract`` heading. Fail closed: every token of a row is a path — only
``# comments`` and ``(parentheticals)`` are dropped, backticks and ``:12-40`` line ranges
stripped, ``→``/``->`` read as separators — because a dropped path would pass silently.
``{a,b}`` lists expand, bounded: past ``MAX_EXPANSIONS`` the token stays whole.
"""

from __future__ import annotations

import re

from aa_ma.grammar import PLAN_MILESTONE_RE, scan_fences

__all__ = [
    "MAX_EXPANSIONS",
    "ROW_VERBS",
    "contract_rows",
    "milestone_contract_rows",
    "row_re",
]

ROW_VERBS = ("Create", "Modify", "Test", "Move", "Merge", "Delete")
MAX_EXPANSIONS = 256  # `{a,b}` x 25 is 2**25 paths; past this the token is kept whole

_CONTRACT_RE = re.compile(r"^#### Contract[ \t]*$")
_HEADING_RE = re.compile(r"^(#{1,6})[ \t]")
_FILE_RE = re.compile(r"^[ \t]*#[ \t]*file:[ \t]*(\S+)")
_PAREN_RE = re.compile(r"\([^()]*\)")
_LINES_RE = re.compile(r":\d+(?:-\d+)?$")
_BRACES_RE = re.compile(r"\{([^{}]*)\}")  # innermost group
_ARROWS = frozenset({"→", "->"})  # Move/Merge `old → new`: a separator, never a path


def row_re(verbs: tuple[str, ...]) -> re.Pattern[str]:
    """The row regex for ``verbs``: named groups ``verb`` and ``text`` (the row after it)."""
    return re.compile(
        rf"^[ \t]*(?:[-*|][ \t]*)?(?P<verb>{'|'.join(verbs)})[ \t]*:?[ \t|]+(?P<text>[^#]*)"
    )


_ALL_ROWS_RE = row_re(ROW_VERBS)


def milestone_contract_rows(plan_text: str, milestone: str) -> list[tuple[str, str]]:
    """``(verb, path)`` per row path of Milestone ``milestone``'s Contract, in order, deduped.

    The milestone is the ``##``-``####`` heading :data:`aa_ma.grammar.PLAN_MILESTONE_RE`
    reads as ``milestone`` up to the next heading of the same or a higher level. Every verb,
    nothing exempt. ``[]`` when it is absent, has no Contract, or the plan has an
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
    rows = contract_rows(lines[start:end], bare[start:end], _ALL_ROWS_RE)
    return list(dict.fromkeys((verb, path) for _, verb, path in rows))


def contract_rows(
    lines: list[str], bare: list[str], pattern: re.Pattern[str]
) -> list[tuple[int, str, str]]:
    """(1-based line, verb, path) per row path in the fences right under each ``#### Contract``.

    ``lines`` is the text, ``bare`` the same lines with fenced content blanked
    (``scan_fences(...).stripped``); ``pattern`` comes from :func:`row_re`.
    """
    out: list[tuple[int, str, str]] = []
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
                out += [(k + 1, v, p) for v, p in _row_paths(lines[k], pattern)]
            k += 1
    return out


def _row_paths(line: str, pattern: re.Pattern[str]) -> list[tuple[str, str]]:
    if m := _FILE_RE.match(line):
        verb, tokens = "Modify", [m.group(1)]
    elif m := pattern.match(line):
        verb = m.group("verb")
        tokens = _split(_PAREN_RE.sub(" ", m.group("text")).replace("|", " "))
    else:
        return []
    paths = (_LINES_RE.sub("", tok.strip("`")) for tok in tokens if tok not in _ARROWS)
    return [(verb, p) for path in paths if path for p in _expand(path)]


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
