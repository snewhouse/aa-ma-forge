# Impl Review Report: codebase-analysis-skills / Milestone 1
Generated: 2026-09-28T13:39:00Z (14:39 +01:00) | Audit-Profile: full | Budget: normal
Window: `c9cfbe5..0ae6e8a` (branch `feat/cas-m1-analysis-core`)

## Summary
- CRITICAL: 3 findings (3 accepted, 0 disputed, 0 deferred)
- WARNING: 9 findings (all to be fixed in M1 — Ste, 2026-09-28)
- INFO: 17 findings (cheap ones fixed with the warnings; rest logged)
- Overall: **BLOCKED** until sub-step 1.7 lands the fixes and §6.8 re-runs clean — *superseded: re-run PASS WITH WARNINGS, 0 CRITICAL (see Re-run section below)*

| Agent | CRITICAL | WARNING | INFO | Verdict |
|---|:-:|:-:|:-:|---|
| code-reviewer | 1 | 6 | 6 | BLOCKED |
| security-auditor | 2 | 1 | 6 | BLOCKED |
| tdd-sequence-auditor | 0 | 0 | 1 | PASS |
| context7-evidence-auditor | 0 | 0 | 0 | PASS |
| future-proofing-auditor | 0 | 2 | 4 | PASS |

---

## Code Review (code-reviewer agent)

Patterns: scope discipline clean; schema-breaking output none; dead code = M2-bound interface only (expected).

- [CRITICAL] [secret gate fails open]: `src/aa_ma/analysis/secrets.py:323-324` — one unmappable gitleaks entry discards every gitleaks hit and returns UNKNOWN, and `scan-secrets` exits 0 when the regex set is clean — a secret only gitleaks detected survives. Fix: keep mapped hits; known text + bad span → blank the whole text; entry tied to no text → fail closed (exit 1).
- [WARNING] [spec drift]: `secrets.py:344-345` — dedup compares whole Hits (rule included), §5a says path+line+span.
- [WARNING] [DRY]: `secrets.py` — pointer format built separately in scan and redact paths.
- [WARNING] [contract over-claims]: `ANALYSIS-CONTRACT.md:51-58` — `UnsafePath → exit 2` and the self-ignoring root are not reachable from any M1 CLI path.
- [WARNING] [contract claim contradicted]: `ANALYSIS-CONTRACT.md:74-75` — the output gate may further redact a stored anchor after the id was hashed.
- [WARNING] [untrusted input]: `models.py:164` — `path` accepts absolute / `..` paths that flow into SARIF `uri`.
- [WARNING] [magic number]: literal 12 in ids/stamp/models.
- [INFO] `redacted: true` only for `.jsonl`; `date_utc` not forced to UTC; unnamed gitleaks offsets; `fresh` traceback on non-UTF-8; negative counts accepted; JSONL splitting duplicated in cli.

## Security (security-auditor agent)

### Mechanical pre-check (security-static-check.sh): PASS

- [CRITICAL] [A04/A09]: `secrets.py:173-185` — duplicate JSON keys: `json.loads` keeps the last value, the first is never scanned, raw file keeps the secret. Reproduced live (exit 0). Fix: `object_pairs_hook` refusing repeated keys → UnsupportedFile.
- [CRITICAL] [A04]: `secrets.py:28-30,197` — any file named `.gitignore` at any depth is skipped unscanned. Reproduced live (exit 0). Fix: skip only `root/.gitignore` whose content is exactly `*\n`; otherwise fail closed.
- [WARNING] [A09]: `cli.py:88-92` — `validate` prints pydantic `input_value=` (can echo a secret). Fix: `errors(include_input=False)`.
- [INFO] redaction writes follow hardlinks; `safe_dir` check-then-use window; lone-surrogate strings crash rather than refuse; decoded temp files survive SIGKILL; `gitleaks:allow` honoured (document); file names never scanned.

## TDD Sequence (tdd-sequence-auditor agent)

### Verdict: PASS
- First `tests/` commit `f341108` (14:22:29) precedes first `src/` commit `9023e53` (14:28:02); RED commit tests-only (L-028). Regression pair `993047e` → `d48ca0e` ordered by parentage.

## External Library Evidence (context7-evidence-auditor agent)

PASS — 0 new PyPI deps, 0 major bumps (only a `[project.scripts]` entry).

## Future-Proofing (future-proofing-auditor agent)

- [WARNING] gitleaks column offsets are bare literals tied to 8.18.
- [WARNING] contract prose restates enum values / limits / regex families not pinned by `test_contract_doc.py`.
- [INFO] literal 12; `2000`/`8000`/40-lines unnamed; M2-bound interface has only test callers (intended, re-check at M2); `.importlinter` lists already pinned by test.

## User Override Decisions

| # | Finding | Decision | By | Date |
|---|---|---|---|---|
| 1 | Duplicate JSON keys bypass (security) | **accept** — fix now | Ste | 2026-09-28 |
| 2 | Nested / altered `.gitignore` skipped (security) | **accept** — fix now | Ste | 2026-09-28 |
| 3 | gitleaks unmappable entry fails open (code-review) | **accept** — fix now | Ste | 2026-09-28 |
| — | All 9 WARNINGs + cheap INFOs | fix all now (before M2 consumes the schemas) | Ste | 2026-09-28 |

## Re-run (post-remediation) — 2026-09-28, window `0ae6e8a..56f1cc6`, then `..bb1f389`

| Agent | CRITICAL | WARNING | INFO | Verdict |
|---|:-:|:-:|:-:|---|
| code-reviewer (re-run) | 0 | 2 | 5 | PASS WITH WARNINGS |
| security-auditor (re-run, live vs gitleaks 8.18) | 0 | 2 | 4 | PASS WITH WARNINGS |

- All 3 accepted CRITICALs verified CLOSED (live reproductions now exit 1).
- Re-run WARNINGs, fixed in `84d4faa` (RED) → `f02431a` (GREEN): JSON key context blinded contextual rules (pre-existing); `validate` echoed key names; `Finding.path` accepted URI schemes / `%` / control chars; unused `NOTE_TAIL_LINES`.
- Re-run INFOs fixed in the same pair: split-path name echo, JSONL `\n`-only split, deep-nesting → UnsupportedFile, gitleaks index range, file mode kept, contract wording (UTC, gitleaks status caveat).
- Logged, not fixed (by design / M2): `gitleaks:allow` honoured (regex still runs); gitleaks `unknown` with clean regex exits 0 (documented; callers record tool status); field_validator rules not expressed in golden JSON Schemas (note for M2 consumers); decoded temp files survive SIGKILL; `safe_dir` check-then-use window; JSONL splitting in cli vs secrets.

**Overall after re-run: PASS WITH WARNINGS (all fixed) — 0 open CRITICAL.**
