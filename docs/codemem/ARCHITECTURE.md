# codemem — Architecture

**Status**: M1 placeholder pass (Task 1.12). Sections marked _M2 TBD_
and _M4 final_ get filled in at those milestone gates. See
[`codemem-plan.md`](../../.claude/dev/active/codemem/codemem-plan.md) for the overall
roadmap and [`codemem-reference.md`](../../.claude/dev/active/codemem/codemem-reference.md)
for the pinned invariants this doc references.

---

## 1. Layering contract + import rules

codemem's Python source is organised in a strict four-layer cake. The
upper layers may import from lower layers; lower layers must NOT
import from upper layers.

```
┌────────────────────────────────────────────────┐
│  Orchestrators + Public API (top)              │
│  codemem.mcp_tools | codemem.indexer |          │
│  codemem.resolver  | codemem.pagerank           │
├────────────────────────────────────────────────┤
│  Parser                                        │
│  codemem.parser.python_ast                     │
│  codemem.parser.ast_grep                       │
├────────────────────────────────────────────────┤
│  Storage (leaf)                                │
│  codemem.storage                               │
└────────────────────────────────────────────────┘
```

**Enforcement**: [`.importlinter`](../../.importlinter) at the repo root
defines two contracts:

1. `codemem-layers` — the layered contract above (peers allowed within
   a layer, no upward imports).
2. `parser-is-pure` — a forbidden contract preventing `codemem.parser.*`
   from importing any orchestrator/API module. Keeps the parser layer
   reusable in isolation.

`uv run lint-imports` passes in CI; both contracts are also verified
by `tests/codemem/test_install_and_cli.py::TestImportLinterContract`.

**Plugin surface (outside `codemem.*` package)**: the MCP server at
`claude-code/codemem/mcp/server.py` MUST route ALL calls through
`codemem.mcp_tools`. Direct imports of `codemem.storage`,
`codemem.parser`, `codemem.indexer`, `codemem.resolver`, or
`codemem.pagerank` from the plugin surface are forbidden. Since
`claude-code/` isn't a Python package, this is enforced by a grep
guard in `TestPluginSurfaceNoBypass` (import-linter's package-scoped
analysis can't reach it).

---

## 2. Dual-WAL semantics — _M2 TBD_

**Status at M1**: placeholder. The full state diagram lands at M2
Task 2.3 with the WAL JSONL journal, the
intent-append → SQLite-commit → ack-append ordering, and the
idempotency-key (`op`, `prev_user_version`, `content_sha`) contract.

The pinned contract in `codemem-reference.md §WAL JSONL Replay State
Diagram` is the authoritative reference until M2 ships; two engineers
implementing the replay semantics from that diagram MUST produce
identical behaviour.

Summary of the M2 contract:

* Every mutation appends intent JSON to `.codemem/wal.jsonl` BEFORE
  any SQLite write.
* SQLite write is a single transaction.
* After commit, a second append `{"ack": true, "id": <wal_id>}` marks
  the entry as applied. Atomic via `O_APPEND`.
* Replay walks wal.jsonl in order; entries with matching `ack` are
  skipped. Entries whose `content_sha`/`prev_user_version` already
  match the current DB state are recognised as idempotent and
  skipped (log warning, append ack).
* Entries whose `prev_user_version` does NOT match the current DB
  state raise `ReplayConflict` — this is the "we don't know how to
  continue" signal that falls back to full rebuild.

M4 Task 4.9 finalises this section with the property-test evidence
and the concurrent-refresh single-writer lock integration.

---

## 3. Symbol ID grammar

SCIP-shaped IDs per [`docs/codemem/symbol-id-grammar.md`](symbol-id-grammar.md)
(pinned in M1 Task 1.2b, frozen unless schema version bumps).

Short form:

```
<scheme> ' ' <package> ' ' <kind-marker><file> '#' <symbol-path>

scheme       = 'codemem'
package      = repo-relative directory (e.g. '.', 'src/pkg')
kind-marker  = '/' (term) | '#' (type) | '.' (member)
symbol-path  = <name> ( ('.' | '#') <name> )*
```

See the grammar doc for per-language examples (Python, TypeScript,
Tsx, JavaScript, Go, Rust, Java, Ruby, Bash) and the parser contract
fixtures.

Any parser change that alters an emitted ID is an implicit schema
migration — bump `PRAGMA user_version` and provide a
`codemem migrate-symbol-ids` utility.

---

## 4. Concurrency model — _M2 TBD_

**Status at M1**: placeholder. Full contract lands at M2 Task 2.7
with the process-level single-writer lock
(`fcntl.lockf` POSIX / `msvcrt.locking` Windows, abstracted behind
`_acquire_writer_lock(path)`), lock-file conventions
(`.codemem/db.lock` vs `.codemem/refresh.pid`), and the
"second-invocation no-ops with informative log line" policy.

M1 ships a single-writer runtime by construction:
`build_index` is called synchronously; the post-commit hook
backgrounds `codemem refresh` (M2 placeholder) via `&` but serializes
against itself via a PID file in M2 Task 2.5.

MCP server reads are always `mode=ro` (URI opens a read-only
connection); they never touch the writer lock. WAL journal mode
allows concurrent readers during a writer transaction.

---

## 5. Performance SLOs + measurement

Budgets and measurement methodology: see
[`docs/codemem/performance-slo.md`](performance-slo.md).

**M1-enforced budgets** (CI fails on > 10% regression):

| SLO | Budget | Harness |
|-----|--------|---------|
| `codemem build` cold, ~10k-LOC Python repo | < 30s | `tests/perf/test_budgets.py::test_cold_build` |
| `codemem build` warm (same) | < 5s | `tests/perf/test_budgets.py::test_warm_build` |
| `who_calls("extract_python_signatures")` on /index's index_utils.py | < 100ms | `tests/perf/test_budgets.py::test_who_calls_anchor` |
| `PROJECT_INTEL.json` size at budget=1024 | ≤ 5KB on aa-ma-forge | `tests/perf/test_budgets.py::test_project_intel_size` |

All perf tests are marked `@pytest.mark.perf` so they run only in the
perf job, not in the fast unit-test loop. The perf run uses
`pytest-benchmark`; budget failures (regression beyond the documented
tolerance) halt the CI pipeline.

Benchmark data points accumulate in `.benchmarks/` (git-ignored).
M4 Task 4.1 compares the same harness against `/index` on three
reference repos and publishes the cross-tool numbers to
`docs/benchmarks/codemem-vs-index.md`.

---

## Related documents

* [`symbol-id-grammar.md`](symbol-id-grammar.md) — SCIP-shaped IDs (M1 Task 1.2b).
* [`performance-slo.md`](performance-slo.md) — measured budgets (M1 Task 1.13).
* [`design-scratchpad.md`](design-scratchpad.md) — M1 Task 1.0 pre-flight research
  (Aider PageRank, `/index` pagerank.py, repowise symbol_diff,
  GitNexus 2026 landscape, lessons L-052). Not load-bearing — a
  snapshot frozen at plan v3→v4 transition.
* [`kill-criteria.md`](kill-criteria.md) — _M4 TBD_. The public list of
  signals that tell us to drop codemem back into `/index`.
* [`codemem-reference.md`](../../.claude/dev/active/codemem/codemem-reference.md)
  — the pinned invariants that this architecture doc normalises.
