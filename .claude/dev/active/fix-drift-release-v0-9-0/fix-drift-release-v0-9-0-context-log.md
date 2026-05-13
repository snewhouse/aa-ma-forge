# Context Log — Fix Pre-existing Drift & Release v0.9.0

## [2026-05-13] Initial context

**Feature request (verbatim from user `/aa-ma-plan` args):**
> a few things: 1) fix `Pre-existing drift` ; 2) commit and merge to main and  cz bump → v0.9.0 at release; DO NOT MAKE ASSUMPTIONS

**Source of the "Pre-existing drift" backlog:** explicitly enumerated in the predecessor task's `understand-codebase-skill-tasks.md` §3.5 Result Log and `understand-codebase-skill-context-log.md` line 86 / 108 as items deliberately deferred (out of scope at the time):
- `README.md:37` — "templates for all 7 AA-MA file types" (now 8)
- `README.md:307` — "ships five hooks" (now 8)
- `README.md` Skills table — non-exhaustive curated subset (missing `verify-impl`, `grill-with-docs`, `prototype`, `write-a-skill`; needs `understand-codebase` added too)

**Key decisions (made during planning):**

1. **Task slug = `fix-drift-release-v0-9-0`** (kebab-case, no dots — consistent with all existing tasks in `.claude/dev/active/` and `.claude/dev/completed/`).

2. **Branch choice — apply the drift fix on `feature/understand-codebase-skill`, not on a new branch.** The drift was deferred at ship time of that branch's only commit (`7cacff5`); applying the fix on the same branch keeps history linear and gives `cz bump` a clean 1-commit-`feat:` + 1-commit-`docs:` lineage on `main` post-merge. The alternative (cut a new `feature/fix-drift` branch) adds a second merge and a second non-ff-friendly history split — KISS rejected.

3. **Single commit covering both README drift AND the 2 hook-generated bookkeeping lines (option (a) in plan §M2.2).** Rationale: the bookkeeping lines belong to `understand-codebase-skill` (now complete) and would otherwise sit orphaned across a separate `[ad-hoc]` commit; folding them in keeps the changelog clean. Trade-off: less granular audit trail — the M2 commit footer references `fix-drift-release-v0-9-0` not `understand-codebase-skill`. If audit purity wins out, switch to option (b) (one extra commit; the plan documents both forms). User can override at execution time.

4. **`cz bump` over `python-semantic-release` for this release.** Both are configured (`[tool.commitizen]` + `[tool.semantic_release]` in `pyproject.toml`). User explicitly said `cz bump`. Both produce the same `0.9.0` outcome here (single `feat:` commit since `v0.8.0`), but `cz bump` is the manual path designed for sole-dev release; semantic-release is for CI auto-release. Choice matches the user's tooling preference.

5. **Do NOT touch `CHANGELOG.md:479`** (historical v0.6.0 line referencing "7 AA-MA files"). CLAUDE.md doctrine: "Historical docs are frozen." Only `README.md:37` is updated.

6. **No new tests.** Pure doc + version-string bump. `uv run pytest`, `ruff`, `bats` are NOT in the gate. Skipping the test suite is intentional and defensible.

7. **No `Skill(plan-verification)` (Phase 4.5).** Mechanical work, complexity ~20%, additive doc edits + automated cz bump. The 6-angle adversarial verification would burn 5-10 min for negligible signal.

8. **M3 `Audit-Profile: docs-only`.** Created date is `2026-05-13` (post-v0.8.0 cutover of 2026-05-11) → Phase 6.8 `/verify-impl` would fire automatically. `docs-only` profile means only scope-discipline check from `code-reviewer` (cheap).

**Open question (parked, not blocking):**

- Should branch `feature/understand-codebase-skill` be deleted post-merge (M3.7)? Default: keep — preserves the named link between commit `7cacff5` and its feature work. User decides at M3.7.

**Research findings:**

- `git log v0.8.0..HEAD --oneline` → exactly one commit (`7cacff5 feat(skills): …`). Deterministic minor bump from `0.8.0` → `0.9.0` under `cz_conventional_commits`.
- `commitizen` config sets `version_files = ["VERSION:__version__"]` and `version_provider = "pep621"` → both `VERSION` and `pyproject.toml` are bumped atomically by cz.
- `update_changelog_on_bump = true` → CHANGELOG `## [Unreleased]` header is promoted to `## v0.9.0 (2026-05-13)` automatically. Content already present (the M3 reconcile-foundations entry from the `understand-codebase-skill` plan).
- `major_on_zero = false` (in `[tool.semantic_release]`) — irrelevant here (no breaking change), but documented for completeness.

**Remaining questions:**

- None — every workflow step has a deterministic outcome verified by `git ls-files`, `git tag`, or `grep` evidence captured in `reference.md`.

_Engineering Standards Declaration (plan §12): Themes **1, 4, 5, 6** materially apply. Themes 2, 3 only mildly. See plan §12 for per-theme rationale._
