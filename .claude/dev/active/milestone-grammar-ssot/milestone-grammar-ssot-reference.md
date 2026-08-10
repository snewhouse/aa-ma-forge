# milestone-grammar-ssot Reference

Immutable facts. Every figure measured at **b11c46d** by executing the real code.

## Repo

- **Root:** `/home/sjnewhouse/projects/github_private/aa-ma-forge`
- **Base commit:** `b11c46d`
- **Setup:** `uv sync`
- **Suite baseline:** `783 passed, 1 failed, 1 skipped, 7 deselected`. The single failure is `tests/codemem/test_corpus_grandfathering.py::test_audit_profile_absence_is_valid_for_pre_v080_corpus[sole-dev-merge-pr-workflow]`.
- **bats counts, as of b11c46d:** `tests/hooks/` **112 non-recursive, 118 recursive** (`tests/hooks/fixtures/build_active_dir.bats` holds 6; CI uses `--recursive`) · `tests/commands/sole-dev-merge/` 69. After M1's added case: **113 / 119**. After M3's added case: `tests/commands/sole-dev-merge/` **70**. Counts are `@test` lines; runs executed via `npx bats@1.11.0` (bats is not installed locally).

## Tooling present / absent

| Tool | State | Consequence |
|---|---|---|
| `shellcheck` | **present**, 0.11.0, `/usr/bin/shellcheck` | C4's failure is a flake, not a missing dependency |
| `bats` | **absent** locally | use `npx bats@1.11.0` |
| `yq` | **absent** here and in CI | CI assertions must be coreutils-only |
| `pydantic` | 2.12.5 | rejects `int` for a `str` field unless `coerce_numbers_to_str=True` |

## The six milestone grammars

| # | Location | Pattern |
|---|---|---|
| 1 | `src/aa_ma/tui/parser.py:49` | `^## Milestone (\d+):\s*(.+?)\s*$` |
| 2 | `src/aa_ma/tui/parser.py:50` | `^### Step (\d+\.\d+):\s*(.+?)\s*$` |
| 3 | `tests/codemem/test_corpus_grandfathering.py:45-48` | `^## (?:Milestone\s+)?M?\d+(?:\.\d+)?:.+?$` |
| 4 | `claude-code/hooks/lib/aa-ma-parse.sh:75` | awk `/^## /` (over-tolerant) |
| 5 | `claude-code/commands/execute-aa-ma-milestone.md:504,518,529,692` | awk `/^## Milestone.*/` — **drives the HARD gate** |
| 6 | `claude-code/skills/verify-impl/SKILL.md:57` | awk `/^## (Milestone\s+)?M?$N(:\|\s)/` |

## Canonical forms

- **Writer (canonical):** `## Milestone N: Title` / `### Sub-step N.N: Title`
  Source: `docs/templates/tasks-template.md:26,89,127,147,155`; `docs/spec/aa-ma-specification.md:697,704`.
  **Eleven** shipped files write or teach a tasks.md heading. At b11c46d only `docs/templates/tasks-template.md` was canonical; the other ten were fixed in M2 (see tasks.md Sub-step 2.3 Result Log). The authoritative list is `WRITER_TEMPLATES` in `tests/test_active_plans_canonical.py`, each covered by a mutation guard.
- **Reader (tolerant):** keywords `Sub-step|Step|Task`; separator `(?::|[ \t]+[–—-][ \t]+)` — a **space-delimited** dash, never a bare hyphen.

## Field format `tasks.md` MUST use

Two consumers, two requirements. Both must hold or the gate reads empty.

| Field | Required form | Enforced by |
|---|---|---|
| `Audit-Profile` | `- Audit-Profile: code-only` — own line, **unbackticked** | `plan_parsers._extract_field` anchors `^[ \t]*-?[ \t]*` |
| `Critical-Path` | `- **Critical-Path:** data-xform` — own line, **bold**, unbackticked | `execute-aa-ma-milestone.md:520` greps `^- \*\*Critical-Path:\*\* \S` |
| `Prototype-Required` | `- **Prototype-Required:** YES` — own line, **bold** | `execute-aa-ma-milestone.md:531` greps `^- \*\*Prototype-Required:\*\* YES` |

Measured: mid-line + backticked → `(None, True, None)`; own line + backticked → `('`code-only`', False, "Non-canonical…")`; own line + bare → `('code-only', True, None)`.

## Canonical enum values

- `Audit-Profile`: `full | code-only | docs-only | infra | custom` (`plan_parsers.CANONICAL_AUDIT_PROFILES`)
- `TDD-Waiver`: `refactor | docs-only | prototype | hotfix-emergency | tooling-config` (`plan_parsers.CANONICAL_TDD_WAIVERS`)
- `Critical-Path`: `auth-flow | data-xform | external-api | version-pipeline | doc-count-drift | hook-modification` (`plan_parsers.CANONICAL_CRITICAL_PATHS`, added in M4, with `parse_critical_path()`; `plan-verification` Angle 6 check #2 now invokes it instead of eyeballing a prose list).

## Bash-side grammar (added M4)

`claude-code/hooks/lib/aa-ma-parse.sh` is the single bash-side implementation,
mirroring `src/aa_ma/grammar.py` and pinned to it by `tests/test_grammar_parity.py`:

| Symbol | Purpose |
|---|---|
| `AA_MA_MILESTONE_ERE` | prefix ERE mirroring `MILESTONE_RE`; POSIX-only so gawk and mawk agree |
| `aa_ma_is_milestone_heading <line>` | recognition (ERE **plus** non-empty title — the ERE alone over-matches `## Milestone 5:`) |
| `aa_ma_extract_milestone_block <file> <title>` | rc **0** found / **1** no match / **2** config error / **3** ambiguous |
| `aa_ma_extract_milestone_block_by_number <file> <num>` | same, addressed by number (`2a`, `3.5`) |
| `aa_ma_field_value <name>` / `aa_ma_count_field <name> <val>` | field reads tolerating `- X:` **and** `- **X:**` |

Callers MUST refuse on non-zero rc. The old contract returned 0-and-empty for
every failure, which the gate read as a clean milestone.

Block extraction opens only on a milestone heading but closes on **any H2** —
deliberately asymmetric, and deliberately different from `split_milestones`, so
a trailing `## Summary Counts` section is not absorbed into the last milestone.

## Corpus baseline — 14 repo tasks measured at b11c46d

`aa-ma-tui --root .claude --json --include-completed`. **This table is the gate.** Task dirs created after b11c46d (including `milestone-grammar-ssot` itself) add rows and are out of scope: the criterion is *every listed row matches*, not *the row count is 14*.

`--root .` returns **23 junk entries** (every top-level directory) — `_resolve_roots` (`__main__.py:85-117`) falls through to a direct scan. Always use `--root .claude`.

| Task | before M/S/status | after M/S | delta |
|---|---|---|---|
| aa-ma-engineering-standards | 5 / 0 / PENDING | 5 / 37 | steps; status → IN_PROGRESS |
| aa-ma-tui-tracker | 6 / 42 / COMPLETE | 6 / 42 | none |
| codemem | 0 / 0 / ERROR | 5 / 47 | blind → visible |
| codemem-benchmark-fairness-v2 | 3 / 0 / COMPLETE | 6 / 30 | **milestones + steps** |
| codemem-token-benchmarks | 4 / 0 / COMPLETE | 4 / 16 | steps |
| fix-drift-release-v0-9-0 | 3 / 0 / COMPLETE | 3 / 15 | steps |
| harden-aa-ma-plan | 0 / 0 / ERROR | 5 / 24 | blind → visible |
| hooks-hardening-m1 | 5 / 17 / COMPLETE | 5 / 19 | `.bis` steps |
| post-impl-adversarial-review | 6 / 23 / COMPLETE | 6 / 23 | none |
| ship-missing-skills | 4 / 0 / COMPLETE | 4 / 15 | steps |
| skill-ecosystem-integration | 0 / 0 / ERROR | 3 / 26 | blind → visible |
| sole-dev-merge-pr-workflow | 0 / 0 / ERROR | 5 / 42 | blind → visible |
| token-stack-integration | 5 / 12 / COMPLETE | 5 / 12 | none |
| understand-codebase-skill | 3 / 0 / COMPLETE | 3 / 20 | steps |

**Totals: 44 → 65 milestones, 94 → 368 steps.**

The 94 is *TUI-reachable* steps — those inside a parsed milestone block, which is what the per-file column above reports. A raw `^### Step (\d+\.\d+):` scan across the same files returns **135**, because 41 of them sit in `sole-dev-merge-pr-workflow`, whose milestones the old grammar could not parse at all. Both figures are correct answers to different questions; the gate uses the per-file table, not either total. Zero unparsed headings, zero false positives on 9 negatives. Only 3 of 14 tasks unchanged — the gate is *"every delta is one we predicted"*, not *"no deltas"*.

The 4 ERROR tasks raise `ParseError` (`parser.py:277`) → `aggregate_status=ERROR` (`parser.py:341-347`). `model.py:27-30` documents ERROR as **terminal**, so restoring them moves kanban columns.

## Exact line references

| Fact | Location |
|---|---|
| `int()` cast to remove | `src/aa_ma/tui/parser.py:172` |
| block-tuple annotation | `src/aa_ma/tui/parser.py:168` |
| `Milestone.number: int` | `src/aa_ma/tui/model.py:190` |
| `Milestone` ConfigDict | `src/aa_ma/tui/model.py:188` |
| `SCHEMA_VERSION` | `src/aa_ma/tui/model.py:141` |
| `discover_tasks(roots: list[Path])` | `src/aa_ma/tui/parser.py:313` — takes a **list** |
| `ParseError` message (keep "Milestone") | `src/aa_ma/tui/parser.py:271` |
| parser docstrings documenting old grammar | `src/aa_ma/tui/parser.py:5-7` and `:22-24` |
| C4 test opens | `tests/commands/sole-dev-merge/test_stage_c_dispatch.bats:124` (`:118` is a bandit assert) |
| `SLUG` derivation | `tests/commands/sole-dev-merge/test_stage_c_dispatch.bats:30` |
| shared shellcheck tmp path | `test_stage_c_dispatch.bats:48`, `test_stage_d_triage.bats:52`, `test_smoke_e2e.bats:218` |
| existing skip-guard to reuse | `tests/hooks/security-static-check.bats:248-251` |
| `rules/aa-ma.md` symlink | `scripts/install.sh:284` → `~/.claude/rules/` (live, no reinstall) |
| `_strip_html_comments` precedent | `src/aa_ma/plan_parsers.py:67` |

## Sites broken by `Milestone.number: int → str`

Construction (fixed by `coerce_numbers_to_str=True`): `tests/tui/_static_tasks.py` (6 milestones), `tests/tui/test_snapshot.py:143`, `tests/tui/test_model.py:75`, `tests/tui/test_parser.py:242`.
Comparison (coercion does **not** help — edit): `tests/tui/test_parser_properties.py:152` (`@pytest.mark.slow`, one of the 7 deselected — invisible to the default run), `tests/tui/test_parser.py:242`.
Golden: `tests/tui/snapshots/data.json` pins `"number": 1|2` and `"schema_version": 1` — regenerate.
`SCHEMA_VERSION == 1` assertions: `tests/tui/test_json_output.py:39`, `tests/tui/test_integration.py:117`, `tests/tui/test_main_dispatch.py:102`.
Docs pinning 1: `src/aa_ma/tui/json_output.py:8`, `docs/adr/0007-aa-ma-tui-tracker.md:161,184`.
Unaffected: `.txt` and SVG snapshots — built from hand-constructed `Task` objects (`tests/tui/_static_tasks.py`), and both read sites (`snapshot.py:127`, `screens/task_detail.py:58`) are f-strings.

## Out of repo (not CI-reproducible)

`agent-token-optimization` and `safety-app-production-settings` live in `~/.claude/dev/completed/`. `__main__.py:113-118` scans `cwd()` **and** `home()`, which is why they appear in an unscoped run. `agent-token-optimization` uses `## Step N:` at H2 and unnumbered `### Sub-step:` — the grammar does **not** match it by design.

## Canonical lint candidate selection (M2)

A heading is a *candidate* for the canonical lint only if it matches the tolerant
`grammar.MILESTONE_RE` / `grammar.STEP_RE`. It is a *violation* if it is a candidate but does
not also match `CANONICAL_M` / `CANONICAL_S`. Without this rule a plain `## Summary Counts`
heading would be flagged, and this plan's own tasks.md would fail M2 acceptance #4.

_Last updated: 2026-08-09_
