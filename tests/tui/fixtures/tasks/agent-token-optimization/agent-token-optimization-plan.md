# Agent Token Optimization Plan

**Objective:** Reduce agent description tokens from ~18.8K to under 15K
**Owner:** sjnewhouse
**Created:** 2025-11-25
**Last Updated:** 2025-11-25

## Executive Summary

The Claude Code startup warning indicates agent descriptions total ~18.8K tokens, exceeding the 15K performance threshold. This plan consolidates 4 obvious duplicate agents to achieve a ~20% reduction with minimal disruption.

## Implementation Steps

### Milestone 1: Audit & AA-MA Setup
- Create AA-MA directory structure
- Document baseline metrics
- Generate agent inventory

### Milestone 2: Consolidate Obvious Duplicates
| Duplicate | Action | Est. Savings |
|-----------|--------|--------------|
| `sre.md` vs `sre-engineer.md` | Delete `sre.md` | ~1K tokens |
| `wordpress-master.md` (2 copies) | Delete from `08-business-product/` | ~1K tokens |
| `incident-responder.md` variants | Merge into single agent | ~1K tokens |
| Tier pairs (react/next/django/angular) | Clarify or merge | ~800 tokens |

### Milestone 3: Verify & Document
- Restart Claude Code (no warning)
- Test agent functionality
- Commit changes

## Success Criteria

1. Claude Code starts without token warning
2. All retained agents function correctly
3. Changes tracked in AA-MA artifacts
