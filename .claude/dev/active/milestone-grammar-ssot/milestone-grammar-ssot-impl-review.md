# §6.8 Post-Impl Adversarial Review — Milestone 1

Audit-Profile: `code-only` · Plan `Created: 2026-08-09` (post-v0.8.0 cutover) · Window: working tree vs `77e38d4`
Agents dispatched: code-reviewer, security-auditor, tdd-sequence-auditor, future-proofing-auditor.
context7-evidence-auditor: **N/A** — zero dependency additions or version bumps in this milestone.

## Verdict: PASS_WITH_WARNINGS (after inline fixes)

Initial: **6 CRITICAL, 22 WARNING, 11 INFO**. All 6 CRITICAL fixed inline; suite 819 passed / 0 failed.

## CRITICAL — all fixed

| # | Finding | Fix |
|---|---|---|
| C1 | `coerce_numbers_to_str=True` is **model-wide**, not field-scoped. Reproduced: `Milestone(title=42)` → `'42'`; `dependencies=7` → `'7'`. Also permanently masked the migration — 6 sites still passed ints. | Config dropped entirely; all `Milestone(number=<int>)` sites converted to str. Explicit over clever. |
| C2 | `_FENCE_RE` paired fences **flat**, so nested fences emitted phantom milestones. Reproduced: a 4-backtick block containing a 3-backtick block yielded 2 phantom milestones. | Replaced with a CommonMark line scanner: same-char + length-based close, unterminated runs to EOF, `~~~` supported. |
| C3 | Headings inside **HTML comments** parsed as real. Reproduced: `<!--\n## Milestone 9: commented out\n-->` → a milestone. `docs/templates/tasks-template.md` has ten comment blocks. | New `sanitize()` composes fence stripping with `plan_parsers._strip_html_comments`. |
| C4 | plan.md AC#9 pinned `--recursive ... exactly 113 ^ok`; recursive baseline is 118 (+6 in `fixtures/build_active_dir.bats`). The HARD gate's own criterion was unsatisfiable. | Corrected to 119; reference.md now records 112/118 as-of-b11c46d and 113/119 after M1. |
| C5 | `passed == 784 + 32` is **self-invalidating** — archiving this very plan adds 2 parametrized cases to `test_corpus_grandfathering`. | Replaced with `failed == 0 and errors == 0` plus a scoped per-milestone delta. |
| C6 | `--root .claude` now returns **15** tasks (this plan's own dir), so AC#5/#7's "14/14, matches exactly" was unsatisfiable. My own verification had silently filtered the row out with `jq`. | Table reframed as "measured at b11c46d; every listed row must match, rows added later are out of scope". |

## Notable WARNINGs actioned

- **ReDoS (security):** `_NUM_S`'s `(?:\.\d+)*` measured **linear** — my suspicion was wrong (6.4 KB → 259 µs). The real defect was `_FENCE_RE`: **O(n²)**, 78 KiB of language-tagged fences → **5.15 s** through `parse_task_dir`, because a ```` ```python ```` line can open a fence but never close one. Fixed by the same line scanner as C2; a regression test now asserts sub-quadratic growth. An atomic-group "fix" was tested and **rejected** — it silently disables stripping entirely.
- `.bis` hardcoded in the grammar → generalised to `(?:\.[a-z]{2,}|[a-z])?`. The tests immediately caught that the first attempt dropped single-letter forms (`2.7b`).
- `_NUM_M` capped milestones at one dot while `_NUM_S` allowed any depth — `## Milestone 3.5.1:` silently dropped. Now symmetric.
- `Block` was a bare 3-tuple of same-typed strings → `NamedTuple`.
- `_split_milestone_blocks` / `_split_step_blocks` were one-line delegations with one caller each — deleted; callers use `grammar` directly (L-005).
- Broken reference in shipped source: `grammar.py` docstring cited a file M2 has not created → reworded to future tense.
- `test_json_output.py:53` docstring still said `schema_version: 1` → made version-free so it cannot go stale again.
- `CLAUDE.md` architecture tree lacked `grammar.py` and described `parser.py` as "regex grammar" → corrected.
- `tests/hooks/aa-ma-parse.bats` was missing from plan §5 Artefacts → added.
- `test_case_counts_are_pinned` used `==`, punishing legitimate additions → `>=`.

## Deferred (not blocking)

- `aa-ma-scribe.md:148,163` still mandates `### Step N.M:`, which M2's strict writer will outlaw — **M2 scope gap**, logged for M2.
- `_provenance_tail` reads an entire append-only log to return 5 lines (CWE-770). Pre-existing, unrelated to this diff.
- `--json` emits `provenance_tail` verbatim and absolute paths — treat output as sensitive. Pre-existing.
- `test_corpus_grandfathering`'s `assert milestones` will red on archiving any out-of-grammar plan; no allowlist. Pre-existing pattern.

## TDD verdict: PASS

Canonical git-log check UNVERIFIABLE (single uncommitted window), but substitute evidence is stronger: commit `77e38d4` enumerates all 24 test cases verbatim **before** any implementation existed, and the delivered file matches with zero drift. RED is guaranteed by construction — `grammar.py` provably absent at that commit while the test imports it at module level. A mutation harness killed **6 of 7** mutants (the survivor being a provably equivalent mutant).

**Acted on its recommendation:** split into two commits — tests first (legitimately RED), then implementation — so intra-milestone TDD ordering is mechanically verifiable rather than reconstructable only by mutation testing.

---

# Milestone 3 — §6.8 Post-Impl Adversarial Review

- **Audit-Profile:** code-only
- **Window:** `9ffd3d0..bb1120f`
- **Agents dispatched:** code-reviewer, security-auditor, tdd-sequence-auditor,
  future-proofing-auditor. `context7-evidence-auditor` **not dispatched** —
  its trigger is new PyPI deps or MAJOR version bumps, and
  `git diff --name-only` shows no `pyproject.toml` / `uv.lock` / `requirements`
  in the window.
- **Raw:** 6 CRITICAL / 17 WARNING / 14 INFO → 5 distinct CRITICAL after dedup.
- **Verdict: PASS_WITH_WARNINGS** after inline fixes.

## CRITICAL

| # | Finding | Disposition |
|---|---|---|
| 1 | **WARNING never reached `$FINDINGS`** — stdout only. Stage D (`sole-dev-merge.md:424`) reads `$FINDINGS` exclusively, so with the scanner missing the machine-readable artefact was byte-identical to a clean scan: `TOTAL=0`, triage skipped, PR body renders a clean security narrative. Raised independently by code-reviewer and security-auditor. | **FIXED.** Degraded state now writes `[HIGH] … UNKNOWN … (scanner-unavailable)` into `$FINDINGS`, mirroring the safe-default `parse_agent_file` has used at `:319-324` all along. |
| 2 | **Guard tested resolvability, not execution.** `command -v` answers a different question: `true`, `:` and `/bin/false` all resolve and all leave an empty report → `0 findings`, no warning. Reproduced before accepting. | **FIXED.** The test is now on the report: ShellCheck exits 0 (clean) or 1 (findings), so `rc > 1 || ! -s "$SHELLCHECK_OUT"` is the degraded condition. Subsumes absence (rc 127), so the separate `command -v` branch was removed rather than added to. |
| 3 | **New shipped branch had zero coverage** and was structurally unreachable: the only test setting `CHANGED_SH` is C4, which now skips under exactly the condition that reaches the new branch. `New-Tests: 0` was accurate and that was the problem. | **FIXED.** Added `C4 records UNKNOWN in findings when the scanner does not run` — needs no external binary, so it can never skip; loops over absent / mute / non-JSON. Mutation-verified: reverting the sentinel to stdout-only makes it fail by name. `New-Tests: 0 → 1`. |
| 4 | **`sweep_slug_tmp` reached 2 of 3 sites**, and the un-migrated one (`test_smoke_e2e.bats:214`) cleaned up in the *test body*, not `teardown()` — so it leaked on exactly the runs where a test failed. AC#3 ("0 leftovers") therefore held only on the all-green path. | **FIXED.** Moved to `teardown()` in `test_smoke_e2e.bats` and `test_stage_e3_body.bats`; in-body cleanups deleted. |
| 5 | **C3/bandit retains the identical defect** on the higher-value scanner — undeclared dependency, absent from the bats CI job, and it drives Stage D's auto-remediation. | **DEFERRED to user.** Outside "fix the flaky C4 test"; recorded in CHANGELOG as a known gap. |

## Fourth degraded mode, found while verifying the fix

Re-running the probe after fixing #2 showed `SHELLCHECK_BIN=echo` still slipping
through: rc 0, non-empty but non-JSON output, and the parser's
`except (JSONDecodeError, FileNotFoundError): sys.exit(0)` laundered it back to
a silent zero. Matches the security-auditor's "truncated JSON" WARNING (a
scanner OOM-killed mid-write looks identical). The `except` now prints
`[HIGH] C4 REPORT UNPARSEABLE …` to stdout, which is appended to `$FINDINGS`.

Final matrix — every degraded mode is now non-silent and non-zero:

| `SHELLCHECK_BIN` | aggregate | `$FINDINGS` |
|---|---|---|
| (default) | 4 findings | real SC1009/1072/1073/1080 |
| `true` / `:` / `/bin/false` | 1 finding | `[HIGH] C4 NOT RUN` |
| `echo` | 1 finding | `[HIGH] C4 REPORT UNPARSEABLE` |
| `/nonexistent/shellcheck` | 1 finding | `[HIGH] C4 NOT RUN` |

## WARNINGs actioned

- **Two false claims in my own comments** — "three teardowns each hardcoded five
  filenames" (it was two teardowns; the third site was an in-body cleanup with
  six names) and "the glob cannot fall behind the code that writes the files"
  (it required a `-` before SLUG and a `.` after, so `sole-dev-merge-${SLUG}.md`
  and extensionless names were unmatchable; three un-slugged writers can never
  match by design). Both corrected; the glob widened to `*"${SLUG}"*`.
- **`command -v` matches shell builtins** — the C4 skip guard now requires the
  binary to identify itself via `--version | grep -qi shellcheck`.
- **CI claimed a guarantee nothing asserted** — bats reports a skip as
  `ok N # skip` and exits 0, so a stray `SHELLCHECK_BIN` would have let C4
  evaporate green. Added a `shellcheck --version` step that fails at 127.
  Install made conditional (`command -v shellcheck || apt-get …`), removing an
  unconditional ~20 s network dependency without weakening the guarantee.
- **CHANGELOG omission** — `sole-dev-merge.md` is symlinked live by
  `install.sh`, and the change adds both a new stdout line and a new public env
  var. Entry added; `SHELLCHECK_BIN` documented in CLAUDE.md.
- **Indentation** — the flat `else` body was re-nested. The claim that the
  heredoc forced it was wrong: only the body and the column-0 `PY` terminator
  are position-locked.

## Deferred, with reasons

- **C3/bandit + both `python3` `|| true` paths** (CRITICAL #5) — user's call.
- **`sev_map.get(level, "LOW")` fails open**: an unknown severity in a future
  ShellCheck downgrades a real error to `[LOW]`, which Stage D triages as a
  reviewer note. One word to change, but it alters a mapping that
  `reference.md` mirrors — wants its own change.
- **Unpinned `shellcheck` version in CI.** C4's assertion accepts
  `[CRITICAL] || [HIGH]`, so an `error`→`warning` demotion upstream passes
  silently. Pinning wants its own decision.
- **Predictable `/tmp` paths** (`SLUG="${SLUG:-$(date +%s)}"`, `: > "$FINDINGS"`
  with no `O_EXCL`) — pre-existing symlink-truncation exposure on shared hosts.
  Security-auditor rated WARNING, not CRITICAL.
- **`.bash` files are not linted in CI** — `find . -name '*.sh'` misses
  `helpers.bash`, where this milestone added a function.

## TDD verdict: PASS (ordering), with the gap now closed

Ordering verified: first `tests/` commit precedes first source commit by 3m50s.
`New-Tests: 0` was independently confirmed accurate at the time — 69 `@test`
blocks unchanged — but the auditor's substantive point stood: there was no
revision at which the suite was red, and at `fd473b6` the guard could not
observe the code it guarded, because the `SHELLCHECK_BIN` seam only landed in
`bb1120f`. Green by construction, not by fix. Closed by CRITICAL #3's test.

**Same lesson, third variant.** M1: a verification command that filtered out its
own failing row. M2: a lint that could not see inside the fences it was linting.
M3: a fix proved by hand in both directions, written up in a Result Log, and
shipped with no test. Prose evidence does not re-run.

---

# Milestone 4 — §6.8 Post-Impl Adversarial Review

- **Audit-Profile:** infra → code-reviewer, security-auditor, future-proofing-auditor
  (tdd-sequence-auditor and context7-evidence-auditor are not in the `infra` slate)
- **Raw:** 17 CRITICAL / ~20 WARNING / 14 INFO across three agents → **8 distinct CRITICAL**
- **Verdict: PASS_WITH_WARNINGS** after all 8 were fixed inline.

## The finding that mattered

My M4 fix was still inert, and my own verification had hidden it.

`MILESTONE_TITLE` is assigned at line 869 — 347 lines *after* the §6.7 gate
consumes it at 522. The extractor received an empty title, returned empty, and
every condition passed. I had "dogfooded" the new logic against M4 and reported
it working; that probe set `MILESTONE_TITLE` by hand. I verified the helper, not
the shipped code path.

The security auditor named the structural cause, which is worth more than any
individual fix: **the gate's only refusal signal is *finding* something**, so
wrong pattern, wrong milestone, truncated block, missing library and unset
variable all converge on the same output as a clean milestone. Fixing them
one at a time leaves the next undiscovered instance live. Hence exit codes.

## The 8 distinct CRITICALs

| # | Finding | Fix |
|---|---|---|
| 1 | `MILESTONE_TITLE` unset at gate time → empty title → PASS | Derived in the §6.7 preamble via `aa_ma_extract_active_milestone`; refuses if still empty |
| 2 | Bold `- **Status:**` / `- **Gate:**` invisible. 22 and 24 in corpus; the shipped Phase 5 writer emits bold, so standard-path plans were born un-gateable | `aa_ma_field_value` / `aa_ma_count_field` accept both |
| 3 | Fail-open: missing file, empty title and no-match all returned 0-and-empty | rc 0/1/2/3; every caller refuses on non-zero |
| 4 | `index($0, title)` substring match returned the wrong milestone's block | Exact title match; duplicates return rc 3 |
| 5 | `## Milestone` inside a fenced block truncated the block | `_aa_ma_sanitize` (CommonMark line scanner) |
| 6 | Multi-line HTML comments truncated the block; the Python docstring falsely claimed parity | Same sanitizer; 3 corpus files carry multi-line comments today |
| 7 | `verify-impl` kept a divergent extractor whose `$((N+1))` is a hard bash error on `2a` (corpus ships `2a/2b/2c`) | Migrated to `aa_ma_extract_milestone_block_by_number` |
| 8 | Scope: `aa-ma-parse.sh` (sourced by every hook) was outside the plan's declared artefacts | plan §5 and §6 Rollback amended |

## WARNINGs actioned

- Provenance evidence greps were **file-global** — once any milestone wrote
  `CRITICAL_PATH_REVIEW`, every later one was pre-satisfied. Now milestone-scoped.
- `grep -q "GATE APPROVAL: $TITLE"` treated the title as a BRE; a title with `.`
  matched another milestone's approval. Now `grep -qF --`.
- `- Gate: Hard` extracted `Hard`, so `== "HARD"` silently skipped the HARD gate.
- `${HOME}` hardcoded with no fallback, unlike every shipped hook; the guard's
  `# HALT` was a comment, so control fell through into the failing `source`.
  Now repo-local-first resolution and a real `exit 1`.
- `parse_critical_path` had **zero** production callers — the constant got a
  parser and the parser got no caller. `plan-verification` Angle 6 check #2 now
  invokes it, and its prose copy of the enum was deleted rather than becoming a
  third source of truth.
- Test weaknesses, all mine: an `-eq 0` assertion that could not fail for the
  regression it named; a `[A-Z]+` re-implementation that did not exercise the
  shipped `[A-Za-z]+`; `_exec_lines` accepting only ```` ```bash ````; the
  mawk/gawk parity loop passing with `-ge 1` on a gawk-only host.

## Repo-wide: four dead assertions, none of them mine

`! cmd` is exempt from `set -e` (POSIX: "-e shall be ignored when the command is
the `!` reserved word"), so a **non-final** `! cmd` line in a bats test can never
fail it. An audit found four, two of which asserted that a security vulnerability
had been removed:

- `test_smoke_e2e.bats:211` — `! grep -q 'shell=True' src/vuln.py`
- `test_stage_d_triage.bats:163` — line-scoped B602 auto-fix check
- `test_stage_e3_body.bats:171` — markdown-injection neutralisation check
- `aa-ma-plan-skip-warn.bats:119` — first of two stacked `!` lines

All four rewritten as explicit `if …; then false; fi`. Re-audit: 0 remaining.

## New guards, both mutation-verified

- `tests/test_grammar_parity.py` — pins `AA_MA_MILESTONE_ERE` against
  `grammar.py::MILESTONE_RE` over the corpus plus an edge-case table, under every
  awk on the host. The two were called mirrors with nothing checking. Dropping
  `|M` from the ERE fails 6 of 7 cases. It also surfaced a real divergence
  (`## Milestone 5:` — empty title), fixed by `aa_ma_is_milestone_heading`.
- Exports-header drift test in `aa-ma-parse.bats` — caught
  `aa_ma_is_milestone_heading`, which I had added minutes earlier and not
  documented. The header is the discovery surface; a symbol missing from it gets
  reimplemented, which is how this repo reached six milestone grammars.

## Lesson, fourth variant

M1: a verification command that filtered out its own failing row. M2: a lint
blind to the fences it was linting. M3: a fix proved by hand and shipped with no
test. M4: a dogfood probe that set the one variable the shipped path never sets.
Each time the green tick was real and measured the wrong thing.

---

# §6.8 Post-Impl Adversarial Review — Milestone 5: Gate enforcement reads the Python SSoT

Generated: 2026-09-11 · Audit-Profile: `infra` · Budget: normal · Window: `8c632bc..516fc4e`
Agents dispatched: code-reviewer, security-auditor, future-proofing-auditor (infra slate; tdd-sequence and context7 skipped per profile — TDD sequence is visible in the window anyway: `e4d1433 test(gate): RED` precedes `e311666 feat(gate)`).

## Verdict: PASS_WITH_WARNINGS (after inline fixes)

Raw: **5 CRITICAL, 21 WARNING, 17 INFO** (code-reviewer 3/6/5, security 1/3/4, future-proofing 1/12/8). Deduplicated: **4 distinct CRITICAL — all reproduced by the lead before fixing, all fixed inline**, plus 12 WARNINGs actioned. pytest 959 → **972**, hooks bats 161 → **168**, both 0 failures.

## CRITICAL — all fixed (each has a regression test that failed before the fix)

| # | Finding (agent) | Reproduced | Fix |
|---|---|---|---|
| C1 | Fence-close inside an HTML comment: `has_unterminated_fence` ran on raw text, `split_milestones` on comment-stripped text — a ``` closer inside `<!-- -->` satisfied the check and then vanished, fence ran to EOF, PENDING sub-step hidden (code-reviewer) | `exit 0, pending 0` | One fence state machine, `grammar.scan_fences` → `FenceScan(stripped, blocks, unterminated)`; the three readers are views over it; `has_unterminated_fence` runs on `_strip_html_comments(text)`, the same input `sanitize` feeds. `test_fence_closed_only_inside_an_html_comment_is_still_unterminated` |
| C2 | Invisible line separators (FF, VT, NEL, LS, PS, FS/GS/RS): `str.splitlines()` splits on them, no regex or renderer does — `- Status: ACTIVE\x0c```` opened a fence the reader never saw (security-auditor CRITICAL and code-reviewer C2, independently) | `exit 0, pending 0` for `\x0c`, `\x0b`, `\x85`, ` `, `\x1c` | Scanners split on `\n` only; `read_tasks_text` refuses any C0/C1/LS/PS control character with line number quoted (row-10 semantics: invisible ⇒ refuse). Parametrised test over 5 separators |
| C3 | §7.1 fence trusted `${GATE}`/`${MILESTONE_TITLE}` from §6.7; run in a fresh shell both are empty, `[[ "" == HARD ]]` is false, the HARD gate is skipped with rc 0 and no output — the exact "GATE was always empty" failure of the awk it replaced; and no test executed §7.1 (code-reviewer) | rc 0, silent, no artifact | §7.1 is self-sufficient: resolves the lib, calls `aa_ma_gate` itself (two calls to one SSoT cannot drift), refuses on empty heading/gate. Six bats cases execute the shipped §7.1 text under `env -i` |
| C4 | ADR-0009 stated "the corpus uses [the annotated form] 24 times" with no counting command; measured 17 line-anchored (future-proofing) | 17 | ADR and reference row 8 corrected to 17 with the grep recorded; the same number was wrong in context-log (left as history) |

## WARNINGs actioned

- **Duplicate milestone numbers in ACTIVE mode** (security): `Milestone 1: Foo` vs `Milestone 1: Foo bar` — distinct headings, but §7.1's `grep -F "GATE APPROVAL: Milestone 1: Foo"` is a prefix match. Now `exit 3` on duplicate numbers as well as headings. Test added.
- **Duplicate step numbers** (code-reviewer): `--step 1.1` returned the first's Mode silently. Now `exit 3`. Test added.
- **Uncaught `UnicodeDecodeError`** / `ValueError` broke the exit-code contract (security): now `Unreadable` → exit 2 with envelope; a last-resort `except` in `main` keeps "JSON is always written" true; `--step` without `--milestone` is an argparse usage error. 1 MiB size cap added (quadratic-regex hardening). Tests added.
- **kv newline injection via path** (code-reviewer): `error=` embedded the raw path; a path containing `\nexit_code=0` forged kv lines. Every value now has `\n` escaped. Test added (line-anchored assertions — the first draft asserted a substring and was wrong).
- **First-occurrence-wins hides a stale second value** (code-reviewer): measured the corpus first — 42 step blocks carry two `Mode:` candidate lines because the command itself writes `- Mode: AFK — auto-dispatched` into Result Logs — so the rule adopted is *refuse when candidates disagree*, not *refuse on >1*. Tests added both ways.
- **Quadratic title regex** (security): `(?P<title>.+?)[ \t]*$` was O(n²) on a long whitespace run (20k spaces → 1 s); now `(?P<title>.*[^ \t\n])` — 200k spaces → 0.000 s. (`[^ \t]` without `\n` let the title swallow the newline; caught by the existing `test_match_does_not_span_lines`.)
- **§5.2 fence could not run as shipped** (code-reviewer): it sourced `${AA_MA_LIB}` "resolved as in §6.7", 300 lines later; bats passed only because the harness injected it. Fence now resolves the lib itself; the injection is removed from the harness.
- **plan-verification check #2 used undefined `$TASK_DIR/$TASK_NAME`** and Phase 4.5 runs before Phase 5 writes tasks.md → spurious CRITICAL on every fresh plan (code-reviewer). Inputs defined from the task name; missing file is a SKIP with a re-run instruction.
- **Schema enums duplicated `enforce.GATES`/`MODES` as literals** (future-proofing): now `sorted(GATES)` / `sorted(MODES)` / new `MODE_SOURCES`; schema `maximum` tied to `EXIT_NOT_FOUND`; dead `mode or "HITL"` dropped.
- **Symlinked-lib root resolution untested** (future-proofing): bats case sources the lib through a symlink from another directory and asserts kv output.
- **README omitted the `uv` requirement at gate time**; **`engineering-standards.md` `hook-modification` did not cover `src/aa_ma/{gate,enforce,grammar,plan_parsers}.py`** (extended under ADR-0009, which now says so); **`rules/aa-ma.md` still told the reader to `grep -c "Status: PENDING"`** (now: ask the gate); **`§5.3` cited three times in `gate.py`** (the fence is §5.2); **`grammar.py` docstring cited "the bash gate"** deleted in the same window; **8/4/9 narrative in code comments** trimmed to "see ADR-0009" in `gate.py`, `aa-ma-parse.sh` and the §6.7 preamble; **`(3 lines)` / `(42 such blocks)` live counts** removed from `enforce.py`; **`--step` missing from the launcher docblock**; **`bats_require_minimum_version 1.5.0`** added (BW02 silenced).
- **Count claims in 5.2/5.7 Result Logs** (future-proofing): "33 cases" → 40; "516 → 300" → 563 → 290; "40 → 10" → 36 → 10; "161 (was 167)" → recursive count, 187 immediately pre-rewrite. Corrected in place with the measuring command; provenance CORRECTION entry appended.

## Acknowledged, not changed (with reason)

- Exit-code meanings appear in ~10 places (future-proofing W). Bash consumers all use `*)` so a new code fails closed; the prose copies in the command/skill files were reduced to "codes per `aa-ma-gate --help`" where they were lists, but the `case` arms necessarily name them. Accepted.
- Library resolution loop repeated in §5.2, §6.7, §7.1, verify-impl and plan-verification (both reviewers). Deliberate after C3: each fence must be runnable in a fresh shell, and a shared bootstrap file would itself need resolving. Recorded in ADR-0009.
- `uv run --project` may sync the forge `.venv` while gating a consumer repo (code-reviewer INFO). `--no-sync` would turn a missing venv into a 127 on first use; auto-sync is the documented toolchain behaviour. Accepted.
- `Block.heading` in grammar.py (INFO): `Block` is unpacked positionally in `tui/parser.py`; adding a field is a TUI change outside M5. `_heading` is a trim, pinned by parity. Deferred.
- ESC in a heading reaches the terminal unescaped (security INFO): cosmetic; titles are already refused for C0 controls including ESC (`\x1b` is in the refused range), so this is now closed as a side effect of C2.
- `docs/spec/aa-ma-specification.md` line pointers to §6.7/§7.1 were stale before M5 (INFO). Not touched — a line-number pointer into a living file is the drift surface; a follow-up should replace them with heading anchors.
- Sourcing `aa-ma-parse.sh` from the *current* repo first is pre-existing RCE-by-design if the clone ships `claude-code/hooks/lib/` (security INFO). Noted in ADR-0009's "only tasks.md is untrusted" premise; out of window.
- `- Decision: REJECTED` beneath a `GATE APPROVAL:` heading still satisfies §7.1 (security INFO, pre-existing). Out of window; worth a follow-up.

## User Override Decisions

None required — no CRITICAL was disputed or deferred; all four were accepted and fixed before this report was written.
