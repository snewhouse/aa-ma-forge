# understand-codebase-skill Reference

**Immutable facts and constants for this task.**

_Last Updated: 2026-05-12 00:00_

---

## API Endpoints

_None. This task is pure local file movement + documentation edits + `install.sh` symlink deployment. No external API is exercised._

| Endpoint | URL | Auth | Notes |
|----------|-----|------|-------|
| — | — | — | N/A — no API in scope `[valid: 2026-05-12]` |

## File Paths

### Source artifacts (under `~/.claude/`, the canonical originals being vendored)

`[valid: 2026-05-12]` — all built ad-hoc directly in `~/.claude/` on 2026-05-12; assumed final.

- `~/.claude/skills/understand-codebase/SKILL.md` — the skill definition (frontmatter `name: understand-codebase`, `allowed-tools:` YAML list).
- `~/.claude/skills/understand-codebase/references/AGENTS-MD-TEMPLATE.md`
- `~/.claude/skills/understand-codebase/references/DEEPDIVE-TEMPLATES.md`
- `~/.claude/skills/understand-codebase/references/DIMENSIONS.md`
- `~/.claude/skills/understand-codebase/references/ONBOARDING-TEMPLATE.md`
- `~/.claude/skills/understand-codebase/references/PLAYBOOK-ADD-FEATURE.md`
- `~/.claude/skills/understand-codebase/references/PLAYBOOK-CONTRIBUTE.md`
- `~/.claude/skills/understand-codebase/references/PROS-CONS-RUBRIC.md`
- `~/.claude/skills/understand-codebase/references/REUSE-MAP.md`
- `~/.claude/skills/understand-codebase/references/RULES-FILES.md`
  - (= 9 files under `references/`)
- `~/.claude/skills/understand-codebase/templates/onboarding-team.md` — (= 1 file under `templates/`)
  - **Total skill dir = 11 files** (SKILL.md + 9 references + 1 template).
- `~/.claude/agents/codebase-onboarding-conventions.md`
- `~/.claude/agents/codebase-onboarding-health.md`
- `~/.claude/agents/codebase-onboarding-runbook.md`
- `~/.claude/agents/codebase-onboarding-synthesizer.md`
  - (= 4 worker agents; frontmatter uses `name`/`description` with a `>-` block scalar; `tools:` (comma-separated string) must be normalized in if missing.)
- `~/.claude/commands/understand-codebase.md` — the slash command (keeps `argument-hint:` frontmatter key; body references `Skill(understand-codebase)`, mentions `--quick`/`--standard`/`--deep`).

### Destination paths (in the `aa-ma-forge` repo)

`[valid: 2026-05-12]`

- `claude-code/skills/understand-codebase/` — whole skill dir moved verbatim (SKILL.md + `references/`×9 + `templates/`×1). Prepend to SKILL.md: `<!-- Maintained in aa-ma-forge as of v<next> — see docs/adr/0006-understand-codebase-adoption.md -->`
- `claude-code/agents/codebase-onboarding-conventions.md`
- `claude-code/agents/codebase-onboarding-health.md`
- `claude-code/agents/codebase-onboarding-runbook.md`
- `claude-code/agents/codebase-onboarding-synthesizer.md`
- `claude-code/commands/understand-codebase.md`

### Files to Create (in repo)

- `docs/adr/0006-understand-codebase-adoption.md` — from `docs/adr/TEMPLATE.md`. Status Accepted (→ Implemented once merged, per the 0005 pattern). `[valid: 2026-05-12]`
- `tests/skills/test_understand_codebase_frontmatter.py` — reuses `tests/skills/_helpers.py`.
- `tests/agents/__init__.py` — empty marker so pytest collects the new dir.
- `tests/agents/test_codebase_onboarding_agents.py` — parametrized over the 4 agent names.
- `tests/commands/test_understand_codebase_command.py`
- `tests/assets/test_understand_codebase_xrefs.py` — *(stretch — optional, skip if time-boxed)*.

### Files to Modify (in repo)

- `CLAUDE.md` — Architecture block: commands `9 → 10`, skills `17 → 18`, agents `7 → 11` (rephrase "7 specialized agents (scribe, validator, + 5 verify-impl audit agents)" → "11 specialized agents (scribe, validator, 5 verify-impl audit agents, + 4 codebase-onboarding agents)").
- `SECURITY.md` — command list `9 → 10` (add `understand-codebase`); skills list `17 → 18` (add `understand-codebase`); agents list `7 → 11` (add the 4 `codebase-onboarding-*`); update count words.
- `docs/spec/claude-code-foundations.md` — reconcile fully: Commands table → **10 rows** (+ `/understand-codebase`); Skills table → **18 rows** (+ `understand-codebase`, + any missing since freeze e.g. `verify-impl`); Agents table → **11 rows** (was 2 → add `code-reviewer`, `security-auditor`, `tdd-sequence-auditor`, `context7-evidence-auditor`, `future-proofing-auditor`, `codebase-onboarding-conventions`, `codebase-onboarding-health`, `codebase-onboarding-runbook`, `codebase-onboarding-synthesizer`). Incidentally fixes pre-existing v0.8.0 drift.
- `docs/spec/aa-ma-quick-reference.md` — add `/understand-codebase` to the commands area (~line 98 region).
- `README.md` — only if it carries hardcoded counts; bump if present; add a brief `/understand-codebase` mention if there's a natural commands list (light touch — README is narrative).
- `CHANGELOG.md` — add `## [Unreleased]` → `### Feat` → "**skills**: vendor `understand-codebase` onboarding skill + 4 `codebase-onboarding-*` worker agents + `/understand-codebase` command into the AA-MA Forge ecosystem; maintained here going forward (ADR-0006)".
- `docs/adr/INDEX.md` — add a row for ADR-0006.

### Key Directories

- `~/.claude/backups/aa-ma-forge-<ts>/` — where `scripts/install.sh` backs up existing **real** (non-symlink) `~/.claude/` targets *before* replacing them with symlinks. After M1, this holds the originals of: the `understand-codebase` skill dir, the 4 `codebase-onboarding-*` agents, and the `understand-codebase` command. `[valid: 2026-05-12]`
- `.claude/dev/active/understand-codebase-skill/` — this task's AA-MA directory.

## Configuration

### Environment Variables

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `AA_MA_HOOKS_DISABLE` | unset | no | Master kill switch — disables all AA-MA hooks/gates. Not used by this task; listed for awareness only. `[valid: 2026-05-12]` |

_No new env vars introduced by this task. No `os.getenv()` changes in `src/`._

### Config / install behaviour

- `scripts/install.sh` **AUTO-DISCOVERS** `claude-code/{skills/*/,agents/*.md,commands/*.md}` — confirmed by reading `scripts/install.sh` lines 113–186 and 254–265. **Therefore NO `install.sh` edit is needed** when adding the new skill dir / 4 agents / command. `[valid: 2026-05-12]`
- `scripts/install.sh` **BACKS UP** existing real (non-symlink) targets to `~/.claude/backups/aa-ma-forge-<ts>/` before symlinking — backup logic at `scripts/install.sh` lines 157–186. The user's existing `~/.claude/` copies of these 6 assets are therefore **preserved**, not clobbered. `[valid: 2026-05-12]`
- `scripts/uninstall.sh` restores backups from `~/.claude/backups/`.
- Skill `SKILL.md` frontmatter convention: `name: understand-codebase`; `allowed-tools:` is a **YAML list** (non-empty).
- Agent frontmatter convention (aa-ma-forge): `---`-delimited; `name:` (== filename stem); `description:` (non-empty; `>-` block scalar is fine); `tools:` (**comma-separated string**, non-empty — e.g. `tools: Read, Glob, Grep, Bash, Write` — must be normalized in for any agent missing it).
- Command frontmatter: `name: understand-codebase`; `argument-hint:` key retained (Claude Code supports it).

## Dependencies

| Package / asset | Version / state | Class | Purpose |
|---|---|---|---|
| `~/.claude/skills/understand-codebase/` source | built 2026-05-12, assumed final | Required (source) | Canonical originals being vendored. |
| `scripts/install.sh` auto-discovery + backup | present in repo | Required (in-repo) | Deploys vendored assets; backs up originals. |
| `agent-teams` skill | present in `claude-code/skills/` | Required (in-repo) | Composed by Deep tier. |
| `impact-analysis` skill | present in `claude-code/skills/` | Required (in-repo) | Composed by Deep tier; also used in 3.9. |
| `system-mapping` skill | present in `claude-code/skills/` | Required (in-repo) | Composed by Deep tier. |
| `code-reviewer` agent | present in `claude-code/agents/` | Required (in-repo) | Reused by Deep tier reviewer step (read-only). Also one of the M3 `Audit-Profile` agents. |
| `/aa-ma-plan` command | present in `claude-code/commands/` | Required (in-repo) | Add-a-feature playbook hands off to it. |
| `future-proofing-auditor` agent | present in `claude-code/agents/` | Required (in-repo) | M3 `Audit-Profile` agent (Phase 6.8 `/verify-impl`). |
| `/index` + `~/.claude-code-project-index/scripts/project_index.py` | NOT shipped by aa-ma-forge | Optional (soft-dep) | code-intelligence-index plugin. Skill skips + notes in Provenance if absent. |
| `/codebase-deep-dive` | NOT shipped | Optional (soft-dep) | Skill skips + notes if absent. |
| `gsd-map-codebase` / `gsd-scan` / `gsd-intel` / `gsd-codebase-mapper` | NOT shipped (gsd plugin) | Optional (soft-dep) | Skill skips + notes if absent. |
| `code-intelligence` / `code-intelligence-index` | NOT shipped | Optional (soft-dep) | Skill skips + notes if absent. |
| `doc-drift-detection` | NOT shipped by aa-ma-forge | Optional (soft-dep) | Skill skips + notes if absent. (Also referenced by 3.7's drift check — use `/doc-sync` report-only if absent.) |
| `improve-codebase-architecture` | NOT shipped | Optional (soft-dep) | Skill skips + notes if absent. |
| `deep-analysis` | NOT shipped | Optional (soft-dep) | Skill skips + notes if absent. |
| `ShareOnboardingGuide` | harness built-in | n/a | Tool provided by the Claude Code harness, not a plugin asset. |
| `pytest` / `ruff` / `bats` | repo dev tooling | Dev-only | Test, lint, hook-test. |

**Graceful-degradation contract (from SKILL.md):** "if any reused tool/agent is missing → skip, note in Provenance, never hard-fail." This is the load-bearing reason vendoring as-is is safe — see ADR-0006.

## Constants

| Constant | Value | Context |
|----------|-------|---------|
| Skill dir file count | 11 | `SKILL.md` + 9 `references/*.md` + 1 `templates/*.md`. M1 acceptance check. `[valid: 2026-05-12]` |
| `references/` file count | 9 | `ls claude-code/skills/understand-codebase/references/ \| wc -l` == 9. |
| `templates/` file count | 1 | `onboarding-team.md`. |
| Worker agent count (new) | 4 | `codebase-onboarding-{conventions,health,runbook,synthesizer}`. |
| Companion-file size floor (test 2.1) | > 1 KB | Every `references/*.md` + `templates/*.md` named in SKILL.md must be > 1 KB. |
| Commands count: before → after | 9 → 10 | CLAUDE.md / SECURITY.md / foundations Commands table. |
| Skills count: before → after | 17 → 18 | CLAUDE.md / SECURITY.md / foundations Skills table. |
| Agents count: before → after | 7 → 11 | CLAUDE.md / SECURITY.md / foundations Agents table (foundations was frozen at 2 pre-v0.8.0 → reconcile to 11). |
| Next ADR number | 0006 | 0005 is the highest existing ADR. File: `docs/adr/0006-understand-codebase-adoption.md`. |
| v0.8.0 cutover date | 2026-05-11 | `Created: 2026-05-12` > `V080_CUTOVER 2026-05-11` ⇒ Phase 6.8 `/verify-impl` applies to M3. |

## Count-Bump Locations — Complete Enumeration (HIGHEST-VALUE FACT — drift here is the #1 risk)

`[valid: 2026-05-12]` — every place that must be touched so asset counts stay consistent. Verify with `Skill(doc-drift-detection)` Tier 6 in step 3.7.

1. **`CLAUDE.md`** — Architecture block:
   - commands `9 → 10`
   - skills `17 → 18`
   - agents `7 → 11` — rephrase the line "7 specialized agents (scribe, validator, + 5 verify-impl audit agents)" → "11 specialized agents (scribe, validator, 5 verify-impl audit agents, + 4 codebase-onboarding agents)".
2. **`SECURITY.md`**:
   - command list `9 → 10` — add `understand-codebase`
   - skills list `17 → 18` — add `understand-codebase`
   - agents list `7 → 11` — add the 4 `codebase-onboarding-*` (conventions, health, runbook, synthesizer)
   - plus update the count *words* (prose numbers, not just list entries)
3. **`docs/spec/claude-code-foundations.md`**:
   - Commands table → **10 rows** (add `/understand-codebase`)
   - Skills table → **18 rows** (add `understand-codebase`; also add any skill missing since the doc froze, e.g. `verify-impl`)
   - Agents table → **11 rows** — reconciled from the current **2 rows** (frozen pre-v0.8.0) by adding: `code-reviewer`, `security-auditor`, `tdd-sequence-auditor`, `context7-evidence-auditor`, `future-proofing-auditor`, `codebase-onboarding-conventions`, `codebase-onboarding-health`, `codebase-onboarding-runbook`, `codebase-onboarding-synthesizer` (+ the existing 2 = 11). Note the incidental v0.8.0-drift fix in the commit body.
4. **`docs/spec/aa-ma-quick-reference.md`** — add `/understand-codebase` near line 98 (the commands area).
5. **`README.md`** — only if it carries hardcoded counts (it's narrative — light touch). Bump any present; add a brief `/understand-codebase` mention if there's a natural commands list.
6. **`CHANGELOG.md`** — add `## [Unreleased]` → `### Feat` entry: "**skills**: vendor `understand-codebase` onboarding skill + 4 `codebase-onboarding-*` worker agents + `/understand-codebase` command into the AA-MA Forge ecosystem; maintained here going forward (ADR-0006)".
7. **`docs/adr/INDEX.md`** — add a row for ADR-0006 (not a count, but part of the same documentation-consistency sweep).

> **No `scripts/install.sh` edit** — it auto-discovers `claude-code/{skills/*/,agents/*.md,commands/*.md}` and backs up existing real targets to `~/.claude/backups/aa-ma-forge-<ts>/`. Editing it would violate L-005 (don't touch install.sh — its KISS auto-discovery already does the job).

## ADR-0006 Facts

`[valid: 2026-05-12]`

- **Next number is 0006** — 0005 is the highest existing ADR.
- **File:** `docs/adr/0006-understand-codebase-adoption.md`, created from `docs/adr/TEMPLATE.md`.
- **Precedent:** follows the `0002-grill-with-docs` / `0003-prototype` / `0004-write-a-skill` "adoption" pattern (vendoring an external/ad-hoc asset into the maintained ecosystem).
- **Status:** Accepted → Implemented once merged (per the 0005 pattern).
- **Documents:** the cross-plugin **soft-dependency posture** — aa-ma-forge now *names by reference* gsd / code-intelligence / `/codebase-deep-dive` / `/index` etc., mitigated by the skill's graceful degradation.
- **INDEX:** add a row to `docs/adr/INDEX.md` in the same commit as the ADR.
- **References section should cite:** this plan, `claude-code/skills/understand-codebase/SKILL.md`, ADR-0002, ADR-0003, ADR-0004.

## Commit Signature

When this plan is active, ALL commits MUST include as the last footer line:

```
[AA-MA Plan] understand-codebase-skill .claude/dev/active/understand-codebase-skill
```

(Phase 6.8 `/verify-impl` applies to M3 — `Created: 2026-05-12` is after the v0.8.0 cutover `2026-05-11` — using `Audit-Profile: custom: code-reviewer, future-proofing-auditor`.)

## Git State at Branch Cut

| Fact | Value |
|------|-------|
| Branch | `feature/understand-codebase-skill` `[valid: 2026-05-12]` |
| Cut from | `main` |
| HEAD at cut | `3a90325` |

## Temporal Validity Convention

Facts above carry `[valid: 2026-05-12]` markers where dated. Entries without markers are assumed always-valid for the duration of this task. When a fact becomes obsolete during execution, add `[superseded: YYYY-MM-DD by ...]` rather than deleting.

## External References

- AA-MA spec: `docs/spec/aa-ma-specification.md`
- AA-MA quick reference: `docs/spec/aa-ma-quick-reference.md`
- Engineering standards: `claude-code/rules/engineering-standards.md`
- ADR template: `docs/adr/TEMPLATE.md`; ADR index: `docs/adr/INDEX.md`
- Approved plan source: `~/.claude/plans/are-main-and-the-rustling-lantern.md` (the plan this artifact set was scribed from)

## Glossary

| Term | Definition |
|------|-----------|
| Soft-dep | A tool/agent the `understand-codebase` skill *can* use but aa-ma-forge does **not** ship; the skill skips it gracefully and notes the skip in Provenance. |
| In-repo dep | A skill/agent/command already shipped by aa-ma-forge that the `understand-codebase` skill composes. |
| Auto-discovery | `scripts/install.sh` finds `claude-code/{skills/*/,agents/*.md,commands/*.md}` automatically — no manifest to maintain. |
| Graceful degradation | The skill's contract: missing reused tool/agent → skip, note in Provenance, never hard-fail. |
| Count-bump | Updating hardcoded asset counts (commands/skills/agents) across docs so they stay consistent — Tier 6 doc-drift domain. |
