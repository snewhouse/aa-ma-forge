<!-- ARCHIVED: 2026-04-10 21:35 -->
<!-- Plan: token-stack-integration - COMPLETE -->
<!-- Total Milestones: 5 | Duration: 2026-04-10 to 2026-04-10 -->

# token-stack-integration Context Log

_This log captures architectural decisions, trade-offs, and unresolved issues._

## [2026-04-10] Initial Context

**Feature Request (Phase 1):**

Stephen installed RTK and wanted to evaluate how all four community tools (RTK, Caveman, MemPalace, and AA-MA) compose together. The goal is to cherry-pick the best patterns from each tool and integrate them into AA-MA Forge, making it more autonomous, more token-efficient, more searchable, and better documented -- without adding runtime dependencies.

**Key Decisions (Phase 2 Brainstorming via /grill-me):**

- **Decision AD-001:** Fork caveman's communication mode skill into AA-MA
  - **Rationale:** HITL/AFK intensity mapping is a feature caveman cannot provide. AA-MA already has the execution mode infrastructure to drive compression levels dynamically.
  - **Alternatives Considered:** (a) Use caveman directly as a companion, (b) Skip output compression entirely, (c) Create compression from scratch
  - **Trade-offs:** Forking means maintaining our own copy, but gains tight integration with HITL/AFK modes. Using caveman directly would mean two plugins competing for prompt space.

- **Decision AD-002:** Skip caveman-commit, caveman-review, and compress CLI
  - **Rationale:** AA-MA has its own commit conventions (/commit-and-push, conventional commits, AA-MA commit signatures) and review workflows. Importing caveman's would create conflicts and duplication.
  - **Alternatives Considered:** Adopt caveman wholesale
  - **Trade-offs:** Leaves some caveman features unused, but avoids convention conflicts.

- **Decision AD-003:** Enhanced grep/BM25 search now, vector DB later
  - **Rationale:** Current scale (<100 task files) does not justify ChromaDB dependency. Grep-based search with term frequency sorting is sufficient and adds zero dependencies.
  - **Alternatives Considered:** (a) ChromaDB like MemPalace, (b) SQLite FTS5, (c) No search at all
  - **Trade-offs:** Loses semantic search capability but maintains KISS principle. Vector DB can be added when scale demands it.

- **Decision AD-004:** Cross-project memory bank is future roadmap (YAGNI)
  - **Rationale:** MemPalace's cross-session ChromaDB knowledge graph is impressive but adds significant complexity. AA-MA's file-per-task architecture handles the current use case.
  - **Alternatives Considered:** Adopt MemPalace's memory MCP tools
  - **Trade-offs:** No cross-project knowledge sharing, but no new runtime dependency either.

- **Decision AD-005:** Learn hook patterns from all 3 tools, apply to AA-MA
  - **Rationale:** RTK uses PreToolUse hooks, Caveman uses activation scripts, MemPalace uses save hooks. SessionStart and Stop hooks would make AA-MA more autonomous (auto-detect tasks, auto-checkpoint).
  - **Alternatives Considered:** Manual task detection only
  - **Trade-offs:** Hooks add shell script maintenance but reduce manual ceremony at session boundaries.

- **Decision AD-006:** Temporal validity markers via markdown convention
  - **Rationale:** Reference.md facts go stale silently. Simple date markers (`[valid: YYYY-MM-DD]`) let agents assess fact freshness without any tooling changes.
  - **Alternatives Considered:** (a) Metadata database, (b) Git blame integration, (c) No validity tracking
  - **Trade-offs:** Relies on agents to apply markers consistently (mitigated by scribe agent prompt). Zero tooling change.

- **Decision AD-007:** README companion tools section
  - **Rationale:** Minimal effort, high SEO value, honest documentation of the ecosystem. Attribution is the right thing to do.
  - **Alternatives Considered:** Separate ecosystem docs page
  - **Trade-offs:** README gets longer, but companion tools context helps users understand the token stack.

- **Decision AD-008:** Zero new runtime dependencies (KISS)
  - **Rationale:** AA-MA's pure-markdown architecture is its differentiator. Adding ChromaDB, SQLite, or Node.js dependencies would undermine the simplicity that makes it portable and debuggable.
  - **Alternatives Considered:** Add ChromaDB for semantic search, add SQLite for structured queries
  - **Trade-offs:** Limits search and memory capabilities but preserves the "just files" philosophy.

- **Decision AD-009:** Branch strategy -- work on expt/rocket_mems_playground
  - **Rationale:** Experimental integration work belongs on an experimental branch, not main.
  - **Alternatives Considered:** Feature branch per milestone
  - **Trade-offs:** Single branch is simpler but makes per-milestone rollback slightly harder (git revert vs branch delete).

**Research Findings (Phase 3 -- Deep Code Analysis):**

- Caveman's SKILL.md uses a tiered prompt injection approach: "casual" drops pleasantries, "focused" drops articles and hedging, "compressed" uses abbreviated syntax. Directly adaptable.
- MemPalace's `mempal_save_hook.sh` writes to ChromaDB on session end. The checkpoint pattern (timestamp + state) is adoptable without the DB.
- RTK's PreToolUse hook rewrites CLI commands (e.g., `git status` becomes `rtk git status`) for token compression. Already installed; no changes needed in AA-MA.
- Caveman's `caveman-activate.js` uses PostToolUse to inject compression prompt. AA-MA's SessionStart hook can achieve similar effect via stdout hidden context.
- All three tools are April 2026 community projects. Repo stability is unknown; links should reference specific commits.

**Remaining Questions / Unresolved Issues:**

- Claude Code SessionStart hook API: Exact stdout/stderr behavior needs verification during M2 implementation. SessionStart stdout should become hidden system context, but this needs empirical testing.
- Compression effectiveness measurement: No built-in way to measure actual token savings. RTK has `rtk gain`; AA-MA will not have an equivalent. Accepted as out of scope.
- Scribe agent compliance with temporal markers: Will agents consistently apply `[valid:]` markers? Only observable after deployment. Mitigation: prompt instruction + review during first few tasks.

---

## [2026-04-10] Post-Creation Verification — 4 CRITICALs Fixed

**Verification agents:** aa-ma-validator (5-dimension check) + Plan verifier (6-angle adversarial)

**Validator result:** PASS WITH WARNINGS (33/33 checks pass, 1 warning)
**Verifier result:** 4 CRITICAL, 8 WARNING, 5 INFO

### CRITICALs Found and Fixed:

1. **Wrong scribe agent path** — All files referenced `claude-code/agents/aa-ma-scribe/AGENT.md` but actual file is `claude-code/agents/aa-ma-scribe.md` (flat file, not directory). **Fixed** in plan.md, reference.md, tasks.md.

2. **install.sh cannot register hooks in settings.json** — It only creates symlinks. Hooks must also be registered in `~/.claude/settings.json` to fire on events. **Fixed** by specifying `jq`-based settings.json modification in Step 2.3 acceptance criteria.

3. **Stop event fires after EVERY response, not session end** — Would spam provenance.log with checkpoint lines. **Fixed** by replacing separate Stop hook with enhancement to existing PreCompact hook (which fires at context compression — a natural checkpoint moment). Step 2.2 changed from "Create Stop hook" to "Enhance PreCompact hook with CHECKPOINT line."

4. **Untestable timeout criterion** — "Does not hang" is not falsifiable. **Fixed** by replacing with specific `timeout 5 bash` command assertion.

### Key WARNINGs acknowledged (non-blocking):
- Step 1.3 grep test uses exact text match — verify actual text in operational-constraints before execution
- "BM25-like ranking" in search command is LLM-interpreted, not algorithmic — documented accurately
- Hook symlinks in install.sh are hardcoded, not auto-discovered — must add explicit lines

---

## [2026-04-10] Milestone 1 Completion: Caveman-Inspired Output Compression Skill
- Status: COMPLETE
- Key outcome: Created `token-compression` skill with 3 intensity levels (lite/full/ultra), integrated with AA-MA execution modes (HITL→lite, AFK→ultra), and replaced vague token directives in operational-constraints with specific skill pointer.
- Artifacts: Created `claude-code/skills/token-compression/SKILL.md` (73 lines). Modified `claude-code/skills/aa-ma-execution/SKILL.md` (Section 7) and `claude-code/skills/operational-constraints/SKILL.md` (Section 1, Quick Ref, Activation).
- Tests: 5/5 acceptance criteria verified via grep. Impact analysis: LOW risk (all additive changes).

---

## [2026-04-10] Milestone 2 Completion: Hook Architecture Expansion
- Status: COMPLETE
- Key outcome: Created SessionStart hook that auto-detects active AA-MA tasks and emits hidden context (task name, milestone, step). Enhanced install.sh with jq-based settings.json registration. Fixed hook to check project-level `.claude/dev/active/` first, HOME fallback. PreCompact CHECKPOINT already existed from commit 33764c0.
- Artifacts: Created `claude-code/hooks/aa-ma-session-start.sh` (65 lines). Modified `scripts/install.sh` (+43 lines: symlink + settings.json registration). Modified `scripts/uninstall.sh` (+22 lines: settings.json cleanup).
- Tests: 7/7 acceptance criteria verified. ShellCheck clean on all 3 scripts. Hook exits 0 with/without active tasks. Execution time: 3ms.

---

## [2026-04-10] Milestone 3 Completion: Enhanced Search Command
- Status: COMPLETE
- Key outcome: Created `/aa-ma-search` command with --active/--completed/--all scope flags. Added Section XIII (Cross-Task Search) to specification documenting scope, target files, limitations, and future semantic search roadmap.
- Artifacts: Created `claude-code/commands/aa-ma-search.md` (117 lines). Modified `docs/spec/aa-ma-specification.md` (+35 lines, Section XIII).
- Tests: 6/6 acceptance criteria verified.

---

## [2026-04-10] Milestone 4 Completion: Temporal Validity in Reference Files
- Status: COMPLETE
- Key outcome: Defined 3 temporal marker formats ([valid: date], [valid: range], [superseded: date by task]). Convention added to spec, template, and scribe agent. All optional and backward compatible. HITL gate: user approved 3-format syntax.
- Artifacts: Modified `docs/spec/aa-ma-specification.md` (Section II), `docs/templates/reference-template.md`, `claude-code/agents/aa-ma-scribe.md`.
- Tests: 5/5 acceptance criteria verified.

---

## [2026-04-10] Milestone 5 Completion: README Companion Tools Section (FINAL)
- Status: COMPLETE
- Key outcome: Added "Companion tools and the token stack" section to README with token stack diagram, 3-tool table, and attribution subsection. Humanised via stephen-newhouse-voice skill. Updated asset counts across 4 documentation files (README, SECURITY, foundations, CHANGELOG). All stale counts resolved.
- Artifacts: Modified `README.md`, `CHANGELOG.md`, `SECURITY.md`, `docs/spec/claude-code-foundations.md`.
- Tests: 6/6 acceptance criteria verified.
- ALL 5 MILESTONES COMPLETE.
