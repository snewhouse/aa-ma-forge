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
- **M4.2 gate:** Confirmation of **Signal 2** (M1 architectural kill) status-line wording — composite stays DID-NOT-TRIGGER; Aider sub-claim state (confirmed / provisional / fails) per M3 findings.
