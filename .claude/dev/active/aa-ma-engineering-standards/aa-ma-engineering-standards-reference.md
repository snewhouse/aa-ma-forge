# aa-ma-engineering-standards Reference

**Immutable facts and constants for this task.**

_Last Updated: 2026-05-09 14:55_

---

## API Endpoints

_None — this task is pure local code (plugin scaffolding, doctrine, doc edits, release pipeline). No external API exercised._

| Endpoint | URL | Auth | Notes |
|----------|-----|------|-------|
| N/A | N/A | N/A | Task is local-only; `Baseline: N/A — pure local code, no API exercised` applies to all milestones. |

## File Paths

### Files to Create

- `claude-code/rules/engineering-standards.md` — doctrine file (the 6 themes), ~100 lines, auto-loaded `[valid: 2026-05-09]`
- `docs/templates/engineering-standards-template.md` — optional per-task artifact template `[valid: 2026-05-09]`
- `docs/adr/INDEX.md` — ADR index per existing doc-drift Tier 5 convention `[valid: 2026-05-09]`
- `docs/adr/TEMPLATE.md` — MADR-style template for future ADRs `[valid: 2026-05-09]`
- `docs/adr/0001-engineering-standards-architecture.md` — captures decisions D1–D8 `[valid: 2026-05-09]`
- `.claude/dev/active/aa-ma-engineering-standards/aa-ma-engineering-standards-plan.md` `[valid: 2026-05-09]`
- `.claude/dev/active/aa-ma-engineering-standards/aa-ma-engineering-standards-reference.md` `[valid: 2026-05-09]`
- `.claude/dev/active/aa-ma-engineering-standards/aa-ma-engineering-standards-context-log.md` `[valid: 2026-05-09]`
- `.claude/dev/active/aa-ma-engineering-standards/aa-ma-engineering-standards-tasks.md` `[valid: 2026-05-09]`
- `.claude/dev/active/aa-ma-engineering-standards/aa-ma-engineering-standards-provenance.log` `[valid: 2026-05-09]`
- `.claude/dev/active/aa-ma-engineering-standards/aa-ma-engineering-standards-verification.md` — produced by plan-verification skill in M0.5 `[valid: 2026-05-09]`

### Files to Modify

- `claude-code/rules/aa-ma.md` — Planning Standard section bumps 11 → 12 elements (M3.1)
- `claude-code/skills/operational-constraints/SKILL.md` — reference engineering-standards rule; cap +20 lines (M2.1)
- `claude-code/skills/plan-verification/SKILL.md` — extend Angle 6 (or add Angle 7) to detect missing element #12 (M2.2)
- `claude-code/skills/aa-ma-plan-workflow/SKILL.md` — Phase 4 description references element #12 (M3.5)
- `claude-code/commands/aa-ma-plan.md` — Phase 1 lessons scan + Phase 2 declaration prompt + Phase 4 element #12 emit (M2.3)
- `claude-code/commands/execute-aa-ma-step.md` — per-step advisory checklist injected into prompt contract (M2.4)
- `claude-code/commands/execute-aa-ma-milestone.md` — milestone HARD gate (clean git, zero PENDING, tests pass, impact-analysis run, provenance evidence for Critical-Path/Prototype-Required) (M2.5)
- `docs/spec/aa-ma-specification.md` — Section XI bumps to 12 elements with full description of #12 (M3.2)
- `docs/spec/aa-ma-quick-reference.md` — element count 11 → 12 (M3.3)
- `docs/spec/claude-code-foundations.md` — element count + rules-list count (1 → 2) (M3.4)
- `docs/templates/plan-template.md` — placeholder for element #12 (M3.6)
- `docs/templates/tasks-template.md` — add `Prototype-Required:` and `Critical-Path:` fields (M2.7)
- `README.md` — feature mention; counts (rules 1 → 2 if cited) (M3.8)
- `CHANGELOG.md` — `[0.5.0]` section (M4.4)
- `SECURITY.md` — count refresh if applicable (M3.8)
- `pyproject.toml` — version bump 0.4.0 → 0.5.0 via commitizen (M4.5)
- `docs/adr/0001-engineering-standards-architecture.md` — Status field Accepted → Implemented after M1 ships (M1.2); also self-update line 10 "11-element Planning Standard" → "12-element" during M3.5 (verification finding I5)
- `VERSION` — bump `__version__ = "0.4.0"` → `"0.5.0"` via cz `[tool.commitizen] version_files=["VERSION:__version__"]` (M4.5) — **(verification finding C-version)**
- `scripts/install.sh` — add `create_symlink` for new `claude-code/rules/engineering-standards.md` (lines 145, 283-284 currently hardcode `aa-ma.md` only) (M4.3) — **(verification finding C-install)**
- `claude-code/agents/aa-ma-validator.md:143` — change `Score: [N]/11 elements present` → `/12` (M3.5) — **(verification finding I3)**
- `claude-code/skills/aa-ma-plan-workflow/references/PHASE_4_PLAN_GENERATION.md` — 3 stale "11" references; covered by M3.5 widened scope — **(verification finding C-PHASE)**
- `claude-code/skills/aa-ma-plan-workflow/references/PHASE_5_ARTIFACT_CREATION.md` — 1 stale "11" reference; covered by M3.5 widened scope — **(verification finding C-PHASE)**

### Key Directories

- `.claude/dev/active/aa-ma-engineering-standards/` — task home; 5 standard artifacts + optional verification.md
- `docs/adr/` — new ADR convention directory (introduced by this plan)
- `claude-code/rules/` — auto-loaded rule files; `engineering-standards.md` joins `aa-ma.md`
- `claude-code/skills/` — operational-constraints, plan-verification, aa-ma-plan-workflow amended
- `claude-code/commands/` — aa-ma-plan, execute-aa-ma-step, execute-aa-ma-milestone amended
- `docs/spec/` — canonical specification, quick reference, foundations
- `docs/templates/` — plan, tasks, engineering-standards templates

## Configuration

### Environment Variables

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `AA_MA_HOOKS_DISABLE` | unset | no | Master kill switch for AA-MA hooks; recognized by existing hook scripts. Not modified by this plan; documented for emergency bypass. |

### Config Files

- `pyproject.toml`:
  - `version`: `0.4.0` → `0.5.0` (set by commitizen in M4.5)
  - `[tool.commitizen]` and `[tool.semantic_release]` sections drive the bump (existing, unchanged)
- `commitizen` reads `[tool.commitizen]` from `pyproject.toml`
- Hook bypass marker: `[AA-MA Plan] aa-ma-engineering-standards .claude/dev/active/aa-ma-engineering-standards` — required as last footer line on every commit during this plan's execution.

## Dependencies

| Package | Version | Class | Purpose |
|---------|---------|-------|---------|
| uv | (project-pinned) | Required | Test runner / dependency resolution |
| commitizen | >= 3.x | Required | Version bump and CHANGELOG management |
| python-semantic-release | (project-pinned) | Required | Tag automation, paired with commitizen |
| ruff | (project-pinned) | Dev-only | Lint and format (M4.2) |
| bats | system pkg | Dev-only | Hook test runner (M4.1) — install via `apt-get install -y bats` |
| pytest | (project-pinned) | Dev-only | Default test suite (M4.1) |

## Constants

| Constant | Value | Context |
|----------|-------|---------|
| Branch name | `feature/aa-ma-engineering-standards_001` | M0 commit target; all M1–M4 commits land here `[valid: 2026-05-09]` |
| Target version | `0.5.0` | Single coordinated minor bump from `0.4.0`; per locked decision D8 `[valid: 2026-05-09]` |
| Tag | `v0.5.0` | Pushed in M4.6 `[valid: 2026-05-09]` |
| Planning Standard count (post-bump) | 12 | Was 11; element #12 = "Engineering Standards Declaration" `[valid: 2026-05-09]` |
| Doctrine file size cap | ≤ 120 lines | Hard cap for `claude-code/rules/engineering-standards.md` to keep doctrine principles-only `[valid: 2026-05-09]` |
| Skill amendment size cap | +20 lines per skill | Cap for `operational-constraints/SKILL.md` and `plan-verification/SKILL.md` amendments — references-not-duplicates `[valid: 2026-05-09]` |
| Phase 1 lessons-scan timeout | hard 30 seconds via `timeout 30s` | **(ceo-review CEO-3)** Hard timeout, not soft budget. On timeout: emit notice, continue without scan results, never hang. Scan covers `docs/lessons.md` + `git log --grep="revert\|fix\|hotfix"` (6 months) + top-3 most-recent completed context-logs `[valid: 2026-05-09]` |
| AA-MA commit footer | `[AA-MA Plan] aa-ma-engineering-standards .claude/dev/active/aa-ma-engineering-standards` | Last footer line on every plan-related commit `[valid: 2026-05-09]` |
| Distribution context | `distributed plugin` | **(ceo-review CEO-1)** aa-ma-forge is a distributed Claude Code plugin; `install.sh` symlinks `engineering-standards.md` into `~/.claude/rules/` for ALL consumers on next session after install. Soft-breaking change in v0.5.0. Opt-out: `AA_MA_HOOKS_DISABLE=1` master kill switch OR remove the symlink `[valid: 2026-05-09]` |
| Pre-v0.5.0 plan grandfathering | `enabled` | **(ceo-review CEO-4)** Plans authored before v0.5.0 (without element #12) remain valid. plan-verification Angle 6 only flags missing #12 for plans created at-or-after v0.5.0 origin. Detection: front-matter version field or git creation date `[valid: 2026-05-09]` |
| Observability provenance entry | `[ts] ENG_STANDARDS_DECLARED: themes=[...]` | **(ceo-review CEO-5)** Every aa-ma-plan invocation that emits a Phase 2 declaration writes this entry to provenance.log. Provides per-plan audit trail. Eliminates silent-compliance failure mode `[valid: 2026-05-09]` |
| Rollback runbook | `docs/runbooks/rollback-v0.5.0.md` | **(ceo-review CEO-6)** Authored in M4.8. Steps: (1) `git checkout v0.4.0 -- claude-code/rules/ docs/spec/ docs/adr/ docs/templates/`; (2) `scripts/install.sh`; (3) verify symlink removed; (4) optional `AA_MA_HOOKS_DISABLE=1` `[valid: 2026-05-09]` |

## Schema Definitions

### Doctrine themes (six themes shipped in `claude-code/rules/engineering-standards.md`)

Source: this plan's design — 6 themes documented below.

| Theme # | Title | Core principle |
|---------|-------|----------------|
| 1 | Verification & Truth | Code as source of truth; empirical testing; prototype-first; double-check critical paths |
| 2 | Development Principles | TDD, KISS, DRY, SOLID, SOC |
| 3 | Reasoning & Planning | First-principles, Socratic questioning, skill assessment, strategic subagent use |
| 4 | Safety & Continuity | Non-breaking, lessons learned, avoid repeated mistakes, incremental validation |
| 5 | Execution Checklist | Step-level advisory + milestone-level HARD/SOFT enforcement |
| 6 | Sync & Commit Discipline | Sub-step Result Log; milestone HARD gate refuses dirty git or PENDING within milestone |

### Per-task fields introduced by this plan

Source: amendments to `docs/templates/tasks-template.md` (M2.7).

| Field | Required | Default | Purpose |
|-------|----------|---------|---------|
| `Prototype-Required:` | optional | absent | When `YES`, milestone HARD gate requires a `[ts] PROTOTYPE — <verdict>` provenance entry before COMPLETE |
| `Critical-Path:` | optional | absent | When set (e.g. `auth-flow`), milestone HARD gate requires `[ts] CRITICAL_PATH_REVIEW` provenance entry |

### Critical-Path enum (eng-review finding 1.5; defined in M1.1)

Canonical values for the `Critical-Path:` field. Defined in `claude-code/rules/engineering-standards.md` Theme 1. Plan-verification rejects novel values; new values added only via plan + ADR.

| Value | Applies to |
|-------|-----------|
| `auth-flow` | Authentication, authorization, session, token handling |
| `data-xform` | Data transformations, schema migrations, format conversions |
| `external-api` | Calls to third-party APIs (rate limits, error handling, contract surface) |
| `version-pipeline` | Release, version-bump, tag-and-push, CHANGELOG mechanics |
| `doc-count-drift` | Hardcoded counts in docs (Tier 6 detector domain — element counts, file counts, skill counts) |
| `hook-modification` | Changes to `claude-code/hooks/*.sh` (BLOCKING hooks affect all sessions) |

### Locked decisions D1–D8 (captured in ADR-0001)

Source: this plan's "Locked Decisions" table (lines 60–69 of source plan).

| ID | Decision |
|----|----------|
| D1 | Sharper multi-artifact: 1 new doctrine rule + amend existing skills/commands |
| D2 | Step-level ADVISORY + milestone-level tiered HARD/SOFT enforcement |
| D3 | Planning Standard 11 → 12 elements (#12 = Engineering Standards Declaration) |
| D4 | Cheap inline lessons scan in Phase 1 (lessons.md + git log + top-3 completed context-logs) |
| D5 | Prototype/empirical evidence via provenance.log entries + per-task flag |
| D6 | Milestone-end commit gate only — no step-level commit nudges |
| D7 | Introduce ADR convention (`docs/adr/`); first ADR is 0001-engineering-standards-architecture |
| D8 | Single coordinated minor bump 0.4.0 → 0.5.0 |

## Temporal Validity Convention

Facts in this file carry `[valid: YYYY-MM-DD]` markers based on extraction date. When a fact becomes obsolete during execution, append `[superseded: YYYY-MM-DD by step-N.M]` rather than deleting.

## External References

- AA-MA operational rules: `claude-code/rules/aa-ma.md` (in repo)
- AA-MA spec: `docs/spec/aa-ma-specification.md`
- AA-MA quick reference: `docs/spec/aa-ma-quick-reference.md`
- Foundations: `docs/spec/claude-code-foundations.md`
- Doc-drift Tier 6 detector definition: `~/.claude/rules/doc-drift-checks.md` (user-global; not in repo)
- Sub-step sync rule (L-080, L-081, L-082): `claude-code/rules/aa-ma.md` lines 47-66
- Existing post-commit drift hook: `claude-code/hooks/aa-ma-commit-drift.sh` (**ADVISORY** — warns but does not block; always exits 0; kept as-is) — **(verification finding C1)** prior characterization as "BLOCKING" was incorrect; corrected here
- HARD/SOFT gate format: `claude-code/rules/aa-ma.md` lines 153-178
- Source plan: `~/.claude/plans/engineering-standards-for-eventual-toast.md` (out-of-repo working draft; final design rationale ships at ADR-0001)
- MADR ADR template reference: https://adr.github.io/madr/ (off-the-shelf format; adopted in `docs/adr/TEMPLATE.md`)

## Glossary

| Term | Definition |
|------|-----------|
| AA-MA | Advanced Agentic Memory Architecture — the 5-file (+2 optional) external memory system for long-horizon plan-driven tasks |
| ADR | Architecture Decision Record — MADR-style document capturing context, decision, and consequences for non-trivial design choices |
| Doctrine | Principles-only content (the engineering-standards rule file); excludes procedures (those live in skills) |
| Element #12 | The Engineering Standards Declaration — the new 12th item in the AA-MA Planning Standard, introduced by this plan |
| HARD gate | Artifact-enforced milestone gate; `/execute-aa-ma-milestone` refuses to advance without signed approval in `context-log.md` |
| SOFT gate | Convention-based milestone gate; agent instructed to seek approval but no programmatic enforcement |
| HITL | Human-In-The-Loop — task pauses for user input before proceeding |
| AFK | Away-From-Keyboard — task can be auto-dispatched without user intervention |
| Critical-Path | Per-task flag in tasks.md indicating the task touches an irreversible/high-stakes path; requires `CRITICAL_PATH_REVIEW` provenance entry |
| Prototype-Required | Per-task flag in tasks.md indicating uncertainty justifies a throwaway POC; requires `PROTOTYPE — <verdict>` provenance entry |
| Lessons Scan | Phase 1 of `/aa-ma-plan` — automated scan of `docs/lessons.md` + `git log --grep="revert\|fix\|hotfix"` + top-3 most-recent completed context-logs; ~30s budget |
| MADR | Markdown Architecture Decision Records — off-the-shelf ADR format with Title / Status / Context / Decision / Consequences sections |
| Tier 6 drift | Hardcoded-count drift detector defined in `~/.claude/rules/doc-drift-checks.md`; catches stale element counts after the 11 → 12 bump |

---
