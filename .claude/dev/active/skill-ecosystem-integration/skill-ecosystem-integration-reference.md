# skill-ecosystem-integration Reference

**Immutable facts. High-priority context. Load FIRST.**

_Last Updated: 2026-05-10_

---

## Repo & Branch

- **Repo root:** `/home/sjnewhouse/biorelate/projects/gitlab/github_private/aa-ma-forge`
- **Plan branch (to be cut from main):** `feature/skill-ecosystem-integration`
- **Current main HEAD at planning:** `9b5ae85 chore: archive AA-MA plan aa-ma-engineering-standards`
- **Current version (pre-plan):** `0.5.0` (in `pyproject.toml`)
- **Target version (post-plan):** `0.6.0`

## Critical Paths in This Plan (per `claude-code/rules/engineering-standards.md`)

- `doc-count-drift` — affects M1.5, M1.6 (skill count 13 → 14) AND M2.6, M2.7 (skill count 14 → 16).
- `version-pipeline` — affects M3.5 (single 0.5.0 → 0.6.0 bump covering M1+M2+M3 deferred to plan close).

## Skill Count Trajectory

| Stage | Count | Skills added |
|-------|-------|--------------|
| Pre-plan (post-v0.5.0) | 13 | (baseline) |
| Post-M1 | 14 | grill-with-docs |
| Post-M2 | 16 | prototype + write-a-skill |
| Post-M3 | 16 | (no skill changes, audit doc + version bump only) |

## File Paths to Modify (M1 — grill-with-docs)

| Path | Operation |
|------|-----------|
| `claude-code/skills/grill-with-docs/SKILL.md` | Create (forked from upstream) |
| `claude-code/skills/grill-with-docs/CONTEXT-FORMAT.md` | Create (forked from upstream) |
| `claude-code/skills/grill-with-docs/ADR-FORMAT.md` | Create (forked from upstream) |
| `claude-code/commands/aa-ma-plan.md` | Edit Phase 1.3 (conditional + flag) |
| `claude-code/rules/aa-ma.md` | Edit (mention grill-with-docs in Phase 1.3 ref) |
| `docs/adr/0002-grill-with-docs-adoption.md` | Create |
| `docs/adr/INDEX.md` | Edit (register ADR-0002) |
| `CLAUDE.md` | Edit (skill list 13 → 14) |
| `SECURITY.md` | Edit (skill list 13 → 14) |
| `tests/skills/test_grill_with_docs_frontmatter.py` | Create |
| `tests/hooks/install_dry_run.bats` | Create or extend |

## File Paths to Modify (M2 — prototype + write-a-skill)

| Path | Operation |
|------|-----------|
| `claude-code/skills/prototype/SKILL.md` | Create (forked from upstream) |
| `claude-code/skills/prototype/LOGIC.md` | Create (forked from upstream) |
| `claude-code/skills/prototype/UI.md` | Create (forked from upstream) |
| `claude-code/skills/write-a-skill/SKILL.md` | Create (forked from upstream) |
| `claude-code/rules/engineering-standards.md` | Edit (Theme 1 cross-ref to Skill(prototype)) |
| `docs/adr/0003-prototype-adoption.md` | Create |
| `docs/adr/0004-write-a-skill-adoption.md` | Create |
| `docs/adr/INDEX.md` | Edit (register ADR-0003 and ADR-0004) |
| `CLAUDE.md` | Edit (skill list 14 → 16) |
| `SECURITY.md` | Edit (skill list 14 → 16) |
| `tests/skills/test_prototype_frontmatter.py` | Create |
| `tests/skills/test_write_a_skill_frontmatter.py` | Create |

## File Paths to Modify (M3 — audit doc + version bump)

| Path | Operation |
|------|-----------|
| `docs/research/_inventories/mattpocock-inventory.json` | Move from `.claude/dev/active/skill-ecosystem-integration/` |
| `docs/research/_inventories/gstack-inventory.json` | Move from `.claude/dev/active/skill-ecosystem-integration/` |
| `docs/research/_inventories/gsd-inventory.json` | Move from `.claude/dev/active/skill-ecosystem-integration/` |
| `docs/research/skill-ecosystem-audit.md` | Create |
| `CONTEXT.md` (root) | Create only if M3.3 introduces canonical terms not yet defined |
| `pyproject.toml` | Edit (version 0.5.0 → 0.6.0) |
| `CHANGELOG.md` | Edit (add comprehensive v0.6.0 section) |
| `docs/spec/aa-ma-quick-reference.md` | Edit (Phase 1.3 grill-mode flag mention) |

## Upstream Sources (Read-Only References)

| Source | Canonical URL | On-Disk Location | Verified | Used For |
|--------|---------------|------------------|----------|----------|
| `grill-with-docs` (upstream skill) | github.com/mattpocock/skills/skills/engineering/grill-with-docs | `~/.claude/skills/grill-with-docs/{SKILL.md, CONTEXT-FORMAT.md, ADR-FORMAT.md}` | Yes — gh api fetch matches local MD5 | Fork into our `claude-code/skills/` (M1) |
| `mattpocock/skills` repo (full) | https://github.com/mattpocock/skills | (no full local clone — fetch via gh api as needed) | Yes — root contents listed via `gh api`, 17 production skills enumerated | M2 audit research (authoritative source) |
| `gstack` ecosystem | (checked CLAUDE.md disposition guide) | `~/.claude/skills/gstack/` | Partial — local install verified; some agent-cited names invented | M2 audit research only |
| `get-shit-done` | github.com/gsd-build/get-shit-done | `~/.claude/get-shit-done/` | Local install verified | M2 audit pattern extraction (inspiration only — ship nothing direct) |
| `anthropic-agent-skills` (different from mattpocock) | https://github.com/anthropics/skills | `~/.claude/plugins/cache/anthropic-agent-skills/` | Yes — separate from mattpocock | Reference only; NOT the source of grill-with-docs |

## mattpocock/skills Catalog (verified 2026-05-10 via `gh api`)

**Engineering (10 production):** `diagnose`, `grill-with-docs`, `improve-codebase-architecture`, `prototype`, `setup-matt-pocock-skills`, `tdd`, `to-issues`, `to-prd`, `triage`, `zoom-out`

**Productivity (3 production):** `caveman`, `grill-me`, `write-a-skill`

**Misc (4 production):** `git-guardrails-claude-code`, `migrate-to-shoehorn`, `scaffold-exercises`, `setup-pre-commit`

**Deprecated (4 — exclude):** `design-an-interface`, `qa`, `request-refactor-plan`, `ubiquitous-language` (conceptual ancestor of `grill-with-docs`)

**In-progress (4 — exclude):** `handoff`, `writing-beats`, `writing-fragments`, `writing-shape`

**Personal (2 — exclude):** `edit-article`, `obsidian-vault`

**Adoption-relevant subset for M3+ candidates** (see context-log for rationale):
- `prototype` — direct match to engineering-standards `Prototype-Required: YES`
- `tdd` — operationalises Theme 2 of engineering-standards
- `diagnose` — diff against aa-ma-forge `debugging-strategies` skill
- `caveman` — diff against aa-ma-forge `token-compression` skill
- `to-prd` — candidate Phase 2.5 of /aa-ma-plan
- `to-issues` — candidate post-Phase-4 export of plan tasks to GitHub/GitLab issues
- `git-guardrails-claude-code` — diff against aa-ma-forge commit-signature + commit-drift hooks
- `write-a-skill` — canonical skill-authoring workflow (relevant if/when aa-ma-forge ships new skills)
- `triage` — conceptual fit with HITL/AFK/SOFT/HARD gating

## Lineage: aa-ma-forge `/grill-me` ← mattpocock `productivity/grill-me`

aa-ma-forge's `/grill-me` command (`claude-code/commands/grill-me.md`, 42 lines) is a derivative extension of mattpocock's productivity/grill-me (frontmatter + 4 lines). aa-ma-forge added: explicit protocol numbering (1–5), constraint list, "Resolve don't just surface" rule, "Know when to stop" rule. The relationship is **derived-from with extensions**, not "two independent skills".

## install.sh Behavior (verified at planning)

- Skills are **auto-discovered** by `install.sh` line 266: `for d in "${REPO_ROOT}/claude-code/skills/"*/`. **No edit to install.sh required for the new skill itself.**
- `create_symlink` removes stale symlinks before linking. `collect_backup_target` backs up real files (non-symlinks) before replacement.
- `scripts/uninstall.sh` ships in repo for clean rollback.

## Engineering Standards Critical-Path Enum (Canonical Values)

| Value              | Applies When |
|--------------------|--------------|
| `auth-flow`        | NO (this plan does not touch auth) |
| `data-xform`       | NO |
| `external-api`     | NO |
| `version-pipeline` | YES (M1.9) |
| `doc-count-drift`  | YES (M1.5, M1.6) |
| `hook-modification`| NO (existing hooks not modified) |

## Test Commands (verified)

```bash
uv run pytest                 # Default suite (skips perf, slow)
uv run pytest -m perf         # Perf suite (codemem M1)
uv run pytest -m slow         # Slow property tests
uv run ruff check src/
uv run ruff format src/
bash scripts/install.sh --dry-run
bash scripts/install.sh
bash scripts/uninstall.sh
```

## Hook Bypass Markers (per CLAUDE.md)

- `[ad-hoc]` — for plan-unrelated housekeeping commits during this plan (e.g., the initial AA-MA scaffold commit before branch-cut).
- `[no-sync-check]` — skip post-commit drift detector for one commit.
- `[AA-MA Plan] skill-ecosystem-integration .claude/dev/active/skill-ecosystem-integration` — required footer on plan-related commits.
- `AA_MA_HOOKS_DISABLE=1` — emergency master kill switch.

## Skill Count Audit (current state, pre-M1)

13 skills directories in `claude-code/skills/`:
1. aa-ma-execution
2. aa-ma-plan-workflow
3. agent-teams
4. complexity-router
5. debugging-strategies
6. defense-in-depth
7. dispatching-parallel-agents
8. impact-analysis
9. operational-constraints
10. plan-verification
11. retro
12. system-mapping
13. token-compression

**Post-M1 target:** 14 (add `grill-with-docs`).

## ADR Convention (verified)

- Index at `docs/adr/INDEX.md`
- Template at `docs/adr/TEMPLATE.md`
- Existing ADR: `0001-engineering-standards-architecture.md`
- Next: `0002-grill-with-docs-adoption.md`

## Grill Protocol Decision Matrix (canonical for Phase 1.3)

| Project state | Default `--grill-mode=auto` resolves to |
|---------------|-----------------------------------------|
| `CONTEXT.md` exists OR `docs/adr/` exists | `with-docs` (invoke grill-with-docs) |
| Neither exists | `simple` (existing /grill-me protocol) |

User overrides:
- `--grill-mode=with-docs` → force grill-with-docs (creates CONTEXT.md/docs/adr/ lazily)
- `--grill-mode=simple` → force /grill-me regardless of project state
- `--grill-mode=skip` → bypass Phase 1.3 entirely (parallel to existing `--skip-lessons`)
- `AA_MA_GRILL_MODE` env var (same values) — config-file friendly alternative

## Project-Index Available

`PROJECT_INDEX.json` exists (129.1K). Available MCP tools: `who_calls`, `blast_radius`, `dependency_chain`, `search_symbols`, `file_summary`, `dead_code`. Use these instead of full repo greps where applicable.
