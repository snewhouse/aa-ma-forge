"""Provenance stamp, SHA freshness, and the only safe way to create output directories.

Dirty = TRACKED changes only (`git status --porcelain --untracked-files=no`), so a freshly
written, untracked ONBOARDING.md never makes the run that wrote it stale. Every git call ends
its options with `--end-of-options` so no value can be read as a flag."""

from __future__ import annotations

import os
import stat
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from .models import Stamp, ToolStatus

REPORTS_ROOT = Path(".claude/reports/assess-codebase")
NOT_A_REPO = "not a git repo with ≥1 commit"


class NotAGitRepo(Exception):
    pass


class UnsafePath(Exception):
    pass


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
    )


def head_stamp(repo: Path) -> tuple[str, bool, str]:
    """(sha12, dirty, branch) for HEAD; branch is "(detached)" on a detached HEAD."""
    head = _git(repo, "rev-parse", "--verify", "--end-of-options", "HEAD")
    if head.returncode != 0:
        raise NotAGitRepo(f"{repo}: {NOT_A_REPO}")
    status = _git(
        repo, "status", "--porcelain", "--untracked-files=no", "--end-of-options"
    )
    if status.returncode != 0:
        raise NotAGitRepo(f"{repo}: git status failed: {status.stderr.strip()}")
    branch = _git(repo, "symbolic-ref", "--short", "-q", "--end-of-options", "HEAD")
    return (
        head.stdout.strip()[:12],
        bool(status.stdout.strip()),
        branch.stdout.strip() or "(detached)",
    )


def build_stamp(
    repo: Path,
    tier: str,
    tools: dict[str, ToolStatus] | None = None,
    absorbed: list[str] | None = None,
    fresh_run: list[str] | None = None,
) -> Stamp:
    sha12, dirty, branch = head_stamp(repo)
    return Stamp(
        date_utc=datetime.now(UTC).replace(microsecond=0),
        sha12=sha12,
        dirty=dirty,
        branch=branch,
        tier=tier,  # type: ignore[arg-type]  # validated by the model
        tools=tools or {},
        absorbed=absorbed or [],
        fresh_run=fresh_run or [],
    )


def is_fresh(s: Stamp, repo: Path) -> bool:
    sha12, dirty, _ = head_stamp(repo)
    return s.sha12 == sha12 and not s.dirty and not dirty


def report_dir(repo: Path) -> Path:
    sha12, dirty, _ = head_stamp(repo)
    return Path(repo) / REPORTS_ROOT / (f"{sha12}-dirty" if dirty else sha12)


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
    gitignore = root / ".gitignore"
    if gitignore.is_symlink():
        raise UnsafePath(f"{gitignore}: refusing a symlinked .gitignore")
    fd = os.open(
        gitignore, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o644
    )
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write("*\n")
