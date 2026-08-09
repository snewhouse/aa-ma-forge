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
- Result Log: Added `aa_ma_extract_active_milestone reads an em-dash milestone heading` to tests/hooks/aa-ma-parse.bats (17 in file). Pins only the em-dash behaviour; the helper's over-tolerance is explicitly NOT pinned, with a comment saying why.

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

- Status: ACTIVE
- Gate: SOFT
- Mode: AFK
- Dependencies: None
- Complexity: 55%
- Audit-Profile: code-only
- **Prototype-Required:** YES
- New-Tests: 0
- Acceptance Criteria: plan §3 M3 acceptance 1-5

### Sub-step 3.1: Reproduce the flake

- Status: PENDING
- Mode: AFK
- Action: `Skill(systematic-debugging)`. Run the suite in a loop until C4 fails; capture the failing output. shellcheck is present (0.11.0) — the missing-binary theory is already disproven.
- Result Log: REPRODUCED, but not by looping. A 25-run loop with `shellcheck` on PATH produced 0 failures, which is itself the finding: the flake is not resident in the test's own state. Reproduced deterministically instead by removing **only** `shellcheck` from PATH (shadow dir of symlinks to /usr/local/bin + /usr/bin + /bin minus shellcheck, so git/grep/python3 stay resolvable). Signature matches the reported failure exactly: `not ok 1 C4 maps ShellCheck error to [CRITICAL]` … `line 147: [[ "$FINDINGS" == *"[CRITICAL]"* ]] || [[ "$FINDINGS" == *"[HIGH]"* ]]' failed`. Mechanism: `sole-dev-merge.md:362` runs `shellcheck -f json $CHANGED_SH > "$SHELLCHECK_OUT" 2>/dev/null || true`; absent binary → empty file → `[[ -s ]]` false → zero findings → opaque assertion failure instead of a skip. With shellcheck present the tool output is deterministic (`info SC1009`, `error SC1073/SC1080/SC1072` → 3 × CRITICAL), so there is no ambiguity on the happy path. Note: `python3` at `sole-dev-merge.md:344,364` is a second unguarded dependency with the identical silent-swallow signature.

### Sub-step 3.2: Test the SLUG-collision hypothesis

- Status: PENDING
- Mode: AFK
- Action: `test_stage_c_dispatch.bats:30` builds `SLUG="bats-$$-$(date +%s%N | tail -c 6)"`; three files share `/tmp/sole-dev-merge-shellcheck-${SLUG}.json`. Confirm or refute before fixing.
- Result Log: **REFUTED — measured, not reasoned.** Built a 2-file / 10-test probe replicating the SLUG derivation verbatim under `bats@1.11.0 --recursive`. Every `setup()` observed a *distinct* `$$` (612456, 612463, 612470, 612477, 612484, 612526, 612557, 612581, 612589, 612596): bats forks a fresh subshell per **test**, not per file, so the PID component alone guarantees uniqueness. Duplicate SLUGs across the run: **0**. A collision would additionally require PID reuse *and* a matching 5-digit nanosecond suffix inside one run. The shared `/tmp` path is therefore not the flake. Recorded as a finding, not a failure, per plan §3 M3 acceptance 5. Sub-step 3.3 still proceeds — a real cleanup leak was found independently (see 3.3).

### Sub-step 3.3: Isolate temp state

- Status: PENDING
- Mode: AFK
- Action: unique path per test under `BATS_TEST_TMPDIR`; fix the cleanup leak across all three files.
- Result Log: _pending_

### Sub-step 3.4: Skip guard and binary indirection

- Status: PENDING
- Mode: AFK
- Action: `SHELLCHECK_BIN="${SHELLCHECK_BIN:-shellcheck}"` plus the guard pattern reused from `tests/hooks/security-static-check.bats:248-251`.
- Result Log: _pending_

### Sub-step 3.5: CI install step

- Status: PENDING
- Mode: AFK
- Action: add `apt-get install -y shellcheck` to the **bats** job in `.github/workflows/security.yml`; verify with the coreutils awk extractor (0 before, 1 after).
- Result Log: _pending_

### Sub-step 3.6: 20-run soak

- Status: PENDING
- Mode: AFK
- Action: 20 consecutive `bats -F tap --recursive tests/commands/sole-dev-merge/` — 69 ok, 0 not-ok, every run. Write `PROTOTYPE — <verdict>` to provenance. Record root cause in context-log.
- Result Log: _pending_

## Milestone 4: Close the HARD-gate scan blindness

- Status: PENDING
- Gate: HARD
- Mode: HITL
- Dependencies: Milestone 1
- Complexity: 45%
- **Critical-Path:** hook-modification
- Audit-Profile: infra
- New-Tests: 0
- Acceptance Criteria: plan §3 M4 acceptance 1-3

### Sub-step 4.1: RED — failing bats per scan point

- Status: PENDING
- Mode: AFK
- Action: fixtures using `## M1:` and `## Milestone 1 —`, each with one sub-step whose status field is the pending value, plus a `- **Critical-Path:** data-xform` line. Assert every scan finds them. Currently returns empty. (Deliberately avoids writing the literal pending-status string here — the HARD gate greps for it and would count a prose mention as a real pending sub-step.)
- Result Log: _pending_

### Sub-step 4.2: Align the gate scans

- Status: PENDING
- Mode: AFK
- Action: `execute-aa-ma-milestone.md:504,518,529,692` and `verify-impl/SKILL.md:57` to an ERE equivalent of `MILESTONE_RE`.
- Result Log: _pending_

### Sub-step 4.3: Add CANONICAL_CRITICAL_PATHS

- Status: PENDING
- Mode: AFK
- Action: add the 6-value constant to `plan_parsers.py` — it does not exist, so the check is manual-only today.
- Result Log: _pending_

### Sub-step 4.4: Widen hook-modification scope

- Status: PENDING
- Mode: AFK
- Action: `claude-code/rules/engineering-standards.md` currently scopes `hook-modification` to `claude-code/hooks/*.sh`; widen to cover shipped commands and skills, or this milestone's own Critical-Path value reads as a violation.
- Result Log: _pending_

### Sub-step 4.5: Verify and gate

- Status: PENDING
- Mode: HITL
- Action: `bats -F tap --recursive tests/hooks/` green; `Skill(impact-analysis)` with HIGH findings resolved; `CRITICAL_PATH_REVIEW — hook-modification` in provenance; HARD gate approval in context-log.
- Result Log: _pending_

## Summary Counts

- Milestones: 4 (2 HARD, 2 SOFT)
- Sub-steps: 25
- New tests declared: 37 python (M1 35, M2 2) + bats cases in M1/M4
- Suite gate: `failed == 0 and errors == 0`, plus a **scoped** delta — `pytest tests/test_grammar.py -q` reports exactly `New-Tests` for M1. A whole-repo absolute total is self-invalidating: archiving this very plan adds 2 parametrized cases to `test_corpus_grandfathering`, and any unrelated test added before M4 breaks it.
