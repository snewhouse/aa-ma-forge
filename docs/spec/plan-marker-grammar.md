# Plan Marker Grammar

Canonical contract for `/aa-ma-plan` phase markers. This document is the
single source of truth for marker syntax, semantics, fingerprint correlation,
and slug derivation. Downstream artifacts (parser, hook, command body) refer
back to this spec.

## Purpose

`/aa-ma-plan` defines a workflow of 5 numbered phases (1–5) with documented
sub-phases (1.3, 1.5, 4.2, 4.5). All sub-phases are individually skip-able
via flags, env vars, or user choice. Skips are currently **invisible after
the fact** because no artifact records what ran.

Phase markers make skip behavior observable. The runtime log of a single
`/aa-ma-plan` invocation records, per phase: was it run, was it skipped,
why, and what evidence supports the claim.

## Marker Grammar

```
[<ISO8601-timestamp>] PHASE_<id> <STATUS> — <key>=<value> [<key>=<value> ...]
```

Field rules:

| Field | Constraint |
|-------|------------|
| `<ISO8601-timestamp>` | RFC 3339 / ISO 8601 with timezone offset, e.g. `2026-05-11T12:30:15+01:00` |
| `<id>` | Letters, digits, underscore, and `.` for sub-phases. Examples: `0`, `1`, `1.3`, `4.5` |
| `<STATUS>` | `DONE` or `SKIPPED` (uppercase, exactly) |
| `<key>` | Lowercase ASCII, underscores allowed; `[a-z][a-z0-9_]*` |
| `<value>` | Single shell-token. Spaces forbidden; use `_` instead. Quote-free. |
| Separator | Em-dash `—` (U+2014) surrounded by single spaces |

Semantic rules:

1. `SKIPPED` MUST include a `reason=<token>` payload.
2. `DONE` SHOULD include payload describing what was accomplished.
3. Each marker is one line. No multi-line markers.
4. The runtime log is append-only during a plan run.
5. Lines that do not match this grammar are warned and ignored (forward-compatibility).
6. Unknown `PHASE_<id>` values produce a warning, not an error.

## 9 Required Markers per `/aa-ma-plan` Run

A complete, non-skipping run produces these 10 lines (PHASE_0 INIT is the
record of stub creation, not counted in "9 required"):

| # | Marker prefix | Expected payload keys |
|---|---------------|----------------------|
| 0 | `PHASE_0 INIT` | `slug=<slug>` |
| 1 | `PHASE_1 DONE` | `context_gathering=complete` |
| 2 | `PHASE_1.3 DONE` | `grill_mode={auto\|with-docs\|simple\|skip}`, `branches_resolved=<N>`, `questions_asked=<N>` |
| 3 | `PHASE_1.5 DONE` | `lessons_loaded=<N>`, `git_grep_hits=<N>` |
| 4 | `PHASE_2 DONE` | `brainstorm_skill=invoked`, `alternatives_considered=<N>` |
| 5 | `PHASE_3 DONE` | `context7_calls=<N>`, `web_fetches=<N>` |
| 6 | `PHASE_4 DONE` | `complexity_score=<N>%`, `plan_elements=<N>/12` |
| 7 | `PHASE_4.2 DONE` | `reviews=<csv>` |
| 8 | `PHASE_4.5 DONE` | `verdict={GREEN\|YELLOW\|RED}`, `criticals=<N>`, `warnings=<N>` |
| 9 | `PHASE_5 DONE` | `artifacts=5`, `task_dir=<path>` |

Any of markers 2, 3, 7, 8 may appear as `SKIPPED` instead of `DONE`,
provided they include `reason=<token>`.

Example complete log:

```
[2026-05-11T12:30:15+01:00] PHASE_0 INIT — slug=harden-aa-ma-plan-20260511123015
[2026-05-11T12:31:00+01:00] PHASE_1 DONE — context_gathering=complete
[2026-05-11T12:32:10+01:00] PHASE_1.3 DONE — grill_mode=with-docs branches_resolved=7 questions_asked=12
[2026-05-11T12:33:05+01:00] PHASE_1.5 DONE — lessons_loaded=12 git_grep_hits=4
[2026-05-11T12:34:30+01:00] PHASE_2 DONE — brainstorm_skill=invoked alternatives_considered=3
[2026-05-11T12:38:55+01:00] PHASE_3 DONE — context7_calls=3 web_fetches=1
[2026-05-11T12:42:00+01:00] PHASE_4 DONE — complexity_score=42% plan_elements=12/12
[2026-05-11T12:43:15+01:00] PHASE_4.2 SKIPPED — reason=user_passed
[2026-05-11T12:48:00+01:00] PHASE_4.5 DONE — verdict=GREEN criticals=0 warnings=2
[2026-05-11T12:50:30+01:00] PHASE_5 DONE — artifacts=5 task_dir=.claude/dev/active/harden-aa-ma-plan
```

## Storage Lifecycle

1. **Phase 0 (init)** — `/aa-ma-plan` writes the log header at
   `~/.claude/runtime/aa-ma-plan-<slug>.log`. The first line is the
   `PHASE_0 INIT` marker.
2. **Phases 1–4** — markers appended to the runtime log as each phase
   completes (or as a `SKIPPED` line if the phase is bypassed).
3. **Phase 5 (artifact creation)** — `aa-ma-scribe` writes the
   `PHASE_5 DONE` marker, then **moves** the runtime log into the active
   task directory as `<task>-plan-run.log`. The log becomes a permanent
   AA-MA artifact alongside the 5 standard files.
4. **Failure mode**: if Phase 5 doesn't run (e.g., context pressure), the
   runtime log remains at `~/.claude/runtime/`. The advisory hook surfaces
   this at `ExitPlanMode` / `SessionEnd`. A subsequent
   `/execute-aa-ma-*` command's auto-recovery for Phase 5 should also
   perform the move.

## Fingerprint Correlation (transcript-derived)

The advisory hook does not trust markers as ground truth — it reads the
JSONL transcript at `$TRANSCRIPT_PATH` (provided by Claude Code in every
hook event's stdin per [Claude Code hooks docs][hooks]) and matches
`tool_use` entries against per-phase fingerprints.

[hooks]: https://code.claude.com/docs/en/hooks

Transcript entry shape:

```jsonc
{ "type": "tool_use",
  "name": "Skill",
  "input": { "skill": "plan-verification", "args": "..." } }
```

Fingerprint table — `name` and `input.<key>` reference the transcript fields:

| Marker | Required evidence in transcript (any one match) |
|--------|--------------------------------------------------|
| `PHASE_1`   | `name=Agent` ∧ `input.subagent_type ∈ {Explore, general-purpose}` OR ≥1 `name=Read` of `src/**` |
| `PHASE_1.3` | ≥3 `name=AskUserQuestion` OR `name=Skill` ∧ `input.skill ∈ {grill-me, grill-with-docs, grill-me:grill-me}` |
| `PHASE_1.5` | `name=Read` ∧ `input.file_path ~ /lessons\.md$/` OR `name=Bash` ∧ `input.command ~ /git log .*--grep/` |
| `PHASE_2`   | `name=Skill` ∧ `input.skill ~ /brainstorming/` (matches `superpowers:brainstorming` etc.) |
| `PHASE_3`   | `name=WebFetch` OR `name=WebSearch` OR `name ~ /^mcp__.*context7.*/` OR `name=Agent` ∧ `input.subagent_type=Explore` |
| `PHASE_4`   | `name=Skill` ∧ `input.skill ~ /complexity-router/` |
| `PHASE_4.2` | `name=Skill` ∧ `input.skill ~ /plan-(ceo\|eng\|design)-review/` |
| `PHASE_4.5` | `name=Skill` ∧ `input.skill ~ /plan-verification/` OR `name=Agent` ∧ `input.prompt ~ /verification\|adversarial\|6 angles/i` |
| `PHASE_5`   | `name=Agent` ∧ `input.subagent_type=aa-ma-scribe` AND `name=Agent` ∧ `input.subagent_type=aa-ma-validator` |

**Override:** a `SKIPPED — reason=<token>` marker in the runtime log
bypasses the fingerprint check for its phase (skip is its own evidence;
reason captures the why). This is the legitimate-skip path.

## Slug Derivation

```
slug = <first 4 lowercased non-stopword tokens of user prompt,
        joined by '-', stripped of non-[a-z0-9-] chars,
        truncated to 40 chars>
       + '-' + <YYYYMMDDHHMMSS>
```

Stopwords (case-insensitive): `the,a,an,is,of,for,to,in,on,and,or,with`

Timestamp suffix ensures uniqueness across concurrent runs (L-066
cross-session safety).

Examples:

| Prompt | Slug |
|--------|------|
| "harden /aa-ma-plan against step-skipping" | `harden-aa-ma-plan-against-step-skipping-20260511123015` |
| "/aa-ma-plan add docstring to src/aa_ma/__init__.py" | `add-docstring-src-aa-ma-20260511123015` |
| "fix the lessons scan" | `fix-lessons-scan-20260511123015` |

The slug is included in the `PHASE_0 INIT` marker payload and informs
the eventual task directory name when `aa-ma-scribe` runs at Phase 5.

## Parser & Hook Implementation Contracts

- **Parser**: `src/aa_ma/plan_markers/parser.py` exposes
  `parse_log(text: str) -> list[Marker]`. `Marker` is a typed dataclass:
  `{timestamp: datetime, phase_id: str, status: Literal["DONE","SKIPPED"], payload: dict[str, str]}`.
- **Fingerprint matcher**: `src/aa_ma/plan_markers/fingerprint.py` exposes
  `correlate(markers: list[Marker], transcript_path: Path) -> list[CorrelationResult]`.
  Each result reports per-phase: `expected`, `marker_status` ∈ {DONE, SKIPPED, MISSING},
  `evidence_found` ∈ {present, absent, skipped_with_reason}, `warning` ∈ {None, "<msg>"}.
- **Hook**: `claude-code/hooks/aa-ma-plan-skip-warn.sh` reads stdin JSON,
  extracts `transcript_path`, finds newest `~/.claude/runtime/aa-ma-plan-*.log`,
  shells out to the Python fingerprint matcher, prints warnings to stderr,
  exits 0 (advisory).

## Version

- v1 (initial): this document. Forward-compatibility hooks: unknown phase
  IDs warn, not error; unknown payload keys are preserved; malformed
  marker lines are ignored after warning.

## Bypass

- `AA_MA_HOOKS_DISABLE=1` — disables the advisory hook (existing master
  kill switch).
- `AA_MA_PLAN_MARKER_DEBUG=1` — enables verbose tracing of the
  fingerprint matcher's decision tree to stderr.

## Cross-References

- AA-MA active plan: `.claude/dev/active/harden-aa-ma-plan/`
- AA-MA specification (parent): `docs/spec/aa-ma-specification.md`
- Engineering Standards (governs this plan): `claude-code/rules/engineering-standards.md`
- Claude Code hooks reference: https://code.claude.com/docs/en/hooks
