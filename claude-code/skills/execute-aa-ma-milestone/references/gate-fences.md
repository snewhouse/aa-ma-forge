# §6.7 gate fences: what each one checks, its verdicts, and why its order is fixed

## Contents

- [Absent-field semantic (fence 1)](#absent-field-semantic-fence-1)
- [Fence 2 — §13 sigil edges verified](#fence-2--13-sigil-edges-verified)
- [Fence 3 — TESTS_VERIFIED](#fence-3--tests_verified)

## Absent-field semantic (fence 1)

**Absent-field semantic** (M2.5 verification finding): when `Critical-Path:` or
`Prototype-Required:` is **absent** from a task, the corresponding check is
**skipped (no failure)**. Only present-but-without-evidence triggers a HALT.
This preserves backward compat with `examples/` plans authored before v0.5.0.

## Fence 2 — §13 sigil edges verified

**§13 sigil edges verified — HARD, opt-in** (ADR-0015; Execution Checklist row in
`engineering-standards.md` §5). HARD ≠ `gate.py`: `aa-ma-gate` reads only `tasks.md`,
while §13 lives in `plan.md`, so this item is enforced here and the gate CLI, its kv
envelope and the fence above are unchanged. It applies only when the plan's §13 carries
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
This fence must stay AFTER the gate fence above: `tests/hooks/aa-ma-gate-python.bats`
(`_gate_fence`) executes the *first* ```bash fence after the `### 6.7 ` heading, and
`tests/hooks/test_diagram_verified.bats` asserts the order.

## Fence 3 — TESTS_VERIFIED

Implemented by `scripts/tests-verified.sh`; tested by `tests/hooks/test_tests_verified.bats`.
It is the THIRD ```bash fence in §6.7: the two fences above keep their places, because
`aa-ma-gate-python.bats` runs the first and `test_diagram_verified.bats` the second.

**Inputs, from the merge-base copy of `<task>-reference.md`** (`git merge-base <origin/HEAD | main | master> HEAD`),
so a branch cannot change what proves it:

| Line | Meaning |
|------|---------|
| `Test-Command: <cmd>` | The command, run as a shlex argv (never `bash -c`). Absent → `uv run pytest`. `; \| & $ ` < >` are rejected. |
| `Test-Command-Pass-Regex: <ERE>` | Optional, for a runner other than pytest. Group 1 must capture the pass count. |
| `Test-Command: none — <reason>` | Opt-out. Needs, in context-log.md: `## [date] GATE APPROVAL: Test-Command none — <milestone heading>` then `- Decision: APPROVED`. |

A repeated line, an empty value or an invalid regex is BLOCKED before anything runs.

**Verdicts** (timeout `${AA_MA_TEST_TIMEOUT:-540}` s):

| Outcome | Verdict |
|---------|---------|
| rc 0, default: the final non-empty line, `=` banner stripped, matches `(^|, )([0-9]+) passed` | PASS — `passed=N` |
| rc 0, Pass-Regex: the LAST output line matching it gives an all-digit group 1 | PASS — `passed=N` |
| rc 0 but no such line, or group 1 not a number | BLOCKED |
| rc ≠ 0 (rc 5 also names the opt-out) | BLOCKED — fix the tests and re-run; no auto-rerun |
| timeout (rc 124) | BLOCKED — raise the timeout, run in the background |
| opt-out with its GATE APPROVAL | `TESTS_VERIFIED — <heading> — skipped: <reason>` |

Why the LAST matching line, not the final line: real testthat 3.2.3 run through `Rscript` printed a
praise line after its `[ FAIL 0 | WARN 0 | SKIP 0 | PASS 2 ]` summary in 1 of 8 passing runs.
Residual risk: a runner that exits 0 on failure AND prints an earlier line matching the regex.
Write the regex to require zero failures, as `\[ FAIL 0 \| … PASS ([0-9]+) \]` does.
