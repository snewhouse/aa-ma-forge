<!-- ARCHIVED: 2026-05-11 22:20 -->
<!-- Plan: post-impl-adversarial-review - COMPLETE -->
<!-- Total Milestones: 6 (21 sub-tasks: 21 COMPLETE) | Duration: 2026-05-11 12:00 to 2026-05-11 22:10 (~10h) -->

# post-impl-adversarial-review Reference

**Immutable facts and constants for this task.**

_Last Updated: 2026-05-11 00:00_

---

## API Endpoints

_None — this task is pure-local plugin work; no external API is exercised by any milestone._

| Endpoint | URL | Auth | Notes |
|----------|-----|------|-------|
| (n/a) | (n/a) | (n/a) | All milestones declare `Baseline: N/A — pure local code, no API exercised` |

## File Paths

### Files to Create

- `claude-code/skills/verify-impl/SKILL.md` — new `/verify-impl` skill (mirror of `/verify-plan`) [valid: 2026-05-11]
- `claude-code/agents/code-reviewer.md` — KISS/DRY/SOLID/SOC + L-005/L-006/L-007 regression auditor [valid: 2026-05-11]
- `claude-code/agents/security-auditor.md` — semantic security review (milestone-close layer) [valid: 2026-05-11]
- `claude-code/agents/tdd-sequence-auditor.md` — verifies first `tests/` commit precedes first `src/` commit; honors `TDD-Waiver` [valid: 2026-05-11]
- `claude-code/agents/context7-evidence-auditor.md` — checks Context7 evidence for new deps + MAJOR bumps [valid: 2026-05-11]
- `claude-code/agents/future-proofing-auditor.md` — backwards-compat + grandfathering review [valid: 2026-05-11]
- `claude-code/hooks/security-static-check.sh` — mechanical pre-commit security pattern detector [valid: 2026-05-11]
- `docs/templates/impl-review-template.md` — template for `[task]-impl-review.md` artefact [valid: 2026-05-11]
- `docs/adr/0005-post-impl-adversarial-review.md` — ADR documenting cutover decision [valid: 2026-05-11]
- `src/aa_ma/plan_parsers.py` — `Audit-Profile` + `TDD-Waiver` field parsers [valid: 2026-05-11]
- `tests/codemem/test_audit_profile_parser.py` — pytest cases for Audit-Profile parser [valid: 2026-05-11]
- `tests/codemem/test_tdd_waiver_parser.py` — pytest cases for TDD-Waiver parser [valid: 2026-05-11]
- `tests/codemem/test_corpus_grandfathering.py` — corpus regression against `.claude/dev/completed/*/*-tasks.md` [valid: 2026-05-11]
- `tests/hooks/security_static_check.bats` — bats test suite for security hook [valid: 2026-05-11]
- `tests/hooks/execute_aa_ma_milestone_phase_6_8.bats` — E2E §6.8 trigger scenarios [valid: 2026-05-11]

### Files to Modify

- `claude-code/commands/execute-aa-ma-milestone.md` — insert §6.8 between current §6.7 (line 481) and §7.1 (line 559) [valid: 2026-05-11]
- `claude-code/commands/execute-aa-ma-full.md` — delegate §6.8 to milestone command [valid: 2026-05-11]
- `claude-code/skills/plan-verification/SKILL.md` — Angle 6 adds `Audit-Profile` + `TDD-Waiver` structural checks [valid: 2026-05-11]
- `claude-code/rules/engineering-standards.md` — add canonical `TDD-Waiver` enum (mirrors `Critical-Path:` pattern) [valid: 2026-05-11]
- `docs/spec/aa-ma-specification.md` — document §6.8 and `[task]-impl-review.md` file type [valid: 2026-05-11]
- `docs/adr/INDEX.md` — list ADR-0005 [valid: 2026-05-11]
- `scripts/install.sh` — register new hook, skill, and 5 agents [valid: 2026-05-11]
- `CHANGELOG.md` — feat entry via `cz bump` (NOT manual — per L-003) [valid: 2026-05-11]
- `pyproject.toml` — version bump 0.7.0 → 0.8.0 via `cz bump` [valid: 2026-05-11]
- `README.md` — skill count, agent count, hook count sweep [valid: 2026-05-11]
- `docs/spec/claude-code-foundations.md` — count sweep [valid: 2026-05-11]
- `docs/spec/aa-ma-quick-reference.md` — count sweep [valid: 2026-05-11]
- `SECURITY.md` — count sweep [valid: 2026-05-11]

### Key Directories

- `claude-code/agents/` — currently contains only `aa-ma-scribe`, `aa-ma-validator`; gains 5 new agents in M4 [valid: 2026-05-11]
- `claude-code/hooks/` — gains `security-static-check.sh` in M2 [valid: 2026-05-11]
- `claude-code/skills/verify-impl/` — new skill directory in M4 [valid: 2026-05-11]
- `docs/adr/` — currently contains ADR-0001 through ADR-0004; ADR-0005 is next available [valid: 2026-05-11]
- `.claude/dev/active/post-impl-adversarial-review/` — task home directory [valid: 2026-05-11]

## Configuration

### Environment Variables

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `AA_MA_HOOKS_DISABLE` | unset | no | Master kill switch. When `=1`, disables ALL AA-MA hooks including the new `security-static-check.sh` and §6.8 enforcement. Existing variable, reused. [valid: 2026-05-11] |
| `AA_MA_AUDIT_BUDGET` | unset | no | Phase 6.8 budget escape valve. Accepted values: `low` (sequential agent dispatch) and `off` (skip §6.8 entirely, logged to provenance.log). Introduced by this plan. [valid: 2026-05-11] |
| `AA_MA_PLAN_MARKER_DEBUG` | unset | no | Pre-existing tracing flag for `/aa-ma-plan` phase-marker hook. Listed for cross-reference only. [valid: 2026-05-11] |

### Config Files

- `pyproject.toml`:
  - `version`: `0.7.0` → `0.8.0` via `cz bump` (NOT manual edit per L-003)
- `scripts/install.sh`:
  - Symlink registry — must add `security-static-check.sh`, `verify-impl/`, 5 agents, `impl-review-template.md`

## Dependencies

| Package | Version | Class | Purpose |
|---------|---------|-------|---------|
| `commitizen` | `>= 3.0` | Required | cz bump for version + CHANGELOG (already installed) [valid: 2026-05-11] |
| `uv` | `>= 0.7` | Required | Runs pytest + ruff (already installed) [valid: 2026-05-11] |
| `bats-core` | system pkg | Dev-only | Required to run `tests/hooks/*.bats` locally — install via `sudo apt-get install -y bats` [valid: 2026-05-11] |
| `shellcheck` | system pkg | Dev-only | Validates hook scripts [valid: 2026-05-11] |
| `Skill(prototype)` | ADR-0003 | Required | M4 prototype phase (LOGIC branch) [valid: 2026-05-11] |
| Existing `aa-ma-validator` agent | n/a | Required | M5 reuses for Tier 2 content checks [valid: 2026-05-11] |
| Existing `Skill(plan-verification)` | n/a | Required | M3 extends Angle 6 [valid: 2026-05-11] |
| Existing `Skill(impact-analysis)` | n/a | Required | §6.8 invokes before user approval [valid: 2026-05-11] |

## Constants

| Constant | Value | Context |
|----------|-------|---------|
| Version target (current) | `0.7.0` | `pyproject.toml` source-of-truth [valid: 2026-05-11] |
| Version target (post-M6) | `0.8.0` | Cut via `cz bump` in M6 [valid: 2026-05-11] |
| ADR number | `0005` | Next available; `ls docs/adr/` shows 0001-0004 [valid: 2026-05-11] |
| §6.8 insertion range (milestone cmd) | L-481 → L-559 | `execute-aa-ma-milestone.md`: §6.7 at line 481, §7.1 at line 559 [valid: 2026-05-11] |
| Total effort | 26h | Sum across 6 milestones [valid: 2026-05-11] |
| HIGH-COMPLEXITY threshold | `>= 80%` | Engineering-standards convention; M4 and M5 flagged [valid: 2026-05-11] |
| Token-budget per milestone close (est.) | 100-200k | Falsifier for assumption #4; if exceeded, `AA_MA_AUDIT_BUDGET=low` forces sequential mode [valid: 2026-05-11] |

## Canonical Enums

### `Audit-Profile`
Plan-declared per milestone; drives Phase 6.8 agent dispatch.

| Value | Meaning |
|-------|---------|
| `full` | Dispatch all 5 audit agents [valid: 2026-05-11] |
| `code-only` | Code-reviewer + security-auditor + tdd-sequence-auditor [valid: 2026-05-11] |
| `docs-only` | future-proofing-auditor only [valid: 2026-05-11] |
| `infra` | code-reviewer + security-auditor (no TDD check; infra rarely has tests) [valid: 2026-05-11] |
| `custom` | Plan declares explicit agent list inline [valid: 2026-05-11] |

### `TDD-Waiver`
Optional per-task field; bypasses tdd-sequence-auditor when canonical value supplied. New values require plan + ADR.

| Value | Meaning |
|-------|---------|
| `refactor` | No behavior change; existing tests cover the surface [valid: 2026-05-11] |
| `docs-only` | No code touched [valid: 2026-05-11] |
| `prototype` | Throwaway POC under `Skill(prototype)` [valid: 2026-05-11] |
| `hotfix-emergency` | Time-critical fix; test-debt logged for follow-up [valid: 2026-05-11] |
| `tooling-config` | Build, lint, or formatter configuration only [valid: 2026-05-11] |

### `Critical-Path` (pre-existing — listed for cross-reference)
Defined in `claude-code/rules/engineering-standards.md` Theme 1.

| Value | Applies to |
|-------|-----------|
| `auth-flow` | Authentication, authorization, session, token handling [valid: 2026-05-11] |
| `data-xform` | Data transformations, schema migrations, format conversions [valid: 2026-05-11] |
| `external-api` | Third-party API calls (rate limits, error handling, contract surface) [valid: 2026-05-11] |
| `version-pipeline` | Release, version-bump, tag-and-push, CHANGELOG mechanics [valid: 2026-05-11] |
| `doc-count-drift` | Hardcoded counts in docs (Tier 6 detector domain) [valid: 2026-05-11] |
| `hook-modification` | Changes to `claude-code/hooks/*.sh` (affect all sessions) [valid: 2026-05-11] |

## Hook Patterns to Mirror

- `aa-ma-commit-drift.sh` — post-commit advisory pattern; reference for non-blocking detector design [valid: 2026-05-11]
- `aa-ma-commit-signature.sh` — PreToolUse exit-2 pattern; reference for HARD gate refusal mechanics [valid: 2026-05-11]

## Lessons in Scope

Lessons applied during plan authoring; regression tests in M4 verify the new auditors would have caught them:

| Lesson ID | Pattern | Where regression-tested |
|-----------|---------|------------------------|
| L-001 | External URL first principle → Context7 evidence | context7-evidence-auditor scope (Branch 7b) [valid: 2026-05-11] |
| L-002 | (referenced via grilling Q1-Q7b) | context-log.md decision history [valid: 2026-05-11] |
| L-003 | Never manually edit `cz bump` headings | M6 CHANGELOG protocol [valid: 2026-05-11] |
| L-005 | KISS violation: two-mechanism `install.sh` | code-reviewer "mechanism duplication" check (Test 8) [valid: 2026-05-11] |
| L-006 | Schema-breaking output regression (CHANGELOG prose stripped) | code-reviewer "schema-breaking output" check (Test 9); M6 post-bump verify [valid: 2026-05-11] |
| L-007 | Out-of-scope drift (diff outside Required Artefacts) | code-reviewer "scope discipline" check (Test 10) [valid: 2026-05-11] |

## Schema Definitions

### Phase 6.8 Audit Finding Output (agent-emitted)

Each of the 5 audit agents emits findings conforming to this shape. Schema defined by M4.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `severity` | enum | yes | One of `CRITICAL`, `WARNING`, `INFO` |
| `file` | string | yes | Affected file path |
| `line` | integer | no | Line number if applicable |
| `impact` | string | yes | What the issue affects |
| `fix` | string | yes | Suggested remediation |
| `agent` | string | yes | Emitting agent name |

> INCOMPLETE — finalized field set is decided in M4 prototype phase; verify against `docs/templates/impl-review-template.md` once written.

## External References

- AA-MA Specification: `docs/spec/aa-ma-specification.md`
- Engineering Standards (canonical themes): `claude-code/rules/engineering-standards.md`
- AA-MA Operational Rules: `claude-code/rules/aa-ma.md`
- ADR-0001 (engineering-standards-architecture): `docs/adr/0001-engineering-standards-architecture.md`
- ADR-0003 (prototype-adoption): `docs/adr/0003-prototype-adoption.md`
- Lessons archive: `docs/lessons.md`

## Glossary

| Term | Definition |
|------|-----------|
| Phase 6.8 | Post-Impl Adversarial Review — new phase in `/execute-aa-ma-milestone` between §6.7 (Engineering Standards HARD Gate) and §7 (Finalization). Mirrors `/verify-plan` but runs post-implementation. |
| `Audit-Profile` | Plan-declared per-milestone field controlling which subset of the 5 audit agents fire in §6.8. |
| `TDD-Waiver` | Optional per-task field bypassing tdd-sequence-auditor with a canonical-enum reason. |
| Grandfathering | Backwards-compat mechanism using `Created:` front-matter date: plans created before v0.8.0 release date skip §6.8 entirely. Mirrors v0.5.0 element #12 precedent. |
| Override panel | `AskUserQuestion`-driven accept/dispute/defer prompt fired when any §6.8 agent emits CRITICAL severity. |

---
