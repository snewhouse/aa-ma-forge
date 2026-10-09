# code-conventions-impact Context Log

_This log captures architectural decisions, trade-offs, and unresolved issues._

---

## [2026-10-08] Plan Approved

- Plan: code-conventions-impact
- Approved by: Ste (Stephen J Newhouse)
- Milestones: 14
- HARD gates: Milestone 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 14 (SOFT: Milestone 4, 13)

---

## [2026-10-08] Initial Context

**Feature Request (Phase 1):**

Imported from the charting map (`/aa-ma-plan --from-map code-conventions-impact`; map Destination, verbatim):

> A plan-ready spec for one `/aa-ma-plan` that (1) wires impact analysis into the coding workflow at author time and at review, (2) sets forge-canonical coding conventions — comments, docstrings, logging, SecOps, design principles — for Python, Bash, Markdown skills, TS/JS and R/SQL, and (3) defines how reusable code is captured and when it graduates from snippet to module to library.

Plan objective as approved: make the forge's coding conventions (comments, docstrings, logging, SecOps, design principles, testing, prompt-as-code) stated once and mechanically enforced on touched code, and wire impact analysis into authoring (pre-edit hook) and the milestone gate (gate-computed `IMPACT_VERIFIED`, `TESTS_VERIFIED`). Theme (3), reuse, moved to a later `reuse-kit` plan (D1).

Standing map decisions (Ste, 2026-10-08): forge is canonical; tiered language depth (full for Python/Bash/Markdown, cards for TS/JS, R, SQL); touched code only, no backfill; Biorelate `galactic-*` material is pattern reference only (L-1289). Engineering Standards: all six themes selected by Ste.

**Key Decisions (Phase 2 Brainstorming):**

- **Decision AD-001 (D1, Ste):** Two plans. This plan covers map groups 1–12, the forge only; reuse (T13/T14: kit repo, template repo, router skill, graduation CI) moves to a later `reuse-kit` plan. T13's in-repo git-HEAD helper stays here (M10).
  - **Rationale:** reuse work creates two new GitHub repos and has its own confidentiality gate; keeping it separate keeps this plan forge-only and shippable.
  - **Alternatives Considered:** one plan for all three themes (the map's original "One plan" decision) — rejected as too large (~150 files already).
  - **Trade-offs:** faster delivery of conventions + impact; reuse-first-while-coding (T14) waits for the router skill.

- **Decision AD-002 (D2, Ste):** `deslop-shared-libs` is declared-external (gstack-owned, byte-identical to `~/.claude/skills/gstack/deslop-shared-libs/SKILL.md`). Migration is 5 skills, not 7.
  - **Rationale:** it is owned upstream by gstack; forking it would create drift.
  - **Alternatives Considered:** migrate as a fork — rejected.
  - **Trade-offs:** one less in-repo skill; it stays an external reference on the allowlist (added in M12 only if referenced).

- **Decision AD-003 (D3, Ste):** `senior-secops` becomes a new forge skill `secops` (thin router). The global copy (a byte-identical fork of davila7/claude-code-templates, disabled at `settings.json:295 "off"`) is backed up and removed, which deletes the stub scanner (carried defect 2). The `"off"` override is left alone (L-1210).
  - **Rationale:** the stub scanner always reports clean — a silent pass; a router to real tools is honest.
  - **Alternatives Considered:** migrate the skill as-is — rejected (keeps the stub).
  - **Trade-offs:** outside-repo removal needs HITL + backup.

- **Decision AD-004 (D4, Ste):** Retire the forge `/grill-me`; 13 commands convert to skills.
  - **Rationale:** the forge ships `grilling` + `grill-with-docs`, and an external `~/.claude/skills/grill-me → ~/.agents/skills/grill-me` exists.
  - **Alternatives Considered:** convert all 14 commands — rejected (duplicate of existing skills).
  - **Trade-offs:** one user-facing `/name` disappears from the forge; the external one remains.

- **Decision AD-005 (D5, Ste):** Milestone order approved, with commands→skills early (M3).
  - **Rationale:** later milestones edit the converted skill files; converting first avoids editing them twice.
  - **Alternatives Considered:** convert late — rejected.
  - **Trade-offs:** the executor converts itself mid-plan (mitigated by the M3.1 prototype + D7).

- **Decision AD-006 (D6, Ste):** Prototypes on M3 (install path), M10 (hook UX), M11 (co-change threshold).
  - **Rationale:** highest implementation uncertainty; throwaway POCs are cheaper than wrong abstractions.
  - **Alternatives Considered:** no prototypes — rejected.
  - **Trade-offs:** extra HITL steps; PROTOTYPE evidence becomes a HARD gate check.

- **Decision AD-007 (D7, Ste, CEO review F17):** Each milestone executes in its own worktree `.worktrees/<branch>`.
  - **Rationale:** `install.sh` symlinks `~/.claude` into the main checkout, so branch edits must never go live mid-session.
  - **Alternatives Considered:** work in the main checkout — rejected (live surface changes mid-session).
  - **Trade-offs:** a new gate fence is first exercised by the milestone after the one that ships it; post-merge work becomes step N.0 of the next milestone; each worktree needs `uv sync && uv run codemem build`.

- **Decision AD-008 (D8, Ste, Verification v1):** Touched files comply in full (file-level, not line-level); `check_conventions.py` rules (WHY001, TODO001) stay added-lines-only.
  - **Rationale:** measured debt is ≤11 findings per planned file; the edit-time ruff-format hook already reformats whole files.
  - **Alternatives Considered:** line-level compliance — rejected (complex, inconsistent with ruff/format behaviour).
  - **Trade-offs:** small extra churn when an old file is first touched.

- **Decision AD-009 (D9 → D9 revised, Ste, Wave 2):** `disable-model-invocation: true` on `sole-dev-merge` and `aa-ma-share` ONLY; the other 11 converted skills stay model-invocable. (Original D9: none — superseded.) **Revised again 2026-10-09 (M3 §6.8, Ste):** also execute-aa-ma-full and archive-aa-ma → 4 skills; see "M3 §6.8 decisions" below.
  - **Rationale:** those two merge, push or publish, and nothing delegates to them; execute-aa-ma-full delegates to execute-aa-ma-milestone and aa-ma-execution routes to it.
  - **Alternatives Considered:** user-only for all converted commands — rejected (breaks delegation).
  - **Trade-offs:** model-invocable `aa-ma-plan` may trigger unprompted; mitigated by scoped descriptions and a 2-week re-evaluation.

- **Decision AD-010 (D10, Ste, Verification v1):** `Test-Command: none — <reason>` opt-out for TESTS_VERIFIED, visible as `skipped: <reason>` in provenance and requiring a context-log GATE APPROVAL.
  - **Rationale:** non-pytest repos and docs-only repos need an explicit, visible escape.
  - **Alternatives Considered:** silent skip — rejected (no silent failures).
  - **Trade-offs:** one more gate input to protect (read from the merge-base copy).

- **Decision AD-011 (D11, Ste):** One release (v0.18.0) in its own milestone M14; interim releases dropped. M14 runs on main after M13 merges and sets `IMPACT_CUTOVER`.
  - **Rationale:** the cutover date must equal the release date; one release keeps that atomic.
  - **Alternatives Considered:** interim releases at M5/M9 — rejected.
  - **Trade-offs:** public users get all changes at once (upgrade note: re-run `scripts/install.sh`).

- **Decision AD-012 (D12, Ste; reopens T10/T15 "advisory"):** The commit scan keeps blocking: `security-static-check.sh` runs the forge-pinned `ruff check --isolated --select S602,S604,S307,S608,S301` on staged .py plus the secret-literal and path-traversal regexes, and exits 2 on findings in ANY repo. Regex classes Ruff covers are retired.
  - **Rationale:** Security specialist (Verification v2) — a relabel to advisory would weaken the commit layer.
  - **Alternatives Considered:** advisory hook (map T15 §7) — rejected on review.
  - **Trade-offs:** no ruff → `fail_open_notice` + exit 0 (never a silent pass).

- **Planner decisions P1–P9 (approved by Ste with the plan):** P1 touched-files harness = pre-commit; P2 Expected-Blast-Radius = Contract `Files:` rows; P3 `aa-ma-impact` CLI shells out to codemem (import-linter forbids `aa_ma` → `codemem`); P4 TESTS_VERIFIED for every plan, IMPACT_VERIFIED only post-cutover; P5 delete pyproject's unbacked claims; P6 griffe for aa_ma + codemem only; P7 Dependabot github-actions + uv only; P8 split-on-touch is its own milestone (M5); P9 evals advisory (release + weekly local; no GitHub-hosted schedule on a public repo).

**Review Summaries:**

- **CEO review (2026-10-08):** mode HOLD SCOPE (Ste chose HOLD over the rule-recommended REDUCTION). 17 findings, 2 CRITICAL GAPS (F1 stale-index silent pass; F7 evals that can push), both fixed in-plan. New decision D7 (worktree per milestone). Error & Rescue Registry: 10 rows, 0 critical gaps. Status CLEAR.
- **Eng review (2026-10-08):** FULL_REVIEW, scope accepted as-is (S1, original arrangement). 5 issues, 0 critical gaps, all resolved in plan: R1 merge-base milestone window (`aa_ma_milestone_base`, shared by IMPACT fence + verify-impl, fails closed); E2 contract-row grammar with full verb set; E3 co_changes threshold/min-ratio/multi-path; E4 diagram edge correction (`impact.py → logsetup.py`); E5 fence parses the FINAL pytest summary line.
- **Outside voice:** unavailable (codex not installed; no native fallback).
- **Verification (automated, 3 revisions):** 16 CRITICAL found and resolved; ~45 WARNING reconciled; verdict PASS WITH WARNINGS. Structural lint: `aa-ma-lint-views --coverage` exit 0, `render: PASS`, `sigils: edges=25 checked=25 phantom=0 unknown=0`. Revisions: v1 inline fixes + amendments + D8–D10; v2 post-merge N.0 steps, M14 release, §0 security hardening, D11, D12, D9 revised; v3 reconciliation (precedence rule, contract_rows module, pronoun rule, version-pipeline globs, grandfather-before-merge-base).

**Research Findings (Phase 3):**

- [docs/research/code-conventions-impact-inventory.md](../../../../docs/research/code-conventions-impact-inventory.md) (T1) — ~8.8k auto-loaded tokens; the real comments/docstring/logging standard is global-only; Bandit `|| true` (`security.yml:39`); D101–D107 ignored; contradictions (ponytail vs SOLID/TDD, 4 debug env-var names, ruff hook discards findings).
- [docs/research/code-conventions-impact-best-practice.md](../../../../docs/research/code-conventions-impact-best-practice.md) (T2) — 4 silent-pass security checks; no supply-chain checks; 6 files over 500 lines; unknown frontmatter keys ignored; no behavioural evals; 19 prioritised actions.
- [docs/research/code-conventions-impact-language-cards.md](../../../../docs/research/code-conventions-impact-language-cards.md) (T3) — TS/JS, R and SQL one-page cards (68 primary sources); conflicts: pino stdout, `@param` vs `Args:`, SQL keyword case.
- [docs/research/code-conventions-impact-impact-status.md](../../../../docs/research/code-conventions-impact-impact-status.md) (T4) — gap 3 partly fixed, gap 7 docs-only (`aa_ma_context` key bug, defect 1); gaps 1, 2, 4, 5, 6 and R1–R4, R6 open; no general coding skill invokes impact analysis.
- [docs/research/code-conventions-impact-reuse-prior-art.md](../../../../docs/research/code-conventions-impact-reuse-prior-art.md) (T5) — nothing packaged; ~3k untested snippet fences; git-HEAD helper ×6 (input to M10.4 gitutil and the reuse-kit plan).
- Eng-review test plan artifact: `~/.gstack/projects/snewhouse-aa-ma-forge/sjnewhouse-feature-engineering-standards-eng-review-test-plan-20261008-132258.md`.
- Folded-in map: `.claude/dev/charting/writing-for-agents-eval/writing-for-agents-eval-map.md` (4/4 RESOLVED; executed by M4).
- Verified at planning (Verification Angle 2): A1 additionalContext support per docs; D417 under google; A3 JSON output; A5 3 fixture-only gitleaks hits; merge-base viability. Contradicted: A6 (`uv audit` experimental, 13 vulnerable packages).

**Remaining Questions / Unresolved Issues:**

- A1 — PreToolUse/PostToolUse `hookSpecificOutput.additionalContext`: VERIFIED against docs in verification; live probe still due in M10.1 (fallback `systemMessage`).
- A2 — `claude plugin eval` targets `claude-code/skills/` without `plugin.json`: OPEN; proven or replaced by the `claude -p` harness in M4.3.
- A3 — `codemem query` prints JSON: VERIFIED 2026-10-08; co_changes gains `--threshold/--min-ratio`/multi-path in M10.
- A4 — Ruff S at 0.15.9 covers every Bandit test that fires here: OPEN until M8.1 (S404 preview-only vs B404 ×10 decides the fallback list).
- A5 — gitleaks full history finds no live secret: VERIFIED at planning (3 fixture hits); confirmed with a reviewed `.gitleaksignore` in M8.3.
- A6 — `uv audit` usable: CONTRADICTED; pip-audit fallback + triage Sub-step 8.5 (plan 8.4a).
- Residual (verification): review appendices (CEO/Eng output) keep pre-revision wording; the precedence rule governs.
- Residual (verification): amendment-only files (forks.py, fork-drift.sh, git_mining.py, .importlinter, aa-ma-scribe.md, sanitizers.py) are not Contract `Files:` rows, so coverage lint cannot see them; nothing is gated on it because this plan is grandfathered from IMPACT_VERIFIED.
- Residual (verification): re-run `/verify-plan code-conventions-impact` after Phase 5 so the tasks.md gate parse (check #2) runs.
- Resolved (plan §13): the Milestone graph was appended to plan.md §13 by `aa_ma_deps graph` (2026-10-08, Phase 5). The pronoun rule was confirmed as v3, second-person only, in plan.md and tasks.md 4.1.
- Re-evaluate the model-invocable `aa-ma-plan` description after 2 weeks of use (M3 Risk 3).

## [2026-10-08] ADR APPROVAL: ADR-0018 touched-code lint gate (Sub-step 1.5)
- Approved by: Ste (AskUserQuestion, 2026-10-08)
- Decision: APPROVED — `docs/adr/0018-touched-code-lint-gate.md` Status: Accepted
- Accepted gap recorded: untouched files are no longer linted in CI; full-repo Ruff S returns in M8.

## [2026-10-08] GATE APPROVAL: Milestone 1: Touched-files lint harness + baseline
- Gate: HARD
- Approved by: Ste (AskUserQuestion, 2026-10-08)
- Criteria verified: 6/6
- Decision: APPROVED

## [2026-10-08] Milestone Completion: Milestone 1: Touched-files lint harness + baseline
- Status: COMPLETE
- Key outcome: pre-commit is the one touched-files harness (4 `repo: local` hooks + stdlib `scripts/check_conventions.py`, 0 checks); CI `touched` replaces the src-only `ruff` job; dev deps merged into `[dependency-groups] dev` with pre-commit and bandit==1.9.4; ADR-0018 Accepted.
- Artifacts: .pre-commit-config.yaml, scripts/check_conventions.py, tests/scripts/test_check_conventions.py, tests/test_precommit_config.py, .github/workflows/security.yml, pyproject.toml, uv.lock, docs/adr/0018-touched-code-lint-gate.md, docs/adr/INDEX.md, docs/architecture/* (regenerated), impl-review.md.
- Tests: full suite 2450 passed / 5 skipped / 7 deselected; PR #18 all 7 CI jobs green at d3b6bc4; canary PR #17 failed `touched` on F401.
- Decisions: §6.6 folded into the §6.8 code-reviewer pass (/rigor 5-agent cap). Double-check F1–F3 fixed in M1 (Ste). Deferred to M6: escape control characters in finding output (security I1); single-call diff if latency shows (code-review I2).
- Observed, out of scope: `src/aa_ma/grammar.py:263` SyntaxWarning (invalid escape `\S` in a docstring) on every gate call. `gh pr checks` in this gh version has no `--json`; polls must not hide stderr (L-036).
- Post-merge (Sub-step 2.0): update gitignored project CLAUDE.md:141 "Ruff lint on `src/`".

## [2026-10-09] ADR-0019 approval + M2 decisions
- ADR-0019 (coding-doctrine skill migration) → Accepted by Ste (AskUserQuestion, 2026-10-09).
- 2.1: secrets-management pinned to live upstream wshobson/agents @ 46891e7 byte-exact (picks up no-echo + pinned-image fixes); bash-defensive-patterns kept as Ste's copy, derived @ 5d65aa1 (upstream restructure not rebased). Adoption rows have no upstream SHA (Ste-authored).
- 2.3: every fork ships its upstream MIT LICENSE, incl. the 5 pre-existing mattpocock forks (gap found by the new test).
- 2.4: payload captured via isolated headless `claude -p --settings <tmp>` (Ste's choice). AA_MA_HOOKS keeps the `|` schema; install.sh parses rows anchored on `<name>.sh|<timeout>|` like codemem `_HOOK_ROW` (a `;` switch broke the plugin-surface extractor).
- 2.5: five user-local `/x` refs in python-quality-gates reworded (allowlist policy: local-only commands are not declared-external); llm-output-safety + bash-defensive-patterns pinned as orphans until M12; ruff-format.sh stays verbatim and does not honour AA_MA_HOOKS_DISABLE (README states the exception). **Superseded by §6.8 (adb3524):** hook adapted, honours AA_MA_HOOKS_DISABLE + CLAUDE_HOOK_LOG; README carve-out removed.

## [2026-10-09] M2 §6.8 decisions (Ste)
- TDD CRITICAL (tests + src in one commit) → **disputed**; RED runs are in the Result Logs. Convention: RED gets its own `test(...)` commit from now on (applied: 4e6889e → adb3524).
- Leak (private Carmen repo path in imported `logging-and-comments/SKILL.md:66`) → **rewrite + force-push**: filter-branch done locally, history hits 0; force-push denied by tool permission; **done by Ste** (pre-rewrite tip → 4a23e0a, remote history hits 0); GitHub Support purge of orphaned SHAs still pending (Ste). L-039 tightened (scan any imported content before its first commit).
- secrets-management → **patched, state derived** (supersedes the 2.1 "current @ 46891e7, byte-exact" choice).
- Other warnings → **all fixed**: hook kill switch + CLAUDE_HOOK_LOG (hook now "Adoption, adapted"), settings backups as sibling files, `--restore` walks all backups newest-first, README "9 hooks", tests read SHAs from FORKS.json, `_helpers` requires a manifest entry.

## [2026-10-09] GATE APPROVAL: Milestone 2: Migrate 5 skills + ruff hook into the forge
- Gate: HARD
- Approved by: Ste
- Criteria verified: 8/8
- Decision: APPROVED

## [2026-10-09] Milestone Completion: Migrate 5 skills + ruff hook into the forge
- Status: COMPLETE
- Key outcome: 5 coding-doctrine skills (3 adopted, 2 wshobson forks, both derived) and the adapted ruff-format hook ship from the forge; install/uninstall handle them; fork tooling is multi-repo with per-fork LICENSE.
- Artifacts: claude-code/skills/{logging-and-comments,python-quality-gates,llm-output-safety,secrets-management,bash-defensive-patterns}/, claude-code/hooks/ruff-format.sh, FORKS.json, src/aa_ma/forks.py, scripts/{fork-drift,install,uninstall}.sh, surface_allowlist.py, tests/hooks/{ruff-format,install-migration}.bats, ADR-0019, counts docs, regenerated golden/architecture.
- Tests: pytest 2482 passed / 0 failed; bats 355/355; PR #19 CI 7/7 (run 37914723912).
- Open (outside repo): GitHub Support purge of orphaned leaked SHAs (Ste). Next: Sub-step 3.0 post-merge (live install.sh from main, L-1315 probe).

## [2026-10-09T10:32:10Z] Compaction Summary (auto-generated by hook)
- Active step at compaction: Sub-step 3.0: Post-merge of M2
- Snapshot saved to: ~/.claude/hooks/cache/compaction-snapshots/code-conventions-impact-snapshot.md
- Note: Context compacted. Reload AA-MA files to resume.

## [2026-10-09] M3.1 Complexity routing + prototype decision
- complexity-router: Scope 82, Arch 75, Risk 60, Deps 40, Uncertainty 25 → 61% weighted; auto-triggers 50+ files and a breaking path contract (commands/ → skills/) → **80% Critical**. Route: deep review = the 3.1 prototype + HITL gates (plan states 85%; consistent).
- Prototype verdict: **GO** — commands convert to skills by `git mv`; the install path needs (a) a REPO_ROOT-scoped stale-command-link sweep and (b) foreign-symlink recording before replacement. Plan change (verdict-changes-plan: YES): `uninstall.sh --restore` must replay the foreign-symlink manifest (new 3.2 AC). Evidence: tasks 3.1 Result Log; branch prototype/cmd-to-skill @ ac5f814.
- Pre-execution validator: WARN (0 FAIL, 7 WARN). Fixed now: W1 (plan.md 3.4 prose → SKILL.md body), W4 (reference status rows), W6 (provenance line for the M3 worktree cut below). W2 (list of the 31 test files) → 3.3 Result Log. W3/W5/W7: no action (Contract Files: rows are grandfathered; §2 ADR number is historical, reference says 0020; W7 done above).

## [2026-10-09] ADR-0020 approval — Commands become skills
- Approved by: Ste (AskUserQuestion, M3.5) — Decision: Accept
- Status Proposed → Accepted; INDEX row 0020 Accepted.
- Deferred to Sub-step 4.0 (post-merge): the gitignored local CLAUDE.md:51-52 edit (commands/ 14 → none; skills count), so main's CLAUDE.md never describes a tree main does not have yet.

## [2026-10-09] M3 §6.6 decision — fix all, including one shared hook table
- 3 review agents: 0 CRITICAL, 15 WARNING, 17 INFO. Ste chose "Fix all incl. shared hook table" over deferring the table move to M7.
- Format change with 4 readers (L-041 grep): install.sh, uninstall.sh, codemem plugin_surface via surface_allowlist.HOOK_TABLE (+ its tmp-tree test fixtures, test_draw_check), the bats oracle; docs CONTRIBUTING.md, regen-generated.sh. All moved in 41d8288; the array syntax is unchanged so `_HOOK_BLOCK`/`_HOOK_ROW` read the new file as-is.
- Skipped: porting the deleted frozen-regex test to skills (test_a_slash_glob_expands_over_skills_too covers the glob rule); `.worktrees/` links are now foreign rather than documented-only.

## [2026-10-09] M3 §6.8 decisions — D9 revised again (4 skills), fix all WARNINGs
- 5 agents: 0 CRITICAL / 7 WARNING / 18 INFO (PASS_WITH_WARNINGS). No override panel needed.
- D9 revised again (Ste): execute-aa-ma-full and archive-aa-ma also get `disable-model-invocation: true` — they commit, tag and push with no per-step gate, and nothing delegates to them. execute-aa-ma-milestone stays model-invocable (execute-aa-ma-full delegates to it).
- Fixed now (Ste): broken `../` links + a guard test; `..` manifest rows refused; jq write failure warns; settings.json mode kept; aa-ma-share refuses without its checkout; doc drift.
- Record correction: 256237f is labelled format-only but also carries the 11 renames (pushed; not rewritten).

## [2026-10-09] GATE APPROVAL: Milestone 3: Commands → skills (13), install hygiene
- Gate: HARD
- Approved by: Ste (AskUserQuestion: "Fix F1+F2, then approve") — F1/F2 fixed in 38e3b20 before this record
- Criteria verified: 7/7 (double-check report 2026-10-09T113200Z, Verified; §6.7 PASS; §6.8 PASS_WITH_WARNINGS, all fixed)
- Decision: APPROVED

## [2026-10-09] Milestone Completion: Milestone 3: Commands → skills (13), install hygiene
- Status: COMPLETE
- Key outcome: every forge `/name` is now a skill (13; /grill-me retired), and install/uninstall clean up after the move: stale command links swept, foreign symlinks recorded and restored, one validated hook table shared with codemem.
- Artifacts: claude-code/skills/{aa-ma-chart,aa-ma-plan,aa-ma-search,aa-ma-share,archive-aa-ma,execute-aa-ma-full,execute-aa-ma-milestone,execute-aa-ma-step,ops-mode,sole-dev-merge,verify-plan}/SKILL.md, assess-codebase + understand-codebase SKILL.md, scripts/{install,uninstall}.sh, scripts/lib/aa-ma-install-lib.sh, codemem plugin_surface.py + surface_allowlist.py, ADR-0020, tests (install_dry_run.bats, test_hook_table, test_model_invocation_list, test_no_command_skill_collision, test_skill_links_resolve), counts docs, regenerated golden/architecture.
- Tests: pytest 2571 passed / 0 failed; bats 378/378; shellcheck rc=0.
- Open (outside repo / next): Sub-step 4.0 — live install from main, 13 isolated probes, `ls ~/.claude/commands` drop of 14 (COMMANDS pre/post), CLAUDE.md local edit, pre-compact hook absolute-path fix decision; GitHub Support purge (Ste).

## [2026-10-09] M4.3 Eval mechanism — `claude plugin eval` (A2 proven, with one correction)
- Decision: `scripts/run-evals.sh` drives `claude plugin eval` (Claude Code 2.1.295), not the `claude -p` fallback. Ste approved the paid proof run (HITL, cap $0.50).
- A2: a directory with `skills/<x>/SKILL.md` and no `plugin.json` loads as a plugin named after the directory (docs: plugins-reference "Manifest file"; plugin-evals "Choose what to evaluate"). Plugin skills are namespaced `<plugin>:<skill>`.
- Correction found in the proof: run 1 prompted `/aa-ma-search …` inside plugin `q`; the skill never loaded ("`/aa-ma-search` isn't installed in this session") yet the `llm` grader scored the case 1.0 (votes PASS FAIL PASS). A judge alone gives false passes. Rule for every case: one `tool_used` grader `tool: Skill`, `input_match: '"skill"\s*:\s*"(?:[\w-]+:)?<skill>"'` plus one result grader; prompts are phrased as a user would ask, not as `/<name>`.
- Placement: cases at repo-root `evals/<skill>/<case>/case.yaml` with `plugins: ["../../../claude-code"]`, run as `claude plugin eval <repo-root>`. A case-file target refuses that `plugins` entry (containment root = the case dir); the repo-root target accepts it. Results land in `evals/results/<ts>/` → gitignore it; run-evals.sh converts to `.claude/evals/<date>.jsonl`.
- Flags: always `--no-publish --runs 1 --ablation none --trust-plugin --max-cost-usd <cap> --json <file>`, `</dev/null`. Isolation is built in: each run gets a temp HOME and an empty cwd; Bash/Write/Edit/WebFetch/WebSearch are removed unless `--allow-tools` grants them (granted Bash runs under the OS sandbox, needs bubblewrap+socat on Linux).
- Cost of one case: $0.0034 (haiku agent, 2 graders incl. 3 haiku judge votes), 12 s wall.
- JSONL proof line: see provenance `EVAL_PROOF`.

## [2026-10-09] ADR-0021 approval — Fork writing-for-agents; retire write-a-skill
- Approved by: Ste (AskUserQuestion, M4.4) — Decision: Accept
- Status Proposed → Accepted; INDEX row 0021 Accepted; ADR-0004 → Superseded by 0021.
- Scope added in 4.4 (found while writing the ADR): `install.sh` swept only stale *command* links, so retiring a skill would leave `~/.claude/skills/write-a-skill` dangling into the repo after 5.0's live install. The sweep now covers `skills/*` and `agents/*.md` too (RED d3830a8 → GREEN 4ae7c7c). Same predicate as before (`points_into_repo`, dangling only), so foreign links are untouched.
- Not taken from upstream: `agents/openai.yaml` (Codex display metadata; Claude Code does not read it; a YAML companion also has no slot for the HTML provenance line the fork test requires).
