# mattpocock-trio-adoption Context Log

_This log captures architectural decisions, trade-offs, gate approvals and unresolved issues. Append-only; new entries at the bottom._

---

## [2026-09-20] Plan Approved

- Plan: mattpocock-trio-adoption
- Approved by: Stephen Newhouse (Phase 4 eng review + Phase 4.5 automated verification, PASS WITH WARNINGS)
- Milestones: 5 (+ one pre-M1 `[ad-hoc]` housekeeping commit)
- HARD gates: Milestone 3, Milestone 5
- Releases: v0.13.0 after Milestone 4, v0.14.0 after Milestone 5

---

## [2026-09-20] Initial Context

**Feature Request (Phase 1):**

Bring every mattpocock fork in `claude-code/skills/` to a known, detectable lifecycle state and adopt the three skills researched in `docs/research/mattpocock-trio-2026-09.md`: re-fork `prototype` (drifted since 2026-05-10) and make the prototype decision explicit in `/aa-ma-plan`; adopt `research` with a non-nesting background agent that writes cited files under `docs/research/`; adapt `wayfinder` as a pre-plan **charting** step (`/aa-ma-chart`, single-file decision map, handoff via `/aa-ma-plan --from-map`); fork upstream `grilling` behind the existing `grill-with-docs` name; reclassify `write-a-skill` as Derived. Ste's stated style (2026-09-20): "a big fan of prototyping and actually coding up solutions using trial and error." One memory system, one directory tree, ≤5 agents at a time. Upstream = `mattpocock/skills` at HEAD `c55ee46` (2026-09-18), not the v1.2.3 plugin cache.

**Key Decisions (Phase 2 Brainstorming — design spec D1–D9, all HITL 2026-09-20):**

- **Decision D1:** Glossary (`CONTEXT.md`) gains **Re-fork / Drift / Orphan / Adaptation**; "sync" and "vendor" banned.
  - **Rationale:** the plan needs precise fork-lifecycle vocabulary; the grill surfaced four undefined terms.
  - **Alternatives Considered:** none — terminology gap.
  - **Trade-offs:** small glossary maintenance cost for unambiguous ADRs and commit messages.

- **Decision D2:** `grill-with-docs` keeps its **name** (Phase 1.3 dispatch + fingerprint contract); fork upstream `grilling` only; `grill-with-docs` becomes **Derived** with its `<what-to-do>` block replaced by a call to `grilling`.
  - **Rationale:** `fingerprint.py` and `/aa-ma-plan` Phase 1.3 depend on the `grill-with-docs` name; upstream split the skill into `grilling` + `domain-modeling`.
  - **Alternatives Considered:** faithful two-dir re-fork (+2 dirs, file moves); verbatim stub (breaks dispatch).
  - **Trade-offs:** one extra Derived file to maintain vs zero contract breakage.

- **Decision D3:** our `CONTEXT-FORMAT.md` stays **Derived** (retains Relationships / Example dialogue / Flagged ambiguities); `ADR-FORMAT.md` byte-identical upstream.
  - **Rationale:** our `CONTEXT.md` already honours the "glossary only" rule at term level; the extra sections are useful.
  - **Alternatives Considered:** migrate `CONTEXT.md` to upstream's stricter format.
  - **Trade-offs:** `grill-with-docs` reads ORPHAN in `fork-drift.sh` (the two format files 404 upstream) — accepted, recorded in reference.md.

- **Decision D4:** `write-a-skill` → **Derived** (upstream deleted in 1.0.0); recipe retained; `writing-for-agents` re-evaluated as a Candidate in the audit refresh (M5 charting prototype effort).
  - **Alternatives Considered:** retire; re-fork successor; adopt both.
  - **Trade-offs:** keeps a useful recipe at the cost of an Orphan row in the manifest.

- **Decision D5:** **Fork manifest** `claude-code/skills/FORKS.json` + detector test; Drift/Orphan reported as warnings; `tests/skills` added to CI.
  - **Alternatives Considered:** detector parsing ADR prose; manual checks.
  - **Trade-offs:** one more JSON to keep current (hard-fail test enforces it) for machine-checkable fork state.

- **Decision D6:** `prototype`: Re-fork at HEAD; Step 2.5 "Prototype decision" in `/aa-ma-plan`; gate rolls up sub-step `Prototype-Required`.
  - **Alternatives Considered:** re-fork only; drop the sub-step slot.
  - **Trade-offs:** `gate.py` change under `Critical-Path: hook-modification` (HARD gate) for the ability to flag one uncertain sub-step.

- **Decision D7:** `research`: fork + hardening lines; new **`aa-ma-researcher` agent** (no Agent tool) writes `docs/research/<plan-slug>-<topic>.md`.
  - **Rationale:** upstream's documented self-nesting failure (issue #530, ~450k tokens) — an agent without the Agent tool cannot re-delegate.
  - **Alternatives Considered:** Explore agent returns text, main writes the file.
  - **Trade-offs:** one more agent file (+1 count) for a verified non-nesting contract.

- **Decision D8:** `wayfinder` → **charting** Adaptation: `/aa-ma-chart` + single-file map under `.claude/dev/charting/<effort>/`; exits via `/aa-ma-plan --from-map`; optional 9th AA-MA file type (`<task>-map.md`).
  - **Alternatives Considered:** verbatim fork on GitHub Issues; document only.
  - **Trade-offs:** no files forked (cannot Drift) but our own guard + template to maintain.

- **Decision D9:** Order M1 manifest → M2 grill → M3 prototype → M4 research → M5 charting.
  - **Rationale:** M5's resolvers need M2/M3/M4's skills; M1's manifest is needed by every fork step.
  - **Alternatives Considered:** charting first.
  - **Trade-offs:** charting lands last; the "one release" part of D9 was superseded by OV4 (two releases).

**Eng-review decisions (Phase 4.2, 2026-09-20 — 7 findings accepted):**

- **1A** — the charting guard ships under `claude-code/hooks/lib/aa-ma-chart-guard.sh` (installed by an explicit `install.sh` block), so M5 carries `Critical-Path: hook-modification`.
- **1B** — tickets carry `Claimed-at:`; `work <effort> <ticket> --reclaim` resets a stuck CLAIMED ticket (append `- Reclaimed: <ts>`) then claims it.
- **1C** — `research` is forked as **Derived** (renamed, AA-MA lines appended); manifest md5 recipe pinned to exactly two fields (`files.<f>` = `tail -n +2` local; `upstream_md5.<f>` = whole upstream file), no line ranges.
- **2A** — `gate.py` gets a named `StepsRead` dataclass (`pending`, `prototype_required`) replacing `_count_pending`'s tuple.
- **3A** — `classify_fork` is a pure function (no I/O) proven by hand-built dicts; `scripts/fork-drift.sh` is the only place that fetches.
- **3B** — `test_grill_with_docs_frontmatter.py` asserts the Derived line and that `<what-to-do>` names `grilling`.
- **Regression test** — a sub-step with the literal empty `- **Prototype-Required:**` slot must exit 2 with `empty value` (`test_empty_substep_prototype_slot_exits_2`); this is the behaviour change the template fix exists for.
- **Scope D1 (deferral)** — fingerprint `_phase_3` evidence and `docs/research/README.md` deferred to `TODOS.md`.

**Outside-voice decisions (Claude subagent, Phase 4.2 — 9 of 10 challenges accepted):**

- **OV1** — the research skill is named `aa-ma-research` (not `research`) so `~/.claude/skills/research` (a real dir) is never backed up or shadowed.
- **OV2** — drop the plugin-cache comparison entirely; Drift/Orphan detection compares against the manifest's `upstream_md5` via `gh api`.
- **OV3** — M2, M4 and M5 carry **live** acceptance criteria (fresh session, real `Skill(...)` call, excerpt pasted into the Result Log, `LIVE_CHECK` / `PROTOTYPE` provenance line).
- **OV4** — two releases: v0.13.0 after M4, v0.14.0 after M5 (charting ships alone, on evidence from its prototype run).
- **OV5** — charting invariant reworded to "≤1 non-research ticket CLAIMED at a time" (research tickets run in parallel, AFK).
- **OV6** — no numeric ticket cap on a map; the command tells the user to split an effort whose *Not yet specified* keeps growing.
- **OV7** — pre-existing count/taxonomy drift is fixed in a separate pre-M1 `[ad-hoc]` commit so M1's rollback stays honest and M5 is a clean +1.
- **OV8** — plan and reference.md locate edits by anchor text, never by line number (lines quoted as of `c87135b` only).
- **Bullet 2 rejected on evidence** — "deferring the fingerprint breaks skip-warn": `aa-ma-plan-skip-warn.sh:19-21` is a marker-only correlator; the fingerprint is not read by the hook. Verification Angle 2 confirmed.

**Verification decisions (Phase 4.5, automated, 2 revisions, 9 CRITICAL → 9 resolved):**

- Gate roll-up scope = the **selected milestone only**, implemented beside `_count_pending` as `_read_steps` and applied at the selected-milestone override (`gate.py:~382`), never in `_read_milestone` — see the dedicated entry below.
- The scribe writes `Critical-Path:` / `Prototype-Required:` only where the plan sets them; blank slots are exit-2 errors (milestone level today, sub-step level after M3). Archived plans under `.claude/dev/completed/**` still contain blank slots but are never gated again (grandfathered in ADR-0011).
- Every fork/re-fork comes from upstream HEAD `c55ee46` via `gh api`, never from the plugin cache (which equals v1.2.3, 54 commits behind).
- The classifier is fed by `gh api` responses (`scripts/fork-drift.sh`): only HTTP 404 becomes `null` → ORPHAN; 403/auth/network → exit 1, never ORPHAN; empty content (file >1 MB) → exit 1.
- `install.sh` does not auto-discover `hooks/lib` helpers — the guard needs its own `create_symlink` block + `install_dry_run.bats` case (found independently by outside voice and the impact angle; treated as one CRITICAL).
- `CLAUDE.md` is gitignored → excluded from every count assertion.
- ADR-0002 recorded no md5 values → `grill-with-docs` `upstream_md5` is derived from the local byte-faithful fork (`upstream_md5_source: derived-from-local-fork`).
- Guard resolution uses the `_cand` pattern (repo path first, then `${CLAUDE_HOME:-$HOME/.claude}`), never a literal `~/.claude` path; `import` handles both tracked (`git mv`) and untracked (`mv` + `git add`) maps.
- Research-file header gains a `Sources:` field (5 fields total).

**Research Findings (Phase 3):**

- Research note: `docs/research/mattpocock-trio-2026-09.md` (Created 2026-09-20; Reviewed-Through-Date 2026-09-20; Valid-Through 2026-Q4) — upstream state at `c55ee46`, the three subject skills, our adoption seams, plus inventories under `docs/research/_inventories/`.
- Verification report: `mattpocock-trio-adoption-verification.md` (6 angles, 62/62 criteria falsifiable after revision, PASS WITH WARNINGS).
- Upstream `research` has documented self-nesting (issue #530) and no stopping criterion — the reason for D7's agent-without-Agent-tool design.
- Upstream `prototype` (HEAD) captures results on a `prototype/<name>` branch and uses a single self-contained HTML demo for LOGIC — the reason Theme 1 wording changes in M3.
- `grill-with-docs` upstream was split (2026-07) into `grilling` (primitive) + `domain-modeling`; `write-a-skill` was removed in 1.0.0 (2026-06-17).

**Remaining Questions / Unresolved Issues:**

- Does the unprefixed `Skill(grilling)` resolve to `~/.claude/skills/grilling` (ours) rather than `mattpocock-skills:grilling` (plugin)? — decided by M2's live criterion (Step 2.3); fallback: rename ours `aa-ma-grilling` (Derived) in the same milestone.
- Can the `aa-ma-researcher` agent nest by running `claude -p` from `Bash` even without the Agent tool? — decided by M4's prototype run (Step 4.3: `grep -c 'claude -p'` on the subagent transcript = 0); the prompt prohibition ("never run `claude`") is the fallback.

---

## [2026-09-20] Decision: gate roll-up reads sub-steps only for the selected milestone

- **Decision AD-001:** `_read_steps` (replacing `_count_pending`) reads `Status`, `Mode` and `Prototype-Required` per sub-step **only within the milestone selected by `--milestone N`**, and its `prototype_required` is OR-ed into `MilestoneRead` at the selected-milestone override (`gate.py:~382`). `_read_milestone` and the file-wide scan are unchanged; JSON schema and `to_kv` unchanged.
  - **Rationale:** reading sub-step fields file-wide (inside `_read_milestone`) would make any bad sub-step token anywhere in tasks.md — an invalid `maybe`, or a blank `- **Prototype-Required:**` slot left by the old template — exit 2 on **every** `aa-ma-gate` call, including calls for milestones that are already COMPLETE or not yet started. Scoping to the selected milestone keeps the gate's blast radius equal to the milestone being gated, matching how `_count_pending` already behaves for `Status: PENDING`.
  - **Alternatives Considered:**
    1. Roll up in `_read_milestone` (file-wide) — rejected: turns one stray token into a whole-file failure; breaks `--milestone` calls on unrelated milestones.
    2. Keep milestone-only semantics and forbid sub-step `Prototype-Required` — rejected: loses D6's ability to flag one uncertain sub-step.
  - **Trade-offs:** a bad token in a non-selected milestone is not reported until that milestone is gated (acceptable — that is when it matters); `tests/test_active_plans_canonical.py` still scans `active/` for template hygiene.
  - **Impact:** `src/aa_ma/gate.py`, `tests/test_gate.py`, `tests/hooks/fixtures/gate-scans/prototype-rollup-tasks.md`, `tests/hooks/aa-ma-gate-python.bats`, `execute-aa-ma-milestone.md` §6.7 BLOCKED text, `execute-aa-ma-step.md` advisory, ADR-0011. Milestone 3 (HARD gate, `Critical-Path: hook-modification`).

---

## [2026-09-21] Milestone Completion: Milestone 1 — Fork manifest, Drift/Orphan detector, Derived reclassifications, CI coverage
- Status: COMPLETE — approved by Ste at §7.3, 2026-09-21
- Key outcome: `claude-code/skills/FORKS.json` is the fork SSoT; `aa_ma.forks` is a pure SAME/DRIFT/ORPHAN classifier with `classify` / `files` / `classify-all` CLI; `scripts/fork-drift.sh` is the only fetcher and fails closed (bad manifest, hidden repo, 403, partial fetch → exit 1). Live `--sha c55ee46`: grill-with-docs ORPHAN, prototype DRIFT, write-a-skill ORPHAN — exactly as reference.md predicted. `write-a-skill` is Derived. CI pytest step is exclusion-based (was enumerated and silently missing 190 tests).
- Artifacts: src/aa_ma/forks.py, claude-code/skills/FORKS.json, scripts/fork-drift.sh, tests/skills/test_fork_manifest.py, tests/skills/_helpers.py, tests/hooks/fork-drift.bats (+fixture), tests/commands/test_aa_ma_share_command.py, .github/workflows/security.yml, pyproject.toml, uv.lock, .importlinter, write-a-skill/SKILL.md, ADR-0004, README.md, CHANGELOG.md, docs/lessons.md (L-017), mattpocock-trio-adoption-impl-review.md
- Commits: 8d91442 (M1), d755920 (red), 4144305 (green §6.8 fixes)
- Tests: 513 passed (CI command), bats fork-drift 7/7, shellcheck clean, lint-imports 3 kept
- §6.8: PASS_WITH_WARNINGS — 2 CRITICAL (1 fixed, 1 disputed: TDD same-commit tie, provenance RED→GREEN cited), 8 WARNING (5 fixed), 13 INFO (4 fixed)

### Decisions
- **AD-002** — `aa_ma.forks` owns all manifest reading (`files` / `classify-all` subcommands); the shell never parses FORKS.json. Rationale: two readers with different failure semantics was the root of the fail-open CRITICAL. Additive to the M1 Contract (reference.md addendum).
- **AD-003** — CI pytest step is exclusion-based, never enumerated (L-017c). Supersedes Step 1.6's "exact list" AC wording (user-approved at §6.8 panel).
- **AD-004** — fork-drift.sh pre-flights `gh api repos/mattpocock/skills` because GitHub returns 404 for hidden repos; only a file-level 404 may become ORPHAN.
- **Process** — from M2 on, the red test is committed on its own before the implementation commit (L-017a) so the mechanical TDD criterion passes.

---

## [2026-09-21] Milestone Completion: Milestone 2 — Fork `grilling`; `grill-with-docs` becomes Derived
- Status: COMPLETE (pending §7.3 approval at time of writing)
- Key outcome: `claude-code/skills/grilling/` is a verbatim fork of upstream `skills/productivity/grilling` @ `c55ee46` (manifest `state: current`, live fork-drift → SAME). `grill-with-docs` keeps its name and domain block and is now Derived: `<what-to-do>` reads the glossary docs then delegates the interview to `Skill(grilling)`. Live criterion met in-session: unprefixed `Skill(grilling)` resolved to `~/.claude/skills/grilling` (ours) — no rename to `aa-ma-grilling` needed. Skills 19→20 at every count site.
- Artifacts: claude-code/skills/grilling/SKILL.md, claude-code/skills/grill-with-docs/{SKILL,CONTEXT-FORMAT}.md, claude-code/skills/FORKS.json, tests/skills/test_grilling_frontmatter.py, tests/skills/test_grill_with_docs_frontmatter.py, claude-code/commands/aa-ma-plan.md, SECURITY.md, README.md, docs/spec/claude-code-foundations.md, docs/ATTRIBUTION.md, docs/adr/0002 (+amendment), docs/adr/0012 (count fix), CHANGELOG.md, impl-review.md (M2 section)
- Commits: 7542c30 (red 2.1), bc329d4 (2.1), 936fb1d (red 2.2), 7030200 (2.2), ba36187 (2.3 docs), 5d2ff5d (gate evidence), + §6.8 fix commit
- Tests: 142 passed (milestone cmd); CI cmd 515 passed; bats install_dry_run 4/4; live fork-drift: grilling SAME
- §6.8: PASS_WITH_WARNINGS — 0 CRITICAL, 4 WARNING (all fixed), 9 INFO (2 fixed, 7 acknowledged)

### Decisions
- **AD-005** — `grill-with-docs` `<what-to-do>` deviates from the M2 Contract's verbatim text by one leading line ("First locate and read `CONTEXT.md` / `CONTEXT-MAP.md` / `docs/adr/` yourself…"). Rationale (code-reviewer W2): after delegation, `grilling`'s fact-finding sub-agents never see `<supporting-info>`, so glossary discovery must happen in the orchestrator's context before the interview starts. Still ≤6 lines, still names `grilling`; the ≤6-line assert now guards it.
- **AD-006** — Fact-finding sub-agents dispatched by `grilling` inside `/aa-ma-plan` are scoped in plugin-owned text (`aa-ma-plan.md` with-docs bullet: at most 5 at once; read-only, repo-local; no external connectors or writes). Rationale (security-auditor W1): the verbatim upstream prompt must not define the lookup boundary. The fork stays byte-identical.
- **Observation** — the "fresh session before a live criterion" rule in reference.md is falsified: the Skill listing hot-reloads after `install.sh`. M4's live criterion may run in-session.
