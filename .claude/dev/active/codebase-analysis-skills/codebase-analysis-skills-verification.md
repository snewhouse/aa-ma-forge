# Verification Report: codebase-analysis-skills
Generated: 2026-09-27 | Mode: automated | Revision: 2 (v1 draft → v4 after loop 1 → v5 after loop 2)

## Summary
- CRITICAL: 18 findings (18 resolved)
- WARNING: ~45 findings (all but the residuals below resolved in the plan)
- INFO: ~12
- Overall: **PASS WITH WARNINGS**

Pre-verification reviews: CEO (HOLD SCOPE, 4 hardening ACs added) and Eng (4 issues fixed) — see plan.md "Plan Review History".

## Angle 1: Ground-Truth Audit
### Findings
- [CRITICAL → resolved] M4 removing `Skill(aa-ma-plan)` drops the pinned DANGLING golden edge → M4 now updates `test_plugin_surface.py:66-68` to `{"haiku-eval"}` + regen (M4 AC7).
- [CRITICAL → resolved] M4 AC1 contradicted the `KEPT` pin (`test_understand_codebase_rewire.py:61`) → KEPT moved to the one flagged legacy rule.
- [WARNING → resolved] "7 references" → 5; forge file count 659 → 665 at `f3ad912`; `.importlinter:75-81`; NO-SECRETS at `SKILL.md:269-273`; `SKILL.md:97` is the gsd row (keeps its date rule); codemem `choices`/help/docstring also change; ADR-0014 seam wording; A1 missing `test_doc_counts.py`/SECURITY name-list test; `test_install_and_cli.py` only checks `--help` (round-trip test added).
- ~40 claims confirmed OK (line refs, counts, test names, CI lines, scripts, ADR numbering).

## Angle 2: Assumption Extraction & Challenge
- [CRITICAL → resolved] `/sole-dev-merge` rebase-merges by default → Ste accepted rebase (V1); rollback = commit-range revert.
- [CRITICAL → resolved] `release.sh` requires `main`, clean, HEAD == origin/main → 8.3 runs on `main` after the M8 merge.
- [CRITICAL → resolved] `release.sh` refuses an empty `## Unreleased` → bullets per milestone + 8.2 curation.
- [CRITICAL → resolved] `codemem build` never fills commits tables; empty `owners` returns no error → `refresh-commits` + empty → UNKNOWN.
- [CRITICAL → resolved] SARIF ID belongs in `fingerprints`, not `partialFingerprints`.
- [WARNING → resolved] `--db` before `query`; fixture git identity in CI; research files untracked (committed in the planning commit); pydantic bump → golden regen; leaf contract explicit lists; dirty tracked-only caveats; pip-audit only in a conda env.
- Verified: `uv run --project` from a consumer keeps cwd and finds forge codemem; Draft4Validator importable; pydantic StrEnum/Literal/forbid schema export; `--untracked-files=no` semantics; `claude-security` exists (not installed); private repo report exists (shape/count only); hono 485 blobs; `main` unprotected.

## Angle 3: Impact Analysis on Proposed Changes
- [CRITICAL → resolved] `docs/architecture/` drift from new `src/aa_ma/analysis/*.py` → regen in every code milestone (cross-cutting rule).
- [CRITICAL → resolved] M4 plugin-surface golden/pin/drift (same as Angle 1).
- [CRITICAL → resolved] `render-is-leaf` + `tests/render/test_leaf_contract.py` must list `aa_ma.analysis`.
- [CRITICAL → resolved] Runtime SARIF schema validation would need jsonschema → runtime = pydantic + writer invariants; schema validation in tests only.
- [WARNING → resolved] local `CLAUDE.md` count pin; security hook vs fixture secrets (runtime fragments); extractor would lose 70 ON_DISK edges (V3); CHANGELOG curation; `owners` repo_root; `SKILL.md:97` scope; NO-SECRETS DRY across 4 agents (verbatim copies, test-enforced); runbook agent `:28`; `run.py` shell handling (V2); canonical tasks.md headings; "6 tools" docs; README skills row.

## Angle 4: Acceptance Criteria Falsifiability
### Score: 45/55 falsifiable as written → 55/55 after rewrites
- Rewritten: M1-AC7 (model fields == table rows), M2-AC5 (baseline equality incl. zero keys), M2-AC7 (fixture index), M2-AC11 (crash seam), M3-AC2 (exact strings), M5-AC3 (heading set), M5-AC5 (expected sections), M6-AC2/AC3 (pinned sets, ≥1 edge), M7-AC1 (accuracy/density formulas), M7-AC4 (`command -v` record), M8-AC4 (dated RETIREMENT line); M2 AC order fixed.

## Angle 5: Fresh-Agent Simulation
- [CRITICAL → resolved] Task dir / tasks.md missing → created in Phase 5.
- [CRITICAL → resolved] Research files untracked → committed in the planning commit.
- [CRITICAL → resolved] MEASURED finding definitions → §5a table (rule, source, argv, threshold, severity, anchor).
- [CRITICAL → resolved] Tool invocation/parse spec → §5a argv per tool; gitleaks `--redact`, temp report outside the scanned dir.
- [WARNING → resolved] enum casing, field types, internal helper types, secrets API, regex set, CLI argv, work-dir file schemas, Quick-tier ratings, severity-vs-confidence wording, `&&` part reporting, prototype deliverables, agents' deny-list (verbatim + test), `Onboarding.ledger`, unstamped legacy dirs in `fresh`, `--write-schemas` entry point.

## Angle 6: Specialist Domain Audit
### Specialists Dispatched: Pydantic v2, Security, Engineering Standards (always-on)
- [CRITICAL → resolved] PEM body survived header-only redaction → whole-block PEM/PGP regex, whole-text scan of `.md/.log`.
- [CRITICAL → resolved] JSON-quoted generic secrets missed → scan decoded JSON string values and keys; quoted + unquoted generic rules.
- [CRITICAL → resolved] gitleaks-only hits unredactable → `Hit` carries lines + columns; gitleaks runs on decoded values; unknown span blanks the whole value/line.
- [CRITICAL → resolved, re-verify loop 1] multi-line block vs line-by-line `.md` scan → whole-text scan, `Hit(start_line, end_line, …)`.
- [WARNING → resolved] extra patterns (URL creds, AIza, sk_live, glpat, env-style); `sk-` boundary; idempotent redaction; keys + unknown extensions fail closed; `run` argv[0] gate + extended refuse-list + minimal env + stdin DEVNULL; symlink component checks; fresh per-run codemem index; git option injection (`sha12` pattern, `--end-of-options`); JudgedFinding vs Finding; Counts/Baseline models; strict metrics; `PositiveInt` line; M1/§5a reconciliation; `EXPECTED_REFERENCES` into the RED commit; M2 tool-count pin.
- Engineering standards structural checks: element #12 present; Critical-Path/Audit-Profile/TDD-Waiver values canonical (parsed with `aa_ma.plan_parsers`); §13 Component + Flow views + derived Milestone graph; `aa-ma-lint-views --coverage`: sigils 5/5 checked, phantom 0, render PASS, no UNDRAWN_PATH; `aa-ma-gate` on tasks.md: no field errors (exit 1 = no ACTIVE milestone, expected pre-execution); `aa_ma_deps check` clean; `tests/test_active_plans_canonical.py` 26 passed.

## Residual WARNINGs (owned by the milestone named; not blocking)
- M2: a grandchild that calls `setsid()` escapes `killpg` — documented limit in the contract.
- M2: lizard/jscpd anchors are raw source lines; "anchor never contains secret text" relies on the secret gate running after finalize.
- M2: a secret split across a JSON key and its value is not scanned as one string (low risk: only `metrics`/`sections` have free keys).
- M2: `Literal[1]` accepts JSON `true`/`1.0` in pydantic 2.12 — add a before-validator if the negative fixtures should cover it.
- M2 (2.1): gitleaks `detect` is deprecated from 8.19 (`gitleaks dir`); confirm argv against the installed version.
- M3/M5: `extra="forbid"` on judged lines means a stray field fails the run — the skill must re-ask the judge once.
- M7: the L-029 name gate needs a curated distinctive-name list kept outside the repo.
- Local-only: `pip-audit` resolves only inside a conda env on BATS (reads ABSENT elsewhere).

## Revision History
- v1: 2026-09-27 — Wave 1 + Wave 2: 17 CRITICAL, ~45 WARNING → FAIL (automated)
- v2 (loop 1): 2026-09-27 — 15/16 re-checked resolved; 1 new CRITICAL (multi-line block scan) + 11 consistency WARNINGs → FAIL
- v3 (loop 2): 2026-09-27 — all fixed, lint clean, no leftover contradictions → PASS WITH WARNINGS
