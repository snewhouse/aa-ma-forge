# Context Log: harden-aa-ma-plan

## 2026-05-11 — Plan origination via /grill-me + /double-check

Stephen invoked `/grill-me` with concerns about `/aa-ma-plan` step-skipping
and a request to design empirical tests. Five design decisions resolved
interactively. After initial plan generation, `/double-check` was invoked,
which caught 3 critical unverified assumptions about Claude Code hook
capabilities. These were verified via WebFetch of `code.claude.com/docs/en/hooks`
before plan approval.

### Design decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Enforcement strength | Markers + ADVISORY hook | Additive, non-breaking; escalate to HARD after empirical validation |
| Marker storage | `~/.claude/runtime/*.log` → task dir at Phase 5 | Survives plan mode pre-task-dir-creation; becomes artifact at Phase 5 |
| Granularity | Sub-phase markers + transcript correlation | Catches the actual bug class (sub-phase skips); transcript = falsifiable evidence |
| Test scope | 4-tier pyramid (pytest + bats + smoke + 5 live) | Comprehensive empirical coverage; CI runs tiers 1-2 |
| Hook trigger | `PreToolUse(ExitPlanMode)` + `SessionEnd` | Belt-and-suspenders: catch at ExitPlanMode if possible, fallback at session end |

### Architectural reframe (from /double-check)

The initial design treated my (Claude's) marker writes as the source of truth
for the hook's skip-detection. This had a voluntary-marker failure mode: when
I skip a phase, I'd also skip its marker. The hook would detect nothing.

**Fix:** since `transcript_path` is included in every hook event's stdin
JSON (verified at `code.claude.com/docs/en/hooks` 2026-05-11), the hook reads
the JSONL transcript directly and computes phase fingerprints from `tool_use`
entries. The transcript is the source of truth. Markers become documentation
and skip-reason capture. I cannot fake markers because the hook doesn't trust
them; it trusts the transcript.

### Unverified assumptions caught by /double-check

| Assumption | Status | Resolution |
|------------|--------|------------|
| `PreToolUse` matcher `"ExitPlanMode"` supported | VERIFIED | Docs explicitly list ExitPlanMode as matchable tool name |
| `transcript_path` in `SessionEnd` stdin | VERIFIED | Docs: "included in all events" |
| Fingerprint table syntax (`Skill(plan-verification)`) | WRONG → FIXED | Real format: `{name: "Skill", input: {skill: "plan-verification"}}` |
| Slug derivation rule | UNSPECIFIED → SPECIFIED | First 4 non-stopwords + timestamp |
| AC "command body has explicit instruction" | UNFALSIFIABLE → FIXED | Replaced with `grep -c` assertion |

### Lessons applied

- **L-001** (Phase 1.3 context-gathering): WebFetched Claude Code hook docs DURING the double-check before committing the design.
- **L-059** (falsifiable AC): All task ACs rewritten as single-line grep / pytest exit / bats green assertions.
- **L-063** (precision claims): "Falsifiable from session state" qualified to "when `transcript_path` is provided to the hook".
- **L-066** (cross-session coordination): Implementation tasks will create `git worktree` if work spans sessions.
- **L-080–L-082** (sub-step sync rule): Each task to write `Status: COMPLETE` + `Result Log:` immediately, never batched.

## 2026-05-11 — Implementation starting on M1

AA-MA artifacts created under `.claude/dev/active/harden-aa-ma-plan/`.
TaskList tracks 5 milestones (#1-#5). Starting with M1 Task 1.1 (write the
marker grammar spec).

Implementation strategy: linear progression M1 → M5; commit after each task
completes its AC; AA-MA Plan footer on all commits. No git worktree needed —
working on existing `dev/run_aa_ma_plan_recon` feature branch.
