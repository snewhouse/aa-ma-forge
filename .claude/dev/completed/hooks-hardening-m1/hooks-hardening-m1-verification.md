<!-- ARCHIVED: 2026-04-12 17:29 UTC+01:00 -->
<!-- Plan: hooks-hardening-m1 - COMPLETE -->
<!-- Total Milestones: 5 | Duration: 2026-04-12 to 2026-04-12 -->

# hooks-hardening-m1 Verification Audit Trail

**Verification Mode:** Automated (CRITICALs block advancement)
**Date:** 2026-04-12
**Waves Completed:** 2 of 2 (Wave 2 Angle 6 specialist skipped — no domain keywords matched)
**Revision Loops:** 2 of max 2 used
**Final Status:** PASS (0 unresolved CRITICALs after revisions)

---

## Wave 1 — Four Parallel Angles

### Angle 1 — Ground-Truth Cross-Check

- Findings: **1 CRITICAL**, 1 WARNING, 20 OK
- CRITICAL: Pre-compact install.sh registration gap exists in the current repo. The shipped `pre-compact-aa-ma.sh` hook is present but unregistered in `scripts/install.sh`. Plan now explicitly addresses this via M3.3(c).
- WARNING: Pre-existing bug in `~/.claude/hooks/lib/guard-protected-dirs.sh:14` reads `.command` instead of `.tool_input.command`. Logged as out-of-scope; scheduled for follow-up plan.

### Angle 2 — Assumption Validation

- Findings: **2 CRITICAL**, 10 WARNING, 23 VERIFIED
- CRITICAL-1: Stop hook semantics. Initial plan proposed Stop for dirty detector; Stop fires per turn, not at session end. Revision R1 retargeted M4 to SessionEnd.
- CRITICAL-2: Status format scope. Original plan proposed canonicalizing 20+ files. Wave 1 verified most files are already plain; scope reduced to 3 files via Revision R2.
- All 23 verified assumptions (PreToolUse stdin shape, exit code semantics, SessionEnd existence, bats-action availability, PATH conventions, etc.) passed cross-check against Claude Code documentation.

### Angle 3 — Impact Analysis (Blast Radius)

- Findings: **4 CRITICAL**, 4 WARNING, 4 OK
- CRITICAL-1: Format canonicalization scope excessive (see Angle 2). Resolved by R2.
- CRITICAL-2: No `uninstall.sh` updates despite adding 3 new hook registrations. Resolved by Revision R3 (added M3.3.bis).
- CRITICAL-3: M3.5 file list was incomplete (initially only named one of three target files). Resolved by R2 (expanded to 3 files with exact line numbers).
- CRITICAL-4: session-start path emission bug (line 72) identified and explicitly called out as part of M2.2 scope.

### Angle 4 — Falsifiability Audit

- Findings: **0 CRITICAL**, 2 WARNING, 15 OK
- 88% of acceptance criteria were falsifiable in first draft. Two rewrites applied:
  - Step 1.2: replaced "yaml compiles" with "`yamllint .github/workflows/security.yml` exits 0".
  - Step 3.4: replaced "README updated" with "CHANGELOG Unreleased entry matches regex `feat\\(hooks\\): commit-signature`" and explicit `/doc-sync` gate.
- Post-rewrite: 100% falsifiable.

---

## Wave 2 — Fresh-Agent Simulation

### Angle 5 — Fresh-Agent Feasibility

A fresh agent with no prior context was simulated against the plan. Ambiguities surfaced:

- Findings: **3 CRITICAL**, 5 WARNING, 3 INFO
- CRITICAL-1: `mtime_offsets` parameter undefined. A fresh agent could not derive expected semantics. Resolved by Revision R4 — "comma-separated integer seconds offset from now (negative = past)".
- CRITICAL-2: File set per fixture task was ambiguous. A fresh agent did not know how many AA-MA files to emit. Resolved by Revision R5 — "5 standard AA-MA files per fixture task" with explicit filenames.
- CRITICAL-3: No test existed for the fixture builder itself (M1.1) — a fresh agent cannot verify fixture correctness. Resolved by Revision R6 — added M1.1.bis with 4 bats cases.
- WARNINGs covered minor naming clarifications and example values; all folded into the plan.

### Angle 6 — Specialist Review

- **Skipped.** Scope filter: no domain keywords (Pydantic/API/schema/auth/FastAPI/etc.) present in the plan. Bash shell-hook domain does not trigger specialist review under the automated verification rubric.

---

## Revision History

| Revision | Trigger (Angle/CRITICAL) | Change | Resolution Status |
|----------|--------------------------|--------|------------------|
| R1 | Angle 2 CRITICAL-1 (Stop semantics) | M4 retargeted from Stop to SessionEnd; hook filename and stdin shape updated | RESOLVED |
| R2 | Angle 2 CRITICAL-2 + Angle 3 CRITICAL-1/3 (Status format scope) | Declared plain Status canonical; flip scope reduced to 3 files (`docs/templates/tasks-template.md`, `claude-code/agents/aa-ma-scribe.md`, `claude-code/hooks/aa-ma-session-start.sh`); helper remains format-agnostic | RESOLVED |
| R3 | Angle 3 CRITICAL-2 (uninstall.sh) | Added M3.3.bis sub-step: uninstall.sh deregisters all 5 hook entries | RESOLVED |
| R4 | Angle 5 CRITICAL-1 (mtime_offsets) | M1.1 signature spec: "comma-separated integer seconds offset from now" with negative-past semantics | RESOLVED |
| R5 | Angle 5 CRITICAL-2 (file set) | M1.1 spec: 5 standard AA-MA files per fixture task, with explicit filename list and optional `--with-git` flag | RESOLVED |
| R6 | Angle 5 CRITICAL-3 (no fixture test) | Added M1.1.bis — fixture builder has its own red-green bats test with 4 cases | RESOLVED |

---

## Final Sign-Off

- Total CRITICALs found: 6
- Total CRITICALs resolved: 6
- Revision loops consumed: 2 of 2 maximum
- Final verification verdict: **PASS**
- Plan approved for execution: 2026-04-12

**Notes for executors:**

- Any deviation from the canonicalized Status format (plain, per R2) in M3.5 target files must update this verification record.
- If additional hook types are registered in install.sh post-M3, the uninstall.sh deregistration list (from R3) must be extended in parallel.
- The "skipped" Angle 6 status should be reconsidered if M5 scope expands to include non-shell components (e.g., Python wrappers).
