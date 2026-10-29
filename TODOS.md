# TODOS

## AA-MA Tooling

### PR #74 (run-evals clean checkout) review notes: 1 MEDIUM (fixed) + 9 LOW, deferred under the stop rule
**What:**
- [MEDIUM, fixed 2026-10-29 on `fix/run-evals-warning-order`: the warning is now on the summary line] The new outside-case WARNING pushed the summary line out of `release.sh`'s `tail -n 2`, which happens exactly when the warning matters. Print it before the summary or on stderr — `scripts/run-evals.sh:104` (consumer `scripts/release.sh:73`).
- [LOW] `RUN_EVALS_REF` reaches `git worktree add` without `--end-of-options`, so a value starting with `-` is read as an option — `scripts/run-evals.sh:47`.
- [LOW] The header and runbook don't say the chosen ref must be trusted: its scaffolds and plugin run as you — `scripts/run-evals.sh:21-26`, `docs/runbooks/release.md:23-25`.
- [LOW] The bad-ref path prints `rc=128`, which is not claude's exit code as the header promises — `scripts/run-evals.sh:51`.
- [LOW] A failed `worktree remove` is silent and leaves a stale `.git/worktrees/` entry; add `git worktree prune` to the trap — `scripts/run-evals.sh:45`.
- [LOW] The outside-case check fails open when `.dir` is missing, and a trailing `/` in `RUN_EVALS_DIR` flags every case — `scripts/run-evals.sh:103-104`.
- [LOW] One test assumes TMPDIR is outside the repo — `tests/scripts/test_run_evals_sandbox.bats:72`.
- [LOW] A relative `CLAUDE_BIN` (or relative extra argument) now resolves against the temp checkout — `scripts/run-evals.sh:65`.
- [LOW] The `HEAD~1` test fails on a shallow clone, and `tests/scripts/` is not run in CI at all — `tests/scripts/test_run_evals_sandbox.bats:82-84`, `.github/workflows/security.yml`.
- [LOW] The "no result" exit block appears 3 times; use one helper — `scripts/run-evals.sh:48-52, 78-81, 85-89`.
**Also:** the first valid eval run against v0.18.0 (2026-10-29: 31 cases, 27 pass) failed `execute-aa-ma-step/next-step` (result), `impact-analysis/private-helper` (skill-fired; it passed 2026-10-26), `plan-verification/missing-criteria` (result) and `secops/shell-true` (skill-fired). Each ran once: re-run them with `--runs 3` before treating any as a regression.
**Why:** sole-dev-merge C1/C2 round 1 on PR #74 (2026-10-29). **Effort:** S · **Priority:** P2 (the MEDIUM and the CI gap); the rest P3

### M13 sdm review (PR #72): 4 LOW — fixed before v0.18.0 (M14.0b)
**What:** SECURITY.md "UNKNOWN, never zero" scope and "Claude Code sessions only"; spec TESTS_VERIFIED `skipped:` form and `inputs: local` prefix; TODOS pointers `impact-verified.sh:84` → `src/aa_ma/impact.py:292`. All fixed on main in M14.0b; kept here as the PR's review record.

### M12 sdm C1 review (PR #71): deferred (1 MEDIUM + 3 LOW)
**What:**
- [MEDIUM] language-conventions shared suppression forms for R/SQL name no rule code and drop the cards' "syntax not verified" caveat — `claude-code/skills/language-conventions/SKILL.md:23` (cards: `references/sql.md:12`, `references/r.md:12`).
- [LOW] Opt-out pointer uses the repo path `docs/spec/aa-ma-specification.md`, unreachable from `~/.claude/rules/` (use `../docs/aa-ma-specification.md`) — `claude-code/rules/engineering-standards.md:125`.
- [LOW] `[task]-map.md` row no longer names `/aa-ma-plan --from-map` (doc loss; ADR-0013 keeps it) — `claude-code/rules/aa-ma.md:18`.
- [LOW] "may only fall" is not enforced: RATCHET can be raised up to 20,249 and stay green — `tests/test_autoload_budget.py:19,34`.

### pyproject.toml:74 TODO-format comment (M12 §6.8 INFO)
**What:** the comment says `TODO(owner/issue): text`; check_conventions TODO001 and coding-standards.md accept only `TODO(#N)` / `TODO(ADR-NNNN)`. One-line comment fix.

### M11 sdm C1/C2 review: deferred (2 MEDIUM + 8 LOW)
**What:**
- C2 [MEDIUM] A04 design: a symlinked `<task>-plan.md` is followed, so the merge-base date is read from the link target — `src/aa_ma/impact.py:297` (refuse symlinked plan/tasks/reference).
- C2 [LOW] A04 design: with no milestone window, the working-copy `Created:` dates the plan — `src/aa_ma/impact.py:292` (`_plan_date`, the `run.base is None` branch) (inert until M14.1 sets `IMPACT_CUTOVER`).
- C2 [LOW] A09 logging: `rel`, `REASON`, `TEST_CMD` not sanitised beside the sanitised heading — `src/aa_ma/impact.py:306`, `tests-verified.sh:104,206`.
- C1 [MEDIUM] the milestone window (merge-base) assumes one milestone per branch; undocumented — `claude-code/hooks/lib/aa-ma-parse.sh:588`.
- C1 [LOW] `_partners` ignores codemem `truncated` / top_n=50 cap (fail-open) — `src/aa_ma/impact.py:539`.
- C1 [LOW] the 500-commit co-change window is not enforced when the cache is already wider — `src/aa_ma/impact.py:518`.
- C1 [LOW] a co-change partner may be a path gone from the tree — `src/aa_ma/impact.py:692`.
- C1 [LOW] `Impact-Explained:` cannot name a path with whitespace — `src/aa_ma/impact.py:100`.
- C1 [LOW] DRY: `_plan_date` repeats toplevel/verify_ref — `src/aa_ma/impact.py:294`.
- C1 [LOW] `--head` retro-checks use today's index and cache; undocumented — `src/aa_ma/impact.py:471`.

**Why:** PR #70 (M11, merged 01acbcea, 2026-10-28) sdm review round 1 on 1202cb58: 0 CRITICAL, 0 HIGH, 2 MEDIUM, 8 LOW; none blocks under the stop rule (L-061), no round 2. **Effort:** S–M · **Priority:** P3

### code-conventions-impact M11 §6.3/§6.6: deferred findings (fence 4)
**What:**
- codemem's `sanitize_symbol_arg` allowlist `[A-Za-z0-9_./-]` (≤256, no `..`) rejects legal paths (spaces, `+`, `@`); a changed file like that makes `aa-ma-impact` exit 3 with no fix but a rename. Skip-and-report such paths (kv `cochange_skipped=`), or widen the allowlist for co_changes paths. 0 such tracked files in the forge.
- Efficiency INFO: aa-ma-impact starts codemem 4 times (status, refresh, refresh-commits, query); `query co_changes` opens one read-only connection per path. ~1.1 s per milestone today; fold into one codemem subcommand if it grows.
- `codemem.gitutil` has no production caller (aa_ma.gitutil now does: aa_ma.impact) — adopt in git_mining/indexer when next touched, or drop the twin.
- From M10 §6.8 (still open): ruff-format reflow of untouched lines in feature commits (process); name sanitize_context_line's 200-char default; `CODEMEM_TIMEOUT_S` 2 s vs 30 s naming; relax `griffe==2.3.2` to `>=2.3.2,<3` after the cooldown; CHANGELOG note on git_mining HEAD names.

**Why:** M11 boundary (2026-10-27): §6.6 0 CRITICAL / 9 WARNING / 18 INFO — Ste fixed the four groups (7b9cc4d1, 58e7cdbc) and left these; §6.3 found the allowlist limit. Closed by M11: derive_critical_paths + aa_ma.gitutil callers (aa_ma.impact), FILE_IMPACT_BUDGET, co_changes --threshold default, one verb tuple for coverage rows, shell↔Python T7 constants test, griffe Context7 lookup, M11 Contract rows. **Effort:** S–M · **Priority:** P3

### code-conventions-impact M10 §6.6 review: deferred W6 + efficiency/reuse INFOs
**What:**
- W6: three test-path predicates disagree — `codemem.mcp_tools._is_test_path` (`tests/`, `test/`, `test_*`), `codemem.draw.cut.is_test_path` (`tests/` only), `aa_ma.analysis.measure._is_test`; a diagram and `file_impact` classify one file differently. One shared predicate (changes draw output → regen + golden).
- Every incremental refresh re-extracts the whole plugin surface (~68 ms, 230 rows) even when no `claude-code/` file changed (`codemem/incremental.py` `_refresh_plugin_edges`); gate on a claude-code/ signature.
- `co_changes` builds `kept_commits` (GROUP BY over commit_files) twice even when `max_commit_files` is None; omit the CTE then.
- Multi-path `query co_changes` opens one connection per path (~50 for a Contract); share one.
- `callees` / `who_calls` resolve result ids with one SELECT each (N+1, pre-M10); one `WHERE id IN (…)`.
- `git_mining._apply_moves_to_cached_rows`: 2 statements per rename re-parse the batch SHA JSON; skip on a full refresh.
- `codemem.gitutil._SAFE_PREFIX` restates `codemem.safety.SAFE_GIT`; no production caller of either gitutil yet — adopt in M11 (`check_conventions._git`, codemem indexer/git_mining, `aa_ma.analysis.stamp.run_git`).
- `sdm.sh:45` and `aa-ma-footer.sh:43` keep their own default-base logic (different semantics); move to `aa_ma_default_base_ref` when those scripts are next touched.

**Why:** M10 §6.6 (2026-10-26), 3 review agents: 0 CRITICAL; Ste fixed W1–W5, W7 + 4 INFOs and deferred these. **Effort:** M · **Priority:** P3

### PR for code-conventions-impact 10.0 (live worktree, ADR-0025) review notes: 5 LOW + 1 LOW (C2), deferred under the stop rule
**What:**
- LOW: a dangling `codemem-plugin` link whose parent dir is gone stops install.sh at `plugin_wt="$(readlink -f …)"` (set -e) with exit 1 and no message (`scripts/install.sh` §0); use `readlink -f … || readlink …` plus a warning.
- LOW: the hook table, `aa_ma_hooks_validate` and the `collect_backup_target` hooks/lib list come from the RUNNING install.sh while sources come from `SRC_ROOT` (main): a branch-added hook logs "source not present (future milestone?)"; document, or re-exec `${SRC_ROOT}/scripts/install.sh` when it differs.
- LOW: the `--wire-git-hook` "runs another copy" warn branch has no bats case (pre-wire to the checkout; assert the warning and an unchanged file).
- LOW: install.sh run from inside the live worktree prints "not a worktree of this forge" (wt == REPO_ROOT); say so with an info line instead.
- LOW: uninstall.sh counts live-worktree links as ours only while the plugin link still targets it; also accept any linked worktree with the forge's common dir.
- LOW (C2): `SOURCE_HOOK` is written into the post-commit stanza in double quotes; a path with `"`, `$` or a backtick would expand on each commit (same as before ADR-0025); write it with `printf %q`.
- LOW (round 2): the hooks/lib sweep removes a branch-only hook's link but its settings.json entry stays (register_hook only adds), so that event errors until the hook reaches main; deregister rows whose source is absent from `SRC_ROOT`.
- LOW (round 2): the dirty / failed-refresh abort tests start from an empty `~/.claude`; install from the checkout first and assert the links are unchanged after the abort.
- LOW (round 2): the branch-only sweep test covers skills and agents only; add a rules/ and hooks/lib case, and one asserting a link outside the forge is kept.
- (round 2 restates the first LOW: the empty-path guard in `aa_ma_live_worktree` is not reached from install.sh while `plugin_wt="$(readlink -f …)"` runs first under set -e.)

**Why:** sdm.sh C1/C2 round 1 on the 10.0 PR (2026-10-25): C1 2 MEDIUM (fixed test-first) + 5 LOW, C2 2 LOW (dirty fallback fixed as fail-closed, Ste); round 2 (fix only) C1 1 MEDIUM (jq preflight order; fixed test-first, Ste: no round 3) + 4 LOW, C2 0 (1 INFO). **Effort:** S · **Priority:** P3

### PR #65 (M16 codemem index location) review notes: 1 MEDIUM + 2 LOW, deferred under the stop rule
**What:**
- MEDIUM: §6.0 probes codemem with the caller's full PATH while the post-commit worker drops relative PATH entries; with no forge venv and only a relative-PATH `codemem`, §6.0 can record `skipped(codemem not installed)` (`claude-code/skills/execute-aa-ma-milestone/scripts/code-intel-refresh.sh:76`). Resolve with `aa_ma_codemem_bin` in both.
- LOW: shell twin vs pathlib disagree for a `CODEMEM_DB` ending in `/.` (`claude-code/hooks/lib/aa-ma-parse.sh:431`); add the case to `tests/codemem/test_safety_parity.py`.
- LOW (PR #63): ruff split a short `.mkdir()` across three lines (`tests/render/test_explorer_fixture.py:173`); join when the file is next touched.

**Why:** sdm.sh C1/C2 on PR #65 (2026-10-23), filed at code-conventions-impact 10.0 (L-037). **Effort:** S · **Priority:** P3

### Hook hot-path and helper tidy-ups (M7 §6.6 review, deferred)

**What:**
- `ruff-format.sh` runs ruff three times per .py edit (check --fix, format, check; ~11 ms each). Take the findings from one `check --fix --output-format concise` run.
- `_aa_ma_log` builds `hook` and `msg` in `$(…)` subshells, one fork per field per line. Use `printf -v` or globals.
- `~/.claude/hooks/cache/ruff-format-no-ruff-<sid>` markers are never removed. Prune old ones, e.g. from session-start.
- The forge-root lookup (`readlink -f` + strip path components) is written out in `aa-ma-log.sh`, `aa-ma-parse.sh` (3×) and `ruff-format.sh`. Make it one helper in `aa-ma-log.sh`.
- Three hooks load `aa-ma-log.sh` three ways and react differently when it is missing: `aa-ma-parse.sh` sources it, `aa-ma-plan-skip-warn.sh` stubs `log_debug`, and `ruff-format.sh` prints a systemMessage. Use one loader with one rule (§6.8 C-W1).
- The 8192-char cap and 256-char overlap are defined in both `aa-ma-log.sh` and `logsetup.py`. Tests pin both, but a change needs 4 edits. Read them from the TSV, or add a parity test (§6.8 F-W1).

**Why:** found by the code-conventions-impact M7 post-milestone review. Ste chose to fix the WARNINGs in M7 and defer these INFO items. None is a defect: each costs a few ms, or is one marker file per session.

**Effort:** S
**Priority:** P3
**Depends on:** —

### Move the commit-time security checks into a git pre-commit hook (upgrade path, ADR-0022 amendment)
**What:** run the Ruff S subset and the secret/path regexes from the repo's pre-commit framework (inside git, on the real index, for every commit form), and shrink `security-static-check.sh` to a nudge.
**Why:** the PreToolUse hook only sees the Bash command text, so env-var commits, aliases, `cd && git commit` and scripts bypass it by design (six review rounds, 2026-10-12/13). **Effort:** M · **Priority:** P2

### security-static-check LOWs (split from the PR #30 Stage C entry, 2026-10-13)
**What:**
- The header doesn't document that unstaged-modified (and now untracked) `.py` are scanned on a plain commit, which can false-block.
- The bypass marker can't override a `-C` refusal.
- Only the first `-C` is entered.
- A text hunk in one diff hides a `Binary files` line in the other.

**Why:** the Stage C1/C2 review of PR #30 (2026-10-13); split out at sole-dev-merge-simplify 1.0 when the sole-dev-merge half went moot. **Effort:** S · **Priority:** P3

### Refuse to append AA-MA records through a symlink (all writers, not just fence 3)
**What:** fence 3 (`execute-aa-ma-milestone/scripts/tests-verified.sh`) now refuses to append when `provenance.log`, or any directory on its path, is a symlink. The other appenders have no such check (each needs a probe):
- the diagram fence (`execute-aa-ma-milestone/SKILL.md:363`);
- `references/post-impl-review.md:34,41`;
- `verify-impl/SKILL.md:105`;
- `hooks/pre-compact-aa-ma.sh:131,147` (provenance and context-log);
- `hooks/aa-ma-commit-drift.sh`.

One shared guard in `hooks/lib/aa-ma-parse.sh` would cover them all.
**Why:** a repo can commit `<task>-provenance.log` as a link to `~/.bashrc`. The appended line carries repo-controlled text (the milestone heading), so the next shell start runs it. Found by the background security review of the fence 3 commit (de3f390, 2026-10-13). **Effort:** S · **Priority:** P1

### Fence 3 (TESTS_VERIFIED) follow-ups from the M9 §6.6 review
**What:**
- Killing the fence (SIGTERM to the gate) leaves the test run going. GNU `timeout` puts itself in its own process group. Fix: background `timeout`, `trap 'kill -TERM -- -$pid' TERM INT`, then `wait`.
- Children a test starts with `setsid` outlive the timeout. Same fix area.
- `reference.md` is read line by line. A `Test-Command:` line inside a multi-line `<!-- -->` or a code fence counts, which gives a confusing "more than one" BLOCKED (it fails closed). Run it through `_aa_ma_strip_html_comments` / `aa_ma.grammar.sanitize` first.
- One default-branch helper (`aa_ma_default_branch` in `hooks/lib/aa-ma-parse.sh`) for fence 3 and sole-dev-merge step 5, which pick the branch differently (remote-tracking vs local).

**Why:** the M9 §6.6 reuse, quality and efficiency reviews (2026-10-13); the verified WARNINGs were fixed in M9 and these remain. **Effort:** S · **Priority:** P3

### Gate scripts: use the installed copy unless the repo is the plugin itself (M9 §6.8)
**What:** the §6.7/§7.1 fences, and now fence 3 and `tests-verified.sh`, source `aa-ma-parse.sh` and run
scripts from `$(git rev-parse --show-toplevel)/claude-code/…` before `~/.claude/…`. In an inherited repo
a committed copy replaces the whole gate. Prefer the installed copy unless the toplevel is the
aa-ma-forge checkout. Also bound the Pass-Regex scan (a backreference regex on large output can hang
`grep`/`=~` after the timeout window).
**Why:** M9 §6.8 security-auditor INFOs (pre-existing lookup order; a hang, not a bypass). M15 §6.6
(2026-10-14): `scripts/code-intel-refresh.sh` already loads the lib from its own forge; move the shared
guards (`blocked`, slug check, provenance symlink refusal, heading read — tests-verified.sh:22-58) into one
sourced helper so the two scripts cannot drift. **Effort:** S · **Priority:** P2

### Hooks resolve the active plan from $PWD
**What:** four hooks list active plans with `aa_ma_list_active_tasks`, which reads `${PWD}/.claude/dev/active`:
- `aa-ma-commit-drift.sh:68` (and its repo root at `:110`);
- `aa-ma-session-end-dirty.sh:59` (and `:77`);
- `aa-ma-session-start.sh:101`;
- `aa-ma-commit-signature.sh:103`.
A session rooted in the main checkout that `cd`s into a worktree for each command, or one whose cwd is a subdirectory, sees the wrong plans or none. pre-compact has the same root cause (global L-1347); sole-dev-merge-fixes M5 adds an optional root argument to the helper and fixes pre-compact only. Apply the same root (stdin `cwd` → toplevel, now `aa_ma_list_active_tasks "$ROOT"`) to these four. pre-compact's version (sole-dev-merge-fixes M5) is the pattern, including its fail-open notices.
**Why:** commit-signature blocked commits from a main-rooted session for a plan that existed only on the branch (probed rc 2, 2026-10-15).
**Effort:** S
**Priority:** P2

### session-start says "AA-MA ACTIVE" for a milestone that is only next PENDING
**What:** when no milestone is ACTIVE, `aa_ma_extract_active_milestone` (`claude-code/hooks/lib/aa-ma-parse.sh`) returns the first PENDING milestone in file order, and `aa-ma-session-start.sh` prints it as `AA-MA ACTIVE: … milestone=[…]`. Print it as "next PENDING", or honour `Dependencies:` when choosing it.
**Why:** Ste, 2026-10-23: the session line names a milestone as active that nobody started (and may not be the next runnable one). DISPLAY reader only; no gate reads it.
**Effort:** S
**Priority:** P3

### Check the AA-MA commit signature at the `commit-msg` stage, not in the command text
**What:**
- `aa-ma-commit-signature.sh` (PreToolUse) reads only the literal command, so it guesses at messages it can't see. Rule 8 (sole-dev-merge-fixes 1.7) now trusts one canonical shape, `FOOTER=$(emit_aa_ma_footer); git commit -m "…${FOOTER}"`.
- Gaps that remain:
  - a helper sourced from an arbitrary file;
  - `-m "$MSG"` and `-F file`, which still pass;
  - combined short flags (`git commit -am "unsigned"` passes as "editor form", rc 0). This was probed 2026-10-15 on the hook at `1d760f1`, so it predates rule 8.
  - `git -C <dir> commit` and `git -c k=v commit` never match the hook's `git commit` pattern (rc 0; §6.8 security review, 2026-10-15).
  - rule 8 trusts the helper's output; it can't tell which `aa-ma-footer.sh` the command sourced.
- Fix: a `commit-msg` hook, installed per repo or via pre-commit's `commit-msg` stage, that reads the real message file and applies the same rule as `aa-ma-footer.sh`. Keep the PreToolUse hook as an early warning.

**Why:** a check that sees the actual message has no shapes to guess, and it ends the literal-text bypasses. **Effort:** M · **Priority:** P2

### pre-compact: deferred §6.8 M5 INFOs
**What:**
- Extract the root resolution (`root_of` + stdin `cwd`) into `aa_ma_project_root` in `aa-ma-parse.sh` before the "Hooks resolve the active plan from $PWD" entry copies it into four hooks.
- Read `git worktree list --porcelain -z` (git ≥ 2.36) with `mapfile -d ''`, so a worktree path holding a newline cannot misparse.
- Pass `-c core.fsmonitor=false` on the hook's git calls, as `aa-ma-session-start.sh` does (git 2.53 runs no fsmonitor for `rev-parse` or `worktree list`; tested at §6.8).
- Compare the `$HOME` exemption against `$(cd "$HOME" && pwd -P)`, since ROOT is a realpath.
- The symlink checks and the appends are check-then-use; an O_NOFOLLOW append helper would close the race (needs a process racing the compaction).
**Why:** sole-dev-merge-fixes M5 §6.8 INFOs (code-reviewer, security-auditor), deferred by Ste 2026-10-18. **Effort:** S · **Priority:** P3

### pre-compact: deferred M5 live-run-3 findings (MEDIUM/LOW, stop rule)
**What:**
- MEDIUM: ROOT is always the git toplevel, so a plan under `<repo>/sub/.claude/dev/active` (session launched in `sub/`) gets no snapshot or CHECKPOINT, and only an INFO log line says so. Use `$base` when `$base/.claude/dev/active` exists, else walk up to the toplevel. No such layout exists in ~/projects or ~/dev today (code-reviewer scan).
- The early "no active AA-MA tasks" exit drops the collected notices; emit them before `exit 0`.
- No `timeout` binary (macOS without coreutils) → the stdin read fails (rc 127) every run; add a notice or use `read -t`.
- The "stdin cwd is not in a git repo" notice also fires when git refuses the repo (safe.directory); word it "git could not resolve a toplevel".
- A TAB/LF in the root path itself splits `aa_ma_list_active_tasks` rows (needs a tar-extracted dir; `git clone` turns them into spaces): skip a `source_dir` holding a control character, or emit NUL-delimited rows.
- `root_of` accepts an ancestor checkout reached through a committed embedded gitdir whose `core.worktree` names the enclosing repo (the user's own project; not an escalation over fsmonitor): compare `--absolute-git-dir` with `$top/.git` or its gitfile target.
- Unicode bidi/line-separator characters (U+202E, U+2028/2029) survive both log writers.
- Comment at the `linked=` assignment reads as its failure case; reword.
**Why:** sole-dev-merge-fixes M5 live run 3, Stage C (code-reviewer 1M/5L, security-auditor 3L); deferred under Ste's stop rule (only CRITICAL/HIGH block). **Effort:** S · **Priority:** P3

### /sole-dev-merge M2 SKILL.md: review-step items (from the stop-rule PR review)
**What:** for sole-dev-merge-simplify 2.2, where the C1/C2 review steps and the stop rule move into SKILL.md:
- A round-2 notes write must not drop round-1 notes: append to the notes file, or keep one per round.
- The round cap and the round-1 HEAD exist only in prose; say in SKILL.md how round 3 is refused (L-1358).
- "File the MEDIUMs in TODOS" has no fallback for a repo without TODOS.md and no commit point.
- Security MEDIUMs reach the PR body word for word.
- Nothing stops `ship` while a HIGH is open.

**Why:** /sole-dev-merge on fix/sdm-stop-rule, round 1, 2026-10-20 (0C/0H); carried at sole-dev-merge-simplify 1.0. **Effort:** S · **Priority:** P3
**Done:** sole-dev-merge-simplify M2 2.2 (2026-10-22) — SKILL.md step 2: notes appended per round under `### Round <n>`; round 3 refused (an open CRITICAL/HIGH after round 2 stops `ship`, re-plan); no TODOS.md → the final report; security notes name the class and `path:line`, no exploit steps, no closing keywords; never `ship` with an accepted CRITICAL/HIGH unfixed.

### security-auditor threat model: severity list and coverage (fix/auditor-threat-model-scope review)
**What:**
- Libraries and infra/CI (Audit-Profile `infra`) fit neither default. When in doubt, or when a file is reachable from user-facing code, use the user-facing model.
- Judge each finding by the model of the code its failure path runs in, not by file.
- Write the model used ("Threat model: contract|user-facing|tooling") in the output.
- In the tooling bucket, drop "(not the end users of any code under review)" and narrow "requests and data from the reviewed code's own users" to network peers and other users' data the tool processes.
- The spec line says "its default" (now two). The Priority wording in the entry above.

**Why:** /sole-dev-merge on fix/auditor-threat-model-scope, round 1, 2026-10-20: 0C/0H, 3 MEDIUM + 6 LOW, so nothing blocked. The PR improves on main, which had a tooling-only default with the same list. **Effort:** S · **Priority:** P3. The P1 severity-list item is done in `fix/auditor-authz-g2-wait` (2026-10-20): unauthorized access is in the CRITICAL/HIGH list.

### `sdm.sh ship`: the CI wait ends at the first registered check
**What:** `ship`'s appear-wait stops once any check registers, so a fast first check going green before a later workflow registers can end `--watch` green on partial CI and print `CI_STATE=green`. Re-homed from the old Stage G2 (sole-dev-merge-simplify M2): still true of `sdm.sh`. Narrowed by PR #57 (a check registered after the watch makes the re-read exit 8 → `CI_STATE=timeout`). The merge is safe either way: `finish` requires every check-run at HEAD completed, ≥ 1 success and none failed. Fix if it matters: re-read the check-run count once after the watch.
**Why:** PR #50 review (2026-10-20), LOW, both reviewers. **Effort:** S · **Priority:** P3

### Stage G2 appear-wait: leading-zero cap and counting (fix/g2-appear-wait-hardening review)
**What:**
- `^[0-9]+$` accepts `08`/`09`, which `[[ -ge ]]` rejects as invalid octal on every pass, so the cap never fires. Fails safe; operator env only. Use `^(0|[1-9][0-9]*)$`.
- LOW:
  - the "about 17 minutes" and "after Ns" figures count only the sleeps (each look can add up to 30 s);
  - the defaults 120/10 are written twice;
  - the real-wait test's `-ge 3` also counts the `--watch` call.

**Why:** /sole-dev-merge on fix/g2-appear-wait-hardening, round 1, 2026-10-20: 0C/0H, 1 MEDIUM + 4 LOW, operator-set env only. Hardening an input outside the threat model keeps turning up the next edge (forge L-060), so leave this until the variables are used for real. **Effort:** S · **Priority:** P3
**Closed:** sole-dev-merge-simplify M2 (2026-10-22) — moot: the old G2 is deleted. `sdm.sh` decodes the caps with `10#` (tests `09`, `010`), names the 120/10 defaults once (PR #57), and the stage-block test is gone.

### sole-dev-merge-simplify plan: review notes for M1 (docs/sole-dev-merge-simplify-plan review)
**What:** fix each in the plan text when its sub-step starts.
- ~~MEDIUM: 1.2's `pre-commit run --files …` AC needs `PRE_COMMIT_FROM_REF=main PRE_COMMIT_TO_REF=HEAD` in env, or check-conventions exits 2 "no diff source" (`scripts/check_conventions.py:108`, ADR-0018) once nothing is staged (tasks.md:57).~~ **Done:** tasks.md 1.2 AC and Result Log carry the env.
- LOW:
  - ~~1.4 names no output path for the C1/C2 reviews; `sdm.sh check` makes no `$SDM_DIR` (tasks.md:82).~~ **Done:** private `mktemp -d` run dir (1.4 Result Log).
  - ~~new test 1 ("a cancelled check is not green") is `ship`'s CI_STATE rule, not `finish.bats`'s, and the `ship` contract does not state it (plan.md:291);~~ **Done:** `ship.bats` "new: 1"; the exit table states it (`sdm.sh` STATUS: CI_FAILED row).
  - ~~2.3's `glab|gitlab` grep counts comments; 1.2's DROP grep skips them (tasks.md:159);~~ **Done:** moot — the skill dir has no `glab|gitlab` at all, comments included (2.3 AC: 0).
  - ~~2.0's `aa-ma-gate` AC uses a bare relative path (tasks.md:116, plan.md:152);~~ **Done:** tasks.md 2.0 AC uses the repo-relative path (plan.md keeps its historical text).
  - the `finish`/`ship` lookup does not pin `baseRefName` to the default branch (plan.md:233).
- Round 2 (the MERGED arm, plan.md:233 / reference.md:49):
  - ~~MEDIUM: the branch delete has no lease, so commits pushed to the remote branch after the merge are deleted with it. Use `--force-with-lease=refs/heads/<b>:$SHA`.~~ **Done:** `sdm.sh` delete uses the lease; `finish.bats` "new 15".
  - ~~LOW: say the MERGED arm skips the strategy re-read and the check-runs gate.~~ **Done:** sole-dev-merge-simplify M2 2.2 (2026-10-22), SKILL.md `BRANCH_NOT_DELETED` row.
  - ~~LOW: "a cleanup failure" re-run works only from the feature branch.~~ **Done:** sole-dev-merge-simplify M2 2.2 (2026-10-22), SKILL.md says "from the feature branch's worktree".

**Why:** /sole-dev-merge on docs/sole-dev-merge-simplify-plan, 2026-10-20. Round 1: 0C, 1 HIGH applied (`finish` accepts MERGED at HEAD), 1 MEDIUM + 5 LOW deferred. Round 2 (fix only): 0C/0H, 1 MEDIUM + 2 LOW deferred under the stop rule. **Effort:** S · **Priority:** P2 (before M1 1.1)

### sdm.sh M1 §6.8 review notes: 14 WARNING + 15 INFO, deferred under the exit contract
**What:** the full list with `sdm.sh:line` is in `.claude/dev/completed/sole-dev-merge-simplify/sole-dev-merge-simplify-impl-review.md`. The ones worth doing first:
- ~~Every failure prints a line: a rejected `git push` in `ship` and a hook-refused auto-fix commit in `check` exit 1 with no `ABORT:` line; the worktree cleanup `fetch`/`rev-parse` after a merge are unguarded.~~ **Done:** PR #57 (`0ca6a5fa`).
- `ship`: ~~`--notes` with a missing path silently becomes `(none)`; a failed `gh pr checks` re-read reports green;~~ **Done:** PR #57 (`0ca6a5fa`). Still open: the PR title is `chore(scope): pre-PR auto-fixes` after an auto-fix commit; ~~a lagging `headRefOid` right after a re-push reads as `not-this-branch`~~ **Done:** `ae90cd2b` (proven live on PR #55, merge run 2).
- ~~Inputs: validate `CI_POLL_TIMEOUT` (0 disables the timeout); cut the URL userinfo at the last `@` (a raw `@` in a password leaks its tail).~~ **Done:** PR #57 (`0ca6a5fa`).
- ~~Constants: name `70`, `timeout 30`, `--interval 30`, `per_page=100` and the `120`/`10` fallbacks once, each with a unit and reason.~~ **Done:** PR #57 (`0ca6a5fa`).
- pre-commit's `./` prefix stops anchored `files:`/`exclude:` patterns matching (ported from the old Stage B).

**Why:** §6.8 of sole-dev-merge-simplify M1, 2026-10-22: 1 CRITICAL fixed (ruff `--force-exclude`), 0 HIGH; plan §3 sends WARNING/INFO here. **Effort:** S · **Priority:** P2 (the failure-line items before M2's SKILL.md relies on ABORT parsing)

### sdm.sh M1 PR review (C1/C2, round 1): 1 MEDIUM + 3 LOW, deferred under the stop rule
**What:**
- ~~MEDIUM: `BASE_REF` prefers the local default branch even when it lags origin (after a web-UI merge, with the branch rebased onto origin/main). `check` then widens scope to upstream files and auto-commits fixes to them; `ship`'s body lists commits already on main. Prefer `origin/<d>` when it exists (`sdm.sh:43`; inherited from the old Stage A).~~ **Done:** PR #57 (`0ca6a5fa`).
- ~~LOW: `ship` reads the merge strategy after the PR create and before `PR_NUM=`, so a failed settings read ABORTs with an open PR and no number; move it after the result lines or drop it (`finish` re-reads) (`sdm.sh:166`).~~ **Done:** PR #57 (`0ca6a5fa`).
- ~~LOW: plain-checkout `finish` cleanup checks out the default branch with no clean-tree check (the worktree path has `MAIN_CHECKOUT_DIRTY`) (`sdm.sh:251`).~~ **Done:** PR #57 (`0ca6a5fa`).
- LOW: `ssh://git@ssh.github.com:443/…` (GitHub's SSH-over-443) ABORTs as not github.com; fails closed (`sdm.sh:58`).
- Re-check of the head-lag fix (`ae90cd2b`, merge run 3):
  - ~~MEDIUM: the state is not re-read after the head wait, so a PR closed during it (head = HEAD) gets its body PATCHed and its CI watched; add `state == OPEN` to the loop and a `not-open` reason (`sdm.sh:165`).~~ **Done:** PR #57 (`0ca6a5fa`).
  - LOW: ~~the re-read `gh pr view` calls have no `timeout 30`;~~ **Done:** PR #57 (`0ca6a5fa`). Still open: the worst case before the CI result is now 2 × `CI_APPEAR_TIMEOUT_S` and help does not say so; the stub's lookup count is 0 when `CLI_LOG` is unset (latent); the "fork or another head branch" test covers only the fork (add `GH_PR_HEAD_REF=other`).

**Why:** the branch's own `sdm.sh` merge of refactor/sdm-script (sole-dev-merge-simplify 1.4), 2026-10-22: C1 0C/0H/1M/3L, C2 0/0/0/0; fix re-check 0C/0H/1M/4L. **Effort:** S · **Priority:** P2 (the BASE_REF and closed-during-wait items)

### sdm.sh fix/sdm-failure-lines PR #57 review (C1/C2, 2 rounds): 0 CRITICAL/HIGH, 1 MEDIUM fixed, 7 LOW deferred under the stop rule
**What:**
- LOW: a re-read rc 8 (pending) skips the cancel/fail row scan, so a cancelled check plus a pending one reads CI_TIMEOUT, not CI_FAILED; status text only, `finish` blocks the merge (`sdm.sh` re-read after the watch; C1+C2 round 2).
- LOW: `footer=$(sdm_footer)` hands a failing footer helper's rc to `set -e`, so `check` exits with no ABORT line (operator-set `AA_MA_FOOTER_HELPER` only).
- LOW: fractional `CI_POLL_TIMEOUT` (`1.5m`, accepted by timeout(1)) is replaced by 900s with a stderr line; say "whole numbers" in help or accept `[0-9]+(\.[0-9]+)?`.
- LOW: the head-wait loop's `state == OPEN` early exit has no test of its own (the `not-open` outcome is tested); keep the oid stale for all calls and assert fewer `pr view` calls than cap/step.
- LOW: DRY: the MAIN_CHECKOUT_DIRTY check-and-emit is in two places (plain and worktree cleanup); one helper.
- LOW (out of scope): a raw `/` in URL userinfo prints the userinfo up to `/` as the host in the ABORT (invalid URL, git cannot use it); and the scp form still cuts at the first `@` (no password field).

**Why:** `sdm.sh`'s own merge of PR #57, 2026-10-22: round 1 C1 0C/0H/1M/6L, C2 0/0/0/2L; the MEDIUM (rc 8 read as CI_FAILED) fixed test-first (`5de1e8ed`→`0ca6a5fa`); round 2 (fix only) C1 1L, C2 1L (the same one). **Effort:** S · **Priority:** P3

### sole-dev-merge-simplify M2 §6.8 notes: 10 WARNING + 16 INFO (wrong instructions fixed; the rest here)
**What:** full list in the plan's archived `impl-review.md` (Milestone 2). Fixed in M2 (Ste): SKILL.md BRANCH_NOT_DELETED/MERGE_FAILED/several-STATUS/pre-commit rc/no-ABORT exit/no secrets/no force-push wording, the hook's stale comments, and a drift test tying SKILL.md's STATUS/reason/quoted lines to `sdm.sh`. Open:
- Rule 8 of `aa-ma-commit-signature.sh` (helper-built footer) has no shipped caller since `/sole-dev-merge` moved into `sdm.sh`, yet still widens the signature bypass: retire it with its tests, or record why it stays.
- `test_says_which_calls_push_and_merge` matches any `ship…push` / `finish…merge` line (shape only).
- A08 (out of scope): inside aa-ma-forge the branch's own `sdm.sh check` runs before review; fine for own branches only.

**Why:** §6.8 of sole-dev-merge-simplify M2, 2026-10-22: 0 CRITICAL; plan §3 sends WARNING/INFO here. **Effort:** S · **Priority:** P3

### /sole-dev-merge M2 PR #58 review (C1/C2, round 1): 1 MEDIUM + 2 LOW, deferred under the stop rule
**What:**
- ~~MEDIUM: SKILL.md step 1 gives no recovery for `ABORT: check: files outside the branch changed`. `check` exits before `git add`, so the tree is left dirty and a re-run hits "Uncommitted changes"; the shortcut (commit everything) brings back the L-007 scope widening. Add: the tree was clean at the start, so `git restore --staged --worktree -- <listed files>`, then step 1 again (the in-scope fixes are re-made).~~ **Done:** fix/sdm-skill-recovery (2026-10-23): SKILL.md step 1 "Out-of-scope ABORT" (restore tracked fixer changes, ask before removing untracked ones, fix the cause or take the file on purpose); prototyped live in a sandbox.
- LOW: `tests/codemem/test_plugin_surface.py:99` keeps `sole-dev-merge` off the orphan list only because hook comments name it; retiring rule 8 (entry above) or re-wording those comments makes the skill an orphan and fails the test unexpectedly. Give the skill a non-comment edge or name it in the expected set.
- ~~LOW: CHANGELOG/ADR-0024 said SKILL.md is 125 lines; it is 130 after the §6.8 fixes.~~ **Done:** chore/sdm-simplify-finalize.

**Why:** `/sole-dev-merge` (the new SKILL.md, first live run) on refactor/sdm-switch-over, 2026-10-22: C1 0C/0H/1M/2L, C2 0/0/0/0; one round. **Effort:** S · **Priority:** P2 (the MEDIUM: the model needs it the first time a fixer touches an out-of-scope file)

### /sole-dev-merge SKILL.md recovery (fix/sdm-skill-recovery review, round 2): 1 MEDIUM + 2 LOW, deferred under the stop rule
**What:**
- MEDIUM: the out-of-scope ABORT recovery restores all-or-nothing (`git restore --staged --worktree -- .`). When the user keeps some changed files (e.g. an edit saved while `check` ran), say to restore only the paths the user agrees to (`git restore --staged --worktree -- <paths>`) (`SKILL.md:53`).
- LOW: step 3 "commit that change on the branch" comes after step 2 has undone it; say to decide before restoring, or that the fixer must re-make it (`SKILL.md:55`).
- LOW: `test_abort_recovery_discards_or_commits_nothing_without_asking` counts "only with the user's yes" ≥ 2 but does not tie it to the commit step (`tests/skills/test_sole_dev_merge_skill.py:169`).

**Why:** `/sole-dev-merge` on fix/sdm-skill-recovery, 2026-10-23: round 1 C1 0C/0H/1M/1L and C2 0C/0H/2M/1L (all fixed in round 2, Ste); round 2 C2 none, C1 0C/0H/1M/2L. Stop rule: no round 3. **Effort:** S · **Priority:** P2 (the MEDIUM)

### `measure.py` docstring: "the report-based rule of /sole-dev-merge Stage C" is history
**What:** `src/aa_ma/analysis/measure.py:4-5` cites "/sole-dev-merge Stage C", which sole-dev-merge-simplify M2 deleted (ADR-0024). Re-word it to "the former … Stage C (ADR-0008)". Any edit puts the file under the touched-file gate (ADR-0018 file-level compliance), which reports the file's existing ruff D-rule errors (`uv run ruff check src/aa_ma/analysis/measure.py`; 20 on 2026-10-22), so do the re-word together with that docstring cleanup.
**Why:** sole-dev-merge-simplify 2.3 (2026-10-22) listed this comment; left out to keep a docs step from becoming a 20-error docstring refactor. **Effort:** S · **Priority:** P3
**Done:** fix/measure-docstrings (2026-10-23). Comment re-worded; the 20 were 18 docstring errors (10 D209 auto-fixed, 8 D205 summaries rewritten) plus PLR0913 on `_tool` and C901 on `_job_codemem`, both pre-existing and suppressed with the D8 pay-down `# why:` (listed in the entry below). `ruff check` on the file: 0.

### `emit_aa_ma_footer`: reuse CCI's milestone merge-base helper
**What:** `aa-ma-footer.sh` computes the branch's merge-base itself (`git merge-base HEAD "$ref"`). code-conventions-impact M11 plans `aa_ma_milestone_base` in `aa-ma-parse.sh` for the same question. Once both are on main, make the footer call that helper so the two cannot disagree.
**Why:** sole-dev-merge-fixes plan 5.3 (DRY). Not on main yet: `grep -rn aa_ma_milestone_base claude-code src` is empty (2026-10-18). **Effort:** S · **Priority:** P3

### /sole-dev-merge: source the repo's own `aa-ma-footer.sh` only inside aa-ma-forge
**What:** `sdm_footer` in `sdm.sh` (was the `footer-resolve` chain; re-homed in sole-dev-merge-simplify M2) tries `<toplevel>/claude-code/hooks/lib/aa-ma-footer.sh` in **any** repo and sources it for the auto-fix commit's footer. Check that the repo is aa-ma-forge (plugin manifest name) before taking the repo copy; otherwise use the installed `~/.claude/hooks/lib` link.
**Why:** §6.8 security review of M1 (INFO, A08). Low risk, because `sdm.sh check` already runs the repo's own pre-commit hooks (repo code) on the branch's files. **Effort:** S · **Priority:** P3

### A reusable `secops-ci` template for other repos
**What:** a drop-in set (security.yml jobs ruff-security / gitleaks / deps, `.gitleaksignore`, `.pip-audit-ignore`, `dependabot.yml`, a pre-commit gitleaks entry) plus a short install note in `Skill(secops)`.
**Why:** M8's CI gates exist only in aa-ma-forge; new, old and inherited repos get none of them (Ste, 2026-10-13). **Effort:** M · **Priority:** P2

### security-static-check: per-file forks cap a commit at 250 .py files
**What:** one `git checkout-index --prefix=<tmp>/` plus a single `ruff check`, mapping paths back, then raise `MAX_PY_FILES`.
**Why:** about 20 ms per file. The 10 s hook timeout is a non-blocking error, so the hook now refuses more than 250 files (5.7 s measured) rather than letting the commit through (PR #30 background review). **Effort:** S · **Priority:** P3

### Review the security pins Dependabot cannot bump (quarterly; next 2027-01-12)
**What:** check for newer releases and bump them by hand:
- gitleaks: `security.yml` tarball URL + sha256, `.pre-commit-config.yaml` rev + `# frozen:` comment, `tests/security/test_gitleaks.py` VERSION/TARBALL_SHA256. `test_precommit_rev_and_ci_tarball_name_the_same_gitleaks_version` keeps them aligned.
- the uv `version:` input of setup-uv in every job.

Dependabot bumps the setup-uv SHA itself.
**Why:** Dependabot watches only the github-actions and uv ecosystems; a curl URL, a pre-commit rev and an action input age silently (M8 §6.8 future-proofing). **Effort:** S · **Priority:** P3

### Migrate codemem to fastmcp 3.x (and aa-ma to watchfiles 1.x) before 2027-01-12
**What:** `fastmcp>=3.2,<4` in `packages/codemem-mcp/pyproject.toml` and `watchfiles>=1.0` in `pyproject.toml` (TUI watcher, `src/aa_ma/tui/watcher.py`). Re-test the TUI and a live MCP stdio round-trip. Then delete the three `.pip-audit-ignore` entries, or re-check diskcache: it has no fix yet.
**Why:** M8.5 ignored PYSEC-2026-2475/2476 (fastmcp <3.2) and PYSEC-2026-2447 (diskcache) because they are unreachable from a stdio-only server. The ignores expire on 2027-01-12, and `test_deps_audit.py` then fails CI. **Effort:** M · **Priority:** P2

### Refactor the 10 functions M8.2 suppressed with `noqa: C901` / `PLR0913`
**What:** split these so the per-site suppressions can go:
- `codemem/incremental.py::_refresh_locked` (17)
- `codemem/parser/ast_grep.py::_build_parse_result` (15)
- `scripts/bench_codemem_vs_aider.py::_parse_munch_gen1` (16)
- `check_codemem_doc_drift.py::check_tier_2_changelog_completeness` (13)
- `render/mermaid_lint.py::_sigil_claims` (13), `::lint_text` (12)
- `mcp_tools::diagram` (12), `ast_grep.py::extract_with_ast_grep` (12)
- `indexer.py::parse_files` (11)
- `cli.py::_cmd_query` (12; touched by M15.2)
- `claude-code/codemem/mcp/server.py::build_server` (22; touched by M15.3)
- `bench_codemem_vs_aider.py::_build_report` (PLR0913, 7 args)
- `src/aa_ma/analysis/measure.py::_tool` (PLR0913, 8 args), `::_job_codemem` (12; both touched by the 2026-10-23 docstring fix)

Find them with `grep -rn "M8.2 D8 pay-down"`.
**Why:** M8.2 had to add security `noqa`s to these files, which made them touched files (D8). Refactoring codemem and render logic inside a security milestone was out of scope (Ste, 2026-10-12). **Effort:** M · **Priority:** P3

### Remove the `AA_MA_PLAN_MARKER_DEBUG` alias

**What:** Delete the alias line in `claude-code/hooks/aa-ma-plan-skip-warn.sh` (and its bats case and the note in `docs/spec/plan-marker-grammar.md`) one release after v0.18.0.

**Why:** M7.3 of code-conventions-impact moved the hook to `HOOK_DEBUG`, the one debug switch for every hook; the old name stays for one release so existing shells keep working, with a deprecation notice.

**Effort:** XS
**Priority:** P3
**Depends on:** the release after v0.18.0

### Remove the codemem `blast_radius` alias

**What:** Delete the `blast_radius` MCP tool alias in `claude-code/codemem/mcp/server.py` (and its `mcp_tools` entry) after v0.18.x, as its docstring says; move its tests in `tests/codemem/` to `callees`. Before deleting, re-point the skills that still name codemem's `blast_radius` (`grep -rn blast_radius claude-code/`), but leave project-index's `blast_radius`, which is a different server's tool.

**Why:** M10.2 of code-conventions-impact renamed the downstream query to `callees` (ADR-0026); the old name returns callees, not callers, which misleads anyone who reads it as "what breaks". It stays one release so existing prompts keep working.

**Effort:** S
**Priority:** P3

### Review fence 4 once `IMPACT_CUTOVER` is live

**What:** M14.1 sets `IMPACT_CUTOVER` (`src/aa_ma/impact.py`) to the v0.18.0 release date. After the first 2–3 plans `Created:` on or after it finish, review `IMPACT_VERIFIED`: `Impact-Explained:` lines per milestone against the 11.1 prototype's measure (5 co-change lines over 15 milestones), any BLOCKED that was noise, and whether `COCHANGE_MIN_SHARED`, `COCHANGE_MIN_RATIO` and `COCHANGE_WINDOW_COMMITS` (`src/aa_ma/impact.py`) still fit. Amend ADR-0027 if a threshold moves. The deferred C2 finding at `src/aa_ma/impact.py:292` (`_plan_date`) (M11 sdm entry above) becomes live at the same time.

**Why:** Until v0.18.0 every plan was grandfathered (sentinel `9999-12-31`), so fence 4 has never gated a real milestone. ADR-0027's driver is "quiet enough not to be bypassed"; that needs live data.

**Effort:** S
**Priority:** P2

### Companion plan seed: `reuse-kit`

**What:** Plan the reusable-code collection decided in code-conventions-impact map Tickets 13 and 14 (`.claude/dev/completed/code-conventions-impact/code-conventions-impact-map.md`; evidence `docs/research/code-conventions-impact-reuse-prior-art.md`). Answers to carry in:
- **Where (T13):** library tier in a **private** repo in the company org (uv package, consumed by git source pinned to a tag; the public forge never depends on it); snippet tier as PEP 723 scripts with a test each, in the kit's `snippets/`; a **public** copier project template in the Carmen org carrying the T10 SecOps baseline (CI, pre-commit, gitleaks, Dependabot). Generic helpers the forge itself uses stay canonical in the forge and are vendored into the kit with a FORKS.json-style pin.
- **Confidentiality gate (T13):** every entry has a provenance header (`origin: generic | biomedical | client-derived`, source, date) that CI checks; client-derived entries also pass a genericization checklist, a client-term denylist grep (denylist outside every repo), gitleaks and `approved-by: Ste YYYY-MM-DD`.
- **Graduation (T14):** snippet → module (`kit._experimental`) at evidenced reuse (about the third occurrence, or 2 repos) with one contract; module → library after 2 minor releases and ≥2 consuming repos; library gets SemVer via commitizen and `griffe check` in CI. Rot: weekly CI opens an issue on a failing test; fix in 30 days or delete.
- **Reuse-first while coding (T14):** before writing a generic helper, Claude consults a forge **router skill** (reads the kit index at runtime from `*_KIT_PATH`, ships no entry names in the public forge, prints a notice when the checkout is missing), then reuses or vendors an entry or records "none fits" in one line; the §6.8 code-reviewer WARNs on a helper written twice. This rule needs the router skill, so it lands with the kit, not before.
- **Outward-facing (HITL):** the plan creates two new GitHub repos (private kit, public template); confirm with Ste at execution time.

**Why:** code-conventions-impact plan decision D1 (plan.md:9, :111) moved reuse to this later plan, with T10's "rollout via template" and the P7 YAGNI items (osv-scanner, npm release-age, eslint-plugin-security) for the template. The answers were decided with Ste on 2026-10-08; recording them keeps the next plan from re-grilling them.

**Effort:** L (its own AA-MA plan)
**Priority:** P2

### Fail the build on a dangling plugin reference

**What:** Generating `docs/architecture/plugin-surface.md` exits non-zero when a reference from `claude-code/` resolves nowhere — on disk or in the declared-external allowlist.

**Why:** Three instances of one class surfaced during the diagram-generation charting: `/codebase-deep-dive` (Ticket 9), `/index` in `REUSE-MAP.md` (Ticket 19), and the `senior-architect` stub. Each is a shipped skill telling a consumer to run something only the author's machine has. Ticket 8's `codemem draw --check` will **not** catch them: it is a regenerate-and-compare, and a dangling reference does not change the generated output.

**Context:** The detector already exists as a by-product — `docs/research/diagram-generation-plugin-surface-extraction.md` classifies 41 `Skill()` targets into 17 on-disk / 20 declared-external / 4 dangling, plus 7 orphans, in one regex pass. This is wiring, not new analysis. Needs the external allowlist the research already calls for (one of its three). Pairs with the three-valued reference contract now in `CLAUDE.md`. Belongs in the plugin-surface milestone of `/aa-ma-plan --from-map diagram-generation`.

**Effort:** S
**Priority:** P2
**Depends on:** the diagram-generation plan's plugin-surface milestone

### Fix the `edges` composite PK that never de-duplicates

**What:** Replace `edges`' NULL-bearing composite `PRIMARY KEY` with two partial unique indexes, and de-duplicate the existing rows.

**Why:** Measured on the live index 2026-09-22: **6516 rows, 3258 distinct — exactly 2x**. `schema.sql:62-69` declares `PRIMARY KEY(src_symbol_id, kind, dst_symbol_id, dst_unresolved)`, but SQLite treats NULLs as DISTINCT in the implicit unique index and does not enforce NOT NULL on PK columns of a rowid table. `dst_symbol_id` and `dst_unresolved` are mutually exclusive by design, so **every row carries a NULL in the key** and the index never matches — `INSERT OR IGNORE` (`resolver.py:159`, `indexer.py:310`, `journal/wal.py:447`) de-duplicates nothing. Every consumer that counts or weights edges is reading inflated numbers today.

**Context:** Found by the Phase 4.5 adversarial verification of the diagram-generation plan (2026-09-22), which was about to copy the same DDL shape into a new `file_edges` table. That table now ships partial unique indexes instead — verified empirically: 3 identical inserts collapse to 1 row on both the resolved and unresolved paths. The diagram-generation plan deliberately does NOT repair `edges`: M2's `render/graph.py` reads `SELECT DISTINCT`, which makes the `@call` tier correct without a data migration over a rebuildable, gitignored index. Fixing it properly needs a v4 migration plus a one-time de-dupe. Copy the working DDL from that plan's M1.

**Effort:** M
**Priority:** P2
**Depends on:** diagram-generation M1 (establishes the partial-unique-index pattern)

### codemem: isolate the rest of its git calls from repo config

**What:** Route codemem's remaining git calls (`analysis/git_mining.py` `git log`, `owners` blame, `symbol_history` `git log -L`, `cli.py` refresh-commits) through `indexer.SAFE_GIT`, or adopt `src/aa_ma/analysis/stamp.py`'s allowlist-and-refuse model. Also: `git_tracked_files` resolves tracked symlinks, so a tracked `x.py -> /etc/...` is read into the index.

**Why:** M15.2's security review showed `git ls-files` and `git status` run a repo's `core.fsmonitor` (measured 2026-10-14). M15.2 pinned the index path only (`ls-files`, `rev-parse`, `cat-file`); `git log`/`blame` can also run config-named commands (diff drivers, textconv). Matters once codemem answers in every repo at user scope (M15.8).

**Effort:** M
**Priority:** P1
**Depends on:** code-conventions-impact M15.2 (`SAFE_GIT`)

### codemem positioning after kill Signal 4 fired (2026-10-14)

**What:** Rewrite `docs/codemem/positioning.md`, the codemem README landscape section and `packages/codemem-mcp/README.md` "Design notes" for the consolidated framing. codemem is AA-MA's internal code-intelligence engine, not a standalone code-intel tool. Name repowise in the landscape section.
**Why:** `docs/codemem/kill-criteria.md` Signal 4, review of 2026-10-14: repowise matches 3 of the 5 git-mining differentiators. Ste applied the rule pre-committed on 2026-05-08.
**Effort:** S
**Priority:** P2

### Re-narrow the graphify skill trigger after every graphify upgrade

**What:** After `graphify install` or an upgrade of the `graphifyy` package, re-apply the M15.9 description in `~/.claude/skills/graphify/SKILL.md` (concept and doc questions; structural questions go to codemem). Check with `grep -c 'any question about a codebase' ~/.claude/skills/graphify/SKILL.md`, which must print 0.
**Why:** graphify ships its own SKILL.md, and an upgrade restores the "any question about a codebase" trigger that `~/.claude/rules/code-intel-routing.md` routes away from.
**Effort:** XS
**Priority:** P3

### codemem freshness follow-ups (M15 §6.6, deferred by Ste 2026-10-14)

**What:**
- Try `db.lock` in-process (non-blocking) before spawning a `codemem refresh` that would only exit 75, which saves a Python start and two refresh.log lines per query while a long rebuild holds the lock.
- Drop `mcp_tools.ensure_built`, which has no production caller since M15.3, and rename the server's `_with_autobuild` (it now refreshes and adds the X2 fields).
- Give `indexer.py` one public git helper next to `SAFE_GIT` (and `GIT_TIMEOUT_S`) for `incremental`, `draw/views.py` and `build_index`, and one sidecar writer for `build_index` and `refresh_index` (today `build_index(write_sidecars=...)` picks between two; §6.8 re-run 1).
- If commit bursts make the post-commit queue costly (about 7.6 s per worker, mostly graphify), let a worker skip when HEAD has moved past its SHA. That changes the 15.4 race AC ("A last → .built_sha == A"); Ste kept that AC on 2026-10-14.

**Why:** These are the M15 §6.6 review findings that were not fixed in the milestone.
**Effort:** S
**Priority:** P3

### codemem freshness: §6.8 deferrals (M15, recorded 2026-10-14)

**What:**
- Tie the "5 s" in `claude-code/codemem/README.md`, `commands/codemem.md` and `SECURITY.md` to `mcp_tools.REFRESH_CAP_S` with a doc-count test, so the number cannot drift from the constant.
- `server.py` `_with_autobuild` returns `query failed: <class>: <message>`; the message can carry repo-controlled text such as paths. Return the class name only and log the rest.
- Add a test for the `_rebuild_and_swap` claim that readers of the new DB never replay the old DB's WAL frames.
- Label every M15 measurement in the docs with date, machine and repo; some are unlabelled.
- ~~**P1 → code-conventions-impact Milestone 16:** move the default index out of the repo; a committed regular `index.db-wal` beside a stamped index replays forged pages (M15 §6.8 re-run 3, reproduced).~~ **Done:** code-conventions-impact M16 (2026-10-23): the default index is `${XDG_CACHE_HOME:-~/.cache}/codemem/<sha256(realpath root)>/`; only a `CODEMEM_DB` inside a repo keeps the limit.
- ~~**P1 → Milestone 16 (M15 pre-merge review, 2026-10-15):** a planted `index.db-journal` is rolled back into a stamped index (reproduced); a relative `CODEMEM_DB`/`CODEMEM_REPO_ROOT` misdirects the capped refresh; the §6.0 gate cold-builds where it documents `skipped(no index)`. All three are M16 acceptance criteria.~~ **Done:** code-conventions-impact M16 (2026-10-23): index outside the repo, every SQLite cleanup includes `-journal`, both env paths made absolute, §6.0 blocks a failed build (`skipped(codemem not installed)` only with no binary).
- Pre-merge review LOWs (P3): a FIFO at `refresh.log` in the index dir (repo-controlled only when `CODEMEM_DB` points into a repo, M16) blocks `_log`'s `O_WRONLY` open and the worker's `>>` (open `O_NONBLOCK`, require `S_ISREG`); a tracked symlink to a file outside the repo fails every build (drop resolved candidates outside `repo_root`, `indexer.py:94`); `_ls_files` on the query path has no `GIT_TIMEOUT_S`; a `TrustStoreError` in the first-query cold build reports `no_index`, not `trust_store`; `ensure_built` has no production caller; `scripts/install.sh:592` `readlink -f` under `set -e` aborts on a missing parent.
- `codemem replay --from-wal` trusts `wal.jsonl`, which a repo can commit when `--wal` or `CODEMEM_DB` points into it (M16): a replayed DB is created (so stamped) by codemem. Stamp the journal too, or refuse a journal codemem did not write here (§6.8 re-run 2 limit).
- Trust records (`$XDG_STATE_HOME/codemem/trust/`) accumulate one 33-byte file per index dir ever built; add a `codemem trust --prune` (drop records whose dir is gone) if the count ever matters.
- `codemem refresh` skips a file whose content hash is unchanged without updating its stored `mtime`, so `aa-ma-lint-views` (`render/graph.py::_stale_paths`) reports a touched-but-unchanged file (e.g. after `git checkout -- f`) as changed since indexing until a full `codemem build`. Pre-existing (M2 refresh, M8 lint); found in the §6.8 fix pass. Update `mtime`/`size` on a hash match.

**Why:** These are M15 §6.8 WARNING/INFO findings that Ste recorded rather than fixed in the milestone.
**Effort:** S
**Priority:** P3

### codemem index dir: owner/mode check on the cache dir (M16 background security review, 2026-10-23)

**What:** codemem creates `$XDG_CACHE_HOME/codemem/` and the per-repo `<sha256>/` dir with the default umask and checks neither's owner or mode. If `XDG_CACHE_HOME` is set to a dir another account can write, that account could plant WAL frames beside the index. Create `codemem/` and the per-repo dir 0700 and apply the trust store's checks (`safety._open_store`: owned by this user, not group/other-writable, opened `O_NOFOLLOW`) before opening the index.
**Why:** Background security review MEDIUM (2026-10-23). Not reachable via repo content: it needs a misconfigured `XDG_CACHE_HOME` or a shared cache dir.
**Effort:** S
**Priority:** P3

### codemem index dir: orphaned cache dirs (M16, 2026-10-23)

**What:** a removed worktree or clone leaves `~/.cache/codemem/<hash>/` behind. A `codemem gc` could prune dirs whose repo realpath no longer exists. The hash cannot be reversed, so each dir would need a recorded root file (written at build) for gc to check.
**Why:** Cache dirs accumulate one per checkout ever indexed (M16 moved the index out of the repo, so deleting a checkout no longer deletes its index).
**Effort:** S
**Priority:** P3

### X4: graphify tree-sitter call edges as codemem's non-Python fallback

**What:** Feed graphify's tree-sitter call edges into codemem for the language families whose calls codemem leaves unresolved (TS/JS, Java, shell, Go/Rust/Ruby), then rerun the per-language parity check for each family.

**Why:** codemem resolves calls fully only for Python: TS/JS/Java calls stay unresolved, and it does not index Kotlin, C#, C/C++ or R at all (`indexer.py` language table). The codemem/graphify review (report 03, decision ledger X4) deferred this. It is now the only path to retiring project-index outright: every family except Python keeps project-index until X4 lands and that family passes parity (report 03 R03-D10).

**Trigger:** a language family fails the parity gate (report 03 P1 #7), or a client repo needs callers/callees in a non-Python language.

**Effort:** L
**Priority:** P2
**Depends on:** code-conventions-impact Milestone 15 (fresh index, `stale` envelope); the Python parity check (report 03 T10)

### Make aa-ma-tui runnable from any project

**What:** Resolve the aa-ma-forge checkout from the install.sh symlink (`readlink -f ~/.claude/skills/<any>/SKILL.md` → repo root) and run `uv run --project <root> aa-ma-tui`, via a thin wrapper or documented alias.

**Why:** The TUI only works from inside the aa-ma-forge checkout; every client repo with an active AA-MA plan cannot use it. The same gap was found and fixed for `/aa-ma-share` (plan-eng-review D2, 2026-09-11).

**Context:** The resolution snippet lands in `claude-code/skills/aa-ma-share/SKILL.md` (was `commands/aa-ma-share.md`) at plan-architecture-views M3.1; reuse it verbatim. Needs one bats test that the wrapper resolves the root from a symlinked command file.

**Effort:** S
**Priority:** P3
**Depends on:** plan-architecture-views M3 (the snippet)

## mattpocock-trio-adoption follow-ups (eng review 2026-09-20)

### install.sh: back up every `hooks/lib/` target it replaces; `lib/aa-ma-footer.sh` is never linked

**What:** `scripts/install.sh` backs up only two `hooks/lib/` targets (`collect_backup_target` for `pre-compact-aa-ma.sh` and `ruff-format.sh`). Every other `hooks/lib/` path it links with `create_symlink` or `register_hook` (including `aa-ma-footer.sh`, added by sole-dev-merge-fixes M1) is replaced with no backup. Collect a backup for each of them, derived from the same calls rather than a second hand-kept list. ~~Separately decide whether `claude-code/hooks/lib/aa-ma-footer.sh` should be installed or removed.~~ **Done:** sole-dev-merge-fixes M1 (2026-10-15) — `install.sh` links it, because `/sole-dev-merge` resolves it there outside this repo.

**Why:** Found by the M4.3 `aa-ma-researcher` live run (`docs/research/mattpocock-trio-adoption-install-backup.md`) and confirmed by hand 2026-09-21. L-016 (b) pattern: `hooks/lib` helpers are per-file, not auto-discovered.

**Effort:** S
**Priority:** P3

### §6.8 M4 deferred INFOs — README skills-table test; `plan_elements=<N>/12` → `/13`

**What:** (a) Extend `tests/commands/test_aa_ma_share_command.py::test_readme_slash_names_are_shipped_skills` (was `test_command_count_sites_match_disk`) to the README skills table (split on the skills heading, regex `^\| \`([a-z0-9-]+)\``) so the row-set is asserted against `claude-code/skills/*/` like the commands table is. (b) `docs/spec/plan-marker-grammar.md:59` and `claude-code/skills/aa-ma-plan/SKILL.md` (was `commands/aa-ma-plan.md:89`) still read `plan_elements=<N>/12`; the planning standard has had 13 elements since v0.12.0 (element #13, Architecture View). Update both and any fixture that carries `/12`.

**Why:** Both surfaced by the M4 future-proofing audit (2026-09-21) as out-of-window / Tier-6 retroactive drift; neither is M4 work.

**Effort:** S
**Priority:** P3

### `/aa-ma-share` refuses `*-map.md` — decide whether charting maps are shareable

**What:** `scripts/aa-ma-share-allow.sh` allowlists `*-plan.md`, `docs/adr/*.md`, `docs/spec/*.md`; a `[task]-map.md` / `.claude/dev/charting/<effort>/<effort>-map.md` is refused. Decide (maps hold decisions, not secrets — closer to a plan than to a context-log) and, if yes, add the glob + a bats case in `tests/commands/aa-ma-share-allow.bats`.

**Why:** M5 risk 3 — recorded as a follow-up rather than silently widening the allowlist during the charting milestone.

**Effort:** S
**Priority:** P3

### Teach fingerprint._phase_1_3 about grilling done in a charting session (`--from-map`)

**What:** Under `/aa-ma-plan --from-map`, Phase 1.3 asks only what the map did not settle — often nothing — so the transcript carries no `grill-with-docs`/`grilling` Skill call and `src/aa_ma/plan_markers/fingerprint.py::_phase_1_3` sees Phase 1.3 as unevidenced. Add a disjunct for the `MAP_IMPORTED` provenance line (or a `--from-map` marker) so grilling evidenced in the map counts; test case in `tests/plan_markers/test_fingerprint.py`; row in `docs/spec/plan-marker-grammar.md`.

**Why:** Same shape as the `_phase_3` entry below; surfaced while wiring `--from-map` (M5.4).

**Effort:** S
**Priority:** P3
**Depends on:** mattpocock-trio-adoption M5

### §6.8 M5 deferred INFOs — install.sh lib loop; mawk-shimmed bats; template-count test

**What:** (a) `scripts/install.sh` now carries three copies of the `if [ -f hooks/lib/X ]; then create_symlink X; fi` block (`aa-ma-parse.sh`, `aa-ma-chart-guard.sh`, plus `aa-ma-plan-marker.sh` from `hooks/`); replace with one `for f in "${REPO_ROOT}"/claude-code/hooks/lib/*.sh` loop so a new helper can never be forgotten (fixes L-005/L-016 at the root; fold into the existing install.sh backup entry above). (b) `tests/hooks/aa-ma-chart-guard.bats` runs under whichever `awk` is on PATH — add one skip-if-absent case that prepends a mawk shim (the `AA_MA_MILESTONE_ERE` comment exists because a mawk-only breakage once went unnoticed). (c) No test asserts the "9 AA-MA file types / 5 standard + 4 optional" sites against `docs/templates/`; extend `tests/commands/test_aa_ma_share_command.py` (pattern: `test_command_count_sites_match_disk`) to count `*-template.*` and check README.md, CLAUDE.md, `docs/templates/README.md`, `claude-code/rules/aa-ma.md`, foundations, quick-ref.

**Why:** Surfaced by the M5 §6.8 audit (code-reviewer, context7-evidence, future-proofing) as out-of-window hardening; none is M5 work.

**Effort:** S
**Priority:** P3

### Teach fingerprint._phase_3 about Skill(aa-ma-research) / aa-ma-researcher

**What:** Add two disjuncts to `src/aa_ma/plan_markers/fingerprint.py::_phase_3` (`Skill` with `skill=^aa-ma-research$`, `Agent` with `subagent_type=^aa-ma-researcher$`), a `_tc(...)` case in `tests/plan_markers/test_fingerprint.py`, and the PHASE_3 row in `docs/spec/plan-marker-grammar.md`.

**Why:** After mattpocock-trio-adoption M4, `/aa-ma-plan` Phase 3 delegates web/Context7 calls to the researcher agent, so the parent transcript has none of the tool calls `_phase_3` looks for. Nothing consumes the correlator yet (`aa-ma-plan-skip-warn.sh` is marker-only, hook :19-21), so this is spec debt, not a live bug.

**Context:** Deferred in eng-review scope decision D1. Start at `fingerprint.py::_phase_3`; mirror the `_phase_1_3` regex style.

**Effort:** S
**Priority:** P3
**Depends on:** mattpocock-trio-adoption M4

### docs/research/README.md with the Valid-Through rule

**What:** A short README in `docs/research/` stating: one file per question, the `Created / Author / Reviewed-Through-Date / Valid-Through / Sources` header, and that a file past its `Valid-Through` is re-verified against primary sources, never trusted.

**Why:** M4 makes `/aa-ma-plan` write a research file per plan; readers need the convention in one place.

**Context:** Deferred in eng-review D1 / TODO-2. Convention already exemplified by `docs/research/skill-ecosystem-audit.md:1-12` and `docs/research/mattpocock-trio-2026-09.md`.

**Effort:** XS
**Priority:** P3
**Depends on:** —

### Let /aa-ma-share publish charting maps

**What:** Extend the allowlist in `scripts/aa-ma-share-allow.sh` (`*-plan.md|docs/adr/*.md|docs/spec/*.md`) with `*-map.md`; add a bats case in `tests/commands/aa-ma-share-allow.bats`; update `README.md` (share section) and `claude-code/skills/aa-ma-share/SKILL.md`.

**Why:** A charting map is the kind of document you would share for a second opinion. Today it is refused.

**Context:** Found by the M5 impact analysis. Decide after the first real map exists — maps carry open questions and fog, so sharing half-formed thinking may not be the right default.

**Effort:** XS
**Priority:** P3
**Depends on:** mattpocock-trio-adoption M5

### Retire the dead global ~/.claude/skills/research

**What:** Remove or rename `~/.claude/skills/research/` (outside this repo). Its body runs `/conduct-research`, which does not exist, and names `perplexity-researcher` agents that are not installed.

**Why:** It advertises "do research" triggers that do nothing; once `aa-ma-research` exists the two names invite confusion.

**Context:** Verified dead 2026-09-20. Check other projects' CLAUDE.md/hooks for references to the name before removing (eng-review OV1).

**Effort:** XS
**Priority:** P3
**Depends on:** —

## diagram-generation follow-ups (carried forward at archive, 2026-09-27)

Each was deferred inside a milestone with Ste's agreement; the source line is in the archived
`diagram-generation-tasks.md` (M<n> carry-forwards).

### Tighten the render/explorer CSP
**What:** `script-src` to the exact mermaid bundle URL (not the whole cdn.jsdelivr.net host); add `base-uri 'none'; form-action 'none'`; regenerate `tests/golden/render_plan_ok.html` (the explorer inherits via `html.csp()`). **Why:** M12 §6.8, deferred by Ste; pre-existing. **Effort:** S · **Priority:** P2

### Record function-local imports in codemem
**What:** persist imports made inside a function (flagged, e.g. `lazy=1`) in `file_edges`, then re-lint every plan's §13. **Why:** today a true `@import` on one reads `PHANTOM_EDGE` and the §6.7 diagram item refuses; ADR-0015 tells authors to label such edges in prose meanwhile. **Effort:** M · **Priority:** P2

### TS/TSX/JS calls inside module-scope arrow functions
**What:** treat `variable_declarator` → `arrow_function | function_expression` as callables so their calls produce edges. **Why:** io.md undercounts JS/TS I/O (disclosed in its prose). Fresh impact analysis needed — they become symbols (component view, dead_code, who_calls change for every TS/JS repo); re-measure the polyglot band after. **Effort:** M · **Priority:** P3

### Plugin sigils checked like `@import`
**What:** if the index gains plugin-surface edges, delete `_PLUGIN_SIGILS` / `_PLUGIN_REASON` in `src/aa_ma/render/mermaid_lint.py` together and evaluate `@skill/@command/@agent/@hook` against the graph. **Why:** they read `UNKNOWN` today. **Effort:** M · **Priority:** P3

### Explorer captions
**What:** JS `_names` / `@start` rule pinned by caption cases in the shared fixture; `&` → `#38;` in both `escape_label` twins if names ever carry entities; escape any `edges.dst_unresolved` callee shown in the explorer (untrusted source text). **Why:** deferred at M12 (Ste). **Effort:** S · **Priority:** P3

### `cut._neighbourhood` early exit
**What:** `if not frontier: break` in the hop loop. **Why:** efficiency only — `diagram()` already bounds `hops` at 10 (M13 §6.8). **Effort:** XS · **Priority:** P3

## codebase-analysis-skills follow-ups (carried forward at M8, 2026-10-01)

Deferred with Ste's agreement. Source lines are in the plan's `context-log.md` (M2/M3/M7
backlogs) and `impl-review.md`.

### Incremental assess re-analysis (v2)
**What:** re-measure and re-judge only what changed since the last Fresh report. Reuse
`changed-since`'s section map idea for assess dimensions; carry unchanged findings forward by ID.
**Why:** a Standard run re-reads the whole repo every time (forge 251 s). **Effort:** L · **Priority:** P2

### `unshare -rn` hardening for `aa-ma-analysis run`
**What:** when `unshare -r -n` works, run approved commands with no network namespace. Fall back
to today's offline env otherwise, and say which in run.log. It also brings loopback down, so
tests binding localhost fail. Make it opt-in.
**Why:** the offline env is best-effort; `make test` can still reach the network
(`docs/research/codebase-analysis-skills-offline-command-run.md` §3). **Effort:** M · **Priority:** P2

### `codemem refresh` is still a placeholder
**What:** `codemem refresh` logs and exits 0 (`packages/codemem-mcp/src/codemem/cli.py`
`_cmd_refresh`). Implement the incremental driver or remove the subcommand. assess runs a full
`build` + `refresh-commits` per run today.
**Why:** a command that succeeds without doing anything misleads callers. **Effort:** M · **Priority:** P3

### Understand density: one `path:line` citation per factual unit
**What:** tighten the onboarding templates so every factual list item, row or sentence carries a
citation `ground` can check.
**Why:** M7 Conditional PASS. The private Python repo trailed on claim density by 0.05–0.08 on
both judges. **Effort:** S · **Priority:** P1

### Collapse measured-secret hits to one finding per file and rule
**What:** emit one `security.secret` finding per (path, rule) with a hit count, not one per hit.
**Why:** 2565 hits on one eval repo; most are fixtures, now MEDIUM. **Effort:** S · **Priority:** P2

### Review other measured-HIGH sources for refuter bypass
**What:** semgrep ERROR, lizard CCN > 25 and fixable vulns are measured HIGH and skip the refuter
(L-034). Each needs a severity that is safe by construction, plus a test pinning it on a shipped
path and a fixture path, before Deep is evaluated.
**Why:** Standard runs produced none in M7, so this is unmeasured. **Effort:** M · **Priority:** P1

### Smaller assess/understand hardening (M2/M3 backlog)
**What:**
- a repo owned by another uid (`safe.directory`) should get a "dubious ownership" message, not "not a git repo"
- ignore planted untracked baseline reports by keeping an index of dirs this tool wrote
- `run` reports a passing command as `timeout` when a detached grandchild holds the pipe
- assign live IDs before refuted twins
- cap `refutation_reason` below `EVIDENCE_MAX` after redaction
- validate `refutation_reason` against `refutation`
- follow git renames instead of reading a rename as fixed + new
**Why:** each fails closed or is a usability gap; none is a leak. **Effort:** M total · **Priority:** P3

## Completed

### run-evals: case discovery walks nested worktrees under the repo
**What:** `scripts/run-evals.sh` (`claude plugin eval . --eval-dir evals`) also ran the cases under `.worktrees/<branch>/evals/` — at 10.9 each `--case '<skill>-*'` run doubled (6 runs for 3 cases) with stale copies from `.worktrees/prototype/codemem-refresh-cap`. Exclude `.worktrees/` (or point the run at a path that cannot contain them) and add a bats case.
**Why:** code-conventions-impact 10.9 (2026-10-26): doubled cost and results mixing branch copies. **It recurred at the v0.18.0 release (M14.2, 2026-10-29):** 46 cases, 28 from `prototype/codemem-refresh-cap` and 18 from `prototype/m11-cochange-threshold`, and 0 from main's `evals/`. The `$5` cap ran out at $5.04, so the release eval summary is invalid. After the fix, re-run main's full `evals/` suite against v0.18.0. **Effort:** S · **Priority:** P1 — **Done 2026-10-29** (`fix/run-evals-nested-worktrees`: run-evals evaluates a clean checkout outside the repo; 4 bats cases)

### sole-dev-merge C3/D and security-static-check LOWs (PR #30 Stage C, 2026-10-13)
**What:**
- C3 runs `ruff check --select S` without `--force-exclude`, so it reports the deliberate `shell=True` fixtures under `extend-exclude` (`tests/fixtures/canary/`, `tests/fixtures/evals/py-secops/`) as CRITICAL. Stage D's S602 auto-fix would then rewrite them and break the canary tests. Add `--force-exclude`, and never let Stage D edit an excluded path.
- C3 is not `--isolated`, so a PR can mute its own findings through per-file-ignores or `noqa`. Flag S ignores the PR adds.
- Stage D reads its findings from predictable `/tmp` paths; use a `mktemp -d` per run.
- `"${FIXED_KEYS[@]}"` aborts under `set -u` on bash < 4.4 when the array is empty.
- security-static-check:
  - The header doesn't document that unstaged-modified (and now untracked) `.py` are scanned on a plain commit, which can false-block.
  - The bypass marker can't override a `-C` refusal.
  - Only the first `-C` is entered.
  - A text hunk in one diff hides a `Binary files` line in the other.

**Why:** the Stage C1/C2 review of PR #30 found 7 LOWs and 2 disputed CRITICALs (Ste: notes + TODOS). **Effort:** S · **Priority:** P3
**Closed:** sole-dev-merge-simplify 1.0 (2026-10-20). The C3/Stage D bullets are moot: sdm.sh drops C3/C4 and the Stage D bash (AD-003, AD-008). The four security-static-check bullets are still open, moved to "security-static-check LOWs" above.

### sole-dev-merge: two inputs still split or defaulted (M2 §6.8 INFO)
**What:**
- ~~`$CHANGED_PY`/`$CHANGED_SH` reach `ruff` and `shellcheck` unquoted, and `$CHANGED_FILES` reaches `pre-commit run --files` the same way.~~ **Done in sole-dev-merge-fixes M3.** ruff and shellcheck get `-- "${arr[@]}"`. pre-commit gets `./`-prefixed names, because its argparse rejects `--` (probed).
- ~~`REMOTE_CHOICE="${REMOTE_CHOICE:-github}"` in E0, F and G1–G3 is a masking default (L-055 rule). G1 with a refused state file would save a strategy read from the wrong host. Fix: `${REMOTE_CHOICE:?}`.~~ **Done in sole-dev-merge-fixes M4.** E0, F and G1–G3 now use `${REMOTE_CHOICE:?…}`, and E2's `n_github`/`n_gitlab` are required too. E2's dual-remote `:-$DUAL_DEFAULT` (the host origin pushes to) stays: it is the prompt's default answer, not a missing input.

**Why:** both predate M2 and are outside its key list; the §6.8 security and code reviews raised them as INFO. **Effort:** S · **Priority:** P3
**Closed:** sole-dev-merge-simplify 1.0 (2026-10-20). Both bullets were already done; the stage blocks they name are deleted in M2.

### sole-dev-merge Stage B: three LOWs from PR #44's Stage D (run 2)
**What:**
- A non-empty env `CHANGED_FILES` overrides the state file. The loader's "a non-empty explicit env wins" rule (`SKILL.md` stage-b-commit `sdm_load`) lets a stale exported value pick B-commit's scope.
- B-commit re-adds an untracked file at a path the branch deleted, because the path is in `CHANGED_FILES` and `git status --porcelain` shows it dirty (`??`). Suggested fix: stage only paths in HEAD or the branch diff, or skip `??` rows.
- Names containing `"`, `\` or control characters are still C-quoted where `--name-only` runs without `-z`. Raw names are echoed unescaped in the guard and B-commit lines (terminal spoofing). Fix: `-z` + `mapfile -d ''` end to end, and `printf '%q'` when echoing.

**Why:** Stage D LOW reviewer notes on PR #44 (sole-dev-merge-fixes M3). Ste chose 2026-10-17 to file these three here. The Y=R guard item and the two doc-only notes went into M4. **Effort:** S · **Priority:** P3
**Closed:** sole-dev-merge-simplify 1.0 (2026-10-20). 1: moot, no state file or env scope. 2: moot, `sdm.sh check` aborts on any dirty tree before it runs. 3 (C-quoted, unescaped names): carried to sole-dev-merge-simplify 1.1 as a `check.bats` test.

### sole-dev-merge GitLab path: probe the real `glab mr view -F json --jq` output; close three gaps
**What:** sole-dev-merge-fixes M4 gave Stage F and G3 a GitLab ownership check: `glab mr view [iid] -F json --jq '"\(.iid)\t\(.web_url)\t\(.source_project_id == .target_project_id)\t\(.source_branch)\t\(.state)"'`. The flags and fields come from the glab docs and the GitLab MR API (Context7). It was not probed, because glab is not installed on the dev machine. On the first real GitLab run, check that the line has 5 tab-separated fields and that `state` is `opened`. Then record the result here, or fix the format.
- Two more GitLab gaps, from live run 3 (Ste, 2026-10-18: "we use GitHub", so the GitHub path only in M4):
  - Stage F's create path re-reads the new MR with a no-arg `glab mr view`, which selects by branch, and does not check `opened`. Fix: take the iid from the URL `glab mr create` prints (`${url##*/}`, checked numeric), run `glab mr view "$iid"`, and require `opened`.
  - G3's GitLab branch has no `opened` check before `glab mr merge`, the counterpart of GitHub's new `OPEN` check. A failed `glab mr merge` ends G3 through `set -e` with no `STATUS:` line and no `MERGE_DISPATCHED=0`. Fix: read the MR state after the merge, as GitHub does, then `STATUS: MERGE_FAILED`.

**Why:** a format surprise fails closed (treated as not this branch's), but it would stop every GitLab merge. aa-ma-forge itself is GitHub-only, so none of this runs here. **Effort:** S · **Priority:** P2
**Closed:** sole-dev-merge-simplify 1.0 (2026-10-20). GitLab support is dropped (AD-002); CHANGELOG "Removed" in M2.

### sole-dev-merge: deferred §6.8 INFOs from sole-dev-merge-fixes M4
**What:**
- Stage F's origin-host guard (live run 5 LOWs):
  - It is a deny-list. An origin on neither forge (a mirror or a self-hosted server) next to a github/gitlab remote passes it, so F pushes to origin while gh/glab resolve the PR on the other remote.
  - It substring-matches the whole push URL, so `https://github.com/org/gitlab.com-tools.git` is refused for both choices. E1 and E2 also classify that URL differently.
  - Fix: extract the host (scp `user@host:` or `scheme://[user@]host[:port]/`), compare it exactly in one shared pattern, and require a positive match, with a test seam for local bare remotes.
- E2's dual-remote prompt still offers the non-origin host as an equal second option, which Stage F now always refuses. Fix: drop that option, or label it "refused by Stage F: origin is on <host>" (live run 5 LOW).
- G3 does not pin the merge to the reviewed head SHA: a commit pushed after G2 goes green is merged unreviewed, and the lease-less `git push origin :refs/heads/<b>` drops a commit pushed after the merge. Fix: `gh pr merge --match-head-commit "$(git rev-parse HEAD)"` (gh 2.46 supports it), and `--force-with-lease=<b>:<sha>` on the delete (live run 4 C2 LOW).
- `git check-ref-format --branch` expands `@{-N}` (rc 0, prints the previous branch). A tampered `DEFAULT_BRANCH='@{-1}'` passes G3/G4, and G4 would `git checkout '@{-1}'`. Fix: also require `git check-ref-format "refs/heads/$X"` in G3/G4. Stage A can't reach this, because `symbolic-ref` refuses such a ref.
- `PR_BODY_FILE` is not confined to `SDM_DIR`: whatever file the state or env names is published as the PR body (pre-existing; same uid). Fix: require `realpath` of it under `realpath "$SDM_DIR"`.
- G2/G3 check PR_NUM with `^[0-9]+$` and so accept 0, while Stage F uses `^[1-9][0-9]*$`. F never saves 0. Fix: one pattern.
- No static check that every `sdm_save` key is in `SDM_KEYS`. An unlisted key is dropped with an "ignoring unknown key" line.

**Why:** security-auditor and code-reviewer INFOs at M4 §6.8 (impl-review.md "Milestone 4"). Each needs the same uid, or is pre-existing. **Effort:** S · **Priority:** P3
**Closed:** sole-dev-merge-simplify 1.0 (2026-10-20). Host guard: `ship` matches origin's host exactly (1.1 tests). E2 prompt, `@{-N}`, `PR_BODY_FILE`, `SDM_KEYS`: moot (no E2, no state file, mktemp body). `--match-head-commit` and the lease on the delete: in `finish` (contract; lease probed live at 1.0). PR_NUM: one `^[1-9][0-9]*$` pattern (1.1 new test 10).

### sole-dev-merge Stage C: `${CHANGED_PY:-}` / `${CHANGED_SH:-}` masking defaults
**What:** `references/stage-c-review-and-security.md` reads `${CHANGED_PY:-}` / `${CHANGED_SH:-}` in its `N_PY=`/`N_SH=` count lines and its `if [[ -n "${CHANGED_PY:-}" ]]` / `${CHANGED_SH:-}` scanner guards. If Stage C runs in a fresh shell and the state file was refused, the scanners skip silently and C prints `Ruff S 0 file(s), ShellCheck 0 file(s)`, which looks like a clean scan (L-055 rule). Fix: tell "no state" apart from "no files", e.g. require `CHANGED_FILES` to be set (`${CHANGED_FILES?}`) before reading the subsets. Add a fresh-shell no-state case to `test_stage_c_dispatch.bats`.
**Why:** pre-existing; raised by C1 on PR #44 (run 2). Kept out of M4 (Ste, 2026-10-17) because the Stage C reference is outside M4's Contract. **Effort:** S · **Priority:** P2
**Closed:** sole-dev-merge-simplify 1.0 (2026-10-20). Stage C's scanners are dropped (AD-003).

### stop-rule PR (fix/sdm-stop-rule) review: 4 MEDIUM + 7 LOW, deferred under the stop rule
**What:**
- Round 2 runs Ruff S and ShellCheck over the whole branch again, so a HIGH already disputed or deferred in round 1 comes back. Count only findings in the fix diff, or not yet decided, as "open after round 2".
- Round 2 reuses `SDM_DIR`, and Stage D writes `reviewer-notes.md` with `>`, so round-1 notes drop out. Append instead, or keep one file per round.
- The round cap and the round-1 HEAD exist only in prose. `sdm_save` a `REVIEW_ROUND` / `ROUND1_HEAD` and have Stage D refuse a round 3 (the L-1358 "wire it in" point).
- LOW:
  - "file the MEDIUMs in TODOS" has no fallback for repos without TODOS.md and no commit point;
  - the Stage E3 comment still says "LOW";
  - a bare-negation output check in the new test (L-045);
  - the TODO's hardcoded "67 links";
  - security MEDIUMs now reach the PR body word for word;
  - nothing gates Stage F on an open HIGH.

**Why:** /sole-dev-merge run on fix/sdm-stop-rule, round 1, 2026-10-20: 0 CRITICAL / 0 HIGH, so nothing blocked. **Effort:** S · **Priority:** P3 (the threat-model wording, P1, done in `fix/auditor-threat-model-scope` 2026-10-20: a user-facing-code default and a local-tooling default)
**Closed:** sole-dev-merge-simplify 1.0 (2026-10-20). The scanner bullet and the E3-comment/L-045/"67 links" LOWs are moot (code deleted in M2). The notes, round-cap, TODOS-fallback, PR-body and open-HIGH items are still open, moved to "/sole-dev-merge M2 SKILL.md: review-step items" above.

### Stage G2 appear-wait: review notes (fix/auditor-authz-g2-wait)
**What:**
- Validate `CI_APPEAR_TIMEOUT_S` as `^[0-9]+$` and `CI_APPEAR_INTERVAL_S` as `^[1-9][0-9]*$` (else use the defaults), as G2 already does for `PR_NUM` and the GitLab `TIMEOUT_S`. An interval of 0 or a non-number spins forever.
- Wrap the probe in `timeout 30s`, so one stalled gh call cannot hold G2 past its caps.
- Say in the Stage G summary that the real cap is now 120 s + 900 s.
- Add a test that drives a real wait (TIMEOUT=2, INTERVAL=1 → "after 2s").
- Pre-existing: the wait ends at the first registered check, so a fast first check can end `--watch` green before a later workflow registers. Branch protection's required checks are the backstop.

**Why:** /sole-dev-merge on fix/auditor-authz-g2-wait, round 1, 2026-10-20: 0C/0H, 1 MEDIUM + 6 LOW (operator-set env only, so no normal-use path). **Effort:** S · **Priority:** P3
**Done:** `fix/g2-appear-wait-hardening` (2026-10-20): both settings are validated and fall back to the default with a message; each look runs under `timeout 30`; the Stage G summary gives the ~17-minute worst case; a real-wait test was added (`test_stage_g_poll.bats`). The first-check race is its own TODO above.

### install.sh links a clone pinned to main; then work on plain branches
**What:** the 67 links `install.sh` puts in `~/.claude` point into the main checkout, so switching branches there would make work-in-progress (RED hooks included) live for every session. Point the links at a separate clone that stays on main and is fast-forwarded after each merge (like `codemem-plugin-wt`). Then drop linked worktrees for plan work.
**Why:** Ste asked (2026-10-20) whether worktrees caused problems. Measured: L-1332, L-052 and L-1347 were worktree-only (6 PRs, by-hand G4 merges, all of M5); L-141 is false (worktrees share `origin/HEAD`). Plain branches avoid that class, but not while the live links point at the checkout being switched. **Effort:** S–M · **Priority:** P2
**Dropped (Ste, 2026-10-20):** the worktree failures (L-1332, L-052, L-1347) are fixed and worktrees ran cleanly through PRs #47–#50, so plain branches are now mainly a convenience. A pinned worktree would also repeat the `codemem-plugin-wt` side effect: any linked worktree holding the task stops pre-compact writing a CHECKPOINT in main-rooted sessions. Keep worktrees for plan work.

### /sole-dev-merge Stage D: only CRITICAL/HIGH block and restart a merge run
**What:** in `references/stage-d-triage.md`, route MEDIUM and LOW findings to reviewer notes and TODOS, and ask the operator (AskUserQuestion) only for CRITICAL and HIGH. Only an applied CRITICAL/HIGH fix restarts the run from Stage A. Update the Stage D row in ADR-0008 and the d_triage bats tests.
**Why:** each run sends fresh reviewers at new code, so a gate that stops on MEDIUM never converges: M4 took 5 live runs and M5 3, every one with new MEDIUMs in the previous round's fix (forge L-060). Ste decided the rule 2026-10-18; M5 used it by hand from run 3. **Effort:** S · **Priority:** P1
**Done:** `fix/sdm-stop-rule` (2026-10-20): `stage-d-triage.md` routes MEDIUM with LOW to reviewer notes and asks only for CRITICAL/HIGH. At most 2 review rounds; round 2 reviews only the fix. Reviewers apply `security-auditor.md` § Threat model. Tested in `test_stage_d_triage.bats`.

### pre-compact: also skip a project whose `.claude`, `.claude/dev` or `.claude/dev/active` is a symlink
**What:** sole-dev-merge-fixes 1.8 skips a task whose dir or AA-MA file is a symlink. A cloned repo can still commit `.claude/dev/active` as a symlink to another project's active dir. The hook would then append CHECKPOINT lines to that project's `<task>-provenance.log` and `<task>-context-log.md` and copy its reference.md into the snapshot. Only AA-MA-shaped files are reachable. Skip project tasks when any of the three parents under the project root is `-L`. Don't apply this to `$HOME/.claude`, which is often a legitimate dotfiles symlink. Fold it into M5, which reworks this hook's roots anyway.
**Why:** §6.8 security review of M1 (INFO, 2026-10-15). **Effort:** S · **Priority:** P3
**Done:** sole-dev-merge-fixes M5 (`3d800b9`, 2026-10-18): the hook skips ROOT's tasks when any of the three parents is a symlink, `$HOME` exempt; tested in `tests/hooks/pre-compact.bats`.

### sole-dev-merge Stage F: update an existing PR through REST, not `gh pr edit`
**What:**
- Stage F (`references/stage-f-push.md:50`) updates an existing PR with `gh pr edit --body-file "$PR_BODY_FILE"`. On this repo that call hits a Projects-classic GraphQL error (`repository.pullRequest.projectCards`) and the body is not updated.
- Fix: replace it with `gh api -X PATCH "repos/{owner}/{repo}/pulls/$PR_NUM" -F body=@"$PR_BODY_FILE"`, resolving `PR_NUM` from `gh pr view` first. Read the body back and fail loud if it's unchanged.
- Update `tests/commands/sole-dev-merge/test_stage_f_idempotent.bats:106` (it asserts `gh pr edit` is called).

**Why:** on PR #30 (2026-10-13) the body edit silently didn't land, and a chained `gh pr ready` never ran. Only a read-back caught it (global lesson L-1309). **Effort:** S · **Priority:** P2

**Done:** sole-dev-merge-fixes M4 (2026-10-17). Stage F resolves `PR_NUM`, then runs `gh api -X PATCH repos/{owner}/{repo}/pulls/$PR_NUM -F "body=@$PR_BODY_FILE"` and reads the body back. `cmp <(cat body; echo) <(… --jq .body)`, because `--jq` adds one newline (probed live on PR #45). A failed PATCH or a mismatch prints `STATUS: PR_BODY_NOT_UPDATED — PR #N`, rc 0. `test_stage_f_idempotent.bats:106` now asserts 0 `pr edit` calls.

### sole-dev-merge Stage G3/G4: don't break when run from a worktree
**What:**
- Stage G3 (`references/stage-g-merge.md:158`) always runs `gh pr merge "$PR_NUM" --"$MERGE_STRATEGY" --delete-branch`. When the branch lives in a worktree, gh's local step fails with `fatal: 'main' is already used by worktree at …`, and the remote branch is left behind.
- Stage G4 (`:220`) runs `git checkout -q "$DEFAULT_BRANCH"` under `set -euo pipefail`, which fails the same way.
- Fix: detect a worktree with `[ "$(git rev-parse --path-format=absolute --git-common-dir)" != "$(git rev-parse --path-format=absolute --git-dir)" ]`. Without `--path-format=absolute` the comparison reports a worktree when run from a subdirectory of the main checkout (probed 2026-10-13, git 2.53). In a worktree:
  - G3 merges without `--delete-branch`, then runs `git push origin --delete "$ORIGINAL_BRANCH"` and asserts `git ls-remote --heads origin "$ORIGINAL_BRANCH"` prints nothing.
  - G4 fast-forwards the main checkout (`git -C "$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")" pull --ff-only`) instead of switching branches.
- Update `tests/commands/sole-dev-merge/test_stage_g_merge.bats:100,112` (they pin `--delete-branch`), and add worktree-case tests.

**Why:** this happened on PRs #18, #19, #25, #27 and #30 (global lesson L-1332). The skill's own G3 contradicts the lesson's rule, so the lesson alone can't prevent it. **Effort:** S · **Priority:** P2

**Done:** sole-dev-merge-fixes M1 (2026-10-15) — G3 merges without `--delete-branch`, decides by `gh pr view --json state`, deletes `:refs/heads/<b>` and asserts with `ls-remote`; G4 fast-forwards the main worktree with `git -C` and prints the cleanup commands (`test_stage_g_merge.bats`).

### Generate the milestone dependency graph from tasks.md

**What:** `aa-ma-tui --graph` (or an `aa_ma.render` sub-command) emits a mermaid `flowchart` of milestones from their `Dependencies:` fields.

**Why:** The planning standard (element #13, v0.11.0) says the milestone graph is never hand-authored because it is derivable. Today nothing derives it, so no plan has one.

**Context:** Decided during the plan-architecture-views grill (2026-09-11). `src/aa_ma/tui/model.py` already carries `Milestone.dependencies`; `tui/parser.py::discover_tasks` loads every active plan. Start in `src/aa_ma/tui/snapshot.py` next to `render_tree`. Output goes to stdout as a fenced block so it can be pasted or rendered.

**Effort:** S
**Priority:** P3
**Depends on:** milestone-grammar-ssot M5 (reliable `split_milestones`)

**Done:** diagram-generation M7 (2026-09-24) — `python -m aa_ma.deps graph <tasks.md>` (launcher `aa_ma_deps`); `/aa-ma-plan` Step 5.5 appends it to §13.

### `codemem draw --write` refuses to overwrite a hand-authored view
**What:** `codemem.draw.views.write_views` refuses a target whose line 1 lacks the generated stamp (`STAMP_RE`). **Why:** only the understand-codebase fence checks today (M13 §6.8 CRITICAL), so a bare `--write` in a consumer repo still overwrites a team's own `docs/architecture/README.md`. **Effort:** S · **Priority:** P2

**Done:** 2026-09-27 — `views.write_views` refuses a stampless target before any write; `--check` names it and says move it aside (`tests/codemem/test_draw_check.py`).

### Repoint the PROJECT_INDEX references outside the M13 rewire at codemem
**What:** `claude-code/skills/aa-ma-plan/SKILL.md` (was `commands/aa-ma-plan.md:181,184,857`), `claude-code/skills/execute-aa-ma-milestone/SKILL.md` (was `commands/…:332`), `claude-code/agents/codebase-onboarding-{runbook,conventions}.md` name codemem as default, PROJECT_INDEX.json as fallback; `aa-ma-plan.md:181` stops suggesting `/index`. **Why:** §6.3's blast-radius advice assumes project-index's upstream `blast_radius`; codemem's is downstream (callers are `who_calls`). The gate file is fence-position-tested — `Critical-Path: hook-modification`. **Effort:** S · **Priority:** P2

**Done:** 2026-09-27 — all four files name codemem as the default index with PROJECT_INDEX.json as fallback; `aa-ma-plan` Step 1.2 no longer suggests `/index`; §6.3's pre-check asks codemem's `who_calls` for callers (`tests/skills/test_understand_codebase_rewire.py`).
