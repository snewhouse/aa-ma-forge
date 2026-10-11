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
from typing import NamedTuple

log = logging.getLogger(__name__)

Finding = tuple[str, int, str, str]
# A check gets (path, {lineno: added text}, whole new-side file text).
Check = Callable[[str, dict[int, str], str], list[Finding]]

_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
_SHEBANG_SH_RE = re.compile(r"^#!.*\b(?:ba|da|k|z)?sh\b")
_PY_SUPPRESS_RE = re.compile(
    r"#\s*(?:(?:ruff|flake8):\s*)?(?:noqa|type:\s*ignore|pyright:\s*ignore|nosec)\b",
    re.IGNORECASE,
)
_SH_SUPPRESS_RE = re.compile(
    r"\|\|\s*(?:true|:)(?![\w-])|(?:2|&)>\s*/dev/null|>\s*/dev/null\s+2>&1"
)
_WHY_RE = re.compile(r"#\s*why:")
# why: a tag right after `#`, as ruff TD reads it — "the TODO below" is prose.
_TODO_RE = re.compile(r"#\s*(?:TODO|FIXME)\b", re.IGNORECASE)
_TODO_REF_RE = re.compile(r"(?<![\w#])(?:#\d+|ADR-\d{4})(?!\w)")
_HEREDOC_RE = re.compile(r"<<(-?)\s*\\?(['\"]?)([A-Za-z_][^\s'\"<>;&|()]*)\2")
_HEREDOC_OP_RE = re.compile(r"(?<!<)<<(?!<)")  # a heredoc's <<, not a <<< here-string
_PY_SUFFIXES = (".py", ".pyi")
_SH_SUFFIXES = (".sh", ".bash")
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
# Each language reduces a file to {lineno: (code, comment)}. Strings, docstrings,
# heredoc bodies and Markdown never reach a check (T8). For shell, code is the line
# with quoted text blanked; for Python it is the text before the comment, unblanked,
# because Python suppressions are read from comment tokens only.


class _Lang(NamedTuple):
    lines: dict[int, tuple[str, str]]
    suppress: re.Pattern
    in_comment: bool  # Python suppressions live in comments, shell ones in code


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
        log.warning(
            "check_conventions: %s: not tokenizable, skipped: %s",
            _printable(path),
            _printable(str(exc)),
        )
        return {}
    return lines


# Shell contexts on a stack that persists across lines: "'" and "$'" and '"' are
# quotes (text blanked); "$(", "(", "`" are code again, even inside "..."; "((" is
# arithmetic, where `<<` is a shift, not a heredoc. Each step returns
# (chars consumed, replacement of the same length) so code stays index-aligned with
# the raw line, from which heredoc delimiters are read back.
# (opener, context, closer); longest opener first, so `$((` wins over `$(` and `(`.
_CONTEXTS = (
    ("$((", "((", "))"),
    ("((", "((", "))"),
    ("$(", "$(", ")"),
    ("$'", "$'", "'"),
    ("(", "(", ")"),
    ("`", "`", "`"),
    ("'", "'", "'"),
    ('"', '"', '"'),
)
_CLOSERS = {ctx: closer for _, ctx, closer in _CONTEXTS}
_QUOTES = ("'", "$'", '"')


def _step_quoted(line: str, i: int, stack: list[str]) -> tuple[int, str]:
    top, c = stack[-1], line[i]
    if c == "\\" and top != "'":
        n = len(line[i : i + 2])
        return n, " " * n
    if line.startswith(_CLOSERS[top], i):
        stack.pop()
        return 1, c
    if top == '"' and (line.startswith("$(", i) or c == "`"):
        return _step_code(line, i, stack)
    return 1, " "


def _in_arithmetic(stack: list[str]) -> bool:
    # why: O(1), not `"((" in stack` — an unclosed `$(` run must not make each `<`
    # cost the stack depth (§6.8 security). Misses only `$(( (a << b) ))`.
    return bool(stack) and (
        stack[-1] == "((" or (stack[-1] == "(" and len(stack) > 1 and stack[-2] == "((")
    )


def _step_code(line: str, i: int, stack: list[str]) -> tuple[int, str]:
    c = line[i]
    if c == "\\":
        return len(line[i : i + 2]), line[i : i + 2]
    if c == "<" and _in_arithmetic(stack):
        return 1, " "
    if stack and line.startswith(_CLOSERS[stack[-1]], i):
        closer = _CLOSERS[stack.pop()]
        return len(closer), closer
    for opener, ctx, _ in _CONTEXTS:
        if line.startswith(opener, i):
            stack.append(ctx)
            return len(opener), opener
    return 1, c


def _shell_code_comment(line: str, stack: list[str]) -> tuple[str, str]:
    """Split one shell line into (code with quoted text blanked, comment)."""
    code: list[str] = []
    i = 0
    while i < len(line):
        if not stack and line[i] == "#" and (i == 0 or line[i - 1] in " \t;|&("):
            return "".join(code), line[i:]
        quoted = stack and stack[-1] in _QUOTES
        n, out = (_step_quoted if quoted else _step_code)(line, i, stack)
        code.append(out)
        i += n
    return "".join(code), ""


def _shell_lines(path: str, text: str) -> dict[int, tuple[str, str]]:
    lines: dict[int, tuple[str, str]] = {}
    stack: list[str] = []
    heredocs: list[tuple[bool, str]] = []  # (strip leading tabs, delimiter), in order
    for n, line in enumerate(text.splitlines(), start=1):
        if heredocs:
            strip_tabs, delim = heredocs[0]
            if (line.lstrip("\t") if strip_tabs else line) == delim:
                heredocs.pop(0)
            lines[n] = ("", "")
            continue
        code, comment = _shell_code_comment(line, stack)
        for m in _HEREDOC_OP_RE.finditer(code):
            here = _HEREDOC_RE.match(line, m.start())
            if here:
                heredocs.append((here.group(1) == "-", here.group(3)))
        lines[n] = (code, comment)
    if stack or heredocs:
        # why: an unclosed quote or heredoc hides every later line from the checks;
        # say so rather than report a clean file (no silent fail-open, L-1319).
        log.warning(
            "check_conventions: %s: shell context unbalanced at end of file; "
            "later lines may be unchecked",
            _printable(path),
        )
    return lines


def _scannable(path: str) -> bool:
    # why: shell is recognised by suffix, or by shebang only when there is no suffix,
    # so a .md/.json/.bats file is never read at all (.bats is not plain shell, as the
    # shellcheck hook, ADR-0018).
    return path.endswith(_PY_SUFFIXES + _SH_SUFFIXES) or "." not in os.path.basename(
        path
    )


def _scan(path: str, text: str) -> _Lang | None:
    """Return the file's scanned lines and suppression rule, or None if not scanned."""
    if path.endswith(_PY_SUFFIXES):
        return _Lang(_python_lines(path, text), _PY_SUPPRESS_RE, in_comment=True)
    if not _scannable(path):
        return None
    if path.endswith(_SH_SUFFIXES) or _SHEBANG_SH_RE.match(text):
        return _Lang(_shell_lines(path, text), _SH_SUPPRESS_RE, in_comment=False)
    return None


def _why_covered(lines: dict[int, tuple[str, str]]) -> set[int]:
    """Lines with a `# why:` on them or anywhere in the comment block directly above."""
    # why: one forward pass; walking back per line was O(n²) on a long comment block,
    # which a PR could use to hang CI (§6.8 security).
    covered: set[int] = set()
    block_has_why = False
    for n in sorted(lines):
        code, comment = lines[n]
        why = bool(_WHY_RE.search(comment))
        if why or block_has_why:
            covered.add(n)
        comment_only = bool(comment) and not code.strip()
        block_has_why = (block_has_why or why) if comment_only else False
    return covered


def check_why(path: str, added: dict[int, str], text: str) -> list[Finding]:
    """WHY001: an added suppression needs a `# why:` on its line or the comment above.

    Args:
        path: Repo-relative path of the file.
        added: The added lines, ``{lineno: text}``.
        text: The whole new-side file.

    Returns:
        One finding per added line that suppresses without a reason.
    """
    lang = _scan(path, text)
    if lang is None:
        return []
    findings = []
    covered = _why_covered(lang.lines)
    for n in sorted(added):
        code, comment = lang.lines.get(n, ("", ""))
        hit = lang.suppress.search(comment if lang.in_comment else code)
        if hit and n not in covered:
            token = " ".join(hit.group().split())
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
    lang = _scan(path, text)
    if lang is None:
        return []
    lines = lang.lines
    message = "TODO/FIXME without a reference: write TODO(#N) or TODO(ADR-NNNN)"
    return [
        (path, n, "TODO001", message)
        for n in sorted(added)
        if _TODO_RE.search(c := lines.get(n, ("", ""))[1])
        and not _TODO_REF_RE.search(c)
    ]


CHECKS: list[Check] = [check_why, check_todo]


def new_text(range_args: Sequence[str], path: str, top: str) -> str:
    """Return the new side of ``path``: the index for ``--cached``, else the to-commit.

    Args:
        range_args: What `resolve_range` returned.
        path: Repo-root-relative path, as `added_lines` reports it.
        top: The repository's top-level directory.

    Returns:
        The file text (undecodable bytes surrogate-escaped).
    """
    # why: `:0:` names stage 0 explicitly, so a staged `1:x.py` is not read as stage 1.
    side = ":0" if list(range_args) == ["--cached"] else range_args[0].split("...")[1]
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
        top = _git_out(["rev-parse", "--show-toplevel"], None).strip()
        touched = {
            path: (
                lines,
                new_text(range_args, path, top) if lines and _scannable(path) else "",
            )
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
        shown = _printable(path)
        # why: a line starting `::` is a GitHub workflow command (fake annotations).
        shown = f"./{shown}" if shown.startswith("::") else shown
        print(f"{shown}:{lineno}: {code} {message}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
