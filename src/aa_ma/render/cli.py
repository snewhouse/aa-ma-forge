"""Console entry points for aa_ma.render. argparse, like aa_ma.tui.__main__."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from aa_ma.render.html import render_markdown
from aa_ma.render.coverage import coverage_findings
from aa_ma.render.graph import printable
from aa_ma.render.mermaid_lint import INDEX_UNKNOWN, SIGIL_FINDINGS, LintReport, lint_plan


def lint_main(argv: Sequence[str] | None = None) -> int:
    """aa-ma-lint-views <plan.md> [--repo-root DIR] [--tasks FILE] [--coverage] — exit 0 clean / 1 findings / 2 usage."""
    p = argparse.ArgumentParser(
        prog="aa-ma-lint-views", description="Lint plan.md §13 Architecture View"
    )
    p.add_argument("plan", nargs="?", type=Path)
    p.add_argument("--repo-root", type=Path, default=Path.cwd())
    p.add_argument(
        "--tasks",
        type=Path,
        default=None,
        help="tasks.md to read Audit-Profile/Critical-Path from",
    )
    p.add_argument(
        "--coverage",
        action="store_true",
        help="Angle 6 check 8 (planning time only): every Contract Create/Modify path is drawn in §13",
    )
    a = p.parse_args(argv)
    if (
        a.plan is None
        or not a.plan.is_file()
        or (a.tasks is not None and not a.tasks.is_file())
    ):
        p.print_usage(sys.stderr)  # usage errors go to stderr; stdout is the report
        return 2
    rep = lint_plan(a.plan, a.repo_root, tasks_path=a.tasks)
    findings = list(rep.findings)
    if a.coverage:  # never passed by the milestone gate (ADR-0009)
        try:
            findings += coverage_findings(a.plan.read_text(encoding="utf-8"))
        except Exception as e:  # a crash is UNKNOWN (exit 2), never "findings" or clean (L-012)
            print(f"{a.plan}:1: UNKNOWN: coverage could not run: {printable(type(e).__name__)}")
            return 2
    for f in findings:
        print(f"{a.plan}:{f.line}: {f.code}: {printable(f.message)}")
    for f in rep.unknowns:  # informational: an unevaluable claim never sets the exit (L-012)
        print(f"{a.plan}:{f.line}: UNKNOWN: {printable(f.message)}")
    print(f"sigils: {_sigil_summary(rep)}")  # read by the §6.7 HARD item (ADR-0015)
    print(f"render: {rep.render_status}")
    return 1 if findings else 0


def _sigil_summary(rep: LintReport) -> str:
    if rep.sigil_edges is None:
        return "UNKNOWN (§13 not read)"
    phantom = sum(f.code in SIGIL_FINDINGS for f in rep.findings)
    index = sum(f.code == INDEX_UNKNOWN for f in rep.unknowns)
    return f"edges={rep.sigil_edges} phantom={phantom} unknown={len(rep.unknowns)} index-unknown={index}"


def render_main(argv: Sequence[str] | None = None) -> int:
    """aa-ma-render <md>... [--out DIR] — writes DIR/<stem>.html per source; exit 0 ok / 2 usage."""
    p = argparse.ArgumentParser(
        prog="aa-ma-render", description="Render markdown to self-contained HTML"
    )
    p.add_argument("sources", nargs="*", type=Path)
    p.add_argument("--out", type=Path, default=Path("build/render"))
    a = p.parse_args(argv)
    if not a.sources:
        p.print_usage(sys.stderr)
        return 2
    names = [f"{s.stem}.html" for s in a.sources]
    if dupes := {n for n in names if names.count(n) > 1}:
        print(f"aa-ma-render: output name collision: {sorted(dupes)}", file=sys.stderr)
        return 2
    try:  # read everything first: a bad source means no output at all, not a partial set
        texts = [s.read_text(encoding="utf-8") for s in a.sources]
        a.out.mkdir(parents=True, exist_ok=True)
        for src, name, text in zip(a.sources, names, texts, strict=True):
            target = a.out / name
            target.write_text(render_markdown(text, title=src.stem), encoding="utf-8")
            print(target)
    except OSError as e:  # unreadable source, --out is a file, unwritable dir: exit 2, never a traceback
        print(f"aa-ma-render: {e}", file=sys.stderr)
        p.print_usage(sys.stderr)
        return 2
    return 0
