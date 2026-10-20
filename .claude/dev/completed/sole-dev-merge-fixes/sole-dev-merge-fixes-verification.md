# Verification Report: sole-dev-merge-fixes
Generated: 2026-10-15 | Mode: automated | Revision: 4

## Summary
- CRITICAL: 17 raised across both waves (some overlap between angles), **17 resolved**. Loop 2 raised 1 more, which is resolved in rev 4.
- WARNING: about 45 raised. Each was resolved in revs 2–4 or accepted, as listed below.
- INFO: about 30.
- Overall: **PASS WITH WARNINGS** (rev 4). The accepted warnings are listed at the end.

Checks re-run on rev 4:
- `aa_ma_gate` rc 1 ("no milestone is ACTIVE", which is expected before execution); `aa_ma_deps check` rc 0;
- `aa-ma-lint-views --coverage` rc 0, render PASS, no UNDRAWN_PATH;
- `aa_ma.grammar.find_non_canonical` → `[]`; canonical dependency lines → none bad;
- privacy check: denylist count 0, private-path grep 0.

## Angle 1: Ground-Truth Audit
- **CRITICAL, resolved:**
  - Existing G3/G4 tests never set ORIGINAL_BRANCH → added to `setup()`.
  - The plan cited a G3 "blocked" test that doesn't exist → the existing tests are now named instead.
  - The `~/.claude/hooks/lib/aa-ma-footer.sh` fallback was never installed → new Sub-step 1.9 adds the install link.
  - "Hooks lib unchanged since 9546a2e" was false (aa-ma-parse.sh +52 lines) → reference corrected; anchors re-checked.
  - The gh stub's `api` arm would answer the read-back with `true` → the arm ordering is specified.
- **WARNING, resolved:**
  - `aa-ma-parse.sh:242` vs `:243`;
  - SKILL.md `:13` is prose, not frontmatter;
  - the smoke `set -a` lines are `:146-204`;
  - the commit-drift and session-end-dirty anchors;
  - the draw-node-ids premise was wrong;
  - the `prompt_id` field;
  - the ADR-0008 range;
  - the PR list (#25 was a close).
- 50 claims confirmed OK.

## Angle 2: Assumption Extraction & Challenge
- **CRITICAL, resolved:**
  - The commit-signature hook lists plans from `$PWD`, so a main-rooted session can't commit M1 (probed rc 2) → execution sessions start in the worktree (decision 14).
  - The state loader was first-write-wins, and lost a trailing `=` → rev 2, then the rev 3/4 base64 loader (last good write wins).
  - The footer's `|| echo main` was dead code without pipefail → a no-pipeline fallback.
  - Fence 3 would run only pytest → `Test-Command: bats --tap …` added.
  - "main is protected" was false (404) → rollback text corrected.
- **WARNING, resolved:**
  - CCI file overlap is listed in §0.
  - Bootstrap gaps: don't run the unfixed G4; check before B-commit; run the Stage C scans by hand.
  - Untracked plan dirs now count as touched.
  - The loader's branch check is in place.
  - Merge-queue behaviour is documented (A6).
  - Empty env does not mask the file.
- Verified: A1 (per-worktree git-dir); the first `worktree list` entry is the main worktree; `delete_branch_on_merge=false`; `%q`/eval round-trips (since replaced by base64).

## Angle 3: Impact Analysis
- **CRITICAL, resolved:**
  - The commit-signature hook reads only literal text, so the skill's `${FOOTER}` commits are blocked → Sub-step 1.7 accepts the canonical helper shape.
  - Footer install link → Sub-step 1.9.
- **WARNING, resolved:**
  - check-conventions WHY001 on new `.sh` lines → `# why:` comments added.
  - The plugin-surface golden drifts → regen runs at every verify step.
  - The pre-compact stdin read and the jq-missing path → `[[ -t 0 ]]` plus a timeout; fail open.
  - CCI M11's merge-base helper (DRY) → a TODO.
  - The M2 bats files feed blocks through env → listed in the Contract.
  - The ADR-0008 drift is fixed in M1.
  - TODOS:239 is closed.
  - The lesson-ID namespace is noted.
- OK: SKILL.md/references callers; CONTEXT.md; ADR-0018.

## Angle 4: Acceptance Criteria Falsifiability
- Score at rev 1: 51/82 falsifiable (62%). Banned terms: "works" ×2, "is complete" ×1.
- Rev 2 rewrote every flagged criterion as a command, grep, @test name or provenance/context-log literal.
  - RED claims now say "record the not-ok count and name the guard cases", since some new cases already pass on unfixed code.
  - The M2 grep that could pass falsely now covers `SLUG.*date +%s`, `PR_NUM:-0`, `:-feature` and `NOSLUG`.
  - The 1.0 verdict string is unified.
  - Impact evidence is a provenance line.
  - Live checks name the artefact that proves them.

## Angle 5: Fresh-Agent Simulation
- **CRITICAL, resolved:**
  - The AC grep for `--delete-branch` contradicted the snippet's own comment → comment reworded, and the grep is anchored to `gh pr merge.*--delete-branch`.
  - The E6 probe could not delete its repo (no `delete_repo` scope) → `gh auth refresh -s delete_repo` plus explicit steps.
- **WARNING, resolved:**
  - The verdict strings disagreed.
  - The G4 test text vs snippet, and the cleanup quoting → `%q`, plus an AC2.2b test.
  - 1.10 now depends on 1.4.
  - The AA-MA files are committed first, in 1.0.
  - ACs that could not fail: WHY001 on `.md` → an awk check; the AA_MA_FOOTER_HELPER grep → a `footer-resolve` marker.
  - The post-merge records go to 2.0, and the worktree cleanup and M2 naming are stated.
  - The TODO convention (`## Completed` plus `**Done:**`).
  - Test line numbers replaced by test names.
- **INFO, applied:** the full G4 tail; the stub arm order; CLAUDE_HOME isolation in the footer test; the header comments; install backup handling; the spec §VI note; G4 avoids SIGPIPE.

## Angle 6: Specialist Domain Audit
### Specialists dispatched: Engineering Standards Auditor (always), Security Auditor
- **Engineering standards:**
  - All 13 elements present; parsers valid (hook-modification, full, Diagram-Waiver none); TDD RED before GREEN; deps canonical; lint rc 0; 0 private-repo names.
  - **WARNING, resolved:** M4 now names its gate lines; L-037 `[post-merge]` tagging covers M2–M5; 1.5 depends on 1.0.
  - **WARNING, accepted:** 1.7, 1.8 and 1.9 each hold RED and GREEN in one sub-step. Their criteria require RED evidence, and commit order enforces the sequence.
- **Security:**
  - **CRITICAL, resolved:** the pre-compact hook follows symlinks when it appends and when it `cat`s, so an untrusted clone could write into `~/.bashrc` (reproduced with a fake HOME). This predates the plan; Ste moved the fix into M1 as Sub-step 1.8.
  - **WARNING, resolved:**
    - The state loader `eval` → base64 with no eval, a 15-key allowlist, and a symlink/owner/permission refusal; Stage A recreates the file under umask 077.
    - G3 delete → `:refs/heads/<b>`, an exact-ref ls-remote, and the head-ref, default-branch and check-ref-format guards.
    - G4 option injection → check-ref-format and `refs/heads/` forms.
    - 1.7 hook trust → canonical shape only, with bypass RED cases.
    - `/tmp` run files → a private `$SDM_DIR` under the git-dir.
    - Probe evidence leaking paths → redaction plus a per-gate privacy check.

## Re-verification (loop 2, rev 3 → rev 4)
- All 13 prior CRITICALs are RESOLVED. Each snippet was run verbatim in scratch repos: the G3 arm against a bare remote with tag `feature` and branch `other/feature`; the footer helper with and without pipefail; the loader with hostile lines.
- **CRITICAL, resolved:** the sub-step IDs `1.6b/c/d` were non-canonical, which would break CI and main after merge → renumbered 1.7–1.12. `find_non_canonical` → `[]`.
- **WARNING, resolved:**
  - The privacy grep matched its own text → bracketed pattern.
  - A G3 `# why:` sat two lines above its line → moved.
  - The FOOTER reassignment bypass → RED case plus single-assignment rule.
  - Loader: a bad line overwrote a good one, and a bad ORIGINAL_BRANCH bypassed the branch check → decode into a temp; missing or empty counts as foreign. Re-tested: PR_NUM stays 7; `$(touch PWN)` runs nothing; a branchless file is ignored.
  - M5 test counts are now ≥ 24, with 16 of 17 tests having no stdin.

## Accepted warnings (not fixed)
- Sub-steps 1.7, 1.8 and 1.9 are RED/GREEN in one sub-step (see Angle 6).
- Portability: `stat -c %a` in a test, and `base64 -d` on old macOS. CI runs Linux.
- State values lose trailing newlines. Documented; no key needs one.
- Fence 3's runtime for about 580 bats tests is unmeasured against its 540 s timeout (the SDM suite alone takes 20 s). Check it at 1.11.

## Revision History
- v1: 2026-10-15 — Wave 1 (4 angles): 13 CRITICAL, 27 WARNING → FAIL.
- v2: 2026-10-15 — Wave 1 fixes; Ste decisions 14–16; criteria rewritten.
- v3: 2026-10-15 — Wave 2 (fresh agent, engineering standards, security): 3 CRITICAL → fixed; Ste decision 18 (pre-compact symlink guard into M1).
- v4: 2026-10-15 — loop 2 re-check: 1 CRITICAL (non-canonical IDs) plus 5 WARNING → fixed. **PASS WITH WARNINGS.**
