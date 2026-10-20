# sole-dev-merge-simplify: behaviour and test inventory of the v2 skill

- **Created:** 2026-10-20
- **Author:** Explore agent (read-only) for plan sole-dev-merge-simplify; condensed by the lead
- **Reviewed-Through-Date:** 2026-10-20 (main `04d2490`)
- **Valid-Through:** until M2 deletes the stage blocks
- **Sources:** `claude-code/skills/sole-dev-merge/SKILL.md` (S), `references/stage-{c,d,e,f,g}-*.md` (RC, RD, RE, RF, RG), `tests/commands/sole-dev-merge/*.bats`, and the external files named below, all at `04d2490`.

## Decisions this inventory applies (Ste, grill 2026-10-20)
GitHub only. No stage state file. No local Ruff S, ShellCheck, pytest or mypy. Ruff format/fix and pre-commit stay on changed files. `check` stops on out-of-scope dirt, never restores. Reviews C1/C2 and the Stage D stop rule stay as SKILL.md steps.

## KEEP: behaviours sdm.sh must have (with the lesson each encodes)
- **check (A + B + B-commit)**
  - Not-a-repo, detached HEAD, refusing main/master and the remote's default branch, an option-shaped DEFAULT_BRANCH (`check-ref-format`), BASE_REF local-else-origin, nothing ahead: S:105-166, M4 of sole-dev-merge-fixes.
  - A dirty tree aborts at the start (S:129-133).
  - CHANGED_FILES is a triple-dot `git -c core.quotePath=false diff --name-only BASE...HEAD` (S:234-236).
  - `ruff format` and `ruff check --fix` on in-scope `.py` only (L-007).
  - pre-commit on in-scope files, with the range in env (`PRE_COMMIT_FROM_REF`/`TO_REF`), never as flags, and `./`-prefixed names (ADR-0018, L-051).
  - Out-of-scope detection keeps the `-z` porcelain parse, rename sources and `GIT_LITERAL_PATHSPECS=1` (L-053), then **stops and names the files** (CHANGE from restore).
  - Staged-set check before and after staging, with `--no-renames` (L-048).
  - Footer-helper chain (L-054). `chore(scope): pre-PR auto-fixes` commit.
- **ship (E0 + E3 + F + G1 + G2)**
  - origin push URL on github.com, else abort before any push. Replaces E1/E2.
  - `gh auth status`, else `STATUS: AUTH_REQUIRED`.
  - PR body sections, reviewer notes or `(none)`, a `Plan context` line with `tr -d` control characters, the generated-by footer (RE:265-299).
  - `git push -u origin HEAD`.
  - One `gh pr view --json number,url,isCrossRepository,headRefName,state` lookup:
    - an OPEN own PR gets a REST `PATCH … -F body=@file` plus a read-back `cmp`;
    - otherwise `gh pr create --title (subject cut to 70 chars) --body-file`, then re-read by URL;
    - `STATUS: PR_BODY_NOT_UPDATED — reason=not-this-branch|no-pr-number|patch-failed|readback-differs` (RF:102-149, L-1309).
  - G1 rebase-else-merge from `allow_rebase_merge`. **Fix:** an API failure must not count as "true" (RG:96).
  - G2:
    - the appear-wait with validated settings and `timeout 30` per look (RG:161-175, PR #49/#51);
    - `timeout $CI_POLL_TIMEOUT gh pr checks N --watch --interval 30 --fail-fast`;
    - CI_TIMEOUT/CI_FAILED.
    - **Fix:** the recovery hint uses the chosen strategy, not `--rebase` (RG:183).
    - **Add:** after rc 0, require no check in bucket `fail` or `cancel`. `gh pr checks` exits 0 for a cancelled check (see the gh research file).
- **finish (G3 + G4)**
  - Refuse when ORIGINAL_BRANCH is the default branch.
  - One lookup of headRefName, isCrossRepository, state, headRefOid. Abort when the head differs, the PR is cross-repo, the PR is unreadable, or it is not OPEN.
  - MERGED at HEAD means no merge call. MERGED elsewhere aborts (RG:301-326).
  - `gh pr merge N --<strategy> --match-head-commit <sha>`, never `--delete-branch` (L-1332). The rc is not trusted: re-read the state, `MERGE_FAILED`.
  - `git push origin :refs/heads/<b>` (a same-named tag survives), then `git ls-remote --exit-code origin refs/heads/<b>`: rc 2 means gone, else `BRANCH_NOT_DELETED`.
  - G4 detects a worktree via absolute `--git-dir` vs `--git-common-dir`.
    - **Plain checkout:** checkout the default branch, `fetch --prune`, `merge --ff-only`, `branch -D`. **Fix:** a failure prints a STATUS line instead of dying under `set -e` (RG:465-468).
    - **Worktree:** the main worktree (first porcelain entry) is fast-forwarded; `MAIN_NOT_UPDATED` / `MAIN_CHECKOUT_DIRTY`; print the `worktree remove` and `branch -D` cleanup commands (L-052, L-1347).
  - Final lines: `Stage G4: cleanup done`, `Final:`, `STATUS: OK[ worktree=…]`.

## DROP
- The banner; the state file and its 13 loader copies; SLUG and the run dir.
- GitLab and glab: E1/E2 counts, the dual-remote prompt, the glab arms in E0/F/G1/G2/G3, `REMOTE_UNKNOWN`, `CI_BLOCKED`.
- C3/C4 scanners with their severity tables and parse-failure→HIGH; the Stage D bash, S602 auto-fix and CRITICAL tagging.
- mypy and pytest in Stage B.
- Re-validating values the script computes itself: G3/G4 branch and strategy checks, the numeric PR_NUM in G2/G3. A value now crosses only process boundaries the script owns.

## Tests: 199 now; 102 to port (79 KEEP + 23 CHANGE), 97 drop
| File | KEEP | CHANGE | DROP |
|---|---|---|---|
| A preflight | 6 | 2 | 0 |
| B scope | 16 | 8 (restore → stop) | 2 |
| C dispatch | 0 | 0 | 8 |
| D triage | 0 | 0 | 9 |
| E remote | 0 | 3 (origin is github.com) | 6 |
| E3 body | 7 | 1 | 1 |
| F idempotent | 13 | 5 | 9 |
| G poll | 8 | 0 | 5 |
| G merge | 27 | 2 | 14 |
| smoke | 0 | 1 (check end-to-end) | 3 |
| state | 2 | 1 | 40 |

### Per-test map
Format: `file:line` → target file in `tests/commands/sdm/`. Everything not listed is DROP.

- **A preflight → check.bats**
  - KEEP: :35 main, :49 master, :62 dirty tree, :95 nothing ahead, :148 trunk default, :159 option-shaped default (drop its state-file line).
  - CHANGE: :78 no remote (new message), :112 happy path (output only).
- **B scope → check.bats**
  - KEEP:
    - :87 in-scope reformat, :211 zero-Python;
    - pre-commit: :240, :249, :259, :270, :279, :287;
    - B-commit: :392, :406, :419, :434, :464, :480, :494, :508.
  - CHANGE, from restore to "stop and name, leave untouched": :130, :180, :315, :327, :337, :348, :360, :373.
- **E remote → ship.bats**
  - CHANGE, becoming "origin is github.com: pass/abort": :52, :139, :164.
- **E3 body → ship.bats**
  - KEEP: :55, :65, :72, :84, :93, :102, :139.
  - CHANGE: :118 (notes path).
- **F idempotent → ship.bats**
  - KEEP: :73, :94, :107, :128, :153, :179, :191, :215, :304, :317 (becomes a grep on sdm.sh), :322, :360, :388.
  - CHANGE: :142, :163, :202, :275, :410 (PR_NUM/PR_URL printed).
- **G poll → ship.bats**
  - KEEP: :59, :69, :83, :96, :105, :114, :134, :142.
- **G merge → ship.bats** (G1)
  - KEEP: :82, :91.
- **G merge → finish.bats** (G3/G4)
  - KEEP:
    - :107, :118, :130, :142, :153, :163, :174, :211, :222, :244, :255, :270;
    - :329, :384, :399, :419, :431, :444, :457, :471;
    - :556, :568, :578, :620, :632.
  - CHANGE: :303, :314 (CI timeout/failed become flow tests).
- **smoke → check.bats**
  - CHANGE: :87 (check end-to-end, no S602).
- **state**
  - KEEP → check.bats: :297 outside a repo, :306 detached HEAD.
  - CHANGE → finish.bats: :390 (no cleanup unless the merge is confirmed).

**Totals:** 79 KEEP + 23 CHANGE = 102.

- Fixtures: keep `fixtures/bin/gh`, `fixtures/bin/pre-commit` and `fixtures/helpers.bash`; drop `fixtures/bin/glab`.
- Drop `extract_stage.sh` only after the hooks suites below stop using it.
- Use `.invalid` hosts for remotes (L-058). Re-create the exit-table sync test (state.bats:517) against sdm.sh.

## External files M2 must touch
- **Break:**
  - `tests/hooks/aa-ma-footer.bats:167-206` (4 tests extract the stage-b-commit / stage-d-triage blocks).
  - `tests/hooks/commit-signature.bats:228-240` (2 tests feed hook rule 8 the block text). Rule 8 has no caller once commits run inside sdm.sh.
  - `.github/workflows/security.yml:184-187` (runs the bats dir; comments at 145-158 and "60+" at 185).
  - `tests/golden/plugin-surface.json:142-146,1050-1060` and `docs/architecture/plugin-surface.md`: regenerate with `scripts/regen-generated.sh`.
  - `tests/codemem/test_plugin_surface.py:94-106`: the skill must stay non-orphan (the hook comment `aa-ma-commit-signature.sh:149` names it).
- **Stale docs:**
  - ADR-0008 (amend or supersede via ADR-0024), `docs/adr/INDEX.md:30`.
  - ADR-0022:27,49,101 (Ruff S "in Stage C"), ADR-0018:82-88.
  - `CONTEXT.md:158-160` ("Stage state file").
  - README.md:226, `docs/spec/claude-code-foundations.md:91`, `docs/spec/aa-ma-quick-reference.md:156-157`.
  - CHANGELOG Unreleased 11-25; `aa-ma-footer.sh:4-5`.
  - Lessons "Fixed in" pointers (L-007, L-048, L-051–L-055, L-060, L-061).
  - TODOS entries at 25, 81, 88, 96, 104, 119 and 157 go moot; 182, 186, 196, 200, 123 and 354 still apply.
- **Constraints:**
  - `disable-model-invocation: true` stays (`tests/skills/test_model_invocation_list.py`).
  - SKILL.md ≤ 500 lines (`tests/test_prompt_size.py`).
  - Links resolve (`tests/skills/test_skill_links_resolve.py`).
  - M2's subject must not start with `refactor(skills): split sole-dev-merge `.
  - Only `claude-code/skills/sole-dev-merge/scripts/` gets installed (`scripts/install.sh:316-321`).

## Not pursued
- Rule 8 of the signature hook: keep it as a generic shape, or remove it. Left to M2.
- Whether to keep a findings parser in sdm.sh, or have the model write `reviewer-notes.md` directly.
