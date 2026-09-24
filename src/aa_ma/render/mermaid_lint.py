"""Structural lint for plan.md §13 Architecture View. Pure Python; mmdc optional (L-012)."""

from __future__ import annotations

import os
import re
import shutil
import sqlite3
import subprocess  # nosec B404 — optional mmdc render seam, never shell=True
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from aa_ma.grammar import (
    MILESTONE_RE,
    H2_RE,
    scan_fences,
    split_milestones,
    strip_fenced_blocks,
)
from aa_ma.plan_parsers import (
    parse_audit_profile,
    parse_critical_path,
    parse_diagram_waiver,
)
from aa_ma.render.graph import GraphStatus, call_edges, file_langs, import_edges, open_graph

# Allowlist by policy, not a mermaid inventory: the views a plan is expected to hold.
# A newer type (architecture-beta, mindmap, timeline...) is UNKNOWN_TYPE until added here
# deliberately — the point is that a typo'd first line never renders as a diagram.
KNOWN_TYPES: tuple[str, ...] = (
    "flowchart",
    "graph",
    "sequenceDiagram",
    "classDiagram",
    "stateDiagram-v2",
    "erDiagram",
    "C4Context",
    "C4Container",
    "C4Component",
)
# `custom` is deliberately excluded (context-log 2026-09-12): a custom milestone
# that dispatches code-reviewer via Audit-Run: declares its View voluntarily.
CODE_AUDIT_PROFILES: frozenset[str] = frozenset({"full", "code-only", "infra"})
PARSE_ERROR_SIGNATURES: tuple[str, ...] = ("Parse error on line", "UnknownDiagramError")

_SECTION_RE = re.compile(r"^## (?:13\.?[ \t]+)?Architecture View[ \t]*$", re.M)
_VIEW_RE = re.compile(r"^### (Component|Flow|Data/State) view[ \t]*$", re.M)
_FENCE_LINE_RE = re.compile(
    r"^[ \t]{0,3}(`{3,}|~{3,})[ \t]*([^`\s]*)"
)  # CommonMark opener/closer
_MAX_TOKEN = (
    256  # PATH_MAX-ish: _PATH_RE only sees a bounded token, so it cannot go quadratic
)
# exemption survives shape punctuation: [("x (new)")]
_NEW_RE = re.compile(r"\(new\)\W*$")
# lines a fence may open with before the diagram type: %% directives, --- front-matter
_DIRECTIVE_RE = re.compile(r"^%%[^\n]*\n", re.M)
_FRONT_MATTER_RE = re.compile(r"\A---[ \t]*\n.*?^---[ \t]*\n", re.M | re.S)
# Labels scanned: the `[...]` family only (incl. shapes `[(...)]`, `[[...]]`, `[/.../]`);
# `(...)`, `{...}` and `|edge|` labels are not path claims.
_PATH_RE = re.compile(
    r"[A-Za-z0-9_./-]+/[A-Za-z0-9_.-]+\.(?:md|py|sh|yaml|yml|toml|json|bats)"
)


@dataclass(frozen=True)
class Finding:
    code: str
    line: int
    message: str


@dataclass(frozen=True)
class LintReport:
    findings: tuple[Finding, ...]
    render_status: str  # PASS | FAIL | UNKNOWN
    unknowns: tuple[Finding, ...] = ()  # unevaluable sigil claims (code UNKNOWN); never set the exit


# Opt-in edge claims (diagram-generation M8, map Ticket 5). An edge is checked ONLY when its
# label carries a reserved sigil; unlabelled and prose-labelled edges never are.
_EDGE_READERS = {"@import": import_edges, "@call": call_edges}  # graph-backed sigils
_PLUGIN_SIGILS = ("@skill", "@command", "@agent", "@hook")  # UNKNOWN until the index holds them (M13)
SIGILS: tuple[str, ...] = (*_EDGE_READERS, *_PLUGIN_SIGILS)
_PLUGIN_REASON = "plugin-surface edges are not in the codemem index"
_ID = r"[A-Za-z_][\w-]*"
_DECL = r"(?:[ \t]*\[[^\]\n]*\]+)?"  # inline `[...]`; ONE `[` opens it (`\[+` was quadratic)
# One whole line: `A["x"] -->|"@import"| B["y"]`. Anything else carrying a sigil is UNKNOWN.
_EDGE_RE = re.compile(
    rf'^[ \t]*({_ID}){_DECL}[ \t]*(?:-->|-\.->|==>)[ \t]*\|("[^"\n]*"|[^|\n]*)\|[ \t]*({_ID}){_DECL}[ \t]*;?[ \t]*$'
)
_SIGIL_SLOT_RE = re.compile(r'(?:\||--|==)[ \t]*"?@[\w-]')  # an `@` where an edge label sits
_ID_TAIL_RE = re.compile(rf"({_ID})[ \t]*$")


@dataclass(frozen=True)
class _Graph:
    status: GraphStatus
    reason: str | None
    edges: dict[str, set[tuple[str, str]]]  # sigil -> (src_path, dst_path)
    langs: dict[str, str]  # indexed path -> language
    edge_langs: dict[str, set[str]]  # sigil -> languages with at least one such edge

    def models(self, sigil: str, path: str) -> bool:
        """Can the graph hold this sigil's edge at ``path``? Data, not a language list: an
        indexed file whose language has at least one such edge. codemem indexes `.sh` for
        symbols but persists imports for Python only, so an `@import` on a shell script is
        UNKNOWN, while an isolated Python file is still evaluable (and PHANTOM if absent)."""
        return self.langs.get(path) in self.edge_langs[sigil]


def _load_graph(repo_root: Path) -> _Graph:
    h = open_graph(repo_root)
    empty = {s: set() for s in _EDGE_READERS}
    try:
        if h.status is not GraphStatus.OK:  # its claims are UNKNOWN anyway: read nothing
            return _Graph(h.status, h.reason, empty, {}, dict(empty))
        edges = {s: read(h) for s, read in _EDGE_READERS.items()}
        langs = file_langs(h)
    except sqlite3.Error as exc:  # a v3 index missing tables/columns: UNKNOWN, never a crash
        reason = f"codemem index is unreadable ({type(exc).__name__}); run `codemem build`"
        return _Graph(GraphStatus.MISSING, reason, empty, {}, dict(empty))
    finally:
        if h.conn is not None:
            h.conn.close()
    edge_langs = {s: {langs[p] for e in es for p in e if p in langs} for s, es in edges.items()}
    return _Graph(h.status, h.reason, edges, langs, edge_langs)


def _line(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def _milestone_facts(text: str) -> tuple[bool, bool, list[str]]:
    """(any code Audit-Profile, any Critical-Path, Audit-Profile errors) — fences stripped first.

    plan.md writes milestones as `### Milestone N:` (plan-template.md) while grammar's
    MILESTONE_RE is `## Milestone N:` (the tasks.md form). Promote H3 milestones to H2 so a
    brand-new plan — the case Angle 6 runs on, before any tasks.md exists — is readable.
    """
    code = crit = False
    errors: list[str] = []
    lines = strip_fenced_blocks(text).split("\n")
    normalised = "\n".join(
        ln[1:] if ln.startswith("###") and MILESTONE_RE.match(ln[1:]) else ln
        for ln in lines
    )
    for block in split_milestones(normalised):
        value, ok, err = parse_audit_profile(block.text)
        if not ok:
            errors.append(f"milestone {block.number}: {err}")
        elif value in CODE_AUDIT_PROFILES:
            code = True
        if parse_critical_path(block.text)[0] is not None:
            crit = True
    return code, crit, errors


def _views(
    section_lines: list[str], stripped_lines: list[str]
) -> dict[str, tuple[int, str]]:
    """name -> (0-based heading line within the section, body text).

    Headings are located on the fence-stripped lines (a `### Component view` quoted inside a
    fenced example is content, not a view); bodies are sliced from the original lines so the
    mermaid fences are intact. scan_fences blanks lines rather than dropping them, so the two
    lists are line-aligned.
    """
    heads = [
        (i, m.group(1))
        for i, ln in enumerate(stripped_lines)
        if (m := _VIEW_RE.match(ln))
    ]
    out: dict[str, tuple[int, str]] = {}
    for k, (i, name) in enumerate(heads):
        end = heads[k + 1][0] if k + 1 < len(heads) else len(section_lines)
        out[name] = (i, "\n".join(section_lines[i + 1 : end]))
    return out


def _bracketed(line: str) -> list[tuple[int, str]]:
    """(index of `[`, contents) per `[...]` via str.find — linear on a hostile line of
    200 000 `[` where a `\\[([^\\]]*)\\]` regex re-scanned to EOL from every opener."""
    out: list[tuple[int, str]] = []
    i = line.find("[")
    while i >= 0:
        j = line.find("]", i + 1)
        if j < 0:
            break
        out.append((i, line[i + 1 : j]))
        i = line.find("[", j + 1)
    return out


def _labels(line: str) -> list[str]:
    return [label for _, label in _bracketed(line)]


def _label_paths(label: str) -> list[str]:
    """Repo-path claims in one `[...]` label; none when it is planned `(new)`. The one rule
    STALE_PATH and sigil endpoints share (§6.8 M8 found two copies, one without `_inside`)."""
    if _NEW_RE.search(label):
        return []
    # [/x/] is a shape; a leading "/" would otherwise resolve from the fs root
    return [q.lstrip("/") for t in label.split() if len(t) <= _MAX_TOKEN for q in _PATH_RE.findall(t)]


def _inside(repo_root: Path, rel: str) -> bool:
    """A label path is a claim about *this* repo. Absolute paths and `..` would otherwise
    turn the existence check into an oracle for arbitrary host files."""
    try:
        return (repo_root / rel).resolve().is_relative_to(repo_root.resolve())
    except OSError:
        return False


def _stale_paths(src: str, repo_root: Path) -> list[tuple[int, str]]:
    """Path claims per [label]; a label ending in '(new)' is exempt, other labels on the line are not."""
    hits: list[tuple[int, str]] = []
    for ln, line in enumerate(src.splitlines(), start=1):
        for label in _labels(line):
            for q in _label_paths(label):
                if not _inside(repo_root, q) or not (repo_root / q).exists():
                    hits.append((ln, q))
    return hits


def _node_labels(src: str) -> dict[str, str]:
    """id -> `[...]` label per fence; the LAST declaration wins, as in mermaid."""
    labels: dict[str, str] = {}
    for line in src.split("\n"):
        for i, content in _bracketed(line):
            m = _ID_TAIL_RE.search(line, max(0, i - _MAX_TOKEN), i)  # bounded look-back: linear
            if m:
                labels[m.group(1)] = _unwrap(content)
    return labels


def _unwrap(label: str) -> str:
    """`("x (new)")` -> `x (new)`: peel matched shape pairs, then quotes — never a `)` of
    `(new)`. Two indices, one slice: re-slicing per peel was quadratic."""
    i, k = 0, len(label)
    while True:
        while i < k and label[i] in " \t":
            i += 1
        while k > i and label[k - 1] in " \t":
            k -= 1
        if k - i > 1 and label[i] in "([/" and label[k - 1] in ")]/":
            i, k = i + 1, k - 1
            continue
        return label[i:k].strip('"').strip()


def _endpoint(node: str, labels: dict[str, str], repo_root: Path) -> tuple[str | None, str | None]:
    """(repo path, None) or (None, why it cannot be a graph node) — graph-independent part."""
    label = labels.get(node, "")
    if _NEW_RE.search(label):
        return None, f"endpoint planned (new): {label[:_MAX_TOKEN]}"
    paths = _label_paths(label)
    if not paths:
        return None, f"no repo path in node label: {node}"
    if not _inside(repo_root, paths[0]):  # never probed: existence outside is not ours to report
        return None, f"endpoint outside the repo: {paths[0]}"
    return paths[0], None


def _sigil_claims(
    src: str, first_line: int, repo_root: Path, graph: list[_Graph]
) -> tuple[list[Finding], list[Finding]]:
    """PHANTOM_EDGE / LABEL_UNKNOWN findings and UNKNOWN notes for one fence.

    ``graph`` is a one-slot cache: the index is opened only when a claim needs it.
    """
    found: list[Finding] = []
    unknown: list[Finding] = []
    labels = _node_labels(src)
    for ln, line in enumerate(src.split("\n")):
        if line.lstrip().startswith("%%"):
            continue  # a mermaid comment is not a claim
        line_no = first_line + ln
        m = _EDGE_RE.match(line)
        if m is None:
            if _SIGIL_SLOT_RE.search(line):  # chained, `&`, `-- "@x" -->`, `--o`...: never a silent pass
                unknown.append(Finding("UNKNOWN", line_no, "unparsed sigil edge form"))
            continue
        sigil = m.group(2).strip().strip('"').strip()
        if not sigil.startswith("@"):
            continue  # unlabelled or prose: never checked, never reported
        if sigil not in SIGILS:
            found.append(Finding("LABEL_UNKNOWN", line_no, f"unknown sigil {sigil!r}; reserved: {', '.join(SIGILS)}"))
            continue
        if sigil in _PLUGIN_SIGILS:
            unknown.append(Finding("UNKNOWN", line_no, f"{sigil}: {_PLUGIN_REASON}"))
            continue
        (sp, s_why), (dp, d_why) = _endpoint(m.group(1), labels, repo_root), _endpoint(m.group(3), labels, repo_root)
        if s_why or d_why:
            unknown.append(Finding("UNKNOWN", line_no, s_why or d_why or ""))
            continue
        if not graph:
            graph.append(_load_graph(repo_root))
        g = graph[0]
        if g.status is not GraphStatus.OK:  # missing, too old or stale: never PASS (L-012)
            unknown.append(Finding("UNKNOWN", line_no, g.reason or g.status.value))
            continue
        outside = next((p for p in (sp, dp) if not g.models(sigil, p)), None)
        if outside is not None:
            why = "endpoint missing" if not (repo_root / outside).exists() else (  # inside: checked
                "unparsed language, isolated file or out of graph")
            unknown.append(Finding("UNKNOWN", line_no, f"not in the codemem graph for {sigil} ({why}): {outside}"))
        elif (sp, dp) not in g.edges[sigil]:
            found.append(Finding("PHANTOM_EDGE", line_no, f"{sp} -->|{sigil}| {dp}: no such edge in the codemem graph"))
    return found, unknown


def _mermaid_fences(body: str) -> list[tuple[int, str]]:
    """(1-based line of first content line, source) per ```mermaid fence, one linear pass.

    Mirrors the CommonMark rule in grammar.scan_fences (closer = same char, >= opener
    length, no info string) rather than calling it: scan_fences returns block contents
    but not their info strings or positions, and a lazy `^```mermaid\\n(.*?)^```` regex
    re-scanned to EOF from every unclosed opener (measured 14.5 s at 18 000 openers).
    """
    lines = body.split("\n")
    out: list[tuple[int, str]] = []
    i = 0
    while i < len(lines):
        m = _FENCE_LINE_RE.match(lines[i])
        if not m:
            i += 1
            continue
        marker, info = m.group(1), m.group(2)
        j = i + 1
        while j < len(lines):
            c = _FENCE_LINE_RE.match(lines[j])
            if (
                c
                and c.group(1)[0] == marker[0]
                and len(c.group(1)) >= len(marker)
                and not c.group(2)
            ):
                break
            j += 1
        if info == "mermaid":
            out.append((i + 2, "\n".join(lines[i + 1 : j])))
        i = j + 1
    return out


def lint_text(plan_text: str, repo_root: Path, *, tasks_text: str = "") -> LintReport:
    out: list[Finding] = []
    code_ms, has_crit, audit_errors = _milestone_facts(plan_text + "\n" + tasks_text)
    out += [Finding("AUDIT_PROFILE_INVALID", 1, e) for e in dict.fromkeys(audit_errors)]
    # One scan answers "unterminated?" and "stripped?", so the two cannot disagree.
    # grammar.has_unterminated_fence strips HTML comments first (the gate's view): a
    # literal "<!--" inside a code fence then pairs with a later "-->" and eats a fence
    # closer — this very plan's M4 Contract does exactly that.
    scan = scan_fences(plan_text)
    if scan.unterminated:  # L-012: a fence to EOF hides §13; never lint as clean
        out.append(Finding("UNTERMINATED_FENCE", 1, "a code fence is never closed"))
        return LintReport(tuple(out), "UNKNOWN")
    stripped = scan.stripped  # headings inside fences are content, not structure
    first_h2 = H2_RE.search(stripped)
    front = stripped[: first_h2.start()] if first_h2 else stripped
    waiver, ok, err = parse_diagram_waiver(front)
    waiver = waiver or "none"
    if not ok:
        out.append(Finding("WAIVER_INVALID", 1, err or "non-canonical Diagram-Waiver"))
    elif waiver != "none" and code_ms:
        out.append(
            Finding(
                "WAIVER_NOT_ALLOWED",
                1,
                f"Diagram-Waiver: {waiver} but a milestone has a code Audit-Profile",
            )
        )
    m = _SECTION_RE.search(stripped)
    if m is None:
        if ok and waiver == "none":
            out.append(Finding("NO_SECTION", 1, "missing '## 13. Architecture View'"))
        return LintReport(tuple(out), "UNKNOWN")
    nxt = H2_RE.search(stripped, m.end())
    first = _line(stripped, m.start()) - 1  # 0-based line index of the section heading
    last = _line(stripped, nxt.start()) - 1 if nxt else None
    section_lines = plan_text.split("\n")[first:last]
    stripped_lines = stripped.split("\n")[first:last]
    base = first  # absolute line = base + 1-based line within the section
    views = _views(section_lines, stripped_lines)
    if "Component" not in views:
        out.append(
            Finding("NO_COMPONENT_VIEW", base + 1, "missing '### Component view'")
        )
    if has_crit and "Flow" not in views:
        out.append(
            Finding(
                "NO_FLOW_VIEW", base + 1, "Critical-Path present but no '### Flow view'"
            )
        )
    sources: list[str] = []
    unknowns: list[Finding] = []
    graph: list[_Graph] = []
    for name, (idx, body) in views.items():
        vline = base + idx + 1
        fences = [(ln, src) for ln, src in _mermaid_fences(body) if src.strip()]
        if not fences:
            out.append(
                Finding(
                    "EMPTY_FENCE", vline, f"{name} view has no non-empty mermaid fence"
                )
            )
            continue
        for fline, src in fences:
            head = _DIRECTIVE_RE.sub("", src.lstrip())
            head = _FRONT_MATTER_RE.sub("", head).strip()
            first_word = head.split()[0] if head else ""
            if first_word not in KNOWN_TYPES:
                out.append(
                    Finding(
                        "UNKNOWN_TYPE",
                        vline,
                        f"{name} view: unknown diagram type {first_word!r}",
                    )
                )
            out += [
                Finding(
                    "STALE_PATH",
                    vline + fline + ln - 1,
                    f"{p} not found (suffix the label with '(new)' if planned)",
                )
                for ln, p in _stale_paths(src, repo_root)
            ]
            claims, notes = _sigil_claims(src, vline + fline, repo_root, graph)
            out += claims
            unknowns += notes
            sources.append(src)
    return LintReport(tuple(out), render_check(sources), tuple(unknowns))


def lint_plan(
    plan_path: Path, repo_root: Path, *, tasks_path: Path | None = None
) -> LintReport:
    if tasks_path is None:
        cand = plan_path.with_name(plan_path.name.replace("-plan.md", "-tasks.md"))
        tasks_path = cand if cand != plan_path and cand.is_file() else None
    return lint_text(
        plan_path.read_text(encoding="utf-8"),
        repo_root,
        tasks_text=tasks_path.read_text(encoding="utf-8") if tasks_path else "",
    )


def render_check(sources: Sequence[str], *, timeout_s: float = 90.0) -> str:
    """timeout_s is per source, not total. PASS iff every source yields a non-empty SVG via MMDC_BIN; FAIL only on a mermaid parse
    error (stderr signature); UNKNOWN for everything else — mermaid-cli exits 1 for *all* errors,
    including a missing Chromium, so rc alone cannot distinguish a bad diagram from a bad install (L-012).
    """
    binary = shutil.which(os.environ.get("MMDC_BIN", "mmdc"))
    if binary is None or not sources:
        return "UNKNOWN"
    for src in sources:
        with tempfile.TemporaryDirectory() as d:
            inp, out = Path(d) / "in.mmd", Path(d) / "out.svg"
            inp.write_text(src, encoding="utf-8")
            try:
                proc = subprocess.run(  # nosec B603 — binary from MMDC_BIN seam, args are our own temp paths
                    [binary, "-i", str(inp), "-o", str(out)],
                    capture_output=True,
                    text=True,
                    timeout=timeout_s,
                )
            except (OSError, subprocess.TimeoutExpired):
                return "UNKNOWN"
            if proc.returncode != 0:
                return (
                    "FAIL"
                    if any(s in proc.stderr for s in PARSE_ERROR_SIGNATURES)
                    else "UNKNOWN"
                )
            if not out.is_file() or out.stat().st_size == 0:
                return "UNKNOWN"
    return "PASS"
