# Impl Review Report: mattpocock-trio-adoption / Milestone 1
Generated: 2026-09-21T09:05:00+01:00 | Audit-Profile: code-only | Budget: normal
Window: c47e15b..8d91442 (M1 commit) · fixes landed in d755920 (red) + 4144305 (green)

## Summary
- CRITICAL: 2 findings (1 accepted → fixed, 1 disputed, 0 deferred)
- WARNING: 8 findings (5 fixed, 3 acknowledged)
- INFO: 13 findings (4 fixed, 9 acknowledged)
- Overall: PASS WITH WARNINGS (after fix-now pass)

---

## Code Review (code-reviewer agent)

Scope discipline CLEAN (18 files, all in Required Artefacts or AA-MA artifacts); mechanism duplication NONE; schema-breaking output NONE; dead code NONE; Contract conformance verified against reference.md "Milestone 1 Contract".

### Findings

- [CRITICAL] fail-open on malformed manifest: `scripts/fork-drift.sh:46-51` — `python3 -c` flatten inside `< <(…)`; missing key → traceback, exit 0, zero rows. Reproduced live (`KeyError: 'files'`, `EXIT=0`). **FIXED**: manifest read only by `aa_ma.forks` (`files` subcommand, `rows="$(forks files)"` under `set -e`); bats case "malformed manifest → exit 1 naming the key".
- [WARNING] temp-file leak: `${err}.json` outside the trap. **FIXED**: no second temp file; fetch buffered in a variable.
- [WARNING] KISS / double manifest reader (three inline python3 programs). **FIXED**: `files` + `classify-all` subcommands; shell is fetch loop only; one interpreter.
- [WARNING] DRY — manifest path ×3. **FIXED**: `aa_ma.forks.DEFAULT_MANIFEST`; `_helpers.FORKS_MANIFEST = DEFAULT_MANIFEST`; test imports it.
- [INFO] magic number `sed -n '2,13p'` for --help. **FIXED**: awk leading-comment block; bats case.
- [INFO] CLI edge cases (IndexError/KeyError). **FIXED**: exit 2 with usage; pytest case.
- [INFO] double `read_bytes()`. **FIXED**.
- [INFO] N interpreter startups. **FIXED** (one `classify-all`).

---

## Security (security-auditor agent)

### Mechanical pre-check (security-static-check.sh): PASS (no `[security-bypass:` marker on 8d91442)

### Semantic findings

- [WARNING] CWE-377 predictable sibling temp path `${err}.json` (fork-drift.sh:33/58). **FIXED** (file removed entirely).
- [INFO] A03 manifest values reach the `gh api` path unvalidated — not exploitable (quoted array, fixed prefix, same principal, tab/newline fails closed). Acknowledged; optional allowlist deferred.
- [INFO] A08 `GH=` env seam runs an arbitrary command — same-principal; constraint recorded: never wire fork-drift.sh into a hook/CI step with untrusted env. Acknowledged.
- [INFO] A07 GitHub answers 404 (not 403) for a repo the caller cannot see → would have reported every fork ORPHAN. **FIXED**: repo pre-flight `gh api repos/mattpocock/skills` before the loop; bats case. During the fix a second fail-open surfaced and was fixed: a mid-loop 403 still fed partial rows to the classifier via the pipe (beta printed ORPHAN before pipefail returned 1) — the fetch is now buffered and classification runs only on a complete fetch.
- [INFO] A02 MD5 for drift detection — acceptable (gates no trust decision). Acknowledged; switch to sha256 if a future milestone auto-applies upstream content.

---

## TDD Sequence (tdd-sequence-auditor agent)

### Verdict: FAIL (git-log criterion) — DISPUTED with evidence

### Evidence
- Milestone window: c47e15b .. 8d91442
- First `tests/` commit: 8d91442 at 2026-09-21T09:55:08+01:00
- First `src/` commit: 8d91442 at 2026-09-21T09:55:08+01:00 (same commit; delta 0 → `>=` branch)
- TDD-Waiver: (none)
- Provenance evidence (not admissible to the auditor, weighed by the orchestrator): provenance.log `STEP 1.1 COMPLETE … RED: ModuleNotFoundError aa_ma.forks` (09:49:53) precedes `STEP 1.2 COMPLETE — src/aa_ma/forks.py` (09:50:51); tasks.md Sub-step 1.1 Result Log records the RED run.
- Corrective action: the §6.8 fix pass was committed red-first (`d755920 test(forks): …` before the green commit); rule recorded as L-017(a) for M2+.

### Per-file pairing (informational only)
- src/aa_ma/forks.py → tests/skills/test_fork_manifest.py ✅ paired
- scripts/fork-drift.sh → tests/hooks/fork-drift.bats ✅ paired (bats)

---

## External Library Evidence (context7-evidence-auditor agent)

### New PyPI dependencies in milestone diff

- [WARNING] pyyaml>=6 (`[dependency-groups] dev`, pyproject.toml:100) — no CONTEXT7 evidence at review time. Mitigation: `yaml.safe_load` already used in 4 test files at the base sha; declaration-only, no new API surface. Stub written to provenance.log: `CONTEXT7 — pyyaml@6.x — yaml.safe_load (declaration-only …)`. Acknowledged.

### Major version bumps in milestone diff

No major version bumps introduced.

---

## Future-Proofing (future-proofing-auditor agent)

Source-of-truth verified on disk: skills 19 / commands 12 / agents 11; foundations headings match.

### Findings

- [WARNING] enumerated CI pytest list (security.yml:169) already missed `tests/test_grammar.py`, `test_grammar_parity.py`, `test_active_plans_canonical.py` and `tests/tui` (190 tests in no workflow). **FIXED** (user-approved, Step 1.6 Result Log amended): exclusion-based `pytest tests --ignore=tests/codemem --ignore=tests/perf --ignore=tests/test_goal_synthesis.py` → 513 passed locally. L-017(c).
- [WARNING] magic help range `sed -n '2,13p'`. **FIXED** (awk block + bats case).
- [WARNING] `8b1a9953…` = md5("Hello") pasted 4× across fixture + bats. **FIXED**: derived in bats `setup()`; fixture row carries a `_comment` linking it to the stub payload.
- [INFO] README `write-a-skill` row "100-line split, 6-item checklist" — numerals unpinned. Acknowledged (plan-mandated wording; Tier 6 watch).
- [INFO] `aa-ma-forge v0.13.0` forward-stamp on write-a-skill line 1 — contract-mandated (v0.6.0 precedent); outside the md5 recipe. Acknowledged; runbook note deferred to TODOS.md.
- [INFO] `parents[2]` depth-pinned path — commented (`# src/aa_ma/forks.py → repo root`); repo idiom. Acknowledged.
- [INFO] literal sha in fixture/test — not load-bearing (classifier never reads `upstream_sha`). Acknowledged.
- [INFO] upstream repo identity hardcoded in two sites — YAGNI; add optional `upstream_repo` row key if a second upstream ever appears. Acknowledged.

---

## User Override Decisions

| Severity | Finding | Decision | Rationale |
|---|---|---|---|
| CRITICAL | fork-drift.sh fail-open on malformed manifest | accept → fixed now | Reproduced live; fixed via `aa_ma.forks` subcommands (also closes 3 WARNING + 1 INFO); red test committed first (d755920) |
| CRITICAL | TDD sequence FAIL (tests + src in one commit) | dispute | RED→GREEN evidenced by provenance.log + tasks.md Result Log; commit already pushed to main; L-017(a) makes the git-log criterion pass mechanically from M2 on |

Convention learned for this project: the milestone's *first* commit after a RED run is a `test(...)`-only commit.

---

## Revision History

- v1: 2026-09-21 — Initial impl review: 2 CRITICAL, 8 WARNING, 13 INFO → BLOCKED pending panel
- v2: 2026-09-21 — Fix-now pass (1 accepted CRITICAL fixed, 1 disputed; 5 WARNING + 4 INFO fixed) → PASS WITH WARNINGS
