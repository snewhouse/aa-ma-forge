"""aa-ma-tui CLI entry point — M0 skeleton.

Created in aa-ma-tui-tracker M0 T0.5 (2026-05-17).

M0 contract (this file): argparse skeleton that handles `--version` and exits 0.

Future extension points (do not implement at M0):
    - M2 wires snapshot subcommand: `--snapshot[=board|tree|summary]`, `--json`,
      `--include-completed`, `--task NAME`. Exit codes 0/2/3 per plan.
    - M3 wires default branch: no-arg invocation launches the Textual app
      (DashboardScreen → TaskDetailScreen).

Per KISS + SOLID Open/Closed: keep this file minimal; subcommands extend, not
refactor.
"""

from __future__ import annotations

import argparse
import sys

from aa_ma.tui import __version__


def _build_parser() -> argparse.ArgumentParser:
    """Construct the CLI argparser.

    Factored out so M2/M3 can extend by importing this and adding arguments,
    not by rewriting `main`.
    """
    parser = argparse.ArgumentParser(
        prog="aa-ma-tui",
        description="Terminal UI for tracking AA-MA tasks (M0 skeleton).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"aa-ma-tui {__version__}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns process exit code.

    M0 behaviour: prints version on `--version`, otherwise prints a one-line
    placeholder and exits 0. M2 will replace the default-branch body with
    snapshot dispatch; M3 will replace it with Textual app launch.
    """
    parser = _build_parser()
    parser.parse_args(argv)
    # M0 skeleton: no subcommand wiring yet. M2/M3 land here.
    print(
        "aa-ma-tui M0 scaffolding only. Snapshot modes land in M2; "
        "interactive TUI in M3."
    )
    return 0


if __name__ == "__main__":  # pragma: no cover — argparse covers exit path
    sys.exit(main())
