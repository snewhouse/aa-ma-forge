# codebase-analysis-skills Context Log

## [2026-09-27] Initial Context

**Feature Request:** `/aa-ma-plan --from-map codebase-analysis-skills` — ship a clean-room whole-repo assessment skill (`assess-codebase`, successor to Ste's local `/codebase-deep-dive`) and an improved `understand-codebase`, per the cleared charting map (12/12 tickets RESOLVED, imported as `codebase-analysis-skills-map.md`).

**Key Decisions (grill, with Ste, 2026-09-27 — on top of the map's 12 tickets):**
- Git: plan artifacts on `main`; one branch + PR per milestone via `/sole-dev-merge`.
- Prototype-Required: M1 (analysis schemas), M2 (assess core), M5 (incremental regeneration).
- Rating: rubric + numeric anchors in `references/RATING.md`; a dimension whose core measured input is UNKNOWN can never be Strong.
- Models: sonnet judge agents; refuter inherits the session model.
- Code home: new leaf package `src/aa_ma/analysis/` + `aa-ma-analysis` CLI (pydantic models are the schemas); both skills call it via `AA_MA_ROOT`.
- R4 extractor: backticked unresolved `/x` → DECLARED_EXTERNAL or DANGLING; local-only user commands are DANGLING and fixed.
- Eval public repo: `honojs/hono`, SHA-pinned.
- Running repo commands: approve list + refuse installers + offline env + timeout (best-effort, stated).
- Engineering standards: all six themes apply.

**Key Decisions (brainstorm/design, Ste approved):** 8 milestones — M1 core+contract → M2 engine → M3 skill → M4 understand rewire → M5 understand v1 → M6 extractor → M7 evaluation → M8 ADRs/release. Deviation from map order: counts move into M3 (tests go red when the skill dir appears); `run` safety lands in M2.

**Key Decisions (reviews + verification):**
- CEO review (HOLD SCOPE, approach A confirmed): +4 ACs — CLI-absent degrade, non-git stamp, untrusted judged input, tool timeouts + run.log.
- Eng review: tracked-only dirty (E1), `.work-<sha12>/` hand-off (E2), one baseline vocabulary (E3), codemem `--db` seam (E4).
- Phase 4.5 V1: accept `/sole-dev-merge` rebase-merge (supersedes the grill's "merge commit").
- Phase 4.5 V2: `run` never uses a shell; `&&` split into approved parts; pipes/`;`/redirects/`$(` → not_run.
- Phase 4.5 V3: extractor keeps today's any-occurrence match for names that resolve (no ON_DISK edge lost); backtick-only applies to unresolved names.
- Phase 4.5 V4: network-reaching tools (semgrep, osv-scanner, pip-audit) run in Deep only, disclosed; Quick/Standard mark them `skipped`.
- Design choice (no question needed): `aa_ma.analysis` reaches codemem by subprocess (import forbidden by `.importlinter`), adding `hot_spots/co_changes/owners/layers` to `codemem query`; each run builds a fresh codemem index under the work dir (target `.codemem/` never read or written — Angle 6).

**Research Findings:**
- `docs/research/codebase-analysis-skills-sarif.md` — minimal valid SARIF 2.1.0 (validated with Draft4Validator), `fingerprints` vs `partialFingerprints`, `baselineState` values.
- `docs/research/codebase-analysis-skills-offline-command-run.md` — offline env per ecosystem, `npx` non-TTY `--yes`, process-group kill, `unshare -rn` caveat.
- Charting research (Tickets 1–4): prior-art, codemem-coverage, agent-scope, measurement-tools files in `docs/research/`.

**Lessons applied:** L-022 (tests under `tests/`), L-024 (fresh index before measuring; UNKNOWN-forever is a defect), L-025 (push only green), L-026 (`git add` before regen), L-027 (no hook bypass), L-028 (RED commit tests-only), L-029 (private repo by shape/count only), L-003/L-006/L-008 (CHANGELOG via Unreleased + release.sh).

**Remaining Questions:**
- None blocking. Residual verification WARNINGs are listed in `codebase-analysis-skills-verification.md` for the milestone that owns each.

_This log will be updated via context compaction as the task progresses._

## [2026-09-28] PLAN APPROVAL — treated as approved (Ste)
- Gate: planning (post-/double-check)
- Approved by: Ste — decision 2026-09-28: the design, grill, CEO/Eng and V1–V4 approvals suffice; plan at `bed5a2b` (+ this sync's corrections) is the approved baseline.
- Context: the plan was committed before Ste read the final text (double-check finding; lesson L-030).

## [2026-09-28] Decisions closing the /double-check (Ste)
- "Use at most 5 agents" means **at most 5 subagents running at once** (not a total). Planning complied (peak 4). Rule written into plan §0 for execution; M7 judges run in waves.
- CONTEXT.md *Codebase analysis* glossary (8 terms, my wording) stays; Ste approves the wording at M8.1 (M14 precedent).
- A fresh read-only consistency pass over plan v5 was run before this sync; its findings are fixed in the same commit.

## [2026-09-28] M1.1 Prototype verdict + §5a refinements (Ste) — recorded before the RED commit
- Prototype: `prototype/cas-analysis-schemas` @ `9cbd29d` (`src/aa_ma/analysis/PROTOTYPE-analysis-schemas.html`); JS `findingId` == Python hashlib (`F-8eee32c533b2` for `security/security.secret/src/db.py/aws-access-token`).
- Verdict: **PASS as specced** — §5a field set (Summary, Finding, JudgedFinding, SARIF shape) accepted unchanged.
- Refinement R-1 (redact before hashing): a judged finding's anchor = whitespace-collapsed source line **after** the regex secret set has replaced each span with `[REDACTED:<rule>]`. `ids.anchor_for(line) -> str` does both; the stored and hashed anchor are the same redacted text, so IDs stay stable and no secret reaches `findings.jsonl`. `ids.py` may import `secrets.py` (intra-package).
- Refinement R-2 (accepted edge): identical twins get `#k` by order of appearance (k ≥ 2 appends `#k` to the anchor before hashing); an inserted twin above the original takes the original's ID. Counts stay correct; the contract states it.
- Refinement R-3 (accepted edge): path is part of the ID, so a file rename reads as fixed + new. Git rename detection deferred (TODOS in M8.2).
- Validator WARN #3 folded into 1.3: negative fixture `schema_version: true` (strict mode must reject it).

## [2026-09-28] M1 review outcomes (§6.8 + §6.6)
- §6.8: 3 CRITICALs accepted by Ste and fixed (dup JSON keys, stray `.gitignore`, gitleaks unmappable entry fail-open); all WARNINGs fixed (Ste: "fix all now"); re-run 0 CRITICAL. Detail: `codebase-analysis-skills-impl-review.md`.
- §6.6: a CRITICAL in the new key-context scan (value offset searched, not known) fixed test-first; distinct-text scanning gives ~12× on a 5000-finding report.
- Decisions for M2 (logged, not done): batch gitleaks into one file per source (touches fail-closed mapping — needs its own tests); decide whether `--redact` keeps the full rescan; key SARIF maps by enums; golden JSON Schemas do not express field_validator rules (path, UTC) — non-Python consumers must use `aa-ma-analysis validate`.

## [2026-09-28] GATE APPROVAL: Milestone 1: Analysis contract + `aa_ma.analysis` core
- Gate: HARD
- Approved by: Ste (AskUserQuestion, 2026-09-28: "Approve + PR + merge")
- Criteria verified: 11/11
- Decision: APPROVED
- Evidence: 1843 passed / 2 pre-existing skips; codemem 791 passed; lint-imports 6/6 KEPT; §6.8 re-run 0 CRITICAL; §6.6 CRITICAL fixed; TDD PASS; PROTOTYPE + CRITICAL_PATH_REVIEW in provenance.

## [2026-09-28] Milestone Completion: Milestone 1 — Analysis contract + `aa_ma.analysis` core
- Status: COMPLETE
- Key outcome: a tested leaf package (`aa_ma.analysis`, CLI `aa-ma-analysis stamp|fresh|validate|scan-secrets`) defines every M1 output schema, the SHA stamp, stable finding IDs, SARIF 2.1.0 and a fail-closed secret gate; `ANALYSIS-CONTRACT.md` is the one contract both skills obey.
- Artifacts: src/aa_ma/analysis/*.py; tests/analysis/* (+ fixtures, goldens, vendored SARIF schema); references/ANALYSIS-CONTRACT.md; SKILL.md + 4 onboarding agents; .importlinter; pyproject.toml; CHANGELOG Unreleased; docs/architecture regenerated.
- Tests: 1843 passed / 2 pre-existing skips; codemem 791 passed; lint-imports 6/6 KEPT; §6.7 ENG-STANDARDS + DIAGRAM gates PASS.
- Next: Milestone 2 — Dependencies: Milestone 1.
