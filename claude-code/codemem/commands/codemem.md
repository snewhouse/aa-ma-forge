# /codemem — structural code intelligence for Claude Code

**Status**: M1 shippable. M1 subcommands are `build`, `query`, `status`.
M2 adds `refresh` and `replay --from-wal`; M3 adds the git-mining
subcommands. M4 adds benchmarks.

The `/codemem` slash command is the interactive entry point. For agent
use, see the MCP server (started separately — Task 1.10); for CI /
automation, the Python API (`codemem.indexer.build_index`, the
`codemem.mcp_tools.*` functions, `codemem.pagerank.write_project_intel`)
is more ergonomic than shelling out.

---

## Subcommand reference

### `codemem build [--package PACKAGE] [--db PATH]`

Build the SQLite index + `PROJECT_INTEL.json` from scratch for the
current repo.

**Arguments:**
- `--package PACKAGE` — SCIP `<package>` prefix for generated IDs.
  Defaults to `.` (repo-root). See
  [`symbol-id-grammar.md`](../../../docs/codemem/symbol-id-grammar.md)
  for examples.
- `--db PATH` — output DB location. Defaults to `.codemem/index.db`
  relative to repo root.

**Behaviour (M1):**
1. Discovers tracked files via `git ls-files` (respects `.gitignore`).
2. Dispatches `.py` to the stdlib `ast` parser; everything else
   (TypeScript, Go, Rust, Java, Ruby, Bash) batched via one `sg scan`
   per language.
3. Bulk-inserts `files` / `symbols` / `edges` with
   `PRAGMA foreign_keys = OFF` toggled around the transaction;
   re-enables and runs `foreign_key_check` + `integrity_check` on exit.
4. Runs the four-strategy cross-file resolver against Python imports.
5. Writes `PROJECT_INTEL.json` (≤ 1024 tokens by default; ≤ 5KB on
   aa-ma-forge).

**Perf budgets (enforced in `tests/perf/test_budgets.py` once Task 1.13
lands):**
- Cold cache on ~10k-LOC Python repo: < 30s
- Warm cache (same): < 5s

### `codemem query <tool> [args...]`

Call 10 of the MCP tools directly. No MCP server required. (`symbol_history`, `aa_ma_context` and
`diagram` are MCP-only; `codemem draw` renders diagrams.)

**Tools:**

| Tool | Usage | Returns |
|------|-------|---------|
| `who_calls` | `codemem query who_calls NAME [--max-depth N] [--budget TOKENS]` | upstream callers via canonical CTE |
| `blast_radius` | `codemem query blast_radius NAME [--max-depth N] [--budget TOKENS]` | downstream callees transitively |
| `dead_code` | `codemem query dead_code [--budget TOKENS]` | functions/methods with zero inbound call edges |
| `dependency_chain` | `codemem query dependency_chain SOURCE TARGET [--max-depth N] [--budget TOKENS]` | shortest call-path |
| `search_symbols` | `codemem query search_symbols QUERY [--budget TOKENS]` | name-substring match with exact/prefix/contains ranking |
| `file_summary` | `codemem query file_summary PATH [--budget TOKENS]` | symbols in a file, ordered by line |
| `hot_spots` | `codemem query hot_spots [--budget TOKENS]` | files ranked by commits in the last 90 days × function count (needs `refresh-commits`) |
| `co_changes` | `codemem query co_changes FILE [--budget TOKENS]` | files that change with FILE but lack an import edge (needs `refresh-commits`) |
| `owners` | `codemem query owners PATH [--repo-root R] [--budget TOKENS]` | per-author line share; a directory needs a trailing `/`; `--repo-root` computes the blame, otherwise only the cache is read |
| `layers` | `codemem query layers [--budget TOKENS]` | files bucketed core / middle / periphery by in-degree |

All tools return structured JSON:

```json
{
  "target": "...",
  "<list_key>": [...],
  "truncated": false,
  "error": null
}
```

Adversarial input (path traversal, 10KB unicode, regex metachars, SQL
injection attempts) is rejected BEFORE any SQL runs — `error` is
populated and the list is empty. No tool raises under untrusted input.

### `codemem status [--db PATH]`

Print a summary of the current index: file count, symbol count, edge
count (resolved vs unresolved), last build time, schema version.

### `codemem refresh [--repo-root PATH]`

Incremental refresh of the index (`codemem.incremental.refresh_index`): content-hash
dirty detection, `git mv` detection, symbol-level deltas. With `last_sha` missing,
malformed or orphaned by a history rewrite it does a full rebuild into a sibling file
and swaps it in with `os.replace`, so readers never see a half-built DB. Records
`.codemem/last_sha` and `.codemem/tree_sig`. Exit 0 refreshed, 75 another refresh holds
`.codemem/db.lock`, 1 error (one line in `.codemem/refresh.log`). Run by the post-commit
step and, capped at 5 s, by any MCP query that finds the index stale; responses then
carry `index_sha`, `head_sha`, `stale` and `stale_reason`.

### `codemem replay --from-wal [--wal PATH]`

Reconstruct SQLite state from a JSONL write-ahead journal (default `.codemem/wal.jsonl`).
Idempotent via `(op, prev_user_version, content_sha)` keys. The journal is written only when a caller passes `build_index(wal_path=…)` from Python; `codemem build` and `codemem refresh` do not write it (checked 2026-10-14).

---

### `codemem draw [--level L0|L1|L2|L3] [--scope PATH] [--hops N] [--include-tests] [--direction up|down|both] [--kind import|call|both]`

Emit a mermaid `flowchart` of the graph to stdout (a one-line node/edge summary goes
to stderr, so stdout stays pure mermaid). Levels: **L0** top directories, **L1**
directories at depth 2, **L2** files, **L3** symbols (calls only). `--scope` centres
any level on a path prefix and walks `--hops` in `--direction`; `tests/` is excluded
unless `--include-tests`. Edges carry their kind as a quoted sigil —
`A -->|"@import"| B` — the form PHANTOM_EDGE checks read (a bare `|@import|` is a
mermaid 11 parse error). Over 500 edges (mermaid's `maxEdges`) the rest are dropped
and reported. Exit 0 ok, 1 no/old/unreadable index (run `codemem build`), 2 usage.

### A refused `.codemem/`

Every subcommand and MCP tool refuses a `.codemem/` (or the `CODEMEM_DB` directory)
that is or holds a symlink or cannot be listed: a repo controls that directory, and a
link would be written through. The CLI prints `codemem <cmd>: refused: …` and exits 1;
an MCP response carries `stale: "unknown"`, `stale_reason: "unsafe_db_path"` and an
`error`. Remove the link, run `codemem build`, and keep `CODEMEM_DB` in a dedicated
directory.

codemem also reads only an index it built for this user and this directory. A
committed, copied or unzipped `index.db` (or one in a moved repo) carries no stamp for you (the nonce lives in
`$XDG_STATE_HOME/codemem/trust/`, default `~/.local/state`): read-only commands refuse
it (`run codemem build`), `codemem refresh` and any MCP query rebuild it, and until the
rebuild finishes an MCP response is an `error` with `stale_reason: "untrusted"`.
If the trust store itself cannot be used (unreadable, not a private directory of this user,
a record that is not a nonce), the CLI prints `codemem <cmd>: trust store error: …` and an MCP
response is an `error` with `stale_reason: "trust_store"`: fix the state dir; a rebuild will
not help. `codemem draw --check` reports it as UNKNOWN (exit 0).
`codemem replay --from-wal` trusts its journal: replay only one codemem wrote here.
Keep `XDG_STATE_HOME` the same for every process that runs codemem, or each rebuilds the
other's index. Known limit until Milestone 16 moves the index out of the repo: a
committed `index.db-wal` beside an index built here is still replayed by SQLite, and committing
your own `.codemem/` publishes its stamp: keep `.codemem/` ignored.

## Related documents

- [`docs/codemem/symbol-id-grammar.md`](../../../docs/codemem/symbol-id-grammar.md)
  — SCIP-shaped symbol ID grammar pinned in M1 Task 1.2b.
- [`.claude/dev/active/codemem/codemem-reference.md`](../../../.claude/dev/active/codemem/codemem-reference.md)
  — full reference for the in-progress plan (public API, contract
  invariants, perf SLOs).
- [`docs/codemem/ARCHITECTURE.md`](../../../docs/codemem/ARCHITECTURE.md)
  — 5-section architecture document (M1 Task 1.12 placeholders,
  finalised in M4 Task 4.9).
- [`docs/codemem/performance-slo.md`](../../../docs/codemem/performance-slo.md)
  — enforced perf budgets (Task 1.13).
