# Impl Review Report: [task-name] / Milestone [N]
Generated: [YYYY-MM-DDTHH:MM:SSZ] | Audit-Profile: [profile] | Budget: [normal|low]

## Summary
- CRITICAL: [N] findings ([M] accepted, [P] disputed, [Q] deferred)
- WARNING: [N] findings
- INFO: [N] findings
- Overall: [BLOCKED | PASS WITH WARNINGS | PASS]

---

## Code Review (code-reviewer agent)

Catches: KISS / SOLID / SOC / DRY violations, scope discipline (L-007), mechanism duplication (L-005), schema-breaking output (L-006), dead code, magic numbers.

### Findings

<!-- One entry per finding. Required for CRITICAL: file:line + impact + suggested fix -->
<!-- - [CRITICAL] [pattern]: file:line — impact: "X" — suggested fix: "Y" -->
<!-- - [WARNING] [pattern]: file:line — "X" -->
<!-- - [INFO] [pattern]: file:line — "X" -->

No findings — code review clean.

---

## Security (security-auditor agent)

Mechanical layer caught at commit time by `security-static-check.sh` PreToolUse hook (CWE-502, injection, secrets, etc.). The agent below performs the **semantic** review.

### Mechanical pre-check (security-static-check.sh): [PASS | BLOCKED at commit | BYPASSED via marker]

### Semantic findings

<!-- - [CRITICAL] [OWASP class]: file:line — impact: "X" — suggested fix: "Y" -->
<!-- - [WARNING] [concern]: file:line — "X" -->

No findings — security review clean.

---

## TDD Sequence (tdd-sequence-auditor agent)

### Verdict: [PASS | FAIL | WAIVED]

### Evidence
- Milestone window: [base_sha] .. [head_sha]
- First `tests/` commit: [sha] at [timestamp]
- First `src/` commit: [sha] at [timestamp]
- TDD-Waiver: [canonical-value or "(none)"]

### Per-file pairing (informational only)

<!-- One entry per touched src file -->
<!-- - src/foo.py → tests/test_foo.py ✅ paired -->
<!-- - src/bar.py → no matching test file (integration-tested elsewhere) -->

---

## External Library Evidence (context7-evidence-auditor agent)

### New PyPI dependencies in milestone diff

<!-- - [PASS] new-package@1.2.3 — Context7 evidence at provenance.log:line N -->
<!-- - [WARNING] new-package@1.2.3 — no Context7 evidence found; auto-stub: -->
<!--     [ts] CONTEXT7 — new-package@1.2.3 — <doc-section-referenced> -->

No new PyPI dependencies introduced.

### Major version bumps in milestone diff

<!-- - [WARNING] commitizen: 3.x → 4.x — no Context7 evidence; verify API surface unchanged -->

No major version bumps introduced.

---

## Future-Proofing (future-proofing-auditor agent)

Catches: hardcoded counts about to drift (Tier 6+), magic numbers, pinned version strings, premature abstractions.

### Findings

<!-- - [CRITICAL] hardcoded count: README.md:42 says "5 skills" but skills/ has 16 — drift -->
<!-- - [WARNING] magic number (3+ occurrences): src/foo.py:N — extract constant -->
<!-- - [INFO] hardcoded version: pyproject.toml:N pinned at ==1.2.3 — consider >=1.2,<2.0 -->

No findings — future-proofing clean.

---

## User Override Decisions

<!-- One row per CRITICAL finding surfaced via AskUserQuestion -->

| Severity | Finding | Decision | Rationale |
|---|---|---|---|
| CRITICAL | [summary] | [accept|dispute|defer] | [user note] |

Disputes are logged here and fed back to the next-run agent prompt as
"convention learned for this project" — reduces false-positive rate over time.

---

## Revision History

<!-- One entry per run. Format: vN: [date] — N CRITICAL, N WARNING → result -->

- v1: [YYYY-MM-DD] — Initial impl review: [N] CRITICAL, [N] WARNING → [result]
