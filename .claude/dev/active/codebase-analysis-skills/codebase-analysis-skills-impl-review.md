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

---

# Milestone 2 — Assess engine (CLI) — §6.8 Post-Impl Review

- Window: `256e58c..3e0bb10` (19 commits, `feat/cas-m2-assess-engine`) · Audit-Profile: full · budget normal, parallel
- Date: 2026-09-28

| Agent | CRITICAL | WARNING | INFO | Verdict |
|---|:-:|:-:|:-:|---|
| code-reviewer | 0 | 7 | 9 | WARN |
| security-auditor | 1 | 7 | 5 | BLOCKED (pending decision) |
| tdd-sequence-auditor | 0 | 0 | 1 | PASS |
| context7-evidence-auditor | 0 | 0 | 0 | PASS |
| future-proofing-auditor | 0 | 6 | 6 | WARN |
| **TOTAL** | **1** | **20** | **21** | pending |

## CRITICAL
- **C1 (security, A01/A09) — `finalize._previous` follows symlinks in a report dir committed by the target.** `summary.json`/`findings.jsonl` are read through symlinks; the uncaught `ValidationError` at finalize.py:150 prints a traceback whose `input_value` quotes the outside file. **Reproduced by the orchestrator** (scratch repo, committed `zzz/findings.jsonl → ../outside.txt`, far-future stamp): `finalize` rc 1, traceback, outside text in stderr. Also: permanent finalize failure; with a far-future stamp a committed fake baseline hides new findings (W-S1).

## WARNINGs (deduplicated; source in brackets)
- W1 [cr+sec] `run.spawn`: `communicate()` after the group kill has no timeout — a setsid() escaper holding stdout hangs `run`/`measure` forever.
- W2 [cr] finalize rename not rolled back: between `os.replace(target, old)` and `os.rename(tmp, target)` a failure strands the previous report in `.old-*`.
- W3 [cr] `_previous` findings.jsonl read unguarded (corrupt/old-schema previous report → traceback, finalize dead until the dir is deleted) — same fix as C1.
- W4 [cr] report.md rendered before the gate → always "0 redacted".
- W5 [cr] `deps.vulns` summed across osv + pip-audit runs → a partial count (one tool unknown) shows as a number, not None.
- W6 [cr] `duplication.pct` covers prose formats while `duplication.clones` is code-only.
- W7 [cr+fp] `finalize.REPORT_FILES` dead.
- W8 [cr] Contract lists git "last-touch"; not implemented.
- W-S1 [sec] fake committed baseline (far-future stamp) masks new findings / injects fake fixed — same fix as C1.
- W-S2 [sec] argv gate misses: joined flags (`-Ic`, `-c"…"`, `-mpip`), `nodejs`, `node -p`, `perl -E`, `awk`, `deno`, `git -c alias=!…`, `uv run python -c`, `npm exec`, `make -f`, bare `yarn`, `pip3.12`, launchers `timeout/xargs/nice/nohup/setsid/stdbuf/find/busybox`.
- W-S3 [sec] target config files weaken tools (`.gitleaks.toml`/`.gitleaksignore`, `.semgrepignore`/`nosemgrep`, `osv-scanner.toml`, `whitelizard.txt`) while status stays `ran`.
- W-S4 [sec] a tracked file name with `%`/control char/scheme-like prefix that draws a finding crashes `measure` (Finding validator); a `:` passes the model but fails `sarif.verify` → report refused.
- W-S5 [sec] `_gate`'s FinalizeError embeds `str(ValidationError)` (quotes input) — re-validation runs before the "hits remain" check.
- W-S6 [sec] `CommandCheck.note` gets only the 13 regex rules before stdout (no gitleaks).
- W-F1 [fp] "10 … MCP tools" in 3 docs + docstring unguarded (only the help string is tested).
- W-F2 [fp] metric keys bake constants: `complexity.over_15`, `churn.90d`.
- W-F3 [fp] `report_md.DEEP_ONLY_NOTE` restates CORE_INPUTS/NETWORK_TOOLS in prose.
- W-F4 [fp] `<sha12>[-dirty]` naming in 4 places (stamp.report_dir, cli, finalize, report_md).
- W-F5 [fp] tool versions not recorded; positional lizard columns, semgrep unknown-severity fallback, osv rc 128 meaning are version-specific and would parse wrong silently.

## INFO (selected)
tdd: `test_findings_on_untracked_paths_are_dropped` landed with its implementation (f488b82) — retroactive RED check suggested. cr: codemem resolves `CODEMEM_BIN` not `_binary` by contract (AC12) — comment it; `co_changes` UNKNOWN when hot_spots empty; trail says ran before parse; gitleaks `File` not normpath'd; E2BIG → unknown without cause; judged `#k` order-dependent; osv 128 constant; test re-declares constants. sec: relative PATH entries resolve inside the target; tools get full env; `.git/config` hooks if the target ships `.git`; unbounded stdout buffer; history paths in hot_spot/co_change keys. fp: gitleaks `detect` deprecated in 8.19+ (`dir`); layer names repeated; run.py comment restates NOTE_LINES; codemem.md "90 days".

## User Override Decisions
| # | Finding | Decision (Ste, 2026-09-28) |
|---|---|---|
| 1 | C1 committed/symlinked baseline read | **Accept — fix now** (blocks until fixed + §6.8 re-run) |
| 2 | W1–W7, W-S4, W-S5 (code/robustness) | Fix all now |
| 3 | W-S2 argv gate, W-S3 config overrides, W-S6 notes full scan, W-F5 tool versions | Fix all now |
| 4 | W-F1–W-F4 drift, W8 last-touch | Fix all; add `last_touch_days:<dir>` metric |

Overall verdict: **BLOCKED** until sub-step 2.8 lands and §6.8 re-runs clean.
