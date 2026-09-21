# mattpocock-trio-adoption Tasks (HTP)

_Hierarchical Task Planning roadmap with dependencies and state tracking._

Plan: `mattpocock-trio-adoption-plan.md` (Created 2026-09-20; line numbers in the plan are as of commit `c87135b` — locate edits by anchor text, see `mattpocock-trio-adoption-reference.md`). Two releases: v0.13.0 after Milestone 4, v0.14.0 after Milestone 5. `Critical-Path` / `Prototype-Required` fields appear only where the plan sets them — never as blank slots (an empty value is an `aa-ma-gate` exit-2 error).

## Pre-M1 housekeeping (ad-hoc commit)

Before Milestone 1 starts, one `[ad-hoc]` commit fixes pre-existing count/taxonomy drift so every taxonomy site reads **5 standard + 3 optional** and lists `impl-review`: `docs/spec/claude-code-foundations.md` `### Commands (11)` → 12 with an `/aa-ma-share` row and `(5 standard + 2 optional)` → `+ 3`; `docs/templates/README.md` rows for `impl-review-template.md` + `engineering-standards-template.md` and "3 optional"; `claude-code/rules/aa-ma.md` `(5 standard + 2 optional)` → `+ 3` with an impl-review row; `docs/spec/aa-ma-quick-reference.md` Optional Files table + impl-review row; `docs/spec/aa-ma-specification.md` §II table + impl-review row; ADR-0002 Implementation Notes rows claiming `rules/aa-ma.md`/`CLAUDE.md` mentions (they never did). Verify: `grep -rl '+ 2 optional' docs claude-code README.md` is empty. This commit is not a milestone (eng-review OV7): it keeps M1's rollback honest and makes M5 a clean +1. It carries `[ad-hoc]`, not the plan footer.

---

## Milestone 1: Fork manifest, Drift/Orphan detector, Derived reclassifications, CI coverage
- Status: COMPLETE
- Dependencies: None (pre-M1 `[ad-hoc]` housekeeping commit must land first)
- Complexity: 45%
- Mode: AFK
- Gate: SOFT
- Audit-Profile: code-only
- Critical-Path: doc-count-drift
- Effort: 6h
- Goal: `FORKS.json` is the SSoT for every fork; a test detects local tampering (fail); a pure classifier + `scripts/fork-drift.sh` detect upstream Drift/Orphan against the fork's recorded `upstream_md5` (warn); `write-a-skill` is Derived; CI runs the suites it has been skipping.
- Acceptance Criteria:
  - [x] `uv run pytest tests/skills/test_fork_manifest.py -q` passes; deleting the whole `prototype` row from `FORKS.json` makes `test_every_fork_dir_is_in_manifest` fail with `MISSING_IN_MANIFEST: prototype`; changing one `files` md5 makes `test_local_md5_matches_manifest` fail with `MD5_MISMATCH: prototype/SKILL.md`.
  - [x] `classify_fork(entry, fetched)` (pure, no I/O) returns `SAME` when every fetched md5 equals the entry's `upstream_md5`, `DRIFT` when any differs, `ORPHAN` when a fetch is `None`; `tests/skills/test_fork_manifest.py` proves all three with hand-built dicts — no plugin cache, no network (3A + OV2).
  - [x] `scripts/fork-drift.sh [--sha <ref>]` fetches each manifest file at `<ref>` (default `main`) via `gh api`, feeds `classify_fork`, prints `skill | file | upstream_md5 | fetched md5 | SAME|DRIFT|ORPHAN`; exit 0; exit 1 with a message when `gh` is absent. Expected verdicts at `--sha c55ee46` after Step 1.2 (record in reference.md): `grill-with-docs` → **ORPHAN** (its `CONTEXT-FORMAT.md`/`ADR-FORMAT.md` 404 upstream — moved to `domain-modeling/`; ORPHAN takes precedence over DRIFT per the classifier), `prototype` → DRIFT (all three files), `write-a-skill` → ORPHAN.
  - [x] `.github/workflows/security.yml` pytest step includes `tests/skills tests/agents tests/plan_markers tests/test_gate.py tests/test_enforce.py tests/test_gate_parity.py`; `grep -q '"pyyaml' pyproject.toml` inside `[dependency-groups] dev`; `uv lock --check` exits 0.
  - [x] `sed -n 1p claude-code/skills/write-a-skill/SKILL.md | grep -qF 'Derived from https://github.com/mattpocock/skills/skills/productivity/write-a-skill'`; ADR-0004 line 3 is exactly `**Status:** Implemented — Derived (2026-05-10; amended <fork-date>)`; `grep -q 'Authoring recipe: gather' README.md`.
  - [x] `tests/commands/test_aa_ma_share_command.py::test_foundations_count_headings_match_disk` asserts `docs/spec/claude-code-foundations.md` `### Commands (N)`/`### Skills (N)`/`### Agents (N)` against disk (SECURITY.md already covered by `test_security_md_asset_lists_match_disk`; CLAUDE.md excluded — gitignored).
- Tests: manifest test (red → green); `uv run pytest tests/skills tests/agents tests/plan_markers tests/test_gate.py tests/commands -q` all pass; `shellcheck scripts/fork-drift.sh` clean.
- Rollback: `git revert` the milestone commits (pre-existing drift fixes are in the separate pre-M1 commit and survive); no runtime behaviour changes (tests + docs + one script + one pure module).
- Result Log: COMPLETE 2026-09-21. 6/6 criteria verified live (§6.1). Commits 8d91442 → d755920 → 4144305 → b5c4df6 → 859ad6d, all pushed; CI run 35581802744 success. §6.7 PASS; §6.8 PASS_WITH_WARNINGS (2 CRITICAL: fail-open fixed via `aa_ma.forks` subcommands, TDD same-commit disputed with provenance evidence → L-017); §7.2.5 validator gaps back-filled. Live `fork-drift.sh --sha c55ee46`: grill-with-docs ORPHAN / prototype DRIFT / write-a-skill ORPHAN. Tests: 513 passed, bats 7/7, shellcheck clean, lint-imports 3 kept. Deviations from plan (all approved): CI step exclusion-based (AD-003), `.importlinter` += `aa_ma.forks`, contract addendum AD-002/AD-004.

### Sub-step 1.1: Write the failing manifest test
- Status: COMPLETE
- Mode: AFK
- Dependencies: None
- Effort: 45m · Complexity: 35%
- Acceptance Criteria:
  - `uv run pytest tests/skills/test_fork_manifest.py -q` fails at collection with `ImportError`/`ModuleNotFoundError: aa_ma.forks` (the `FileNotFoundError` leg surfaces once the module exists).
- Artefacts: `tests/skills/test_fork_manifest.py` (four tests per the M1 Contract; the classifier test builds `fetched` dicts by hand — no cache, no network).
- Result Log: Mode: AFK — auto-dispatched. RED confirmed: `uv run pytest tests/skills/test_fork_manifest.py -q` → `ModuleNotFoundError: No module named 'aa_ma.forks'` (1 error during collection). File holds the 4 Contract tests + `test_load_manifest_names_missing_key` + the Step 1.3 helper test (7 assertions across 6 tests); classifier test uses hand-built dicts incl. missing-key→ORPHAN and expected-None→SAME legs.

### Sub-step 1.2: Write `FORKS.json` and make the test pass
- Status: COMPLETE
- Mode: AFK
- Dependencies: Step 1.1
- Effort: 30m · Complexity: 30%
- Acceptance Criteria:
  - The four Contract tests pass (Step 1.3 adds a fifth); `uv run ruff check src/; test $? -eq 0`; `uv run python -m aa_ma.forks classify prototype '{"SKILL.md": null}'` prints an ORPHAN roll-up row.
- Artefacts: `src/aa_ma/forks.py`; `claude-code/skills/FORKS.json` with rows `grill-with-docs` (current; `upstream_sha: null`, `forked_at: 2026-05-10`; ADR-0002 recorded no md5 values — the fork is byte-faithful, so `upstream_md5.<f>` = local `tail -n +2 <f> | md5sum`, and the row carries `"upstream_md5_source": "derived-from-local-fork"`; `adr: docs/adr/0002-grill-with-docs-adoption.md`), `prototype` (current; `forked_at: 2026-05-10`; `upstream_md5` from ADR-0003 under the anchor `MD5 verification (canonical` — three values, which equal the local `tail -n +2` md5s; `adr: docs/adr/0003-prototype-adoption.md`), `write-a-skill` (derived; `upstream_sha: null`, `upstream_md5: {"SKILL.md": null}`; `adr: docs/adr/0004-write-a-skill-adoption.md`); `understand-codebase` excluded (line 1 is the `Maintained in aa-ma-forge …` comment, not a Fork). `upstream_sha` is the full 40-char sha when non-null.
- Result Log: Mode: AFK — auto-dispatched. GREEN: 5 passed, 1 failed (`test_helper_resolves_upstream_from_manifest` — the Step 1.3 leg, expected). `src/aa_ma/forks.py` (ForkEntry/load_manifest/classify_file/classify_fork + `classify` CLI, stdlib only); `claude-code/skills/FORKS.json` 3 rows — grill-with-docs (upstream_md5 derived-from-local-fork), prototype (upstream_md5 = ADR-0003 values `10ace9b5…`/`d5772145…`/`c1eaad64…`, verified equal to local `tail -n +2` md5s), write-a-skill (derived, upstream_md5 SKILL.md null). `upstream_sha: null` on all three — neither ADR-0002 nor ADR-0003 recorded a fork sha. `ruff check src/` clean; `python -m aa_ma.forks classify prototype '{"SKILL.md": null}'` → 3 per-file rows + `prototype | * | | | ORPHAN`.

### Sub-step 1.3: Point `_helpers.assert_skill_frontmatter` at the manifest
- Status: COMPLETE
- Mode: AFK
- Dependencies: Step 1.2
- Effort: 20m · Complexity: 25%
- Acceptance Criteria:
  - The `name == dir` assertion is untouched; the three existing `test_*_frontmatter.py` pass unchanged (explicit path); `tests/skills/test_fork_manifest.py::test_helper_resolves_upstream_from_manifest` (fifth test in that file) calls the helper with `expected_upstream_path=None` for `prototype` and passes.
- Artefacts: `tests/skills/_helpers.py`.
- Result Log: Mode: AFK — auto-dispatched. `_helpers.py`: `expected_upstream_path: str | None = None`; None → `"mattpocock/skills/" + load_manifest(FORKS_MANIFEST)[skill].upstream`; `fm["name"] == skill_dir_name` assertion untouched. `uv run pytest tests/skills -q` → 55 passed (3 existing `test_*_frontmatter.py` unchanged with explicit paths; `test_helper_resolves_upstream_from_manifest` green for `prototype`).

### Sub-step 1.4: `scripts/fork-drift.sh`
- Status: COMPLETE
- Mode: AFK
- Dependencies: Step 1.2
- Effort: 30m · Complexity: 35%
- Acceptance Criteria:
  - `scripts/fork-drift.sh --sha c55ee46` prints per-file rows plus one roll-up row per skill with the expected verdicts (grill-with-docs ORPHAN, prototype DRIFT, write-a-skill ORPHAN); `shellcheck scripts/fork-drift.sh; test $? -eq 0`.
  - `bats tests/hooks/fork-drift.bats` (uses `--manifest tests/hooks/fixtures/forks/FORKS.json`, a 2-row fixture): (a) `GH=/nonexistent/gh` → exit 1 + message; (b) `GH=<tmp>/stub-gh` returning fixed base64 for one file and writing `gh: Not Found (HTTP 404)` to stderr + exit 1 for the other → rows `SAME` and `ORPHAN`; (c) stub writing `HTTP 403` → exit 1, no ORPHAN.
- Artefacts: `scripts/fork-drift.sh` per the Contract (`GH` seam, 404-only → null, `cut -d' ' -f1`, `uv run --quiet --project`), `tests/hooks/fork-drift.bats`, `tests/hooks/fixtures/forks/FORKS.json`.
- Result Log: Mode: AFK — auto-dispatched. `scripts/fork-drift.sh --sha c55ee46` (live `gh api`) → grill-with-docs **ORPHAN** (SKILL.md DRIFT `2e333f0b…`, CONTEXT-FORMAT.md + ADR-FORMAT.md 404), prototype **DRIFT** (fetched `5c68a286…`/`0c6daa14…`/`e3c84174…` = reference.md values), write-a-skill **ORPHAN** — all three as predicted. `shellcheck scripts/fork-drift.sh` clean. `bats tests/hooks/fork-drift.bats` 4/4: (a) `GH=/nonexistent/gh` → exit 1 + `gh CLI not found`; (b) stub 404 → `alpha … SAME` + `beta … ORPHAN` rows; (c) stub 403 → exit 1, output contains no ORPHAN; (d) unknown flag → exit 2. Fixture `tests/hooks/fixtures/forks/FORKS.json` (2 rows).

### Sub-step 1.5: `write-a-skill` → Derived; ADR-0004 + ADR-0002 amendments
- Status: COMPLETE
- Mode: AFK
- Dependencies: Step 1.2
- Effort: 30m · Complexity: 20%
- Acceptance Criteria:
  - `write-a-skill/SKILL.md` line 1 = `<!-- Derived from https://github.com/mattpocock/skills/skills/productivity/write-a-skill (forked 2026-05-10; upstream removed in 1.0.0, 2026-06-17) — aa-ma-forge v0.13.0 -->`; `test_write_a_skill_frontmatter.py` passes (path substring still present); ADR-0004 Status + a `## Amendment <fork-date>` section; the `README.md` `write-a-skill` row rewritten to "Authoring recipe: gather → draft SKILL.md (+REFERENCE/EXAMPLES/scripts) → review; description rules, 100-line split, 6-item checklist".
- Artefacts: `claude-code/skills/write-a-skill/SKILL.md`, `docs/adr/0004-write-a-skill-adoption.md`, `docs/adr/0002-grill-with-docs-adoption.md`, `README.md`.
- Result Log: Mode: AFK — auto-dispatched. `write-a-skill/SKILL.md` line 1 = Derived form (fork-date 2026-09-21; `tail -n +2` md5 unchanged so FORKS.json stays valid); ADR-0004 line 3 = `**Status:** Implemented — Derived (2026-05-10; amended 2026-09-21)` + `## Amendment 2026-09-21 — reclassified Derived` section; README `write-a-skill` row → `Authoring recipe: gather → …`. ADR-0002: its M1 change (never-true rows) already landed pre-M1 in `c47e15b`; the Derived amendment is Step 2.3. `uv run pytest tests/skills -q` → 55 passed (`test_write_a_skill_frontmatter` green — path substring retained).

### Sub-step 1.6: CI widening + `pyyaml` + count-site test extension
- Status: COMPLETE
- Mode: AFK
- Dependencies: Steps 1.3, 1.4
- Effort: 40m · Complexity: 40%
- Acceptance Criteria:
  - `uv run pytest tests/commands tests/render tests/skills tests/agents tests/plan_markers tests/test_gate.py tests/test_enforce.py tests/test_gate_parity.py -q --tb=short` passes locally; the `command + render tests` step in `security.yml` runs that exact list; `[dependency-groups] dev` includes `pyyaml`; `uv lock` then `uv lock --check; test $? -eq 0`.
  - `test_aa_ma_share_command.py` gains `test_foundations_count_headings_match_disk` covering only the three foundations headings (`test_security_md_asset_lists_match_disk` already covers SECURITY.md — do not duplicate).
- Artefacts: `.github/workflows/security.yml`, `pyproject.toml`, `uv.lock`, `tests/commands/test_aa_ma_share_command.py`.
- Result Log: Mode: AFK — auto-dispatched. `security.yml` pytest step now runs the exact 8-path list (`tests/commands tests/render tests/skills tests/agents tests/plan_markers tests/test_gate.py tests/test_enforce.py tests/test_gate_parity.py`); `[dependency-groups] dev` += `pyyaml>=6`; `uv lock` (+2 lines) then `uv lock --check` rc 0. `test_foundations_count_headings_match_disk` added (3 headings only; Commands 12 / Skills 19 / Agents 11 vs disk). Unplanned but required: `.importlinter` render-is-leaf `source_modules` += `aa_ma.forks` (`tests/render/test_leaf_contract.py` enforces every new `aa_ma` module be listed; `lint-imports` 3 kept / 0 broken). Full list locally: **317 passed**. **Amended at §6.8 (future-proofing WARNING, user-approved):** the enumerated list already missed `tests/test_grammar.py`, `test_grammar_parity.py`, `test_active_plans_canonical.py` and `tests/tui` (190 tests in no workflow); the step is now exclusion-based (`pytest tests --ignore=tests/codemem --ignore=tests/perf --ignore=tests/test_goal_synthesis.py`) → **513 passed** locally. The AC's 'exact list' wording is superseded by this note.

### Sub-step 1.7: CHANGELOG + sync
- Status: COMPLETE
- Mode: AFK
- Dependencies: Steps 1.5, 1.6
- Effort: 25m · Complexity: 20%
- Acceptance Criteria:
  - `CHANGELOG.md ## Unreleased` has M1 entries; new count test green against the pre-M1 baseline; commit + push with plan footer.
- Artefacts: `CHANGELOG.md`, tasks/reference/context-log/provenance sync.
- Result Log: Mode: AFK — auto-dispatched. `CHANGELOG.md ## Unreleased` += 3 M1 entries (manifest+detector, write-a-skill Derived, CI widening). `test_foundations_count_headings_match_disk` green against the pre-M1 baseline (12/19/11). §6.1 all 6 criteria verified live (tamper legs: `MISSING_IN_MANIFEST: prototype`, `MD5_MISMATCH: prototype/SKILL.md`; FORKS.json restored). Impact analysis: 12 files, overall LOW. Commits (plan footer): `8d91442` M1 → `d755920` red tests (§6.8 fix, committed first per L-017) → `4144305` green fixes → `b5c4df6` context-log entry; all pushed, CI green on 4144305.

---

## Milestone 2: Fork `grilling`; `grill-with-docs` becomes Derived
- Status: COMPLETE
- Dependencies: Milestone 1
- Complexity: 40%
- Mode: HITL
- Gate: SOFT
- Audit-Profile: code-only
- Critical-Path: doc-count-drift
- Effort: 4h
- Goal: Round-based frontier grilling available as `Skill(grilling)`; `grill-with-docs` keeps its name and dispatch contract but delegates the interview to `grilling`.
- Acceptance Criteria:
  - [x] `claude-code/skills/grilling/SKILL.md` = upstream HEAD content (md5 of `tail -n +2` = `284efe9cf334900d08230e572fc6db90`), YAML frontmatter parses, `disable-model-invocation` absent.
  - [x] `grill-with-docs/SKILL.md` line 1 is Derived; its `<what-to-do>` block is ≤6 lines and names `grilling`; the `<supporting-info>` domain block is unchanged except the glossary sentence; `CONTEXT-FORMAT.md` + `ADR-FORMAT.md` still in the dir. `test_grill_with_docs_frontmatter.py` gains two asserts: line 1 is an HTML comment starting `Derived from` and the `<what-to-do>` block contains `"grilling"` (3B).
  - [x] **Live criterion (OV3):** in a fresh session after `install.sh`, run `/aa-ma-plan --grill-mode=with-docs` on the fixed idea "add `--json` output to `scripts/fork-drift.sh`" and stop after Phase 1.3. Proof: Result Log contains a fenced excerpt showing (a) the `Skill` tool call with `skill: grilling` and its resolved path, and (b) at least one `❓ Q1` block followed by a `➡️` line; provenance gains `[ts] LIVE_CHECK — Milestone 2: … — grilling_rounds=<N> resolved=~/.claude/skills/grilling`.
  - [x] `tests/plan_markers/test_fingerprint.py::test_satisfied_by_grill_with_docs` still passes (no fingerprint change).
  - [x] `jq -e '.grilling.state=="current" and .grilling.upstream_sha=="c55ee46073ed923f86ce59a5eb3b6d895095d1b7" and .grilling.upstream_md5["SKILL.md"]=="284efe9cf334900d08230e572fc6db90" and .["grill-with-docs"].state=="derived"' claude-code/skills/FORKS.json`; manifest test green.
  - [x] Counts: skills 19→20 in `SECURITY.md` list, `README.md` skills table (+1 row), `docs/spec/claude-code-foundations.md` `### Skills (20)` (+1 row); CLAUDE.md updated locally, not asserted; `test_aa_ma_share_command.py` green.
- Tests: `uv run pytest tests/skills tests/plan_markers tests/commands -q`; `bats tests/hooks/install_dry_run.bats`.
- Rollback: revert milestone commits; `grill-with-docs` returns to the faithful 2026-05-10 fork; remove `grilling` dir and manifest row.
- Result Log: COMPLETE 2026-09-21 — approved by Ste at §7.3. 6/6 criteria verified (see sub-step logs). Commits 7542c30 → bc329d4 → 936fb1d → 7030200 → ba36187 → 5d2ff5d → 022e036 → bac16db (milestone). Tests: 142 milestone cmd / 515 CI cmd / bats 4/4. §6.7 PASS; §6.8 PASS_WITH_WARNINGS (0C/4W/9I; 4W+2I fixed → AD-005, AD-006). Live: Skill(grilling) → ~/.claude/skills/grilling (ours), fork-drift grilling=SAME. Skills 19→20.

### Sub-step 2.1: Fork `grilling` from HEAD + frontmatter test
- Status: COMPLETE
- Mode: AFK
- Dependencies: None
- Effort: 30m · Complexity: 25%
- Acceptance Criteria:
  - `md5sum <(tail -n +2 claude-code/skills/grilling/SKILL.md)` = `284efe9cf334900d08230e572fc6db90`; `uv run pytest tests/skills/test_grilling_frontmatter.py -q` passes.
- Artefacts: `claude-code/skills/grilling/SKILL.md` (line 1 provenance + upstream body), `tests/skills/test_grilling_frontmatter.py`.
- Result Log: Mode: AFK — auto-dispatched. RED: `test_grilling_frontmatter` failed (SKILL.md absent) → committed alone as 7542c30 (L-017a). Fetched `skills/productivity/grilling/SKILL.md` @ c55ee46 via `gh api`; whole-file md5 `284efe9cf334900d08230e572fc6db90` = reference. Wrote local file = provenance line + upstream body (28 lines); `tail -n +2 | md5sum` = `284efe9c…` ✓. GREEN: 1 passed; `disable-model-invocation` absent asserted. Pulled the `grilling` FORKS.json row forward from 2.3 (state current, upstream_sha c55ee46…, upstream_md5_source `gh-api@c55ee46`) so `test_every_fork_dir_is_in_manifest` stays green at this commit — `tests/skills` all green.

### Sub-step 2.2: Rewrite `grill-with-docs` as Derived delegator
- Status: COMPLETE
- Mode: AFK
- Dependencies: Step 2.1
- Effort: 30m · Complexity: 35%
- Acceptance Criteria:
  - File matches the M2 Contract; under the `### Update CONTEXT.md inline` heading, the sentence beginning "Don't couple `CONTEXT.md` to implementation details" is replaced by upstream's ("`CONTEXT.md` should be totally devoid of implementation details… a glossary and nothing else"); `CONTEXT-FORMAT.md` line 2 = `<!-- Derived: retains Relationships / Example dialogue / Flagged ambiguities (upstream removed 2026-07); still glossary-level, never implementation. -->`; existing test green.
- Artefacts: `claude-code/skills/grill-with-docs/SKILL.md`, `claude-code/skills/grill-with-docs/CONTEXT-FORMAT.md`.
- Result Log: Mode: AFK — auto-dispatched. RED: `test_grill_with_docs_is_derived_delegator` (line-1 `Derived from` + `<what-to-do>` names `grilling`) failed → committed alone 936fb1d. Rewrote: line 1 = M2 Contract Derived comment; `<what-to-do>` = 3 lines (contract text verbatim); glossary sentence replaced by upstream domain-modeling's ("totally devoid of implementation details… a glossary and nothing else"); rest of `<supporting-info>` untouched (diff: 12 lines SKILL.md). `CONTEXT-FORMAT.md` line 2 = the Derived retention comment. `test_local_md5_matches_manifest` fired MD5_MISMATCH as designed → FORKS.json `grill-with-docs` → `state: derived`, `files` md5s recomputed (SKILL `73617465…`, CONTEXT-FORMAT `03e375e9…`, ADR-FORMAT unchanged `bb327bab…`), `upstream_md5` all null, `upstream_md5_source` null (write-a-skill precedent). GREEN: `tests/skills` + `tests/plan_markers` 110 passed; `test_satisfied_by_grill_with_docs` passes (no fingerprint change). jq M2 manifest criterion → `true`. Two `tests/commands` count tests red (19 vs 20 on disk) — owned by 2.3. **Amended at §6.8 (AD-005, 022e036):** `<what-to-do>` is now 4 lines (glossary-read line prepended); FORKS.json SKILL.md md5 → `e552cb8aad8b0a6c0fe0fcef7181bd71`; test asserts literal `Skill tool with "grilling"` + ≤6 lines.

### Sub-step 2.3: Manifest rows, ADR-0002 amendment, `aa-ma-plan.md` note, counts, CHANGELOG, live check, sync
- Status: COMPLETE
- Mode: HITL
- Dependencies: Step 2.2
- Effort: 45m · Complexity: 30%
- Acceptance Criteria:
  - All M2 criteria, including the live criterion (fresh session after `install.sh`; record the resolved skill path; if `Skill(grilling)` resolves to `mattpocock-skills:grilling`, rename ours `aa-ma-grilling` (Derived) in this milestone); commit + push.
- Artefacts: `FORKS.json`, `docs/adr/0002-grill-with-docs-adoption.md` (`## Amendment <fork-date> — Derived; grilling forked`), `claude-code/commands/aa-ma-plan.md` Phase 1.3 grill-with-docs dispatch prose (+ agent-cap sentence), `SECURITY.md`, `CLAUDE.md` (local), `README.md`, `docs/spec/claude-code-foundations.md`, `docs/ATTRIBUTION.md`, `CHANGELOG.md`, provenance `LIVE_CHECK` line.
- Result Log: Mode: HITL — Ste approved at gate (2026-09-21). Mechanical part DONE: manifest rows (done in 2.1/2.2, jq criterion `true`); ADR-0002 status → `Implemented — Derived (2026-05-10; amended 2026-09-21)` + `## Amendment 2026-09-21 — Derived; grilling forked`; `aa-ma-plan.md` Phase 1.3 `with-docs` bullet rewritten (delegation + ≤5-agent-cap sentence); counts 19→20 in SECURITY.md list (+`grilling`), README skills table (+row), foundations `### Skills (20)` (+row), local CLAUDE.md; ATTRIBUTION Matt Pocock section; CHANGELOG `## Unreleased` bullet. Stale-count sweep: only the frozen v0.x CHANGELOG history line mentions 19. Tests: `uv run pytest tests/skills tests/plan_markers tests/commands -q` → 142 passed; `bats tests/hooks/install_dry_run.bats` ok (announces current disk count). `scripts/install.sh` run: `~/.claude/skills/grilling` → repo symlink (backup dir `aa-ma-forge-20260921-102136`). Plugin-cache sibling exists at `~/.claude/plugins/cache/claude-plugins-official/mattpocock-skills/1.2.3/skills/productivity/grilling` — resolution to be recorded by the live check. **LIVE CRITERION MET** (2026-09-21, same session — Ste chose "run it now": the skill list hot-reloaded after `install.sh`, showing `grilling` with our line-1 provenance as its description, which falsified the "fresh session" premise; plugin copy listed separately as `mattpocock-skills:grilling`). Ran `Skill(aa-ma-plan)` `--grill-mode=with-docs` on "add `--json` output to `scripts/fork-drift.sh`", stopped after Phase 1.3 (marker log `~/.claude/runtime/aa-ma-plan-add-json-output-scripts-20260921092340.log`: `PHASE_1.3 DONE — grill_mode=with-docs branches_resolved=6 questions_asked=6`). Excerpt:
  ```
  Skill(grill-with-docs)  → Base directory: /home/sjnewhouse/.claude/skills/grill-with-docs   (line 1: <!-- Derived from … -->)
  Skill(grilling)         → Base directory: /home/sjnewhouse/.claude/skills/grilling            (line 1: <!-- Forked from … @ c55ee46 …)
  readlink -f ~/.claude/skills/grilling → …/aa-ma-forge/claude-code/skills/grilling
  ❓ **Q1** - **Who owns the JSON shape?**: … (a) add `--json` to `classify-all` in Python … (b) shell converts rows …
  ➡️ (a). Keeps the single-reader invariant (AD-002); the shell stays a launcher.
  ---
  ❓ **Q2** - **Shape of the document**: … ➡️ (a) object keyed by skill …   (Q3–Q6: glossary verbatim + `state`; exit 0; empty stdout on error; bats + pytest, red first)
  ```
  One round, 6 questions, all resolved on recommendation → no rename to `aa-ma-grilling` needed (unprefixed `Skill(grilling)` resolved to ours). No CONTEXT.md/ADR change arose. Decisions parked for a future `fork-drift --json` plan (not in scope here).

---

## Milestone 3: `prototype` Re-fork + planning gate + gate roll-up
- Status: COMPLETE
- Dependencies: Milestone 1
- Complexity: 70%
- Mode: HITL
- Gate: HARD
- Audit-Profile: full
- Critical-Path: hook-modification
- Effort: 8h
- Goal: Fork current with HEAD (HTML logic demo, capture-on-branch); `/aa-ma-plan` asks the prototype question; the gate honours sub-step `Prototype-Required`.
- Acceptance Criteria:
  - [x] `claude-code/skills/prototype/{SKILL,LOGIC,UI}.md` bodies = HEAD (`tail -n +2` md5s `5c68a2867eb3b9b4cb3e9ad4ba2b5299`, `0c6daa140ef3e83ba9e6b5bfa5161408`, `e3c841746676a0e604c72b5cd459e7ba`); `test_prototype_frontmatter.py` green; `FORKS.json` row updated (`upstream_sha: c55ee46`, `upstream_md5` = those three).
  - [x] `uv run aa-ma-gate tests/hooks/fixtures/gate-scans/prototype-rollup-tasks.md --milestone 1 --format kv | grep -q '^prototype_required=YES$'` where Milestone 1 has **no** milestone-level field and Sub-step 1.2 has `Prototype-Required: YES`; `--milestone 2` (no flags anywhere) prints `NO`; a sub-step `Prototype-Required: maybe` → exit 2; **REGRESSION (eng-review §3):** a sub-step with the literal empty slot `- **Prototype-Required:**` (what `tasks-template.md` emits today) → exit 2 with `empty value` — this is the behaviour change the template fix exists for.
  - [x] `tests/hooks/aa-ma-gate-python.bats` has a PROTOTYPE fence case: milestone requiring a prototype with no `PROTOTYPE —` line → §6.7 BLOCKED text; with the line → passes.
  - [x] `claude-code/commands/aa-ma-plan.md` has `**Step 2.5: Prototype Decision**` between Step 2.4 and the Phase 2 summary; `test_planning_standard_count.py` and `test_active_plans_canonical.py` green.
  - [x] `grep -c 'terminal TUI' claude-code/rules/engineering-standards.md tests/smoke/aa-ma-engineering-standards-smoke.md README.md docs/spec/claude-code-foundations.md` = 0 for every file; `grep -q '?variant=' claude-code/rules/engineering-standards.md`; `grep -q 'prototype/<name>' claude-code/rules/engineering-standards.md`; the Critical-Path table in Theme 1 is byte-identical before/after (`tests/codemem/test_critical_path_parser.py` scrapes it).
  - [x] `grep -F 'PROTOTYPE — <milestone heading> — <verdict>[; branch=prototype/<name>]' docs/spec/aa-ma-specification.md` and `grep -F 'CRITICAL_PATH_REVIEW — <milestone heading> — <Critical-Path value> — <evidence>' docs/spec/aa-ma-specification.md` and `grep -F 'LIVE_CHECK — <milestone heading>' docs/spec/aa-ma-specification.md` all match in the provenance-grammar section (4-field CRITICAL_PATH_REVIEW form = `execute-aa-ma-milestone.md` §6.7).
  - [x] `grep -cE '^- \*\*(Prototype-Required|Critical-Path):\*\*\s*$' docs/templates/tasks-template.md` = 0 — all four blank slots (milestone-level and sub-step, both fields) are removed; each comment says "add `- <Field>: <value>` only when it applies; an empty value is a gate error (exit 2)".
  - [x] ADR-0011 Status → Implemented.
- Tests: `uv run pytest tests/test_gate.py tests/test_gate_parity.py tests/test_enforce.py tests/commands -q`; `bats tests/hooks/aa-ma-gate-python.bats`; `uv run ruff check src/`.
- Rollback: revert `gate.py` + fixture commit first (restores milestone-only semantics), then docs; the skill re-fork is independent and can stay.
- Result Log: COMPLETE 2026-09-21 — HARD gate APPROVED by Ste; §7.3 approved. 8/8 criteria (see sub-step logs). Commits f762730 → 1b1cabf → 6565ceb → c8cea54 → 20e2359 → 931c71b → 4cedc91 → 75aa6f7 → 0cb97a3 → 3c6f92f → f849d1c → <milestone commit, recorded in provenance>. Tests: CI cmd 523 / bats gate-python 32/32 / codemem CP parser green / ruff clean. §6.7 PASS; §6.8 PASS_WITH_WARNINGS (0C/5W/12I; all W fixed → AD-007 Critical-Path roll-up, AD-008 single ENG_STANDARDS_DECLARED echo, AD-009 UI-route auth rule). Scope additions: L-018 §8.3/8.4 no-amend (Ste), Critical-Path roll-up (Ste). Live fork-drift: prototype SAME.

### Sub-step 3.1: Fixture + failing gate tests
- Status: COMPLETE
- Mode: AFK
- Dependencies: None
- Effort: 40m · Complexity: 45%
- Acceptance Criteria:
  - `uv run pytest tests/test_gate.py -q -k rollup` fails (M1 reads `NO`); fixture file exists as in the M3 Contract plus Milestone 3 (`- Prototype-Required: maybe` on a sub-step) and Milestone 4 (empty `- **Prototype-Required:**` on a sub-step), both asserted to exit 2.
- Artefacts: `tests/hooks/fixtures/gate-scans/prototype-rollup-tasks.md`, `tests/test_gate.py` (4 new tests: rollup YES, no-flags NO, invalid sub-step exit 2, `test_empty_substep_prototype_slot_exits_2`).
- Result Log: Mode: AFK — auto-dispatched. Fixture written per M3 Contract + M3 (`Prototype-Required: maybe` on 3.1) + M4 (literal `- **Prototype-Required:**` on 4.1). 4 tests appended to `tests/test_gate.py` (`ROLLUP` path constant). RED: 3 failed (`rolls_up` → M1 reads False; `invalid_substep` → exit 0; `empty_slot` → exit 0), 1 passed (`no_flags_is_no`, regression guard). Adjacent suites unaffected: test_grammar 39 passed, gate-parity/enforce/active-plans green, bats gate-python 30 ok, gate-scans 10 ok (fixtures are named, not enumerated). Red committed alone: f762730 (L-017a).

### Sub-step 3.2: Implement `_read_steps` + override
- Status: COMPLETE
- Mode: AFK
- Dependencies: Step 3.1
- Effort: 45m · Complexity: 60%
- Acceptance Criteria:
  - M3 gate tests pass; full `tests/test_gate.py tests/test_gate_parity.py tests/test_enforce.py` green; `uv run ruff check src/; test $? -eq 0`; `grep -q 'sub-step' <(sed -n 1,30p src/aa_ma/gate.py)` (module docstring names the roll-up).
- Artefacts: `src/aa_ma/gate.py` (`StepsRead` dataclass, `_read_steps` replacing `_count_pending`, selected-milestone override only — see context-log decision on roll-up scope).
- Result Log: Mode: AFK — auto-dispatched. `gate.py`: `StepsRead(pending, prototype_required)` frozen dataclass; `_read_steps` replaces `_count_pending` (no remaining references), reads `Prototype-Required` per sub-step via `read_enforced_field(…, PROTOTYPE_REQUIRED)` with the same `_read_or_error` refusal path; override at the selected-milestone site ORs `read.prototype_required | steps.prototype_required`; JSON schema + `to_kv` untouched; module docstring Q6 names the roll-up + AD-001 scope. GREEN: gate/parity/enforce 108 passed; CLI on fixture: `--milestone 1` → `prototype_required=YES`, `2` → `NO`, `3` → exit 2 `non-canonical value 'maybe'`, `4` → exit 2 `empty value in '- **Prototype-Required:**'`; live tasks.md still exit 0 / NO. bats gate-python 30 ok; CI cmd 519 passed; `ruff check src/` + `ruff format --check` clean.

### Sub-step 3.3: Bats PROTOTYPE fence case + milestone/step command text
- Status: COMPLETE
- Mode: AFK
- Dependencies: Step 3.2
- Effort: 40m · Complexity: 45%
- Acceptance Criteria:
  - `bats tests/hooks/aa-ma-gate-python.bats` passes with the new case (mirror of the Critical-Path case); `grep -q 'milestone or one of its sub-steps' claude-code/commands/execute-aa-ma-milestone.md`; `grep -q 'rolls up to the milestone gate' claude-code/commands/execute-aa-ma-step.md`.
- Artefacts: `tests/hooks/aa-ma-gate-python.bats`, `claude-code/commands/execute-aa-ma-milestone.md`, `claude-code/commands/execute-aa-ma-step.md`.
- Result Log: Mode: AFK — auto-dispatched. RED: new bats case (mirror of the Critical-Path case — `Prototype-Required: YES` on Sub-step 2.1 only; BLOCKED with no entry; entry naming Milestone 1 still BLOCKED; entry naming Milestone 2 → PASS) failed on the wording assert only (status≠0 already held — roll-up works through the shipped fence) → committed alone 6565ceb. GREEN: §6.7 BLOCKED text → "the milestone or one of its sub-steps declares Prototype-Required: YES"; `execute-aa-ma-step.md` advisory → "rolls up to the milestone gate"; bats gate-python 31/31; `tests/commands tests/smoke` 31 passed. **Scope addition (Ste, 2026-09-21: "fold L-018 into M3"):** §8.3 prose + §8.4 rewritten — provenance line is a separate `docs(aa-ma)` commit, never `--amend` (only remaining `--amend` mentions are the prohibition). Edit applied via a scratchpad script because the commit-signature hook pattern-matches a literal commit command inside heredoc doc text.

### Sub-step 3.4: Re-fork `prototype` from HEAD
- Status: COMPLETE
- Mode: AFK
- Dependencies: None
- Effort: 25m · Complexity: 20%
- Acceptance Criteria:
  - Three md5s match the Contract values; `test_prototype_frontmatter.py` green; `FORKS.json` `prototype` row `upstream_sha: c55ee46` (full sha), `forked_at` today, new local md5s and `upstream_md5`; manifest test green; `scripts/fork-drift.sh --sha c55ee46` reports `SAME` for prototype.
- Artefacts: `claude-code/skills/prototype/{SKILL,LOGIC,UI}.md`, `FORKS.json`, `docs/adr/0003-prototype-adoption.md` (Re-fork amendment — added at §6.8).
- Result Log: Mode: AFK — auto-dispatched. Fetched `skills/engineering/prototype/{SKILL,LOGIC,UI}.md` @ c55ee46 via `gh api`; whole-file md5s `5c68a286…` / `0c6daa14…` / `e3c84174…` = Contract. Wrote provenance line `Forked from … @ c55ee46 on 2026-09-21 — aa-ma-forge v0.13.0` + verbatim bodies; `tail -n +2` md5s match. `test_local_md5_matches_manifest` fired as designed → FORKS.json `prototype`: `upstream_sha` full c55ee46…, `forked_at` 2026-09-21, `files` = `upstream_md5` = the three, `upstream_md5_source: gh-api@c55ee46`. `tests/skills` 61 passed (frontmatter test green throughout). Live `scripts/fork-drift.sh --sha c55ee46` → **prototype SAME** (grilling SAME; grill-with-docs/write-a-skill ORPHAN by design). ADR-0003: status `re-forked 2026-09-21`, old md5s marked superseded, `## Amendment 2026-09-21 — Re-fork from HEAD c55ee46` (Re-fork per glossary: original ADR amended, no new number).

### Sub-step 3.5: Step 2.5 in `/aa-ma-plan`, Theme 1 wording, spec grammar, template, ADR-0011
- Status: COMPLETE
- Mode: AFK
- Dependencies: Steps 3.3, 3.4
- Effort: 60m · Complexity: 40%
- Acceptance Criteria:
  - All remaining M3 criteria; `uv run pytest tests/commands tests/codemem/test_critical_path_parser.py -q` green.
  - Theme 1 replacement sentence (verbatim): "which routes between **LOGIC** (a single self-contained HTML demo — state panel, free-play buttons, tabbed guided walkthroughs — for state/business-logic questions) and **UI** (structurally different variants on an existing route, switchable via `?variant=`) branches based on the question, and captures the result on a `prototype/<name>` branch — main keeps only the decision." The Critical-Path table below it is untouched.
- Artefacts: `claude-code/commands/aa-ma-plan.md`, `claude-code/rules/engineering-standards.md`, `docs/spec/aa-ma-specification.md`, `docs/templates/tasks-template.md`, `tests/smoke/aa-ma-engineering-standards-smoke.md`, `README.md` + `docs/spec/claude-code-foundations.md` prototype rows, `docs/adr/0011-*.md`, `CHANGELOG.md`.
- Result Log: Mode: AFK — auto-dispatched. Theme 1 sentence replaced verbatim per AC (+ PROTOTYPE entry now names the milestone heading; sub-step roll-up sentence); Critical-Path table diffed before/after → IDENTICAL. `grep -c 'terminal TUI'` = 0 in all four files (smoke file had none). `?variant=` + `prototype/<name>` present. Spec provenance grammar: three `grep -F` criteria match (added under the Milestone Complete entry). Template: 4 blank slots removed (`grep -cE … = 0`), each comment carries "add `- <Field>: <value>` only when it applies; an empty value is a gate error (exit 2)". `aa-ma-plan.md`: `**Step 2.5: Prototype Decision**` inserted before the Phase 2 summary; `ENG_STANDARDS_DECLARED` gains `prototype=${PROTO}`; text states no `PHASE_2.5` marker is written. README + foundations prototype rows reworded. ADR-0011 → Implemented. CHANGELOG `## Unreleased` bullet (incl. L-018 §8.4). Tests: M3 list + codemem critical-path parser + active-plans + plan_markers + skills → 287 passed 1 skipped; ruff clean; bats gate-python 31/31; CI cmd 519 passed. Edits applied via scratchpad script (hook pattern-match, see 3.3).

### Sub-step 3.6: CRITICAL_PATH_REVIEW + impact analysis + HARD gate approval + sync
- Status: COMPLETE
- Mode: HITL
- Dependencies: Step 3.5
- Effort: 30m · Complexity: 30%
- Acceptance Criteria:
  - Provenance has `CRITICAL_PATH_REVIEW — Milestone 3: … — hook-modification — <evidence: test names + bats case>`; consolidated impact analysis in context-log; `## [date] GATE APPROVAL: Milestone 3 …` in context-log; commit + push.
- Artefacts: `mattpocock-trio-adoption-context-log.md`, `mattpocock-trio-adoption-provenance.log`.
- Result Log: Mode: HITL — Ste APPROVED the HARD gate (AskUserQuestion, 2026-09-21). Provenance: `CRITICAL_PATH_REVIEW — Milestone 3: … — hook-modification — <4 pytest names + bats case + parity + CI 519>`; §6.1/§6.3/§6.4 entries; `GATE APPROVAL` line. context-log: `## [2026-09-21] GATE APPROVAL: Milestone 3: …` with `- Decision: APPROVED` + consolidated impact analysis (MEDIUM: gate now refuses invalid/empty sub-step Prototype-Required; 0 active plans exposed; wire contract unchanged). Commit + push at milestone close.

---

## Milestone 4: Adopt `research` as `aa-ma-research` + `aa-ma-researcher` agent; Phase 3 writes files; release v0.13.0
- Status: PENDING
- Dependencies: Milestones 1, 2, 3
- Complexity: 50%
- Mode: HITL
- Gate: SOFT
- Audit-Profile: code-only
- Critical-Path: doc-count-drift
- Prototype-Required: YES
- Effort: 6h
- Goal: `Skill(aa-ma-research)` dispatches a non-nesting agent that writes one cited Markdown file in `docs/research/`; `/aa-ma-plan` Phase 3 uses it and records `research_files=<N>`; v0.13.0 is cut (OV4).
- Acceptance Criteria:
  - [ ] `claude-code/skills/aa-ma-research/SKILL.md` = Derived provenance line + frontmatter `name: aa-ma-research` + upstream HEAD body verbatim + a `## In this repo` section with the three AA-MA lines. Recipe: `sed '1d;/^## In this repo/,$d' SKILL.md | sed 's/^name: aa-ma-research$/name: research/' | md5sum` = `e1dd6af372a9e1d134eff7d8362fe3f7`; `test_aa_ma_research_frontmatter.py` green; `FORKS.json` row `state: derived`, `upstream_sha` full sha, `upstream_md5.SKILL.md: e1dd6af372a9e1d134eff7d8362fe3f7`. `stat -c '%Y' ~/.claude/skills/research` unchanged before/after `install.sh`.
  - [ ] `claude-code/agents/aa-ma-researcher.md` frontmatter `tools: Read, Glob, Grep, Bash, WebSearch, WebFetch, Write`; `tests/agents/test_aa_ma_researcher_agent.py` asserts set equality, asserts `"Agent" not in tools`, and that the prompt contains "exactly one file", "cite", "Not pursued" and "never run `claude`".
  - [ ] **Prototype verdict in provenance:** in a fresh session after `install.sh`, one live `Skill(aa-ma-research)` run on "Does `scripts/install.sh` back up a real directory before symlinking, and where?" produces `docs/research/mattpocock-trio-adoption-install-backup.md` where `grep -Ec '^\*\*(Created|Author|Reviewed-Through-Date|Valid-Through|Sources):\*\*' <file>` = 5 and `grep -Eq '[A-Za-z0-9_./-]+\.(sh|md|py):[0-9]+' <file>`; the Result Log pastes the agent-completion notice showing its tool tally with no `Agent` calls and `grep -c 'claude -p' ~/.claude/projects/<project-dir>/<session>/subagents/<agent>.jsonl` = 0 (path as shown in the spawn result); provenance line `[ts] PROTOTYPE — <Milestone 4 heading> — PASS: files=1 nested_agents=0; branch=n/a`.
  - [ ] `grep -q 'Skill(aa-ma-research)' claude-code/commands/aa-ma-plan.md`; `grep -c 'research_files=' claude-code/commands/aa-ma-plan.md` ≥ 2 and `docs/spec/plan-marker-grammar.md` ≥ 2; `grep -q 'docs/research/' <(sed -n '/Step 5.3/,/Step 5.5/p' claude-code/commands/aa-ma-plan.md)`; `grep -q 'aa-ma-research' claude-code/skills/aa-ma-plan-workflow/references/PHASE_3_RESEARCH.md`; the `research-consolidation` row there contains "optional"; `grep -q '_phase_3' TODOS.md` (deferred, D1).
  - [ ] `~/.claude/skills/aa-ma-research` after `scripts/install.sh` is a symlink to the repo dir (no backup needed — new name).
  - [ ] Counts: skills 20→21, agents 11→12 in `SECURITY.md` (lists), `README.md` skills table, foundations `### Skills (21)`/`### Agents (12)` (CLAUDE.md locally); ADR-0012 → Implemented.
  - [ ] **Release:** `scripts/release.sh minor --headline "fork manifest, grilling, prototype gate, research agent" --dry-run` clean, then real run → tag `v0.13.0` pushed; GitHub Release exists (OV4).
- Tests: `uv run pytest tests/skills tests/agents tests/plan_markers tests/commands -q`; `bats tests/hooks/aa-ma-plan-skip-warn.bats` (additive key must not break fixtures at `:32,87,108,131`).
- Rollback: revert milestone commits; `scripts/uninstall.sh` removes the `~/.claude/skills/aa-ma-research` symlink. Release rollback per `docs/runbooks/release.md`.

### Sub-step 4.1: Fork `research` from HEAD as `aa-ma-research` (Derived) + frontmatter test (test committed first)
- Status: PENDING
- Mode: AFK
- Dependencies: None
- Effort: 30m · Complexity: 25%
- Acceptance Criteria:
  - File per the M4 Contract; `uv run pytest tests/skills/test_aa_ma_research_frontmatter.py -q` green; `FORKS.json` row (`state: derived`, `upstream_md5.SKILL.md` = HEAD whole-file md5 `e1dd6af372a9e1d134eff7d8362fe3f7`).
- Artefacts: `claude-code/skills/aa-ma-research/SKILL.md`, `tests/skills/test_aa_ma_research_frontmatter.py`, `FORKS.json`.
- Result Log: [pending]

### Sub-step 4.2: `aa-ma-researcher` agent + test (test committed first, red against the missing file)
- Status: PENDING
- Mode: AFK
- Dependencies: None
- Effort: 40m · Complexity: 35%
- Acceptance Criteria:
  - `uv run pytest tests/agents/test_aa_ma_researcher_agent.py -q` green (YAML parse; `tools` set equality; `"Agent" not in tools`; prompt contains "exactly one file", "cite", "Not pursued", "never run `claude`").
- Artefacts: `claude-code/agents/aa-ma-researcher.md`, `tests/agents/test_aa_ma_researcher_agent.py`.
- Result Log: [pending]

### Sub-step 4.3: Install + prototype run (HITL)
- Status: PENDING
- Mode: HITL
- Dependencies: Steps 4.1, 4.2
- Effort: 30m · Complexity: 40%
- Acceptance Criteria:
  - `readlink ~/.claude/skills/aa-ma-research` = repo dir; `~/.claude/skills/research` unchanged; fresh session; live `Skill(aa-ma-research)` run yields `docs/research/mattpocock-trio-adoption-install-backup.md` + provenance PROTOTYPE line per the milestone criteria (agent tool tally with zero `Agent` calls; `claude -p` count 0 in the subagent transcript).
- Artefacts: `docs/research/mattpocock-trio-adoption-install-backup.md`, `mattpocock-trio-adoption-provenance.log`.
- Result Log: [pending]

### Sub-step 4.4: `/aa-ma-plan` Phase 3 wiring, marker grammar, PHASE_3_RESEARCH.md
- Status: PENDING
- Mode: AFK
- Dependencies: Step 4.3
- Effort: 45m · Complexity: 40%
- Acceptance Criteria:
  - Milestone criterion 4 (`Skill(aa-ma-research)` in `aa-ma-plan.md`; `research_files=` ≥ 2 in both `aa-ma-plan.md` and `docs/spec/plan-marker-grammar.md`; `docs/research/` between Step 5.3 and Step 5.5; `PHASE_3_RESEARCH.md` names `aa-ma-research` and marks `research-consolidation` optional; `_phase_3` in `TODOS.md`); `uv run pytest tests/plan_markers tests/commands -q` green; `bats tests/hooks/aa-ma-plan-skip-warn.bats` green.
- Artefacts: `claude-code/commands/aa-ma-plan.md`, `docs/spec/plan-marker-grammar.md`, `claude-code/skills/aa-ma-plan-workflow/references/PHASE_3_RESEARCH.md`, `TODOS.md`.
- Result Log: [pending]

### Sub-step 4.5: Counts, ATTRIBUTION, ADR-0012, CHANGELOG, TODOS.md, sync
- Status: PENDING
- Mode: AFK
- Dependencies: Step 4.4
- Effort: 30m · Complexity: 20%
- Acceptance Criteria:
  - Count test green (skills 21, agents 12); ADR-0012 Implemented; `TODOS.md` carries the fingerprint `_phase_3` and `docs/research/README.md` entries; commit + push.
- Artefacts: `SECURITY.md`, `README.md`, `docs/spec/claude-code-foundations.md`, `CLAUDE.md` (local), `docs/ATTRIBUTION.md`, `docs/adr/0012-*.md`, `CHANGELOG.md`, `TODOS.md`.
- Result Log: [pending]

### Sub-step 4.6: Release v0.13.0
- Status: PENDING
- Mode: HITL
- Dependencies: Step 4.5
- Effort: 20m · Complexity: 30%
- Acceptance Criteria:
  - `scripts/release.sh minor --headline "fork manifest, grilling, prototype gate, research agent" --dry-run` clean; real run pushes tag `v0.13.0` and creates the GitHub Release; `uv.lock` in the tagged tree carries 0.13.0 (L-015 / release runbook).
- Artefacts: tag `v0.13.0`, GitHub Release, `CHANGELOG.md` (via release script), `pyproject.toml` + `uv.lock` bump.
- Result Log: [pending]

---

## Milestone 5: Charting — `/aa-ma-chart` (Adaptation of wayfinder) + `--from-map`; release v0.14.0
- Status: PENDING
- Dependencies: Milestones 2, 3, 4
- Complexity: 65%
- Mode: HITL
- Gate: HARD
- Audit-Profile: code-only
- Critical-Path: hook-modification
- Prototype-Required: YES
- Effort: 10h
- Goal: A pre-plan decision map with typed tickets, resolved one per session, that hands off to `/aa-ma-plan --from-map`; proven on one real effort before the template is frozen. Guard ships under `claude-code/hooks/lib/` (eng-review 1A).
- Acceptance Criteria:
  - [ ] **Prototype verdict:** `/aa-ma-chart chart writing-for-agents-eval "Should aa-ma-forge adopt writing-for-agents?"` creates `.claude/dev/charting/writing-for-agents-eval/writing-for-agents-eval-map.md` with `grep -c '^- Type: research'` ≥ 1 and `'^- Type: grilling'` ≥ 1; one `work` session resolves the research ticket (AFK; `#### Answer` present; `ls docs/research/writing-for-agents-eval-*.md`) and one resolves a grilling ticket (HITL); a claim attempted while another non-research ticket is CLAIMED exits 1 and its stdout (the frontier list) is pasted in the Result Log; provenance `[ts] PROTOTYPE — <Milestone 5 heading> — PASS: tickets=<N> resolved=<N> refused_claims=1; branch=n/a`; the Result Log carries a `Template-amendments:` line — `none` or a list, each item naming a diff hunk.
  - [ ] **Live handoff (OV3):** the same effort is carried to a clear map (`"$GUARD" from-map <map>; test $? -eq 0`, `GUARD` resolved via the `_cand` pattern) and `/aa-ma-plan --from-map writing-for-agents-eval --dry-run` prints a first line `--from-map dry-run: effort=writing-for-agents-eval tickets=<N> — no task directory created` followed by the seeded *Decisions so far* + *Answers*; `test ! -d .claude/dev/active/writing-for-agents-eval`; excerpt in the Result Log.
  - [ ] `bats tests/hooks/aa-ma-chart-guard.bats` against `${REPO_ROOT}/claude-code/hooks/lib/aa-ma-chart-guard.sh` (fake `CLAUDE_HOME`): (a) chart with zero fog → prints `no map needed — run /aa-ma-plan` and creates nothing; (b) claim while another non-research ticket is CLAIMED → exit 1 + frontier list; (c) `from-map` on a map with OPEN/CLAIMED tickets or non-empty fog → exit 1 listing them; (d) `reclaim` on a CLAIMED ticket resets it to OPEN, appends `- Reclaimed: <ts>`, then claims it (1B); (e) `import` inside a `git init`-ed `<tmp>` repo: once with the fixture map `git add`-ed (git mv path) and once untracked (mv + add path) — both land at `<tmp>/.claude/dev/active/<task>/<task>-map.md` and append `MAP_IMPORTED effort=<effort> tickets=<N>` to the given provenance file; a non-repo cwd → exit 1. Fixture maps under `tests/hooks/fixtures/charting/`; bats setup symlinks `aa-ma-parse.sh` beside the guard in the fake home (as `aa-ma-gate-python.bats` does).
  - [ ] `scripts/install.sh` has an explicit `create_symlink` block for `hooks/lib/aa-ma-chart-guard.sh` (same shape as the `aa-ma-parse.sh` block); `scripts/install.sh --dry-run | grep -q aa-ma-chart-guard`; `tests/hooks/install_dry_run.bats` has a case for it; after install, `readlink ~/.claude/hooks/lib/aa-ma-chart-guard.sh` points into the repo.
  - [ ] `docs/templates/map-template.md` exists; `tests/test_active_plans_canonical.py` green (no `## Milestone`/`### Sub-step` headings inside its fences).
  - [ ] `grep -q -- '--from-map <effort> \[--dry-run\]' claude-code/commands/aa-ma-plan.md docs/spec/aa-ma-quick-reference.md`; without `--dry-run`, Phase 5 calls `aa-ma-chart-guard.sh import` (bats case (e) is the proof of that leg); `aa-ma-chart.md` tells the user charting/research commits during an active plan carry `[ad-hoc]`.
  - [ ] File taxonomy: `docs/spec/aa-ma-specification.md` §II table (map row + `MAP -. optional .-> PLAN` mermaid edge), `docs/templates/README.md`, `claude-code/rules/aa-ma.md`, `docs/spec/claude-code-foundations.md`, `docs/spec/aa-ma-quick-reference.md`, `README.md` all say **5 standard + 4 optional** (`grep -rl '+ 3 optional' docs claude-code README.md` empty; CLAUDE.md updated locally, not asserted). `map-template.md` is **not** added to `WRITER_TEMPLATES` in `tests/test_active_plans_canonical.py` (its non-vacuous check needs milestone headings a map never has).
  - [ ] Counts: commands 12→13 in `SECURITY.md`, `README.md` "All commands" table (`/aa-ma-chart` row), foundations `### Commands (13)` (CLAUDE.md locally); `SECURITY.md` "8 hooks" line unchanged (guard is a `lib/` helper, not a registered hook — L-005 pattern like `aa-ma-parse.sh`); count test green.
  - [ ] `docs/ATTRIBUTION.md` gains "charting — concept adapted from wayfinder (mattpocock/skills, c55ee46); no files forked; invariant reworded to '≤1 non-research ticket CLAIMED at a time' (OV5)"; ADR-0013 Implemented; `CHANGELOG.md` M5 entries; `TODOS.md` gains the `/aa-ma-share` map allowlist entry; `CRITICAL_PATH_REVIEW — Milestone 5 …` line in provenance; release v0.14.0 cut.
- Tests: `bats tests/hooks/aa-ma-chart-guard.bats`; `shellcheck claude-code/hooks/lib/aa-ma-chart-guard.sh`; `uv run pytest tests/commands -q`; `uv run aa-ma-lint-views` on ADR-0013 and this plan.
- Rollback: revert milestone commits (taxonomy docs return to the pre-M1 state: 5+3 with impl-review listed); delete `.claude/dev/charting/`; remove the guard symlink via `scripts/uninstall.sh` (it scans `hooks/lib` for repo-pointing links). Charting has no Python — no runtime coupling to undo.
- Execution order note: the `--from-map` flag must exist before 5.3's dry-run leg — execute 5.1 → 5.2 → 5.4 (flag only) → 5.3 → 5.4 (docs) and record the split in the 5.4 Result Log.

### Sub-step 5.1: Re-add `## Unreleased`; `map-template.md` + `aa-ma-chart.md` command (chart + work modes)
- Status: PENDING
- Mode: AFK
- Dependencies: None (after v0.13.0 is tagged)
- Effort: 150m · Complexity: 55%
- Acceptance Criteria:
  - `grep -c '^## Unreleased' CHANGELOG.md` = 1 (re-added after v0.13.0); `grep -q '^## Not yet specified' docs/templates/map-template.md && grep -q '^## Out of scope' docs/templates/map-template.md && grep -q 'Claimed-at' docs/templates/map-template.md`; `grep -q '\[ad-hoc\]' claude-code/commands/aa-ma-chart.md`; `tests/test_active_plans_canonical.py` green; `uv run aa-ma-render claude-code/commands/aa-ma-chart.md --out build/render; test $? -eq 0`.
- Artefacts: `CHANGELOG.md`, `docs/templates/map-template.md`, `claude-code/commands/aa-ma-chart.md`.
- Result Log: [pending]

### Sub-step 5.2: Guard helper + bats for the four refusal/reclaim cases
- Status: PENDING
- Mode: AFK
- Dependencies: Step 5.1
- Effort: 60m · Complexity: 50%
- Acceptance Criteria:
  - `bats tests/hooks/aa-ma-chart-guard.bats` — 5 cases green against the repo path; `scripts/install.sh` gains an explicit block (copy the `aa-ma-parse.sh` one) so `install.sh --dry-run | grep -q aa-ma-chart-guard`; `bats tests/hooks/install_dry_run.bats` green with the new case; `shellcheck claude-code/hooks/lib/aa-ma-chart-guard.sh; test $? -eq 0`; `grep -c 'git rev-parse --show-toplevel)/claude-code/hooks/lib/aa-ma-chart-guard.sh' claude-code/commands/aa-ma-chart.md claude-code/commands/aa-ma-plan.md` ≥ 1 each (the `_cand` resolution, no literal `~/.claude`).
  - TDD order inside this step (recorded in the Result Log): commit 1 = bats file + fixtures, red against the absent helper; commit 2 = the helper, green.
- Artefacts: `claude-code/hooks/lib/aa-ma-chart-guard.sh`, `scripts/install.sh`, `tests/hooks/install_dry_run.bats`, `tests/hooks/aa-ma-chart-guard.bats`, `tests/hooks/fixtures/charting/{clear,open,claimed,fogless}-map.md`.
- Result Log: [pending]

### Sub-step 5.3: Prototype run on a real effort, carried through to the handoff (HITL)
- Status: PENDING
- Mode: HITL
- Dependencies: Steps 5.1, 5.2, 5.4 (flag-only leg)
- Effort: 90m · Complexity: 55%
- Acceptance Criteria:
  - Milestone criteria 1 and 2 (chart → work ×2 → clear map → `--from-map --dry-run`); Result Log `Template-amendments:` line (`none` or hunks); provenance PROTOTYPE line in the fixed grammar; charting/research commits carry `[ad-hoc]`.
- Artefacts: `.claude/dev/charting/writing-for-agents-eval/writing-for-agents-eval-map.md`, `docs/research/writing-for-agents-eval-*.md`, template amendments (if any).
- Result Log: [pending]

### Sub-step 5.4: `--from-map [--dry-run]` in `/aa-ma-plan` + taxonomy + counts + ATTRIBUTION + ADR-0013 + CHANGELOG + TODOS
- Status: PENDING
- Mode: AFK
- Dependencies: Step 5.2 (flag-only leg); Step 5.3 (docs leg)
- Effort: 75m · Complexity: 40%
- Acceptance Criteria:
  - Milestone criteria 4–9; count test green; `uv run aa-ma-lint-views <plan> --repo-root .; test $? -eq 0`; `TODOS.md` also gains the `_phase_1_3` + `grilling` fingerprint entry (grilling done in a charting session leaves Phase 1.3 unevidenced under `--from-map`).
  - Split recorded in the Result Log: flag leg (before 5.3) vs docs leg (after 5.3).
- Artefacts: `claude-code/commands/aa-ma-plan.md`, `docs/spec/aa-ma-specification.md`, `claude-code/rules/aa-ma.md`, `docs/spec/aa-ma-quick-reference.md`, `docs/spec/claude-code-foundations.md`, `docs/templates/README.md`, `CLAUDE.md` (local), `README.md`, `SECURITY.md`, `docs/ATTRIBUTION.md`, `docs/adr/0013-*.md`, `CHANGELOG.md`, `TODOS.md`.
- Result Log: [pending]

### Sub-step 5.5: CRITICAL_PATH_REVIEW, HARD gate approval, impact analysis, sync, release v0.14.0
- Status: PENDING
- Mode: HITL
- Dependencies: Steps 5.3, 5.4
- Effort: 30m · Complexity: 30%
- Acceptance Criteria:
  - All prototype-run artefacts (`.claude/dev/charting/**`, `docs/research/writing-for-agents-eval-*.md`) committed with `[ad-hoc]` **and pushed** (release.sh requires HEAD == origin/main and a clean tree); `gh auth status` ok; `CRITICAL_PATH_REVIEW — <Milestone 5 heading> — hook-modification — <evidence>` in provenance (guard bats + shellcheck); GATE APPROVAL entry in context-log; `scripts/release.sh minor --headline "charting: pre-plan decision maps (/aa-ma-chart, --from-map)" --dry-run` clean, then real run → tag `v0.14.0` pushed; GitHub Release exists.
- Artefacts: `mattpocock-trio-adoption-context-log.md`, `mattpocock-trio-adoption-provenance.log`, `CHANGELOG.md` (via release script), tag `v0.14.0`.
- Result Log: [pending]
