# codemem-token-benchmarks Tasks (HTP)

_Hierarchical Task Planning roadmap with dependencies and state tracking._

---

## Milestone 1: Environment Setup + Precondition Re-Verification
- Status: PENDING
- Mode: HITL
- Gate: SOFT
- Dependencies: None
- Complexity: 25%
- Effort: ~1 focused-dev day
- Acceptance Criteria:
  - `aider --version` and `jcodemunch-mcp --version` (or equivalent) return pinned values
  - `uv run codemem intel --budget=1024 --out=/tmp/bench-intel-1024.json` produces file with `_meta.written_symbols >= 1` and PageRank-ranked `symbols[]`
  - HITL decision recorded in context-log.md under heading `## 2026-MM-DD — M1.3 scope decision`

### Task 1.1: Install Aider + jCodeMunch in throwaway uv tool env (pinned versions)
- Status: PENDING
- Mode: AFK
- Dependencies: None
- Acceptance Criteria:
  - `uv tool install aider-chat==0.86.2` succeeds
  - `uv tool install jcodemunch-mcp` succeeds (pin version recorded at install time)
  - `aider --version` returns `0.86.2`
  - `jcodemunch-mcp --version` (or equivalent) returns pinned value recorded in reference.md
- Result Log:

### Task 1.2: Re-run each tool's smoke test; confirm Phase-3 findings still hold
- Status: PENDING
- Mode: AFK
- Dependencies: Task 1.1
- Acceptance Criteria:
  - Aider v0.86.2 behavior matches Phase-3 research findings (format, `--map-tokens` flag, ranking ordering)
  - jCodeMunch MCP invocation shape matches documented userguide
  - codemem PROJECT_INTEL schema matches the contract in reference.md (`{_meta, symbols[]}`, per-entry `{scip_id, name, kind, file, line, rank}`)
  - Any divergence from Phase-3 findings is documented in context-log.md and triggers an M1 extension
- Result Log:

### Task 1.3: HITL decision gate — confirm scope
- Status: PENDING
- Mode: HITL
- Dependencies: Task 1.2
- Acceptance Criteria:
  - User confirms scope: size+coverage (default) OR size-only / qualitative / cancel
  - Decision recorded in context-log.md under heading `## 2026-MM-DD — M1.3 scope decision`
  - Proceeding to M2 is blocked until this gate is recorded
- Result Log:

---

## Milestone 2: Harness + Parser (TDD)
- Status: PENDING
- Mode: AFK
- Gate: SOFT
- Dependencies: Milestone 1
- Complexity: 55%
- Effort: ~1.5-2 focused-dev days
- Acceptance Criteria:
  - `uv run pytest tests/codemem/test_bench_harness.py` → all green
  - `uv run python scripts/bench_codemem_vs_aider.py --repo . --requested-budget 1024 --out /tmp/bench.json` → produces valid JSON with keys `{requested_budget, tools: {codemem, aider, jcodemunch}, overlap}`
  - Ruff clean on new files
  - Import-linter still 2/2 (no changes to package boundaries)

### Task 2.1: Add `tiktoken` as dev dep in root pyproject.toml
- Status: PENDING
- Mode: AFK
- Dependencies: Milestone 1
- Acceptance Criteria:
  - `pyproject.toml` has `tiktoken` under dev dependency group
  - `uv sync` succeeds
  - `uv run python -c "import tiktoken; print(tiktoken.encoding_for_model('gpt-4'))"` succeeds
- Result Log:

### Task 2.2: TDD — write parser unit tests with golden Aider fixture
- Status: PENDING
- Mode: AFK
- Dependencies: Task 2.1
- Acceptance Criteria:
  - `tests/codemem/fixtures/aider_repo_map_aa-ma-forge.txt` captured from live Aider invocation against aa-ma-forge
  - `tests/codemem/test_bench_harness.py` exists with failing tests for Aider prose-output parser
  - Tests assert parser extracts `(file, symbol_name, kind)` rows from golden fixture
  - Test file follows project pytest conventions
- Result Log:

### Task 2.3: GREEN — implement Aider parser (inline unless > 100 LOC)
- Status: PENDING
- Mode: AFK
- Dependencies: Task 2.2
- Acceptance Criteria:
  - Parser logic implemented (inline in `bench_codemem_vs_aider.py` OR in `scripts/bench_aider_parser.py` if > 100 LOC)
  - All tests from Task 2.2 pass
  - Parser handles `│def`, `│class`, `│@` prefixes and `⋮` elision marker
  - Ruff clean on new code
- Result Log:

### Task 2.4: TDD — tiktoken normalization test
- Status: PENDING
- Mode: AFK
- Dependencies: Task 2.3
- Acceptance Criteria:
  - Test file includes tiktoken normalization test
  - Given captured outputs from all 3 tools at requested budget 1024, test asserts `len(tiktoken.encode(output_text))` produces a comparable integer for each
  - Test verifies the output contract shape (raw_bytes, tiktoken_tokens, symbol_count) is populated correctly
- Result Log:

### Task 2.5: Implement `scripts/bench_codemem_vs_aider.py` harness
- Status: PENDING
- Mode: AFK
- Dependencies: Task 2.4
- Acceptance Criteria:
  - Script invokes all 3 tools at a configurable `--requested-budget`
  - Captures outputs, normalizes via tiktoken
  - Emits comparison JSON with per-tool (a) raw output size bytes, (b) tiktoken-counted tokens, (c) symbol-row count, (d) top-N overlap via Jaccard against codemem's symbols
  - Script is invokable as `uv run python scripts/bench_codemem_vs_aider.py --repo . --requested-budget N --out FILE`
  - Ruff clean
- Result Log:

### Task 2.6: Integration test — harness self-exercises against aa-ma-forge
- Status: PENDING
- Mode: AFK
- Dependencies: Task 2.5
- Acceptance Criteria:
  - Integration test runs the harness against aa-ma-forge
  - Asserts structured JSON output with all 3 tools present under `tools` key
  - Asserts `requested_budget` and `overlap` keys present
  - Test handles known edge case: jCodeMunch may require remote fixture (log and skip if unavoidable)
  - Import-linter contracts still 2/2
- Result Log:

---

## Milestone 3: Execute
- Status: PENDING
- Mode: AFK
- Gate: SOFT
- Dependencies: Milestone 2
- Complexity: 30%
- Effort: ~1 focused-dev day
- Acceptance Criteria:
  - Two JSON result files on disk, each containing all 4 budget levels × 3 tools = 12 measurements
  - No tool-invocation failures (or failures are explicitly recorded in the JSON)
  - At least one clear data point — e.g. codemem's symbol count vs Aider's at budget=1024 — is quotable for the report

### Task 3.1: Clone fastapi at pinned commit into /tmp/bench-fastapi
- Status: PENDING
- Mode: AFK
- Dependencies: Milestone 2
- Acceptance Criteria:
  - `tiangolo/fastapi` cloned into `/tmp/bench-fastapi`
  - Pinned commit SHA recorded in provenance.log
  - `.git` present (for tool introspection if needed)
- Result Log:

### Task 3.2: Run harness against aa-ma-forge at budgets {512, 1024, 2048, 4096}
- Status: PENDING
- Mode: AFK
- Dependencies: Task 3.1
- Acceptance Criteria:
  - `/tmp/bench-aa-ma-forge.json` exists
  - Contains 4 budget × 3 tools = 12 measurements
  - Each measurement has raw_bytes, tiktoken_tokens, symbol_count fields
  - Each measurement is a median of 3 runs (per AD-006)
- Result Log:

### Task 3.3: Run harness against fastapi at same budget sweep
- Status: PENDING
- Mode: AFK
- Dependencies: Task 3.1
- Acceptance Criteria:
  - `/tmp/bench-fastapi.json` exists
  - Contains 4 budget × 3 tools = 12 measurements
  - If fastapi is too large for jCodeMunch: fallback to `pallets/click` recorded in provenance.log with deviation note
- Result Log:

### Task 3.4: Sanity check — all outputs non-empty, symbol count > 0
- Status: PENDING
- Mode: AFK
- Dependencies: Tasks 3.2, 3.3
- Acceptance Criteria:
  - For each tool at each budget in both JSON files: output is non-empty
  - For each tool at each budget in both JSON files: symbol_count > 0
  - Any zero-result cell is explicitly flagged in the JSON with an error reason
- Result Log:

---

## Milestone 4: Report + Integrate
- Status: PENDING
- Mode: HITL
- Gate: SOFT
- Dependencies: Milestone 3
- Complexity: 40%
- Effort: ~1 focused-dev day
- Acceptance Criteria:
  - `docs/benchmarks/codemem-vs-aider.md` committed, passes stephen-newhouse-voice (no marketing, direct, honest about limits)
  - `docs/codemem/kill-criteria.md` Signal 1 status updated to reflect actual measurement
  - If Signal 1 fires: `context-log.md` records the architectural-kill event with a linked pointer to the root cause (tokenization inefficiency / algorithm choice / etc)
  - Commit pushed; CI green

### Task 4.1: Draft docs/benchmarks/codemem-vs-aider.md
- Status: PENDING
- Mode: HITL
- Dependencies: Milestone 3
- Acceptance Criteria:
  - Structure: Methodology (with tokenizer-mismatch caveats PROMINENT) → Results Tables (2 repos × 4 budgets × 3 tools) → Per-signal verdict (size, top-symbol overlap, qualitative) → Implications for kill-criteria §1
  - Starts with 15-min sanity pass over M3 JSON before drafting (per M4 R3 mitigation)
  - User reviews wording, revision cycle applied until stephen-newhouse-voice approval
  - Committed `docs/benchmarks/results-codemem-vs-aider-2026-04-18.json` alongside
- Result Log:

### Task 4.2: Update docs/codemem/kill-criteria.md Signal 1 status line
- Status: PENDING
- Mode: HITL
- Dependencies: Task 4.1
- Acceptance Criteria:
  - Signal 1 status line replaces the 2026-04-17 "DID NOT trigger ... Aider comparison DEFERRED" text
  - Status reflects actual measurement:
    - Case (a) codemem ≤ 1.5× → "DID NOT trigger, confirmed"
    - Case (b) codemem > 1.5× → "FIRED — architectural kill triggered"
    - Case (c) ambiguous → "provisional — see benchmark §X for discussion"
  - If Signal 1 fires: architectural-kill event recorded in context-log.md with root-cause pointer
- Result Log:

### Task 4.3: Commit with AA-MA signature
- Status: PENDING
- Mode: AFK
- Dependencies: Task 4.2
- Acceptance Criteria:
  - Commit message uses Conventional Commits format
  - Last footer line: `[AA-MA Plan] codemem-token-benchmarks .claude/dev/active/codemem-token-benchmarks`
  - No AI attribution
  - Commit pushed to `expt/code_mem_store_what`
  - CI green
- Result Log:
