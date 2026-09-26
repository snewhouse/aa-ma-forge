"""Console entry points for aa_ma.render. argparse, like aa_ma.tui.__main__."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from aa_ma.render.html import render_markdown
from aa_ma.render.coverage import coverage_findings
from aa_ma.render.graph import printable
from aa_ma.render.mermaid_lint import SIGIL_FINDINGS, UNKNOWN_INDEX, UNKNOWN_INVALID, LintReport, lint_plan


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
    where = printable(str(a.plan))
    for f in findings:
        print(f"{where}:{f.line}: {f.code}: {printable(f.message)}")
    for f in rep.unknowns:  # informational: an unevaluable claim never sets the exit (L-012)
        print(f"{where}:{f.line}: UNKNOWN: {printable(f.message)}")
    print(f"sigils: {_sigil_summary(rep)}")  # read by the §6.7 HARD item (ADR-0015)
    print(f"render: {rep.render_status}")
    return 1 if findings else 0


def _sigil_summary(rep: LintReport) -> str:
    """`edges=N checked=C phantom=P unknown=K invalid=V index-unknown=I`; invalid and
    index-unknown are subsets of unknown. `UNKNOWN (…)` when not every sigil claim was read."""
    if rep.sigil_edges is None:
        return "UNKNOWN (§13 not fully read)"
    phantom = sum(f.code in SIGIL_FINDINGS for f in rep.findings)
    invalid = sum(f.code == UNKNOWN_INVALID for f in rep.unknowns)
    index = sum(f.code == UNKNOWN_INDEX for f in rep.unknowns)
    return (
        f"edges={rep.sigil_edges} checked={rep.sigil_checked} phantom={phantom} "
        f"unknown={len(rep.unknowns)} invalid={invalid} index-unknown={index}"
    )


def render_main(argv: Sequence[str] | None = None) -> int:
    """aa-ma-render <md>... [--out DIR] — writes DIR/<stem>.html per source; exit 0 ok / 2 usage.
    aa-ma-render --explorer [--repo-root R] [--out DIR] — writes DIR/explorer.html (DIR: build)."""
    p = argparse.ArgumentParser(
        prog="aa-ma-render", description="Render markdown to self-contained HTML"
    )
    p.add_argument("sources", nargs="*", type=Path)
    p.add_argument("--out", type=Path, default=None, help="default build/render, or build with --explorer")
    p.add_argument("--explorer", action="store_true", help="the codemem graph as one clickable page")
    p.add_argument("--repo-root", type=Path, default=Path.cwd(), help="with --explorer: the indexed repo")
    a = p.parse_args(argv)
    if a.explorer:
        if a.sources:
            p.print_usage(sys.stderr)
            return 2
        return _explorer(a.repo_root, a.out or Path("build"))
    a.out = a.out or Path("build/render")
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


def _explorer(repo_root: Path, out: Path) -> int:
    # Imported here, not at module top: this module also hosts aa-ma-lint-views, which the
    # §6.7 HARD item runs, and a broken explorer must never take the lint down with it.
    from aa_ma.render.explorer import build_explorer

    try:
        page, stale = build_explorer(repo_root)
    except ValueError as e:  # missing / too-old / unreadable index: nothing is written
        print(f"aa-ma-render: {printable(str(e))}", file=sys.stderr)
        return 2
    if stale:
        print(f"aa-ma-render: warning: index is stale — {printable(stale)}", file=sys.stderr)
    try:
        out.mkdir(parents=True, exist_ok=True)
        target = out / "explorer.html"
        target.write_text(page, encoding="utf-8")
    except OSError as e:
        print(f"aa-ma-render: {printable(str(e))}", file=sys.stderr)
        return 2
    print(target)
    return 0
