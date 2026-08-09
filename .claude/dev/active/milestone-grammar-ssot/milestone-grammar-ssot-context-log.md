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

## [2026-08-09] GATE APPROVAL: Milestone 1 — Shared grammar, type fix and TUI rewire

- **Gate:** HARD
- **Approved by:** Stephen J Newhouse (via /execute-aa-ma-milestone §7.3)
- **Criteria verified:** 9/9
  1. ✅ `pytest tests/codemem/ tests/tui/ tests/test_grammar.py` exit 0 — the originally-failing `test_audit_profile_absence_is_valid_for_pre_v080_corpus[sole-dev-merge-pr-workflow]` now passes
  2. ✅ `pytest -m slow tests/tui/` exit 0 (scoped — `test_bench_harness` fails on the clean baseline, a third pre-existing failure)
  3. ✅ 15 positive / 12 negative cases, negatives asserted through the splitters
  4. ✅ `grep -rnE "\b_split_milestones\b" src/ tests/` empty
  5. ✅ Per-file counts match every b11c46d row of the reference table
  6. ✅ `discover_tasks([active, completed])` → 15 tasks, no `ValueError`
  7. ✅ 4 blind tasks restored: codemem 5/47, harden-aa-ma-plan 5/24, skill-ecosystem-integration 3/26, sole-dev-merge-pr-workflow 5/42; zero tasks report 0 milestones
  8. ✅ `SCHEMA_VERSION == 2` + CHANGELOG BREAKING entry
  9. ✅ `bats -F tap --recursive tests/hooks/` → 119 ok, 0 not ok
- **§6.7 Engineering Standards gate:** 5/5 PASS — artifacts synced, zero PENDING in M1, tests pass, IMPACT_ANALYSIS + CRITICAL_PATH_REVIEW (data-xform) in provenance; `Prototype-Required` absent on M1 → skipped per absent-field semantic
- **§6.8 Post-Impl Adversarial Review:** initial 6 CRITICAL / 22 WARNING / 11 INFO → all CRITICAL fixed inline → **PASS_WITH_WARNINGS**. Detail in `impl-review.md`
- **Decision: APPROVED**

### What the §6.8 slate caught that I had already declared verified

Worth recording, because the pattern repeated from the planning phase: claims I *reasoned* to failed; claims I *measured* held.

- `coerce_numbers_to_str=True` is model-wide, not field-scoped — it silently laundered `title=42` into `"42"` and masked six unmigrated call sites. Dropped; migration completed properly.
- Flat fence pairing emitted **phantom milestones** from nested code blocks, and headings inside HTML comments parsed as real. The templates this project ships are full of both.
- The fence regex was **O(n²)** — 78 KiB → 5.15 s. Meanwhile the ReDoS I *suspected* (`(?:\.\d+)*`) measured strictly linear. I had the risk in the wrong place.
- My own AC#7 verification silently `jq`-filtered out the 15th task — the row that would have failed the "matches exactly" criterion I wrote.

**Lesson for the remaining milestones:** a verification command that filters its own input is not verification. Pin the filter in the criterion, or assert on the unfiltered set.


## [2026-08-09] D8 — M2 scope expanded from 1 writer to 11

Plan §3 M2 scoped a single file, `claude-code/rules/aa-ma.md:78`. That was wrong,
and the §6.8 review on M1 predicted it.

Surveying the actual writer surface found **eleven** shipped files that write or
teach a tasks.md heading, of which exactly one — `docs/templates/tasks-template.md`
— was already canonical. Fixing only `rules/aa-ma.md` would have left the scribe,
the `/aa-ma-plan` Phase 5 template, the spec, the team guide and the README all
emitting a form the new lint rejects: writer and linter disagreeing by
construction, with the next authored plan failing on arrival.

Two of those were worse than merely non-canonical. `docs/spec/aa-ma-specification.md:518,526`
and `claude-code/skills/aa-ma-execution/SKILL.md` taught **unnumbered** forms
(`## Task Title`, `### Sub-step: [Action]`) that match neither the tolerant reader
nor the canonical writer — so a plan authored from the spec parsed as zero
milestones and zero steps while passing the lint silently. `examples/aa-ma-team-guide/`
had the same shape. That is the failure class M1 existed to kill, shipped in the
spec itself.

**Plan §3 M2 and §5 Artefacts are amended accordingly** — per `rules/aa-ma.md`,
scope change is one of the few legitimate reasons to edit plan.md.

### The more important correction

The first version of the writer guard was **inert**. `find_non_canonical` calls
`sanitize()`, which strips fenced blocks — and every writer template lives inside
a ```markdown fence. Both §6.8 agents caught it independently; the
future-proofing agent mutation-tested it and found 4 of 5 checks passing green
against the exact drift they existed to catch. The Sub-step 2.4 Result Log had
already claimed divergence "cannot silently return".

Fixed by linting fenced-block *contents* (`grammar.iter_fenced_blocks`), and —
because a documentation file's own `### Step 3: Dispatch agents` section is prose
rather than tasks.md content — linting **only** inside fences when fences exist.
Every writer now carries `test_writer_check_is_not_vacuous`, which corrupts the
file and asserts a violation appears. Re-verified by mutation: 5/5 caught, where
4/5 were previously missed.

**Lesson, and it is the same one as M1:** a guard that has never been observed to
fail is not a guard. Assert the positive case — corrupt the input and require the
check to complain — or the green tick means nothing.

## [2026-08-09T17:31:48Z] Compaction Summary (auto-generated by hook)
- Active step at compaction: Sub-step 2.4: Verify this plan's own artifacts pass
- Snapshot saved to: /home/sjnewhouse/.claude/hooks/cache/compaction-snapshots/milestone-grammar-ssot-snapshot.md
- Note: Context compacted. Reload AA-MA files to resume.
