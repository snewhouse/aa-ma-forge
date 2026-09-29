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
from typing import BinaryIO

from .models import HEX12, Stamp, Tier

REPORTS_ROOT = Path(".claude/reports/assess-codebase")
# The reports root's self-ignoring marker; the secret gate exempts exactly this file, byte for byte.
SELF_IGNORE_NAME, SELF_IGNORE_TEXT = ".gitignore", "*\n"
NOT_A_REPO = "not a git repo with ≥1 commit"
# What report_name() produces.
REPORT_NAME = re.compile(rf"[0-9a-f]{{{HEX12}}}(-dirty)?")


class NotAGitRepo(Exception):
    pass


class UnsafePath(Exception):
    pass


class UnsafeRepo(Exception):
    """The target's own git config could make our git calls run commands."""


# Command-scope git config (GIT_CONFIG_COUNT) outranks the repo's .git/config: never run its
# fsmonitor or hooks, whatever the target ships.
GIT_OVERRIDES = (
    ("core.fsmonitor", "false"),
    ("core.hooksPath", "/dev/null"),
    ("log.showSignature", "false"),
    ("core.quotePath", "false"),  # non-ASCII paths as-is, not C-quoted
)
# The only keys a target's own config (local, worktree or a submodule's) may hold: what a clone
# and a user identity write. Anything else refuses the target — four review rounds each found a
# key that runs a command (fsmonitor, filter, gpg.program, …); an allowlist cannot miss one.
SAFE_GIT_CONFIG = re.compile(
    r"core\.(repositoryformatversion|filemode|bare|logallrefupdates|ignorecase"
    r"|precomposeunicode|symlinks|autocrlf|eol|safecrlf|quotepath)"
    r"|extensions\.(objectformat|refstorage|worktreeconfig|relativeworktrees)"
    r"|remote\..+\.(url|pushurl|fetch|tagopt|prune|mirror)"
    r"|branch\..+\.(remote|merge|rebase|pushremote|description|vscode-merge-base)"
    r"|submodule\..+\.(url|active)"
    r"|lfs\.repositoryformatversion"
    r"|user\.(name|email)|init\.defaultbranch|pull\.rebase|push\.default|fetch\.prune"
)
TARGET_SCOPES = {"local", "worktree"}
# git writes core.worktree into every submodule's own config; in the target's local config it
# stays refused.
SUBMODULE_KEYS = {"core.worktree"}
# A git call on the target that has not finished by now is refused (a FIFO in its config blocks).
GIT_TIMEOUT_S = 300
# Only the target's own config is read: the user's global and system config may define filters
# (git-lfs) that the target's .gitattributes could select.
ISOLATED_CONFIG = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}


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
        | ISOLATED_CONFIG
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


def open_regular(path: Path, identity: tuple[int, int] | None = None) -> BinaryIO:
    """A regular file opened for reading; never through a symlink as its last component, never
    blocking on a FIFO. With `identity` (st_dev, st_ino from a listing) the opened file must be
    that one: a parent dir swapped for a symlink since the listing opens another (OSError)."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    fh = os.fdopen(fd, "rb")
    st = os.fstat(fd)
    if not stat.S_ISREG(st.st_mode) or identity not in (None, (st.st_dev, st.st_ino)):
        fh.close()
        raise OSError(f"{path}: not the regular file that was listed")
    return fh


def read_regular(
    path: Path, identity: tuple[int, int] | None = None, limit: int | None = None
) -> str:
    """A regular file's text (see open_regular); more than `limit` bytes is an OSError."""
    with open_regular(path, identity) as fh:
        data = fh.read(-1 if limit is None else limit + 1)
    if limit is not None and len(data) > limit:
        raise OSError(f"{path}: larger than {limit} bytes")
    return data.decode("utf-8")


def contained(repo: Path, rel: str) -> bool:
    """Does repo/rel, symlinks resolved, stay inside the repo? (finalize; ground in M5)"""
    root = Path(repo).resolve()
    return (root / rel).resolve().is_relative_to(root)


def run_git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(  # nosec B603 B607 — fixed `git` argv; --end-of-options before user values
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            check=False,
            env=safe_env(),
            timeout=GIT_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        raise UnsafeRepo(
            f"{repo}: git did not finish within {GIT_TIMEOUT_S}s — assess a fresh clone"
        ) from None


def _inside(root: str, path: str) -> bool:
    return path == root or path.startswith(root + os.sep)


# A worktree's `gitdir` back-reference is one short path.
BACKREF_MAX_BYTES = 4096


def _is_worktree_of(root: str, git_dir: str, common: str) -> bool:
    """Is git_dir a linked-worktree git dir (`<common>/worktrees/<name>`) whose `gitdir` file
    names `<root>/.git` back? Relative back-references (`--relative-paths`) resolve against
    git_dir. A hostile repo cannot write into another repo's `worktrees/`."""
    if _inside(root, git_dir) or os.path.dirname(git_dir) != os.path.join(
        common, "worktrees"
    ):
        return False
    try:
        back = read_regular(Path(git_dir) / "gitdir", limit=BACKREF_MAX_BYTES).strip()
    except (OSError, UnicodeDecodeError):
        return False
    return bool(back) and os.path.realpath(os.path.join(git_dir, back)) == os.path.join(
        root, ".git"
    )


def _check_git_dir(repo: Path) -> Path:
    """The git dir and common dir must be the repo's own: a `.git` file or `commondir` naming
    another repo would have us mine its history. A linked worktree of the user's repo is the
    one exception, proved by its git dir's `gitdir` file naming this worktree back."""
    out = run_git(
        repo,
        "rev-parse",
        "--path-format=absolute",
        "--git-dir",
        "--git-common-dir",
        "--end-of-options",
    )
    lines = out.stdout.splitlines()  # rev-parse echoes --end-of-options as a last line
    if out.returncode != 0 or len(lines) < 2:
        raise UnsafeRepo(f"{repo}: cannot resolve its git dir — assess a fresh clone")
    root = os.path.realpath(repo)
    git_dir, common = (os.path.realpath(p) for p in lines[:2])
    if (_inside(root, git_dir) and _inside(root, common)) or _is_worktree_of(
        root, git_dir, common
    ):
        return Path(common)
    raise UnsafeRepo(f"{repo}: its git dir is outside the repo — assess a fresh clone")


def _config_keys(repo: Path, *args: str) -> list[str]:
    """Keys from `git config --list -z` (`[scope\\0]key\\nvalue\\0` entries); values never kept."""
    listed = run_git(repo, "config", *args, "--list", "-z", "--end-of-options")
    if listed.returncode != 0:
        raise UnsafeRepo(f"{repo}: cannot read its git config — assess a fresh clone")
    return [e.split("\n", 1)[0] for e in listed.stdout.split("\0") if e]


def _key_class(key: str) -> str:
    section, _, rest = key.partition(".")
    return f"{section}.*.{rest.rsplit('.', 1)[1]}" if "." in rest else key


def check_git_config(repo: Path) -> None:
    """Refuse a repo whose own git config — local, worktree or any submodule's — holds a key
    outside SAFE_GIT_CONFIG (names the keys, never values)."""
    common_dir = _check_git_dir(repo)
    entries = _config_keys(repo, "--show-scope")
    found = {
        k for scope, k in zip(entries[::2], entries[1::2]) if scope in TARGET_SCOPES
    }
    for module in common_dir.glob("modules/**/config"):
        found |= set(_config_keys(repo, "--file", str(module))) - SUBMODULE_KEYS
    # Named by section and variable only: a subsection can hold a credential (url.<base>.insteadOf).
    unsafe = sorted({_key_class(k) for k in found if not SAFE_GIT_CONFIG.fullmatch(k)})
    if unsafe:
        raise UnsafeRepo(
            f"{repo}: its git config sets keys outside the safe list ({', '.join(unsafe)})"
            " — remove them or assess a fresh clone"
        )


def head_stamp(repo: Path) -> tuple[str, bool, str]:
    """(sha12, dirty, branch) for HEAD; branch is "(detached)" on a detached HEAD."""
    head = run_git(repo, "rev-parse", "--verify", "--end-of-options", "HEAD")
    if head.returncode != 0:
        raise NotAGitRepo(f"{repo}: {NOT_A_REPO}")
    check_git_config(repo)  # before `status`, which runs the filters a config names
    status = run_git(
        repo,
        "status",
        "--porcelain",
        "--untracked-files=no",
        "--ignore-submodules=all",
        "--end-of-options",
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
