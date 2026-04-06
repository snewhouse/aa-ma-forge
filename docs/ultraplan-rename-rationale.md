# Why `/ultraplan` Was Renamed to `/aa-ma-plan`

**Date:** 2026-04-06
**Trigger:** Anthropic shipped a built-in Claude Code feature called "Ultraplan" on 2026-04-04

## What Happened

On April 4, 2026, Anthropic launched a built-in Claude Code feature called "Ultraplan" ([official docs](https://code.claude.com/docs/en/ultraplan)). Our AA-MA ecosystem had been using `/ultraplan` as the command name for our structured planning workflow since late 2025. The names collided exactly.

## The Two Systems Compared

| Dimension | Anthropic's Ultraplan | Our `/aa-ma-plan` (formerly `/ultraplan`) |
|-----------|----------------------|------------------------------------------|
| **Purpose** | Cloud-based planning handoff | Structured AA-MA methodology engine |
| **Where it runs** | Cloud (CCR) + web browser | Local terminal only |
| **Output** | Single plan document | 6 AA-MA structured files |
| **Planning process** | Explore, plan, approve | 5 phases + adversarial verification |
| **Multi-agent** | Disabled in remote session | Parallel agent dispatch |
| **Memory system** | None | Full AA-MA 5-file memory |
| **Requirements** | GitHub repo + web account | None (works fully offline) |
| **Model** | Opus 4.6 with 30-min compute window | Whatever model is active |
| **Review surface** | Browser with inline comments | Terminal + plan file |
| **Execution options** | Web PR or terminal teleport | Local AA-MA workflow |

## They're Complementary

The two features solve different problems:

- **Anthropic's Ultraplan** is about *where* planning happens — offloading to the cloud for async, browser-based review
- **Our `/aa-ma-plan`** is about *how* planning happens — structured methodology with brainstorming, research, verification, and artifact generation

You could use Anthropic's Ultraplan to draft a rough plan, then feed it into `/aa-ma-plan` to apply AA-MA methodology with structured artifacts.

## Resolution

Renamed our command from `/ultraplan` to `/aa-ma-plan` to:
1. Avoid collision with the built-in feature
2. Align with the existing AA-MA ecosystem naming (`/execute-aa-ma-*`, `/archive-aa-ma`)
3. Clearly signal AA-MA methodology ownership

The skill was renamed from `ultraplan-workflow` to `aa-ma-plan-workflow`. All cross-references across commands, skills, agents, specs, and documentation were updated.

## Migration for Existing Users

If you previously ran `scripts/install.sh`, you'll have a dangling `~/.claude/commands/ultraplan.md` symlink. To update:

```bash
rm ~/.claude/commands/ultraplan.md  # remove old symlink
./scripts/install.sh                 # creates new aa-ma-plan.md symlink
```
