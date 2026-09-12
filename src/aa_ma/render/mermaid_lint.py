"""Structural lint for plan.md §13 Architecture View. Pure Python; mmdc optional (L-012)."""

from __future__ import annotations

import os
import re
import shutil
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
_FENCE_RE = re.compile(r"^```mermaid[ \t]*\n(.*?)^```[ \t]*$", re.M | re.S)
_LABEL_RE = re.compile(r"\[([^\]]*)\]")
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


def _stale_paths(src: str, repo_root: Path) -> list[tuple[int, str]]:
    """Path claims per [label]; a label ending in '(new)' is exempt, other labels on the line are not."""
    hits: list[tuple[int, str]] = []
    for ln, line in enumerate(src.splitlines(), start=1):
        for label in _LABEL_RE.findall(line):
            if _NEW_RE.search(label):
                continue
            # [/x/] is a shape; a leading "/" would otherwise resolve from the filesystem root
            paths = (q.lstrip("/") for q in _PATH_RE.findall(label))
            hits += [(ln, q) for q in paths if not (repo_root / q).exists()]
    return hits


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
    for name, (idx, body) in views.items():
        vline = base + idx + 1
        fences = [
            (_line(body, fm.start(1)), fm.group(1)) for fm in _FENCE_RE.finditer(body)
        ]
        fences = [(ln, src) for ln, src in fences if src.strip()]
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
                        f"{name} view: unknown diagram type '{first_word}'",
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
            sources.append(src)
    return LintReport(tuple(out), render_check(sources))


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
