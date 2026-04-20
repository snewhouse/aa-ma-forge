# codemem-benchmark-fairness-v2 Context Log

_This log captures architectural decisions, trade-offs, gate approvals, and unresolved issues for the v2 fair benchmark plan._

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
