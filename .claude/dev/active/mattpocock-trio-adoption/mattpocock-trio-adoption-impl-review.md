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

---

# Impl Review Report: mattpocock-trio-adoption / Milestone 2

**Milestone:** Milestone 2: Fork `grilling`; `grill-with-docs` becomes Derived · **Audit-Profile:** code-only · **Window:** 771bc25..5d2ff5d (+ post-review fix commit) · **Date:** 2026-09-21 · **Budget:** normal (parallel, full context)

## Summary

| Agent                     | CRITICAL | WARNING | INFO | Verdict |
|---------------------------|:--------:|:-------:|:----:|---------|
| code-reviewer             |    0     |    2    |  3   | WARN    |
| security-auditor          |    0     |    1    |  3   | WARN    |
| tdd-sequence-auditor      |    0     |    0    |  0   | PASS    |
| context7-evidence-auditor |    0     |    0    |  0   | PASS    |
| future-proofing-auditor   |    0     |    1    |  3   | WARN    |
| **TOTAL**                 |  **0**   |  **4**  |**9** | **PASS_WITH_WARNINGS** |

Disposition: 4/4 WARNING fixed; 2/9 INFO fixed; 7/9 INFO acknowledged. No override panel (0 CRITICAL).

## Code Review (code-reviewer agent)

Mandatory patterns: scope discipline CLEAN (15 files, all in Required Artefacts / AA-MA); mechanism duplication CLEAN (rounds vs one-at-a-time split documented in ADR-0002 amendment); schema-breaking output CLEAN; dead code CLEAN.

### Findings
- [WARNING] dangling-constant: `claude-code/commands/aa-ma-plan.md` — "the ≤5 concurrent-agent cap" referenced with a definite article but defined nowhere shipped. **FIXED** → direct instruction "dispatch at most 5 fact-finding sub-agents at once".
- [WARNING] delegation-seam: `grill-with-docs/SKILL.md` — `<supporting-info>` assumed the orchestrator explores the codebase; after delegation, `grilling`'s fact sub-agents never see the domain block, so CONTEXT.md / docs/adr discovery might not fire. **FIXED** → `<what-to-do>` gains a first line: read `CONTEXT.md` / `CONTEXT-MAP.md` / `docs/adr/` yourself before calling grilling (block now 4 lines, ≤6 AC; Contract deviation recorded as AD-005).
- [INFO] cosmetic-churn: `FORKS.json` write-a-skill row reformatted compact→expanded by the serialiser. Acknowledged.
- [INFO] weak-assertion: `test_grill_with_docs_frontmatter.py` substring match + no ≤6-line assert. **FIXED** → asserts literal `Skill tool with "grilling"` and `len(lines) <= 6`.
- [INFO] documented-split: `with-docs` interviews in rounds, `simple` stays one-at-a-time — already in ADR-0002 amendment. Acknowledged.

## Security (security-auditor agent)

### Mechanical pre-check (security-static-check.sh): PASS (no `[security-bypass:` marker in window)

Verified clean: supply chain — fork pinned to `c55ee46`, agent re-fetched upstream, body byte-identical, md5 `284efe9c…` matches `files` + `upstream_md5`, integrity enforced by `test_local_md5_matches_manifest`; prompt-injection surface of the 29-line fork — none; credential/log flow — none; test path handling — constants + `yaml.safe_load`.

### Semantic findings
- [WARNING] A08 third-party prompt with session authority: `grilling/SKILL.md:27` "dispatch a sub-agent" — upstream text defines the lookup boundary; the agent cap bounds concurrency not scope. **FIXED** in plugin-owned text (`aa-ma-plan.md` with-docs bullet): sub-agents scoped to read-only, repo-local exploration (filesystem, git, Context7), never external connectors or writes. Fork stays verbatim.
- [INFO] A08 name-based resolution `Skill("grilling")` — live check recorded resolution to ours. Acknowledged.
- [INFO] A08 `grill-with-docs` drift tracking dropped by design — confirmed: live `fork-drift.sh --sha c55ee46` → grill-with-docs ORPHAN (by design), **grilling SAME**. Acknowledged.
- [INFO] A09 absolute `/home/…` paths in context-log excerpt — private repo, consistent with existing artefacts. Acknowledged.

## TDD Sequence (tdd-sequence-auditor agent)

### Verdict: PASS
No `TDD-Waiver`. Strict rule (src/): vacuous PASS (no src/ commits). Lead-directed rule (`claude-code/skills/` as impl tree): M2.1 red 7542c30 (10:17:54) → green bc329d4 (10:18:25), +31s; M2.2 red 936fb1d (10:18:48) → green 7030200 (10:19:49), +61s. Test commits pure; impl commits contain no tests. L-017a applied.

## External Library Evidence (context7-evidence-auditor agent)

`git diff 771bc25..5d2ff5d -- pyproject.toml uv.lock` empty. No new PyPI deps, no major bumps. PASS (not applicable).

## Future-Proofing (future-proofing-auditor agent)

Source-of-truth verified: 20 skill dirs; SECURITY.md / foundations / local CLAUDE.md all 20; count tests derive from disk (`is_dir()`), so FORKS.json correctly excluded.

### Findings
- [WARNING] hardcoded count drift caused by M2 outside the window: `docs/adr/0012-research-skill-adoption.md:95` said "19 → 20 skills" for M4. **FIXED** → "20 → 21 skills".
- [INFO] undefined-referent "≤5 cap" (same as code-reviewer W1). **FIXED** (see above).
- [INFO] `docs/adr/0002` amendment said "`<what-to-do>` is three lines". **FIXED** → "a short delegating block".
- [INFO] source-of-truth trap: `ls claude-code/skills | wc -l` = 21 because FORKS.json lives there; use `find … -type d`. Acknowledged — noted in reference.md count-site table.

## User Override Decisions

None required (0 CRITICAL).

## Revision History

- 2026-09-21 — M2 review run; 4 WARNING + 2 INFO fixed in the same session before §7.3; 7 INFO acknowledged.
