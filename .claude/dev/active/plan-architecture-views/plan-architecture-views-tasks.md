# plan-architecture-views Tasks (HTP)

Plan: `plan-architecture-views-plan.md` (rev 4). Sub-step detail, code blocks and `Run:` expectations live in the plan; this file tracks state. Every sub-step carries `Mode:` (the scribe does not add it — set here per plan Global Constraints).

## Milestone 1: Standard — element #13, Contract blocks, verification, exemplar ADR

- Status: COMPLETE
- Result Log: 8/8 sub-steps COMPLETE; acceptance 5/5 verified (7/7 authoring files; angle6 test 2 passed; ADR-0010 with rendered View; element-count grep 0; cutover literal). Gates: impact LOW; §6.7 PASS; §6.8 PASS_WITH_WARNINGS 0C/2W/5I (see impl-review.md); HARD gate APPROVED 2026-09-12 (context-log). pytest 978 / bats 165 ok. Release retargeted v0.12.0. Commits 543d014..b7c750c + close-out.
- Gate: HARD
- Mode: HITL
- Dependencies: None
- Complexity: 45%
- **Critical-Path:** hook-modification
- Audit-Profile: docs-only
- TDD-Waiver: docs-only
- Acceptance Criteria: plan §3 M1 measurable goal — 7 authoring files mention "Architecture View"; `tests/commands/test_plan_verification_angle6.py` passes; `docs/adr/0010-*.md` exists with a `## Architecture View` mermaid block; scoped element-count grep (reference.md §Element-count sites) returns 0 hits; cutover date 2026-09-11 literal in SKILL.md and spec.

### Sub-step 1.1: Spec §XI — add element #13 and the Contract-block rule

- Status: COMPLETE
- Mode: HITL
- Result Log: HITL gate approved. Inserted item 13 after item 12 at docs/spec/aa-ma-specification.md:591 (text verbatim from plan). `grep -c "^13\. \*\*Architecture View" docs/spec/aa-ma-specification.md` → 1.

### Sub-step 1.2: engineering-standards.md — Diagram-Waiver canonical table + maintenance rule

- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. Diagram-Waiver table (4 values) inserted at engineering-standards.md:48 before §2; diagram-maintenance bullet at :99 in §4. `tests/codemem/test_critical_path_parser.py` 14 passed (table scrape is a subset check, second table is harmless).

### Sub-step 1.3: plan-template.md — add §12 (stale fix) and §13, Contract example

- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. plan-template.md: `**Diagram-Waiver:** none` at :13; `#### Contract` block at :82 (before Step 1.1); `## 12.` at :149 and `## 13.` at :162 before Next Action. `grep -c "^## 1[23]\."` → 2.

### Sub-step 1.4: ADR template — recommended Architecture View + Example

- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. docs/adr/TEMPLATE.md gained `## Architecture View (recommended)` and `## Example (recommended)` between Consequences and Implementation Notes.

### Sub-step 1.5: PHASE_4, aa-ma-plan command, scribe and all 29 element-count sites — 13 elements everywhere

- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. Gate grep re-run at HEAD: 29 hits → edited 14 files (assert-guarded replacements) → **0 hits**. Item 13 added to every enumerated list (rules/aa-ma.md inline list + v0.12.0 grandfathering paragraph, PHASE_4 + mermaid-notation note, aa-ma-plan.md ×2 + Step 5.3 pointer-line bullet, scribe list + extraction rule, validator Dimension 2 item 13 + severity 12-13 + /13, validation-checklist items 12-13, README items 12-13 — README previously said 12 but listed 11). `uv run pytest -q` 973 passed.

### Sub-step 1.6: plan-verification Angle 6 — checks #6 and #7 (hook-modification surface)

- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. TDD: `tests/commands/test_plan_verification_angle6.py` written first → 2 failed; checks #6/#7 inserted after #5 (SKILL.md:396-409) + grandfathering bullet (literal 2026-09-11, labelled v0.12.0) → 2 passed; full suite 975 passed. Empirical: the check-#6 grep matches this plan's front-matter (`Diagram-Waiver: none`) and returns rc 1 on grammar-ssot's plan (no field, grandfathered). CRITICAL_PATH_REVIEW entry written to provenance.log naming Milestone 1.

### Sub-step 1.7: ADR-0010 exemplar + spec flow diagram + INDEX row

- Status: COMPLETE
- Mode: HITL
- Result Log: HITL gate approved. Created `docs/adr/0010-architecture-views-and-render.md` (Accepted; Options A–D; `## Architecture View` = plan §13 Component view; `## Example` = front-matter + §13 snippet; Implementation Notes; References). INDEX.md row 0010 appended after 0009. Spec §II: file-flow mermaid diagram inserted under the taxonomy table (aa-ma-specification.md:32). preview: mmdc rc=1 (no chrome-headless-shell → UNKNOWN, as pinned); so parsed+rendered every new fence with mermaid 11.17.2 UMD in Playwright's headless Chromium — 7/7 PASS with non-empty SVG (ADR ×3, spec ×1, ADR TEMPLATE ×1, plan-template ×2). Script: scratchpad/parse_check.py (session-local).

### Sub-step 1.8: Counts, CHANGELOG, cross-reference check, install.sh re-run, sync

- Status: COMPLETE
- Mode: HITL
- Result Log: HITL gate approved (user installed bats). CHANGELOG `## Unreleased` re-created above `## v0.11.0` (Added ×7, Fixed ×2; no version heading, L-003). Cross-reference grep: every `aa-ma-lint-views|aa-ma-render|aa-ma-share` hit outside docs/superpowers and .claude/dev carries an M2/M3/M4 qualifier (3 added: spec item 13, plan-template:164, ADR-0010:68); no hardcoded command/skill count changed this milestone (M3 owns 11→12). `scripts/install.sh` re-run: 53 symlinks, 5 copied; `diff -q` installed spec copy matches. `uv run pytest -q` 975 passed; `bats tests/hooks` 165 ok / 0 not ok. Sync of reference/context-log/provenance + gate approval in the milestone-close commit.

## Milestone 2: Lint — Diagram-Waiver parser, mermaid structural lint, aa-ma-lint-views

- Status: COMPLETE
- Result Log: 8/8 sub-steps COMPLETE (2.8 added for §6.8 remediation); acceptance 4/4 (plan rc=0 render UNKNOWN; 50 collected ≥49; lint-imports 3 kept + mutation BROKEN; test_contracts_kept 3). Impact LOW; §6.7 PASS; §6.8 PASS after remediation (4C/8W all fixed with tests, 0bd8987 + 167a57f); HARD gate APPROVED 2026-09-12. pytest 1046 / bats 165 ok / bandit 0. Commits d5f56ac..b861e25 + close-out.
- Gate: HARD
- Mode: AFK
- Dependencies: Milestone 1; milestone-grammar-ssot M5 merged (grammar.split_milestones trailing-H2 fix; aa_ma.enforce / aa_ma.gate exist)
- Complexity: 55%
- **Critical-Path:** data-xform
- Audit-Profile: code-only
- Acceptance Criteria: plan §3 M2 measurable goal — `uv run aa-ma-lint-views <this plan> --repo-root .` exits 0 with a `render:` line; ≥49 new tests green (collect-only count); `uv run lint-imports` green and the mutation step breaks it; `test_contracts_kept` updated to 3.

### Sub-step 2.1: RED — parse_diagram_waiver

- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. `tests/codemem/test_diagram_waiver_parser.py` written (15 cases: 4×2 canonical forms, 5 rejections, absent, backtick-wrapped). RED confirmed: `ImportError: cannot import name 'CANONICAL_DIAGRAM_WAIVERS'`.

### Sub-step 2.2: GREEN — parser

- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. `CANONICAL_DIAGRAM_WAIVERS` + `parse_diagram_waiver` appended to plan_parsers.py via `_parse_canonical_field` (no new grammar). 15 passed; `ruff check` clean; `ruff format --check` clean for plan_parsers.py (3 pre-existing tui/ drifts untouched, out of scope L-007); full suite 993 passed.

### Sub-step 2.3: RED — structural lint fixtures and tests

- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. `tests/render/{__init__,conftest}.py`, 17 fixtures derived programmatically from `plan_ok.md` (real `### Milestone` form), `test_mermaid_lint.py` (20 cases). RED confirmed: `ModuleNotFoundError: No module named 'aa_ma.render'`.

### Sub-step 2.4: GREEN — mermaid_lint.py

- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. `src/aa_ma/render/{__init__,mermaid_lint}.py` per Contract (reuses grammar.split_milestones/strip_fenced_blocks + plan_parsers; H3→H2 promotion; per-label `(new)` exemption). tests/render 20 passed; ruff check + format clean; bandit B404/B603 (Low) annotated `# nosec` with reason (subprocess has no shell, args are own temp paths, binary from MMDC_BIN seam); full suite 1013 passed.

### Sub-step 2.5: mmdc seam tests (mutation-guarded)

- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. 8 seam tests appended (fake `mmdc` shell scripts; conftest autouse pins /nonexistent/mmdc). tests/render 28 passed. Mutation guard, each restored after: rc≠0→always FAIL (1 failed), empty-svg passes (1 failed), no-sources passes (1 failed), timeout uncaught (1 failed) — every seam rule has a test that turns red.

### Sub-step 2.6: CLI + entry point + import-linter contract (mutation-checked)

- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. RED `tests/render/test_cli.py` (ModuleNotFoundError) → GREEN `src/aa_ma/render/cli.py`; plan code sent usage to stdout, test (correctly) expects stderr — code fixed (`print_usage(sys.stderr)`). `pyproject [project.scripts] aa-ma-lint-views`; `.importlinter` `root_packages = codemem, aa_ma` + `render-is-leaf`; `test_contracts_kept` → "3 kept". **Mutation:** `import aa_ma.render` appended to grammar.py → `aa_ma.render is a leaf package BROKEN / Contracts: 2 kept, 1 broken.`; removed → `KEPT / 3 kept, 0 broken.` **Live run found a lint bug:** `aa-ma-lint-views` on this plan reported STALE_PATH at plan.md:128 — a ````markdown fence in sub-step 1.3 *quoting* §13 was matched as the section. Fixed TDD (fixture `plan_quoted_section.md` RED → GREEN): section/view headings located on `strip_fenced_blocks` text, bodies sliced from original lines; fence line numbers now exact (injected stale path reported at 1151 = its true line). Live run on ADR-0010: NO_COMPONENT_VIEW — added `### Component view` to ADR-0010 and docs/adr/TEMPLATE.md; ADR-0010 now rc=0. Measurable goal: real plan rc=0 `render: UNKNOWN`; collect-only 50 tests (≥49); full suite 1028 passed.

### Sub-step 2.7: Angle 6 uses the lint; enum test wired to the parser; sync

- Status: COMPLETE
- Mode: HITL
- Deferred from M1 §6.8 (future-proofing WARNING/INFO, L-013): (a) pin `CODE_AUDIT_PROFILES` (= {full, code-only, infra}; `custom` excluded — context-log 2026-09-12) against the 8 prose sites that inline the set (aa-ma.md:117, engineering-standards.md:59, plan-verification SKILL.md:406/411, spec:604 ×2, plan-template.md:12/79) with a `test_enum_matches_*`-style test; (b) upgrade `test_angle6_lists_waiver_values` to `CANONICAL_DIAGRAM_WAIVERS` and extend it to the engineering-standards table; (c) spec:604 forward-references `plan_parsers.parse_diagram_waiver` — resolves when 2.2 lands; SKILL.md:415 "Parsers for checks #2, #4 and #5" gains #6.
- Result Log: HITL gate approved. Angle 6 check #6 now runs `uv run --project "$AA_MA_ROOT" aa-ma-lint-views` (AA_MA_ROOT via `readlink -f` on the installed skill symlink — verified resolves to the checkout; run from /tmp → rc=0 `render: UNKNOWN`); grep stopgap removed; parser pointer names #6/`parse_diagram_waiver`/`CODE_AUDIT_PROFILES`. Deferred items closed: (a) `test_prose_code_profile_sets_match_the_constant` (5 files, ≥5 sites) — mutation `+custom` → 1 failed; (b) `test_angle6_lists_every_canonical_waiver_value` + `test_engineering_standards_table_matches_waiver_enum` import `CANONICAL_DIAGRAM_WAIVERS` — mutation (drop `single-file` row) → 1 failed; (c) spec forward reference resolved (parser exists), SKILL.md pointer updated. pytest 1031 passed; bats 0 not ok. CRITICAL_PATH_REVIEW (data-xform) written naming Milestone 2.

### Sub-step 2.8: §6.8 remediation — code/security/future-proofing findings

- Status: COMPLETE
- Mode: AFK
- Result Log: Added at the milestone boundary (not in the plan) to hold the §6.8 outcome per L-013. 4 CRITICAL / 8 WARNING, every one fixed TDD-style (RED fixtures/tests written and observed failing — the ReDoS tests timed out the suite at 120 s — then GREEN): commits 0bd8987 (code-review + future-proofing) and 167a57f (security). New tests: 6 fixtures in test_mermaid_lint.py, test_hostile_input.py (6), test_leaf_contract.py (1), angle6 subset test (1). Live: real plan rc=0 `render: UNKNOWN`; full suite 1046 passed; bandit 0 issues; lint-imports 3 kept, mutation BROKEN in a previously-uncovered module. Report: plan-architecture-views-impl-review.md.

## Milestone 3: Share — /aa-ma-share publishes markdown as a private Artifact

- Status: PENDING
- Gate: HARD
- Mode: HITL
- Dependencies: Milestone 1 (Milestone 2 recommended, not required)
- Complexity: 30%
- **Critical-Path:** doc-count-drift
- Audit-Profile: docs-only
- TDD-Waiver: docs-only
- Acceptance Criteria: plan §3 M3 measurable goal — command file with valid frontmatter; `scripts/install.sh --dry-run` lists it; from a directory outside aa-ma-forge, `/aa-ma-share <ADR-0010>` publishes and `/browse` records `svg >= 1`, console errors == 0; `aa-ma-share-allow.bats` 10/10; commands count 12 in CLAUDE.md:48, SECURITY.md:11, README table; provenance `SHARE —` line.

### Sub-step 3.1: Command file + allowlist script + bats

- Status: PENDING
- Mode: HITL
- Result Log: [placeholder]

### Sub-step 3.2: Frontmatter test + counts + README table row

- Status: PENDING
- Mode: AFK
- Result Log: [placeholder]

### Sub-step 3.3: Live check from another repo + ADR status + sync

- Status: PENDING
- Mode: HITL
- Result Log: [placeholder]

## Milestone 4: Render (optional, last) — markdown to self-contained HTML, aa-ma-render

- Status: PENDING
- Gate: HARD
- Mode: AFK
- Dependencies: Milestone 2
- Complexity: 55%
- Audit-Profile: code-only
- Prototype-Required: YES
- Acceptance Criteria: plan §3 M4 measurable goal — `aa-ma-render` writes `build/render/<stem>.html`; `/browse` records `svg >= 1`, `table >= 1`, console errors == 0; golden green; `build/` untracked. Optional: dropped only via a documented scope reduction (context-log entry + this section removed) — `SKIPPED` is not a status.

### Sub-step 4.1: Prototype (UI branch) — fence hook + html rules + mermaid ESM + theme

- Status: PENDING
- Mode: HITL
- Result Log: [placeholder]

### Sub-step 4.2: RED — render tests + golden

- Status: PENDING
- Mode: AFK
- Result Log: [placeholder]

### Sub-step 4.3: GREEN — html.py, dep promotion, golden

- Status: PENDING
- Mode: AFK
- Result Log: [placeholder]

### Sub-step 4.4: aa-ma-render CLI

- Status: PENDING
- Mode: AFK
- Result Log: [placeholder]

### Sub-step 4.5: Docs + sync + finalization

- Status: PENDING
- Mode: HITL
- Result Log: [placeholder]

## Summary Counts

- Milestones: 4 (M4 optional)
- Sub-steps: 23
- Critical-Path fields: 3 (M1 hook-modification, M2 data-xform, M3 doc-count-drift)
- Prototype-Required: 1 (M4)
