"""Angle 6 check 8: every path a milestone's Contract creates or modifies is drawn in §13.

diagram-generation M10. Planning-time only: ``aa-ma-lint-views --coverage`` runs it for
``Skill(plan-verification)``; the milestone gate never passes ``--coverage`` (ADR-0009).

Rows read (both grammars in use, Ste 2026-09-25): ``Create``/``Modify`` rows and template
``# file: <path>`` lines, inside the fences under a ``#### Contract`` heading. ``{a,b}``
lists expand. Exempt: ``Test``/``Verify`` rows, ``tests/`` and ``docs/``, root docs, and
dependency manifests / lockfiles. A node covers its own path and — when it names a
directory — everything beneath it; a ``(new)`` node covers the path it plans.
"""

from __future__ import annotations

import re

from aa_ma.grammar import H2_RE, scan_fences
from aa_ma.render.mermaid_lint import (
    _NEW_RE,
    Finding,
    _mermaid_fences,
    _node_labels,
    section_13,
)

__all__ = ["COVERAGE_CUTOVER", "contract_paths", "coverage_findings", "drawn_paths"]

COVERAGE_CUTOVER = "2026-09-11"  # spec §XI item 13's cutover; a literal date, not a tag
_CREATED_RE = re.compile(r"^(?:\*\*Created:\*\*|Created:)[ \t]*(\d{4}-\d{2}-\d{2})", re.M)
_CONTRACT_RE = re.compile(r"^#### Contract[ \t]*$")
_ROW_RE = re.compile(r"^[ \t]*(?:Create|Modify)[ \t]+([^#]+)")
_FILE_RE = re.compile(r"^[ \t]*#[ \t]*file:[ \t]*(\S+)")
_TOKEN_RE = re.compile(r"[^\s,{}]*\{[^}]*\}[^\s,]*|[^\s,]+")  # keeps `a/{b,c}.py` whole
_PATHLIKE_RE = re.compile(r"[\w.@*/-]+")
_BRACES_RE = re.compile(r"\{([^{}]*)\}")
_ROOT_DOCS = frozenset({"README.md", "CHANGELOG.md", "SECURITY.md", "CONTEXT.md"})
_MANIFESTS = frozenset({"pyproject.toml", "package.json"})  # and every *.lock


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
    return {
        tok.rstrip("/")
        for _, src in _mermaid_fences(body)
        for label in _node_labels(src).values()
        for tok in _NEW_RE.sub("", label).split()
        if _pathlike(tok)
    }


def _in_force(stripped: str) -> bool:
    first_h2 = H2_RE.search(stripped)
    m = _CREATED_RE.search(stripped[: first_h2.start()] if first_h2 else stripped)
    return m is not None and m.group(1) >= COVERAGE_CUTOVER


def _row_paths(line: str) -> list[str]:
    if m := _FILE_RE.match(line):
        tokens = [m.group(1)]
    elif m := _ROW_RE.match(line):
        tokens = _TOKEN_RE.findall(m.group(1))
    else:
        return []
    return [p for tok in tokens for p in _expand(tok) if _pathlike(p)]


def _expand(token: str) -> list[str]:
    m = _BRACES_RE.search(token)
    if m is None:
        return [token]
    head, tail = token[: m.start()], token[m.end():]
    return [p for alt in m.group(1).split(",") for p in _expand(head + alt.strip() + tail)]


def _pathlike(tok: str) -> bool:
    """`src/x.py`, `uv.lock`, `claude-code/skills/u/` — not `(append)`, `§13` or `Files:`."""
    name = tok.rstrip("/").rsplit("/", 1)[-1]
    return bool(_PATHLIKE_RE.fullmatch(tok)) and ("/" in tok or "." in name[1:])


def _exempt(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    return (
        path.startswith(("tests/", "docs/"))
        or path in _ROOT_DOCS
        or name in _MANIFESTS
        or name.endswith(".lock")
    )
