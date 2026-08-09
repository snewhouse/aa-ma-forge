# milestone-grammar-ssot Tasks (HTP)

Field format is load-bearing — see `reference.md` "Field format tasks.md MUST use".
`Audit-Profile` must be own-line and unbackticked; `Critical-Path` must be own-line and bold.
Headings use the canonical form this plan enforces (`## Milestone N:` / `### Sub-step N.N:`).

## Milestone 1: Shared grammar, type fix and TUI rewire

- Status: PENDING
- Gate: HARD
- Mode: AFK
- Dependencies: None
- Complexity: 60%
- **Critical-Path:** data-xform
- Audit-Profile: code-only
- New-Tests: 26
- Acceptance Criteria: plan §3 M1 acceptance 1-9

### Sub-step 1.0: Confirm baseline reproduces

- Status: PENDING
- Mode: AFK
- Action: `uv sync`; `uv run pytest --tb=short -q` must report `783 passed, 1 failed, 1 skipped, 7 deselected` with the single failure being the corpus-grandfathering sole-dev-merge param. Confirm the 14-row table in `reference.md` reproduces via `aa-ma-tui --root .claude --json --include-completed`.
- Result Log: _pending_

### Sub-step 1.1: RED — write tests/test_grammar.py

- Status: PENDING
- Mode: AFK
- Action: 26 cases — 15 positive (5 milestone variants incl. `2a`; keywords `Sub-step`/`Step`/`Task`; 7 number shapes `N.N`, `N.N.N`, `N.NN`, `N.Na`, `N.N.bis`, `MN.N`, `MNa.N`), 9 negative (`## Summary Counts`, `## Notes`, `## Milestone Gate Types`, `## 2024 — Retro`, `### Result Log`, `### Step: no number`, `#### Step 1.1:`, fenced-code-block heading, `### Step 1.1-alpha:`), plus `group(0)` no-newline and `discover_tasks` no-crash. Negatives assert against `split_milestones()`/`split_steps()`, not the raw regexes.
- Result Log: _pending_

### Sub-step 1.2: GREEN — src/aa_ma/grammar.py

- Status: PENDING
- Mode: AFK
- Action: `MILESTONE_RE`, `STEP_RE`, `strip_fenced_blocks`, `split_milestones`, `split_steps` returning `list[Block]` where `Block = tuple[str, str, str]`. Separator `(?::|[ \t]+[–—-][ \t]+)` — the bare hyphen is excluded deliberately. Line ends `[ \t]*$`, never `\s*$`. Block runs from match start to next match start or EOF; preamble discarded.
- Result Log: _pending_

### Sub-step 1.3: Milestone.number int → str

- Status: PENDING
- Mode: AFK
- Action: `model.py:190` `number: str`; add `coerce_numbers_to_str=True` to the ConfigDict at `model.py:188`; drop `int()` at `parser.py:172` and fix the annotation at `parser.py:168`.
- Result Log: _pending_

### Sub-step 1.4: Rewire parser.py to grammar.py

- Status: PENDING
- Mode: AFK
- Action: import `MILESTONE_RE`/`STEP_RE`/splitters; delete `_MILESTONE_RE`/`_STEP_RE`; update docstrings at `:5-7` and `:22-24`; keep the word "Milestone" in the `ParseError` at `:271`.
- Result Log: _pending_

### Sub-step 1.5: SCHEMA_VERSION 1 → 2 and its assertions

- Status: PENDING
- Mode: AFK
- Action: bump `model.py:141`; update `test_json_output.py:39`, `test_integration.py:117`, `test_main_dispatch.py:102`; fix docstring `json_output.py:8`; update `docs/adr/0007-aa-ma-tui-tracker.md:161,184`; CHANGELOG breaking entry.
- Result Log: _pending_

### Sub-step 1.6: Fix comparison sites and regenerate the golden

- Status: PENDING
- Mode: AFK
- Action: `test_parser_properties.py:152` and `test_parser.py:242` compare against ints — coercion does not help. Regenerate `tests/tui/snapshots/data.json`.
- Result Log: _pending_

### Sub-step 1.7: Rewire the corpus test

- Status: PENDING
- Mode: AFK
- Action: import `split_milestones` in `test_corpus_grandfathering.py`; delete private `_split_milestones`; add the missing `assert milestones` at `:80`.
- Result Log: _pending_

### Sub-step 1.8: bats case for aa-ma-parse.sh

- Status: PENDING
- Mode: AFK
- Action: pin only that `aa_ma_extract_active_milestone` returns `Milestone 1 — Pre-flight + scope-aware CI checks` rc 0 on the em-dash fixture. Do NOT pin its over-tolerance.
- Result Log: _pending_

### Sub-step 1.9: Verify and gate

- Status: PENDING
- Mode: HITL
- Action: run all 9 acceptance criteria including `uv run pytest -m slow -q` and `bats -F tap --recursive tests/hooks/` (113 ok). Write `IMPACT_ANALYSIS` and `CRITICAL_PATH_REVIEW — data-xform` to provenance. HARD gate approval in context-log.
- Result Log: _pending_

## Milestone 2: Strict writer, canonical Sub-step

- Status: PENDING
- Gate: SOFT
- Mode: AFK
- Dependencies: Milestone 1
- Complexity: 35%
- Audit-Profile: code-only
- New-Tests: 2
- Acceptance Criteria: plan §3 M2 acceptance 1-4

### Sub-step 2.1: Malformed fixture

- Status: PENDING
- Mode: AFK
- Action: `tests/fixtures/canonical/malformed-task/malformed-task-tasks.md` with `## M1: x`, `## Milestone M2: x`, `## Milestone 3 — x`, `### Task 1.1: x`.
- Result Log: _pending_

### Sub-step 2.2: Canonical lint

- Status: PENDING
- Mode: AFK
- Action: `tests/test_active_plans_canonical.py` with `CANONICAL_M` / `CANONICAL_S`, scanning `.claude/dev/active/**/*-tasks.md`, excluding `.worktrees/`. Two tests: clean pass, and a meta-test asserting the fixture yields exactly 4 violations.
- Result Log: _pending_

### Sub-step 2.3: Fix rules/aa-ma.md

- Status: PENDING
- Mode: AFK
- Action: `claude-code/rules/aa-ma.md:78` `### Task 1.1:` → `### Sub-step 1.1:`. Note the file is symlinked live by `scripts/install.sh:284` — the change is immediate for all sessions.
- Result Log: _pending_

### Sub-step 2.4: Verify this plan's own artifacts pass

- Status: PENDING
- Mode: AFK
- Action: run the lint against `.claude/dev/active/milestone-grammar-ssot/`. Revision 2 of this plan would have failed here.
- Result Log: _pending_

## Milestone 3: Fix the flaky C4 test

- Status: PENDING
- Gate: SOFT
- Mode: AFK
- Dependencies: None
- Complexity: 55%
- Audit-Profile: code-only
- Prototype-Required: YES
- New-Tests: 0
- Acceptance Criteria: plan §3 M3 acceptance 1-5

### Sub-step 3.1: Reproduce the flake

- Status: PENDING
- Mode: AFK
- Action: `Skill(systematic-debugging)`. Run the suite in a loop until C4 fails; capture the failing output. shellcheck is present (0.11.0) — the missing-binary theory is already disproven.
- Result Log: _pending_

### Sub-step 3.2: Test the SLUG-collision hypothesis

- Status: PENDING
- Mode: AFK
- Action: `test_stage_c_dispatch.bats:30` builds `SLUG="bats-$$-$(date +%s%N | tail -c 6)"`; three files share `/tmp/sole-dev-merge-shellcheck-${SLUG}.json`. Confirm or refute before fixing.
- Result Log: _pending_

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
- New tests declared: 28 python (M1 26, M2 2) + bats cases in M1/M4
- Expected suite on completion: `passed == 784 + 28`, `failed == 0`, `skipped == 1`, `deselected == 7`
