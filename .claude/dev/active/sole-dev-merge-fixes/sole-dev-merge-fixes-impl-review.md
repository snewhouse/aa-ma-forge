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
