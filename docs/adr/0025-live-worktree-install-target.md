# 0025. `~/.claude` Links Into a Live Worktree; Milestones Use Plain Branches

**Status:** Accepted
**Date:** 2026-10-25
**Deciders:** Ste
**Tags:** `install`, `workflow`, `git`
**Amends:** code-conventions-impact decision D7 ("worktree per milestone").

## Context and Problem Statement

`scripts/install.sh` links `~/.claude` (skills, agents, rules, hook scripts) into the checkout
it runs from. That was always the main checkout, so a branch checked out there would be live
for every Claude session at once, including the session's own gate and hooks. D7 (2026-10-08)
therefore ran each milestone in its own worktree `.worktrees/<branch>`. That costs a `uv sync`
and a `codemem build` per milestone, plus cleanup, for a sole developer whose milestones run
one at a time (Ste, 2026-10-23). M15.8 already keeps a detached worktree of the forge on main
for the user-scope codemem MCP (`~/.local/share/codemem-plugin` → `codemem-plugin-wt`, R03-D13).
How do we work on plain branches without a half-edited hook going live?

## Decision Drivers

- A branch under edit must never be what `~/.claude` runs (M10–M12 are `hook-modification`).
- One place to refresh after a merge, not two.
- No change for an install without the plugin link.

## Considered Options

1. **A. Keep worktree per milestone** (D7 as written).
2. **B. Plain branches in the main checkout, links unchanged.** A half-edited hook or skill breaks every session until fixed.
3. **C. Link `~/.claude` into the live worktree** (the codemem-plugin worktree), refreshed to main by `install.sh` before it links; plain branches in the main checkout.

## Decision Outcome

**Chosen:** C.

`install.sh` resolves the live worktree with `aa_ma_live_worktree` (`scripts/lib/aa-ma-install-lib.sh`):
the target of `~/.local/share/codemem-plugin` when it is a linked worktree of this forge and
not the checkout itself. It refreshes it to `main` and `uv sync`s it FIRST (§0), then takes every
link, spec copy and the `--wire-git-hook` path from it (`SRC_ROOT`). A dirty live worktree is
linked as it stands, with a warning. With no link, or a link to anything else, install.sh links
into the checkout it runs from, as before. `points_into_repo` counts links into the live worktree
as ours, so re-pointing records nothing in the foreign-link manifest and `uninstall.sh` removes
them. Tests: `tests/hooks/install-live-worktree.bats` (fake `HOME`).

**Step N.0 becomes:** `git pull` on main, then `scripts/install.sh` (from any checkout: the links
land on the refreshed live worktree), then cut the milestone branch in the main checkout.

## Consequences

- `readlink -f` on an installed hook now names the live worktree, so `<forge>/.venv/bin/codemem`
  is its venv (install.sh syncs it). The separate `~/.local/share/codemem-plugin/.venv` step in
  the M10 Contract's codemem lookup is the same binary and is dropped (validator W3).
- Gate semantics are unchanged (validator W6): the §6.7 fence text is the installed skill
  (live worktree = main); the `_cand` launcher and the gate Python come from
  `git rev-parse --show-toplevel`, i.e. the branch under test, as they did inside a D7 worktree.
- A `.git/hooks/post-commit` stanza wired before this ADR names its checkout's copy; install.sh
  now warns about a stanza that names another copy instead of skipping it silently.
- M14's "D7 exception" (release on the main checkout) is unaffected.

## Pros and Cons of the Options

### A. Keep worktrees
- ✅ No change.
- ❌ Per-milestone `uv sync` + `codemem build` + cleanup; two kinds of checkout to reason about.

### B. Plain branches, links unchanged
- ✅ Simplest git.
- ❌ The branch under edit is live everywhere; a broken hook blocks the session that would fix it.

### C. Live worktree (chosen)
- ✅ Plain branches; the live code is always merged main.
- ✅ Reuses the worktree M15.8 already maintains: one refresh, one venv.
- ❌ install.sh must run after each merge for the live code to advance (it already had to).
