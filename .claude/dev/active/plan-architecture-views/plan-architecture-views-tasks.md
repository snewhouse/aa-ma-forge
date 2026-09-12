# plan-architecture-views Tasks (HTP)

Plan: `plan-architecture-views-plan.md` (rev 4). Sub-step detail, code blocks and `Run:` expectations live in the plan; this file tracks state. Every sub-step carries `Mode:` (the scribe does not add it — set here per plan Global Constraints).

## Milestone 1: Standard — element #13, Contract blocks, verification, exemplar ADR

- Status: ACTIVE
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

- Status: PENDING
- Gate: HARD
- Mode: AFK
- Dependencies: Milestone 1; milestone-grammar-ssot M5 merged (grammar.split_milestones trailing-H2 fix; aa_ma.enforce / aa_ma.gate exist)
- Complexity: 55%
- **Critical-Path:** data-xform
- Audit-Profile: code-only
- Acceptance Criteria: plan §3 M2 measurable goal — `uv run aa-ma-lint-views <this plan> --repo-root .` exits 0 with a `render:` line; ≥49 new tests green (collect-only count); `uv run lint-imports` green and the mutation step breaks it; `test_contracts_kept` updated to 3.

### Sub-step 2.1: RED — parse_diagram_waiver

- Status: PENDING
- Mode: AFK
- Result Log: [placeholder]

### Sub-step 2.2: GREEN — parser

- Status: PENDING
- Mode: AFK
- Result Log: [placeholder]

### Sub-step 2.3: RED — structural lint fixtures and tests

- Status: PENDING
- Mode: AFK
- Result Log: [placeholder]

### Sub-step 2.4: GREEN — mermaid_lint.py

- Status: PENDING
- Mode: AFK
- Result Log: [placeholder]

### Sub-step 2.5: mmdc seam tests (mutation-guarded)

- Status: PENDING
- Mode: AFK
- Result Log: [placeholder]

### Sub-step 2.6: CLI + entry point + import-linter contract (mutation-checked)

- Status: PENDING
- Mode: AFK
- Result Log: [placeholder]

### Sub-step 2.7: Angle 6 uses the lint; enum test wired to the parser; sync

- Status: PENDING
- Mode: HITL
- Result Log: [placeholder]

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
