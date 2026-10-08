# Verification Report: code-conventions-impact
Generated: 2026-10-08 | Mode: automated | Revision: 3 (2 revision loops + reconciliation)

## Summary
- CRITICAL: 16 found, 16 resolved
- WARNING: ~45 found; all reconciled in the plan text (Revision 3), apart from the residuals listed under "Residual"
- INFO: ~20
- Overall: **PASS WITH WARNINGS**
- Structural lint (Angle 6, checks 6/7/8): `aa-ma-lint-views --coverage` exit 0, `render: PASS`, `sigils: edges=25 checked=25 phantom=0 unknown=0`. Checked after `codemem build` (239 files); the index had been 7 files stale.

## Angle 1: Ground-Truth Audit (Explore)
CRITICAL (resolved):
- The M4 TOC rule would fail on 23 existing references files over 100 lines. Fix: the rule applies to touched files only, with a TOC_ALLOWLIST for the existing files.
- Four descriptions start with "Use ", not one. Fix: the rule is now second person only (`you`/`your` outside quoted trigger phrases).
- The plan relied on `mcp_tools/sanitizers` functions that do not exist (the sanitizers validate and raise). Fix: a new never-raising `sanitize_context_line`.

WARNING (reconciled): the `languages:` frontmatter key; ADR count is 8 (next free 0018); install.sh does not back up ruff-format.sh; fork tooling hard-codes mattpocock; co_changes excludes linked partners; settings line :561; 31 test files; the readlink target also needs changing.

OK: 60+ claims confirmed (paths, line citations, counts, tool versions, outside-repo state).

## Angle 2: Assumption Challenge
CRITICAL (resolved):
- The fence-3 regex rejected pytest's default `=== N passed ===` line. Fix: strip the banner, then match.
- `gitleaks git` does not exist in 8.18. Fix: `detect` / `protect`.
- `uv audit` is experimental and reports 13 vulnerable packages. Fix: the pip-audit fallback plus triage step 8.4a.
- Fence 4 could not see uncommitted milestone changes. Fix: changed set = merge-base..HEAD ∪ working tree.

VERIFIED: A1 (PreToolUse and PostToolUse additionalContext), D417 under the google convention, A3 (JSON output), A5 (3 fixture-only gitleaks hits), merge-base viability.

WARNING (reconciled): worktree `.venv` and index; mixed fence/gate versions; plan files not on main (prerequisite merge added); `PRE_COMMIT_*_REF` env vars; fetch-depth 0; pre-commit install; ruff version skew; Bash 600 s timeout; non-pytest repos (D10 opt-out); co_changes cache, ghost paths and the lock-held refresh; mkdir markers; MultiEdit does not exist; D9 delegation; plugin eval publishes by default; allowlist test; the M3.4 references pin; M13 docs-only vs src; rebase-merge rollback; S404 preview-only; P1 vs map wording (Ste D8).

## Angle 3: Impact Analysis
CRITICAL (resolved):
- impact.py would have imported aa_ma.render, breaking the render-is-leaf contract. Fix: a new `aa_ma.contract_rows` leaf module.
- log.sh was never installed. Fix: `aa-ma-log.sh`, plus install and uninstall entries.
- The new fences would have sat inside the first §6.7 block that `_gate_fence` runs. Fix: separate blocks.
- A live install.sh run from a worktree would point `~/.claude` at it. Fix: live installs run from main only, as post-merge step N.0.
- Indexing markdown edges had side effects. Fix: a new `plugin_edges` table, with `.md` not indexed.

WARNING (reconciled): the MCP tool count (13 to 14) in 5 docs and a test; verify-impl fallback; per-milestone counts (standing rule); golden/architecture regen; commands-path readers; text pinned by tests in M5; Stage D and the bats job Bandit; leftovers in M7 and M12.

## Angle 4: Acceptance Criteria Falsifiability
Initial score: 59/94 falsifiable (63%). Revisions added concrete ACs to every flagged step: 1.1 BASELINE format; 1.3 `--files`; 2.1, 3.6, 4.3, 7.5, 8.1, 8.3, 9.3, 11.2, 11.7, 12.1–12.4, 13.2, 14.x; generic ADR AC; the standing rule "no explicit AC means the Contract-named tests pass". Banned or vague terms rewritten. Human-judgement ACs now name a context-log or provenance artifact.

## Angle 5: Fresh-Agent Simulation
Cannot start until the AA-MA artifacts exist (expected; Phase 5 creates them). Resolved: the 1.3 AC was a backfill; line vs file scope; CLI flag/env precedence; pre-commit hook sourcing (all local); BASELINE commands; the 1.2 failing-first test; canary PR mechanics; ADR INDEX row.

## Angle 6: Specialist Domain Audit
Specialists dispatched: Engineering Standards Auditor (always), Security Auditor (keywords: secret, token, credential).
- Engineering Standards: 1 CRITICAL resolved. Post-merge sub-steps inside HARD milestones moved to step N.0 of the next milestone, and the release moved to its own milestone M14 (Ste D11). Warnings reconciled: brace globs (fnmatch), version-pipeline globs, impact.py/gitutil in hook-modification scope, M1 profile `full`, M13/M14 Risks and tests, complexity-router, CRITICAL_PATH_REVIEW standing rule, §5a MultiEdit, the `--json` and `contract_paths` names. All canonical values were checked with plan_parsers.
- Security: 1 CRITICAL resolved. `ruff-format.sh` must never run the edited repo's `.venv/bin/ruff`; it resolves only via the forge root or PATH, with a sentinel bats test. Warnings applied as §0 "Security hardening (v2)":
  - hook JSON via `jq --arg`;
  - gate inputs read from the merge-base copy;
  - `.gitleaksignore` fingerprints;
  - hashed pip-audit;
  - setup-uv pinned to a SHA;
  - the `env -i` eval sandbox;
  - redaction in a Formatter, with ReDoS bounds;
  - MIT LICENSE files for forks;
  - git ref validation;
  - install.sh backups.
  
  Two prior decisions were reopened and re-decided by Ste: D12 (the commit scan keeps blocking via forge-pinned Ruff S) and D9 revised (sole-dev-merge and aa-ma-share become user-only).

## Re-verification (loop 2, fresh agent)
All 16 CRITICALs RESOLVED. 8 warnings plus INFO stale text were fixed in Revision 3:
- a precedence rule;
- the contract_rows module (avoids a grammar↔plan_parsers cycle);
- a pronoun-rule refinement;
- the version-pipeline globs;
- §2a Critical-Path for M4/M12;
- grandfather check before merge-base;
- the D12 test row;
- stale text.

## Residual (accepted)
- The review appendices (CEO/Eng output) are historical records and keep pre-revision wording; the precedence rule governs.
- Amendment-only files (forks.py, fork-drift.sh, git_mining.py, .importlinter, aa-ma-scribe.md, sanitizers.py) are not Contract `Files:` rows, so coverage lint cannot see them. This plan is grandfathered from IMPACT_VERIFIED, so nothing is gated on it.
- Re-run `/verify-plan code-conventions-impact` after Phase 5, so the tasks.md gate parse (check #2) runs.

## Revision History
- v0: 2026-10-08. Wave 1 + 2: 16 CRITICAL, about 45 WARNING → FAIL.
- v1: 2026-10-08. Inline fixes + per-milestone amendments; decisions D8–D10.
- v2: 2026-10-08. Post-merge steps (N.0), M14 release, security hardening; decisions D11, D12, D9 revised.
- v3: 2026-10-08. Re-verification reconciliation → PASS WITH WARNINGS.
