# Fence 4 runbook: reading an IMPACT_VERIFIED block and clearing it

Fence 4 (`scripts/impact-verified.sh`, ADR-0027) compares what the milestone changed with what
its plan Contract predicted. This page is for the moment it says BLOCKED. What it checks and
its exit codes: [gate-fences.md](gate-fences.md#fence-4--impact_verified).

## Reading the block

```
  - unexplained_file=unpredicted:src/aa_ma/new_helper.py
  - unexplained_file=predicted-unchanged:docs/templates/plan-template.md
  - unexplained_file=cochange:scripts/uninstall.sh
  - api_break=aa_ma.gate.answer: Parameter was removed
  - unreviewed_cp=hook-modification:claude-code/hooks/aa-ma-parse.sh
BLOCKED: aa-ma-impact rc 1: 3 unexplained file(s); 1 public API break(s) without API-Break:; …
```

| Line | Means | Clear it with |
|------|-------|---------------|
| `unpredicted:<path>` | changed, but no Contract row names it (a directory row covers what is beneath it) | add the row if it was planned work (a Contract clarification, logged in context-log), or `Impact-Explained:` |
| `predicted-unchanged:<path>` | a Contract row whose path did not change | `Impact-Explained:` (work dropped or moved), or remove the row with a context-log note |
| `cochange:<path>` | codemem says this file changes with one you changed (≥5 shared commits, ≥50% of yours), and it did not | check it; change it, or `Impact-Explained:` why not |
| `api_break=<dotted.path>: <kind>` | griffe found a public API break in `aa_ma` / `codemem` | `API-Break:` in the Contract, after checking its callers (`who_calls`) |
| `unreviewed_cp=<value>:<path>` | the file falls under a Critical-Path glob | a `CRITICAL_PATH_REVIEW` provenance line for the milestone naming the file (or its glob) |
| `codemem index stale (<reason>)` | the index changed under the run | re-run; if it persists, `codemem refresh` |
| rc 3, `codemem build` | no index, or a refresh failed or was skipped | `codemem build --repo-root <repo>`, then re-run |
| `no milestone window` | on the default branch tip, or no origin | run the gate on the milestone branch |

## Writing `Impact-Explained:`

One line per file in the milestone's block of tasks.md (anywhere under `## Milestone N:`), the
path first, then a dash and a reason. A line without a reason, with a non-canonical bullet, or
inside a code fence explains nothing.

```
- Impact-Explained: scripts/uninstall.sh — reads the same AA_MA_HOOKS table; no row changed
- Impact-Explained: `docs/templates/plan-template.md` — moved to Milestone 12 (Ste, 2026-10-27)
```

## Declaring `API-Break:`

In the milestone's `#### Contract` fence of plan.md, the dotted path griffe printed (a module path
covers its members), then a dash and a reason:

```
API-Break: aa_ma.gate.answer — `strict` removed; its two callers updated in this milestone
```

griffe compares source expressions: a default rewritten from `2_000` to a named constant of the
same value is still reported. Declare it.

## Keeping Contract rows readable by the gate

Every token on a row is read as a path. Put prose after `#`:

```
  Test    tests/test_impact.py   # fixture repos: unpredicted, predicted-unchanged, rename
```

not `Test tests/test_impact.py (fixture repos: … (4 vs 5) …)` — a one-level `( … )` is dropped,
but a nested one leaves words behind, and prose after a colon is read too; each such word is a
predicted file that never changed.
