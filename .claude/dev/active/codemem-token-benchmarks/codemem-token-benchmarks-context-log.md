# codemem-token-benchmarks Context Log

_This log captures architectural decisions, trade-offs, and unresolved issues._

---

## 2026-04-20 — RISK-SIGNAL (not kill): Signal 2 conjunct (b) fails on both repos

**Event:** The Aider token-efficiency benchmark (plan Task 4.2) has measured conjunct (b) of kill-criteria Signal 2 ("`PROJECT_INTEL.json` at `--budget=1024` fails to beat Aider's repo-map token efficiency at the same budget") and **conjunct (b) fails** on both reference repos exercised: aa-ma-forge and `tiangolo/fastapi` 0.136.0.

**Numbers (in `cl100k_base` tokens, tokens-per-symbol lower is better):**
- aa-ma-forge: codemem 72.8 tok/sym vs Aider 30.0. Aider **2.4×** more token-efficient per symbol.
- fastapi: codemem 57.5 tok/sym vs Aider 47.3. Aider **1.2×** more token-efficient per symbol.

Full tables and methodology: [`docs/benchmarks/codemem-vs-aider.md`](../../../docs/benchmarks/codemem-vs-aider.md).

**Classification: RISK-SIGNAL, NOT KILL.** The composite AND verdict for Signal 2 remains **PROVISIONAL DID-NOT-TRIGGER** because conjunct (a) (`codemem build` > 1.5× `/index` wall-clock) still holds at 0.73× on aa-ma-forge and a single-conjunct failure cannot trigger an AND composite. Medium-repo and 50k-LOC wall-clock measurements remain the gate on flipping the composite from PROVISIONAL to PINNED.

**Root cause pointer:** the benchmark report's ["Implications for kill-criteria Signal 2"](../../../docs/benchmarks/codemem-vs-aider.md#implications-for-kill-criteria-signal-2) section identifies a two-fold root cause:

1. **Tokeniser proxy under-reporting.** codemem's `pagerank.py` budget loop measures content in 4-chars-per-token, which systematically under-reports actual `cl100k_base` tokens by 6-26% across the sweep. Switching to a `cl100k_base` counter inside the budget loop would yield honest per-symbol budgets but would not, on its own, close the 2.4× per-symbol gap on the small repo.
2. **Structured-metadata format overhead.** codemem's per-entry payload (SCIP ID + file + line + kind + rank) is genuinely more verbose than Aider's signature-line format. This is a design trade: codemem's output is structured for programmatic consumption; Aider's is shaped for LLM prompt injection. A condensed codemem output mode (e.g. `file:line name`) specifically for prompt-injection callers would close most of the gap without touching the core architecture.

**Why this is not a kill:** Signal 2 was designed to detect failure of the **SQLite-canonical architectural bet** (is the schema complexity earning its keep on speed + efficiency?). The two root causes identified above are (1) a tokeniser-accounting bug and (2) an output-format choice for a specific consumer. Neither demands an architectural rewrite. The SQLite-canonical bet remains defensible on the wall-clock conjunct and the qualitative split (codemem serves a programmatic-consumption niche Aider does not).

**Monitoring action:** medium-repo and 50k-LOC wall-clock measurements are the decisive data that would flip Signal 2 to PINNED (either DID-NOT-TRIGGER or FIRED). Until then, conjunct (b)'s failure is a live risk flag on future planning: any work that adds per-entry metadata to `PROJECT_INTEL.json` should weigh the tokens/symbol cost against the programmatic-consumption benefit.

**Artefacts:**
- `docs/benchmarks/codemem-vs-aider.md` (new, 249 lines, the report itself)
- `docs/benchmarks/results-codemem-vs-aider-2026-04-18.json` (new, combined raw data)
- `docs/codemem/kill-criteria.md` (Signal 2 status line rewritten; header date bumped)

---

## 2026-04-20 Milestone Completion: M3 Execute

- **Status:** COMPLETE (SOFT gate)
- **Acceptance criteria:** 3/3 empirically verified
  - ✅ Two JSON result files on disk — `/tmp/bench-aa-ma-forge.json` and `/tmp/bench-fastapi.json`, each with 4 budget × 3 tools = 12 measurements
  - ✅ No tool-invocation failures — Task 3.4 sanity verified 24/24 cells (16 status=ok, 8 status=skipped per AD-012 jCodeMunch stub)
  - ✅ Quotable data points — budget=4096 aa-ma-forge cell is the headline signal for M4.1 (codemem 72 sym/5168 tok; aider 268 sym/8408 tok; aider is 2.3× more token-efficient per symbol; Jaccard=0.253)

**Key empirical findings (consolidated across both repos):**

| | aa-ma-forge (own repo) | fastapi 0.136.0 |
|---|---|---|
| Codemem token overshoot | +15% → +26% | +6% → +18% |
| Aider token overshoot | +93% → +114% | +111% → +131% |
| Aider overshoot relative to codemem | ~4-8× | ~5-20× |
| Codemem determinism | all runs identical | all runs identical |
| Aider determinism | trivial jitter at budget=4096 | larger jitter at budget=4096 (161/178/187 → median 178) |
| Jaccard(cm, ai) range | 0.048 → 0.253 | 0.069 → 0.157 |

**Tokenizer-mismatch invariant empirically confirmed** — the hypothesis that drove the entire plan. Codemem's 4-char proxy is consistently conservative (underreports tokens by ~15-25%); aider's cl100k_base is consistently aggressive (overreports by ~95-130% relative to requested budget). This means "equal requested budget" across the two tools is a ~2× apples-to-oranges comparison without normalization. The benchmark JSON captures both for parity.

**Observation OBS-002 — codemem-build prereq (discovered during Task 3.3):**
- `codemem intel` requires a pre-existing `.codemem/index.db` produced by `codemem build`.
- Fresh clones (like `/tmp/bench-fastapi`) don't have this DB → `intel` fails with `sqlite3.OperationalError: unable to open database file`.
- aa-ma-forge's sweep worked because the repo has a `.codemem/index.db` (676KB) from prior development.
- **Fix applied for M3 execution:** manually ran `codemem build` inside `/tmp/bench-fastapi` once (1129 files, 4954 symbols, 0.89s) before re-running the sweep.
- **Future improvement (out of this plan's scope):** `scripts/bench_sweep.py` could detect missing `.codemem/index.db` and invoke `codemem build` automatically. Idempotent (cheap no-op on existing DB). Logged here for eventual picking up.
- **Impact on findings:** None — codemem data in both sweep JSONs was collected with a properly-built DB. The aa-ma-forge DB was warm from recent development (last_sha tracking); the fastapi DB was fresh from our one-shot build. Both conditions are representative of real benchmark use.

**Decisions this milestone:** None new beyond AD-013 (U-002 pinned fastapi 0.136.0 at SHA 708606c9, recorded via Task 3.1 and reference.md).

**Artifacts:**
- `scripts/bench_sweep.py` (158 LOC, 8-test coverage) — committed
- `/tmp/bench-aa-ma-forge.json`, `/tmp/bench-fastapi.json` — throwaway per reference.md §Temporary/Throwaway; feed M4.1

**Commits this milestone:** `a4dd02f` (T3.1 + sweep), `c2d43ea` (T3.2 closure).

**Next Milestone:** M4 Report + Integrate — HITL, SOFT gate, ~1 focused-dev day, complexity 40%. Tasks 4.1-4.3: draft `docs/benchmarks/codemem-vs-aider.md`, update `docs/codemem/kill-criteria.md` Signal 2 Aider sub-claim, commit. M4.1 is an HITL task — stephen-newhouse-voice review gate before drafting is approved.

---

## 2026-04-20 Milestone Completion: M2 Harness + Parser (TDD)

- **Status:** COMPLETE (SOFT gate — convention-based)
- **Acceptance criteria:** 4/4 empirically verified
  - ✅ `uv run pytest tests/codemem/test_bench_harness.py` → 22 passed, 1 deselected (slow integration)
  - ✅ `uv run python scripts/bench_codemem_vs_aider.py --repo . --requested-budget 1024 --out /tmp/bench.json` → valid JSON: `{requested_budget, tools: {codemem, aider, jcodemunch}, overlap, tokenizer, repo}`
  - ✅ `uv run ruff check` → clean on new files
  - ✅ `uv run lint-imports` → "Contracts: 2 kept, 0 broken"
- **Sub-Step Audit (L-081, L-083):** 0 PENDING sub-steps in M2 scope; 6 COMPLETE (Tasks 2.1-2.6).

**Key outcomes:**
- TDD RED/GREEN loops executed cleanly: Task 2.2 RED → Task 2.3 GREEN → Task 2.4 RED → Task 2.5 GREEN → Task 2.6 integration
- Harness is live and working against aa-ma-forge. Live M2 smoke signal (budget=1024): codemem 17 sym / 1239 tok, aider 67 sym / 1995 tok, jCodeMunch stub-skipped, Jaccard cm-vs-aider = 0.125.
- **Tokenizer-mismatch invariant empirically confirmed at M2 smoke time**: aider's cl100k_base count is ~95% over the requested 1024 budget; codemem's 4-char proxy yields ~21% over. M3's budget sweep {512,1024,2048,4096} × 2 repos will quantify the effect across the operating envelope.

**Artifacts created during M2:**
- `scripts/bench_codemem_vs_aider.py` (241 LOC; parser, measure_output, jaccard, 3 tool runners, CLI)
- `tests/codemem/test_bench_harness.py` (~230 LOC; 4 classes, 23 tests — 22 default + 1 @slow)
- `tests/codemem/fixtures/aider_repo_map_aa-ma-forge.txt` (golden fixture)
- `tests/codemem/fixtures/codemem_intel_aa-ma-forge.json` (golden fixture)
- `tests/codemem/conftest.py` (scoped sys.path injection for scripts/ imports)

**Decisions made during M2:**
- AD-009 — scripts/ test-import strategy (scoped conftest)
- AD-010 — Decorator kind string `"decorator"` (not `"@"`)
- AD-011 — codemem-mcp as explicit dev-dependency (OBS-001 fix)
- AD-012 — jCodeMunch invocation stub in Task 2.5 (MCP-protocol only)

**Unplanned blocker handled:** OBS-001 (pre-existing env drift — codemem-mcp editable install pointed at a moved repo path). Resolved in the middle of M2 via AD-011 — 1-line pyproject.toml change + `uv sync`. Retrospective positive: 24 previously-broken codemem tests now green.

**Tests state at M2 close:**
- Default `pytest`: 370 passed, 1 skipped, 5 deselected
- `pytest -m slow`: 1 additional passed (integration)
- Ruff: clean
- Import-linter: 2/2

**Commits this milestone:** `cea953f` (T2.1 tiktoken dep — yesterday), `edf9dcb` (T2.2 RED), `4d784e7` (T2.3 GREEN), `7e79ed1` (OBS-001 fix), `47d4e10` (T2.4 RED), `ab99bb3` (T2.5 GREEN), `f8aa1f2` (T2.6 integration).

**Next Milestone:** M3 Execute — AFK, SOFT gate, ~1 focused-dev day, complexity 30%. Tasks 3.1–3.4: clone fastapi at pinned commit, run harness at budgets {512, 1024, 2048, 4096} on aa-ma-forge + fastapi, sanity-check outputs. Produces the data that M4 report will consume.

---

## 2026-04-20 — OBS-001 RESOLVED via AD-011

**Resolution:** Added `"codemem-mcp"` to root `[tool.uv] dev-dependencies` in `pyproject.toml`. `uv sync` then installed the workspace member editably into `.venv` with the correct current-dir path.

**Root cause (full picture after deep investigation):**
- User moved the repo from `/home/sjnewhouse/github_private/aa-ma-forge/` to `/home/sjnewhouse/biorelate/projects/gitlab/github_private/aa-ma-forge/` (confirmed by user 2026-04-20).
- The conda env `bio312_07_25` (always active in this WSL shell) had an editable install of `codemem-mcp` pinned at the old path, so `codemem` CLI stopped working once the old path was gone.
- The project's `.venv` had NEVER installed `codemem-mcp` as a Python package — workspace declaration (`[tool.uv.workspace] members = [...]` + `[tool.uv.sources] codemem-mcp = { workspace = true }`) does NOT cause installation by itself; uv only installs it if it's a declared dep.
- Yesterday's Task 1.2 AC#4 (`uv run codemem intel ...`) succeeded because PATH fell through to the conda env's binary while the old path still existed.

**Decision AD-011 — Workspace member as explicit dev-dependency:**
- **Rationale:** Workspace membership declaration alone does not trigger installation in `uv sync`. For `import codemem` and `uv run codemem` to work reliably from this project's `.venv`, `codemem-mcp` must be a real dep. Dev-dep is the correct category (it's a runtime tool for the benchmark, not a shipped library dep of `aa_ma`).
- **Alternatives considered:**
  - (a) Add to `[project.dependencies]` — would pollute the public `aa_ma` package's deps. Rejected.
  - (b) Leave it implicit and rely on ambient installs — exactly the fragile state OBS-001 exposed. Rejected.
  - (c) Run `uv pip install -e packages/codemem-mcp` manually — imperative, not captured in version control, re-breaks on `.venv` recreation. Rejected.
- **Trade-off:** The workspace's `aa_ma` package now has a dev-dep on its own workspace sibling. Slightly circular-looking, but idiomatic for uv workspaces and is what the uv docs recommend for workspace members you want auto-installed.

**Empirical verification (post-fix, 2026-04-20):**
- `uv run python -c "import codemem; print(codemem.__file__)"` → `/home/sjnewhouse/biorelate/projects/gitlab/github_private/aa-ma-forge/packages/codemem-mcp/src/codemem/__init__.py` ✅
- `uv run codemem intel --budget=1024 --out=/tmp/obs001-resolved.json` → "wrote 17 symbols (4003B)" — matches Phase-3 + yesterday's baseline exactly ✅
- `.venv/bin/codemem` now exists (PATH resolution of `uv run codemem` hits .venv first, bypasses the broken conda-env binary) ✅
- Full test suite: **370 passed, 1 skipped, 5 deselected** (was 24 collection errors before fix) ✅
- New Task 2.2/2.3 tests: 13/13 still pass (no regression) ✅

**Knock-on positive effect:** 370 previously-uncollectable codemem tests now run green. This is retroactive evidence that the codemem package itself is healthy — the only break was the env-linkage.

**Impact on plan:** M3 prerequisite unblocked. No changes to M2 task structure. Plan proceeds at Task 2.4 (TDD RED for tiktoken normalization).

---

## 2026-04-20 — Task 2.3 GREEN: parser implementation + env drift observation

**Summary:** `parse_aider_output` implemented inline in `scripts/bench_codemem_vs_aider.py` (75 LOC total). All 13 Task 2.2 tests pass. Ruff clean. Two new decisions + one environmental observation logged below.

**Decision AD-010 — Decorator kind string = `"decorator"`:**
- **Rationale:** Task 2.2 tests don't pin the kind string for decorators. Choice is between `"@"` (terse, matches the prefix) and `"decorator"` (self-describing). Chose `"decorator"` — downstream consumers reading row tuples see a human-readable type; no information loss vs the terse form.
- **Alternatives rejected:** `"@"` (opaque at the tuple-level, requires kind-key legend); `"deco"` (abbreviation with zero benefit).
- **Trade-offs:** 6 extra chars per decorator row in the output. Negligible vs the readability gain.

**Observation OBS-001 — Pre-existing environment drift in `.venv`:**
- `uv pip list` reports `codemem-mcp 0.1.0.dev0` editable-installed from `/home/sjnewhouse/github_private/aa-ma-forge/packages/codemem-mcp`, but the current working directory is `/home/sjnewhouse/biorelate/projects/gitlab/github_private/aa-ma-forge/`.
- Effect: `from codemem.X import ...` in `tests/codemem/test_*.py` modules fails with `ModuleNotFoundError: No module named 'codemem'` — the install location is a different (possibly stale) clone of aa-ma-forge.
- Scope: all tests/codemem/test_*.py modules except `test_bench_harness.py` (the only file in this suite that imports from `scripts/` via conftest, not from `codemem`).
- **Confirmed pre-existing**, not caused by this plan: temporarily renaming `tests/codemem/conftest.py` → `.bak` and re-running `pytest tests/codemem/test_pagerank.py` produces the same `ModuleNotFoundError`. Conftest.py cannot cause this — it only adds `scripts/` to sys.path, never shadows `codemem`.
- **Suggested fix (NOT APPLIED — out of scope for this plan):** `uv sync --reinstall-package codemem-mcp` from the current-working-dir aa-ma-forge copy. This rebinds the editable install to the correct path. Deferring to user — running `uv sync` has side effects beyond this fix (may pull other dep updates).
- **Impact on this benchmark plan:** None. The benchmark harness does not import from `codemem` — it invokes `codemem` via `uv run codemem intel ...` (subprocess) per reference.md §API/CLI Endpoints. Subprocess invocation uses the project-venv's `codemem` console script which resolves correctly regardless of the import-path drift.

**Artifacts:** `scripts/bench_codemem_vs_aider.py` (new, 75 LOC, committed in the 2026-04-20 Task 2.3 commit).

---

## 2026-04-18 — Plan genesis

This plan is a direct continuation of the DEFERRED codemem Task 4.2. The original deferral (2026-04-17) cited 3 unverified preconditions. Those are now verified via 3 parallel research agents dispatched during the Phase 3 of THIS plan's authoring — findings pinned in reference.md §Phase-3 Research Findings.

**Key architectural decision:** Tokenizer normalization (codemem's 4-chars/token proxy vs Aider + jCodeMunch tiktoken) is the single subtlest measurement risk. Chosen mitigation: external `tiktoken` re-tokenization of all 3 tools' outputs before comparison. Alternatives rejected:
- (a) Standardize all 3 tools on the same tokenizer by modifying them — scope creep, not our code.
- (b) Report raw bytes only, punt on token comparability — misleads readers about the "equal budget" framing.
- (c) Hand-normalize with a character ratio — too fragile.

**Scope posture:** (iii) research-first, commit-later — user-selected 2026-04-18. Reflected in M1's HITL scope decision gate at sub-step 1.3.

---

## 2026-04-18 — Initial Context

### Feature Request (Phase 1)

Execute the token-budget benchmark DEFERRED as Task 4.2 from the archived codemem plan. Compare `PROJECT_INTEL.json` (codemem), Aider's repo-map, and jCodeMunch at equal budget on 2 reference repos. Feed the result back into the archived codemem plan's §12 M1-exit kill signal.

### Key Decisions (Phase 2 Brainstorming)

- **Decision AD-001:** Use external `tiktoken` to normalize all 3 tools' outputs before comparison.
  - **Rationale:** The 3 tools count tokens differently (codemem: 4-chars/token proxy; Aider: tiktoken-against-configured-model; jCodeMunch: tiktoken `cl100k_base`). Comparing at "equal requested budget" without external re-tokenization is apples-to-oranges.
  - **Alternatives Considered:**
    - (a) Modify all 3 tools to share a tokenizer — scope creep; not our code.
    - (b) Report raw bytes only, skip token comparability — misleads readers about the "equal budget" framing.
    - (c) Hand-normalize with a character ratio — too fragile across content types.
  - **Trade-offs:** Adds a `tiktoken` dev dep and a second normalization pass per measurement. In exchange: defensible, reproducible comparison.

- **Decision AD-002:** Scope = size + coverage (both raw bytes/tokens and top-symbol overlap).
  - **Rationale:** Research-supported default. Single-axis (size-only) would miss a key failure mode: codemem could win on size but lose on semantic coverage.
  - **Alternatives Considered:** (i) size-only, (ii) qualitative, (iii) cancel. User selected (iii) research-first, commit-later posture — reflected in M1.3 as a HITL confirmation gate rather than a hardcoded scope.
  - **Trade-offs:** More harness complexity (Jaccard overlap logic) vs stronger conclusions.

- **Decision AD-003:** Pin Aider at `aider-chat==0.86.2`, pin jCodeMunch at M1.1 install-time.
  - **Rationale:** Phase-3 research verified empirically against v0.86.2. Any upstream format change breaks the parser; pinning is the only defense.
  - **Alternatives Considered:** Track latest (too fragile); pin commit SHA (overkill for a one-shot benchmark).
  - **Trade-offs:** Future re-runs require re-pinning and potentially re-verifying.

- **Decision AD-004:** Use `fastapi` (tiangolo/fastapi) as the OSS benchmark repo; fallback `pallets/click`.
  - **Rationale:** fastapi is a well-known Python project with sufficient symbol density to stress all 3 tools. Public GitHub repo satisfies jCodeMunch's `index_repo` constraint. Click is the fallback if fastapi is too large for jCodeMunch's indexer.
  - **Alternatives Considered:** Internal biorelate repos (too client-sensitive); synthetic fixtures (don't exercise real-world ranking signal).
  - **Trade-offs:** First-run cost (initial clone + index) vs real-world signal.

- **Decision AD-005:** Inline the Aider output parser unless it grows beyond 100 LOC.
  - **Rationale:** KISS. Premature modularization is a documented anti-pattern; split only on proven need.
  - **Alternatives Considered:** Always split to `scripts/bench_aider_parser.py` (premature), never split (code smell if >100 LOC).
  - **Trade-offs:** Slightly more harness file size if inline; trivially refactorable later.

- **Decision AD-006:** Run each measurement 3× and report median, matching Task 4.1 `scripts/bench_codemem.py` pattern.
  - **Rationale:** PageRank tie-breaks and tiktoken edge cases produce non-determinism. Median of 3 collapses jitter without over-engineering.
  - **Alternatives Considered:** Single-run (too noisy); mean (sensitive to outliers); 10 runs (over-engineered for this scale).
  - **Trade-offs:** 3× wall-clock cost per budget × tool × repo cell.

### Research Findings (Phase 3)

Full findings in reference.md §Phase-3 Research Findings. Summary:

- **Aider** (empirically verified v0.86.2): `--map-tokens N` flag, PageRank ranking, hybrid prose/markdown output parseable via regex. Install: `uv tool install aider-chat==0.86.2`.
- **jCodeMunch** (docs-sourced): `token_budget=N` on multiple MCP tools, PageRank on import graph (direct parity with codemem), structured JSON output, public-repo-only fixture requirement.
- **codemem PROJECT_INTEL.json** (empirical ground truth): `{_meta, symbols[]}` shape; 17 symbols / 4003 bytes at budget=1024 on aa-ma-forge HEAD `3ab0aa9`; soft-budget binary-search logic at `pagerank.py:132-194`.
- **Tokenizer-mismatch invariant:** Report raw bytes + tiktoken tokens + symbol count per measurement. NEVER compare raw output at "equal requested budget" alone.

### Unresolved / Open Questions

- **U-001 — jcodemunch-mcp pin version:** to be chosen at M1.1 when install probes upstream release list. Deferred as HITL if install fails on non-python-dev-env.
- **U-002 — fastapi pinned commit:** to be chosen at M3.1 (target: stable recent release).
- **U-003 — Kill-criteria Signal 2 (M1 architectural kill) narrative framing:** The composite DID-NOT-TRIGGER verdict stays pinned by Task 4.1's 0.73× wall-clock (first conjunct of the AND). This benchmark only updates the Aider sub-claim state. If findings are ambiguous (codemem wins size but loses top-symbol overlap), M4.2 defaults to a "provisional — see benchmark §X" note on the Aider sub-claim while keeping the composite verdict unchanged.
- **U-004 — fastapi too large for jCodeMunch:** Fallback to `pallets/click`; trigger condition is M3.3 wall-clock exceeding the 30-min docs-first budget. Recorded as a risk (M3 R1).

### Remaining Questions (for HITL gates)

- **M1.3 gate:** Confirm scope = size+coverage (default) OR revise to size-only / qualitative / cancel.
- **M4.1 gate:** Stephen-newhouse-voice review of `docs/benchmarks/codemem-vs-aider.md`.
- **M4.2 gate:** Confirmation of **Signal 2** (M1 architectural kill) status-line wording — composite remains PROVISIONAL DID-NOT-TRIGGER (condition (a) cleared on small repo only; medium+large wall-clock measurements are still pending per existing kill-criteria.md status); Aider sub-claim state (confirmed / provisional / fails) per M3 findings.

---

## 2026-04-19 — M1.2 divergence: AC#3 CLI-vs-MCP-runtime category error

**Divergence:** Task 1.2 AC#3 specified that `jcodemunch-mcp --help 2>&1` should "mention at least one of: `token_budget`, `search_symbols`, `get_ranked_context`". Empirical check across top-level `--help` AND 6 subcommand helps (`serve`, `watch`, `config`, `claude-md`, `index`, `init`) found **zero** occurrences of those keywords.

**Root cause:** The Phase-3 research correctly identified `token_budget` / `search_symbols` / `get_ranked_context` as MCP tool parameters and tool names — these are exposed over the MCP protocol at runtime, NOT as CLI help text. AC#3's wording was authored assuming CLI `--help` would surface MCP tool metadata. That was a category error.

**Functional status (empirically verified 2026-04-19):**
- `jcodemunch-mcp --help` exit 0 ✅
- Subcommands present: `serve`, `watch`, `config`, `claude-md`, `index`, `index-file`, `init`, `hook-*`, `watch-claude`, `download-model`, `install-pack` ✅
- `jcodemunch-mcp config` shows `Tool Profile: full (all tools)` (default); `disabled_tools: ['test_summarizer']` ✅
- Phase-3 findings on jCodeMunch's `token_budget` flag, `search_symbols` tool, PageRank-on-import-graph ranking: unchanged. These are MCP protocol-level artifacts; they will be re-verified at M2 harness time via actual MCP protocol exercise (when harness invokes `get_ranked_context(query, token_budget=N)`).

**Resolution:** AC#3 reframed to reality-aligned CLI-level sanity check (new wording in tasks.md): `jcodemunch-mcp --help 2>&1` exit 0 AND `serve` subcommand exists AND `jcodemunch-mcp config` shows `Tool Profile` row. Phase-3 findings in reference.md §jCodeMunch remain valid unchanged — they describe MCP-runtime behavior which was outside the scope of CLI `--help` probing.

**Impact on downstream:** None. M2 harness will exercise jCodeMunch via actual MCP protocol (`get_ranked_context`, `search_symbols`) during the real benchmark — that IS the substantive verification that the tool surface is intact. CLI-level check is a pre-flight sanity only.

**Decision AD-007:** Accept divergence as an AC-wording error (not a tool regression). Do NOT extend M1 to re-research. Move to Task 1.3 (HITL scope gate).
- **Rationale:** Phase-3 findings on jCodeMunch functionality are intact; the plan's "extends M1 to re-research" rule was intended for functional regressions, not AC-wording bugs.
- **Alternatives considered:** (a) full MCP-protocol empirical probe (start serve + send `tools/list` JSON-RPC) — higher complexity, introduces subprocess management; (b) skip AC#3 — loses the CLI sanity signal entirely; (c) halt & re-research — slows progress with no new signal.
- **Trade-offs:** This decision trades AC-adherence-by-letter for AC-adherence-by-spirit. The reframed AC preserves the intent ("tool is installed and functional at CLI level") while aligning with CLI reality.

---

## 2026-04-19 — M1.3 scope decision

**Decision AD-008:** Benchmark scope = **size + coverage** (AD-002 default, Phase-3 research-validated).

- **Scope confirmed (HITL):** User selected `size+coverage` at the M1.3 HITL gate 2026-04-19. AD-002 moves from provisional to pinned.
- **What this means operationally:**
  - M2 harness (Task 2.5) MUST emit per-measurement `{raw_bytes, tiktoken_tokens, symbol_count}` (size axis) AND `overlap: {codemem_vs_aider, codemem_vs_jcodemunch, aider_vs_jcodemunch}` (coverage axis via top-N Jaccard)
  - M3 execution sweeps both axes at budgets `{512, 1024, 2048, 4096}`
  - M4 report presents a 2-axis comparison table, not 1-axis
- **Alternatives considered and rejected at this gate:**
  - `size-only`: would miss the "wins size, loses coverage" failure mode; rejected as weaker.
  - `qualitative`: non-reproducible; rejected — cannot feed kill-criteria Signal 2 with hand-grades.
  - `cancel`: rejected — benchmark still worth running given Phase-3 research investment.
- **Rationale for recommended path:** Research-supported default; the slightly higher M2 harness complexity (Jaccard logic) is worth the stronger downstream conclusions. M2 AC already assumes this path (test matrix structured around `overlap` key).
- **Downstream impact:** No changes to M2/M3/M4 task structure — they were authored against the default scope. Unblocks M2 start.
- **Kill-criteria Signal 2 effect:** Continues to be updated by **Aider sub-claim only** per M4.2. Composite verdict remains PROVISIONAL DID-NOT-TRIGGER (condition (a) via Task 4.1 0.73× holds on small repo only; medium+large still pending per kill-criteria.md).

---

## 2026-04-20 — AD-009: scripts/ test-import strategy (test infrastructure)

**Decision AD-009:** Tests that need to import from `scripts/` (e.g., the bench harness with its inline parser) use a scoped `tests/codemem/conftest.py` that adds `scripts/` to `sys.path` at collection time.

- **Rationale:** AD-005 pins the parser inline in `scripts/bench_codemem_vs_aider.py` (no split unless >100 LOC). But tests need to `from bench_codemem_vs_aider import parse_aider_output`. The scripts/ directory is not a Python package; making it one is scope creep. A 1-line-of-logic conftest is the minimal test-infrastructure change that satisfies both constraints.
- **Scope:** Limited to `tests/codemem/` subtree (conftest.py autoloads in pytest for that directory's tests only). No effect on production imports or non-codemem tests.
- **Alternatives considered:**
  - (a) Convert `scripts/` to a package — would require `__init__.py`, affects all script files unrelated to this benchmark, unnecessary scope expansion.
  - (b) `importlib.util.spec_from_file_location` inside each test — DRY violation, per-test boilerplate for a test-infra concern.
  - (c) Hoist parser into `packages/codemem-mcp/src/codemem/parsers/aider_repomap.py` — contradicts AD-005 (which explicitly allows "inline OR scripts/bench_aider_parser.py if >100 LOC" — both options are in scripts/, not a real package).
- **Trade-offs:** sys.path injection is a test-infra side effect. In exchange: AD-005 integrity preserved; imports are natural; no production code modifications.
- **Verification pending:** Conftest correctness can only be proven transitively — when Task 2.3 GREEN creates the parser module and tests collect successfully, conftest is confirmed working. Before then, "parser module not found" is indistinguishable from "scripts/ not on sys.path".

---

## 2026-04-20 — Task 2.2 RED: parser API pinned via failing tests

**What was done:** 12 failing pytest tests written against a live-captured Aider fixture, defining the `parse_aider_output(text: str) -> list[tuple[str, str, str]]` contract. TDD RED verified via `pytest` → `ModuleNotFoundError` (correct fail reason: production code intentionally absent).

**Parser contract pinned (reviewed by Task 2.3 GREEN):**
- Signature: `parse_aider_output(text: str) -> list[tuple[str, str, str]]`
- Row shape: `(file, symbol_name, kind)` — all strings, non-empty
- Empty input → `[]`
- `kind` includes at minimum `"def"` and `"class"`; decorator kind-name left unconstrained
- `⋮` never in symbol names (elision, not a symbol)
- Preamble (lines 1-10 of fixture: `Aider`, `Model`, `Git`, `Repo-map`, `Using`) never leaks
- Wrapped continuations (e.g., line 18 `dict:` from signature wrap) never mistaken for headers

**Trap discovered at test-design time (before any code):** Naive regex `line ends with :` would match `dict:` on line 18 — a line-wrapped return type from `│def blast_radius(...) -> ` on line 17. Test `test_file_fields_look_path_like` is the permanent regression guard; Task 2.3's parser must handle this.

**Fixture characteristics (empirical, HEAD af10ec6):** 257 lines; 59 symbol markers (43 `│def`, 10 `│class`, 6 `│@`-adjacent); 78 `⋮` elisions; 22 naive header-candidates (1 is the `dict:` trap).

**Next:** Task 2.3 GREEN — implement `parse_aider_output` inline in `scripts/bench_codemem_vs_aider.py`. Target: all 12 tests green, <100 LOC parser (AD-005 inline clause).

---

## 2026-04-19 Milestone Completion: M1 Environment Setup + Precondition Re-Verification

- **Status:** COMPLETE (HITL-approved via AskUserQuestion 2026-04-19)
- **Acceptance criteria:** 4/4 empirically verified
  - ✅ `aider --version` returns `0.86.2` (pinned per AD-003)
  - ✅ `jcodemunch-mcp --version` returns `1.59.1` (pinned this session per AD-003 + AD-006)
  - ✅ `uv run codemem intel --budget=1024 --out=/tmp/bench-intel-1024.json` produces JSON with `_meta.written_symbols = 17` + PageRank-ranked `symbols[]` (per-entry schema exact match to plan)
  - ✅ HITL decision AD-008 recorded under `## 2026-04-19 — M1.3 scope decision`
- **Key outcome:** Pinned tool surface confirmed; codemem intel JSON schema stable; scope decision AD-008 = size+coverage pins AD-002.
- **Artifacts:** 3 tasks closed with full Result Logs; 2 new decisions (AD-007 AC-reframe, AD-008 scope-pin); reference.md jcodemunch-mcp pin TBD → ==1.59.1 (+binary list).
- **Tests:** N/A for M1 (setup milestone, no pytest; all AC were empirical shell verifications).
- **Commits:** `767acb0` (T1.1), `deee7c5` (T1.1 provenance), `e334e42` (T1.2 + divergence), `e174635` (T1.2 provenance), [this commit] (T1.3 + M1 finalization).
- **Divergences handled:** 1 (AC#3 CLI-vs-MCP-runtime category error → AC reframe, not research re-extension).
- **Next Milestone:** M2 Harness + Parser (TDD) — AFK, SOFT gate, ~1.5-2 days, complexity 55%. Task 2.1: Add `tiktoken` as dev dep in root pyproject.toml.
