# skill-ecosystem-integration Tasks (HTP)

**Plan version:** 1.2 (3-milestone re-scope after caveman→token-compression discovery)
**Skill counts:** baseline 13 → after M1 = 14 → after M2 = 16 → M3 no change
**Single version bump:** 0.5.0 → 0.6.0 at end of M3 (covers all 3 skill additions + audit doc)

---

## Milestone M1: Adopt grill-with-docs

- Status: ACTIVE
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
- Status: PENDING
- Mode: AFK
- Acceptance Criteria:
  - If `tests/skills/` directory does not exist, create it with `__init__.py` (covers H1 fix)
  - `tests/skills/test_grill_with_docs_frontmatter.py` parses SKILL.md, asserts `name == "grill-with-docs"` and `description` non-empty
  - bats test verifies `bash scripts/install.sh --dry-run` outputs symlink line for grill-with-docs
- Result Log: PENDING

### Task 1.7a: Add Phase 1.3 grill-mode resolver unit tests (NEW v1.3 — addresses C4 test coverage gap)
- Status: PENDING
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
- Result Log: PENDING

### Task 1.8: Run full test suite + regression check
- Status: PENDING
- Mode: AFK
- Acceptance Criteria:
  - `uv run pytest` exit 0 (default markers)
  - `uv run ruff check src/` exit 0
  - bats hook tests exit 0
  - Manual smoke: existing /grill-me command still works (regression)
  - Manual smoke: /aa-ma-plan Phase 1.3 invokes grill-with-docs in this repo (which has docs/adr/)
  - Live execution evidence captured in provenance.log
- Result Log: PENDING

### Task 1.9: Milestone close + HARD gate
- Status: PENDING
- Mode: HITL
- Gate: HARD
- Acceptance Criteria:
  - All sub-steps 1.1–1.8 marked COMPLETE with concrete Result Logs
  - `git status` clean for AA-MA files
  - Zero `Status: PENDING` within M1
  - `provenance.log` has: IMPACT_ANALYSIS entry, doc-count-drift CRITICAL_PATH_REVIEW entry
  - `context-log.md` has: GATE APPROVAL entry
  - Milestone-close commit with `[AA-MA Plan] skill-ecosystem-integration .claude/dev/active/skill-ecosystem-integration` footer
- Result Log: PENDING

---

## Milestone M2: Adopt prototype + write-a-skill

- Status: PENDING
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
- Status: PENDING
- Mode: AFK
- Acceptance Criteria:
  - `claude-code/skills/prototype/SKILL.md`, `LOGIC.md`, `UI.md` match upstream substance
  - Provenance comment at top of SKILL.md: `<!-- Forked from https://github.com/mattpocock/skills/skills/engineering/prototype on 2026-05-10 — aa-ma-forge v0.6.0 -->`
  - `diff` against upstream (live `gh api` fetch) shows only provenance comments as diff
- Result Log: PENDING

### Task 2.2: Fork write-a-skill into claude-code/skills/
- Status: PENDING
- Mode: AFK
- Acceptance Criteria:
  - `claude-code/skills/write-a-skill/SKILL.md` matches upstream substance
  - Provenance comment at top: `<!-- Forked from https://github.com/mattpocock/skills/skills/productivity/write-a-skill on 2026-05-10 — aa-ma-forge v0.6.0 -->`
  - `diff` against upstream shows only provenance comment as diff
- Result Log: PENDING

### Task 2.3: Author ADR-0003 (prototype adoption)
- Status: PENDING
- Mode: HITL
- Acceptance Criteria:
  - `docs/adr/0003-prototype-adoption.md` follows `docs/adr/TEMPLATE.md`
  - Captures: context (engineering-standards Theme 1 already has `Prototype-Required: YES` enum but no operational guidance), decision (fork mattpocock prototype to provide the "how"), alternatives (write our own, reference upstream, skip), consequences (LOGIC branch is cross-language; UI branch is web-frontend only — documented constraint)
  - Registered in `docs/adr/INDEX.md`
- Result Log: PENDING

### Task 2.4: Author ADR-0004 (write-a-skill adoption)
- Status: PENDING
- Mode: HITL
- Acceptance Criteria:
  - `docs/adr/0004-write-a-skill-adoption.md` follows template
  - Captures: context (no native skill-authoring framework in aa-ma-forge), decision (fork mattpocock write-a-skill), alternatives (rely on document-skills:skill-creator, reference gstack /skillify, write our own), consequences (lightweight skill at 3KB; canonical pattern for new skills going forward)
  - Registered in `docs/adr/INDEX.md`
- Result Log: PENDING

### Task 2.5: Cross-reference prototype from engineering-standards.md
- Status: PENDING
- Mode: AFK
- Acceptance Criteria:
  - `claude-code/rules/engineering-standards.md` Theme 1 ("Verification & Truth") `Prototype-Required: YES` paragraph extended with: "When a task carries `Prototype-Required: YES`, invoke `Skill(prototype)` (forked from mattpocock/skills) which routes between LOGIC (terminal TUI) and UI (web variants) branches based on the question."
  - This is a SOFT cross-reference (not a behavior change to the gate itself)
- Result Log: PENDING

### Task 2.6: Update operational rules + skill list (14 → 16)
- Status: PENDING
- Mode: AFK
- Critical-Path: doc-count-drift
- Acceptance Criteria:
  - `claude-code/rules/aa-ma.md` updated if appropriate
  - `CLAUDE.md` skill list extended with prototype + write-a-skill
  - `provenance.log`: `[ts] CRITICAL_PATH_REVIEW — doc-count-drift evidence (M2): files updated = [list]`
- Result Log: PENDING

### Task 2.7: Update SECURITY.md skill count (14 → 16)
- Status: PENDING
- Mode: AFK
- Critical-Path: doc-count-drift
- Acceptance Criteria:
  - `SECURITY.md` line "14 skills directories" → "16 skills directories" with prototype + write-a-skill listed alphabetically
  - `grep -rn "14 skills" claude-code/ docs/ CLAUDE.md SECURITY.md README.md 2>/dev/null` returns zero matches
- Result Log: PENDING

### Task 2.8: Add SKILL.md frontmatter tests for new skills
- Status: PENDING
- Mode: AFK
- Acceptance Criteria:
  - `tests/skills/test_prototype_frontmatter.py` parses SKILL.md, asserts `name == "prototype"`
  - `tests/skills/test_write_a_skill_frontmatter.py` parses SKILL.md, asserts `name == "write-a-skill"`
  - Both tests pass
- Result Log: PENDING

### Task 2.9: Run full test suite + regression check
- Status: PENDING
- Mode: AFK
- Acceptance Criteria:
  - `uv run pytest` exit 0
  - `uv run ruff check src/` exit 0
  - bats hook tests exit 0
  - Manual smoke: `Skill(prototype)` invocation works; `Skill(write-a-skill)` invocation works
  - Live execution evidence captured in provenance.log
- Result Log: PENDING

### Task 2.10: Milestone close + HARD gate
- Status: PENDING
- Mode: HITL
- Gate: HARD
- Acceptance Criteria:
  - All sub-steps 2.1–2.9 marked COMPLETE
  - `git status` clean for AA-MA files
  - Zero `Status: PENDING` within M2
  - `provenance.log` has: IMPACT_ANALYSIS entry, doc-count-drift CRITICAL_PATH_REVIEW entry (M2)
  - `context-log.md` has: GATE APPROVAL entry for M2
  - Milestone-close commit with `[AA-MA Plan]` footer
- Result Log: PENDING

---

## Milestone M3: Audit Research Note + Version Bump

- Status: PENDING
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
- Status: PENDING
- Mode: AFK
- Acceptance Criteria:
  - Move/copy `inventory-{mattpocock,gstack,gsd}.json` from `.claude/dev/active/skill-ecosystem-integration/` (where they were drafted) to `docs/research/_inventories/`
  - Inventory files validated: each has `_meta.source_url`, `_meta.fetched_at`, `_meta.verifier_method`
  - Inventory files committed as-is (already verified during planning; no re-fetch needed unless > 7 days stale)
- Result Log: PENDING

### Task 3.2: Author audit research note
- Status: PENDING
- Mode: HITL
- Acceptance Criteria:
  - `docs/research/skill-ecosystem-audit.md` has top metadata (Created, Author, Reviewed-Through-Date, Plan-Version, Inventory-Files)
  - 4 sections built from 3.1 inventories: (a) **mattpocock/skills** — 17 production skills with status (PROPOSED-M3+ / ALREADY-PRESENT / DERIVED / ADOPTED-M1 / ADOPTED-M2 / EXCLUDED-DEPRECATED / EXCLUDED-PERSONAL); (b) **gstack** — 34 commands with verified disposition extending CLAUDE.md guide; (c) **get-shit-done** — 6 patterns + DO-NOT-BORROW subsection; (d) **Ranked M3+ candidates** across all sources
  - Top summary table: ecosystem | candidate | status | effort | priority | rationale
  - Provenance subsection citing all three inventory files
  - Each recommendation includes a "valid through" decay date (e.g., "valid through 2026-Q3")
- Result Log: PENDING

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
