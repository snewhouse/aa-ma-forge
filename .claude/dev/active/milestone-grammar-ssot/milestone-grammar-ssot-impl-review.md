# §6.8 Post-Impl Adversarial Review — Milestone 1

Audit-Profile: `code-only` · Plan `Created: 2026-08-09` (post-v0.8.0 cutover) · Window: working tree vs `77e38d4`
Agents dispatched: code-reviewer, security-auditor, tdd-sequence-auditor, future-proofing-auditor.
context7-evidence-auditor: **N/A** — zero dependency additions or version bumps in this milestone.

## Verdict: PASS_WITH_WARNINGS (after inline fixes)

Initial: **6 CRITICAL, 22 WARNING, 11 INFO**. All 6 CRITICAL fixed inline; suite 819 passed / 0 failed.

## CRITICAL — all fixed

| # | Finding | Fix |
|---|---|---|
| C1 | `coerce_numbers_to_str=True` is **model-wide**, not field-scoped. Reproduced: `Milestone(title=42)` → `'42'`; `dependencies=7` → `'7'`. Also permanently masked the migration — 6 sites still passed ints. | Config dropped entirely; all `Milestone(number=<int>)` sites converted to str. Explicit over clever. |
| C2 | `_FENCE_RE` paired fences **flat**, so nested fences emitted phantom milestones. Reproduced: a 4-backtick block containing a 3-backtick block yielded 2 phantom milestones. | Replaced with a CommonMark line scanner: same-char + length-based close, unterminated runs to EOF, `~~~` supported. |
| C3 | Headings inside **HTML comments** parsed as real. Reproduced: `<!--\n## Milestone 9: commented out\n-->` → a milestone. `docs/templates/tasks-template.md` has ten comment blocks. | New `sanitize()` composes fence stripping with `plan_parsers._strip_html_comments`. |
| C4 | plan.md AC#9 pinned `--recursive ... exactly 113 ^ok`; recursive baseline is 118 (+6 in `fixtures/build_active_dir.bats`). The HARD gate's own criterion was unsatisfiable. | Corrected to 119; reference.md now records 112/118 as-of-b11c46d and 113/119 after M1. |
| C5 | `passed == 784 + 32` is **self-invalidating** — archiving this very plan adds 2 parametrized cases to `test_corpus_grandfathering`. | Replaced with `failed == 0 and errors == 0` plus a scoped per-milestone delta. |
| C6 | `--root .claude` now returns **15** tasks (this plan's own dir), so AC#5/#7's "14/14, matches exactly" was unsatisfiable. My own verification had silently filtered the row out with `jq`. | Table reframed as "measured at b11c46d; every listed row must match, rows added later are out of scope". |

## Notable WARNINGs actioned

- **ReDoS (security):** `_NUM_S`'s `(?:\.\d+)*` measured **linear** — my suspicion was wrong (6.4 KB → 259 µs). The real defect was `_FENCE_RE`: **O(n²)**, 78 KiB of language-tagged fences → **5.15 s** through `parse_task_dir`, because a ```` ```python ```` line can open a fence but never close one. Fixed by the same line scanner as C2; a regression test now asserts sub-quadratic growth. An atomic-group "fix" was tested and **rejected** — it silently disables stripping entirely.
- `.bis` hardcoded in the grammar → generalised to `(?:\.[a-z]{2,}|[a-z])?`. The tests immediately caught that the first attempt dropped single-letter forms (`2.7b`).
- `_NUM_M` capped milestones at one dot while `_NUM_S` allowed any depth — `## Milestone 3.5.1:` silently dropped. Now symmetric.
- `Block` was a bare 3-tuple of same-typed strings → `NamedTuple`.
- `_split_milestone_blocks` / `_split_step_blocks` were one-line delegations with one caller each — deleted; callers use `grammar` directly (L-005).
- Broken reference in shipped source: `grammar.py` docstring cited a file M2 has not created → reworded to future tense.
- `test_json_output.py:53` docstring still said `schema_version: 1` → made version-free so it cannot go stale again.
- `CLAUDE.md` architecture tree lacked `grammar.py` and described `parser.py` as "regex grammar" → corrected.
- `tests/hooks/aa-ma-parse.bats` was missing from plan §5 Artefacts → added.
- `test_case_counts_are_pinned` used `==`, punishing legitimate additions → `>=`.

## Deferred (not blocking)

- `aa-ma-scribe.md:148,163` still mandates `### Step N.M:`, which M2's strict writer will outlaw — **M2 scope gap**, logged for M2.
- `_provenance_tail` reads an entire append-only log to return 5 lines (CWE-770). Pre-existing, unrelated to this diff.
- `--json` emits `provenance_tail` verbatim and absolute paths — treat output as sensitive. Pre-existing.
- `test_corpus_grandfathering`'s `assert milestones` will red on archiving any out-of-grammar plan; no allowlist. Pre-existing pattern.

## TDD verdict: PASS

Canonical git-log check UNVERIFIABLE (single uncommitted window), but substitute evidence is stronger: commit `77e38d4` enumerates all 24 test cases verbatim **before** any implementation existed, and the delivered file matches with zero drift. RED is guaranteed by construction — `grammar.py` provably absent at that commit while the test imports it at module level. A mutation harness killed **6 of 7** mutants (the survivor being a provably equivalent mutant).

**Acted on its recommendation:** split into two commits — tests first (legitimately RED), then implementation — so intra-milestone TDD ordering is mechanically verifiable rather than reconstructable only by mutation testing.
