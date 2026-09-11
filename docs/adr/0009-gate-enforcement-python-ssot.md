# 0009. Gate enforcement reads the Python SSoT; bash keeps display readers only

**Status:** Implemented
**Date:** 2026-09-11
**Deciders:** Stephen Newhouse (sole maintainer)
**Tags:** `aa-ma`, `hooks`, `enforcement`, `grammar`

## Context and Problem Statement

`/execute-aa-ma-milestone` refuses or passes a milestone on the answers to
seven questions about `[task]-tasks.md`: which milestone is ACTIVE (and its
exact heading), how many of its sub-steps are still PENDING, whether its
`Gate:` is HARD, whether it declares `Critical-Path:` or `Prototype-Required:`,
and — for `verify-impl` — a milestone's `Audit-Profile:` by number. Until
milestone-grammar-ssot M4 those answers came from awk ranges in the command
file that had never worked (`awk "/^## Milestone.*$T/,/^## Milestone/"`
self-terminates; `grep -A1` cannot reach a `Gate:` past a blank line), so the
gate had never refused anything.

M4 rebuilt the scans as a bash-side parser in `aa-ma-parse.sh`. Three
post-implementation adversarial reviews (§6.8) over three consecutive windows
of that work found **8, then 4, then 9** distinct CRITICALs — the third window
being the remediation of the second, with seven of its nine introduced by the
fixes themselves. Each fix was correct about its target and wrong about the
input space: tightening the ACTIVE derivation opened an indent bypass;
tightening Status matching to equality hid the annotated `Status: COMPLETE (…)`
form the corpus uses 24 times; unifying the H2 predicate opened a bare-`##`
truncation that hid PENDING sub-steps from three enforcement points; and an
implicit awk global whose unset value is the empty regex made every line a
milestone heading with exit 0 and no diagnostic.

Meanwhile a tested parser already existed: `src/aa_ma/grammar.py` was declared
the single source of truth for heading structure in M1, `tui/parser.py` reads
the fields, `plan_parsers.py` holds the canonical value sets. The only thing
pinning bash to Python was a test that re-implemented the recogniser a third
time — mutation-verified as blind (two strong mutants left it green).

How should the gate obtain its seven answers so that a wrong answer is a loud
refusal rather than a silent false PASS?

## Decision Drivers

- **Fail closed.** Every failure mode found across three reviews presented as a
  clean milestone. The one direction that must never occur is a false PASS.
- **One parser.** Hand-aligning a second markdown parser with the first did not
  converge in three rounds; a fourth round was not going to.
- **Reading intent vs enforcing form are different concerns.** `- Gate: hard`
  was a HARD gate in bash and a SOFT gate in Python; `**infra**` is rejected by
  the linter but is unambiguous to a reader.
- **Non-breaking for display.** `aa-ma-session-start.sh` and
  `pre-compact-aa-ma.sh` print a briefing line; a wrong answer there is
  cosmetic and a Python round-trip on every session start is unwelcome.
- **Testable as shipped.** The command file is markdown; a guard that greps it
  for a literal goes green when an edit adds quotes. The shipped text must be
  executed by tests.

## Considered Options

1. **Keep aligning bash with Python** — a fourth remediation round on
   `aa-ma-parse.sh`, plus a stronger parity test.
2. **Enforcement calls Python; bash keeps display readers** — `src/aa_ma/gate.py`
   answers the seven questions over `grammar.py` + a new strict `enforce.py` +
   `plan_parsers.py`; a bash launcher runs it; the enforcing awk is deleted.
3. **Everything calls Python, including the display hooks** — delete all awk.

## Decision Outcome

**Chosen:** Option 2.

**Rationale:** Option 1 is the measured non-convergence. Option 3 buys nothing
the drivers ask for and costs a `uv run` on every session start and every
compaction, in hooks whose worst failure is a wrong line of prose. Option 2
puts the one parser at the one place a wrong answer matters, and lets the
launcher's failure mode be a loud refusal (rc 127, "a gate that cannot run
must not pass") rather than a skip.

Two contract decisions fell out of the review that follow the same principle:

- **`enforce.py` normalises rather than rejects.** Leading token, bold
  stripped, case-folded, then canonical membership. Reading *intent* is the
  gate's job; enforcing that plans are *written* canonically is the M2 linter's
  (`grammar.find_non_canonical`). What it cannot read — a typo value, an
  asterisk bullet, an NBSP, an empty value — it refuses with the line quoted,
  and the candidate pattern is deliberately wider than the accept pattern so
  those forms are *found and refused* rather than reported absent.
- **`grammar.split_milestones` closes on any H2.** Bash had this right (4.2);
  Python absorbed a trailing `## Summary Counts` into the last milestone. Fixed
  in the SSoT for both consumers rather than patched at the gate.

## Pros and Cons of the Options

### Option 1 — keep aligning bash

- ✅ No Python dependency at gate time
- ❌ Three rounds of measured non-convergence; each round's accepted-string set
  was decided by reasoning, not measurement
- ❌ The parity test that was supposed to pin the two was mutation-blind

### Option 2 — enforcement calls Python (chosen)

- ✅ One parser, already the declared SSoT, already tested; the exploit
  fixtures from all three reviews become its test corpus
- ✅ Refusal on ambiguity is natural in Python (`exit 3`, all candidates named)
  and awkward in awk
- ✅ Display hooks untouched
- ❌ `uv` and Python required wherever `/execute-aa-ma-milestone` runs — true
  of everything else in this repo, and the launcher makes absence a refusal

### Option 3 — everything calls Python

- ✅ Zero awk anywhere
- ❌ Python round-trip in every session-start and pre-compact hook
- ❌ No driver asks for it; display readers have no false-PASS failure mode

## Consequences

**Positive:**
- The gate refuses on: no/2+ ACTIVE, duplicate headings, unreadable fields,
  unclosed fences, orphaned sub-steps, and the tool being unable to run.
  Measured on this repo's own plan, the shipped text counts its PENDING
  sub-steps correctly for the first time.
- Byte-exact titles: the heading reaches §7.1's `grep -F` through `key=value`
  lines, never through `awk -v` (which escape-processes) or `eval`.
- `Mode: TYPO` can no longer auto-dispatch a human-in-the-loop sub-step.

**Negative:**
- Python at gate time. Stated, tested (bats: `uv` absent → BLOCKED), and
  refused loudly rather than skipped.
- `aa-ma-parse.sh` lost 8 public/private functions in one release; the
  CHANGELOG records them as added-then-removed within `Unreleased`.

**Neutral:**
- `tests/hooks/aa-ma-gate-scans.bats` shrinks to guards on the awk that
  remains; `tests/hooks/aa-ma-gate-python.bats` executes the shipped fences.

## Implementation Notes

- `src/aa_ma/enforce.py` — `FieldRead`, `read_enforced_field`,
  `read_milestone_status`, `read_step_status`; canonical sets.
- `src/aa_ma/gate.py` — `answer(path, number=None, step=None)`, `main()`;
  console script `aa-ma-gate`; `--format json|kv`; exit codes 0/1/2/3/4.
- `claude-code/hooks/lib/aa-ma-parse.sh` — `aa_ma_gate` (launcher, rc 127 on
  cannot-run), `aa_ma_gate_field`; header states the DISPLAY/ENFORCING
  boundary. Rule: **file-derived data never crosses into awk via `-v`**, and
  no new awk is added for an enforcing question — add it to `gate.py`.
- Callers: `/execute-aa-ma-milestone` §5.2 (Mode), §6.7 (preamble + conditions
  1, 2, 5), §7.1 (reuses `${GATE}`); `verify-impl` Step 1;
  `plan-verification` Angle 6 check #2.
- Contract (18-row form table, exit codes, seven questions):
  `.claude/dev/active/milestone-grammar-ssot/milestone-grammar-ssot-reference.md`
  "M5 enforcement contract", to be archived with the plan.
