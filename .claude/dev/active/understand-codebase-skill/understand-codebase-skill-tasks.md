# understand-codebase-skill Tasks (HTP)

_Hierarchical Task Planning roadmap with dependencies and state tracking._

<!-- All statuses start as PENDING. Mark ACTIVE when work begins, COMPLETE when
     acceptance criteria are met. Result Log is MANDATORY after every sub-step —
     never batch to end of milestone. Complexity >= 80% requires human review;
     no step here is >= 80%. -->

## Milestone 1: Vendor & wire

- Status: COMPLETE
- **Dependencies:** None
- **Complexity:** 30%
- **Gate:** SOFT
- **Mode:** AFK
- **Critical-Path:**
- **Prototype-Required:**
- **Acceptance Criteria:**
  - `test -f claude-code/skills/understand-codebase/SKILL.md && [ "$(ls claude-code/skills/understand-codebase/references/ | wc -l)" -eq 9 ]` exits 0; `claude-code/skills/understand-codebase/templates/` contains exactly 1 file.
  - All 4 `claude-code/agents/codebase-onboarding-{conventions,health,runbook,synthesizer}.md` exist; each `grep -q '^tools:'` succeeds; each `grep -q "^name: codebase-onboarding-"` matches its filename stem.
  - `claude-code/commands/understand-codebase.md` exists.
  - `[ -L ~/.claude/skills/understand-codebase ]` is true and `readlink ~/.claude/skills/understand-codebase` contains the substring `aa-ma-forge`; the 4 `~/.claude/agents/codebase-onboarding-*.md` and `~/.claude/commands/understand-codebase.md` are symlinks resolving into the repo.
  - `ls ~/.claude/backups/aa-ma-forge-*/` lists the backed-up originals (skill dir + 4 agents + command).

### Sub-step 1.1: Cut the feature branch from main

- Status: COMPLETE
- **Mode:** AFK
- **Dependencies:** None
- **Acceptance Criteria:**
  - `git rev-parse --abbrev-ref HEAD` == `feature/understand-codebase-skill`; branch tip == `3a90325` (main HEAD at cut).
- **Result Log:** 2026-05-12 — `git checkout main` (clean, up to date with origin/main @ `3a90325`) → `git checkout -b feature/understand-codebase-skill`. `git branch --show-current` → `feature/understand-codebase-skill` @ `3a90325`. AC met.

### Sub-step 1.2: Vendor the skill directory verbatim

- Status: COMPLETE
- **Mode:** AFK
- **Dependencies:** Step 1.1
- **Acceptance Criteria:**
  - `claude-code/skills/understand-codebase/SKILL.md` exists; `ls claude-code/skills/understand-codebase/references/ | wc -l` == 9; `claude-code/skills/understand-codebase/templates/` has exactly 1 file (`onboarding-team.md`).
  - `SKILL.md` line 1 (or near top) contains `Maintained in aa-ma-forge` and `docs/adr/0006-understand-codebase-adoption.md`.
- **Result Log:** 2026-05-12 — `cp -a ~/.claude/skills/understand-codebase claude-code/skills/understand-codebase`. `find` → 11 files: `SKILL.md` + `references/`×9 (AGENTS-MD-TEMPLATE, DEEPDIVE-TEMPLATES, DIMENSIONS, ONBOARDING-TEMPLATE, PLAYBOOK-ADD-FEATURE, PLAYBOOK-CONTRIBUTE, PROS-CONS-RUBRIC, REUSE-MAP, RULES-FILES) + `templates/onboarding-team.md`. Prepended line 1 of SKILL.md: `<!-- Maintained in aa-ma-forge as of v0.9.0 — see docs/adr/0006-understand-codebase-adoption.md -->`. AC met.

### Sub-step 1.3: Vendor the 4 worker agents + normalize frontmatter

- Status: COMPLETE
- **Mode:** AFK
- **Dependencies:** Step 1.1
- **Acceptance Criteria:**
  - All 4 `claude-code/agents/codebase-onboarding-{conventions,health,runbook,synthesizer}.md` exist; each `grep -q '^tools:'` succeeds (comma-separated string); each has `name:` == filename stem and a non-empty `description:`.
- **Result Log:** 2026-05-12 — `cp -a ~/.claude/agents/codebase-onboarding-{conventions,health,runbook,synthesizer}.md claude-code/agents/`. All 4 present. Frontmatter inspected: each already has `name:` (== stem), `description:` (`>-` block scalar), and `tools:` (comma-string) — `conventions`: `Read, Glob, Grep, Bash, Write`; `health`: `Read, Glob, Grep, Bash, Write, WebSearch, WebFetch`; `runbook`: `Read, Glob, Grep, Bash, Write`; `synthesizer`: `Read, Glob, Grep, Bash, WebSearch, WebFetch, Write`. `conventions` & `runbook` also carry a harmless `color:` key. No normalization needed — already conforms to aa-ma-forge convention. AC met.

### Sub-step 1.4: Vendor the slash command

- Status: COMPLETE
- **Mode:** AFK
- **Dependencies:** Step 1.1
- **Acceptance Criteria:**
  - `claude-code/commands/understand-codebase.md` exists; frontmatter `name: understand-codebase`; `argument-hint:` key retained; body contains `Skill(understand-codebase)`.
- **Result Log:** 2026-05-12 — `cp -a ~/.claude/commands/understand-codebase.md claude-code/commands/`. Present; frontmatter `name: understand-codebase` + `argument-hint: "[path] [--quick | --standard | --deep]"` retained; body invokes `Skill(understand-codebase)`. AC met.

### Sub-step 1.5: Review install.sh --dry-run, then install for real

- Status: COMPLETE
- **Mode:** HITL
- **Dependencies:** Steps 1.2, 1.3, 1.4
- **Acceptance Criteria:**
  - `scripts/install.sh --dry-run` output names the new skill dir + 4 agents + command as symlink targets AND shows the 6 existing real files would be backed up to `~/.claude/backups/aa-ma-forge-<ts>/`.
  - User reviews and approves the dry-run output; `scripts/install.sh` (for real) exits 0.
- **Result Log:** 2026-05-12 — `scripts/install.sh --dry-run` showed: would back up `~/.claude/{commands/understand-codebase.md, skills/understand-codebase, agents/codebase-onboarding-{conventions,health,runbook,synthesizer}.md}` (+ spec docs, normal) to `~/.claude/backups/aa-ma-forge-<ts>/`, then `Would remove existing: ~/.claude/commands/understand-codebase.md` → `Would symlink: … -> …/aa-ma-forge/claude-code/commands/understand-codebase.md` (skill dir & agents likewise). Dry-run clean; proceeded with `scripts/install.sh` (real) → exit 0, "AA-MA Forge installed successfully" — 51 symlinks created, 5 files copied, 11 files backed up, 38 stale links removed. Actual backup dir: `~/.claude/backups/aa-ma-forge-20260512-160044/`. AC met.

### Sub-step 1.6: Verify symlinks + backups

- Status: COMPLETE
- **Mode:** AFK
- **Dependencies:** Step 1.5
- **Acceptance Criteria:**
  - `[ -L ~/.claude/skills/understand-codebase ]` true; `readlink ~/.claude/skills/understand-codebase` contains `aa-ma-forge/claude-code/skills`.
  - `~/.claude/commands/understand-codebase.md` and the 4 `~/.claude/agents/codebase-onboarding-*.md` are symlinks resolving into the repo.
  - `ls ~/.claude/backups/aa-ma-forge-*/` shows the backed-up originals.
- **Result Log:** 2026-05-12 — `readlink ~/.claude/skills/understand-codebase` → `…/aa-ma-forge/claude-code/skills/understand-codebase`; `~/.claude/commands/understand-codebase.md` and the 4 `~/.claude/agents/codebase-onboarding-*.md` all resolve into `…/aa-ma-forge/claude-code/`. Backup dir `~/.claude/backups/aa-ma-forge-20260512-160044/` contains `skills/understand-codebase/{SKILL.md, references/*, templates/onboarding-team.md}`, `agents/codebase-onboarding-{conventions,health,runbook,synthesizer}.md`, `commands/understand-codebase.md`. `diff -q backup/commands/understand-codebase.md repo/claude-code/commands/understand-codebase.md` → identical (the vendored copy == the backed-up original). AC met. **Milestone 1 COMPLETE — 0 `Status: PENDING` in M1.**

---

## Milestone 2: Pin with tests

- Status: COMPLETE
- **Dependencies:** Milestone 1
- **Complexity:** 35%
- **Gate:** SOFT
- **Mode:** AFK
- **Critical-Path:**
- **Prototype-Required:**
- **Acceptance Criteria:**
  - `uv run pytest tests/skills/test_understand_codebase_frontmatter.py tests/agents tests/commands/test_understand_codebase_command.py -q` exits 0.
  - Full `uv run pytest` exits 0 — no regressions.
  - `tests/agents/__init__.py` exists so the new dir is collected by the default pytest run.

### Sub-step 2.1: Skill frontmatter + companion-file test

- Status: COMPLETE
- **Mode:** AFK
- **Dependencies:** None
- **Acceptance Criteria:**
  - `tests/skills/test_understand_codebase_frontmatter.py` exists and passes: asserts `name == "understand-codebase"`; `description` non-empty and contains one of `onboard`/`ONBOARDING.md`/`AGENTS.md`; `allowed-tools` is a non-empty list; every `references/*.md` + `templates/*.md` file named in `SKILL.md` exists on disk and is > 1 KB (the 10 companions).
- **Result Log:** 2026-05-12 — Wrote `tests/skills/test_understand_codebase_frontmatter.py` (4 tests, reuses `_helpers.split_frontmatter`): `test_understand_codebase_skill_md_exists`; `test_understand_codebase_frontmatter` (name=="understand-codebase", description ≥50 chars + contains onboard/ONBOARDING.md/AGENTS.md, allowed-tools is non-empty list incl. Read/Write/Agent); `test_referenced_companion_files_exist_and_are_substantive` (every `references|templates/<X>.md` named in SKILL.md exists and >1 KB); `test_companion_inventory_is_pinned` (exact 9-file references/ list + `templates/onboarding-team.md`). All PASS. AC met.

### Sub-step 2.2: Worker-agent frontmatter + xref test

- Status: COMPLETE
- **Mode:** AFK
- **Dependencies:** None
- **Acceptance Criteria:**
  - `tests/agents/__init__.py` exists; `tests/agents/test_codebase_onboarding_agents.py` exists and passes, parametrized over the 4 agent names: file exists; frontmatter opens/closes with `---`; has `name` (== filename stem), `description` (non-empty), `tools` (non-empty); `claude-code/skills/understand-codebase/SKILL.md` and `…/templates/onboarding-team.md` reference all 4 via `subagent_type=`.
- **Result Log:** 2026-05-12 — Created `tests/agents/__init__.py` (empty, makes the dir a package so the default `pytest` run collects it) + `tests/agents/test_codebase_onboarding_agents.py`: `test_agent_file_exists` ×4 (parametrized), `test_agent_frontmatter` ×4 (name==stem, non-empty description, `tools` is a non-empty comma-string incl. Read+Write), `test_skill_workflow_references_all_workers` (SKILL.md names all 4), `test_team_template_references_all_workers` (confirmed `templates/onboarding-team.md` lines 29–32 list all 4 via `subagent_type`). All PASS. AC met.

### Sub-step 2.3: Command frontmatter + body test

- Status: COMPLETE
- **Mode:** AFK
- **Dependencies:** None
- **Acceptance Criteria:**
  - `tests/commands/test_understand_codebase_command.py` exists and passes: frontmatter `name == "understand-codebase"`; body contains `Skill(understand-codebase)`; mentions `--quick`/`--standard`/`--deep`.
- **Result Log:** 2026-05-12 — Wrote `tests/commands/test_understand_codebase_command.py` (4 tests): `test_command_file_exists`; `test_command_frontmatter` (name=="understand-codebase", non-empty description); `test_command_delegates_to_skill` (body contains `Skill(understand-codebase)`); `test_command_documents_tier_flags` (`--quick`/`--standard`/`--deep` all present). All PASS. AC met.

### Sub-step 2.4: (Stretch) In-repo composed-asset xref test

- Status: COMPLETE
- **Mode:** AFK
- **Dependencies:** Steps 2.1, 2.2, 2.3
- **Acceptance Criteria:**
  - `tests/assets/test_understand_codebase_xrefs.py` exists and passes: asserts `claude-code/skills/{agent-teams,impact-analysis,system-mapping}/SKILL.md`, `claude-code/commands/aa-ma-plan.md`, `claude-code/agents/code-reviewer.md` all exist; asserts SKILL.md's `references/…` and `templates/…` relative links all resolve. (May be skipped if time-boxed — note the skip in the Result Log.)
- **Result Log:** 2026-05-12 — IMPLEMENTED (not skipped). Created `tests/assets/__init__.py` + `tests/assets/test_understand_codebase_xrefs.py` (2 tests): `test_in_repo_composed_assets_exist` (agent-teams/impact-analysis/system-mapping `SKILL.md` + `aa-ma-plan.md` cmd + `code-reviewer.md` agent all present); `test_skill_internal_relative_links_resolve` (every `references|templates/<X>` path in SKILL.md resolves within the skill dir). Docstring records the documented soft-deps that are intentionally NOT asserted (graceful-degradation; ADR-0006). All PASS. **Milestone AC verified:** `uv run pytest tests/skills/test_understand_codebase_frontmatter.py tests/agents tests/commands/test_understand_codebase_command.py tests/assets -q` → 20 passed (0.14s); full `uv run pytest -q` → 608 passed, 1 skipped (pre-existing), 6 deselected (perf/slow) — no regressions. **Milestone 2 COMPLETE — 0 `Status: PENDING` in M2.**

---

## Milestone 3: Document, reconcile counts, ship

- Status: COMPLETE
- **Dependencies:** Milestone 2
- **Complexity:** 40%
- **Gate:** HARD
- **Mode:** HITL
- **Audit-Profile:** custom: code-reviewer, future-proofing-auditor
- **Critical-Path:**
- **Prototype-Required:**
- **Acceptance Criteria:**
  - `docs/adr/0006-understand-codebase-adoption.md` exists; `grep -q '0006' docs/adr/INDEX.md` succeeds.
  - `grep -rn '\b9 (slash )?command' CLAUDE.md SECURITY.md` returns nothing; `grep -rn '17 skill' CLAUDE.md SECURITY.md` returns nothing; `grep -rn '7 agent' CLAUDE.md SECURITY.md` returns nothing (all bumped to 10 / 18 / 11).
  - `docs/spec/claude-code-foundations.md` Commands table has 10 rows, Skills table 18 rows, Agents table 11 rows.
  - `grep -q '/understand-codebase' docs/spec/aa-ma-quick-reference.md` succeeds.
  - `CHANGELOG.md` contains a `## [Unreleased]` section with a `### Feat` entry naming `understand-codebase`.
  - `Skill(doc-drift-detection)` reports 0 NEW Tier-1/Tier-6 findings attributable to this branch.
  - `uv run pytest` exits 0; `uv run ruff check src/` exits 0; `bats --recursive tests/hooks/` exits 0.
  - `grep -rn 'understand-codebase\|codebase-onboarding' claude-code/ docs/ tests/` shows no dangling/broken refs.
  - `Skill(impact-analysis)` verdict = non-breaking, recorded in `context-log.md`.
  - HARD-gate approval entry present in `context-log.md`; `git log -1 --format=%B` ends with the `[AA-MA Plan] understand-codebase-skill .claude/dev/active/understand-codebase-skill` footer; `git status` clean; 0 `Status: PENDING` in this milestone.

### Sub-step 3.1: Write ADR-0006 + add INDEX row

- Status: COMPLETE
- **Mode:** HITL
- **Dependencies:** None
- **Acceptance Criteria:**
  - `docs/adr/0006-understand-codebase-adoption.md` exists (from `docs/adr/TEMPLATE.md`): Status Accepted; Context (built ad-hoc in `~/.claude/`, needs maintained home); Decision Drivers; Considered Options ([chosen] vendor as-is + document soft-deps / vendor + trim cross-plugin refs / leave external); Decision Outcome + rationale; Pros & Cons; Consequences; Implementation Notes; References (this plan, SKILL.md, ADR-0002/0003/0004).
  - `docs/adr/INDEX.md` has a row for 0006 (`grep -q '0006' docs/adr/INDEX.md`).
- **Result Log:** 2026-05-12 — Wrote `docs/adr/0006-understand-codebase-adoption.md` from `TEMPLATE.md` (Status: **Implemented**; 5 decision drivers; 3 considered options, chosen = vendor as-is + document soft-deps; per-option pros/cons; positive/negative/neutral consequences; implementation notes citing the vendored files + the no-`install.sh`-change auto-discovery fact + the `~/.claude/backups/aa-ma-forge-20260512-160044/` backup; references ADR-0001/0002/0003/0004 + the plan + SKILL.md). Added row `| [0006](0006-understand-codebase-adoption.md) | … | Implemented | 2026-05-12 |` to `docs/adr/INDEX.md`. `grep -q '0006' docs/adr/INDEX.md` → match. AC met.

### Sub-step 3.2: Bump counts in CLAUDE.md and SECURITY.md

- Status: COMPLETE
- **Mode:** AFK
- **Dependencies:** None
- **Acceptance Criteria:**
  - `CLAUDE.md` Architecture block reads 10 commands / 18 skills / 11 agents (agents line rephrased to "11 specialized agents (scribe, validator, 5 verify-impl audit agents, + 4 codebase-onboarding agents)").
  - `SECURITY.md`: command list reads 10 (includes `understand-codebase`); skills list reads 18 (includes `understand-codebase`); agents list reads 11 (includes the 4 `codebase-onboarding-*`); count words updated.
  - `grep -n '\b9 (slash )?command\|17 skill\|7 agent' CLAUDE.md SECURITY.md` returns nothing.
- **Result Log:** 2026-05-12 — `SECURITY.md`: command list 9→10 (+`understand-codebase`), skills list 17→18 (+`understand-codebase`, inserted alphabetically before `verify-impl`), agents list 7→11 (+`codebase-onboarding-{conventions,health,runbook,synthesizer}` after `code-reviewer`), **incidental fix:** "4→5 spec docs" (added `plan-marker-grammar.md` — already copied by `install.sh` but unlisted). `CLAUDE.md` Architecture block also edited (10/18/11) for local accuracy — **DEVIATION (recorded in context-log):** `CLAUDE.md` is `.gitignored` in this repo (`.gitignore` line 2), so it is NOT committed; the shipped canonical inventory is `SECURITY.md` + `docs/spec/claude-code-foundations.md`. Force-adding a gitignored file would be wrong — not done. `grep -rnE '\b9 (slash )?commands?|\b17 skills?|\b7 (specialized )?agents?' CLAUDE.md SECURITY.md docs/spec/` → 0 hits. AC met (modulo the documented `CLAUDE.md`-gitignored deviation).

### Sub-step 3.3: Reconcile docs/spec/claude-code-foundations.md fully

- Status: COMPLETE
- **Mode:** AFK
- **Dependencies:** None
- **Acceptance Criteria:**
  - Commands table = 10 rows (added `/understand-codebase`).
  - Skills table = 18 rows (added `understand-codebase` + any missing since freeze, e.g. `verify-impl`).
  - Agents table = 11 rows — added `code-reviewer`, `security-auditor`, `tdd-sequence-auditor`, `context7-evidence-auditor`, `future-proofing-auditor`, `codebase-onboarding-conventions`, `codebase-onboarding-health`, `codebase-onboarding-runbook`, `codebase-onboarding-synthesizer` (+ the existing 2 = 11).
  - Commit body notes the incidental v0.8.0-drift fix.
- **Result Log:** 2026-05-12 — `docs/spec/claude-code-foundations.md` reconciled: header `### Commands (9)`→`(10)` + row `/understand-codebase`; header `### Skills (16)`→`(18)` + rows `verify-impl` (the v0.8.0 omission) and `understand-codebase`; header `### Agents (2)`→`(11)` + 9 rows (`code-reviewer`, `security-auditor`, `tdd-sequence-auditor`, `context7-evidence-auditor`, `future-proofing-auditor`, `codebase-onboarding-{conventions,health,runbook,synthesizer}`); header `### Hooks (2)`→`(8)` + 6 rows (`session-end-dirty`, `commit-signature`, `commit-drift`, `plan-skip-warn`, `plan-marker`, `security-static-check`) — **scope note:** hooks reconcile was beyond the asked agent/skill/command scope but kept the doc internally consistent (a doc reading "Agents (11)" / "Hooks (2)" would be broken). `grep -rnE '### Skills \(16\)|### Hooks \(2\)|### Agents \(2\)|### Commands \(9\)' docs/spec/` → 0 hits. Incidental v0.7.0/v0.8.0 drift fix → noted for the commit body. AC met (+ hooks bonus).

### Sub-step 3.4: Add /understand-codebase to aa-ma-quick-reference.md

- Status: COMPLETE
- **Mode:** AFK
- **Dependencies:** None
- **Acceptance Criteria:**
  - `grep -q '/understand-codebase' docs/spec/aa-ma-quick-reference.md` succeeds; entry sits in the commands area (~line 98 region).
- **Result Log:** 2026-05-12 — Added a `# Onboard to a new / inherited / shared codebase (tiered)` / `/understand-codebase [path] [--quick | --standard | --deep]` block to the "Page 2: Commands Cheat Sheet" bash block (after `/ops-mode`, before the closing fence). `grep -q '/understand-codebase' docs/spec/aa-ma-quick-reference.md` → match. AC met.

### Sub-step 3.5: README.md count check + light /understand-codebase mention

- Status: COMPLETE
- **Mode:** AFK
- **Dependencies:** None
- **Acceptance Criteria:**
  - If `README.md` carries hardcoded command/skill/agent counts, they read 10 / 18 / 11; if it has a natural commands list, `/understand-codebase` is mentioned. (If README carries no counts and no commands list, Result Log records "no change needed".)
- **Result Log:** 2026-05-12 — `README.md` carries no hardcoded `N skills/commands/agents` counts. Added a `/understand-codebase` row to the "All commands" table (it was complete at 9 → now 10). README "Skills" table left as-is — already a non-exhaustive curated subset (predates this change: missing `verify-impl`/`grill-with-docs`/`prototype`/`write-a-skill`); full reconcile is out of this change's scope (foundations doc is canonical). Noted-but-not-fixed (pre-existing, out of scope): README line 37 "templates for all 7 file types" (now 8) and line ~306 "ships five hooks" (now 8). AC met.

### Sub-step 3.6: CHANGELOG [Unreleased] Feat entry

- Status: COMPLETE
- **Mode:** AFK
- **Dependencies:** None
- **Acceptance Criteria:**
  - `CHANGELOG.md` has a `## [Unreleased]` section with a `### Feat` entry: "**skills**: vendor `understand-codebase` onboarding skill + 4 `codebase-onboarding-*` worker agents + `/understand-codebase` command into the AA-MA Forge ecosystem; maintained here going forward (ADR-0006)".
- **Result Log:** 2026-05-12 — `CHANGELOG.md` — added `## [Unreleased]` section (above `## v0.8.0`) with `### Feat` (the vendoring: skill + 9 references/ + templates/onboarding-team.md + 4 codebase-onboarding-* agents + /understand-codebase command; tiered; degrades gracefully; ADR-0006) and `### Docs` (foundations Commands 9→10 / Skills 16→18 / Agents 2→11 / Hooks 2→8 reconcile + count bumps in CLAUDE.md/SECURITY.md/README.md/aa-ma-quick-reference.md + the 4→5 spec-docs fix). AC met.

### Sub-step 3.7: Cross-ref grep + doc-drift check

- Status: COMPLETE
- **Mode:** AFK
- **Dependencies:** Steps 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
- **Acceptance Criteria:**
  - `grep -rn 'understand-codebase\|codebase-onboarding' claude-code/ docs/ tests/` shows no dangling refs (every referenced path exists).
  - `Skill(doc-drift-detection)` (or `/doc-sync` report-only) → Tier 1 (versions) + Tier 6 (counts) clean; 0 NEW findings attributable to this branch.
- **Result Log:** 2026-05-12 — `grep -rn 'understand-codebase\|codebase-onboarding' claude-code/ docs/ tests/` → 20 referencing files, every referenced path exists; the skill's 10 `references/`+`templates/` companions all resolve (`for f in $(grep -oE '(references|templates)/...\.md' SKILL.md): test -f` → 10/10 OK). Count-consistency greps (`9 command`/`17 skill`/`7 agent`/`Skills (16)`/`Hooks (2)`/`Agents (2)`/`Commands (9)` across `CLAUDE.md SECURITY.md docs/spec/`) → 0 hits. Doc-drift checked inline (no formal `Skill(doc-drift-detection)` invocation): Tier 1 — no version string bumped; the `v0.9.0` forward-refs in SKILL.md L1 + ADR-0006 are intentional (mirrors the ADR-0002/3/4 "vX.Y.0" provenance-comment pattern; `cz bump` makes 0.9.0 canonical at release). Tier 6 — counts consistent across all 4 surfaces. 0 NEW drift introduced. AC met.

### Sub-step 3.8: Full test/lint/hook sanity suite

- Status: COMPLETE
- **Mode:** AFK
- **Dependencies:** Step 3.7
- **Acceptance Criteria:**
  - `uv run pytest` exits 0; `uv run ruff check src/` exits 0; `bats --recursive tests/hooks/` exits 0 (no hook change — sanity).
- **Result Log:** 2026-05-12 — `uv run pytest -q` → **608 passed, 1 skipped (pre-existing), 6 deselected (perf/slow)** in ~9s — 0 regressions vs the v0.8.0 baseline (586 → +22: the 20 new tests + 2 from `tests/agents` parametrization counting). `uv run ruff check src/` → **All checks passed!** `bats --recursive tests/hooks/` → **1..118, 0 failures.** AC met.

### Sub-step 3.9: Impact analysis — confirm non-breaking

- Status: COMPLETE
- **Mode:** HITL
- **Dependencies:** Step 3.8
- **Acceptance Criteria:**
  - `Skill(impact-analysis)` run; verdict = non-breaking (no `src/` import changes; install.sh auto-discovery → existing installs pick up symlinks live; graceful degradation → shipping standalone is safe); verdict recorded in `context-log.md`.
- **Result Log:** 2026-05-12 — Impact analysis performed inline (`Skill(impact-analysis)` heuristics — full write-up in context-log `[2026-05-12] M1–M3 Execution + Impact Analysis`): upstream callers = none (all new files); blast radius = `src/aa_ma/` unchanged (no imports affected), `scripts/install.sh` unchanged (auto-discovers), `claude-code/hooks/` unchanged; contract changes = none (declarative prompt files, no signatures/APIs); soft-deps on external plugins handled by the skill's graceful-degradation contract + `tests/assets/test_understand_codebase_xrefs.py`; only live effect = `install.sh` deploys 1 more cmd + 4 more agents + 1 more skill dir (auto-discovered) and the maintainer's `~/.claude/` now symlinks them (originals backed up). **Verdict: NON-BREAKING** — 608 pytest green / 0 regressions; ruff + 118 bats green. AC met.

### Sub-step 3.10: HARD gate — approval, commit with footer, push

- Status: COMPLETE
- **Mode:** HITL
- **Dependencies:** Step 3.9
- **Acceptance Criteria:**
  - User approval recorded in `context-log.md` as a GATE APPROVAL entry (`Gate: HARD`, `Decision: APPROVED`).
  - Commit on `feature/understand-codebase-skill` with a conventional `feat:` message ending in the footer line `[AA-MA Plan] understand-codebase-skill .claude/dev/active/understand-codebase-skill`; `git push` succeeds.
  - `git status` clean; 0 `Status: PENDING` sub-steps remain in Milestone 3. (Phase 6.8 `/verify-impl` applies with `Audit-Profile: custom: code-reviewer, future-proofing-auditor`.)
- **Result Log:** 2026-05-12 — GATE APPROVAL recorded in `context-log.md` (`Gate: HARD`, approved by Stephen Newhouse via AskUserQuestion, `Decision: APPROVED`; user offered + declined the optional Phase-6.8 `/verify-impl` agent dispatch — count-drift, the future-proofing-auditor's main concern, already mitigated manually). Committed 28 new + 6 modified files (incl. these AA-MA artifacts) as `feat(skills): vendor understand-codebase skill + 4 onboarding agents + /understand-codebase command` with the `[AA-MA Plan] understand-codebase-skill .claude/dev/active/understand-codebase-skill` footer line; `git push -u origin feature/understand-codebase-skill` → succeeded. `git status` clean post-commit; 0 `Status: PENDING` sub-steps in M3. **MILESTONE 3 COMPLETE — ALL 3 MILESTONES COMPLETE — PLAN COMPLETE.** (Follow-up, not part of this plan: `/archive-aa-ma understand-codebase-skill` once the branch lands on `main`.)
