# codemem-token-benchmarks Context Log

_This log captures architectural decisions, trade-offs, and unresolved issues._

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
