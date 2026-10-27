# 0027. Gate-Computed `IMPACT_VERIFIED`: §6.7 Fence 4

**Status:** Proposed
**Date:** 2026-10-27
**Deciders:** Ste
**Tags:** `gate`, `impact-analysis`, `codemem`
**Plan:** code-conventions-impact Milestone 11 (map Ticket 7; R1; P2, P3, P4, P6). Scope: ADR-0009 (gate readings come from Python).

## Context and Problem Statement

The milestone gate certified tests (fence 3, ADR-0023) but not impact. §5 of
engineering-standards listed "Non-breaking constraint verified" as HARD, yet the only
evidence was that `Skill(impact-analysis)` had run — a claim, not a check. M10's §6.3
predicted-vs-actual list showed the gap: 31 files changed that the Contract never named,
all of them missed impact. How does the gate itself decide whether a milestone changed only
what it planned, or explained the rest?

## Decision Drivers

- Computed by the gate from git and the plan, not reported by the agent (DIAGRAM_VERIFIED pattern).
- Fail closed: no index, a failed or skipped refresh, a stale answer, no milestone window — never a pass.
- Cheap to satisfy honestly: one line per difference, in the files the agent already edits.
- Quiet enough not to be bypassed (the 11.1 prototype measured the noise before the threshold was set).
- New plans only: grandfathered plans keep their contracts.

## Considered Options

1. **A Python CLI (`aa-ma-impact`) run by a fourth §6.7 fence, comparing the window with the Contract, codemem co-change and the public API** (chosen).
2. **Keep it advisory** (M10's §6.3 list judged by the §6.8 reviewer) — leaves "Non-breaking constraint verified" without evidence.
3. **Block on callers** (who_calls of every changed symbol must be in the Contract) — callers are a review question, not a set equality; it would flag every leaf edit.

## Decision Outcome

**Chosen:** option 1.

- **Window (R1):** `aa_ma_milestone_base` = `git merge-base origin/<default> HEAD`, origin only;
  `origin/HEAD` must be a `refs/remotes/origin/<name>` ref other than the branch's own. Changed
  set = that base against the working tree plus untracked files (§8.1 commits after the gate),
  minus `IMPACT_EXCLUDE`.
- **Predicted set (P2):** the milestone's Contract rows, every verb, nothing exempt
  (`aa_ma.contract_rows`, shared with Angle 6 check 8). A row holds paths only — prose goes
  after `#`; a stray word reads as a predicted file (Ste, 2026-10-27).
- **Differences needing `Impact-Explained: <path> — <reason>`** (tasks.md): unpredicted files,
  predicted-unchanged rows, and codemem co-change partners (≥5 shared commits and ≥50% of the
  file's, last 500 commits; 11.1 prototype, Ste) that did not change.
- **Public API (P6):** griffe 2.3.2, static, for `aa_ma` and `codemem` only; each break needs
  `API-Break: <dotted.path> — <reason>` in the Contract. Unloadable → `api_diff=skipped(<reason>)`.
- **Derived Critical-Path:** `CRITICAL_PATH_GLOBS` over the changed set; each value needs a
  `CRITICAL_PATH_REVIEW` line naming its files (or the glob).
- **Applicability (P4):** plans `Created:` on or after `IMPACT_CUTOVER` (sentinel `9999-12-31`
  until the v0.18.0 release date in M14.1); the grandfather check runs first, so an older plan
  reads "not applicable" even with no window. Exit codes 0 / 1 / 2 / 3 / 5; launcher 127.
- **Callers are not fence 4's domain.** Partners linked by an import/call edge are excluded by
  codemem's co-change query on purpose; who depends on a changed symbol is answered by
  `who_calls` / `Skill(impact-analysis)` (§6.3) and judged by the §6.8 reviewers.
- Overrides: `Cochange-Threshold: <n> <ratio>` in the merge-base reference.md (n ≤ 20,
  ratio ≤ 0.9) with a `GATE APPROVAL: Cochange-Threshold <n> <ratio> — <heading>`
  (`enforce.has_gate_approval`, pinned to the shell reader).

## Consequences

- Measured on this repo (11.1): 5 co-change lines over the last 3 completed plans' 15
  milestones (11 over this plan's 12); a full run takes ~1.5 s including the API diff.
- The codemem CLI's `query co_changes` now reports `stale` / `stale_reason` per path
  (additive). aa-ma-impact runs `codemem refresh` first, so a stale answer means a race.
- griffe compares source expressions: a default rewritten to a named constant of the same
  value is a break to declare.
- verify-impl's Phase 6.8 window uses the same base (one WARN and a working `HEAD~10`
  fallback on the default branch).
- Known limits: co-change history outside the 500-commit window is invisible (F1, accepted);
  the linked-file exclusion uses the current index; a local actor can still bypass any gate
  (`AA_MA_HOOKS_DISABLE`) — this is a discipline check, not a security boundary (ADR-0022).

## Pros and Cons of the Options

### 1. Gate-computed fence 4 (chosen)
- ✅ Evidence instead of a claim; same pattern as fences 2 and 3.
- ✅ Every difference is one line in a file the agent already edits.
- ❌ Plans must keep Contract rows to paths, or pay in explanations.

### 2. Advisory only
- ✅ No friction.
- ❌ The HARD row in §5 keeps no evidence behind it.

### 3. Block on callers
- ✅ Catches a missed caller directly.
- ❌ Every symbol edit drags its callers into the Contract; noise ensures bypass.
