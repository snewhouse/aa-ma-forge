"""The output secret gate: scan a report dir, redact what it finds, fail closed on what it cannot parse.

Layer 3 of three (agents never read secret files → sources are masked → this gate). The built-in
regex set ALWAYS runs; gitleaks (GITLEAKS_BIN, else PATH) adds hits when it runs. Both see DECODED
content: every JSON string value and key, and the whole text of .md/.log. A Hit never carries the
value it found. JSON is parsed and re-dumped, never byte-patched; any other file type fails closed.
gitleaks status follows the report-based rule: rc≠0 or no readable report → unknown."""

from __future__ import annotations

import bisect
import dataclasses
import json
import os
import re
import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from .models import ToolStatus

TEXT_SUFFIXES = {".md", ".log"}
JSON_SUFFIXES = {".json", ".sarif"}
JSONL_SUFFIXES = {".jsonl"}
IGNORED_NAMES = {
    ".gitignore"
}  # the self-ignoring marker written by stamp.ensure_self_ignoring
GITLEAKS_TIMEOUT_S = 300
_NOT_REDACTED = r"(?!\[REDACTED:)"

# (rule, pattern). A named group `secret` narrows the redacted span to the value; otherwise the whole
# match is redacted. The `(?!\[REDACTED:)` guards keep redaction idempotent.
PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("aws-access-key", re.compile(r"A(?:KIA|SIA)[0-9A-Z]{16}")),
    ("github-token", re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}")),
    ("github-pat", re.compile(r"github_pat_[A-Za-z0-9_]{22,}")),
    ("gitlab-token", re.compile(r"glpat-[0-9A-Za-z_-]{20,}")),
    ("google-api-key", re.compile(r"AIza[0-9A-Za-z_-]{35}")),
    ("stripe-key", re.compile(r"(?:sk|rk)_live_[0-9A-Za-z]{24,}")),
    ("slack-token", re.compile(r"xox[abprs]-[A-Za-z0-9-]{10,}")),
    ("sk-key", re.compile(r"(?<![A-Za-z0-9])sk-(?:ant-)?[A-Za-z0-9_-]{20,}")),
    ("jwt", re.compile(r"eyJ[\w-]{10,}\.[\w-]{10,}\.[\w-]{10,}")),
    (
        "private-key-block",
        re.compile(
            r"-----BEGIN [A-Z ]*PRIVATE KEY(?: BLOCK)?-----.*?-----END [A-Z ]*PRIVATE KEY(?: BLOCK)?-----",
            re.S,
        ),
    ),
    (
        "url-credential",
        re.compile(
            r"[a-z][a-z0-9+.-]*://[^\s:/@]+:" + _NOT_REDACTED + r"(?P<secret>[^\s@/]+)@"
        ),
    ),
    (
        "generic-quoted",
        re.compile(
            r"""(?i)["']?(?:password|passwd|secret|api[_-]?key|token)["']?\s*[:=]\s*["']"""
            + _NOT_REDACTED
            + r"""(?P<secret>[^"'\s]{8,})["']"""
        ),
    ),
    (
        "generic-env",
        re.compile(
            r"""(?i)\b[A-Z0-9_]*(?:PASSWORD|SECRET|TOKEN|API_KEY)\s*[=:]\s*"""
            + _NOT_REDACTED
            + r"""(?P<secret>[^\s'"]{8,})"""
        ),
    ),
]


class UnsupportedFile(Exception):
    """A file the gate cannot decode — the gate refuses rather than pass it unscanned."""


@dataclasses.dataclass(frozen=True)
class Hit:
    """Where a secret is — never what it is. Lines are 1-based, columns 0-based end-exclusive,
    both relative to the scanned text: the file for .md/.log, the decoded string for JSON."""

    rule: str
    path: str
    start_line: int
    end_line: int
    start_col: int
    end_col: int
    # Location of the string inside a JSON document: list items as /<index>, object members as
    # /@<position> — never the key text, since a key can itself be the secret. .jsonl prefixes the
    # 1-based line number.
    pointer: str | None = None
    is_key: bool = False


@dataclasses.dataclass(frozen=True)
class ScanResult:
    hits: list[Hit]
    tool_status: ToolStatus


@dataclasses.dataclass(frozen=True)
class _Text:
    path: str
    text: str
    pointer: str | None = None
    is_key: bool = False


# --- spans ---------------------------------------------------------------------------------------


def _line_starts(text: str) -> list[int]:
    return [0] + [i + 1 for i, ch in enumerate(text) if ch == "\n"]


def _to_offset(starts: list[int], line: int, col: int) -> int:
    return starts[line - 1] + col


def _to_line_col(starts: list[int], offset: int) -> tuple[int, int]:
    line = bisect.bisect_right(starts, offset)
    return line, offset - starts[line - 1]


def _regex_spans(text: str) -> list[tuple[str, int, int]]:
    spans = []
    for rule, pattern in PATTERNS:
        for m in pattern.finditer(text):
            group = "secret" if "secret" in pattern.groupindex else 0
            spans.append((rule, m.start(group), m.end(group)))
    return spans


def _apply(text: str, spans: list[tuple[str, int, int]]) -> tuple[str, int]:
    """Replace merged spans with [REDACTED:<rule>]; returns (text, number of spans replaced)."""
    merged: list[list[Any]] = []
    for rule, start, end in sorted(spans, key=lambda s: (s[1], -s[2])):
        if merged and start < merged[-1][2]:
            merged[-1][2] = max(merged[-1][2], end)
        else:
            merged.append([rule, start, end])
    for rule, start, end in reversed(merged):
        text = text[:start] + f"[REDACTED:{rule}]" + text[end:]
    return text, len(merged)


def redact_text(text: str) -> str:
    """Regex-only redaction of one string (used for finding anchors before hashing)."""
    return _apply(text, _regex_spans(text))[0]


# --- decoding --------------------------------------------------------------------------------------


def _walk(node: Any, pointer: str) -> Iterator[tuple[str, str, bool]]:
    if isinstance(node, str):
        yield pointer, node, False
    elif isinstance(node, dict):
        for pos, (key, value) in enumerate(node.items()):
            child = f"{pointer}/@{pos}"
            yield child, key, True
            yield from _walk(value, child)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from _walk(value, f"{pointer}/{i}")


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise UnsupportedFile(
            f"{path}: not valid JSON ({exc.__class__.__name__})"
        ) from exc


def _load_jsonl(path: Path) -> list[Any]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        return [json.loads(line) if line.strip() else None for line in lines]
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise UnsupportedFile(
            f"{path}: not valid JSON Lines ({exc.__class__.__name__})"
        ) from exc


def _files(root: Path) -> list[Path]:
    out = []
    for p in sorted(root.rglob("*")):
        if p.is_symlink():
            raise UnsupportedFile(f"{p}: symlink in report dir")
        if not p.is_file() or p.name in IGNORED_NAMES:
            continue
        if p.suffix not in TEXT_SUFFIXES | JSON_SUFFIXES | JSONL_SUFFIXES:
            raise UnsupportedFile(
                f"{p}: unsupported file type {p.suffix or '(none)'}; the secret gate fails closed"
            )
        out.append(p)
    return out


def _texts(root: Path) -> list[_Text]:
    out = []
    for p in _files(root):
        rel = str(p)
        if p.suffix in TEXT_SUFFIXES:
            try:
                out.append(_Text(rel, p.read_text(encoding="utf-8")))
            except UnicodeDecodeError as exc:
                raise UnsupportedFile(f"{p}: not UTF-8 text") from exc
        elif p.suffix in JSON_SUFFIXES:
            out.extend(_Text(rel, s, ptr, k) for ptr, s, k in _walk(_load_json(p), ""))
        else:
            for n, doc in enumerate(_load_jsonl(p), 1):
                out.extend(
                    _Text(rel, s, f"{n}{ptr}", k) for ptr, s, k in _walk(doc, "")
                )
    return out


# --- scanning ----------------------------------------------------------------------------------------


def _hits_for(t: _Text, spans: list[tuple[str, int, int]]) -> list[Hit]:
    starts = _line_starts(t.text)
    hits = []
    for rule, start, end in spans:
        sl, sc = _to_line_col(starts, start)
        el, ec = _to_line_col(starts, end)
        hits.append(Hit(rule, t.path, sl, el, sc, ec, t.pointer, t.is_key))
    return hits


def _gitleaks_bin() -> str | None:
    configured = os.environ.get("GITLEAKS_BIN")
    candidate = configured if configured is not None else shutil.which("gitleaks")
    return (
        candidate
        if candidate and os.path.isfile(candidate) and os.access(candidate, os.X_OK)
        else None
    )


def _widen(line: str, start: int, end: int) -> tuple[int, int]:
    """gitleaks 8.18 columns are off by one; grow the span to the enclosing non-whitespace run."""
    start, end = max(0, min(start, len(line))), max(0, min(end, len(line)))
    if end <= start:
        return 0, len(line)  # unknown span → blank the whole line
    while start > 0 and not line[start - 1].isspace():
        start -= 1
    while end < len(line) and not line[end].isspace():
        end += 1
    return start, end


def _gitleaks(texts: list[_Text]) -> tuple[list[Hit], ToolStatus]:
    binary = _gitleaks_bin()
    if binary is None:
        return [], ToolStatus.ABSENT
    with (
        tempfile.TemporaryDirectory(prefix="aa-ma-gl-src-") as src,
        tempfile.TemporaryDirectory(prefix="aa-ma-gl-rep-") as rep,
    ):
        for i, t in enumerate(texts):
            Path(src, f"{i}.txt").write_text(t.text, encoding="utf-8")
        report = Path(rep, "report.json")
        argv = [
            binary,
            "detect",
            "--no-git",
            "--redact",
            "-s",
            src,
            "-f",
            "json",
            "-r",
            str(report),
            "--exit-code",
            "0",
        ]
        try:
            proc = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                timeout=GITLEAKS_TIMEOUT_S,
                check=False,
            )
            leaks = (
                json.loads(report.read_text(encoding="utf-8"))
                if proc.returncode == 0
                else None
            )
        except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
            leaks = None
    if not isinstance(leaks, list):
        return [], ToolStatus.UNKNOWN
    hits = []
    for leak in leaks:
        try:
            t = texts[int(Path(leak["File"]).stem)]
            lines = t.text.split("\n")
            sl, el = int(leak["StartLine"]), int(leak["EndLine"])
            first, last = lines[sl - 1], lines[el - 1]
            if sl == el:
                sc, ec = _widen(
                    first, int(leak["StartColumn"]) - 2, int(leak["EndColumn"]) - 1
                )
            else:
                sc, _ = _widen(first, int(leak["StartColumn"]) - 2, len(first))
                _, ec = _widen(last, 0, int(leak["EndColumn"]) - 1)
        except (KeyError, ValueError, IndexError, TypeError):
            return [], ToolStatus.UNKNOWN  # a report we cannot map back is not a scan
        hits.append(
            Hit(
                str(leak.get("RuleID", "gitleaks")),
                t.path,
                sl,
                el,
                sc,
                ec,
                t.pointer,
                t.is_key,
            )
        )
    return hits, ToolStatus.RAN


def scan(root: Path) -> ScanResult:
    texts = _texts(Path(root))
    hits = [h for t in texts for h in _hits_for(t, _regex_spans(t.text))]
    extra, status = _gitleaks(texts)
    known = set(hits)
    hits.extend(h for h in extra if h not in known)
    return ScanResult(hits, status)


# --- redaction ----------------------------------------------------------------------------------------


def _redact_string(text: str, hits: list[Hit]) -> tuple[str, int]:
    starts = _line_starts(text)
    spans = [
        (
            h.rule,
            _to_offset(starts, h.start_line, h.start_col),
            _to_offset(starts, h.end_line, h.end_col),
        )
        for h in hits
    ]
    return _apply(text, spans)


def _redact_node(
    node: Any, pointer: str, by_ptr: dict[tuple[str, bool], list[Hit]]
) -> tuple[Any, int]:
    if isinstance(node, str):
        hits = by_ptr.get((pointer, False))
        return _redact_string(node, hits) if hits else (node, 0)
    count = 0
    if isinstance(node, list):
        out_list = []
        for i, value in enumerate(node):
            new, n = _redact_node(value, f"{pointer}/{i}", by_ptr)
            out_list.append(new)
            count += n
        return out_list, count
    if isinstance(node, dict):
        out: dict[str, Any] = {}
        for pos, (key, value) in enumerate(node.items()):
            child = f"{pointer}/@{pos}"
            new_value, n = _redact_node(value, child, by_ptr)
            new_key, m = (
                _redact_string(key, by_ptr[(child, True)])
                if (child, True) in by_ptr
                else (key, 0)
            )
            while new_key in out:
                new_key += "#"
            out[new_key] = new_value
            count += n + m
        return out, count
    return node, 0


def _index(hits: list[Hit]) -> dict[tuple[str, bool], list[Hit]]:
    by_ptr: dict[tuple[str, bool], list[Hit]] = {}
    for h in hits:
        by_ptr.setdefault((h.pointer or "", h.is_key), []).append(h)
    return by_ptr


def redact(root: Path, hits: list[Hit]) -> int:
    """Apply hits in place; returns the number of spans replaced. Files without hits are untouched."""
    by_file: dict[str, list[Hit]] = {}
    for h in hits:
        by_file.setdefault(h.path, []).append(h)
    total = 0
    for path_str, file_hits in by_file.items():
        path = Path(path_str)
        if Path(root).resolve() not in path.resolve().parents:
            raise UnsupportedFile(f"{path}: hit outside the report dir")
        if path.suffix in TEXT_SUFFIXES:
            text, n = _redact_string(path.read_text(encoding="utf-8"), file_hits)
            path.write_text(text, encoding="utf-8")
        elif path.suffix in JSON_SUFFIXES:
            doc, n = _redact_node(_load_json(path), "", _index(file_hits))
            path.write_text(
                json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
        elif path.suffix in JSONL_SUFFIXES:
            n, lines = 0, []
            for i, doc in enumerate(_load_jsonl(path), 1):
                line_hits = [
                    h for h in file_hits if (h.pointer or "").split("/", 1)[0] == str(i)
                ]
                if doc is None:
                    lines.append("")
                    continue
                if line_hits:
                    stripped = [
                        dataclasses.replace(h, pointer=(h.pointer or "")[len(str(i)) :])
                        for h in line_hits
                    ]
                    doc, m = _redact_node(doc, "", _index(stripped))
                    if m and isinstance(doc, dict) and "redacted" in doc:
                        doc["redacted"] = True
                    n += m
                lines.append(json.dumps(doc, ensure_ascii=False))
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        else:
            raise UnsupportedFile(f"{path}: unsupported file type")
        total += n
    return total
