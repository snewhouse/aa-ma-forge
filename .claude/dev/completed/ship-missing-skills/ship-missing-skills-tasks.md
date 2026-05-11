<!-- ARCHIVED: 2026-04-07 13:45 -->
<!-- Plan: ship-missing-skills - COMPLETE -->
<!-- Total Milestones: 4 | Duration: 2026-04-06 to 2026-04-07 -->

# ship-missing-skills Tasks (HTP)

## Milestone 1: Copy and audit custom assets
- Status: COMPLETE
- Gate: SOFT
- Dependencies: None
- Complexity: 20%
- Acceptance Criteria: All 5 assets in claude-code/, no internal refs, git-tracked

### Task 1.1: Copy grill-me command
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: `claude-code/commands/grill-me.md` exists, no internal refs
- Result Log: Copied from ~/.claude/commands/grill-me.md, chmod 644. File exists, 50 lines.

### Task 1.2: Copy plan-verification skill
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: `claude-code/skills/plan-verification/SKILL.md` + `references/` exist, no internal refs
- Result Log: Copied SKILL.md (471 lines) + references/verification-standards.md. chmod 644.

### Task 1.3: Copy impact-analysis skill
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: `claude-code/skills/impact-analysis/SKILL.md` exists, no internal refs
- Result Log: Copied SKILL.md (276 lines). chmod 644.

### Task 1.4: Copy system-mapping skill
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: `claude-code/skills/system-mapping/SKILL.md` exists, no internal refs
- Result Log: Copied SKILL.md (421 lines). chmod 644.

### Task 1.5: Copy retro skill
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: `claude-code/skills/retro/SKILL.md` + `references/` exist, SKILL.md.tmpl excluded, no internal refs
- Result Log: Copied SKILL.md (406 lines) + references/output-format.md. SKILL.md.tmpl excluded. chmod 644.

### Task 1.6: Audit all copied assets
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: Zero grep hits for Biorelate, internal URLs, personal paths, API keys, client names
- Result Log: Grep for biorelate/zoetis/galactic/sjnewhouse/client/private/api_key/secret/password/credential: 0 hits. All assets clean for public repo.

## Milestone 2: Update install.sh and uninstall.sh
- Status: COMPLETE
- Gate: SOFT
- Dependencies: Milestone 1
- Complexity: 30%
- Acceptance Criteria: install.sh --dry-run shows all 5 skill dirs; uninstall.sh --dry-run shows cleanup

### Task 2.1: Update install.sh skills section
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: Skills section uses loop over `claude-code/skills/*/`; backup collection updated
- Result Log: Replaced hardcoded aa-ma-execution with `for d in claude-code/skills/*/` loop in both backup collection (line 131) and symlink creation (line 260-264).

### Task 2.2: Update uninstall.sh skills section
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: Uninstall removes all skill symlinks via matching loop
- Result Log: No changes needed — uninstall.sh already uses `find -maxdepth 1 -type l` auto-discovery against repo root. All new skill symlinks will be caught automatically.

### Task 2.3: Test install/uninstall dry-run
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: Both scripts show correct output for all 5 new skills
- Result Log: install.sh --dry-run shows 16 symlinks (7 commands, 5 skills, 2 agents, 1 rule, 1 hook), 4 copied docs, 18 backed up. All 5 skills correctly listed: aa-ma-execution, impact-analysis, plan-verification, retro, system-mapping.

## Milestone 3: Document dependencies in README
- Status: COMPLETE
- Gate: SOFT
- Dependencies: Milestone 1
- Complexity: 25%
- Acceptance Criteria: README has deps section, command table updated, broken ref fixed

### Task 3.1: Add dependencies section to README
- Status: COMPLETE
- Mode: HITL
- Acceptance Criteria: Section lists superpowers, gstack, Context7 with links and purpose
- Result Log: Added "Optional extras" section with 3-row table (superpowers, gstack, Context7). User approved wording. Placed between "What else helped" and "Credits".

### Task 3.2: Update command table with grill-me
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: `/grill-me` appears in README command table
- Result Log: Added `/grill-me` row to "All commands" table. Now 8 commands listed.

### Task 3.3: Fix broken doc reference in verify-plan.md
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: verify-plan.md:149 no longer references missing file
- Result Log: Replaced missing `docs/plans/2026-03-08-aa-ma-plan-verification-design.md` reference with `claude-code/skills/plan-verification/SKILL.md` (the actual skill file that now ships in repo).

## Milestone 4: Commit, verify, push
- Status: COMPLETE
- Gate: SOFT
- Dependencies: Milestones 1, 2, 3
- Complexity: 5%
- Acceptance Criteria: git status clean, install.sh --dry-run complete, pushed

### Task 4.1: Commit all changes
- Status: COMPLETE
- Mode: AFK
- Result Log: Commit 563ee3a — 10 files changed, 1902 insertions. AA-MA signature included.

### Task 4.2: Final verification
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: install.sh --dry-run shows 7 commands, 5 skills, 2 agents, 1 rule, 1 hook
- Result Log: install.sh --dry-run: 16 symlinks (7 commands + 5 skills + 2 agents + 1 rule + 1 hook), 4 copied docs. All assets accounted for.

### Task 4.3: Push
- Status: COMPLETE
- Mode: AFK
- Result Log: Pushed to origin/main. 1b1b005..563ee3a.
