# Engineering Standards (auto-loaded)

Doctrine governing how AA-MA plans are authored and executed in this plugin.
Principles only — procedures live in skills (`Skill(operational-constraints)`,
`Skill(plan-verification)`, `Skill(impact-analysis)`) and commands (`/aa-ma-plan`,
`/execute-aa-ma-step`, `/execute-aa-ma-milestone`). Companion rule:
[`aa-ma.md`](aa-ma.md). Architectural rationale: ADR-0001
([`docs/adr/0001-engineering-standards-architecture.md`](../../docs/adr/0001-engineering-standards-architecture.md)).

The 6 themes below are referenced by name in plan element #12
("Engineering Standards Declaration"). A plan must declare which themes
materially apply to its work and how.

### 1. Verification & Truth

- Code and git history are the single source of truth — never assume behavior
  without reading the actual implementation.
- Test empirically — validate with running code and live API/tool calls before
  drawing conclusions. The output of an in-memory model of the system does not
  count as evidence.
- Prototype first on uncertain changes. Throwaway proofs-of-concept are cheap;
  shipping the wrong abstraction is expensive. When a task carries
  `Prototype-Required: YES`, invoke `Skill(prototype)` (forked from
  mattpocock/skills — see [ADR-0003](../../docs/adr/0003-prototype-adoption.md))
  which routes between **LOGIC** (terminal TUI for state/business-logic
  questions, fully cross-language) and **UI** (web-frontend variants
  switchable via `?variant=` URL search param) branches based on the question.
  Then write a `[ts] PROTOTYPE — <verdict>` entry to `provenance.log` before
  milestone COMPLETE. The skill provides the *how*; this rule provides the
  *when* — both must align before the gate (Section 6.7 condition 5) accepts
  evidence.
- Double-check critical paths. When a task carries `Critical-Path: <value>`,
  write a `[ts] CRITICAL_PATH_REVIEW — <evidence>` entry to `provenance.log`
  before milestone COMPLETE.

**Critical-Path canonical values** (the only accepted values; novel values are
rejected by `Skill(plan-verification)`. Add new values via plan + ADR.):

| Value              | Applies to                                                          |
|--------------------|---------------------------------------------------------------------|
| `auth-flow`        | Authentication, authorization, session, token handling              |
| `data-xform`       | Data transformations, schema migrations, format conversions         |
| `external-api`     | Third-party API calls (rate limits, error handling, contract surface) |
| `version-pipeline` | Release, version-bump, tag-and-push, CHANGELOG mechanics            |
| `doc-count-drift`  | Hardcoded counts in docs (Tier 6 detector domain)                   |
| `hook-modification`| Changes to `claude-code/hooks/*.sh` (affect all sessions)           |

### 2. Development Principles

- **TDD** — write failing tests before implementation; cover happy path, edge
  cases, regressions. Skip only for docs-only, config-only, or
  infrastructure-only milestones.
- **KISS** — simple, obvious solutions by default; complexity requires
  justification recorded in `context-log.md`.
- **DRY** — extract shared logic; document why duplication is intentional when
  it is.
- **SOLID** — single responsibility per module; depend on abstractions; favor
  composition over inheritance.
- **SOC** — separate business logic, data access, API integration, and
  presentation concerns.

### 3. Reasoning & Planning

- **First-principles thinking** — break problems to fundamental truths; challenge
  inherited assumptions. (Invoke `Skill(first-principles-framework)` if
  available in your environment.)
- **Socratic questioning** — repeated "why?"; surface hidden dependencies and
  false constraints.
- **Skill assessment** — before implementing, list which skills should fire and
  why. Record decisions in `context-log.md`.
- **Strategic subagent use** — delegate bounded specialist work (security audit,
  test generation, code review). Record dispatches in `provenance.log`.

### 4. Safety & Continuity

- **Non-breaking constraint** — changes preserve existing behavior unless the
  change is explicitly intended. Verified at milestone HARD gate via
  `Skill(impact-analysis)`.
- **Apply lessons learned** — Phase 1 of `/aa-ma-plan` runs an inline lessons
  scan: `docs/lessons.md` (if present) + `git log --grep="revert\|fix\|hotfix"`
  (last 6 months) + top-3 most-recent completed `context-log.md` files.
  Hard 30s timeout via `timeout 30s ...`; on timeout, emit notice and continue
  without scan results.
- **Avoid repeated mistakes** — same scan; declare relevance in element #12 of
  the plan output.
- **Incremental validation** — verify each step before proceeding. The
  `aa-ma-commit-drift.sh` post-commit hook (advisory) flags drift between code
  and AA-MA artifacts; the milestone HARD gate refuses COMPLETE while git is
  dirty or any `Status: PENDING` remains within the milestone.

### 5. Execution Checklist

Per task, before flipping to COMPLETE, the agent self-reports against this
checklist. The HARD/SOFT column indicates milestone-level enforcement:

| Item                                            | Tier | Verification                                                            |
|-------------------------------------------------|------|-------------------------------------------------------------------------|
| Implementation tested with running code/API     | HARD | `provenance.log` shows live execution evidence                          |
| Tests written and passing                       | HARD | `uv run pytest` exit 0 (or project equivalent)                          |
| Non-breaking constraint verified                | HARD | `Skill(impact-analysis)` run; tests still pass                          |
| AA-MA artifacts in sync; git clean              | HARD | `git status` clean for AA-MA files; zero `Status: PENDING` in milestone |
| `Critical-Path:` evidence (when field present)  | HARD | `CRITICAL_PATH_REVIEW` entry in `provenance.log`                        |
| `Prototype-Required:` evidence (when YES)       | HARD | `PROTOTYPE — <verdict>` entry in `provenance.log`                       |
| No assumptions left unvalidated                 | SOFT | Declared in `context-log.md`                                            |
| Relevant skills/subagents consulted             | SOFT | `provenance.log` shows skill invocations                                |
| Changes reviewed against past mistakes          | SOFT | Declared in plan element #12                                            |

When `Critical-Path:` or `Prototype-Required:` is **absent** from a task, the
corresponding HARD check is skipped (no failure). Only present-but-without-
evidence triggers a refusal — preserves backward-compatibility with plans
authored before v0.5.0.

### 6. Sync & Commit Discipline

- **Sub-step sync rule** (L-080–L-082, see [`aa-ma.md`](aa-ma.md) lines 47-66) —
  write `Status: COMPLETE` and a concrete `Result Log:` immediately per
  sub-step. Never batch updates to "end of milestone".
- **Milestone HARD gate** refuses to mark COMPLETE while git is dirty for AA-MA
  files or while any `Status: PENDING` remains within the milestone. Pre-COMPLETE
  refusal complements the post-commit `aa-ma-commit-drift.sh` hook (advisory,
  always exits 0).
- **Conventional Commits** with `[AA-MA Plan]` footer when a plan is active —
  see [`aa-ma.md`](aa-ma.md) "Commit Signature" section.

**See also:** [`aa-ma.md`](aa-ma.md); ADR-0001; doc-drift Tier 6 detector.

## Opt-out

These standards are opinionated. The plugin ships them as defaults to encourage
discipline; consumers may opt out at any layer:

- **Master kill switch:** `export AA_MA_HOOKS_DISABLE=1` disables all AA-MA
  hooks and gate enforcement (the same env var that already controls
  `aa-ma-commit-drift.sh` and the milestone HARD gate's Engineering Standards
  Section 6.7).
- **Per-rule removal:** delete the symlink at `~/.claude/rules/engineering-standards.md`
  (created by `scripts/install.sh`) to stop auto-loading this rule on session
  start. The plan-verification structural check still runs on `Created:`
  on-or-after v0.5.0 plans; remove the engineering-standards section from
  `claude-code/skills/plan-verification/SKILL.md` Angle 6 to fully disable.
- **Project-local override:** projects with their own `claude-code/rules/`
  may ship a stricter or laxer engineering-standards.md; the project-local
  copy takes precedence over the plugin-shipped one when both are loaded.

Pre-v0.5.0 plans are grandfathered automatically (no opt-out needed) — see
the grandfathering note in [`aa-ma.md`](aa-ma.md) Planning Standard section.
