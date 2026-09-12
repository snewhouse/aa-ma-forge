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

from aa_ma.grammar import split_milestones, strip_fenced_blocks
from aa_ma.plan_parsers import (
    parse_audit_profile,
    parse_critical_path,
    parse_diagram_waiver,
)

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
_H2_RE = re.compile(r"^## ", re.M)
_VIEW_RE = re.compile(r"^### (Component|Flow|Data/State) view[ \t]*$", re.M)
_FENCE_RE = re.compile(r"^```mermaid[ \t]*\n(.*?)^```[ \t]*$", re.M | re.S)
_LABEL_RE = re.compile(r"\[([^\]]*)\]")
_PATH_RE = re.compile(
    r"[A-Za-z0-9_./-]+/[A-Za-z0-9_.-]+\.(?:md|py|sh|yaml|yml|toml|json|bats)"
)
_PLAN_MILESTONE_H3 = re.compile(r"^###([ \t]+Milestone\b)", re.M)


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
    normalised = _PLAN_MILESTONE_H3.sub(r"##\1", strip_fenced_blocks(text))
    for block in split_milestones(normalised):
        value, ok, err = parse_audit_profile(block.text)
        if not ok:
            errors.append(f"milestone {block.number}: {err}")
        elif value in CODE_AUDIT_PROFILES:
            code = True
        if parse_critical_path(block.text)[0] is not None:
            crit = True
    return code, crit, errors


def _views(section: str) -> dict[str, tuple[int, str]]:
    heads = list(_VIEW_RE.finditer(section))
    out: dict[str, tuple[int, str]] = {}
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(section)
        out[m.group(1)] = (m.start(), section[m.end() : end])
    return out


def _stale_paths(src: str, repo_root: Path) -> list[tuple[int, str]]:
    """Path claims per [label]; a label ending in '(new)' is exempt, other labels on the line are not."""
    hits: list[tuple[int, str]] = []
    for ln, line in enumerate(src.splitlines(), start=1):
        for label in _LABEL_RE.findall(line):
            label = label.strip().strip(
                '"'
            )  # mermaid quoted-label form: ["path (new)"]
            if label.endswith("(new)"):
                continue
            hits += [
                (ln, p) for p in _PATH_RE.findall(label) if not (repo_root / p).exists()
            ]
    return hits


def lint_text(plan_text: str, repo_root: Path, *, tasks_text: str = "") -> LintReport:
    out: list[Finding] = []
    code_ms, has_crit, audit_errors = _milestone_facts(plan_text + "\n" + tasks_text)
    out += [Finding("AUDIT_PROFILE_INVALID", 1, e) for e in audit_errors]
    front = plan_text.split("\n## ", 1)[0]
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
    m = _SECTION_RE.search(plan_text)
    if m is None:
        if ok and waiver == "none":
            out.append(Finding("NO_SECTION", 1, "missing '## 13. Architecture View'"))
        return LintReport(tuple(out), "UNKNOWN")
    nxt = _H2_RE.search(plan_text, m.end())
    section = plan_text[m.start() : nxt.start() if nxt else len(plan_text)]
    base = _line(plan_text, m.start()) - 1
    views = _views(section)
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
    for name, (pos, body) in views.items():
        vline = base + _line(section, pos)
        fences = [f for f in _FENCE_RE.findall(body) if f.strip()]
        if not fences:
            out.append(
                Finding(
                    "EMPTY_FENCE", vline, f"{name} view has no non-empty mermaid fence"
                )
            )
            continue
        for src in fences:
            first = src.strip().splitlines()[0].split()[0]
            if first not in KNOWN_TYPES:
                out.append(
                    Finding(
                        "UNKNOWN_TYPE",
                        vline,
                        f"{name} view: unknown diagram type '{first}'",
                    )
                )
            out += [
                Finding(
                    "STALE_PATH",
                    vline + ln,
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
    """PASS iff every source yields a non-empty SVG via MMDC_BIN; FAIL only on a mermaid parse
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
