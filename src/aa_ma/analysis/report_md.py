"""The human-readable report.md: ratings, findings, baseline, tool coverage, and what the target
did to its scanners. Rendered by finalize from the already-redacted outputs, then gated again."""

from __future__ import annotations

import re

from .models import CORE_INPUTS, NETWORK_TOOLS, Finding, Refutation, Severity, Summary
from .stamp import report_name

ORDER = {s: i for i, s in enumerate(Severity)}


# The threat model (M2 §6.8 round 5, Ste): hostile content at rest.
SCOPE = [
    "## Scope",
    "",
    "The repository was treated as untrusted content: its own git config, scanner configs and "
    "symlinks were checked, not obeyed or followed. Not covered: a process changing the "
    "repository while the analysis runs, and any approved test, build or lint command, which "
    "runs the repository's code by design.",
    "",
]


def deep_only_note() -> str:
    """Which dimensions cap at Adequate outside Deep, and why — from the constants, not prose."""
    capped = {d: t for d, t in CORE_INPUTS.items() if set(t) <= set(NETWORK_TOOLS)}
    dims = " and ".join(capped)
    tools = " / ".join(t for ts in capped.values() for t in ts)
    return f"{dims} rate at most Adequate outside Deep: their core tools ({tools}) reach the network and run only in Deep."


# Repo-derived text (branch, paths, tool titles) is written as inert Markdown: HTML entities
# for & < >, a backslash before every Markdown punctuation mark — no span, link, image or tag.
MD_SPECIAL = re.compile(r"([\\`*_{}\[\]()#+!|~-])")


def _cell(text: str) -> str:
    text = " ".join(text.split())
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return MD_SPECIAL.sub(r"\\\1", text)


def _target_notes(m: dict[str, int | float | None]) -> list[str]:
    """What the target did to its scanners, and findings that could not be reported."""
    notes = []
    configs = m.get("tool_config.overrides") or 0
    if configs:
        notes.append(
            f"- {configs} scanner config file(s) shipped by the target: recorded in run.log, not obeyed."
        )
    marks = {
        k.split(".", 1)[1]: v
        for k, v in m.items()
        if k.startswith("suppressions.") and v
    }
    if marks:
        notes.append(
            "- Inline suppressions the scanners still honour: "
            + ", ".join(f"{k} {v}" for k, v in sorted(marks.items()))
            + "."
        )
    unscanned = (m.get("files.unstaged") or 0) + (m.get("files.escaping") or 0)
    if unscanned:
        notes.append(
            f"- {unscanned} tracked file(s) not scanned: changed after listing, or behind a"
            " directory that is a symlink."
        )
    dropped = m.get("findings.unreportable") or 0
    if dropped:
        notes.append(
            f"- {dropped} finding(s) dropped: their file names cannot be reported safely."
        )
    return ["## What the target did to its scanners", "", *notes, ""] if notes else []


def _where(f: Finding) -> str:
    return f"{f.path}:{f.line}" if f.line else f.path


def render(summary: Summary, findings: list[Finding]) -> str:
    s = summary.stamp
    lines = [
        f"# Codebase assessment — {report_name(s.sha12, s.dirty)}",
        "",
        f"Tier **{s.tier}** · branch {_cell(s.branch)} · {s.date_utc.isoformat().replace('+00:00', 'Z')}",
        "",
        "## Ratings",
        "",
        "| dimension | rating | confidence | capped |",
        "|---|---|---|---|",
        *(
            f"| {d.dimension} | {d.rating} | {d.confidence} | {'yes' if d.capped else ''} |"
            for d in summary.dimensions
        ),
        "",
    ]
    if s.tier != "deep":
        lines += [f"> {deep_only_note()}", ""]
    c, b = summary.counts, summary.baseline
    lines += [
        f"## Findings — {c.findings} ({c.refuted} refuted, listed below; {c.redacted} redacted)",
        "",
        f"Baseline: {b.new} new · {b.persisting} persisting · {b.fixed} fixed",
        "",
        "| severity | rule | where | title | id |",
        "|---|---|---|---|---|",
    ]
    ordered = sorted(
        findings, key=lambda f: (ORDER[f.severity], f.rule, f.path, f.line or 0)
    )
    refuted = [f for f in ordered if f.refutation == Refutation.REFUTED]
    for f in ordered:
        if f.refutation != Refutation.REFUTED:
            lines.append(
                f"| {f.severity} | {f.rule} | {_cell(_where(f))} | {_cell(f.title)} | {f.id} |"
            )
    if refuted:
        lines += [
            "",
            f"## Refuted — {len(refuted)}",
            "",
            "Disproved by the refuter; not counted, not in SARIF, kept here with the reason.",
            "",
            "| severity | rule | where | title | reason | id |",
            "|---|---|---|---|---|---|",
            *(
                f"| {f.severity} | {f.rule} | {_cell(_where(f))} | {_cell(f.title)} "
                f"| {_cell(f.refutation_reason or '')} | {f.id} |"
                for f in refuted
            ),
        ]
    lines += [
        "",
        "## Tools",
        "",
        *(f"- {name}: {status}" for name, status in sorted(s.tools.items())),
        "",
        *_target_notes(summary.metrics),
        *SCOPE,
    ]
    return "\n".join(lines)
