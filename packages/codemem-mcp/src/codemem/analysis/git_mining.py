"""Git mining base layer (M3 Task 3.1).

Provides a single ``GitMiner`` class that wraps the two ``git`` subprocess
calls every M3 feature needs:

* ``git log --name-status -M --pretty=format:<sentinel-fenced>`` — populates
  the ``commits`` + ``commit_files`` tables (used by :mod:`codemem.analysis`
  downstream: ``hot_spots``, ``co_changes``, ``symbol_history``). Renames
  are followed: every path is stored under its name at HEAD, so co-change
  history survives a ``git mv``; a path whose newest change is a delete
  (absent at HEAD) is dropped, so it is never reported as a partner.
* ``git blame --line-porcelain`` — per-file author attribution for the
  ``owners`` tool (cached in the ``ownership`` table).

Security contract (per ``codemem-reference.md`` §Input Sanitization):

* Every subprocess call uses ``shell=False`` — no shell interpretation,
  no injection path via the shell.
* ``git log`` path-filter args pass through ``--`` before user input so
  git cannot interpret them as flags.
* File-path args are validated by :func:`codemem.mcp_tools.sanitizers.sanitize_path_arg`
  BEFORE the subprocess argv is built — adversarial strings like
  ``"$(rm -rf /tmp)"`` never reach git at all.

Cache-cap policy: ``refresh_commits_cache(limit=N)`` keeps the N most
recent commits (by ``author_time``) and relies on the ``commit_files``
``ON DELETE CASCADE`` to purge junction rows when a commit is evicted.
"""

from __future__ import annotations

import json
import re
import sqlite3
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from codemem.mcp_tools.sanitizers import sanitize_path_arg


__all__ = ["GitMiner"]


# A fence token that can never appear inside a commit subject line because
# it contains an ASCII record-separator (U+001E). ``git log --pretty=format:``
# does not escape this for us.
_COMMIT_FIELD_SEP = "\x1f"  # unit separator between fields
_COMMIT_RECORD_SEP = "\x1e"  # record separator between commits


# `git log --pretty=format:` fields: sha | unix-timestamp | author-email | subject.
# The record separator goes at the FRONT of each record so when we combine
# with `--name-only`, every commit's file list trails cleanly inside its
# own block. A trailing RS would push each commit's files into the next
# block (fencepost bug).
_PRETTY_FORMAT = f"{_COMMIT_RECORD_SEP}%H{_COMMIT_FIELD_SEP}%at{_COMMIT_FIELD_SEP}%ae{_COMMIT_FIELD_SEP}%s"


@dataclass(frozen=True)
class _CommitRecord:
    sha: str
    author_time: int
    author_email: str
    message: str
    files: tuple[str, ...]


@dataclass
class _History:
    """Commits read in one batch, newest first, with paths as named at HEAD.

    ``renames`` maps each path renamed in the batch to its name at HEAD;
    ``deleted`` holds paths whose newest change in the batch is a delete.
    Both are applied to rows cached by earlier refreshes too. ``seen`` is
    the parse state: paths already met in a newer commit.
    """

    records: list[_CommitRecord] = field(default_factory=list)
    renames: dict[str, str] = field(default_factory=dict)
    deleted: set[str] = field(default_factory=set)
    seen: set[str] = field(default_factory=set)


class GitMiner:
    """Thin, read-only git wrapper feeding the v2 schema.

    Thread-unsafe by design — SQLite's single-writer model already serialises
    callers. Construct one per operation; each ``refresh_commits_cache``
    call is a single transaction.
    """

    def __init__(self, *, repo_root: Path) -> None:
        self.repo_root = Path(repo_root).resolve()

    # -----------------------------------------------------------------
    # Subprocess primitives
    # -----------------------------------------------------------------

    def _git(
        self,
        args: list[str],
        *,
        timeout: float | None = 30.0,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """Run ``git`` with ``shell=False`` inside the repo root.

        The first argv entry is literally ``"git"``; ``-C <repo_root>``
        pins the working directory so the caller cannot influence it via
        env or cwd mutation.
        """
        cmd = ["git", "-C", str(self.repo_root), *args]
        return subprocess.run(  # noqa: S603  # why: argv[0] is literally `git`, -C pins repo_root; shell=False
            cmd,
            shell=False,
            check=check,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    # -----------------------------------------------------------------
    # Commits cache refresh
    # -----------------------------------------------------------------

    def refresh_commits_cache(
        self,
        conn: sqlite3.Connection,
        *,
        limit: int = 500,
    ) -> int:
        """Populate ``commits`` + ``commit_files`` from ``git log``.

        * Uses incremental ``git log <last_cached_sha>..HEAD`` when the
          cache already has rows AND the newest cached sha is still an
          ancestor of HEAD. Otherwise falls back to full ``git log -n <limit>``.
        * After insertion, trims the cache to ``limit`` rows (newest by
          ``author_time``). Junction rows cascade-delete automatically.

        Returns the number of commits inserted by this call.
        """
        # Choose full vs. incremental mode.  We identify the "last cached sha"
        # by walking git's own topo-ordered log and picking the first sha
        # already present in our cache.  This is robust when multiple cached
        # commits share an identical author_time (SQLite's ORDER BY tiebreak
        # is undefined), and it naturally detects rebased history: if none of
        # the cached shas appear in HEAD's lineage, we fall back to full.
        last_sha = self._last_cached_sha_in_head_lineage(conn, limit=limit)
        if last_sha is not None:
            range_expr = f"{last_sha}..HEAD"
            full_refresh = False
        else:
            range_expr = None
            full_refresh = True

        history = self._read_commits(range_expr=range_expr, limit=limit)
        records = history.records
        if not records:
            return 0

        with conn:  # atomic insert + trim
            # Upsert commits; junction rows use INSERT OR IGNORE since the
            # PK (commit_sha, file_path) makes duplicates harmless.
            conn.executemany(
                "INSERT OR REPLACE INTO commits "
                "(sha, author_email, author_time, message) VALUES (?, ?, ?, ?)",
                [(r.sha, r.author_email, r.author_time, r.message) for r in records],
            )
            junction_rows = [(r.sha, fp) for r in records for fp in r.files]
            if junction_rows:
                conn.executemany(
                    "INSERT OR IGNORE INTO commit_files "
                    "(commit_sha, file_path) VALUES (?, ?)",
                    junction_rows,
                )
            _apply_moves_to_cached_rows(conn, history)
            # Enforce cap. Full-refresh respects limit directly; incremental
            # also trims so a repo that outgrew the cap gets pruned.
            conn.execute(
                "DELETE FROM commits WHERE sha NOT IN "
                "(SELECT sha FROM commits ORDER BY author_time DESC LIMIT ?)",
                (limit,),
            )

        return len(records) if full_refresh else len(records)

    def _last_cached_sha_in_head_lineage(
        self,
        conn: sqlite3.Connection,
        *,
        limit: int,
    ) -> str | None:
        """Return the newest cached sha that appears in HEAD's ancestry.

        Walks ``git log -n<limit> HEAD`` in topo order; returns the first
        sha also present in the ``commits`` table. ``None`` if cache is
        empty, or if history has been rebased so no cached sha is still
        reachable from HEAD (forces full refresh).
        """
        cur = conn.execute("SELECT sha FROM commits")
        cached = {row[0] for row in cur.fetchall()}
        if not cached:
            return None
        proc = self._git(
            ["log", f"-n{limit}", "--pretty=format:%H", "HEAD", "--"],
            check=False,
            timeout=5.0,
        )
        if proc.returncode != 0:
            return None
        for sha in proc.stdout.splitlines():
            if sha in cached:
                return sha
        return None

    def _read_commits(
        self,
        *,
        range_expr: str | None,
        limit: int,
    ) -> _History:
        args = [
            "log",
            f"-n{limit}",
            f"--pretty=format:{_PRETTY_FORMAT}",
            "--name-status",
            "-M",  # follow renames, so history is stored under the HEAD name
        ]
        if range_expr is not None:
            args.append(range_expr)
        # `--` separator: no path filters, but the presence of `--` ensures
        # git treats subsequent tokens as pathspecs if any future call adds them.
        args.append("--")
        proc = self._git(args, timeout=30.0)
        return _parse_git_log_output(proc.stdout)

    # -----------------------------------------------------------------
    # Blame / ownership
    # -----------------------------------------------------------------

    def get_blame(
        self,
        file_path: str,
        *,
        timeout: float = 2.0,
    ) -> dict[str, tuple[int, float]]:
        """Return ``{author_email: (line_count, percentage)}`` for a file.

        Returns an empty dict if the file is unknown to git. 2-second default
        timeout matches Task 3.4's per-file policy.
        """
        sanitized = sanitize_path_arg(file_path, self.repo_root)
        rel = sanitized.relative_to(self.repo_root).as_posix()
        proc = self._git(
            ["blame", "--line-porcelain", "--", rel],
            check=False,
            timeout=timeout,
        )
        if proc.returncode != 0:
            # git emits non-zero for unknown files / binary files / not-in-HEAD.
            return {}
        return _parse_blame_porcelain(proc.stdout)


# ---------------------------------------------------------------------------
# Parsers (pure; tested indirectly + can be unit-tested directly)
# ---------------------------------------------------------------------------


def _parse_git_log_output(stdout: str) -> _History:
    r"""Parse fence-delimited ``git log --pretty=format:<_PRETTY_FORMAT> --name-status -M`` output.

    Layout: each commit is ``<RS>sha<US>time<US>email<US>subject\n`` then one
    ``STATUS\tpath`` line per file (``R<score>\told\tnew`` for a rename).
    git lists commits newest first, so a rename is seen before the older
    commits that use the old name, and a path's first status is its newest.
    """
    history = _History()
    if not stdout:
        return history
    for block in stdout.split(_COMMIT_RECORD_SEP):
        block = block.strip()
        if not block:
            continue
        head, _, files_blob = block.partition("\n")
        fields = head.split(_COMMIT_FIELD_SEP)
        if len(fields) != 4:
            # Malformed — skip defensively rather than raise.
            continue
        sha, at, ae, subject = fields
        try:
            author_time = int(at)
        except ValueError:
            continue
        history.records.append(
            _CommitRecord(
                sha=sha,
                author_time=author_time,
                author_email=ae,
                message=subject,
                files=_walk_files(files_blob, history),
            )
        )
    return history


def _walk_files(files_blob: str, history: _History) -> tuple[str, ...]:
    """One commit's paths as named at HEAD; records its renames and deletes.

    Deleted-at-HEAD paths are left out; only a path's newest status counts.
    """
    seen = history.seen
    files: dict[str, None] = {}
    for line in files_blob.splitlines():
        status, _, rest = line.strip().partition("\t")
        if not rest:
            continue
        paths = rest.split("\t")
        path = paths[-1]
        current = history.renames.get(path, path)
        if path not in seen:
            seen.add(path)
            if status == "D":
                history.deleted.add(path)
        if status.startswith("R") and len(paths) == 2:
            history.renames[paths[0]] = current
        if current not in history.deleted:
            files[current] = None
    return tuple(files)


def _apply_moves_to_cached_rows(conn: sqlite3.Connection, history: _History) -> None:
    """Carry this batch's renames and deletes onto rows from earlier refreshes.

    Rows of this batch already use HEAD names; only older commits are moved.
    A row whose new name already exists for that commit is a duplicate and
    is dropped.
    """
    batch = json.dumps([r.sha for r in history.records])
    older = "commit_sha NOT IN (SELECT value FROM json_each(?))"
    for old, new in history.renames.items():
        conn.execute(
            f"UPDATE OR IGNORE commit_files SET file_path = ? WHERE file_path = ? AND {older}",  # noqa: S608  # why: `older` is a literal with a `?`; values are bound
            (new, old, batch),
        )
        conn.execute(
            f"DELETE FROM commit_files WHERE file_path = ? AND {older}",  # noqa: S608  # why: `older` is a literal with a `?`; values are bound
            (old, batch),
        )
    conn.executemany(
        "DELETE FROM commit_files WHERE file_path = ?",
        [(p,) for p in sorted(history.deleted)],
    )


_BLAME_AUTHOR_MAIL_RE = re.compile(r"^author-mail <([^>]+)>")


def _parse_blame_porcelain(stdout: str) -> dict[str, tuple[int, float]]:
    """Extract per-author line counts + percentages from ``--line-porcelain`` output.

    Porcelain format: each content line is preceded by a metadata block that
    begins with ``<sha> <orig-line> <final-line>`` and continues with
    header lines (author, author-mail, committer, ...). Lines NOT starting
    with a 40-hex prefix or a known header key are content lines — we
    attribute each content line to the most-recent ``author-mail``.
    """
    counts: dict[str, int] = {}
    total = 0
    current_email: str | None = None

    for line in stdout.splitlines():
        m = _BLAME_AUTHOR_MAIL_RE.match(line)
        if m:
            current_email = m.group(1)
            continue
        if line.startswith("\t"):
            # Content line. git prefixes it with a single TAB in porcelain.
            if current_email is None:
                continue
            counts[current_email] = counts.get(current_email, 0) + 1
            total += 1

    if total == 0:
        return {}
    return {email: (n, (n / total) * 100.0) for email, n in counts.items()}
