# understand-codebase-skill Plan

**Objective:** Vendor the ad-hoc `~/.claude/` `understand-codebase` skill, its 4 `codebase-onboarding-*` worker agents, and the `/understand-codebase` command into `aa-ma-forge/claude-code/` so they become official, maintained, install-deployed, tested, CI-covered, semver-versioned ecosystem components.
**Owner:** AI + Stephen Newhouse
**Created:** 2026-05-12
**Last Updated:** 2026-05-12

## Executive Summary

Move the `understand-codebase` skill (SKILL.md + `references/`×9 + `templates/`×1), the 4 `codebase-onboarding-*` agents, and the `/understand-codebase` command verbatim into `aa-ma-forge/claude-code/`; normalize agent frontmatter; re-run `install.sh` (auto-discovers + backs up the originals); pin everything with frontmatter/structure tests; write ADR-0006 and reconcile all asset counts (CLAUDE.md, SECURITY.md, claude-code-foundations.md, aa-ma-quick-reference.md, CHANGELOG.md); commit + push behind the milestone HARD gate. Success = `install.sh --dry-run` shows the backup plan, post-install the 6 `~/.claude/` targets are symlinks into the repo, full `uv run pytest`/ruff/bats green, counts consistent everywhere (10 cmds / 18 skills / 11 agents), ADR-0006 + INDEX row present, HARD-gate approval recorded, branch committed + pushed with the `[AA-MA Plan]` footer.

## Target Audience

- **aa-ma-forge maintainers:** get a single maintained source of truth for the onboarding skill — versioned, tested, CI-covered — replacing loose untracked `~/.claude/` copies.
- **Plugin users (anyone who runs `scripts/install.sh`):** `/understand-codebase` deploys automatically; existing real `~/.claude/` copies are backed up, not clobbered; the skill degrades gracefully when optional cross-plugin tools are absent.
- **Future contributors:** ADR-0006 records the cross-plugin soft-dependency posture so the dependency surface is documented, not surprising.

## Context

The `understand-codebase` skill, its 4 worker agents (`codebase-onboarding-conventions|health|runbook|synthesizer`), and the `/understand-codebase` command were built ad-hoc directly inside `~/.claude/` (real files, created 2026-05-12). They have no maintained home: no version, no tests, no CI, no ADR, not symlinked from any repo. We want them to become **official, maintained components of the AA-MA Forge ecosystem** — vendored into the `aa-ma-forge` repo so `scripts/install.sh` deploys them, `pytest` pins them, CI sees them, and `python-semantic-release` versions them. Intended outcome: the loose `~/.claude/` files are replaced by symlinks into `aa-ma-forge/claude-code/`, with the originals backed up by `install.sh`.

**User-confirmed decisions:**
1. Branch name: `feature/understand-codebase-skill`.
2. Vendor **as-is** — keep the skill's references to tools aa-ma-forge does *not* ship (`/index`, `/codebase-deep-dive`, `gsd-map-codebase`/`gsd-scan`/`gsd-intel`, `gsd-codebase-mapper`, `code-intelligence`, `doc-drift-detection`, `improve-codebase-architecture`, `~/.claude-code-project-index/scripts/project_index.py`). The skill already **degrades gracefully** ("if any reused tool/agent is missing → skip, note in Provenance, never hard-fail"). **ADR-0006** documents this cross-plugin soft-dependency posture. (aa-ma-forge *does* already ship the in-repo pieces it uses: `agent-teams`, `impact-analysis`, `system-mapping`, `code-reviewer`, `/aa-ma-plan`.)
3. `docs/spec/claude-code-foundations.md` — **reconcile its asset tables fully** to current+new reality (agent table is frozen pre-v0.8.0 at 2 agents; reality after this work = 11 agents / 18 skills / 10 commands). Incidentally fixes the pre-existing v0.8.0 drift.

## Implementation Steps

This plan satisfies all 12 AA-MA planning elements. Sections 1–12 below mirror the approved plan.

### 1. Executive summary

Move the `understand-codebase` skill (SKILL.md + `references/`×9 + `templates/`×1), the 4 `codebase-onboarding-*` agents, and the `/understand-codebase` command verbatim into `aa-ma-forge/claude-code/`; normalize agent frontmatter; re-run `install.sh` (auto-discovers + backs up the originals); pin everything with frontmatter/structure tests; write ADR-0006 and reconcile all asset counts (CLAUDE.md, SECURITY.md, claude-code-foundations.md, aa-ma-quick-reference.md, CHANGELOG.md); commit + push behind the milestone HARD gate.

### 2. Stepwise implementation plan (by milestone)

#### Milestone 1 — Vendor & wire — `Gate: SOFT`

- **Goal:** 11 skill files under `claude-code/skills/understand-codebase/` + 4 agents in `claude-code/agents/` + 1 command in `claude-code/commands/`; `install.sh --dry-run` shows the backup plan; post-install the 6 `~/.claude/` targets are symlinks into the repo; `~/.claude/backups/aa-ma-forge-<ts>/` holds the originals.
- **Effort:** ~1.5 h. **Complexity:** ~30%. **Mode:** mixed (1.1–1.4, 1.6 AFK; 1.5 HITL). **Gate:** SOFT.
- **Baseline:** N/A — pure local code, no API exercised (file moves + `install.sh` symlink deployment, verified with `readlink`/`[ -L ]` and `ls ~/.claude/backups/`).

- **1.1** *(AFK)* `git checkout main && git pull` (already current), then `git checkout -b feature/understand-codebase-skill`. **← first execution action.**
- **1.2** *(AFK)* Copy `~/.claude/skills/understand-codebase/` (whole dir — `SKILL.md`, `references/`×9, `templates/onboarding-team.md`) → `claude-code/skills/understand-codebase/`. Prepend a one-line provenance comment to `SKILL.md`: `<!-- Maintained in aa-ma-forge as of v<next> — see docs/adr/0006-understand-codebase-adoption.md -->` (mirrors the forked-skills convention; "maintained", not "forked", since this is original work).
- **1.3** *(AFK)* Copy `~/.claude/agents/codebase-onboarding-{conventions,health,runbook,synthesizer}.md` → `claude-code/agents/`. **Normalize frontmatter to aa-ma-forge convention**: each must have `name:` (== filename stem), `description:`, and `tools:` as a comma-separated string. If a file lacks `tools:`, add one derived from the agent body (e.g. `tools: Read, Glob, Grep, Bash, Write`). Keep the `>-` block-scalar descriptions as-is.
- **1.4** *(AFK)* Copy `~/.claude/commands/understand-codebase.md` → `claude-code/commands/` (keep its `argument-hint:` frontmatter key — Claude Code supports it).
- **1.5** *(HITL)* `scripts/install.sh --dry-run` → review: confirm it would back up the 6 existing real files (skill dir + 4 agents + command) to `~/.claude/backups/aa-ma-forge-<ts>/` and then symlink them. **User reviews dry-run output**, then `scripts/install.sh` for real.
- **1.6** *(AFK)* Verify: `readlink ~/.claude/skills/understand-codebase` points into `…/aa-ma-forge/claude-code/skills/`; `~/.claude/commands/understand-codebase.md` and the 4 agent files are symlinks; `ls ~/.claude/backups/aa-ma-forge-*/` shows the backed-up originals.

**Acceptance Criteria (M1):**
- `test -f claude-code/skills/understand-codebase/SKILL.md && [ "$(ls claude-code/skills/understand-codebase/references/ | wc -l)" -eq 9 ]` true; `claude-code/skills/understand-codebase/templates/` has exactly 1 file.
- All 4 `claude-code/agents/codebase-onboarding-{conventions,health,runbook,synthesizer}.md` exist; each `grep -q '^tools:'` succeeds; each `grep -q "^name: codebase-onboarding-"` matches its filename stem.
- `claude-code/commands/understand-codebase.md` exists.
- `[ -L ~/.claude/skills/understand-codebase ]` true and `readlink ~/.claude/skills/understand-codebase` contains `aa-ma-forge`; the 4 agent symlinks + command symlink all resolve into the repo.
- `ls ~/.claude/backups/aa-ma-forge-*/` lists the backed-up originals (skill dir + 4 agents + command).

**Required Artefacts (M1):** `claude-code/skills/understand-codebase/` (11 files), `claude-code/agents/codebase-onboarding-{conventions,health,runbook,synthesizer}.md` (4), `claude-code/commands/understand-codebase.md` (1).

**Tests (M1):** `scripts/install.sh --dry-run` (manual review) → `scripts/install.sh` → `readlink`/`[ -L ]` symlink checks → `ls ~/.claude/backups/aa-ma-forge-*`.

**Rollback Strategy (M1):** `git restore` the new `claude-code/` files; `scripts/uninstall.sh` restores backups from `~/.claude/backups/`. No DB, no released artifact.

**Risks (M1):**
1. Frontmatter format mismatch → skill/agent fails to load → normalize in 1.3, prove in M2.
2. `install.sh` clobbers the user's working `~/.claude/` files → `--dry-run` reviewed first (1.5); backup logic exercised by `scripts/install.sh` lines 157–186; `scripts/uninstall.sh` restores.
3. The skill dir's `references/…` relative links break after the move → they're relative to the skill dir, which moves wholesale; 3.7 cross-ref grep confirms.

---

#### Milestone 2 — Pin with tests — `Gate: SOFT`

- **Goal:** New tests in `tests/skills/`, `tests/agents/`, `tests/commands/` (+ optional `tests/assets/`) all pass; full `uv run pytest` green (no regressions).
- **Effort:** ~1.5 h. **Complexity:** ~35%. **Mode:** AFK. **Gate:** SOFT.
- **Baseline:** N/A — pure local code, no API exercised (pytest assertions over vendored asset files).

- **2.1** *(AFK)* `tests/skills/test_understand_codebase_frontmatter.py` — reuse `tests/skills/_helpers.py`: `name == "understand-codebase"`; `description` non-empty + contains `onboard`/`ONBOARDING.md`/`AGENTS.md`; `allowed-tools` is a non-empty list; every `references/*.md` + `templates/*.md` file named in `SKILL.md` exists on disk and is > 1 KB (the 10 companions).
- **2.2** *(AFK)* `tests/agents/__init__.py` + `tests/agents/test_codebase_onboarding_agents.py` — parametrized over the 4 agent names: file exists; frontmatter opens/closes with `---`; has `name` (== filename stem), `description` (non-empty), `tools` (non-empty); `claude-code/skills/understand-codebase/SKILL.md` and `…/templates/onboarding-team.md` reference all 4 via `subagent_type=`.
- **2.3** *(AFK)* `tests/commands/test_understand_codebase_command.py` — frontmatter `name == "understand-codebase"`; body contains `Skill(understand-codebase)`; mentions `--quick`/`--standard`/`--deep`.
- **2.4** *(AFK, stretch)* `tests/assets/test_understand_codebase_xrefs.py` — assert in-repo composed assets exist (`claude-code/skills/{agent-teams,impact-analysis,system-mapping}/SKILL.md`, `claude-code/commands/aa-ma-plan.md`, `claude-code/agents/code-reviewer.md`); assert SKILL.md's `references/…`/`templates/…` relative links all resolve. (Documents the boundary; skip if time-boxed.)
- Run `uv run pytest tests/skills tests/agents tests/commands -q` then full `uv run pytest`.

**Acceptance Criteria (M2):**
- `uv run pytest tests/skills/test_understand_codebase_frontmatter.py tests/agents tests/commands/test_understand_codebase_command.py -q` exit 0.
- Full `uv run pytest` exit 0 — no regressions.
- `tests/agents/__init__.py` exists (so the new dir is collected by the default pytest run).

**Required Artefacts (M2):** `tests/skills/test_understand_codebase_frontmatter.py`, `tests/agents/__init__.py`, `tests/agents/test_codebase_onboarding_agents.py`, `tests/commands/test_understand_codebase_command.py`, *(stretch)* `tests/assets/test_understand_codebase_xrefs.py`.

**Tests (M2):** `uv run pytest tests/skills tests/agents tests/commands -q`; then full `uv run pytest`.

**Rollback Strategy (M2):** `git restore` the new test files. No side effects.

**Risks (M2):**
1. Tests too brittle (pin prose that'll churn) → pin frontmatter/structure/file-existence, never body prose.
2. `tests/agents/` not picked up by pytest → add `__init__.py`, mirror `tests/skills/` layout; default `pytest` runs it (not `perf`/`slow`-marked).
3. The 4 agents lack `tools:` → 2.2 fails → 1.3 adds `tools:` before tests are written.

---

#### Milestone 3 — Document, reconcile counts, ship — `Gate: HARD` · `Audit-Profile: custom: code-reviewer, future-proofing-auditor`

- **Goal:** `docs/adr/0006-*.md` + INDEX row exist; counts consistent across CLAUDE.md / SECURITY.md / claude-code-foundations.md / aa-ma-quick-reference.md (all read 10 cmds / 18 skills / 11 agents); CHANGELOG `[Unreleased]` entry present; `grep -rn` finds no dangling refs; full suite + ruff + bats green; impact-analysis = non-breaking; HARD-gate approval in context-log; branch committed + pushed.
- **Effort:** ~2 h. **Complexity:** ~40% (M3.3 foundations reconcile is the fiddliest piece — bounded, mechanical; no step ≥ 80%). **Mode:** mixed (3.2–3.8 AFK; 3.1, 3.9, 3.10 HITL). **Gate:** HARD. **Audit-Profile:** custom: code-reviewer, future-proofing-auditor.
- **Baseline:** N/A — pure local code, no API exercised (doc edits + grep cross-ref + impact-analysis verdict).

- **3.1** *(HITL)* `docs/adr/0006-understand-codebase-adoption.md` from `docs/adr/TEMPLATE.md` — Status Accepted (→ Implemented once merged, per the 0005 pattern); Context (built ad-hoc in `~/.claude/`, needs a maintained home); Decision Drivers (single source of truth, install.sh auto-discovery, versioned releases, test/CI coverage); Considered Options ([chosen] vendor as-is + document soft-deps / vendor + trim cross-plugin refs / leave external); Decision Outcome + rationale; Pros & Cons; Consequences (+ maintained/tested/released; − aa-ma-forge now names gsd/code-intelligence/codebase-deep-dive/index by reference, mitigated by graceful degradation; ~ install.sh auto-discovers → zero manifest churn); Implementation Notes (cite M1 commit + v<next> tag once known); References (this plan, SKILL.md, ADR-0002/0003/0004). **Add a row to `docs/adr/INDEX.md`.**
- **3.2** *(AFK)* Bump counts (full list in `reference.md`): `CLAUDE.md` Architecture block — commands `9 → 10`, skills `17 → 18`, agents `7 → 11` (rephrase "7 specialized agents (scribe, validator, + 5 verify-impl audit agents)" → "11 specialized agents (scribe, validator, 5 verify-impl audit agents, + 4 codebase-onboarding agents)"). `SECURITY.md` — command list `9 → 10` (add `understand-codebase`); skills list `17 → 18` (add `understand-codebase`); agents list `7 → 11` (add the 4 `codebase-onboarding-*`); update the count words.
- **3.3** *(AFK)* `docs/spec/claude-code-foundations.md` — **reconcile fully**: Commands table → 10 rows (+ `/understand-codebase`); Skills table → 18 rows (+ `understand-codebase`, + any missing since it froze, e.g. `verify-impl`); Agents table → 11 rows (was 2 → add `code-reviewer`, `security-auditor`, `tdd-sequence-auditor`, `context7-evidence-auditor`, `future-proofing-auditor`, `codebase-onboarding-conventions`, `codebase-onboarding-health`, `codebase-onboarding-runbook`, `codebase-onboarding-synthesizer`). Note the incidental v0.8.0-drift fix in the commit body.
- **3.4** *(AFK)* `docs/spec/aa-ma-quick-reference.md` — add `/understand-codebase` to the commands area (~line 98 region).
- **3.5** *(AFK)* `README.md` — check "What's in this repo"/Architecture for hardcoded counts; bump if present; add a brief `/understand-codebase` mention if there's a natural commands list (light touch — README is narrative).
- **3.6** *(AFK)* `CHANGELOG.md` — add `## [Unreleased]` → `### Feat` → "**skills**: vendor `understand-codebase` onboarding skill + 4 `codebase-onboarding-*` worker agents + `/understand-codebase` command into the AA-MA Forge ecosystem; maintained here going forward (ADR-0006)".
- **3.7** *(AFK)* Cross-ref + drift check: `grep -rn 'understand-codebase\|codebase-onboarding' claude-code/ docs/ tests/` → no dangling refs; `Skill(doc-drift-detection)` (or `/doc-sync` report-only) → Tier 1 (versions) + Tier 6 (counts) clean, no NEW drift.
- **3.8** *(AFK)* `uv run pytest` (full default suite) green; `uv run ruff check src/` clean; `bats --recursive tests/hooks/` green (no hook change — sanity).
- **3.9** *(HITL)* `Skill(impact-analysis)` — confirm non-breaking (no `src/` import changes; install.sh auto-discovery → existing installs pick up symlinks live; graceful degradation → shipping standalone is safe). Record in `context-log.md`.
- **3.10** *(HITL)* HARD gate: record user approval in `context-log.md`; commit on `feature/understand-codebase-skill` with conventional message + `[AA-MA Plan] understand-codebase-skill .claude/dev/active/understand-codebase-skill` footer; push. (Phase 6.8 `/verify-impl` applies — `Created: 2026-05-12` > `V080_CUTOVER 2026-05-11` — using `Audit-Profile: custom: code-reviewer, future-proofing-auditor`.)

**Acceptance Criteria (M3):**
- `docs/adr/0006-understand-codebase-adoption.md` exists; `grep -q '0006' docs/adr/INDEX.md` succeeds.
- `grep -rn '\b9 (slash )?command' CLAUDE.md SECURITY.md` returns nothing (all bumped to 10); same for `17 skill`/`7 agent`.
- `claude-code-foundations.md` Commands table has 10 rows, Skills table 18 rows, Agents table 11 rows.
- `grep -q '/understand-codebase' docs/spec/aa-ma-quick-reference.md` succeeds.
- `CHANGELOG.md` contains a `## [Unreleased]` section with a `### Feat` entry naming `understand-codebase`.
- `Skill(doc-drift-detection)` reports 0 NEW Tier-1/Tier-6 findings attributable to this branch.
- `uv run pytest` exit 0; `uv run ruff check src/` exit 0; `bats --recursive tests/hooks/` exit 0.
- `git log -1 --format=%B` ends with the `[AA-MA Plan] understand-codebase-skill .claude/dev/active/understand-codebase-skill` footer; `git status` clean; 0 `Status: PENDING` in M3.
- HARD-gate approval entry present in `context-log.md`; `Skill(impact-analysis)` verdict = non-breaking, recorded in `context-log.md`.

**Required Artefacts (M3):** `docs/adr/0006-understand-codebase-adoption.md`; **modified:** `CLAUDE.md`, `SECURITY.md`, `docs/spec/claude-code-foundations.md`, `docs/spec/aa-ma-quick-reference.md`, `README.md` (if it carries counts), `CHANGELOG.md`, `docs/adr/INDEX.md`.

**Tests (M3):** full `uv run pytest`; `uv run ruff check src/`; `bats --recursive tests/hooks/`; `Skill(doc-drift-detection)` report; `grep -rn 'understand-codebase\|codebase-onboarding' claude-code/ docs/ tests/`; `Skill(impact-analysis)`.

**Rollback Strategy (M3):** `git restore` the modified docs + the new ADR; no released artifact yet (release is a later `cz bump`). Whole-branch rollback = `git checkout main && git branch -D feature/understand-codebase-skill`, then `scripts/uninstall.sh`.

**Risks (M3):**
1. Miss a count location → exactly the stale-count drift CLAUDE.md warns about → enumerate all locations in `reference.md`; run `Skill(doc-drift-detection)` Tier 6 in 3.7.
2. ADR number/INDEX mismatch → 0005 confirmed highest; add INDEX row in the same commit as the ADR.
3. Full foundations-doc reconcile pulls in unrelated churn → scope to the 3 asset tables only; document the incidental v0.8.0-drift fix in the commit body; touch nothing else.

### 3. Milestones with measurable goals

| M | Goal (measurable) |
|---|---|
| M1 | 11 skill files under `claude-code/skills/understand-codebase/` + 4 agents in `claude-code/agents/` + 1 command in `claude-code/commands/`; `install.sh --dry-run` shows the backup plan; post-install the 6 `~/.claude/` targets are symlinks into the repo; `~/.claude/backups/aa-ma-forge-<ts>/` holds the originals. |
| M2 | New tests in `tests/skills/`, `tests/agents/`, `tests/commands/` (+ optional `tests/assets/`) all pass; full `uv run pytest` green (no regressions). |
| M3 | `docs/adr/0006-*.md` + INDEX row exist; counts consistent across CLAUDE.md / SECURITY.md / claude-code-foundations.md / aa-ma-quick-reference.md (all read 10 cmds / 18 skills / 11 agents); CHANGELOG `[Unreleased]` entry present; `grep -rn` finds no dangling refs; full suite + ruff + bats green; impact-analysis = non-breaking; HARD-gate approval in context-log; branch committed + pushed. |

### 4. Acceptance criteria per step

Falsifiable, condensed (full per-step ACs land in `tasks.md`):
- 1.2 → `test -f claude-code/skills/understand-codebase/SKILL.md && ls claude-code/skills/understand-codebase/references/ | wc -l` == 9; `templates/` has 1 file.
- 1.3 → all 4 `claude-code/agents/codebase-onboarding-*.md` exist; each `grep -q '^tools:'` succeeds.
- 1.6 → `[ -L ~/.claude/skills/understand-codebase ]` true; `readlink` contains `aa-ma-forge`.
- 2.1–2.3 → `uv run pytest tests/skills/test_understand_codebase_frontmatter.py tests/agents tests/commands/test_understand_codebase_command.py -q` exit 0.
- 3.1 → `docs/adr/0006-understand-codebase-adoption.md` exists; `grep -q '0006' docs/adr/INDEX.md`.
- 3.2–3.4 → `grep -rn '\b9 (slash )?command' CLAUDE.md SECURITY.md` returns nothing (all bumped to 10); same for `17 skill`/`7 agent`.
- 3.7 → `Skill(doc-drift-detection)` reports 0 NEW Tier-1/Tier-6 findings attributable to this branch.
- 3.8 → `uv run pytest` exit 0; `uv run ruff check src/` exit 0; `bats --recursive tests/hooks/` exit 0.
- 3.10 → `git log -1 --format=%B` ends with the `[AA-MA Plan]` footer; `git status` clean; 0 `Status: PENDING` in M3.

### 5. Required artefacts

- **New (in repo):** `claude-code/skills/understand-codebase/` (11 files), `claude-code/agents/codebase-onboarding-{conventions,health,runbook,synthesizer}.md` (4), `claude-code/commands/understand-codebase.md` (1), `docs/adr/0006-understand-codebase-adoption.md`, `tests/skills/test_understand_codebase_frontmatter.py`, `tests/agents/__init__.py`, `tests/agents/test_codebase_onboarding_agents.py`, `tests/commands/test_understand_codebase_command.py`, *(stretch)* `tests/assets/test_understand_codebase_xrefs.py`.
- **Modified:** `CLAUDE.md`, `SECURITY.md`, `docs/spec/claude-code-foundations.md`, `docs/spec/aa-ma-quick-reference.md`, `README.md` (if it carries counts), `CHANGELOG.md`, `docs/adr/INDEX.md`.
- **AA-MA:** `.claude/dev/active/understand-codebase-skill/{plan,reference,tasks,context-log}.md` + `…-provenance.log` (created in aa-ma-plan Phase 5).
- **Outside repo (side effect of `install.sh`):** `~/.claude/backups/aa-ma-forge-<ts>/` (the backed-up originals) + 6 new symlinks under `~/.claude/{skills,agents,commands}/`.

### 6. Tests to validate each milestone

- M1: `scripts/install.sh --dry-run` (manual review) → `scripts/install.sh` → `readlink`/`[ -L ]` symlink checks → `ls ~/.claude/backups/aa-ma-forge-*`.
- M2: `uv run pytest tests/skills tests/agents tests/commands -q`; then full `uv run pytest`.
- M3: full `uv run pytest`; `uv run ruff check src/`; `bats --recursive tests/hooks/`; `Skill(doc-drift-detection)` report; `grep -rn 'understand-codebase\|codebase-onboarding' claude-code/ docs/ tests/`; `Skill(impact-analysis)`.

### 7. Rollback strategy

Pure-additive file moves + doc edits on a throwaway feature branch. Rollback = `git checkout main && git branch -D feature/understand-codebase-skill`, then `scripts/uninstall.sh` (restores backups from `~/.claude/backups/`) — or simply re-run `scripts/install.sh` after deleting the new `claude-code/` files (it re-symlinks whatever's present and the originals are still backed up). No DB, no migration, no released artifact. Per-milestone: M1 reverted by `git restore` + uninstall; M2/M3 reverted by `git restore`.

### 8. Dependencies & assumptions

- **Assumes** the `~/.claude/` versions (built 2026-05-12) are the canonical/final source.
- **Assumes** `scripts/install.sh` auto-discovers `claude-code/{skills/*/,agents/*.md,commands/*.md}` and backs up real (non-symlink) targets — *confirmed by reading `scripts/install.sh` lines 113–186, 254–265*.
- **Assumes** no other in-flight AA-MA plan touches `claude-code/skills|agents|commands/` — *confirmed: `.claude/dev/active/` is absent*.
- **Soft-deps (NOT shipped by aa-ma-forge; skill degrades gracefully):** `/index` & `~/.claude-code-project-index/scripts/project_index.py` (code-intelligence-index plugin), `/codebase-deep-dive`, `gsd-map-codebase`/`gsd-scan`/`gsd-intel`/`gsd-codebase-mapper` (gsd plugin), `code-intelligence`/`code-intelligence-index`, `doc-drift-detection`, `improve-codebase-architecture`, `deep-analysis`. **In-repo deps (present):** `agent-teams`, `impact-analysis`, `system-mapping`, `code-reviewer`, `/aa-ma-plan`. The `ShareOnboardingGuide` tool is a harness built-in.
- **Versioning:** next release is a **minor** bump (new feature, additive) — `cz bump` will compute it from the `feat:` commit; CHANGELOG `[Unreleased]` reconciled at release time.
- **Known wrinkle (non-blocking):** the Deep tier's Reviewer step uses `Agent(subagent_type=code-reviewer)`; aa-ma-forge's `code-reviewer` is described in AA-MA-milestone terms but is read-only, so reuse for onboarding-doc review is harmless. Not generalized here (out of scope).

#### Dependencies table

| Dependency | Class | Notes |
|-----------|-------|-------|
| `~/.claude/skills/understand-codebase/` (source artifacts) | Required | Canonical source being vendored; assumed final. |
| `scripts/install.sh` auto-discovery + backup logic | Required | Deploys vendored assets; backs up existing real `~/.claude/` copies. |
| `agent-teams`, `impact-analysis`, `system-mapping` skills | Required (in-repo, present) | Composed by the Deep tier of the skill. |
| `code-reviewer` agent | Required (in-repo, present) | Reused by the Deep tier's reviewer step (read-only). |
| `/aa-ma-plan` command | Required (in-repo, present) | Add-a-feature playbook hands off to it. |
| `/index`, `~/.claude-code-project-index/scripts/project_index.py` | Optional (soft-dep, not shipped) | Skill skips + notes in Provenance if absent. |
| `/codebase-deep-dive` | Optional (soft-dep, not shipped) | Skill skips + notes if absent. |
| `gsd-map-codebase`/`gsd-scan`/`gsd-intel`/`gsd-codebase-mapper` | Optional (soft-dep, not shipped) | Skill skips + notes if absent. |
| `code-intelligence`/`code-intelligence-index` | Optional (soft-dep, not shipped) | Skill skips + notes if absent. |
| `doc-drift-detection`, `improve-codebase-architecture`, `deep-analysis` | Optional (soft-dep, not shipped) | Skill skips + notes if absent. |
| `pytest`, `ruff`, `bats` | Dev-only | Test/lint/hook-test tooling. |

#### Assumptions

1. The `~/.claude/` versions (built 2026-05-12) are canonical/final — if wrong, the vendored copies are stale and M1 must re-copy.
2. `scripts/install.sh` auto-discovers `claude-code/{skills/*/,agents/*.md,commands/*.md}` and backs up real targets — confirmed by code read; if wrong, manifest edits would be needed.
3. No other in-flight AA-MA plan touches `claude-code/skills|agents|commands/` — confirmed `.claude/dev/active/` absent; if wrong, reconciliation overhead.
4. ADR 0005 is the highest existing number → next is 0006 — if wrong, renumber the ADR + INDEX row.
5. `docs/spec/claude-code-foundations.md` agent table is frozen at 2 (pre-v0.8.0) → reconcile to 11; if it's already partially updated, adjust the diff accordingly.

### 9. Effort estimate & complexity

~4–6 hours. **Complexity: ~40%.** No step ≥ 80% (no Chain-of-Thought / human-review gate triggered). M3.3 (foundations reconcile) is the fiddliest piece — bounded, mechanical.

### 10. Risks & mitigations (top 3 per milestone)

**M1** — (a) frontmatter format mismatch → skill/agent fails to load → *normalize in 1.3, prove in M2*. (b) `install.sh` clobbers the user's working `~/.claude/` files → *`--dry-run` reviewed first (1.5); backup logic is exercised by `scripts/install.sh` lines 157–186 and there's `scripts/uninstall.sh` restore*. (c) the skill dir's `references/…` relative links break after the move → *they're relative to the skill dir, which moves wholesale; 3.7 cross-ref grep confirms*.

**M2** — (a) tests too brittle (pin prose that'll churn) → *pin frontmatter/structure/file-existence, never body prose*. (b) `tests/agents/` not picked up by pytest → *add `__init__.py`, mirror `tests/skills/` layout; default `pytest` runs it (not `perf`/`slow`-marked)*. (c) the 4 agents lack `tools:` → 2.2 fails → *1.3 adds `tools:` before tests are written*.

**M3** — (a) miss a count location → exactly the stale-count drift CLAUDE.md warns about → *enumerate all locations in `reference.md`; run `Skill(doc-drift-detection)` Tier 6 in 3.7*. (b) ADR number/INDEX mismatch → *0005 confirmed highest; add INDEX row in the same commit as the ADR*. (c) full foundations-doc reconcile pulls in unrelated churn → *scope to the 3 asset tables only; document the incidental v0.8.0-drift fix in the commit body; touch nothing else*.

### 11. Next action + AA-MA file to update

**Next action:** on approval → exit plan mode → `git checkout main && git checkout -b feature/understand-codebase-skill` → run `/aa-ma-plan` Phase 5 (scribe writes the 5 AA-MA artifacts to `.claude/dev/active/understand-codebase-skill/` from this plan) → begin M1.2.
**First AA-MA files to update after M1:** `understand-codebase-skill-tasks.md` (mark 1.1–1.6 with concrete Result Logs as each completes) + `understand-codebase-skill-provenance.log` (init line + `ENG_STANDARDS_DECLARED: themes=[1,2,4,5,6]`).

### 12. Engineering Standards Declaration

Per `claude-code/rules/engineering-standards.md` — materially applicable themes: **1, 2, 4, 5, 6** (Theme 3 only mildly — see note).
- **Theme 1 — Verification & Truth:** `install.sh --dry-run` before the real run; `readlink`/`[ -L ]` symlink assertions; `grep -rn` cross-ref check; `Skill(doc-drift-detection)` empirical drift verdict — every "it works" claim is backed by a command, not assertion.
- **Theme 2 — Development Principles:** TDD-flavoured (M2 writes structure/frontmatter tests that pin the vendored assets); KISS (move files verbatim, refactor nothing — `install.sh` already auto-discovers, so no manifest edit); DRY (the entire point — one maintained source of truth in `aa-ma-forge` replacing loose `~/.claude/` copies); SoC honoured (skill / agents / command / docs / tests as separate concerns).
- **Theme 4 — Safety & Continuity:** non-breaking constraint — `install.sh` backs up the existing real files; auto-discovery means zero risk of stale manifests; the skill already degrades gracefully so shipping it standalone changes no behaviour; lessons applied — L-005 (don't touch `install.sh` — its KISS auto-discovery already does the job), L-322/L-323 (be careful moving files between a config dir and a repo; the `--dry-run`-first + backup-verify steps cover this); incremental validation (M1 → M2 → M3 each verified before the next).
- **Theme 5 — Execution Checklist:** standard per-task HARD/SOFT enforcement — tests written & passing (HARD), non-breaking verified via `Skill(impact-analysis)` (HARD), AA-MA artifacts synced & git clean (HARD), `Audit-Profile` declared on M3 so Phase 6.8 `/verify-impl` runs (`code-reviewer` + `future-proofing-auditor`).
- **Theme 6 — Sync & Commit Discipline:** sub-step `Result Log:` written immediately per sub-step (never batched); M3 is `Gate: HARD` — refuses COMPLETE while git is dirty or any `Status: PENDING` remains; commit carries the `[AA-MA Plan] understand-codebase-skill …` footer.
- *Theme 3 — Reasoning & Planning (mild):* the one genuine design question — "should aa-ma-forge own a skill with cross-plugin soft-deps?" — was resolved first-principles ("vendor as-is; degrades gracefully; documented") and is recorded in ADR-0006; no further first-principles/Socratic work needed for this mechanical vendoring.

## Next Action

**Do this first:** `git checkout main && git checkout -b feature/understand-codebase-skill`, then begin M1.2 — copy `~/.claude/skills/understand-codebase/` (whole dir) → `claude-code/skills/understand-codebase/` and prepend the maintained-provenance comment to `SKILL.md`.
**Update:** TASKS (mark 1.1–1.6 Result Logs as each completes) and PROVENANCE (`ENG_STANDARDS_DECLARED: themes=[1,2,4,5,6]`). REFERENCE already holds the count-bump enumeration and source/destination paths.

## Optional Next Steps (post-artifact-creation)

- `/verify-plan understand-codebase-skill` — 6-angle adversarial verification (recommended-but-optional given ~40% complexity and additive-only scope). **Status: deferred** (no `verification.md` created).
- Plan reviews (`/plan-eng-review`, `/plan-ceo-review`) — likely overkill; skip unless a second pair of eyes on ADR-0006's dependency-posture call is wanted.

## AA-MA File Mapping

- **tasks.md:** Milestones M1/M2/M3 → `## Milestone N`; sub-steps 1.1–1.6 / 2.1–2.4 / 3.1–3.10 → `### Sub-step N.M`; all `Status: PENDING`; Mode per `(AFK)`/`(HITL)` tags above; M3 carries `Gate: HARD` + `Audit-Profile: custom: code-reviewer, future-proofing-auditor`.
- **reference.md:** source artifact paths, destination paths, the full count-bump enumeration, install.sh auto-discovery/backup facts, soft-dep vs in-repo dep lists, ADR-0006 facts, frontmatter conventions, commit-signature footer.
- **context-log.md:** initial entry dated 2026-05-12 — feature request, 3 user-confirmed decisions, research findings, Engineering Standards Declaration; note `verification: deferred`.
- **provenance.log:** init line, branch-cut line, artifacts-created line, `ENG_STANDARDS_DECLARED: themes=[1,2,4,5,6]`.
