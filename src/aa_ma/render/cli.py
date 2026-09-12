"""Console entry points for aa_ma.render. argparse, like aa_ma.tui.__main__."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from aa_ma.render.mermaid_lint import lint_plan


def lint_main(argv: Sequence[str] | None = None) -> int:
    """aa-ma-lint-views <plan.md> [--repo-root DIR] [--tasks FILE] — exit 0 clean / 1 findings / 2 usage."""
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
    a = p.parse_args(argv)
    if (
        a.plan is None
        or not a.plan.is_file()
        or (a.tasks is not None and not a.tasks.is_file())
    ):
        p.print_usage(sys.stderr)  # usage errors go to stderr; stdout is the report
        return 2
    rep = lint_plan(a.plan, a.repo_root, tasks_path=a.tasks)
    for f in rep.findings:
        print(f"{a.plan}:{f.line}: {f.code}: {f.message}")
    print(f"render: {rep.render_status}")
    return 1 if rep.findings else 0
