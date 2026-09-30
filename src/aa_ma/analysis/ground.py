"""Grounding: every backticked name and number in a cited claim must occur in the cited file.

A claim unit is one list item or table row, or one sentence of prose, that cites a repo file as
`path` or `path:line`. Tokens are searched within ±WINDOW lines of a cited line, or anywhere in a
file cited without one. A cited path that is missing or leaves the repo is ungrounded itself.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from . import stamp

WINDOW = 20
CITED_FILE_MAX_BYTES = 2_000_000  # also the cap on the markdown file being grounded
SPAN = re.compile(r"`([^`\n]+)`")
# `path:10-40` is grounded against lines 10-40 widened by ±WINDOW.
CITATION = re.compile(
    r"(?P<path>[\w./-]+?)(?::(?P<line>\d{1,9})(?:-(?P<end>\d{1,9}))?)?"
)
# A number standing alone: not inside a word or a dotted version (v0.16.0), not a list marker.
NUMBER = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?![\w]|\.\d)")
LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
FENCE = re.compile(r"^\s*(```|~~~)")


@dataclass(frozen=True)
class Ungrounded:
    md_line: int
    citation: str
    token: str
    missing: bool = False  # the cited path itself is missing or outside the repo


def _units(text: str):
    """(1-based md line, unit text) for every list item, table row and prose sentence."""
    fenced = False
    for n, line in enumerate(text.splitlines(), 1):
        if FENCE.match(line):
            fenced = not fenced
            continue
        if fenced or not line.strip():
            continue
        if LIST_ITEM.match(line):
            yield n, LIST_ITEM.sub("", line, count=1)
        elif line.lstrip().startswith("|"):
            yield n, line
        else:
            for sentence in SENTENCE_END.split(line):
                yield n, sentence


def _kind(repo: Path, rel: str) -> str:
    """'file', 'dir', 'escapes' or 'missing' for a repo-relative path."""
    if not stamp.contained(repo, rel):
        return "escapes"
    target = (repo / rel).resolve()
    if target.is_file():
        return "file"
    return "dir" if target.is_dir() else "missing"


def _spans(unit: str, repo: Path):
    """(span, citation match or None, path kind or None) for each backticked span.

    A span is a citation when it names an existing repo path, carries `:line`, or has a `/`."""
    for span in SPAN.findall(unit):
        m = CITATION.fullmatch(span)
        kind = _kind(repo, m["path"]) if m else None
        if m and (m["line"] or "/" in m["path"] or kind in ("file", "dir")):
            yield span, m, kind
        else:
            yield span, None, None


def _window(lines: list[str], m: re.Match[str]) -> str:
    if m["line"] is None:
        return "\n".join(lines)
    start = int(m["line"])
    end = int(m["end"] or start)
    return "\n".join(lines[max(0, start - 1 - WINDOW) : end + WINDOW])


def ground(md_path: Path, repo: Path) -> list[Ungrounded]:
    """Raises OSError when `md_path` is a symlink, not a regular file, or over the size cap."""
    repo = Path(repo)
    text = stamp.read_regular(Path(md_path), limit=CITED_FILE_MAX_BYTES)
    files: dict[str, list[str] | None] = {}  # each cited file is read once per call
    out: list[Ungrounded] = []
    for n, unit in _units(text):
        cites, names, dirs = [], [], []
        for span, m, kind in _spans(unit, repo):
            if kind == "dir":
                dirs.append(m["path"])
            elif m is None:
                # A markdown table cell must write `|` as `\|`; the source holds the bare `|`.
                names.append(span.replace("\\|", "|"))
            else:
                cites.append((m, kind))
        windows = []
        for m, kind in cites:
            path = m["path"]
            if path not in files:
                try:
                    if kind != "file":
                        raise OSError(kind)
                    files[path] = stamp.read_regular(
                        (repo / path).resolve(), limit=CITED_FILE_MAX_BYTES
                    ).splitlines()
                except (OSError, UnicodeDecodeError):
                    files[path] = None
            if files[path] is None:
                out.append(Ungrounded(n, m[0], path, missing=True))
            else:
                windows.append(_window(files[path], m))
        if not windows:
            continue
        # ADR-0008 is grounded by citing docs/adr/0008-….md; a cited dir grounds its own name.
        windows += [m["path"] for m, _ in cites] + dirs
        tokens = dict.fromkeys(names + NUMBER.findall(SPAN.sub(" ", unit)))
        out += [
            Ungrounded(n, cites[0][0][0], t)
            for t in tokens
            if not any(t in w for w in windows)
        ]
    return out


def cited_paths(md: str, repo: Path) -> list[str]:
    """Every existing repo file and directory (`dir/`) the text cites — a section's map entry."""
    repo = Path(repo)
    found = set()
    for _, unit in _units(md):
        for _, m, kind in _spans(unit, repo):
            if kind == "file":
                found.add(m["path"])
            elif kind == "dir":
                found.add(m["path"].rstrip("/") + "/")
    return sorted(found)
