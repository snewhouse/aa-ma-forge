# codemem-benchmark-fairness-v2 Plan

**Objective:** Re-run the codemem-vs-Aider benchmark with v1 methodology flaws corrected (proxy fix, tokeniser-equalised Aider, RBO, jCodeMunch live round-trip) and expand to a 5-tool panel (add Repomix + Yek), superseding v1 and re-baselining kill-criteria Signal 2.
**Owner:** AI + User (Stephen Newhouse)
**Created:** 2026-04-20
**Last Updated:** 2026-04-20

## Executive Summary

Re-run the v1 codemem-vs-Aider benchmark with the identified methodology flaws fixed (tiktoken budget in codemem, tokeniser-equalised Aider, rank truncation), expand to a 5-tool panel (adding jCodeMunch live + Repomix + Yek), add RBO@10 alongside Jaccard, and produce a v2 report that re-baselines kill-criteria Signal 2 against honest numbers.

## Target Audience

- Downstream consumers of the v1 benchmark verdict (kill-criteria Signal 2): need honest numbers before citation in architectural decisions.
- Future plan authors touching codemem ranking or benchmarking: need a documented fair harness with live adapters.
- Stephen: needs the composite Signal 2 verdict re-stated against the corrected data.

## Provenance

Derived from the `/grill-me` adversarial review of the v1 `codemem-token-benchmarks` report (completed 2026-04-20 at commit `7a335fc`). The review surfaced 11 methodology concerns (1 HIGH: jCodeMunch stubbed; 8 MEDIUM; 2 LOW). Tier 3 scope (proxy fix + jCodeMunch live + RBO + Repomix + Yek) was user-selected over Tier 1 (surgical proxy fix only), Tier 2 (methodology-only) and Tier 4 (LLM utility test, deferred to a v3 follow-up).

## Phase 0: Operational Readiness

- Ops mode: standard. No destructive or production-side actions.
- Quick complexity estimate: **55%** overall. Max-task complexity 60% at M2a. Below the 80% deep-review threshold.
- Parallel research opportunity: executed in plan-mode (3 parallel Explore agents + 1 sequential verification agent via `/double-check`).
- Plan-authoring-standards review (L-054 to L-066) applied inline.

## Phase 1: Context

- Task name: `codemem-benchmark-fairness-v2` (kebab-case).
- Branch: `expt/code_mem_store_what` (active; M4 of v1 shipped at `7a335fc`).
- Parent plan: `.claude/dev/active/codemem-token-benchmarks/` (COMPLETE as of 2026-04-20, pending `/archive-aa-ma`; archive scheduled inside M4 of this plan).
- Why now: before citing v1 numbers in downstream architectural decisions, the bias in codemem's own 4-char proxy must be removed and the comparison must actually include the serious competitors (Repomix, Yek) that v1 missed.

## Phase 2: Structured Thinking

### 2.1 Alternatives considered

- **A. Tier 1 (surgical):** fix only codemem proxy + rank truncation. ~3-4 hours. Leaves jCodeMunch stubbed.
- **B. Tier 2 (methodology):** A + live jCodeMunch + RBO + tokeniser-equalised Aider. ~2-3 days. Addresses 1 HIGH + 3 MEDIUM concerns.
- **C. Tier 3 (SELECTED):** B + Repomix (23.6k stars, git-change-frequency ranking) + Yek (2.4k stars, Rust, 230x faster than Repomix). 5-tool panel, materially broader fairness claim. ~3-5 days.
- **D. Tier 4:** C + end-to-end LLM utility test. ~5-7 days. Rejected for v2; deferred to a v3 follow-up.

### 2.2 Assumptions (validated in Phase 3)

| Assumption | Validation method | Status |
|---|---|---|
| codemem `_CHARS_PER_TOKEN = 4` proxy is the fixable root cause | Read `pagerank.py:32` + `pagerank.py:136-137` | VERIFIED (see Phase 3) |
| Aider exposes a tokeniser-switch surface | `aider --help`, search source | VERIFIED via `--model` (not `--tokenizer` or `--encoding`) |
| jcodemunch-mcp supports stdio MCP transport | `jcodemunch-mcp serve --help` | VERIFIED (`--transport {stdio,sse,streamable-http}`) |
| Repomix supports `--token-count-encoding=cl100k_base` | WebFetch project README | VERIFIED |
| Yek supports `--tokens N --json` | WebFetch project README | VERIFIED |
| Python MCP SDK is pip-installable as `mcp` | PyPI lookup | VERIFIED (mcp 1.27.0 latest) |
| RBO formula (Webber et al 2010) is the right coverage metric | Academic verification | VERIFIED; inline impl preferred per AD-005 |
| fastapi 0.136.0 shape (1119 py, 56MB) remains | v1 Task 3.1 empirical | PRE-VERIFIED |

### 2.3 Edge cases

- **E1:** codemem proxy fix causes binary search to include MORE symbols at budget=1024 on aa-ma-forge. Downstream MCP consumers that cache symbol-IDs may see cache invalidation.
- **E2:** jCodeMunch MCP server startup delay dominates wall-clock at budget=512. Per-cell timing is excluded from aggregation for jCodeMunch.
- **E3:** Repomix and Yek do not emit per-symbol data natively. Either post-hoc regex count or `status=ok_no_symbols`.
- **E4:** Aider `--model gpt-3.5-turbo` changes MORE than just the tokeniser (prompts, defaults). Claim is strictly true only on the tokeniser axis.
- **E5:** Medium / 50k-LOC repo measurements remain blocked on user-supplied paths. v2 limits itself to aa-ma-forge + fastapi.

### 2.4 Applied principles

- KISS: inline RBO (~20 LOC) over a new pip dep.
- DRY: reuse `parse_aider_output`, `measure_output`, `jaccard`, `aggregate`, `_median_int` from v1 harness.
- SOLID / SOC: each new tool adapter is a standalone function (`_run_jcodemunch`, `_run_repomix`, `_run_yek`) matching the v1 pattern.
- Env-var-drift: no new env vars; `JCODEMUNCH_TRANSPORT` is documented where the adapter reads it.

## Phase 3: Research & Verification (empirically probed 2026-04-20)

### 3.1 Probes executed

**Probe A: pagerank.py state:**

```
_CHARS_PER_TOKEN = 4                        # pagerank.py:32 (module constant)
def _budget_chars(budget_tokens: int):      # pagerank.py:132-133
    return max(budget_tokens, 1) * _CHARS_PER_TOKEN
def _fits(payload: dict, budget_tokens):    # pagerank.py:136-137
    return len(json.dumps(payload, ...)) <= _budget_chars(budget_tokens)
# Binary search over symbols[:mid] at lines 187-194
# Symbol emission with raw float rank at pagerank.py:171 ("rank": ranks.get(r["id"], 0.0))
```

The proxy lives at **line 32** as a module-level constant. Fix is ~5 lines total: replace constant + swap `_fits()` to use tiktoken.

**Probe B: aider CLI surface (`aider --help`):**

- `--model MODEL` exists (env var: `AIDER_MODEL`).
- `--encoding ENCODING` is documented as input/output I/O, NOT tokenisation.
- No `--tokenizer` flag.
- Tokeniser is derived from `--model` via `litellm`.
- Workaround: `aider --model gpt-3.5-turbo --show-repo-map --map-tokens N` (gpt-3.5-turbo uses cl100k_base per litellm).

**Probe C: jcodemunch-mcp transport surface (`jcodemunch-mcp serve --help`):**

```
--transport {stdio,sse,streamable-http}   Transport mode: stdio (default), sse, or streamable-http
```

**Probe D: tiktoken cl100k_base sanity:**

```
cl100k_base OK, sample tokens for 'def foo(): pass' → [755, 15586, 4658, 1522]
```

Already a pinned dev dep (`tiktoken==0.12.0`, v1 M2.1).

**Probe E: external tool install state:**

```
yek:            (not on PATH)
repomix:        (not on PATH)
jcodemunch-mcp: /home/sjnewhouse/.local/bin/jcodemunch-mcp
```

Repomix and Yek are install-time prerequisites for M2b / M2c.

### 3.2 External claim verification table

| Claim | Verdict | Source |
|---|---|---|
| Repomix `--style xml --token-count-encoding=cl100k_base <dir>` | CONFIRMED | github.com/yamadashy/repomix README |
| Yek `--tokens N --json` | CONFIRMED | github.com/bodo-run/yek README |
| Python MCP SDK is `mcp` on PyPI, 1.27.0, has `mcp.client.stdio` | CONFIRMED | pypi.org/project/mcp/ |
| RBO formula `(1-p) * Sum p^(d-1) * |S[:d] n T[:d]| / d`, p=0.9 convention | CONFIRMED | Webber, Moffat, Zobel 2010 (ACM TOIS) |
| Aider v0.86.2 `--model gpt-3.5-turbo` uses cl100k_base via litellm | CONFIRMED | aider/models.py + litellm docs |
| jcodemunch-mcp tools: `get_ranked_context(query, token_budget)` via MCP | CONFIRMED | USER_GUIDE.md in repo |
| fastapi 0.136.0 = 1119 py files, 56MB | PRE-VERIFIED | v1 Task 3.1 Result Log |

### 3.3 Impact analysis

| File | Change class | Downstream consumers |
|---|---|---|
| `packages/codemem-mcp/src/codemem/pagerank.py` | semantic change (proxy -> tiktoken) | `tests/codemem/test_pagerank.py`, MCP tools that parse `PROJECT_INTEL.json` |
| `scripts/bench_codemem_vs_aider.py` | extend (new adapters) | `tests/codemem/test_bench_harness.py`, `scripts/bench_sweep.py` |
| `scripts/bench_sweep.py` | extend (5-tool loop) | harness tests |
| `pyproject.toml` | add `mcp>=1.27` dev dep | `uv sync` |
| `docs/benchmarks/codemem-vs-aider.md` | modify (add v2 banner + link) | external referrers (none in current repo) |
| `docs/benchmarks/codemem-vs-aider-v2.md` | new | `docs/codemem/kill-criteria.md` link |
| `docs/codemem/kill-criteria.md` | modify (Signal 2 second re-baseline) | README, ARCHITECTURE, install-zero-config, codemem-co-changes-transcript |

No HIGH-risk impacts if the proxy fix is gated on tests passing before commit.

## Phase 4: Plan (11 AA-MA elements)

### 4.1 Executive summary

See top of file.

### 4.2 Ordered stepwise implementation plan

Vertical slices. Each milestone produces a demoable / verifiable state.

### 4.3 Milestones with measurable goals

| M | Title | Mode | Gate | Effort | Complexity | Measurable goal |
|---|---|---|---|---|---|---|
| M1 | Codemem proxy + rank truncation | AFK | SOFT | 0.5 day | 30% | `codemem intel --budget=1024` on aa-ma-forge emits >= 17 symbols (v1 baseline) with `rank` rounded to 3 sig figs and budget enforced by cl100k_base; full test suite green |
| M2a | Fair 3-way re-run (jCodeMunch live + RBO + Aider tokeniser-equalised) | AFK | SOFT | 1-1.5 days | 60% | v1 harness replaced: 3 tools x 4 budgets x 3 runs produces JSON with no stubs, both Jaccard and RBO@10 populated, Aider run with `--model gpt-3.5-turbo` |
| M2b | Repomix adapter | AFK | SOFT | 0.5 day | 45% | `scripts/bench_codemem_vs_aider.py --requested-budget 1024` emits a `tools.repomix` cell with `status=ok` and non-zero `tiktoken_tokens` on aa-ma-forge |
| M2c | Yek adapter + full 5-tool sweep | AFK | SOFT | 0.5 day | 45% | `tools.yek` populated; full 5-tool x 4-budget x 2-repo x 3-run sweep produces two JSON files with 40 cells each |
| M3 | v2 report + Signal 2 second re-baseline | HITL | SOFT | 0.5-1 day | 40% | `docs/benchmarks/codemem-vs-aider-v2.md` committed, voice-pass green, Signal 2 status line updated with v2 numbers, composite verdict re-examined |
| M4 | Finalization + archive v1 | AFK | SOFT | 1 hour | 10% | M4 commit pushed; `/archive-aa-ma codemem-token-benchmarks` run; v2 AA-MA dir exists and is synced |

**Total:** ~3.5-5 focused-dev days. **Max-task complexity:** 60% at M2a (below the 80% deep-review threshold).

### 4.4 Acceptance criteria per milestone (falsifiable)

**M1:**
- `grep -n "_CHARS_PER_TOKEN" packages/codemem-mcp/src/codemem/pagerank.py` returns **zero** occurrences after the fix (constant removed, not just reassigned).
- `grep -n "tiktoken" packages/codemem-mcp/src/codemem/pagerank.py` returns **>= 1** (module-level import + encoder cache).
- `uv run python -c "import json; d=json.load(open('/tmp/post-m1-intel.json')); [print(s['rank']) for s in d['symbols'][:5]]"` emits values matching `/^[01]\.\d{1,3}(e-?\d+)?$/` (3 sig figs).
- `uv run pytest tests/codemem/` returns green (may require updating N pagerank tests; that is part of M1).
- `uv run codemem intel --budget=1024 --out=/tmp/post-m1-intel.json` on aa-ma-forge emits `_meta.written_symbols >= 17` (v1 baseline).

**M2a:**
- `scripts/bench_codemem_vs_aider.py --repo . --requested-budget 1024 --out /tmp/v2a.json` produces JSON with `tools.jcodemunch.status == "ok"` (no stub), `tiktoken_tokens > 0`, `symbol_count > 0`.
- `tools.aider` populated from an Aider invocation with `--model gpt-3.5-turbo` (parse via existing `parse_aider_output`).
- `overlap.budget_1024.codemem_vs_aider.rbo_at_10` present and in `[0.0, 1.0]`; same for all three tool-pairs.
- `tests/codemem/test_bench_harness.py` has new assertions: `TestJCodeMunchAdapter` (>=3 tests), `TestRBOMetric` (>=3 tests), `TestAiderModelOverride` (>=1 test). All green.
- `uv run pytest -m slow tests/codemem/` still passes.

**M2b:**
- `scripts/bench_codemem_vs_aider.py --repo . --requested-budget 1024 --out /tmp/v2b.json` produces JSON with `tools.repomix.status == "ok"`, `tiktoken_tokens > 0`. Symbol-count may be 0 (OK: status `ok_no_symbols` and documented).
- Repomix invocation pinned: `repomix --style xml --output /tmp/repomix-out.xml --token-count-encoding cl100k_base .` (or equivalent after version confirmation).
- `TestRepomixAdapter` tests (>=3) green.

**M2c:**
- `scripts/bench_codemem_vs_aider.py --repo . --requested-budget 1024 --out /tmp/v2c.json` produces JSON with `tools.yek.status == "ok"`, `tiktoken_tokens > 0`.
- `scripts/bench_sweep.py --repo . --out /tmp/bench-aa-ma-forge-v2.json` and same for fastapi: each produces 5x4 = 20 cells + overlap triples for all 10 pairs.
- `TestYekAdapter` tests (>=3) green.
- Full sweep wall-clock documented (expected 20-60 minutes per repo).

**M3:**
- `docs/benchmarks/codemem-vs-aider-v2.md` exists; `grep -c '—' docs/benchmarks/codemem-vs-aider-v2.md` returns `0`; `grep -iEn "\b(crucial|delve|leverage|landscape)\b"` returns no matches.
- v1 file `docs/benchmarks/codemem-vs-aider.md` has a "superseded by v2" banner at top (single edit, preserves v1 content).
- `docs/codemem/kill-criteria.md` Signal 2 status line dated 2026-04-XX (second re-baseline); "Latest update" header bumped.
- HITL approval gate passed on both the report and the Signal 2 rewrite.
- If v2 codemem beats Aider after the proxy fix, conjunct (b) flips FAILS -> PASSES on small repo; Signal 2 composite verdict line updated accordingly per v1 plan §Task 4.2 case (a) wording.
- `docs/benchmarks/results-codemem-vs-aider-v2-2026-04-XX.json` committed (combined 5-tool raw data).

**M4:**
- Single commit per milestone with AA-MA signature footer: `[AA-MA Plan] codemem-benchmark-fairness-v2 .claude/dev/active/codemem-benchmark-fairness-v2`.
- `git push origin expt/code_mem_store_what` succeeds; `git rev-parse HEAD == git rev-parse origin/expt/code_mem_store_what`.
- `/archive-aa-ma codemem-token-benchmarks` run, v1 plan moves to `.claude/dev/completed/codemem-token-benchmarks/`.
- Pre-commit sanity green: `uv run pytest` (>=387 passed), `uv run ruff check`, `uv run lint-imports` (2/2 contracts).

### 4.5 Required artefacts per milestone

| M | NEW | MODIFIED |
|---|---|---|
| M1 | (none) | `packages/codemem-mcp/src/codemem/pagerank.py`; `tests/codemem/test_pagerank.py` (likely); `pyproject.toml` if pagerank imports tiktoken at runtime (may need to move from dev-only) |
| M2a | `tests/codemem/fixtures/jcodemunch_mcp_response.json` (optional fixture); inline RBO in `scripts/bench_codemem_vs_aider.py` | `scripts/bench_codemem_vs_aider.py`; `tests/codemem/test_bench_harness.py`; `pyproject.toml` (`mcp>=1.27` dev dep) |
| M2b | `tests/codemem/fixtures/repomix_output_aa-ma-forge.xml` (golden) | `scripts/bench_codemem_vs_aider.py`; `tests/codemem/test_bench_harness.py` |
| M2c | `tests/codemem/fixtures/yek_output_aa-ma-forge.json` (golden) | `scripts/bench_codemem_vs_aider.py`; `scripts/bench_sweep.py`; `tests/codemem/test_bench_harness.py` |
| M3 | `docs/benchmarks/codemem-vs-aider-v2.md`; `docs/benchmarks/results-codemem-vs-aider-v2-2026-04-XX.json` | `docs/benchmarks/codemem-vs-aider.md` (superseded banner); `docs/codemem/kill-criteria.md` (Signal 2 second re-baseline) |
| M4 | (none) | AA-MA state files (tasks.md, context-log.md, provenance.log) |

### 4.6 Tests per milestone

| M | Tests |
|---|---|
| M1 | Extend existing `test_pagerank.py` with assertions tying budget to tiktoken; add a test that `rank` is emitted rounded. All existing tests in `tests/codemem/test_pagerank.py` remain green (update call sites if signature changes). |
| M2a | New: `TestJCodeMunchAdapter` (subprocess stdio round-trip with mock MCP server fixture); `TestRBOMetric` (unit tests against hand-computed values for p=0.9, k=10); `TestAiderModelOverride` (assert harness passes `--model gpt-3.5-turbo` when flag set). |
| M2b | New: `TestRepomixAdapter` (parse golden XML fixture, assert symbol extraction and token count). |
| M2c | New: `TestYekAdapter`. Integration test marked `@pytest.mark.slow` runs the full 5-tool sweep against aa-ma-forge. |
| M3 | Voice-pass automated via grep (no em dashes, no AI vocab, no US-English slips). Link-validity check via `grep -c '\[.*\](' docs/benchmarks/codemem-vs-aider-v2.md` + manual verification. |
| M4 | Pre-commit sanity: pytest, ruff, import-linter. |

### 4.7 Rollback strategies

| M | Rollback |
|---|---|
| M1 | `git revert` the M1 commit; codemem proxy returns to 4-char. Zero production data loss. |
| M2a/b/c | `git revert` the respective commit(s); harness returns to v1 (or previous vN state). `/tmp/` JSONs are regenerable. |
| M3 | `git revert` the M3 commit; v1 report and v1 Signal 2 status restored. External docs reference `kill-criteria.md` generically, so no external links break. |
| M4 | `/archive-aa-ma` is reversible via `git mv` or `git revert` of the move commit. |

Across all milestones: no DB migrations, no irreversible filesystem actions, no external messages. Rollback cost is one `git revert` per milestone.

### 4.8 Dependencies & assumptions

**Hard dependencies:**

| Dependency | Class | Notes |
|---|---|---|
| `aider-chat==0.86.2` | Required (dev-tool) | Already pinned in v1 reference |
| `jcodemunch-mcp==1.59.1` | Required (dev-tool) | Already pinned in v1 reference |
| `tiktoken>=0.7` | Required (resolved 0.12.0) | Already dev-dep; may need runtime hoist in M1 |
| `mcp>=1.27` | Required (dev-dep) | NEW in M2a |
| `repomix` via npm (`npm install -g repomix` or `npx -y repomix`) | Required (external tool) | NEW install prerequisite for M2b; verify `which npm` before M2b |
| `yek` via cargo (`cargo install yek`) or pre-built | Required (external tool) | NEW install prerequisite for M2c; verify rust toolchain before M2c |

**Soft dependencies:**
- User approval of the 2 HITL gates within M3 (M3.2 voice review, M3.3 Signal 2 rewrite).
- No conflicting AA-MA plans active during execution (v1 codemem-token-benchmarks archives as part of M4; may need to archive FIRST if AA-MA hooks block cross-plan commits).

**Unverified-at-planning-time, deferred to execution:**
- Exact npm / cargo install time cost for Repomix / Yek.
- Whether `aider --model gpt-3.5-turbo --show-repo-map` has Aider-specific quirks (e.g. requires API key). CONTINGENCY: fall back to default model and document tokeniser mismatch explicitly; do NOT hardcode an API key.

### 4.9 Effort estimates & complexity

- Overall effort: ~3.5-5 focused-dev days.
- Overall complexity: 55%.
- Max-task complexity: M2a at 60%.
- Deep architectural review gate: NOT required (max is under 80%).

### 4.10 Risks & mitigations (top 3 per milestone)

**M1:**
1. Proxy fix changes v1 determinism -> symbol list at budget=1024 may shift from 17 to N>17. Mitigation: log delta pre/post; treat as a known methodology correction, not a regression.
2. Existing pagerank tests assume 4-char proxy. Mitigation: TDD cycle; red-green-refactor tests alongside the fix.
3. tiktoken import cost at encoder-construction. Mitigation: module-level `_TIKTOKEN_ENCODER = tiktoken.get_encoding("cl100k_base")` cache.

**M2a:**
1. jCodeMunch MCP stdio handshake harder than 0.5d estimate. Mitigation: cap at 1.5d; if exceeded keep stub for v2 and document deferral.
2. Aider `--model gpt-3.5-turbo` requires an API key -> subprocess fails. Mitigation: skip Aider-re-tokeniser arm; fall back to default model and document bias.
3. RBO inline implementation bug vs `rbo` PyPI package -> subtly wrong numbers. Mitigation: unit tests against hand-computed values for 3 known list pairs; cross-verify against `rbo` package in one test.

**M2b:**
1. Repomix CLI shape changes between versions. Mitigation: pin Repomix at exact version; capture golden fixture.
2. Repomix does not emit symbol-granular data -> symbol_count=0. Mitigation: `status=ok_no_symbols` with reason; report Repomix at file-level only; include regex-based post-hoc symbol count as secondary metric.
3. npm / node not available. Mitigation: M2b starts with `which npm` pre-flight; if absent, plan halts and M2c inherits the blocker.

**M2c:**
1. Yek CLI surface differs from guessed `--tokens N --json`. Mitigation: confirm via `yek --help` at M2c start; adapter built against confirmed flags.
2. Yek output format requires custom parsing. Mitigation: `measure_output` on the raw packed bytes regardless of internal format.
3. Rust toolchain not available. Mitigation: same pre-flight as M2b.1 for npm.

**M3:**
1. v2 numbers contradict v1 conclusions -> kill-criteria Signal 2 flips verdict. This is the point of the exercise. Mitigation: honest framing in v2 intro; keep v1 accessible.
2. stephen-newhouse-voice review fails. Mitigation: HITL gate with explicit preview (same pattern as v1 M4).
3. Signal 2 re-baseline language ambiguous (conjunct a PROVISIONAL, conjunct b flipped). Mitigation: reuse v1 plan §Task 4.2 case-a/case-b/case-c wording verbatim.

**Plan-wide top 5:**
1. M2a jCodeMunch scope creep.
2. External tool install prerequisites (node, rust) discovered only at M2b/c execution.
3. Proxy fix ripple into test suite breaks CI (TDD discipline mitigates).
4. Aider API key requirement for model override.
5. v2 findings force Signal 2 re-baseline the other way (codemem wins after proxy fix).

### 4.11 Next action + AA-MA file to update first

**Next action (on approval):** M1.0 archive v1 first (if AA-MA cross-plan hook blocks commits), then M1.1 replace `_CHARS_PER_TOKEN` proxy with cl100k_base tiktoken encoder in `packages/codemem-mcp/src/codemem/pagerank.py`.

**First AA-MA file to update after M1 commit:** `codemem-benchmark-fairness-v2-reference.md`: pin resolved tool versions (mcp SDK, Repomix, Yek) as immutable facts. Then `-tasks.md` Result Log for M1, then `-provenance.log` with M1 commit hash.

## Phase 4.5: Adversarial verification summary

11 findings surfaced and corrected during `/double-check`:

| # | Finding | Severity | Correction |
|---|---|---|---|
| 1 | Wrong line numbers in v0 plan ("pagerank.py lines 132-194 block") | HIGH | Corrected: proxy at line 32; `_budget_chars` 132-133; `_fits` 136-137; binary search 187-194 |
| 2 | v0 said Aider `--encoding cl100k_base` would equalise tokeniser | HIGH | Corrected: `--encoding` is I/O; tokeniser via `--model`. Use `--model gpt-3.5-turbo`. Added API-key risk |
| 3 | v0 missing Rollback section | MEDIUM | Added §4.7 |
| 4 | v0 missing Dependencies & Assumptions distinct section | MEDIUM | Added §4.8 |
| 5 | v0 missing Next-Action pointer | MEDIUM | Added §4.11 |
| 6 | M2 was horizontally sliced (all 3 adapters lumped) | MEDIUM | Split into M2a / M2b / M2c |
| 7 | Falsifiable-AC compliance (L-059) weak on HITL items | LOW | M3 AC now has grep-based voice checks + HITL gates stated explicitly as non-falsifiable human gates |
| 8 | RBO formula stated but not verified against academic source | LOW | Verified against Webber et al. 2010 |
| 9 | Repomix / Yek install state unverified | LOW | Probed; both NOT installed; install is M2b/M2c prerequisite |
| 10 | jCodeMunch MCP surface assumed, not probed | LOW | Probed via `serve --help` |
| 11 | Python MCP SDK name assumed | LOW | Verified on PyPI: `mcp` 1.27.0 |

### Remaining unverified-until-execution items

- Exact Repomix and Yek CLI output shapes (docs-verified only; adapters built against confirmed real output at M2b / M2c start).
- Whether `aider --model gpt-3.5-turbo --show-repo-map` is invokable without an API key; verify at M2a start.
- Full-sweep wall-clock on both repos (expected 20-60 min per repo). Non-blocking risk.

## Verification (end-to-end, post-M4)

```bash
# From aa-ma-forge checkout root.

# 1. Test suite
uv run pytest -q                                      # expect >=387 passed, >=0 new RBO/Adapter tests
uv run pytest -m slow tests/codemem/                  # expect >=2 passed
uv run ruff check src/ scripts/ tests/
uv run lint-imports                                   # 2/2 kept

# 2. Single-budget 5-tool smoke
uv run python scripts/bench_codemem_vs_aider.py \
    --repo . --requested-budget 1024 \
    --out /tmp/v2-smoke.json
uv run python -c '
import json
d = json.load(open("/tmp/v2-smoke.json"))
expected = {"codemem","aider","jcodemunch","repomix","yek"}
assert set(d["tools"].keys()) == expected
for t in expected:
    c = d["tools"][t]
    assert c["status"] in {"ok", "ok_no_symbols", "skipped", "error"}
    if c["status"] == "ok":
        assert c["tiktoken_tokens"] > 0 and c["symbol_count"] > 0
for pair in ("codemem_vs_aider","codemem_vs_jcodemunch","aider_vs_jcodemunch"):
    rbo = d["overlap"][pair]["rbo_at_10"]
    assert 0.0 <= rbo <= 1.0
print("Smoke OK")
'

# 3. Full v2 sweep (both repos)
uv run python scripts/bench_sweep.py --repo . --out /tmp/bench-aa-ma-forge-v2.json
uv run python scripts/bench_sweep.py --repo /tmp/bench-fastapi --out /tmp/bench-fastapi-v2.json

# 4. Voice + kill-criteria gates
test "$(grep -c '—' docs/benchmarks/codemem-vs-aider-v2.md)" -eq 0
grep -q "2026-04-" docs/codemem/kill-criteria.md

# 5. AA-MA state integrity
ls .claude/dev/active/codemem-benchmark-fairness-v2/*.md    # 4 .md + 1 .log expected
```

## Critical files (paths to be touched or read)

| Path | Role |
|---|---|
| `packages/codemem-mcp/src/codemem/pagerank.py` | M1 primary edit site (line 32 constant, 132-137, 187-194) |
| `packages/codemem-mcp/src/codemem/storage/db.py` | M1 read-only verification |
| `scripts/bench_codemem_vs_aider.py` | M2a/b/c primary edit site (v1 harness, extend with 3 new adapters + RBO) |
| `scripts/bench_sweep.py` | M2c edit site (5-tool loop) |
| `tests/codemem/test_bench_harness.py` | M2a/b/c test additions (>=9 new test cases) |
| `tests/codemem/test_pagerank.py` | M1 test updates |
| `tests/codemem/conftest.py` | unchanged |
| `tests/codemem/fixtures/` | new golden fixtures per adapter |
| `pyproject.toml` | M2a: add `mcp>=1.27` dev dep |
| `docs/benchmarks/codemem-vs-aider.md` | M3: add superseded banner |
| `docs/benchmarks/codemem-vs-aider-v2.md` | M3: new report |
| `docs/benchmarks/results-codemem-vs-aider-v2-2026-04-XX.json` | M3: new combined raw data |
| `docs/codemem/kill-criteria.md` | M3: Signal 2 second re-baseline |
| `.claude/dev/active/codemem-token-benchmarks/` | M4: `/archive-aa-ma` target |
| `.claude/dev/active/codemem-benchmark-fairness-v2/` | created by scribe after approval |

## Reuse existing (DRY)

| Utility | File:line | Reuse in |
|---|---|---|
| `parse_aider_output` | `scripts/bench_codemem_vs_aider.py` (v1) | M2a (unchanged) |
| `measure_output` | `scripts/bench_codemem_vs_aider.py` (v1) | M2a/b/c (shared normaliser) |
| `jaccard` | `scripts/bench_codemem_vs_aider.py` (v1) | M2a (kept alongside new RBO) |
| `aggregate` + `_median_int` | `scripts/bench_sweep.py` (v1) | M2c (5-tool loop) |
| `tests/codemem/conftest.py` | (v1) | all M2 tests |
| `tests/codemem/fixtures/aider_repo_map_aa-ma-forge.txt` | (v1 golden) | M2a Aider-default-model parity check |
| `tests/codemem/fixtures/codemem_intel_aa-ma-forge.json` | (v1 golden) | M1 post-fix delta assertion |
| AD-002 (size+coverage scope) | v1 context-log | CARRIED FORWARD |
| AD-006 (3-run median) | v1 context-log | CARRIED FORWARD |
| AD-012 (jCodeMunch stub) | v1 context-log | SUPERSEDED by M2a live implementation |

## Open questions (HITL-gate-sized)

- **Q1 (M3):** keep v1 report file and add "superseded" banner vs overwrite v1 content with v2. Recommended: keep both; v1 banner. Decision point: Task 3.2 HITL gate.
- **Q2 (M3):** if v2 codemem beats Aider after proxy fix, does Signal 2 flip? Recommended: yes per v1 plan §Task 4.2 case (a); Aider sub-claim "PASS on small repo". Composite remains PROVISIONAL until user-supplied medium + 50k-LOC repos arrive. Decision point: Task 3.3 HITL gate.
- **Q3 (M2a):** use `mcp>=1.27` Python SDK for jCodeMunch stdio vs hand-rolled JSON-RPC over stdio. Recommended: use the SDK (~30 LOC). Decision point: implicit at M2a start.
- **Q4 (M2a):** if `aider --model gpt-3.5-turbo --show-repo-map` requires an API key we do not have, skip the Aider-tokeniser-equalised arm vs invent a workaround. Recommended: skip and document. Decision point: M2a.3 first-probe.

## Worktree / cross-session coordination (L-066)

- Recommendation: if another session runs concurrently on `expt/code_mem_store_what`, create `.worktrees/codemem-benchmark-fairness-v2` via `git worktree add`. Otherwise (solo dev), continue on the current branch.
- Concurrent plans: v1 is COMPLETE (synced, awaiting archive). No active sibling sessions expected.

## Next Action

**Do this first:** execute M1.0 (archive v1 AA-MA plan if required to unblock cross-plan commits), then M1.1 (replace `_CHARS_PER_TOKEN` proxy with module-level cl100k_base tiktoken encoder in `packages/codemem-mcp/src/codemem/pagerank.py`).
**Update:** REFERENCE (pin mcp SDK version once installed) and TASKS (Result Log for M1.1).

## AA-MA File Mapping

- `tasks.md`: Milestones M1, M2a, M2b, M2c, M3, M4 at `## Milestone` level; each sub-task at `### Step` level with Status PENDING, Mode, Dependencies, Acceptance Criteria, Result Log.
- `reference.md`: Immutable facts carried forward from v1 plus v2 additions (Repomix/Yek CLI flags, RBO convention, MCP SDK). Tokeniser-mismatch invariant remains TOP PRIORITY.
- `context-log.md`: Initial entry 2026-04-20 with Phase 4.5 findings table, carry-forward decisions, and open questions Q1-Q4 as U-005 to U-008.
- `provenance.log`: Seeded with plan-creation + scribe-materialisation events.
