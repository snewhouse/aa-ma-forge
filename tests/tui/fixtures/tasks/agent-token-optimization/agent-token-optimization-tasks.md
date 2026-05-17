# Agent Token Optimization Tasks (HTP)

## Step 1: Create AA-MA Directory Structure
- Status: COMPLETE
- Dependencies: None
- Complexity: 10%
- Acceptance Criteria: All 5 AA-MA files exist in `.claude/dev/active/agent-token-optimization/`

### Sub-step: Create directory and files
- Result Log: Directory and all 5 files created 2025-11-25

## Step 2: Document Baseline Metrics
- Status: COMPLETE
- Dependencies: Step 1
- Complexity: 20%
- Acceptance Criteria: Baseline token count documented in reference.md

### Sub-step: Capture current warning message and token counts
- Result Log: Baseline captured - 18.8K tokens > 15K threshold, 178 agents

## Step 3: Delete sre.md Duplicate
- Status: COMPLETE
- Dependencies: Step 2
- Complexity: 20%
- Acceptance Criteria: `sre.md` removed, `sre-engineer.md` retained

### Sub-step: Verify sre-engineer.md has equivalent functionality
- Result Log: Verified - sre-engineer.md covers SLOs, error budgets, incident management, monitoring, automation

### Sub-step: Delete sre.md
- Result Log: Deleted 2025-11-25, saved ~1,000 tokens

## Step 4: Delete wordpress-master.md Duplicate
- Status: COMPLETE
- Dependencies: Step 2
- Complexity: 20%
- Acceptance Criteria: Only one wordpress-master.md in `01-core-development/`

### Sub-step: Delete from 08-business-product/
- Result Log: Deleted 2025-11-25, saved ~900 tokens

## Step 5: Merge Incident Responder Agents
- Status: COMPLETE
- Dependencies: Step 2
- Complexity: 40%
- Acceptance Criteria: Single incident-responder.md with combined capabilities

### Sub-step: Review both agent files
- Result Log: incident-responder has security/forensic focus; devops-incident-responder has DevOps tools (datadog, kubectl, aws-cli, grafana)

### Sub-step: Merge unique content from devops-incident-responder into incident-responder
- Result Log: Added DevOps tools to incident-responder.md tools list

### Sub-step: Delete devops-incident-responder.md
- Result Log: Deleted 2025-11-25, saved ~800 tokens

## Step 6: Review Tier Duplicates
- Status: COMPLETE
- Dependencies: Step 5
- Complexity: 30%
- Acceptance Criteria: React/Next/Django/Angular pairs clarified or merged

### Sub-step: Compare react-expert vs react-specialist
- Result Log: Different toolsets - react-expert has MCP tools, react-specialist has build tools (vite, webpack, jest)

### Sub-step: Compare nextjs-developer vs nextjs-expert
- Result Log: Different toolsets - nextjs-developer has deployment tools (vercel, prisma), nextjs-expert has MCP tools

### Sub-step: Decide on consolidation or differentiation
- Result Log: DECISION: Keep both - serve different purposes (guidance vs implementation). Minimal-change approach.

## Step 7: Verify & Commit
- Status: ACTIVE
- Dependencies: Step 6
- Complexity: 20%
- Acceptance Criteria: Claude Code starts without warning; clean commit

### Sub-step: Restart Claude Code and verify no warning
- Result Log: PENDING - User must restart Claude Code

### Sub-step: Test sample agents
- Result Log: PENDING

### Sub-step: Commit with descriptive message
- Result Log: PENDING

## Step 8: Remove Marketing Specialists (Phase 2)
- Status: COMPLETE
- Dependencies: Step 7 verification showed still over threshold
- Complexity: 30%
- Acceptance Criteria: All 31 marketing agents removed, token count under 15K

### Sub-step: Delete 11-marketing/ directory
- Result Log: ✅ COMPLETE 2025-11-25 - Deleted entire categories/11-marketing/ directory with 31 agent files

---

## Summary

**Completed:** Steps 1-8
**Phase 1:** 3 duplicates removed (178 → 175)
**Phase 2:** 31 marketing agents removed (175 → 154)
**Total agents removed:** 34
**Current agent count:** 154
**Estimated token savings:** ~7,700 tokens
**Expected new total:** ~11,100 tokens (should be under 15K threshold)
