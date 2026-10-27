# §6.7 gate fences: what each one checks, its verdicts, and why its order is fixed

## Contents

- [Absent-field semantic (fence 1)](#absent-field-semantic-fence-1)
- [Fence 2 — §13 sigil edges verified](#fence-2--13-sigil-edges-verified)
- [Fence 3 — TESTS_VERIFIED](#fence-3--tests_verified)
- [Fence 4 — IMPACT_VERIFIED](#fence-4--impact_verified)

## Absent-field semantic (fence 1)

**Absent-field semantic** (M2.5 verification finding): when `Critical-Path:` or
`Prototype-Required:` is **absent** from a task, the corresponding check is
**skipped (no failure)**. Only present-but-without-evidence triggers a HALT.
This preserves backward compat with `examples/` plans authored before v0.5.0.

**Why fence 1 asks Python** (moved from the fence's comments, M11): the awk that once read the
milestone was a hand-written markdown parser whose accepted-string set was decided by reasoning,
not measurement; ADR-0009 records what three reviews found in it. So bash asks, Python answers:
`aa_ma_gate` is a launcher, not a parser; `aa-ma-gate` (`src/aa_ma/gate.py`) answers all seven
questions over `grammar.py` + `enforce.py` + `plan_parsers.py` and refuses on ambiguity rather
than choosing. The lib resolves repo-local first, so a clone that has not run install.sh works.
Exit codes fail closed: 0 one ACTIVE and every enforced field readable · 1 no ACTIVE ·
2 unreadable (missing file, unclosed fence, invalid field, orphan sub-step) · 3 ambiguous
(2+ ACTIVE, duplicate heading) · 127 the gate could not run (`aa_ma_gate` then prints only a
BLOCKED line, so `error=` lines are always the Python gate's own words). The dirty-artifacts
check `exit 1`s: it once was a `# HALT` comment that printed BLOCKED and then PASS with exit 0.
The Critical-Path / Prototype evidence greps are milestone-scoped: a bare
`grep -q CRITICAL_PATH_REVIEW` over the whole log is pre-satisfied once any milestone writes it.

## Fence 2 — §13 sigil edges verified

**§13 sigil edges verified — HARD, opt-in** (ADR-0015; Execution Checklist row in
`engineering-standards.md` §5). HARD ≠ `gate.py`: `aa-ma-gate` reads only `tasks.md`,
while §13 lives in `plan.md`, so this item is enforced here and the gate CLI, its kv
envelope and the gate fence (fence 1) are unchanged. It applies only when the plan's §13 carries
a sigil edge (`-->|"@import"|`, `-->|"@call"|`, …); a plan without one is a no-op.

| Lint says | Verdict |
|-----------|---------|
| `edges=0` | not applicable — no evidence written |
| `phantom>0` (`PHANTOM_EDGE` / `LABEL_UNKNOWN`) | BLOCKED — the diagram claims an edge the code does not hold |
| `invalid>0` — an edge to a missing file, a stale `(new)` on a file that exists, a path-less label, an unparsed edge form, a path outside the repo | BLOCKED — an authoring error the diagram can fix now |
| `index-unknown>0` (no, stale, too-old or unreadable index) | BLOCKED — the check did not run (L-012); run `codemem build` and re-run |
| no `sigils:` line / `sigils: UNKNOWN` (a sigil edge outside §13's views, an unterminated fence) / the lint did not run | BLOCKED — not every sigil edge could be read |
| otherwise | PASS — appends `[ts] DIAGRAM_VERIFIED — <milestone heading> — edges=N checked=C phantom=0 unknown=K` |

What still passes, counted in `unknown=K`: a claim that cannot be checked *yet* — a
genuinely planned `(new)` file, a plugin sigil (`@skill`/`@command`/`@agent`/`@hook`), a
language the graph does not model. `checked=C` is how many edges were actually compared
with the code. The fence run is the check; the `DIAGRAM_VERIFIED` line is its record.
This fence must stay AFTER the gate fence (fence 1): `tests/hooks/aa-ma-gate-python.bats`
(`_gate_fence`) executes the *first* ```bash fence after the `### 6.7 ` heading, and
`tests/hooks/test_diagram_verified.bats` asserts the order.

## Fence 3 — TESTS_VERIFIED

Implemented by `scripts/tests-verified.sh`; tested by `tests/hooks/test_tests_verified.bats`.
It is the THIRD ```bash fence in §6.7: the two fences above keep their places, because
`aa-ma-gate-python.bats` runs the first and `test_diagram_verified.bats` the second.

**Inputs, from the merge-base copy of `<task>-reference.md`** (`git merge-base <origin/HEAD | main | master> HEAD`),
so a branch cannot change the command or the pass rule that prove it (the branch still controls
the code and test configuration under test). That guard is only as upstream as the base: with no
`origin/HEAD` the base is a local `main`/`master` this session can change (on `main` itself the
plan is self-authored), so the fence prints a NOTE and the line gains an
`inputs: local <ref> (no origin/HEAD) — ` segment before `passed=`. A reference.md new on the branch has no merge-base
copy: if the default branch has it (this branch forked before the plan existed), that copy is used;
otherwise the plan is new and its HEAD copy, then its uncommitted working-tree copy, is used,
with a notice (a brand-new plan is self-authored either way). The argv split runs `python3 -I`, so a
`shlex.py` in the repo cannot replace the standard library's:

| Line | Meaning |
|------|---------|
| `Test-Command: <cmd>` | The command, run as a shlex argv (never `bash -c`). Absent → `uv run pytest`. ``; \| & $ ` < >`` are rejected. |
| `Test-Command-Pass-Regex: <ERE>` | Optional, for a runner other than pytest. Group 1 must capture the pass count. |
| `Test-Command: none — <reason>` | Opt-out. Needs, in context-log.md: `## [date] GATE APPROVAL: Test-Command none — <milestone heading>` then `- Decision: APPROVED`. |

A repeated line, an empty value or an invalid regex is BLOCKED before anything runs.

**Verdicts** (timeout `${AA_MA_TEST_TIMEOUT:-540}` s; a test that ignores SIGTERM is killed
`${AA_MA_TEST_KILL_AFTER:-30}` s later, via `timeout -k`; GNU `timeout` exits 124 on the timeout and
137 = 128 + SIGKILL when the kill was needed — see `timeout(1)`; 540 s stays under the Claude Code
Bash tool's 600 s cap):

| Outcome | Verdict |
|---------|---------|
| rc 0, default: the final non-empty line, `=` banner stripped, matches `(^|, )([0-9]+) passed` | PASS — `passed=N` |
| rc 0, Pass-Regex: the LAST output line matching it gives an all-digit group 1 | PASS — `passed=N` |
| rc 0 but no such line, or group 1 not a number | BLOCKED |
| rc ≠ 0 (rc 5 also names the opt-out) | BLOCKED — fix the tests and re-run; no auto-rerun |
| timeout (rc 124, or 137 after the kill) | BLOCKED — raise the timeout, run in the background |
| rc 126 / 127 (the command cannot start) | BLOCKED — a configuration error, named as such |
| provenance.log unwritable, or a symlink / non-file at append time | BLOCKED — never a PASS without its line |
| opt-out with its GATE APPROVAL | `TESTS_VERIFIED — <heading> — skipped: <reason>` |

Why the LAST matching line, not the final line: real testthat 3.2.3 run through `Rscript` printed a
praise line after its `[ FAIL 0 | WARN 0 | SKIP 0 | PASS 2 ]` summary in 1 of 8 passing runs.
Residual risk: a runner that exits 0 on failure AND prints an earlier line matching the regex.
Write the regex to require zero failures, as `\[ FAIL 0 \| … PASS ([0-9]+) \]` does.

## Fence 4 — IMPACT_VERIFIED

Implemented by `scripts/impact-verified.sh` (the Python is `aa-ma-impact`, `src/aa_ma/impact.py`);
tested by `tests/hooks/test_impact_verified.bats` and `tests/test_impact.py`. It is the FOURTH
```bash fence in §6.7, after fence 3 (ticket T7; ADR-0009 scope). How to read a BLOCKED report
and fix it: [impact-gate.md](impact-gate.md).

**Window**: `aa_ma_milestone_base` = `git merge-base origin/<default> HEAD` (origin only); the
changed set is that base against the working tree (committed, staged, unstaged) plus untracked
files, minus `IMPACT_EXCLUDE` (`.claude/dev/**`, `docs/architecture/**`, `tests/golden/**`,
`uv.lock`, `CHANGELOG.md`). No window (on the default branch tip, no origin) is BLOCKED for a
plan in force; the grandfather check runs first, so an older plan still reads "not applicable".

**Why fence 3 and fence 4 take different bases** (Ste, M11 §6.6): fence 3 reads its *inputs*
(`Test-Command:`) from the merge-base with `aa_ma_default_base_ref`, which falls back to a local
`main`/`master` with a NOTE and an `inputs: local …` segment — the command is what matters, and a
self-authored plan on `main` still runs its tests. Fence 4 certifies a *window*, so its base must
be one this session cannot move: `aa_ma_milestone_base` reads origin only and refuses an
`origin/HEAD` that points at the branch itself. Both fences share their scaffolding
(`scripts/fence-common.sh`).

| Check | Needs |
|-------|-------|
| Changed, no Contract row names it (a directory row covers beneath) | `Impact-Explained: <path> — <reason>` in the milestone's tasks.md block |
| A Contract row whose path did not change | the same |
| codemem co-change partner (≥5 shared commits and ≥50% of the file's, last 500 commits; import/call-linked files excluded) that did not change | the same |
| griffe public-API break in `aa_ma` / `codemem` | `API-Break: <dotted.path> — <reason>` in the Contract |
| A derived Critical-Path value (`CRITICAL_PATH_GLOBS`) | a `CRITICAL_PATH_REVIEW` line for the milestone naming each file or its glob |

| `aa-ma-impact` rc | Fence |
|------|-------|
| 0 | PASS — appends `[ts] IMPACT_VERIFIED — <heading> — changed=N predicted=P cochange=C unexplained=0 api_diff=<summary>` |
| 5 | `IMPACT-GATE: not applicable (grandfathered)` — plan `Created:` before `IMPACT_CUTOVER`, read from the merge-base plan (a plan new on the branch: its own date, never before the base commit) |
| 1 | BLOCKED — lists `unexplained_file=`, `api_break=`, `unreviewed_cp=`; also a stale codemem answer |
| 2 | BLOCKED — usage, unreadable input, git error, no milestone window |
| 3 | BLOCKED — codemem index missing, or a refresh failed or was skipped (`codemem build`) |
| 127 | BLOCKED — uv missing or the CLI did not run |

Overrides: `Cochange-Threshold: <n> <ratio>` in the merge-base reference.md (n ≤ 20, ratio ≤ 0.9)
with `## [date] GATE APPROVAL: Cochange-Threshold <n> <ratio> — <milestone heading>`.

