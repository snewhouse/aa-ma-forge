# milestone-grammar-ssot Plan (revision 3)

**Objective:** Unify AA-MA milestone/step header parsing behind one shared grammar, restore TUI visibility for the tasks it silently drops, close the HARD-gate scan blindness that widening exposes, and fix the intermittent C4 bats failure.
**Owner:** Stephen J Newhouse + AI
**Created:** 2026-08-09
**Base commit:** b11c46d
**Revision:** 3 — after Phase 4.2 eng review and two Phase 4.5 automated verification loops (6 angles, 11 CRITICAL total). §11 lists what revisions 1 and 2 got wrong.

## 1. Executive Summary

Six independent header grammars disagree about what a milestone is. `aa-ma-tui` drops 4 repo tasks entirely and shows 0 steps for 6 more; `test_corpus_grandfathering` fails; and the `/execute-aa-ma-milestone` HARD gate silently scans empty on non-canonical plans. Replace the Python grammars with one shared module, align the bash/awk gate scans, enforce the canonical writer form, and fix the flaky C4 test.

## 2. Ground Truth (measured at b11c46d)

### 2.1 The six grammars

| # | Location | Pattern | Blind to |
|---|---|---|---|
| 1 | `src/aa_ma/tui/parser.py:49` | `^## Milestone (\d+):` | `MN:`, `Milestone MN:`, em-dash, `2a` |
| 2 | `src/aa_ma/tui/parser.py:50` | `^### Step (\d+\.\d+):` | `Task`, `Sub-step`, `.bis`, `2.7b`, `M2a.1` |
| 3 | `tests/codemem/test_corpus_grandfathering.py:45-48` | `^## (?:Milestone\s+)?M?\d+(?:\.\d+)?:` | em-dash, `2a` |
| 4 | `claude-code/hooks/lib/aa-ma-parse.sh:75` | awk `/^## /` | nothing — **over**-tolerant |
| 5 | `claude-code/commands/execute-aa-ma-milestone.md:504,518,529,692` | awk `/^## Milestone.*/` | `MN:`, em-dash — **drives the HARD gate** |
| 6 | `claude-code/skills/verify-impl/SKILL.md:57` | awk `/^## (Milestone\s+)?M?$N(:\|\s)/` | em-dash |

### 2.2 Corpus census (14 repo `*-tasks.md`)

Milestones: `## Milestone N:` 10 files · `## Milestone MN:` 2 · `## MN:` 1 · `## Milestone N —` 1 · `## Milestone 2a:` letter-suffixed 1.
Steps: `### Step N.N:` 6 files/151 · `### Task N.N:` 5/128 · `### Sub-step N.N:` 3/72. No majority. Number shapes: `N.N`, `N.N.N`, `N.NN`, `N.Na`, `N.N.bis`, `MN.N`, `MNa.N`.

**Canonical is `## Milestone N: Title` / `### Sub-step N.N: Title`** (`docs/templates/tasks-template.md:26,89,127,147,155`; `docs/spec/aa-ma-specification.md:697,704`). `claude-code/rules/aa-ma.md:78` contradicts with `### Task 1.1:`.

### 2.3 Measured damage — repo-local, `aa-ma-tui --root .claude --json --include-completed`

`--root .` returns **23 junk entries** (every top-level directory) because `_resolve_roots` (`__main__.py:85-117`) falls through to a direct scan. **`--root .claude` returns the 14 real tasks.**

| Task | now M/S | after M/S | note |
|---|---|---|---|
| codemem | 0/0 ERROR | 5/47 | blind |
| harden-aa-ma-plan | 0/0 ERROR | 5/24 | blind |
| skill-ecosystem-integration | 0/0 ERROR | 3/26 | blind |
| sole-dev-merge-pr-workflow | 0/0 ERROR | 5/42 | blind |
| codemem-benchmark-fairness-v2 | 3/0 | 6/30 | milestone count changes |
| aa-ma-engineering-standards | 5/0 PENDING | 5/37 **IN_PROGRESS** | status changes |
| codemem-token-benchmarks | 4/0 | 4/16 | |
| fix-drift-release-v0-9-0 | 3/0 | 3/15 | |
| ship-missing-skills | 4/0 | 4/15 | |
| understand-codebase-skill | 3/0 | 3/20 | |
| hooks-hardening-m1 | 5/17 | 5/19 | `.bis` steps |
| aa-ma-tui-tracker | 6/42 | 6/42 | unchanged |
| post-impl-adversarial-review | 6/23 | 6/23 | unchanged |
| token-stack-integration | 5/12 | 5/12 | unchanged |

Totals **44 → 65 milestones, 135 → 368 steps**. Only 3 of 14 unchanged. The constraint is *"every delta is one we predicted"*, not *"no deltas"*.

### 2.4 C4 is flaky, not environmental

`shellcheck` **is** installed (0.11.0). C4 passes alone and passed 3/3 full-suite runs; failed twice earlier the same session. `bats` is genuinely absent locally (`npx bats@1.11.0` works). Suspect: `test_stage_c_dispatch.bats:30` `SLUG="bats-$$-$(date +%s%N | tail -c 6)"` — bats reuses `$$` within a file — with `/tmp/sole-dev-merge-shellcheck-${SLUG}.json` shared across `test_stage_c_dispatch.bats:48`, `test_stage_d_triage.bats:52`, `test_smoke_e2e.bats:218`. Cleanup leaks: 3 stray files survived 3 runs.

### 2.5 REFERENCE-grade: how `tasks.md` must write fields

Verified by executing the real parsers. **Two different consumers, two different requirements — both must be satisfied:**

| Field | Required form | Why |
|---|---|---|
| `Audit-Profile` | `- Audit-Profile: code-only` — own line, **unbackticked** | `plan_parsers._extract_field` anchors `^[ \t]*-?[ \t]*`; backticks make the value non-canonical |
| `Critical-Path` | `- **Critical-Path:** data-xform` — own line, **bold**, unbackticked | `execute-aa-ma-milestone.md:520` greps `^- \*\*Critical-Path:\*\* \S` |

Measured: mid-line `· Audit-Profile: \`code-only\`` → `(None, True, None)`; own-line backticked → `('\`code-only\`', False, "Non-canonical…")`; own-line bare → `('code-only', True, None)`.

**Revisions 1–2 wrote fields mid-line and backticked, so all five milestones parsed as `Audit-Profile: None` and the `Critical-Path` gate scan read empty — the plan reproduced, in its own artifacts, the exact blindness M4 exists to fix.**

### 2.6 Latent defect

`test_corpus_grandfathering.py:80` (`test_tdd_waiver_canonical_or_absent_for_corpus`) has no non-empty assert — passes vacuously on zero milestones. Its sibling at :63 has one.

## 3. Milestones

### M1 — Shared grammar, type fix and TUI rewire (atomic)
- **Gate:** HARD
- **Mode:** AFK
- **Complexity:** 60%
- **Effort:** ~3h
- **Critical-Path:** data-xform
- **Audit-Profile:** code-only

Merged from revisions 1–2's M1+M2: **not separable.** Changing `Milestone.number` without rewiring leaves the type unreachable (`(\d+)` can never yield `"2a"`); rewiring without the type change crashes. Splitting them lets M1 pass a HARD gate green while the suite is broken.

**`src/aa_ma/grammar.py` — full API, no ambiguity:**
```python
Block = tuple[str, str, str]          # (number, title, block_text)

_SEP   = r"(?::|[ \t]+[–—-][ \t]+)"   # colon, or a SPACE-DELIMITED dash
_NUM_M = r"\d+[a-z]?(?:\.\d+)?"                    # 1, 2a, 3.5
_NUM_S = r"M?\d+[a-z]?(?:\.\d+)*(?:\.bis|[a-z])?"  # 1.1, M2a.1, 1.1.bis, 2.7b, 3.5.1

MILESTONE_RE = re.compile(rf"^##[ \t]+(?:Milestone[ \t]+M?|M)(?P<number>{_NUM_M}){_SEP}[ \t]*(?P<title>.+?)[ \t]*$", re.M)
STEP_RE      = re.compile(rf"^###[ \t]+(?:Sub-step|Step|Task)[ \t]+(?P<number>{_NUM_S}){_SEP}[ \t]*(?P<title>.+?)[ \t]*$", re.M)

def strip_fenced_blocks(text: str) -> str: ...   # mirrors plan_parsers._strip_html_comments
def split_milestones(text: str) -> list[Block]: ...
def split_steps(milestone_block: str) -> list[Block]: ...
```
- **Boundary rule:** a block runs from its match start to the next match start, or EOF. Text before the first match is discarded. A step block terminates at the next step match or the end of its milestone block.
- **Return type is `list[Block]`** — supersedes both predecessors (`test_corpus_grandfathering._split_milestones` → `list[str]`; `parser._split_milestone_blocks` → `list[tuple[int,str,str]]`). `number` is `str` in both.
- **`_SEP` excludes the bare hyphen.** A raw `[:–—-]` class matched `### Step 1.1-alpha:` as number `1.1` + title `alpha:` — a mandated negative case that the mandated regex accepted. Verified fixed: `1.1-alpha` and `2.3 -- dashes` now reject; corpus still 65/368, zero unparsed.
- **Fences are stripped in the splitters, not the regexes.** A flat `re.M` regex cannot see fences, so the fenced negative case is only satisfiable at function level. Measured occurrences in corpus: **zero** — this is prophylactic.
- `[ \t]*$` never `\s*$` (`\s` eats newlines; `group(0)` would span lines).

**Type change and its full ripple** — `Milestone.number: int → str` (`model.py:190`), drop `int()` at **`parser.py:172`**, and update the local/return annotations at `parser.py:168`:
- Add `coerce_numbers_to_str=True` to `Milestone`'s `ConfigDict` (`model.py:188`). Pydantic 2.12.5 **rejects** int for a str field by default; coercion fixes 10 construction sites in one line instead of 10 edits.
- Coercion does **not** fix comparisons: `test_parser_properties.py:152` (`@pytest.mark.slow`, one of the 7 deselected) and `test_parser.py:242` compare against ints — edit those.
- `SCHEMA_VERSION` 1 → 2 (`model.py:141`) — `"number": 1` → `"number": "1"` is a shape change. Update the three tests that pin 1: `test_json_output.py:39`, `test_integration.py:117`, `test_main_dispatch.py:102`; regenerate the golden `tests/tui/snapshots/data.json`; fix the docstring at `json_output.py:8`; update `docs/adr/0007-aa-ma-tui-tracker.md:161,184`; CHANGELOG breaking entry.
- `parser.py` docstrings at **lines 5-7 and 22-24** both document the old grammar. Keep the word "Milestone" in the `ParseError` message at :271 — `test_parser.py:199-202` asserts on it.
- Fixture ripple, accepted: `tests/tui/fixtures/tasks/security-quality-remediation/` uses `### Task 0.1:` → **0→24 steps**, consumed by 6 live tests.
- Rewire `test_corpus_grandfathering.py` to import `split_milestones`; delete its private `_split_milestones`; add the missing `assert milestones` at :80.
- `aa-ma-parse.sh`: **no change** — verified tolerant. Add a bats case pinning only the em-dash behaviour, **not** its over-tolerance (`## Status:` parsing as a milestone stays a known wart, not a contract).

**Sub-step 1.0 (must run first):** write the 14-row × 3-column baseline table (milestones, steps, aggregate_status — 42 values) into `reference.md`. Acceptance #5 reads it; without this the gate is decorative.

**RED first** — `tests/test_grammar.py`, **26 cases**: 15 positive (5 milestone variants incl. `2a`, 3 step keywords, 7 number shapes) + 9 negative (`## Summary Counts`, `## Notes`, `## Milestone Gate Types`, `## 2024 — Retro`, `### Result Log`, `### Step: no number`, `#### Step 1.1:`, fenced-code-block heading, `### Step 1.1-alpha:`) + `group(0)` no-newline + `discover_tasks` no-crash. Negatives assert against `split_milestones()`/`split_steps()`, not the raw regexes.

**Acceptance**
1. `uv run pytest tests/codemem/ tests/tui/ tests/test_grammar.py -q` exits 0 — **`tests/tui/` included deliberately**; excluding it was how revision 2 would have passed green over a broken suite.
2. `uv run pytest -m slow tests/tui/ -q` exits 0 (catches `test_parser_properties.py:152`, invisible to the default run). Scoped to `tests/tui/` because `tests/codemem/test_bench_harness.py::test_harness_e2e_against_aa_ma_forge` fails on the clean baseline — a third pre-existing failure, unrelated to this work.
3. `assert len(POSITIVE_CASES) == 15 and len(NEGATIVE_CASES) == 9`, and every negative returns `[]` from the splitters.
4. `grep -rn "_split_milestones" src/ tests/` empty (scoped — a repo-wide grep walks `.worktrees/`).
5. New per-file `(milestones, steps, aggregate_status)` equals the `reference.md` table from Sub-step 1.0 **exactly**.
6. `uv run python -c "from pathlib import Path; from aa_ma.tui.parser import discover_tasks; discover_tasks([Path('.claude/dev/active'), Path('.claude/dev/completed')])"` exits 0. (`discover_tasks` takes `list[Path]`; revisions 1–2 passed a bare `Path` → `TypeError` before and after, gating nothing.)
7. `aa-ma-tui --root .claude --json --include-completed` yields exactly codemem 5/47, harden-aa-ma-plan 5/24, skill-ecosystem-integration 3/26, sole-dev-merge-pr-workflow 5/42, and no task reports 0 milestones (14/14).
8. `SCHEMA_VERSION == 2`; CHANGELOG breaking entry present.
9. `bats -F tap --recursive tests/hooks/` → exactly **119** `^ok`, zero `^not ok` (recursive baseline 118 — `fixtures/build_active_dir.bats` adds 6 — plus this milestone's one case; 113 non-recursive).

**Rollback:** one commit; `git revert`. `grammar.py` is additive and may stay.

### M2 — Strict writer (canonical = `Sub-step`)
- **Gate:** SOFT
- **Mode:** AFK
- **Complexity:** 35%
- **Effort:** ~1h
- **Audit-Profile:** code-only

(`docs-only` was wrong — this milestone ships Python and edits a live-symlinked ruleset. `docs-only` dispatches only the future-proofing auditor per `verify-impl/SKILL.md:40`.)

```python
CANONICAL_M = re.compile(r"^## Milestone (\d+): \S.*$")
CANONICAL_S = re.compile(r"^### Sub-step (\d+\.\d+): \S.*$")
```
Tolerant reader, strict writer: no letter suffixes, no `.bis`, no em-dash, exactly one space after the colon.
- Fix **all eleven** shipped writers of tasks.md headings (scope expanded from 1 during execution — see context-log D8). The authoritative list is `WRITER_TEMPLATES` in `tests/test_active_plans_canonical.py`; only `docs/templates/tasks-template.md` was already canonical. **Symlinked live** by `scripts/install.sh:284` — the edit changes the auto-loaded ruleset for every subsequent session with no reinstall.
- `tests/test_active_plans_canonical.py` lints `.claude/dev/active/**/*-tasks.md`, excluding `.worktrees/`.
- Fixture: `tests/fixtures/canonical/malformed-task/malformed-task-tasks.md` with `## M1: x`, `## Milestone M2: x`, `## Milestone 3 — x`, `### Task 1.1: x`.

**Acceptance**
1. `uv run pytest tests/test_active_plans_canonical.py -q` exits 0.
2. `check_canonical(FIXTURE)` returns exactly 4 violations (meta-test — a test that "fails against a fixture" cannot live in the suite).
3. No shipped writer emits a non-canonical tasks.md heading — enforced by `test_shipped_writers_emit_canonical_headings` across all 11, not by a single-file grep.
4. **This plan's own `tasks.md` passes the lint**, and every writer carries a mutation guard (`test_writer_check_is_not_vacuous`) proving the check is not inert. The original rationale — "the scribe writes from tasks-template.md, consistent by construction" — was **refuted**: the scribe carries its own template at `agents/aa-ma-scribe.md:148,153,163`. Consistency is enforced by test, not by construction. Note this `plan.md`'s own `### M1 —` headings use two outlawed forms; harmless here (no grammar scans `plan.md`) but the scribe must not carry the style into `tasks.md`.

### M3 — Fix the flaky C4 test
- **Gate:** SOFT
- **Mode:** AFK
- **Complexity:** 55%
- **Effort:** ~2h (uncertain — intermittent)
- **Audit-Profile:** code-only
- **Prototype-Required:** YES

Highest-complexity milestone with a named unproven hypothesis — Theme 1's prototype-first trigger. The 20× soak result lands as a `PROTOTYPE — <verdict>` provenance entry.

**Scope amended 2026-08-09 (D9, user decision at the §6.8 panel):** extended from
C4/shellcheck to **both Stage C scanners**. C3/bandit carried the identical
silent-swallow defect on a scanner that is not a declared dependency and that
drives Stage D's auto-remediation. Also amended: the `BATS_TEST_TMPDIR`
re-pathing below is **dropped** — it existed only to defeat the SLUG-collision
hypothesis, which Sub-step 3.2 refuted by measurement.

Invoke `Skill(systematic-debugging)` — root cause before fix.
- First hypothesis: `SLUG` collision + shared `/tmp/sole-dev-merge-shellcheck-${SLUG}.json` across the three `.bats` files.
- Unique path per test under `BATS_TEST_TMPDIR`; fix the cleanup leak.
- Skip guard as hygiene — **reuse** `tests/hooks/security-static-check.bats:248-251`.
- `SHELLCHECK_BIN="${SHELLCHECK_BIN:-shellcheck}"` so absence is simulable (`PATH` cannot simulate absence without removing `git`/`grep`).
- CI: `apt-get install -y shellcheck` in the **bats** job.

**Acceptance**
1. 20 consecutive `bats -F tap --recursive tests/commands/sole-dev-merge/` runs: 69 `^ok`, 0 `^not ok`, every time. One green run proves nothing about a flake.
2. `SHELLCHECK_BIN=/nonexistent/shellcheck bats -F tap …test_stage_c_dispatch.bats` exits 0 with exactly one `# skip` naming C4. (C4 opens at **line 124**; :118 is a bandit assertion. Reference by name, not line.)
3. `ls /tmp/sole-dev-merge-* 2>/dev/null | wc -l` = 0 after a full run.
4. Coreutils only — `yq` is **not** installed here or in CI, and `pyyaml` would be an undeclared transitive dep:
   ```bash
   awk '/^  bats:/{f=1;next} f&&/^  [a-z]/{f=0} f' .github/workflows/security.yml \
     | grep -cE 'apt-get install( -y)? .*shellcheck'   # >= 1
   ```
   Verified 0 at b11c46d, 1 with the step spliced in, no leakage from the standalone `shellcheck:` job.
5. Root cause in `context-log.md`. A wrong hypothesis is a finding, not a failure.

### M4 — Close the HARD-gate scan blindness
- **Gate:** HARD
- **Mode:** HITL
- **Complexity:** 45%
- **Effort:** ~1.5h
- **Critical-Path:** hook-modification
- **Audit-Profile:** infra

Legitimising `## M1:` and em-dash styles while grammar #5 stays blind leaves the HARD gate reporting zero `Status: PENDING` and missing `Critical-Path:` on milestones that have both. A safety regression, not cosmetics.
- Align `execute-aa-ma-milestone.md:504,518,529,692` and `verify-impl/SKILL.md:57` to an ERE equivalent of `MILESTONE_RE`. Bash cannot import Python — the shared contract is the corpus.
- Widen the `hook-modification` scope line in `engineering-standards.md` (currently "Changes to `claude-code/hooks/*.sh`") to cover shipped commands and skills, or the value/scope mismatch reads as a violation to the next auditor.
- Add `CANONICAL_CRITICAL_PATHS` to `plan_parsers.py`. It does not exist, so Angle 6 check #2 is manual-only today.

**Acceptance**
1. RED first: a bats case per scan point — `## M1:` and `## Milestone 1 —` fixtures each with one `Status: PENDING` sub-step and a `- **Critical-Path:** data-xform` line; every scan finds them. Currently returns empty.
2. `bats -F tap --recursive tests/hooks/` all green.
3. `Skill(impact-analysis)` run; HIGH findings resolved before COMPLETE.

## 4. Tests per milestone

| M | Command | Expected |
|---|---|---|
| M1 | see M1 Acceptance 1-9 — the per-milestone block is the single source of truth for commands and expected values |
| M2 | `uv run pytest tests/test_active_plans_canonical.py -q` | exit 0; fixture → 4 violations |
| M3 | 20× `bats -F tap tests/commands/sole-dev-merge/` | 69 ok × 20 |
| M4 | `bats -F tap --recursive tests/hooks/` | all green incl. new cases |
| ALL | `uv run pytest --tb=short -q` | below |

**Baseline pinned:** b11c46d = **783 passed, 1 failed, 1 skipped, 7 deselected**. On completion: `failed == 0 and errors == 0 and skipped == 1 and deselected == 7 and passed == 784 + N_new`, where `N_new` is the sum of the per-milestone `New-Tests:` counts declared in `tasks.md`. No second copy of those numbers lives here — that is the whole mechanism. The gate computes `N_new` from those declarations — it is not a second hardcoded number to drift.

## 5. Artefacts

**New:** `src/aa_ma/grammar.py`, `tests/test_grammar.py`, `tests/test_active_plans_canonical.py`, `tests/fixtures/canonical/malformed-task/`.
**Modified (M2 writers):** `claude-code/rules/aa-ma.md`, `claude-code/agents/aa-ma-scribe.md`, `claude-code/commands/aa-ma-plan.md`, `claude-code/commands/execute-aa-ma-milestone.md`, `claude-code/commands/execute-aa-ma-full.md`, `claude-code/commands/execute-aa-ma-step.md`, `claude-code/skills/aa-ma-execution/SKILL.md`, `claude-code/skills/aa-ma-plan-workflow/references/PHASE_5_ARTIFACT_CREATION.md`, `docs/templates/plan-template.md`, `docs/spec/aa-ma-team-guide.md`, `docs/spec/aa-ma-specification.md`, `README.md`, `examples/aa-ma-team-guide/aa-ma-team-guide-tasks.md`.

**Modified (M1):** `src/aa_ma/tui/parser.py`, `src/aa_ma/tui/model.py`, `src/aa_ma/tui/json_output.py` (docstring), `tests/codemem/test_corpus_grandfathering.py`, `tests/tui/_static_tasks.py`, `tests/tui/test_parser.py`, `tests/tui/test_parser_properties.py`, `tests/tui/test_model.py`, `tests/tui/test_snapshot.py`, `tests/tui/test_json_output.py`, `tests/tui/test_integration.py`, `tests/tui/test_main_dispatch.py`, `tests/tui/snapshots/data.json` (regenerate), `tests/hooks/aa-ma-parse.bats`, `tests/commands/sole-dev-merge/test_stage_c_dispatch.bats` (+ `test_stage_d_triage.bats`, `test_smoke_e2e.bats`), `.github/workflows/security.yml`, `claude-code/rules/aa-ma.md`, `claude-code/rules/engineering-standards.md`, `claude-code/commands/execute-aa-ma-milestone.md`, `claude-code/skills/verify-impl/SKILL.md`, `src/aa_ma/plan_parsers.py`, `docs/adr/0007-aa-ma-tui-tracker.md`, `CHANGELOG.md`, `CLAUDE.md`.

## 6. Rollback

One commit per milestone; `git revert` each. M1 carries the only runtime behaviour change. M4 touches shipped, live-symlinked commands/skills — revert restores immediately, no reinstall. No data migration, no archive edits, no force-push.

## 7. Dependencies & assumptions

- Setup: `uv sync`. Baseline reproduces exactly (`783/1/1/7`) — confirm before touching anything.
- `bats` absent locally; `npx bats@1.11.0` is the fallback. `shellcheck` 0.11.0 present. `yq` absent here and in CI.
- `--root .claude`, never `--root .` (23 junk entries).
- `plan_parsers.py` has 3 test importers, 0 `src/` importers. `_split_milestones` is unique to `test_corpus_grandfathering.py`.
- `.txt`/SVG snapshots are built from hand-constructed `Task` objects and are genuinely unaffected; **`snapshots/data.json` is not** — it pins `"number": 1` and `"schema_version": 1`.
- `.claude/dev/active/` is empty now; executing this plan populates it, so M2 lints its own artifacts.
- **Out of scope:** normalizing archived tasks.md (frozen); `archive-aa-ma.md:167` and `aa-ma-parse.sh` over-tolerance (no gate impact); the 2 home-directory tasks (`agent-token-optimization`, `safety-app-production-settings` — outside the repo, unreproducible in CI, verified manually into `provenance.log`); gstack 1.34→1.61.

## 8. Risks & mitigations

| Risk | Mitigation |
|---|---|
| `int → str` breaks hidden consumers | Audited: no validator, no sort/compare, no `model_validate`, `extra='ignore'`, both read sites are f-strings. `coerce_numbers_to_str` + the 12 enumerated test/golden edits cover the rest. |
| Non-breaking gate blocks on intended deltas | Acceptance #5 pins the exact 14-row table written by Sub-step 1.0 |
| M3's hypothesis is wrong | The 20× soak is the gate, not the fix; `Prototype-Required: YES` forces the verdict into provenance |
| M4 edits live-symlinked shipped assets | HITL gate, impact-analysis, RED-first bats per scan point |
| Fields written so parsers can't see them | §2.5 pins the exact form; M2 acceptance #4 checks it |

## 9. Effort & complexity

~7.5h. M1 60% · M2 35% · M3 55% · M4 45%. Nothing ≥80%.

## 10. Next action

Sub-step 1.0: write the 14-row baseline table into `reference.md`. Then M1 RED: `tests/test_grammar.py`, 26 cases, watch it fail.

## 11. What revisions 1 and 2 got wrong (do not repeat)

**Revision 1:** claimed `### Step` canonical (spec has zero occurrences); claimed "10 working files unchanged" (only 3 are — the criterion would block its own milestone); missed `Milestone.number: int` (the grammar as specified **crashes** `aa-ma-tui`); counted 3 grammars (there are 6, and #5 drives the HARD gate); asserted on 2 out-of-repo tasks; diagnosed C4 as missing-shellcheck (it is flaky, shellcheck is installed); `grep -c shellcheck >= 2` and `785+` both already true; called fenced headings a critical gap (measured zero).

**Revision 2:** left `grammar.py`'s API undefined (two predecessors return different types); `discover_tasks(Path('.'))` raises `TypeError` — gated nothing; the "pinned table" it read did not exist; **2 of its 9 mandated negatives matched its own mandated regex** (bare `-` in the separator class); `int→str` silently broke 5 test files, a golden, and 3 `SCHEMA_VERSION == 1` assertions while M1's test command excluded `tests/tui/`; used `--root .` (23 junk entries); wrote `Audit-Profile`/`Critical-Path` mid-line and backticked so **both parsers read them as absent** — reproducing the exact defect M4 exists to fix; `yq` unavailable; `N_new` 22 vs 27 arithmetically unsatisfiable.

## 12. Engineering Standards Declaration

- **Theme 1 — Verification & Truth:** every figure in §2 came from executing the real parsers; eleven CRITICAL findings across two verification loops killed claims that read as obviously true. `Critical-Path: data-xform` (M1), `hook-modification` (M4), `Prototype-Required: YES` (M3).
- **Theme 2 — Development Principles:** TDD (RED before M1 and M4; M1 absorbs the rewire precisely so no milestone can pass green over a broken suite), DRY (6 grammars → 1 module + 1 aligned ERE; M3 reuses the existing skip-guard; `strip_fenced_blocks` mirrors `_strip_html_comments`), KISS (two regexes and two splitters), SOLID (`grammar.py` owns header structure, `plan_parsers.py` keeps field values).
- **Theme 3 — Reasoning & Planning:** strategic subagent use is load-bearing here — six verification angles found what three rounds of self-review did not. `Skill(systematic-debugging)` (M3) and `Skill(impact-analysis)` (M4) are named in the milestones; dispatches recorded in `provenance.log`.
- **Theme 4 — Safety & Continuity:** the non-breaking constraint is enforced by an exact pinned table rather than a prose claim. M4 exists solely because widening the readers without widening the gate scans would weaken a live safety check.
- **Theme 6 — Sync & Commit Discipline:** Result Log per sub-step immediately (L-080–L-082), HARD gates on M1 and M4, conventional commits with the `[AA-MA Plan]` footer, and the §2.5 field format so the gate can actually read what it is gating.
