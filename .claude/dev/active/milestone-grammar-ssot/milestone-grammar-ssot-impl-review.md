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
