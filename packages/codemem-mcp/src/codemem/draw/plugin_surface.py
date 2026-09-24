"""The plugin surface: commands -> skills -> agents -> hooks, from markdown (diagram-generation M4).

Regex over ``claude-code/{commands,skills,agents,hooks,rules}`` (Ticket 4:
``docs/research/diagram-generation-plugin-surface-extraction.md``). No codemem index.

* Node identity is the dir/file STEM, never frontmatter ``name:`` (6/21 SKILL.md open
  with an HTML comment; one ``name:`` differs from its dir).
* Four syntaxes: ``Skill(x)``, ``/x`` kept only when ``commands/x.md`` exists (``/x-*``
  expands), ``subagent_type: x``, and an ``aa-ma-*.sh``-style hook literal.
* Every reference is ON_DISK, DECLARED_EXTERNAL (``surface_allowlist.EXTERNAL``) or
  DANGLING. ``/x`` is filtered, never classified: ``/tmp``, ``/goal`` are noise.
* Edge kind is the DESTINATION kind — M6's ``@skill``/``@command``/``@agent``/``@hook``
  sigils filter on it. Self-edges are dropped; ``docs/`` and ``claude-code/codemem/``
  are out of the graph.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from .cut import Cut, Level, from_edges
from .surface_allowlist import EXTERNAL, HOOK_TABLE

__all__ = ["RefClass", "Surface", "SurfaceEdge", "as_json", "extract"]

_DIRS = {"commands": "command", "skills": "skill", "agents": "agent", "hooks": "hook", "rules": "rule"}
_REFS = (
    ("skill", re.compile(r"Skill\(([A-Za-z0-9_:-]+)\)")),  # ':' — plugin-namespaced names
    ("agent", re.compile(r'subagent_type\s*[=:]\s*"?([A-Za-z0-9_:-]+)')),
    ("hook", re.compile(r"\b((?:aa-ma-|pre-compact-aa-ma|security-static-check)[a-z0-9-]*\.sh)\b")),
)
# Lookbehind/ahead keep path fragments out: `/tmp/x-y.log`, `.../aa-ma-plan-${SLUG}.log`.
_COMMAND = re.compile(r"(?<![A-Za-z0-9_./~-])/([a-z][a-z0-9-]*)(\*?)(?![A-Za-z0-9_./-])")
_HOOK_ROW = re.compile(r'"([A-Za-z]+)\|([A-Za-z|]*)\|([a-z0-9-]+\.sh)\|')


class RefClass(StrEnum):
    ON_DISK = "ON_DISK"
    DECLARED_EXTERNAL = "DECLARED_EXTERNAL"
    DANGLING = "DANGLING"


@dataclass(frozen=True, order=True)
class SurfaceEdge:
    src: str  # "<kind>:<stem>"
    dst: str
    kind: str  # destination kind: skill|command|agent|hook
    ref_class: RefClass


@dataclass(frozen=True)
class Surface:
    cut: Cut  # DANGLING edges are not drawn
    edges: list[SurfaceEdge]  # every classified reference, sorted
    orphans: list[str]  # bare stems with no inbound ON_DISK edge; rules are entry points
    hook_events: dict[str, list[str]]  # hook -> ["Event" | "Event:Matcher"]
    errors: list[str]


def extract(repo_root: Path) -> Surface:
    cc = repo_root / "claude-code"
    nodes = _nodes(cc)
    commands = [n.split(":", 1)[1] for n in nodes if n.startswith("command:")]
    found: set[SurfaceEdge] = set()
    for top in _DIRS:
        for f in sorted((cc / top).rglob("*")):
            src = _owner(cc, f)
            if src is None:
                continue
            text = f.read_text(encoding="utf-8", errors="replace")
            for kind, rx in _REFS:
                for name in rx.findall(text):
                    found.add(SurfaceEdge(src, f"{kind}:{name}", kind, _classify(kind, name, nodes)))
            for name, glob in _COMMAND.findall(text):
                if glob:
                    hits = [c for c in commands if c.startswith(name)]
                else:
                    hits = [name] if name in commands else []
                found |= {SurfaceEdge(src, f"command:{c}", "command", RefClass.ON_DISK) for c in hits}
    edges = sorted(e for e in found if e.src != e.dst)

    inbound = {e.dst for e in edges if e.ref_class is RefClass.ON_DISK}
    errors: list[str] = []
    return Surface(
        cut=from_edges({(e.src, e.dst, e.kind) for e in edges if e.ref_class is not RefClass.DANGLING}, Level.L2),
        edges=edges,
        orphans=sorted(n.split(":", 1)[1] for n in nodes if not n.startswith("rule:") and n not in inbound),
        hook_events=_hook_events(repo_root, nodes, errors),
        errors=errors,
    )


def as_json(s: Surface) -> dict:
    """The golden's shape; ``cut`` is omitted because it is derived from ``edges``."""
    return {
        "edges": [{"src": e.src, "dst": e.dst, "kind": e.kind, "ref_class": e.ref_class.value} for e in s.edges],
        "orphans": s.orphans,
        "hook_events": s.hook_events,
        "errors": s.errors,
    }


def _nodes(cc: Path) -> set[str]:
    nodes = {f"skill:{p.name}" for p in (cc / "skills").glob("*") if p.is_dir()}
    for top, kind in (("commands", "command"), ("agents", "agent"), ("rules", "rule")):
        nodes |= {f"{kind}:{p.stem}" for p in (cc / top).glob("*.md")}
    return nodes | {f"hook:{p.name}" for p in (cc / "hooks").rglob("*.sh")}


def _owner(cc: Path, f: Path) -> str | None:
    """The node a file belongs to: a skill owns everything under its dir."""
    if not f.is_file() or f.suffix not in (".md", ".sh"):
        return None
    parts = f.relative_to(cc).parts
    kind = _DIRS[parts[0]]
    if kind == "skill":
        return f"skill:{parts[1]}" if len(parts) > 2 else None
    return f"hook:{f.name}" if kind == "hook" else f"{kind}:{f.stem}"


def _classify(kind: str, name: str, nodes: set[str]) -> RefClass:
    if f"{kind}:{name}" in nodes:
        return RefClass.ON_DISK
    return RefClass.DECLARED_EXTERNAL if name in EXTERNAL.get(kind, ()) else RefClass.DANGLING


def _hook_events(repo_root: Path, nodes: set[str], errors: list[str]) -> dict[str, list[str]]:
    table = repo_root / HOOK_TABLE
    if not table.is_file():
        errors.append(f"{HOOK_TABLE}: not found — hook wiring unreadable")
        return {}
    events: dict[str, set[str]] = defaultdict(set)
    for event, matcher, hook in _HOOK_ROW.findall(table.read_text(encoding="utf-8")):
        events[hook].add(f"{event}:{matcher}" if matcher else event)
    if not events:
        errors.append(f"{HOOK_TABLE}: no event|matcher|hook.sh rows parsed — table format changed?")
    errors += [f"{HOOK_TABLE} wires {h}, not in claude-code/hooks/" for h in sorted(events) if f"hook:{h}" not in nodes]
    return {h: sorted(v) for h, v in sorted(events.items())}
