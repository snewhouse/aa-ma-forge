"""The human-readable report.md: ratings, findings, baseline, tool coverage. Written before the
secret gate runs, so it is redacted with everything else."""

from __future__ import annotations

from .models import Finding, Severity, Summary

ORDER = {s: i for i, s in enumerate(Severity)}
DEEP_ONLY_NOTE = (
    "security and tests_deps rate at most Adequate outside Deep: their core tools "
    "(semgrep, osv-scanner / pip-audit) reach the network and run only in Deep."
)


def _cell(text: str) -> str:
    return " ".join(text.split()).replace("|", "\\|")


def render(summary: Summary, findings: list[Finding]) -> str:
    s = summary.stamp
    lines = [
        f"# Codebase assessment — {s.sha12}{'-dirty' if s.dirty else ''}",
        "",
        f"Tier **{s.tier}** · branch `{_cell(s.branch)}` · {s.date_utc.isoformat().replace('+00:00', 'Z')}",
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
        lines += [f"> {DEEP_ONLY_NOTE}", ""]
    c, b = summary.counts, summary.baseline
    lines += [
        f"## Findings — {c.findings} ({c.refuted} refuted and dropped, {c.redacted} redacted)",
        "",
        f"Baseline: {b.new} new · {b.persisting} persisting · {b.fixed} fixed",
        "",
        "| severity | rule | where | title | id |",
        "|---|---|---|---|---|",
    ]
    for f in sorted(
        findings, key=lambda f: (ORDER[f.severity], f.rule, f.path, f.line or 0)
    ):
        where = f"{f.path}:{f.line}" if f.line else f.path
        lines.append(
            f"| {f.severity} | {f.rule} | `{_cell(where)}` | {_cell(f.title)} | {f.id} |"
        )
    lines += [
        "",
        "## Tools",
        "",
        *(f"- {name}: {status}" for name, status in sorted(s.tools.items())),
        "",
    ]
    return "\n".join(lines)
