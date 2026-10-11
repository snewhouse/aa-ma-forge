# Phase 0: runtime log — derive the plan slug and write the phase markers the plan-marker hook checks.

### Phase 0: Runtime Log Initialization

**Purpose:** make every phase skip observable + falsifiable. A runtime
log is initialized BEFORE Phase 1 begins; subsequent phases append
markers to it. See `docs/spec/plan-marker-grammar.md` for the canonical
grammar.

**Step 0.1: Derive the plan slug.**

Take the user's request and produce a slug per the algorithm in
`docs/spec/plan-marker-grammar.md` §Slug Derivation:
1. Take the first 4 lowercased non-stopword tokens of the request.
2. Join with hyphens; strip non-`[a-z0-9-]`; truncate to 40 chars.
3. Append `-<YYYYMMDDHHMMSS>` (UTC) for uniqueness.

Stopwords: `the, a, an, is, of, for, to, in, on, and, or, with`.

**Step 0.2: Write the PHASE_0 INIT marker.**

```bash
bash ~/.claude/hooks/lib/aa-ma-plan-marker.sh <slug> 0 INIT slug=<slug>
```

This creates `~/.claude/runtime/aa-ma-plan-<slug>.log` and writes the
init line. The advisory hook (`aa-ma-plan-skip-warn.sh`) will later read
this log at `PreToolUse(ExitPlanMode)` and `SessionEnd` to detect any
skipped phase markers.

**Step 0.3: Marker discipline — required writes at end of each phase.**

After each phase completes (or is legitimately skipped), append the
corresponding marker via `bash ~/.claude/hooks/lib/aa-ma-plan-marker.sh`.
This list is the canonical contract; the advisory hook warns if any
of these are missing or if a SKIPPED marker lacks `reason=<token>`.

| End of Phase | Append marker (DONE form) |
|--------------|---------------------------|
| Phase 1      | `... <slug> 1 DONE context_gathering=complete` |
| Step 1.3     | `... <slug> 1.3 DONE grill_mode=<mode> branches_resolved=<N> questions_asked=<N>` |
| Step 1.5     | `... <slug> 1.5 DONE lessons_loaded=<N> git_grep_hits=<N>` |
| Phase 2      | `... <slug> 2 DONE brainstorm_skill=invoked alternatives_considered=<N>` |
| Phase 3      | `... <slug> 3 DONE context7_calls=<N> web_fetches=<N> research_files=<N>` |
| Phase 4      | `... <slug> 4 DONE complexity_score=<N>% plan_elements=<N>/12` |
| Phase 4.2    | `... <slug> 4.2 DONE reviews=<csv>` |
| Phase 4.5    | `... <slug> 4.5 DONE verdict=<GREEN\|YELLOW\|RED> criticals=<N> warnings=<N>` |
| Phase 5      | `... <slug> 5 DONE artifacts=5 task_dir=<path>` |

**Legitimate skip form:** if a phase is bypassed, append a SKIPPED
marker with a `reason=<token>` payload, e.g.:
```bash
bash ~/.claude/hooks/lib/aa-ma-plan-marker.sh <slug> 1.5 SKIPPED reason=flag_--skip-lessons
bash ~/.claude/hooks/lib/aa-ma-plan-marker.sh <slug> 4.2 SKIPPED reason=user_passed
bash ~/.claude/hooks/lib/aa-ma-plan-marker.sh <slug> 4.5 SKIPPED reason=user_choice
```

The shorthand `... <slug> N STATUS ...` above means: invoke
`bash ~/.claude/hooks/lib/aa-ma-plan-marker.sh` with those arguments.
Replace `<slug>` with the slug from Step 0.1.
