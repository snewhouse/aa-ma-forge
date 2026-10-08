#!/usr/bin/env python3
"""Check repo conventions on the lines a change adds (touched-files harness, ADR-0018).

Usage: check_conventions.py [--from-ref REF --to-ref REF] [FILE...]

The diff source is, in order of precedence: the --from-ref/--to-ref flags, the
PRE_COMMIT_FROM_REF/PRE_COMMIT_TO_REF environment (pre-commit cannot template refs
into hook args), then the staged changes. Ref diffs are three-dot (``from...to``).
FILE arguments filter the diff. Untouched lines are never checked (D8: no backfill).

Exit codes: 0 clean | 1 findings (``path:line: CODE message`` on stdout) |
2 usage or git error, including "no diff source".

Stdlib only, so it stays a leaf: no import from aa_ma or codemem, any python3 runs it.
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import subprocess
import sys
from collections.abc import Callable, Sequence

log = logging.getLogger(__name__)

Finding = tuple[str, int, str, str]
Check = Callable[[str, dict[int, str]], list[Finding]]

# M1 ships the harness with no checks; M6 adds WHY001 and TODO001.
CHECKS: list[Check] = []

_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


class UsageError(Exception):
    """A bad argument, an unresolvable ref, or a git failure (exit 2)."""


def _git(
    args: Sequence[str], cwd: str | os.PathLike | None
) -> subprocess.CompletedProcess:
    # why: --literal-pathspecs so a filename like `*.py` matches itself, not a glob;
    # core.quotePath=false so non-ASCII paths come back verbatim.
    return subprocess.run(
        ["git", "-c", "core.quotePath=false", "--literal-pathspecs", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="surrogateescape",
        check=False,
    )


def _git_out(args: Sequence[str], cwd: str | os.PathLike | None) -> str:
    proc = _git(args, cwd)
    if proc.returncode != 0:
        raise UsageError(f"git {args[0]} failed: {proc.stderr.strip()}")
    return proc.stdout


def _verify_commit(ref: str, cwd: str | os.PathLike | None) -> str:
    # why: --end-of-options stops a ref like `--output=x` being read as an option.
    proc = _git(
        ["rev-parse", "--verify", "--quiet", "--end-of-options", f"{ref}^{{commit}}"],
        cwd,
    )
    if proc.returncode != 0:
        raise UsageError(f"not a commit: {ref!r}")
    return proc.stdout.strip()


def resolve_range(
    from_ref: str | None, to_ref: str | None, cwd: str | os.PathLike | None = None
) -> list[str]:
    """Return the `git diff` arguments selecting the change: a verified range or `--cached`."""
    if from_ref or to_ref:
        if not (from_ref and to_ref):
            raise UsageError("--from-ref and --to-ref must be given together")
        return [f"{_verify_commit(from_ref, cwd)}...{_verify_commit(to_ref, cwd)}"]
    rc = _git(["diff", "--cached", "--quiet"], cwd).returncode
    if rc == 0:
        raise UsageError("no diff source: pass --from-ref/--to-ref or stage changes")
    if rc != 1:
        raise UsageError("git diff --cached failed (not a git repository?)")
    return ["--cached"]


def _parse_added(patch: str) -> dict[int, str]:
    added: dict[int, str] = {}
    lineno = None
    for line in patch.split("\n"):
        if line.startswith("diff --git "):
            lineno = None
            continue
        hunk = _HUNK_RE.match(line)
        if hunk:
            lineno = int(hunk.group(1))
        elif lineno is not None and line.startswith("+"):
            # why: inside a -U0 hunk only '+', '-' and '\ No newline' lines occur, so a
            # '+' here is content even when it reads like a '+++' header.
            added[lineno] = line[1:]
            lineno += 1
    return added


def added_lines(
    range_args: Sequence[str],
    files: Sequence[str] | None = None,
    cwd: str | os.PathLike | None = None,
) -> dict[str, dict[int, str]]:
    """Map each added, modified or renamed file to its added lines ``{lineno: text}``.

    Deleted files are omitted. A rename reports only the lines that differ from the
    old path, so moving a file does not make every line in it "touched".
    """
    wanted = set(files) if files else None
    # why: same -z token walk as src/aa_ma/analysis/changed.py (not imported: this
    # script stays stdlib-only); keep the two in step.
    fields = _git_out(["diff", "--name-status", "-z", "-M", *range_args], cwd).split(
        "\0"
    )
    result: dict[str, dict[int, str]] = {}
    i = 0
    while i < len(fields) and fields[i]:
        status = fields[i]
        width = 2 if status[0] in "RC" else 1
        paths = fields[i + 1 : i + 1 + width]
        i += 1 + width
        path = paths[-1]
        if status.startswith("D") or (wanted is not None and path not in wanted):
            continue
        patch = _git_out(
            [
                "diff",
                "-U0",
                "-M",
                "--no-color",
                "--no-ext-diff",
                *range_args,
                "--",
                *paths,
            ],
            cwd,
        )
        result[path] = _parse_added(patch)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    """Run every enabled check over the touched lines; return the exit code."""
    parser = argparse.ArgumentParser(description=(__doc__ or "").partition("\n")[0])
    parser.add_argument("--from-ref")
    parser.add_argument("--to-ref")
    parser.add_argument("files", nargs="*", metavar="FILE")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stderr)

    if args.from_ref or args.to_ref:
        from_ref, to_ref = args.from_ref, args.to_ref
    else:
        from_ref = os.environ.get("PRE_COMMIT_FROM_REF")
        to_ref = os.environ.get("PRE_COMMIT_TO_REF")
    try:
        touched = added_lines(resolve_range(from_ref, to_ref), files=args.files or None)
    except UsageError as exc:
        # why: a bad ref or empty diff is an expected usage error; one line, no traceback.
        log.error("check_conventions: %s", exc)  # noqa: TRY400
        return 2

    log.info("check_conventions: %d checks enabled", len(CHECKS))
    findings = [
        f
        for path, lines in touched.items()
        for check in CHECKS
        for f in check(path, lines)
    ]
    for path, lineno, code, message in findings:
        print(f"{path}:{lineno}: {code} {message}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
