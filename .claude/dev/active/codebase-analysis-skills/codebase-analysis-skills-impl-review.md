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

## Milestone 2 — §6.8 re-run + §6.6 (2026-09-28)
| Agent | CRITICAL | WARNING | INFO |
|---|:-:|:-:|:-:|
| §6.8 code-reviewer (re-run) | 0 | 7 | 7 |
| §6.8 security-auditor (re-run) | 0 | 2 | 5 |
| §6.6 reuse | 0 | 3 | 7 |
| §6.6 quality | 0 | 5 | 16 |
| §6.6 efficiency | 0 | 3 | 7 |

All first-round items verified closed (C1, W-S1, W-S4, W-S5, W-S6, W1, W2 (partial: restore-failure path), W4–W8, W-F1–F5). Open (deduplicated): argv denylist still bypassable (uv run value-taking options, node -r, php -r, poetry/pdm/hatch run, bun x, git push, …) and over-refuses (`python -Werror`, `cargo test --features fetch`); `-`-prefixed tracked names become lizard/jscpd options; owners parse not wrapped (crash); last_touch_days vs wall clock (non-deterministic); _swap deletes the old report if the restore also fails; sast/deps counts before the untracked filter; gitleaks/git resolved on raw PATH in secrets/stamp; overrides and unreportable not shown in report.md; gitleaks walks the untracked tree (11 s on the forge, `.venv`); REPORT_NAME second naming rule; command text not scrubbed; FIFO blocks `_read_regular`; DRY/tidy list (binary lookup ×3, gitleaks argv ×2, symlink-safe reader in the wrong module, CORE_INPUTS in measure, `_codemem` length, encodings, formatter-damaged comments, JSONL readers ×3, test helpers). Disputed: `REPORT_FILES` dead (quality W3) — it is asserted by `test_the_report_dir_holds_exactly_the_report_files`.

### User Override Decisions (round 2)
| Item | Decision (Ste) |
|---|---|
| run gate | **Allowlist** of known test-runner forms; everything else `not_run — run by hand` (§5a contract change) |
| correctness fixes + gitleaks tracked-only | Fix all now |
| DRY/tidy | Do them now |
| inline suppressions, parallel tool runs, faster owners blame, huge-repo argv | All done in M2 |

Design (orchestrator, first principles): one **staging dir** of hard-linked tracked regular files in the work dir, target scanner configs left out; lizard/jscpd/gitleaks/semgrep/osv/pip-audit run with cwd = staging on `.` — closes gitleaks' untracked walk, `-`-named files as options, argv size limits and config obedience in one change.

## Milestone 2 — §6.8 round 3 (2026-09-29), diff cb63e50..7bfc75e
| Agent | CRITICAL | WARNING | INFO |
|---|:-:|:-:|:-:|
| code-reviewer | 1 | 6 | 8 |
| security-auditor | 0 | 4 | 7 |

- **C-R3 (code, confirmed live by the orchestrator):** `_allowed` matched `basename(argv[0])` — `./ruff check .` ran a binary planted in the target.
- Security (reproduced by the auditor): allowed runners took any option — `cargo test --config target.…runner=[…]` and `node --test --import=data:` ran code; `pylint --init-hook`, `go test -exec`, `tox exec -- sh`, `yarn run node -e`, `npm test --node-options=/--registry=http://` pass; target `.git/config` `core.fsmonitor` ran a command during measure/finalize; a symlinked parent dir (`p` → `/proc`) made measure read and report `p/self/environ`.
- Code: /tmp is tmpfs → staging always copies into RAM (ENOSPC crash risk); `_stage` crashes on files changed mid-run; target `.gitignore` staged (hides force-added files from semgrep); jscpd `package.json` key still obeyed; suppression counts include mentions in docs/tests (forge report.md "semgrep 4, gitleaks 6" false); formatters/`--fix` would rewrite the target; INFOs: formatter-damaged comments, three JSONL readers, empty `.old-*` leak, relative `*_BIN`, timeouts under concurrency, merge-sum invariant, stale stages after SIGKILL, `_previous` ls-files failure open, lstat races.

### User Override Decisions (round 3, Ste)
| Item | Decision |
|---|---|
| C-R3 + option vectors | **Strict grammar**: bare argv[0]; only paths + a small per-runner flag set; check-only formatter forms; else `not_run` |
| target `.git/config` | **Harden + refuse**: git config overrides on every call (env `GIT_CONFIG_COUNT`), measure/finalize refuse (exit 2) when the local config sets include*/filter.*/diff.*.command|textconv/core.fsmonitor/core.sshCommand |
| everything else | Fix all now; then one more §6.8 pass on the diff |

## Milestone 2 — §6.8 round 4 (2026-09-29), diff bc35b34..4b032e4 (sub-step 2.10)
| Agent | CRITICAL | WARNING | INFO |
|---|:-:|:-:|:-:|
| code-reviewer | 1 | 4 | 6 |
| security-auditor | 3 | 4 | 3 |
| AC evidence (§6.1 pre-check) | — | AC9 PARTIAL | — |

- **C-R4a (both agents; reproduced by the orchestrator, PWNED created):** `check_git_config` read `--local` only; `extensions.worktreeConfig` + `filter.x.clean` in `config.worktree` ran during `head_stamp`'s `git status` on a touched file.
- **C-R4b (security, reproduced by the auditor):** `log.showSignature=true` + relative `gpg.program` + a `gpgsig` commit → `_git_metrics`' `git log` ran it.
- **C-R4c (security, reproduced by the auditor):** submodule config `.git/modules/<n>/config` never checked; `git status` recursed and ran its filter.
- WARNINGs: `uv run ruff` ran a planted `.venv/bin/ruff`; `python -m mypy` imported a planted `./mypy.py`; cargo `[alias] fmt` ran target code; parent-dir symlink swap mid-stage passes the `S_ISREG` post-check; `check_git_config` fails open on rc∉{0,1}; in-repo tracked symlinks counted in `files.escaping`; `includeIf`/`diff.*.command` untested; `-k`/`-run` values with `^$|` → not_run (fail-safe; documented).
- **Disputed (orchestrator):** "staged `.codemem/` hard-linked, codemem writes the target's db" — every codemem call passes `--db <work>/codemem.db` with cwd = target (`measure.py` `_Codemem.call`), so the stage's `.codemem/` is never opened.
- INFOs: stage-root mode unchecked; `RecursionError` from a deep package.json; `STALE_STAGE_S` duplicates `SECONDS_PER_DAY`; formatter-split comments (run.py `valued`, measure.py post-check); `python -m ruff/black` asymmetry; staged package.json line numbers shift; no fresh-stage-survives test; linters that run repo code by design (documented).
- AC9 uncovered: finalize refusing when post-redaction re-validation fails; vendored SARIF schema on a redacted report.

### User Override Decisions (round 4, Ste)
| Item | Decision |
|---|---|
| C-R4a/b/c | **Allowlist + isolate**: refuse (exit 2) a target whose local/worktree/submodule config holds a key outside a safe set; `log.showSignature=false` override + `--no-show-signature`; `--ignore-submodules=all` on status; fail closed when config is unreadable |
| run/stage WARNINGs + INFOs + AC9 gaps | **Fix all now** (`uv run` only for test runners; `python -P -m` for lint modules; refuse cargo forms when `.cargo/config*` exists; (dev, ino) recorded at listing and compared after staging) |

## Milestone 2 — §6.8 round 5 (2026-09-29), diff 1f55f08..ffb50eb (sub-step 2.11), security-auditor
SUMMARY: 2 CRITICAL / 3 WARNING / 5 INFO.
- **R5-1 (reproduced by the orchestrator, PWNED):** `aa-ma-analysis stamp` / `fresh` never called `check_git_config`; `git status` ran the target's `filter.x.clean`. measure/finalize refused correctly.
- **R5-2 (auditor, with a concurrent swapper):** `_tracked_regular_files` lstat → realpath(parent) window lets a racing process get an outside inode listed; later identity checks then accept it.
- WARNINGs: `.git` file / `commondir` pointing at another repo is mined (history, emails); `PYTHONSAFEPATH` does not stop linters loading plugins from their own config (mypy `plugins`, flake8 local-plugins) — the 6c37fd2 claim "lint modules never import from the target" is too strong; no timeout on git calls (FIFO via include.path hangs forever).
- INFOs: user's global filter (git-lfs) reachable from target `.gitattributes`; cargo walk stops at a nested `.git`; `rust-toolchain.toml` path (unreproduced); python < 3.11 ignores PYTHONSAFEPATH; reads not size-capped.

### User Override Decisions (round 5, Ste)
| Item | Decision |
|---|---|
| R5-1 | Fix now: `head_stamp` calls `check_git_config`, covering every caller |
| R5-2 / threat model | **Hostile content at rest**: a concurrently running hostile process is out of scope (it already runs as the user); inode checks stay as defence in depth; boundary documented in §5a and the report |
| at-rest items | Fix: git dir / common dir inside the repo (linked worktrees verified by back-reference); git call timeout → refused; `GIT_CONFIG_GLOBAL=/dev/null` + `GIT_CONFIG_NOSYSTEM=1`; explicit `-P` for non-test `python -m`; capped reads. Document: linters run repo code via their config; cargo walk; rust-toolchain |
| close-out | One regression pass on the new diff; anything new and out of scope → M2 follow-up backlog, not another round |

## Milestone 2 — §6.8 regression pass (2026-09-29), diff 6a203df..a7b95e1 (sub-step 2.12), security-auditor
SUMMARY: 0 CRITICAL / 0 WARNING / 4 INFO. All 13 earlier findings re-reproduced and hold at HEAD (config.worktree, gpg/showSignature, submodule filter, stamp/fresh, foreign `.git` file, FIFO hang, global lfs filter, `./ruff`, `uv run ruff`, planted `./flake8.py`, cargo alias, symlinked parent at rest, C1 baseline). No in-scope git call runs before the config check.
- INFO ×3 (worktree back-reference: forgeable from a hostile enclosing clone; unbounded read; `--relative-paths` worktrees refused) → fixed in 2.12 test-first (see tasks.md), both new conditions mutation-checked.
- INFO (ISOLATED_CONFIG drops a global `safe.directory`: a repo owned by another uid reports "not a git repo") → **M2 follow-up backlog** (usability, fails closed).
- Review loop closed per Ste's round-5 decision.

## Milestone 2 — /sole-dev-merge Stage C (2026-09-29), diff main...HEAD
| Source | CRITICAL | HIGH | MEDIUM | LOW |
|---|:-:|:-:|:-:|:-:|
| code-reviewer (C1) | 0 | 0 | 1 | 10 |
| security-auditor (C2) | 0 | 0 | 2 | 1 |
| bandit (C3, changed files incl. tests) | 1 (B613) | 5 | 449 | 0 |
- MEDIUMs, all reproduced (credential in refusal message and non-ASCII churn by the orchestrator): **fixed** (Ste) in `b85d6df`→`d2dbccb`.
- Bandit: B613 = the deliberate U+202E in the bidi-refusal test → written as an escape; B608 ×3 in codemem SQL predate this branch (git blame) → not this PR; B108/B105/B101/B603/B607/B404 → disputed, test-fixture false positives (Ste).
- LOWs: 5 bugs + 2 comments + 2 test gaps **fixed** (Ste); 2 → backlog.
- Out-of-scope: Stage B's auto-fix commit reformatted untouched lines of touched files → dropped before push; lesson L-031.

---

# Milestone 3 — post-impl review (§6.8, Audit-Profile: full) — 2026-09-29

Window `d13e790..6dc9b4f`. Agents: code-reviewer (+ §6.6 reuse/quality/efficiency folded in), security-auditor, tdd-sequence-auditor, context7-evidence-auditor, future-proofing-auditor.

| Agent | CRITICAL | WARNING | INFO | Verdict |
|---|:-:|:-:|:-:|---|
| code-reviewer | 0 | 6 | 7 | WARN |
| security-auditor | 0 | 5 | 3 | WARN |
| tdd-sequence-auditor | 0 | 1 | 2 | PASS |
| context7-evidence-auditor | 0 | 0 | 0 | PASS |
| future-proofing-auditor | 0 | 2 | 7 | WARN |
| **TOTAL** | **0** | **14** | **19** | **PASS_WITH_WARNINGS** |

**WARNINGs**
- CR-1 SKILL.md Step 6 (Deep extras) runs after judges/ratings/refuter — claude-security evidence and new Critical/High never reach the refuter; test result never folded into ratings.json.
- CR-2 SKILL.md:39-40 "only the CLI writes" contradicts main-thread writes (ledger, ratings, judged.jsonl).
- CR-3 SKILL.md:34 "restate verbatim" claims all 4 constraints; prompts restate only NO SECRETS verbatim.
- CR-4 AGENT-PROMPTS.md tests_deps names "last-touch age" — metric is `last_touch_days:<dir>` (exists; wording vague) / owners keys missing from RATING.md.
- CR-5 AGENT-PROMPTS.md refuter "You may write exactly one file: none — you write no file."
- CR-6 AGENT-PROMPTS.md judge tail copied 4× (DRY).
- SEC-W1 A judge can pre-set refutation `refuted`/`survived` on its own Critical/High → silently dropped or never attacked; finalize only refuses `pending`.
- SEC-W2 Refuted findings/reasons leave no audit trail (count only).
- SEC-W3 Deep test command chosen from untrusted repo docs; `npm run`/`make`/pytest run repo code with HOME + network; consent shows argv only.
- SEC-W4 Judge text not secret-gated before the refuter prompt / session transcript; work dir kept on failure.
- SEC-W5 Judges/refuter are general-purpose (Bash/Write) while reading hostile content; read-only is prompt-only.
- TDD-W1 same-second test/fix timestamps (4621f54/ccac6bb) — in-session evidence: new test run against the old text failed (1 failed) before the fix commit.
- FP-W1 "at most 2000 chars" restates `models.EVIDENCE_MAX` untested.
- FP-W2 RATING.md `complexity.over_15` / "~25" restate `measure.CCN_FLAG`/`CCN_HIGH` untested.

**INFO (selected):** stamp tier hardcoded in Step 0; `[path]` never applied (`--repo .`); `{PENDING}` missing from placeholder list; test checks subcommand names not flags; `Explore` alternative dead in test; judges' `uv run validate` may sync; AA_MA_ROOT env trust (no new boundary); `fresh` shows a planted untracked same-SHA report; orphan pin removed in M4.
