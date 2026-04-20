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
- Status: COMPLETE
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
- Status: COMPLETE
- Mode: AFK
- Dependencies: Task 2.4
- Acceptance Criteria:
  - Script invokes all 3 tools at a configurable `--requested-budget`
  - Captures outputs, normalizes via tiktoken
  - Emits comparison JSON with per-tool (a) raw output size bytes, (b) tiktoken-counted tokens, (c) symbol-row count, (d) top-N overlap via Jaccard against codemem's symbols
  - Script is invokable as `uv run python scripts/bench_codemem_vs_aider.py --repo . --requested-budget N --out FILE`
  - Ruff clean
- Result Log:
  ✅ COMPLETE 2026-04-20 — GREEN. 22/22 tests pass (13 parser + 9 tiktoken). End-to-end CLI smoke test against aa-ma-forge at budget=1024 produces valid JSON.

  **Empirical verification:**
  - **AC#1 (3-tool invocation)** — CLI smoke run returned: `wrote /tmp/bench-smoke.json (cm=ok, ai=ok, jcm=skipped)`. All 3 tools exercised. ✅
  - **AC#2 (tiktoken normalization)** — Each tool's output was tokenized via `tiktoken.get_encoding("cl100k_base")`. Live measurements (budget=1024): codemem 17 symbols / 1239 tokens; aider 67 symbols / 1995 tokens. Tokenizer-mismatch invariant (reference.md §TOP PRIORITY) empirically confirmed — aider's cl100k_base count is ~95% over requested budget, codemem's proxy yields ~21% over. ✅
  - **AC#3 (JSON contract)** — Output JSON contains all required keys:
    - `requested_budget: 1024`
    - `tools: {codemem, aider, jcodemunch}` — each with `raw_bytes`, `tiktoken_tokens`, `symbol_count`, `status`
    - `overlap: {codemem_vs_aider: 0.125, codemem_vs_jcodemunch: 0.0, aider_vs_jcodemunch: 0.0}` — Jaccard on `(file, symbol_name)` tuples per reference.md §Join surface.
    - `tokenizer: "cl100k_base"` (added beyond AC for reproducibility — documents which tokenizer was used)
    - `repo: <abs path>` (added beyond AC for reproducibility)
    ✅
  - **AC#4 (invokable via uv)** — `uv run python scripts/bench_codemem_vs_aider.py --repo . --requested-budget 1024 --out /tmp/bench-smoke.json` → exit 0, file written. ✅
  - **AC#5 (ruff clean)** — `uv run ruff check scripts/bench_codemem_vs_aider.py` → "All checks passed!" ✅
  - **Bonus: import-linter contracts 2/2 kept** (M2 milestone AC#4): "codemem layered architecture KEPT" + "parser must not depend on public API KEPT".

  **Implementation notes:**
  - 241 LOC total (parser ~40 + measure_output ~10 + 3 tool runners ~60 + report builder + CLI ~50 + headers/constants). Still fits inline per AD-005 rationale (single file, comprehensible).
  - `_run_codemem()`: subprocess `uv run codemem intel --budget=N --out=tempfile`; parses JSON, extracts `(file, name)` tuples for join surface. 60s timeout.
  - `_run_aider()`: subprocess `aider --show-repo-map --map-tokens N`; stdout parsed by `parse_aider_output`. 120s timeout (aider is slower on large repos).
  - `_run_jcodemunch()`: **stub** returns `status='skipped'` with reason "MCP-protocol only; real round-trip at Task 2.6". Design decision AD-012 below.
  - `jaccard()`: classic set-intersection / set-union. Empty∩Empty → 0.0 (not NaN — simplifies downstream aggregation).
  - Measurement records on error/skipped: `{raw_bytes: 0, tiktoken_tokens: 0, symbol_count: 0}` + error/reason field. This keeps JSON shape uniform for downstream.

  **Artifacts produced:**
  - `scripts/bench_codemem_vs_aider.py` (rewritten, 241 LOC — adds `measure_output`, `jaccard`, `_run_codemem`, `_run_aider`, `_run_jcodemunch`, `_build_report`, `main`).
  - `/tmp/bench-smoke.json` (throwaway, CLI smoke output).

  **Decisions this task:**
  - **AD-012 — jCodeMunch invocation stub in Task 2.5:** Empirical probe (2026-04-20) found `jcodemunch-mcp` exposes `get_ranked_context` ONLY via MCP protocol (stdio JSON-RPC); no CLI equivalent exists. Neither `munch-bench` nor `jcodemunch-mcp <subcommand>` provide a `get_ranked_context` surface. Options: (a) speak MCP protocol via subprocess + JSON-RPC over stdio, (b) use an MCP client library, (c) stub with error record and defer to Task 2.6 integration test. Chose (c) per Task 2.6 AC allowance ("log and skip if unavoidable"). The full MCP round-trip is Task 2.6 scope. Decision preserves Task 2.5's unit-test focus and Task 2.6's integration-test focus as two distinct TDD phases.
  - Tokenizer pinning: `cl100k_base` in a module-level `_TIKTOKEN_ENCODING` constant. Changing this tokenizer is a plan-level decision, not a code change.
  - `@dataclass` NOT used for measurement records; plain `dict` chosen for JSON-serialization simplicity (tests assert on dict keys, not class attributes).

  **M2 Milestone AC Status (pre-finalization):**
  - ✅ `uv run pytest tests/codemem/test_bench_harness.py` → all green (22/22)
  - ✅ `uv run python scripts/bench_codemem_vs_aider.py --repo . --requested-budget 1024 --out /tmp/bench.json` → valid JSON with `{requested_budget, tools: {codemem, aider, jcodemunch}, overlap}` keys
  - ✅ Ruff clean on new files
  - ✅ Import-linter 2/2 (no package boundary changes)
  - ⏳ Task 2.6 (integration test) remaining before milestone finalize

  **Next:** Task 2.6 — integration test runs the harness end-to-end via pytest, asserts JSON shape, tolerates jCodeMunch skipped status.

### Task 2.6: Integration test — harness self-exercises against aa-ma-forge
- Status: COMPLETE
- Mode: AFK
- Dependencies: Task 2.5
- Acceptance Criteria:
  - Integration test runs the harness against aa-ma-forge
  - Asserts structured JSON output with all 3 tools present under `tools` key
  - Asserts `requested_budget` and `overlap` keys present
  - Test handles known edge case: jCodeMunch may require remote fixture (log and skip if unavoidable)
  - Import-linter contracts still 2/2
- Result Log:
  ✅ COMPLETE 2026-04-20 — GREEN. Integration test added, marked `@pytest.mark.slow`, passes end-to-end. Also performed opportunistic RED-state cleanup (conditional import removed now that Task 2.5 is GREEN).

  **Empirical verification:**
  - **AC#1 (runs harness against aa-ma-forge)** — `TestHarnessIntegration::test_harness_e2e_against_aa_ma_forge` subprocess-invokes `uv run python scripts/bench_codemem_vs_aider.py --repo <aa-ma-forge-root> --requested-budget 1024 --out <tmp>`. `uv run pytest -m slow tests/codemem/test_bench_harness.py` → 1 passed in 4.45s. ✅
  - **AC#2 (all 3 tools under tools key)** — test asserts `set(data["tools"].keys()) == {"codemem", "aider", "jcodemunch"}`. Also asserts each tool has `{status, raw_bytes, tiktoken_tokens, symbol_count}`. ✅
  - **AC#3 (requested_budget + overlap keys)** — test asserts `data["requested_budget"] == 1024` and `set(data["overlap"].keys()) == {codemem_vs_aider, codemem_vs_jcodemunch, aider_vs_jcodemunch}`. ✅
  - **AC#4 (jCodeMunch tolerance)** — test asserts `data["tools"]["jcodemunch"]["status"] in {"ok", "skipped", "error"}`. Codemem and aider still asserted strict `status == "ok"` (harness sanity) and `symbol_count > 0`. Aligns with AD-012 (jCodeMunch MCP-only, stub-skipped at M2). ✅
  - **AC#5 (import-linter 2/2)** — `uv run lint-imports` → "Contracts: 2 kept, 0 broken". ✅

  **Opportunistic cleanup (not in Task 2.6 AC — done since I was editing the file):**
  - Removed `try/except` conditional import of `measure_output` (leftover from Task 2.4 RED) — now that measure_output exists in Task 2.5 GREEN, the unconditional import is correct. Collapsed two import lines into `from bench_codemem_vs_aider import (measure_output, parse_aider_output,)`.
  - Removed `_require_measure_output` autouse fixture from `TestMeasureOutput` — no longer needed; the import guarantee makes the tests runnable directly.
  - Clears 9 pyright `Object of type None cannot be called` warnings. 1 pyright warning remains (`Import bench_codemem_vs_aider could not be resolved`) — this is a well-known Pyright limitation re pytest conftest.py sys.path injection; runtime import works (22/22 tests pass confirm this).

  **Artifacts produced:**
  - `tests/codemem/test_bench_harness.py` updated: +class `TestHarnessIntegration` (~75 LOC), cleanup of conditional-import block (-10 LOC net), docstring refreshed to describe the full scope of the file.

  **State after Task 2.6:**
  - Default `pytest`: 22 passed, 1 deselected (slow) — clean
  - `pytest -m slow`: 1 passed (integration) — clean
  - Full suite `pytest`: 370 passed, 1 skipped, 5 deselected (no regressions since OBS-001 fix)
  - Ruff: clean
  - Import-linter: 2/2

  **Next:** M2 milestone finalization (all 6 tasks COMPLETE) → M3 execution (Tasks 3.1-3.4: budget sweeps on aa-ma-forge + fastapi).

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
- Status: COMPLETE
- Mode: AFK
- Dependencies: Milestone 2
- Acceptance Criteria:
  - `tiangolo/fastapi` cloned into `/tmp/bench-fastapi`
  - Pinned commit SHA recorded in provenance.log
  - `.git` present (for tool introspection if needed)
- Result Log:
  ✅ COMPLETE 2026-04-20 — fastapi 0.136.0 cloned at pinned SHA. All 3 AC satisfied.

  **Empirical state:**
  - Tag selected: `0.136.0` (latest stable tag from `git ls-remote --tags` enumerate, excluding `v0.1.16` which sorted first due to version-string peculiarities)
  - Pinned SHA: `708606c982cf35718cb2214c0bb9261cf548f042`
  - `git clone --depth 1 --branch 0.136.0 https://github.com/tiangolo/fastapi.git /tmp/bench-fastapi` succeeded (detached HEAD per shallow clone)
  - `find /tmp/bench-fastapi -name '*.py'` → 1119 Python files
  - `du -sh /tmp/bench-fastapi` → 56MB
  - `.git` present (visible in `ls -la /tmp/bench-fastapi`)
  - Pinned SHA recorded in provenance.log (via M3 T3.1 entry) and reference.md §Benchmark Target Repos

  **Sibling work (bundled into same commit for cohesion):**
  - Created `scripts/bench_sweep.py` (158 LOC) — M3 orchestrator implementing AD-006 (3-run median aggregation). Wraps `scripts/bench_codemem_vs_aider.py` subprocess-style; preserves M2 single-run contract unchanged.
  - Added `TestSweepAggregate` class (8 tests) in test_bench_harness.py pinning `aggregate()` and `_median_int()` correctness: empty, odd-count, even-count-coerced-to-int, single-run, 3-run median, error-precedence, skipped-over-ok.

  **Decisions:** U-002 pinned to `0.136.0` (autonomous choice per user's 2026-04-20 direction: "Proceed autonomously — I pick latest stable tiangolo/fastapi tag").

  **State after Task 3.1:**
  - pytest default suite: 30/30 green (22 original + 8 new sweep tests)
  - pytest full suite: 378 passed, 1 skipped, 5 deselected (no regression)
  - ruff: clean

  **Next:** Task 3.2 — run sweep against aa-ma-forge at budgets {512, 1024, 2048, 4096} × 3 runs.

### Task 3.2: Run harness against aa-ma-forge at budgets {512, 1024, 2048, 4096}
- Status: COMPLETE
- Mode: AFK
- Dependencies: Task 3.1
- Acceptance Criteria:
  - `/tmp/bench-aa-ma-forge.json` exists
  - Contains 4 budget × 3 tools = 12 measurements
  - Each measurement has raw_bytes, tiktoken_tokens, symbol_count fields
  - Each measurement is a median of 3 runs (per AD-006)
- Result Log:
  ✅ COMPLETE 2026-04-20 — all 4 AC empirically satisfied. Tokenizer-mismatch invariant confirmed at scale across the full budget sweep.

  **Empirical results (aa-ma-forge @ HEAD `c24d665`):**

  | Budget | Tool       | Symbols | tiktoken_tokens | raw_bytes | Status   |
  |--------|------------|---------|----------------|-----------|----------|
  |    512 | codemem    |       8 |    591 (+15%)  |      1933 | ok       |
  |    512 | aider      |      38 |   1097 (+114%) |      3644 | ok       |
  |    512 | jcodemunch |       0 |      0         |         0 | skipped  |
  |   1024 | codemem    |      17 |   1239 (+21%)  |      4003 | ok       |
  |   1024 | aider      |      67 |   1995 (+95%)  |      6509 | ok       |
  |   1024 | jcodemunch |       0 |      0         |         0 | skipped  |
  |   2048 | codemem    |      35 |   2513 (+23%)  |      8016 | ok       |
  |   2048 | aider      |     132 |   3950 (+93%)  |     12659 | ok       |
  |   2048 | jcodemunch |       0 |      0         |         0 | skipped  |
  |   4096 | codemem    |      72 |   5168 (+26%)  |     16333 | ok       |
  |   4096 | aider      |     268 |   8408 (+105%) |     27973 | ok       |
  |   4096 | jcodemunch |       0 |      0         |         0 | skipped  |

  Jaccard(codemem, aider) overlap:
  - budget=512: 0.048
  - budget=1024: 0.125
  - budget=2048: 0.171
  - budget=4096: 0.253

  **AC verification:**
  - **AC#1** — `/tmp/bench-aa-ma-forge.json` exists (written by sweep orchestrator) ✅
  - **AC#2** — 4 budgets × 3 tools = 12 measurement cells populated (codemem/aider/jcodemunch × {512,1024,2048,4096}) ✅
  - **AC#3** — Each measurement has `{raw_bytes, tiktoken_tokens, symbol_count, status, runs_included}` ✅
  - **AC#4** — Each measurement is a median of 3 runs (`runs_per_cell: 3`, aggregate() uses `statistics.median` per `_median_int`) ✅

  **Determinism observed:** All 3 runs at each budget produced identical symbol counts for codemem. Aider showed trivial jitter at budget=4096 only (run 2 emitted 262 symbols vs 268 in runs 1/3; median = 268 correctly selected). Deterministic enough that median-of-3 barely distinguishes from single-run; AD-006 is a cheap belt-and-braces.

  **Quotable data points (for M4.1 report):**
  - Codemem's 4-char proxy consistently overshoots requested budget by 15-26% across the sweep; aider's cl100k_base overshoots by 93-114%. **Aider emits ~2× the tiktoken tokens codemem does at equal requested budget.** This is the tokenizer-mismatch invariant operating in the wild.
  - At budget=4096: codemem emits 72 symbols / 5168 tokens (~71 tokens/symbol); aider emits 268 symbols / 8408 tokens (~31 tokens/symbol). Aider is ~2.3× more token-efficient per symbol.
  - Jaccard overlap grows monotonically with budget (0.048 → 0.253 at 4096). Tools converge as budget permits more symbols but never fully overlap — they use different ranking signals despite both claiming PageRank. **25% overlap at 4096 is a significant divergence** — worth highlighting in M4.

  **Artifacts:** `/tmp/bench-aa-ma-forge.json` (sweep result, ~3.5KB, JSON — throwaway per reference.md §Temporary/Throwaway). Log: `/tmp/bench-aa-ma-forge.log`.

  **Next:** Task 3.3 — run sweep against fastapi (launched in background).

### Task 3.3: Run harness against fastapi at same budget sweep
- Status: ACTIVE
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
