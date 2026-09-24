"""codemem CLI entry point (M1 Task 1.11).

Minimal argparse dispatcher composing the M1 modules:

* ``codemem build``           — :func:`codemem.indexer.build_index`
* ``codemem status``          — prints file/symbol/edge counts from the DB
* ``codemem refresh``         — M2 placeholder; logs and exits 0
* ``codemem refresh-commits`` — populate git-mining cache via
                                  :meth:`GitMiner.refresh_commits_cache`
                                  (M4 Task 4.8 / L-254 — the production
                                  wiring missing from M3)
* ``codemem replay``          — M2 placeholder; logs and exits 0
* ``codemem query``           — calls one of the six MCP tools via stdlib JSON
* ``codemem intel``           — writes PROJECT_INTEL.json via the PageRank
                                  projection

The CLI is what the post-commit hook runs; it must stay
side-effect-safe (no mutation without explicit subcommand), fast to
exit (heavy imports are lazy), and return non-zero on sanitization or
build failure.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _default_db_path() -> Path:
    return Path.cwd() / ".codemem" / "index.db"


def _cmd_build(args: argparse.Namespace) -> int:
    from .indexer import build_index

    db_path = Path(args.db) if args.db else _default_db_path()
    repo_root = Path(args.repo_root) if args.repo_root else Path.cwd()
    stats = build_index(repo_root, db_path, package=args.package or ".")
    print(
        f"codemem build: {stats.files_indexed} files, "
        f"{stats.symbols_inserted} symbols, {stats.edges_inserted} edges "
        f"(cross-file: {stats.cross_file_resolved} resolved / "
        f"{stats.cross_file_unresolved} unresolved) "
        f"in {stats.elapsed_seconds:.2f}s — {db_path}"
    )
    return 0


def _cmd_status(args: argparse.Namespace) -> int:
    from .storage import db

    db_path = Path(args.db) if args.db else _default_db_path()
    if not db_path.exists():
        print(f"codemem status: no DB at {db_path}", file=sys.stderr)
        return 1

    with db.connect(db_path, read_only=True) as conn:
        files = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        symbols = conn.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]
        edges = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
        resolved = conn.execute(
            "SELECT COUNT(*) FROM edges WHERE dst_symbol_id IS NOT NULL"
        ).fetchone()[0]
        schema = conn.execute("PRAGMA user_version").fetchone()[0]

    print(f"codemem status — {db_path}")
    print(f"  schema version:  {schema}")
    print(f"  files:           {files}")
    print(f"  symbols:         {symbols}")
    print(
        f"  edges:           {edges} "
        f"({resolved} resolved, {edges - resolved} unresolved)"
    )
    return 0


def _cmd_refresh(args: argparse.Namespace) -> int:
    # M2 replaces this with the incremental refresh driver (Task 2.2).
    # M1 logs and exits 0 — the post-commit hook calls it, so the
    # wiring is verifiable without shipping an incomplete implementation.
    db_path = Path(args.db) if args.db else _default_db_path()
    log_dir = db_path.parent
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "refresh.log"
    with log_file.open("a", encoding="utf-8") as fh:
        fh.write(
            "codemem refresh: M2 placeholder — post-commit hook fired, "
            "no-op in M1\n"
        )
    print(
        "codemem refresh: M1 placeholder (real incremental refresh "
        "ships in M2)"
    )
    return 0


def _cmd_refresh_commits(args: argparse.Namespace) -> int:
    """Populate ``commits`` + ``commit_files`` cache from ``git log``.

    The default ``codemem refresh`` is an M2 placeholder that does NOT
    populate the git-mining cache, so out of the box ``co_changes`` /
    ``hot_spots`` / cached portions of ``owners``+``symbol_history``
    return empty until this command runs once. Same minimal-wiring
    pattern as L-253's ``db.ensure_schema``: a single named CLI
    choke-point users can run after install (or post-commit) to light
    up the M3 git-mining tools.

    Acquires the same writer lock (``.codemem/db.lock``) that
    ``incremental.py`` and ``mcp_tools`` use to serialise writers, so
    running this concurrently with ``codemem build`` or a post-commit
    refresh no-ops cleanly rather than racing on SQLite.
    """
    import sqlite3

    from .analysis.git_mining import GitMiner
    from .journal.lock import acquire_writer_lock
    from .storage import db as storage_db

    db_path = Path(args.db) if args.db else _default_db_path()
    repo_root = Path(args.repo_root) if args.repo_root else Path.cwd()

    if not db_path.exists():
        print(
            f"codemem refresh-commits: no DB at {db_path}; "
            f"run `codemem build` first",
            file=sys.stderr,
        )
        return 1

    lock_file = db_path.parent / "db.lock"
    try:
        with acquire_writer_lock(lock_file) as acquired:
            if not acquired:
                print(
                    "codemem refresh-commits: another writer holds "
                    f"{lock_file} — skipped",
                    file=sys.stderr,
                )
                return 0
            miner = GitMiner(repo_root=repo_root)
            with storage_db.connect(db_path) as conn:
                inserted = miner.refresh_commits_cache(conn, limit=args.limit)
    except FileNotFoundError as exc:
        # `git` binary missing, or repo_root not a directory.
        print(
            f"codemem refresh-commits: required dependency missing: {exc}",
            file=sys.stderr,
        )
        return 1
    except subprocess.CalledProcessError as exc:
        print(
            f"codemem refresh-commits: git subprocess failed "
            f"(exit {exc.returncode}): {exc.stderr or exc}",
            file=sys.stderr,
        )
        return 1
    except sqlite3.Error as exc:
        # Corrupt DB, schema mismatch, or no `commits` table (v1 DB
        # predates M3 Task 3.8). Users fix by running `codemem build`.
        print(
            f"codemem refresh-commits: SQLite error: {exc} — try "
            f"`codemem build` to re-create the DB at the current schema",
            file=sys.stderr,
        )
        return 1

    print(
        f"codemem refresh-commits: inserted {inserted} commits "
        f"(cap={args.limit}) — {db_path}"
    )
    return 0


def _cmd_replay(args: argparse.Namespace) -> int:
    """M2 Task 2.4: codemem replay --from-wal reconstructs SQLite from
    the WAL JSONL journal using idempotency keys.
    """
    from .journal.wal import replay_wal

    if not args.from_wal:
        print(
            "codemem replay: pass --from-wal to replay the JSONL journal",
            file=sys.stderr,
        )
        return 2

    db_path = Path(args.db) if args.db else _default_db_path()
    wal_path = Path(args.wal) if args.wal else db_path.parent / "wal.jsonl"
    if not wal_path.exists():
        print(f"codemem replay: no WAL at {wal_path}", file=sys.stderr)
        return 1

    stats = replay_wal(wal_path, db_path)
    print(
        f"codemem replay: applied={stats['applied']} "
        f"skipped_already_acked={stats['skipped_already_acked']} "
        f"skipped_idempotent={stats['skipped_idempotent']} "
        f"total={stats['total']} — db={db_path}"
    )
    return 0


def _cmd_query(args: argparse.Namespace) -> int:
    from . import mcp_tools

    db_path = Path(args.db) if args.db else _default_db_path()
    kwargs: dict = {"budget": args.budget}
    if args.max_depth is not None:
        kwargs["max_depth"] = args.max_depth

    tool = args.tool
    if tool == "who_calls":
        result = mcp_tools.who_calls(db_path, args.positional[0], **kwargs)
    elif tool == "blast_radius":
        result = mcp_tools.blast_radius(db_path, args.positional[0], **kwargs)
    elif tool == "dead_code":
        result = mcp_tools.dead_code(db_path, budget=args.budget)
    elif tool == "dependency_chain":
        result = mcp_tools.dependency_chain(
            db_path,
            args.positional[0],
            args.positional[1],
            max_depth=args.max_depth or 5,
            budget=args.budget,
        )
    elif tool == "search_symbols":
        result = mcp_tools.search_symbols(
            db_path, args.positional[0], budget=args.budget
        )
    elif tool == "file_summary":
        result = mcp_tools.file_summary(
            db_path, args.positional[0], budget=args.budget
        )
    else:
        print(f"codemem query: unknown tool '{tool}'", file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2, default=str))
    return 0 if not result.get("error") else 1


def _cmd_intel(args: argparse.Namespace) -> int:
    from .pagerank import write_project_intel

    db_path = Path(args.db) if args.db else _default_db_path()
    out = Path(args.out) if args.out else Path.cwd() / "PROJECT_INTEL.json"
    stats = write_project_intel(db_path, out, budget=args.budget)
    print(
        f"codemem intel: wrote {stats['written_symbols']} symbols "
        f"({stats['size_bytes']}B) → {out}"
    )
    return 0


def _non_negative_int(text: str) -> int:
    value = int(text)
    if value < 0:
        raise argparse.ArgumentTypeError(f"must be >= 0, got {value}")
    return value


def _cmd_draw(args: argparse.Namespace) -> int:
    import sqlite3

    from .draw.cut import MIN_SCHEMA_VERSION, Level, cut
    from .draw.mermaid import to_mermaid
    from .storage.db import connect

    views_mode = args.write or args.check
    if views_mode and (args.level is not None or args.scope is not None):
        args._draw_parser.error("--write/--check regenerate the registered views; --level/--scope do not apply")
    who = "codemem draw --check" if args.check else "codemem draw"
    db_path = Path(args.db) if args.db else _default_db_path()

    def no_graph(reason: str) -> int:
        # --check cannot run without a graph: UNKNOWN, never PASS, and never a block (ADR-0016).
        if args.check:
            print(f"{who}: UNKNOWN — {reason}; run `codemem build`")
            return 0
        print(f"{who}: {reason}; run `codemem build`", file=sys.stderr)
        return 1

    if not db_path.is_file():
        return no_graph(f"no index at {db_path}")
    conn = connect(db_path, read_only=True)
    try:
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        if version < MIN_SCHEMA_VERSION:
            return no_graph(f"index is schema v{version}, need v{MIN_SCHEMA_VERSION}")
        if views_mode:
            return _draw_views(args, conn)
        level = Level[args.level or Level.L0.name]
        try:
            c = cut(
                conn, level, scope=args.scope, hops=args.hops,
                include_tests=args.include_tests, direction=args.direction, kind=args.kind,
            )
        except ValueError as exc:
            args._draw_parser.error(str(exc))  # usage error: message + exit 2
    except sqlite3.Error as exc:
        return no_graph(f"unreadable index {db_path} ({exc})")
    finally:
        conn.close()
    sys.stdout.write(to_mermaid(c))
    dropped = f", {c.dropped} dropped over maxEdges" if c.dropped else ""
    print(f"codemem draw: {level.name} {len(c.nodes)} nodes / {len(c.edges)} edges{dropped}",
          file=sys.stderr)
    return 0


def _draw_views(args: argparse.Namespace, conn) -> int:
    from .draw import views

    repo_root = Path.cwd()
    try:
        if args.write:
            for p in views.write_views(repo_root, conn):
                print(f"codemem draw: wrote {p.relative_to(repo_root)}", file=sys.stderr)
            return 0
        findings = views.check_views(repo_root, conn)
    except ValueError as exc:  # malformed captions sidecar, or a write outside docs/architecture/
        print(f"codemem draw: {exc}", file=sys.stderr)
        return 1
    for f in findings:
        print(f"codemem draw --check: {f}")
    if findings:
        print(f"codemem draw --check: {len(findings)} finding(s) — {views.REMEDY}")
        return 1
    print("codemem draw --check: OK")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codemem",
        description="codemem — structural code intelligence",
    )
    parser.add_argument(
        "--db",
        help="Path to codemem SQLite DB (default: .codemem/index.db)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    pb = sub.add_parser("build", help="Index the current repo (full build)")
    pb.add_argument(
        "--package", default=".", help="SCIP <package> prefix (default: .)"
    )
    pb.add_argument("--repo-root", help="Repo root to index (default: cwd)")

    sub.add_parser("status", help="Print current index summary")
    sub.add_parser("refresh", help="Incremental refresh (M2 placeholder)")

    prc = sub.add_parser(
        "refresh-commits",
        help="Populate git-mining cache (commits + commit_files) from git log",
    )
    prc.add_argument(
        "--limit", type=int, default=500,
        help="Max commits to keep in cache (newest by author_time, default 500)",
    )
    prc.add_argument("--repo-root", help="Repo root (default: cwd)")

    pr = sub.add_parser("replay", help="Replay from WAL JSONL journal")
    pr.add_argument("--from-wal", action="store_true")
    pr.add_argument(
        "--wal",
        help="Path to WAL JSONL (default: <db_parent>/wal.jsonl)",
    )

    pq = sub.add_parser("query", help="Invoke one of the 6 MCP tools")
    pq.add_argument(
        "tool",
        choices=[
            "who_calls", "blast_radius", "dead_code",
            "dependency_chain", "search_symbols", "file_summary",
        ],
    )
    pq.add_argument(
        "positional", nargs="*", help="Positional args for the tool"
    )
    pq.add_argument("--max-depth", type=int, default=None)
    pq.add_argument("--budget", type=int, default=8000)

    pi = sub.add_parser("intel", help="Write PROJECT_INTEL.json")
    pi.add_argument("--out", help="Output path (default: PROJECT_INTEL.json)")
    pi.add_argument("--budget", type=int, default=1024)

    from .draw.cut import DIRECTIONS, KINDS, Level

    pd = sub.add_parser("draw", help="Emit a mermaid diagram of the graph")
    mode = pd.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true",
                      help="Regenerate every registered view under docs/architecture/")
    mode.add_argument("--check", action="store_true",
                      help="Exit 1 if docs/architecture/ drifted from the code (UNKNOWN + 0 with no index)")
    pd.add_argument("--level", choices=[lv.name for lv in Level], default=None,
                    help="L0 top dirs, L1 dirs depth 2, L2 files, L3 symbols (default L0)")
    pd.add_argument("--scope", help="Path prefix to centre the cut on")
    pd.add_argument("--hops", type=_non_negative_int, default=1,
                    help="Neighbourhood radius for --scope")
    pd.add_argument("--include-tests", action="store_true", help="Keep tests/ (excluded by default)")
    pd.add_argument("--direction", choices=DIRECTIONS, default="both")
    pd.add_argument("--kind", choices=KINDS, default="both",
                    help="Edge kinds at L0-L2 (L3 is calls only; --kind import is refused there)")
    pd.set_defaults(_draw_parser=pd)

    return parser


_CMD_DISPATCH = {
    "build":            _cmd_build,
    "status":           _cmd_status,
    "refresh":          _cmd_refresh,
    "refresh-commits":  _cmd_refresh_commits,
    "replay":           _cmd_replay,
    "query":            _cmd_query,
    "intel":            _cmd_intel,
    "draw":             _cmd_draw,
}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = _CMD_DISPATCH.get(args.cmd)
    if handler is None:
        parser.print_help()
        return 2
    return handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
