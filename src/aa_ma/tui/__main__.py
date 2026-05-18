"""aa-ma-tui CLI entry point — M0 skeleton + M2 snapshot/json dispatch.

Created in aa-ma-tui-tracker M0 T0.5 (2026-05-17),
extended in M2 T2.5 (2026-05-18) with snapshot+json modes.

Wiring contract (M2):
    --snapshot[=board|tree|summary] — render to stdout
    --json                          — emit JSON envelope to stdout
    --task NAME                     — required by --snapshot=tree; filter scope
    --include-completed             — extend roots to .claude/dev/completed
    --root PATH                     — explicit root (default scans ./ and ~/)

Exit codes (per M2 plan):
    0 — normal
    2 — --task NAME not found in discovered tasks
    3 — no tasks discovered at all

M3 will replace the no-flag default branch with Textual app launch.
Per KISS + SOLID Open/Closed: dispatch logic is a single match-statement
in `main()`; subcommands extend by adding cases, not refactoring.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from aa_ma.tui import __version__
from aa_ma.tui.json_output import dump as json_dump
from aa_ma.tui.parser import discover_tasks
from aa_ma.tui.snapshot import render_board, render_summary, render_tree

# Exit code constants — single source of truth for the contract.
EXIT_OK = 0
EXIT_TASK_NOT_FOUND = 2
EXIT_NO_TASKS = 3


def _build_parser() -> argparse.ArgumentParser:
    """Construct the CLI argparser.

    Factored out so M3 can extend by importing this and adding arguments,
    not by rewriting `main`.
    """
    parser = argparse.ArgumentParser(
        prog="aa-ma-tui",
        description="Terminal UI for tracking AA-MA tasks.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"aa-ma-tui {__version__}",
    )
    parser.add_argument(
        "--snapshot",
        nargs="?",
        const="board",
        choices=["board", "tree", "summary"],
        help="render snapshot to stdout (default: board)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit JSON envelope of discovered tasks to stdout",
    )
    parser.add_argument(
        "--task",
        metavar="NAME",
        help="filter to a single task (required for --snapshot=tree)",
    )
    parser.add_argument(
        "--include-completed",
        action="store_true",
        help="extend discovery to <root>/.claude/dev/completed/",
    )
    parser.add_argument(
        "--root",
        metavar="PATH",
        help="root dir to scan (default: ./ and ~/)",
    )
    return parser


def _resolve_roots(root_arg: str | None, include_completed: bool) -> list[Path]:
    """Build the list of root dirs to scan based on CLI args.

    Two `--root` interpretations (auto-detected):
        (a) Direct scan root — children are task dirs (used by tests).
        (b) `.claude` project root — traverse to `dev/active[/completed]`
            (used by `--root ~/.claude` in production).

    Default (no --root): scan both `./.claude/dev/active` and
    `~/.claude/dev/active` (and the `completed` siblings if requested),
    per the plan's "scan BOTH" behaviour for v1 demo corpus.
    """
    if root_arg is not None:
        base = Path(root_arg).expanduser()
        canonical_active = base / "dev" / "active"
        canonical_completed = base / "dev" / "completed"
        # Layout (b) — `.claude`-style project root
        if canonical_active.exists() or canonical_completed.exists():
            roots: list[Path] = []
            if canonical_active.exists():
                roots.append(canonical_active)
            if include_completed and canonical_completed.exists():
                roots.append(canonical_completed)
            return roots
        # Layout (a) — direct scan root
        return [base]

    # Default: scan both `./` and `~/` under canonical AA-MA paths
    roots = []
    for default_base in (Path.cwd(), Path.home()):
        roots.append(default_base / ".claude" / "dev" / "active")
        if include_completed:
            roots.append(default_base / ".claude" / "dev" / "completed")
    return roots


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns process exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    # No mode flag → launch interactive Textual app (M3).
    if args.snapshot is None and not args.json:
        roots = _resolve_roots(args.root, args.include_completed)
        tasks = discover_tasks(roots)
        # Local import keeps Textual off the CLI hot path when only --snapshot / --json used.
        from aa_ma.tui.app import AAMAApp

        AAMAApp(initial_tasks=tasks, watch_roots=roots).run()
        return EXIT_OK

    # Discover tasks via the SINGLE canonical discover_tasks function
    # (L-052 dual-formatter rule — verified by tests in test_snapshot.py
    # and test_json_output.py).
    roots = _resolve_roots(args.root, args.include_completed)
    tasks = discover_tasks(roots)

    if not tasks:
        return EXIT_NO_TASKS

    # JSON mode takes precedence if both flags given (defensive).
    if args.json:
        print(json_dump(tasks))
        return EXIT_OK

    # Snapshot dispatch
    if args.snapshot == "board":
        print(render_board(tasks))
        return EXIT_OK

    if args.snapshot == "summary":
        print(render_summary(tasks))
        return EXIT_OK

    if args.snapshot == "tree":
        if not args.task:
            parser.error("--snapshot=tree requires --task NAME")
        match = next((t for t in tasks if t.name == args.task), None)
        if match is None:
            return EXIT_TASK_NOT_FOUND
        print(render_tree(match))
        return EXIT_OK

    # Defensive — argparse choices=[] should prevent this branch.
    parser.error(f"unknown --snapshot mode: {args.snapshot!r}")
    return EXIT_OK  # pragma: no cover — parser.error raises SystemExit


if __name__ == "__main__":  # pragma: no cover — argparse covers exit path
    sys.exit(main())
