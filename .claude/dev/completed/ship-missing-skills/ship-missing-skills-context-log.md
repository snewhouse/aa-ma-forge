<!-- ARCHIVED: 2026-04-07 13:45 -->
<!-- Plan: ship-missing-skills - COMPLETE -->
<!-- Total Milestones: 4 | Duration: 2026-04-06 to 2026-04-07 -->

# ship-missing-skills Context Log

## [2026-04-06] Initial Context

**Trigger:** New-user experience audit revealed that AA-MA commands reference 5 custom assets not shipped in the repo. A fresh install produces broken `Skill()` calls.

**Key Decisions:**
- Ship our own skills (plan-verification, impact-analysis, system-mapping, retro) and grill-me command
- Document third-party deps (superpowers, gstack, Context7) — don't add guards, just document
- Use auto-discovery loop in install.sh for skills (not hardcoded entries)
- Copy then review approach (copy assets, audit for public-readiness)
- Exclude retro's SKILL.md.tmpl (template file, not shipped)

**Audit Findings (from conversation):**
- 5 assets missing from repo but referenced in commands
- 3 third-party plugin dependencies (superpowers, gstack, Context7 MCP) — optional, document only
- 1 broken file reference (verify-plan.md → missing design doc)
- grill-me concept adapted from Matt Pocock, our own implementation as command
- Commands already have fallback sections for when superpowers/Context7 unavailable

**Remaining Questions:** None — all decisions resolved via grill-me protocol.

## [2026-04-07] Session 2 — Dependency Closure & Brainstorm

**What was completed:**
- Shipped aa-ma-plan-workflow skill (434 lines + 10 references + 2 templates)
- Shipped operational-constraints skill (302 lines) + /ops-mode command (136 lines)
- Updated all spec docs (foundations, quick-reference, CHANGELOG) across multiple /double-check passes
- 4 /double-check passes total — each found progressively deeper gaps

**Key Decision: Ship all remaining skills**
- Approach: B then A — review each for quality first, then ship all organised by tier
- Reason: Stephen's bar is "would a senior engineer I respect be comfortable cloning this?" Quality is the gate, not secrecy.
- The 7 remaining skills are all Stephen's original work, exist in ~/.claude/skills/

**7 Skills Still To Ship (review first):**

| Skill | Lines | Tier | Phase |
|---|---|---|---|
| complexity-router | 233 | CORE | Phase 4 "Always" |
| agent-teams | 322 | CORE | Phase 3+5 "Always" |
| defense-in-depth | 127 | CORE | Phase 5 "Always" |
| senior-architect | 209 | ENHANCEMENT | Phase 4 ≥80% |
| llm-evaluation | 471 | ENHANCEMENT | Phase 4 quality gate |
| dispatching-parallel-agents | 184 | ENHANCEMENT | Phase 3 ≥3 domains |
| debugging-strategies | 473 | ENHANCEMENT | Error recovery |

**Other Outstanding:**
- verification.md: No anatomy, no template, no example (critical doc gap)
- Quick-reference: Add /ops-mode to cheat sheet
- Archive this AA-MA task when all milestones done

**Lessons Extracted:** L-193 through L-197 (shipping & completeness audits)
