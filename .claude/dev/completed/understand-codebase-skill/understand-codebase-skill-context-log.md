# understand-codebase-skill Context Log

_Decision history, trade-offs, approvals, and unresolved issues for this task._

<!-- Append-only. New entries at the bottom. Date headers in [YYYY-MM-DD]. -->

---

## [2026-05-12] Plan Approved

- Plan: understand-codebase-skill
- Approved by: Stephen Newhouse
- Milestones: 3 (M1 Vendor & wire, M2 Pin with tests, M3 Document/reconcile/ship)
- HARD gates: Milestone 3 (`Gate: HARD`; `Audit-Profile: custom: code-reviewer, future-proofing-auditor` — Phase 6.8 `/verify-impl` applies because `Created: 2026-05-12` > v0.8.0 cutover `2026-05-11`)
- Complexity: ~40% overall; no step ≥ 80%
- Plan source: `~/.claude/plans/are-main-and-the-rustling-lantern.md`
- Verification (Phase 4.5): **deferred** — no `verification.md` created. Optional `/verify-plan understand-codebase-skill` may be run before execution given ~40% complexity + additive-only scope.

---

## [2026-05-12] Initial Context

**Feature Request (Phase 1):**

Vendor the `understand-codebase` skill + 4 `codebase-onboarding-*` worker agents + `/understand-codebase` command into `aa-ma-forge` as official, maintained ecosystem components. They were built ad-hoc directly inside `~/.claude/` on 2026-05-12 as real files — no version, no tests, no CI, no ADR, not symlinked from any repo. Goal: move them into `aa-ma-forge/claude-code/` so `scripts/install.sh` deploys them (replacing the loose `~/.claude/` files with symlinks, originals backed up), `pytest` pins them, CI sees them, and `python-semantic-release` versions them.

**Key Decisions (Phase 2 Brainstorming):**

- **Decision AD-001: Branch name `feature/understand-codebase-skill`.**
  - **Rationale:** Conventional `feature/<task-slug>` naming; matches the AA-MA task slug `understand-codebase-skill`. Cut from `main` (== `origin/main` == `3a90325`).
  - **Alternatives Considered:** `feat/vendor-understand-codebase` — rejected: the AA-MA task slug should match the branch slug for traceability.
  - **Trade-offs:** None material — purely a naming convention choice.

- **Decision AD-002: Vendor as-is + ADR-0006 documents the cross-plugin soft-deps.**
  - **Rationale:** The skill already degrades gracefully ("if any reused tool/agent is missing → skip, note in Provenance, never hard-fail"), so shipping it standalone — with its references to tools aa-ma-forge does *not* ship (`/index`, `/codebase-deep-dive`, `gsd-map-codebase`/`gsd-scan`/`gsd-intel`, `gsd-codebase-mapper`, `code-intelligence`, `doc-drift-detection`, `improve-codebase-architecture`, `~/.claude-code-project-index/scripts/project_index.py`) — changes no behaviour. aa-ma-forge *does* already ship the in-repo pieces it composes: `agent-teams`, `impact-analysis`, `system-mapping`, `code-reviewer`, `/aa-ma-plan`. KISS: move files verbatim, refactor nothing; `install.sh` auto-discovers so no manifest edit. ADR-0006 records the dependency posture so the surface is documented, not surprising — following the `0002-grill-with-docs` / `0003-prototype` / `0004-write-a-skill` adoption precedent.
  - **Alternatives Considered:** (a) Vendor + trim the cross-plugin refs — rejected: would fork the skill from its upstream behaviour, add maintenance burden, and lose value when those plugins *are* installed. (b) Leave it external (don't vendor) — rejected: that's the status quo we're explicitly fixing (no version/tests/CI/maintained home).
  - **Trade-offs:** Gained: single maintained source of truth, versioned + tested + CI-covered, install.sh auto-deploys, originals backed up. Sacrificed: aa-ma-forge now *names by reference* gsd/code-intelligence/codebase-deep-dive/index — accepted, mitigated by graceful degradation and documented in ADR-0006.

- **Decision AD-003: Reconcile `docs/spec/claude-code-foundations.md` asset tables fully.**
  - **Rationale:** Its Agents table is frozen pre-v0.8.0 at 2 agents; reality after this work is 11 agents / 18 skills / 10 commands. Reconciling all three asset tables to current+new reality incidentally fixes the pre-existing v0.8.0 drift — the right time to do it is now, while we're already touching the count surface.
  - **Alternatives Considered:** Only add the new `/understand-codebase` + 4 `codebase-onboarding-*` rows, leaving the rest of the v0.8.0 drift in place — rejected: half-reconciled tables are still inconsistent and the next person hits the same drift; bounded mechanical work, do it once.
  - **Trade-offs:** Gained: foundations doc is consistent end-to-end. Sacrificed: slightly larger diff in `claude-code-foundations.md` — bounded to the 3 asset tables only; the incidental v0.8.0-drift fix is called out in the commit body.

**Research Findings (Phase 3):**

- `scripts/install.sh` **auto-discovers** `claude-code/{skills/*/,agents/*.md,commands/*.md}` — confirmed by reading `scripts/install.sh` lines 113–186 and 254–265. ⇒ **No `install.sh` edit needed** when adding the new skill dir / 4 agents / command (and editing it would violate L-005 — its KISS auto-discovery already does the job).
- `scripts/install.sh` **backs up** existing real (non-symlink) `~/.claude/` targets to `~/.claude/backups/aa-ma-forge-<ts>/` *before* symlinking — backup logic at `scripts/install.sh` lines 157–186; `scripts/uninstall.sh` restores. ⇒ The user's existing `~/.claude/` copies of these 6 assets are **preserved**, not clobbered.
- The skill **degrades gracefully** — SKILL.md contract: missing reused tool/agent → skip, note in Provenance, never hard-fail. This is the load-bearing reason vendoring as-is is safe.
- `docs/spec/claude-code-foundations.md` Agents table is **stale at 2 rows** (frozen pre-v0.8.0); reality is 11 after this work. Reconcile to: existing 2 + `code-reviewer`, `security-auditor`, `tdd-sequence-auditor`, `context7-evidence-auditor`, `future-proofing-auditor`, `codebase-onboarding-conventions`, `codebase-onboarding-health`, `codebase-onboarding-runbook`, `codebase-onboarding-synthesizer` = 11.
- Next ADR number is **0006** — 0005 is the highest existing ADR.
- No other in-flight AA-MA plan touches `claude-code/skills|agents|commands/` — confirmed `.claude/dev/active/` was absent before this task.
- Skill `SKILL.md` frontmatter uses `allowed-tools:` (a YAML list) and `name: understand-codebase`. The 4 agents use `name`/`description` (`>-` block scalar); they need `tools:` (comma-separated string) normalized in to match aa-ma-forge convention if missing.
- Versioning: next release is a **minor** bump (additive feature) — `cz bump` computes it from the `feat:` commit; CHANGELOG `[Unreleased]` reconciled at release time.
- Known wrinkle (non-blocking): the Deep tier's reviewer step uses `Agent(subagent_type=code-reviewer)`; aa-ma-forge's `code-reviewer` is described in AA-MA-milestone terms but is read-only, so reuse for onboarding-doc review is harmless. Not generalized here (out of scope).

**Engineering Standards Declaration (plan element #12):**

Per `claude-code/rules/engineering-standards.md` — materially applicable themes: **1, 2, 4, 5, 6** (Theme 3 only mildly).

- **Theme 1 — Verification & Truth:** `install.sh --dry-run` before the real run; `readlink`/`[ -L ]` symlink assertions; `grep -rn` cross-ref check; `Skill(doc-drift-detection)` empirical drift verdict — every "it works" claim is backed by a command, not assertion.
- **Theme 2 — Development Principles:** TDD-flavoured (M2 writes structure/frontmatter tests that pin the vendored assets); KISS (move files verbatim, refactor nothing — `install.sh` already auto-discovers, so no manifest edit); DRY (the entire point — one maintained source of truth in `aa-ma-forge` replacing loose `~/.claude/` copies); SoC honoured (skill / agents / command / docs / tests as separate concerns).
- **Theme 4 — Safety & Continuity:** non-breaking constraint — `install.sh` backs up the existing real files; auto-discovery means zero risk of stale manifests; the skill already degrades gracefully so shipping it standalone changes no behaviour; lessons applied — L-005 (don't touch `install.sh` — its KISS auto-discovery already does the job), L-322/L-323 (be careful moving files between a config dir and a repo; the `--dry-run`-first + backup-verify steps cover this); incremental validation (M1 → M2 → M3 each verified before the next).
- **Theme 5 — Execution Checklist:** standard per-task HARD/SOFT enforcement — tests written & passing (HARD), non-breaking verified via `Skill(impact-analysis)` (HARD), AA-MA artifacts synced & git clean (HARD), `Audit-Profile` declared on M3 so Phase 6.8 `/verify-impl` runs (`code-reviewer` + `future-proofing-auditor`).
- **Theme 6 — Sync & Commit Discipline:** sub-step `Result Log:` written immediately per sub-step (never batched); M3 is `Gate: HARD` — refuses COMPLETE while git is dirty or any `Status: PENDING` remains; commit carries the `[AA-MA Plan] understand-codebase-skill .claude/dev/active/understand-codebase-skill` footer.
- *Theme 3 — Reasoning & Planning (mild):* the one genuine design question — "should aa-ma-forge own a skill with cross-plugin soft-deps?" — was resolved first-principles ("vendor as-is; degrades gracefully; documented") and is recorded in ADR-0006; no further first-principles/Socratic work needed for this mechanical vendoring.

**Remaining Questions / Unresolved Issues:**

- Does `README.md` carry hardcoded asset counts? Resolve at step 3.5 — if no counts and no natural commands list, no change needed.
- Are there *other* skills missing from the foundations Skills table besides `verify-impl`? Resolve at step 3.3 by enumerating `claude-code/skills/` against the table.
- Phase 4.5 plan verification was deferred (not skipped permanently) — user may choose to run `/verify-plan understand-codebase-skill` before M1.2.

---

## [2026-05-12] M1–M3 Execution + Impact Analysis (pre-gate)

**M1 (Vendor & wire) — COMPLETE (Gate SOFT).** Branch `feature/understand-codebase-skill` cut from `main` @ `3a90325`. `cp -a` vendored `claude-code/skills/understand-codebase/` (11 files), `claude-code/agents/codebase-onboarding-{conventions,health,runbook,synthesizer}.md` (4), `claude-code/commands/understand-codebase.md` (1). SKILL.md L1 provenance comment added. The 4 agents already conformed (`name`/`description`/`tools`) — **no normalization needed** (Phase-3 prediction that they "might need `tools:` added" turned out moot). `scripts/install.sh --dry-run` reviewed → `scripts/install.sh` for real: exit 0, 51 symlinks / 5 copies / 11 backups / 38 stale removed; originals preserved at `~/.claude/backups/aa-ma-forge-20260512-160044/`; all 6 `~/.claude/` targets now symlink into the repo.

**M2 (Pin with tests) — COMPLETE (Gate SOFT).** Added `tests/skills/test_understand_codebase_frontmatter.py` (4 tests), `tests/agents/__init__.py` + `tests/agents/test_codebase_onboarding_agents.py` (10 parametrized), `tests/commands/test_understand_codebase_command.py` (4), `tests/assets/__init__.py` + `tests/assets/test_understand_codebase_xrefs.py` (2 — step 2.4 implemented, not skipped). New suite: 20 passed. Full `uv run pytest -q`: 608 passed, 1 skipped (pre-existing), 6 deselected — **0 regressions**. (Reuse note: skill test imports `_helpers.split_frontmatter`; agents/commands/assets tests use small inline frontmatter parsers — cross-package test imports kept minimal by design.)

**M3 (Document, reconcile, ship) — work done; commit pending HARD gate.**
- 3.1 `docs/adr/0006-understand-codebase-adoption.md` written from `TEMPLATE.md` (Status: Implemented; chosen option = vendor as-is + document soft-deps; full pros/cons + consequences + implementation notes); `docs/adr/INDEX.md` row 0006 added.
- 3.2 Count bumps: `SECURITY.md` (commands 9→10 +understand-codebase; skills 17→18 +understand-codebase; agents 7→11 +4 codebase-onboarding-*; **incidental fix:** "4→5 spec docs" — `plan-marker-grammar.md` was already being copied but not listed). `CLAUDE.md` also edited (9→10 / 17→18 / 7→11) — **DEVIATION:** `CLAUDE.md` is `.gitignored` in this repo (`.gitignore` line 2 — maintainer-local file, not shipped), so that edit is local-only and will NOT be committed. The *shipped* canonical inventory is `SECURITY.md` + `docs/spec/claude-code-foundations.md`, both updated. (The system-prompt header calling CLAUDE.md "checked into the codebase" is inaccurate for this repo.) Force-adding a gitignored file would be wrong — left as-is.
- 3.3 `docs/spec/claude-code-foundations.md` reconciled **fully**: Commands 9→10 (+`/understand-codebase`); Skills 16→18 (+`verify-impl` — the v0.8.0 omission — and +`understand-codebase`); Agents 2→11 (+5 v0.8.0 audit agents +4 codebase-onboarding-*); Hooks 2→8 (+6: commit-signature, commit-drift, session-end-dirty, plan-skip-warn, plan-marker, security-static-check). Incidental v0.7.0/v0.8.0 drift fix — called out for the commit body.
- 3.4 `docs/spec/aa-ma-quick-reference.md` — `/understand-codebase [path] [--quick|--standard|--deep]` added to the commands cheat-sheet.
- 3.5 `README.md` — `/understand-codebase` row added to the "All commands" table (now 10). README "Skills" table left as-is (it is already a non-exhaustive curated subset — missing verify-impl/grill-with-docs/prototype/write-a-skill predates this change; fully reconciling it is out of scope — foundations doc is the canonical inventory). Also noted-but-not-fixed (pre-existing, out of scope): README line 37 "templates for all 7 file types" (now 8) and line ~306 "ships five hooks" (now 8).
- 3.6 `CHANGELOG.md` — `## [Unreleased]` section added with `### Feat` (vendoring) + `### Docs` (foundations reconcile + count bumps) entries.
- 3.7 Cross-ref grep (`claude-code/ docs/ tests/`) → every referenced path exists; the skill's 10 `references/`+`templates/` companions all resolve; count-consistency greps (`9 command`/`17 skill`/`7 agent`/`Skills (16)`/`Hooks (2)`/`Agents (2)`/`Commands (9)`) → 0 hits (clean). No `Skill(doc-drift-detection)` formal invocation — manual Tier-1 (no version bumped; `v0.9.0` forward-refs in SKILL.md/ADR are intentional per the ADR-0002/3/4 pattern) + Tier-6 (counts) checks performed inline; no NEW drift introduced.
- 3.8 `uv run pytest -q` → 608 passed / 1 skipped / 6 deselected; `uv run ruff check src/` → all checks passed; `bats --recursive tests/hooks/` → 118 ok, 0 failures.
- 3.9 **Impact analysis (inline — `Skill(impact-analysis)` heuristics applied):** *Upstream callers* — none; all new assets are new files, no existing code touched. *Downstream / blast radius* — `src/aa_ma/` unchanged (no imports affected); `scripts/install.sh` unchanged (auto-discovers the new skill dir / 4 agents / command); `claude-code/hooks/` unchanged. The only live effect: `install.sh` now deploys 1 more command + 4 more agents + 1 more skill dir, and the maintainer's `~/.claude/` now symlinks them (originals backed up — verified M1.6). *Contract changes* — none (no function signatures, no APIs; the new prompt files are declarative). *Soft-deps* — the skill names external plugins (`gsd-*`, `/index`, `/codebase-deep-dive`, `code-intelligence`, `doc-drift-detection`, `improve-codebase-architecture`) but degrades gracefully (SKILL.md "Error handling" table; `tests/assets/test_understand_codebase_xrefs.py` asserts only the *in-repo* composed assets must exist). *Verdict:* **NON-BREAKING.** 608 tests green, 0 regressions; ruff + 118 bats green.

**Awaiting:** M3 HARD-gate approval (3.10) before commit + push.

---

## [2026-05-12] GATE APPROVAL: Milestone 3 — Document, reconcile counts, ship

- Gate: HARD
- Approved by: Stephen Newhouse (via AskUserQuestion — "Approve — commit & push now")
- Criteria verified: ADR-0006 + INDEX row present ✓ · counts consistent 10/18/11 across SECURITY.md + claude-code-foundations.md (CLAUDE.md edited locally but `.gitignored` — documented deviation) ✓ · foundations Commands/Skills/Agents/Hooks tables reconciled (9→10 / 16→18 / 2→11 / 2→8) ✓ · `/understand-codebase` in aa-ma-quick-reference.md ✓ · CHANGELOG `## [Unreleased]` Feat+Docs ✓ · cross-ref grep clean (all referenced paths exist; 10/10 skill companions resolve) ✓ · `uv run pytest` 608 passed / 0 regressions ✓ · `ruff check src/` clean ✓ · `bats --recursive tests/hooks/` 118 ok / 0 failures ✓ · impact-analysis NON-BREAKING ✓ (full evidence: this context-log's `[2026-05-12] M1–M3 Execution + Impact Analysis` entry; tasks.md sub-step Result Logs; provenance.log)
- Phase 6.8 / Audit-Profile note: plan `Created: 2026-05-12` > v0.8.0 cutover `2026-05-11`, so `Audit-Profile: custom: code-reviewer, future-proofing-auditor` applies under Phase 6.8 of `/execute-aa-ma-milestone`. This plan was executed manually (within the harness plan-mode workflow), not via `/execute-aa-ma-milestone`; the user was offered the option to run `/verify-impl` (code-reviewer + future-proofing-auditor) before committing and chose "commit & push now". The future-proofing-auditor's primary concern (hardcoded-count drift, Tier 6) was already mitigated manually (count-consistency greps → 0 stale hits across all 4 surfaces). Decision: APPROVED to ship without the agent dispatch.
- Decision: **APPROVED** → commit `feat(skills): vendor understand-codebase …` (with the `[AA-MA Plan] understand-codebase-skill .claude/dev/active/understand-codebase-skill` footer) on `feature/understand-codebase-skill`; push to origin.

---

## [2026-05-12] Plan COMPLETE

All 3 milestones COMPLETE (M1 Vendor & wire — SOFT; M2 Pin with tests — SOFT; M3 Document, reconcile counts, ship — HARD, approved above). Plan delivered: `understand-codebase` skill + 4 `codebase-onboarding-*` agents + `/understand-codebase` command are now first-class, maintained AA-MA Forge components (versioned, tested, CI-checked, `install.sh`-deployed, ADR-0006). 28 new files + 6 modified docs committed & pushed on `feature/understand-codebase-skill`. Open follow-ups (not part of this plan): (1) `/archive-aa-ma understand-codebase-skill` once the branch lands; (2) optional pre-existing-drift cleanup — README "templates for all 7 file types" → 8, README "ships five hooks" → 8, README "Skills" table is a non-exhaustive subset (missing verify-impl/grill-with-docs/prototype/write-a-skill); (3) at release, `cz bump` → v0.9.0 + reconcile `## [Unreleased]` into the version section + update the `v0.9.0` forward-refs' "as of" wording if desired.

## [2026-05-13T09:26:58Z] Compaction Summary (auto-generated by hook)
- Active step at compaction: Sub-step 1.6: Verify symlinks + backups
- Snapshot saved to: /home/sjnewhouse/.claude/hooks/cache/compaction-snapshots/understand-codebase-skill-snapshot.md
- Note: Context compacted. Reload AA-MA files to resume.
