# codemem-benchmark-fairness-v2 Reference

_Load-first priority file. Contains immutable facts, v1 carry-forward invariants, Phase-3 research findings, and all external claim verifications. An agent resuming this task reads THIS FILE FIRST._

---

## TOP PRIORITY: Tokeniser-Mismatch Invariant (CARRIED FORWARD FROM v1)

**When benchmarking, NEVER compare raw output sizes at "equal requested budget" alone; tools count budgets differently.**

Every measurement MUST report three numbers:
- **(a) Raw output bytes**: the actual file/string size produced
- **(b) tiktoken-counted tokens**: external normalisation via `tiktoken.get_encoding("cl100k_base").encode(text)`
- **(c) Symbol-row count**: semantic unit count (may be 0 for Repomix if `status=ok_no_symbols`)

Reason: codemem WAS using a `4 chars/token` proxy (removed in M1 of v2), Aider uses tiktoken against the configured model, jCodeMunch uses tiktoken `cl100k_base`, Repomix supports `--token-count-encoding=cl100k_base`, Yek uses `--tokens N`. A "1024-token budget" means different things across tools unless each tool is normalised at the harness boundary.

After M1 lands, codemem itself uses cl100k_base at budget time, but the invariant still applies: ALL five tools' outputs are re-tokenised with tiktoken at the harness measurement step.

[valid: 2026-04-20]

---

## Phase 3 Research Findings (2026-04-20)

### pagerank.py probe (empirical, Read tool)

| Aspect | Finding | [valid] |
|---|---|---|
| Proxy constant location | `_CHARS_PER_TOKEN = 4` at `packages/codemem-mcp/src/codemem/pagerank.py:32` | 2026-04-20 |
| `_budget_chars` | `packages/codemem-mcp/src/codemem/pagerank.py:132-133` | 2026-04-20 |
| `_fits` | `packages/codemem-mcp/src/codemem/pagerank.py:136-137` | 2026-04-20 |
| Binary search | `packages/codemem-mcp/src/codemem/pagerank.py:187-194` | 2026-04-20 |
| Rank emission (raw float) | `packages/codemem-mcp/src/codemem/pagerank.py:171` (`"rank": ranks.get(r["id"], 0.0)`) | 2026-04-20 |
| Fix size | ~5 lines total: replace constant + swap `_fits()` to tiktoken | 2026-04-20 |

### Aider CLI surface

| Aspect | Finding | [valid] |
|---|---|---|
| `--model MODEL` | Exists; env var `AIDER_MODEL` | 2026-04-20 |
| `--encoding ENCODING` | Exists but documents I/O, NOT tokenisation | 2026-04-20 |
| `--tokenizer` flag | Does NOT exist | 2026-04-20 |
| Tokeniser routing | Derived from `--model` via `litellm` (source: `aider/models.py`) | 2026-04-20 |
| cl100k_base equalisation | `aider --model gpt-3.5-turbo --show-repo-map --map-tokens N` | 2026-04-20 |
| Output format (v1 carry-forward) | Hybrid prose/markdown; tree-sitter-style symbol skeletons; `│def`/`│class`/`│@` prefixes; `⋮` elision marker; regex-extractable to `(file, symbol_name, kind)` | 2026-04-18 |
| Budget empirical (v1 carry-forward) | `--map-tokens 256 → 81 lines; 1024 → 253; 4096 → 965` | 2026-04-18 |
| Ranking (v1 carry-forward) | PageRank on symbol reference graph (`aider/repomap.py:525`); deterministic for fixed repo + model + budget | 2026-04-18 |

### jcodemunch-mcp probe

| Aspect | Finding | [valid] |
|---|---|---|
| `--transport` flag | `{stdio,sse,streamable-http}`; stdio is default | 2026-04-20 |
| Install path | `/home/sjnewhouse/.local/bin/jcodemunch-mcp` | 2026-04-20 |
| Tool (v1 carry-forward) | `get_ranked_context(query, token_budget=N)` returns budget-capped pack | 2026-04-18 |
| Tool (v1 carry-forward) | `search_symbols(top=N)` returns ranked symbol metadata | 2026-04-18 |
| Tool (v1 carry-forward) | `index_repo(owner/repo)`: public GitHub only; rejects local paths | 2026-04-18 |
| Symbol ID shape (v1) | `{file_path}::{qualified_name}#{kind}` | 2026-04-18 |
| Budget unit (v1) | `tiktoken cl100k_base` | 2026-04-18 |

### External tools (Repomix, Yek)

| Tool | Finding | [valid] |
|---|---|---|
| Repomix | Not on PATH at plan time; install via `npm install -g repomix` OR `npx -y repomix` | 2026-04-20 |
| Repomix invocation | `repomix --style xml --output /tmp/repomix-out.xml --token-count-encoding cl100k_base .` | 2026-04-20 |
| Yek | Not on PATH at plan time; install via `cargo install yek` OR pre-built | 2026-04-20 |
| Yek flags | `--tokens N --json` (confirmed in README; verify exact flags via `yek --help` at M2c start) | 2026-04-20 |

### tiktoken sanity

| Aspect | Finding | [valid] |
|---|---|---|
| cl100k_base import | `tiktoken.get_encoding("cl100k_base")` works | 2026-04-20 |
| Pinned version | `tiktoken==0.12.0` (resolved from `>=0.7` in pyproject.toml, v1 M2.1) | 2026-04-19 |

---

## External Claim Verification (2026-04-20)

| # | Claim | Verdict | Source | [valid] |
|---|---|---|---|---|
| 1 | Repomix `--style xml --token-count-encoding=cl100k_base <dir>` | CONFIRMED | github.com/yamadashy/repomix README | 2026-04-20 |
| 2 | Yek `--tokens N --json` | CONFIRMED | github.com/bodo-run/yek README | 2026-04-20 |
| 3 | Python MCP SDK is `mcp` on PyPI, current 1.27.0, has `mcp.client.stdio` | CONFIRMED | pypi.org/project/mcp/ | 2026-04-20 |
| 4 | RBO formula `(1-p) * Sum p^(d-1) * |S[:d] n T[:d]| / d`, p=0.9 convention | CONFIRMED | Webber, Moffat, Zobel 2010 (ACM TOIS) | 2026-04-20 |
| 5 | `rbo` PyPI package exists as cross-reference (test-only, not runtime) | CONFIRMED | pypi.org/project/rbo/ | 2026-04-20 |
| 6 | Aider v0.86.2 `--model gpt-3.5-turbo` uses cl100k_base via litellm | CONFIRMED | aider/models.py + litellm docs | 2026-04-20 |
| 7 | jcodemunch-mcp tools: `get_ranked_context(query, token_budget)` via MCP | CONFIRMED | USER_GUIDE.md in repo; v1 Phase-3 research | 2026-04-18 |
| 8 | fastapi 0.136.0 = 1119 py files, 56MB | PRE-VERIFIED | v1 Task 3.1 Result Log (direct `find`) | 2026-04-20 |
| 9 | pagerank.py `_CHARS_PER_TOKEN` constant location line 32 | VERIFIED | Read tool, 2026-04-20 | 2026-04-20 |
| 10 | jcodemunch-mcp supports stdio MCP transport | VERIFIED | `jcodemunch-mcp serve --help` | 2026-04-20 |
| 11 | tiktoken cl100k_base encodes correctly | VERIFIED | `uv run python -c "..."` | 2026-04-20 |

---

## Immutable Facts and Constants

### File Paths: To Create (v2)

| Path | Purpose | Milestone | [valid] |
|---|---|---|---|
| `tests/codemem/fixtures/jcodemunch_mcp_response.json` | Optional golden fixture for jCodeMunch MCP round-trip | M2a | 2026-04-20 |
| `tests/codemem/fixtures/repomix_output_aa-ma-forge.xml` | Golden Repomix XML output fixture | M2b | 2026-04-20 |
| `tests/codemem/fixtures/yek_output_aa-ma-forge.json` | Golden Yek JSON output fixture | M2c | 2026-04-20 |
| `docs/benchmarks/codemem-vs-aider-v2.md` | v2 benchmark report | M3 | 2026-04-20 |
| `docs/benchmarks/results-codemem-vs-aider-v2-2026-04-XX.json` | Combined 5-tool raw benchmark data | M3 | 2026-04-20 |

### File Paths: To Modify (v2)

| Path | Change | Milestone | [valid] |
|---|---|---|---|
| `packages/codemem-mcp/src/codemem/pagerank.py` | Remove `_CHARS_PER_TOKEN`; add module-level tiktoken cl100k_base encoder cache; swap `_fits()` to use encoder; round `rank` to 3 sig figs at emission (line 171) | M1 | 2026-04-20 |
| `tests/codemem/test_pagerank.py` | Update tests assuming 4-char proxy; add tests for tiktoken budget and rounded rank | M1 | 2026-04-20 |
| `scripts/bench_codemem_vs_aider.py` | Add `_run_jcodemunch`, `_run_repomix`, `_run_yek`; inline RBO; Aider `--model gpt-3.5-turbo` path | M2a/b/c | 2026-04-20 |
| `scripts/bench_sweep.py` | Extend aggregation loop from 3-tool to 5-tool | M2c | 2026-04-20 |
| `tests/codemem/test_bench_harness.py` | Add `TestJCodeMunchAdapter`, `TestRBOMetric`, `TestAiderModelOverride`, `TestRepomixAdapter`, `TestYekAdapter` | M2a/b/c | 2026-04-20 |
| `pyproject.toml` | Add `mcp>=1.27` dev dep (M2a); consider hoisting `tiktoken` from dev-only to runtime if pagerank imports at runtime (M1) | M1, M2a | 2026-04-20 |
| `docs/benchmarks/codemem-vs-aider.md` | Add "superseded by v2" banner at top (single edit, preserve v1 content) | M3 | 2026-04-20 |
| `docs/codemem/kill-criteria.md` | Second re-baseline of Signal 2 status line; bump "Latest update" header | M3 | 2026-04-20 |

### File Paths: To Reference (read-only)

| Path | Purpose | [valid] |
|---|---|---|
| `packages/codemem-mcp/src/codemem/storage/db.py` | M1 read-only verification | 2026-04-20 |
| `tests/codemem/conftest.py` | sys.path injection unchanged | 2026-04-20 |
| `tests/codemem/fixtures/aider_repo_map_aa-ma-forge.txt` | v1 golden, reused for M2a Aider-default-model parity check | 2026-04-18 |
| `tests/codemem/fixtures/codemem_intel_aa-ma-forge.json` | v1 golden, reused for M1 post-fix delta assertion | 2026-04-18 |
| `.claude/dev/active/codemem-token-benchmarks/` | v1 plan dir, M4 `/archive-aa-ma` target | 2026-04-20 |
| `.claude/dev/completed/codemem/codemem-plan.md` | Original codemem parent plan §12 kill-signal definition | 2026-04-18 |

### File Paths: Temporary / Throwaway

| Path | Purpose | [valid] |
|---|---|---|
| `/tmp/post-m1-intel.json` | M1 codemem post-fix smoke-test output | 2026-04-20 |
| `/tmp/v2a.json` | M2a single-budget 3-tool JSON | 2026-04-20 |
| `/tmp/v2b.json` | M2b single-budget 4-tool JSON | 2026-04-20 |
| `/tmp/v2c.json` | M2c single-budget 5-tool JSON | 2026-04-20 |
| `/tmp/v2-smoke.json` | Post-M4 smoke output | 2026-04-20 |
| `/tmp/bench-aa-ma-forge-v2.json` | M2c full sweep output on aa-ma-forge | 2026-04-20 |
| `/tmp/bench-fastapi-v2.json` | M2c full sweep output on fastapi | 2026-04-20 |
| `/tmp/bench-fastapi` | fastapi clone (v1 carry-forward) | 2026-04-18 |
| `/tmp/repomix-out.xml` | Repomix raw output per invocation | 2026-04-20 |

### Dependencies

| Package | Version | Class | New/Carry | [valid] |
|---|---|---|---|---|
| `aider-chat` | `==0.86.2` | Required (dev-tool) | carry-forward from v1 | 2026-04-18 |
| `jcodemunch-mcp` | `==1.59.1` | Required (dev-tool) | carry-forward from v1 | 2026-04-19 |
| `tiktoken` | `>=0.7` (resolved `0.12.0`) | Required (dev; may hoist to runtime in M1) | carry-forward from v1 | 2026-04-19 |
| `mcp` | `>=1.27` | Required (dev-dep) | NEW in M2a | 2026-04-20 |
| `rbo` | latest | Optional (test-only cross-reference) | NEW in M2a | 2026-04-20 |
| `repomix` (npm) | TBD at install | Required (external tool via npm or npx) | NEW in M2b | 2026-04-20 |
| `yek` (cargo) | TBD at install | Required (external tool via cargo) | NEW in M2c | 2026-04-20 |

### Install Commands (canonical)

```bash
# Carry-forward from v1
uv tool install aider-chat==0.86.2
uv tool install jcodemunch-mcp==1.59.1

# New in v2
uv sync                              # picks up mcp>=1.27 after pyproject.toml edit
npm install -g repomix               # or: npx -y repomix <args>
cargo install yek                    # or use pre-built binary
```

[valid: 2026-04-20]

### Configuration / CLI flags

| Key | Value | Purpose | [valid] |
|---|---|---|---|
| `--map-tokens` | `256 / 1024 / 2048 / 4096` | Aider budget flag (carry-forward) | 2026-04-18 |
| `--model` | `gpt-3.5-turbo` | Aider cl100k_base tokeniser equalisation | 2026-04-20 |
| `--show-repo-map` | (flag) | Aider repo-map emission mode | 2026-04-18 |
| `--requested-budget` | `512 / 1024 / 2048 / 4096` | harness CLI flag (carry-forward) | 2026-04-18 |
| `token_budget` | `N` (int) | jCodeMunch MCP parameter (carry-forward) | 2026-04-18 |
| `--budget` | `N` (int) | codemem CLI flag (carry-forward) | 2026-04-18 |
| `--transport` | `stdio` | jcodemunch-mcp serve mode | 2026-04-20 |
| `--style xml` | (Repomix) | emits structured XML packed format | 2026-04-20 |
| `--token-count-encoding cl100k_base` | (Repomix) | equalise tokeniser | 2026-04-20 |
| `--tokens N` | (Yek) | token budget flag | 2026-04-20 |
| `--json` | (Yek) | JSON output mode | 2026-04-20 |

### Constants

| Constant | Value | Context | [valid] |
|---|---|---|---|
| RBO persistence `p` | `0.9` | Webber et al. 2010 convention; top-heavy comparator | 2026-04-20 |
| RBO truncation depth `k` | `10` | `rbo_at_10` in harness output | 2026-04-20 |
| Budget sweep | `{512, 1024, 2048, 4096}` | carry-forward from v1 | 2026-04-18 |
| Run repetition | `3x` per measurement, report median | carry-forward (AD-006 v1) | 2026-04-18 |
| Tool panel size | `5` (codemem, aider, jcodemunch, repomix, yek) | v2 expansion from 3-tool v1 | 2026-04-20 |
| Overlap pair count | `10` pairs for 5 tools (C(5,2)) | new in v2 | 2026-04-20 |
| Full sweep cell count per repo | `20` (5 tools x 4 budgets) | new in v2 | 2026-04-20 |
| Expected full-sweep wall-clock | `20-60 minutes per repo` | unverified estimate (execution-time measurement) | 2026-04-20 |
| Codemem post-M1 baseline at budget=1024 (aa-ma-forge) | `>= 17 symbols` | v1 baseline; verify delta post-fix | 2026-04-20 |
| Rank rounding at emission | `3 significant figures` | M1 deliverable; regex `/^[01]\.\d{1,3}(e-?\d+)?$/` | 2026-04-20 |

### Signal 2 (from v1, still governing)

> Signal 2 M1-exit trigger = `codemem build > 1.5x /index wall-clock ON reference repos AND PageRank doesn't beat Aider`. AND composite. Task 4.1 measured 0.73x for the first conjunct on the small reference repo only (medium-repo and 50k-LOC measurements still pending per the archived kill-criteria.md status). Composite therefore remains **PROVISIONAL DID-NOT-TRIGGER**. v2 updates the Aider sub-claim only; composite verdict cannot be flipped to a pinned state until the pending wall-clock measurements land.

[valid: 2026-04-20]

### API / CLI Endpoints (5-tool panel)

| Tool | Invocation | Purpose | [valid] |
|---|---|---|---|
| codemem | `uv run codemem intel --budget=N --out=FILE` | PROJECT_INTEL.json emission | 2026-04-18 |
| aider | `aider --show-repo-map --map-tokens N --model gpt-3.5-turbo <repo>` | Repo-map emission, cl100k_base equalised | 2026-04-20 |
| jCodeMunch (MCP) | `get_ranked_context(query, token_budget=N)` over stdio transport | Ranked context pack | 2026-04-18 |
| jCodeMunch (MCP) | `search_symbols(top=N)` | Symbol search | 2026-04-18 |
| jCodeMunch (MCP) | `index_repo(owner/repo)` | Repo indexing (public GitHub only) | 2026-04-18 |
| Repomix | `repomix --style xml --output FILE --token-count-encoding cl100k_base <dir>` | Packed XML repo output | 2026-04-20 |
| Yek | `yek --tokens N --json <dir>` (verify exact flags at M2c start) | Git-importance-ordered packed output | 2026-04-20 |

### Benchmark Target Repos

| Repo | Clone path | Pinned commit | [valid] |
|---|---|---|---|
| aa-ma-forge | `.` (working repo) | HEAD of `expt/code_mem_store_what` (post-M4 of v1, `7a335fc` or later) | 2026-04-20 |
| tiangolo/fastapi | `/tmp/bench-fastapi` | `0.136.0` → `708606c982cf35718cb2214c0bb9261cf548f042` (1119 .py files, 56MB) | 2026-04-20 |
| Fallback | `pallets/click` | If fastapi too large for jCodeMunch (v1 carry-forward) | 2026-04-18 |

### Harness JSON Output Contract (v2)

Required top-level keys:

```
{
  "requested_budget": int,
  "tools": {
    "codemem":    { raw_bytes, tiktoken_tokens, symbol_count, status, ... },
    "aider":      { raw_bytes, tiktoken_tokens, symbol_count, status, ... },
    "jcodemunch": { raw_bytes, tiktoken_tokens, symbol_count, status, ... },
    "repomix":    { raw_bytes, tiktoken_tokens, symbol_count, status, ... },   // status may be "ok_no_symbols"
    "yek":        { raw_bytes, tiktoken_tokens, symbol_count, status, ... }
  },
  "overlap": {
    "codemem_vs_aider":      { jaccard, rbo_at_10, ... },
    "codemem_vs_jcodemunch": { jaccard, rbo_at_10, ... },
    "codemem_vs_repomix":    { jaccard, rbo_at_10, ... },
    "codemem_vs_yek":        { jaccard, rbo_at_10, ... },
    "aider_vs_jcodemunch":   { jaccard, rbo_at_10, ... },
    "aider_vs_repomix":      { jaccard, rbo_at_10, ... },
    "aider_vs_yek":          { jaccard, rbo_at_10, ... },
    "jcodemunch_vs_repomix": { jaccard, rbo_at_10, ... },
    "jcodemunch_vs_yek":     { jaccard, rbo_at_10, ... },
    "repomix_vs_yek":        { jaccard, rbo_at_10, ... }
  }
}
```

Tool `status` enum: `"ok"`, `"ok_no_symbols"`, `"skipped"`, `"error"`.

[valid: 2026-04-20]

### Git / Branch Facts

| Fact | Value | [valid] |
|---|---|---|
| Active branch | `expt/code_mem_store_what` | 2026-04-20 |
| Parent commit reference | `7a335fc` (v1 M4 shipped) | 2026-04-20 |
| v1 archive path (post-M4) | `.claude/dev/completed/codemem-token-benchmarks/` | 2026-04-20 |
| v2 active path | `.claude/dev/active/codemem-benchmark-fairness-v2/` | 2026-04-20 |
| Commit signature (this plan) | `[AA-MA Plan] codemem-benchmark-fairness-v2 .claude/dev/active/codemem-benchmark-fairness-v2` | 2026-04-20 |

### Quality Gates

| Gate | Requirement | [valid] |
|---|---|---|
| ruff | clean on all new / modified files | 2026-04-20 |
| import-linter | 2/2 contracts passing | 2026-04-20 |
| pytest default | >=387 passed | 2026-04-20 |
| pytest `-m slow` | >=2 passed (v1 + new v2 integration) | 2026-04-20 |
| Voice gate (M3 report) | `grep -c '—' docs/benchmarks/codemem-vs-aider-v2.md` returns 0; no AI vocab (`crucial`, `delve`, `leverage`, `landscape`) | 2026-04-20 |
| AA-MA commit signature | last footer line = `[AA-MA Plan] codemem-benchmark-fairness-v2 .claude/dev/active/codemem-benchmark-fairness-v2` | 2026-04-20 |

---

_Last Updated: 2026-04-20_
