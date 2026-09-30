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
CITED_FILE_MAX_BYTES = 2_000_000
SPAN = re.compile(r"`([^`\n]+)`")
CITATION = re.compile(r"(?P<path>[\w./-]+?)(?::(?P<line>\d+)(?:-\d+)?)?")
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


def _is_citation(repo: Path, span: str) -> re.Match[str] | None:
    """A span is a citation when it names an existing repo path, carries `:line`, or has a `/`."""
    m = CITATION.fullmatch(span)
    if m is None:
        return None
    path = m["path"]
    if m["line"] or "/" in path or _kind(repo, path) in ("file", "dir"):
        return m
    return None


def _window(repo: Path, path: str, line: str | None) -> str:
    lines = stamp.read_regular(
        (repo / path).resolve(), limit=CITED_FILE_MAX_BYTES
    ).splitlines()
    if line is None:
        return "\n".join(lines)
    at = int(line)
    return "\n".join(lines[max(0, at - 1 - WINDOW) : at + WINDOW])


def ground(md_path: Path, repo: Path) -> list[Ungrounded]:
    repo = Path(repo)
    out: list[Ungrounded] = []
    for n, unit in _units(Path(md_path).read_text(encoding="utf-8")):
        cites, names = [], []
        for span in SPAN.findall(unit):
            m = _is_citation(repo, span)
            # A markdown table cell must write `|` as `\|`; the source holds the bare `|`.
            (cites if m else names).append(m or span.replace("\\|", "|"))
        if not cites:
            continue
        windows = []
        for m in cites:
            kind = _kind(repo, m["path"])
            if kind == "dir":
                continue
            try:
                if kind != "file":
                    raise OSError(kind)
                windows.append(_window(repo, m["path"], m["line"]))
            except (OSError, UnicodeDecodeError):
                out.append(Ungrounded(n, m[0], m["path"]))
        if not windows:
            continue
        windows += [
            m["path"] for m in cites
        ]  # ADR-0008 is grounded by citing docs/adr/0008-….md
        tokens = dict.fromkeys(names + NUMBER.findall(SPAN.sub(" ", unit)))
        out += [
            Ungrounded(n, cites[0][0], t)
            for t in tokens
            if not any(t in w for w in windows)
        ]
    return out


def cited_paths(md: str, repo: Path) -> list[str]:
    """Every existing repo file and directory (`dir/`) the text cites — a section's map entry."""
    repo = Path(repo)
    found = set()
    for _, unit in _units(md):
        for span in SPAN.findall(unit):
            m = _is_citation(repo, span)
            if m is None:
                continue
            kind = _kind(repo, m["path"])
            if kind == "file":
                found.add(m["path"])
            elif kind == "dir":
                found.add(m["path"].rstrip("/") + "/")
    return sorted(found)
