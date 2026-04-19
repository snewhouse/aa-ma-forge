# codemem-token-benchmarks Plan

**Objective:** Execute the DEFERRED codemem Task 4.2 token-budget benchmark comparing `PROJECT_INTEL.json` (codemem), Aider's repo-map, and jCodeMunch at equal budget on 2 reference repos, with tiktoken normalization.
**Owner:** Stephen Newhouse + AI
**Created:** 2026-04-18
**Last Updated:** 2026-04-18
**Branch:** `expt/code_mem_store_what`
**Parent plan:** `.claude/dev/completed/codemem/` (archived 2026-04-18, commit `3ab0aa9`)

---

## Executive Summary

Execute the token-budget benchmark that was DEFERRED from the archived codemem plan as Task 4.2: compare `PROJECT_INTEL.json` (codemem), Aider's repo-map, and jCodeMunch at equal budget on 2 reference repos. The 3 original preconditions have been resolved empirically via parallel research (findings pinned in reference.md); execution requires external tiktoken normalization to avoid apples-to-oranges. The outcome feeds the archived codemem plan's §12 M1-exit kill signal.

---

## Context

On 2026-04-17, Task 4.2 was DEFERRED because 3 preconditions were unverified: Aider's output format, `--budget=N` support across tools, and top-symbol ranking comparability. On 2026-04-18 three parallel research agents resolved all three — findings are in reference.md §Phase-3 Research Findings. The plan can now execute cleanly with tokenizer normalization as the key added constraint.

Cross-reference: the M1-exit kill signal this benchmark feeds is defined in `.claude/dev/completed/codemem/codemem-plan.md` §12 (Signal 1).

---

## 2. Stepwise Implementation Plan

### Milestone 1 — Environment Setup + Precondition Re-Verification
**Mode:** HITL, **Gate:** SOFT, **Complexity:** 25%, **Effort:** ~1 focused-dev day
**Dependencies:** none

- **Task 1.1** — Install Aider + jCodeMunch in throwaway `uv tool` env. Pin versions. Mode: AFK.
- **Task 1.2** — Re-run each tool's smoke test against aa-ma-forge root; confirm Phase-3 findings still hold (Aider v0.86.2 behavior, jCodeMunch MCP invocation, PROJECT_INTEL schema). Mode: AFK.
- **Task 1.3** — HITL decision gate: confirm scope = size+coverage (default, research-supported) OR revise to size-only / qualitative / cancel. Mode: HITL.

### Milestone 2 — Harness + Parser (TDD)
**Mode:** AFK, **Gate:** SOFT, **Complexity:** 55%, **Effort:** ~1.5-2 focused-dev days
**Dependencies:** M1 complete

- **Task 2.1** — Add `tiktoken` as dev dep in root `pyproject.toml`. Mode: AFK.
- **Task 2.2** — TDD: `tests/codemem/test_bench_harness.py` — unit tests for Aider prose-output parser. Use a golden fixture copied from a live Aider invocation against aa-ma-forge. Assert parser extracts `(file, symbol_name, kind)` rows. Mode: AFK.
- **Task 2.3** — GREEN: implement parser module (`scripts/bench_aider_parser.py` OR inline in `bench_codemem_vs_aider.py` — KISS says inline unless parser grows beyond 100 LOC). Mode: AFK.
- **Task 2.4** — TDD: tiktoken normalization test — given captured outputs from all 3 tools at requested budget 1024, assert `len(tiktoken.encode(output_text))` for each. Mode: AFK.
- **Task 2.5** — Implement `scripts/bench_codemem_vs_aider.py`: invokes all 3 tools at a configurable `--requested-budget`, captures outputs, normalizes via tiktoken, emits comparison JSON with (a) raw output size bytes, (b) tiktoken-counted tokens, (c) symbol-row count, (d) top-N overlap via Jaccard against codemem's symbols. Mode: AFK.
- **Task 2.6** — Integration test: harness self-exercises against aa-ma-forge. Asserts structured JSON output with all 3 tools present. Mode: AFK.

### Milestone 3 — Execute
**Mode:** AFK, **Gate:** SOFT, **Complexity:** 30%, **Effort:** ~1 focused-dev day
**Dependencies:** M2 complete

- **Task 3.1** — Clone `fastapi` (tiangolo/fastapi) into `/tmp/bench-fastapi` at a pinned commit. Mode: AFK.
- **Task 3.2** — Run harness against aa-ma-forge at budgets `{512, 1024, 2048, 4096}`; capture to `/tmp/bench-aa-ma-forge.json`. Mode: AFK.
- **Task 3.3** — Run harness against fastapi at the same budget sweep; capture to `/tmp/bench-fastapi.json`. Mode: AFK.
- **Task 3.4** — Sanity check: for each tool at each budget, output is non-empty and symbol count > 0. Mode: AFK.

### Milestone 4 — Report + Integrate
**Mode:** HITL, **Gate:** SOFT, **Complexity:** 40%, **Effort:** ~1 focused-dev day
**Dependencies:** M3 complete

- **Task 4.1** — Draft `docs/benchmarks/codemem-vs-aider.md`. Structure: Methodology (with tokenizer-mismatch caveats PROMINENT) → Results Tables (2 repos × 4 budgets × 3 tools) → Per-signal verdict (size, top-symbol overlap, qualitative) → Implications for kill-criteria §1. Mode: HITL — user reviews wording.
- **Task 4.2** — Update `docs/codemem/kill-criteria.md` Signal 1 status line: replace the 2026-04-17 "DID NOT trigger ... Aider comparison DEFERRED" with actual findings. Two cases: (a) codemem ≤ 1.5× → "DID NOT trigger, confirmed"; (b) codemem > 1.5× → "FIRED — architectural kill triggered". Mode: HITL.
- **Task 4.3** — Commit with `[AA-MA Plan] codemem-token-benchmarks .claude/dev/active/codemem-token-benchmarks` signature. Mode: AFK.

---

## 3. Milestones With Measurable Goals

| Milestone | Measurable Goal |
|-----------|-----------------|
| M1 | All 3 tools installed at pinned versions; each emits non-empty output at `--budget=1024` on aa-ma-forge; HITL scope decision recorded |
| M2 | `pytest tests/codemem/test_bench_harness.py` green; harness emits valid JSON with all 3 tools; ruff clean; import-linter still 2/2 |
| M3 | Two JSON result files (aa-ma-forge + fastapi), each with 4 budgets × 3 tools = 12 measurements |
| M4 | `docs/benchmarks/codemem-vs-aider.md` committed; kill-criteria Signal 1 updated to reflect actual measurement; CI green |

---

## 4. Acceptance Criteria Per Step

### M1 Acceptance Criteria
- `aider --version` and `jcodemunch-mcp --version` (or equivalent) return pinned values
- `uv run codemem intel --budget=1024 --out=/tmp/bench-intel-1024.json` produces file with `_meta.written_symbols >= 1` and PageRank-ranked `symbols[]`
- HITL decision recorded in context-log.md under heading `## 2026-MM-DD — M1.3 scope decision`

### M2 Acceptance Criteria
- `uv run pytest tests/codemem/test_bench_harness.py` → all green
- `uv run python scripts/bench_codemem_vs_aider.py --repo . --requested-budget 1024 --out /tmp/bench.json` → produces valid JSON with keys `{requested_budget, tools: {codemem: {...}, aider: {...}, jcodemunch: {...}}, overlap: {...}}`
- Ruff clean on new files
- Import-linter still 2/2 (no changes to package boundaries)

### M3 Acceptance Criteria
- Two JSON result files on disk, each containing all 4 budget levels × 3 tools = 12 measurements
- No tool-invocation failures (or failures are explicitly recorded in the JSON)
- At least one clear data point — e.g. codemem's symbol count vs Aider's at budget=1024 — is quotable for the report

### M4 Acceptance Criteria
- `docs/benchmarks/codemem-vs-aider.md` committed, passes stephen-newhouse-voice (no marketing, direct, honest about limits)
- `docs/codemem/kill-criteria.md` Signal 1 status updated to reflect actual measurement
- If Signal 1 fires: `context-log.md` records the architectural-kill event with a linked pointer to the root cause (tokenization inefficiency / algorithm choice / etc)
- Commit pushed; CI green

---

## 5. Required Artefacts

### M1 Artefacts
- context-log.md entry with HITL decision
- provenance.log entry per sub-step

### M2 Artefacts
- `scripts/bench_codemem_vs_aider.py` NEW
- `tests/codemem/test_bench_harness.py` NEW
- `tests/codemem/fixtures/aider_repo_map_aa-ma-forge.txt` NEW (golden fixture from M1)
- `pyproject.toml` MODIFIED (tiktoken dev dep)

### M3 Artefacts
- `docs/benchmarks/results-codemem-vs-aider-2026-04-18.json` NEW (committed raw data)
- provenance entries capturing pinned SHAs + tool versions

### M4 Artefacts
- `docs/benchmarks/codemem-vs-aider.md` NEW
- `docs/codemem/kill-criteria.md` MODIFIED
- `docs/benchmarks/results-codemem-vs-aider-2026-04-18.json` (already from M3, confirmed committed)

---

## 6. Tests Per Milestone

| Milestone | Tests |
|-----------|-------|
| M1 | pytest smoke — assert three tools return non-empty outputs at `--budget=1024` |
| M2 | Unit (parser + normalization), integration (harness self-exercise) |
| M3 | None new; the harness itself is the test from M2 |
| M4 | None new; CI green gate applies |

---

## 7. Rollback Strategies

| Milestone | Rollback |
|-----------|----------|
| M1 | `uv tool uninstall aider-chat jcodemunch-mcp`; no production code touched |
| M2 | `git revert` the M2 commit; no production code touched |
| M3 | Delete result files; re-run |
| M4 | `git revert` the M4 commit (reversible until merged to main) |

---

## 8. Dependencies & Assumptions

- Assumes aa-ma-forge repo at HEAD `3ab0aa9` or later (post-codemem-archive).
- Assumes `uv` package manager available on PATH (project standard).
- Assumes tiktoken can be installed from PyPI (verified 2026-04-18).
- Assumes Aider v0.86.2 upstream package remains available (known-good from Phase 3 research — if delisted, pin to latest 0.86.x and re-verify).
- Assumes jCodeMunch public-repo fixture workflow is documented (per Phase 3 research confirmed at `/tmp/jcm_userguide.md`).

---

## 9. Effort Estimate & Complexity

**Overall effort:** ~4.5 focused-dev days
**Overall complexity:** 50%
**Max-task complexity:** M2 at 55%
**Deep-review gate required:** No (all milestones under 80%)

| Milestone | Effort | Complexity |
|-----------|--------|------------|
| M1 | ~1 day | 25% |
| M2 | ~1.5-2 days | 55% |
| M3 | ~1 day | 30% |
| M4 | ~1 day | 40% |

---

## 10. Risks & Mitigations

### M1 Top 3 Risks
1. **(R1)** jCodeMunch install fails on non-python-dev-env — mitigation: capture stderr and file as blocker; escalate HITL.
2. **(R2)** Aider pinning breaks if upstream ships a major version — mitigation: pin to `aider-chat==0.86.2` (known-good per Phase 3 research).
3. **(R3)** Phase-3 findings no longer hold due to tool updates — mitigation: re-verify empirically; if diverged, extend M1 to re-research before proceeding.

### M2 Top 3 Risks
1. **(R1)** Aider output format shifts between versions → parser breaks. Mitigation: pin Aider; test with golden fixture.
2. **(R2)** tiktoken encoding mismatch with Aider/jCodeMunch's internal counting → reported counts diverge. Mitigation: report BOTH raw bytes AND tiktoken-normalized counts; document the proxy for codemem's 4-chars/token.
3. **(R3)** jCodeMunch public-repo fixture requirement blocks self-exercise. Mitigation: seed the harness with a synthetic fixture OR run jCodeMunch only on the M3 OSS-repo run.

### M3 Top 3 Risks
1. **(R1)** fastapi repo is too large for jCodeMunch's indexer within the time budget. Mitigation: fall back to a smaller OSS Python repo (`click` candidate); record deviation.
2. **(R2)** Results reveal codemem is 1.5× or worse — fires §12 M1-exit kill signal. Mitigation: that IS the point of the benchmark; honest recording goes into M4 report.
3. **(R3)** Non-deterministic outputs across runs (e.g. PageRank tie-breaks). Mitigation: run each measurement 3× and report median, matching Task 4.1 `scripts/bench_codemem.py` pattern.

### M4 Top 3 Risks
1. **(R1)** Findings are ambiguous (codemem wins size but loses top-symbol overlap, or vice versa). Mitigation: report both signals separately; leave Signal 1 kill state in "provisional — see benchmark §X for discussion" rather than forcing a binary.
2. **(R2)** Stephen-newhouse-voice review fails on first draft. Mitigation: HITL review + revision cycle, matching Task 4.4 pattern from the archived plan.
3. **(R3)** M3 data has a subtle bug that the report surfaces late. Mitigation: M4 starts with 15-min sanity pass over M3 JSON before drafting; if a bug is found, cycle back to M2/M3.

### Plan-Wide Top 5 Risks
1. Tokenizer normalization subtly biases one tool — mitigated by reporting both raw and normalized.
2. jCodeMunch live-probe complexity exceeds 30-min budget — mitigated by docs-first execution, fallback to smaller repo.
3. Results fire the M1-exit architectural kill signal — this IS the kill signal's purpose; honest reporting wins.
4. Upstream tool updates invalidate Phase-3 research — mitigated by pinning all versions in M1.1.
5. Benchmark harness itself has a bug that invalidates the numbers — mitigated by TDD in M2 + 15-min sanity pass at M4.1.

---

## 11. Next Action + AA-MA File to Update

**Next action:** Execute M1.1 — install Aider and jCodeMunch in a throwaway uv tool env with pinned versions. Log the install command + resulting versions in provenance.log.

**AA-MA file to update first:** `codemem-token-benchmarks-provenance.log` (install commands + versions), then `codemem-token-benchmarks-tasks.md` (mark Task 1.1 COMPLETE with Result Log).
