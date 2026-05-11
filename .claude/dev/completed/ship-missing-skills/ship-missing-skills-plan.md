<!-- ARCHIVED: 2026-04-07 13:45 -->
<!-- Plan: ship-missing-skills - COMPLETE -->
<!-- Total Milestones: 4 | Duration: 2026-04-06 to 2026-04-07 -->

# ship-missing-skills Plan

**Objective:** Ship 5 missing custom assets (1 command + 4 skills) into aa-ma-forge, update install.sh to deploy them, and document third-party optional dependencies in the README.

**Owner:** Stephen J. Newhouse + Claude Code
**Created:** 2026-04-06
**Last Updated:** 2026-04-06

## Executive Summary

The AA-MA commands reference 5 custom assets (grill-me command, plan-verification/impact-analysis/system-mapping/retro skills) that live in Stephen's personal `~/.claude/` but aren't shipped in this repo. A new user who installs aa-ma-forge gets broken references. This plan copies those assets into the repo, updates the installer, and documents what's included vs what's optional third-party.

## Milestone 1: Copy and audit custom assets

**Goal:** Get all 5 assets into the repo, reviewed for public-readiness.
**Acceptance Criteria:** All 5 assets exist in `claude-code/`, contain no personal/internal references, and are git-tracked.

### Task 1.1: Copy grill-me command
- Copy `~/.claude/commands/grill-me.md` → `claude-code/commands/grill-me.md`
- Review for internal references
- Mode: AFK

### Task 1.2: Copy plan-verification skill (with references/)
- Copy `~/.claude/skills/plan-verification/` → `claude-code/skills/plan-verification/`
- Includes `SKILL.md` + `references/verification-standards.md`
- Review for internal references
- Mode: AFK

### Task 1.3: Copy impact-analysis skill
- Copy `~/.claude/skills/impact-analysis/` → `claude-code/skills/impact-analysis/`
- Review for internal references
- Mode: AFK

### Task 1.4: Copy system-mapping skill
- Copy `~/.claude/skills/system-mapping/` → `claude-code/skills/system-mapping/`
- Review for internal references
- Mode: AFK

### Task 1.5: Copy retro skill (with references/)
- Copy `~/.claude/skills/retro/` → `claude-code/skills/retro/`
- Includes `SKILL.md` + `references/output-format.md`
- Exclude `SKILL.md.tmpl` (template, not shipped)
- Review for internal references
- Mode: AFK

### Task 1.6: Audit all copied assets for public-readiness
- Grep for: Biorelate, internal URLs, personal paths, API keys, client names
- Fix any findings
- Mode: AFK

**Risks:**
1. Skills may reference other personal skills not in scope → Mitigate: grep for `Skill(` calls, document any external refs
2. File permissions may be restrictive (some are `600`) → Mitigate: `chmod 644` after copy
3. retro has a `.tmpl` file we don't want → Mitigate: exclude explicitly

## Milestone 2: Update install.sh and uninstall.sh

**Goal:** Installer deploys all skills via auto-discovery loop; uninstaller removes them.
**Acceptance Criteria:** `install.sh --dry-run` shows all 5 new skill directories; `uninstall.sh --dry-run` shows cleanup for them.

### Task 2.1: Update install.sh skills section
- Replace hardcoded `aa-ma-execution` symlink with loop over all `claude-code/skills/*/`
- Update backup collection to loop over skills dirs too
- Mode: AFK

### Task 2.2: Update uninstall.sh skills section
- Ensure uninstall removes all skill symlinks (not just aa-ma-execution)
- Mode: AFK

### Task 2.3: Test install/uninstall dry-run
- Run `scripts/install.sh --dry-run` and verify output
- Run `scripts/uninstall.sh --dry-run` and verify output
- Mode: AFK

**Risks:**
1. Loop may pick up non-directory files in skills/ → Mitigate: use `*/` glob which only matches dirs
2. Existing symlinks from prior install may conflict → Mitigate: `create_symlink` already handles stale links

## Milestone 3: Document dependencies in README

**Goal:** README clearly states what's included vs what's optional third-party.
**Acceptance Criteria:** New "Dependencies" or "Optional extras" section in README listing all third-party tools with links and what they enhance.

### Task 3.1: Add dependencies section to README
- After "What else helped" section (line ~119)
- List: superpowers plugin, gstack plugin, Context7 MCP server
- For each: what it is, what it enhances, link to install
- Note: "AA-MA works without these. They enhance the workflow."
- Mode: HITL (voice/wording review)

### Task 3.2: Update command table with grill-me
- Add `/grill-me` to the "All commands" table in README
- Mode: AFK

### Task 3.3: Fix broken doc reference
- `verify-plan.md:149` references `docs/plans/2026-03-08-aa-ma-plan-verification-design.md` which doesn't exist
- Either create a stub or remove the reference
- Mode: AFK

**Risks:**
1. README getting too long → Mitigate: keep deps section compact (10-15 lines max)

## Milestone 4: Commit, verify, push

**Goal:** Everything committed and pushed with clean status.
**Acceptance Criteria:** `git status` clean, all new files tracked, install.sh --dry-run shows complete deployment.

### Task 4.1: Commit all changes
- Stage new files and modified files
- Conventional commit message
- Mode: AFK

### Task 4.2: Final verification
- Run `install.sh --dry-run`
- Confirm all 7 commands, 5 skills, 2 agents, 1 rule, 1 hook show in output
- Mode: AFK

### Task 4.3: Push
- Mode: AFK

## Rollback Strategy

- All changes are additive (new files + installer loop change)
- Rollback: `git revert` the commit
- No database, no external systems, no risk of data loss

## Dependencies and Assumptions

- Source skills exist at `~/.claude/skills/{plan-verification,impact-analysis,system-mapping,retro}/`
- Source command exists at `~/.claude/commands/grill-me.md`
- These are Stephen's original work, not third-party plugins
- Apache-2.0 licence covers all shipped content

## Effort Estimate

| Milestone | Complexity | Estimate |
|-----------|-----------|----------|
| M1: Copy and audit | 20% | ~10 min |
| M2: Update installers | 30% | ~10 min |
| M3: Document deps | 25% | ~10 min |
| M4: Commit and push | 5% | ~5 min |
| **Total** | **25%** | **~35 min** |

## Next Action

Start with Task 1.1: Copy grill-me command into `claude-code/commands/`.
