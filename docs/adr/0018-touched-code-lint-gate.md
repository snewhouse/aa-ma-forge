# 0018. Touched-code lint gate: pre-commit as the one harness, file-level compliance, no backfill

**Status:** Accepted
**Date:** 2026-10-08
**Deciders:** Stephen Newhouse (sole maintainer)
**Tags:** `lint`, `ci`, `conventions`, `pre-commit`

## Context and Problem Statement

The code-conventions-impact plan adds new rules (Ruff D, `# why:` on suppressions, TODO
references, logging, SecOps) to a repo that does not meet them today. CI ran one lint job,
`uv run ruff check src/`, over `src/` only, so `packages/`, `scripts/` and every shell file
went unlinted, and any new rule would have to be met by the whole repo at once or not at all.
The measured debt is small per file (≤11 strict findings per planned file) but spread wide.

**How do we enforce new conventions on the code we change, without a repo-wide backfill and
without a second tool deciding what "changed" means locally versus in CI?**

## Decision Drivers

- **One definition of "touched"** shared by the local commit and CI, so a commit that passes
  locally does not fail in CI over a different file set.
- **No backfill.** Old debt is paid when a file is next edited, not in a sweep.
- **One tool version.** Ruff comes from `uv.lock`, never a copy on PATH.
- **Fail loud.** A gate that cannot run must not pass (L-012).

## Considered Options

1. **pre-commit with `repo: local` hooks** — staged files locally; `--from-ref/--to-ref` over
   the PR diff in CI.
2. **A hand-written `git diff | xargs ruff` script** in CI only.
3. **Full-repo lint with a baseline file** (ratchet the finding count down).

## Decision Outcome

**Chosen:** Option 1, pre-commit as the one harness.

**Rationale:** pre-commit already passes staged files locally and the PR's changed files in CI
(`pre-commit run --from-ref origin/<base> --to-ref HEAD`), so both sides share one definition
of "touched". `repo: local` hooks run `uv run ruff`, so `uv.lock` pins the version. Rules that
need line granularity (M6's `WHY001`, `TODO001`) run in `scripts/check_conventions.py`, which
reads the same refs from `PRE_COMMIT_FROM_REF`/`PRE_COMMIT_TO_REF` and checks only added lines.

Compliance is **file-level** for the whole-file tools (D8): a touched file passes `ruff check`,
`ruff format --check` and `shellcheck` in full. This adds no churn: the edit-time `ruff-format`
hook already reformats the whole file on every Edit.

## Pros and Cons of the Options

### Option 1 — pre-commit

- ✅ Same file set locally and in CI; one config, `.pre-commit-config.yaml`.
- ✅ Each hook is a uv-locked tool; adding a check is one hook entry.
- ❌ A large file touched later carries its whole debt into that change.

### Option 2 — custom diff script

- ✅ No new dependency.
- ❌ Reimplements file selection pre-commit already has, and covers CI only.

### Option 3 — full repo + baseline

- ✅ Catches debt in untouched files.
- ❌ Baseline files drift and need regeneration; every new rule is a repo-wide change.

## Consequences

**Positive:**
- `packages/`, `scripts/` and shell files are linted when touched; CI previously skipped them.
- New rules (M6–M8) land as one hook or one `CHECKS` entry, enforced from the next touch.

**Negative (accepted gap):**
- **Untouched files are no longer linted in CI.** The removed `ruff` job checked all of `src/`
  on every PR; now a file is checked only when a PR touches it. Full-repo **Ruff S** returns
  as its own CI job in M8.
- `touched` runs on pull requests only, so a push to `main` runs no lint. Every change reaches
  `main` through a PR (`/sole-dev-merge`), where `touched` has already run.
- `pre-commit run --all-files` is a backfill and is not part of any gate. With nothing staged
  and no refs, `check-conventions` exits 2 ("no diff source"): it needs a diff, not a file list.

**Neutral:**
- Touched `.sh` files are shellchecked twice on a PR: by the all-files `shellcheck` job and
  by the hook. The overlap is deliberate; the hook also covers extensionless shell scripts.
- `pre-commit install` (the local git hook) runs from the main checkout after merge (M2.0),
  not inside a worktree.

## Implementation

- `.pre-commit-config.yaml` — hooks `ruff-check`, `ruff-format`, `shellcheck`,
  `check-conventions`, all `repo: local`.
- `scripts/check_conventions.py` — stdlib-only added-lines extractor; exit 0 clean / 1 findings
  / 2 usage or git error (incl. "no diff source"). Ships zero checks.
- `.github/workflows/security.yml` — job `touched` (pull_request only, `fetch-depth: 0`,
  `persist-credentials: false`, uv pinned in the job) replaces job `ruff`.
- Tests: `tests/scripts/test_check_conventions.py`, `tests/test_precommit_config.py`.
