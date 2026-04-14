"""Git mining base layer (M3 Task 3.1).

Provides a single ``GitMiner`` class that wraps the two ``git`` subprocess
calls every M3 feature needs:

* ``git log --name-only --pretty=format:<sentinel-fenced>`` — populates the
  ``commits`` + ``commit_files`` tables (used by :mod:`codemem.analysis`
  downstream: ``hot_spots``, ``co_changes``, ``symbol_history``).
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

import re
import sqlite3
import subprocess
from dataclasses import dataclass
from pathlib import Path

from codemem.mcp_tools.sanitizers import sanitize_path_arg


__all__ = ["GitMiner"]


# A fence token that can never appear inside a commit subject line because
# it contains an ASCII record-separator (U+001E). ``git log --pretty=format:``
# does not escape this for us.
_COMMIT_FIELD_SEP = "\x1f"   # unit separator between fields
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
        return subprocess.run(
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

        records = self._read_commits(range_expr=range_expr, limit=limit)
        if not records:
            return 0

        with conn:  # atomic insert + trim
            # Upsert commits; junction rows use INSERT OR IGNORE since the
            # PK (commit_sha, file_path) makes duplicates harmless.
            conn.executemany(
                "INSERT OR REPLACE INTO commits "
                "(sha, author_email, author_time, message) VALUES (?, ?, ?, ?)",
                [
                    (r.sha, r.author_email, r.author_time, r.message)
                    for r in records
                ],
            )
            junction_rows = [
                (r.sha, fp) for r in records for fp in r.files
            ]
            if junction_rows:
                conn.executemany(
                    "INSERT OR IGNORE INTO commit_files "
                    "(commit_sha, file_path) VALUES (?, ?)",
                    junction_rows,
                )
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
    ) -> list[_CommitRecord]:
        args = [
            "log",
            f"-n{limit}",
            f"--pretty=format:{_PRETTY_FORMAT}",
            "--name-only",
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


def _parse_git_log_output(stdout: str) -> list[_CommitRecord]:
    """Parse fence-delimited ``git log --pretty=format:<_PRETTY_FORMAT> --name-only`` output.

    Layout: each commit is ``sha<US>time<US>email<US>subject<RS>\\nfile_a\\nfile_b\\n\\n``.
    We split on the record separator first, then on field separator inside
    each record. The trailing block after the last RS contains the files
    of the last commit; git emits files separated by newlines with a blank
    terminator when ``--name-only`` is combined with ``--pretty=format:``.
    """
    if not stdout:
        return []
    # The RS appears at the END of each record, so split and drop the empty
    # tail. In the incremental case there may be a trailing newline before
    # the final RS; both strip below.
    records: list[_CommitRecord] = []
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
        files = tuple(
            f.strip() for f in files_blob.splitlines() if f.strip()
        )
        records.append(
            _CommitRecord(
                sha=sha,
                author_time=author_time,
                author_email=ae,
                message=subject,
                files=files,
            )
        )
    return records


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
    return {
        email: (n, (n / total) * 100.0) for email, n in counts.items()
    }
