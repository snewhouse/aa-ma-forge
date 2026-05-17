# Agent Token Optimization Reference

Immutable facts and constants for this optimization task.

## Baseline Metrics (Pre-Optimization)

- **Warning Message:** `Large cumulative agent descriptions will impact performance (~18.8k tokens > 15.0k)`
- **Total Agents:** 178
- **Total Words:** ~222,000
- **Estimated Tokens:** ~288,000 (full content), ~18,800 (descriptions)
- **Target Threshold:** 15,000 tokens
- **Required Reduction:** ~3,800 tokens (~20%)

## Agent Locations

```
AGENTS_ROOT: /home/sjnewhouse/.claude/agents/awesome-claude-code-subagents/
CATEGORIES_DIR: /home/sjnewhouse/.claude/agents/awesome-claude-code-subagents/categories/
```

## Identified Duplicates

| Agent File | Location | Lines | Action |
|------------|----------|-------|--------|
| `sre.md` | `03-infrastructure/` | 354 | DELETE |
| `sre-engineer.md` | `03-infrastructure/` | 294 | KEEP |
| `wordpress-master.md` | `01-core-development/` | 336 | KEEP |
| `wordpress-master.md` | `08-business-product/` | 336 | DELETE |
| `incident-responder.md` | `03-infrastructure/` | 293 | KEEP (merge content) |
| `devops-incident-responder.md` | `03-infrastructure/` | 294 | DELETE (merge into above) |

## Post-Optimization Metrics (Phase 1)

- **Final Agent Count:** 175 (reduced from 178)
- **Agents Removed:** 3
  - `sre.md` (~1,000 tokens)
  - `wordpress-master.md` from 08-business-product (~900 tokens)
  - `devops-incident-responder.md` (~800 tokens, merged into incident-responder)
- **Estimated Token Savings:** ~2,700 tokens
- **Verification Status:** COMPLETE - Still exceeded threshold

## Post-Optimization Metrics (Phase 2)

- **Final Agent Count:** 154 (reduced from 175)
- **Agents Removed:** 31 (entire 11-marketing/ category)
- **Marketing Agents Deleted:**
  - brand-messaging/* (3 agents)
  - content-analytics/* (1 agent)
  - content-production/* (4 agents)
  - email-marketing/* (4 agents)
  - marketing-technology/* (3 agents)
  - pr-communications/* (3 agents)
  - social-media/* (5 agents)
  - Root level: content-strategist, conversion-optimizer, geo-strategist, seo-expert, seo-strategist (5 agents)
- **Estimated Token Savings:** ~5,000+ tokens
- **Total Reduction:** 178 → 154 agents (-24 counted, -34 total removed)
- **Verification Status:** PENDING - Requires Claude Code restart

## Tier Duplicates (Not Consolidated)

The following pairs were reviewed but NOT merged due to different toolsets and purposes:
- `react-expert` (MCP tools) vs `react-specialist` (build tools)
- `nextjs-expert` (MCP tools) vs `nextjs-developer` (deployment tools)
- Django and Angular pairs follow similar pattern

## Post-Optimization Metrics (Phase 3)

- **Final Agent Count:** 114 (reduced from 154)
- **Categories Removed:** 3
  - `07-specialized-domains/` (16 agents): blockchain, NFT, IoT, game dev, fintech, payment
  - `12-industry/` (13 agents): healthcare, fintech, education, government
  - `08-business-product/` (11 agents): PM, sales, legal, tech writer
- **Agents Removed This Phase:** 40
- **Estimated Token Savings:** ~6,300 tokens
- **Verification Status:** PENDING - Restart Claude Code

## Cumulative Results

| Phase | Action | Agents Removed | Running Total |
|-------|--------|----------------|---------------|
| Baseline | - | 0 | 178 |
| Phase 1 | Duplicates | 3 | 175 |
| Phase 2 | Marketing | 31 | 154* |
| Phase 3 | Specialized/Industry/Business | 40 | 114 |
| **Total** | | **64** | **114** |

*Note: Some agents were untracked files, actual counts may vary

**Estimated Total Token Savings:** ~14,000 tokens (from ~18.8K to ~4.8K)

_Last Updated: 2025-11-25_
