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
