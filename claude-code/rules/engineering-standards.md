# Engineering Standards (auto-loaded)

How AA-MA plans are authored and executed: principles only; procedures live in the skills
(`Skill(plan-verification)`, `Skill(impact-analysis)`, `/execute-aa-ma-milestone`).
Companions: [`aa-ma.md`](aa-ma.md), [`coding-standards.md`](coding-standards.md); rationale ADR-0001.
A plan declares which of the 6 themes below apply (plan element #12).

### 1. Verification & Truth

- Code and git history are the single source of truth — never assume behavior
  without reading the actual implementation.
- Test empirically — validate with running code and live API/tool calls before
  drawing conclusions. The output of an in-memory model of the system does not
  count as evidence.
- Prototype first on uncertain changes. When a task carries `Prototype-Required: YES`,
  use `Skill(prototype)` (ADR-0003; the result lives on a `prototype/<name>` branch), then
  write `[ts] PROTOTYPE — <milestone heading> — <verdict> — verdict-changes-plan: YES|NO`
  to `provenance.log` before milestone COMPLETE; `YES` triggers a `Skill(plan-verification)`
  Angle-3 check. A sub-step's `YES` rolls up to its milestone (ADR-0011). A UI throwaway
  route stays behind the app's auth and reads stubs or fixtures, never live records.
- Double-check critical paths. When a task carries `Critical-Path: <value>`,
  write a `[ts] CRITICAL_PATH_REVIEW — <evidence>` entry to `provenance.log`
  before milestone COMPLETE.
- **References are three-valued, not binary.** A name invoked from shipped
  plugin content is **on disk** (shipped by this repo), **declared-external**
  (resolvable in `~/.claude/skills`, gstack, or another ecosystem — a
  legitimate cross-ecosystem edge), or **dangling** (resolvable nowhere).
  Only *dangling* is a defect; an external dependency is declared, not silently
  tolerated. The plugin-surface extractor classifies all three against an explicit
  allowlist; the live split is regenerated (`docs/architecture/plugin-surface.md`), and
  the 2026-09-22 measurement that motivated the rule is in
  `docs/research/diagram-generation-plugin-surface-extraction.md`.

**Critical-Path canonical values** (novel values are rejected; add one via plan + ADR):

| Value              | Applies to                                                          |
|--------------------|---------------------------------------------------------------------|
| `auth-flow`        | Authentication, authorization, session, token handling              |
| `data-xform`       | Data transformations, schema migrations, format conversions         |
| `external-api`     | Third-party API calls (rate limits, error handling, contract surface) |
| `version-pipeline` | Release, version-bump, tag-and-push, CHANGELOG mechanics — `scripts/release.sh`, `VERSION` |
| `doc-count-drift`  | Hardcoded counts in docs (Tier 6 detector domain)                   |
| `hook-modification`| Changes to the shipped enforcement surface: `claude-code/hooks/**` (incl. `lib/`), the CI workflows `.github/workflows/**`, the gate/scan logic inside `claude-code/skills/**` (`claude-code/skills/execute-aa-ma-*/**`, `claude-code/skills/sole-dev-merge/**`), and the Python the gate reads — `src/aa_ma/{gate,enforce,grammar,plan_parsers}.py` (ADR-0009) (affect all sessions); also `src/aa_ma/{impact,gitutil}.py`, `scripts/check_conventions.py`, `scripts/{install,uninstall,lib/aa-ma-install-lib}.sh`, `.pre-commit-config.yaml`, `.gitleaksignore`, `.github/dependabot.yml` |

§6.7 fence 4 derives these values from a milestone's changed files (`aa_ma.plan_parsers.CRITICAL_PATH_GLOBS`,
equal to this table by test): each derived value needs a `CRITICAL_PATH_REVIEW` naming its files (ADR-0027).

**Diagram-Waiver canonical values** (plan front-matter, read at planning time only;
novel values are rejected):

| Value          | Meaning                                                                  |
|----------------|--------------------------------------------------------------------------|
| `none`         | Architecture View present (default when the field is absent)             |
| `docs-only`    | No milestone touches `src/`, `claude-code/hooks/`, or CI                  |
| `config-only`  | `pyproject.toml` / CI / dotfiles only                                     |
| `single-file`  | Exactly one non-test file changes; a diagram would have one node          |

A waiver is invalid when any milestone declares `Audit-Profile ∈ {full, code-only, infra}`.

### 2. Development Principles

<!-- BEGIN GENERATED tdd-waivers: from src/aa_ma/plan_parsers.py TDD_WAIVER_RULES; regenerate with scripts/regen-generated.sh -->
- **TDD** — write failing tests before implementation; cover happy path, edge
  cases, regressions. A milestone skips the test-first sequence only with a
  canonical `TDD-Waiver:` value:
  - `docs-only` — no `src/` touched (also auto-detected).
  - `hotfix-emergency` — a production incident; requires a follow-up test task.
  - `prototype` — `Prototype-Required: YES` is set; `Skill(prototype)` governs.
  - `refactor` — behaviour-preserving; the existing tests must stay green.
  - `tooling-config` — `pyproject.toml`, CI config or a Dockerfile only.
<!-- END GENERATED tdd-waivers -->
- **KISS, DRY, YAGNI, SoC, SOLID**, the testing floor and the conflict policy:
  [`coding-standards.md`](coding-standards.md).

### 3. Reasoning & Planning

- **First principles and Socratic questioning** — challenge inherited assumptions;
  surface hidden dependencies (`Skill(first-principles-framework)` if available).
- **Skill assessment** — list the skills that should fire, and why, in `context-log.md`.
- **Strategic subagent use** — delegate bounded specialist work; record dispatches in
  `provenance.log`.

### 4. Safety & Continuity

- **Non-breaking constraint** — changes preserve existing behaviour unless the change
  is intended; verified at the milestone gate (`Skill(impact-analysis)`, fence 4).
- **Apply lessons learned; avoid repeated mistakes** — `/aa-ma-plan` Phase 1 scans
  `docs/lessons.md`, fix/revert history and recent context-logs; the plan declares
  their relevance in element #12.
- **Diagram maintenance is part of the change** — when a step changes a file
  named in the Architecture View, update the View in the same commit
  (`aa-ma-lint-views` reports stale paths and phantom edges; ADR-0015).
- **Incremental validation** — verify each step before the next; the advisory
  `aa-ma-commit-drift.sh` hook flags code/artifact drift after each commit.

### 5. Execution Checklist

Before COMPLETE, the agent self-reports against this checklist (Tier = milestone enforcement):

| Item                                            | Tier | Verification                                                            |
|-------------------------------------------------|------|-------------------------------------------------------------------------|
| Implementation tested with running code/API     | HARD | `provenance.log` shows live execution evidence                          |
| Tests written and passing                       | HARD | §6.7 fence 3 runs `Test-Command:` and records `TESTS_VERIFIED — <milestone heading> — passed=N` in `provenance.log` (ADR-0023) |
| Non-breaking constraint verified                | HARD | §6.7 fence 4 computes `IMPACT_VERIFIED — <milestone heading> — … unexplained=0 api_diff=…` (plans `Created:` ≥ `IMPACT_CUTOVER`, ADR-0027); `Skill(impact-analysis)` at §6.3 for callers |
| AA-MA artifacts in sync; git clean              | HARD | `git status` clean for AA-MA files; zero `Status: PENDING` in milestone |
| `Critical-Path:` evidence (when field present)  | HARD | `CRITICAL_PATH_REVIEW` entry in `provenance.log`                        |
| `Prototype-Required:` evidence (when YES)       | HARD | `PROTOTYPE — <milestone heading> — <verdict> — verdict-changes-plan: YES\|NO` entry in `provenance.log` |
| `@kind` sigil edges verified (when §13 carries any) | HARD | §6.7 diagram fence passes; it records `DIAGRAM_VERIFIED — <milestone heading> — edges=N checked=C phantom=0 unknown=K` in `provenance.log` (ADR-0015) |
| No assumptions left unvalidated                 | SOFT | Declared in `context-log.md`                                            |
| Relevant skills/subagents consulted             | SOFT | `provenance.log` shows skill invocations                                |
| Changes reviewed against past mistakes          | SOFT | Declared in plan element #12                                            |

An absent `Critical-Path:` or `Prototype-Required:`, or a §13 with no sigil edge, skips
that HARD check; only a field present without its evidence refuses.

### 6. Sync & Commit Discipline

- [`aa-ma.md`](aa-ma.md) owns the Sub-Step Sync Rule and the Commit Signature; the HARD
  gate refuses COMPLETE while AA-MA files are dirty or a sub-step is PENDING.

## Opt-out

`AA_MA_HOOKS_DISABLE=1` disables all AA-MA hooks and gate enforcement. Deleting a
`~/.claude/rules/*.md` symlink stops that rule auto-loading; a project's own rule copy
takes precedence. Details: `docs/spec/aa-ma-specification.md` §XI element 12.
