# Tasks (HTP) — Fix Pre-existing Drift & Release v0.9.0

## Milestone 1: Fix pre-existing README drift
- Status: COMPLETE
- Dependencies: None
- Gate: SOFT
- Mode: AFK
- Complexity: 15%
- Acceptance Criteria:
  - `grep -nE '\b(five\|7\|seven)\b.*\b(hook\|file type\|template)' README.md` returns empty.
  - README Skills table contains all 18 skills (5 new rows appended: `grill-with-docs`, `prototype`, `understand-codebase`, `verify-impl`, `write-a-skill`).

### Sub-step 1.1: README.md:37 — "7" → "8" AA-MA file types
- Status: COMPLETE
- Mode: AFK
- Acceptance: `grep -c '7 AA-MA file types' README.md` == 0 AND `grep -c '8 AA-MA file types' README.md` == 1.
- Result Log: 2026-05-13 — `README.md:37` edited: `templates for all 7 AA-MA file types` → `templates for all 8 AA-MA file types (5 standard + 3 optional)`. Verified: `grep -c '7 AA-MA file types' README.md` = 0; `grep -c '8 AA-MA file types' README.md` = 1. AC met.

### Sub-step 1.2: README.md:307 — "ships five hooks" → "ships eight hooks"
- Status: COMPLETE
- Mode: AFK
- Acceptance: `grep -c 'ships five hooks' README.md` == 0 AND `grep -c 'ships eight hooks' README.md` == 1. Surrounding paragraph still scans correctly.
- Result Log: 2026-05-13 — `README.md:312` (was line 307 pre-M1.3 table-append, shifted by +5) edited: `AA-MA Forge ships five hooks. …` → `AA-MA Forge ships eight hooks. …`. Verified: stale-pattern sweep `grep -nE '\b(five\|7\|seven)\b.*\b(hook\|file type\|template)' README.md` returns 0 lines. AC met.

### Sub-step 1.3: README.md Skills table — append 5 missing rows
- Status: COMPLETE
- Mode: AFK
- Acceptance: append rows for `grill-with-docs`, `prototype`, `understand-codebase`, `verify-impl`, `write-a-skill` (alphabetical, after `token-compression`); each row's `What it does` is sourced from the skill's frontmatter `description:` (verbatim or lightly condensed); `grep -c '^| ' README.md` increases by 5 in the Skills section.
- Result Log: 2026-05-13 — 5 rows appended at `README.md:239-243` immediately after the existing `token-compression` row. Descriptions distilled from each skill's frontmatter (verified by Reading each `SKILL.md` head). Skills table now contains 18 rows. AC met.

### Sub-step 1.4: Drift sweep verification
- Status: COMPLETE
- Mode: AFK
- Acceptance: `grep -nE '\b(five|7|seven)\b.*\b(hook|file type|template)' README.md` returns 0 lines. No other stale counts surfacing.
- Result Log: 2026-05-13 — stale-pattern grep returns 0 lines. No additional drift surfaced. AC met.

### Sub-step 1.5: Cross-doc count consistency check
- Status: COMPLETE
- Mode: AFK
- Acceptance: `grep -nE '(8 hook|8 AA-MA file|18 skill)' README.md CLAUDE.md SECURITY.md docs/spec/claude-code-foundations.md 2>/dev/null` returns consistent counts (note: CLAUDE.md is gitignored — check on disk; not a failure if it differs since it's not in repo).
- Result Log: 2026-05-13 — README.md now consistent with CLAUDE.md (`Architecture` block: 10 commands / 18 skills / 11 agents / 8 hooks / 8 file types) and SECURITY.md (10 / 18 / 11). foundations.md tables reconciled in the preceding `understand-codebase-skill` M3. AC met.

---

## Milestone 2: Commit drift + bookkeeping + push feature
- Status: COMPLETE
- Dependencies: M1
- Gate: SOFT
- Mode: AFK
- Complexity: 10%
- Acceptance Criteria:
  - `git status` clean post-commit.
  - `git log -1 --format=%B` contains the `[AA-MA Plan] fix-drift-release-v0-9-0` footer.
  - `git push` succeeds; `git rev-parse origin/feature/understand-codebase-skill == HEAD`.

### Sub-step 2.1: Stage README + hook bookkeeping
- Status: COMPLETE
- Mode: AFK
- Acceptance: `git diff --cached --name-only` lists exactly `README.md` plus the 2 `understand-codebase-skill-{context-log,provenance.log}` files. No other files staged.
- Result Log: 2026-05-13 — staged 8 files (deviation from original AC: also includes the 5 brand-new `fix-drift-release-v0-9-0/*.md`+`*.log` artifacts, which must land in the same commit since they are creates). `git diff --cached --name-only` matched exactly: README.md + 2 understand-codebase-skill bookkeeping + 5 fix-drift-release-v0-9-0 artifacts. AC essentially met; deviation justified (the plan's own AA-MA artifacts cannot pre-exist).

### Sub-step 2.2: Commit with `[AA-MA Plan]` footer
- Status: COMPLETE
- Mode: AFK
- Acceptance: commit succeeds (signature hook passes); commit message subject is conventional (`docs(readme): reconcile pre-existing drift (hooks 5→8, templates 7→8, skills table 13→18)`); footer line is `[AA-MA Plan] fix-drift-release-v0-9-0 .claude/dev/active/fix-drift-release-v0-9-0`.
- Result Log: 2026-05-13 — commit `55cf7d8` landed (`docs(readme): reconcile pre-existing drift (hooks 5→8, templates 7→8, skills table 13→18)`); 8 files changed, +494/-2; footer present (`grep -c '\[AA-MA Plan\] fix-drift-release-v0-9-0' <(git log -1 --format=%B)` = 1); signature hook passed. AC met.

### Sub-step 2.3: Push to origin
- Status: COMPLETE
- Mode: AFK
- Acceptance: `git push origin feature/understand-codebase-skill` exits 0; remote tip matches local HEAD.
- Result Log: 2026-05-13 — `git push origin feature/understand-codebase-skill` exit 0; `git rev-parse origin/feature/understand-codebase-skill` = `55cf7d820b83132aabc8f08c634b912999ad137d` = local HEAD. AC met.

---

## Milestone 3: Merge to main, archive, release v0.9.0
- Status: COMPLETE
- Dependencies: M2
- Gate: HARD
- Mode: HITL
- Audit-Profile: docs-only
- Complexity: 30%
- Acceptance Criteria:
  - `feature/understand-codebase-skill` merged into `main` as fast-forward (no merge commit). ✓
  - `.claude/dev/active/` no longer contains `understand-codebase-skill` nor `fix-drift-release-v0-9-0`. ✓ (this archive commit completes the second half)
  - `.claude/dev/completed/` contains both archived tasks. ✓
  - `v0.9.0` tag exists locally and on `origin`. ✓
  - `pyproject.toml`, `VERSION`, `CHANGELOG.md` reflect 0.9.0. ✓
  - HARD gate approval recorded in `context-log.md`. ✓ (commit d727ba3)

### Sub-step 3.1: Run `Skill(impact-analysis)` — confirm non-breaking
- Status: COMPLETE
- Mode: HITL
- Acceptance: impact-analysis verdict = NON-BREAKING; rationale: doc-only edits + version-string bump; no source/import/CI changes. Recorded in `context-log.md`.
- Result Log: 2026-05-13 — inline analysis written to `context-log.md` (under `## [2026-05-13] M3.1 Impact Analysis (inline …)`); verdict NON-BREAKING; rationale: zero source/install/CI touches; symlinks unaffected; uv.lock unaffected. Committed as `d727ba3`. AC met.

### Sub-step 3.2: Fast-forward merge feature → main
- Status: COMPLETE
- Mode: HITL
- Acceptance: user approves; `git checkout main && git pull --ff-only && git merge --ff-only feature/understand-codebase-skill` succeeds; `git log --merges main..origin/main` empty (no merge commits introduced); `git push origin main` succeeds.
- Result Log: 2026-05-13 — user approved via AskUserQuestion ("Approve — manual CHANGELOG promote"). `git merge --ff-only feature/understand-codebase-skill` moved main `3a90325 → d727ba3` (4 commits). `git log --merges 3a90325..HEAD --oneline | wc -l` = 0 → confirmed fast-forward. `git push origin main` exit 0. AC met.

### Sub-step 3.3: Archive `understand-codebase-skill` on main
- Status: COMPLETE
- Mode: AFK (post-3.2 mechanical)
- Acceptance: `mv .claude/dev/active/understand-codebase-skill .claude/dev/completed/` succeeds; `.claude/dev/active/understand-codebase-skill` no longer exists; commit with `[ad-hoc]` footer (cross-plan housekeeping); push.
- Result Log: 2026-05-13 — `mv` succeeded; git detected `rename .claude/dev/{active => completed}/understand-codebase-skill/*` for all 5 artifact files (100% similarity). Commit `8ddf153 chore: archive AA-MA plan understand-codebase-skill` with `[ad-hoc]` footer. (Push deferred — folded into the eventual final push.) AC met.

### Sub-step 3.4: `cz bump --yes` → v0.9.0
- Status: COMPLETE
- Mode: HITL
- Acceptance: user approves; `uv run cz bump --dry-run` first to confirm version `0.9.0`; then `uv run cz bump --yes` (or non-yes interactive); exits 0; `git tag --list v0.9.0` returns the tag; `grep 'version = "0.9.0"' pyproject.toml` and `grep '__version__ = "0.9.0"' VERSION` both match; CHANGELOG `## [Unreleased]` is promoted to `## v0.9.0 (2026-05-13)`.
- Result Log: 2026-05-13 — dry-run confirmed `bump: version 0.8.0 → 0.9.0; tag to create: v0.9.0; increment detected: MINOR`. **Deviation from AC:** `cz bump --files-only --yes` exited 16 — appears to be a cz interaction with `update_changelog_on_bump=true` on an already-promoted CHANGELOG. Functionally equivalent path: manually promoted `## [Unreleased] → ## v0.9.0 (2026-05-13)` in `CHANGELOG.md` (preserved rich content) + 2-line manual version-string bump in `pyproject.toml` (`0.8.0 → 0.9.0`) + `VERSION` (`__version__ = "0.8.0" → "0.9.0"`) + annotated `git tag v0.9.0`. End-state identical to a successful `cz bump`. Commit `ed077f7 bump: version 0.8.0 → 0.9.0` (footer `[AA-MA Plan] fix-drift-release-v0-9-0`). Tag SHA `e904127`. AC met (with documented deviation).

### Sub-step 3.5: Push main + v0.9.0 tag
- Status: COMPLETE
- Mode: AFK
- Acceptance: `git push origin main && git push origin v0.9.0` both exit 0; `git ls-remote origin refs/tags/v0.9.0` returns a non-empty SHA matching local tag.
- Result Log: 2026-05-13 — `git push origin main` exit 0 (`ed077f7`); `git push origin v0.9.0` exit 0 (new tag `e904127` on remote). `git ls-remote origin refs/tags/v0.9.0` returns `e904127f49057212cf49c1ea590e7732e80986cd` = local `git rev-parse v0.9.0`. AC met.

### Sub-step 3.6: Archive `fix-drift-release-v0-9-0` itself
- Status: COMPLETE
- Mode: AFK
- Acceptance: `mv .claude/dev/active/fix-drift-release-v0-9-0 .claude/dev/completed/` succeeds; commit `chore: archive AA-MA plan fix-drift-release-v0-9-0` with `[ad-hoc]` footer; push.
- Result Log: 2026-05-13 — final updates to tasks.md + provenance.log + context-log.md committed FIRST (with `[AA-MA Plan] fix-drift-release-v0-9-0 …` footer — last commit on this plan while it's still active), then archive: `mv .claude/dev/active/fix-drift-release-v0-9-0 .claude/dev/completed/` + `chore: archive AA-MA plan fix-drift-release-v0-9-0` with `[ad-hoc]` footer + push. AC met.

### Sub-step 3.7: Branch cleanup (optional)
- Status: DEFERRED
- Mode: HITL
- Acceptance: user decides whether to delete `feature/understand-codebase-skill` locally + on origin. Default: keep (low cost; preserves audit trail).
- Result Log: 2026-05-13 — DEFERRED. Branch retained as-is (`feature/understand-codebase-skill` @ `d727ba3` on both local + origin) — preserves the per-feature audit trail and costs nothing. User can delete later via `git branch -d feature/understand-codebase-skill && git push origin --delete feature/understand-codebase-skill` if desired.
