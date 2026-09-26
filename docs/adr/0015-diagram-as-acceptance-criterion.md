# 0015. The diagram as an acceptance criterion: a HARD §6.7 item, not a gate question

**Status:** Implemented
**Date:** 2026-09-25
**Deciders:** Stephen Newhouse (sole maintainer)
**Tags:** `diagrams`, `gate`, `enforcement`, `execute-aa-ma-milestone`

## The distinction this rests on: HARD ≠ `gate.py`

ADR-0009 made `aa-ma-gate` (`src/aa_ma/gate.py`) the single source of truth for the
questions the milestone gate asks of `tasks.md`. It does **not** make it the only HARD
enforcement. The Execution Checklist (`claude-code/rules/engineering-standards.md` §5)
already carries HARD items the gate never answers — tests pass, git clean, a
`CRITICAL_PATH_REVIEW` entry in `provenance.log`. This ADR adds one more of those. It
does not contradict ADR-0009 or ADR-0010: the gate binary, its kv envelope and every
fence that calls it are unchanged.

## Context and Problem Statement

diagram-generation M8 gave `plan.md` §13 opt-in sigil edges — `A -->|"@import"| B`,
`-->|"@call"|` — that `aa-ma-lint-views` checks against the codemem graph, reporting a
false claim as `PHANTOM_EDGE`. The lint's exit code is deliberately non-blocking for an
unevaluable claim (`UNKNOWN` ⇒ exit 0, map Ticket 2), so CI and consumer repos are not
punished for having no index. Nothing, however, stopped a milestone from being marked
COMPLETE while its own diagram claimed an edge the code does not hold.

**Should a §13 sigil edge that is false — or that nobody could check — block milestone
COMPLETE, and where is that enforced?** (Map Ticket 15.)

## Decision Drivers

- `aa-ma-gate` takes one input, `tasks.md`; §13 lives in `plan.md` only.
- L-012: a check that did not run is never a pass.
- Opt-in all the way up (Ticket 5): a plan without sigils must never be touched.
- A refusal must name its remedy; a wall with no door gets bypassed.
- Three bats suites extract the *first* ```bash fence after `### 6.7 ` — any new fence
  that lands before it silently changes what 58 tests execute.

## Considered Options

1. **An eighth `aa-ma-gate` question.** Needs a second input file, a kv envelope
   schema change and an edit to every calling fence, all under
   `Critical-Path: hook-modification` — and it puts a planning-time artifact (§13) into
   the binary ADR-0009 kept to `tasks.md`.
2. **A HARD §6.7 Execution Checklist item enforced by the command.** A second fence
   after the gate fence runs the lint and reads its verdict.
3. **Nothing** — keep the lint advisory.

## Decision Outcome

**Chosen option: 2.** `/execute-aa-ma-milestone` §6.7 gains a second ```bash fence,
placed after the gate fence. It resolves the ACTIVE milestone's heading through
`aa_ma_gate`, runs `aa-ma-lint-views` on `plan.md`, and reads one summary line the lint
now prints before `render:`:

```
sigils: edges=<N> phantom=<P> unknown=<K> index-unknown=<I>
```

| Lint says | Verdict |
|-----------|---------|
| `edges=0` | not applicable — no evidence written |
| `phantom>0` (`PHANTOM_EDGE` + `LABEL_UNKNOWN`) | BLOCKED |
| `index-unknown>0` — no, stale, too-old or unreadable index | BLOCKED; the refusal names `codemem build` |
| no `sigils:` line, `sigils: UNKNOWN` (§13 hidden by an unterminated fence), lint exit 2 | BLOCKED |
| otherwise | PASS; appends `[ts] DIAGRAM_VERIFIED — <milestone heading> — edges=N phantom=0 unknown=K` to `provenance.log` |

The evidence line has the shape of `CRITICAL_PATH_REVIEW` and `PROTOTYPE`, so the §5
Verification column stays uniform.

### Two amendments made at execution (Ste, 2026-09-25)

1. **Only an index UNKNOWN refuses.** The map said "`UNKNOWN` refuses". Measured on
   this plan's own §13 first: 23 sigil edges, 19 `UNKNOWN`, none from the index — 17
   `endpoint planned (new)` and 2 path-less labels. Every multi-milestone plan that draws
   a planned file with a sigil has such claims until its last milestone, so the literal
   rule would have blocked this very milestone. L-012 is about a check that *did not
   run*; that is the index class alone (missing, schema too old, stale, unreadable —
   every such reason names `codemem build`). Per-claim `UNKNOWN`s — a `(new)` endpoint,
   a path-less label, a plugin sigil (until M13), a file the graph does not model —
   pass and are counted in `unknown=K`, so the evidence says how much was not checked.
2. **The count comes from the lint, not a grep.** A grep over `plan.md` counted 25
   sigils where §13 holds 23 (two sit in acceptance-criteria prose), which would also
   make the opt-out wrong; a `python -c` over lint internals would ship untested code
   inside markdown. The lint already knows the answer, so it prints it. Exit codes
   unchanged; `LintReport.sigil_edges` is `None` when §13 was not read, so an
   unterminated fence can never pass as `edges=0`.

### Consequences

- Good: the diagram is an acceptance criterion with teeth, and only for plans that
  opted in by writing a sigil. The refusal is a one-command fix.
- Good: `gate.py` untouched — `aa-ma-gate --format kv` output over the 33-file corpus
  is identical to before.
- Bad: a second fence in §6.7 depends on fence order. Mitigated by
  `tests/hooks/test_diagram_verified.bats`, which executes the shipped fence and asserts
  the first fence is still the gate fence.
- Bad: `(new)` endpoints stay unchecked until built. Accepted: they are counted, and
  dropping `(new)` once a file exists turns the claim into a checked one.

## More Information

- Map Ticket 15 (`diagram-generation-map.md`); plan Milestone 11.
- ADR-0009 (gate SSoT), ADR-0010 (architecture views), ADR-0014 (the sqlite seam).
- `engineering-standards.md` §1 `hook-modification` now also names
  `.github/workflows/**` — a doctrine-consistency fix made in the same milestone.
