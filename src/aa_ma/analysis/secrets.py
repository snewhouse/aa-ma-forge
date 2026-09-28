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
import subprocess  # nosec B404 — gitleaks runs from an argv list, never a shell
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from .models import ToolStatus
from .stamp import SELF_IGNORE_NAME, SELF_IGNORE_TEXT, find_binary

TEXT_SUFFIXES = {".md", ".log"}
JSON_SUFFIXES = {".json", ".sarif"}
JSONL_SUFFIXES = {".jsonl"}
GITLEAKS_TIMEOUT_S = 300
# gitleaks 8.18 columns (live-probed 2026-09-28): a token at 0-based index i, length L is reported
# as StartColumn i+2, EndColumn i+L+1 — one lower on a file's first line. _widen absorbs either.
GL_START_ADJ, GL_END_ADJ = 2, 1
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


class GateError(Exception):
    """The gate cannot vouch for the report dir — callers must treat the output as not cleared."""


class UnsupportedFile(GateError):
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
    # > 0: a synthetic `"key": "value"` context text for the string value at `pointer`, which starts
    # at this offset — so rules that need the key beside the value (generic-quoted, gitleaks'
    # generic-api-key) see it. Hits are mapped back onto the value; the key is never redacted.
    value_offset: int = 0

    def value(self) -> _Text:
        return _Text(self.path, self.text[self.value_offset : -1], self.pointer)


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


def secret_lines(text: str) -> list[tuple[str, int]]:
    """(rule, 1-based line) per built-in regex hit, in PATTERNS order — for repo source, which is
    only reported on, never rewritten, so no span or value is kept."""
    starts = _line_starts(text)
    return [
        (rule, _to_line_col(starts, start)[0]) for rule, start, _ in _regex_spans(text)
    ]


def redact_text(text: str) -> str:
    """Regex-only redaction of one string (used for finding anchors before hashing)."""
    return _apply(text, _regex_spans(text))[0]


# --- decoding --------------------------------------------------------------------------------------
# One place builds each location format, for both the scan and the redact walk.


def _member_ptr(pointer: str, pos: int) -> str:
    return f"{pointer}/@{pos}"


def _item_ptr(pointer: str, index: int) -> str:
    return f"{pointer}/{index}"


def _line_ptr(line_no: int, pointer: str = "") -> str:
    return f"{line_no}{pointer}"


def _split_line_ptr(pointer: str) -> tuple[str, str]:
    head, sep, rest = pointer.partition("/")
    return head, sep + rest


def _walk(node: Any, pointer: str) -> Iterator[tuple[str, str, bool]]:
    if isinstance(node, str):
        yield pointer, node, False
    elif isinstance(node, dict):
        for pos, (key, value) in enumerate(node.items()):
            child = _member_ptr(pointer, pos)
            yield child, key, True
            yield from _walk(value, child)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from _walk(value, _item_ptr(pointer, i))


def _contexts(node: Any, pointer: str) -> Iterator[tuple[str, str, int]]:
    """(value pointer, `"key": "value"` text, value offset) for every string-valued object member.
    The offset is the prefix length, never searched for — a key may itself contain '": "'."""
    if isinstance(node, dict):
        for pos, (key, value) in enumerate(node.items()):
            child = _member_ptr(pointer, pos)
            prefix = f'"{key}": "'
            if isinstance(value, str):
                yield child, f'{prefix}{value}"', len(prefix)
            elif isinstance(
                value, list
            ):  # {"api_key": ["..."]}: each string item gets its key too
                for i, item in enumerate(value):
                    if isinstance(item, str):
                        yield _item_ptr(child, i), f'{prefix}{item}"', len(prefix)
            yield from _contexts(value, child)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from _contexts(value, _item_ptr(pointer, i))


def _doc_texts(rel: str, doc: Any, prefix: str) -> list[_Text]:
    out = [_Text(rel, s, prefix + ptr, k) for ptr, s, k in _walk(doc, "")]
    out += [
        _Text(rel, text, prefix + ptr, False, off)
        for ptr, text, off in _contexts(doc, "")
    ]
    return out


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    keys = [k for k, _ in pairs]
    if len(set(keys)) != len(keys):
        # json.loads would keep only the last value; the earlier ones would never be scanned.
        raise ValueError("duplicate object key")
    return dict(pairs)


def _decode(path: Path, text: str, kind: str) -> Any:
    try:
        doc = json.loads(text, object_pairs_hook=_no_duplicate_keys)
        # Walk once here so the later scan and redact walks cannot fail: a lone surrogate cannot be
        # written back or handed to gitleaks, and nesting deeper than the recursion limit is refused.
        for _, value, _ in _walk(doc, ""):
            value.encode("utf-8")
    except (
        json.JSONDecodeError,
        ValueError,
        UnicodeEncodeError,
        RecursionError,
    ) as exc:
        raise UnsupportedFile(
            f"{path}: not valid {kind} ({exc.__class__.__name__})"
        ) from exc
    return doc


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise UnsupportedFile(f"{path}: not UTF-8 text") from exc


def _load_json(path: Path) -> Any:
    return _decode(path, _read(path), "JSON")


def _load_jsonl(path: Path) -> list[Any]:
    return [
        _decode(path, line, "JSON Lines") if line.strip() else None
        for line in _read(path).split("\n")
    ]


def _files(root: Path) -> list[Path]:
    out = []
    for p in sorted(root.rglob("*")):
        rel = str(p.relative_to(root))
        if _regex_spans(rel) or _regex_spans(rel.replace(os.sep, "")):
            # Never echo the name: it is the thing that matched.
            raise UnsupportedFile(
                "a file or directory name in the report dir matches a secret pattern"
            )
        if p.is_symlink():
            raise UnsupportedFile(f"{p}: symlink in report dir")
        if p.is_dir():
            continue
        if not p.is_file():
            raise UnsupportedFile(f"{p}: not a regular file")
        if p.stat().st_nlink != 1:
            raise UnsupportedFile(
                f"{p}: hard-linked file; redaction would rewrite its other names"
            )
        if p == root / SELF_IGNORE_NAME and p.read_bytes() == SELF_IGNORE_TEXT.encode():
            continue
        if p.suffix not in TEXT_SUFFIXES | JSON_SUFFIXES | JSONL_SUFFIXES:
            raise UnsupportedFile(
                f"{p}: unsupported file type; the secret gate fails closed"
            )
        out.append(p)
    return out


def _texts(root: Path) -> list[_Text]:
    out = []
    for p in _files(root):
        rel = str(p)
        if p.suffix in TEXT_SUFFIXES:
            out.append(_Text(rel, _read(p)))
        elif p.suffix in JSON_SUFFIXES:
            out.extend(_doc_texts(rel, _load_json(p), ""))
        else:
            for n, doc in enumerate(_load_jsonl(p), 1):
                out.extend(_doc_texts(rel, doc, _line_ptr(n)))
    return out


# --- scanning ----------------------------------------------------------------------------------------


def _hits_for(t: _Text, spans: list[tuple[str, int, int]]) -> list[Hit]:
    if not spans:
        return []
    if t.value_offset:
        # A context text: clip spans onto the value, then shift into the value's coordinates.
        lo, hi = t.value_offset, len(t.text) - 1
        clipped = [
            (r, max(s, lo) - lo, min(e, hi) - lo)
            for r, s, e in spans
            if min(e, hi) > max(s, lo)
        ]
        return _hits_for(t.value(), clipped)
    starts = _line_starts(t.text)
    hits = []
    for rule, start, end in spans:
        sl, sc = _to_line_col(starts, start)
        el, ec = _to_line_col(starts, end)
        hits.append(Hit(rule, t.path, sl, el, sc, ec, t.pointer, t.is_key))
    return hits


def _whole(rule: str, t: _Text) -> Hit:
    lines = t.text.split("\n")
    return Hit(rule, t.path, 1, len(lines), 0, len(lines[-1]), t.pointer, t.is_key)


def _gitleaks_bin() -> str | None:
    return find_binary("gitleaks")


def _widen(line: str, start: int, end: int) -> tuple[int, int]:
    """Clamp, trim edge whitespace (an off-by-one start may sit on the gap before a token), then grow
    the span to the enclosing non-whitespace run. An empty span blanks the whole line."""
    start, end = max(0, min(start, len(line))), max(0, min(end, len(line)))
    while start < end and line[start].isspace():
        start += 1
    while end > start and line[end - 1].isspace():
        end -= 1
    if end <= start:
        return 0, len(line)
    while start > 0 and not line[start - 1].isspace():
        start -= 1
    while end < len(line) and not line[end].isspace():
        end += 1
    return start, end


def gitleaks_args(source: str, report: Path) -> list[str]:
    """The one gitleaks 8.x invocation (measure uses it too): redacted JSON report, exit 0."""
    return [
        "detect",
        "--no-git",
        "--redact",
        "-s",
        source,
        "-f",
        "json",
        "-r",
        str(report),
        "--exit-code",
        "0",
    ]


def _run_gitleaks(binary: str, texts: list[_Text]) -> list[Any] | None:
    with (
        tempfile.TemporaryDirectory(prefix="aa-ma-gl-src-") as src,
        tempfile.TemporaryDirectory(prefix="aa-ma-gl-rep-") as rep,
    ):
        for i, t in enumerate(texts):
            Path(src, f"{i}.txt").write_text(t.text, encoding="utf-8")
        report = Path(rep, "report.json")
        argv = [binary, *gitleaks_args(src, report)]
        try:
            proc = subprocess.run(  # nosec B603 — binary from GITLEAKS_BIN/PATH, args are our temp paths
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
        except (
            OSError,
            subprocess.TimeoutExpired,
            ValueError,
        ):  # ValueError: bad JSON / not UTF-8
            return None
    return leaks if isinstance(leaks, list) else None


def _leak_hit(leak: Any, texts: list[_Text]) -> tuple[int, Hit]:
    try:
        index = int(Path(leak["File"]).stem)
        if not 0 <= index < len(texts):
            raise IndexError(index)
        t = texts[index]
    except (KeyError, ValueError, IndexError, TypeError) as exc:
        raise GateError(
            "gitleaks reported a finding that maps to no scanned text; refusing to clear"
        ) from exc
    rule = str(leak.get("RuleID", "gitleaks"))
    if t.value_offset:
        # A context-text hit: blank the value, keep the key.
        return index, _whole(rule, t.value())
    try:
        lines = t.text.split("\n")
        sl, el = int(leak["StartLine"]), int(leak["EndLine"])
        if not 1 <= sl <= el <= len(lines):
            raise IndexError(sl)
        first, last = lines[sl - 1], lines[el - 1]
        start, end = (
            int(leak["StartColumn"]) - GL_START_ADJ,
            int(leak["EndColumn"]) - GL_END_ADJ,
        )
        if sl == el:
            sc, ec = _widen(first, start, end)
        else:
            sc, _ = _widen(first, start, len(first))
            _, ec = _widen(last, 0, end)
    except (KeyError, ValueError, IndexError, TypeError):
        return index, _whole(rule, t)  # known text, unknown span → blank the whole text
    return index, Hit(rule, t.path, sl, el, sc, ec, t.pointer, t.is_key)


def _gitleaks(texts: list[_Text]) -> tuple[list[tuple[int, Hit]], ToolStatus]:
    """(index into texts, hit) pairs — the index, not the location, says which text a hit is on."""
    binary = _gitleaks_bin()
    if binary is None:
        return [], ToolStatus.ABSENT
    leaks = _run_gitleaks(binary, texts)
    if leaks is None:
        return [], ToolStatus.UNKNOWN
    return [_leak_hit(leak, texts) for leak in leaks], ToolStatus.RAN


def _move(h: Hit, t: _Text) -> Hit:
    """The same span on another occurrence of the same text."""
    return dataclasses.replace(
        h, path=t.path, pointer=t.pointer, is_key=t.is_key and not t.value_offset
    )


def _span_key(h: Hit) -> tuple[Any, ...]:
    return (
        h.path,
        h.pointer,
        h.is_key,
        h.start_line,
        h.end_line,
        h.start_col,
        h.end_col,
    )


def scan(root: Path) -> ScanResult:
    """Raises GateError (incl. UnsupportedFile) when the dir cannot be cleared."""
    # Scan each distinct text once (report keys and enum values repeat thousands of times), then
    # give every occurrence its own hit.
    groups: dict[tuple[str, int], list[_Text]] = {}
    for t in _texts(Path(root)):
        groups.setdefault((t.text, t.value_offset), []).append(t)
    occurrences = list(groups.values())
    found = [
        _move(h, t)
        for group in occurrences
        for h in _hits_for(group[0], _regex_spans(group[0].text))
        for t in group
    ]
    pairs, status = _gitleaks([group[0] for group in occurrences])
    found += [_move(h, t) for i, h in pairs for t in occurrences[i]]
    hits, seen = [], set()
    for h in found:
        if _span_key(h) not in seen:
            seen.add(_span_key(h))
            hits.append(h)
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
            new, n = _redact_node(value, _item_ptr(pointer, i), by_ptr)
            out_list.append(new)
            count += n
        return out_list, count
    if isinstance(node, dict):
        out: dict[str, Any] = {}
        for pos, (key, value) in enumerate(node.items()):
            child = _member_ptr(pointer, pos)
            new_value, n = _redact_node(value, child, by_ptr)
            key_hits = by_ptr.get((child, True))
            new_key, m = _redact_string(key, key_hits) if key_hits else (key, 0)
            while new_key in out:
                new_key += "#"
            out[new_key] = new_value
            count += n + m
        if count and isinstance(out.get("redacted"), bool):
            out["redacted"] = True  # a finding whose strings changed says so
        return out, count
    return node, 0


def _index(hits: list[Hit]) -> dict[tuple[str, bool], list[Hit]]:
    by_ptr: dict[tuple[str, bool], list[Hit]] = {}
    for h in hits:
        by_ptr.setdefault((h.pointer or "", h.is_key), []).append(h)
    return by_ptr


def _replace(path: Path, text: str) -> None:
    """Write beside the file and rename over it: the original is intact or fully replaced."""
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".aa-ma-redact-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.chmod(tmp, path.stat().st_mode & 0o7777)  # mkstemp creates 0600
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def _redact_jsonl(path: Path, file_hits: list[Hit]) -> tuple[str, int]:
    by_line: dict[str, list[Hit]] = {}
    for h in file_hits:
        line_no, rest = _split_line_ptr(h.pointer or "")
        by_line.setdefault(line_no, []).append(dataclasses.replace(h, pointer=rest))
    total, lines = 0, []
    for i, doc in enumerate(_load_jsonl(path), 1):
        if doc is None:
            lines.append("")
            continue
        line_hits = by_line.get(_line_ptr(i))
        if line_hits:
            doc, n = _redact_node(doc, "", _index(line_hits))
            total += n
        lines.append(json.dumps(doc, ensure_ascii=False))
    return "\n".join(
        lines
    ), total  # split("\n") kept the final "" — joining restores the framing


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
            text, n = _redact_string(_read(path), file_hits)
        elif path.suffix in JSON_SUFFIXES:
            doc, n = _redact_node(_load_json(path), "", _index(file_hits))
            text = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
        elif path.suffix in JSONL_SUFFIXES:
            text, n = _redact_jsonl(path, file_hits)
        else:
            raise UnsupportedFile(f"{path}: unsupported file type")
        _replace(path, text)
        total += n
    return total
