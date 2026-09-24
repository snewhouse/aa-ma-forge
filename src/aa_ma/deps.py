"""`Dependencies:` — tolerant reader, `M`-prefix-aware resolver, Milestone graph, advisory.

diagram-generation M7 (map Tickets 7 and 16). Planning-time only: ``aa-ma-gate`` never
reads this field, and the advisory never blocks. The canonical *write* form lives in
:data:`aa_ma.grammar.CANONICAL_DEPENDENCY_RE`; this module reads every legacy form::

    None (…)            Milestone 2 · Milestone M2 · M2 · M2a    Milestones 1, 2 · 1-3
    Sub-step 1.1 · Step 1.1 · Task 1.1 · M1.1 · Steps 1.1–1.3    `other-plan` M5 (cross-plan)

The hazard is the resolver: ``MILESTONE_RE`` strips a leading ``M`` but step numbers keep
it (``### Step M2a.1:``), so a resolver that "normalises" both sides alike reports dozens of
false failures on the correct corpus (measured: context-log 2026-09-24). Milestone references are compared M-stripped, step
references are tried as written, with and without the ``M``.

    python -m aa_ma.deps graph <tasks.md>      # '### Milestone graph' mermaid block, for plan §13
    python -m aa_ma.deps check <tasks.md>      # UNRESOLVED_DEPENDENCY lines; exit 1 on any
    python -m aa_ma.deps advisory <tasks.md>   # the warning line, if any; always exit 0
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from aa_ma.grammar import NUMBER_BODY, Block, field_pattern, own_text, split_milestones, split_steps

__all__ = [
    "MAX_FINDINGS", "MAX_SPAN", "DepRef", "Kind", "advisory", "check", "dependency_fields", "main", "milestone_graph",
    "parse_dependencies", "resolve",
]


Kind = Literal["milestone", "step", "none", "cross-plan"]

# ponytail: no real plan spans more than a few dozen milestones; a wider range is a typo, and
# expanding `1-99999999` was an OOM. Beyond the cap only the endpoint is kept (and reported).
MAX_SPAN = 100
MAX_FINDINGS = 200  # `check` output reaches an agent's context; the rest is counted, not printed


@dataclass(frozen=True)
class DepRef:
    raw: str
    kind: Kind
    number: str | None  # "2", "2a", "1.1", "M2a.1"; milestone numbers are M-stripped
    task_slug: str | None  # set iff kind == "cross-plan"


# One number shape, from the heading grammar: an optional `M`, then this body.
_BODY = NUMBER_BODY
_END = r"(?![\w.]|-(?!\d))"  # a number ends here; `1-3` is a range, `1.1-alpha` is not a number
_NUM = rf"M?{_BODY}{_END}"
_SEP = r"(?:,[ \t]*and|,|and|[–-])"
_REF_RE = re.compile(
    rf"(?<![\w.`/-])(?:`?(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)+)`?[ \t]+)?"
    rf"(?:(?P<noun>Milestones?|Sub-steps?|Steps?|Tasks?)[ \t]+(?P<num>{_NUM})|(?P<bare>M{_BODY}{_END}))"
    rf"(?P<more>(?:[ \t]*{_SEP}[ \t]*{_NUM})*)"
)
_MORE_RE = re.compile(rf"[ \t]*({_SEP})[ \t]*({_NUM})")
_PARENS_RE = re.compile(r"\([^()]*\)")


_DEPS_RE = field_pattern("Dependencies")
_STATUS_RE = field_pattern("Status")


def parse_dependencies(value: str) -> list[DepRef]:
    """Every reference in one field value; ``[]`` means prose with no reference at all."""
    text = _PARENS_RE.sub("", value)  # asides never name a dependency: "M2 (M1 recommended)"
    if re.match(r"None\b", text.strip()):
        return [DepRef("None", "none", None, None)]
    refs: list[DepRef] = []
    for m in _REF_RE.finditer(text):
        first = m["num"] or m["bare"]
        milestone = (m["noun"] or "").startswith("Milestone") or (not m["noun"] and "." not in first)
        kind: Kind = "cross-plan" if m["slug"] else "milestone" if milestone else "step"
        numbers = [first]
        for sep, num in _MORE_RE.findall(m["more"]):
            numbers += _span(numbers[-1], num) if sep in "–-" else [num]
        span = m.group(0)[: len(m.group(0)) - len(m["more"])]
        for i, n in enumerate(numbers):
            number = n.lstrip("M") if kind != "step" else n
            refs.append(DepRef(span if i == 0 else n, kind, number, m["slug"]))
    return refs


def resolve(refs: list[DepRef], tasks_md: str) -> list[DepRef]:
    """The references that name no heading in ``tasks_md``; ``none`` and cross-plan are exempt."""
    milestones, steps = _numbers(tasks_md)
    return [
        r for r in refs
        if (r.kind == "milestone" and r.number not in milestones)
        or (r.kind == "step" and _step(r.number, steps) is None)
    ]


def dependency_fields(tasks_md: str) -> list[tuple[str, str]]:
    """``(owner, value)`` per milestone and sub-step that has a ``Dependencies:`` field."""
    return [(owner, value) for owner, _, value, _ in _fields(tasks_md)]


def check(tasks_md: str) -> list[str]:
    """``UNRESOLVED_DEPENDENCY`` findings — a planning-time finding, never a gate."""
    out = []
    for owner, value in dependency_fields(tasks_md):
        refs = parse_dependencies(value)
        if not refs:
            out.append(f"UNRESOLVED_DEPENDENCY {owner}: no reference in {value!r}")
        out += [f"UNRESOLVED_DEPENDENCY {owner}: {r.raw}" for r in resolve(refs, tasks_md)]
    return out


def milestone_graph(tasks_md: str) -> str:
    """Mermaid flowchart of milestone ``Dependencies:`` — the §13 Milestone graph.

    Round ``("…")`` nodes on purpose: §13's lint reads ``[...]`` labels as path claims, and a
    milestone title may name a file that does not exist yet.
    """
    lines = ["flowchart LR"]
    for b in split_milestones(tasks_md):
        title = f"Milestone {b.number}: {b.title}"
        title = title.replace('"', "#quot;").replace("<", "#lt;").replace(">", "#gt;")
        lines.append(f'  {_id(b.number)}("{title}")')
    lines += [f"  {_id(src)} --> {_id(dst)}" for src, dst in _edges(tasks_md)]
    return "\n".join(lines) + "\n"


def advisory(tasks_md: str) -> str:
    """One line per ACTIVE milestone whose dependency is not COMPLETE; ``""`` when none."""
    status = {b.number: _status(b) for b in split_milestones(tasks_md)}
    return "\n".join(
        f"Milestone {dst} is ACTIVE but Milestone {src} (Dependencies) is {status[src] or 'UNKNOWN'}"
        for src, dst in _edges(tasks_md)
        if status[dst] == "ACTIVE" and status[src] != "COMPLETE"
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m aa_ma.deps", description="Dependencies: graph, check, advisory (planning-time).")
    ap.add_argument("command", choices=("graph", "check", "advisory"))
    ap.add_argument("tasks_md", type=Path)
    args = ap.parse_args(argv)
    try:
        text = args.tasks_md.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"aa_ma.deps: {exc}", file=sys.stderr)
        return 2
    if args.command == "graph":
        print(f"### Milestone graph\n\n```mermaid\n{milestone_graph(text)}```")
        return 0
    if args.command == "check":
        findings = check(text)
        for f in findings[:MAX_FINDINGS]:
            print(f)
        if len(findings) > MAX_FINDINGS:
            print(f"… {len(findings) - MAX_FINDINGS} more UNRESOLVED_DEPENDENCY findings")
        return 1 if findings else 0
    if note := advisory(text):
        print(note)
    return 0


def _span(lo: str, hi: str) -> list[str]:
    """``1-3`` -> 2, 3; ``1.1–1.3`` -> 1.2, 1.3. Anything else: just the endpoint."""
    a, _, x = lo.rpartition(".")
    b, _, y = hi.rpartition(".")
    if a == b and x.isdigit() and y.isdigit() and int(x) < int(y) <= int(x) + MAX_SPAN:
        return [f"{a}.{i}" if a else str(i) for i in range(int(x) + 1, int(y) + 1)]
    return [hi]


def _fields(tasks_md: str) -> list[tuple[str, Block, str, bool]]:
    """``(owner, milestone block, value, is_milestone_level)`` per ``Dependencies:`` field."""
    out = []
    for m in split_milestones(tasks_md):
        if v := _first(_DEPS_RE, own_text(m)):
            out.append((f"Milestone {m.number}", m, v, True))
        out += [
            (f"Sub-step {s.number}", m, v, False) for s in split_steps(m.text) if (v := _first(_DEPS_RE, s.text))
        ]
    return out


def _edges(tasks_md: str) -> list[tuple[str, str]]:
    milestones, steps = _numbers(tasks_md)
    owner = {s.number: b.number for b in split_milestones(tasks_md) for s in split_steps(b.text)}
    edges: list[tuple[str, str]] = []
    for _, m, value, milestone_level in _fields(tasks_md):
        if not milestone_level:
            continue
        for r in parse_dependencies(value):
            src = r.number if r.kind == "milestone" and r.number in milestones else None
            if r.kind == "step" and (s := _step(r.number, steps)):
                src = owner[s]
            if src and src != m.number and (src, m.number) not in edges:
                edges.append((src, m.number))
    return edges


def _numbers(tasks_md: str) -> tuple[set[str], set[str]]:
    blocks = split_milestones(tasks_md)
    return {b.number for b in blocks}, {s.number for b in blocks for s in split_steps(b.text)}


def _step(number: str | None, steps: set[str]) -> str | None:
    bare = (number or "").removeprefix("M")
    return next((n for n in (number, bare, f"M{bare}") if n in steps), None)


def _first(regex: re.Pattern[str], text: str) -> str | None:
    m = regex.search(text)
    return m.group(1) if m else None


def _status(b: Block) -> str | None:
    v = _first(_STATUS_RE, own_text(b))
    return v.split()[0].strip("*").upper() if v else None


def _id(number: str) -> str:
    return "M" + number.replace(".", "_")


if __name__ == "__main__":
    sys.exit(main())
