# Plan: Harden /aa-ma-plan against step-skipping + design empirical tests

Created: 2026-05-11
Status: APPROVED — implementation begun

## Executive Summary

Make every `/aa-ma-plan` phase skip **observable** (in a runtime log) and
**falsifiable from session state** (via transcript-derived fingerprints
computed by an advisory hook). Ship 4-tier test pyramid (pytest unit + bats
hook + bash smoke + 5 live scenarios) that catches the skipping behavior
empirically. Additive design, default-advisory, fully opt-out via existing
`AA_MA_HOOKS_DISABLE=1` kill switch. **Breaks nothing.**

## Context & Origin

Stephen reported that I "often skip steps" in `/aa-ma-plan`, confirmed across
Phase 1.3 (grill), Phase 1.5 (lessons), Phase 4.2 (reviews), Phase 4.5
(verification), and "random others." Root cause: structurally, every skip is
**invisible after the fact**. `provenance.log` records commits, not phases;
`ExitPlanMode` is ungated; no machine-readable phase-status file exists.

Plan was authored via interactive `/grill-me` session resolving 5 design
decisions, then hardened via `/double-check` which caught 3 unverified
hook-system assumptions (verified via WebFetch of `code.claude.com/docs/en/hooks`).

## Design Decisions

| Decision | Choice |
|----------|--------|
| Enforcement strength | Markers + ADVISORY hook (additive) |
| Marker storage | `~/.claude/runtime/aa-ma-plan-<slug>.log` → moved to task dir at Phase 5 |
| Granularity | 9 sub-phase markers + transcript-fingerprint correlation |
| Test scope | 4-tier pyramid (pytest + bats + smoke + 5 live scenarios) |
| Hook trigger | `PreToolUse` matcher=`"ExitPlanMode"` + `SessionEnd` |

## Architectural Reframe (from double-check)

Initial design had the hook validate markers I (Claude) wrote during the run.
That has a voluntary-marker problem: if I skip a phase, I'll also skip
writing its marker, so the hook detects nothing.

**Reframed:** since `transcript_path` is included in every hook event
(verified at `code.claude.com/docs/en/hooks`), the hook reads the JSONL
transcript directly and computes phase fingerprints from `tool_use` entries.
The transcript is the source of truth; markers are documentation +
skip-reason capture. I cannot fake markers because the hook doesn't trust
them — it trusts the transcript.

## Milestones (5)

- **M1** Foundation — parser + fingerprint (TDD-first)
- **M2** Hook implementation (advisory)
- **M3** Command body integration
- **M4** Live empirical test runs (Tier 4 — 5 scenarios)
- **M5** Documentation + release

See `harden-aa-ma-plan-tasks.md` for full task breakdown.

## Engineering Standards Declaration (element #12)

| Theme | Applies | Why |
|-------|---------|-----|
| 1. Verification & Truth | YES | Whole plan exists to make skips falsifiable from transcript. |
| 2. Development Principles | YES | TDD (red-green per task), KISS (regex parser, bash hook), SOC (Python parsing / bash wiring / markdown instructions). |
| 3. Reasoning & Planning | YES | Plan authored via Socratic grilling + adversarial double-check. |
| 4. Safety & Continuity | YES | Non-breaking: additive + `AA_MA_HOOKS_DISABLE=1` kill switch. Advisory mode by design. |
| 5. Execution Checklist | YES | Every task has falsifiable AC (grep / pytest exit / bats green). |
| 6. Sync & Commit Discipline | YES | Sub-step Result Logs written incrementally per L-080–L-082; Conventional Commits + `[AA-MA Plan]` footer. |

## Rollback Strategy

- Hook is advisory (exit 0 always); cannot block any workflow.
- `export AA_MA_HOOKS_DISABLE=1` disables all AA-MA hooks (existing kill switch).
- `scripts/uninstall.sh` removes new symlinks.
- `git revert` is safe — no schema/data migrations.
- Failed marker writes are no-ops; do not fail the plan.

## Risks (top 3 cross-milestone)

1. *I (Claude) ignore marker-write instructions in modified `aa-ma-plan.md`.*
   Mitigation: hook reads transcript as source of truth; markers are advisory documentation only. M4 Scenario 4 explicitly tests the missing-marker case.
2. *`PreToolUse(ExitPlanMode)` doesn't fire in some Claude Code versions.*
   Mitigation: belt-and-suspenders with `SessionEnd` which always fires.
3. *Transcript JSONL format changes across Claude Code versions.*
   Mitigation: parser reads transcript opportunistically; absence is non-fatal.

## Next Action

M1 Task 1.1 — Write `docs/spec/plan-marker-grammar.md` (REFERENCE-grade
marker contract + fingerprint table + slug derivation algorithm). HITL gate
for Stephen review of the contract before downstream tasks consume it.
