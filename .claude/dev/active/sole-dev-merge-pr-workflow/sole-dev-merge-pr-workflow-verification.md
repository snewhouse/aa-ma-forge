# Verification Report: sole-dev-merge-pr-workflow

**Generated:** 2026-05-18T11:35:00+01:00
**Mode:** automated
**Revision:** 1 (pre-revision)
**Result:** **FAIL** (17 CRITICAL — blocks artifact creation in automated mode)

## Summary

| Severity | Count |
|----------|------:|
| CRITICAL | 17 |
| WARNING | 23 |
| INFO     | 5  |

Plan has substantial fact-grounding gaps + 1 unspecified-novel-architecture gap + post-v0.8.0 standards-compliance gaps. Revision required before AA-MA artifact creation.

---

## Angle 1: Ground-Truth Audit

### CRITICAL

| # | Finding |
|---|---------|
| C1 | `security-scanning:security-sast` is **NOT a skill** — it is a slash command (`/security-scanning:security-sast`). It cannot be dispatched via the Agent tool as plan M2.2 attempts. |
| C2 | `superpowers:security-review` **does not exist** in the installed superpowers plugin v5.1.0. Available skills: brainstorming, dispatching-parallel-agents, executing-plans, finishing-a-development-branch, receiving-code-review, requesting-code-review, subagent-driven-development, systematic-debugging, test-driven-development, using-git-worktrees, using-superpowers, verification-before-completion, writing-plans, writing-skills. M2.2 fallback path has no implementation. |

### OK (verified)

- All file path existence claims correct (15/15)
- All gh/glab CLI flag claims correct except as noted
- gh v2.92.0 / glab v1.80.4 verified
- Biorelate dual-remote pattern verified in `bk_*.md` rules
- L-007 in docs/lessons.md verified
- aa-ma.md L-080/081/082 references verified

---

## Angle 2: Assumption Extraction & Challenge

### CRITICAL

| # | Finding |
|---|---------|
| C3 | **Rollback baseline broken.** Section 7 step #2 says `git show c2bf40c:claude-code/commands/sole-dev-merge.md` — but file is **user-local at `~/.claude/commands/`**, not in plugin git history. `git show c2bf40c:...` returns "fatal: path does not exist." Correct rollback path uses install.sh's `.bak.<ts>` mechanism (line 116). |
| C4 | **Code-reviewer agent contract MISMATCH.** `feature-dev:code-reviewer` emits "confidence scores 0-100" + "Critical/Important" 2-tier; alt `code-reviewer` agent uses "Critical/Warnings/Suggestions" 3-tier. **Neither emits the CRITICAL/HIGH/MEDIUM/LOW 4-tier** the plan's `findings-triage.sh` parses for. M2.3 auto-fix never triggers; M2.4 routes nothing to user. |
| C5 | **`gh pr checks --watch` exit-code claim unverified.** Plan acceptance 4.1: "exits with code 0 (clean)" after 901s timeout. But `timeout 900s gh pr checks --watch` returns 124 on SIGTERM, not 0. The script must explicitly `|| true` or translate exit codes. Criterion unachievable as written. |
| C6 | **glab `--remove-source-branch=false` is wrong syntax.** Boolean flag — no `=value` accepted. Will either silently truthify or fail parse. Plan probably means "omit the flag entirely." |
| C7 | **`Critical-Path: external-api` is the wrong canonical match for M4 (auto-merge).** Per canonical table in engineering-standards.md, `version-pipeline` (release/merge mechanics) fits better. M3 (gh/glab CLI contract surface) is OK as `external-api`. |

### WARNING

- W1: code-reviewer agent defaults to **unstaged changes**, not `git diff main...HEAD` — plan must explicitly inject scope
- W2: Commitizen does **not** enforce per-commit (no commit-msg hook) — plan claim mischaracterized
- W3: Force-push semantics unspecified for rebase
- W4: AskUserQuestion limit conflated (per-question vs per-panel; 4 questions per call, each with up to 4 options)
- W5: README "currently 19 skills" is off-by-one (actual is 19 today, becomes 20 with new skill)
- W6: "First line of plan objective" is ambiguous
- W7: Smoke test dual-remote venue unspecified

---

## Angle 3: Impact Analysis

### CRITICAL

| # | Finding |
|---|---------|
| C8 | **install.sh modification is a PHANTOM requirement.** `scripts/install.sh` lines 257-269 auto-discover commands (`for f in claude-code/commands/*.md`) and skills (`for d in claude-code/skills/*/`). New command + skill picked up automatically. Plan M5.2 over-specifies. |
| C9 | **SECURITY.md omitted from MODIFY list.** Lines 11-12 have hardcoded counts (`10 command files`, `19 skills directories`) and inline name lists. Need updating to 11 / 20 + name appended to both lists. Pre-existing drift: SECURITY.md says 19, CLAUDE.md says 18. Real count via `ls` is 19. |

### WARNING

- W8: CLAUDE.md lines 48-50 hardcoded counts (`10 slash commands`, `18 reusable procedures`) — plan must specify 11 and 19 explicitly (and reconcile pre-existing drift)
- W9: `tests/skills/test_sole_dev_merge_frontmatter.py` should be added (precedent set by 5 other skills)
- W10: `.github/workflows/security.yml` doesn't run bats — new bats tests are local-only without CI step
- W11: No ADR mentioned for this architectural change (precedent: ADRs 0001-0007)
- W12: `docs/spec/aa-ma-quick-reference.md` "table row" — no command table exists yet to add to
- W13: `tests/hooks/install_dry_run.bats` should be extended (precedent at lines 25-41 for grill-with-docs)

---

## Angle 4: Acceptance Criteria Falsifiability

### Score: 10/10 falsifiable (target met)

All criteria are falsifiable as written. Two have minor harness-spec gaps that can be closed in reference.md:

- W14: 2.4 + 3.2 — AskUserQuestion test harness mechanism not specified (need spy/log contract)
- W15: 2.3 wording slight ambiguity ("file no longer matches `bandit -t B602`")

No banned vague terms found. L-059 discipline followed.

---

## Angle 5: Fresh-Agent Simulation (Step 1.1)

### CRITICAL

| # | Finding |
|---|---------|
| C10 | **Step 1.1 has no concrete `SKILL.md` frontmatter content.** Plan says "frontmatter declares the skill name + description" but never gives the exact name, description string, or any required schema fields. Implementer must invent. |
| C11 | **No precedent for `skill/lib/*.sh` architecture in this repo.** All 19 existing skills are single `SKILL.md` files — no `lib/` subdirectory pattern exists. Plan introduces a novel pattern without justification, schema, or discovery mechanism. |
| C12 | **Skill ↔ command markdown ↔ lib invocation contract undefined.** Does the command call `Skill(sole-dev-merge)` (single dispatch), or directly `bash claude-code/skills/sole-dev-merge/lib/preflight.sh` (subprocess), or `source ...` (shared shell env)? Each model has very different implications for env vars, exit codes, and test mocking. Plan must pick one before Step 1.1 can be implemented. |

### WARNING

- W16: Existing user-local global skill `sole-dev-merge` (in skill list) will collide with plugin skill of the same name — install.sh symlink behaviour for skills not specified
- W17: `lib/` directory creation not explicitly in Step 1.1 artefacts (Step 1.2 implicitly creates it)
- W18: "thin orchestration wrapper" qualitatively undefined
- W19: Step 1.1 has no acceptance criterion (Section 4 starts at 1.3) — violates plan's own L-059 rule
- W20: Step 1.1 has no test (M1 tests start at 1.6)

### INFO

- I1: Plan should explicitly invoke `Skill(write-a-skill)` for Step 1.1
- I2: Plan should embed a 10-line `SKILL.md` template inline

---

## Angle 6: Specialist Domain Audit (API Contract + Engineering Standards)

### CRITICAL

| # | Finding |
|---|---------|
| C13 | **`glab mr create --description-file` is a FABRICATED flag.** Actual `glab mr create` has only `-d/--description` (string). The plan's GitLab branch in 3.4 fails immediately on flag parse error. Additionally, `--remove-source-branch=false` (already flagged as C6) compounds the issue. |
| C14 | **`gh pr create` duplicate-PR failure unhandled.** Re-running `/sole-dev-merge` after a partial prior run finds an existing PR → `gh pr create` exits non-zero with "pull request already exists." No idempotency check. Required: pre-check `gh pr view --json url` and reuse. |
| C15 | **`glab ci status` is NOT a script-safe poller.** Plan M4.1 says "poll `glab ci status` in a bash loop." But `glab ci status` (and `--live`) is a TTY/UI command with no documented exit-code contract for pass/fail/pending. Must use `glab api /projects/:id/merge_requests/<iid>` and parse JSON status. |
| C16 | **Audit-Profile absent from all 5 milestones (post-v0.8.0 cutover).** v0.8.0 released 2026-05-11; plan Created: 2026-05-18 = 7 days post-cutover. Per plan-verification Angle 6 Check #4, every milestone MUST declare `Audit-Profile: full | code-only | docs-only | infra | custom`. Plan declares NONE. `/execute-aa-ma-milestone` Phase 6.8 refuses advance on first close. |
| C17 | **`Prototype-Required: YES` misapplied on Step 3.1.** Canonical Theme 1: "Prototype first on uncertain changes." Plan's own description says "short bash script touched once" with deterministic JSON output. This is NOT uncertain. The HARD gate forces an artificial PROTOTYPE ceremony. If the dual-remote UX is uncertain, move flag to Step 3.2 instead. |

### WARNING

- W21: `gh pr update-branch` (Risk M4.2 mitigation) is admin-only on protected branches — returns 403 otherwise
- W22: Auth pre-check missing — 15min unattended poll can hit token expiry mid-flight
- W23: rebase-merge × branch-protection collision (plan doesn't pre-check `allow_rebase_merge`)
- W24: Concurrent invocation race (multiple `/sole-dev-merge` runs)
- W25: Section 12 uses non-canonical "STRONGLY YES" value for Theme 4 (should be "YES")
- W26: M5 should also carry `Critical-Path: doc-count-drift` (Tier 6 detector domain — M5 explicitly enumerates count updates)
- W27: 3.3 (AI body gen) and 3.5 (AA-MA footer) produce code without bats tests — need either tests or canonical `TDD-Waiver:`

### INFO

- I3: gh API rate-limit headroom is fine (5000 req/hr) but `--watch` performs 5-10 calls per poll cycle; concurrent runs could pressure it
- I4: Concurrent invocations: pre-merge rebase can race; plan should at least document "one run per repo at a time" assumption

---

## Specialist Recommendations (highest priority for revision)

1. **Replace M2 security agent path entirely.** Use `security-auditor` agent (exists in `~/.claude/agents/security-auditor.md`) OR keep just `feature-dev:code-reviewer` and explicitly task it with security-focused prompt for files matching auth/secrets/exec patterns.
2. **Define the skill architecture concretely.** Pick: (a) command-only with helpers as bash functions inlined in command markdown, or (b) skill with lib/ pattern + explicit invocation contract documented in SKILL.md, or (c) a single executable script under `scripts/sole-dev-merge.sh`.
3. **Convert severity scheme.** Either: (a) post-process agent's free-form output through a deterministic classifier, or (b) bring the reviewer in-tree as `claude-code/agents/sole-dev-merge-reviewer.md` with explicit severity contract.
4. **Add `Audit-Profile:` to all 5 milestones** (suggested: M1=code-only, M2=full, M3=full, M4=code-only, M5=docs-only).
5. **Re-tag Critical-Path:** M3=external-api (keep), M4=version-pipeline, M5=doc-count-drift.
6. **Drop or relocate `Prototype-Required:`** from 3.1; if applied, apply to 3.2 (decision logic) which has UX uncertainty.
7. **Add SECURITY.md + ADR-0008 to MODIFY list.** Resolve pre-existing CLAUDE.md vs SECURITY.md skill-count drift in the same PR.
8. **Remove install.sh modification step from M5** (auto-discovery already covers it). Replace with `./scripts/install.sh --dry-run` verification.
9. **Fix gh/glab CLI contracts:**
   - Add `gh pr view --json url || gh pr create ...` idempotency wrapper for 3.4
   - Replace `glab mr create --description-file` with `glab mr create -d "$(cat $BODY)"` or `glab api`
   - Replace `glab ci status` polling with `glab api /projects/:id/merge_requests/<iid>` JSON parse
   - Add `|| true` / exit-code translation around `timeout 900s gh pr checks --watch`
10. **Fix rollback Section 7** to reference `.bak.<ts>` mechanism, not non-existent git path.
11. **Add Step 1.1 concrete deliverable:** inline `SKILL.md` template + Step 1.1 acceptance criterion.

---

## Revision History

- **v1 (2026-05-18T11:35:00+01:00):** Initial verification, automated mode. **FAIL** — 17 CRITICAL, 23 WARNING, 5 INFO. Plan requires revision before artifact creation.
- **v2 (2026-05-18T11:55:00+01:00):** Plan revised. Spot-check verification against all 17 CRITICALs:

  | # | CRITICAL | v2 Status | Evidence |
  |---|----------|-----------|----------|
  | C1 | security-scanning:security-sast not a skill | **RESOLVED** | Plan §2.2 dispatches `security-auditor` agent (verified exists at `~/.claude/agents/security-auditor.md`) |
  | C2 | superpowers:security-review doesn't exist | **RESOLVED** | Same — security-auditor + Bandit + ShellCheck replaces both |
  | C3 | Rollback git path broken | **RESOLVED** | §5.1 + §7 use `~/.claude/backups/aa-ma-forge-<ts>/` (install.sh's existing `.bak` mechanism) |
  | C4 | Severity scheme mismatch | **RESOLVED** | §2.1/§2.2 specify explicit `[CRITICAL]/[HIGH]/[MEDIUM]/[LOW]` prompt contract; safe-default fallback (all-HIGH) when agent ignores contract |
  | C5 | gh exit-code translation | **RESOLVED** | §4.2 GitHub branch translates RC=124 → STATUS:CI_TIMEOUT + clean exit 0 |
  | C6 | glab --remove-source-branch=false syntax | **RESOLVED** | §3.4 omits the flag at create time; deletion handled at merge time via `--remove-source-branch` (boolean) |
  | C7 | Critical-Path:external-api wrong for M4 | **RESOLVED** | M3=external-api (CLI contract); M4=version-pipeline (release/merge mechanics); M1+M5=doc-count-drift |
  | C8 | install.sh phantom edit | **RESOLVED** | §5.2 replaced with `./scripts/install.sh --dry-run` verification; "EXPLICITLY NOT MODIFIED" §5 note added |
  | C9 | SECURITY.md/CLAUDE.md count drift omitted | **RESOLVED** | §5.4 enumerates 5 docs (SECURITY.md added) with explicit count deltas; resolves pre-existing 18↔19 drift |
  | C10 | Step 1.1 no concrete frontmatter | **RESOLVED** | §2 M1.1 inlines the YAML frontmatter verbatim |
  | C11 | Novel skill/lib pattern undefended | **RESOLVED** | Entire skill/lib pattern DROPPED; command-only design per user choice |
  | C12 | Skill/command contract undefined | **N/A** | No skill exists; single command file |
  | C13 | glab --description-file fabricated | **RESOLVED** | §3.4 uses `glab mr create ... --description "$(cat $BODY)"` |
  | C14 | gh duplicate PR failure | **RESOLVED** | §3.4 GitHub branch: `gh pr view --json url 2>/dev/null` idempotency pre-check, reuses via `gh pr edit` |
  | C15 | glab ci status not script-safe | **RESOLVED** | §4.2 GitLab branch uses `glab api /projects/:id/merge_requests/<iid>` JSON polling |
  | C16 | Audit-Profile absent on all milestones | **RESOLVED** | All 5 milestones declare canonical value: M1/M4=code-only, M2/M3=full, M5=docs-only |
  | C17 | Prototype-Required misapplied | **RESOLVED** | Dropped from 3.1; not relocated (no truly uncertain step in workflow) |

  **WARNINGs addressed (partial list of high-priority items):**
  - W2 (no per-commit commitizen): plan §3.3 acknowledges fallback for non-conventional subjects
  - W5 (off-by-one skill count): §5.4 corrects to actual count (19 stays 19 — no skill added)
  - W21 (gh pr update-branch admin-only): §10 M4.2 mitigation adds local rebase fallback
  - W22 (auth pre-check missing): §3.5 added explicit auth pre-flight
  - W23 (rebase × branch-protection): §4.1 added `allow_rebase_merge` pre-check with --merge fallback
  - W25 (STRONGLY YES non-canonical): purged — all Theme entries use plain "YES"
  - W26 (M5 should be doc-count-drift): added
  - W27 (3.3/3.5 lack tests): test_stage_f_idempotent.bats covers §3.4 idempotency including body usage

  **Remaining WARNINGs (intentional):**
  - W3, W4, W6, W7, W8 (subtler items): deferred to execution-time refinement
  - W9, W10, W11 (frontmatter test, bats CI, ADR): ADR-0008 added to MODIFY; bats CI step in §5.6
  - W12, W13 (quick-reference table, install_dry_run extension): captured in §5.4 + §5.2

  **v2 Result:** **PASS WITH WARNINGS** — proceeding to AA-MA artifact creation.

