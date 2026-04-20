# codemem-token-benchmarks Reference

_Load-first priority file. Contains immutable facts, Phase-3 research findings, and the tokenizer-mismatch invariant. An agent resuming this task reads THIS FILE FIRST._

---

## TOP PRIORITY: Tokenizer-Mismatch Invariant

**When benchmarking, NEVER compare raw output sizes at "equal requested budget" alone — tools count budgets differently.**

Every measurement MUST report three numbers:
- **(a) Raw output bytes** — the actual file/string size produced
- **(b) tiktoken-counted tokens** — external normalization via `tiktoken.encoding_for_model("gpt-4").encode(text)`
- **(c) Symbol-row count** — semantic unit count

Reason: codemem uses a `4 chars/token` proxy, Aider uses tiktoken against the configured model, jCodeMunch uses tiktoken `cl100k_base`. A "1024-token budget" means three different things across the three tools.

---

## Phase-3 Research Findings (2026-04-18)

_Three parallel research agents resolved all preconditions cited in the 2026-04-17 DEFERRAL. Findings below are empirically verified unless marked "(docs-sourced)"._

### Aider (empirically verified, `aider-chat` v0.86.2)

| Aspect | Finding |
|--------|---------|
| **Output format** | Hybrid prose/markdown — tree-sitter-style symbol skeletons grouped by file. `│def`/`│class`/`│@` prefixes on signature lines; `⋮` elision marker. Designed for LLM-prompt injection, not JSON consumption. Regex-extractable to `(file, symbol_name, kind)` tuples. [valid: 2026-04-18] |
| **Budget flag** | `--map-tokens N` (default adaptive 1024-4096 via `aider/models.py:767-774`; counted via tiktoken against the configured model). Empirically: `--map-tokens 256 → 81 lines; 1024 → 253; 4096 → 965`. [valid: 2026-04-18] |
| **Ranking** | PageRank on symbol reference graph (`aider/repomap.py:525`). Deterministic given fixed repo + model + budget. [valid: 2026-04-18] |
| **Scores NOT exposed** | Output ordering implies rank; no per-symbol float scores. [valid: 2026-04-18] |
| **Install command (pinned)** | `uv tool install aider-chat==0.86.2` [valid: 2026-04-18] |

### jCodeMunch (docs-sourced, `jgravelle/jcodemunch-mcp`)

| Aspect | Finding |
|--------|---------|
| **Output format** | Structured JSON (with optional compact "MUNCH" wire format via `format=compact`). `search_symbols` returns ranked symbol metadata; `get_ranked_context(query, token_budget=N)` returns a budget-capped pack. Symbol IDs: `{file_path}::{qualified_name}#{kind}`. [valid: 2026-04-18] |
| **Budget flag** | `token_budget=N` on multiple tools (`get_ranked_context`, `search_symbols`, `get_context_bundle`). Unit: tiktoken `cl100k_base`. [valid: 2026-04-18] |
| **Ranking** | PageRank on import graph (per `get_symbol_importance`). Direct PageRank parity with codemem. [valid: 2026-04-18] |
| **95% benchmark methodology** | Measured on `search_symbols(top 5) + get_symbol_source × 3` workflow, NOT semantic retrieval. Semantic search is opt-in (`semantic=true`). [valid: 2026-04-18] |
| **Public-repo fixture requirement** | `index_repo` rejects local paths — requires GitHub `owner/repo` format. fastapi satisfies this. [valid: 2026-04-18] |
| **Install command** | `uv tool install jcodemunch-mcp==1.59.1` (pinned 2026-04-19; binaries installed: `gcm`, `jcodemunch-mcp`, `munch-bench`) [valid: 2026-04-19] |
| **Userguide cache** | `/tmp/jcm_userguide.md` (Phase-3 research artifact) [valid: 2026-04-18] |

### codemem PROJECT_INTEL.json (empirical ground truth)

| Aspect | Finding |
|--------|---------|
| **Top-level keys** | `{_meta: object, symbols: array}` — rank-sorted by `-rank`. [valid: 2026-04-18] |
| **Per-entry shape** | `{scip_id: str, name: str, kind: str, file: str, line: int, rank: float}`. [valid: 2026-04-18] |
| **Default budget (1024) on aa-ma-forge at HEAD `3ab0aa9`** | 17 symbols, 4003 bytes. [valid: 2026-04-18] |
| **Budget mechanics (soft)** | Binary-search longest rank-ordered prefix fitting `budget * 4 chars`. Logic in `packages/codemem-mcp/src/codemem/pagerank.py:132-194`. [valid: 2026-04-18] |
| **Proxy divergence** | Uses `4 chars/token` vs tiktoken. Real bytes/token varies by content — for benchmark parity, re-tokenize all outputs with tiktoken. [valid: 2026-04-18] |
| **Top-N source** | `symbols[]` array directly. Ranking exposed as per-entry `rank: float`. Join surface against Aider: `(file, symbol_name)` tuple. [valid: 2026-04-18] |

### Blockers Resolved

| Blocker (from 2026-04-17 deferral) | Status |
|-------------------------------------|--------|
| Aider CLI surface | RESOLVED — `--map-tokens` + `--show-repo-map` [valid: 2026-04-18] |
| jCodeMunch output shape | RESOLVED — structured JSON [valid: 2026-04-18] |
| PROJECT_INTEL schema | RESOLVED — full contract in `pagerank.py` [valid: 2026-04-18] |

---

## Immutable Facts and Constants

_Non-negotiable facts extracted from the plan and research._

### File Paths

#### To Create
| Path | Purpose | Milestone |
|------|---------|-----------|
| `scripts/bench_codemem_vs_aider.py` | Benchmark harness | M2.5 [valid: 2026-04-18] |
| `tests/codemem/test_bench_harness.py` | Parser + normalization tests | M2.2 [valid: 2026-04-18] |
| `tests/codemem/fixtures/aider_repo_map_aa-ma-forge.txt` | Golden Aider output fixture | M2.2 [valid: 2026-04-18] |
| `docs/benchmarks/results-codemem-vs-aider-2026-04-18.json` | Raw benchmark data (committed) | M3 [valid: 2026-04-18] |
| `docs/benchmarks/codemem-vs-aider.md` | Benchmark report | M4.1 [valid: 2026-04-18] |

#### To Modify
| Path | Change | Milestone |
|------|--------|-----------|
| `pyproject.toml` | Add `tiktoken` dev dep | M2.1 [valid: 2026-04-18] |
| `docs/codemem/kill-criteria.md` | Update **Signal 2** (M1 architectural kill) status line — composite DID-NOT-TRIGGER stays pinned by Task 4.1's 0.73× wall-clock; Aider sub-claim status updates per M3 findings | M4.2 [valid: 2026-04-18] |

#### To Reference (read-only)
| Path | Purpose | [valid] |
|------|---------|---------|
| `.claude/dev/completed/codemem/codemem-plan.md` | Parent plan §12 kill-signal definition | 2026-04-18 |
| `packages/codemem-mcp/src/codemem/pagerank.py` | Budget mechanics (lines 132-194) | 2026-04-18 |
| `/tmp/jcm_userguide.md` | jCodeMunch userguide cache | 2026-04-18 |

#### Temporary / Throwaway
| Path | Purpose | [valid] |
|------|---------|---------|
| `/tmp/bench-intel-1024.json` | codemem smoke-test output | 2026-04-18 |
| `/tmp/bench-aa-ma-forge.json` | M3.2 aa-ma-forge results | 2026-04-18 |
| `/tmp/bench-fastapi.json` | M3.3 fastapi results | 2026-04-18 |
| `/tmp/bench-fastapi` | fastapi clone | 2026-04-18 |
| `/tmp/bench.json` | M2 harness self-exercise output | 2026-04-18 |

### Dependencies

| Package | Version | Class | [valid] |
|---------|---------|-------|---------|
| `aider-chat` | `==0.86.2` (pinned) | dev-tool (uv tool install) | 2026-04-18 |
| `jcodemunch-mcp` | `==1.59.1` (pinned, recorded at M1.1 install) | dev-tool (uv tool install) | 2026-04-19 |
| `tiktoken` | `>=0.7` in pyproject.toml; resolved to `0.12.0` at install | dev-only (pyproject.toml) | 2026-04-19 |

### Install Commands (canonical)

```bash
uv tool install aider-chat==0.86.2
uv tool install jcodemunch-mcp==1.59.1  # pinned at M1.1 (installed 2026-04-19, binaries: gcm, jcodemunch-mcp, munch-bench)
```

### Configuration

| Key | Value | Purpose | [valid] |
|-----|-------|---------|---------|
| `--map-tokens` | `256 / 1024 / 2048 / 4096` | Aider budget flag | 2026-04-18 |
| `--requested-budget` | `512 / 1024 / 2048 / 4096` | harness CLI flag | 2026-04-18 |
| `token_budget` | `N` (int) | jCodeMunch parameter | 2026-04-18 |
| `--budget` | `N` (int) | codemem CLI flag | 2026-04-18 |
| `format` | `compact` (optional) | jCodeMunch wire format | 2026-04-18 |
| `semantic` | `true` (opt-in) | jCodeMunch semantic search | 2026-04-18 |

### Constants

| Constant | Value | Context | [valid] |
|----------|-------|---------|---------|
| Signal 2 M1-exit trigger | `codemem build > 1.5× /index wall-clock ON reference repos AND PageRank doesn't beat Aider` | **AND composite.** Task 4.1 measured 0.73× for the first conjunct **on the small reference repo only** (medium-repo and 50k-LOC measurements still pending per the archived kill-criteria.md status). Composite therefore remains **PROVISIONAL DID-NOT-TRIGGER** — this benchmark updates the Aider sub-claim only; the composite verdict cannot be flipped to a pinned state until the pending wall-clock measurements land. | 2026-04-18 |
| Tokenizer-bias direction | codemem disadvantaged | At `requested_budget=1024`, codemem emits ≤4096 chars via its 4-char/token proxy, while Aider/jCodeMunch emit ≤1024 tiktoken tokens (~800-1200 chars). Without external normalization, codemem systematically emits less content at "equal" budget. Report BOTH raw-requested and tiktoken-equalized measurements in M4.1. | 2026-04-18 |
| Budget sweep | `{512, 1024, 2048, 4096}` | M3 benchmark budgets | 2026-04-18 |
| Top-N overlap metric | Jaccard against codemem's symbols | M2.5 harness metric | 2026-04-18 |
| Codemem char/token proxy | `4 chars/token` | Internal to codemem; source of normalization need | 2026-04-18 |
| Parser LOC threshold | `100` LOC | If Aider parser > 100 LOC → split to `scripts/bench_aider_parser.py`; else inline | 2026-04-18 |
| Run repetition | `3×` per measurement, report median | Matches Task 4.1 `bench_codemem.py` pattern | 2026-04-18 |
| codemem CLI availability | `uv sync` required once in the aa-ma-forge project env | `codemem` is a workspace-member console script; every M1+ task that does `uv run codemem ...` assumes project deps are installed. Not a task step — implicit prerequisite. | 2026-04-18 |

### API / CLI Endpoints

| Tool | Invocation | Purpose | [valid] |
|------|-----------|---------|---------|
| codemem | `uv run codemem intel --budget=N --out=FILE` | PROJECT_INTEL.json emission | 2026-04-18 |
| aider | `aider --show-repo-map --map-tokens N` | Repo-map emission | 2026-04-18 |
| jCodeMunch | MCP tool `get_ranked_context(query, token_budget=N)` | Ranked context pack | 2026-04-18 |
| jCodeMunch | MCP tool `search_symbols(top=N)` | Symbol search | 2026-04-18 |
| jCodeMunch | MCP tool `index_repo(owner/repo)` | Repo indexing (public GitHub only) | 2026-04-18 |

### Benchmark Target Repos

| Repo | Clone path | Pinned commit | [valid] |
|------|-----------|---------------|---------|
| aa-ma-forge | `.` (working repo) | HEAD `3ab0aa9` or later | 2026-04-18 |
| tiangolo/fastapi | `/tmp/bench-fastapi` | `0.136.0` → `708606c982cf35718cb2214c0bb9261cf548f042` (1119 .py files, 56MB) | 2026-04-20 |
| Fallback | `pallets/click` | If fastapi too large for jCodeMunch | 2026-04-18 |

### Harness JSON Output Contract

Required top-level keys in harness output:
```
{
  "requested_budget": int,
  "tools": {
    "codemem":    { raw_bytes, tiktoken_tokens, symbol_count, ... },
    "aider":      { raw_bytes, tiktoken_tokens, symbol_count, ... },
    "jcodemunch": { raw_bytes, tiktoken_tokens, symbol_count, ... }
  },
  "overlap": { ... }    // Jaccard metrics keyed by tool-pair
}
```

### Git / Branch Facts

| Fact | Value | [valid] |
|------|-------|---------|
| Active branch | `expt/code_mem_store_what` | 2026-04-18 |
| Parent commit reference | `3ab0aa9` (codemem archive) | 2026-04-18 |
| Archive path | `.claude/dev/completed/codemem/` | 2026-04-18 |
| Commit signature (this plan) | `[AA-MA Plan] codemem-token-benchmarks .claude/dev/active/codemem-token-benchmarks` | 2026-04-18 |

### Quality Gates (from project rules)

| Gate | Requirement | [valid] |
|------|-------------|---------|
| ruff | clean on all new files | 2026-04-18 |
| import-linter | 2/2 contracts passing | 2026-04-18 |
| pytest | `tests/codemem/test_bench_harness.py` green | 2026-04-18 |
| CI | green before M4 merge | 2026-04-18 |

---

_Last Updated: 2026-04-19_
