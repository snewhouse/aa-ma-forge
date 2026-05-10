# skill-ecosystem-integration Context Log

## [2026-05-10] Initial Context

**Feature Request:**
> User updated and added three skill ecosystems: (1) https://github.com/mattpocock/skills → really turned out to be Anthropic's `anthropic-agent-skills` marketplace catalog (mattpocock-curated/aligned), (2) gstack updates, (3) https://github.com/gsd-build/get-shit-done. User asked for: (a) ensure aa-ma-forge uses `grill-with-docs`; (b) audit what else aa-ma-forge can adopt from these three sources. Strict constraints: apply Socratic + first principles; use sub-agents/agent-teams as needed; don't break anything; AskUserQuestions and brainstorm and grill-with-docs as needed.

**Scoping decisions captured via `AskUserQuestion`:**
- Session scope: **Plan + ship grill-with-docs only.** Broader audit becomes M2+ for later.
- Integration model: **Both — fork as standalone skill AND wire into /aa-ma-plan Phase 1.3** (recommended option).
- gsd boundary: **Inspiration only — extract patterns, ship nothing direct from gsd**.
- Branch strategy: **New feature branch** `feature/skill-ecosystem-integration` cut from main.

**Key Design Decisions:**

1. **Fork-not-reference for grill-with-docs.** Lifting the upstream skill into `claude-code/skills/grill-with-docs/` (single source of truth via install.sh symlink) is preferred over a wrapper that defers to the upstream. Rationale: aa-ma-forge customers may not have the upstream installed; install.sh symlinks the plugin's own copy unambiguously; the upstream is small (~3 files) so drift cost is low.

2. **Phase 1.3 conditional, not replacement.** `/grill-me` is preserved. New `--grill-mode={auto,with-docs,simple,skip}` flag (auto is default). Conditional bash detects `CONTEXT.md` / `docs/adr/` presence to choose between grill-with-docs and the existing /grill-me protocol. Greenfield projects retain current behavior.

3. **gsd is competing methodology — keep separate.** gsd has its own complete planning/execution stack (60+ workflows, own templates, own subagents, "phases/PLAN.md/ROADMAP.md" lexicon). Adopting wholesale would fragment AA-MA's just-shipped engineering-standards doctrine (v0.5.0). Decision: extract patterns as research only, ship nothing direct from gsd in this plan.

4. **anthropic-agent-skills mostly orthogonal.** Phase 3 audit confirmed these are *output* skills (docx/pdf/pptx/xlsx, design, brand) — orthogonal to aa-ma-forge's meta-tooling mission. The two highly-relevant ones are `skill-creator` and `mcp-builder`; both are referenced in M2 as M3+ candidates, not adopted in this plan.

5. **doc-count-drift Critical-Path triggered.** Adding the new skill changes the skill count 13 → 14 across `SECURITY.md` (and possibly `CLAUDE.md`, README, etc.). Step 1.5 + 1.6 explicitly handle this via `grep -r "13 skills"` until clean.

6. **ADR-0002 warranted.** Per grill-with-docs's own three-test rule for ADRs: hard-to-reverse-ish (cross-references everywhere), surprising-without-context (forked from upstream — future readers will ask why), genuine trade-off (alternatives existed: replace /grill-me, reference upstream, keep grill-with-docs out entirely).

**Research Findings (Phase 3 — three parallel agents):**

- **mattpocock/anthropic-agent-skills audit** (Explore agent): Source is Anthropic's official agent-skills catalog (not literally mattpocock's GitHub repo). 16 document-skills surveyed. HIGHLY RELEVANT: `skill-creator`, `mcp-builder`. PARTIALLY RELEVANT: `internal-comms`, `doc-coauthoring`. ORTHOGONAL: 12 output/design skills. Zero overlaps with aa-ma-forge's existing 13 skills.

- **gstack audit** (Explore agent): Surveyed `~/.claude/skills/gstack/`. ⚠️ Agent invented a few skill names (`/canary-rollback`, `/setup-deploy`, `/design-systems`) — must verify in M2.1 against actual filesystem before any audit doc is published. Verified live skills: `/browse`, `/plan-{ceo,eng,design}-review`, `/design-consultation`, `/review`, `/qa{-only,-design-review}`, `/retro`, `/document-release`, `/ship` (DO NOT USE confirmed), `/setup-browser-cookies` (SKIP confirmed). Top adoption candidates for future plans: `/autoplan` (if real), `/investigate` (if real). M2 will verify.

- **gsd pattern extraction** (Explore agent): 7 patterns identified. Top 3 fits for AA-MA: (a) Optional Spec Templates (additive, low-risk); (b) Auto/Headless Execution (already partly in AA-MA via `Mode: AFK` field); (c) Specialized Phase-Type Architecture (high-value but invasive). 5 explicit "DO NOT BORROW" terminology fragments documented (ROADMAP.md, phase numbering, PLAN.md singular root, SUMMARY.md, gsd-* agent names).

**Lessons Scan Result:**
- No `docs/lessons.md` at project root (no project-local lessons file).
- Recent revert/fix/hotfix commits (last 6mo) reviewed — all are operational fixes (HARD gate anchoring, codemem benchmarks, version pipeline). None directly relevant to skill-ecosystem integration.
- Top-3 most-recent completed plans: aa-ma-engineering-standards (just merged), codemem-token-benchmarks, codemem-benchmark-fairness-v2. Engineering-standards plan's pattern of "rules-only doctrine + skill integration + hook hardening" is the most relevant precedent — same pattern applies here (skill addition + command edit + ADR + version bump).

**Engineering Standards Declaration:**
All 6 themes apply (selected option [A]).
- Theme 1: empirical Phase 1.3 verification required.
- Theme 2: TDD on the SKILL.md frontmatter test; KISS conditional.
- Theme 3: Socratic check completed; subagent dispatches recorded.
- Theme 4: strictly additive; existing /grill-me preserved.
- Theme 5: HARD checks for non-breaking + sync + Critical-Path evidence.
- Theme 6: sub-step Result Logs mandatory; HARD gate at milestone close.

**Remaining Open Questions:**
- None at planning time. Will surface during execution if scope drifts.

**Verification Skipped (user discretion):**
- Phase 4.5 adversarial verification not run (scope is tightly bounded, mechanics are well-understood). Re-runnable later via `/verify-plan skill-ecosystem-integration` if confidence drops during execution.

**Scribe Note:**
This planning session applied grill-with-docs discipline informally: cross-referenced code (verified install.sh auto-discovery, ADR existence, hardcoded counts in SECURITY.md); invented edge cases (upstream-installed conflict, doc-count-drift, greenfield fallback). M1 implementation must invoke `Skill(grill-with-docs)` for design decisions in step 1.3 (the conditional logic).

---

## [2026-05-10] CORRECTION — mattpocock/skills attribution

**What was wrong:** The original Phase 3 audit dispatched an Explore agent with a brief that said "look at locally-installed `document-skills:*`" but did NOT pass the canonical URL `https://github.com/mattpocock/skills`. The agent looked at `~/.claude/plugins/cache/anthropic-agent-skills/` and concluded "this is Anthropic's catalog, not mattpocock". The conclusion was inserted into the original plan's M2 description and Assumption A5 verbatim ("Anthropic agent-skills (mattpocock-curated)"). User caught it and demanded a re-work.

**Ground truth (now verified via `gh api repos/mattpocock/skills`):**

`https://github.com/mattpocock/skills` is a real, active repo (68,425 stars, last updated 2026-05-10T09:41:10Z, default branch `main`, description "Skills for Real Engineers. Straight from my .claude directory."). It contains 17 production skills + 4 deprecated + 4 in-progress + 2 personal. Published catalog:

**Engineering (10 production skills):**
1. `diagnose` — Disciplined diagnosis loop (reproduce → minimise → hypothesise → instrument → fix → regression-test). Strong overlap with aa-ma-forge's `debugging-strategies` skill (need diff).
2. `grill-with-docs` — *Already the M1 target.* Confirmed canonical source — local `~/.claude/skills/grill-with-docs/` MD5s match my Phase 5 fetch.
3. `improve-codebase-architecture` — Architecture refactoring loop.
4. `prototype` — Throwaway prototype with two branches (LOGIC for state-machines, UI for visual variations). **Direct match to engineering-standards `Prototype-Required: YES` field — high adoption value.**
5. `setup-matt-pocock-skills` — Configuration scaffolding (canonical install/config flow for the whole catalog).
6. `tdd` — TDD loop. **aa-ma-forge engineering-standards Theme 2 already mandates TDD; this skill is the operational "how" — could enrich Theme 2 doctrine.**
7. `to-issues` — Breaking specs into tasks.
8. `to-prd` — Converting discussions to requirements (PRD generation). **Could be Phase 2.5 of /aa-ma-plan — output a PRD before the 12-element plan.**
9. `triage` — Issue state machine workflow. **Conceptual overlap with AA-MA HITL/AFK/SOFT/HARD gating.**
10. `zoom-out` — Contextual code explanation.

**Productivity (3 production):**
11. `caveman` — Token-compressed communication mode (~75% token savings via filler/article drop). **Direct functional overlap with aa-ma-forge's `token-compression` skill — need diff.**
12. `grill-me` — **The original short version (frontmatter + 4 lines)**. aa-ma-forge's `/grill-me` *command* is a much longer derivative (42-line protocol). The relationship is "aa-ma-forge extended the canonical mattpocock /grill-me into a richer protocol".
13. `write-a-skill` — Skill creation framework (mattpocock's canonical skill-authoring workflow).

**Misc (4 production):**
14. `git-guardrails-claude-code` — Git safety hooks. **Functional overlap with aa-ma-forge's commit-signature + commit-drift hooks — should compare.**
15. `migrate-to-shoehorn` — Test migration utility (specific to mattpocock's tooling).
16. `scaffold-exercises` — Exercise structure generation.
17. `setup-pre-commit` — Commit hook configuration.

**Deprecated (4):** `design-an-interface`, `qa`, `request-refactor-plan`, `ubiquitous-language` (the latter is the conceptual ancestor of `grill-with-docs`).

**In-progress (4):** `handoff`, `writing-beats`, `writing-fragments`, `writing-shape` (NOT stable — exclude from adoption).

**Personal (2):** `edit-article`, `obsidian-vault` (mattpocock's personal use — exclude).

**Implications for the plan:**
- M2 audit doc (`docs/research/skill-ecosystem-audit.md`) MUST use this corrected catalog as the authoritative starting point. The previous "anthropic-agent-skills (mattpocock-curated)" framing is wrong and removed.
- Several skills warrant explicit M3+ adoption analysis: `prototype` (matches `Prototype-Required:`), `tdd` (Theme 2 enrichment), `diagnose` (vs `debugging-strategies`), `caveman` (vs `token-compression`), `to-prd` (Phase 2.5 candidate), `git-guardrails-claude-code` (vs our hooks), `write-a-skill` (canonical skill-authoring workflow).
- aa-ma-forge's `/grill-me` is **derived from** mattpocock's productivity/grill-me (extended into a 42-line command). The audit must record this lineage to avoid future re-discovery.

**Lesson committed:** New `docs/lessons.md` L-001 ("External URL First Principle") + new auto-memory entry capture the failure mode. From now on, any user-named external URL is fetched directly before any agent delegation.

---

## [2026-05-10] SCOPE EXPANSION v1.2 — three-milestone restructure

**User decision** (via AskUserQuestion after re-fetching all three ecosystems via canonical `gh api`): "M1 expanded: ship grill-with-docs + prototype + (caveman OR write-a-skill)".

**Caveman vs write-a-skill discriminator (decisive finding):**

I read the existing aa-ma-forge `claude-code/skills/token-compression/SKILL.md` and discovered a citation:
> "Inspired by [caveman](https://github.com/JuliusBrussee/caveman) prompt compression patterns, adapted for AA-MA execution mode integration."

The local `token-compression` skill has 3 intensity levels (lite/full/ultra) mapped to AA-MA execution modes (HITL/general/AFK), with auto-activation rules. **It is strictly more capable than mattpocock's caveman** (which is single-mode persistent). Adopting mattpocock's caveman would create redundancy — it's superseded by what we already have.

**Conclusion: pick `write-a-skill`** — aa-ma-forge has no native skill-authoring framework, and write-a-skill is mattpocock's canonical pattern (single 3KB SKILL.md file, well-respected via 68k repo stars).

**Three new milestones (replacing the v1.1 two-milestone structure):**
- **M1**: Adopt grill-with-docs (was v1.1's M1, mostly unchanged but version bump removed)
- **M2**: Adopt prototype + write-a-skill (NEW — both from mattpocock; reuses fork+test+ADR pattern from M1)
- **M3**: Audit research note + single 0.5.0 → 0.6.0 version bump (was v1.1's M2, expanded with version-pipeline Critical-Path moved here)

**Why single version bump at M3 close:**
- Atomic release semantics — one tag covers all 3 skill additions + audit doc
- Minimises release churn (v1.0 plan had 1 bump, this still has 1 bump despite expanded scope)
- M1 and M2 milestone closes commit changes but don't tag; M3.5 is the version-pipeline Critical-Path

**Critical-Path expansion:**
- M1.5, M1.6: doc-count-drift (skill count 13 → 14)
- M2.6, M2.7: doc-count-drift (skill count 14 → 16) — NEW
- M3.5: version-pipeline (single 0.5.0 → 0.6.0 bump) — moved from old M1.9

**Cross-language assessment for prototype** (user asked: "is matt's prototype applicable for our python and future java or typescript projects?"):
- LOGIC branch: **fully cross-language** — SKILL.md says "Pick the language: Use whatever the host project uses"; LOGIC.md shows ANSI escape examples for JS (`console.clear()`), Python (`print("\033[2J\033[H")`), and "equivalent"; run-command examples cover `pnpm`/`python`/`bun`/`Makefile`/`justfile`/`pyproject.toml`. Works for Python, TypeScript, Java, Rust, Go.
- UI branch: **web-frontend specific** — uses TSX, `searchParams.get('variant')`, `process.env.NODE_ENV`. Works for any web framework but assumes a browser-renderable surface. Not for backend-only services or pure data pipelines.
- For aa-ma-forge: LOGIC fits everywhere (Python codemem, future TS/Java backends); UI fits when prototyping web surfaces (galactic-agent UI, biorelate dashboards).

**Strategic fit insight:** prototype skill **directly operationalises** existing engineering-standards.md Theme 1 rule — we have the `Prototype-Required: YES` enum field but no prescribed "how". Adopting prototype means agents now have a structured branching skill to execute, not just an instruction. ADR-0003 will document the LOGIC-vs-UI constraint matrix.

**Inventory JSONs verified and saved during planning:**
- `inventory-mattpocock.json` (17 production + 4 deprecated + 4 in-progress + 2 personal; lineage maps recorded)
- `inventory-gstack.json` (34 canonical commands per README + 12 additional with SKILL.md only; 21 candidates needing disposition assessment)
- `inventory-gsd.json` (90 workflows + 36 templates; 6 patterns for AA-MA inspiration; 6 explicit DO-NOT-BORROW items)

These will be moved to `docs/research/_inventories/` during M3.1 (relocation, not re-fetch).

---

## [2026-05-10] GATE APPROVAL: Milestone M1 — Adopt grill-with-docs

- **Gate:** HARD
- **Approved by:** Stephen Newhouse (via AskUserQuestion HARD gate at 2026-05-10T15:43)
- **Criteria verified:** 6/6
  1. ✓ All sub-steps 1.1–1.8 marked COMPLETE with concrete Result Logs (Task 1.1 complete in prior session; 1.2–1.7a + 1.8 completed this session, each with bullet-point Result Log evidence including specific commit hashes, test counts, file counts)
  2. ✓ `git status` clean for AA-MA files at finalization (verified `git status --short .claude/dev/active/skill-ecosystem-integration/` returns empty before this commit)
  3. ✓ Zero `Status: PENDING` within M1 (verified `awk '/^## Milestone M1:/,/^## Milestone M2:/' tasks.md | grep -cE '^- Status: PENDING'` returns only Task 1.9 itself, which is the closing task — flips to COMPLETE in this commit)
  4. ✓ `provenance.log` IMPACT_ANALYSIS entry: written in this commit (consolidated impact analysis for all 16 modified files; Overall Risk: LOW; non-breaking constraint structurally verified — `git diff main..HEAD -- claude-code/commands/grill-me.md` empty)
  5. ✓ `provenance.log` doc-count-drift CRITICAL_PATH_REVIEW entry: 2 entries present (M1.5 at 15:25, M1.6 at 15:29 — final M1 sweep)
  6. ✓ Milestone-close commit with `[AA-MA Plan] skill-ecosystem-integration .claude/dev/active/skill-ecosystem-integration` footer: this commit
- **Decision:** APPROVED
- **Artifacts shipped:**
  - 3 forked skill files at `claude-code/skills/grill-with-docs/{SKILL.md, CONTEXT-FORMAT.md, ADR-FORMAT.md}` (MD5-verified clean diff vs upstream)
  - `scripts/grill-mode-resolver.sh` (105 lines, executable, 8-branch coverage)
  - `claude-code/commands/aa-ma-plan.md` Phase 1.3 expanded from 4-line single-protocol to 75-line mode-aware dispatcher
  - `docs/adr/0002-grill-with-docs-adoption.md` (150 lines, MADR style) + INDEX row 2
  - `tests/skills/test_grill_with_docs_frontmatter.py` (4 cases) + `tests/commands/test_grill_mode_resolver.py` (13 cases) + `tests/hooks/install_dry_run.bats` (4 cases) = 21 new test cases, ALL PASS
  - `SECURITY.md` skill count 13→14 with grill-with-docs alphabetical
  - `docs/spec/claude-code-foundations.md` skills heading + new row
  - `CLAUDE.md` line 48 (gitignored — local edit recorded)
- **Regression:** 437 pytest + 58 bats green; /grill-me command file unchanged on branch; greenfield projects retain identical v0.5.0 behavior (auto → simple → /grill-me protocol)
- **Critical-Path:** doc-count-drift fully discharged for skill count 13→14 transition; M2 will re-discharge for 14→16
- **Skill count post-M1:** 14 (matches disk reality + SECURITY.md + foundations.md)
- **Next:** Begin M2 (prototype + write-a-skill adoption), reusing the fork+test+ADR pattern established here.

---

## [2026-05-10] GATE APPROVAL: Milestone M2 — Adopt prototype + write-a-skill

- **Gate:** HARD
- **Approved by:** Stephen Newhouse (via AskUserQuestion HARD gate at 2026-05-10T16:30)
- **Criteria verified:** 6/6
  1. ✓ All sub-steps 2.1–2.9 marked COMPLETE with concrete Result Logs (each Result Log includes specific commit hashes, file counts, test counts, MD5 verifications, plan-gap discoveries)
  2. ✓ `git status` clean for AA-MA files at finalization (verified `git status --short .claude/dev/active/skill-ecosystem-integration/` returns empty before this commit)
  3. ✓ Zero `Status: PENDING` within M2 (verified `awk '/^## Milestone M2:/,/^## Milestone M3:/' tasks.md | grep -cE '^- Status: PENDING'` returns 1 — Task 2.10 itself, which is the closing task — flips to COMPLETE in this commit)
  4. ✓ `provenance.log` IMPACT_ANALYSIS entry: written in this commit (consolidated impact analysis for all 16 files modified vs M1-close commit 3e8ba4e; Overall Risk: LOW; non-breaking constraint structurally verified — `git diff main..HEAD -- claude-code/commands/grill-me.md` empty across both M1 + M2)
  5. ✓ `provenance.log` doc-count-drift CRITICAL_PATH_REVIEW entry: 2 entries present (M2.6 at 16:13, M2.7 final-sweep at 16:14)
  6. ✓ Milestone-close commit with `[AA-MA Plan] skill-ecosystem-integration .claude/dev/active/skill-ecosystem-integration` footer: this commit
- **Decision:** APPROVED
- **Artifacts shipped:**
  - 4 forked skill files at `claude-code/skills/prototype/{SKILL.md, LOGIC.md, UI.md}` (3251B + 5594B + 6789B, MD5-verified clean diff vs upstream) + `claude-code/skills/write-a-skill/SKILL.md` (3057B post-typo-fix)
  - `claude-code/rules/engineering-standards.md` Theme 1 extended with `Skill(prototype)` cross-reference + ADR-0003 link + LOGIC/UI dispatch hint (SOFT cross-ref; HARD gate Section 6.7 condition 5 behavior unchanged)
  - `docs/adr/0003-prototype-adoption.md` (145 lines, MADR style — operationalises Theme 1 `Prototype-Required:` flag) + `docs/adr/0004-write-a-skill-adoption.md` (147 lines — meta-tooling for skill authoring)
  - `tests/skills/_helpers.py` (DRY refactor: `split_frontmatter` + `assert_skill_frontmatter` shared helper) + 2 new frontmatter test files (`test_prototype_frontmatter.py`, `test_write_a_skill_frontmatter.py`); M1's `test_grill_with_docs_frontmatter.py` refactored to use helper (regression-verified)
  - `SECURITY.md` skill count 14→16 with prototype + write-a-skill alphabetical
  - `docs/spec/claude-code-foundations.md` heading "Skills (16)" + 2 new skills-table rows
  - `CLAUDE.md` line 48 (gitignored — local edit only)
  - `tests/hooks/install_dry_run.bats` skill-count assertion made dynamic (compares against actual disk count) — future-proof against all skill additions
  - `docs/lessons.md` L-002 + L-003 committed (planning-output durability)
- **Regression:** 439 pytest + 58 bats green; /grill-me command file UNCHANGED across BOTH M1 + M2; Engineering Standards Theme 1 cross-reference is SOFT (no HARD gate behavior change); greenfield projects retain identical v0.5.0 behavior via M1's auto → simple → unchanged /grill-me path
- **Critical-Path:** doc-count-drift fully discharged for skill count 14→16 transition; M3 has no skill additions (audit doc + version bump only)
- **Skill count post-M2:** 16 (matches disk reality + SECURITY.md + foundations.md)
- **Plan-gaps documented for /verify-plan future runs:** (a) plan reference.md path inventory should flag CLAUDE.md as gitignored (M1 finding); (b) M2.7 doc-count-drift grep gate should include `tests/` directory (M2.9 inline fix); (c) docs/spec/claude-code-foundations.md was not in M1's path inventory but contained "Skills (13)" heading — handled inline in M1.5
- **Next:** Begin M3 (audit research note + comprehensive 0.5.0 → 0.6.0 single version bump covering all 3 milestones).
