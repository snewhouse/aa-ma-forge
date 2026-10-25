"""Run git from codemem: argv only, scrubbed environment, verified refs, NUL-split output.

Twin of ``aa_ma.gitutil`` (aa_ma never imports codemem, see .importlinter);
tests/test_gitutil_contract.py keeps the two in step, so edit both.

Rules every call follows:

- git runs as an argv list, never through a shell, in ``repo``.
- Every ``GIT_*`` variable is dropped from the child's environment (a stray
  ``GIT_DIR`` or ``GIT_INDEX_FILE`` would point the call at another repo), and
  ``LC_ALL=C`` makes messages and sort order locale-independent.
- Command-scope config disables ``core.fsmonitor`` and hooks, which a repo's
  own ``.git/config`` could otherwise make git run.
- ``--literal-pathspecs``: a path is itself, never a glob.
- Paths go only through ``paths=``, after ``--``; refs go through
  :func:`verify_ref`; ``-z`` output goes through :func:`split_z`.
- A non-zero exit, a timeout or a missing git raises :class:`GitError`.
"""

from __future__ import annotations

import os
import subprocess
from collections.abc import Sequence
from pathlib import Path

__all__ = ["DEFAULT_TIMEOUT_S", "GitError", "git", "split_z", "verify_ref"]

# Seconds per git call. Local plumbing takes milliseconds; a call still running
# after 10 s is wedged (a stuck index.lock, a hung mount), not slow.
DEFAULT_TIMEOUT_S = 10.0

# Command-scope config outranks the repo's .git/config, which can name programs
# git runs (codemem.safety.SAFE_GIT measured core.fsmonitor on ls-files/status).
_SAFE_PREFIX = (
    "git",
    "-c",
    "core.fsmonitor=false",
    "-c",
    "core.hooksPath=/dev/null",
    "--literal-pathspecs",
)


class GitError(RuntimeError):
    """git exited non-zero, timed out, or could not be started.

    Attributes:
        args_: The git arguments that failed (without the safety prefix).
        returncode: git's exit status; ``None`` when it timed out or never ran.
        stderr: git's stderr, decoded; empty when there was none.
    """

    def __init__(
        self, message: str, args_: Sequence[str], returncode: int | None, stderr: str
    ) -> None:
        """Build the error; ``message`` already carries the stderr text."""
        super().__init__(message)
        self.args_ = list(args_)
        self.returncode = returncode
        self.stderr = stderr


def _child_env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["LC_ALL"] = "C"
    return env


def git(
    args: list[str],
    repo: Path,
    timeout: float = DEFAULT_TIMEOUT_S,
    *,
    paths: Sequence[str] = (),
) -> str:
    """Run ``git <args> [-- <paths>]`` in ``repo`` and return its stdout.

    Args:
        args: git arguments as a list (a bare string is refused: it would
            iterate as characters).
        repo: Directory git runs in.
        timeout: Seconds before the call is killed.
        paths: Pathspecs, passed literally after ``--``.

    Returns:
        stdout decoded as UTF-8 (undecodable bytes kept via surrogateescape).

    Raises:
        TypeError: ``args`` or ``paths`` is a string.
        GitError: git exited non-zero, timed out, or is not installed.
    """
    if isinstance(args, str) or isinstance(paths, str):
        raise TypeError("git() takes argument lists, not a string")
    argv = [*_SAFE_PREFIX, *args]
    if paths:
        argv += ["--", *paths]
    try:
        proc = subprocess.run(  # noqa: S603  # why: fixed `git` argv, no shell; env scrubbed
            argv,
            cwd=repo,
            env=_child_env(),
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise GitError(
            f"git {_name(args)} timed out after {timeout:g}s", args, None, ""
        ) from exc
    except OSError as exc:
        raise GitError(
            f"git {_name(args)} could not start: {exc}", args, None, ""
        ) from exc
    # why: decode by hand, not text=True — universal newlines would turn a lone \r
    # in a path into a line break.
    stderr = proc.stderr.decode("utf-8", "surrogateescape")
    if proc.returncode != 0:
        raise GitError(
            f"git {_name(args)} failed (exit {proc.returncode}): {stderr.strip()}",
            args,
            proc.returncode,
            stderr,
        )
    return proc.stdout.decode("utf-8", "surrogateescape")


def _name(args: Sequence[str]) -> str:
    return next((a for a in args if not a.startswith("-")), "<no subcommand>")


def verify_ref(ref: str, repo: Path, timeout: float = DEFAULT_TIMEOUT_S) -> str:
    """Return the full sha of the commit ``ref`` names, or raise :class:`GitError`.

    ``--end-of-options`` stops a ref such as ``--output=x`` being read as an
    option, and ``^{commit}`` refuses trees, blobs and unknown names.
    """
    try:
        out = git(
            [
                "rev-parse",
                "--verify",
                "--quiet",
                "--end-of-options",
                f"{ref}^{{commit}}",
            ],
            repo,
            timeout,
        )
    except GitError as exc:
        raise GitError(
            f"not a commit: {ref!r}", exc.args_, exc.returncode, exc.stderr
        ) from exc
    return out.strip()


def split_z(out: str) -> list[str]:
    """Split NUL-terminated ``-z`` output into its fields; a trailing NUL is optional."""
    fields = out.split("\0")
    if fields and fields[-1] == "":
        fields.pop()
    return fields
