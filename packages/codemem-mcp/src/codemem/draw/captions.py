"""Authored captions over the derived graph (diagram-generation M5, map Ticket 12).

One flat, path-keyed JSON sidecar feeds both the living doc and the explorer::

    {"@start": "src/aa_ma/render/cli.py",
     "src/aa_ma/render/": "Markdown -> HTML and view linting."}

Prose renders OUTSIDE the mermaid fence (``%%`` comments are invisible at render), so
a caption edit is never diagram drift; only ``@start`` reaches the mermaid, as a
highlight. Path keying makes zoom levels free: a directory key (trailing ``/``) covers the
node that is that directory and every node inside it; a file key covers its file and
symbol nodes; nothing covers an ancestor. No tool deletes a caption.
"""

from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from pathlib import Path

from .cut import Cut

__all__ = [
    "CAPTIONS_PATH", "GENERATED_DIR", "MAX_SIDECAR_BYTES", "START", "CaptionFinding",
    "check_generated_target", "escape_prose", "for_cut", "json_island", "load", "orphans", "start_ids",
]

CAPTIONS_PATH = "docs/architecture.captions.json"  # beside, never inside, the generated dir
GENERATED_DIR = "docs/architecture/"  # 100% generated (M6); nothing authored lives here
MAX_SIDECAR_BYTES = 1 << 20  # authored prose; a megabyte is already absurd
START = "@start"
_BLOCK_START = re.compile(r"^(```|~~~|[#|+*-])")  # `>` is already `&gt;` by then


@dataclass(frozen=True)
class CaptionFinding:
    path: str
    code: str  # ORPHAN_CAPTION | UNKNOWN
    reason: str


def load(repo_root: Path) -> dict[str, str]:
    """The sidecar's mapping; an absent file means no captions, a malformed one is an error.

    Every failure is a ``ValueError`` naming the file: bad JSON, deep nesting, an
    unreadable file, a duplicate key, an unknown ``@`` directive, an empty ``@start``.
    """
    p = repo_root / CAPTIONS_PATH
    if not p.is_file():
        return {}
    try:
        if p.stat().st_size > MAX_SIDECAR_BYTES:
            raise ValueError(f"larger than {MAX_SIDECAR_BYTES} bytes")
        data = json.loads(p.read_text(encoding="utf-8"), object_pairs_hook=_unique_keys)
    except (ValueError, RecursionError, OSError) as exc:  # JSONDecodeError, UnicodeDecodeError are ValueErrors
        raise ValueError(f"{CAPTIONS_PATH}: {type(exc).__name__}: {exc}") from exc
    if not isinstance(data, dict) or not all(isinstance(v, str) for v in data.values()):
        raise ValueError(f"{CAPTIONS_PATH}: must be a flat object of path -> string")
    unknown = sorted(k for k in data if k.startswith("@") and k != START)
    if unknown:
        raise ValueError(f"{CAPTIONS_PATH}: unknown directive {unknown[0]!r}; only {START} exists")
    if START in data and not data[START]:
        raise ValueError(f"{CAPTIONS_PATH}: {START} is empty")
    return data


def orphans(
    captions: dict[str, str], known_paths: set[str], planned_paths: set[str]
) -> list[CaptionFinding]:
    """Captions whose path is gone. ``planned_paths`` is the plan's ``(new)`` set: UNKNOWN, not orphan.

    A symbol key (``a.py::f``) exists when its file does.
    """
    findings = []
    for key, value in sorted(captions.items()):
        path = value if key == START else key
        file = path.split("::", 1)[0]
        if _exists(file, known_paths):
            continue
        if _exists(file, planned_paths) or file.rstrip("/") in planned_paths:
            findings.append(CaptionFinding(path, "UNKNOWN", "planned (new) in the plan; not on disk yet"))
        elif not file.endswith("/") and _exists(file + "/", known_paths):
            findings.append(CaptionFinding(path, "ORPHAN_CAPTION", "a directory: the key needs a trailing /"))
        else:
            findings.append(CaptionFinding(path, "ORPHAN_CAPTION", "path not in the repo"))
    return findings


def for_cut(c: Cut, captions: dict[str, str]) -> dict[str, str]:
    """The captions that apply to this cut's nodes, keyed by caption path."""
    labels = c.nodes.values()
    return {
        k: v for k, v in sorted(captions.items())
        if k != START and any(_names(k, label) for label in labels)
    }


def start_ids(c: Cut, captions: dict[str, str] | None) -> list[str]:
    """Node ids that are, or contain, the ``@start`` path — so collapsed levels still point the way."""
    start = (captions or {}).get(START)
    if not start:
        return []
    return sorted(
        nid for nid, label in c.nodes.items()
        if _names(start, label) or start.startswith(label + "/")  # or a collapsed dir holding it
    )


def escape_prose(text: str) -> str:
    """A caption as ONE inert markdown line, for M6's living doc (outside the fence).

    Whitespace runs (incl. newlines) collapse to a space; ``< > &`` become entities; a
    leading fence opener or block marker (```` ``` ~~~ # | + * - ````) is backslash-escaped
    (a leading ``>`` is already the inert ``&gt;``).
    """
    line = html.escape(" ".join(text.split()), quote=False)
    return _BLOCK_START.sub(r"\\\1", line)


def json_island(obj: object) -> str:
    """JSON safe inside ``<script type="application/json">`` (M12): no ``< > &`` survive,
    so a caption holding ``</script>`` or ``<!--`` cannot end the island."""
    return (
        json.dumps(obj, ensure_ascii=False, sort_keys=True)
        .replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    )


def check_generated_target(repo_root: Path, target: Path) -> None:
    """Refuse a generated write outside ``docs/architecture/`` or onto the authored sidecar."""
    root = repo_root.resolve()
    generated = root / GENERATED_DIR  # built, never followed: a symlinked docs/ must not move it
    if (root / GENERATED_DIR).resolve() != generated:
        raise ValueError(f"refusing to write: {GENERATED_DIR} (or a parent) is a symlink")
    resolved = target.resolve()
    if resolved == root / CAPTIONS_PATH:
        raise ValueError(f"refusing to overwrite the authored sidecar {CAPTIONS_PATH}")
    if not resolved.is_relative_to(generated):
        raise ValueError(f"refusing to write {target}: generated files live under {GENERATED_DIR}")


def _names(key: str, label: str) -> bool:
    if key.endswith("/"):  # the directory itself, or anything inside it — never an ancestor
        return label == key[:-1] or label.startswith(key)
    return label == key or label.startswith(key + "::")


def _unique_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    keys = [k for k, _ in pairs]
    if dup := next((k for k in keys if keys.count(k) > 1), None):
        raise ValueError(f"duplicate key {dup!r}")
    return dict(pairs)


def _exists(path: str, known: set[str]) -> bool:
    if path.endswith("/"):
        return any(k.startswith(path) for k in known)
    return path in known
