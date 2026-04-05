# AA-MA Team Guide - Context Log

## [2025-11-26] Initial Planning Session

**Planning Method:** Brainstorming skill with Socratic questioning

**Key Decisions:**

1. **Audience**: Mixed experience levels (progressive depth)
   - Rationale: Team has both newcomers and experienced users
   - Implication: Need Quick Start for beginners, advanced sections for experts

2. **Structure**: "Principles first, then tool sections"
   - Rationale: Cleaner separation than side-by-side columns
   - Alternatives rejected: Parallel columns (repetitive), unified with callouts (complex formatting)

3. **Cursor Coverage**: Equal to Claude Code
   - Rationale: Team actively uses both tools
   - Key insight: AA-MA and Memory Banks are structurally equivalent

4. **Examples**: Generic/fictional (not project-specific)
   - Rationale: Wider applicability, avoids exposing internal projects

5. **Format**: Quick Reference Card + Detailed Guide
   - Rationale: Serves both quick lookups and deep learning

**Research Conducted:**
- Explored existing AA-MA documentation in codebase (comprehensive, ~2000+ lines)
- Researched Cursor Memory Banks via web search
- Found direct mapping between AA-MA 5-file system and Cursor 6-file system

**Pain Points Identified:**
1. Context loss between sessions
2. Inconsistent approaches across team
3. Unclear when to use AA-MA vs ad-hoc

---

## [2025-11-26] Implementation Complete

**Deliverables Created:**
1. `docs/aa-ma-team-guide.md` - Comprehensive guide (~1200 lines)
   - Part 0: Quick Start (5-minute intro)
   - Part 1: AA-MA Principles (tool-agnostic)
   - Part 2: Claude Code Implementation
   - Part 3: Cursor Implementation
   - Part 4: Decision Framework (when to use AA-MA)
   - Part 5: Team Collaboration
   - Appendix: Troubleshooting & FAQ

2. `docs/aa-ma-quick-reference.md` - 2-page cheat sheet
   - Page 1: Workflow diagram, 5 files, principles, decision matrix
   - Page 2: Commands for Claude Code and Cursor, file mappings

**Key Design Decisions:**
- Structure: "Principles first, then tool sections" (cleaner than parallel columns)
- Examples: Generic/fictional (wider applicability)
- Depth: Progressive (beginner → advanced)

**Sources Used:**
- Cursor Memory Banks: https://www.lullabot.com/articles/supercharge-your-ai-coding-cursor-rules-and-memory-banks
- Cursor Rules: https://docs.cursor.com/context/rules
- cursor-bank npm package: https://github.com/tacticlaunch/cursor-bank

---
