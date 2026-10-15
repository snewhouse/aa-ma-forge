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
