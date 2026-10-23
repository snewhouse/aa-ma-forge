# Verification Report: sole-dev-merge-simplify
Generated: 2026-10-20 | Mode: automated | Revision: 4

## Summary
- **CRITICAL:** 6 found, 6 resolved.
- **WARNING:** about 45 raised; those that pinned a contract or AC were folded into revs 2–4, and the rest are recorded below.
- **INFO:** about 25.
- **Overall:** PASS WITH WARNINGS (0 open CRITICAL after rev 4).
- **Exit contract applied** (plan §3): a CRITICAL needs a concrete failure path. There were two revision loops (rev 2 after Wave 1, rev 3 after Angle 5). Angle 6 found no CRITICAL, and its warnings went into rev 4 as text only, with no re-run.

## Angle 1: Ground-Truth Audit (38 OK)
- **[CRITICAL → fixed rev 2]** The 2.2 AC grep could never reach 0. The frozen draw snapshots `tests/fixtures/draw-node-ids.json` and `draw-prototype-graph.json` name `extract_stage.sh`. Fix: `--exclude-dir=fixtures`.
- **[WARNING → fixed rev 2]**
  - Threat-Model line missing from the Contracts.
  - Stale size (now 1,994 lines / 77%).
  - The 409 stub should be a GraphQL error.
  - The appear-wait came from PRs #50/#51, not #49.
- **[WARNING, open]** The gh contract was not probed live; the 1.0 prototype is the live check.

## Angle 2: Assumption Challenge (9 verified)
- **[CRITICAL → fixed rev 2]** The shared gh stub has no check-runs arm and no rc control for G1, so 3 new tests could not go GREEN. Fix: new `tests/commands/sdm/fixtures/`; the old ones stay untouched.
- **[CRITICAL → fixed rev 2]** The fixture grep (same as Angle 1).
- **[WARNING → fixed rev 2]**
  - Prototype branch unnamed (now `prototype/sdm-script`, never merged).
  - `/sole-dev-merge` loads main's skill, so the worktree's script runs by path.
  - Hidden pushes: separate Bash calls.
  - The M2 refactor waiver was contradicted.
  - A red window between 2.1 and 2.2 (now one commit).
  - The finalize branch was unnamed.

## Angle 3: Impact Analysis (13 OK)
- **[CRITICAL → resolved by Ste]** code-conventions-impact M14 owns v0.18.0. Ste decided this plan cuts no release; its changes ship in v0.18.0.
- **[WARNING → fixed rev 2]**
  - Plugin-surface regen in M1.
  - New stub arms.
  - The fixtures move and its load paths (moot: new fixtures).
  - The rule-8 comment and the non-orphan token.
  - Step order in M2.
  - Touched-job shellcheck args and exec bit.
  - Stale comments (install.sh:385, measure.py:5).

## Angle 4: Criteria Falsifiability (31/39 falsifiable before revs)
- **[CRITICAL → fixed rev 2]** An all-`skipped` run met the green rule. Now: all completed, ≥ 1 success, and all conclusions in success/skipped/neutral.
- **[WARNING → fixed revs 2–3]** Made concrete:
  - who merged (STATUS: OK quoted in PL);
  - prototype findings `n=<k>`;
  - the TODOS triage grep;
  - `bats --count` with N recorded, plus a RED log;
  - the sources for the size limits;
  - the footer and DROP greps;
  - the SKILL.md call grep;
  - the 2.2/2.3 deliverable ACs.

## Angle 5: Fresh-Agent Simulation
- **[CRITICAL → fixed rev 3]** No per-test map existed. One was added to the inventory: file:line → KEEP/CHANGE → target file (79 + 23 = 102).
- **[WARNING → fixed rev 3]** Pinned:
  - the strategy source in `finish`;
  - the check-runs rule, endpoint and stub knob;
  - the output strings;
  - the notes file and the reviews in 1.0/1.4;
  - the CI_TIMEOUT hint (no `--auto`);
  - 1.3 observed at 1.4;
  - the hook tests (2 re-pointed, 2 dropped, sdm.sh sourceable);
  - the PL/CL abbreviations;
  - the 1.2 AC commands.

## Angle 6: Specialist Domain Audit
- **Specialists dispatched:** Engineering Standards Auditor (always), API Contract + Security.
- **Engineering standards: 0 CRITICAL.** Every parser value is valid, lint PASS, 13/13 elements.
  - **[WARNING → fixed rev 4]**
    - `Prototype-Required: YES` and `Gate: HARD` are now fields;
    - the M2 TDD-Waiver was dropped (the auditor passes without it);
    - `scripts/install.sh` is drawn;
    - a plan-wide Test-Command plus pass regex.
- **API/security: 0 CRITICAL.**
  - **[WARNING → fixed rev 4]**
    - `--match-head-commit` takes `$SHA`, not the literal `HEAD`;
    - `PR_NUM` is validated (`^[1-9][0-9]*$`);
    - `allow_rebase_merge` must be literal true/false (`null` ABORTs);
    - the PR is used only if OPEN, own repo and headRefOid == SHA;
    - MERGED is confirmed before any delete;
    - check-runs `total_count` equals the runs read;
    - the watch output goes to /dev/null;
    - the slug is derived from origin.
  - **[INFO, accepted]**
    - A closing keyword in the notes could close an issue (recorded in ADR-0024).
    - Commit statuses are not gated.

## Revision History
- **v1** (2026-10-20): Wave 1 found 4 distinct CRITICAL (fixture grep, shared stub, all-skipped green, v0.18.0 owner) → FAIL.
- **v2:** all 4 resolved; v0.18.0 decided by Ste.
- **v3:** Angle 5 CRITICAL (per-test map) resolved; ambiguities pinned.
- **v4:** Angle 6 found 0 CRITICAL; its warnings were folded in → PASS WITH WARNINGS.
