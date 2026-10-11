#!/usr/bin/env python3
"""Check repo conventions on the lines a change adds (touched-files harness, ADR-0018).

Usage: check_conventions.py [--from-ref REF --to-ref REF] [FILE...]

The diff source is, in order of precedence: the --from-ref/--to-ref flags, the
PRE_COMMIT_FROM_REF/PRE_COMMIT_TO_REF environment (pre-commit cannot template refs
into hook args), then the staged changes. Ref diffs are three-dot (``from...to``).
FILE arguments (repo-root-relative, as pre-commit passes them) filter the diff.
Untouched lines are never checked (D8: no backfill).

Exit codes: 0 clean | 1 findings (``path:line: CODE message`` on stdout) |
2 usage or git error, including "no diff source".

Stdlib only, so it stays a leaf: no import from aa_ma or codemem, any python3 runs it.
"""

from __future__ import annotations

import argparse
import io
import logging
import os
import re
import subprocess
import sys
import tokenize
from collections.abc import Callable, Sequence

log = logging.getLogger(__name__)

Finding = tuple[str, int, str, str]
# A check gets (path, {lineno: added text}, whole new-side file text).
Check = Callable[[str, dict[int, str], str], list[Finding]]

_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
_SHEBANG_SH_RE = re.compile(r"^#!.*\b(?:ba|da|k|z)?sh\b")
_PY_SUPPRESS_RE = re.compile(r"#\s*(noqa|type:\s*ignore)\b", re.IGNORECASE)
_SH_SUPPRESS_RE = re.compile(r"(\|\|\s*true\b|2>\s*/dev/null)")
_WHY_RE = re.compile(r"#\s*why:")
_TODO_RE = re.compile(
    r"#\s*(TODO|FIXME)\b"
)  # why: a tag, as ruff TD reads it — not prose
_TODO_REF_RE = re.compile(r"#\d+|ADR-\d{4}")
_HEREDOC_RE = re.compile(r"<<(-?)\s*(['\"]?)([A-Za-z0-9_]+)\2")
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")


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
    wanted = {os.path.normpath(f) for f in files} if files else None
    # why: --name-status prints root-relative paths but pathspecs resolve against the cwd,
    # so a run from a subdirectory would diff nothing; run every diff from the top level.
    top = _git_out(["rev-parse", "--show-toplevel"], cwd).strip()
    # why: same -z token walk as src/aa_ma/analysis/changed.py (not imported: this
    # script stays stdlib-only); keep the two in step.
    fields = _git_out(["diff", "--name-status", "-z", "-M", *range_args], top).split(
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
                "--no-textconv",  # why: a local driver would shift line numbers and run code
                *range_args,
                "--",
                *paths,
            ],
            top,
        )
        result[path] = _parse_added(patch)
    return result


# --- Comment scanning ---------------------------------------------------------------
# Each language reduces a file to {lineno: (code, comment)}: code is the line with
# string contents blanked, comment is the comment text. Strings, docstrings, heredoc
# bodies and Markdown never reach a check (T8).


def _python_lines(path: str, text: str) -> dict[int, tuple[str, str]]:
    lines = {n: (line, "") for n, line in enumerate(text.splitlines(), start=1)}
    try:
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type == tokenize.COMMENT:
                row = tok.start[0]
                lines[row] = (lines[row][0][: tok.start[1]], tok.string)
    except (tokenize.TokenError, SyntaxError) as exc:
        # why: a file that cannot be tokenized is ruff's to report (it runs in the same
        # hook set); say so and check nothing rather than guess at comments.
        log.warning("check_conventions: %s: not tokenizable, skipped: %s", path, exc)
        return {}
    return lines


def _shell_code_comment(line: str, quote: str | None) -> tuple[str, str, str | None]:
    """Split one shell line into (code with quoted text blanked, comment, open quote)."""
    code: list[str] = []
    i = 0
    while i < len(line):
        c = line[i]
        if quote is None and c == "#" and (i == 0 or line[i - 1] in " \t;|&("):
            return "".join(code), line[i:], None
        if c == "\\" and quote != "'":
            # why: keep code[] index-aligned with line so heredoc delimiters can be read
            # back from the raw line at the same offset.
            code.append(
                line[i : i + 2] if quote is None else "  "[: len(line[i : i + 2])]
            )
            i += 2
            continue
        if quote is None and c in "'\"":
            quote = c
            code.append(c)
        elif quote is not None and c == quote:
            quote = None
            code.append(c)
        else:
            code.append(" " if quote is not None else c)
        i += 1
    return "".join(code), "", quote


def _shell_lines(text: str) -> dict[int, tuple[str, str]]:
    lines: dict[int, tuple[str, str]] = {}
    quote: str | None = None
    heredocs: list[tuple[bool, str]] = []  # (strip leading tabs, delimiter), in order
    for n, line in enumerate(text.splitlines(), start=1):
        if heredocs:
            strip_tabs, delim = heredocs[0]
            if (line.lstrip("\t") if strip_tabs else line) == delim:
                heredocs.pop(0)
            lines[n] = ("", "")
            continue
        code, comment, quote = _shell_code_comment(line, quote)
        for m in re.finditer(r"(?<!<)<<(?!<)", code):
            here = _HEREDOC_RE.match(line, m.start())
            if here:
                heredocs.append((here.group(1) == "-", here.group(3)))
        lines[n] = (code, comment)
    return lines


def _scan(path: str, text: str) -> tuple[dict[int, tuple[str, str]], re.Pattern] | None:
    """Return the file's (lines, suppression pattern), or None if it is not scanned."""
    if path.endswith((".py", ".pyi")):
        return _python_lines(path, text), _PY_SUPPRESS_RE
    if path.endswith(".bats"):
        return None  # why: bats is not plain shell (as the shellcheck hook, ADR-0018)
    if path.endswith((".sh", ".bash")) or _SHEBANG_SH_RE.match(text):
        return _shell_lines(text), _SH_SUPPRESS_RE
    return None


def _has_why(lines: dict[int, tuple[str, str]], n: int) -> bool:
    if _WHY_RE.search(lines[n][1]):
        return True
    # why: a reason often spans a comment block; any `# why:` in the block directly
    # above the line covers it.
    n -= 1
    while n in lines and not lines[n][0].strip() and lines[n][1]:
        if _WHY_RE.search(lines[n][1]):
            return True
        n -= 1
    return False


def check_why(path: str, added: dict[int, str], text: str) -> list[Finding]:
    """WHY001: an added suppression needs a `# why:` on its line or the comment above.

    Args:
        path: Repo-relative path of the file.
        added: The added lines, ``{lineno: text}``.
        text: The whole new-side file.

    Returns:
        One finding per added line that suppresses without a reason.
    """
    scanned = _scan(path, text)
    if scanned is None:
        return []
    lines, pattern = scanned
    findings = []
    for n in sorted(added):
        code, comment = lines.get(n, ("", ""))
        # why: Python suppressions live in comments, shell ones in code.
        hit = pattern.search(comment if pattern is _PY_SUPPRESS_RE else code)
        if hit and not _has_why(lines, n):
            token = (
                "# " + hit.group(1).split()[0]
                if pattern is _PY_SUPPRESS_RE
                else hit.group(1)
            )
            message = f"suppression `{token}` without a `# why:` on this line or the comment above"
            findings.append((path, n, "WHY001", message))
    return findings


def check_todo(path: str, added: dict[int, str], text: str) -> list[Finding]:
    """TODO001: an added TODO/FIXME comment must cite an issue or ADR.

    Args:
        path: Repo-relative path of the file.
        added: The added lines, ``{lineno: text}``.
        text: The whole new-side file.

    Returns:
        One finding per added TODO/FIXME comment with no ``#N`` or ``ADR-NNNN``.
    """
    scanned = _scan(path, text)
    if scanned is None:
        return []
    lines = scanned[0]
    message = "TODO/FIXME without a reference: write TODO(#N) or TODO(ADR-NNNN)"
    return [
        (path, n, "TODO001", message)
        for n in sorted(added)
        if _TODO_RE.search(c := lines.get(n, ("", ""))[1])
        and not _TODO_REF_RE.search(c)
    ]


CHECKS: list[Check] = [check_why, check_todo]


def new_text(
    range_args: Sequence[str], path: str, cwd: str | os.PathLike | None = None
) -> str:
    """Return the new side of ``path``: the index for ``--cached``, else the to-commit.

    Args:
        range_args: What `resolve_range` returned.
        path: Repo-root-relative path, as `added_lines` reports it.
        cwd: Any directory inside the repo.

    Returns:
        The file text (undecodable bytes surrogate-escaped).
    """
    side = "" if list(range_args) == ["--cached"] else range_args[0].split("...")[1]
    top = _git_out(["rev-parse", "--show-toplevel"], cwd).strip()
    return _git_out(["show", f"{side}:{path}"], top)


def _printable(text: str) -> str:
    return _CONTROL_RE.sub(lambda m: f"\\x{ord(m.group()):02x}", text)


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
        range_args = resolve_range(from_ref, to_ref)
        touched = {
            path: (lines, new_text(range_args, path))
            for path, lines in added_lines(range_args, files=args.files or None).items()
        }
    except UsageError as exc:
        # why: a bad ref or empty diff is an expected usage error; one line, no traceback.
        log.error("check_conventions: %s", exc)  # noqa: TRY400
        return 2

    log.info("check_conventions: %d checks enabled", len(CHECKS))
    findings = [
        f
        for path, (lines, text) in touched.items()
        for check in CHECKS
        for f in check(path, lines, text)
    ]
    # why: git paths may carry undecodable bytes (surrogate-escaped) and control
    # characters; neither may reach the terminal raw.
    sys.stdout.reconfigure(errors="backslashreplace")  # type: ignore[union-attr]  # why: always a TextIOWrapper here
    for path, lineno, code, message in findings:
        print(f"{_printable(path)}:{lineno}: {code} {message}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
