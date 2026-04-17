# codemem — Architecture

**Status**: M3.5 complete. §2 (dual-WAL) and §4 (concurrency model) carry
M2 actuals per Task 4.9; §3 (symbol ID grammar) cross-references the
per-language examples in [`symbol-id-grammar.md`](symbol-id-grammar.md).
See [`codemem-plan.md`](../../.claude/dev/active/codemem/codemem-plan.md) for the overall
roadmap and [`codemem-reference.md`](../../.claude/dev/active/codemem/codemem-reference.md)
for the pinned invariants this doc references. Line-and-file references
below were verified against source at the time of the final pass; see the
cited modules for the current truth if anything diverges.

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

## 2. Dual-WAL semantics

codemem runs two write-ahead logs side by side. They solve different
failure modes and must be reasoned about separately.

**Log 1 — SQLite's built-in WAL (`.codemem/index.db-wal`).** Enabled by
`PRAGMA journal_mode = WAL` (persistent across connections per
`storage/db.py:41` and pinned in [`codemem-reference.md §SQLite PRAGMA Values`](../../.claude/dev/active/codemem/codemem-reference.md)).
Gives us concurrent readers during a writer transaction and
crash-survivable atomic commits at the SQLite-row level. Truncated by
`PRAGMA wal_checkpoint(TRUNCATE)` at the end of every `build_index` and
`refresh_index` (Task 2.6) so the `-wal` file does not grow unbounded.

**Log 2 — codemem's JSONL journal (`.codemem/wal.jsonl`).** Sits
one layer above SQLite and makes codemem's per-file mutation sequence
replayable from scratch. Implemented in
[`codemem/journal/wal.py`](../../packages/codemem-mcp/src/codemem/journal/wal.py).
This is what we mean when we say "the WAL" in the codemem sense.

### Ordering contract (intent → commit → ack)

Every write the indexer performs follows this three-phase sequence:

1. **`append_intent(wal_path, op=..., args=..., prev_user_version=..., content_sha=...)`** — one JSON line
   describing what is about to happen. Written via
   `os.open(path, O_WRONLY | O_CREAT | O_APPEND)` + `os.fsync`, so POSIX
   guarantees atomicity per line below `PIPE_BUF` (entries are
   sub-kilobyte in practice). The intent lands on disk before any
   SQLite write occurs.
2. **SQLite transaction commit.** Inside `db.transaction(conn)` —
   a rollback-on-exception context manager.
3. **`append_ack(wal_path, entry_id)`** — a second line of the form
   `{"ack": true, "id": <uuid-hex>}` written only after the SQLite
   commit succeeds.

Crashing between any two of these phases is safe because replay can
reconstruct the correct state from whatever survived. See the state
diagram below.

### Entry schema (`ENTRY_SCHEMA_VERSION = 1`)

```
{
  "id":                 <uuid4 hex>,
  "ts":                 <local ISO timestamp>,
  "op":                 "file_upsert" | "file_delete",
  "args":               {<op-specific payload>},
  "prev_user_version":  <int — the DB's user_version when the intent was written>,
  "content_sha":        <str — idempotency discriminator>,
  "schema_version":     1
}
```

Op vocabulary v1 is deliberately minimal: file-level upsert and delete
only. Symbol-level ops are a post-M2 extension; the crash-safety
contract is defined at file granularity because that's the unit the
indexer actually batches.

### Idempotency key

`(op, prev_user_version, content_sha)`. The replay engine uses this to
decide whether a given intent has "already happened" from the DB's
perspective. For `file_upsert`, `content_sha` equals the entry's
`content_hash_after` — replay compares it against the live
`files.content_hash` column.

### Replay state diagram (state-first semantics — see [`codemem/journal/wal.py::replay_wal`](../../packages/codemem-mcp/src/codemem/journal/wal.py))

```
for each intent in wal.jsonl (oldest first, spans rotated archives):

    if _is_idempotent(conn, entry):      # DB already matches target state
        if entry.id in acked_ids:
            skipped_already_acked += 1    # branch 1
        else:
            append_ack(entry.id)          # branch 2: crash after commit, before ack
            skipped_idempotent += 1
        continue

    if entry.prev_user_version != current_user_version:
        raise ReplayConflict(...)         # branch 3: schema drift — caller rebuilds
        # (also the test shape at test_wal.py::test_schema_version_mismatch_raises)

    _apply_op(conn, entry)                 # branch 4: apply + append_ack
    if entry.id not in acked_ids:
        append_ack(entry.id)
    applied += 1
```

Key property: the DB is the source of truth, **not the ack log.** A
WAL entry whose target state already exists in the DB is idempotent
regardless of whether an ack was written — this is what makes
`build → snapshot → wipe → replay` a round-trip identity.

### Property-test evidence (Task 2.4)

The `tests/codemem/test_wal_replay_roundtrip.py::test_property_roundtrip_slow`
harness uses `hypothesis` to generate 100 random edit sequences and
asserts that `build → wipe → replay_wal` reproduces a byte-equivalent
DB (modulo `last_indexed` timestamps). Passes in ~3.5 seconds. The
fast-suite variant runs 10 examples on every test run.

### Rotation (Task 2.8)

`rotate_if_needed(wal_path)` fires whenever the live `wal.jsonl` exceeds
`ROTATION_THRESHOLD_BYTES = 10 * 1024 * 1024` (10 MB). It shifts
existing archives (`.3.gz` dropped, `.2.gz → .3.gz`, `.1.gz → .2.gz`),
compresses the live WAL into `.1.gz` using chunked I/O (1 MB buffer to
cap memory), then truncates the live file. `ROTATION_RETAIN_COUNT = 3`
— anything older is discarded.

Replay reads transparently across the rotation boundary via
`_rotated_archive_paths()` which yields `.3.gz → .2.gz → .1.gz → live`
in chronological (oldest-first) order — verified by
`test_wal_rotation.py::test_replay_equal_regardless_of_rotation`.

### Crash-survivability matrix

| Crash point | Next replay outcome |
|-------------|---------------------|
| Before intent written | No entry visible, no effect. |
| After intent, before SQLite commit | DB state doesn't match target → `_apply_op` runs → ack appended. |
| After SQLite commit, before ack | DB state matches target but no ack → branch 2 appends the missing ack. |
| After ack | Steady state, nothing to do. |

`ReplayConflict` is the only unrecoverable branch: if the DB's
`user_version` has moved past what the intent was written against
(typically because of a schema migration applied out-of-band), the
caller should fall back to a full rebuild. The `incremental.py`
refresh driver already does this whenever `last_sha` is orphaned
(Task 2.2) — the same fallback covers the `ReplayConflict` case.

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

### Per-language coverage (locked at M4 Task 4.9)

The grammar doc pins per-language emission rules with fixture-backed
examples for eight languages. Each language's section gives: the
enclosing-container pattern, the kind-marker choice for each syntactic
construct, and the parser-contract test shape.

| Language | Covered constructs (grammar doc §) | Parser |
|----------|------------------------------------|--------|
| Python | top-level function, class, method, decorated method, metaclass, nested class, module variable, `__init__.py` | stdlib `ast` (M1 Task 1.3) |
| TypeScript / JavaScript | function, class, method, interface, type alias, namespace (nested), arrow const | `ast-grep` (M1 Task 1.4) |
| Tsx | same as TypeScript, separate rule file (ast-grep treats them as distinct languages; empirically verified) | `ast-grep` |
| Java | class, method, inner class, anonymous class (`$N` synthetic), enum | `ast-grep` |
| Go | function, struct, method on value + pointer receivers `(*Type)`, interface | `ast-grep` |
| Rust | function, struct, impl-block methods, trait, trait method, `impl-Trait-for-Type` convention (macros deferred to v2) | `ast-grep` |
| Ruby | class, method, module | `ast-grep` |
| Bash | functions only (no classes / structs / modules in shell) | `ast-grep` |

Golden fixtures live under `tests/fixtures/codemem/symbol_ids/` — any
parser change that alters an emitted ID must update the fixture and is
treated as an implicit schema migration: bump `PRAGMA user_version`
and ship a `codemem migrate-symbol-ids` utility.

Open extensions tracked in the grammar doc's "Open questions" section
(MRO, re-exports, deleted-file tombstones, overload disambiguation,
Rust macros) are deliberately out of v1 scope.

---

## 4. Concurrency model

codemem's concurrency contract rests on three orthogonal primitives.
Each has a single responsibility; mixing them produces bugs (see
L-253's adjacent pattern), so the names and files below matter.

### Primitive 1 — SQLite WAL journal mode

`PRAGMA journal_mode = WAL` (persisted at DB creation) allows an
unlimited number of reader connections to proceed concurrently with an
active writer transaction. The readers see a snapshot from before the
writer opened its transaction until commit. This is the foundation:
every MCP tool query is a reader, every indexer pass is the writer,
and they never block each other.

MCP connections open read-only via the `file:...?mode=ro` URI form
(`storage/db.py::connect(..., read_only=True)` at line 126). A
read-only connection ignores FK enforcement (no-op on read paths) but
otherwise gets the same per-connection PRAGMAs (busy_timeout,
cache_size, mmap_size).

### Primitive 2 — Process-level writer lock (`.codemem/db.lock`)

Implemented in
[`codemem/journal/lock.py`](../../packages/codemem-mcp/src/codemem/journal/lock.py)
as a context manager:

```python
with acquire_writer_lock(Path(".codemem/db.lock")) as acquired:
    if not acquired:
        return  # another writer is active; no-op, do NOT queue
    ...  # do the write
```

The implementation is cross-platform by branching on `sys.platform`:

- **POSIX** (Linux, macOS): `fcntl.lockf(fd, LOCK_EX | LOCK_NB)` on an
  `O_CREAT | O_WRONLY` file descriptor. Non-blocking — contention returns
  `False` via `BlockingIOError`, never raises. Released via `LOCK_UN`.
- **Windows**: `msvcrt.locking(fd, LK_NBLCK, 1)` / `LK_UNLCK`. Not
  exercised by CI (POSIX-only runners); `# pragma: no cover — POSIX CI`
  on the Windows branches. Stdlib-only — `portalocker` is not needed.

**Policy: second invocation no-ops, does not queue.** If process B
calls `refresh_index` while process A holds the lock, B logs
`refresh: skipped (another refresh holds db.lock)` to
`.codemem/refresh.log`, returns `RefreshStats(skipped_locked=True)`
and exits. It does not wait. Rationale: whatever change triggered B's
refresh is already on disk, so when A's in-flight refresh finishes it
will pick up B's changes naturally via the same file-discovery pass.

Test evidence: `tests/codemem/test_writer_lock.py::TestCrossProcessContention`
uses `multiprocessing.Process` + `multiprocessing.Event` to verify the
contention path deterministically (holder process acquires, second
process fails to acquire, succeeds once holder releases).

### Primitive 3 — Post-commit hook PID tracking (`.codemem/refresh.pid`)

Separate from `db.lock` and with a different job. Lives in
`claude-code/codemem/hooks/post-commit.sh` (M2 Task 2.5). Its
responsibilities:

- Skip during `rebase`, `cherry-pick`, `revert`, `merge` via
  `GIT_REFLOG_ACTION` prefix check.
- On every commit, check whether `.codemem/refresh.pid` names a live
  process; if so, kill the **entire process group** (`kill -- -<pgid>`)
  with a 50 ms sleep for clean shutdown. The leading minus is load-
  bearing: `codemem refresh` spawns `sg scan` and `python` subprocesses
  and we need all of them gone.
- Spawn the new refresh under `setsid` so its PGID equals its PID —
  this is what makes the `kill -- -<pgid>` in the next commit hit the
  whole subprocess tree. On macOS where `setsid` isn't in the default
  shell, fall back to plain `&` background spawn.
- Write the new PID to `.codemem/refresh.pid`; redirect stdout + stderr
  to `.codemem/refresh.log`; close stdin.
- `exit 0` unconditionally. The hook must NEVER fail a commit.

Storm-test gate: `tests/codemem/test_post_commit_storm.py` rapid-fires
five `git commit --amend` calls in under two seconds and asserts
`pgrep -af codemem | wc -l == 1` after quiesce.

### Why the two files are separate

`.codemem/db.lock` is about the DB and owned by the indexer process
that happens to be writing. `.codemem/refresh.pid` is about the hook
and owned by whatever process the post-commit spawned. Merging them
would couple the hook's liveness to the DB-write contract — a hook
killed between commits shouldn't look like a writer who vanished.

### Reads never touch either file

Every MCP tool invocation opens its SQLite connection with
`read_only=True` (verified by `TestReadOnlyConnectionPolicy` in
`test_mcp_server.py` grepping the server source for `read_only=False`).
That code path does not import `journal.lock` and is not gated on
either file. A query can complete successfully while a refresh is in
progress, serving the pre-commit snapshot view.

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

* [`symbol-id-grammar.md`](symbol-id-grammar.md) — SCIP-shaped IDs with
  per-language examples and parser-contract fixture shape (M1 Task 1.2b).
* [`performance-slo.md`](performance-slo.md) — measured budgets and
  reproduction methodology (M1 Task 1.13).
* [`migration-from-index.md`](migration-from-index.md) — 5-minute switch
  guide from Eric Buess's `/index`; side-by-side MCP tool comparison,
  data-model differences, hook interaction (M4 Task 4.3).
* [`design-scratchpad.md`](design-scratchpad.md) — M1 Task 1.0 pre-flight
  research (Aider PageRank, `/index` pagerank.py, repowise symbol_diff,
  GitNexus 2026 landscape, lessons L-052). Not load-bearing — a snapshot
  frozen at plan v3→v4 transition.
* [`kill-criteria.md`](kill-criteria.md) — _M4 Task 4.10 TBD_. The public
  list of signals that tell us to drop codemem back into `/index`.
* [`codemem-reference.md`](../../.claude/dev/active/codemem/codemem-reference.md)
  — the pinned invariants that this architecture doc normalises, including
  the `db.ensure_schema` contract (L-253), the v2 schema tables added by
  M3 Task 3.8 (`commits`, `commit_files`, `ownership`, `co_change_pairs`),
  and the WAL intent-tagging rule (`prev_user_version = db.CURRENT_SCHEMA_VERSION`).
