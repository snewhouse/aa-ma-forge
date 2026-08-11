# milestone-grammar-ssot Tasks (HTP)

Field format is load-bearing — see `reference.md` "Field format tasks.md MUST use".
`Audit-Profile` must be own-line and unbackticked; `Critical-Path` must be own-line and bold.
Headings use the canonical form this plan enforces (`## Milestone N:` / `### Sub-step N.N:`).

## Milestone 1: Shared grammar, type fix and TUI rewire

- Status: COMPLETE
- Gate: HARD
- Mode: AFK
- Dependencies: None
- Complexity: 60%
- **Critical-Path:** data-xform
- Audit-Profile: code-only
- New-Tests: 35
- Acceptance Criteria: plan §3 M1 acceptance 1-9
- Result Log: COMPLETE. 819 passed / 0 failed (783 baseline + 1 repaired + 35 new). Corpus 44→65 milestones, 94→368 steps; 4 previously-blind tasks restored, zero tasks report 0 milestones. §6.8 found 6 CRITICAL (model-wide coercion, nested-fence phantoms, HTML-comment phantoms, unsatisfiable bats count, self-invalidating suite total, 15th-task table drift) — all fixed inline; security audit refuted the suspected ReDoS and found a real O(n²) fence scan (78KiB→5.15s), fixed by a CommonMark line scanner. Verdict PASS_WITH_WARNINGS.

### Sub-step 1.0: Confirm baseline reproduces

- Status: COMPLETE
- Mode: AFK
- Action: `uv sync`; `uv run pytest --tb=short -q` must report `783 passed, 1 failed, 1 skipped, 7 deselected` with the single failure being the corpus-grandfathering sole-dev-merge param. Confirm the 14-row table in `reference.md` reproduces via `aa-ma-tui --root .claude --json --include-completed`.
- Result Log: Baseline reproduced exactly: `783 passed, 1 failed, 1 skipped, 7 deselected`; failure is the corpus-grandfathering sole-dev-merge param as predicted. 14-task corpus table matches reference.md row-for-row.

### Sub-step 1.1: RED — write tests/test_grammar.py

- Status: COMPLETE
- Mode: AFK
- Action: 26 cases — 15 positive (5 milestone variants incl. `2a`; keywords `Sub-step`/`Step`/`Task`; 7 number shapes `N.N`, `N.N.N`, `N.NN`, `N.Na`, `N.N.bis`, `MN.N`, `MNa.N`), 9 negative (`## Summary Counts`, `## Notes`, `## Milestone Gate Types`, `## 2024 — Retro`, `### Result Log`, `### Step: no number`, `#### Step 1.1:`, fenced-code-block heading, `### Step 1.1-alpha:`), plus `group(0)` no-newline and `discover_tasks` no-crash. Negatives assert against `split_milestones()`/`split_steps()`, not the raw regexes.
- Result Log: RED confirmed — `ModuleNotFoundError: No module named 'aa_ma.grammar'`. 30 cases written (15 positive, 9 negative, group(0), discover_tasks no-crash, case-count pin, 3 splitter contract tests).

### Sub-step 1.2: GREEN — src/aa_ma/grammar.py

- Status: COMPLETE
- Mode: AFK
- Action: `MILESTONE_RE`, `STEP_RE`, `strip_fenced_blocks`, `split_milestones`, `split_steps` returning `list[Block]` where `Block = tuple[str, str, str]`. Separator `(?::|[ \t]+[–—-][ \t]+)` — the bare hyphen is excluded deliberately. Line ends `[ \t]*$`, never `\s*$`. Block runs from match start to next match start or EOF; preamble discarded.
- Result Log: GREEN — `src/aa_ma/grammar.py` (MILESTONE_RE, STEP_RE, strip_fenced_blocks, split_milestones, split_steps, Block). 30/30 pass. Declared New-Tests was 26; actual 30 — corrected in this file so the suite gate stays honest.

### Sub-step 1.3: Milestone.number int → str

- Status: COMPLETE
- Mode: AFK
- Action: `model.py:190` `number: str`; add `coerce_numbers_to_str=True` to the ConfigDict at `model.py:188`; drop `int()` at `parser.py:172` and fix the annotation at `parser.py:168`.
- Result Log: `model.py`: `Milestone.number: int -> str`, `coerce_numbers_to_str=True` added to ConfigDict, `SCHEMA_VERSION` 1 -> 2 with v2 rationale in the docstring. `int()` cast dropped at parser.py:172, annotations now `Block`.

### Sub-step 1.4: Rewire parser.py to grammar.py

- Status: COMPLETE
- Mode: AFK
- Action: import `MILESTONE_RE`/`STEP_RE`/splitters; delete `_MILESTONE_RE`/`_STEP_RE`; update docstrings at `:5-7` and `:22-24`; keep the word "Milestone" in the `ParseError` at `:271`.
- Result Log: `parser.py` imports `Block, split_milestones, split_steps` from `aa_ma.grammar`; `_MILESTONE_RE`/`_STEP_RE` deleted; `_split_*` are thin delegations; module docstring lines 5-11 rewritten; ParseError at :262 still contains 'Milestone' (test_parser.py:199-202 asserts on it).

### Sub-step 1.5: SCHEMA_VERSION 1 → 2 and its assertions

- Status: COMPLETE
- Mode: AFK
- Action: bump `model.py:141`; update `test_json_output.py:39`, `test_integration.py:117`, `test_main_dispatch.py:102`; fix docstring `json_output.py:8`; update `docs/adr/0007-aa-ma-tui-tracker.md:161,184`; CHANGELOG breaking entry.
- Result Log: SCHEMA_VERSION assertions updated at test_json_output.py:39, test_integration.py:117, test_main_dispatch.py:102 (+ the :36 docstring). `json_output.py:8` docstring -> 2. ADR-0007:161,184 annotated. CHANGELOG gained a BREAKING section.

### Sub-step 1.6: Fix comparison sites and regenerate the golden

- Status: COMPLETE
- Mode: AFK
- Action: `test_parser_properties.py:152` and `test_parser.py:242` compare against ints — coercion does not help. Regenerate `tests/tui/snapshots/data.json`.
- Result Log: Comparison sites fixed: test_parser.py:31 (`== "1"`), test_parser_properties.py:152 (`str(exp["number"])`). Golden `tests/tui/snapshots/data.json` regenerated (4891 bytes, schema_version 2).

### Sub-step 1.7: Rewire the corpus test

- Status: COMPLETE
- Mode: AFK
- Action: import `split_milestones` in `test_corpus_grandfathering.py`; delete private `_split_milestones`; add the missing `assert milestones` at `:80`.
- Result Log: `test_corpus_grandfathering.py` imports the shared `split_milestones`; private `_split_milestones` deleted; missing `assert milestones` added at :60. **The originally-failing param now passes** — 29/29 green.

### Sub-step 1.8: bats case for aa-ma-parse.sh

- Status: COMPLETE
- Mode: AFK
- Action: pin only that `aa_ma_extract_active_milestone` returns `Milestone 1 — Pre-flight + scope-aware CI checks` rc 0 on the em-dash fixture. Do NOT pin its over-tolerance.
- Result Log: Added `aa_ma_extract_active_milestone reads an em-dash milestone heading` to tests/hooks/aa-ma-parse.bats. Pins only the em-dash behaviour; the helper's over-tolerance is explicitly NOT pinned, with a comment saying why.

### Sub-step 1.9: Verify and gate

- Status: COMPLETE
- Mode: HITL
- Action: run all 9 acceptance criteria including `uv run pytest -m slow tests/tui/ -q` and `bats -F tap --recursive tests/hooks/` (119 ok). Write `IMPACT_ANALYSIS` and `CRITICAL_PATH_REVIEW — data-xform` to provenance. HARD gate approval in context-log.
- Result Log: All 9 acceptance criteria verified — see the milestone Result Log. AC4's grep needed tightening to `\b_split_milestones\b`: the loose form matched the test *name* `test_split_milestones_returns_...`. Impact analysis (MEDIUM) and CRITICAL_PATH_REVIEW — data-xform written to provenance.log.

## Milestone 2: Strict writer, canonical Sub-step

- Status: COMPLETE
- Gate: SOFT
- Mode: AFK
- Dependencies: Milestone 1
- Complexity: 35%
- Audit-Profile: code-only
- New-Tests: 22  <!-- 1 active plan + 1 fixture meta + 1 non-vacuity + (11 writers x 2 checks) -->
- Acceptance Criteria: plan §3 M2 acceptance 1-4

### Sub-step 2.1: Malformed fixture

- Status: COMPLETE
- Mode: AFK
- Action: `tests/fixtures/canonical/malformed-task/malformed-task-tasks.md` with `## M1: x`, `## Milestone M2: x`, `## Milestone 3 — x`, `### Task 1.1: x`.
- Result Log: Created `tests/fixtures/canonical/malformed-task/malformed-task-tasks.md` with one heading per observed drift style (`## M1:`, `## Milestone M2:`, `## Milestone 3 —`, `### Task 1.1:`) plus a canonical milestone, a canonical sub-step and a `## Summary Counts` prose heading as negative controls.

### Sub-step 2.2: Canonical lint

- Status: COMPLETE
- Mode: AFK
- Action: `tests/test_active_plans_canonical.py` with `CANONICAL_M` / `CANONICAL_S`, scanning `.claude/dev/active/**/*-tasks.md`, excluding `.worktrees/`. Two tests: clean pass, and a meta-test asserting the fixture yields exactly 4 violations.
- Result Log: RED confirmed (`ImportError: find_non_canonical`). GREEN: `CANONICAL_MILESTONE_RE`, `CANONICAL_STEP_RE` and `find_non_canonical()` added to `grammar.py` so one module owns both the tolerant reader and the strict writer form. Candidate selection per reference.md: a line is a candidate only if the tolerant grammar matches it, a violation only if it is not also canonical.

### Sub-step 2.3: Fix rules/aa-ma.md

- Status: COMPLETE
- Mode: AFK
- Action: `claude-code/rules/aa-ma.md:78` `### Task 1.1:` → `### Sub-step 1.1:`. Note the file is symlinked live by `scripts/install.sh:284` — the change is immediate for all sessions.
- Result Log: **Scope expanded from 1 file to 5.** The §6.8 review flagged that fixing only `rules/aa-ma.md` would leave the scribe emitting `### Step N.M:` — a form the new lint forbids. Survey found FIVE writers disagreeing: `rules/aa-ma.md:78`, `agents/aa-ma-scribe.md:148,153,163`, `commands/aa-ma-plan.md:748,752`, `skills/aa-ma-plan-workflow/references/PHASE_5_ARTIFACT_CREATION.md:223`, `docs/templates/plan-template.md:150`. Only `docs/templates/tasks-template.md` was already canonical. All five fixed. Note `claude-code/` files are symlinked live by install.sh:284 — effective immediately for every session, no reinstall.

### Sub-step 2.4: Verify this plan's own artifacts pass

- Status: COMPLETE
- Mode: AFK
- Action: run the lint against `.claude/dev/active/milestone-grammar-ssot/`. Revision 2 of this plan would have failed here.
- Result Log: This plan's own tasks.md returns zero violations. Added `test_shipped_writers_emit_canonical_headings`, parametrized over all 5 writer templates, so writer↔linter divergence cannot silently return — that recurrence was the actual risk, not the one-off fix. New-Tests 2 → 7.

## Milestone 3: Fix the flaky C4 test

- Status: COMPLETE
- Gate: SOFT
- Mode: AFK
- Dependencies: None
- Complexity: 55%
- Audit-Profile: code-only
- **Prototype-Required:** YES
- New-Tests: 1  <!-- was 0; §6.8 found the new shipped branch had zero coverage -->
- Acceptance Criteria: plan §3 M3 acceptance 1-5
- Result Log: COMPLETE. 5/5 acceptance criteria verified. The named hypothesis (SLUG collision) was **refuted by measurement** before any fix was written; the real cause is an unguarded dependency on the `shellcheck` binary, reproduced deterministically by substitution rather than by waiting for a recurrence. The flaky test turned out to be the visible symptom of a shipped false negative: `|| true` let Stage C report "0 findings" for shell code it never scanned. Fixed in the command, in the test, and in CI. §6.8 then found the first fix was half a fix — the WARNING went to stdout only, leaving `$FINDINGS` (the artefact Stage D actually reads) byte-identical to a clean scan, and `command -v` caught only 1 of 4 degraded modes. Both closed, plus a fifth mode found while re-verifying. Final soak **20/20 at `ok=70 notok=0 skip=0`**; `/tmp` leak 29 → 0. Scope reduction declared: `BATS_TEST_TMPDIR` re-pathing dropped with the hypothesis that motivated it. Deferred to user: C3/bandit carries the identical defect.

### Sub-step 3.1: Reproduce the flake

- Status: COMPLETE
- Mode: AFK
- Action: `Skill(systematic-debugging)`. Run the suite in a loop until C4 fails; capture the failing output. shellcheck is present (0.11.0) — the missing-binary theory is already disproven.
- Result Log: REPRODUCED, but not by looping. A 25-run loop with `shellcheck` on PATH produced 0 failures, which is itself the finding: the flake is not resident in the test's own state. Reproduced deterministically instead by removing **only** `shellcheck` from PATH (shadow dir of symlinks to /usr/local/bin + /usr/bin + /bin minus shellcheck, so git/grep/python3 stay resolvable). Signature matches the reported failure exactly: `not ok 1 C4 maps ShellCheck error to [CRITICAL]` … `line 147: [[ "$FINDINGS" == *"[CRITICAL]"* ]] || [[ "$FINDINGS" == *"[HIGH]"* ]]' failed`. Mechanism: `sole-dev-merge.md:362` runs `shellcheck -f json $CHANGED_SH > "$SHELLCHECK_OUT" 2>/dev/null || true`; absent binary → empty file → `[[ -s ]]` false → zero findings → opaque assertion failure instead of a skip. With shellcheck present the tool output is deterministic (`info SC1009`, `error SC1073/SC1080/SC1072` → 3 × CRITICAL), so there is no ambiguity on the happy path. Note: `python3` at `sole-dev-merge.md:344,364` is a second unguarded dependency with the identical silent-swallow signature.

### Sub-step 3.2: Test the SLUG-collision hypothesis

- Status: COMPLETE
- Mode: AFK
- Action: `test_stage_c_dispatch.bats:30` builds `SLUG="bats-$$-$(date +%s%N | tail -c 6)"`; three files share `/tmp/sole-dev-merge-shellcheck-${SLUG}.json`. Confirm or refute before fixing.
- Result Log: **REFUTED — measured, not reasoned.** Built a 2-file / 10-test probe replicating the SLUG derivation verbatim under `bats@1.11.0 --recursive`. Every `setup()` observed a *distinct* `$$` (612456, 612463, 612470, 612477, 612484, 612526, 612557, 612581, 612589, 612596): bats forks a fresh subshell per **test**, not per file, so the PID component alone guarantees uniqueness. Duplicate SLUGs across the run: **0**. A collision would additionally require PID reuse *and* a matching 5-digit nanosecond suffix inside one run. The shared `/tmp` path is therefore not the flake. Recorded as a finding, not a failure, per plan §3 M3 acceptance 5. Sub-step 3.3 still proceeds — a real cleanup leak was found independently (see 3.3).

### Sub-step 3.3: Isolate temp state

- Status: COMPLETE
- Mode: AFK
- Action: unique path per test under `BATS_TEST_TMPDIR`; fix the cleanup leak across all three files.
- Result Log: COMPLETE, with a **deliberate scope reduction** — flagged, not silent. The leak is real and fixed; the `BATS_TEST_TMPDIR` re-pathing is not done. Measured leak: after 25 suite runs, `ls /tmp/sole-dev-merge-* | wc -l` = **29**, all `reviewer-notes-*`. Cause: `test_stage_c_dispatch.bats` and `test_stage_d_triage.bats` each enumerated the same five filenames in teardown, and Stage D later grew a sixth (`sole-dev-merge.md:477` writes `reviewer-notes`) that no teardown learned about. Fixed with `sweep_slug_tmp` in `fixtures/helpers.bash` — a `"/tmp/sole-dev-merge-"*"-${SLUG}."*` glob guarded on non-empty `SLUG`, so it cannot fall behind a new writer and cannot widen to another run's files. Why the re-pathing was dropped: the aggregator hardcodes `/tmp/…` at `sole-dev-merge.md:288-293`, so honouring `BATS_TEST_TMPDIR` means changing shipped path semantics plus every test that asserts a `/tmp/` path. The only justification for that was the SLUG-collision risk, which 3.2 refuted. None of M3's five acceptance criteria requires it; #3 requires the leak be zero, which the sweep delivers.

### Sub-step 3.4: Skip guard and binary indirection

- Status: COMPLETE
- Mode: AFK
- Action: `SHELLCHECK_BIN="${SHELLCHECK_BIN:-shellcheck}"` plus the guard pattern reused from `tests/hooks/security-static-check.bats:248-251`.
- Result Log: COMPLETE — and the shipped-code half is the more important one. `sole-dev-merge.md` C4 now resolves `SHELLCHECK_BIN="${SHELLCHECK_BIN:-shellcheck}"` and, when the binary is unresolvable, prints `Stage C: WARNING — '<bin>' not found; C4 did not run. Shell findings are UNKNOWN, not zero.` instead of letting `|| true` launder a missing scanner into a clean report — a false negative in a security stage, not merely a test annoyance. Test guard mirrors `security-static-check.bats:248-251` and resolves through the same env var. **Both halves proven, not assumed** — running the extracted aggregator directly: binary present → `4 findings`, 3 × `[CRITICAL]`; `SHELLCHECK_BIN=/nonexistent/shellcheck` → WARNING emitted, `0 findings`, findings file 0 lines. Had the shipped code ignored the env var, the test would have skipped while the code still ran, and the guard would have been a lie. AC#2 verified: `SHELLCHECK_BIN=/nonexistent/shellcheck` over the file exits **0** with exactly **1** `# skip`, naming C4. Extracted script passes `bash -n` and `shellcheck -S warning` clean.

### Sub-step 3.5: CI install step

- Status: COMPLETE
- Mode: AFK
- Action: add `apt-get install -y shellcheck` to the **bats** job in `.github/workflows/security.yml`; verify with the coreutils awk extractor (0 before, 1 after).
- Result Log: COMPLETE. Step `Install shellcheck (required by Stage C / C4)` added to the `bats:` job after `bats-core/bats-action@4.0.0`. AC#4 awk extractor scoped to the `bats:` block: **0 before, 1 after**, measured both sides. Leakage control also run — the same extractor scoped to the standalone `shellcheck:` job returns **0**, so the count is not borrowed from that job. `ubuntu-latest` does ship shellcheck today, which is exactly why the step is needed now that 3.4 makes C4 *skip* on absence: an image change would otherwise turn a security assertion green-by-skipping rather than red. YAML re-parsed after the edit (`bats` job = 5 steps); `pyyaml` turned out to be importable here, but the acceptance assertion remains coreutils-only as specified.

### Sub-step 3.6: 20-run soak

- Status: COMPLETE
- Mode: AFK
- Action: 20 consecutive `bats -F tap --recursive tests/commands/sole-dev-merge/` — 69 ok, 0 not-ok, every run. Write `PROTOTYPE — <verdict>` to provenance. Record root cause in context-log.
- Result Log: COMPLETE. Run twice — the first soak (20/20, `ok=69 notok=0 skip=0`) validated code that §6.8 then changed, so it was re-run against the final tree: **20/20 at `ok=70 notok=0 skip=0`**, `/tmp` cleared beforehand. **`skip=0` is the load-bearing number** — it proves C4 actually executed all 20 times rather than the new guard quietly converting a red test into a green skip, which is the obvious way this fix could have faked its own success. Leftovers after the 20 runs: **0** (29 before the sweep), closing AC#3. Plus a 25-run pre-fix loop at 0 failures, establishing that the flake was never resident in the test's state. `PROTOTYPE — hypothesis REFUTED, root cause found by substitution` written to provenance; root cause in context-log per AC#5.

## Milestone 4: Close the HARD-gate scan blindness

- Status: BLOCKED
- Blocked-By: Milestone 5 — M4's acceptance is genuinely unmet and its remaining scope (4.10-4.15) is superseded by M5. BLOCKED rather than an invented status value: it is canonical in `MilestoneStatus`, and it leaves exactly one ACTIVE milestone once M5 starts, which the strict derivation requires.
- Gate: HARD
- Mode: HITL
- Dependencies: Milestone 1
- Complexity: 45%
- **Critical-Path:** hook-modification
- Audit-Profile: infra
- New-Tests: see Summary Counts — this milestone's test count is derived, not declared. Declared 0 at planning; the plan assumed the scans only needed a regex widened.
- Acceptance Criteria: plan §3 M4 acceptance 1-3

### Sub-step 4.1: RED — failing bats per scan point

- Status: COMPLETE
- Mode: AFK
- Action: fixtures using `## M1:` and `## Milestone 1 —`, each with one sub-step whose status field is the pending value, plus a `- **Critical-Path:** data-xform` line. Assert every scan finds them. Currently returns empty. (Deliberately avoids writing the literal pending-status string here — the HARD gate greps for it and would count a prose mention as a real pending sub-step.)
- Result Log: RED confirmed — **17 fail / 2 pass** in `tests/hooks/aa-ma-gate-scans.bats` (19 cases) against `tests/hooks/fixtures/gate-scans/styles-tasks.md` (4 heading styles + 2 prose negative controls). The two passes are legitimate: the vacuity meta-test and `bash -n`. **The diagnosis in the plan was wrong, and understated.** The scans are not merely blind to `## M1:` / em-dash styles — they return nothing for *any* style, canonical included: `awk "/^## Milestone.*$T/,/^## Milestone/"` **self-terminates**, because the start line also matches the end pattern and awk evaluates the end pattern on the same record. Measured on this plan's own tasks.md: 1 line returned, `0` pending where 6 exist, `Critical-Path` empty on a milestone that declares it. Separately, `grep -A1 "## Milestone.*$T" | grep -oP 'Gate: \K\w+'` returns the heading plus a blank line, so `GATE` is always empty and **§7.1 has never enforced a HARD gate**. Fifth defect found: `verify-impl/SKILL.md:57` uses `\s`, a GNU extension mawk does not support — measured 0 lines under mawk (Debian/Ubuntu default awk), i.e. an empty milestone block, silently.

### Sub-step 4.2: Align the gate scans

- Status: COMPLETE
- Mode: AFK
- Action: `execute-aa-ma-milestone.md:504,518,529,692` and `verify-impl/SKILL.md:57` to an ERE equivalent of `MILESTONE_RE`.
- Result Log: COMPLETE — 20/20 green (was 2/19). Rather than repeat an ERE in five places, added `aa_ma_extract_milestone_block()` + `AA_MA_MILESTONE_ERE` to `claude-code/hooks/lib/aa-ma-parse.sh` (**additive only** — no existing function touched) and rewired all four `execute-aa-ma-milestone.md` scan points to it via `MILESTONE_BLOCK`. Same move M1 made on the Python side: one bash-side grammar, one test surface. `verify-impl/SKILL.md:57` keeps its own range but `\s` → `[[:blank:]]`; verified 3 lines under **both** gawk and mawk (was 0 under mawk). **Start/end conditions are asymmetric and that is the fix**: opens only on a milestone heading, closes on **any H2**. Closing on milestone headings only looked symmetric and was wrong — the last milestone then ran to EOF and swallowed `## Summary Counts`, whose prose contains literal `- Status: PENDING`, `- Gate: HARD` and a Critical-Path line. Caught by the fixture's negative controls, and it is not hypothetical: `## Summary Counts` follows the last milestone in this plan's own tasks.md. Portability choices measured, not assumed: `[[:blank:]]` not `\s` (mawk), `[.]` not `\.` (gawk warns then treats it as "any char"), `(-|–|—)` not a bracket class (multibyte). Mutation-verified both ways — reverting the end condition fails 2 cases, removing the empty-title guard fails the fail-closed case. Full suites: hooks bats **139 ok / 0 not ok**, pytest 842 passed, shellcheck clean.

### Sub-step 4.3: Add CANONICAL_CRITICAL_PATHS

- Status: COMPLETE
- Mode: AFK
- Action: add the 6-value constant to `plan_parsers.py` — it does not exist, so the check is manual-only today.
- Result Log: COMPLETE — `CANONICAL_CRITICAL_PATHS` **plus `parse_critical_path()`**, because a constant nothing consumes is a guard that can never fire (L-1214). The parser is a thin reuse of `_parse_canonical_field`; `_extract_field` already tolerated the bold form, so no regex change was needed. 15 new tests in `tests/codemem/test_critical_path_parser.py`, of which three matter more than the happy path: `test_enum_matches_engineering_standards_table` scrapes the rule file and asserts the code constant is a subset — drift between the two is the exact silent-divergence failure this milestone exists to close, one layer up; `test_scrape_is_not_vacuous` pins the scrape at >=6 rows so an empty scrape cannot make the previous test pass trivially; and `test_this_plans_own_milestones_all_parse` dogfoods against the live tasks.md, asserting >=1 milestone parsed first. Backticked and wrong-case values are both rejected, matching the Audit-Profile precedent — a backticked value is what silently broke this plan's own artifacts during planning. Suite 842 → **857 passed**.

### Sub-step 4.4: Widen hook-modification scope

- Status: COMPLETE
- Mode: AFK
- Action: `claude-code/rules/engineering-standards.md` currently scopes `hook-modification` to `claude-code/hooks/*.sh`; widen to cover shipped commands and skills, or this milestone's own Critical-Path value reads as a violation.
- Result Log: COMPLETE. `hook-modification` now reads "the shipped enforcement surface: `claude-code/hooks/**` (incl. `lib/`), and the gate/scan logic inside `claude-code/commands/**` and `claude-code/skills/**`". Verified against this milestone's own diff — all four changed `claude-code/` paths (`hooks/lib/aa-ma-parse.sh`, `commands/execute-aa-ma-milestone.md`, `skills/verify-impl/SKILL.md`, `rules/engineering-standards.md`) now fall inside the declared scope, where under the old wording only the first did. The `**` in the widened text also covers `hooks/lib/`, which the old `hooks/*.sh` glob excluded — the very file this milestone changed. Row keeps its backticked-token-in-leading-cell shape so `test_enum_matches_engineering_standards_table` still scrapes it.

### Sub-step 4.5: Verify and gate

- Status: COMPLETE
- Mode: HITL
- Action: `bats -F tap --recursive tests/hooks/` green; `Skill(impact-analysis)` with HIGH findings resolved; `CRITICAL_PATH_REVIEW — hook-modification` in provenance; HARD gate approval in context-log.
- Result Log: COMPLETE. hooks bats **147 ok / 0 not ok**, sole-dev-merge bats **70 ok / 0 skip**, pytest **864 passed**, shellcheck clean, ruff clean. §6.8 (`Audit-Profile: infra`) dispatched code-reviewer + security-auditor + future-proofing-auditor: **17 raw CRITICAL → 8 distinct, all fixed**, plus ~20 WARNINGs actioned. The review found my first M4 fix was *still* inert — `MILESTONE_TITLE` is assigned 347 lines after the gate consumes it, so the extractor got an empty title and every condition passed on empty input. My own dogfood check had set the variable by hand, so it verified the helper and not the shipped path. Also fixed: bold `- **Status:**`/`- **Gate:**` forms (22+24 in corpus, and the shipped Phase 5 writer emits them); substring title matching; fenced/multi-line-comment ghost headings truncating blocks; fail-open rc (now 0/1/2/3, callers refuse on all non-zero); `verify-impl`'s `$((N+1))` bash error on `2a`/`3.5`; file-global provenance greps; BRE title injection in the approval check; mixed-case `Gate:`. Four pre-existing dead `!` assertions elsewhere in the suite (POSIX exempts `! cmd` from `set -e`) repaired — two of them asserted a security vulnerability had been removed and could never fail. New guards: `tests/test_grammar_parity.py` pins the shell ERE against `grammar.py` (mutation-verified: dropping `|M` fails 6/7) and an Exports-header drift test in `aa-ma-parse.bats`, which immediately caught a symbol I had added minutes earlier and not documented.

### Sub-step 4.6: Refuse an ambiguous milestone derivation

- Status: COMPLETE
- Mode: AFK
- Action: 4.5 fixed the unset-`MILESTONE_TITLE` defect by wiring the gate to `aa_ma_extract_active_milestone`, the loosest grammar in `aa-ma-parse.sh` — which takes the *first* match and cannot signal ambiguity. Measured: with a stale second milestone left ACTIVE the gate derives the wrong milestone and reports `PENDING=0 GATE=SOFT` for a milestone that is 1 PENDING / `Gate: HARD` — a silent **false PASS**, the one direction none of this milestone's other defects could produce. Add a derivation that returns exactly-one-ACTIVE or refuses (rc 1 none / rc 3 many), and switch `execute-aa-ma-milestone.md` §6.7 to it.
- Acceptance Criteria: two ACTIVE milestones → gate exits non-zero naming both; zero ACTIVE → exits non-zero; exactly one → unchanged behaviour. Mutation-verified: reverting the derivation re-fails the ambiguity case.
- Result Log: COMPLETE. Added `aa_ma_active_milestone_strict` (rc 0 one / 1 none / 2 unreadable / 3 many, printing **all** ACTIVE headings on rc 3) and switched the §6.7 preamble to it. Only the milestone's **own** `Status:` counts — fields between the `##` heading and the first `###` — because a sub-step left ACTIVE is normal mid-milestone and would otherwise make its parent a candidate and two milestones look simultaneously active. **Dogfooded through the shipped text, not a hand-set variable**: the §6.7 preamble was extracted verbatim from the command file (47 lines) and run against four task dirs — `two-active` → exit 1 naming both milestones; `no-active` → exit 1; `one-active` → exit 0; the live plan → exit 0 `Milestone 4: Close the HARD-gate scan blindness`. That indirection is the whole lesson of 4.5, where a by-hand probe verified the helper and not the shipped path. **Mutation-verified**: swapping `aa_ma_active_milestone_strict` back to the tolerant reader and deleting the `case` reproduces the false PASS exactly — derives `Milestone 2: Older milestone left ACTIVE`, measures `PENDING=0 GATE=SOFT`, exit 0, on a fixture whose real subject is `PENDING=1 GATE=HARD`. 9 new bats cases, of which 8 went RED and one (`tolerant reader still finds a real milestone`) passed pre-fix as the non-breaking guard — RED 8 fail / 28 pass → GREEN 36/36. (Originally written as "8 new bats cases"; corrected in 4.15 after the §6.8 future-proofing agent measured the file at 27→36 across the window.)


### Sub-step 4.7: One milestone grammar in aa-ma-parse.sh

- Status: COMPLETE
- Mode: AFK
- Action: `aa_ma_extract_active_milestone` still opens a block on bare `/^## /` — the third grammar in a file whose whole purpose after M1 is to hold one. It is the root cause of 4.6: measured returning `Summary Counts` as the active milestone on a plan with trailing prose. Rewire it to `aa_ma_is_milestone_heading`. Blast radius is real and must be measured, not assumed: the function is also read by `aa-ma-session-start.sh`.
- Acceptance Criteria: a corpus-wide old-vs-new diff is recorded in the Result Log with every changed row explained; prose H2s no longer returned; `aa-ma-parse.bats` still green; the session-start hook still reports a milestone for every active plan in the repo.
- Result Log: COMPLETE. `aa_ma_extract_active_milestone` now opens a block via `AA_MA_MILESTONE_ERE` + non-empty-title, matching `aa_ma_is_milestone_heading`; a non-milestone H2 closes the current block instead of opening one. **Measured before changing anything**, old vs new across all 27 tasks files in the repo: **exactly one row differs** — `tests/tui/fixtures/tasks/agent-token-optimization`, `Step 7: Verify & Commit` → empty. Decisive follow-up: `grammar.py::MILESTONE_RE` matches **0 of that fixture's 9 H2 headings**, so the bash function was the only thing in the codebase treating `## Step N:` as a milestone. The change makes bash agree with the Python SSoT rather than losing information — M1's thesis, one layer down. Sole non-test caller `aa-ma-session-start.sh:55` already degrades to `"unknown"` on empty, and was run live for real evidence rather than reasoned about: it still prints `milestone=[Milestone 4: Close the HARD-gate scan blindness]`. Full suites after both sub-steps: hooks bats **157 ok / 0 not ok** (was 148), commands bats **70 ok / 0 skip**, pytest **864 passed / 1 skipped**, shellcheck clean, `ruff check` clean.

### Sub-step 4.8: Close the same defect in the step extractor

- Status: COMPLETE
- Mode: AFK
- Action: `aa_ma_extract_active_step` opens a block on `/^### /` and **never closes on `^## `**, so the first `Status: ACTIVE` awk sees after the last sub-step of milestone N is milestone N+1's own milestone-level status line — and it is attributed to that trailing sub-step. Reset `current` on any H2. Found while verifying 4.7 and initially deferred as display-only; that was wrong — `pre-compact-aa-ma.sh:89` feeds it into the `CHECKPOINT — ActiveStep:` line in provenance.log, which `rules/aa-ma.md` designates as the session-resume signal.
- Acceptance Criteria: a milestone-level ACTIVE status is never attributed to the preceding milestone's last sub-step; the existing PENDING-fallback test still passes; both callers (`aa-ma-session-start.sh`, `pre-compact-aa-ma.sh`) run live and report a defensible step. Mutation-verified: removing the reset re-fails the new case.
- Result Log: COMPLETE. One awk rule — any `^## ` resets `current` — restores the invariant that a sub-step block ends at the next H2. **Three RED cases, all three fixed**, and the second was a surprise: a genuinely `Status: ACTIVE` sub-step was *also* unreachable, because awk exits on the first ACTIVE it sees and the next milestone's own status line came first. So the function could never return an ACTIVE step that followed a completed milestone at all. **Corpus-wide old-vs-new diff, all 27 tasks files: 6 rows change, every one a correction, zero regressions.** Live plan `Sub-step 3.6: 20-run soak` (COMPLETE, M3) -> `Sub-step 4.8` (the real PENDING step); `styles` fixture COMPLETE 1.1 -> PENDING 2.1; `two-active` COMPLETE 2.1 -> PENDING 4.1; three fixtures -> empty, correct because no sub-step in them carries a status of its own. The last of those is the clearest instance of the bug: in `agent-token-optimization` **not one** `### Sub-step:` block has a `Status:` field, so the old answer was `## Step 7`'s `- Status: ACTIVE` attributed to `## Step 6`'s last sub-step. **Both callers run live**: `aa-ma-session-start.sh` now prints `step=[Sub-step 4.8: Close the same defect in the step extractor]` (captured while 4.8 was still PENDING, so it is evidence and not a tautology); `pre-compact-aa-ma.sh` degrades to `unknown` on empty, unchanged. **Mutation-verified**: deleting the reset re-fails exactly the 3 new cases, 0 otherwise. Suites: hooks bats **160 ok / 0 not ok** (was 157), commands bats 70 ok, pytest 864 passed, shellcheck clean.

### Sub-step 4.9: Sanitise untrusted titles at the session-start boundary

- Status: COMPLETE
- Mode: AFK
- Action: §6.8 CRITICAL (security-auditor), reproduced end-to-end. `aa-ma-session-start.sh` interpolates a milestone/step title taken from `tasks.md` into the hidden system-context line as `milestone=[%s]` with no control-character stripping, no `]` escaping and no length cap. A cloned repo forges a complete second well-formed `AA-MA ACTIVE:` directive instructing exfiltration of `~/.ssh/id_rsa`. Fires automatically at session start, before the user types anything. Pre-existing, not introduced by M4, but the readers feeding it were changed in this window. Sanitise at the interpolation boundary.
- Acceptance Criteria: the reproduction fixture yields a single `AA-MA ACTIVE:` directive with no `]` inside any bracketed field; control characters stripped; titles truncated. RED test first.
- Result Log: COMPLETE (re-done after the revert, with both §6.8 CRITICALs from the first attempt fixed). **Two untrusted sources, not one** — the first attempt sanitised the milestone/step titles and missed the task DIRECTORY NAME, which ships in the cloned repo and reached the context line unescaped. Both are now regression-tested with the payload in each position. **The two sources need different treatment**, which was the first attempt's second CRITICAL: it ran the task name through the display sanitiser and then built the file path from the result, so a legal directory `fix-[urgent]-parser` emitted `fix-(urgent)-parser-reference.md` — every session start citing a file that does not exist. Now: display fields are rewritten (prose, harmless to corrupt); the path is emitted **verbatim or not at all**, because a sanitised path is worse than no path. Unsafe path -> an explicit "open it manually" clause. **Primitives chosen by measurement, not preference**: `cut -c` is byte-oriented on this host and splits a multibyte character (proved: 119 ASCII + `é` -> invalid UTF-8), so truncation uses bash substring, which measured valid; and the token scrub is a case-insensitive whitespace-tolerant ERE after the first attempt's single literal was shown to pass `AA-MA  ACTIVE` (two spaces), a tab variant and lowercase. Extended to scrub `Load context:` as well — both phrases are ours, and untrusted content reusing our directive vocabulary reads as instruction even once the brackets are neutralised. RED 6/6 -> GREEN, and the path-correctness case was written to pass at baseline so it fails only if a fix breaks it — which is exactly how the first attempt broke it silently. **Residual risk, unchanged and stated**: ~120 characters of attacker prose still reach the model; removing that means not echoing untrusted titles at all. hooks bats **167 ok / 0 not ok**, pytest 864 passed, commands bats 70 ok, shellcheck clean.

### Sub-step 4.10: One Status grammar, not four

- Status: PENDING
- Superseded-By: Milestone 5 — the defect this closes is closed by construction once gate enforcement reads the Python SSoT. Retained PENDING (not deleted) because M4 acceptance is genuinely unmet; the Result Log below records what was measured before the revert.
- Mode: AFK
- Action: §6.8 CRITICAL (all three agents), verified. `aa_ma_active_milestone_strict` hardcodes `^-?[[:blank:]]*(\*\*)?Status:...`, strictly narrower than the library's own `_aa_ma_field_re` and than the Python SSoT `parser.py::_field_pattern`. `  - Status: ACTIVE` (blanks before the dash) is invisible to it → the rc-3 ambiguity refusal is bypassed and the gate certifies the wrong milestone: measured `PENDING=0 GATE=SOFT` where the truth is `PENDING=1 GATE=HARD`. The false PASS 4.6 exists to close, reintroduced by 4.6. Conversely `- **Status**: ACTIVE` and `- Status: **ACTIVE**` make a plan permanently un-gateable. Reuse `_aa_ma_field_re Status`; delete the fourth grammar.
- Acceptance Criteria: indented, tab-indented, split-bold-key and bold-value forms resolve identically across `aa_ma_field_value`, `aa_ma_active_milestone_strict` and the Python SSoT; pinned by a parity test.
- Result Log: COMPLETE. The fourth Status grammar is deleted, not patched: `aa_ma_active_milestone_strict` now takes `_aa_ma_field_re Status` and compares the extracted value. Introduced `_AA_MA_VALUE_NORM`, one awk prelude defining `aa_ma_norm(line, re)`, and rewired `aa_ma_field_value` and `aa_ma_count_field` to it as well — each had its own inlined `sub()`+`gsub()` copy. **Checked the prerequisite instead of assuming it**: `_aa_ma_field_re` uses `{0,2}` interval expressions and this file's own comments warn about mawk, so before adopting it I measured the full form table under both awks — 5/5 gawk, 5/5 mawk. The normaliser also strips a surrounding bold pair, which closes a second Phase 6.8 finding: `- Status: **PENDING**` never equalled `PENDING`, so the gate counted zero pending sub-steps on a milestone that had them. **The original exploit re-run now returns rc=3 naming both milestones** (was rc=0 certifying the wrong one with PENDING=0 GATE=SOFT). Parity asserted across 6 forms — plain, indented, tab-indented, split-bold key, bold key, bold value — with `aa_ma_field_value` as the reference implementation and a non-vacuity guard. RED 3/3 -> GREEN. hooks bats **166 ok / 0 not ok** (was 163), commands bats 70 ok, pytest 864 passed, shellcheck clean.

### Sub-step 4.11: Pass the title to awk byte-exact

- Status: PENDING
- Superseded-By: Milestone 5 — the defect this closes is closed by construction once gate enforcement reads the Python SSoT. Retained PENDING (not deleted) because M4 acceptance is genuinely unmet; the Result Log below records what was measured before the revert.
- Mode: AFK
- Action: §6.8 CRITICAL (security-auditor), verified. POSIX awk performs escape-sequence processing on `-v` assignments, so `aa_ma_extract_milestone_block` does not compare the bytes the derivation emitted. Measured: `strict` names `Milestone 1: a\tb` (1 PENDING, HARD) and the block scan returns `Milestone 1: a<TAB>b` (COMPLETE, SOFT) → `PENDING=0 GATE=SOFT`. Benign corollary, equally real: a milestone titled `Fix \t handling in parser` gives `strict rc=0` then `block rc=1`, so the gate blocks a valid plan citing a milestone it derived itself. Pass via `ENVIRON[]` or `ARGV`, never `-v`.
- Acceptance Criteria: titles containing `\t`, `\n`, `\\`, `\d` and `C:\dev\path` round-trip exactly; the two-milestone escape fixture refuses instead of certifying the clean one.
- Result Log: COMPLETE. `aa_ma_extract_milestone_block` now receives the title through `ENVIRON["AA_MA_TITLE"]`, which POSIX does not escape-process, instead of `-v title=`, which does. Our own literal patterns (`mre`, `sre`) stay on `-v` — they contain no backslashes, so the transformation is a no-op for them and the narrower change is the honest one. Both halves of the defect now hold: the two-milestone escape fixture keeps `Gate: HARD` / `PENDING=1` with the derivation and the block scan agreeing, and four legitimate backslash titles (`Fix \t handling in parser`, `Windows C:\dev\path`, `Escape \\ pair`, `Regex \d digit`) now round-trip instead of producing a spurious BLOCK. `ENVIRON` confirmed present under mawk as well as gawk by running the real function through a PATH shim — mawk's support was verified, not assumed, because the whole point of this sub-step is that an awk feature behaved differently than expected. RED 2/2 -> GREEN. hooks bats **168 ok / 0 not ok** (was 166), shellcheck clean.

### Sub-step 4.12: One H2 predicate, and actually call the SSoT recogniser

- Status: PENDING
- Superseded-By: Milestone 5 — the defect this closes is closed by construction once gate enforcement reads the Python SSoT. Retained PENDING (not deleted) because M4 acceptance is genuinely unmet; the Result Log below records what was measured before the revert.
- Mode: AFK
- Action: §6.8 WARNING ×2 (code-reviewer), verified. Four spellings of "is this an H2" now exist (`/^## /` ×2, `/^##[[:blank:]]/` ×2, `/^##[^#]/`). On a tab-separated `##\tMilestone 2:` the library contradicts itself: `strict` reads it correctly while `aa_ma_extract_active_step` returns `Sub-step 1.1: done` — the exact defect 4.8 claims to close — and `aa_ma_extract_active_milestone` returns the COMPLETE milestone. Separately, `aa_ma_is_milestone_heading` has **0 callers in shipped code**: 4.7's declared Action was "Rewire it to `aa_ma_is_milestone_heading`" and the implementation inlined its body as a fourth copy instead. Consolidate on `/^##[[:blank:]]/` and share one recognition body.
- Acceptance Criteria: all four call sites agree on a shared edge-case table incl. tab-separated and bare `##`; `aa_ma_is_milestone_heading` has at least one shipped caller or its removal is recorded.
- Result Log: COMPLETE. `AA_MA_H2_ERE` replaces three disagreeing spellings of "this line is an H2" (`/^## /` ×2, `/^##[[:blank:]]/` ×2, `/^##[^#]/`) and now also closes on a bare `##`. `_AA_MA_MILESTONE_AWK` gives the four readers one recognition body — `grep -c 'sub(mre, "", t)'` went 4 → **1**. The reason the shell predicate was never called is now recorded rather than left implied: a shell function cannot be invoked from inside an awk program, so 4.7's declared "rewire it" was not implementable as written; an awk prelude is the form these callers can actually share, and `aa_ma_is_milestone_heading` is now a thin wrapper over it. **I broke the suite doing this** — the block extractors referenced `h2re` before it was passed — and the tests caught it immediately: 146 ok / 25 not ok, repaired to 171 ok / 0 not ok. The tab-separated heading that defeated 4.7 and 4.8 now resolves identically in all three readers.

### Sub-step 4.13: Gate condition 1 must actually halt

- Status: PENDING
- Superseded-By: Milestone 5 — the defect this closes is closed by construction once gate enforcement reads the Python SSoT. Retained PENDING (not deleted) because M4 acceptance is genuinely unmet; the Result Log below records what was measured before the revert.
- Mode: AFK
- Action: §6.8 WARNING (code-reviewer), verified. `execute-aa-ma-milestone.md:498` ends the git-dirty branch with `# HALT`, a comment. Measured against a dirty task dir: the gate prints `BLOCKED: AA-MA artifacts have uncommitted changes.` and then `ENG-STANDARDS-GATE: PASS (all 5 conditions satisfied)` with `EXIT=0` — it contradicts itself in one run and passes. Pre-existing and identical at `f2c83bc`, but it is condition 1 of the gate this milestone hardens, twelve lines above the four real `exit 1`s added in 4.6. Replace with `exit 1`.
- Acceptance Criteria: a dirty AA-MA task dir exits non-zero with no `PASS` line.
- Result Log: COMPLETE. `# HALT` → `exit 1`, with the measurement kept in the comment so the next reader sees why a one-word change mattered. **Mutation-verified**: restoring `# HALT` fails the new dirty-task-dir case, so the guard is load-bearing rather than decorative.

### Sub-step 4.14: Tests that execute the gate, and mawk parity for the changed functions

- Status: PENDING
- Superseded-By: Milestone 5 — the defect this closes is closed by construction once gate enforcement reads the Python SSoT. Retained PENDING (not deleted) because M4 acceptance is genuinely unmet; the Result Log below records what was measured before the revert.
- Mode: AFK
- Action: §6.8 WARNING ×2 (code-reviewer + future-proofing). The guard for 4.6's fix is an exact-literal negative grep over markdown that goes green if a future edit merely adds quotes, reinstating the defect. Nothing in the suite executes the §6.7 preamble, so the `case $?` dispatch, four `exit 1` paths and the rc-3 `printf | sed` are unguarded. Separately, the mawk parity loop covers only `aa_ma_extract_milestone_block`; none of the three functions changed in this window is pinned under mawk. Replace the literal guard with behavioural execution and extend parity coverage.
- Acceptance Criteria: a bats case extracts the §6.7 fence and runs it against each fixture asserting exit status and message; mawk+gawk parity asserted for all three changed functions with the existing non-vacuity guard.
- Result Log: COMPLETE. The exact-literal grep guard is gone; four cases now **execute** the shipped §6.7 text — one-active → exit 0 with the derived title, two-active → non-zero naming both, no-active → non-zero, and a dirty task dir → non-zero with no `PASS` line. Mutation-verified in both directions: reverting the derivation to the tolerant reader fails the two-active case (the old grep would have caught that too only by exact spelling), and restoring `# HALT` fails the dirty case. mawk/gawk parity extended to all three functions changed in this window, keeping the `tested -eq 2` non-vacuity guard. **The mutation run then exposed a defect in my own new test**: it shimmed `awk` at `$BATS_TMPDIR/shim-$bin`, the same fixed path an existing test writes a wrapper script to — and since `BATS_TMPDIR` is `/tmp` here and persists between runs, the symlink made that test's `printf > $shim/awk` follow through to `/usr/bin/mawk` and die with EACCES. Three tests away from the one I was editing, and invisible in the single green run that preceded it. Fixed with `mktemp -d` plus cleanup; verified stable over three consecutive full runs and zero `/tmp/shim-*` left behind.

### Sub-step 4.15: Correct the count claims

- Status: PENDING
- Superseded-By: Milestone 5 — the defect this closes is closed by construction once gate enforcement reads the Python SSoT. Retained PENDING (not deleted) because M4 acceptance is genuinely unmet; the Result Log below records what was measured before the revert.
- Mode: AFK
- Action: §6.8 CRITICAL ×2 (future-proofing), verified. `tasks.md:260` claims M4 added 15 python / 38 bats tests; measured 22 python (10+3 defs → 22 collected under parametrisation — `grep -c '^def test_'` was the wrong metric) and 41 bats (`aa-ma-gate-scans.bats` 0→36, `aa-ma-parse.bats` 17→22). 4.6's own Result Log says "8 new bats cases"; it was 9 — 8 went RED, one passed pre-fix. The `(36 in file)` parenthetical is self-invalidating and its sibling at `:81` has already drifted 17→22 inside this same plan. Nothing parses `New-Tests`, so these are pure rot surface: replace with the derivation command.
- Acceptance Criteria: no hardcoded per-file test count remains in tasks.md; corrected figures stated once, with the command that reproduces them.
- Result Log: COMPLETE. The counts are **removed, not corrected** — `grep -rn "New-Tests" claude-code/ src/ tests/` returns zero hits, so nothing enforced them and they were pure rot surface. `Summary Counts` now carries the derivation commands; the milestone `New-Tests` field points at it; the `(17 in file)` and `(36 in file)` parentheticals are gone. The history is preserved in a comment rather than silently overwritten, including that `(17 in file)` had already drifted to 22 **inside this same plan** — which is the evidence that "recount from the file, never from this comment" is not a working mitigation. 4.6's own "8 new bats cases" corrected in place to 9, with the correction visible.

## Milestone 5: Gate enforcement reads the Python SSoT

- Status: PENDING
- Gate: HARD
- Mode: HITL
- Dependencies: Milestone 1
- Complexity: 70%
- **Critical-Path:** hook-modification
- Audit-Profile: infra
- New-Tests: derived — see Summary Counts
- Contract: `reference.md` "M5 enforcement contract" pins the module layout, signatures, per-field absence semantics, the 18-row form table with a decided verdict per row, the block-end rule, the exit codes, and the seven questions. Sub-steps cite it; they do not restate it.
- Acceptance Criteria: (1) every row of the reference form table is a passing test; (2) §6.7/§7.1 and `verify-impl` obtain **all seven** contract answers from `src/aa_ma/`; (3) no bash function parses a milestone block for an enforcing decision; (4) the four defects live at `d636824` are closed and named individually in the Result Log, not counted.

### Sub-step 5.0: Block-end rule — grammar.py closes on any H2

- Status: PENDING
- Mode: AFK
- Action: `split_milestones` closes a block only at the next milestone heading, so a trailing prose H2 carrying field-shaped lines is absorbed. Measured on `tests/hooks/fixtures/gate-scans/styles-tasks.md`: Python reads **3** line-anchored `Status: PENDING` in the em-dash milestone where bash reads **2**, and swallows both `## Summary Counts` and `## Milestone Gate Types`. Bash is right — 4.2 fixed this after measuring it — and `grammar.py` never got the fix. This is a bug fix for **both** consumers, so it lands in `grammar.py`, not in a gate-local copy.
- Acceptance Criteria: the fixture yields 2, not 3; TUI golden snapshot regenerated and the delta explained line by line; `--json` behavioural change recorded in CHANGELOG with a `schema_version` decision made explicitly (bump or documented no-bump).
- Result Log:

### Sub-step 5.1: Strict, fail-closed field reads

- Status: PENDING
- Mode: AFK
- Action: `src/aa_ma/enforce.py` per the pinned contract — `FieldRead` + `read_enforced_field`, one normalisation (strip bold pair, case-fold, leading token) then canonical membership. `tui/parser.py` is not touched: its defaulting is correct for a dashboard and wrong only for a gate. Milestone and step Status are **separate functions** because `StepStatus` has no `ACTIVE` and one parser cannot serve both.
- Acceptance Criteria: all 18 contract rows assert their decided verdict; every `is_valid=False` quotes the offending text; no enforced field can ever return a default; `uv run pytest` green including the untouched TUI suite.
- Result Log:

### Sub-step 5.2: RED — the gate contract as tests

- Status: PENDING
- Mode: AFK
- Action: `tests/test_gate.py`, written before `gate.py` exists. Corpus is not invented — it is every fixture that broke bash across three §6.8 passes, plus the contract's 18 rows, plus one/two/no ACTIVE, titles containing `\t` and `C:\dev\path`, CRLF, NBSP, unclosed fence, bare `##`, `##<TAB>`, and a trailing prose H2.
- Acceptance Criteria: every case asserts a verdict taken from the reference table, not invented at test-writing time; suite RED before 5.3.
- Result Log:

### Sub-step 5.3: GREEN — src/aa_ma/gate.py

- Status: PENDING
- Mode: AFK
- Action: answer the seven contract questions over `grammar.py` + `enforce.py` + `plan_parsers.py`. Refuse on ambiguity rather than choosing.
- Acceptance Criteria: 5.2 green; the no-second-parser claim asserted **behaviourally** — a test drives `gate.py` and the corresponding `grammar`/`enforce`/`plan_parsers` primitive over the same 18 rows and asserts identical readings. (The first draft's "grep for `re.compile`" is vacuously satisfiable via `re.match` — the shape the §6.8 panel rejected in 4.14.)
- Result Log:

### Sub-step 5.4: CLI with fail-closed exit codes

- Status: PENDING
- Mode: AFK
- Action: `aa-ma-gate` console script (no name collision; `[project.scripts]` pattern matches `aa-ma-tui`), JSON on stdout, exit codes 0/1/2/3/4 per the contract — 4 exists because `verify-impl` needs by-number lookup, which has no notion of "ACTIVE".
- Acceptance Criteria: each of the five codes reachable from a fixture; JSON validates against a declared schema; `--help` documents the codes; **and the interpreter-unavailable path is tested** — with Python absent the gate refuses loudly, never skips. (This was a risk bullet with nothing testing it, which is the fail-open shape again.)
- Result Log:

### Sub-step 5.5: Rewire §6.7, §7.1 and verify-impl

- Status: PENDING
- Mode: AFK
- Action: all seven answers come from the CLI. Condition 1's `# HALT` becomes `exit 1` — measured at HEAD to print BLOCKED and then PASS with exit 0. `verify-impl/SKILL.md` gains the `*)` arm its `case $?` lacks; it already calls `plan_parsers` from Python, so this extends an existing call site rather than introducing the first.
- Acceptance Criteria: bats **executes** the §6.7 fence against each fixture asserting exit status and message — the current guard is an exact-literal negative grep that goes green if an edit merely adds quotes; mutation-verified in both directions.
- Result Log:

### Sub-step 5.6: Mode — close the HITL bypass

- Status: PENDING
- Mode: AFK
- Action: `- Mode: TYPO` resolves to `AFK`, silently converting a human-in-the-loop sub-step into one that auto-dispatches without asking the user. §5.3 dispatch is a different enforcement surface from the gate, and would have been left untouched by M5 as first scoped — the review caught that the milestone's most alarming justification was not in its own scope. Rewire §5.3 to `enforce.read_enforced_field`.
- Acceptance Criteria: an unrecognised `Mode:` halts with the offending text quoted, never dispatches; absent `Mode:` still inherits parent then defaults `HITL` per the documented rule.
- Result Log:

### Sub-step 5.7: Retire the enforcing bash

- Status: PENDING
- Mode: AFK
- Action: measure callers, then delete every bash helper that parses a milestone block for an enforcing decision (the seven sites enumerated by the ground-truth audit). Display readers keep theirs — `aa-ma-session-start.sh`, `pre-compact-aa-ma.sh` — where a wrong answer is cosmetic. `aa_ma_list_active_tasks` is neither display-only nor a block parser and stays. `aa_ma_is_milestone_heading` has zero shipped callers and goes. The tolerant/strict boundary gets stated in the library header so no future caller repeats 4.5's mistake of wiring a gate to a display helper.
- Acceptance Criteria: zero enforcing callers remain; hooks bats green; the boundary documented.
- Result Log:

### Sub-step 5.8: Documentation debt, in one pass

- Status: PENDING
- Mode: AFK
- Action: CHANGELOG has had no entry across three windows including a security fix. Then ADR-0009: `grammar.py` is the SSoT; enforcement calls Python; bash is display-only; reading intent (gate) and enforcing canonical form (M2 linter) are separate concerns; file-derived data never crosses into awk via `-v`.
- Acceptance Criteria: CHANGELOG covers every public-symbol and behavioural change since `b11c46d`, including 5.0's `--json` change; ADR-0009 exists and is referenced from `aa-ma-parse.sh`'s header and `reference.md`.
- Result Log:

### Sub-step 5.9: Verify and gate

- Status: PENDING
- Mode: HITL
- Action: full suites; `Skill(impact-analysis)`; `CRITICAL_PATH_REVIEW — hook-modification` in provenance; §6.8 pass on the M5 window; HARD gate approval in context-log.
- Acceptance Criteria: all four M5 criteria verified with evidence; §6.8 CRITICALs resolved before approval is sought.
- Result Log:

## Summary Counts

- Milestones: 5
- Sub-steps: derive per milestone with `grep -c "^### Sub-step N\." *-tasks.md` from the task directory
- New tests declared: derived, never transcribed. `grep -c '^@test' tests/hooks/*.bats` under-reports — use `find tests/hooks -name '*.bats' -exec grep -hc '^@test' {} \; | paste -sd+ | bc`, which mirrors what CI runs.
- Suite gate: `failed == 0 and errors == 0`, plus a scoped delta per milestone. A whole-repo absolute total is self-invalidating.
