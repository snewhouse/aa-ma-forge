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

**Milestone:** Milestone 2: Fork `grilling`; `grill-with-docs` becomes Derived · **Audit-Profile:** code-only · **Window:** 771bc25..5d2ff5d (fixes landed in 022e036) · **Date:** 2026-09-21 · **Budget:** normal (parallel, full context)

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

---

# Impl Review Report: mattpocock-trio-adoption / Milestone 3

**Milestone:** Milestone 3: `prototype` Re-fork + planning gate + gate roll-up · **Audit-Profile:** full · **Critical-Path:** hook-modification · **Window:** d87c16a..4cedc91 (fixes: 75aa6f7, 0cb97a3, 3c6f92f) · **Date:** 2026-09-21 · **Budget:** normal

## Summary

| Agent                     | CRITICAL | WARNING | INFO | Verdict |
|---------------------------|:--------:|:-------:|:----:|---------|
| code-reviewer             |    0     |    3    |  4   | WARN    |
| security-auditor          |    0     |    2    |  4   | WARN    |
| tdd-sequence-auditor      |    0     |    0    |  0   | PASS    |
| context7-evidence-auditor |    0     |    0    |  0   | PASS    |
| future-proofing-auditor   |    0     |    2    |  4   | WARN    |
| **TOTAL (unique)**        |  **0**   |  **5**  |**12**| **PASS_WITH_WARNINGS** |

Two WARNINGs were raised by both code-reviewer and future-proofing (template "Leave blank"; spec LIVE_CHECK header) → 7 raw, 5 unique. Disposition: 5/5 WARNING fixed; 6/12 INFO fixed; 6 acknowledged. No override panel (0 CRITICAL). Ste chose "roll it up now" for the security WARNING (AskUserQuestion).

## Code Review (code-reviewer agent)

Mandatory patterns: scope discipline CLEAN (ADR-0003 undeclared but mandated by the Re-fork glossary → added to 3.4 Artefacts); mechanism duplication CLEAN (`_read_steps` reuses `read_enforced_field` + `_read_or_error`; scoping difference is AD-001); schema-breaking output CLEAN (`to_kv`/JSON id untouched; `prototype_required` is a superset); dead code CLEAN (`_count_pending` 0 refs); magic numbers CLEAN.

### Findings
- [WARNING] doc-contradiction: `tasks-template.md` milestone Critical-Path comment "Leave blank or omit" two lines above "an empty value is a gate error". **FIXED** → "Omit if no critical path applies."
- [WARNING] doc-accuracy: spec provenance-grammar header claimed §6.7 reads LIVE_CHECK (zero readers). **FIXED** → PROTOTYPE/CRITICAL_PATH_REVIEW gate-read; LIVE_CHECK marked advisory.
- [WARNING] ordering: `ENG_STANDARDS_DECLARED` echo sat in Step 2.4 but needs `PROTO` from Step 2.5; "append to the line above" implied editing an append-only log. **FIXED** → THEMES captured in 2.4, the single echo runs at the end of 2.5 (or 5.6 when buffered).
- [INFO] scope: ADR-0003 not in 3.4 Artefacts. **FIXED** (added).
- [INFO] DRY: `_read_or_error(read_enforced_field(...))` triad at 6 sites. Acknowledged — pre-existing idiom; helper deferred.
- [INFO] KISS: `MilestoneRead(**{**asdict(read), …})` → `dataclasses.replace`. **FIXED**.
- [INFO] granularity: `prototype=<M-list>` has no sub-step notation. **FIXED** → prose states the list names the milestone a flagged sub-step rolls up to.

## Security (security-auditor agent)

### Mechanical pre-check (security-static-check.sh): PASS (no `[security-bypass:` markers in 7 commits)

Verified: no fail-open path in `_read_steps` (absent → None; invalid/empty → exit 2; roll-up is OR-only, a crafted sub-step can only add a requirement); §8.3/8.4 no shell injection (`$COMMIT_HASH` hex, double-quoted `-m`); prototype re-fork pin independently re-fetched from raw.githubusercontent @ c55ee46 — md5s match FORKS.json and local `tail -n +2`, upstream main has no post-pin drift; LOGIC.md inline HTML only, no CDN/shell; fixture path handling constant.

### Semantic findings
- [WARNING] A04 sub-step `Critical-Path` advertised in the template but not read by the gate — a sub-step `auth-flow` passed the HARD gate with no review evidence; invalid value exited 0. **FIXED (user decision: roll it up now)** → `_read_steps` reads `Critical-Path` per sub-step; milestone value wins; disagreeing sub-steps refuse; invalid/empty refuse. Red tests 0cb97a3 → green 3c6f92f; fixture M5–M8; mirror bats fence case (32/32).
- [WARNING] A01 `UI.md` sub-shape B route renders "real data" with no auth guidance (only the switcher is `NODE_ENV`-gated). **FIXED** in plugin-owned text: Theme 1 sentence — UI-branch throwaway routes sit behind the host app's auth middleware and read stubs/fixtures; ADR-0003 amendment records the upstream gap. Fork stays verbatim.
- [INFO] §8.4 fence footer `[AA-MA Plan] $TASK_NAME` unexpanded → commit-signature hook BLOCKs (fail-closed, same shape as §8.2). Acknowledged.
- [INFO] FORKS.json `files` is the banner-stripped hash, not on-disk `md5sum`. Acknowledged — by design (ADR-0003 "modulo provenance comment").
- [INFO] fixture referenced via constant path; bats copies then `sed -i`s the copy. Acknowledged.
- [INFO] HTML-commented `Prototype-Required: YES` reads as absent (pre-existing sanitize behaviour). Acknowledged.

## TDD Sequence (tdd-sequence-auditor agent)

### Verdict: PASS (strict src/ rule)
First tests/ commit f762730 (10:37:13) precedes first src/ commit 1b1cabf (10:38:32) by 79s; red bats 6565ceb precedes commands c8cea54 by 70s. Only src/ touch in window is 1b1cabf. Post-review: red 0cb97a3 precedes 3c6f92f (Critical-Path roll-up). No TDD-Waiver.

## External Library Evidence (context7-evidence-auditor agent)

`pyproject.toml` / `uv.lock` unchanged; no dependency manifest in the 22-file window. PASS (not applicable).

## Future-Proofing (future-proofing-auditor agent)

Verified clean: bats count; gate.py "seven" enumerates 7; template slots 4→0; `_count_pending` 0 refs outside CHANGELOG; "terminal TUI" only in docs/research/; `StepsRead` contract-mandated and not misused; no magic numbers / pins / date literals.

### Findings
- [WARNING] template "Leave blank or omit" contradiction (same as code-reviewer W1). **FIXED**.
- [WARNING] spec header names LIVE_CHECK as gate-read (same as code-reviewer W2). **FIXED**.
- [INFO] grammar drift: template:75 and engineering-standards checklist row still `PROTOTYPE — <verdict>`. **FIXED** → `<milestone heading> — <verdict>` everywhere (0 stragglers incl. both commands).
- [INFO] ADR-0011:63 "line stays `PROTOTYPE — <verdict>`" contradicts implementation. **FIXED** (amended in place).
- [INFO] spec "`## Milestone N: …` byte-for-byte" — gate prints the heading without `## `. **FIXED** → "the text after `## `, as `aa-ma-gate` prints it".
- [INFO] `prototype=<M-list>` token has no reader beyond the smoke test. Acknowledged.

## User Override Decisions

None required (0 CRITICAL). Non-panel decision: security W1 → "Roll it up now" (Ste, AskUserQuestion).

## Revision History

- 2026-09-21 — M3 review run; 5/5 WARNING + 6/12 INFO fixed in 75aa6f7 / 0cb97a3 (red) / 3c6f92f; 6 INFO acknowledged.

---

# Impl Review Report: mattpocock-trio-adoption / Milestone 4

**Milestone:** Milestone 4: Adopt `research` as `aa-ma-research` + `aa-ma-researcher` agent; Phase 3 writes files; release v0.13.0 · **Audit-Profile:** code-only · **Critical-Path:** doc-count-drift · **Window:** 51ec995..d50772b (fixes: 3c31c3c red, 252e690) · **Date:** 2026-09-21 · **Budget:** normal

## Summary

| Agent                     | CRITICAL | WARNING | INFO | Verdict |
|---------------------------|:--------:|:-------:|:----:|---------|
| code-reviewer             |    0     |    3    |  3   | WARN    |
| security-auditor          |    0     |    3    |  4   | WARN    |
| tdd-sequence-auditor      |    0     |    0    |  1   | PASS    |
| context7-evidence-auditor |    0     |    0    |  0   | PASS    |
| future-proofing-auditor   |    0     |    2    |  6   | WARN    |
| **TOTAL**                 |  **0**   |  **8**  |**14**| **PASS_WITH_WARNINGS** |

Disposition: 8/8 WARNING fixed (red test 3c31c3c → 252e690); 3/14 INFO fixed, 2 deferred to TODOS.md, 9 acknowledged. No override panel (0 CRITICAL). No `src/` Python in the window; the code surface is two markdown contracts (skill + agent) with their tests.

## Code Review (code-reviewer agent)

Mandatory patterns: scope discipline PASS (every non-`.claude/dev/` file is a declared artefact or a release.sh/cz-bump dependency); mechanism duplication — one doc-level finding (W3); schema-breaking output PASS (`research_files=` additive, `_KV_RE` key-agnostic, no reader by key name; CHANGELOG heading rename + one bullet, L-006 clear; FORKS.json md5s verified, `derived` in the `Literal` at `forks.py:27`); dead code none; magic numbers none in code.

### Findings
- [WARNING] DRY: `tests/agents/test_aa_ma_researcher_agent.py::_split` was a copy of `test_codebase_onboarding_agents.py::_frontmatter`. **FIXED** → `tests/agents/_helpers.split_frontmatter` (mirrors `tests/skills/_helpers`), both tests import it.
- [WARNING] KISS/naming: Step 3.3 used three names for one dispatch tool and listed `Skill(aa-ma-research)` inside a "Task tool" block. **FIXED** → load the skill once, then `Agent(subagent_type: "aa-ma-researcher")` per question alongside `Agent(subagent_type: "Explore")`.
- [WARNING] mechanism duplication (docs): `PHASE_3_RESEARCH.md` example dispatch still routed research to `Agent 2 (research-analyst)` — an agent that exists nowhere. **FIXED** → `aa-ma-researcher` via `Skill(aa-ma-research)`, writes `docs/research/<slug>-<topic>.md`.
- [INFO] DRY (prose): 5-field header restated at three shipped sites with no test. **FIXED** (see future-proofing W1 — `HEADER_FIELDS` pinned).
- [INFO] consistency: Step 3.4 is the only phase with an inline `Marker:` line (criterion-driven `grep -c ≥ 2`). Acknowledged — asymmetry accepted.
- [INFO] scope: ADR INDEX row 0011 flipped in an M4 commit (M3 drift, recorded in 4.5 Result Log). Acknowledged, no action.

## Security (security-auditor agent)

### Mechanical pre-check (security-static-check.sh): PASS (no bypass markers in the window; no `src/` Python)

Credential-flow, authz, crypto and log-content checks clean by absence. Live-run output `docs/research/mattpocock-trio-adoption-install-backup.md` reviewed: correct path, `~` not absolute home, no tokens/env values, `path:line` cites.

### Semantic findings
- [WARNING] A03 prompt injection across the WebFetch/WebSearch boundary: agent holds Bash + Write with no "fetched text is evidence, not instructions" rule (same gap as `codebase-onboarding-health/synthesizer`; new instance of an existing pattern). **FIXED** → Non-negotiable added (phrase pinned in `REQUIRED_PROMPT_PHRASES`); Bash declared read-only inspection.
- [WARNING] A01 path confinement of the single Write: `<plan-slug>`/`<topic>` unconstrained; `/` or `..` moves the Write outside `docs/research/`. **FIXED** → `[a-z0-9-]+`, "no path separators" (pinned), direct-child rule in agent and in SKILL.md `## In this repo` (dispatching side); FORKS.json `files.SKILL.md` md5 refreshed, upstream recipe md5 unchanged.
- [WARNING] A03 agent-returned `<N>` counts reach the `aa-ma-plan-marker.sh` command line before the script's kv regex runs. **FIXED** → Step 3.4: "`<N>` is an integer you compute; never paste an agent's return text into the marker command line." Marker-regex tightening (`=[0-9]+$` for count keys) not taken — hook-modification Critical-Path, out of M4 scope.
- [INFO] A04 nesting control: structural (no Agent tool, test-pinned) is the real fix; prompt prohibition is fallback; no PreToolUse hook denies `claude -p` from a subagent's Bash. Acknowledged — acceptable for v0.13.0.
- [INFO] A09 live-run output clean. Acknowledged.
- [INFO] A08 FORKS.json provenance pinned (full sha, gh-api md5, ADR-0012). Acknowledged.
- [INFO] A08 release bump c27250b is a single commitizen-owned `[ad-hoc]` commit, no dep changes. Acknowledged.

## TDD Sequence (tdd-sequence-auditor agent)

### Verdict: PASS (no TDD-Waiver; strict `src/` rule vacuous — `claude-code/` skill + agent files treated as the implementation surface per L-017)
M4.1: red 52dfe9d (11:10:04) → green 6479d21 (11:11:10), Δ66s. M4.2: red 3fb7bf6 (11:11:45) → green 9ece1d4 (11:12:27), Δ42s. Each red commit touches only `tests/`; each green only `claude-code/`. Post-review: red 3c31c3c → 252e690.
- [INFO] 3750908 (M4.4) edits `aa-ma-plan.md` / `PHASE_3_RESEARCH.md` with no paired test — prose wiring, expected. Acknowledged.

## External Library Evidence (context7-evidence-auditor agent)

`pyproject.toml` / `uv.lock` diff is the project's own `0.12.0 → 0.13.0` (c27250b). No new PyPI deps, no major bumps. PASS (not applicable).

## Future-Proofing (future-proofing-auditor agent)

Verified clean: skills 21 / agents 12 match disk; SECURITY.md name lists diff clean; README skills table 21 rows; FORKS.json md5s under the `tail -n +2` recipe; `research_files=` needs no parser change (`_KV_RE` generic); `v0.13.0` / `c55ee46` / dates are historical pins; no Python source added.

### Findings
- [WARNING] duplicated contract literal: 5-field header lives at 4 prose sites, nothing tests or greps it. **FIXED** → `HEADER_FIELDS` tuple in the agent test asserts the template's bold fields exactly and that the live M4.3 file carries them; agent prose "the caller greps" → "pinned by the test".
- [WARNING] dangling skill reference: `research-consolidation` (user-local, not shipped) retained on two M4-rewritten lines. **FIXED** → annotated "user-local, not shipped by this plugin" at both sites.
- [INFO] README skills table has no row-set-vs-disk test (commands table has one). **DEFERRED** → TODOS.md.
- [INFO] SECURITY.md counts pinned by test. No action.
- [INFO] foundations headings pinned by test. No action.
- [INFO] "10 lines" cap in agent and command. **FIXED** → command says "short return"; number lives in the agent only.
- [INFO] "≤5 agents" cap duplicated in Step 3.3 and Step 1.3. **FIXED** → Step 3.3 references "the Step 1.3 agent cap".
- [INFO] `@ c55ee46` pinned in README/ATTRIBUTION prose; SSoT is FORKS.json. Acknowledged — matches grilling/prototype convention.
- Out of window (Tier 6 retroactive): `plan_elements=<N>/12` at `plan-marker-grammar.md:59` and `aa-ma-plan.md:89` — the standard has 13 elements since v0.12.0. **DEFERRED** → TODOS.md.

## User Override Decisions

None required (0 CRITICAL).

## Revision History

- 2026-09-21 — M4 review run; 8/8 WARNING + 3/14 INFO fixed in 3c31c3c (red) / 252e690; 2 INFO deferred to TODOS.md; 9 acknowledged.

---

# Post-Impl Adversarial Review — Milestone 5

**Milestone:** Milestone 5: Charting — `/aa-ma-chart` (Adaptation of wayfinder) + `--from-map`; release v0.14.0 · **Audit-Profile:** code-only · **Critical-Path:** hook-modification · **Prototype-Required:** YES · **Window:** 9319aed..cd8e54c (fixes: e42d9e7 red, 2bd406d) · **Date:** 2026-09-21 · **Budget:** normal

## Summary

| Agent                     | CRITICAL | WARNING | INFO | Verdict |
|---------------------------|:--------:|:-------:|:----:|---------|
| code-reviewer             |    0     |    5    |  5   | WARN    |
| security-auditor          |    1     |    4    |  2   | BLOCKED → fixed |
| tdd-sequence-auditor      |    0     |    0    |  1   | PASS    |
| context7-evidence-auditor |    0     |    0    |  2   | PASS    |
| future-proofing-auditor   |    1     |    4    |  5   | BLOCKED → fixed |
| **TOTAL**                 |  **2**   | **13**  |**15**| **PASS_WITH_WARNINGS** (after fix set) |

Disposition: 2/2 CRITICAL **accepted** and fixed; 13/13 WARNING fixed (red pins e42d9e7 → 2bd406d); 7/15 INFO fixed, 3 deferred to TODOS.md, 5 acknowledged. Security re-check on the fix commit: see Revision History. Code surface: one bash+awk helper (`hooks/lib/aa-ma-chart-guard.sh`), two command bodies with executable fences, install.sh block; no `src/` Python.

## Code Review (code-reviewer agent)

Mandatory checks: scope discipline CLEAN (27 diff files all declared in 5.1–5.5); mechanism duplication vs `aa-ma-parse.sh` CLEAN (reuses `aa_ma_is_disabled`; awk-over-markdown read documented as the ADR-0009 tension in the guard header); schema-breaking output CLEAN; dead code CLEAN; contract match ✓ (AD-014 `_cand` deviation accepted).

### Findings
- **[WARNING] KISS/DRY** `do_import` parsed the map three times with two count mechanisms — **FIXED** 2bd406d: one `do_from_map` capture, `n` from its `tickets=`.
- **[WARNING] safety** untracked `mv` clobbered an existing `<task>-map.md` — **FIXED**: `[ -e "$dest" ]` refusal before either branch (bats 24).
- **[WARNING] truthfulness** `claim` printed `claimed:` when no Status line was rewritten — **FIXED**: `set_status` exits 1 unless a Status line was replaced and `mv` succeeded; claim/reclaim refuse (bats 23).
- **[WARNING] broken-reference** spec row cites `[10]`, list ends at `[9]` — **FIXED** (same as FP CRITICAL): `[10]` added.
- **[WARNING] doc-drift** `MAP_IMPORTED` absent from the spec provenance-grammar block — **FIXED**: advisory line added beside LIVE_CHECK.
- [INFO] duplicate `[ -n "$3" ] && [ -n "$4" ]` check — **FIXED** (single check in the dispatcher).
- [INFO] `sed -n '2,10p'` usage tied to header lines — **FIXED**: heredoc `usage()`, pinned by bats 26.
- [INFO] `_cand` resolver duplicated in two command bodies — acknowledged (contract-mandated; extract on a third consumer).
- [INFO] third copy of the `if [ -f hooks/lib/X ]; then create_symlink` block in install.sh — **DEFERRED** → TODOS.md (loop over `hooks/lib/*.sh`, fixes L-005 at the root; ties to the existing install.sh backup entry).
- [INFO] template comment said a block "ends at the next `###`/`##`" — **FIXED**: fields must precede `#### Question`.

## Security (security-auditor agent)

### Mechanical pre-check (security-static-check.sh): PASS (no `[security-bypass:` marker in the window)

### Semantic findings
- **[CRITICAL] A01 path traversal to a destructive sink** — `aa-ma-chart.md` fog-test fence ran `rm -rf "$(dirname "$MAP")"` on an unvalidated `<effort>` and on any non-zero guard exit (incl. usage rc 2); empty or `../` effort could delete other efforts' maps or a live task dir. **User decision: accept → FIXED** 2bd406d: `EFFORT` validated against `^[a-z0-9-]+$` (exit 2) in the guard-resolution fence; removal gated on rc 1 only and scoped to `rm -f -- "$MAP"; rmdir -- "$(dirname "$MAP")"`; guard `map_effort` refuses a non-slug header with exit 2 before `fog` runs. Both fences are now **executed** by bats 27–28 (`../other` and empty effort → exit 2, sibling map intact; fogless draft → exit 1, only its own file + empty dir removed).
- **[WARNING] A01** `import <task>` unvalidated — **FIXED**: `slug_ok "$task"` → usage exit 2 (bats 21).
- **[WARNING] A04** `AA_MA_HOOKS_DISABLE=1` no-op'd `import` (map silently orphaned, `/aa-ma-plan` reported success) — **FIXED**: the kill switch wraps only the enforcing legs; `import` always runs, skipping just the clear check (bats 25).
- **[WARNING] A08** `claim` ignored `set_status` failure — **FIXED** (see code-review truthfulness); temp file removed on failure.
- **[WARNING] A03 prompt injection via repo-tracked map content** — **FIXED**: `aa-ma-plan.md` Step 1.0 loads `$SEED` inside a `<MAP_SEED>` block with a data-not-instructions preamble (only `Decided with <user> <date>` lines count as settled); `aa-ma-chart.md` rule 4 caps a Notes override at `docs/**` and requires `AskUserQuestion` the first time a session acts on one; `task` tickets go AFK only via their own `Mode:` field inside rule-4 paths.
- [INFO] A09 unvalidated map header flowed into `MAP_IMPORTED effort=` — **FIXED** by `map_effort` (slug or exit 2; `_KV_RE` contract in `plan_markers/parser.py` preserved).
- [INFO] research note embeds `/home/sjnewhouse/...` paths — acknowledged (private repo; `aa-ma-share` allowlist refuses `docs/research/*` and `*-map.md`).

Clean: no credential handling; `readlink -f` before `cd`; `mktemp` template; `ticket_num` digit-validates awk `-v` input.

## TDD Sequence (tdd-sequence-auditor agent)

### Verdict: PASS (no TDD-Waiver; tests side `tests/hooks/*.bats` + fixtures vs impl `hooks/lib/aa-ma-chart-guard.sh` + `scripts/install.sh`)
- First tests commit b3ac7ee 13:52:34 precedes first implementation commit 50c8099 13:55:41 by 3m07s (L-017a honoured: RED on its own commit).
- [INFO] 28c6844 changes the guard and adds its pinning bats case in one commit — not a sequence violation. The §6.8 fix set repeated the pattern properly: e42d9e7 (8 red cases) → 2bd406d.

## External Library Evidence (context7-evidence-auditor agent)

No `pyproject.toml`/`uv.lock` change; no Context7 trigger. awk portability verified empirically under mawk 1.3.4 with `awk` shimmed (`from-map`, `claim` identical to gawk).
- [INFO] no mawk-shimmed bats case — **DEFERRED** → TODOS.md (skip-if-absent case).
- [INFO] guard lacked a pointer to the `AA_MA_MILESTONE_ERE` portability rules — **FIXED** (header comment).

## Future-Proofing (future-proofing-auditor agent)

### Findings
- **[CRITICAL] broken-ref** `docs/spec/aa-ma-specification.md` map row cites `[10]`; References ended at `[9]` — **User decision: accept → FIXED**: `[10] Charting — … ADR-0013` added.
- **[WARNING] hook inventory** `SECURITY.md` "8 hooks" + foundations `### Hooks (8)` omit the 2 `hooks/lib/` helpers install.sh links — **FIXED**: explicit "2 library helpers (not event hooks)" line in both; count test still green (it reads the command/skill/agent lines only).
- **[WARNING] version pin** `v0.14.0` written in 4 doc sites before the release exists — **FIXED**: dropped (ADR-0011/0012 style: milestone + date); CHANGELOG `## Unreleased` remains the only pre-release site and release.sh owns the number.
- **[WARNING] local CLAUDE.md** "8 file types" + missing map row — **FIXED** (gitignored; local).
- **[WARNING] magic-number** `sed -n '2,10p'` usage — **FIXED** (heredoc).
- [INFO] hardcoded counts (13 / 5+4 / 9) currently correct; auditor stated no test asserts the command count — **disputed as stated**: `tests/commands/test_aa_ma_share_command.py::test_command_count_sites_match_disk` and `test_foundations_count_headings_match_disk` assert the command count against disk. The *template* count (9) has no test — **DEFERRED** → TODOS.md (extend to `docs/templates/*-template.*` vs the "N file types" sites).
- [INFO] `awk 'NF==5'` coupled to the TSV width — **FIXED**: `grep -c .` on the rows.
- [INFO] two timestamp formats in the guard — **FIXED**: documented on `ts()` (map stamps vs provenance grammar).
- [INFO] "≤5 in parallel" fan-out cap with no source of truth — **FIXED**: tied to AD-006 (the Phase 1.3 sub-agent cap).
- [INFO] `_cand` duplication — acknowledged (see code review).

## User Override Decisions

| # | Finding | Decision | Outcome |
|---|---------|----------|---------|
| 1 | security CRITICAL — `rm -rf` on unvalidated `<effort>` / any non-zero rc | accept | fixed 2bd406d, bats 21–22, 27–28 |
| 2 | future-proofing CRITICAL — dangling `[10]` citation | accept | fixed 2bd406d |
| — | 13 WARNINGs | fix all now (user choice) | fixed 2bd406d |

## Revision History

- 2026-09-21 — M5 review run (5 agents, parallel): 2 CRITICAL accepted; red pins e42d9e7 (8 bats cases, 2 fixtures) → fix set 2bd406d; 13/13 WARNING + 7/15 INFO fixed, 3 INFO deferred to TODOS.md, 5 acknowledged. Security re-check on 2bd406d: [pending — appended below when received].
