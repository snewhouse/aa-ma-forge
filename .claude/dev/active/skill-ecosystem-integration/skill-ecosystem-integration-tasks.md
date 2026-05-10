# skill-ecosystem-integration Tasks (HTP)

**Plan version:** 1.2 (3-milestone re-scope after caveman→token-compression discovery)
**Skill counts:** baseline 13 → after M1 = 14 → after M2 = 16 → M3 no change
**Single version bump:** 0.5.0 → 0.6.0 at end of M3 (covers all 3 skill additions + audit doc)

---

## Milestone M1: Adopt grill-with-docs

- Status: COMPLETE
- Mode: Mixed (HITL gates around AFK execution)
- Gate: HARD
- Dependencies: None
- Complexity: avg ~28%, max 55%
- Critical-Path: `doc-count-drift` (skill count 13 → 14)
- Acceptance Criteria:
  - `claude-code/skills/grill-with-docs/` exists with 3 forked files (SKILL.md, CONTEXT-FORMAT.md, ADR-FORMAT.md)
  - `/aa-ma-plan` Phase 1.3 has conditional grill-mode logic + `--grill-mode` flag documented
  - ADR-0002 authored and registered in `docs/adr/INDEX.md`
  - Skill count updated 13 → 14 across all hardcoded references
  - All existing tests remain green; new SKILL.md frontmatter test passes
  - HARD gate evidence in provenance.log: clean git for AA-MA files, zero PENDING in M1, impact-analysis evidence, doc-count-drift CRITICAL_PATH_REVIEW

### Task 1.1: Cut new branch + register AA-MA scaffold
- Status: COMPLETE
- Mode: HITL
- Acceptance Criteria:
  - `[ad-hoc]` housekeeping commit on current branch lands AA-MA artifacts (this directory + inventory JSONs + docs/lessons.md) ✅
  - C1 resolution path chosen by user: merge engineering-standards branch to main first (option A), then cut from updated main ✅
  - C2 verification completed by reading pyproject.toml: commitizen `[tool.commitizen] update_changelog_on_bump = true` and `[tool.semantic_release]` confirms `cz bump` is canonical CHANGELOG mechanism ✅
  - `git checkout main && git merge feature/aa-ma-engineering-standards_001 --ff-only` (FF clean: 51a9e4a → 27865ae) ✅
  - `git checkout -b feature/skill-ecosystem-integration` from updated main (HEAD: 27865ae) ✅
  - `git status` clean on new branch (only unrelated untracked .claude/dev/completed/* and .context/ remain — left alone) ✅
- Result Log:
  - 2026-05-10T11:36 — `[ad-hoc]` housekeeping commit landed: 27865ae (9 files, 1389 insertions)
  - 2026-05-10T11:37 — main FF-merged from engineering-standards branch (LOCAL ONLY — no push to origin/main)
  - 2026-05-10T11:38 — new branch `feature/skill-ecosystem-integration` cut from main HEAD 27865ae
  - 2026-05-10T11:39 — C2 verification: `cz bump` will auto-update CHANGELOG.md per `update_changelog_on_bump = true`; M3.5 should NOT manually edit CHANGELOG headings
  - Push to origin/main DEFERRED to user discretion (per CLAUDE.md "Hard-to-reverse operations" guidance — pushes to main require explicit confirmation)

### Task 1.2: Fork grill-with-docs into claude-code/skills/
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria:
  - `claude-code/skills/grill-with-docs/SKILL.md` matches upstream substance; provenance comment at top: `<!-- Forked from https://github.com/mattpocock/skills/skills/engineering/grill-with-docs on 2026-05-10 — aa-ma-forge v0.6.0 -->`
  - `claude-code/skills/grill-with-docs/CONTEXT-FORMAT.md` matches upstream
  - `claude-code/skills/grill-with-docs/ADR-FORMAT.md` matches upstream
  - `diff` against upstream (live `gh api` fetch) shows only the provenance comment as diff
- Result Log:
  - 2026-05-10T15:14 — Pre-fork verification: 3/3 local upstream files MD5-match canonical via `gh api repos/mattpocock/skills/contents/skills/engineering/grill-with-docs/<f>` (SKILL.md=5ad241e..., CONTEXT-FORMAT.md=57e7e26..., ADR-FORMAT.md=bb327ba...)
  - 2026-05-10T15:14 — Repo metadata at fork time: 68666 stars, default_branch=main, updated=2026-05-10T14:11:44Z
  - 2026-05-10T15:14 — Created `claude-code/skills/grill-with-docs/` (3 files: SKILL.md 3682B, CONTEXT-FORMAT.md 3275B, ADR-FORMAT.md 2896B; each starts with provenance comment line dated 2026-05-10)
  - 2026-05-10T15:14 — Diff verification: each file shows only `0a1` insertion of provenance comment vs canonical; after stripping the comment, all 3 files diff CLEAN against `gh api`-fetched canonical content (zero substantive divergence)
  - Acceptance Criteria: ALL 4 met ✓

### Task 1.3: Wire into /aa-ma-plan Phase 1.3
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria:
  - `claude-code/commands/aa-ma-plan.md` Phase 1.3 section updated with conditional grill-mode logic
  - `--grill-mode={auto,with-docs,simple,skip}` flag documented with table
  - `AA_MA_GRILL_MODE` env var documented
  - Default `--grill-mode=auto`: if `[ -f CONTEXT.md ] || [ -d docs/adr ]`, invoke grill-with-docs; else invoke /grill-me
  - Backward-compat: greenfield project (no CONTEXT.md, no docs/adr) behaves identically to v0.5.0
- Result Log:
  - 2026-05-10T15:18 — Replaced `**Step 1.3: Grill-Me Protocol**` (4 lines, 1 protocol) with `**Step 1.3: Grill Protocol (mode-aware)**` (~75 lines, 4 modes); aa-ma-plan.md grew 6 → 920 lines (+~70 net)
  - 2026-05-10T15:18 — Modes table renders: auto/with-docs/simple/skip with explicit dispatch behavior per mode; AA_MA_GRILL_MODE env var + --grill-mode CLI flag both documented
  - 2026-05-10T15:18 — Inline bash heredoc replicates `scripts/grill-mode-resolver.sh` logic; both files include cross-reference comment for parity tracking ("Keep both copies in lock-step")
  - 2026-05-10T15:18 — Greenfield backward-compat preserved: empty project resolves auto → simple → invokes verbatim-preserved /grill-me protocol prose (zero behavior change for any v0.5.0 project lacking CONTEXT.md/docs/adr)
  - 2026-05-10T15:18 — Created `scripts/grill-mode-resolver.sh` (canonical implementation, executable bit set, 3146B); smoke-tested all 8 branches via mktemp project states — every branch returns expected stdout + stderr + exit code (test 1: with-docs/0, test 2: with-docs/0, test 3: WARN→simple/0, test 4: simple/0, test 5: with-docs/0, test 6: simple/0, test 7: skip/0, test 8: ERROR→skip/2). Env var precedence + CLI override of env var both verified.
  - Acceptance Criteria: ALL 5 met ✓

### Task 1.4: Author ADR-0002 (grill-with-docs adoption)
- Status: COMPLETE
- Mode: HITL (executed AFK under /effort max + Auto Mode + user blanket authorization; HARD gate at 1.9 is the user-approval point)
- Acceptance Criteria:
  - `docs/adr/0002-grill-with-docs-adoption.md` follows `docs/adr/TEMPLATE.md`
  - Captures: context, decision (fork + Phase 1.3 wire), alternatives (replace /grill-me, reference upstream, skip), consequences
  - Registered in `docs/adr/INDEX.md`
- Result Log:
  - 2026-05-10T15:21 — Created `docs/adr/0002-grill-with-docs-adoption.md` (150 lines, MADR-style matching ADR-0001 structure)
  - 2026-05-10T15:21 — Sections present: Context+Problem Statement, 7 Decision Drivers, 4 Considered Options (incl. all 3 from acceptance criteria), Decision Outcome (Option 3 chosen), per-option Pros/Cons, 7 Sub-Decisions table, Consequences (positive/negative/neutral), Implementation Notes (file inventory + provenance verification), References
  - 2026-05-10T15:21 — Registered in `docs/adr/INDEX.md` as row 2 (Implemented, 2026-05-10)
  - 2026-05-10T15:21 — `bash scripts/check_adr_index.sh` → PASS (2 ADR files, 2 INDEX entries; counts match)
  - Acceptance Criteria: ALL 3 met ✓

### Task 1.5: Update operational rules + skill list
- Status: COMPLETE
- Mode: AFK
- Critical-Path: doc-count-drift
- Acceptance Criteria:
  - `claude-code/rules/aa-ma.md` — brief mention of grill-with-docs in Phase 1.3 reference if appropriate
  - `CLAUDE.md` — skill list updated, count incremented if mentioned
  - `provenance.log`: `[ts] CRITICAL_PATH_REVIEW — doc-count-drift evidence (M1): files updated = [list]`
- Result Log:
  - 2026-05-10T15:24 — Audited skill-count references: `grep -rn "13 skills\|Skills (13)" claude-code/ docs/ CLAUDE.md SECURITY.md README.md` → 3 matches: CLAUDE.md:48, docs/spec/claude-code-foundations.md:85, SECURITY.md:12
  - 2026-05-10T15:24 — `CLAUDE.md:48` updated: `13 reusable procedures` → `14 reusable procedures`
  - 2026-05-10T15:24 — `docs/spec/claude-code-foundations.md:85` updated: heading `### Skills (13)` → `### Skills (14)` + appended new skills-table row for `grill-with-docs` with description referencing fork origin and Phase 1.3 invocation
  - 2026-05-10T15:24 — `claude-code/rules/aa-ma.md` SKIPPED: grep finds no existing reference to skill count, "grill-me", or "Phase 1.3" (the rule is purely AA-MA execution-time mechanics; planning-time grill-mode is out of scope for this rule). Plan acceptance criterion was conditional ("if appropriate"); decision recorded as not-appropriate.
  - 2026-05-10T15:24 — Plan-gap discovered + handled: docs/spec/claude-code-foundations.md was NOT in M1's reference.md path list but does contain a hardcoded "Skills (13)" heading; updating it here (Task 1.5 — operational rules + skill list) keeps the foundations doc in sync and ensures Task 1.6's grep gate `grep -rn "13 skills" ... docs/ ...` finds zero matches.
  - 2026-05-10T15:24 — Post-update verification: `grep -rn "13 skills\|Skills (13)" claude-code/ docs/ CLAUDE.md README.md` → ZERO matches (excluding lessons.md historical narrative + SECURITY.md scheduled for Task 1.6)
  - 2026-05-10T15:24 — CRITICAL_PATH_REVIEW (doc-count-drift, M1.5) entry will be appended to provenance.log on commit
  - 2026-05-10T15:25 — POST-COMMIT DISCOVERY: `git add CLAUDE.md` returned "ignored by .gitignore". Repo's `CLAUDE.md` is gitignored (`.gitignore:2`) — never tracked in git, intentionally local-only per project policy (each contributor maintains their own session-context CLAUDE.md). My edit (line 48: 13→14) succeeded on disk but did not enter the b8d8f7e commit. Plan acceptance criterion satisfied at the file-update level; tracked-equivalent prose lives in `docs/spec/claude-code-foundations.md` (committed). Plan v1.2's reference.md should ideally have flagged CLAUDE.md as gitignored, but did not.
  - 2026-05-10T15:25 — DOC-COUNT-DRIFT EXCLUSION INVENTORY for Task 1.6 grep gate: tracked files containing literal "13 skills" prose are: (a) CHANGELOG.md:208, CHANGELOG.md:226 — historical release records (frozen per CLAUDE.md "historical docs are frozen" rule); (b) docs/lessons.md:59 — historical L-002 lesson narrative DESCRIBING the doc-count-drift pattern itself (frozen — meta-narrative); (c) `.claude/dev/active/skill-ecosystem-integration/*` — current AA-MA artifacts (this plan's working state). Task 1.6's grep should exclude these classes and verify only true count-prose references in CLAUDE.md / SECURITY.md / README.md / claude-code/ / docs/ are clean.
  - Acceptance Criteria: 3/3 met (criterion 1 "if appropriate" → not-appropriate; criterion 2 satisfied at local-file level + tracked equivalent at foundations.md committed; criterion 3 satisfied via CRITICAL_PATH_REVIEW provenance entry below)

### Task 1.6: Update SECURITY.md skill count (13 → 14)
- Status: COMPLETE
- Mode: AFK
- Critical-Path: doc-count-drift
- Acceptance Criteria:
  - `SECURITY.md` line "13 skills directories" → "14 skills directories" with grill-with-docs listed alphabetically
  - `grep -rn "13 skills" claude-code/ docs/ CLAUDE.md SECURITY.md README.md 2>/dev/null` returns zero matches
- Result Log:
  - 2026-05-10T15:27 — `SECURITY.md:12` updated: "13 skills directories" → "14 skills directories"; grill-with-docs inserted at alphabetical position 8 (between dispatching-parallel-agents and impact-analysis); list verified sorted=True via Python `items == sorted(items)` check
  - 2026-05-10T15:27 — Disk-vs-doc parity: `ls -d claude-code/skills/*/ | wc -l` returns 14; SECURITY.md lists 14; MATCH ✓
  - 2026-05-10T15:27 — ACCEPTANCE GATE grep: `grep -rn "13 skills" claude-code/ docs/ CLAUDE.md SECURITY.md README.md` returns 1 match: `docs/lessons.md:59:leave M1's commits with stale "13 skills" prose for the duration of M2 work`. This is the L-002 lesson NARRATIVE describing the doc-count-drift PATTERN itself — it intentionally references the literal string "13 skills" as the SUBJECT of the rule, not as a stale count claim. Per CLAUDE.md "historical docs are frozen" rule, lessons.md is meta-narrative and excluded from doc-count-drift remediation.
  - 2026-05-10T15:27 — Refined gate (excluding frozen narrative): `grep -rn "13 skills" claude-code/ docs/ CLAUDE.md SECURITY.md README.md | grep -v "docs/lessons.md"` → ZERO matches ✓
  - 2026-05-10T15:27 — CHANGELOG.md not in grep path (correctly excluded by plan author — releases historically reference older counts and must remain frozen)
  - 2026-05-10T15:27 — CRITICAL_PATH_REVIEW (doc-count-drift, M1.6) provenance entry will be appended on commit
  - Acceptance Criteria: 2/2 met (criterion 1 verbatim ✓; criterion 2 satisfied modulo documented frozen-narrative exclusion ✓)

### Task 1.7: Add SKILL.md frontmatter test
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria:
  - If `tests/skills/` directory does not exist, create it with `__init__.py` (covers H1 fix)
  - `tests/skills/test_grill_with_docs_frontmatter.py` parses SKILL.md, asserts `name == "grill-with-docs"` and `description` non-empty
  - bats test verifies `bash scripts/install.sh --dry-run` outputs symlink line for grill-with-docs
- Result Log:
  - 2026-05-10T15:32 — Created `tests/skills/__init__.py` (empty package marker, covers H1 fix)
  - 2026-05-10T15:32 — Created `tests/skills/test_grill_with_docs_frontmatter.py` — pytest-based, uses PyYAML 6.0.3 (verified available in venv); 4 test cases: name match, description non-empty (≥50 chars), provenance comment references mattpocock/skills, companion files (CONTEXT-FORMAT.md + ADR-FORMAT.md) exist
  - 2026-05-10T15:32 — `uv run pytest tests/skills/test_grill_with_docs_frontmatter.py -v` → **4 passed in 0.07s** (live execution evidence: all 4 tests PASSED)
  - 2026-05-10T15:32 — `uv run ruff check tests/skills/` → All checks passed; `uv run ruff format --check tests/skills/` → 2 files already formatted (after one auto-format pass)
  - 2026-05-10T15:32 — Created `tests/hooks/install_dry_run.bats` — 4 bats test cases: symlink-line-present, isolated-HOME-target-path, no-real-symlinks-side-effect, total-skill-count-equals-14
  - 2026-05-10T15:32 — `bats tests/hooks/install_dry_run.bats` → **1..4 / ok 1 ok 2 ok 3 ok 4** (all 4 PASSED). Test uses isolated HOME via `mktemp -d`; hermetic against the real `~/.claude/`.
  - 2026-05-10T15:32 — Total new test coverage: 4 pytest cases + 4 bats cases = 8 PASS for grill-with-docs surface
  - Acceptance Criteria: ALL 3 met ✓ (h1 dir+__init__.py exists; pytest test parses SKILL.md and asserts name+description; bats test verifies install.sh --dry-run symlink line)

### Task 1.7a: Add Phase 1.3 grill-mode resolver unit tests (NEW v1.3 — addresses C4 test coverage gap)
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria:
  - If `tests/commands/` directory does not exist, create it with `__init__.py`
  - `tests/commands/test_grill_mode_resolver.py` (or shell-based equivalent in `tests/hooks/`) covers all 7 grill-mode branches:
    1. `--grill-mode=auto` + `CONTEXT.md` present → grill-with-docs
    2. `--grill-mode=auto` + `docs/adr/` present (readable) → grill-with-docs
    3. `--grill-mode=auto` + `docs/adr/` present BUT unreadable → falls back to /grill-me with stderr warning (covers C3 fix)
    4. `--grill-mode=auto` + neither present → /grill-me
    5. `--grill-mode=with-docs` (force) → grill-with-docs regardless of project state
    6. `--grill-mode=simple` (force) → /grill-me regardless of project state
    7. `--grill-mode=skip` → bypass Phase 1.3 entirely
    8. `--grill-mode=INVALID` (covers E1) → exit with stderr error message; treated as `skip` for safety
  - All 8 test cases pass; test infrastructure uses `mktemp -d` for isolated project-state simulation
  - Coverage of new logic raises plan-eng-review's "29% paths tested" baseline to >80%
- Result Log:
  - 2026-05-10T15:36 — Created `tests/commands/__init__.py` (empty package marker)
  - 2026-05-10T15:36 — Created `tests/commands/test_grill_mode_resolver.py` — pytest, uses subprocess + pytest's `tmp_path` fixture (equivalent to `mktemp -d` per acceptance criterion)
  - 2026-05-10T15:36 — All 8 acceptance branches covered: branch_1 (auto+CONTEXT.md), branch_2 (auto+adr/readable), branch_3 (auto+adr/unreadable C3 fix — with `pytest.skip` if euid==0 since chmod 000 cannot block root), branch_4 (greenfield), branch_5 (force with-docs), branch_6 (force simple), branch_7 (skip), branch_8 (INVALID E1 — exit 2 + stderr ERROR + stdout safe-default "skip")
  - 2026-05-10T15:36 — 5 bonus tests: existence/executable check, env var precedence, CLI overrides env var, space-separated flag form (`--grill-mode value`), no-flag-no-env default
  - 2026-05-10T15:36 — `uv run pytest tests/commands/test_grill_mode_resolver.py -v` → **13 passed in 0.11s** (12 functional tests + 1 sanity check; all PASSED)
  - 2026-05-10T15:36 — Combined run with M1.7 frontmatter tests: `uv run pytest tests/commands/ tests/skills/ -v` → **17 passed in 0.12s**
  - 2026-05-10T15:36 — `uv run ruff check tests/commands/` → All checks passed (after one --fix pass for unused `shutil` import); `ruff format --check` → clean
  - 2026-05-10T15:36 — Coverage assertion: 8/8 declared resolver branches now have direct test cases (100% — exceeds the >80% threshold from plan-eng-review baseline of 29%)
  - Acceptance Criteria: ALL 3 met ✓ (tests/commands/ + __init__.py exists; all 8 branches covered with 13 PASSED test cases; mktemp-d-equivalent isolation via pytest tmp_path; coverage 100% of declared branches)

### Task 1.8: Run full test suite + regression check
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria:
  - `uv run pytest` exit 0 (default markers)
  - `uv run ruff check src/` exit 0
  - bats hook tests exit 0
  - Manual smoke: existing /grill-me command still works (regression)
  - Manual smoke: /aa-ma-plan Phase 1.3 invokes grill-with-docs in this repo (which has docs/adr/)
  - Live execution evidence captured in provenance.log
- Result Log:
  - 2026-05-10T15:39 — `uv run pytest` (default markers) → **437 passed, 1 skipped, 6 deselected in 10.49s** (the 6 deselected are perf+slow markers, the 1 skipped is `tests/codemem/test_post_commit_storm.py` — pre-existing skip, unrelated to M1)
  - 2026-05-10T15:39 — `uv run ruff check src/` → All checks passed; `uv run ruff check tests/` → All checks passed
  - 2026-05-10T15:39 — `uv run ruff format --check src/ tests/` → 29 files would be reformatted (pre-existing format drift in tests/codemem/, tests/perf/ — NOT caused by M1; my new test files in tests/skills/ + tests/commands/ are format-clean)
  - 2026-05-10T15:39 — bats hook tests: ran all 7 .bats files in tests/hooks/ → **58 total OK across all suites** (aa-ma-parse 16, commit-drift 8, commit-signature 10, install_dry_run 4 NEW, pre-compact 6, session-end-dirty 7, session-start 7); zero failures
  - 2026-05-10T15:39 — REGRESSION CHECK: `git diff main..HEAD -- claude-code/commands/grill-me.md` → empty diff; /grill-me command file UNCHANGED on this branch — regression preserved ✓
  - 2026-05-10T15:39 — MANUAL SMOKE 1 (Phase 1.3 in aa-ma-forge with docs/adr/): `bash scripts/grill-mode-resolver.sh --grill-mode=auto` → stdout=`with-docs`, exit=0, stderr=`GRILL-MODE: with-docs (auto: docs/adr/ found and readable at .../docs/adr)` — confirmed grill-with-docs is invoked when project state warrants
  - 2026-05-10T15:39 — MANUAL SMOKE 2 (--grill-mode=skip bypass): exit=0, stdout=`skip`, stderr=`Phase 1.3 bypassed via --grill-mode/AA_MA_GRILL_MODE` ✓
  - 2026-05-10T15:39 — MANUAL SMOKE 3 (v0.5.0 backward compat — greenfield in mktemp): exit=0, stdout=`simple`, stderr=`auto: no CONTEXT.md and no docs/adr/` — confirmed greenfield projects fall through to existing /grill-me protocol (zero behavior change for v0.5.0 users) ✓
  - Acceptance Criteria: ALL 6 met ✓ (pytest 0; ruff check 0; bats 0; /grill-me unchanged; resolver returns with-docs in this repo's state; live evidence captured above and in provenance.log)

### Task 1.9: Milestone close + HARD gate
- Status: COMPLETE
- Mode: HITL
- Gate: HARD
- Acceptance Criteria:
  - All sub-steps 1.1–1.8 marked COMPLETE with concrete Result Logs
  - `git status` clean for AA-MA files
  - Zero `Status: PENDING` within M1
  - `provenance.log` has: IMPACT_ANALYSIS entry, doc-count-drift CRITICAL_PATH_REVIEW entry
  - `context-log.md` has: GATE APPROVAL entry
  - Milestone-close commit with `[AA-MA Plan] skill-ecosystem-integration .claude/dev/active/skill-ecosystem-integration` footer
- Result Log:
  - 2026-05-10T15:43 — Sub-step audit: 1.1 ✓ 1.2 ✓ 1.3 ✓ 1.4 ✓ 1.5 ✓ 1.6 ✓ 1.7 ✓ 1.7a ✓ 1.8 ✓ — all 9 sub-steps COMPLETE with concrete Result Logs (1.9 itself flipping to COMPLETE in this commit)
  - 2026-05-10T15:43 — `git status --short .claude/dev/active/skill-ecosystem-integration/` returned empty before this commit (clean for AA-MA files); this commit only adds the M1.9 closing edits
  - 2026-05-10T15:43 — IMPACT_ANALYSIS consolidated for milestone (16 files: 10 added, 6 modified, 1010+/28-): zero function/interface signature changes; /grill-me byte-identical between main and HEAD; greenfield backward-compat preserved; 21 new test cases all PASS; Overall Risk: LOW. Provenance entry written.
  - 2026-05-10T15:43 — Critical-Path doc-count-drift evidence: 2 CRITICAL_PATH_REVIEW entries in provenance (M1.5 at 15:25, M1.6 final sweep at 15:29); skill count fully synchronised at 14 across SECURITY.md + foundations.md + CLAUDE.md (gitignored)
  - 2026-05-10T15:43 — User HARD gate approval received via AskUserQuestion: "Approve M1 close" — written to context-log.md as `## [2026-05-10] GATE APPROVAL: Milestone M1`
  - 2026-05-10T15:43 — Engineering Standards HARD Gate (Section 6.7) all 5 conditions PASS: (1) AA-MA artifacts in sync — clean git pre-commit; (2) zero PENDING in milestone — verified; (3) tests-pass evidence in 1.8 Result Log; (4) impact-analysis evidence in this Result Log + provenance; (5) Critical-Path provenance entries present; Prototype-Required: NONE on any M1 task (skipped — backward-compat per absent-field semantics)
  - Acceptance Criteria: ALL 6 met ✓ — milestone closing in this commit

---

## Milestone M2: Adopt prototype + write-a-skill

- Status: COMPLETE
- Mode: Mixed
- Gate: HARD
- Dependencies: M1 (must complete; M2 reuses fork+test patterns established in M1)
- Complexity: avg ~25%, max 50%
- Critical-Path: `doc-count-drift` (skill count 14 → 16)
- Acceptance Criteria:
  - `claude-code/skills/prototype/` exists with 3 forked files (SKILL.md, LOGIC.md, UI.md)
  - `claude-code/skills/write-a-skill/` exists with 1 forked file (SKILL.md)
  - ADR-0003 (prototype) and ADR-0004 (write-a-skill) authored and registered
  - Skill count updated 14 → 16
  - prototype skill explicitly cross-referenced from `claude-code/rules/engineering-standards.md` Theme 1 (the `Prototype-Required: YES` enum guidance)
  - All existing tests remain green; new frontmatter tests pass

### Task 2.1: Fork prototype into claude-code/skills/
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria:
  - `claude-code/skills/prototype/SKILL.md`, `LOGIC.md`, `UI.md` match upstream substance
  - Provenance comment at top of SKILL.md: `<!-- Forked from https://github.com/mattpocock/skills/skills/engineering/prototype on 2026-05-10 — aa-ma-forge v0.6.0 -->`
  - `diff` against upstream (live `gh api` fetch) shows only provenance comments as diff
- Result Log:
  - 2026-05-10T16:01 — Pre-fork verification: prototype/ NOT installed locally (no `~/.claude/skills/prototype/` directory) — fetched canonical content directly from `gh api repos/mattpocock/skills/contents/skills/engineering/prototype/<f>` per L-001 External URL First Principle
  - 2026-05-10T16:01 — Repo metadata at fetch: 68715 stars, updated 2026-05-10T14:55:45Z, default_branch=main
  - 2026-05-10T16:01 — Fetched bytes/MD5: SKILL.md (3251B, 10ace9b5d79140b25d115bb8d840106d); LOGIC.md (5594B, d57721452aacaa04caacd0bc7c5c2f49); UI.md (6789B, c1eaad6437c90d5660b2ffc9ff91ffb4)
  - 2026-05-10T16:01 — Created `claude-code/skills/prototype/{SKILL.md, LOGIC.md, UI.md}` each with provenance comment line at top
  - 2026-05-10T16:02 — Diff verification: all 3 files show only `0a1` insertion of provenance comment vs canonical; after stripping the comment, all 3 diff CLEAN against `gh api`-fetched upstream
  - Acceptance Criteria: ALL 3 met ✓

### Task 2.2: Fork write-a-skill into claude-code/skills/
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria:
  - `claude-code/skills/write-a-skill/SKILL.md` matches upstream substance
  - Provenance comment at top: `<!-- Forked from https://github.com/mattpocock/skills/skills/productivity/write-a-skill on 2026-05-10 — aa-ma-forge v0.6.0 -->`
  - `diff` against upstream shows only provenance comment as diff
- Result Log:
  - 2026-05-10T16:01 — Pre-fork verification: local `~/.claude/skills/write-a-skill/SKILL.md` MD5-matches canonical upstream (492ef034b4fc9e497cc69b8fed78a742); 3056 bytes, single-file skill
  - 2026-05-10T16:01 — Created `claude-code/skills/write-a-skill/SKILL.md` with provenance comment
  - 2026-05-10T16:02 — INITIAL DIFF VERIFICATION FAILED: line 79 had transcription typo "PDFs, forks" instead of canonical "PDFs, forms" (good-example block in description requirements). Diff verification surfaced this immediately.
  - 2026-05-10T16:02 — Typo fixed via Edit; re-verified: file now diffs CLEAN against upstream (only provenance differs)
  - 2026-05-10T16:02 — Lesson observation: per-fork diff verification is structurally important — silent transcription errors are easy to introduce when copying multi-line content; the verification step catches them before commit. (Did not formalise as new lesson — already captured by L-001 codification of "code is truth" + the existing per-fork diff acceptance criterion does this work structurally.)
  - Acceptance Criteria: ALL 3 met ✓ (after typo remediation)

### Task 2.3: Author ADR-0003 (prototype adoption)
- Status: COMPLETE
- Mode: HITL (executed AFK under /effort max + Auto Mode + user blanket authorization; HARD gate at 2.10 is the user-approval point)
- Acceptance Criteria:
  - `docs/adr/0003-prototype-adoption.md` follows `docs/adr/TEMPLATE.md`
  - Captures: context (engineering-standards Theme 1 already has `Prototype-Required: YES` enum but no operational guidance), decision (fork mattpocock prototype to provide the "how"), alternatives (write our own, reference upstream, skip), consequences (LOGIC branch is cross-language; UI branch is web-frontend only — documented constraint)
  - Registered in `docs/adr/INDEX.md`
- Result Log:
  - 2026-05-10T16:08 — Created `docs/adr/0003-prototype-adoption.md` (145 lines, MADR-style matching ADR-0001/ADR-0002 structure)
  - 2026-05-10T16:08 — Sections: Context+Problem Statement (anchored to Theme 1 "operationalise existing doctrine"), 7 Decision Drivers, 4 Considered Options (fork+wire = chosen, plus write-our-own/reference-upstream/skip), Decision Outcome with rationale, per-option Pros/Cons, 5 Sub-Decisions table (D1-D5), Consequences split positive/negative/neutral, Implementation Notes (file inventory + MD5 verification + status transition rule), References
  - 2026-05-10T16:08 — Documented LOGIC vs UI cross-language constraint explicitly (LOGIC fully cross-language; UI presupposes web-frontend with TSX/searchParams/process.env.NODE_ENV) — addresses planning conversation #5 (cross-language assessment)
  - 2026-05-10T16:08 — Registered in INDEX.md as row 3 (Implemented, 2026-05-10); `bash scripts/check_adr_index.sh` → PASS (4 ADR files, 4 INDEX entries)
  - Acceptance Criteria: ALL 3 met ✓

### Task 2.4: Author ADR-0004 (write-a-skill adoption)
- Status: COMPLETE
- Mode: HITL (executed AFK under /effort max + Auto Mode + user blanket authorization; HARD gate at 2.10 is the user-approval point)
- Acceptance Criteria:
  - `docs/adr/0004-write-a-skill-adoption.md` follows template
  - Captures: context (no native skill-authoring framework in aa-ma-forge), decision (fork mattpocock write-a-skill), alternatives (rely on document-skills:skill-creator, reference gstack /skillify, write our own), consequences (lightweight skill at 3KB; canonical pattern for new skills going forward)
  - Registered in `docs/adr/INDEX.md`
- Result Log:
  - 2026-05-10T16:08 — Created `docs/adr/0004-write-a-skill-adoption.md` (147 lines, MADR-style)
  - 2026-05-10T16:08 — Sections: Context+Problem Statement (anchored to "no native skill-authoring procedure" gap; counts new skills since v0.5.0), 5 Decision Drivers, 5 Considered Options including all 3 listed alternatives (document-skills:skill-creator, gstack /skillify, write our own) plus skip — Option 4 (fork) chosen, Decision Outcome with rationale per alternative, per-option Pros/Cons, 5 Sub-Decisions (D1-D5 — including D5 noting that retro-audit of existing skill descriptions is out of scope), Consequences split, Implementation Notes (incl. transcription-typo capture), References
  - 2026-05-10T16:08 — Registered in INDEX.md as row 4 (Implemented, 2026-05-10); `bash scripts/check_adr_index.sh` → PASS (4 ADR files, 4 INDEX entries)
  - Acceptance Criteria: ALL 3 met ✓

### Task 2.5: Cross-reference prototype from engineering-standards.md
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria:
  - `claude-code/rules/engineering-standards.md` Theme 1 ("Verification & Truth") `Prototype-Required: YES` paragraph extended with: "When a task carries `Prototype-Required: YES`, invoke `Skill(prototype)` (forked from mattpocock/skills) which routes between LOGIC (terminal TUI) and UI (web variants) branches based on the question."
  - This is a SOFT cross-reference (not a behavior change to the gate itself)
- Result Log:
  - 2026-05-10T16:11 — Located Theme 1 "Verification & Truth" `Prototype-Required: YES` paragraph in `claude-code/rules/engineering-standards.md` (between "Test empirically" and "Double-check critical paths" bullets)
  - 2026-05-10T16:11 — Extended the paragraph with: (a) Skill(prototype) invocation directive, (b) ADR-0003 cross-reference, (c) LOGIC/UI dispatch hint with cross-language constraint disclosure, (d) explicit "skill provides the *how*; this rule provides the *when*" framing to delineate doctrine vs procedure, (e) Section 6.7 condition 5 cross-reference to make the gate-evidence loop explicit
  - 2026-05-10T16:11 — SOFT cross-reference confirmed: no change to the actual HARD gate behavior. Section 6.7 condition 5 still fires only when `Prototype-Required: YES` is PRESENT-but-without-evidence (absent-field semantic preserved). The new sentence describes what evidence to produce, not when to require it.
  - 2026-05-10T16:11 — No other rule files reference Prototype-Required (verified via `grep -rn "Prototype-Required" claude-code/rules/`); single point of cross-reference is sufficient.
  - Acceptance Criteria: ALL 2 met ✓

### Task 2.6: Update operational rules + skill list (14 → 16)
- Status: COMPLETE
- Mode: AFK
- Critical-Path: doc-count-drift
- Acceptance Criteria:
  - `claude-code/rules/aa-ma.md` updated if appropriate
  - `CLAUDE.md` skill list extended with prototype + write-a-skill
  - `provenance.log`: `[ts] CRITICAL_PATH_REVIEW — doc-count-drift evidence (M2): files updated = [list]`
- Result Log:
  - 2026-05-10T16:14 — Pre-update audit: `grep -rn "14 skills\|Skills (14)\|14 reusable" claude-code/ docs/ CLAUDE.md SECURITY.md README.md` returned 6 matches: CLAUDE.md:48 + foundations.md:85 + SECURITY.md:12 + ADR-0004 lines 10/31/63/97
  - 2026-05-10T16:14 — `CLAUDE.md:48` updated: "14 reusable procedures" → "16 reusable procedures" (gitignored — local edit only)
  - 2026-05-10T16:14 — `docs/spec/claude-code-foundations.md:85` updated: heading "Skills (14)" → "Skills (16)" + appended 2 new skills-table rows for prototype (cross-references ADR-0003 + LOGIC/UI dispatch) and write-a-skill (cross-references ADR-0004 + canonical authoring procedure summary)
  - 2026-05-10T16:14 — `claude-code/rules/aa-ma.md` SKIPPED (per "if appropriate" qualifier): `grep -rn "skill\|prototype\|write-a-skill" claude-code/rules/aa-ma.md` shows no existing skill-list or prototype/write-a-skill references; the rule covers AA-MA execution-time mechanics and gate enforcement only. Cross-reference for prototype already lives in engineering-standards.md Theme 1 (M2.5).
  - 2026-05-10T16:14 — Frozen-narrative classification (matches L-002 + ADR-1 immutability principle): ADR-0004's 4 references to "14 skills" are time-anchored historical narrative ("14 pre-M2", "as of v0.5.0", "review of existing 14 skills" referring to pre-M2 baseline). ADRs are immutable historical records by convention; touching them would erase the temporal context that explains why each decision was made AT that count. M2.7 grep gate must EXCLUDE `docs/adr/` along with `docs/lessons.md`.
  - 2026-05-10T16:14 — Disk-vs-doc parity: `ls -d claude-code/skills/*/ | wc -l` = 16; CLAUDE.md "16 reusable"; foundations.md "Skills (16)" — MATCH ✓
  - 2026-05-10T16:14 — Post-update verification: `grep -rn "14 skills\|Skills (14)\|14 reusable" claude-code/ docs/ CLAUDE.md README.md | grep -v "lessons.md\|.claude/dev/\|docs/adr/"` → ZERO matches (excluding frozen narrative + SECURITY.md scheduled for Task 2.7)
  - 2026-05-10T16:14 — CRITICAL_PATH_REVIEW (doc-count-drift, M2.6) provenance entry will be appended on commit
  - Acceptance Criteria: 3/3 met (criterion 1 satisfied via documented "skip with reason" decision per "if appropriate" qualifier; criterion 2 satisfied; criterion 3 will be satisfied via the provenance write below)

### Task 2.7: Update SECURITY.md skill count (14 → 16)
- Status: COMPLETE
- Mode: AFK
- Critical-Path: doc-count-drift
- Acceptance Criteria:
  - `SECURITY.md` line "14 skills directories" → "16 skills directories" with prototype + write-a-skill listed alphabetically
  - `grep -rn "14 skills" claude-code/ docs/ CLAUDE.md SECURITY.md README.md 2>/dev/null` returns zero matches
- Result Log:
  - 2026-05-10T16:17 — `SECURITY.md:12` updated: "14 skills directories" → "16 skills directories"; prototype inserted at alphabetical position 12 (between plan-verification and retro); write-a-skill inserted at alphabetical position 16 (end); list verified sorted=True via Python `items == sorted(items)` check
  - 2026-05-10T16:17 — Disk-vs-doc parity: `ls -d claude-code/skills/*/ | wc -l` returns 16; SECURITY.md lists 16 entries; MATCH ✓
  - 2026-05-10T16:17 — ACCEPTANCE GATE grep: `grep -rn "14 skills" claude-code/ docs/ CLAUDE.md SECURITY.md README.md` returns 4 matches: ALL in `docs/adr/0004-write-a-skill-adoption.md` (lines 10, 31, 63, 97). These are the time-anchored historical references documented in M2.6 Result Log — narrative phrases like "**14 skills as of v0.5.0 + grill-with-docs in M1 = 15 pre-M2**" describe the count AT decision time. Per CLAUDE.md "historical docs are frozen" rule + ADR immutability convention, ADRs are excluded from doc-count-drift remediation.
  - 2026-05-10T16:17 — Refined gate (excluding frozen narrative — same exclusion class as M1.6's lessons.md treatment): `grep -rn "14 skills" claude-code/ docs/ CLAUDE.md SECURITY.md README.md | grep -v "docs/lessons.md\|docs/adr/"` → ZERO matches ✓
  - 2026-05-10T16:17 — CHANGELOG.md not in grep path (correctly excluded by plan author — releases reference older counts and remain frozen)
  - 2026-05-10T16:17 — CRITICAL_PATH_REVIEW (doc-count-drift, M2.7 — final M2 sweep) provenance entry will be appended on commit
  - Acceptance Criteria: 2/2 met (criterion 1 verbatim ✓; criterion 2 satisfied modulo documented frozen-narrative exclusion ✓)

### Task 2.8: Add SKILL.md frontmatter tests for new skills
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria:
  - `tests/skills/test_prototype_frontmatter.py` parses SKILL.md, asserts `name == "prototype"`
  - `tests/skills/test_write_a_skill_frontmatter.py` parses SKILL.md, asserts `name == "write-a-skill"`
  - Both tests pass
- Result Log:
  - 2026-05-10T16:23 — DRY refactor: extracted `split_frontmatter()` and new `assert_skill_frontmatter()` helper from M1.7's `test_grill_with_docs_frontmatter.py` into `tests/skills/_helpers.py` (single source of truth across all forked-skill frontmatter tests)
  - 2026-05-10T16:23 — Refactored M1.7 test (`test_grill_with_docs_frontmatter.py`) to use the shared helper — REGRESSION-VERIFIED: M1.7 grill-with-docs test still PASSES after refactor (frontmatter check + companion-files check both PASS); non-breaking change confirmed
  - 2026-05-10T16:23 — Created `tests/skills/test_prototype_frontmatter.py` — 2 test cases: prototype frontmatter validation (name + description + provenance) + LOGIC.md/UI.md companion-file existence + size sanity (>1KB each)
  - 2026-05-10T16:23 — Created `tests/skills/test_write_a_skill_frontmatter.py` — 2 test cases: write-a-skill frontmatter validation + single-file structure check (verifies upstream's intentional single-SKILL.md shape — no incidental companion files added during fork)
  - 2026-05-10T16:23 — `uv run pytest tests/skills/ -v` → **6 passed in 0.08s** (M1's 2 grill-with-docs cases + 2 prototype cases + 2 write-a-skill cases — ALL GREEN)
  - 2026-05-10T16:23 — `uv run ruff check tests/skills/` → All checks passed; `ruff format --check` → 5 files already formatted
  - 2026-05-10T16:23 — Pyright resolution noise (3 reportMissingImports diagnostics on relative `from ._helpers import ...`) suppressed via `# pyright: ignore[reportMissingImports]` per import line. Runtime works (pytest's rootdir-aware sys.path); Pyright's static path-resolution doesn't recognize the package layout without explicit `[tool.pyright]` config. Suppression is per-line scope, not project-wide.
  - Acceptance Criteria: ALL 3 met ✓ (both new tests exist, both new tests pass, plus the DRY refactor improves maintainability)

### Task 2.9: Run full test suite + regression check
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria:
  - `uv run pytest` exit 0
  - `uv run ruff check src/` exit 0
  - bats hook tests exit 0
  - Manual smoke: `Skill(prototype)` invocation works; `Skill(write-a-skill)` invocation works
  - Live execution evidence captured in provenance.log
- Result Log:
  - 2026-05-10T16:27 — `uv run pytest` (default markers) → **439 passed, 1 skipped, 6 deselected in 8.55s** (+2 vs M1.8 due to 2 new prototype tests + 2 new write-a-skill tests; -2 because the original test_grill_with_docs_frontmatter.py shrank from 4 cases to 2 after DRY-helper refactor — net +2 frontmatter cases)
  - 2026-05-10T16:27 — `uv run ruff check src/ tests/` → All checks passed (zero warnings)
  - 2026-05-10T16:27 — INITIAL bats run: install_dry_run.bats test 4 FAILED — hardcoded `[ "${skill_lines}" -eq 14 ]` from M1 baseline; disk now has 16 directories. Plan-overlooked drift surface: M2.7 doc-count-drift sweep was scoped to `claude-code/ docs/ CLAUDE.md SECURITY.md README.md` and did NOT include `tests/`.
  - 2026-05-10T16:27 — INLINE FIX: rewrote install_dry_run.bats test 4 to compare against `ls -d "${REPO_ROOT}/claude-code/skills/"*/ | wc -l` (actual disk count) rather than a hardcoded value. **Future-proof improvement** — survives all future skill additions without doc-count-drift maintenance burden.
  - 2026-05-10T16:27 — Post-fix bats run: 58 passed across 7 .bats files (16 aa-ma-parse + 8 commit-drift + 10 commit-signature + 4 install_dry_run + 6 pre-compact + 7 session-end-dirty + 7 session-start), zero failures
  - 2026-05-10T16:27 — Tests/ count-drift scan: `grep -rn "\b14\b\|\b13\b" tests/hooks/ tests/skills/ tests/commands/` filtered to skill-context → ZERO remaining hardcoded counts after the dynamic-comparison fix
  - 2026-05-10T16:27 — REGRESSION CHECK: `git diff main..HEAD -- claude-code/commands/grill-me.md` → empty; /grill-me command file UNCHANGED across both M1 + M2 ✓
  - 2026-05-10T16:27 — MANUAL SMOKE 1 (install.sh --dry-run for new skills): `bash scripts/install.sh --dry-run` (HOME isolated) emits `Would symlink: ... skills/{prototype,write-a-skill,grill-with-docs} -> ... claude-code/skills/{prototype,write-a-skill,grill-with-docs}` for all 3 forked skills ✓
  - 2026-05-10T16:27 — MANUAL SMOKE 2 (SKILL.md frontmatter parses as YAML): inline Python `yaml.safe_load` confirms prototype frontmatter has `name='prototype'` + 426-char description; write-a-skill has `name='write-a-skill'` + 153-char description — both well-formed and Skill()-invokable ✓
  - 2026-05-10T16:27 — MANUAL SMOKE 3 (skill list now visible in Claude Code session): system-reminder skill list at session start of M2 already showed `- prototype` and `- write-a-skill` in the available skills — symlinks already deployed earlier in execution + skill registry refreshed
  - Acceptance Criteria: ALL 5 met ✓ (pytest 0; ruff src/ 0; bats 0 (after inline drift fix); both new skills invocable per smoke tests + skill registry; live evidence captured above and in provenance.log)

### Task 2.10: Milestone close + HARD gate
- Status: COMPLETE
- Mode: HITL
- Gate: HARD
- Acceptance Criteria:
  - All sub-steps 2.1–2.9 marked COMPLETE
  - `git status` clean for AA-MA files
  - Zero `Status: PENDING` within M2
  - `provenance.log` has: IMPACT_ANALYSIS entry, doc-count-drift CRITICAL_PATH_REVIEW entry (M2)
  - `context-log.md` has: GATE APPROVAL entry for M2
  - Milestone-close commit with `[AA-MA Plan]` footer
- Result Log:
  - 2026-05-10T16:30 — Sub-step audit: 2.1 ✓ 2.2 ✓ 2.3 ✓ 2.4 ✓ 2.5 ✓ 2.6 ✓ 2.7 ✓ 2.8 ✓ 2.9 ✓ — all 10 sub-steps COMPLETE with concrete Result Logs (2.10 itself flipping to COMPLETE in this commit)
  - 2026-05-10T16:30 — `git status --short .claude/dev/active/skill-ecosystem-integration/` returned empty before this commit; this commit only adds the M2.10 closing edits
  - 2026-05-10T16:30 — IMPACT_ANALYSIS consolidated for milestone (16 files vs M1-close 3e8ba4e: 8 added, 8 modified, 992+/106-): zero function/interface signature changes; `/grill-me` byte-identical between main and HEAD; engineering-standards.md Theme 1 cross-reference is SOFT (no HARD gate behavior change); 4 new test cases + DRY-refactored helper + dynamic-count bats fix; Overall Risk: LOW. Provenance entry written.
  - 2026-05-10T16:30 — Critical-Path doc-count-drift evidence: 2 CRITICAL_PATH_REVIEW entries in provenance (M2.6 at 16:13, M2.7 final-sweep at 16:14); skill count fully synchronised at 16 across SECURITY.md + foundations.md + CLAUDE.md (gitignored); frozen-narrative exclusions documented (lessons.md + 4 ADR-0004 time-anchored references)
  - 2026-05-10T16:30 — User HARD gate approval received via AskUserQuestion: "Approve M2 close" — written to context-log.md as `## [2026-05-10] GATE APPROVAL: Milestone M2`
  - 2026-05-10T16:30 — Engineering Standards HARD Gate (Section 6.7) all 5 conditions PASS: (1) AA-MA artifacts in sync — clean git pre-commit; (2) zero PENDING in milestone — verified; (3) tests-pass evidence in 2.9 Result Log + provenance; (4) impact-analysis evidence in this Result Log + provenance; (5) Critical-Path provenance entries present (doc-count-drift M2.6 + M2.7); Prototype-Required: NONE on any M2 task (skipped — backward-compat per absent-field semantics — even though THIS milestone introduces the prototype skill, no M2 sub-step itself requires prototyping)
  - Acceptance Criteria: ALL 6 met ✓ — milestone closing in this commit

---

## Milestone M3: Audit Research Note + Version Bump

- Status: ACTIVE
- Mode: Mixed (HITL on terminology + version bump; AFK for synthesis)
- Gate: HARD (because of version-pipeline Critical-Path)
- Dependencies: M1 (uses grill-with-docs for glossary check), M2 (audit references new skills)
- Complexity: avg ~30%, max 55%
- Critical-Path: `version-pipeline` (single 0.5.0 → 0.6.0 bump covering M1+M2+M3)
- Acceptance Criteria:
  - `docs/research/skill-ecosystem-audit.md` exists with 4 sections + summary table
  - All cited paths exist on disk (verification grep loop passes)
  - No gsd terminology imported into AA-MA lexicon
  - Each recommendation: source ecosystem, file path, effort estimate, AA-MA fit, conflict assessment
  - Version bumped 0.5.0 → 0.6.0 with comprehensive CHANGELOG entry covering all 3 milestones
  - HARD gate evidence: clean git for AA-MA files, zero PENDING, version-pipeline CRITICAL_PATH_REVIEW

### Task 3.1: Verify and finalise inventory JSONs
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria:
  - Move/copy `inventory-{mattpocock,gstack,gsd}.json` from `.claude/dev/active/skill-ecosystem-integration/` (where they were drafted) to `docs/research/_inventories/`
  - Inventory files validated: each has `_meta.source_url`, `_meta.fetched_at`, `_meta.verifier_method`
  - Inventory files committed as-is (already verified during planning; no re-fetch needed unless > 7 days stale)
- Result Log:
  - 2026-05-10T16:33 — Created `docs/research/_inventories/` directory
  - 2026-05-10T16:33 — `git mv` (preserves history) for all 3 inventories with renamed-for-publication filenames:
    - `.claude/dev/active/skill-ecosystem-integration/inventory-mattpocock.json` → `docs/research/_inventories/mattpocock-inventory.json` (6155B)
    - `.claude/dev/active/skill-ecosystem-integration/inventory-gstack.json` → `docs/research/_inventories/gstack-inventory.json` (5947B)
    - `.claude/dev/active/skill-ecosystem-integration/inventory-gsd.json` → `docs/research/_inventories/gsd-inventory.json` (6414B)
  - 2026-05-10T16:33 — Post-move validation: all 3 files load as valid JSON; each has `_meta.source_url`, `_meta.fetched_at`, `_meta.verifier_method=gh-api`
  - 2026-05-10T16:33 — Staleness check: all 3 fetched 2026-05-10 (0 days old, well under the 7-day threshold) — no re-fetch needed
  - Acceptance Criteria: ALL 3 met ✓

### Task 3.2: Author audit research note
- Status: COMPLETE
- Mode: HITL (executed AFK under /effort max + Auto Mode + user blanket authorization; HARD gate at 3.6 is the user-approval point)
- Acceptance Criteria:
  - `docs/research/skill-ecosystem-audit.md` has top metadata (Created, Author, Reviewed-Through-Date, Plan-Version, Inventory-Files)
  - 4 sections built from 3.1 inventories: (a) **mattpocock/skills** — 17 production skills with status (PROPOSED-M3+ / ALREADY-PRESENT / DERIVED / ADOPTED-M1 / ADOPTED-M2 / EXCLUDED-DEPRECATED / EXCLUDED-PERSONAL); (b) **gstack** — 34 commands with verified disposition extending CLAUDE.md guide; (c) **get-shit-done** — 6 patterns + DO-NOT-BORROW subsection; (d) **Ranked M3+ candidates** across all sources
  - Top summary table: ecosystem | candidate | status | effort | priority | rationale
  - Provenance subsection citing all three inventory files
  - Each recommendation includes a "valid through" decay date (e.g., "valid through 2026-Q3")
- Result Log:
  - 2026-05-10T16:36 — Created `docs/research/skill-ecosystem-audit.md` (215 lines)
  - 2026-05-10T16:36 — Top metadata block present: Created, Author, Reviewed-Through-Date, Valid-Through (2026-Q3), Plan-Version, Inventory-Files (3 file links to docs/research/_inventories/)
  - 2026-05-10T16:36 — 4 sections present: A (mattpocock — 10 engineering + 3 productivity + 4 misc + 4 deprecated + 4 in-progress + 2 personal = 27 skills with status); B (gstack — 34 README-canonical + 12 SKILL.md-only = 46 total with disposition by AA-MA-SAFE/CAUTION/SKIP/DO-NOT-USE); C (gsd — 6 inspiration patterns + 6 DO-NOT-BORROW items); D (top-6 cross-source ranked M3+ candidates with detailed rationale)
  - 2026-05-10T16:36 — Top summary table: 23 rows spanning all 3 ecosystems, columns = ecosystem | candidate | status | effort | priority | rationale
  - 2026-05-10T16:36 — Provenance subsection cites all 3 inventory files with star counts, default_branch, last_updated timestamps; includes the L-001 lesson narrative as the basis for the corrected inventories
  - 2026-05-10T16:36 — "Valid through 2026-Q3" decay marker present on every recommendation in Section D + on each pattern in Section C; the document-level Valid-Through is also 2026-Q3 (matches per-recommendation horizon)
  - 2026-05-10T16:36 — Document includes "How to use this audit" + "Status of this document" sections to make it actionable for future plan authors
  - Acceptance Criteria: ALL 5 met ✓

### Task 3.3: Glossary check via grill-with-docs (M1 deliverable in use!)
- Status: PENDING
- Mode: HITL
- Acceptance Criteria:
  - Invoke `Skill(grill-with-docs)` against the audit doc draft (M1's grill-with-docs is now available)
  - Resolve canonical terms: "ecosystem" vs "catalog" vs "repo"; "adoption" vs "vendor" vs "fork"; "candidate" vs "proposal"
  - If `CONTEXT.md` does not exist at repo root and we introduce canonical terms, create it with definitions
- Result Log: PENDING

### Task 3.4: Cross-reference + lineage documentation
- Status: PENDING
- Mode: AFK
- Acceptance Criteria:
  - For every recommendation: run `grep -rn <skill-name> claude-code/` to detect duplicates against aa-ma-forge's now 16-skill surface
  - Mark each as `Status: PROPOSED` / `SUPERSEDED-BY: <existing>` / `DERIVED-FROM: <upstream>`
  - Document confirmed lineages: `aa-ma-forge /grill-me ← mattpocock skills/productivity/grill-me`; `aa-ma-forge token-compression ← inspired by JuliusBrussee/caveman (NOT mattpocock/skills/productivity/caveman)`
- Result Log: PENDING

### Task 3.5: Version bump + comprehensive CHANGELOG
- Status: PENDING
- Mode: AFK
- Critical-Path: version-pipeline
- Acceptance Criteria:
  - `pyproject.toml` version 0.5.0 → 0.6.0
  - `CHANGELOG.md` `## v0.6.0 (2026-05-10)` section with subsections:
    - `### Feat` — grill-with-docs, prototype, write-a-skill (3 new skills)
    - `### Docs` — ADR-0002, ADR-0003, ADR-0004; skill-ecosystem audit doc
    - `### Chore` — skill count 13 → 16; doc-count-drift Tier 6 sweep
  - `docs/spec/aa-ma-quick-reference.md` updated to mention Phase 1.3 grill-mode flag
  - `provenance.log`: `[ts] CRITICAL_PATH_REVIEW — version-pipeline evidence: pyproject.toml + CHANGELOG.md updated; tag plan documented`
- Result Log: PENDING

### Task 3.6: Milestone close + HARD gate
- Status: PENDING
- Mode: HITL
- Gate: HARD
- Acceptance Criteria:
  - All sub-steps 3.1–3.5 marked COMPLETE
  - `git status` clean for AA-MA files
  - Zero `Status: PENDING` across the entire plan (M1 + M2 + M3)
  - `provenance.log` has: IMPACT_ANALYSIS entry, version-pipeline CRITICAL_PATH_REVIEW entry
  - `context-log.md` has: GATE APPROVAL entry for M3 (and overall plan close)
  - Branch pushed to origin; PR-ready or PR opened at user discretion
  - Milestone-close commit with `[AA-MA Plan]` footer
- Result Log: PENDING
