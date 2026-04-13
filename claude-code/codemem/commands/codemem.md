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

Call one of the six MCP tools directly. No MCP server required.

**Tools (M1):**

| Tool | Usage | Returns |
|------|-------|---------|
| `who_calls` | `codemem query who_calls NAME [--max-depth N] [--budget TOKENS]` | upstream callers via canonical CTE |
| `blast_radius` | `codemem query blast_radius NAME [--max-depth N] [--budget TOKENS]` | downstream callees transitively |
| `dead_code` | `codemem query dead_code [--budget TOKENS]` | functions/methods with zero inbound call edges |
| `dependency_chain` | `codemem query dependency_chain SOURCE TARGET [--max-depth N] [--budget TOKENS]` | shortest call-path |
| `search_symbols` | `codemem query search_symbols QUERY [--budget TOKENS]` | name-substring match with exact/prefix/contains ranking |
| `file_summary` | `codemem query file_summary PATH [--budget TOKENS]` | symbols in a file, ordered by line |

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

### `codemem refresh` — _M2 placeholder_

Incremental rebuild for dirty files (mtime+size → SHA-256 fallback).
Writes to `.codemem/wal.jsonl` BEFORE mutating SQLite; crash-safe
replay via `codemem replay --from-wal`. Not yet implemented — shipped
in Milestone M2.

### `codemem replay --from-wal` — _M2 placeholder_

Reconstruct SQLite state from the WAL JSONL journal. Idempotent via
`(op, prev_user_version, content_sha)` keys. Not yet implemented —
shipped in Milestone M2.

---

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
