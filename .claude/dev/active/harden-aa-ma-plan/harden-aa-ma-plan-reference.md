# REFERENCE: harden-aa-ma-plan

Immutable facts (highest-priority memory). Verified during planning; do not
mutate without a corresponding context-log decision.

## Verified Code-Truth

### `/aa-ma-plan` flags (read from `claude-code/commands/aa-ma-plan.md`)

| Surface | Values | Default |
|---------|--------|---------|
| `--grill-mode=<mode>` | `auto`, `with-docs`, `simple`, `skip` | `auto` |
| `AA_MA_GRILL_MODE` env | same | unset |
| `--skip-lessons` | flag | off |
| `AA_MA_SKIP_LESSONS=1` env | flag | off |

### Skip surfaces (5 total)

| Step | Skip mechanism | Auto-recovery |
|------|----------------|---------------|
| Phase 1.3 grill | `--grill-mode=skip` | No |
| Phase 1.5 lessons | `--skip-lessons` | No |
| Phase 4.2 reviews | user `AskUserQuestion` | No |
| Phase 4.5 verification | user "skip" choice | No |
| Phase 5 artifacts | "context pressure" | YES — `/execute-aa-ma-*` re-spawns scribe |

### Existing hook events in this repo (read from `scripts/install.sh:312-319`)

```
SessionStart   (empty matcher)
PreCompact     (empty matcher)
PreToolUse     matcher=Bash       → aa-ma-commit-signature.sh
SessionEnd     (empty matcher)    → aa-ma-session-end-dirty.sh
PostToolUse    matcher=Bash       → aa-ma-commit-drift.sh
```

### Claude Code hook capabilities (verified WebFetch `code.claude.com/docs/en/hooks` 2026-05-11)

- `PreToolUse` matcher `"ExitPlanMode"` is supported (ExitPlanMode listed as matchable tool name)
- `transcript_path` is included in **all** hook events' stdin JSON
- Transcript is JSONL; each line is one turn with `tool_use` entries
- Pipe-separated matchers work (e.g., `"ExitPlanMode|Stop"`)
- Additional events discovered: `SubagentStart`, `SubagentStop`, `TaskCreated`, `TaskCompleted`
- Stdin JSON common fields: `session_id`, `transcript_path`, `cwd`, `permission_mode`, `effort`, `hook_event_name`, `agent_id`, `agent_type`
- `PreToolUse` adds: `tool_name`, `tool_input`, `tool_use_id`

## Marker Grammar (canonical)

Format: `[ISO8601-timestamp] PHASE_<id> <STATUS> — <key>=<value> [<key>=<value> ...]`

- `<STATUS>` ∈ `{DONE, SKIPPED}`
- `SKIPPED` **must** include `reason=<token>`
- Unknown `PHASE_<id>` values warn, not error (forward-compatibility)

## 9 Required Markers per `/aa-ma-plan` Run

1. `PHASE_0 INIT — slug=<slug>` (init record, not a phase)
2. `PHASE_1 DONE — context_gathering=complete`
3. `PHASE_1.3 DONE — grill_mode=<mode> branches_resolved=<N> questions_asked=<N>`
4. `PHASE_1.5 DONE — lessons_loaded=<N> git_grep_hits=<N>` (or SKIPPED)
5. `PHASE_2 DONE — brainstorm_skill=invoked alternatives_considered=<N>`
6. `PHASE_3 DONE — context7_calls=<N> web_fetches=<N>`
7. `PHASE_4 DONE — complexity_score=<%> plan_elements=<N>/12`
8. `PHASE_4.2 DONE — reviews=<list>` (or SKIPPED)
9. `PHASE_4.5 DONE — verdict=<GREEN|YELLOW|RED> criticals=<N> warnings=<N>` (or SKIPPED)
10. `PHASE_5 DONE — artifacts=5 task_dir=<path>`

(N.B. PHASE_0 is an init record, not counted in the "9 required" list.
"9 required" = 1, 1.3, 1.5, 2, 3, 4, 4.2, 4.5, 5.)

## Fingerprint Table (transcript-derived)

Hook reads `$TRANSCRIPT_PATH` JSONL and matches `tool_use` entries:

| Marker | Required evidence in transcript |
|--------|----------------------------------|
| `PHASE_1`   | `name=Agent` ∧ `input.subagent_type∈{Explore,general-purpose}` OR ≥1 `name=Read` of `src/**` |
| `PHASE_1.3` | ≥3 `name=AskUserQuestion` OR `name=Skill` ∧ `input.skill∈{grill-me,grill-with-docs}` |
| `PHASE_1.5` | `name=Read` ∧ `input.file_path~/lessons\.md$/` OR `name=Bash` ∧ `input.command~/git log .*--grep/` |
| `PHASE_2`   | `name=Skill` ∧ `input.skill~/brainstorming/` |
| `PHASE_3`   | `name=WebFetch` OR `name=WebSearch` OR `name~/^mcp__.*context7.*/` OR `name=Agent` ∧ `input.subagent_type=Explore` |
| `PHASE_4`   | `name=Skill` ∧ `input.skill~/complexity-router/` |
| `PHASE_4.2` | `name=Skill` ∧ `input.skill~/plan-(ceo\|eng\|design)-review/` |
| `PHASE_4.5` | `name=Skill` ∧ `input.skill~/plan-verification/` OR `name=Agent` ∧ `input.prompt~/verification\|adversarial\|6 angles/i` |
| `PHASE_5`   | `name=Agent` ∧ `input.subagent_type=aa-ma-scribe` AND `name=Agent` ∧ `input.subagent_type=aa-ma-validator` |

`SKIPPED — reason=...` markers override fingerprint check for their phase.

## Slug Derivation Algorithm

```
slug = <first 4 lowercased non-stopword tokens of user prompt
        joined by '-', stripped to [a-z0-9-], truncated to 40 chars>
       + '-' + <YYYYMMDDHHMMSS>
```

Stopwords: `the,a,an,is,of,for,to,in,on,and,or,with`

## File Paths (canonical)

| Path | Purpose |
|------|---------|
| `~/.claude/runtime/aa-ma-plan-<slug>.log` | Active-run marker log (transient) |
| `.claude/dev/active/<task>/<task>-plan-run.log` | Final artifact (moved at Phase 5) |
| `claude-code/hooks/aa-ma-plan-skip-warn.sh` | Advisory hook (NEW) |
| `claude-code/hooks/aa-ma-plan-marker.sh` | Marker-writer helper (NEW) |
| `src/aa_ma/plan_markers/parser.py` | Marker grammar parser (NEW) |
| `src/aa_ma/plan_markers/fingerprint.py` | Transcript correlator (NEW) |
| `docs/spec/plan-marker-grammar.md` | Public contract (NEW) |

## Lessons Applied

| Lesson | How applied |
|--------|-------------|
| L-001 (Phase 1.3 context-gathering) | WebFetched Claude Code hook docs during double-check before committing design |
| L-059 (falsifiable AC) | All task ACs are single-line `grep -c` / pytest exit / bats green |
| L-063 (precision claims) | "Falsifiable from session state" qualified to "when `transcript_path` is provided" |
| L-066 (cross-session coordination) | Implementation tasks will create `git worktree` if multi-session work emerges |
| L-080–L-082 (sub-step sync rule) | Each task writes `Status: COMPLETE` + `Result Log:` immediately, not batched |

## Env Vars (existing — reused)

- `AA_MA_HOOKS_DISABLE=1` — master kill switch (existing, reused for new hook)
- `AA_MA_PLAN_MARKER_DEBUG=1` — debug verbose mode (NEW, optional)
- `CLAUDE_CODE` — set by Claude Code session; absent in CI → hook silent
