# 0006. Adopt `understand-codebase` (onboarding skill + 4 worker agents + `/understand-codebase`) into the AA-MA Forge ecosystem

**Status:** Implemented
**Date:** 2026-05-12
**Deciders:** Stephen J. Newhouse (with Claude Code)
**Tags:** `workflow`, `onboarding`, `vendoring`, `skills`, `agents`

## Context and Problem Statement

The `understand-codebase` skill — a tiered (Quick / Standard / Deep) codebase-onboarding
workflow that produces `ONBOARDING.md` + `.claude/onboarding/` deep-dives and, with consent,
authors or reviews `AGENTS.md` — together with its 4 worker agents
(`codebase-onboarding-conventions`, `codebase-onboarding-health`, `codebase-onboarding-runbook`,
`codebase-onboarding-synthesizer`) and the thin `/understand-codebase` command wrapper, was
built ad-hoc directly inside `~/.claude/` (real files, 2026-05-12). It had **no maintained
home**: no version, no test coverage, no CI, no ADR, not symlinked from any repo. A loose set
of high-value prompt files in a personal config directory is exactly the kind of thing AA-MA
Forge exists to discipline.

**How do we give `understand-codebase` a maintained home — versioned, tested, CI-checked,
release-managed — without losing the Deep-tier reuse of tooling that AA-MA Forge does not
itself ship?**

## Decision Drivers

- **Single source of truth** — one canonical, versioned copy in `aa-ma-forge`, not a snowflake in `~/.claude/`.
- **Maintenance discipline** — `pytest` coverage, the `security.yml` CI lane, `python-semantic-release` versioning, the doc-drift detectors, and the AA-MA workflow all apply automatically once it's in-repo.
- **Zero-ceremony deployment** — `scripts/install.sh` already auto-discovers `claude-code/{skills/*/, agents/*.md, commands/*.md}` and backs up existing real files before symlinking; vendoring is "drop files in, re-run install.sh".
- **Don't degrade the feature** — the Deep tier composes `gsd-map-codebase`, `/codebase-deep-dive`, `/index`, `code-intelligence`, `doc-drift-detection`, `improve-codebase-architecture` — none of which `aa-ma-forge` ships. The skill is already written to skip missing composed tools and note the downgrade in its Provenance block ("if any reused tool/agent is missing → skip, note, never hard-fail"). Vendoring must keep that intact.
- **Precedent** — ADR-0002 (`grill-with-docs`), ADR-0003 (`prototype`), ADR-0004 (`write-a-skill`) already established the "adopt-and-document" pattern for bringing external skills under `aa-ma-forge`'s roof.

## Considered Options

1. **Vendor as-is + document the cross-plugin soft-dependency posture (this ADR)** — copy `SKILL.md` + `references/`×9 + `templates/onboarding-team.md` + the 4 agents + the command verbatim into `claude-code/`; pin them with tests; record here that the Deep tier names tools `aa-ma-forge` doesn't ship, which is fine because the skill degrades gracefully.
2. **Vendor + trim the cross-plugin references** — edit `SKILL.md` so it only references what `aa-ma-forge` ships.
3. **Leave it external** — keep the files in `~/.claude/`, unversioned, untested.

## Decision Outcome

**Chosen:** Option 1 — vendor as-is, document the soft-deps.

**Rationale:** Drives all the listed decision drivers without any of the costs of the
alternatives. The skill's graceful-degradation behaviour means it is *already* correct when the
composed tools are absent — there is nothing to fix, only something to document. Trimming
(Option 2) would amputate the Deep tier's whole reason for existing (it deliberately reuses
`gsd-map-codebase`/`/codebase-deep-dive`/`/index` rather than re-implementing structural
analysis) and create a permanent divergence from the upstream design. Leaving it external
(Option 3) is the status quo this ADR exists to end. The `aa-ma-forge` repo already references
external plugins by name in its README ("Optional extras: superpowers, gstack, Context7") and in
`grill-with-docs` (forked from `mattpocock/skills`); naming `gsd-*` / `code-intelligence` / etc.
as documented soft-deps is consistent with that posture, not a new kind of coupling.

## Pros and Cons of the Options

### Option 1 — vendor as-is + document soft-deps

- ✅ One maintained, versioned, tested, CI-checked source of truth.
- ✅ Zero `install.sh` change — auto-discovery picks up the new skill dir / 4 agents / command; existing installs get them on next `install.sh` run, with the prior `~/.claude/` copies backed up.
- ✅ Preserves the feature exactly; Deep-tier reuse of `gsd-map-codebase` / `/codebase-deep-dive` / `/index` / `code-intelligence` / `doc-drift-detection` / `improve-codebase-architecture` works when those plugins are present, and the skill self-downgrades (noting it in Provenance) when they aren't.
- ✅ Matches the ADR-0002/0003/0004 adoption precedent.
- ❌ `aa-ma-forge` documentation now names external plugins (`gsd-*`, `code-intelligence`, `codebase-deep-dive`, …) by reference — a reader could mistake them for hard dependencies. Mitigated by this ADR, the `understand-codebase` SKILL.md's own "Error handling / graceful degradation" table, and `tests/assets/test_understand_codebase_xrefs.py` (which asserts only the *in-repo* composed assets must exist).
- ❌ A skill that internally composes ~half-a-dozen non-shipped tools is more surface for "why is this referenced but not here?" confusion than a fully self-contained skill.

### Option 2 — vendor + trim cross-plugin references

- ✅ Cleaner dependency graph; nothing referenced that isn't shipped.
- ❌ Guts the Deep tier — it exists precisely to reuse `gsd-map-codebase` / `/codebase-deep-dive` / `/index` rather than re-implement them.
- ❌ Permanent divergence from the upstream design; every future improvement has to be re-trimmed.

### Option 3 — leave it external

- ✅ Zero work.
- ❌ No version, no tests, no CI, no ADR — exactly the snowflake-in-`~/.claude/` failure mode AA-MA Forge exists to prevent.

## Consequences

**Positive:**
- `understand-codebase` is now a first-class, maintained AA-MA Forge component: versioned by `python-semantic-release`, covered by `pytest` (`tests/skills/test_understand_codebase_frontmatter.py`, `tests/agents/test_codebase_onboarding_agents.py`, `tests/commands/test_understand_codebase_command.py`, `tests/assets/test_understand_codebase_xrefs.py`), checked by the `security.yml` CI lane, and deployed by `install.sh`.
- The `~/.claude/` copies are replaced by symlinks into the repo; edits to `claude-code/skills/understand-codebase/` are immediately live for anyone who ran `install.sh` (the standard `aa-ma-forge` symlink contract).

**Negative:**
- One more skill to keep in sync with the doc-drift count surface (`CLAUDE.md`, `SECURITY.md`, `docs/spec/claude-code-foundations.md`, `docs/spec/aa-ma-quick-reference.md`, `README.md`, `CHANGELOG.md`).
- `aa-ma-forge` now documents soft-dependencies on `gsd-map-codebase` / `gsd-scan` / `gsd-intel` / `gsd-codebase-mapper`, `/codebase-deep-dive`, `/index` (+ `~/.claude-code-project-index/scripts/project_index.py`), `code-intelligence` / `code-intelligence-index`, `doc-drift-detection`, `improve-codebase-architecture`, `deep-analysis`. These are *optional*: present → richer Deep tier; absent → the skill skips them and downgrades Deep to "enhanced Standard", noting it in its Provenance block.

**Neutral:**
- `install.sh` auto-discovery means no manifest to maintain — the new assets just appear in the deploy.
- The skill carries its own `references/` (9 files) and `templates/` (1 file) sub-directory — heavier than the typical `aa-ma-forge` skill but consistent with `aa-ma-plan-workflow`, `agent-teams`, `plan-verification`, etc., which also have `references/`.
- The Deep tier's Reviewer step uses `Agent(subagent_type=code-reviewer)`; `aa-ma-forge`'s `code-reviewer` agent is described in `/execute-aa-ma-milestone` Phase-6.8 terms but is read-only, so reuse for onboarding-doc review is harmless. Not generalised here.

## Implementation Notes

- **Vendored files** (`feature/understand-codebase-skill` branch, AA-MA plan `understand-codebase-skill`):
  - `claude-code/skills/understand-codebase/SKILL.md` (+ a `<!-- Maintained in aa-ma-forge as of v0.9.0 — see docs/adr/0006-understand-codebase-adoption.md -->` provenance comment on line 1) + `references/`×9 (`AGENTS-MD-TEMPLATE.md`, `DEEPDIVE-TEMPLATES.md`, `DIMENSIONS.md`, `ONBOARDING-TEMPLATE.md`, `PLAYBOOK-ADD-FEATURE.md`, `PLAYBOOK-CONTRIBUTE.md`, `PROS-CONS-RUBRIC.md`, `REUSE-MAP.md`, `RULES-FILES.md`) + `templates/onboarding-team.md`
  - `claude-code/agents/codebase-onboarding-{conventions,health,runbook,synthesizer}.md` (already conformed to the `name`/`description`/`tools` agent-frontmatter convention — no normalisation needed)
  - `claude-code/commands/understand-codebase.md`
- **No `install.sh` change** — `scripts/install.sh` auto-discovers `claude-code/skills/*/`, `claude-code/agents/*.md`, `claude-code/commands/*.md` and backs up pre-existing real files to `~/.claude/backups/aa-ma-forge-<ts>/` before symlinking (verified: this adoption produced backup `~/.claude/backups/aa-ma-forge-20260512-160044/`).
- **Count surface reconciled** in the same change: `CLAUDE.md` (9→10 commands, 17→18 skills, 7→11 agents), `SECURITY.md` (command/skill/agent lists + counts; also the incidental "4→5 spec docs" fix), `docs/spec/claude-code-foundations.md` (Commands 9→10, Skills 16→18 — also picking up the v0.8.0 `verify-impl` omission, Agents 2→11 — also picking up the five v0.8.0 audit agents, Hooks 2→8 — also picking up the v0.7.0/v0.8.0 hooks), `docs/spec/aa-ma-quick-reference.md` (+`/understand-codebase`), `README.md` "All commands" table (+`/understand-codebase`), `CHANGELOG.md` (`[Unreleased]` → `### Feat`). <!-- doc-drift-ignore-version -->
- Shipped at v0.9.0 (next `cz bump` from the `feat:` commit) — this row will be marked `Implemented` and the merge/tag commits cited once landed on `main`.

## References

- AA-MA plan: `.claude/dev/active/understand-codebase-skill/understand-codebase-skill-plan.md`
- The skill: `claude-code/skills/understand-codebase/SKILL.md` (and its `references/` + `templates/`)
- Adoption-pattern precedent: [ADR-0002](0002-grill-with-docs-adoption.md), [ADR-0003](0003-prototype-adoption.md), [ADR-0004](0004-write-a-skill-adoption.md)
- Engineering-standards rule (`Critical-Path`, themes): [ADR-0001](0001-engineering-standards-architecture.md)
