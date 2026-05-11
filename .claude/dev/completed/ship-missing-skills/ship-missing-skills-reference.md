<!-- ARCHIVED: 2026-04-07 13:45 -->
<!-- Plan: ship-missing-skills - COMPLETE -->
<!-- Total Milestones: 4 | Duration: 2026-04-06 to 2026-04-07 -->

# ship-missing-skills Reference

## Source Locations

| Asset | Source Path | Destination |
|---|---|---|
| grill-me | `~/.claude/commands/grill-me.md` | `claude-code/commands/grill-me.md` |
| plan-verification | `~/.claude/skills/plan-verification/` | `claude-code/skills/plan-verification/` |
| impact-analysis | `~/.claude/skills/impact-analysis/` | `claude-code/skills/impact-analysis/` |
| system-mapping | `~/.claude/skills/system-mapping/` | `claude-code/skills/system-mapping/` |
| retro | `~/.claude/skills/retro/` | `claude-code/skills/retro/` |

## Skill Sizes (line counts)

- plan-verification: 471 lines + references/verification-standards.md
- impact-analysis: 276 lines
- system-mapping: 421 lines
- retro: 406 lines + references/output-format.md (EXCLUDE SKILL.md.tmpl)

## Where Referenced in Commands

| External Dep | Command Files |
|---|---|
| plan-verification | verify-plan.md:78,89,146 / aa-ma-plan.md:386,389 |
| impact-analysis | aa-ma-execution SKILL.md:182,354,1158 / execute-aa-ma-milestone.md:284 / execute-aa-ma-full.md:252 |
| system-mapping | aa-ma-execution SKILL.md:147 / execute-aa-ma-milestone.md:200 / execute-aa-ma-full.md:207 |
| retro | archive-aa-ma.md:112 |
| grill-me | aa-ma-plan.md:74 (inline discipline, not Skill() invocation) |

## Third-Party Optional Dependencies

| Dependency | Type | What It Enhances | Install |
|---|---|---|---|
| superpowers plugin | Claude Code plugin | brainstorming, writing-plans, TDD skills in /aa-ma-plan and execute commands | superpowers marketplace |
| gstack plugin | Claude Code plugin | plan-ceo-review, plan-eng-review, plan-design-review, qa-only, browse | gstack marketplace |
| Context7 MCP | MCP server | Library docs lookup in planning and execution | context7 MCP setup |

## Install Script Key Lines

- Skills symlink section: install.sh lines 258-261 (currently hardcoded aa-ma-execution only)
- Backup collection for skills: install.sh line 131 (currently hardcoded)
- Uninstall script: needs matching update

## Broken Reference

- `verify-plan.md:149` references `docs/plans/2026-03-08-aa-ma-plan-verification-design.md` — file does not exist in repo
