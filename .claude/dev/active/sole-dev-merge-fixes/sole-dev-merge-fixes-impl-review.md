# sole-dev-merge-fixes — Post-Impl Review (§6.8)

## Milestone 1: Worktree-safe G3/G4, deterministic footer, lessons
- Window: `1d760f1..6b12a9d`. Audit-Profile: full. Budget: normal (parallel).
- Verdict: **PASS_WITH_WARNINGS**. 0 CRITICAL / 9 WARNING / 16 INFO.

| Agent | CRITICAL | WARNING | INFO | Verdict |
|---|:-:|:-:|:-:|---|
| code-reviewer | 0 | 5 | 3 | WARN |
| security-auditor | 0 | 2 | 5 | WARN |
| tdd-sequence-auditor | 0 | 0 | 3 | PASS (6/6 RED→fix pairs in order) |
| context7-evidence-auditor | 0 | 0 | 0 | PASS (no dependency changes) |
| future-proofing-auditor | 0 | 2 | 5 | WARN |
| **Total** | **0** | **9** | **16** | **PASS_WITH_WARNINGS** |

### Warnings and dispositions
| # | Source | Finding | Disposition |
|---|---|---|---|
| 1 | code-reviewer | Contract under-declares regen outputs (`docs/architecture/*`, `test_plugin_surface.py`) | Noted in the context-log; they are outputs of `regen-generated.sh` |
| 2 | code-reviewer | G4 prints `STATUS: OK` after `MAIN_NOT_UPDATED` | Fixed in b31a9c0 (single terminal STATUS line); test AC2.5b |
| 3 | code-reviewer | A failed `ls-remote` reads as "deleted" | Fixed in b31a9c0 (`--exit-code`, rc reported); test added |
| 4 | code-reviewer | G3/G4 exit-1 ABORTs missing from the SKILL.md exit contract | Deferred: M4 4.2's criterion widened |
| 5 | code-reviewer | `substr($0, 10)` magic number | Fixed in b31a9c0 (`sub()`) |
| 6 | security | Rule 8 lets a commit through with an empty footer (no `set -e`, prefix form, comment, subshell, pipe, `&`, `true ||`) | Fixed in e82da0d: exact-line allowlist after `set -e` (L-049: a second finding on the same mechanism means redesign); 8 RED tests, matrix v2 24/24 |
| 7 | security | Rule 8 lets text follow the footer (`--trailer`, `-s`, continuation `-m`) | Fixed in e82da0d (whole commit line must match) |
| 8 | future-proofing | Stale counts and line numbers in the TODOS install entry | Fixed in 1ce6b15 (rewritten without counts) |
| 9 | future-proofing | The pre-compact guard list is separate from the file reads | Fixed in 98b41ab (`AA_MA_FILES`) |

### INFO deferrals
- `git -C`/`git -c` commit forms → the commit-msg TODO.
- pre-compact parent-dir symlinks → TODO, into M5.
- Repo-copy helper resolution outside forge → TODO.
- `DEFAULT_BRANCH` and `MERGE_STRATEGY` validation → done in G3/G4 (b31a9c0); the Stage A part goes to M4.

### User Override Decisions
None. No CRITICAL findings.

## Milestone 2: Stage state file
- Window: `f78bbf9..03f9008`. Audit-Profile: full. Budget: normal (parallel, 5 agents).
- Verdict: **PASS_WITH_WARNINGS**. 0 CRITICAL / 11 WARNING (10 distinct) / 19 INFO.

| Agent | CRITICAL | WARNING | INFO | Verdict |
|---|:-:|:-:|:-:|---|
| code-reviewer | 0 | 6 | 8 | WARN |
| security-auditor | 0 | 2 | 4 | WARN |
| tdd-sequence-auditor | 0 | 0 | 2 | PASS (RED 83d3fa3 20 min before GREEN d43a709; RED tests unchanged since) |
| context7-evidence-auditor | 0 | 0 | 0 | PASS (no dependency changes) |
| future-proofing-auditor | 0 | 3 | 5 | WARN |
| **Total** | **0** | **11** | **19** | **PASS_WITH_WARNINGS** |

### Warnings and dispositions
All fixed test-first (RED 38d6560, then GREEN), except where noted.

| # | Source | Finding | Disposition |
|---|---|---|---|
| 1 | code-reviewer | On a detached HEAD `'' == ''` made the branch check vacuous | Fixed: the loader treats an empty ORIGINAL_BRANCH as foreign; A ABORTs on a detached HEAD |
| 2 | code-reviewer + security W1 | `sdm_save` writes through a file the loader refused (a symlink is followed) | Fixed: `sdm_save` refuses a symlinked or foreign file, rc 1, still one line, in all 13 copies; test checks the link target is unchanged |
| 3 | code-reviewer | `MERGE_DISPATCHED` is saved but nothing reads it | Fixed: G4 ABORTs unless it is `1`; the G4 tests now set it |
| 4 | code-reviewer | A outside a repo died with git's `fatal:` (rc 128) | Fixed: `ABORT: Not inside a git repository` (rc 1), plus an ABORT table row |
| 5 | code-reviewer | "Nothing is written to the shared temp directory" is false (banner sentinel) | Fixed: now says "no run file" |
| 6 | code-reviewer | F's "Stage G will stop" is wrong after an earlier save | Fixed: message reworded |
| 7 | security W2 + future-proofing W3 | A reuses an existing run dir without checks; run dirs pile up in a plain checkout | Fixed: A validates `SLUG` (`^[A-Za-z0-9._-]+$`), removes earlier `sdm-*` (links as links), and always `mkdir -m 700` afresh |
| 8 | future-proofing | Prose and CHANGELOG say "15 keys"; M4 makes it 18 | Fixed: they name `SDM_KEYS`, not a count |
| 9 | future-proofing | Test `BLOCKS` was a hand list, so a new block would escape the checks | Fixed: read from the `(BEGIN)` markers minus `NO_STATE`; A's `sdm_save` is compared too |
| 10 | future-proofing | Test name hardcodes "12 non-A blocks" | Fixed: renamed to "every block but A" |

### INFO dispositions
- security: non-numeric `PR_NUM` reaches gh argv → fixed (G2/G3 numeric checks, 2 tests).
- code-reviewer: an older run's reviewer notes could reach E3 → fixed by item 7 (fresh run dir).
- code-reviewer: helpers.bash and aa-ma-footer.bats are outside the Contract list → recorded in the context-log.
- tdd INFO 1: assertions dropped in the GREEN test migration? Checked: all 5 path assertions survive as `${SDM_DIR}/…`, and `@test` counts are unchanged in the 4 files.
- **Deferred:**
  - `$CHANGED_PY`/`$CHANGED_SH` word-splitting into the scanners (pre-existing) → M3, which rewrites Stage B;
  - `REMOTE_CHOICE:-github` residual defaults → M4.
- **Accepted:** bash ≥ 4 for `declare -A`; unused `sdm_save` in blocks that save nothing (cost of one identical loader); the check-then-open window in `sdm_load` (needs git-dir write, the plan's residual).
- **To check live (2.3):** whether the C1/C2 agents can write into `<git-dir>/sdm-*` without a permission stall.

### User Override Decisions
None. No CRITICAL findings.

## Milestone 3: Stage B scoped commit, guard, check-conventions refs

Window `f8390c6..fa55ec4` (reviewed); remediation `6b9212d` (RED) → `10845fe` (GREEN), docs `17cb01f`. Audit-Profile: full; 5 agents in parallel.

| Agent | CRITICAL | WARNING | INFO | Verdict |
|---|:-:|:-:|:-:|---|
| code-reviewer | 0 | 3 | 3 | WARN (SDM 145/145, hooks 539/539 run read-only) |
| security-auditor | 0 | 2 | 4 | WARN |
| tdd-sequence-auditor | 0 | 0 | 3 | PASS (RED 04e2fd9 27 min before GREEN 21c57e9; 4644eb7 prose-only) |
| context7-evidence-auditor | 0 | 0 | 0 | PASS (no dependency changes) |
| future-proofing-auditor | 0 | 1 | 2 | WARN |
| **Total** | **0** | **6** | **12** | **PASS_WITH_WARNINGS** |

### Warnings and dispositions (all fixed test-first, Ste: "Fix all 6 now")
| # | Source | Finding | Disposition |
|---|---|---|---|
| 1 | code-reviewer | The staged-set assert ran only when something in scope was dirty. A pre-staged out-of-scope file then reached Stage D's pathspec-less commit; the CHANGELOG and L-053 overclaimed | Fixed in 10845fe: the check runs before staging, always. RED "AC4.4 … even when nothing in scope is dirty" |
| 2 | security | Abort `git reset -q` cleared the operator's whole index (`add -p` hunks lost) | Fixed in 10845fe (Ste: "Check first, touch nothing"): the pre-check aborts with the index untouched; the post-add check unstages only B-commit's own paths. AC4.4 now asserts the index is unchanged |
| 3 | code-reviewer | `${line:3}` on porcelain v1 gave C-quoted names and `old -> new`; guard and B-commit disagreed | Fixed in 10845fe: `--porcelain -z` (rename source as next NUL field); `CHANGED_FILES` with `core.quotePath=false`. RED: space-named, rename, non-ASCII cases |
| 4 | code-reviewer | ABORT text listed one direction only, and could be empty | Fixed in 10845fe: the "missing" direction is not an error (an undone change stages nothing → "nothing to commit"); ABORT always names the extra paths. RED "undone … is not an ABORT" |
| 5 | security (+ TODOS:98, planned for M3, missed — L-056) | `$CHANGED_FILES` unquoted into pre-commit (`--config=x` read as a flag); same for Stage C ruff/shellcheck | Fixed in 10845fe: pre-commit gets `./`-prefixed names in an array (its argparse rejects `--`, probed); ruff/shellcheck get `-- "${arr[@]}"` (probed: report names unchanged). RED in b_scope and c_dispatch |
| 6 | future-proofing | Exit contract "(Stages A, B-commit, E2, F)" omitted G2–G4's ABORTs (`stage-g-merge.md:149…414`) | Fixed in 10845fe: "any stage's `ABORT: …` line" |

### INFO dispositions
- **Adopted (Ste):** `export GIT_LITERAL_PATHSPECS=1` in the guard and B-commit. In Stage B it is set after pytest/pre-commit, so the user's tests keep git globs. RED "glob-shaped name matches only itself"; a mutation confirms the post-add check catches a glob.
- **Subsumed by W3:** `cut -c4-` porcelain prefix; quoted-path guard failure.
- **Accepted:** one `git status` per changed file (KISS at branch sizes); `restore --staged --worktree` discards an out-of-scope staged edit (intended, documented); `aa-ma-footer.bats` outside the Contract list (CL deviation); `fresh`/`blk` duplicated with test_stage_state.bats (different semantics: PATH order, lazy extraction); pre-existing `source` of the branch's own footer helper (same trust as running its pytest).
- **Probe findings, recorded:** `git restore --source=HEAD --staged --worktree` deletes a staged path HEAD lacks (rc 0); pre-commit rejects `--` (rc 1) and strips `./`; shellcheck reports `./x` names verbatim, so the scanners use `--`.

### Verification after remediation
bats SDM+hooks **692/0**; b_scope 23/23; c_dispatch 8/8; pytest **3136 passed**; shellcheck 0 on the extracted B, B-commit and C; SKILL.md 497 lines (cap 500); plugin-surface golden unchanged. Mutations: pre-check off → the clean-scope AC4.4 FAILs; literal pathspecs off → the glob case FAILs (the post-add check aborts).

### User Override Decisions
None. No CRITICAL findings.

## Milestone 4: Stage F REST body update, small fixes, docs drift

Window `07a8b45..701d9a7` (reviewed). Audit-Profile: full; 5 agents in parallel.

| Agent | CRITICAL | WARNING | INFO | Verdict |
|---|:-:|:-:|:-:|---|
| code-reviewer | 0 | 5 | 6 | WARN (6 SDM bats files, 133/133, run read-only) |
| security-auditor | 0 | 2 | 3 | WARN (probes in mktemp dirs) |
| tdd-sequence-auditor | 0 | 0 | 1 | PASS (RED a85c2cf 15 min before GREEN b30a410; RED touches no skill file) |
| context7-evidence-auditor | 0 | 0 | 2 | PASS (no dependency changes; gh `-F @file` from Context7, `--jq` +1 NL from the 4.0 live probe) |
| future-proofing-auditor | 0 | 4 | 5 | WARN |
| **Total** | **0** | **11** | **17** | **PASS_WITH_WARNINGS** |

### Warnings and dispositions (Ste: "Fix all 11", test-first)
| # | Source | Finding | Disposition |
|---|---|---|---|
| SEC-1 | security | Loading E1's counts from the state file let `(( n_github … ))` evaluate a planted value such as `BASH_VERSINFO[$(cmd)0]` (probed: code ran). This breaks "the loader never evals a value". Same uid only. | Fix: `^[0-9]+$` check on `n_github`/`n_gitlab` in E2 before any arithmetic; RED with the probe payload, via the state file and via env |
| SEC-2 | security | `gh pr view` (no args) selects by branch. A same-named fork PR could be picked, and then F PATCHes it and G3 merges it (G3 checks only `headRefName`). Unverified gh selection. | Fix: F's one lookup also reads `isCrossRepository,headRefName`; it PATCHes only a same-repo PR whose head is ORIGINAL_BRANCH. Otherwise `STATUS: PR_BODY_NOT_UPDATED … reason=not-this-branch` and PR_NUM is not saved. G3 also requires `isCrossRepository=false`. `headRefOid` was rejected because GitHub updates it asynchronously after a push |
| CR-1 | code-reviewer | F looked the PR up 4 times on the existing path (url, number, url, number), and the two number reads could disagree | Fix: one `gh pr view --json number,url,isCrossRepository,headRefName --jq '[…]\|@tsv'` (probed on gh 2.46.0, PR #45); the create path does one lookup after `pr create` |
| CR-2 | code-reviewer | `PR_BODY_NOT_UPDATED` covered 3 causes and could print `PR #0` | Fix: `reason=no-pr-number\|not-this-branch\|patch-failed\|readback-differs`; documented in the table row |
| CR-3 | code-reviewer | `n_other` is saved and allowed but never read | Fix: a `# why:` comment (kept for diagnosis: it appears in E1's line and in the state file; the 4.2 AC names it) |
| CR-4 | code-reviewer | Stub `*"--jq '.body'"*` alternatives can never match (the shell strips the quotes) | Fix: deleted |
| CR-5 | code-reviewer | stage-state.md: "a missing required value … is never replaced with a default" overclaims (`DEFAULT_BRANCH:-main`, Stage C `:-`, E2 `:-gitlab`) | Fix: sentence narrowed to the values marked required, with the known defaults named |
| FP-1 | future-proofing | The exit-status table is synced by hand with no test; it had already drifted by ~10 rows | Fix: a bats test asserting the table ⊇ every emitted `(STATUS\|ABORT): [A-Z_]+`, and one asserting ADR-0008's backticked block names == the block markers |
| FP-2 | future-proofing | Stage A's aborts are listed in 3 places | Fix: the ADR row points at the SKILL.md Stage A table |
| FP-3 | future-proofing | The ADR stub env list was stale when written (no `GH_API_BODY_STORE`, `GH_PR_STATE`, `GH_HEAD_REF`, `GH_MERGE_RC`; `GLAB_MR_EXISTS` twice) | Fix: replaced with a pointer to the stubs' header comments |
| FP-4 | future-proofing | Magic `42` in the stub (`{"number":42}`, pr view arms) and the F/state tests that read it | Fix: `STUB_PR_NUM` (default 42) read by the stub, exported once in `fixtures/helpers.bash`; the stub-derived assertions use it |

### INFO dispositions
- **Fixed with the WARNINGs (cheap, same files):**
  - ADR-0008 :36/:38/:76 still say Bandit → Ruff S;
  - the gh version (2.46.0) is named on Stage F's newline-rule comment and the PROBE line (C7 INFO-2);
  - Stage A step-2 comment "(main/master)" now points to the default-branch check;
  - ADR "4 sources" count dropped;
  - TODOS Stage C entry cites symbols, not line numbers;
  - 4.2 Result Log corrected: 13 `SDM_KEYS` copies, not 12 (counted before E1's loader was added).
- **Accepted:** git's `fatal:` text before Stage A's new ABORT line (same as G3/G4); `PR_OP=edit` → `update` (no reader); C7 INFO-1 (the citation is prose, not a `CONTEXT7` line).
- **Deferred to TODOS (one entry):**
  - `check-ref-format --branch` expands `@{-N}` (add `refs/heads/$X` validation in G3/G4; Stage A unreachable);
  - PR_BODY_FILE not confined to SDM_DIR (pre-existing; same uid);
  - G2/G3 `^[0-9]+$` accepts PR_NUM 0 (pre-existing; F never saves 0);
  - a static check that every `sdm_save` key is in `SDM_KEYS`.

### Verification after remediation
- RED `7b22079`: 8 not-ok, each at the assertion under test. SEC-1 (status 0, the payload was evaluated), SEC-2 F ×2 (PATCH count), CR-1 ×2 (lookup count; the post-create `number,url` lookup), CR-2 ×2 (no `reason=`), SEC-2 G3 (status 0). The 2 FP-1 sync guards passed, as guards should.
- GREEN `b403f60`: `bats --tap SDM tests/hooks` → **714 ok / 0 not-ok** (707 + 7). The first run had 1 failure: the existing "no masking defaults" test caught a `PR_NUM:-0` this fix had introduced, and it was removed.
- Other checks: shellcheck rc 0 on all 15 extracted blocks; status-table `comm` empty; ADR markers == code; SKILL.md 489 lines; `gh pr edit` in F = 0; pytest 3137 passed; regen header-only (restored).
- **Mutations (L-045), 8/8 CAUGHT, restored from backups and checked with `cmp`:** E2 numeric check dropped; F ownership check dropped; F head-branch half dropped; foreign PR_NUM still saved; G3 cross-repo check dropped; reason dropped; a table row removed (FP-1 guard); an ADR row removed (FP-1 guard).
- Live: the one-call `@tsv` lookup was probed on gh 2.46.0 against PR #45: `45\t<url>\tfalse\tfix/sole-dev-merge-fixes-m4`.

### User Override Decisions
None. No CRITICAL findings.

---

# Milestone 5: pre-compact writes into the worktree — §6.8 (2026-10-18)

- Audit-Profile: full · window `4ec32db..3802ecf` · budget normal · dispatch parallel (5 agents)

| Agent | CRITICAL | WARNING | INFO | Verdict |
|---|:-:|:-:|:-:|---|
| code-reviewer | 2 | 5 | 2 | CRITICAL panel |
| security-auditor | 0 | 2 | 4 | WARN |
| tdd-sequence-auditor | 0 | 0 | 3 | PASS (RED `7d69ea0` 195 s before GREEN `3d800b9`; re-run reproduced the 8 RED) |
| context7-evidence-auditor | 0 | 0 | 2 | PASS (no deps; stdin `cwd` contract backed by the live 5.0 probe + captured fixture) |
| future-proofing-auditor | 0 | 3 | 1 | WARN |
| **TOTAL** | **2** | **10** | **12** | pending Ste's CRITICAL decisions |

## CRITICAL
- **C1 (code-reviewer, verified by the orchestrator):** guard C treats "a linked worktree has the task dir" as "the task is worked there". Plan dirs are tracked, so every worktree cut from a commit that carries the plan has it. Here, `git worktree list` puts the detached `codemem-plugin-wt` (holding both plans) first: a main-rooted compaction would skip the CHECKPOINT and say "log the CHECKPOINT in <codemem-plugin-wt>". Plan Risk 3 does not hold. Fix proposed: a candidate is a linked worktree **on a branch** whose branch has commits touching `.claude/dev/active/<task>` that ROOT's HEAD lacks (`git log HEAD..<branch> -- <taskdir>`); 0 → write ROOT, ≥1 → write nothing and name every candidate. Measured here: m5 branch 10 commits for sole-dev-merge-fixes (candidate), prototype branch 1 for code-conventions-impact (candidate), detached tool worktree excluded.
- **C2 (code-reviewer):** `references/stage-state.md` is outside the M5 Contract `Files:`. Prose-only M4 drift carry-in (`e536836`), recorded in tasks.md but not as a CL deviation.

## WARNING
- W1 (code-reviewer): no test has a linked worktree without the task, or a detached/unrelated one with it; the `-d` check mutated to `true` survives.
- W2 (code-reviewer, KISS): stdin `cwd` == pwd (probe), so roots from `$PWD`'s toplevel would also work and keep the guard on in the no-stdin / no-jq paths (today IN_REPO=0 there → main dirtied, L-1347 itself).
- W3 (code-reviewer): `INPUT=$(timeout 2 cat || true)` swallows rc 124/127 silently.
- W4 (code-reviewer + future-proofing): `timeout 2` unnamed, no unit, no link to the 5 s PreCompact timeout in `scripts/lib/aa-ma-install-lib.sh`.
- W5 (code-reviewer): fallback notices don't say the linked-worktree check was skipped.
- W6 (security, A01, reproduced): `rev-parse --show-toplevel` follows a repo-local `core.worktree`, so a tarball/shared-dir repo can root the hook in another project and append there; no containment check of cwd in ROOT. Fix: `cwd_real=$(cd "$cwd" && pwd -P)`, require `"$cwd_real/" == "$top/"*`.
- W7 (security, A03, reproduced): `_aa_ma_log_oneline`/`mask_secrets` strip only CR/LF; ESC/BEL in a repo-controlled task name reach the systemMessage (new in M5) and hooks.log (pre-M5). Fix in the shared lib: replace every `[[:cntrl:]]`.
- W8 (future-proofing): the final-notice comment still says "both kinds" (three sources now).
- W9 (future-proofing): the no-jq test keeps a fixed tool list (already broke once on `sed`).

## INFO
- code-reviewer: DRY — extract `aa_ma_project_root` before the four-hook TODO copies it; `$HOME` vs realpath ROOT in the exemption.
- security: no `-c core.fsmonitor=false` on the new git calls (they don't run it on git 2.53, tested); porcelain without `-z`; check-then-append race (theoretical); clean checks listed.
- tdd: docs commit is M4 carry-over; literal `src/` rule vacuous; per-file pairing OK.
- context7: probe lacks the Claude Code version (2.1.302 at 5.0); fixture predates the window, still valid.
- future-proofing: plan-local labels ("5.0 probe", "design C") in shipped comments.

## Probed facts (security-auditor, git 2.53): `rev-parse --show-toplevel` and `worktree list --porcelain` do not run `core.fsmonitor`; `git status` does.

## User Override Decisions (Ste, AskUserQuestion, 2026-10-18)
- C1: **Accept — fix test-first.** Candidate = linked worktree on a branch whose branch has commits touching `.claude/dev/active/<task>` that ROOT's HEAD lacks; 0 → write ROOT, ≥ 1 → write nothing, name all. W1 is covered by its RED cases.
- C2: **Accept as a Contract deviation** (CL entry).
- WARNINGs fixed in the same round: W2/W3/W5 (root + notices), W4/W8/W9 (hygiene), W6/W7 (security; W7 widens the Contract to `claude-code/hooks/lib/aa-ma-log.sh` + `tests/hooks/aa-ma-log.bats`).
- INFOs → TODOS (deferred §6.8 M5 INFOs).
