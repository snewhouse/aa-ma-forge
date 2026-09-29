"""Provenance stamp, SHA freshness, and the only safe way to create output directories.

Dirty = TRACKED changes only (`git status --porcelain --untracked-files=no`), so a freshly
written, untracked ONBOARDING.md never makes the run that wrote it stale. Every git call ends
its options with `--end-of-options` so no value can be read as a flag."""

from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess  # nosec B404 — git runs from an argv list, never a shell
from datetime import UTC, datetime
from pathlib import Path

from .models import HEX12, Stamp, Tier

REPORTS_ROOT = Path(".claude/reports/assess-codebase")
# The reports root's self-ignoring marker; the secret gate exempts exactly this file, byte for byte.
SELF_IGNORE_NAME, SELF_IGNORE_TEXT = ".gitignore", "*\n"
NOT_A_REPO = "not a git repo with ≥1 commit"
REPORT_NAME = re.compile(
    rf"[0-9a-f]{{{HEX12}}}(-dirty)?"
)  # what report_name() produces


class NotAGitRepo(Exception):
    pass


class UnsafePath(Exception):
    pass


class UnsafeRepo(Exception):
    """The target's own git config could make our git calls run commands."""


# Command-scope git config (GIT_CONFIG_COUNT) outranks the repo's .git/config: never run its
# fsmonitor or hooks, whatever the target ships.
GIT_OVERRIDES = (("core.fsmonitor", "false"), ("core.hooksPath", "/dev/null"))
# Local config keys that make git run a command or read another file; a target carrying any of
# them is refused rather than trusted (a clone never copies .git/config; a tarball can).
UNSAFE_GIT_CONFIG = r"^(include\.|includeif\.|filter\.|core\.fsmonitor$|core\.sshcommand$|diff\..*\.(command|textconv)$)"


def absolute_path(path: str) -> str:
    """PATH without `.`, empty or relative entries: resolved from inside the target, they would
    find a binary the target planted."""
    return os.pathsep.join(e for e in path.split(os.pathsep) if os.path.isabs(e))


def git_overrides() -> dict[str, str]:
    env = {"GIT_CONFIG_COUNT": str(len(GIT_OVERRIDES))}
    for i, (key, value) in enumerate(GIT_OVERRIDES):
        env |= {f"GIT_CONFIG_KEY_{i}": key, f"GIT_CONFIG_VALUE_{i}": value}
    return env


def safe_env() -> dict[str, str]:
    """This process's environment with an absolute-only PATH and git's command hooks disabled."""
    return (
        dict(os.environ)
        | {"PATH": absolute_path(os.environ.get("PATH", ""))}
        | git_overrides()
    )


def find_binary(name: str) -> str | None:
    """`<NAME>_BIN` if set (must be an executable file), else `name` on an absolute-only PATH."""
    override = os.environ.get(f"{name.upper().replace('-', '_')}_BIN")
    if override is None:
        return shutil.which(name, path=absolute_path(os.environ.get("PATH", "")))
    override = os.path.abspath(override)  # tools run from another cwd
    return (
        override if os.path.isfile(override) and os.access(override, os.X_OK) else None
    )


def read_regular(path: Path) -> str:
    """A regular file's text; never through a symlink, never blocking on a FIFO (OSError)."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, encoding="utf-8") as fh:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise OSError(f"{path}: not a regular file")
        return fh.read()


def contained(repo: Path, rel: str) -> bool:
    """Does repo/rel, symlinks resolved, stay inside the repo? (finalize; ground in M5)"""
    root = Path(repo).resolve()
    return (root / rel).resolve().is_relative_to(root)


def run_git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # nosec B603 B607 — fixed `git` argv; --end-of-options before user values
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
        env=safe_env(),
    )


def check_git_config(repo: Path) -> None:
    """Refuse a repo whose local git config can run commands (names the keys, never values)."""
    found = run_git(repo, "config", "--local", "--get-regexp", UNSAFE_GIT_CONFIG)
    if found.returncode == 0 and found.stdout.strip():
        keys = sorted(
            {
                line.split(maxsplit=1)[0]
                for line in found.stdout.splitlines()
                if line.strip()
            }
        )
        raise UnsafeRepo(
            f"{repo}: its .git/config can run commands ({', '.join(keys)}) — remove those keys or assess a fresh clone"
        )


def head_stamp(repo: Path) -> tuple[str, bool, str]:
    """(sha12, dirty, branch) for HEAD; branch is "(detached)" on a detached HEAD."""
    head = run_git(repo, "rev-parse", "--verify", "--end-of-options", "HEAD")
    if head.returncode != 0:
        raise NotAGitRepo(f"{repo}: {NOT_A_REPO}")
    status = run_git(
        repo, "status", "--porcelain", "--untracked-files=no", "--end-of-options"
    )
    if status.returncode != 0:
        raise NotAGitRepo(f"{repo}: git status failed: {status.stderr.strip()}")
    branch = run_git(repo, "symbolic-ref", "--short", "-q", "--end-of-options", "HEAD")
    return (
        head.stdout.strip()[:HEX12],
        bool(status.stdout.strip()),
        branch.stdout.strip() or "(detached)",
    )


def build_stamp(repo: Path, tier: Tier) -> Stamp:
    sha12, dirty, branch = head_stamp(repo)
    return Stamp(
        date_utc=datetime.now(UTC).replace(microsecond=0),
        sha12=sha12,
        dirty=dirty,
        branch=branch,
        tier=tier,
        tools={},
        absorbed=[],
        fresh_run=[],
    )


def is_fresh(s: Stamp, repo: Path) -> bool:
    sha12, dirty, _ = head_stamp(repo)
    return s.sha12 == sha12 and not s.dirty and not dirty


def report_name(sha12: str, dirty: bool) -> str:
    """The one naming rule for a report dir: `<sha12>` or `<sha12>-dirty`."""
    return f"{sha12}-dirty" if dirty else sha12


def report_dir(repo: Path) -> Path:
    sha12, dirty, _ = head_stamp(repo)
    return Path(repo) / REPORTS_ROOT / report_name(sha12, dirty)


def safe_dir(repo: Path, rel: str) -> Path:
    """Create repo/rel one component at a time, refusing any component that is a symlink, is not a
    directory, or would leave the repo. Nothing is ever written through a symlink."""
    rel_path = Path(rel)
    if rel_path.is_absolute() or ".." in rel_path.parts:
        raise UnsafePath(f"{rel}: must be a relative path inside the repo")
    current = Path(repo).absolute()
    for part in rel_path.parts:
        current = current / part
        try:
            mode = os.lstat(current).st_mode
        except FileNotFoundError:
            current.mkdir()
            continue
        if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
            raise UnsafePath(
                f"{current}: refusing a symlink or non-directory path component"
            )
    return current


def ensure_self_ignoring(root: Path) -> None:
    """root/.gitignore = "*" so everything under the reports root stays out of `git status`."""
    gitignore = root / SELF_IGNORE_NAME
    if gitignore.is_symlink():
        raise UnsafePath(f"{gitignore}: refusing a symlinked .gitignore")
    fd = os.open(
        gitignore, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o644
    )
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(SELF_IGNORE_TEXT)
