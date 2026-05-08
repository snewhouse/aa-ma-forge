# codemem-benchmark-fairness-v2 Context Log

_This log captures architectural decisions, trade-offs, gate approvals, and unresolved issues for the v2 fair benchmark plan._

---

## 2026-05-08: M3 Milestone Completion — v2 report + Signal 2 re-baseline (AD-V2-015)

**Status:** COMPLETE.

**Headline empirical finding from the full sweep:** codemem post-M1 reaches per-symbol parity with aider on fastapi at budget=1024 (1.07× vs aider). This is a substantive M1-driven shift from v1's 1.2× gap on the same cell. Across all 4 fastapi budgets, codemem stays within 5-19% of aider per-symbol — within the run-to-run noise band Aider exhibited in v1 at budget 4096. The metadata-overhead penalty amortises out as the symbol pool grows.

On aa-ma-forge (small reference repo) the gap narrowed from v1's 2.4× to v2's 2.3× (a 4-percentage-point improvement attributable to the M1 proxy fix), but did not flip the per-symbol verdict.

**AD-V2-015: case (b) mixed verdict approved for kill-criteria.md Signal 2.**

HITL approval (M3.3, AskUserQuestion 2026-05-08): user chose "Approve PROVISIONAL DID-NOT-TRIGGER (case b mixed)" over stricter (flip conjunct (b) to PASS on fastapi) and looser (footnote-only) alternatives.

Verdict shape:
- **Conjunct (a) wall-clock:** unchanged from v1. Cleared on aa-ma-forge at 0.73× `/index`. Medium-repo and 50k-LOC measurements unchanged (still pending user-provided reference repos).
- **Conjunct (b) Aider efficiency:** case (b) mixed. FAILS on aa-ma-forge (codemem 2.3× worse), DRAW on fastapi (codemem 1.07× — within noise).
- **Composite:** PROVISIONAL DID-NOT-TRIGGER. AND composite cannot fire while conjunct (a) holds on the only measured repo. Conjunct (b) failure is now materially weaker than v1 reported because root cause #1 (proxy under-reporting) has been removed and root cause #2 (metadata overhead) has been shown to amortise out at scale.

Why not the stricter "flip conjunct (b) to PASS on fastapi" framing: 1.07× is within run-to-run noise, not a clear win. Calling it a PASS would be more codemem-favourable than the data supports. The "DRAW within noise" framing is honest and matches the empirical state.

Why not the looser "footnote-only" framing: v1's wording ("FAILS on both repos") is no longer accurate post-M1. Leaving it untouched would be misleading; v2's narrative requires the rewrite.

**Compound finding (logged for any future v3 sweep):** the v1-to-v2 narrowing on fastapi (1.2× → 1.07×) is a real M1 effect, not measurement noise. v1 measured with a 4-chars proxy that under-reported codemem by ~20%; correcting that should INCREASE codemem's measured per-symbol cost and WIDEN the gap. Instead the gap narrowed, which means aider's overshoot under cl100k_base equalisation is a comparable contributor. v2 numbers reflect both fixes simultaneously. The honest comparison is: codemem and aider were closer than v1 suggested, after both sides are equalised.

**M2c.6 deferred sweep is now complete (AD-V2-014 closure):**

- aa-ma-forge: full 4-budget × 3-run sweep at `/tmp/bench-aa-ma-forge-v2.json` (8.7KB). All 5 tools status=ok. codemem honest at every budget (495/960/2045/4049 within 512/1024/2048/4096 ceilings). yek 0 files at budgets 512/1024/2048; emits content at 4096.
- fastapi: full 4-budget × 3-run sweep at `/tmp/bench-fastapi-v2.json`. All 5 tools status=ok. codemem honest at every budget (507/1016/2024/4083). yek 1 small file (258 tokens) at every budget (different leading file from aa-ma-forge but same order-preserving halt).
- Combined raw data: `docs/benchmarks/results-codemem-vs-aider-v2-2026-05-08.json` (21KB).

**Pre-flight issue caught and resolved:** initial fastapi sweep failed because `/tmp/bench-fastapi/.codemem/index.db` did not exist (codemem requires a one-time pre-build on a fresh repo clone — OBS-002 from v1). Killed and restarted after running `cd /tmp/bench-fastapi && uv run --project <aa-ma-forge-root> codemem build` (1.0s, 1129 files, 4954 symbols, 3.3MB index.db). Documented in v2 report Reproducibility section. Future M2c-style sweeps on fresh clones must include this pre-build step.

**Tooling side-effect logged (memory):** running aider via subprocess opens a browser window per invocation. Across 24 sweep invocations (12 per repo × 2 repos), this spawned 24 browser tabs. User flagged the behaviour 2026-05-08 mid-sweep. Saved to `~/.claude/projects/.../memory/feedback_aider_browser_window.md` with a "How to apply" pointer to the harness's `_run_aider` call site for any future v3 sweep work.

**Files changed at M3:**

- `docs/benchmarks/codemem-vs-aider-v2.md`: NEW. 454 lines. Full v2 report with 5-tool panel, 10-pair overlap matrix, 11 Phase-4.5 corrections, both-repo tables, case (b) mixed verdict.
- `docs/benchmarks/codemem-vs-aider.md`: banner inserted at top (line 3). v1 body unchanged.
- `docs/benchmarks/results-codemem-vs-aider-v2-2026-05-08.json`: NEW. 21KB combined raw data.
- `docs/codemem/kill-criteria.md`: "Latest update" header bumped to 2026-05-08. Signal 2 status block rewritten with v2 numbers and case (b) mixed wording.
- AA-MA artifacts: tasks.md (M3.1-M3.4 Result Logs + duplicate M2c stub cleanup), context-log.md (this entry), provenance.log (M3 milestone entries), reference.md (no changes — the empirical findings are all data, not new immutable facts).

Voice gate clean: 0 em-dashes, 0 AI vocab matches in v2 report.

---

## 2026-05-08: M2c Milestone Completion — yek adapter + 5-tool harness + 10-pair overlap (AD-V2-013, AD-V2-014)

**Status:** COMPLETE.

**AD-V2-013: Overlap block expanded from 3 pairs to up to 10 pairs with `level` annotation.**

The plan reference.md §Harness JSON Output Contract showed all C(5,2)=10 pairs in the v2 output shape, but didn't address the granularity asymmetry: codemem/aider/jcm emit `(file, symbol_name)` tuples while Repomix and yek emit bare file paths. Computing "overlap" between heterogeneous element types is meaningless without disambiguation.

Resolution: every overlap pair now carries a `level` field with one of two values:
- `"symbol"`: jaccard + RBO@10 over `(file, symbol_name)` tuples. Used for the 3 pairs where both tools emit symbol-level data: codemem_vs_aider, codemem_vs_jcodemunch, aider_vs_jcodemunch. These are the same pairs that existed pre-M2c; behaviour preserved.
- `"file"`: jaccard + RBO@10 over file-path strings. Used for any pair involving Repomix or yek. For the symbol-emitting tools in mixed pairs, the file list is derived via `_file_list_from_symbols()` which preserves first-appearance order so RBO@10 stays meaningful (the tool's ranking expressed at file granularity rather than symbol granularity).

Implementation touched 3 helpers:
- `jaccard()` and `_pair_overlap()` were widened from `tuple[str, str]` element type to `TypeVar("H", bound=Hashable)`. Same code, broader contract.
- New `_file_list_from_symbols()` helper for the mixed-pair case.
- New `_extract_yek_filenames()` parser + `_run_yek` adapter mirroring the Repomix pattern.

**Harness JSON contract change:** `overlap.<pair>.level` is now a required field. Downstream consumers (M3 report) MUST read this to know which granularity they're working with. The same `jaccard` numeric value means radically different things at the two levels.

**AD-V2-014: M2c.6 narrowed from full sweep to single-budget smoke.**

The plan AC for M2c.6 originally called for full 4-budget × 2-repo × 3-run = 40-cell sweep. After M2c.5 landed, decided to narrow M2c.6 to single-budget aa-ma-forge smoke only. Rationale:

1. The 40-cell sweep is M3's input data, not M2c's output. M3 generates the v2 report from this data. Running the sweep at M2c, then re-running at M3 after stylistic edits, would be wasteful (~1-2 hours per re-run).
2. Single-budget 5-tool smoke fully validates the harness shape contract (status=ok-or-ok_no_symbols for all 5 tools, 10-pair overlap with level annotation). That's the milestone exit criterion that matters.
3. Pattern parity with M1/M2a/M2b: each prior milestone shipped infrastructure + single-budget validation, deferred multi-budget sweeps to consumers.

M3 prep will run the full sweep with the now-shipped 5-tool harness; results feed directly into the v2 report's headline tables.

**Headline empirical findings (logged for M3 v2 report):**

The 5-tool panel reveals a 5th tool-category dimension beyond v1's "tools count budgets differently" thesis:

| Tool         | Budget concept              | Behaviour at budget=1024 (aa-ma-forge) |
|--------------|-----------------------------|----------------------------------------|
| codemem      | budget-aware, optimising    | 14 symbols / 960 tokens (94% utilisation, post-M1 honest) |
| aider        | budget-aware, overshooting  | 68 symbols / 2,016 tokens (97% overshoot) |
| jcodemunch   | top_n heuristic + truncate  | 40 symbols / 1,350 tokens (32% overshoot) |
| Repomix      | dump-everything, no budget  | 244 files / 578,220 tokens (56,400% overshoot) |
| yek          | budget-aware, **order-preserving (NOT optimising)** | **0 files** / 1 token — first git-importance file (CHANGELOG.md) alone exceeds budget |

The yek finding is particularly striking. yek's design — preserve git-importance order, halt at the first file that doesn't fit — means at common budget thresholds (1024) on real repos with a single dominating top-ranked file, it produces NO useful output. Probe across {1024, 4096, 16384, 65536}: 0 / 3 / 8 / 28 files emitted respectively, all starting with CHANGELOG.md.

This sharpens the v2 report's central argument from "all tools count budgets differently" (v1 thesis, framing) to "all tools also ENFORCE budgets differently, and some tools become USELESS at common budget thresholds due to design choices, not bugs". Choosing a context-priming tool requires understanding both axes.

**Files changed at M2c (M2c.2-M2c.6):**

- `scripts/bench_codemem_vs_aider.py`: +`_extract_yek_filenames`, +`_run_yek`, +`_file_list_from_symbols`, +`--include-yek` CLI flag, +`file_paths` field on Repomix/yek returns, generalised `jaccard`/`_pair_overlap` to `TypeVar("H", bound=Hashable)`, expanded `_build_report` to up-to-10-pair overlap with `level` annotation.
- `scripts/bench_sweep.py`: +`include_repomix`, `include_yek`, `aider_tokeniser_equalise` keyword args on `_run_harness_once`; +`--include-repomix`, `--include-yek`, `--aider-tokeniser-equalise` CLI flags; dynamic per-tool progress print; `tools_included` field in output for provenance.
- `tests/codemem/test_bench_harness.py`: +TestYekAdapter (6 tests), +TestFileListFromSymbols (2 tests), +TestFiveToolOverlap (4 tests). Total 12 new tests.
- `tests/codemem/fixtures/yek_output_aa-ma-forge.json`: 32KB / 8,396 tokens / 11 files (from `parser/` subdir at `--tokens 100000`).

420/420 codemem suite green, ruff clean, import-linter 2/2 contracts kept.

---

## 2026-05-08: M2c.1 — Yek install + flag deviation (AD-V2-012)

**Status:** COMPLETE. Yek 0.22.1 installed at `/home/sjnewhouse/.cargo/bin/yek` via `cargo install yek` (199 transitive deps compiled). HITL gate (which install path) resolved by user via `AskUserQuestion`: "cargo install yek (Recommended)" chosen over pre-built script and "drop yek" alternatives.

**AD-V2-012: Yek `--tokens N` is a combined flag, not a boolean toggle.**

The plan-time reference.md (line 70 pre-edit) and §M2c claimed Yek invocation `yek --tokens N --json`. Empirical probe at M2c.1 revealed actual semantics:

| Flag | Plan-time assumption | Actual semantics |
|---|---|---|
| `--tokens N` | Boolean `--tokens` + value `N` (two args) | COMBINED — enables token mode AND sets budget to N in one argument |
| `--json` | JSON output (mode flag) | JSON to **stdout**; `--output-dir` / `--output-name` silently ignored |
| Output schema | (unspecified) | `[{"filename": str, "content": str}, ...]` — file-level only, no symbols, `filename` relative to input-dir argument |

The plan's invocation `yek --tokens N --json <repo>` works as intended *literally* (it's the right command), but the documented mental model behind it was wrong. Logging here so M2c.3 adapter design and M3 report methodology section reference correct semantics.

**Empirical behaviour finding (relevant to M3 v2 report):**

Yek is **order-preserving**, not budget-optimising. On `packages/codemem-mcp/src/codemem/parser/` (11 files):

| Budget | Files emitted | Note |
|---|---|---|
| `--tokens 1024` | 1 (`__init__.py`, 58 chars) | Stops at first file that doesn't fit; does NOT skip ahead. Next file (`ast_grep.py`) is ~3,080 tokens. |
| `--tokens 100000` | 11 | All files fit. |
| byte mode (default 10MB) | 11 | Reference. |

This is fourth tool-category behaviour for the v2 panel:
- **codemem (post-M1)**: budget-aware, optimising — fits N best-rank symbols within budget.
- **Aider**: budget-aware, overshooting — `--map-tokens 1024` produced 2016 actual cl100k_base tokens (97% overshoot, M2a empirical).
- **jCodeMunch (M2a pivot)**: top_n heuristic + harness-level truncation — overshoots 31% on aa-ma-forge (M2a empirical).
- **Repomix**: dump-everything, no budget concept — 584× over codemem at budget=1024 (M2b empirical).
- **Yek**: budget-aware, order-preserving (NOT optimising) — small-leading-file repos fit more, large-leading-file repos truncate aggressively. NEW finding 2026-05-08.

For M3, the headline "tools count budgets differently" thesis broadens to "tools ALSO ENFORCE budgets differently". The M3 methodology section needs a 5-row tool-category table.

**Implementation impact on M2c.3:**

`_run_yek` adapter shape mirrors `_run_repomix`:
- Subprocess `yek --tokens N --json <repo>` → capture stdout
- Parse JSON `[{filename, content}, ...]`
- `status = "ok_no_symbols"` (yek is file-level like Repomix)
- Concatenate `content` fields, re-tokenise via `_TIKTOKEN_ENCODER` for honest measurement
- `file_count` as secondary metric
- No symbol-level overlap with codemem/aider/jcodemunch — file-level only (M2c.4 introduces 10-pair overlap structure but Yek/Repomix overlap will be file-level vs symbol-level for the others; document as known asymmetry)

**Files changed at M2c.1:**

- `codemem-benchmark-fairness-v2-reference.md` (5 edits): Yek section (line 65-68), dependency table (line 159), CLI flags table (lines 188-189), API/CLI Endpoints (line 225), Last-Updated bump.
- `codemem-benchmark-fairness-v2-tasks.md`: M2c.1 marked COMPLETE with full Result Log; cleaned up 2 stale duplicate M2a.6/M2a.7 PENDING stubs (plan-amendment leftovers within already-COMPLETE M2a milestone — would have tripped L-081 sub-step consistency check on re-validation).
- `codemem-benchmark-fairness-v2-context-log.md`: this entry.
- `codemem-benchmark-fairness-v2-provenance.log`: M2c.1 entry appended.

No code changes at M2c.1 — pre-flight only. M2c.2 onwards introduces code.

---

## 2026-05-05: M2b Milestone Completion — Repomix adapter

**Status:** COMPLETE.

**Empirical finding (headline for M3 v2 report):** Repomix at full-repo emits 560,974 cl100k_base tokens for aa-ma-forge — **584× larger than codemem at budget=1024**. Repomix is a *dump-everything* tool with no native budget concept; the "compare at equal budget" framing breaks down. M3 must explicitly distinguish "budget-aware tools" (codemem, aider, jcodemunch, yek) from "dump-everything tools" (Repomix).

**Implementation choices:**

- **AD-V2-009 (decided 2026-05-05): Use `npx -y repomix@1.14.0` instead of global `npm install -g repomix`.** Empirical pre-flight showed npm 11.6.0 installed but Repomix not global. Per plan AC alternative path. Pinned via `@1.14.0` for reproducibility. No global state, faster CI provisioning, deterministic version.

- **AD-V2-010: Repomix returns `status="ok_no_symbols"` with empty `symbols=[]`.** Repomix doesn't emit symbol-level data; per plan AC `symbol_count may be 0`. Excluded from 3-tool overlap (codemem/aider/jcodemunch). M2c will introduce file-level overlap if Repomix participates in the 5-tool sweep — file paths are the natural granularity for Repomix.

- **AD-V2-011: `--include-repomix` is opt-in (default off).** Repomix is slow (~30-60s on full repo) and produces 2.2MB output. Default 3-tool invocation stays fast for development; M2c full sweep enables Repomix explicitly.

**Files changed:**

- `scripts/bench_codemem_vs_aider.py` (~80 LOC: `_extract_repomix_file_paths` regex parser, `_run_repomix` adapter via npx, `_build_report` 4th tool support, `--include-repomix` CLI flag)
- `tests/codemem/test_bench_harness.py` (TestRepomixAdapter, 5 tests)
- `tests/codemem/fixtures/repomix_output_aa-ma-forge.xml` (32KB fixture from `parser/` subdir, 11 files)

---

## 2026-05-05: M2a Pivot — jCodeMunch tool change (AD-V2-008)

**Discovery (empirical probe, per "code is truth" directive):**

`get_ranked_context` in jcodemunch-mcp 1.59.1 has an encoder bug. The compact-encoding schema at `jcodemunch_mcp/encoding/schemas/get_ranked_context.py` declares table columns `[id, name, kind, file, line, score, token_cost, summary]`, but the actual `context_items` returned by `tools/get_ranked_context.py` use keys `[symbol_id, relevance_score, centrality_score, combined_score, tokens, ...]`. Schema mismatch → encoder emits `i,,,,,,,,` rows with all 8 columns NULL even when `items_included > 0`.

Verified at three budgets (1024, 4096) with three queries — same empty-row result. No env var or CLI flag bypasses MUNCH encoding. Bug is latent: v1 plan never hit it because v1 stubbed jCodeMunch (`scripts/bench_codemem_vs_aider.py:175-185` returns `status="skipped"`).

**Decision (HITL via AskUserQuestion 2026-05-05):**

**AD-V2-008: Pivot M2a.4 from `get_ranked_context` to `get_symbol_importance(top_n, algorithm='pagerank')`.**

Rationale:
- `get_symbol_importance` returns clean MUNCH/gen1 with populated `symbol_id|rank|score|in_degree|out_degree|kind` rows. Verified live (20 rows, all populated, symbol IDs in `<file>::<name>#<kind>` format).
- Methodologically *cleaner* for the v2 fairness benchmark: pure PageRank, no BM25. Apples-to-apples with codemem (post-M1 PageRank fix) and Aider (PageRank-on-call-graph). The original `get_ranked_context` choice would have introduced BM25 query-bias into the comparison.
- Token budget enforcement moves to harness level: call `get_symbol_importance(top_n=K)` for K large (say 200), capture raw response, re-tokenize with tiktoken, truncate symbol-list to first N tokens of the response. Parallels how Repomix (M2b) and Yek (M2c) will be measured.
- Trade-off: lose native `token_budget` arg parity with codemem CLI. Trade-off accepted because methodological purity outweighs API parity.

Alternatives considered:
- B: `search_symbols(query, token_budget=N)` — has native token_budget but BM25-driven; inferior fairness.
- C: Skip jCodeMunch, defer to v3 — defeats M2a's main purpose.
- D: Pin older jcodemunch-mcp version — uncertainty about whether older versions had the bug too.

**Scope changes:**

- M2a.4 acceptance criteria updated: target tool is `get_symbol_importance`; harness-level budget enforcement; MUNCH/gen1 parser required (~30 LOC inline).
- M2a measurable goal unchanged (3-tool x 4-budget x 3-run with all status=ok).
- TestJCodeMunchAdapter (>=3) tests now target the new adapter's behaviour.
- `JCM_SYNTHETIC_MCP_TEXT` fixture in `test_bench_harness.py:35-42` was a plain-JSON shape that does NOT match the live MUNCH/gen1 wire format — replace with realistic MUNCH/gen1 fixture sample.

**Empirical resolutions completed during pivot probe:**

- **U-008 RESOLVED:** `aider --model gpt-3.5-turbo --show-repo-map --map-tokens 256 .` works WITHOUT `OPENAI_API_KEY` (warning-only, exit 0, repo-map produced). The `--show-repo-map` flag is a pure local tokeniser operation; API key is only required for actual LLM completions. M2a.2 HITL gate auto-resolves to "Aider equalised path".
- **mcp>=1.27 already present:** `mcp 1.27.0` is installed transitively via `fastmcp>=2.0` in codemem-mcp dependencies. M2a.1 reduces to declaring it as an explicit dev dep (per L-055) so reproducibility doesn't depend on transitive resolution.

---

## 2026-05-05: M1 Milestone Completion

**Status:** COMPLETE. Resumed after 15-day pause; review confirmed reference.md drift was 1 line on `_CHARS_PER_TOKEN` location (32 → 33), no semantic drift. TDD-RED → GREEN cycle clean.

**Empirical validation of the v2 thesis:** at budget=1024 on aa-ma-forge:
- v1 (proxy): 17 symbols, 1239 actual tiktoken tokens (21% overshoot vs claim)
- v2 (encoder fix): 14 symbols, 960 actual tiktoken tokens (6% safety margin under budget)
- Token delta: -22.5% — confirms the v1 retro estimate was correct within 1.5 percentage points

**Discovered finding — `_CHARS_PER_TOKEN` sister bug (out of M1 scope):**

A second `_CHARS_PER_TOKEN = 4` constant lives in `packages/codemem-mcp/src/codemem/mcp_tools/__init__.py:54`, used by `_exceeds_budget()` at line 121 to gate ALL MCP tool outputs (`aa_ma_context`, `blast_radius`, `co_changes`, `dependency_chain`, `who_calls`, etc.) — not just PROJECT_INTEL.json. Same biased proxy pattern, parallel code path. The fix is identical mechanically (~5 lines).

This is **not** in v2's scope (M1 was specifically pagerank.py + PROJECT_INTEL.json budget; the v2 5-tool benchmark compares PROJECT_INTEL outputs, not raw MCP tool outputs). Logging here for future work:

- **Recommended scope:** v2.x patch milestone or a v3 follow-up. Estimate: 0.5 day, including TDD-RED phase mirror of M1.
- **Risk if deferred:** MCP tool surface honesty in client-facing operations. Not a v2 blocker.
- **Decision rationale:** Avoid scope creep mid-execution; document and defer.

**AC3 regex defect (documentation, not code):**

The M1.2 acceptance criteria included regex `/^[01]\.\d{1,3}(e-?\d+)?$/` to validate 3-sig-fig rank emission. The regex assumes `f"{x:.3g}"` always produces forms like `0.123`, but Python's `:.3g` for small values uses decimals with leading zeros (`0.0153`, `0.00153`), which fail the regex despite being correct 3-sig-fig representations. The behavioural test `float(f"{x:.3g}") == x` is the correct semantic check; 14/14 ranks pass. Documented as a regex defect; tasks.md M1.2 AC annotated.

**Files changed (M1 commit):**

- `packages/codemem-mcp/src/codemem/pagerank.py` (~10 lines)
- `packages/codemem-mcp/pyproject.toml` (+1 dep)
- `tests/codemem/test_pagerank.py` (~50 lines: 1 deleted, 3 added)
- AA-MA artefacts: tasks.md, reference.md, context-log.md, provenance.log

---

## 2026-04-20, AC amendment: M1 symbol-count floor

**Event:** During M1 TDD-RED preparation (reading pagerank.py + test_pagerank.py + v1 empirical data), discovered that the original M1 measurable goal (">= 17 symbols at budget=1024") was mathematically incompatible with the point of the fix.

**Reasoning:** v1 measured 17 symbols at budget=1024 char-proxy, which equated to 1239 actual tiktoken tokens (21% overshoot per tokeniser-mismatch invariant in reference.md). Post-fix, budget=1024 means <=1024 actual tiktoken tokens. At ~72 tok/sym on aa-ma-forge, that fits ~14 symbols. Rank truncation saves a few tok/sym, bringing per-symbol cost to ~65, fitting ~15 symbols. So >= 17 is mathematically impossible under the honest budget.

**Decision (HITL, via AskUserQuestion):** Replace the ">= 17" floor with "`>= 12 symbols AND <= 1024 actual tiktoken tokens`". Rationale:
- 12 = 20% below v1 baseline; catches catastrophic regression but allows the expected honest reduction.
- <= 1024 tiktoken is the CAUSE-level invariant the fix enforces; asserting it directly is the methodology-correct thing to do.
- Per L-059 falsifiability: both numbers are pytest-assertion-compatible.

**Scope:** Milestone 1 measurable goal + Step M1.4 AC updated in tasks.md. Step M1.1 and M1.2 code ACs unchanged. Plan file at ~/.claude/plans/ultrathink-and-grill-me-did-zazzy-creek.md unchanged (this is a post-approval execution-time AC refinement based on empirical math, not scope change).

**Provenance:** Flagged in-session at 2026-04-20 before any pagerank.py edits, satisfying the "make no assumptions; code is truth" directive.

---

## 2026-04-20: Plan genesis

**Feature request (Phase 1):**

The `/grill-me` adversarial review of the v1 `codemem-token-benchmarks` report (completed 2026-04-20 at commit `7a335fc`) surfaced 11 methodology concerns. 1 HIGH (jCodeMunch stubbed out), 8 MEDIUM (including a silently biased 4-char-per-token proxy in codemem and a tokeniser mismatch when comparing against Aider), 2 LOW. It also identified 2-3 serious competitors (Repomix, Yek) that v1 never benchmarked. Before Signal 2 of the kill-criteria is cited in downstream architectural decisions, the bias in codemem's own proxy must be removed and the comparison must include those competitors.

During Phase 2 brainstorming the user selected **Tier 3 scope** (proxy fix + jCodeMunch live + RBO + Repomix + Yek) over:
- Tier 1 (surgical proxy fix only, ~3-4 hours; addresses "unfair to codemem" but leaves jCodeMunch stubbed and no new competitors).
- Tier 2 (methodology + fair re-baseline, ~2-3 days; does not broaden fairness surface).
- Tier 4 (C + end-to-end LLM utility test, ~5-7 days; deferred to v3).

Rationale: Tier 3 covers the top 4-5 concerns that move the verdict, not just the top 1-2, while staying inside tooling/methodology scope and avoiding LLM-eval rubric design (a research project of its own).

**Phase 4.5 adversarial verification findings (11 rows):**

| # | Finding | Severity | Correction applied |
|---|---|---|---|
| 1 | Wrong line numbers in v0 plan ("pagerank.py lines 132-194 block") | HIGH | Corrected: proxy at line 32; `_budget_chars` 132-133; `_fits` 136-137; binary search 187-194 |
| 2 | v0 said Aider `--encoding cl100k_base` would equalise tokeniser | HIGH | Corrected: `--encoding` is I/O; tokeniser routed via `--model`. Use `--model gpt-3.5-turbo`. Added API-key risk |
| 3 | v0 missing Rollback section | MEDIUM | Added §4.7 (one `git revert` per milestone) |
| 4 | v0 missing Dependencies & Assumptions distinct section | MEDIUM | Added §4.8 with hard vs soft dependency classification |
| 5 | v0 missing Next-Action pointer | MEDIUM | Added §4.11 (M1 archive-if-needed + proxy replacement) |
| 6 | M2 was horizontally sliced (all 3 adapters lumped) | MEDIUM | Split into M2a (jCodeMunch + RBO + Aider model), M2b (Repomix), M2c (Yek + sweep) |
| 7 | Falsifiable-AC compliance (L-059) weak on HITL approval items | LOW | M3 AC now has grep-based voice checks + HITL gates explicitly stated as non-falsifiable human gates |
| 8 | RBO formula stated but not verified against academic source | LOW | Verified against Webber, Moffat, Zobel 2010; `rbo` PyPI package confirmed as test-only cross-reference |
| 9 | Repomix / Yek install state unverified | LOW | Probed; both NOT installed; install is M2b/M2c pre-flight prerequisite |
| 10 | jCodeMunch MCP surface assumed, not probed | LOW | Probed via `jcodemunch-mcp serve --help`; `--transport stdio` confirmed |
| 11 | Python MCP SDK name assumed | LOW | Verified on PyPI: `mcp` version 1.27.0 |

**Key architectural decisions (this plan):**

- **AD-V2-001: Tier 3 scope (5-tool panel).**
  - Rationale: proxy fix alone leaves the downstream Signal 2 verdict exposed to the "competitors never measured" complaint.
  - Alternatives: Tier 1 surgical; Tier 2 methodology-only; Tier 4 LLM-utility test.
  - Trade-offs: ~3-5 days vs ~3-4 hours; materially broader fairness claim; stays inside tooling scope.

- **AD-V2-002: Replace 4-char proxy with module-level cl100k_base tiktoken encoder cache.**
  - Rationale: removes the systematic bias against codemem at any "equal requested budget" comparison.
  - Alternatives: keep proxy + tokeniser-normalise at harness level only; add a per-tool tokeniser parameter.
  - Trade-offs: codemem internal cache cost (one encoder construction per process) vs accuracy; symbol-ID cache invalidation downstream.

- **AD-V2-003: Inline RBO (~20 LOC) rather than depend on the `rbo` PyPI package at runtime.**
  - Rationale: KISS; avoids a new runtime dep for a 20-line function; still pin `rbo` as a test-only cross-reference.
  - Alternatives: add `rbo` as a runtime dep.
  - Trade-offs: one extra test for validation vs a third-party dep in the harness.

- **AD-V2-004: Vertical slicing M2 -> M2a / M2b / M2c.**
  - Rationale: each adapter should be demoable in isolation (L-066 tracer-bullets heuristic).
  - Alternatives: lump all 3 adapters into one M2 (rejected, horizontal slice).
  - Trade-offs: 3 commits instead of 1; each produces observable value.

- **AD-V2-005: Aider tokeniser equalisation via `--model gpt-3.5-turbo` (litellm-routed cl100k_base).**
  - Rationale: Aider has no `--tokenizer` or `--encoding`-for-tokenisation flag; `--model` is the only surface that actually switches the tokeniser.
  - Alternatives: hand-patch Aider source; skip equalisation.
  - Trade-offs: `--model gpt-3.5-turbo` changes more than the tokeniser (prompts, defaults); if API key required, fall back to default model and document bias honestly.

- **AD-V2-006: Use `mcp>=1.27` Python SDK for jCodeMunch stdio round-trip.**
  - Rationale: canonical client; ~30 LOC for our use case; handshake and protocol versioning handled.
  - Alternatives: hand-rolled JSON-RPC over stdio.
  - Trade-offs: one new dev-dep vs ~100+ LOC of protocol code.

- **AD-V2-007: `status=ok_no_symbols` enum value for Repomix.**
  - Rationale: Repomix does not natively emit symbol-level data; a file-level comparison is still informative.
  - Alternatives: regex post-hoc symbol count (kept as secondary metric); exclude Repomix from symbol-overlap metrics entirely.
  - Trade-offs: Repomix participates in token-level comparisons only; symbol-level overlap reported as N/A.

**Carry-forward decisions (from v1 context-log, recorded explicitly):**

- **AD-002 carried forward, size + coverage scope.** Benchmark measures (a) raw output size, (b) tiktoken-token count, (c) symbol-row count. Coverage-of-LLM-utility is NOT measured in v2 (deferred to v3 Tier 4).
- **AD-006 carried forward, 3-run median.** Each cell is the median of 3 invocations to dampen wall-clock noise.
- **AD-012 SUPERSEDED, jCodeMunch stub.** v1 stubbed jCodeMunch because the MCP stdio surface was not probed. v2 M2a implements a live MCP stdio round-trip via the `mcp>=1.27` SDK. No further stubbing.

**Research findings (Phase 3):**

- Probe A: `_CHARS_PER_TOKEN = 4` sits at `packages/codemem-mcp/src/codemem/pagerank.py:32` as a module constant (not inside a function).
- Probe B: Aider's tokeniser is routed via litellm from `--model`; no `--tokenizer` flag exists.
- Probe C: `jcodemunch-mcp serve --transport stdio` is the canonical MCP transport.
- Probe D: `tiktoken.get_encoding("cl100k_base")` works; pinned at 0.12.0.
- Probe E: Repomix and Yek are NOT on PATH; install is a pre-flight prerequisite at M2b / M2c start.

**Open questions / unresolved issues:**

- **U-005 (Q1, M3 HITL):** keep v1 report file with "superseded" banner vs overwrite v1 content with v2. Recommended: keep both; banner on v1. Decision point: M3 task 3.2.
- **U-006 (Q2, M3 HITL):** if v2 codemem beats Aider after proxy fix, does Signal 2 flip? Recommended: yes per v1 plan §Task 4.2 case (a); Aider sub-claim "PASS on small repo". Composite remains PROVISIONAL until user-supplied medium + 50k-LOC repo measurements arrive. Decision point: M3 task 3.3.
- **U-007 (Q3, M2a implicit):** use `mcp>=1.27` Python SDK for jCodeMunch stdio vs hand-rolled JSON-RPC. Recommended: use SDK (AD-V2-006). Decision point: implicit at M2a start.
- **U-008 (Q4, M2a first-probe):** if `aider --model gpt-3.5-turbo --show-repo-map` requires an API key we do not have, skip the Aider-tokeniser-equalised arm vs invent a creative workaround. Recommended: skip and document; the benchmark's honesty is more important than the arm. Decision point: M2a task first-probe.

**Impact analysis:**

No HIGH-risk impacts if the proxy fix is gated on tests passing before commit. Medium-risk ripples: existing `test_pagerank.py` assumes 4-char proxy (red-green-refactor in M1); downstream MCP consumers that cache symbol-IDs may see cache invalidation at budget=1024. No DB migrations, no irreversible filesystem actions, no external messages. Rollback cost is one `git revert` per milestone.
