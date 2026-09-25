"""ast-grep subprocess wrapper (M1 Task 1.4).

Batches file parsing per language via a single ``sg scan`` invocation with a
language-specific YAML rule file. Produces :class:`ParseResult` shapes
compatible with the stdlib Python parser (Task 1.3) so the indexer driver
(Task 1.5) consumes a uniform interface.

Rule files live in ``packages/codemem-mcp/src/codemem/parser/rules/``; each
declares patterns matching the five acceptance-criteria kinds
(function / class / method / import / call) for one language.
Cross-file edge resolution for imports and non-local calls is Task 1.6.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from .python_ast import CallEdge, ParseResult, Symbol


__all__ = [
    "SUPPORTED_LANGUAGES",
    "language_from_path",
    "parse_sg_output",
    "extract_with_ast_grep",
]


# ast-grep language name → file extensions it claims. TypeScript and Tsx are
# deliberately separate (the AC calls out ``languageGlobs`` for ``.ts`` ↔
# ``.tsx`` — ast-grep treats them as distinct languages).
SUPPORTED_LANGUAGES: dict[str, set[str]] = {
    "TypeScript": {".ts"},
    "Tsx":        {".tsx"},
    "JavaScript": {".js", ".jsx", ".mjs", ".cjs"},
    "Go":         {".go"},
    "Rust":       {".rs"},
    "Java":       {".java"},
    "Ruby":       {".rb"},
    "Bash":       {".sh", ".bash"},
}

# Language → rule-file basename under rules/. One file per language keeps the
# batched sg invocation per-language simple.
_RULE_FILE_BY_LANG: dict[str, str] = {
    "TypeScript": "typescript.yml",
    "Tsx":        "tsx.yml",
    "JavaScript": "javascript.yml",
    "Go":         "go.yml",
    "Rust":       "rust.yml",
    "Java":       "java.yml",
    "Ruby":       "ruby.yml",
    "Bash":       "bash.yml",
}

# Rule-id suffix → the Symbol.kind we emit. Rules are named
# ``<langprefix>-function-def`` etc. (e.g. ``ts-function-def``).
_KIND_BY_RULE_SUFFIX: dict[str, str] = {
    "-function-def":  "function",
    "-class-def":     "class",
    "-interface-def": "class",       # Java/TS interfaces are containers for methods
    "-struct-def":    "class",       # Go/Rust structs — containers for methods
    "-module-def":    "class",       # Ruby module — container
    "-type-alias":    "class",       # TS type alias — treated as type for SCIP marker
    "-method-def":    "method",
    # imports + calls are edges — handled separately, no Symbol emission.
}

# Rule suffixes whose matches define a CONTAINER (eligible parent for methods).
_CONTAINER_SUFFIXES: frozenset[str] = frozenset({
    "-class-def", "-interface-def", "-struct-def", "-module-def",
})


def language_from_path(path: Path) -> str | None:
    """Return the ast-grep language name for ``path``, or ``None`` if unsupported."""
    ext = path.suffix.lower()
    for lang, exts in SUPPORTED_LANGUAGES.items():
        if ext in exts:
            return lang
    return None


# ---------------------------------------------------------------------
# JSON stream parser
# ---------------------------------------------------------------------

@dataclass
class _SgMatch:
    file: Path
    rule_id: str
    name: str | None
    line: int      # 1-indexed
    end_line: int  # 1-indexed
    text: str
    callee: str | None = None  # $CALLEE of a ``*-call`` rule (diagram-generation M9)
    col: int = 0  # 0-indexed start column; with end_col, places a call inside one of
    end_col: int = 0  # several functions sharing a line (minified code)


def parse_sg_output(stream: str) -> list[_SgMatch]:
    """Parse ``sg scan --json=stream`` output into :class:`_SgMatch` records.

    Blank lines and invalid JSON are silently ignored; that's the expected
    tolerance for a subprocess stream (partial writes, preamble warnings).
    """
    matches: list[_SgMatch] = []
    for raw in stream.splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            j = json.loads(raw)
        except json.JSONDecodeError:
            continue

        name: str | None = None
        meta = j.get("metaVariables", {}).get("single", {})
        for key in ("NAME", "name"):
            if key in meta:
                name = meta[key].get("text")
                break
        callee = meta.get("CALLEE", {}).get("text")

        rng = j.get("range", {})
        start = rng.get("start", {}).get("line", 0)
        end = rng.get("end", {}).get("line", 0)

        matches.append(
            _SgMatch(
                file=Path(j.get("file", "")),
                rule_id=j.get("ruleId", ""),
                name=name,
                line=start + 1,
                end_line=end + 1,
                text=j.get("text", ""),
                callee=callee,
                col=rng.get("start", {}).get("column", 0),
                end_col=rng.get("end", {}).get("column", 0),
            )
        )
    return matches


# ---------------------------------------------------------------------
# Subprocess invocation
# ---------------------------------------------------------------------

def _rules_dir() -> Path:
    return Path(__file__).parent / "rules"


def _rule_file_for_language(language: str) -> Path | None:
    basename = _RULE_FILE_BY_LANG.get(language)
    if not basename:
        return None
    path = _rules_dir() / basename
    return path if path.exists() else None


def _invoke_sg(rule_file: Path, files: list[Path], *, sg_bin: str) -> str:
    """Invoke ``sg scan`` for a batch of same-language files and return stdout.

    Non-zero exit codes from sg (it returns non-zero when matches are found
    at severity ``error`` — we use ``hint``, so this shouldn't fire) are
    tolerated: we use whatever stdout we got. Stderr is deliberately silenced
    to keep the wrapper quiet during indexing; failures surface as empty
    ParseResults.
    """
    cmd = [
        sg_bin, "scan",
        "-r", str(rule_file),
        "--json=stream",
        "--include-metadata",
    ]
    cmd.extend(str(f) for f in files)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout


# ---------------------------------------------------------------------
# ParseResult construction
# ---------------------------------------------------------------------

def _rule_suffix(rule_id: str) -> str | None:
    for suffix in _KIND_BY_RULE_SUFFIX:
        if rule_id.endswith(suffix):
            return suffix
    return None


def _file_rel_to_package(file: Path, repo_root: Path, package: str) -> str:
    """Compute ``file`` relative to the ``<package>`` segment of the SCIP ID."""
    repo_root_abs = repo_root.resolve()
    file_abs = file.resolve()
    try:
        rel_to_repo = file_abs.relative_to(repo_root_abs)
    except ValueError:
        # File outside repo — use name only; Task 1.5 driver is expected to
        # reject this case upstream via path sanitization.
        return file.name

    pkg_path = Path(package)
    try:
        return str(rel_to_repo.relative_to(pkg_path))
    except ValueError:
        return str(rel_to_repo)


def _build_parse_result(
    file: Path,
    matches: list[_SgMatch],
    *,
    package: str,
    repo_root: Path,
) -> ParseResult:
    file_rel = _file_rel_to_package(file, repo_root, package)

    # Sort by (start, end) — containers precede their members in source order.
    matches_sorted = sorted(matches, key=lambda m: (m.line, m.end_line))

    # containers: (name, start_line, end_line, scip_id) — used to infer the
    # enclosing parent for methods via line-range containment.
    containers: list[tuple[str, int, int, str]] = []
    # callables: ((line, col), (end_line, end_col), scip_id) — the enclosing-function lookup.
    callables: list[tuple[tuple[int, int], tuple[int, int], str]] = []
    symbols: list[Symbol] = []

    def _enclosing_container(m: _SgMatch) -> tuple[str | None, str | None]:
        parent_name: str | None = None
        parent_scip: str | None = None
        for pname, pstart, pend, psid in containers:
            if pstart < m.line and m.end_line <= pend:
                # Innermost container wins — later entries override earlier.
                parent_name, parent_scip = pname, psid
        return parent_name, parent_scip

    for m in matches_sorted:
        suffix = _rule_suffix(m.rule_id)
        if suffix is None or not m.name:
            continue

        if suffix in _CONTAINER_SUFFIXES or suffix == "-type-alias":
            parent_name, parent_scip = _enclosing_container(m)
            symbol_path = f"{parent_name}#{m.name}" if parent_name else m.name
            scip_id = f"codemem {package} #{file_rel}#{symbol_path}"
            symbols.append(
                Symbol(
                    scip_id=scip_id,
                    name=m.name,
                    kind=_KIND_BY_RULE_SUFFIX[suffix],
                    line=m.line,
                    signature=None,
                    signature_hash=None,
                    docstring=None,
                    parent_scip_id=parent_scip,
                )
            )
            # Only register actual containers as parent candidates — type
            # aliases are leaves (no methods), don't add them.
            if suffix in _CONTAINER_SUFFIXES:
                containers.append((m.name, m.line, m.end_line, scip_id))

        elif suffix == "-method-def":
            parent_name, parent_scip = _enclosing_container(m)
            if parent_name is None:
                # Orphan method (e.g. object-literal shorthand) — v1 skips.
                continue
            symbol_path = f"{parent_name}.{m.name}"
            scip_id = f"codemem {package} .{file_rel}#{symbol_path}"
            callables.append(((m.line, m.col), (m.end_line, m.end_col), scip_id))
            symbols.append(
                Symbol(
                    scip_id=scip_id,
                    name=m.name,
                    kind="method",
                    line=m.line,
                    signature=None,
                    signature_hash=None,
                    docstring=None,
                    parent_scip_id=parent_scip,
                )
            )

        elif suffix == "-function-def":
            scip_id = f"codemem {package} /{file_rel}#{m.name}"
            callables.append(((m.line, m.col), (m.end_line, m.end_col), scip_id))
            symbols.append(
                Symbol(
                    scip_id=scip_id,
                    name=m.name,
                    kind="function",
                    line=m.line,
                    signature=None,
                    signature_hash=None,
                    docstring=None,
                    parent_scip_id=None,
                )
            )

    # No intra-file edges: ast-grep carries no function-body scope, so a same-file
    # callee cannot be bound by name the way python_ast does. Calls are emitted
    # unresolved, keyed on the innermost enclosing function (diagram-generation M9).
    edges: list[CallEdge] = []
    # One sorted sweep: syntax nests, so the innermost open callable is the stack top.
    # Ties at a start position put callables before calls, outer callables first.
    events = [(start, 0, end, sid) for start, end, sid in callables]
    events += [((m.line, m.col), 1, (m.end_line, m.end_col), c) for m in matches if (c := _callee(m))]
    events.sort(key=lambda ev: (ev[0], ev[1], (-ev[2][0], -ev[2][1])))
    unresolved: dict[tuple[str, str], CallEdge] = {}
    open_: list[tuple[tuple[int, int], str]] = []  # (end, scip_id)
    for start, is_call, end, value in events:
        while open_ and open_[-1][0] <= start:
            open_.pop()
        if not is_call:
            open_.append((end, value))
        elif open_:  # else a top-level call: no symbol to hang it on, as in python_ast
            src = open_[-1][1]
            unresolved.setdefault((src, value), CallEdge(src, None, value, "call"))

    return ParseResult(symbols=symbols, edges=edges, unresolved_edges=list(unresolved.values()))


def _callee(m: _SgMatch) -> str | None:
    """``fs.readFileSync`` from a ``*-call`` match; ``None`` for anything else.

    A callee chained through a call (``fetch(url).then``) is dropped, as in
    python_ast: its receiver is ambiguous. The inner call is its own match.
    """
    if not m.rule_id.endswith("-call") or not m.callee or "(" in m.callee:
        return None
    return "".join(m.callee.split())


# ---------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------

Invoker = Callable[[Path, list[Path]], str]


def extract_with_ast_grep(
    files: Iterable[Path],
    *,
    package: str,
    repo_root: Path,
    sg_bin: str = "sg",
    _invoker: Callable[..., str] | None = None,
) -> dict[Path, ParseResult]:
    """Parse ``files`` via ast-grep, batched per language.

    Returns a mapping from each file to its :class:`ParseResult`. Files whose
    language is unsupported (e.g. ``.py`` — handled by the stdlib parser —
    or ``.md``) are silently skipped.

    ``_invoker`` is an injection point for tests so subprocess behaviour can
    be mocked deterministically.
    """
    invoker = _invoker or _invoke_sg

    files_by_lang: dict[str, list[Path]] = {}
    files_list = list(files)
    for f in files_list:
        lang = language_from_path(f)
        if lang is None:
            continue
        files_by_lang.setdefault(lang, []).append(f)

    all_matches: list[_SgMatch] = []
    for lang, lang_files in files_by_lang.items():
        rule = _rule_file_for_language(lang)
        if rule is None:
            continue
        stream = invoker(rule, lang_files, sg_bin=sg_bin)
        all_matches.extend(parse_sg_output(stream))

    matches_by_file: dict[Path, list[_SgMatch]] = {}
    for m in all_matches:
        matches_by_file.setdefault(m.file, []).append(m)

    results: dict[Path, ParseResult] = {}
    for f in files_list:
        if language_from_path(f) is None:
            continue
        results[f] = _build_parse_result(
            f,
            matches_by_file.get(f.resolve(), matches_by_file.get(f, [])),
            package=package,
            repo_root=repo_root,
        )
    return results
