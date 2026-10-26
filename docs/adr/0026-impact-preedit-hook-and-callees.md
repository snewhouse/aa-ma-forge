# 0026. Impact Pre-Edit Hook, `callees`, and Plugin Edges in the codemem Index

**Status:** Accepted
**Date:** 2026-10-26
**Deciders:** Ste
**Tags:** `hooks`, `codemem`, `impact-analysis`
**Plan:** code-conventions-impact Milestone 10 (map Tickets 4 and 6; R1, R3, R4, R6).

## Context and Problem Statement

Impact analysis existed as a skill (`Skill(impact-analysis)`) and as codemem MCP tools, but
nothing put it in front of an edit: no general coding skill invoked it, and the model edited
shared code without seeing who depended on it (Ticket 4). codemem itself had three gaps: the
"downstream" tool was named `blast_radius` while `aa_ma_context` read a `callees` key (carried
defect 1 — the count was always 0); co-change data had no ratio or large-commit filter; and
skills, agents, hooks and rules had no edges in the index, so their callers were invisible.
How do we show the model a file's dependants before it edits that file, cheaply and safely?

## Decision Drivers

- Before the edit, not after: the moment the model can still change course.
- Cheap enough for every Edit/Write: p95 ≤ 1.5 s (10.1 budget); never blocks an edit.
- Untrusted data: repo-controlled paths and names enter the model's context.
- One index for code and plugin surface; no second store.

## Considered Options

1. **A global PreToolUse(Edit|Write) hook, once per file per session, ≤5 lines of codemem data** (chosen).
2. **Name `Skill(impact-analysis)` in the coding skills only** — relies on the model choosing to call it; Ticket 4 found it rarely did.
3. **Block edits until impact analysis runs** — friction on every trivial edit; a gate belongs at the milestone boundary (M11, IMPACT_VERIFIED).

## Decision Outcome

**Chosen:** option 1, plus option 2 as a complement (the five execution/coding skills now name
`Skill(impact-analysis)` at their pre-edit point).

- **Hook** `claude-code/hooks/aa-ma-impact-preedit.sh`: before the first Edit/Write of a file in a
  session, one `codemem impact --format brief` call (under `timeout -k 1 2`) feeds ≤5 lines of
  `hookSpecificOutput.additionalContext`, framed `codemem data (untrusted): …` and ending with a
  pointer to `Skill(impact-analysis)`. Silent when the file has no callers and no co-changes;
  one notice per session for no index / no codemem / timeout; exit 0 always. A1 (that
  additionalContext reaches the model) was proved live in the 10.1 prototype.
- **Trust** (plan §0 v2): codemem only from the forge (`aa_ma_codemem_bin`), the index only from
  the XDG cache (`aa_ma_codemem_dir`, M16), opened read-only with `trusted_schema=OFF`; the
  path is quoted and passed after `--`; `session_id` is validated before it names a directory;
  every injected line passes `sanitize_context_line`, which drops every Unicode Cc/Cf/Co/Cs/Zl/Zp
  character (C0/C1, bidi, zero-width, tag characters, separators, private use).
- **Once per file per session** is a marker created with bash `set -C` (O_EXCL). Not `mkdir`:
  uutils coreutils mkdir 0.10.0 (Ubuntu 26.04's default) is not test-and-set (L-070).
- **codemem:** `callees` replaces `blast_radius` as the downstream tool (14 MCP tools);
  `blast_radius` stays one release as a deprecated alias returning the same list as
  `downstream` plus a `deprecated` notice — removal tracked as `TODO(ADR-0026)`
  (`mcp_tools/__init__.py`). `aa_ma_context` reads `callees()` (defect 1 fixed).
  `co_changes` gains `min_ratio` and `max_commit_files`; the hook and `file_impact` ignore commits
  touching more than `CO_CHANGE_MAX_COMMIT_FILES = 10` files — the 10.1 prototype showed this
  repo's 12–19-file sweep commits drowning the signal (the MCP tool's default stays unfiltered).
  `git_mining` follows renames and deletes.
- **Plugin edges:** schema v4 table `plugin_edges(src, dst, kind, ref_class)`, filled at build and
  refresh from `plugin_surface.extract()`; `who_calls` and `file_impact` report plugin callers.
  `.md` files are not indexed into `files`, so code views (draw, hot_spots, dead_code, layers)
  are unchanged.

## Consequences

- Measured: p95 133–160 ms per first edit of a file (20 runs × 4 files); later edits of the same
  file cost one marker check.
- The hook goes live at Sub-step 11.0 (live install after the M10 merge, ADR-0025).
- Known limits: the default 500-commit window hides history older than that (the M3 renames
  are 660 commits back); an uncommitted `.md` change does not mark the index stale; a file
  first edited before `codemem build` gets no note later in that session.
- §6.3 gains an advisory predicted-vs-actual list (`UNPREDICTED <path>`) that the §6.8
  code-reviewer judges; M11 turns the comparison into the HARD `IMPACT_VERIFIED` gate.

## Pros and Cons of the Options

### 1. Pre-edit hook (chosen)
- ✅ Reaches the model at the right moment without it having to remember.
- ✅ Measured cheap; fails open.
- ❌ Advisory only: the model can ignore it (M11's gate is the backstop).

### 2. Skill wording only
- ✅ No new hook.
- ❌ Depends on the model invoking the skill; Ticket 4 showed it usually does not.

### 3. Blocking gate per edit
- ✅ Impossible to ignore.
- ❌ Friction on every edit; the milestone gate is the right place for enforcement.
