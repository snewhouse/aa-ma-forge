# milestone-grammar-ssot Context Log

## [2026-08-09] Initial context

**Origin.** After the Biorelate identifier scrub (`b11c46d`), two pre-existing test failures were reported as blocking clean gates for future work. Planning them turned up a defect substantially larger than either failure.

**Feature request (verbatim intent):** fix `test_corpus_grandfathering[sole-dev-merge-pr-workflow]` and the C4 ShellCheck bats failure before starting new work.

## Decisions

### D1 — Tolerant readers, strict writer

Corpus has 4 milestone styles and 3 step keywords against a spec mandating one. Options weighed: normalize the archives (rejected — CLAUDE.md freezes historical docs, and drift recurs with nothing enforcing it); widen parsers only (rejected — no guard against new drift). **Chosen:** one shared tolerant grammar for reading, plus a lint enforcing canonical form on `.claude/dev/active/`. Postel's law.

### D2 — Fix all consumers, not just the failing test

The failing test was the symptom. `aa-ma-tui` drops 4 of 14 repo tasks entirely and shows 0 steps for 6 more — the tracker built by ADR-0007 is blind to 30% of its own corpus. Fixing only the test would have left that latent.

### D3 — Grammar lives in a new `src/aa_ma/grammar.py`

`plan_parsers.py` parses *field values*; header structure is a different concern (SOC). The TUI imports grammar without dragging in enum-validation code it never uses.

### D4 — Canonical step keyword is `Sub-step`

**Revised during verification.** The plan first claimed `### Step` was canonical, justified by "template + spec + 10-file majority". All three were false: `docs/templates/tasks-template.md:89,127,147,155` ship `Sub-step`, `aa-ma-specification.md` contains **zero** `### Step` occurrences, and the corpus splits 6/5/3 with no majority. Chosen `Sub-step` so the writer (scribe, working from the template) and the linter agree by construction — otherwise the lint fails this plan's own artifacts.

### D5 — M4 rescoped from "missing dependency" to "flaky test"

The C4 diagnosis was wrong. `shellcheck` **is** installed (0.11.0); C4 passes alone and passed 3/3 full-suite runs, having failed twice earlier the same session. Rescoped to a systematic-debugging milestone with a 20-run soak as the gate, since one green run proves nothing about an intermittent failure.

### D6 — M1 and M2 merged

Verification showed the type change and the parser rewire are inseparable: changing `Milestone.number` without rewiring leaves the new type unreachable, and rewiring without it crashes. Split across milestones, M1 would have passed a HARD gate green while the suite was broken.

### D7 — M4 (HARD-gate scans) added

Not in the original scope. Widening the readers while `execute-aa-ma-milestone.md`'s awk scans stay blind to `## M1:` and em-dash styles would leave the HARD gate reporting zero `Status: PENDING` on milestones that have them. A safety regression, so it became a milestone rather than a TODO.

## Verification history

Phase 4.2 eng review + two Phase 4.5 automated loops (6 angles). **11 CRITICAL, 19 WARNING.** Full detail in `verification.md`.

The most instructive finding was self-referential: running the real parsers against the plan's own text returned `Audit-Profile: (None, True, None)` for all five milestones, and the `Critical-Path` gate scan read empty — the plan reproduced, in its own artifacts, the exact blindness its own M4 exists to fix. Fields were written mid-line and backticked; `plan_parsers._extract_field` anchors `^[ \t]*-?[ \t]*` and `execute-aa-ma-milestone.md:520` requires the bold line-anchored form. Now pinned in `reference.md`.

Other findings that changed the plan materially:

- `int(m.group(1))` at `parser.py:172` against a grammar admitting `2a` and `3.5` → unhandled `ValueError` (not `ParseError`), crashing `aa-ma-tui`. The plan as first written would have broken the tool it was fixing.
- The separator class `[:–—-]` included a bare hyphen, so `### Step 1.1-alpha:` — a *mandated negative case* — matched the *mandated regex*. Fixed to require a space-delimited dash.
- `--root .` returns 23 junk entries (every top-level directory), not the 14 tasks. `--root .claude` is correct.
- Acceptance criteria that gated nothing: `grep -c shellcheck >= 2` (already true), `785+` (a monotone floor), `discover_tasks(Path('.'))` (raises `TypeError` before and after), and a `yq` assertion (`yq` isn't installed here or in CI).

**Assumptions recorded as unvalidated:** M3's SLUG-collision hypothesis is unproven — Sub-step 3.2 tests it before any fix, and a refutation is recorded as a finding rather than treated as failure.

## Open questions

- Whether the `aa-ma-parse.sh` over-tolerance (`## Status: COMPLETE` parsing as a milestone heading) deserves its own fix. Deliberately not pinned as a contract in M1's bats case so a future correctness fix isn't blocked as a "regression".
- Whether `hook-modification` should formally cover shipped commands and skills, not just `hooks/*.sh`. M4 Sub-step 4.4 widens it; if that's rejected, this plan's own M4 Critical-Path value is out of scope for the rule.
