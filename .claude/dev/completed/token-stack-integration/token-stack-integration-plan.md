<!-- ARCHIVED: 2026-04-10 21:35 -->
<!-- Plan: token-stack-integration - COMPLETE -->
<!-- Total Milestones: 5 | Duration: 2026-04-10 to 2026-04-10 -->

# token-stack-integration Plan

**Objective:** Integrate token optimization patterns from RTK, Caveman, and MemPalace into AA-MA Forge with zero new runtime dependencies.
**Owner:** AI + Stephen Newhouse
**Created:** 2026-04-10
**Last Updated:** 2026-04-10

## Executive Summary

Integrate token optimization patterns from RTK, Caveman, and MemPalace into AA-MA Forge. Five milestones: (1) fork caveman's communication skill with HITL/AFK intensity, (2) add SessionStart+Stop hooks, (3) create enhanced grep search command, (4) add temporal validity markers to reference.md spec, (5) write README companion tools section. Zero new runtime dependencies. ~35% overall complexity.

## Implementation Steps

### Milestone 1: Caveman-Inspired Output Compression Skill

**Goal:** Create native AA-MA skill that reduces output tokens using caveman-style prompt patterns, with intensity tuned to HITL/AFK execution mode.
**Gate:** SOFT
**Complexity:** 35%
**Measurable Goal:** Skill file exists, is referenced by execution modes, and provides three intensity levels mapped to HITL/AFK.

#### Step 1.1: Create token-compression skill

Create `claude-code/skills/token-compression/SKILL.md` with three intensity levels:
- **lite** = HITL mode (preserve clarity for interactive sessions)
- **full** = general use
- **ultra** = AFK mode (maximum compression for autonomous execution)

Prompt patterns forked from caveman's `SKILL.md` with attribution. Rules: drop articles/filler/pleasantries/hedging. Auto-clarity exceptions for security warnings and irreversible actions. Code blocks always rendered normally (never compressed).

**Acceptance Criteria:**
- File exists at `claude-code/skills/token-compression/SKILL.md`
- Contains three named intensity levels (lite, full, ultra) with distinct prompt directives
- Includes attribution to caveman project
- Auto-clarity exceptions documented for security and irreversible actions
- Code blocks explicitly exempted from compression

**Required Artifacts:** `claude-code/skills/token-compression/SKILL.md`

#### Step 1.2: Integrate with AA-MA execution modes

Update `claude-code/skills/aa-ma-execution/SKILL.md` to reference token-compression skill. Map AFK tasks to ultra compression, HITL tasks to lite. Support manual override via `/compress lite|full|ultra`.

**Acceptance Criteria:**
- aa-ma-execution skill references token-compression by name
- AFK mode maps to ultra intensity
- HITL mode maps to lite intensity
- Manual override syntax documented

**Required Artifacts:** Modified `claude-code/skills/aa-ma-execution/SKILL.md`

#### Step 1.3: Update operational-constraints

Replace vague "optimize token utilization" directive in `claude-code/skills/operational-constraints/SKILL.md` with pointer to token-compression skill. No duplicate directives between the two files.

**Acceptance Criteria:**
- Vague token optimization language removed from operational-constraints
- Single pointer to token-compression skill added
- No directive duplication between operational-constraints and token-compression
- `grep -c "token" claude-code/skills/operational-constraints/SKILL.md` shows reduced, focused references

**Required Artifacts:** Modified `claude-code/skills/operational-constraints/SKILL.md`

**Tests for Milestone 1:**
- `test -f claude-code/skills/token-compression/SKILL.md` passes
- `grep -q "lite\|full\|ultra" claude-code/skills/token-compression/SKILL.md` finds all three levels
- `grep -q "token-compression" claude-code/skills/aa-ma-execution/SKILL.md` confirms integration
- `grep -ic "optimi.* token" claude-code/skills/operational-constraints/SKILL.md` returns 0 (vague directive removed — note: current text uses British "Optimise token utilisation")

**Rollback:** Delete `claude-code/skills/token-compression/` directory, revert changes to operational-constraints and aa-ma-execution skills.

**Risks:**
1. Prompt conflict between skills (duplicate/contradictory directives) -- Mitigation: remove vague, replace with specific pointer
2. Confusing unfamiliar users with ultra-compressed output -- Mitigation: auto-clarity exceptions for security, irreversible actions, errors
3. Ultra mode strips error context -- Mitigation: errors always rendered with exact messages, never compressed

---

### Milestone 2: Hook Architecture Expansion

**Goal:** Add SessionStart hook and enhance PreCompact hook to auto-detect active tasks and auto-checkpoint.
**Gate:** SOFT
**Complexity:** 45%
**Measurable Goal:** SessionStart hook installed and registered, emits hidden context for active tasks. PreCompact hook enhanced to write CHECKPOINT line to provenance.log.

#### Step 2.1: Create SessionStart hook

Create `claude-code/hooks/aa-ma-session-start.sh`. Behavior:
- Detect active tasks in `.claude/dev/active/`
- Emit hidden system context with task name, current step, active milestone
- Zero overhead if no active task exists
- Always exit 0 (never block session start)
- Pattern inspired by caveman's `caveman-activate.js`

**Acceptance Criteria:**
- File exists at `claude-code/hooks/aa-ma-session-start.sh`
- Script is executable (`chmod +x`)
- Exits 0 when no active tasks exist
- Exits 0 when active tasks exist (outputs hidden context to stdout)
- Outputs task name and current step from tasks.md when active task detected
- Execution time <100ms on empty and single-task cases

**Required Artifacts:** `claude-code/hooks/aa-ma-session-start.sh`

#### Step 2.2: Create PreCompact-based session checkpoint hook

Create checkpoint logic within the EXISTING `claude-code/hooks/pre-compact-aa-ma.sh` hook (which already fires on PreCompact events). Add a CHECKPOINT entry to provenance.log alongside the existing snapshot logic.

**Important:** Claude Code's `Stop` event fires after EVERY assistant response — NOT at session end. Using it would spam provenance.log with hundreds of checkpoint lines per session. Instead, we leverage the existing PreCompact hook (which fires when context is being compressed — a natural checkpoint moment) and add a lightweight CHECKPOINT line.

**Acceptance Criteria:**
- `pre-compact-aa-ma.sh` already writes to provenance.log (confirmed in code)
- CHECKPOINT line format matches AA-MA spec: `[TIMESTAMP] CHECKPOINT — ActiveStep: [id] — NextAction: "[desc]" — ContextLoaded: [files] — TokenUsage: [%]`
- No new hook file needed — enhancement to existing hook
- `timeout 5 bash claude-code/hooks/pre-compact-aa-ma.sh` exits 0

**Required Artifacts:** Modified `claude-code/hooks/pre-compact-aa-ma.sh`

#### Step 2.3: Register SessionStart hook and update install/uninstall scripts

Add SessionStart hook symlink AND settings.json registration. The hook must be both deployed (symlink) AND registered (settings.json entry) to fire on events.

**Important:** install.sh currently only creates symlinks for hooks — it does NOT modify settings.json. For the SessionStart hook to fire, we must add a `jq`-based settings.json modifier to install.sh (similar to how RTK's `rtk init` patches settings.json).

**Acceptance Criteria:**
- `scripts/install.sh` creates symlink for SessionStart hook
- `scripts/install.sh` adds SessionStart hook entry to `~/.claude/settings.json` using `jq` (idempotent — checks before adding)
- `scripts/uninstall.sh` removes SessionStart symlink and settings.json entry
- `scripts/install.sh --dry-run` shows new hook in preview
- Re-running install.sh does not create duplicate symlinks or settings.json entries
- Existing PreCompact hook registration is not disturbed

**Required Artifacts:** Modified `scripts/install.sh`, modified `scripts/uninstall.sh`

**Tests for Milestone 2:**
- `shellcheck claude-code/hooks/aa-ma-session-start.sh` passes
- `shellcheck claude-code/hooks/pre-compact-aa-ma.sh` passes (after checkpoint enhancement)
- `scripts/install.sh --dry-run` lists SessionStart hook
- `jq '.hooks.SessionStart' ~/.claude/settings.json` shows the new hook entry after install
- Manual test: start new session with active task, verify hidden context emitted

**Rollback:** Delete hook scripts, revert install.sh and uninstall.sh to previous state.

**Risks:**
1. Hook conflicts with other Claude Code plugins (RTK, etc.) -- Mitigation: hooks are additive, not exclusive; always exit 0
2. Stop hook may not fire on abrupt termination -- Mitigation: existing PreCompact hook remains as safety net
3. SessionStart adds startup latency -- Mitigation: shell script implementation, measured <100ms target

---

### Milestone 3: Enhanced Search Command

**Goal:** Create `/aa-ma-search` command that searches across all active and completed task files with basic ranking.
**Gate:** SOFT
**Complexity:** 25%
**Measurable Goal:** Command exists, searches active/completed directories, returns ranked results.

#### Step 3.1: Create aa-ma-search command

Create `claude-code/commands/aa-ma-search.md`. Behavior:
- Search `.claude/dev/active/` and `.claude/dev/completed/`
- Target reference.md, context-log.md, tasks.md files
- Scope options: `--active`, `--completed`, `--all` (default: `--active`)
- Sort results by term frequency (basic BM25-like ranking)
- Output: file path, matching lines, match count

**Acceptance Criteria:**
- File exists at `claude-code/commands/aa-ma-search.md`
- Command accepts a search term argument
- Supports `--active`, `--completed`, `--all` scope flags
- Returns results sorted by relevance (match frequency)
- Returns empty result set gracefully (no error) when no matches found
- Searches reference.md, context-log.md, and tasks.md files (not provenance.log by default)

**Required Artifacts:** `claude-code/commands/aa-ma-search.md`

#### Step 3.2: Document search in specification

Add "Cross-Task Search" section to `docs/spec/aa-ma-specification.md`. Document the command, scope options, and ranking behavior. Note semantic/vector search as future roadmap item.

**Acceptance Criteria:**
- New section exists in aa-ma-specification.md titled "Cross-Task Search" or equivalent
- Documents command syntax and scope options
- Notes semantic search as future enhancement
- Does not break existing spec section numbering/references

**Required Artifacts:** Modified `docs/spec/aa-ma-specification.md`

**Tests for Milestone 3:**
- `test -f claude-code/commands/aa-ma-search.md` passes
- `grep -q "Cross-Task Search" docs/spec/aa-ma-specification.md` confirms spec section exists
- Manual test: run `/aa-ma-search` with a known term from an active task

**Rollback:** Delete command file, revert specification changes.

**Risks:**
1. Slow at scale -- Mitigation: grep-based search is <10ms at current scale (<100 files)
2. Users expect semantic search -- Mitigation: document clearly as keyword search, note vector DB as future roadmap

---

### Milestone 4: Temporal Validity in Reference Files

**Goal:** Add lightweight date marker convention to reference.md entries for tracking fact freshness.
**Gate:** SOFT
**Complexity:** 20%
**Measurable Goal:** Convention defined in spec, template updated with examples, scribe agent instructed to apply markers.

#### Step 4.1: Define temporal marker convention (HITL)

Define three marker formats:
- `[valid: YYYY-MM-DD]` -- fact valid from this date
- `[valid: YYYY-MM-DD to YYYY-MM-DD]` -- fact valid within date range
- `[superseded: YYYY-MM-DD by task-name]` -- fact replaced by newer task

Markers are optional and backward compatible (existing reference.md files without markers remain valid). Update specification, template, and scribe agent prompt.

**Acceptance Criteria:**
- Three marker formats defined in `docs/spec/aa-ma-specification.md`
- Markers documented as optional (backward compatible)
- Scribe agent prompt in `claude-code/agents/aa-ma-scribe.md` includes instruction to apply markers
- Convention does not break any existing reference.md files
- User approval obtained (HITL gate) on final marker syntax

**Required Artifacts:** Modified `docs/spec/aa-ma-specification.md`, modified `claude-code/agents/aa-ma-scribe.md`

#### Step 4.2: Update reference.md template

Add temporal marker examples to `docs/templates/reference-template.md`. Include a "Temporal Validity Convention" section showing all three formats with example usage.

**Acceptance Criteria:**
- Template contains examples of all three temporal marker formats
- Examples are realistic and self-documenting
- Section is clearly labeled "Temporal Validity Convention" or equivalent
- Template remains backward compatible (markers shown as optional)

**Required Artifacts:** Modified `docs/templates/reference-template.md`

**Tests for Milestone 4:**
- `grep -q "valid:" docs/spec/aa-ma-specification.md` confirms convention in spec
- `grep -q "superseded:" docs/templates/reference-template.md` confirms template updated
- `grep -q "valid:" claude-code/agents/aa-ma-scribe.md` confirms scribe agent updated
- Existing reference.md files pass any validation without temporal markers (backward compat)

**Rollback:** Revert specification, template, and scribe agent changes.

**Risks:**
1. Over-engineering the marker syntax -- Mitigation: markers are optional, three simple formats only
2. Agents forget to apply markers -- Mitigation: scribe agent prompt explicitly includes marker instruction

---

### Milestone 5: README Companion Tools Section

**Goal:** Add ecosystem documentation showing how RTK, Caveman, MemPalace complement AA-MA.
**Gate:** SOFT
**Complexity:** 15%
**Measurable Goal:** README has companion tools section, all hardcoded asset counts updated across docs.

#### Step 5.1: Write companion tools section (HITL)

Add "Companion Tools & Ecosystem" section to `README.md`:
- Brief descriptions of RTK, Caveman, MemPalace with links to their repos
- Token stack diagram showing how the tools compose
- "What AA-MA Adopted" subsection with specific attribution
- Honest, factual descriptions (no marketing language)
- Note "as of April 2026" for external repo references

**Acceptance Criteria:**
- New section exists in README.md titled "Companion Tools & Ecosystem" or equivalent
- RTK, Caveman, and MemPalace each have a brief description and repo link
- Attribution subsection lists what AA-MA adopted from each tool
- No marketing language, no superlatives
- User approval obtained (HITL gate) on final section content

**Required Artifacts:** Modified `README.md`

#### Step 5.2: Update asset counts

Update hardcoded counts in all affected files to reflect new assets (1 new skill, 2 new hooks, 1 new command):
- `README.md`
- `CHANGELOG.md`
- `SECURITY.md`
- `docs/spec/claude-code-foundations.md`
- `docs/spec/aa-ma-quick-reference.md`

Run Tier 6 doc-drift check to verify no stale counts remain.

**Acceptance Criteria:**
- All hardcoded asset counts updated in all 5 files
- `grep -rn` for old counts near relevant keywords returns zero matches
- Tier 6 doc-drift check passes clean
- CHANGELOG.md has entry for new assets under Unreleased section

**Required Artifacts:** Modified `README.md`, `CHANGELOG.md`, `SECURITY.md`, `docs/spec/claude-code-foundations.md`, `docs/spec/aa-ma-quick-reference.md`

**Tests for Milestone 5:**
- `grep -q "Companion Tools" README.md` confirms section exists
- Tier 6 doc-drift check reports no stale counts
- `grep -q "token-compression" CHANGELOG.md` confirms changelog entry
- Manual review: README section reads factually and has correct links

**Rollback:** Revert README and all count-updated files.

**Risks:**
1. External repos become unmaintained -- Mitigation: link specific commits, note "as of April 2026"
2. Count drift from other changes -- Mitigation: run asset count update last (Step 5.2 is final step)

---

## Verification Plan

1. Run `scripts/install.sh --dry-run` -- verify new hooks and skills appear in deployment preview
2. Run `scripts/install.sh` -- deploy and verify symlinks created correctly
3. Start new Claude Code session -- verify SessionStart hook emits hidden context for active task
4. Run `/aa-ma-search test` -- verify search returns results from active tasks
5. Run `shellcheck` on all new `.sh` files -- verify clean shell scripts
6. Run `/doc-sync` -- verify no documentation drift
7. Run `grep -r "token-compression" claude-code/ docs/` -- verify no broken cross-references

## Rollback Strategy

Each milestone is independently rollback-able:
- **M1:** Delete `claude-code/skills/token-compression/`, revert operational-constraints and aa-ma-execution
- **M2:** Delete hook scripts, revert install.sh and uninstall.sh
- **M3:** Delete command file, revert specification
- **M4:** Revert specification, template, and scribe agent changes
- **M5:** Revert README and all count-updated files

## Dependencies & Assumptions

- Caveman repo cloned at `~/github_private/caveman/` and accessible for reference
- MemPalace repo cloned at `~/github_private/mempalace/` and accessible for reference
- RTK installed and working (verified via `rtk --version`)
- Working branch: `expt/rocket_mems_playground`
- Current HEAD: commit `24aa245`
- No other active AA-MA plans in `.claude/dev/active/`
- Python environment managed by `uv` with `pyproject.toml`
- Claude Code hook system supports SessionStart and Stop event types

## Effort Estimates & Complexity

| Milestone | Complexity | Estimated Effort |
|-----------|-----------|------------------|
| 1. Compression skill | 35% | ~1 hour |
| 2. Hook expansion | 45% | ~1.5 hours |
| 3. Search command | 25% | ~45 minutes |
| 4. Temporal markers | 20% | ~30 minutes |
| 5. README section | 15% | ~30 minutes |
| **Total** | **~35% avg** | **~4.25 hours** |

No milestone exceeds 80% complexity; no mandatory human review for complexity reasons.

## Next Action

Begin Milestone 1, Task 1.1: Create `claude-code/skills/token-compression/SKILL.md` with three intensity levels (lite, full, ultra), forked from caveman's prompt patterns. Reference source: `~/github_private/caveman/skills/caveman/SKILL.md`.
