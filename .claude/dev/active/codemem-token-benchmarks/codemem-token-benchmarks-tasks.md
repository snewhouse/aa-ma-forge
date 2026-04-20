# codemem-token-benchmarks Tasks (HTP)

_Hierarchical Task Planning roadmap with dependencies and state tracking._

---

## Milestone 1: Environment Setup + Precondition Re-Verification
- Status: COMPLETE
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
- Status: COMPLETE
- Mode: HITL
- Dependencies: Task 1.2
- Acceptance Criteria:
  - User confirms scope: size+coverage (default) OR size-only / qualitative / cancel
  - Decision recorded in context-log.md under heading `## 2026-MM-DD — M1.3 scope decision`
  - Proceeding to M2 is blocked until this gate is recorded
- Result Log:
  ✅ COMPLETE 2026-04-19 — HITL scope decision recorded. All 3 AC satisfied.

  **Empirical gate resolution:**
  - User selected **`size+coverage` (AD-002 default)** at HITL gate via AskUserQuestion 2026-04-19.
  - Decision recorded in context-log.md under `## 2026-04-19 — M1.3 scope decision` as **AD-008**. ✅
  - M2 is now unblocked — M2 task structure already assumes size+coverage scope, no AC revisions needed. ✅

  **Scope confirmed:**
  - Size axis: raw bytes + tiktoken tokens + symbol count per tool per measurement
  - Coverage axis: top-N Jaccard overlap on symbol sets across tool pairs
  - Budget sweep: `{512, 1024, 2048, 4096}` (from reference.md Constants)
  - Repos: aa-ma-forge + tiangolo/fastapi (fallback pallets/click per M3 R1)

  **Alternatives presented at the gate (all rejected with rationale in AD-008):**
  - size-only, qualitative, cancel

  **Decisions:** AD-008 pins AD-002 (provisional → confirmed).

  **Next:** M1 milestone finalization → M2 start (Task 2.1: Add tiktoken dev dep).

---

## Milestone 2: Harness + Parser (TDD)
- Status: ACTIVE
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
- Status: COMPLETE
- Mode: AFK
- Dependencies: Milestone 1
- Acceptance Criteria:
  - `pyproject.toml` has `tiktoken` under dev dependency group
  - `uv sync` succeeds
  - `uv run python -c "import tiktoken; print(tiktoken.encoding_for_model('gpt-4'))"` succeeds
- Result Log:
  ✅ COMPLETE 2026-04-19 — all 3 AC empirically satisfied.

  **Empirical verification (2026-04-19):**
  - **AC#1** — `pyproject.toml:31` now contains `"tiktoken>=0.7",  # codemem-token-benchmarks M2: external tokenizer for cross-tool normalization` in `[tool.uv] dev-dependencies`. Confirmed via file diff. ✅
  - **AC#2** — `uv sync` completed successfully; tiktoken installed to project `.venv`. Resolved version: `0.12.0`. ✅
  - **AC#3** — `uv run python -c "import tiktoken; print(tiktoken.encoding_for_model('gpt-4'))"` outputs `<Encoding 'cl100k_base'>`. ✅

  **Cross-validation insight:** `gpt-4` → `cl100k_base` — which matches jCodeMunch's tokenizer per reference.md §jCodeMunch ("Unit: tiktoken cl100k_base"). This confirms the harness tokenizer is aligned with jCodeMunch's internal unit. Aider uses tiktoken-against-configured-model (may vary by OpenAI vs Anthropic config). Codemem uses a 4-char/token proxy. All three outputs will be re-tokenized at harness time via `cl100k_base` for apples-to-apples comparison (per plan's tokenizer-mismatch invariant).

  **Reference.md updates (this commit):**
  - Dependencies table: tiktoken `latest from PyPI` → `>=0.7 in pyproject.toml; resolved to 0.12.0 at install` + valid-date 2026-04-19

  **Decisions:** None new. Used AD-001 (external tiktoken normalization).

### Task 2.2: TDD — write parser unit tests with golden Aider fixture
- Status: COMPLETE
- Mode: AFK
- Dependencies: Task 2.1
- Acceptance Criteria:
  - `tests/codemem/fixtures/aider_repo_map_aa-ma-forge.txt` captured from live Aider invocation against aa-ma-forge
  - `tests/codemem/test_bench_harness.py` exists with failing tests for Aider prose-output parser
  - Tests assert parser extracts `(file, symbol_name, kind)` rows from golden fixture
  - Test file follows project pytest conventions
- Result Log:
  ✅ COMPLETE 2026-04-20 — TDD RED verified. All 4 AC empirically satisfied. 12 failing tests collected; parser module intentionally absent.

  **Empirical verification:**
  - **AC#1** — `tests/codemem/fixtures/aider_repo_map_aa-ma-forge.txt` captured live via `aider --show-repo-map --map-tokens 1024` at aa-ma-forge HEAD `af10ec6` (aider 0.86.2). 257 lines (within Phase-3 drift tolerance of 253±15). Empirical counts: 59 symbol lines (│def/│class/│@), 78 elision markers (⋮), 22 naive "line ends with :" candidates (including 1 known wrapped-signature continuation `dict:` on line 18 — see AC#3 regression guard). ✅
  - **AC#2** — `tests/codemem/test_bench_harness.py` created (12 tests across 3 classes). `uv run pytest tests/codemem/test_bench_harness.py -v` returns: `ModuleNotFoundError: No module named 'bench_codemem_vs_aider'` → 1 collection error, 0 tests passing. Correct RED: fails because production code (Task 2.3) doesn't exist, not because of typo / import-path bug. ✅
  - **AC#3** — Tests assert `(file, symbol_name, kind)` extraction: `TestParserBehavior.test_row_shape_is_3_tuple`, `test_all_fields_are_nonempty_strings`, `test_extracts_def_kind`, `test_extracts_class_kind`, `test_elision_marker_absent_from_names`, `test_file_fields_look_path_like` (trap guard against line-18-`dict:`-continuation), `test_no_preamble_leakage` (guards against Aider CLI metadata lines 1-10 leaking as symbols). ✅
  - **AC#4** — Test file follows project pytest conventions: module docstring, `from __future__ import annotations`, class-grouped `TestParserSurface` / `TestParserBehavior` / `TestParserEdgeCases`, module-scoped `golden_text` fixture. Pattern-matches `tests/codemem/test_ast_grep_parser.py`. ✅

  **Artifacts produced:**
  - `tests/codemem/fixtures/aider_repo_map_aa-ma-forge.txt` (committed, 257 lines)
  - `tests/codemem/test_bench_harness.py` (12 failing tests)
  - `tests/codemem/conftest.py` (1-line-of-logic sys.path injection, AD-005-compliant — parser stays inline in scripts/ per AD-005, not hoisted to a package)

  **Parser API designed via failing tests (API contract for Task 2.3 GREEN):**
  ```python
  def parse_aider_output(text: str) -> list[tuple[str, str, str]]:
      """Returns list of (file, symbol_name, kind) tuples. Empty input → []."""
  ```
  - `kind` ∈ {`"def"`, `"class"`, ...} — fixture shows def/class; edge-case tests don't yet pin decorator kind string (Task 2.3 free to choose `"@"` or `"decorator"`; tests don't constrain).
  - Elision `⋮` never appears in symbol names
  - Preamble (Using/Aider/Model/Git/Repo-map) never leaks as rows
  - Wrapped-signature continuations (e.g., `dict:`) never mistaken as file headers

  **Decisions this task:**
  - **AD-009:** `scripts/` imported in tests via a scoped `tests/codemem/conftest.py` that adds `scripts/` to `sys.path`. Rationale: AD-005 requires parser inline in `scripts/bench_codemem_vs_aider.py` (not a package), but tests must still import it. Conftest is test infra, not production code — TDD-compliant. Alternatives rejected: (a) convert `scripts/` to a package — scope creep; (b) `importlib.util` boilerplate per-test — DRY violation; (c) hoist parser into a real package under `packages/codemem-mcp/src/codemem/parsers/` — contradicts AD-005.
  - **No new facts for reference.md** — fixture HEAD SHA (`af10ec6`) and fixture line count (257) are task-local anchors; they're in tasks.md Result Log where they belong.

  **TDD RED gate: verified.** Ready for Task 2.3 GREEN.

### Task 2.3: GREEN — implement Aider parser (inline unless > 100 LOC)
- Status: COMPLETE
- Mode: AFK
- Dependencies: Task 2.2
- Acceptance Criteria:
  - Parser logic implemented (inline in `bench_codemem_vs_aider.py` OR in `scripts/bench_aider_parser.py` if > 100 LOC)
  - All tests from Task 2.2 pass
  - Parser handles `│def`, `│class`, `│@` prefixes and `⋮` elision marker
  - Ruff clean on new code
- Result Log:
  ✅ COMPLETE 2026-04-20 — TDD GREEN verified. All 4 AC empirically satisfied. 13/13 tests pass; parser inline at 75 LOC (AD-005 compliant).

  **Empirical verification:**
  - **AC#1** — `scripts/bench_codemem_vs_aider.py` created, 75 LOC total (parser function `parse_aider_output` ≈ 40 LOC). Inline per AD-005 (<100 LOC threshold). No split to `scripts/bench_aider_parser.py`. ✅
  - **AC#2** — `uv run pytest tests/codemem/test_bench_harness.py -v` → 13 PASSED in 0.13s. All tests from Task 2.2 green. ✅
  - **AC#3** — Parser regexes: `_DEF_RE = ^│\s*def\s+([A-Za-z_][A-Za-z0-9_]*)`, `_CLASS_RE = ^│\s*class\s+...`, `_DECORATOR_RE = ^│\s*@([A-Za-z_][A-Za-z0-9_.]*)`. `⋮` elision handled by no-match fall-through (not captured by any regex → no row emitted). Decorator kind string chosen: `"decorator"` (not `"@"`) — more readable, tests didn't pin this. ✅
  - **AC#4** — `uv run ruff check scripts/bench_codemem_vs_aider.py tests/codemem/test_bench_harness.py tests/codemem/conftest.py` → "All checks passed!" ✅

  **Design notes (KISS applied):**
  - Strategy: line-by-line state machine tracking `current_file`. Emit `(current_file, name, kind)` when a `│def`/`│class`/`│@` line is matched.
  - **File-header guard** (path-likeness): `line.endswith(":")` alone is insufficient — fixture line 18 `dict:` is a line-wrapped signature continuation. Guard requires `"/" in candidate OR _FILE_EXT_RE.search(candidate)`. Blocks `dict:`, `str:`, etc. from poisoning `current_file`.
  - **Elision handling**: `⋮` lines simply don't match any regex → silently skipped.
  - **Preamble handling**: lines 1-10 of `aider` stdout contain no `│`, and none are path-like → `current_file` stays `None`, no rows emitted.
  - **No walrus operator** — classic `m = _RE.match(); if m:` for ruff-compatibility across versions.

  **Artifacts produced:**
  - `scripts/bench_codemem_vs_aider.py` (new, 75 LOC, parser + module docstring placeholder for Task 2.4/2.5)

  **Regression check (scoped):**
  - `pytest tests/codemem/test_bench_harness.py`: 13/13 PASS ✅
  - **Pre-existing env drift discovered** (NOT caused by this task — verified via temporary conftest.py removal): `uv pip list` shows `codemem-mcp` editable-installed from `/home/sjnewhouse/github_private/aa-ma-forge/packages/codemem-mcp` rather than the current-working-dir copy at `/home/sjnewhouse/biorelate/projects/gitlab/github_private/aa-ma-forge/packages/codemem-mcp`. All `tests/codemem/test_*.py` modules that do `from codemem.X import ...` fail with `ModuleNotFoundError: No module named 'codemem'` — this predates Task 2.2 and is unrelated to the benchmark plan. Flagged as env observation OBS-001 in context-log.md for user decision (suggested fix: `uv sync --reinstall-package codemem-mcp` from current dir).
  - Scoped verification: `mv tests/codemem/conftest.py .bak` → test_pagerank still fails identically → confirms conftest.py is NOT the cause. Restored after test.

  **Decisions this task:**
  - Decorator kind string: `"decorator"` (not `"@"`). Tests don't pin this; "decorator" is self-describing. Logged as AD-010.
  - File-extension whitelist: 21 common source-code extensions (py, sh, md, toml, yaml, yml, json, txt, rs, go, ts, tsx, js, jsx, c, cpp, h, hpp, java, rb, php, swift, kt). Pragmatic — covers the fixture + common repos; can extend on demand.

  **Next:** Task 2.4 — TDD tiktoken normalization test (TDD RED).

### Task 2.4: TDD — tiktoken normalization test
- Status: COMPLETE
- Mode: AFK
- Dependencies: Task 2.3
- Acceptance Criteria:
  - Test file includes tiktoken normalization test
  - Given captured outputs from all 3 tools at requested budget 1024, test asserts `len(tiktoken.encode(output_text))` produces a comparable integer for each
  - Test verifies the output contract shape (raw_bytes, tiktoken_tokens, symbol_count) is populated correctly
- Result Log:
  ✅ COMPLETE 2026-04-20 — TDD RED verified. All 3 AC empirically satisfied. 9 failing tests for measure_output; parser tests still green (13/13); no collection regression.

  **Empirical verification:**
  - **AC#1** — `TestMeasureOutput` class added to `tests/codemem/test_bench_harness.py` with 9 tests pinning the tiktoken normalization contract. Import guard: `try: from bench_codemem_vs_aider import measure_output except ImportError: measure_output = None`. Autouse fixture `_require_measure_output` fails each test with "measure_output not yet implemented — Task 2.5 GREEN pending". ✅
  - **AC#2** — 3 tool-shape tests cover captured outputs:
    - `test_aider_prose_fixture_normalizes` — uses existing aider golden fixture
    - `test_codemem_json_fixture_normalizes` — uses new `tests/codemem/fixtures/codemem_intel_aa-ma-forge.json` (captured via `uv run codemem intel --budget=1024`, 17 symbols, 4003B)
    - `test_jcodemunch_mcp_synthetic_normalizes` — synthetic MCP-shaped JSON inline constant `JCM_SYNTHETIC_MCP_TEXT`. Real jCodeMunch MCP round-trip deferred to Task 2.6 (integration test) — a synthetic is more robust for a unit-test RED than committing a live-captured MCP response.
    - `test_comparable_integers_across_three_tool_shapes` — core AC assertion: all 3 shapes produce integer token counts usable together.
    ✅
  - **AC#3** — `test_returns_dict_with_three_contract_keys` pins the dict shape `{raw_bytes, tiktoken_tokens, symbol_count}` exactly. `test_empty_text_yields_zero_bytes_zero_tokens`, `test_raw_bytes_equals_utf8_length`, `test_tiktoken_tokens_is_positive_int_for_nonempty_text`, `test_symbol_count_passthrough` pin each field's semantics. ✅

  **State after commit (empirical):**
  - `pytest tests/codemem/test_bench_harness.py`: 13 passed, 9 errors (RED-by-design)
  - `pytest` (full suite): 370 passed, 1 skipped, 5 deselected, 9 errors — zero tests that were passing before Task 2.4 are now failing
  - `ruff check`: clean

  **Parser API pinned via tests for Task 2.5 GREEN:**
  ```python
  def measure_output(text: str, symbol_count: int) -> dict[str, int]:
      """Returns {raw_bytes, tiktoken_tokens, symbol_count} for a tool output."""
  ```
  - `raw_bytes` = `len(text.encode("utf-8"))` (not `len(text)` — UTF-8 byte count, tested via ⋮ which is 3 bytes)
  - `tiktoken_tokens` = `len(enc.encode(text))` using `cl100k_base` (matches jCodeMunch tokenizer per AD-001 + Task 2.1 cross-validation)
  - `symbol_count` = passthrough of caller-supplied int (each tool has a different parser)
  - Empty text → all three fields = 0
  - Handles UTF-8, structured JSON, MCP-wrapper JSON inputs uniformly

  **Artifacts produced:**
  - `tests/codemem/fixtures/codemem_intel_aa-ma-forge.json` (new, 4003B, captured via `uv run codemem intel --budget=1024` at HEAD `7e79ed1`)
  - `tests/codemem/test_bench_harness.py` updated: +1 conditional-import block, +1 autouse fixture, +1 new class `TestMeasureOutput` with 9 tests, +1 inline synthetic MCP constant
  - **No production code changes** (pure RED)

  **Decisions this task:**
  - **Conditional import + autouse fixture pattern** (over module-level required import) to prevent RED-state from regressing the 13 previously-GREEN parser tests. Pyright flags 9 `Object of type None cannot be called` warnings — transient RED-state noise; auto-resolves at Task 2.5 GREEN. Ruff tolerates the pattern (clean).
  - jCodeMunch fixture = inline synthetic MCP-shaped JSON; real capture deferred to Task 2.6.

  **Next:** Task 2.5 GREEN — implement `measure_output` + full CLI harness (codemem/aider/jCodeMunch invocation + Jaccard overlap + JSON output). This is the biggest task in M2; GREEN for Task 2.4's 9 tests + new integration-level ACs.

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
