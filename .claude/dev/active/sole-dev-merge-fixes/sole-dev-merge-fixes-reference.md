# sole-dev-merge-fixes Reference

## Immutable Facts and Constants

Test-Command: bats --tap tests/commands/sole-dev-merge tests/hooks
Test-Command-Pass-Regex: ^ok ([0-9]+)

Verified at main `1bc3849` (2026-10-15) unless noted.
- Unchanged between `9546a2e` and `1bc3849`: the sole-dev-merge files, `check_conventions.py`, `.pre-commit-config.yaml`.
- Changed: `claude-code/hooks/lib/aa-ma-parse.sh` gained 52 lines. Every anchor below is re-checked at `1bc3849`.

- **Fence 3:** `tests-verified.sh:79-105` reads the `Test-Command:` lines above from the merge-base copy, then the default-branch copy, then HEAD.
  - The command is shell-free. Bats TAP numbers its tests across files, so the last `ok N` gives the total, and bats exits non-zero on any failure.
  - These lines must already be on main before M2 (the M1 merge carries them).

### Environment
- git 2.53.0; gh 2.46.0; bats 1.13.0; pre-commit 4.5.1 on PATH (`~/miniforge3/envs/bio312_07_25/bin`), 4.6.2 in `.venv`.
- Baseline: `bats tests/commands/sole-dev-merge/` = **75/75** (smoke_e2e 4, a_preflight 6, b_scope 4, c_dispatch 7, d_triage 8, e3_body 9, e_remote 8, f_idempotent 11, g_merge 11, g_poll 7).
- Existing hook tests: `tests/hooks/pre-compact.bats` 13, `aa-ma-parse.bats` 27 (5 on `list_active_tasks`), session-start 15, commit-drift 8, session-end-dirty 8, commit-signature 11.
- `~/.claude/skills/sole-dev-merge` and the linked `~/.claude/hooks/lib/*.sh` resolve into the **main checkout**.
  - `aa-ma-footer.sh` is **not** linked: `scripts/install.sh:373-381` links only `aa-ma-parse.sh`, `aa-ma-log.sh` and others (TODOS `:239`).
- `aa-ma-commit-signature.sh` reads the literal command text and lists plans from `$PWD` (`:99`, `:116-131`).
  - A `-m "…${FOOTER}"` commit is blocked whenever a plan is visible.
  - A session rooted in main can't see a plan that exists only on a branch (probed rc=2).
- GitHub repo settings (probed 2026-10-15): main is not protected (404), rulesets `[]`, `delete_branch_on_merge=false`, `allow_auto_merge=false`.
- `~/.claude/settings.json:9`: `CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR=1`. Each Bash command starts in the project dir; a `cd` does not carry over (Claude Code docs, tools-reference "Bash tool behavior").

### Stage block markers (extracted by `tests/commands/sole-dev-merge/fixtures/extract_stage.sh`)
- SKILL.md: stage-banner `:44-65`; stage-a-preflight `:93-141`; stage-b-scope `:155-230`; stage-b-commit `:241-261`. Exit-status table `:288-304`.
- references/stage-c-review-and-security.md: stage-c-aggregate `:32-206` (`SLUG` default `:35`; `CHANGED_PY` read `:115`; `CHANGED_SH` `:162`).
- references/stage-d-triage.md: stage-d-triage `:22-131` (helper source `:26-27`; `SLUG` default `:29`).
- references/stage-e-remote-and-body.md: e1 `:32-56`, e2 `:60-95`, e0 `:99-117`, e3 `:121-172` (body path `:125`).
- references/stage-f-push.md: stage-f-push `:19-81` (`gh pr edit` `:50`; PR_NUM resolved after the edit `:59`).
- references/stage-g-merge.md: g1 `:37-62`, g2 `:66-140`, g3 `:144-205` (`--delete-branch` `:158`), g4 `:209-236` (`ORIGINAL_BRANCH:-feature` `:214`; `checkout` `:220`; silent `branch -D` `:230`).
- Only `tests/commands/sole-dev-merge/*.bats` extracts the markers. `test_smoke_e2e.bats:95-99` chains a, b-scope, b-commit, c-aggregate, d-triage with `set -a`. CI runs the suite at `.github/workflows/security.yml:184-187`.

### Defects (from the spec, plus the 2026-10-15 re-check)
- E1: G3 hardcodes `--delete-branch` (`stage-g-merge.md:158`). Tests pin it at `test_stage_g_merge.bats:100,109,112,118,152`.
- E3: in a worktree, `git checkout main` exits 128 ("already used by worktree").
- E5: from a worktree, gh's local step fails and the remote branch stays.
  - Seen on PRs #18, #19, #27, #30, #37 and #41 (lesson L-1332 and CCI provenance `:231`, `:275`).
  - TODOS `:79` also lists #25, which was a `gh pr close`.
- E6: gh's rc in that case is **[U]**: every past run was piped through `| tail`.
- E7: detect a worktree with `--path-format=absolute` on both `--git-dir` and `--git-common-dir`. The raw `--git-common-dir` is `../.git` from a subdirectory.
- E10: `pull --ff-only` with `pull.rebase=true` and a dirty tree exits 128 ("cannot pull with rebase").
- E12: `git push origin --delete` on a branch that is already gone exits **1** ("remote ref does not exist").
- E13: `git branch -D` on a branch checked out in a worktree exits 1.
- E15: `gh pr edit` hits a Projects-classic GraphQL error on aa-ma-forge (L-1309).
- E16: `git checkout -- <untracked>` exits 1. The guard swallows it, and B-commit's `git add -A` (`SKILL.md:256`) stages the file.
- New: `git checkout -- <path>` restores from the **index**, so a staged out-of-scope edit survives with rc 0 (probed `M  a.txt`).
- E25–E30: Stage B step 5 (`SKILL.md:199-203`) runs `pre-commit run --files … || true`. `check_conventions.py:98-111` (`resolve_range`) exits 2 "no diff source" when nothing is staged and there are no refs.
  - `--from-ref` makes pre-commit stash unstaged changes (`pre_commit/commands/run.py:344`), so `ruff format --check` falsely fails.
  - `PRE_COMMIT_FROM_REF`/`TO_REF` env plus `--files` passes cleanly. This is the fix ADR-0018:84-86 already names.
- New: B-commit and D source `<toplevel>/claude-code/hooks/lib/aa-ma-footer.sh` (`SKILL.md:248-249`, `stage-d-triage.md:26-27`), so they fail rc 1 in any other repo.
- New: `emit_aa_ma_footer` uses `find … | head -1` (`aa-ma-footer.sh:30`), which is arbitrary when 2 plans are active.
- New: values don't carry between Bash calls.
  - Stage B never exports CHANGED_PY/SH, so Stage C silently skips Ruff S and ShellCheck.
  - SLUG differs between C and D.
  - G4's `feature` default can delete an unrelated branch.
- L-1347 root cause:
  - `pre-compact-aa-ma.sh` never reads stdin and lists tasks via `aa_ma_list_active_tasks` → `${PWD}/.claude/dev/active` (`hooks/lib/aa-ma-parse.sh:243`).
  - PRs #37 and #41's sessions had cwd = main checkout for all entries (`cd` per command).
  - Also: a cwd in a subdirectory gives a silent "no active tasks".
- PreCompact stdin fields: `session_id, transcript_path, cwd, prompt_id, hook_event_name, trigger, custom_instructions` (`tests/fixtures/hook-payloads/PreCompact.json`).
  - 12 of the 13 `tests/hooks/pre-compact.bats` tests run the hook with no stdin.
  - `aa_ma_list_active_tasks` is at `aa-ma-parse.sh:242`, `${PWD}` at `:243`; it also scans `$HOME/.claude/dev/active` (`:244`, `:249`).

### Conventions
- Footer: `[AA-MA Plan] sole-dev-merge-fixes .claude/dev/active/sole-dev-merge-fixes`. `aa-ma-commit-signature.sh:99-141` accepts any active plan's footer or `[ad-hoc]`.
- Spec §VI (`docs/spec/aa-ma-specification.md` ~:466-473) says "ACTIVE milestone, alphabetical". It is rewritten in M1.
- Exit contract: `SKILL.md:302-304`. Non-zero is reserved for pre-flight-class aborts. Decided: the B-commit staged-set ABORT is rc 1 (nothing committed, index reset); Stage F read-back mismatch is a STATUS line with rc 0.
- Next free forge lesson: **L-051**. Next free global lesson after 2026-10-15: **L-1352**.
- CHANGELOG: add bullets under `## Unreleased → ### Fixed` (`CHANGELOG.md:7-9`). Never hand-edit VERSION (0.17.0); CCI M14 cuts v0.18.0.
- TODOS: G3/G4 entry `TODOS.md:70-80`; Stage F entry `:81-86`.
- Test files: `tests/hooks/commit-signature.bats` (11), `tests/hooks/install_dry_run.bats`, `tests/hooks/pre-compact.bats` (13).
  - SDM `setup()` sets PR_NUM, PR_URL and REMOTE_CHOICE (`test_stage_g_merge.bats:47-49`), but **no test sets ORIGINAL_BRANCH**.
  - The G3 tests are at `:100-121`, timeout `:123`, failed `:134`, gitlab-green `:188`, gitlab-timeout `:200` and unknown `:213`; the G4 test is at `:149`.
  - `test_smoke_e2e.bats` extracts the blocks at `:95-99` and chains them with `set -a` at `:146-204`.

### Research
- No `docs/research/` file was written. Phase 3 facts came from 4 read-only agents (spec re-verify, recurrence mining, multi-plan mechanics, L-1347 mechanics) and Context7 (gh manual: `-F key=@path` reads the value from the file; Claude Code hooks/tools docs). Findings are summarised in context-log.

Architecture View: see plan.md §13

_Last Updated: 2026-10-15_
