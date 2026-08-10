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

## [2026-08-09] M3 root cause — the C4 flake (plan §3 M3 acceptance 5)

**The named hypothesis was wrong, and being wrong was cheap because it was
tested first.**

D5 recorded the C4 diagnosis as "flaky test, probably a SLUG collision on a
shared `/tmp` path". Sub-step 3.2 measured it: a 10-test probe replicating the
SLUG derivation verbatim showed `$$` **distinct on every single `setup()`**
(612456, 612463, 612470, …). bats 1.11 forks a fresh subshell per *test*, not
per file, so the PID component alone makes collision impossible; duplicates
across the run: 0. Refuted.

The real cause is not a flake in the ordinary sense — nothing about the test's
own state varies. A 25-run loop with `shellcheck` present failed 0 times. What
varies is whether the **binary resolves**, and that changed between invocations
earlier in this session (one `command -v shellcheck` returned nothing, which is
what produced the original "shellcheck isn't installed" misdiagnosis; it *is*
installed, at `/usr/bin/shellcheck` 0.11.0).

Confirmed by substitution rather than by waiting for a recurrence: a shadow PATH
containing symlinks to everything in `/usr/local/bin`, `/usr/bin` and `/bin`
**except** `shellcheck` — so `git`, `grep` and `python3` still resolve —
reproduces the reported failure exactly, down to the line:

```
not ok 1 C4 maps ShellCheck error to [CRITICAL]
# (in test file …/test_stage_c_dispatch.bats, line 147)
#   `[[ "$FINDINGS" == *"[CRITICAL]"* ]] || [[ "$FINDINGS" == *"[HIGH]"* ]]' failed
```

**The defect was never really in the test.** `sole-dev-merge.md:362` ran
`shellcheck -f json $CHANGED_SH > "$SHELLCHECK_OUT" 2>/dev/null || true`. That
`|| true` cannot distinguish *scanner ran and found nothing* from *scanner was
never installed*, and the second case makes Stage C report `0 findings` for
shell code nobody scanned. For a stage whose entire purpose is a security
review, that is a false negative shipped to users — the flaky test was the
symptom, and the only reason we ever saw it.

Fixed on both sides: the aggregator resolves `SHELLCHECK_BIN` and prints
`WARNING — '<bin>' not found; C4 did not run. Shell findings are UNKNOWN, not
zero.`; the test skips with the binary named instead of dying on a string match
20 lines away; CI pins the install so the skip path cannot be reached silently.

### Two things worth carrying forward

1. **`skip=0` is the assertion, not `notok=0`.** Adding a skip guard is the
   textbook way to make a red test green without fixing anything. The soak
   records all three counts per run — 20/20 at `ok=69 notok=0 skip=0` — so the
   evidence distinguishes "C4 passed" from "C4 was skipped 20 times".
2. **The same lesson as M1 and M2, third variant.** Both halves of this fix were
   verified in both directions before being believed: had the shipped code
   ignored `SHELLCHECK_BIN`, the test would have skipped while the code happily
   ran shellcheck anyway, and the guard would have been decorative. Measured:
   binary present → 4 findings / 3 CRITICAL; `SHELLCHECK_BIN=/nonexistent` →
   WARNING, 0 findings.

**Scope reduction, declared:** Sub-step 3.3's `BATS_TEST_TMPDIR` re-pathing was
**not** done. It existed only to defeat the collision that 3.2 refuted, and it
would have meant changing hardcoded `/tmp/` semantics in shipped code plus every
test asserting those paths. The half that was independently justified — a real
cleanup leak, 29 files after 25 runs, caused by three teardowns enumerating five
filenames while Stage D quietly grew a sixth — is fixed with a SLUG-keyed glob
sweep that cannot fall behind its writer. No M3 acceptance criterion required
the re-pathing.

## [2026-08-09] D9 — M3 scope extended to C3/bandit (user decision at the §6.8 panel)

Originally logged as "open, not actioned": `bandit` at `sole-dev-merge.md:337`
and both `python3` heredocs carried the same unguarded-dependency shape. I
deferred them as outside "fix the flaky C4 test" and surfaced the choice at the
§6.8 CRITICAL override panel. **Ste chose to fix now, same pattern.**

The auditors' case for treating this as the more serious half held up:

- `bandit` is **not a declared dependency** — absent from `pyproject.toml`, not
  installed by `uv sync`, and (before this change) not installed in the `bats`
  CI job, even though `test_smoke_e2e.bats` asserts a real B602 finding.
- `$BANDIT_OUT` is the trusted input to Stage D's B602 **auto-remediation**, so a
  silently-missing scanner disabled detection *and* fixing.

C3 now carries the identical contract to C4: `BANDIT_BIN` seam, `rc > 1 || empty
report` as the degraded condition, a `[HIGH] … UNKNOWN … (scanner-unavailable)`
sentinel written into `$FINDINGS`, and an unparseable-JSON sentinel in the
parser. Verified across both scanners × three modes each; mutation-tested in
both halves — reverting either sentinel to stdout-only fails the test by name.
CI installs and **version-asserts** both scanners.

Plan §3 M3 and §5 Artefacts amended accordingly.

**Still open, deliberately:** `sev_map.get(level, "LOW")` fails open — an unknown
severity from a future scanner version downgrades a real error to `[LOW]`, which
Stage D triages as a reviewer note. One word to change, but it alters a mapping
`reference.md` mirrors, so it wants its own change. Likewise the unpinned
scanner versions in CI and the predictable `/tmp` paths
(`SLUG="${SLUG:-$(date +%s)}"`, `: > "$FINDINGS"` with no `O_EXCL`).

## [2026-08-09T17:31:48Z] Compaction Summary (auto-generated by hook)
- Active step at compaction: Sub-step 2.4: Verify this plan's own artifacts pass
- Snapshot saved to: /home/sjnewhouse/.claude/hooks/cache/compaction-snapshots/milestone-grammar-ssot-snapshot.md
- Note: Context compacted. Reload AA-MA files to resume.

## [2026-08-10T09:51:33Z] Compaction Summary (auto-generated by hook)
- Active step at compaction: Sub-step 3.6: 20-run soak
- Snapshot saved to: /home/sjnewhouse/.claude/hooks/cache/compaction-snapshots/milestone-grammar-ssot-snapshot.md
- Note: Context compacted. Reload AA-MA files to resume.

## [2026-08-10] DECISION: the gate derives its subject strictly, and ambiguity is a refusal

**Context.** Sub-step 4.5 closed the "MILESTONE_TITLE is unset at gate time" CRITICAL
by wiring the §6.7 preamble to `aa_ma_extract_active_milestone`. That is the loosest
grammar in `aa-ma-parse.sh`: it opens a block on bare `/^## /`, takes the first match,
falls back to the first pending milestone, and always answers.

**What that cost.** Measured, not reasoned: with a stale second `Status: ACTIVE` the
gate derived `Milestone 2` and reported `PENDING=0 GATE=SOFT` while certifying a
milestone that was `PENDING=1 Gate: HARD` — exit 0. Every other defect this milestone
closed produced a false BLOCK. This one produced a **false PASS**, and it was
introduced by the fix for a different defect in the same milestone.

**Decision.** Two changes, both fail-closed:

1. `aa_ma_active_milestone_strict` — rc 0 exactly-one / 1 none / 2 unreadable /
   3 many-with-all-named — and §6.7 refuses on every non-zero. A gate that certifies
   the wrong subject is worse than one that refuses to certify at all.
2. `aa_ma_extract_active_milestone` recognises milestones via `AA_MA_MILESTONE_ERE`,
   removing the third grammar from a file whose purpose after M1 is to hold one.

**Why the tolerant reader survives at all.** It has a legitimate consumer:
`aa-ma-session-start.sh` wants a best-effort label for a briefing and is better off
guessing than saying nothing. The error was not that it is tolerant — it is that a
gate consumed a display helper. The two functions now differ in *contract*, not just
in regex, which is what stops the next caller repeating the mistake.

**Evidence discipline.** 4.5's lesson was that a by-hand probe verified the helper and
not the shipped path. So 4.6 was dogfooded by extracting the §6.7 preamble verbatim
from the command file (47 lines) and running it against four task directories, and
mutation-verified by reverting the derivation in that extract and watching the false
PASS reappear exactly.

**Scope held.** `aa_ma_extract_active_step` was found to carry the same defect one
level down: it opens on `/^### /` and never closes on `^## `, so a milestone-level
`Status: ACTIVE` is attributed to the last sub-step of the *previous* milestone. Live
evidence — this repo's own session briefing reads `step=[Sub-step 3.6: 20-run soak]`,
a COMPLETE sub-step of M3. It is display-only (no gate reads it) and the fix is one
awk line, but it was deliberately NOT folded in: undeclared scope growth is what got
M4 rejected once already. Left for user disposition.

**Not actioned, still open:** `sev_map.get(level, "LOW")` fails open; scanner versions
unpinned in CI; predictable `/tmp` paths in `/sole-dev-merge`; `.bash` files unlinted
in CI; `test_this_plans_own_milestones_all_parse` self-disables on archive.

## [2026-08-10] CORRECTION + DECISION: the step extractor was not display-only

**I called it display-only when deferring it. That was wrong**, and the evidence was
already in this plan's own provenance.log. `pre-compact-aa-ma.sh:89` feeds
`aa_ma_extract_active_step` into the `CHECKPOINT — ActiveStep:` line, which
`rules/aa-ma.md` designates as the session-resume signal. Two entries recorded the
wrong step: `Sub-step 2.4` while M3 was running, `Sub-step 3.6` while M4 was running —
in both cases the last sub-step of the milestone *before* the one being worked on,
which is the defect's exact signature. A resumed session was being pointed at
finished work.

**Root cause, same family as 4.6/4.7.** A block that opens and never closes: the
extractor opened on `/^### /` and had no rule for `^## `, so the first `Status:` line
after milestone N's last sub-step was milestone N+1's own milestone-level status.

**Second defect found by writing the test.** A genuinely `Status: ACTIVE` sub-step was
also unreachable — awk exits on the first ACTIVE, and the milestone's line came first.
So the function could never return an ACTIVE step that followed a completed milestone.
I had predicted one failing case and got three.

**Scope decision reversed, deliberately.** I deferred this rather than fold it into
4.6/4.7, on the grounds that undeclared scope growth is what got M4 rejected. That
reasoning holds — but "declare it and let the user decide" is the resolution, not
"leave a known defect in a shipped hook". The user's answer was to fix it, so it went
in as sub-step 4.8 with its own RED tests, corpus diff and mutation check rather than
as a quiet amendment to the previous commit.

**Verification standard held constant across 4.6/4.7/4.8:** measure the corpus before
changing anything, run the real callers rather than reasoning about them, and mutate
the fix to prove the guard is load-bearing. All 6 changed corpus rows were inspected
individually; every one is a correction.

## [2026-08-10] DECISION: revert 4.9–4.15 and rebuild gate enforcement on the Python SSoT

**The measurement that forced this.** Three §6.8 passes over three consecutive
windows of the same milestone:

| pass | window | distinct CRITICALs found |
|------|--------|--------------------------|
| 1st  | 4.1–4.5  | 8 |
| 2nd  | 4.6–4.8  | 4 |
| 3rd  | 4.9–4.15 (the remediation for those 4) | 9 |

The remediation round produced more CRITICALs than it closed, and seven of the
nine were introduced by the fixes themselves. That is a measured pattern across
three rounds, not a run of bad luck.

**What each round did.** 4.6 tightened the derivation and opened the indent
bypass. 4.10 tightened Status matching and opened the annotated-value bypass
(`- Status: ACTIVE (resumed after compaction)` — a form this repo's own corpus
uses 17 times). 4.12 unified the H2 predicate and opened bare-`##` block
truncation, hiding PENDING sub-steps, `Gate:` and `Critical-Path:` from three
separate enforcement points. Each fix was correct about its target and wrong
about the input space.

**The common factor, stated plainly.** Every round is a hand-written markdown
parser in awk, whose accepted-string set is decided by reasoning rather than by
measuring the corpus. `_aa_ma_field_re` was a *prefix* match for a reason I
never asked about; 4.10 replaced it with equality because equality felt more
precise. Meanwhile a correct, tested parser already exists in
`src/aa_ma/grammar.py` and is the declared SSoT of this very plan — and the
only thing pinning bash to it is a test that re-implements the recogniser a
third time in Python. Verified by mutation: two strong mutants (accept any
`## ` heading; make non-headings non-empty) both leave
`tests/test_grammar_parity.py` green at 7/7.

**The landmine that settled it.** `aa_ma_ms_title` takes `mre` as an implicit
awk global. Omitting `h2re` was loud — 25 test failures, fixed in minutes.
Omitting `mre` is silent: unset is the empty regex, which matches every line,
so `sub()` is a no-op and **every line becomes a milestone heading with a valid
title, exit 0, no diagnostic**. A shared abstraction whose failure mode is
"silently parse everything as a milestone", added to the file whose purpose is
preventing silent wrong parses.

**Decision.** Revert all of 4.9–4.15 to `d636824` and rebuild gate enforcement
on the Python SSoT: `/execute-aa-ma-milestone` §6.7/§7.1 call into `src/aa_ma/`
for the fields they enforce (which milestone is ACTIVE, PENDING count, `Gate:`,
`Critical-Path:`). Bash keeps only the advisory display hooks, where a wrong
answer is cosmetic rather than a false PASS. One parser, already tested, already
declared the SSoT. The cost is a Python dependency at gate time, which this repo
already has everywhere else.

**What the revert restores, deliberately and with eyes open.** `d636824` carries
four known, enumerated defects: the indent-bypass false PASS, the `awk -v`
escape-decoding false PASS, prompt injection via the session-start context line,
and `# HALT` being a comment so gate condition 1 prints BLOCKED then PASS with
exit 0. The judgement is that four *known* defects are a better base for a
rewrite than nine fresh ones — with one exception: the prompt injection is
re-applied immediately, corrected, because the user directed it be fixed ahead
of everything else and it fires automatically at session start.

**Not reverted:** the AA-MA artifacts. The Result Logs for 4.9–4.15 record what
was built and measured and stay as the audit trail; their `Status:` fields go
back to `PENDING` because the code no longer exists. Deleting the record would
lose the evidence that produced this decision.

**Repo is single-maintainer**, which is why a live revert on `main` is
acceptable rather than requiring a branch and a deprecation window.
