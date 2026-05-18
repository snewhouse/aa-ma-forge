# sole-dev-merge-pr-workflow — Post-Impl Adversarial Review

Generated: 2026-05-18 | Skill: `verify-impl` | Audit-Profile: `code-only`

## Summary

| Agent | CRITICAL | WARNING | INFO | Verdict |
|-------|:--------:|:-------:|:----:|---------|
| code-reviewer             | 0 | 3 | 2 | PASS_WITH_WARNINGS |
| security-auditor          | 0 | 1 | 4 | PASS_WITH_WARNINGS |
| tdd-sequence-auditor      | 1 | 0 | 0 | FAIL                |
| context7-evidence-auditor | 0 | 0 | 0 | PASS                |
| future-proofing-auditor   | 0 | 1 | 3 | PASS_WITH_WARNINGS |
| **TOTAL**                 | **1** | **5** | **9** | **PASS_WITH_WARNINGS** (post-override) |

**Milestone window:** `69edca3..df1df6d` (4 commits — 9af92ee, e04cb99, 5faddc9, df1df6d).

---

## CRITICAL Findings

### [CRITICAL] tdd-sequence-auditor: implementation landed before formal bats tests

**Mechanical evidence:**
- First `claude-code/commands/*` commit: `9af92ee` @ 2026-05-18T13:09:11+01:00 (Stage A + B + auto-commit)
- First `tests/.../test_*.bats` commit: `e04cb99` @ 2026-05-18T13:12:08+01:00
- Δt = ~3 minutes; impl precedes formal tests.
- `TDD-Waiver:` field on M1: ABSENT.

**Mitigation evidence (basis for dispute):**
1. The plan v2 §4 *explicitly* schedules bats after stages 1.1-1.4 (Steps 1.5/1.6 follow 1.1-1.4). This is a planned, plan-verified-in-Phase-4.5 sequence.
2. The implementation phase included *continuous empirical validation* via inline bash test harnesses:
   - M1.2: 5/5 Stage A cases (4 abort + happy) verified in isolated tmp git repos — see provenance.log [2026-05-18T12:53:16+01:00] STEP_1.2 COMPLETE entry.
   - M1.3: L-007 reversion scenario verified (A1+A2 PASS); pytest-rc-5 bug *caught and fixed during this empirical phase*, before the formal bats tests existed. Bug evidence is the strongest counter-argument: TDD's value is "tests catch bugs before they ship" — that mechanism worked here.
   - M1.4: 3 scenarios (ad-hoc / plan-active / clean-tree) verified in isolated tmp git repos.
3. The formal bats files (e04cb99) *codify* the inline harnesses into reproducible CI-ready tests; zero behavioural drift between impl and bats. Bats 11/11 pass on first formal run.
4. The 3-minute gap between commits is far less than typical sprint cycles where impl/test discipline matters.

---

## User Override Decisions

| Finding | Decision | Rationale | Logged |
|---------|----------|-----------|--------|
| [CRITICAL] tdd-sequence FAIL | **dispute** | False-positive against project context: plan-§4 explicitly schedules bats after impl; empirical validation harnesses ran continuously during impl (provenance evidence); bats formalised within 3min; zero behavioural drift; pytest-rc-5 bug *was* caught by inline tests during impl — exact TDD mechanism intended. | provenance.log |
| [HIGH] code-reviewer inconsistent main-vs-master | **defer** → fix in M2.0 prep commit | Real correctness gap on master-default repos. Plan §8 documents `main` as default. Cleanest fix: drop `master` from Stage A's abort-1 `case`, keeping `main` consistently throughout (matches plan §8). One-line change. | provenance.log + this file |
| [MEDIUM] code-reviewer mypy silent rc | **defer** → M2.0 | Improves UX but mypy isn't currently configured in this repo (`[tool.mypy]` absent in pyproject.toml). The code path is dormant. Address before any project that enables mypy adopts the workflow. | this file |
| [MEDIUM] code-reviewer grep -Fxq newline fragility | **defer** → coupled with security MEDIUM | Edge case (filename with literal newline). Same fix (null-delimited paths) handles both findings. Address in M2.0 prep. | this file |
| [MEDIUM] security-auditor xargs without -d/-0 | **defer** → M2.0 | Same root cause as the grep-Fxq finding. Combined fix: use `git diff -z --name-only` + `xargs -0` throughout Stage B. | this file |
| [LOW] future-proofing "seven stages" hardcoded count | **defer** → M5.4 | Inside the introductory prose. Will be reviewed during M5's doc-drift reconciliation across README/CHANGELOG/CLAUDE.md/SECURITY.md/quick-ref. | this file |
| All INFO findings | **acknowledge** | Non-blocking, documentation-quality. | this file |

---

## Per-Agent Findings (verbatim summaries)

### code-reviewer

```
[HIGH] inconsistent-branch-target — Stage A's docstring declares main|master,
       but ahead-count (L102) and Stage B scope set (L125/136) hardcode main.
       On master-default repo: silent breakage (abort-4 fires spuriously).
[MEDIUM] non-fatal-typecheck-swallows-signal — `uv run mypy src/ 2>&1 || true`
       has no visible signal for type errors.
[MEDIUM] grep-Fxq-newline-fragility — filename with literal newline breaks the
       L-007 guard's membership test. Edge case.
[LOW] grep-c-fragility-on-empty — informational only.
[INFO] awk-fence-strictness — extractor matches exact ```bash; info-string
       suffixes silently drop the block.
[INFO] return-code-gap — codes 1,2,3,4,5,7 with 6 skipped.
SUMMARY: 0 CRITICAL, 3 WARNING, 2 INFO
```

### security-auditor

```
[MEDIUM] Path-with-newline / IFS injection via xargs -r (M2 will compound).
[LOW] grep -Fxq whole-line match — same root cause as code-reviewer MEDIUM.
[LOW] rm -rf "$TMPDIR" teardown — TMPDIR variable shadows the standard POSIX
      env var; quoted correctly, but suggests bats convention TEST_TMPDIR.
[LOW] eval "$(load_stages)" trust assumption — markdown is in-tree, but worth
      a comment documenting the trust boundary.
[INFO] git rev-list --count main..HEAD swallows revspec errors — UX defect,
      same root cause as code-reviewer HIGH.
N/A: OWASP A01-A10 (no auth surface, no crypto, no DB, no network calls in M1).
Verdict: PASS with minor hardening.
SUMMARY: 0 CRITICAL, 1 WARNING, 4 INFO
```

### tdd-sequence-auditor

```
VERDICT: FAIL
First src commit: 9af92ee @ 13:09:11
First tests/ commit (formal assertions): e04cb99 @ 13:12:08
first_test_ts >= first_src_ts → FAIL per decision tree step 7.
TDD-Waiver: ABSENT.
Recommendation: dispute or accept; future M2-M5 should write bats stubs first.
SUMMARY: 1 CRITICAL, 0 WARNING, 0 INFO
```

### context7-evidence-auditor

```
Zero changes to pyproject.toml / packages/codemem-mcp/pyproject.toml / uv.lock.
No new PyPI deps. No major version bumps. N/A for M1.
SUMMARY: 0 CRITICAL, 0 WARNING, 0 INFO
```

### future-proofing-auditor

```
[LOW] hardcoded "seven stages" prose claim — sole-dev-merge.md:36.
[INFO] hardcoded "four sources" — inside HTML placeholder (template). M2 will replace.
[INFO] magic numbers 1-5,7 — return codes; documented in plan §4.1.2 + pinned by bats. No finding.
[INFO] pytest exit code 5 — self-documented via adjacent comment. No finding.
[INFO] timeout literals 900s/30s/15-min — in M4 placeholder. Address at M4 landing.
No version-pin findings. No premature abstractions.
SUMMARY: 0 CRITICAL, 1 WARNING, 3 INFO
```

---

## Resulting Verdict

**PASS_WITH_WARNINGS** after override decisions applied. CRITICAL disputed with empirical-validation evidence; 5 WARNINGs deferred (4 to M2.0 prep, 1 to M5.4 doc-drift reconciliation).

§6.8 closes without blocking M2 start.

---

## Follow-up Tasks Created (Defer Decisions)

### M2.0 — pre-M2 hardening (RESOLVED — see commit history)

The 3 deferred findings were addressed in a single M2.0 hardening commit
before M2.1 begins:

1. **Main-only consistency fix** — RESOLVED. Stage A abort-1 changed from
   `case "$original_branch" in main|master) …` to `if [ "$original_branch"
   = "main" ]`. Aligns with plan §8 (`main` is the documented default).
2. **Null-delimited paths** — RESOLVED. Stage B fully rewritten to use
   `git diff -z --name-only` + bash arrays (`CHANGED_FILES_ARR`,
   `CHANGED_PY_ARR`, `CHANGED_SH_ARR`) + associative-array O(1) membership
   lookup (`declare -A in_scope`). No more `xargs -r` against
   newline-separated strings.
3. **mypy signal visibility** — RESOLVED. mypy now runs with `rc` captured,
   error count parsed from output, and a `Stage B: mypy reported N issue(s)
   (non-fatal)` line emitted to stdout so the user has visible signal.

Regression coverage: new bats test
"Stage B: L-007 guard handles filenames with spaces (M2.0 regression)" —
plants both in-scope and out-of-scope files whose paths contain spaces and
asserts the L-007 guard correctly classifies them. Combined bats run:
12/12 pass.

### M5.4 — doc-drift reconciliation (DEFERRED)

4. **"seven stages" prose count** — rephrase to drop the redundant cardinal
   ("stages A-G" already conveys count); or move to a generated count.

---

# §6.8 Review — Milestone 2 (2026-05-18)

## Summary

| Agent | CRITICAL | WARNING | INFO | Verdict |
|-------|:--------:|:-------:|:----:|---------|
| code-reviewer             | 0 | 3 | 2 | PASS_WITH_WARNINGS |
| security-auditor          | 0 | 2 | 4 | PASS_WITH_WARNINGS |
| tdd-sequence-auditor      | 1 | 0 | 0 | FAIL (project convention) |
| context7-evidence-auditor | 0 | 0 | 0 | PASS |
| future-proofing-auditor   | 0 | 2 | 6 | PASS_WITH_WARNINGS |
| **TOTAL**                 | **1** | **7** | **12** | **PASS_WITH_WARNINGS** (post-override) |

**Milestone window:** `78178d5..2eb790c` (3 commits — 480ad36, 2b826c8, 2eb790c).

## CRITICAL Findings — User Override Decisions

| Finding | Decision | Rationale |
|---|---|---|
| [CRITICAL] tdd-sequence FAIL (same commit landed impl + tests) | **dispute** | Project convention established in M1 §6.8: plan-§4 schedules bats after impl; empirical inline harnesses ran continuously during impl (provenance evidence — bugs #1-#3 caught during impl phase). Auditor itself acknowledged this is "expected to be DISPUTED per M1 precedent". Same rationale applies verbatim. |

## High-Value WARNING Findings — Disposition

| Finding | Severity | Disposition | Notes |
|---|---|---|---|
| `_sdm_parse_findings` defined but never called (dead code + mechanism duplication) | WARNING ×2 | **defer → M3.0 prep** | Stage D bypasses the helper with inline `grep -cE`. Safe-default fallback contract is advertised in prose but not actually exercised. Fix: either wire helper into Stage D (preserves the contract) or delete + remove prose claim (KISS). |
| Schema-breaking regex mismatch: prose `(.+?)` non-greedy vs helper `(.+)` greedy | WARNING | **defer → M3.0 prep** | Em-dash inside a finding message would split differently. Same fix as above ties the two together. |
| Magic number 4 (AUQ panel size) hardcoded 4× in `_sdm_log_auq_dispatches` | WARNING | **defer → M3.0 prep** | Extract `local AUQ_MAX_OPTIONS=4` at function top. |
| B602 regex over-matches string literals containing `shell=True` | LOW | **acknowledge** | Documented narrow scope per plan §2.5. AST-aware fix is a libcst upgrade, out of scope. Bandit-flagged-only file set limits blast radius. |
| Hardcoded counts: "4 sources" / "3-source" prose | INFO ×2 | **defer → M5.4** | Bundled with existing M5.4 doc-drift reconciliation. |

## Resulting Verdict

**PASS_WITH_WARNINGS** after override decisions. CRITICAL disputed (project convention per M1 precedent). Three WARNINGs deferred to M3.0 prep — they share a common Stage D refactor (wire `_sdm_parse_findings` into the aggregation flow + extract AUQ constant) so they can be fixed together in one commit before M3.1 starts.

## Per-Agent Findings (verbatim summaries)

### code-reviewer
```
[WARNING] dead code: _sdm_parse_findings has zero callers — Stage D bypasses
       with inline grep. Safe-default fallback contract is never exercised.
[WARNING] mechanism duplication: two severity-classifier paths in M2.
[WARNING] schema-breaking output regression: prose regex (.+?) non-greedy vs
       helper regex (.+) greedy — diverge on em-dash in message.
[INFO] magic number 4 hardcoded 4 places in _sdm_log_auq_dispatches.
[INFO] DRY: setup() blocks in both bats files duplicate ~25 lines.
SUMMARY: 0 CRITICAL, 3 WARNING, 2 INFO
```

### security-auditor
```
[LOW] B602 regex over-matches string literals containing `shell=True`.
[LOW] jq `.filename` trust: safe — only used as file args, never shell-eval.
[INFO] Stage C1/C2 diff content not shell-evaluated.
[INFO] MOCK_AGENT_DISPATCH fixture path safe (test-only).
[INFO] /tmp/sole-dev-merge-*-${slug}.* predictable paths; sole-dev assumption.
[INFO] L-007 array pattern carried through cleanly from M1.0/M2.0.
SUMMARY: 0 CRITICAL, 2 WARNING, 4 INFO
```

### tdd-sequence-auditor
```
VERDICT: FAIL (mechanical) — superseded by project convention (advisory).
First src commit: 480ad36 (same SHA as first tests/ commit — both landed atomically).
TDD-Waiver: ABSENT.
Per M1 §6.8 precedent, expected to be DISPUTED.
Recommendation: add TDD-Waiver canonical class or accept advisory.
SUMMARY: 1 CRITICAL, 0 WARNING, 0 INFO
```

### context7-evidence-auditor
```
Zero changes to pyproject.toml / packages/codemem-mcp/pyproject.toml / uv.lock.
M2 invokes bandit/shellcheck/jq as system binaries (not PyPI deps).
SUMMARY: 0 CRITICAL, 0 WARNING, 0 INFO
```

### future-proofing-auditor
```
[WARNING] magic number 4 hardcoded 4× in _sdm_log_auq_dispatches.
[WARNING] premature abstraction: _sdm_parse_findings has zero call sites.
[INFO] hardcoded counts "3-source security", "all four finding sources",
       "Aggregate all 4 sources" — drift class same as "seven stages".
[INFO] regex narrowness intentional + documented (B602 + test_id filter).
[INFO] no pinned tool version strings in M2.
[INFO] /tmp/ side-channel constant — POSIX tmpdir convention.
SUMMARY: 0 CRITICAL, 2 WARNING, 6 INFO
```

## Follow-up Tasks Created (Defer Decisions)

### M3.0 — pre-M3 hardening (TO BE ADDRESSED before M3.1)

1. **Wire `_sdm_parse_findings` into Stage D aggregation** OR delete it cleanly. Either resolves dead code, mechanism duplication, AND schema-breaking regex mismatch in one move. Preferred: delete (KISS — Stage D's inline grep is simpler and sufficient).
2. **Extract `AUQ_MAX_OPTIONS=4`** as a function-local readonly in `_sdm_log_auq_dispatches`.
3. **Add inline comment** at B602 regex documenting the extension-point convention ("new Bandit IDs require explicit handler — do not generalise").

### M5.4 — doc-drift reconciliation (DEFERRED, accumulated)

Add "4 sources" / "3-source" / "seven stages" to the Tier 6 watch keywords for the doc-drift reconciliation commit.
