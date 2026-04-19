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
- Status: COMPLETE
- Mode: AFK
- Dependencies: None
- Acceptance Criteria:
  - `uv tool install aider-chat==0.86.2` succeeds
  - `uv tool install jcodemunch-mcp` succeeds (pin version recorded at install time)
  - `aider --version` returns `0.86.2`
  - `jcodemunch-mcp --version` (or equivalent) returns pinned value recorded in reference.md
- Result Log:
  ✅ COMPLETE 2026-04-19 — all 4 acceptance criteria empirically satisfied.

  **Empirical state at execution (2026-04-19):**
  - `uv --version` → `uv 0.7.19`
  - `uv tool list` shows `aider-chat v0.86.2` (binary: `aider`) — AC#1 satisfied
  - `uv tool list` shows `jcodemunch-mcp v1.59.1` (binaries: `gcm`, `jcodemunch-mcp`, `munch-bench`) — AC#2 satisfied
  - `aider --version` → `aider 0.86.2` — AC#3 satisfied
  - `jcodemunch-mcp --version` → `jcodemunch-mcp 1.59.1` — AC#4 satisfied

  **Divergence from plan:** Installs pre-existed from the Phase-3 research session (2026-04-18) where agents verified tool behavior to resolve the three original DEFERRED preconditions. The formal Task 1.1 closure was never written at that time — a sub-step drift (L-080) that surfaced when this execution cycle performed the empirical pre-flight check (`uv tool list`). Applied KISS: no reinstall (would add risk for zero signal since versions are exact match to plan's pin targets). Recorded findings into reference.md instead.

  **Reference.md updates (this commit):**
  - Dependencies table: `jcodemunch-mcp` version `TBD at M1.1 (pin on install)` → `==1.59.1 (pinned, recorded at M1.1 install)`
  - Install commands block: added `==1.59.1` pin + binaries note
  - jCodeMunch Phase-3 table row: install command updated with binaries + 2026-04-19 valid-date
  - Last Updated: `2026-04-18 12:00` → `2026-04-19`

  **Decisions/assumptions:** None new. Used pre-existing AD-003 (pin Aider at 0.86.2; pin jCodeMunch at M1.1 install time) — both satisfied.

### Task 1.2: Re-run each tool's smoke test; confirm Phase-3 findings still hold
- Status: COMPLETE
- Mode: AFK
- Dependencies: Task 1.1
- Acceptance Criteria (falsifiable):
  - `aider --help 2>&1 | grep -c "map-tokens"` returns `>= 1` (flag still exists)
  - `aider --show-repo-map --map-tokens 1024` run from aa-ma-forge root emits stdout containing both `│def ` and `│class ` markers AND at least one `⋮` elision (prose format unchanged)
  - ~~`jcodemunch-mcp --help 2>&1` returns exit 0 AND mentions at least one of: `token_budget`, `search_symbols`, `get_ranked_context`~~ **REFRAMED 2026-04-19 (see context-log M1.2 divergence):** `jcodemunch-mcp --help 2>&1` returns exit 0 AND includes `serve` subcommand AND `jcodemunch-mcp config` shows a `Tool Profile` row. Rationale: MCP tool names (`token_budget`, `search_symbols`, `get_ranked_context`) are runtime-only MCP protocol artifacts, not CLI-level; original AC wording was a category error. Phase-3 findings on MCP-runtime tool surface remain valid; they will be re-verified at M2 harness time via actual MCP protocol exercise.
  - `uv run codemem intel --budget=1024 --out=/tmp/bench-intel-1024.json` produces JSON with `_meta.written_symbols >= 1` AND per-entry shape `{scip_id, name, kind, file, line, rank}` (schema unchanged)
  - Any divergence triggers a `## 2026-MM-DD — M1.2 divergence` entry in context-log.md and extends M1 to re-research
- Result Log:
  ✅ COMPLETE 2026-04-19 — 3 AC passed as-written; 1 AC reframed after divergence audit (HITL-approved).

  **Empirical results (2026-04-19):**
  - **AC#1** — `aider --help 2>&1 | grep -c "map-tokens"` = `2` (expected >= 1). ✅
  - **AC#2** — `aider --show-repo-map --map-tokens 1024` from aa-ma-forge root emitted 269 lines with `43 │def`, `10 │class`, `78 ⋮` occurrences. All three prose markers present; 269 lines is close to the Phase-3 finding of ~253 (trivial drift from codebase growth). Parser surface unchanged. ✅
  - **AC#3** — DIVERGENCE + REFRAM. Probed `jcodemunch-mcp --help` top-level AND 6 subcommand helps (`serve`, `watch`, `config`, `claude-md`, `index`, `init`): zero occurrences of `token_budget` / `search_symbols` / `get_ranked_context`. Tool IS functional: exit 0, `serve` subcommand present, `jcodemunch-mcp config` shows `Tool Profile: full (all tools)` (default). Concluded: AC#3 wording was a category error — MCP tool names are runtime-only protocol artifacts, not CLI help text. Divergence entry written to context-log.md (`## 2026-04-19 — M1.2 divergence`). AC reframed above to reality-aligned CLI-level sanity check. ✅ (per reframed AC)
  - **AC#4** — `uv run codemem intel --budget=1024 --out=/tmp/bench-intel-1024.json` produced JSON: `_meta.written_symbols = 17`, `symbols[]` length 17, per-entry keys `[file, kind, line, name, rank, scip_id]` — matches plan spec exactly. 4003 bytes — matches Phase-3 finding exactly. Schema stable. ✅

  **Artifacts produced:**
  - `/tmp/bench-intel-1024.json` (4003B, 17 symbols — throwaway, will be regenerated by M3 budget sweeps)

  **Phase-3 findings held:** All substantive findings intact. Only divergence was AC#3's CLI-vs-MCP-runtime category error; corrected.

  **Decisions this task:** AC#3 reframe approved via HITL gate (user chose "Reframe AC#3 & proceed" option 2026-04-19).

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
  - `docs/codemem/kill-criteria.md` **Signal 2** (M1 architectural kill) status updated — Signal 2's composite remains PROVISIONAL DID-NOT-TRIGGER (Task 4.1's 0.73× cleared condition (a) only on the small repo; medium+large pending); this benchmark updates the Aider sub-claim only
  - If codemem loses the Aider sub-comparison: `context-log.md` records the event as a **risk-signal, not a kill** (Signal 2 composite remains PROVISIONAL) with a linked pointer to the root cause (tokenizer proxy / algorithm choice / etc)
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

### Task 4.2: Update docs/codemem/kill-criteria.md Signal 2 (M1 architectural kill) status line
- Status: PENDING
- Mode: HITL
- Dependencies: Task 4.1
- Acceptance Criteria:
  - Signal 2 status line replaces the 2026-04-17 "Aider token-efficiency comparison is deferred post-M4-ship" text with the benchmark findings, while preserving the "DID NOT trigger" composite verdict (Task 4.1's 0.73× wall-clock kept the AND composite from firing regardless of this benchmark)
  - Status reflects actual measurement:
    - Case (a) codemem ≤ 1.5× → "DID NOT trigger, confirmed"
    - Case (b) codemem > 1.5× → "FIRED — architectural kill triggered"
    - Case (c) ambiguous → "provisional — see benchmark §X for discussion"
  - If codemem loses Aider sub-comparison: risk-signal (not kill) recorded in context-log.md with root-cause pointer — Signal 2 composite remains PROVISIONAL DID-NOT-TRIGGER (small repo only; medium+large still pending per kill-criteria.md status)
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
