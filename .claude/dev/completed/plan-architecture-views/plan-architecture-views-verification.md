# Verification Report: plan-architecture-views
Generated: 2026-09-11T17:06:00+01:00 | Mode: automated | Revision: 3 (plan rev 4)

## Summary
- CRITICAL: 8 findings (8 resolved — 6 in pass 1, 2 in pass 2)
- WARNING: 14 findings (11 resolved in plan rev 3/4; 3 accepted as documented residual risk)
- INFO: 5
- Overall: **PASS WITH WARNINGS**

Pass history: pass 1 (6 angles, 6 agents) → FAIL (6 CRITICAL) → plan rev 3 → pass 2 (targeted re-verification, headless-Chromium render of the plan's own §13) → 6/6 resolved, 2 new CRITICAL + 1 WARNING → plan rev 4 → pass 3 → 3/3 resolved, 0 new. Loop budget (max 2 revisions) used exactly.

## Angle 1: Ground-Truth Audit
### Findings
- [CRITICAL → RESOLVED] Claim: ADR-0009 is free | Reality: `milestone-grammar-ssot-tasks.md:400-401` sub-step 5.8 reserves ADR-0009 → plan uses **ADR-0010**; reservation note kept in 1.7.
- [WARNING] The `[t.type for t in m.parse(...)]` one-liner in the verification prompt only shows `html_inline` as a child of `inline`; the rendering fact M4 relies on (an `html_inline` rule fires during `.render()`) holds. No plan change.
- [OK] 30 claims confirmed: spec 579-590; plan-template 11-12/35/77/137; ADR TEMPLATE 49/60; PHASE_4 141/156/193; aa-ma-plan 445/457/462/492/684; scribe 42/237; plan-verification 378/380/385-398; INDEX 30; .gitignore 34; install.sh 127; CLAUDE.md 48; SECURITY.md 11; CHANGELOG 7; .importlinter 18; pyproject 31-33; engineering-standards table 46/48; `_parse_canonical_field`/`parse_*`/`CANONICAL_*`; `_extract_field` rejects backticks and `**none**`; `grammar.split_milestones`/`strip_fenced_blocks`/`Block(number,title,text)`; `test_enum_matches_engineering_standards_table` at `tests/codemem/test_critical_path_parser.py:45`; `test_active_plans_canonical.py` lints `*/*-tasks.md` only; tui `__main__` argparse; `.venv` markdown-it-py **4.0.0**; `commonmark`+`table` renders `<table>`; `RendererHTML.fence` exists; **mmdc on PATH exits rc=1 "Could not find chrome-headless-shell" on a valid diagram** (the plan's UNKNOWN-unless-parse-signature rule is the correct response); import-linter 2.6 supports `root_packages`; grammar-ssot M5 creates `enforce.py`/`gate.py`, edits `grammar.py`, never touches `plan_parsers.py`.

## Angle 2: Assumption Extraction & Challenge
### Assumptions Identified
1. [VERIFIED] `readlink -f` on an installed command/skill resolves into the checkout; `../..` and `../../..` yield the repo root — `scripts/install.sh:257-268`, measured.
2. [VERIFIED] `uv run --project` from another cwd — uv 0.12.3.
3. [VERIFIED] Literal `Created:` cutover date uses the same comparison mechanism as checks #1-#5 — `plan-verification/SKILL.md:385-398`.
4. [WARNING — accepted] No in-repo precedent for a command that publishes via the Artifact tool; M3 is the first. Mitigation: tool contract cited; `/browse` assertion in 3.3.
5. [VERIFIED] Hooks iterate all active plans (`aa_ma_list_active_tasks`, `mapfile`), no `head -1` assumption.
6. [VERIFIED] grammar-ssot M5 sub-step 5.0 is exactly the `split_milestones` trailing-H2 fix; Status PENDING — reflected in Sequencing.
7. [VERIFIED] `test_active_plans_canonical.py` lints tasks.md headings only.
8. [VERIFIED] Nothing in `src/aa_ma` imports `aa_ma.render` today.
9. [VERIFIED] markdown-it-py 4.0.0 emits `html_block`/`html_inline` tokens with `.content` starting `<!--` for comments.
10. [VERIFIED] mermaid ESM from jsdelivr loads from a `file://` page in headless Chromium, 0 console errors.
11. [CRITICAL → RESOLVED] `B[src/x.py (new)]` is a mermaid **parse error** ("Expecting ... got 'PS'"); quoted form `B["src/x.py (new)"]` renders. Plan §13, templates, spec item 13, fixtures and `_stale_paths` (quote-stripping) updated.
12. [VERIFIED] `parse_diagram_waiver(front)` sees `**Diagram-Waiver:** none` in this plan's front matter.

## Angle 3: Impact Analysis on Proposed Changes
### Files Affected
- [CRITICAL → RESOLVED] `tests/codemem/test_install_and_cli.py::test_contracts_kept` asserts `"Contracts: 2 kept, 0 broken."` — M2 adds a third contract → 2.6 now updates the assertion.
- [CRITICAL → RESOLVED] Element-count drift sites beyond the 1.5 list — the scoped gate grep returns **29** live sites at HEAD; all pinned in `reference.md` §Element-count sites; frozen docs (`docs/adr/0001`, `docs/narrative`, `docs/runbooks`, `docs/plans`) excluded from the gate by scope.
- [WARNING → RESOLVED] README `### All commands` table has no `/aa-ma-share` row — added to 3.2 (cannot wait for optional M4).
- [OK] `.importlinter` → `root_packages`: no `aa_ma`↔`codemem` cross-imports; `lint-imports` at HEAD "Contracts: 2 kept". `tests/golden/layers_aa_ma_forge.txt` unrelated.
- [OK] `plan_parsers.py` consumers (`grammar.py`, 3 codemem tests, `verify-impl`, `plan-verification`) — additive change, LOW.
- [OK] all new files — no existing callers.

## Angle 4: Acceptance Criteria Falsifiability
### Criteria Audit
- [OK] M1 goal; 1.1/1.3/1.5/1.6 `Run:` steps; 2.6 mutation step (BROKEN→KEPT captured).
- [WARNING → RESOLVED] M2 test counts 38/46/48 inconsistent → single tally (15+28+6 = 49 after the H3 test) plus `--collect-only` recount at execution.
- [WARNING → RESOLVED] `/browse` checks (M3 goal, 3.3, M4 goal, 4.3) → `querySelectorAll('svg').length` and console-error count written into the Result Log.
- [WARNING → RESOLVED] "May be closed as SKIPPED" — `SKIPPED` is not a `MilestoneStatus` → replaced by a documented scope-reduction path.
- [WARNING → RESOLVED] 1.7 VS Code preview → `preview: OK|FAIL` per fence with a rubric ("Syntax error in text" box = FAIL).
- [WARNING → accepted] 4.3 golden calibration "eyeball" replaced by an svg-count + console assertion; the calibration itself remains a one-time human step.
### Score: 12/12 falsifiable after rev 4 (6/12 before)

## Angle 5: Fresh-Agent Simulation
### Implementation Barriers
- [CRITICAL → RESOLVED] `tests/render/test_cli.py` used `@pytest.mark.parametrize` without `import pytest` → added.
- [CRITICAL → RESOLVED] Lint called `split_milestones` (needs `## Milestone`) on plan.md where milestones are `### Milestone` → `_PLAN_MILESTONE_H3` promotion in `_milestone_facts`; fixtures now use `### Milestone`; new test `test_plan_h3_milestones_are_read_without_tasks`.
- [WARNING → RESOLVED] Fixture convention masked the above → fixed with the fixtures.
- [INFO → RESOLVED] `argument-hint:` frontmatter for the new command → specified in 3.1.
- [INFO] All anchors and cross-file signatures (`Finding`, `LintReport`, `lint_plan(..., tasks_path=)`, `render_check(..., timeout_s=)`, `_views → (pos, body)`) consistent.

## Angle 6: Specialist Domain Audit
### Specialists Dispatched: Engineering Standards Auditor (always) + Security lens
- Element #12 present, 6 themes with rationale. Parsers (run, not eyeballed): `parse_critical_path` M1 `hook-modification` / M2 `data-xform` / M3 `doc-count-drift` — all canonical, bold form parses; `parse_audit_profile` M1 docs-only / M2 code-only / M3 docs-only / M4 code-only; `parse_tdd_waiver` M1/M3 `docs-only`; Gate/Mode on every milestone.
- [WARNING → RESOLVED] Sub-steps need `Mode:` in tasks.md and the scribe does not add it → Phase 5 sets Mode per sub-step (mapping recorded in Global Constraints).
- [WARNING → RESOLVED] `/aa-ma-share` refusal was prose-only → `scripts/aa-ma-share-allow.sh` + `aa-ma-share-allow.bats` (10 cases; relative/absolute/`./` paths verified in bash).
- [INFO] The milestone gate reads fields via `aa_ma_field_value()` (`claude-code/hooks/lib/aa-ma-parse.sh:241`), tolerant of bold/plain — both the plan's `Critical-Path` and `Prototype-Required` forms parse.
- [INFO] Render pipeline: no raw-HTML passthrough; list-form `subprocess.run`; `shutil.which` before exec; timeout → UNKNOWN. No injection vector found.
- [INFO] `readlink -f` copied-not-symlinked case handled (M3 risk 3).

## Pass 2 / Pass 3 (targeted re-verification)
- [CRITICAL → RESOLVED] Plan's own Flow view failed to parse (`;` in a sequence message) — found by rendering both §13 blocks in headless Chromium; fixed; both blocks now render 1 svg / 0 errors each.
- [CRITICAL → RESOLVED] Widened gate grep could not reach zero (frozen docs) → scoped to live surface; 29 sites pinned.
- [WARNING → RESOLVED] Allowlist `case` rejected relative paths → pattern without leading separator, tested.

## Residual (accepted) warnings
1. First Artifact-publishing command in the repo (no precedent) — mitigated by 3.3's live check.
2. Golden calibration is a one-time human step.
3. `mmdc` render status is `UNKNOWN` on BATS until Chromium is installed — by design; `PASS` is proven only through the fake-binary tests.

## Revision History
- v1: 2026-09-11 — pass 1: 6 CRITICAL, 13 WARNING → FAIL
- v2: 2026-09-11 — plan rev 3; pass 2: 6/6 resolved, 2 new CRITICAL, 1 WARNING → FAIL
- v3: 2026-09-11 — plan rev 4; pass 3: 3/3 resolved, 0 new → **PASS WITH WARNINGS**
