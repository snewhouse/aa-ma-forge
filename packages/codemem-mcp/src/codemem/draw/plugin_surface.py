"""The plugin surface: commands -> skills -> agents -> hooks, from markdown (diagram-generation M4).

Regex over ``claude-code/{commands,skills,agents,hooks,rules}`` (Ticket 4:
``docs/research/diagram-generation-plugin-surface-extraction.md``). No codemem index.

* Node identity is the dir/file STEM, never frontmatter ``name:`` (fork-provenance
  SKILL.md files open with an HTML comment; ``name:`` can differ from the dir).
  ``_owner`` is the ONE rule: the node set is exactly the owners of the files walked.
* Four syntaxes: ``Skill(x)``, ``/x`` kept only when ``commands/x.md`` exists (``/x-*``
  expands), ``subagent_type: x``, and a hook literal (the ``aa-ma-*.sh`` naming
  convention, so a missing hook reads DANGLING, plus every on-disk hook by name).
* Every reference is ON_DISK, DECLARED_EXTERNAL (``surface_allowlist.EXTERNAL``) or
  DANGLING. ``/x`` is filtered, never classified: ``/tmp``, ``/goal`` are noise.
* Edge kind is the DESTINATION kind — M6's ``@skill``/``@command``/``@agent``/``@hook``
  sigils filter on it. Self-edges are dropped; ``docs/``, ``claude-code/codemem/`` and
  symlinks are out of the graph.
* ``Level.L2`` is only a fixed ``node_id`` namespace seed here, not a zoom level.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from .cut import MAX_EDGES, Cut, Level, from_edges
from .surface_allowlist import EXTERNAL, HOOK_TABLE

__all__ = ["RefClass", "Surface", "SurfaceEdge", "as_json", "extract"]

_DIRS = {"commands": "command", "skills": "skill", "agents": "agent", "hooks": "hook", "rules": "rule"}
_SKILL = re.compile(r"Skill\(([A-Za-z0-9_:-]+)\)")  # ':' — plugin-namespaced names
_AGENT = re.compile(r'subagent_type\s*[=:]\s*"?([A-Za-z0-9_:-]+)')
_HOOK_CONVENTION = r"(?:aa-ma-|pre-compact-aa-ma|security-static-check)[a-z0-9-]{0,64}\.sh"
# Lookbehind/ahead keep path fragments out (`/tmp/x-y.log`) but let a sentence end: `Run /x.`
_COMMAND = re.compile(r"(?<![A-Za-z0-9_./~-])/([a-z][a-z0-9-]*)(\*?)(?![A-Za-z0-9_/-]|\.[A-Za-z0-9_])")
_HOOK_BLOCK = re.compile(r"AA_MA_HOOKS=\((.*?)\n\)", re.DOTALL)
_HOOK_ROW = re.compile(r'"([A-Za-z]+)\|([^"]*?)\|([A-Za-z0-9_.-]+\.sh)\|')


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
    cut: Cut  # DANGLING edges are not drawn; orphans are, as isolated nodes
    edges: list[SurfaceEdge]  # every classified reference, sorted
    orphans: list[str]  # "<kind>:<stem>" with no inbound ON_DISK edge; rules are entry points
    hook_events: dict[str, list[str]]  # hook -> ["Event" | "Event:Matcher"]
    errors: list[str]


def extract(repo_root: Path) -> Surface:
    cc = repo_root / "claude-code"
    errors: list[str] = [] if cc.is_dir() else ["claude-code/: not found"]
    owned = [(f, o) for top in _DIRS for f in sorted((cc / top).rglob("*")) if (o := _owner(cc, f))]
    nodes = {o for _, o in owned}
    commands = [_stem(n) for n in nodes if n.startswith("command:")]
    hook_names = sorted({_stem(n) for n in nodes if n.startswith("hook:")} | EXTERNAL["hook"])
    hook_rx = re.compile(
        rf"(?<![\w.-])({'|'.join([_HOOK_CONVENTION, *map(re.escape, hook_names)])})(?![\w-])"
    )

    found: set[SurfaceEdge] = set()
    for f, src in owned:
        text = f.read_text(encoding="utf-8", errors="replace")
        for kind, rx in (("skill", _SKILL), ("agent", _AGENT), ("hook", hook_rx)):
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
    orphans = sorted(n for n in nodes if not n.startswith("rule:") and n not in inbound)
    drawn = {(e.src, e.dst, e.kind) for e in edges if e.ref_class is not RefClass.DANGLING}
    cut = from_edges(drawn, Level.L2, frozenset(orphans))
    if cut.dropped:
        errors.append(f"{cut.dropped} surface edges over mermaid maxEdges {MAX_EDGES} not drawn")
    hook_events, hook_errors = _hook_events(repo_root, nodes)
    return Surface(cut=cut, edges=edges, orphans=orphans, hook_events=hook_events, errors=errors + hook_errors)


def as_json(s: Surface) -> dict:
    """The golden's shape; ``cut`` is omitted because it is derived from ``edges``."""
    return {
        "edges": [{"src": e.src, "dst": e.dst, "kind": e.kind, "ref_class": e.ref_class.value} for e in s.edges],
        "orphans": s.orphans,
        "hook_events": s.hook_events,
        "errors": s.errors,
    }


def _stem(node: str) -> str:
    return node.split(":", 1)[1]


def _owner(cc: Path, f: Path) -> str | None:
    """The node a file belongs to — the single definition of node identity.

    Commands, agents and rules are top-level ``*.md``; a skill owns every ``.md``/``.sh``
    under its dir; a hook is any ``*.sh`` under ``hooks/``. Symlinks are never followed.
    """
    if f.is_symlink() or not f.is_file():
        return None
    parts = f.relative_to(cc).parts
    kind = _DIRS[parts[0]]
    if kind == "skill":
        return f"skill:{parts[1]}" if len(parts) > 2 and f.suffix in (".md", ".sh") else None
    if kind == "hook":
        return f"hook:{f.name}" if f.suffix == ".sh" else None
    return f"{kind}:{f.stem}" if len(parts) == 2 and f.suffix == ".md" else None


def _classify(kind: str, name: str, nodes: set[str]) -> RefClass:
    if f"{kind}:{name}" in nodes:
        return RefClass.ON_DISK
    return RefClass.DECLARED_EXTERNAL if name in EXTERNAL.get(kind, ()) else RefClass.DANGLING


def _hook_events(repo_root: Path, nodes: set[str]) -> tuple[dict[str, list[str]], list[str]]:
    table = repo_root / HOOK_TABLE
    if not table.is_file():
        return {}, [f"{HOOK_TABLE}: not found — hook wiring unreadable"]
    block = _HOOK_BLOCK.search(table.read_text(encoding="utf-8", errors="replace"))
    if block is None:
        return {}, [f"{HOOK_TABLE}: no AA_MA_HOOKS=( ... ) table — format changed?"]
    events: dict[str, set[str]] = defaultdict(set)
    errors = []
    for i, line in enumerate(block.group(1).splitlines(), 1):
        if '"' not in line:
            continue
        row = _HOOK_ROW.search(line)
        if row is None:
            errors.append(f"{HOOK_TABLE}: AA_MA_HOOKS row {i} unparsed")
            continue
        event, matcher, hook = row.groups()
        events[hook].add(f"{event}:{matcher}" if matcher else event)
    errors += [f"{HOOK_TABLE} wires {h}, not in claude-code/hooks/" for h in sorted(events) if f"hook:{h}" not in nodes]
    return {h: sorted(v) for h, v in sorted(events.items())}, errors
