# codemem-benchmark-fairness-v2 Tasks (HTP)

_Hierarchical Task Planning roadmap with dependencies, mode classification, and state tracking. All milestones are SOFT-gated (default). Max complexity 60% at M2a; no milestone reaches the 80% deep-review threshold._

---

## Milestone 1: Codemem proxy + rank truncation

- Status: PENDING
- Gate: SOFT
- Mode (milestone-level dispatch): AFK
- Complexity: 30%
- Effort: 0.5 day
- Dependencies: None (pre-M1.0 archive step handles any AA-MA hook conflict with v1 plan)
- Measurable goal: `codemem intel --budget=1024` on aa-ma-forge emits >= 17 symbols (v1 baseline) with `rank` rounded to 3 sig figs and budget enforced by cl100k_base; full test suite green.
- Acceptance Criteria:
  - `grep -n "_CHARS_PER_TOKEN" packages/codemem-mcp/src/codemem/pagerank.py` returns zero occurrences after the fix.
  - `grep -n "tiktoken" packages/codemem-mcp/src/codemem/pagerank.py` returns >= 1.
  - `uv run python -c "import json; d=json.load(open('/tmp/post-m1-intel.json')); [print(s['rank']) for s in d['symbols'][:5]]"` emits values matching `/^[01]\.\d{1,3}(e-?\d+)?$/` (3 sig figs).
  - `uv run pytest tests/codemem/` returns green.
  - `uv run codemem intel --budget=1024 --out=/tmp/post-m1-intel.json` on aa-ma-forge emits `_meta.written_symbols >= 17`.

### Step M1.0: Archive v1 plan (pre-flight) if AA-MA hooks block cross-plan commits
- Status: PENDING
- Mode: HITL
- Dependencies: None
- Acceptance Criteria:
  - If `aa-ma-commit-signature.sh` hook blocks commits tagged for v2 while v1 is still in `.claude/dev/active/`, run `/archive-aa-ma codemem-token-benchmarks`; v1 dir moves to `.claude/dev/completed/codemem-token-benchmarks/`.
  - Otherwise: proceed directly to M1.1 and defer archive to M4.
- Result Log:

### Step M1.1: Replace `_CHARS_PER_TOKEN` proxy with cl100k_base encoder in pagerank.py
- Status: PENDING
- Mode: AFK
- Dependencies: M1.0
- Acceptance Criteria:
  - `_CHARS_PER_TOKEN` constant removed from `packages/codemem-mcp/src/codemem/pagerank.py`.
  - Module-level `_TIKTOKEN_ENCODER = tiktoken.get_encoding("cl100k_base")` cache added.
  - `_fits()` uses `len(_TIKTOKEN_ENCODER.encode(json.dumps(payload, ...))) <= budget_tokens`.
- Result Log:

### Step M1.2: Round `rank` to 3 significant figures at emission
- Status: PENDING
- Mode: AFK
- Dependencies: M1.1
- Acceptance Criteria:
  - Emission at `packages/codemem-mcp/src/codemem/pagerank.py:171` rounds `rank` to 3 sig figs (e.g. `float(f"{rank:.3g}")` or equivalent).
  - `jq '.symbols[0].rank' /tmp/post-m1-intel.json` returns a value matching `/^[01]\.\d{1,3}(e-?\d+)?$/`.
- Result Log:

### Step M1.3: Update `test_pagerank.py` for tiktoken budget + rounded rank
- Status: PENDING
- Mode: AFK
- Dependencies: M1.2
- Acceptance Criteria:
  - Any existing test assuming the 4-char proxy is updated to assert a tiktoken-grounded budget instead.
  - New test asserts `rank` emission pattern matches the 3-sig-fig regex.
  - `uv run pytest tests/codemem/test_pagerank.py` returns green.
- Result Log:

### Step M1.4: Smoke verify on aa-ma-forge + record delta
- Status: PENDING
- Mode: AFK
- Dependencies: M1.3
- Acceptance Criteria:
  - `uv run codemem intel --budget=1024 --out=/tmp/post-m1-intel.json` on aa-ma-forge emits `_meta.written_symbols >= 17`.
  - Delta vs v1 baseline (17 symbols) logged in Result Log.
  - `uv run pytest tests/codemem/` returns green.
- Result Log:

### Step M1.5: Commit M1 with AA-MA signature
- Status: PENDING
- Mode: AFK
- Dependencies: M1.4
- Acceptance Criteria:
  - Commit message last footer line = `[AA-MA Plan] codemem-benchmark-fairness-v2 .claude/dev/active/codemem-benchmark-fairness-v2`.
  - `git push origin expt/code_mem_store_what` succeeds.
  - `provenance.log` contains the commit hash.
- Result Log:

---

## Milestone 2a: Fair 3-way re-run (jCodeMunch live + RBO + Aider tokeniser-equalised)

- Status: PENDING
- Gate: SOFT
- Mode (milestone-level dispatch): AFK
- Complexity: 60%
- Effort: 1-1.5 days
- Dependencies: M1
- Measurable goal: v1 harness replaced; 3 tools x 4 budgets x 3 runs produces JSON with no stubs; both Jaccard and RBO@10 populated; Aider run with `--model gpt-3.5-turbo`.
- Acceptance Criteria:
  - `scripts/bench_codemem_vs_aider.py --repo . --requested-budget 1024 --out /tmp/v2a.json` produces JSON with `tools.jcodemunch.status == "ok"`, `tiktoken_tokens > 0`, `symbol_count > 0`.
  - `tools.aider` populated from an Aider invocation with `--model gpt-3.5-turbo`.
  - `overlap.budget_1024.codemem_vs_aider.rbo_at_10` in `[0.0, 1.0]`; same for `codemem_vs_jcodemunch` and `aider_vs_jcodemunch`.
  - `tests/codemem/test_bench_harness.py` has `TestJCodeMunchAdapter` (>=3 tests), `TestRBOMetric` (>=3 tests), `TestAiderModelOverride` (>=1 test); all green.
  - `uv run pytest -m slow tests/codemem/` still passes.

### Step M2a.1: Add `mcp>=1.27` dev dep in pyproject.toml; `uv sync`
- Status: PENDING
- Mode: AFK
- Dependencies: M1.5
- Acceptance Criteria:
  - `uv run python -c "import mcp; print(mcp.__version__)"` returns `>=1.27.0`.
  - `pyproject.toml` dev-deps list contains `mcp>=1.27`.
- Result Log:

### Step M2a.2: Probe, verify `aider --model gpt-3.5-turbo --show-repo-map` invokable without API key
- Status: PENDING
- Mode: HITL
- Dependencies: M2a.1
- Acceptance Criteria:
  - If invokable: proceed to M2a.3 with Aider `--model gpt-3.5-turbo` path.
  - If NOT invokable (API key required): decision logged in context-log.md (U-008 resolved); M2a falls back to default-model Aider with explicit tokeniser-bias callout in v2 report.
- Result Log:

### Step M2a.3: Implement `_run_aider` with `--model gpt-3.5-turbo` switch
- Status: PENDING
- Mode: AFK
- Dependencies: M2a.2
- Acceptance Criteria:
  - Harness invokes Aider with `--model gpt-3.5-turbo --show-repo-map --map-tokens N` when `--aider-tokeniser-equalise` flag set.
  - Existing `parse_aider_output` reused unchanged.
  - `TestAiderModelOverride` (>=1 test) asserts CLI arg passes through.
- Result Log:

### Step M2a.4: Implement `_run_jcodemunch`, MCP stdio round-trip via `mcp>=1.27` SDK
- Status: PENDING
- Mode: AFK
- Dependencies: M2a.1
- Acceptance Criteria:
  - Adapter spawns `jcodemunch-mcp serve --transport stdio`, calls `get_ranked_context(query, token_budget=N)`, parses result into harness output shape.
  - Returns `status="ok"`, `tiktoken_tokens > 0`, `symbol_count > 0` for aa-ma-forge at budget=1024.
  - `TestJCodeMunchAdapter` (>=3 tests) green against mock MCP server fixture.
- Result Log:

### Step M2a.5: Implement inline RBO@10 (Webber et al. 2010, p=0.9)
- Status: PENDING
- Mode: AFK
- Dependencies: M2a.4
- Acceptance Criteria:
  - `rbo_at_10(list_s, list_t, p=0.9, k=10)` function added to `scripts/bench_codemem_vs_aider.py`; output in `[0.0, 1.0]`.
  - `TestRBOMetric` (>=3 tests) asserts hand-computed values for 3 known list pairs.
  - One test cross-verifies against the `rbo` PyPI package output (pinned as test-only dep).
- Result Log:

### Step M2a.6: Wire overlap block to emit both `jaccard` and `rbo_at_10` per pair
- Status: PENDING
- Mode: AFK
- Dependencies: M2a.5
- Acceptance Criteria:
  - `overlap.budget_1024.<pair>` contains both `jaccard` and `rbo_at_10` keys for all three pairs.
  - Existing v1 jaccard path unchanged.
- Result Log:

### Step M2a.7: Run single-budget 3-tool smoke + commit
- Status: PENDING
- Mode: AFK
- Dependencies: M2a.6
- Acceptance Criteria:
  - `scripts/bench_codemem_vs_aider.py --repo . --requested-budget 1024 --out /tmp/v2a.json` passes the Phase-M2a assertions.
  - Commit signature footer correct; push succeeds.
- Result Log:

---

## Milestone 2b: Repomix adapter

- Status: PENDING
- Gate: SOFT
- Mode (milestone-level dispatch): AFK
- Complexity: 45%
- Effort: 0.5 day
- Dependencies: M2a
- Measurable goal: `scripts/bench_codemem_vs_aider.py --requested-budget 1024` emits a `tools.repomix` cell with `status=ok` and non-zero `tiktoken_tokens` on aa-ma-forge.
- Acceptance Criteria:
  - `scripts/bench_codemem_vs_aider.py --repo . --requested-budget 1024 --out /tmp/v2b.json` produces JSON with `tools.repomix.status == "ok"`, `tiktoken_tokens > 0`. Symbol-count may be 0 (`status="ok_no_symbols"` acceptable and documented).
  - Repomix invocation pinned: `repomix --style xml --output /tmp/repomix-out.xml --token-count-encoding cl100k_base .`.
  - `TestRepomixAdapter` tests (>=3) green.

### Step M2b.1: Pre-flight, verify npm / Repomix install
- Status: PENDING
- Mode: HITL
- Dependencies: M2a.7
- Acceptance Criteria:
  - `which npm` returns a path.
  - `npm install -g repomix` succeeds OR `npx -y repomix --version` returns a pinned version.
  - Exact Repomix version recorded in reference.md.
- Result Log:

### Step M2b.2: Capture golden XML fixture
- Status: PENDING
- Mode: AFK
- Dependencies: M2b.1
- Acceptance Criteria:
  - `tests/codemem/fixtures/repomix_output_aa-ma-forge.xml` committed.
  - File generated by the pinned Repomix invocation.
- Result Log:

### Step M2b.3: Implement `_run_repomix` adapter
- Status: PENDING
- Mode: AFK
- Dependencies: M2b.2
- Acceptance Criteria:
  - Adapter invokes pinned Repomix CLI; captures raw bytes; re-tokenises via `_TIKTOKEN_ENCODER`.
  - Emits `status="ok"` (or `"ok_no_symbols"` if symbol_count=0) with `tiktoken_tokens > 0`.
  - Regex-based post-hoc symbol count captured as secondary metric where possible.
- Result Log:

### Step M2b.4: `TestRepomixAdapter` tests (>=3) + smoke + commit
- Status: PENDING
- Mode: AFK
- Dependencies: M2b.3
- Acceptance Criteria:
  - `TestRepomixAdapter` has >=3 tests parsing the golden XML fixture; all green.
  - `scripts/bench_codemem_vs_aider.py --repo . --requested-budget 1024 --out /tmp/v2b.json` passes M2b assertions.
  - Commit signature footer correct; push succeeds.
- Result Log:

---

## Milestone 2c: Yek adapter + full 5-tool sweep

- Status: PENDING
- Gate: SOFT
- Mode (milestone-level dispatch): AFK
- Complexity: 45%
- Effort: 0.5 day
- Dependencies: M2b
- Measurable goal: `tools.yek` populated; full 5-tool x 4-budget x 2-repo x 3-run sweep produces two JSON files with 40 cells each.
- Acceptance Criteria:
  - `scripts/bench_codemem_vs_aider.py --repo . --requested-budget 1024 --out /tmp/v2c.json` produces JSON with `tools.yek.status == "ok"`, `tiktoken_tokens > 0`.
  - `scripts/bench_sweep.py --repo . --out /tmp/bench-aa-ma-forge-v2.json` and same for fastapi: each produces 5x4 = 20 cells + overlap triples for all 10 pairs.
  - `TestYekAdapter` tests (>=3) green.
  - Full sweep wall-clock documented (expected 20-60 minutes per repo).

### Step M2c.1: Pre-flight, verify cargo / Yek install + confirm CLI flags
- Status: PENDING
- Mode: HITL
- Dependencies: M2b.4
- Acceptance Criteria:
  - `which cargo` returns a path.
  - `cargo install yek` succeeds OR pre-built binary on PATH.
  - `yek --help` output captured; actual flags for token budget and JSON output confirmed.
- Result Log:

### Step M2c.2: Capture golden JSON fixture
- Status: PENDING
- Mode: AFK
- Dependencies: M2c.1
- Acceptance Criteria:
  - `tests/codemem/fixtures/yek_output_aa-ma-forge.json` committed.
- Result Log:

### Step M2c.3: Implement `_run_yek` adapter
- Status: PENDING
- Mode: AFK
- Dependencies: M2c.2
- Acceptance Criteria:
  - Adapter invokes Yek with confirmed flags; captures raw bytes; re-tokenises via `_TIKTOKEN_ENCODER`.
  - Emits `status="ok"` with `tiktoken_tokens > 0`.
- Result Log:

### Step M2c.4: Extend `scripts/bench_sweep.py` to 5-tool loop
- Status: PENDING
- Mode: AFK
- Dependencies: M2c.3
- Acceptance Criteria:
  - Sweep aggregates all 5 tools; `aggregate` + `_median_int` reused unchanged.
  - Output contract matches the 10-pair overlap block in reference.md.
- Result Log:

### Step M2c.5: `TestYekAdapter` (>=3) + `@pytest.mark.slow` full sweep integration
- Status: PENDING
- Mode: AFK
- Dependencies: M2c.4
- Acceptance Criteria:
  - `TestYekAdapter` has >=3 tests; all green.
  - `@pytest.mark.slow` integration test runs the full 5-tool sweep against aa-ma-forge and asserts the 20-cell JSON contract.
- Result Log:

### Step M2c.6: Run full sweep on both repos + commit
- Status: PENDING
- Mode: AFK
- Dependencies: M2c.5
- Acceptance Criteria:
  - `/tmp/bench-aa-ma-forge-v2.json` and `/tmp/bench-fastapi-v2.json` each contain 20 cells and 10 overlap pairs.
  - Wall-clock per repo recorded in Result Log.
  - Commit signature footer correct; push succeeds.
- Result Log:

---

## Milestone 3: v2 report + Signal 2 second re-baseline

- Status: PENDING
- Gate: SOFT
- Mode (milestone-level dispatch): HITL
- Complexity: 40%
- Effort: 0.5-1 day
- Dependencies: M2c
- Measurable goal: `docs/benchmarks/codemem-vs-aider-v2.md` committed, voice-pass green, Signal 2 status line updated with v2 numbers, composite verdict re-examined.
- Acceptance Criteria:
  - `docs/benchmarks/codemem-vs-aider-v2.md` exists; `grep -c '—' docs/benchmarks/codemem-vs-aider-v2.md` returns 0; `grep -iEn "\b(crucial|delve|leverage|landscape)\b"` returns no matches.
  - `docs/benchmarks/codemem-vs-aider.md` has "superseded by v2" banner at top (preserves v1 content).
  - `docs/codemem/kill-criteria.md` Signal 2 status line dated 2026-04-XX (second re-baseline); "Latest update" header bumped.
  - HITL approval gate passed on both the report and the Signal 2 rewrite.
  - If v2 codemem beats Aider after proxy fix: conjunct (b) flips FAILS -> PASSES on small repo; composite verdict line updated per v1 plan §Task 4.2 case (a).
  - `docs/benchmarks/results-codemem-vs-aider-v2-2026-04-XX.json` committed.

### Step M3.1: Draft `docs/benchmarks/codemem-vs-aider-v2.md` from combined raw data
- Status: PENDING
- Mode: AFK
- Dependencies: M2c.6
- Acceptance Criteria:
  - Report includes 5-tool headline table, RBO@10 + Jaccard overlap matrix, methodology-correction section explicitly enumerating the 11 Phase-4.5 findings and which were fixed in v2.
  - Voice grep gates pass: no em dashes, no AI-vocab words.
- Result Log:

### Step M3.2: Add "superseded by v2" banner to v1 report (HITL decision point U-005)
- Status: PENDING
- Mode: HITL
- Dependencies: M3.1
- Acceptance Criteria:
  - User confirms keep-both vs overwrite decision (recommendation: keep both).
  - `docs/benchmarks/codemem-vs-aider.md` has a dated banner at top linking to v2 report.
  - v1 body unchanged.
- Result Log:

### Step M3.3: Second re-baseline of Signal 2 in kill-criteria.md (HITL decision point U-006)
- Status: PENDING
- Mode: HITL
- Dependencies: M3.2
- Acceptance Criteria:
  - If v2 codemem beats Aider post-fix: Aider sub-claim flips "PASS on small repo" per v1 §Task 4.2 case (a).
  - Composite verdict line re-stated using v1 plan case-a/case-b/case-c wording verbatim.
  - "Latest update" header bumped to 2026-04-XX.
  - User sign-off captured in context-log.md.
- Result Log:

### Step M3.4: Commit combined raw data + M3 docs
- Status: PENDING
- Mode: AFK
- Dependencies: M3.3
- Acceptance Criteria:
  - `docs/benchmarks/results-codemem-vs-aider-v2-2026-04-XX.json` committed (5-tool raw data).
  - Single commit with all M3 docs; signature footer correct; push succeeds.
- Result Log:

---

## Milestone 4: Finalization + archive v1

- Status: PENDING
- Gate: SOFT
- Mode (milestone-level dispatch): AFK
- Complexity: 10%
- Effort: 1 hour
- Dependencies: M3
- Measurable goal: M4 commit pushed; `/archive-aa-ma codemem-token-benchmarks` run (if not already done at M1.0); v2 AA-MA dir exists and is synced.
- Acceptance Criteria:
  - Single commit per milestone with AA-MA signature footer: `[AA-MA Plan] codemem-benchmark-fairness-v2 .claude/dev/active/codemem-benchmark-fairness-v2`.
  - `git push origin expt/code_mem_store_what` succeeds; `git rev-parse HEAD == git rev-parse origin/expt/code_mem_store_what`.
  - `/archive-aa-ma codemem-token-benchmarks` run, v1 plan moves to `.claude/dev/completed/codemem-token-benchmarks/` (skip if already archived in M1.0).
  - Pre-commit sanity green: `uv run pytest` (>=387 passed), `uv run ruff check`, `uv run lint-imports` (2/2 contracts).

### Step M4.1: Pre-commit sanity suite
- Status: PENDING
- Mode: AFK
- Dependencies: M3.4
- Acceptance Criteria:
  - `uv run pytest -q` returns >=387 passed.
  - `uv run pytest -m slow tests/codemem/` returns >=2 passed.
  - `uv run ruff check src/ scripts/ tests/` clean.
  - `uv run lint-imports` shows 2/2 contracts kept.
- Result Log:

### Step M4.2: Archive v1 if not done at M1.0
- Status: PENDING
- Mode: AFK
- Dependencies: M4.1
- Acceptance Criteria:
  - `.claude/dev/active/codemem-token-benchmarks/` does NOT exist post-archive.
  - `.claude/dev/completed/codemem-token-benchmarks/` exists with all v1 artefacts.
- Result Log:

### Step M4.3: Sync v2 AA-MA state files + final commit
- Status: PENDING
- Mode: AFK
- Dependencies: M4.2
- Acceptance Criteria:
  - `tasks.md`, `reference.md`, `context-log.md`, `provenance.log` updated with M4 completion.
  - No `Status: PENDING` entries remain in any milestone.
  - Final commit signature footer correct; `git push origin expt/code_mem_store_what` succeeds.
- Result Log:

---

_Total milestones: 6. Total steps: 30. Max-step complexity: 60% (M2a, below deep-review threshold)._
