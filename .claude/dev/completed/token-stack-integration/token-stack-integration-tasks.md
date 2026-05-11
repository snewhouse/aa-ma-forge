<!-- ARCHIVED: 2026-04-10 21:35 -->
<!-- Plan: token-stack-integration - COMPLETE -->
<!-- Total Milestones: 5 | Duration: 2026-04-10 to 2026-04-10 -->

# token-stack-integration Tasks (HTP)

_Hierarchical Task Planning roadmap with dependencies and state tracking._

## Milestone 1: Caveman-Inspired Output Compression Skill
- **Status:** COMPLETE
- **Gate:** SOFT
- **Dependencies:** None
- **Complexity:** 35%
- **Acceptance Criteria:**
  - Skill file exists at `claude-code/skills/token-compression/SKILL.md` with three intensity levels (lite, full, ultra)
  - aa-ma-execution skill references token-compression and maps AFK=ultra, HITL=lite
  - Vague token optimization language removed from operational-constraints, replaced with pointer to token-compression
  - `grep -q "lite\|full\|ultra" claude-code/skills/token-compression/SKILL.md` succeeds
  - `grep -ic "optimi.* token" claude-code/skills/operational-constraints/SKILL.md` returns 0 (British spelling: "Optimise")

### Step 1.1: Create token-compression skill
- **Status:** COMPLETE
- **Mode:** AFK
- **Dependencies:** None
- **Result Log:** Mode: AFK — auto-dispatched. Created `claude-code/skills/token-compression/SKILL.md` (73 lines). Three levels: lite/full/ultra. Caveman attribution included. Auto-clarity exceptions for security, irreversible ops. Code blocks exempt. All 5 acceptance criteria verified via grep.

### Step 1.2: Integrate with AA-MA execution modes
- **Status:** COMPLETE
- **Mode:** AFK
- **Dependencies:** Step 1.1
- **Result Log:** Mode: AFK — auto-dispatched. Added token-compression integration to `aa-ma-execution/SKILL.md` Section 7 (Mode-Based Execution Control). HITL→lite, AFK→ultra. Override via `/compress lite|full|ultra` documented. All 4 acceptance criteria verified.

### Step 1.3: Update operational-constraints
- **Status:** COMPLETE
- **Mode:** AFK
- **Dependencies:** Step 1.1
- **Result Log:** Mode: AFK — auto-dispatched. Replaced vague "Optimise token utilisation" in Section 1 with pointer to `Skill(token-compression)`. Updated Quick Reference Card and Activation Confirmation. `grep -ic "optimi.* token"` returns 0. 3 clean token-compression references added.

---

## Milestone 2: Hook Architecture Expansion
- **Status:** COMPLETE
- **Gate:** SOFT
- **Dependencies:** None
- **Complexity:** 45%
- **Acceptance Criteria:**
  - `claude-code/hooks/aa-ma-session-start.sh` exists and passes shellcheck
  - `claude-code/hooks/pre-compact-aa-ma.sh` passes shellcheck (after CHECKPOINT enhancement)
  - `scripts/install.sh --dry-run` lists both new hooks
  - SessionStart hook exits 0 with and without active tasks
  - PreCompact hook enhanced to write CHECKPOINT line to provenance.log
  - settings.json contains SessionStart hook registration after install
  - Re-running install.sh does not duplicate hook symlinks or settings.json entries

### Step 2.1: Create SessionStart hook
- **Status:** COMPLETE
- **Mode:** AFK
- **Dependencies:** None
- **Result Log:** Mode: AFK — auto-dispatched. Created `claude-code/hooks/aa-ma-session-start.sh` (62 lines). ShellCheck clean. Exits 0 with and without active tasks. Emits hidden context: task name, active milestone, next step. Execution time: 3ms. Pattern: caveman's stdout-as-hidden-context.

### Step 2.2: Enhance PreCompact hook with CHECKPOINT line
- **Status:** COMPLETE
- **Mode:** AFK
- **Dependencies:** None
- **Result Log:** Mode: AFK — auto-dispatched. No changes needed — existing `pre-compact-aa-ma.sh` already writes CHECKPOINT lines (line 79, added in commit 33764c0). Format matches AA-MA spec: `[timestamp] CHECKPOINT — ActiveStep: [id] — NextAction: "[desc]" — ContextLoaded: REFERENCE,TASKS — TokenUsage: N/A`. ShellCheck clean.

### Step 2.3: Register SessionStart hook + update install/uninstall scripts
- **Status:** COMPLETE
- **Mode:** AFK
- **Dependencies:** Step 2.1, Step 2.2
- **Result Log:** Mode: AFK — auto-dispatched. Updated `install.sh`: added symlink for session-start hook + jq-based settings.json registration (idempotent). Updated `uninstall.sh`: removes hook from settings.json on uninstall. Both scripts pass ShellCheck. `install.sh --dry-run` shows new hook in output. Also fixed session-start hook to check project-level `.claude/dev/active/` first (CWD), then HOME fallback.

---

## Milestone 3: Enhanced Search Command
- **Status:** COMPLETE
- **Gate:** SOFT
- **Dependencies:** None
- **Complexity:** 25%
- **Acceptance Criteria:**
  - Command file exists at `claude-code/commands/aa-ma-search.md`
  - Command supports `--active`, `--completed`, `--all` scope flags
  - Returns results sorted by term frequency
  - Returns empty result set gracefully when no matches found
  - `docs/spec/aa-ma-specification.md` contains "Cross-Task Search" section
  - Semantic search noted as future roadmap in spec

### Step 3.1: Create aa-ma-search command
- **Status:** COMPLETE
- **Mode:** AFK
- **Dependencies:** None
- **Result Log:** Mode: AFK — auto-dispatched. Created `claude-code/commands/aa-ma-search.md` (117 lines). Supports --active/--completed/--all scopes. Searches reference.md, context-log.md, tasks.md. Results grouped by task with match count. Empty results handled gracefully. Semantic search noted as future roadmap.

### Step 3.2: Document search in specification
- **Status:** COMPLETE
- **Mode:** AFK
- **Dependencies:** Step 3.1
- **Result Log:** Mode: AFK — auto-dispatched. Added Section XIII "Cross-Task Search" to `docs/spec/aa-ma-specification.md` (35 lines). Documents scope flags, target files, limitations, and future semantic search roadmap. Section numbering preserved (inserted before References).

---

## Milestone 4: Temporal Validity in Reference Files
- **Status:** COMPLETE
- **Gate:** SOFT
- **Dependencies:** None
- **Complexity:** 20%
- **Acceptance Criteria:**
  - Three temporal marker formats defined in `docs/spec/aa-ma-specification.md`: `[valid: YYYY-MM-DD]`, `[valid: YYYY-MM-DD to YYYY-MM-DD]`, `[superseded: YYYY-MM-DD by task-name]`
  - Markers documented as optional (backward compatible)
  - Scribe agent at `claude-code/agents/aa-ma-scribe.md` includes temporal marker instruction
  - `docs/templates/reference-template.md` contains examples of all three formats
  - Existing reference.md files without markers remain valid

### Step 4.1: Define temporal marker convention
- **Status:** COMPLETE
- **Mode:** HITL
- **Dependencies:** None
- **Result Log:** HITL gate: user approved 3-format syntax (valid, valid range, superseded). Added "Temporal Validity Markers" subsection to spec Section II (Immutable Reference Store). Updated scribe agent extraction rules with marker instruction. Updated reference template with examples section.

### Step 4.2: Update reference.md template
- **Status:** COMPLETE
- **Mode:** AFK
- **Dependencies:** Step 4.1
- **Result Log:** Mode: AFK — auto-dispatched. Added "Temporal Validity Convention" section to `docs/templates/reference-template.md` with 4 example entries showing all 3 marker formats. Backward compatible — section uses HTML comments explaining optional nature.

---

## Milestone 5: README Companion Tools Section
- **Status:** COMPLETE
- **Gate:** SOFT
- **Dependencies:** Milestone 1, Milestone 2, Milestone 3, Milestone 4
- **Complexity:** 15%
- **Acceptance Criteria:**
  - README.md contains "Companion Tools & Ecosystem" section with RTK, Caveman, MemPalace descriptions and links
  - Attribution subsection lists what AA-MA adopted from each tool
  - No marketing language or superlatives in section
  - All hardcoded asset counts updated in README.md, CHANGELOG.md, SECURITY.md, `docs/spec/claude-code-foundations.md`, `docs/spec/aa-ma-quick-reference.md`
  - Tier 6 doc-drift check passes clean (no stale counts)
  - CHANGELOG.md has entry for new assets

### Step 5.1: Write companion tools section
- **Status:** COMPLETE
- **Mode:** HITL
- **Dependencies:** Milestone 1, Milestone 2, Milestone 3, Milestone 4
- **Result Log:** HITL gate: user approved content preview. Added "Companion tools and the token stack" section to README.md (28 lines) between "Optional extras" and "Credits". Token stack diagram, 3-tool table (RTK/Caveman/MemPalace), "What we adopted" subsection with attribution. Humanised via stephen-newhouse-voice skill (active voice, UK English, no AI patterns, Stephen's directness).

### Step 5.2: Update asset counts
- **Status:** COMPLETE
- **Mode:** AFK
- **Dependencies:** Step 5.1
- **Result Log:** Mode: AFK — auto-dispatched. Updated counts in: `docs/spec/claude-code-foundations.md` (Commands 8→9, Skills 12→13, Hooks 1→2 with new entries in tables), `SECURITY.md` (same counts + hook list), `README.md` (added token-compression to Skills table, aa-ma-search to Commands table), `CHANGELOG.md` (added Unreleased section with 7 Added + 5 Changed entries). Quick reference had no hardcoded counts. Stale count sweep: clean across active docs.
