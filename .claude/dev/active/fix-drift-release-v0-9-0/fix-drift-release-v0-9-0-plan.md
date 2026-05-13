# Plan — Fix Pre-existing Drift & Release v0.9.0

**Task slug:** `fix-drift-release-v0-9-0`
**Branch:** `feature/understand-codebase-skill` (cut from `main` @ `3a90325`; +1 commit `7cacff5`)
**Created:** 2026-05-13
**Owner:** AI + Stephen Newhouse

---

## Context

The `feature/understand-codebase-skill` branch is +1 commit ahead of `origin/main` (commit `7cacff5`, the verbatim "vendor understand-codebase + 4 agents + command" feat). That commit shipped with **three intentionally-deferred pre-existing-drift items** in `README.md` (explicitly noted in `understand-codebase-skill-tasks.md` §3.5 Result Log and `understand-codebase-skill-context-log.md` line 86 / 108):

1. `README.md:37` — "templates for all **7** AA-MA file types" (now **8** — verified: 8 task file types live in `docs/templates/`; 5 standard + 3 optional per `CLAUDE.md:58`).
2. `README.md:307` — "AA-MA Forge ships **five** hooks" (now **8** — verified: 8 `.sh` files in `claude-code/hooks/` (excluding `lib/`); listed in `CLAUDE.md:51-54`).
3. `README.md:222-238` — Skills table lists **13** skills (actual = **18** — verified: `ls claude-code/skills/` returns 18 dirs). Missing 5 entries: `understand-codebase`, `grill-with-docs`, `prototype`, `verify-impl`, `write-a-skill`.

Additionally the working tree carries **2 auto-generated AA-MA bookkeeping changes** (the `pre-compact-aa-ma.sh` hook appended a CHECKPOINT to `understand-codebase-skill-context-log.md` + `…-provenance.log` at `2026-05-13T09:26:58Z`).

The `understand-codebase-skill` task itself is **functionally complete** (commit `7cacff5` pushed) but **not archived** — it remains under `.claude/dev/active/`.

This plan ships those three drift fixes, folds in the hook bookkeeping, archives the completed `understand-codebase-skill` task, merges to `main`, and cuts release **v0.9.0** via `cz bump` (which the unreleased `feat(skills):` commit deterministically produces — `major_on_zero = false` + `feat:` → minor bump from `0.8.0`).

---

## 1. Executive summary

Apply three surgical `README.md` edits to clear the pre-existing-drift backlog inherited from the `understand-codebase-skill` ship; commit the fix together with the two auto-generated hook bookkeeping lines; merge `feature/understand-codebase-skill` → `main` via fast-forward; archive the completed `understand-codebase-skill` task on `main`; run `cz bump` to cut **v0.9.0** (auto-promotes `## [Unreleased]` → `## v0.9.0 (2026-05-13)` in `CHANGELOG.md`, updates `pyproject.toml` + `VERSION`, creates the `v0.9.0` tag) and push `main` + tag.

## 2. Stepwise implementation plan

### Milestone 1 — Fix pre-existing README drift — `Gate: SOFT`
- **1.1** *(AFK)* Edit `README.md:37`: `templates for all 7 AA-MA file types` → `templates for all 8 AA-MA file types` (`5 standard + 3 optional`).
- **1.2** *(AFK)* Edit `README.md:307`: `AA-MA Forge ships five hooks.` → `AA-MA Forge ships eight hooks.`. Also lightly rewrite the introductory paragraph if it still implies 5 (verify by re-reading).
- **1.3** *(AFK)* Edit `README.md:222-238` (Skills table): append rows for the 5 missing skills, in install-discovery order (alphabetical): `grill-with-docs`, `prototype`, `understand-codebase`, `verify-impl`, `write-a-skill`. One-line `What it does` per row, sourced from each skill's frontmatter `description:`.
- **1.4** *(AFK)* Verify no other README drift: `grep -nE '\b(five|7|seven)\b.*\b(hook|file type|template)' README.md` → empty.
- **1.5** *(AFK)* Cross-check count consistency: `grep -nE '8 hook|8 AA-MA file|18 skill' README.md CLAUDE.md SECURITY.md docs/spec/claude-code-foundations.md` returns consistent counts.

### Milestone 2 — Commit drift + bookkeeping + push feature — `Gate: SOFT`
- **2.1** *(AFK)* Stage `README.md` (M1 changes) **and** the 2 dirty `understand-codebase-skill-{context-log.md,provenance.log}` files (hook-generated checkpoint).
- **2.2** *(AFK)* Commit with split intent in the body. Two reasonable forms — pick (a) for brevity (preferred):
  - **(a)** Single commit `docs(readme): reconcile pre-existing drift (hooks 5→8, templates 7→8, skills table 13→18)` with `[AA-MA Plan] fix-drift-release-v0-9-0 .claude/dev/active/fix-drift-release-v0-9-0` footer. The hook bookkeeping lines belong to a different (now-complete) plan, but folding them into the same commit avoids a noise commit and the `aa-ma-commit-drift.sh` post-commit hook is happy because `tasks.md`/`provenance.log` in an active task dir got touched.
  - **(b)** Split commits — one for README drift signed to `fix-drift-release-v0-9-0`, one for the hook bookkeeping signed to `understand-codebase-skill` (since the dirty files belong to that task). More auditable; one extra commit.
  - **Default**: (a). If `Skill(impact-analysis)` or user prefers cleaner audit trail, switch to (b).
- **2.3** *(AFK)* `git push origin feature/understand-codebase-skill`. Verify push succeeded.

### Milestone 3 — Merge to main, archive, release v0.9.0 — `Gate: HARD` · `Audit-Profile: docs-only`
- **3.1** *(HITL)* Verify `Skill(impact-analysis)` reports **NON-BREAKING** (doc-only edits + version bump only — no source changes).
- **3.2** *(HITL)* User approves merge → main. Then `git checkout main && git pull --ff-only origin main && git merge --ff-only feature/understand-codebase-skill`. Fast-forward only — if it fails, abort and investigate (no merge commits).
- **3.3** *(AFK)* On `main`, archive the completed task: `mv .claude/dev/active/understand-codebase-skill .claude/dev/completed/`. Verify `.claude/dev/active/` no longer contains `understand-codebase-skill`. Commit: `chore: archive AA-MA plan understand-codebase-skill` with `[ad-hoc]` footer (cross-plan housekeeping).
- **3.4** *(HITL)* User approves release. Then `uv run cz bump --yes` (or `cz bump`). This:
  - Reads commits since `v0.8.0` tag.
  - Computes new version: `0.9.0` (single `feat:` commit → minor bump; `major_on_zero=false` guards against jumping to 1.0).
  - Updates `pyproject.toml` `version = "0.9.0"` + `VERSION` `__version__ = "0.9.0"`.
  - Promotes `## [Unreleased]` → `## v0.9.0 (2026-05-13)` in `CHANGELOG.md`.
  - Creates commit `bump: version 0.8.0 → 0.9.0` and tag `v0.9.0`.
- **3.5** *(AFK)* `git push origin main && git push origin v0.9.0`. Verify the v0.9.0 tag is on remote (`git ls-remote origin refs/tags/v0.9.0`).
- **3.6** *(AFK)* On `main`, archive THIS plan: `mv .claude/dev/active/fix-drift-release-v0-9-0 .claude/dev/completed/`. Commit `chore: archive AA-MA plan fix-drift-release-v0-9-0` with `[ad-hoc]`. Push.
- **3.7** *(AFK)* Switch back to `feature/understand-codebase-skill` (or new feature branch). Rebase or delete the merged feature branch locally + on origin if desired (`git branch -d feature/understand-codebase-skill && git push origin --delete feature/understand-codebase-skill`) — sole-dev workflow defers this to the user.

## 3. Milestones with measurable goals

| M | Goal (measurable) |
|---|---|
| M1 | `grep -nE '\b(five\|7\|seven)\b.*\b(hook\|file type\|template)' README.md` returns empty; `grep -c 'understand-codebase\|verify-impl\|grill-with-docs\|prototype\|write-a-skill' README.md` ≥ 5. |
| M2 | `git status` clean; `git log -1 --format=%B` ends with `[AA-MA Plan] fix-drift-release-v0-9-0 .claude/dev/active/fix-drift-release-v0-9-0`; `git push` succeeds; remote ref matches local `feature/understand-codebase-skill` HEAD. |
| M3 | `git tag --list v0.9.0` non-empty on local + `origin`; `grep '^## v0.9.0' CHANGELOG.md` returns 1; `grep '^version = "0.9.0"' pyproject.toml` returns 1; `grep '__version__ = "0.9.0"' VERSION` returns 1; `.claude/dev/active/` no longer contains `understand-codebase-skill` nor `fix-drift-release-v0-9-0`; `.claude/dev/completed/` contains both. |

## 4. Acceptance criteria per step

(Falsifiable — full per-step ACs in `tasks.md`.)

- **1.1** → `grep -c '8 AA-MA file types' README.md` == 1; `grep -c '7 AA-MA file types' README.md` == 0.
- **1.2** → `grep -c 'ships eight hooks' README.md` == 1; `grep -c 'ships five hooks' README.md` == 0.
- **1.3** → README Skills table contains all 18 entries; `grep -c '^| \`' README.md | head -1` shows ≥ 18 skill rows; the 5 added rows reference correct skill names with non-empty descriptions.
- **2.1** → `git diff --cached --name-only` shows `README.md` + the 2 hook bookkeeping files; nothing else.
- **2.2** → `git log -1 --format=%B | grep -c '\[AA-MA Plan\] fix-drift-release-v0-9-0'` == 1.
- **2.3** → `git rev-parse origin/feature/understand-codebase-skill` == `git rev-parse HEAD`.
- **3.2** → `git rev-parse origin/main` updated; merge was fast-forward (no merge commit: `git log --merges main..origin/main` empty).
- **3.3** → `test -d .claude/dev/completed/understand-codebase-skill && ! test -d .claude/dev/active/understand-codebase-skill`.
- **3.4** → `cz bump --yes` exits 0; `git tag --contains HEAD` includes `v0.9.0`; `git show v0.9.0 --stat` shows `pyproject.toml`, `VERSION`, `CHANGELOG.md` all changed.
- **3.5** → `git ls-remote origin refs/tags/v0.9.0` returns a SHA matching the local tag.
- **3.6** → `test -d .claude/dev/completed/fix-drift-release-v0-9-0 && ! test -d .claude/dev/active/fix-drift-release-v0-9-0`.

## 5. Required artefacts

- **Modified:** `README.md` (3 surgical edits — line 37, 307, Skills table); `pyproject.toml` (cz: `version = "0.9.0"`); `VERSION` (cz: `__version__ = "0.9.0"`); `CHANGELOG.md` (cz: `[Unreleased]` → `v0.9.0 (2026-05-13)`).
- **Moved:** `.claude/dev/active/understand-codebase-skill/` → `.claude/dev/completed/`; `.claude/dev/active/fix-drift-release-v0-9-0/` → `.claude/dev/completed/` (at the end).
- **New (in this plan):** `.claude/dev/active/fix-drift-release-v0-9-0/{plan,reference,tasks,context-log}.md` + `…-provenance.log` (this set).
- **Git refs:** local + remote `main` updated; tag `v0.9.0` on local + remote.

## 6. Tests to validate each milestone

- **M1:** `grep` evidence (above); manual visual diff `git diff README.md` to confirm intent.
- **M2:** `git status` clean; `git log -1 --format=%B` contains expected footer; `git push` exits 0.
- **M3:** `git log --oneline main` shows linear history (`7cacff5` followed by `chore: archive …` + `bump: …`); `git tag -l v0.9.0` non-empty; CHANGELOG opens correctly; remote tag exists.
- Full test suite is **NOT** run (no Python source changes — pure doc + version-string bump). `uv run pytest` is therefore not in the gate. Ruff + bats also out of scope.

## 7. Rollback strategy

Pre-merge (M1-M2): `git reset --hard 7cacff5` on `feature/understand-codebase-skill`, then `git push --force-with-lease origin feature/understand-codebase-skill` (sole-dev — main not yet impacted).

Post-merge to main (M3.2 done): merge is fast-forward, so `git push origin main:main --force-with-lease` to roll back IS possible but lands a destructive force-push on `main` — last-resort only. Easier path: revert via `git revert <merge-commit-sha>` on `main`, push the revert.

Post-tag (M3.4 done): tags are easy to delete (`git tag -d v0.9.0 && git push origin :refs/tags/v0.9.0`) but rolling back a release with people watching is awkward — verify M3.1-M3.3 before triggering M3.4.

## 8. Dependencies & assumptions

- **Assumes** `uv run cz bump` works as configured: `version_provider = "pep621"`, `version_files = ["VERSION:__version__"]`, `update_changelog_on_bump = true`, `tag_format = "v$version"` (all verified at plan time). If `commitizen` is not installed in `.venv`, fall back to `pip install --user commitizen` or manual edit.
- **Assumes** `major_on_zero = false` in `[tool.semantic_release]` is respected by `cz bump` too — actually `cz_conventional_commits` defaults to minor-on-feat regardless, so this is safe.
- **Assumes** the single unreleased commit since `v0.8.0` is `7cacff5 feat(skills): vendor understand-codebase …`. Verified: `git log v0.8.0..HEAD --oneline` returned exactly that.
- **Assumes** no concurrent contributor activity on `origin/main` between the merge and the bump (sole-dev — verified).
- **Assumes** the 2 dirty `understand-codebase-skill-{context-log,provenance.log}` lines are legitimate hook output (verified via `git diff` — both timestamps `2026-05-13T09:26:58Z`, both reference the `pre-compact-aa-ma.sh` hook). They are NOT manual edits.
- **No build dependencies** — doc edits + cz bump. No Python source. No new tests. CI (`security.yml`) runs ShellCheck + Bandit + Ruff on `src/` — none affected.

## 9. Effort estimate & complexity

~30-45 minutes end-to-end (10 min M1 + 5 min M2 + 15-30 min M3 incl. user-approval pauses). **Complexity: ~20%.** No step ≥ 80% (no Chain-of-Thought required).

The fiddliest piece is M1.3 (5 skill-table rows with accurate descriptions) — bounded, mechanical, easily verified.

## 10. Risks & mitigations (top 3 per milestone)

**M1** — (a) miss a drift location → *grep verification at 1.4 + 1.5*. (b) Skill descriptions in M1.3 inaccurate → *source descriptions verbatim from each skill's frontmatter `description:`*. (c) accidentally touch the CHANGELOG line 479 historical reference (`templates for all 7 AA-MA files`) → *CLAUDE.md doctrine: "Historical docs are frozen" — leave it; only fix line 37*.

**M2** — (a) commit-signature hook rejects the commit because the marker isn't formatted exactly → *use the exact format from `rules/aa-ma.md` "Commit Signature" section; pre-flight with `bash -x ~/.claude/hooks/lib/aa-ma-commit-signature.sh` on the message if uncertain*. (b) two active plans confuse the post-commit drift hook → *the hook is advisory only (`always exits 0`); ignore the warning if it fires for the "other" task*. (c) push rejected for non-fast-forward → *unlikely (sole-dev) but `git fetch + git status` before push catches it*.

**M3** — (a) ff-merge fails because `main` advanced → *`git fetch && git status` first; if non-ff, branch is stale → rebase the feature branch on main, retry*. (b) `cz bump` writes unexpected version (e.g., 1.0.0) → *dry-run with `cz bump --dry-run` before the real run; if version != 0.9.0, abort and investigate `commitizen` version + config*. (c) push of tag fails after main pushes → *standard `git push origin v0.9.0` with retry; tag exists locally so no work lost*.

## 11. Next action + AA-MA file to update

**Next action:** begin **M1.1** — edit `README.md:37` (`7` → `8`). Update `fix-drift-release-v0-9-0-tasks.md` Status: PENDING → COMPLETE with concrete `Result Log:` immediately after each sub-step (no batching).

**First file to update after M1.1:** `fix-drift-release-v0-9-0-tasks.md` (1.1 Result Log) + `fix-drift-release-v0-9-0-provenance.log` (commit-less entry: `[ts] M1.1 done — README.md:37 edited (7 → 8)`).

## 12. Engineering Standards Declaration

Per `claude-code/rules/engineering-standards.md` — materially applicable themes: **1, 4, 5, 6**. Themes 2, 3 only mildly (mechanical work — no architecture, minimal design discipline beyond KISS).

- **Theme 1 — Verification & Truth:** every drift claim cited above is grounded in `grep` + `ls` evidence captured in this plan; the cz-bump version (`0.9.0`) is grounded in (a) the verified single `feat:` commit since `v0.8.0` and (b) the verified `major_on_zero = false` + `cz_conventional_commits` minor-on-feat behavior; merge is verified linear via `git log --merges`; tag is verified on remote via `git ls-remote`. No "I think it works" — only "the command returned this output".

- **Theme 4 — Safety & Continuity:** doc-only + version-string bump → **non-breaking by construction**. Per-milestone rollback strategies in §7. Lessons applied: L-005 (don't touch `install.sh` — auto-discovery still correct after our edits); the v0.6.0 CHANGELOG "templates for all 7 AA-MA files" line is **NOT** touched (CLAUDE.md doctrine: historical docs are frozen). Incremental validation: M1 verified via grep before M2; M2 verified via `git status` clean + push success before M3; M3 verified per sub-step.

- **Theme 5 — Execution Checklist:** standard per-task HARD/SOFT enforcement. M3 is `Gate: HARD` — refuses COMPLETE while any `Status: PENDING` remains within the milestone. `Audit-Profile: docs-only` declared on M3 → Phase 6.8 `/verify-impl` (if invoked) runs only scope-discipline check.

- **Theme 6 — Sync & Commit Discipline:** sub-step `Result Log:` written immediately per sub-step (never batched — L-080-082); M3 HARD gate refuses dirty; M2 commit carries the `[AA-MA Plan] fix-drift-release-v0-9-0 …` footer; M3.3/M3.6 archive commits carry the `[ad-hoc]` bypass (cross-plan housekeeping, per `git-conventions.md`).

- *Theme 2 — Development Principles (mild):* KISS — single-commit M2 (option a) over split commits (option b) because the resulting audit trail is cleaner and the dirty hook files are de-facto orphans (their parent plan is complete). DRY — no abstraction needed for ~5 README edits.

- *Theme 3 — Reasoning & Planning (mild):* the one genuine call — "should the hook-bookkeeping lines piggy-back on the drift commit or get a separate `understand-codebase-skill`-signed commit?" — is recorded in M2.2 with the rationale (auditability vs noise). If the user wants stricter separation, switching to option (b) is one extra commit.

---

## Verification (end-to-end, post-execution)

1. `git log --oneline v0.8.0..main` shows 3 commits: `7cacff5 feat(skills): vendor understand-codebase …` + `docs(readme): reconcile pre-existing drift …` + `bump: version 0.8.0 → 0.9.0` (cz-generated). Plus the two `chore: archive …` commits if §3.3/3.6 land between.
2. `git tag --list v0.9.0` non-empty locally; `git ls-remote origin refs/tags/v0.9.0` non-empty on remote.
3. `grep -nE '\b(five|7|seven)\b.*\b(hook|file type|template)' README.md` empty.
4. `grep -nE '^\| `(grill-with-docs|prototype|understand-codebase|verify-impl|write-a-skill)`' README.md` returns 5 lines.
5. `head -10 CHANGELOG.md` shows `## v0.9.0 (2026-05-13)` and no `## [Unreleased]` (or empty `[Unreleased]` if cz keeps the header).
6. `grep -E '^version = "0\.9\.0"' pyproject.toml` returns 1 line; `cat VERSION` shows `__version__ = "0.9.0"`.
7. `ls .claude/dev/active/` empty (or only contains non-`understand-codebase-skill`/`fix-drift-release-v0-9-0` tasks); `.claude/dev/completed/understand-codebase-skill/` + `.claude/dev/completed/fix-drift-release-v0-9-0/` present.
