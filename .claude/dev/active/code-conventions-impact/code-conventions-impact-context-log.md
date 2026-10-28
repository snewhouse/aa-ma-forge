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
- Placement: cases at repo-root `evals/<skill>/<case>/case.yaml` with `plugins: ["../../../claude-code"]`, run as `claude plugin eval <repo-root>`. A case-file target refuses that `plugins` entry (containment root = the case dir); the repo-root target accepts it. Results land in `evals/results/<ts>/` → gitignore it; run-evals.sh converts to `.claude/evals/<date>.jsonl`. [Superseded by M4.5: run-evals.sh uses a temp `--output-dir`; `evals/results/` stays ignored for direct runs.]
- Flags: always `--no-publish --runs 1 --ablation none --trust-plugin --max-cost-usd <cap> --json <file>`, `</dev/null`. Isolation is built in: each run gets a temp HOME and an empty cwd; Bash/Write/Edit/WebFetch/WebSearch are removed unless `--allow-tools` grants them (granted Bash runs under the OS sandbox, needs bubblewrap+socat on Linux).
- Cost of one case: $0.0034 (haiku agent, 2 graders incl. 3 haiku judge votes), 12 s wall.
- JSONL proof line: see provenance `EVAL_PROOF`.

## [2026-10-09] ADR-0021 approval — Fork writing-for-agents; retire write-a-skill
- Approved by: Ste (AskUserQuestion, M4.4) — Decision: Accept
- Status Proposed → Accepted; INDEX row 0021 Accepted; ADR-0004 → Superseded by 0021.
- Scope added in 4.4 (found while writing the ADR): `install.sh` swept only stale *command* links, so retiring a skill would leave `~/.claude/skills/write-a-skill` dangling into the repo after 5.0's live install. The sweep now covers `skills/*` and `agents/*.md` too (RED d3830a8 → GREEN 4ae7c7c). Same predicate as before (`points_into_repo`, dangling only), so foreign links are untouched.
- Not taken from upstream: `agents/openai.yaml` (Codex display metadata; Claude Code does not read it; a YAML companion also has no slot for the HTML provenance line the fork test requires).

## [2026-10-09] M4.5 Eval runner decisions
- Billing (Ste asked before any paid run): this machine authenticates with claude.ai (`claude auth status`), no `ANTHROPIC_API_KEY`; eval runs count against plan usage. `costUsd` / `--max-cost-usd` are list-price estimates, not charges. Guard added: `run-evals.sh` drops `ANTHROPIC_API_KEY` unless `RUN_EVALS_ALLOW_API_KEY=1`. Ste chose sonnet as the default model.
- AC mapping: the tasks AC was written for the `claude -p` fallback (`--disallowedTools`, `--allowedTools`). With `claude plugin eval` (4.3), tools a case does not list are absent from the session; `env -i`, the temp output dir, JSONL and exit-0 contract are kept as written. LIVE bats prove git push and `$HOME` writes cannot happen.
- Grader lesson: `tool_used … max: 0` counts refused calls, so "Bash was never used" must be asserted on the session's tool list, with a positive-control regex so `not_contains` is not vacuous.
- Baseline (2026-10-09, sonnet): 14/24 pass; 9 of 10 fails are `skill-fired` (description did not trigger on the user's phrasing). Input for the eval re-runs planned in 9.6, 10.9, 11.8; not fixed here (scope). [Superseded the same day: Ste added Sub-step 4.7, see below.]

## [2026-10-09] Skill-triggering diagnosis → Sub-step 4.7 (Ste: "the skills should trigger — why don't they?")
- Kept traces (sonnet, 4 failing cases; all 17 forge AA-MA skills were in the 55-skill listing):
  - aa-ma-plan/planning-standard → model invoked `aa-ma-plan-workflow` (sibling collision: both claim "plan with AA-MA").
  - plan-verification/bad-critical-path → no skill; read plan.md + reference.md itself. Its description has no "Use when" and says "Invoked by Phase 4.5 … and standalone /verify-plan" (reads as internal machinery); `verify-plan` also claims "verify an AA-MA plan".
  - execute-aa-ma-step/next-step → no skill; globbed and read tasks.md. The case prompt ("report … then stop") made it a Q&A answerable from one file; `aa-ma-execution` ("proactively use when detecting .claude/dev/active") overlaps too.
  - writing-for-agents/write-description → no tool call; wrote from knowledge. Leading words "Writing documents for agents" do not match "write the description for a skill".
- Decision (Ste: add 4.7 now): fix collisions by routing in descriptions (not `disable-model-invocation`, which would cut `Skill()` callers), rewrite the 8 descriptions, rephrase eval prompts, re-run evals vs the 14/24 baseline.

## [2026-10-09] M4.7 follow-up — the 2 remaining eval fails
- aa-ma-plan/first-phase: no Skill call; the model planned a tiny feature inline. Ste decided aa-ma-plan should fire only when AA-MA is named (a small feature can be planned inline); the case prompt now names AA-MA. Description unchanged.
- execute-aa-ma-step/sync-after-step: the skill fired and refused to mark 1.2 COMPLETE without running its criterion — correct behaviour; the rubric was wrong and now accepts it.

## [2026-10-09] M4 §6.8 decisions — fix all 8 WARNINGs (Ste)
- S1 (security): a LIVE hostile case `skill-escape` grants `Skill`, loads the forge plugin and tells the agent to invoke `retro` (pre-approves Bash/Write) and run a shell marker; `retro` was invoked, the marker never appeared, real `~/.probe` absent → skill `allowed-tools` do not add tools in a `claude plugin eval` session. A follow-up trace inspection was denied by the permission prompt and not retried; the bats graders are the evidence.
- C1 (8 one-line `evals/_lib/<fixture>.sh` wrappers) kept by decision: `claude plugin eval` fully resolves the case's `fixture.sh` symlink before running it (argv0 = the real `_lib` path), so a fixture name taken from the link name would be lost; one wrapper per fixture is the simplest correct form.
- C2/C4/F2/F3 are guards over currently-correct code; each proven by a temporary mutation (SKILL-MECHANICS.md +1 line, one case `max_turns: 13`, a `!`git status`` line in retro) → each failed, then restored.

## [2026-10-09] Milestone Completion: Milestone 4: Prompt-as-code checks + writing-for-agents fork
- Status: COMPLETE (Ste approved at §7.3, 2026-10-09; Gate: SOFT)
- Key outcome: forge skills are now checked as code (frontmatter schema, size ratchet) and exercised by 24 advisory `claude plugin eval` cases in a sandbox; writing-for-agents replaces write-a-skill; skill descriptions route each intent to one skill (evals 14/24 → 22/24, every skill triggers).
- Artifacts: tests/test_frontmatter_at_top.py, tests/test_prompt_size.py, tests/test_eval_cases.py, tests/skills/test_writing_for_agents_fork.py, tests/scripts/test_run_evals_sandbox.bats (+ fixtures), scripts/run-evals.sh, scripts/release.sh, scripts/install.sh, evals/ (24 cases, _lib scaffolds), tests/fixtures/evals/, claude-code/skills/writing-for-agents/, FORKS.json, 8 skill descriptions, ADR-0021, CHANGELOG, runbook, counts docs.
- Tests: pytest 2728 passed / 6 skipped / 0 failed; bats 398/398; shellcheck rc=0; LIVE sandbox pass; eval baseline 22/24 (sonnet, single run).
- Open / next: Sub-step 5.0 — merge via /sole-dev-merge, live install from main (sweeps the dead write-a-skill link), L-1315 probe lists writing-for-agents.

## [2026-10-09] M4 double-check decisions (report 2026-10-09T190311Z, Partially verified)
- Gaps: the 4.7 "24/24 on its last runs" sentence joined two partial runs (Contradicted); 4.5 Result Log cited moved fixture paths and "9/9" (stale); LIVE sandbox proofs are opt-in paid runs (disclosed limit, not fixed: by design, AA_MA_EVAL_LIVE=1).
- Ste: fix the records and take one fresh full run as the baseline of record → a9a638f; single run 22/24, skill-fired 24/24 ($2.97 est); the failing pair differs from the previous run (n=1 noise in result graders).
- Validator §7.2.5 WARNINGS_BUT_USABLE (6 WARN) back-filled inline before §7.3.

## [2026-10-10T22:39:24Z] Compaction Summary (auto-generated by hook)
- Active step at compaction: Sub-step 5.0: Post-merge of M4
- Snapshot saved to: ~/.claude/hooks/cache/compaction-snapshots/code-conventions-impact-snapshot.md
- Note: Context compacted. Reload AA-MA files to resume.

## [2026-10-11] M5 start — pre-execution validation and test design
- Tier 2 validator: WARN (no FAIL). Fixed in reference.md: re-measured sizes (sole-dev-merge 1057, execute-aa-ma-full 758; sub-step headings keep the plan-time figures), full reader list of the six SKILL.md files, content-preservation base.
- Decision (deviation from "pre-split file @ base SHA"): `test_split_preserves_content` compares each split commit with its parent, found by subject. Why: a fixed base vs HEAD would fail as soon as M7–M11 edit these files; rebase-merge rewrites SHAs, so the commit is found by its message. Same check (multiset ⊆, only link/TOC lines added), same pre-split content.
- Readers checked per L-041: codemem plugin-surface owns references/ under the skill node, so edges are unchanged; regen-generated run after each split confirms.

## [2026-10-11] M5 §6.6/§6.8 decisions
- §6.6 (3 agents): fixed shared `skill_text` helper, tighter split check (smuggled heading/link/pointer, order), whole-skill writer lint, extractor per-file reset, empty-ALLOWLIST assert (b61aba2). Disputed: checking only the split commit (later commits are ordinary reviewed edits); paths with spaces (fixed repo paths).
- §6.8 (5 agents, PASS_WITH_WARNINGS): fixes in 6a64cd2 (deep-linked stubs, imperative safety stubs, bash helper, CHANGELOG, counts).
- Deferred: execute-aa-ma-milestone and execute-aa-ma-full each ship a byte-identical `references/pre-execution-validation.md` (74 lines; full adds one paragraph). The duplication predates M5 (both SKILL.md held the same §1); merging into one shared reference is a content change, so it belongs to a milestone that edits these skills (M7–M11) or a follow-up, not to a behaviour-preserving split.
- Double-check (2026-10-11T064952Z, standard, fresh challenge subagent): Partially verified — F1 CHANGELOG "every section heading" false (grouped trailing sections share one stub), F2 terminal steps only in pointer prose (execute-aa-ma-milestone §9–§11, execute-aa-ma-full §8.1, aa-ma-plan Phases 0–3), F3 aa-ma-gate-python.bats:396 negative check still SKILL.md-only (an L-047 miss), F4 spec §II line 183 stale. Ste: fix all 4 + re-run evals → 9c03f05; df9142c widened one more SKILL.md-only check (`_resolution_snippets`) found by the L-047 mechanical sweep, and tightened L-047. aa-ma-deps.bats caught the first execute-aa-ma-full wording ("any failure … HALT" beside "dependency chains"); reworded to validation failures.

## [2026-10-11] GATE APPROVAL: Milestone 5: Split the six oversized prompt files (behaviour-preserving)
- Gate: HARD
- Approved by: Ste (AskUserQuestion, 2026-10-11)
- Criteria verified: 5/5
- Decision: APPROVED

## [2026-10-11] Milestone Completion: Milestone 5: Split the six oversized prompt files (behaviour-preserving)
- Status: COMPLETE
- Key outcome: the six oversized skills load as SKILL.md entry points under 500 lines with detail in references/; the split is proven verbatim per commit, executed fences unchanged, and every test that read the moved text still covers it.
- Artifacts: 6 SKILL.md + 28 references/*.md; tests/test_split_preserves_content.py; tests/skills/_helpers.py (skill_files, skill_text); tests/lib/skill_files.bash; extract_stage.sh, phase_6_8/gate-scans/deps/gate-python bats, rewire/canonical/planning-count/angle6/writing-for-agents/prompt_size pytest; CHANGELOG; spec §II; docs/lessons.md L-047.
- Tests: pytest 2774 passed / 6 skipped / 0 failed; bats 403/403; shellcheck rc=0; evals 11/12 (advisory).

## [2026-10-11] M6 — decisions during boundary review
- §6.6 quality review found the shell scanner blanked `$(…)` inside double quotes (CRITICAL, fixed 9edd103) — the hand-written scanner is kept (no stdlib tokenizer gives comment offsets + heredocs; shlex drops them), now a context stack with one opener/closer table.
- `# why:` accepted anywhere in the contiguous comment block above (plan said "line above"): a reason often spans lines; a blank line ends the block (pinned).
- Shell recognised by `.sh`/`.bash`, or by shebang only for extensionless paths, so unscannable files are never read (efficiency + no binary decode).
- WHY001 suppression set widened beyond the plan's four forms to ruff/flake8 file noqa, `pyright: ignore`, `nosec`, `&>/dev/null`, `>/dev/null 2>&1`, `|| :` — same intent (L-1319), measured 131 genuine hits repo-wide, no false positives in the sample.
- Deferred: the ruff-check/ruff-format hooks have the same filename-as-option hole the check-conventions hook had (pre-dates M6, extensionless python-shebang file named `--exit-zero`) → M8 (secops baseline). One-call `git diff` (N+1, 2.5 s at 322 files) — M1-deferred, still deferred. Shared markdown `_section` test helper (3 copies) — later touch. 7 eval scaffold scripts carry SC2312 — fixed when touched (D8).
- code-reviewer eval code-reviewer/what-comment does not discriminate at n=1 (control on the old prompt also passes) — kept as an advisory behaviour check; a discriminating grader needs the WARNING label or n>1.

## [2026-10-11] GATE APPROVAL: Milestone 6: Comments, docstrings, KISS lint (T8, T11 §3)
- Gate: HARD
- Approved by: Ste (AskUserQuestion, 2026-10-11)
- Criteria verified: 5/5
- Decision: APPROVED
- Evidence: test_ruff_config 14, test_check_conventions 84 (17 mutations caught), reviewer rules + eval case (advisory, non-discriminating at n=1 — recorded), CI canary at HEAD PR #26 run 38142145243 FAIL D103 + WHY001, CRITICAL_PATH_REVIEW + addendum; pytest 2866/0 failed, bats 403/403; §6.8 PASS_WITH_WARNINGS (0 CRITICAL, 7 WARNING fixed); double-check Partially verified → F1/F2 closed (fresh canary, addendum), F3 accepted as advisory.

## [2026-10-11] Milestone Completion: Milestone 6: Comments, docstrings, KISS lint (T8, T11 §3)
- Status: COMPLETE
- Key outcome: touched Python files now meet ruff D (google)/RUF100/PGH/C901/PLR0913; added lines are checked for unexplained suppressions (WHY001) and unreferenced TODOs (TODO001); code-reviewer WARNs on comment substance.
- Artifacts: pyproject.toml, scripts/check_conventions.py, .pre-commit-config.yaml, claude-code/agents/code-reviewer.md, docs/adr/0018 (Implementation line), CHANGELOG.md, evals/code-reviewer/what-comment/*, evals/_lib/py-review.sh, tests/fixtures/evals/py-review/stats.py, tests/{test_ruff_config,test_precommit_config,test_eval_cases}.py, tests/scripts/test_check_conventions.py, tests/skills/test_code_reviewer_warn_rules.py, docs/lessons.md (L-048).
- Tests: pytest 2866 passed / 6 skipped / 0 failed, bats 403/403 (cd64eda); touched-set 141 passed at HEAD; CI canary PR #26 FAIL D103 + WHY001.

## [2026-10-11] DECISION — drop SC2312; sweep SC2310 at the start of M7
- Approved by: Ste (after the M6 merge, a063a53)
- SC2312 (masked command-substitution status) made 116 of the 124 shellcheck findings that fall due when a .sh file is touched, mostly `echo "$(cmd)"` — noise relative to its value. Dropped from the hook; SC2310 (set -e off inside a condition) kept.
- With SC2312 gone, 8 SC2310 findings remain in 2 files (4 in claude-code/hooks/). They are swept in Sub-step 7.0, before 7.1, so M7's hook migration (7.3) starts from files that already pass the hook.
- Recorded as two Sub-step 7.0 acceptance criteria; plan.md unchanged (historical record).

## [2026-10-11] DECISION — hook log variable stays `CLAUDE_HOOK_LOG` (M7.0, validator W1)
- Approved by: Ste
- The plan named `AA_MA_HOOK_LOG` for aa-ma-log.sh, but `CLAUDE_HOOK_LOG` already ships: claude-code/hooks/ruff-format.sh:6, tests/hooks/ruff-format.bats:65, logging-and-comments references/bash.md:41, ADR-0019:70 ("the logging-and-comments contract"), CHANGELOG, claude-code-foundations.md.
- Chosen: keep `CLAUDE_HOOK_LOG`; no rename, no alias. Rejected: `AA_MA_HOOK_LOG` + a one-release alias (churns six shipped files for no user benefit).
- tasks.md 7.1 AC and reference.md Environment Variables corrected; plan.md unchanged (historical record).

## [2026-10-11] Sub-step 7.0 — SC2310 sites suppressed, not rewritten
- All 8 findings were deliberate: set -e is meant to be off in pre-compact-aa-ma.sh's fail-open appends, and uninstall.sh's manifest_slot_ok / slot_free_for_restore are pure predicates whose status is the answer. Rewriting (e.g. `now=$(ts)` outside the `||`) would make a date failure fatal and break fail-open — a behaviour change. Each site gets a narrow `# shellcheck disable=SC2310  # why: …`, matching the file's existing SC2088 style.

## [2026-10-11] Sub-step 7.1/7.2 — background security notice on aa-ma-log.sh
- A background commit-security review reported "sensitive-to-observability in claude-code/hooks/lib/aa-ma-log.sh" with no detail in the notice (body held only connector warnings).
- Self-review against that class found one real leak: masking ran AFTER the 8192-char cap, so a secret straddling the cut lost its tail and the fragment (too short to match) was logged. Proven RED in bash at 8928661 against shipped 5fc528b. Fixed in both libraries (mask an 8192+256 window, then truncate) in 0f4cf65.
- Checked and accepted: the hook name is not masked (always a code constant, not data — CR/LF stripped and capped); patterns cover provider tokens only (gitleaks rule ids, per plan); generic `password=` / AWS secret keys are out of scope.
- Design: one pattern source `src/aa_ma/secret_patterns.tsv` read at runtime by both sides (bash via the lib's real path → forge root, the aa_ma_gate pattern; Python via importlib.resources) instead of code generation — nothing to regenerate or drift; the parity test proves identical output.

## [2026-10-11] Sub-step 7.3 — second background security notice; closed-fd defect
- Second notice: "sensitive-data-in-logs in src/aa_ma/logsetup.py", again without detail. Probed empirically: a GitHub-PAT-shaped token in LOG_LEVEL, the message, the exception text and (JSON mode) stack_info → raw token count in output 0 (text) and 0 (JSON). No unmasked path found; noted, no change.
- Real defect found by the existing pre-compact EPIPE test, not by review: aa-ma-log.sh's fail_open_notice ran `jq` as a plain command, so with stdout closed it failed and `set -e` aborted the calling hook — fail-open broken. Fixed (d9ed690): every write in the library has a fallback, every function returns 0; a library-level bats case pins it.
- Decision: blocking hooks keep `exit 1` for infrastructure errors (helper/jq missing, bad stdin). Claude Code treats it as non-blocking, so the commit proceeds; changing it is out of 7.3's scope and would alter a blocking hook's behaviour. The header states it, and hook-headers.bats requires any `exit 1` to be labelled as an infra error.
- 7.3's grep AC spans `claude-code/`, whose only remaining hits are skills that 7.6 rewrites; verified at the milestone boundary rather than forcing 7.6 work into 7.3.

## [2026-10-12] Sub-step 7.5 — captured payloads scrubbed of identity (AC deviation)
- Approved by: Ste ("Proceed, also scrub session_id"; then "Also scrub scratchpad_dir")
- The AC said keep the real session_id/transcript_path. The repo is public and those fields carry the username and real session ids, so: session/prompt/tool_use ids → fixed placeholders, `/home/<user>` → `/home/capture`, `/tmp/claude-<uid>` → `/tmp/claude-capture`. Field names, shapes and every other value are as Claude Code sent them. Transcript contents were never read or committed.
- ExitPlanMode is unavailable in headless `-p`, so Ste ran one interactive plan-mode session. It overwrote 5 earlier captures with plan-mode equivalents (a Write of the plan file, a `cat`), so the Edit and commit pair was recaptured headless into a separate directory.
- Wiring: synthetic make_input/build_stdin helpers now derive from the fixtures rather than gaining a parallel test, so every existing case runs on the real envelope. A first mutation (rename tool_input) was vacuous because the helper re-sets the field; replaced by an unreadable-fixture mutant, which 8/8 hook bats catch.

## [2026-10-12] M7 §6.6 post-milestone review — 16 findings, fixes chosen by Ste
- Approved by: Ste. R1 = "Add generic rules to TSV"; fixes = "Fix WARN+small INFO".
- R1: log masking (`secret_patterns.tsv`) duplicated the report gate's set (`src/aa_ma/analysis/secrets.py`) with other ids and narrower coverage. Decided: two sets remain, because the gate needs lookbehind, named groups and `re.S`, which bash cannot express. The TSV adopts the gate's ids (a test pins the subset) and gains url-credential, generic-quoted and generic-env. The analysis ids are a published contract (ANALYSIS-CONTRACT.md); the TSV ids were new and unreleased, so the TSV moved.
- Found while fixing: private-key masking kept the key body in the log (header only). It now masks the base64 run, with or without END.
- Found while fixing: unbounded runs before a fixed token (`[A-Za-z0-9_]*` before a key word, `[a-z]*` before `://`) were O(n²) and hung the 100 KB timing test. Dropped or bounded, and the rule is now in the TSV header. As a result generic-env leaves the key-name prefix (`DB_[REDACTED:generic-env]`).
- Trade-off: `sk-key` keeps `{32,}`. Without the gate's lookbehind a 20-char minimum masks words like `risk-assessment-…`.
- Hot path re-measured (50 runs, temp HOME, real payloads), branch vs main: commit-signature 44.6 → 46.6 ms, security-static-check 27.9 → 29.9, commit-drift 41.3 → 45.2 (was ~+15 ms each before the fix); ruff-format on a non-.py edit 4.7 → 1.8 ms.
- Not fixed: E4's `printf %(…)T` would print `+0000` and break the `date -Is` line contract, so only the mkdir guard was taken. Q2 sites predate M7 (git blame), so they are out of scope. Deferred to TODOS.md: E5, E7, E8, R2.

## [2026-10-12] M7 §6.8 post-impl review — PASS_WITH_WARNINGS (0 CRITICAL / 8 WARNING / 10 INFO)
- Approved by: Ste ("Fix 6, defer 2").
- The security auditor found the §6.6 masking rules still missed common shapes: quoted values, `--password x`, `Bearer`, and URL passwords with `@` or `/`. That mattered more because `HOOK_DEBUG=1` now writes whole commands to hooks.log on disk. Fixed both ways:
  - the rules were widened;
  - debug lines carry only a command's length and first 120 characters (`AA_MA_DEBUG_CMD_CHARS`), so a mask miss in the tail never reaches disk.
- `bearer-token` is the one log-only rule id, an exception to "ids follow the report gate": report files rarely hold HTTP headers. The subset test names the exception.
- Deferred to TODOS: one aa-ma-log.sh loader (C-W1), the cap and overlap in one place (F-W1), CR/LF flattening in text-mode CLI logs (S-I).

## [2026-10-12] Correction: debug lines carry no command text (third background security notice)
- A background review flagged sensitive-data-in-logs in aa-ma-parse.sh (no detail given). Probed live: the 120-char prefix kept `curl -u admin:hunter2`, `mysql -phunter2` and `sshpass -p hunter2` in hooks.log, since no mask pattern can know every CLI secret form.
- Fix (2b6be1e, RED f644447): `aa_ma_debug_cmd` logs `<label> (<n> chars, first word '<word>')` (word capped at 32, private constant `_AA_MA_DEBUG_WORD_CHARS`). This supersedes the "first 120 characters" in the §6.8 entry above.

## [2026-10-12] Double-check (Partially verified) remediation — Ste: "yes and fix the security warnings too"
- F1: `aa_ma_debug_cmd` skips leading `NAME=value` words. A bounded generic-env row masks `*SECRET*|*PASSWORD*|*PASSWD*|*TOKEN*|*KEY*=` env assignments.
- F2: readlink -f falls back to the path as invoked (macOS < 12.3) in aa-ma-parse.sh, plan-skip-warn and ruff-format; skip-warn stubs log_warn; pre-compact is fail-open on an unset or unwritable HOME.
- Security (4th background notice): the `${HOME:-/tmp}` fallback added in f8f7220 was a symlink-attack surface (append into a world-writable dir). Replaced in 4544060: with neither CLAUDE_HOOK_LOG nor HOME, lines go to stderr and nothing is written. A test forbids `:-/tmp` in the library. My probe-created /tmp/.claude (probe lines only) was removed.
- §6.8 security INFO items closed: text-mode CLI logs flatten CR/LF (logsetup formatMessage); ruff-format's header states its trust boundaries (absolute PATH entries trusted; repo-sourced findings reach the model JSON-escaped and capped).
- F4 CHANGELOG SC2312 corrected; the logging skill points at real files (pre-compact.bats, aa-ma-log.sh) instead of a guard-protected-dirs.sh absent from the repo. plugin-surface gains an ON_DISK skill→hook edge.
- Left as is: plan-skip-warn reads `${HOME:-/tmp}/.claude/runtime` (pre-M7, read-only; it can only raise an advisory warning).
- Process note: the pre-compact HOME-unset test was committed with its GREEN (seen RED first). Lesson L-049 added, with a recurrence entry.

## [2026-10-12] GATE APPROVAL: Milestone 7: Logging standard (T9) + hook contracts (T15 §7)
- Gate: HARD
- Approved by: Ste
- Criteria verified: 6/6 (milestone) + 8/8 sub-steps
- Evidence: bats 452/452, pytest 2968 passed/6 skipped/0 failed at 190508e. §6.3 MEDIUM (no HIGH). §6.6: 16 findings (fixed or deferred to TODOS). §6.7 ENG gate PASS; DIAGRAM_VERIFIED edges=25 phantom=0. §6.8 PASS_WITH_WARNINGS (6 fixed, 2 deferred). Double-check Partially verified → remediated → Verified (re-check 2026-10-12T104810Z). CRITICAL_PATH_REVIEW addendum after 4544060.
- Decision: APPROVED

## [2026-10-12] Milestone Completion: Milestone 7: Logging standard (T9) + hook contracts (T15 §7)
- Status: COMPLETE
- Key outcome: one masked, fail-open logging library for hooks (aa-ma-log.sh) and CLIs (aa_ma.logsetup) sharing one pattern file; every hook states its Event/Mode/Exit/Fail-open contract and is tested against real captured payloads and a fault matrix.
- Artifacts: claude-code/hooks/lib/aa-ma-log.sh, src/aa_ma/logsetup.py, src/aa_ma/secret_patterns.tsv, tests/fixtures/hook-payloads/ (7), tests/lib/hook_payloads.bash, tests/test_hook_payloads.py, 9 hook headers, ruff-format.sh rewrite, logging skills revised.
- Tests: bats 452/452, pytest 2968 passed/6 skipped/0 failed.

## [2026-10-12] M7 sole-dev-merge Stage C/D — 1 HIGH, 1 MEDIUM, 7 LOW fixed or disputed (Ste)
- C1 HIGH: `date -Is` is GNU-only, and a failed stamp aborted set -e hooks. Fixed with a fallback chain (UTC Z form, then `unknown-time`).
- C1 MEDIUM / C2 LOW: a quoted env value's tail leaked as the debug "first word". Only a plain program name is logged now, `?` otherwise.
- LOWs fixed:
  - a new hooks.log is 600 in a 700 dir (an existing file keeps its mode);
  - the pattern loader falls back to a one-level readlink;
  - traceback continuation lines are indented;
  - an empty LOG_FORMAT is treated as unset.
- Disputed (Ste: "Keep both"):
  - LogRecord mutation stays: the 7.2 AC requires it, and it guards other handlers.
  - SECRET_PATTERNS stays: Contract API, first caller M10.
  - Bandit hits in tests/: out of CI scope (src/ = 0).
- RED 8ec4613, GREEN 44defcd. Mutations: umask 1/1, date fallback 2/2. bats 457/457, pytest 2970 passed/6 skipped/0 failed.
- Fifth background security notice (aa-ma-parse.sh, during the PR's CI run). Truncating the debug first word to 32 chars happened *before* masking, which left `ghp_…` / `sk-ant-…` prefixes too short for their rules, so they were logged (probed). Fix: a first word longer than 32 is logged as `?` and is never truncated. RED d0ac20e, GREEN 1f33194. This is the same class as the §6.6 cap-straddle fix in aa-ma-log.sh (mask before cut). L-049's rule covers it: probe every cut-then-mask path.

## [2026-10-12T12:21:53Z] Compaction Summary (auto-generated by hook)
- Active step at compaction: Sub-step 8.0: Post-merge of M7
- Snapshot saved to: ~/.claude/hooks/cache/compaction-snapshots/code-conventions-impact-snapshot.md
- Note: Context compacted. Reload AA-MA files to resume.

## [2026-10-12] M8.0 — live check found a dead M2 hook (ruff-format socket stdin)
- `ruff-format.sh` used `$(</dev/stdin)`. Claude Code delivers stdin on a socket, where opening `/dev/stdin` is ENXIO, so the hook did nothing on every live edit since 563cee4. bats fed it from files and stayed green. The only trace was in the session transcript's `hook_success` stderr.
- Fix `payload=$(cat)` (matches commit-signature / commit-drift / security-static-check). The builtin `read -d ''` was rejected: it reads a socket one byte per syscall (measured 1.9 s vs 34 ms at 2 MB; Edit payloads carry the original file).
- Decision (Ste): ship as a separate fix PR #29 to main ahead of M8 (it blocked 8.0's live criterion); rebase-merged. Lesson L-050.
- M8 AA-MA records live on the M8 branch (main checkout kept clean; no pushes to main for records).

## [2026-10-12] M8.1 — Ruff vs Bandit decision
DECISION ruff-only () — approved by Ste
- Evidence: `docs/research/code-conventions-impact-ruff-vs-bandit.md`. Bandit 39 hits / 5 IDs (B101 1, B404 11, B603 15, B607 9, B608 3) on src+packages+scripts. Each one has a Ruff S hit on the same call; line offsets come only from how each tool anchors a multi-line call. Ruff reports 8 more because it ignores `# nosec`; those get `noqa`+`why` in 8.2.
- 75 Bandit tests: 71 map (58 stable, 13 preview S401–S415); GAPs B613 (→ PLE2502, 0 hits), B614/B615/B703 (no torch/HF/django imports).
- B404 (A4): excluded. S404 is preview-only and flags imports, not calls (S603/S607 cover every call; `codemem/cli.py` imports only for `CalledProcessError`). Revisit trigger: torch / huggingface_hub / django enter deps, or S404 stabilises.
- Rejected: fallback `-t B404 -ll` would gate nothing (B404 is LOW).

## [2026-10-12] M8.2 — Ruff S scope decisions (Ste)
- tests/** S ignores: S101, S108, S603, S607 (+ S110, pre-existing). This deviates from the plan's "ONLY S101". Ruff S over tests/ found 327 hits in 50 files, mostly subprocess calls that tests make on purpose. S602/S604/S105/S106/S307/S608 stay on in tests.
- D8 debt on the 16 files touched for per-site noqa: paid down (format, docstrings). The 10 C901/PLR0913 get noqa+why and a TODOS entry, with no refactor inside a security milestone. Rejected: per-file-ignores (would hide new S60x in those files) and a full refactor (behaviour risk).
- Found during the pay-down: codemem `owners` swallowed blame exceptions silently (L-1319). Now one warning per failure.

## [2026-10-12] M8.3 — gitleaks allowlist approved (Ste)
- 8 fingerprints, not the planned 3 (M7 added 5 fixture hits). Kept the 2 local-only-ref entries so the local `--all` scan stays clean. Fixtures not rewritten: history hits would need fingerprints anyway.
- The pre-commit hook takes its definition from the upstream repo at a frozen SHA, `gitleaks-system`, not `golang` (no Go toolchain needed). The touched CI job skips it; the gitleaks job covers history.

## [2026-10-12] M8.4 — A6 resolution
- `uv audit` is experimental in uv 0.12.3, so the gate is pip-audit 2.10.1 over a hashed `uv export`. Ignores live in `.pip-audit-ignore` with an expiry date; a test fails expired ones. The 13 packages / 72 vulns are triaged in 8.5.
- Local env defect, not repo work: `~/.local/share/uv/python/cpython-3.13.5` has no `venv` package (looks damaged). Left untouched; reinstall with `uv python install 3.13 --reinstall` if you want local pip-audit via `uv run`.

## [2026-10-12] M8.5 — dependency triage decision (Ste)
- 3 advisory IDs ignored to 2027-01-12, not migrated now: fastmcp 3.x requires watchfiles>=1 against the TUI`s <1 pin. That cascade belongs outside a security CI milestone. The advisories are unreachable (stdio-only server, no OAuth proxy, no Gemini install, diskcache unused). The expiry plus the test forces the TODOS migration.
- Rejected: a blanket `--upgrade-package` (it silently moved mcp to 2.x and downgraded fastmcp); a 30-day expiry.

## [2026-10-12] M8.6 — security-static-check design (circuit breaker; Ste)
- DECISION whole-file Ruff S in the commit hook — approved by Ste. Three background review rounds found bypasses in every "only findings this commit introduced" filter: in-file noqa, start-row anchoring, a first-line text key, jq --arg E2BIG, an added `++x` read as a diff header, repo color.diff. Git diff, Ruff and ast number lines differently, so no such mapping is attempted. A pre-existing site in a touched file needs `[security-bypass: <reason>]`. In this repo that is mcp_tools/__init__.py (3× S608) and indexer.py (1× S608).
- `--ignore-noqa`: in-file suppression is repo-controlled; the bypass marker is the auditable escape.
- Fail closed (exit 2) when ruff or git error on a file, the JSON is unreadable, or the diff has no parsable hunk. Only "no ruff at all" stays notice + exit 0 (the plan's contract).
- S102 added to D12's `S602,S604,S307,S608,S301` so exec() keeps the coverage its regex had.
- Stage C runs Ruff S without --isolated (repo per-file-ignores apply, like any lint); severities come from the matching Bandit test's default tier; an unknown code is HIGH.

## [2026-10-13] M8.7 — approvals (Ste)
- ADR-0022 SecOps baseline: Accepted, approved by Ste.
- senior-secops removal approved by Ste after reading the files: a template stub (scanners hard-code zero findings), already off via skillOverrides. Backup /home/sjnewhouse/.claude/backups/cci-m8-senior-secops-20261013-094804.tgz, 7/7 files verified. Removed by Ste with `!` because guard-protected-dirs.sh blocks a recursive rm under ~/.claude/skills; that guard was not bypassed.

## [2026-10-13] M8 §6.6 / §6.8 decisions (Ste)
- §6.6: fixed the CRITICAL timeout fail-open (per-line forks) plus the empty/chmod false block, the git-diff skip, the hot path and the text drift (e1b5c88). Duplicated ruff resolution, per-file forks, CI sync cost and test-helper duplication were acknowledged.
- §6.8 (0 CRITICAL / 16 WARNING): "Fix A–G, defer 2". See impl-review M8.
- DECISION security-static-check is a best-effort guardrail, not a security boundary — approved by Ste. Six review rounds showed that command-text parsing cannot see every commit form. Named non-goals live in the hook header and the ADR-0022 amendment. Enforcement is CI plus the repo's pre-commit. Upgrade path is TODOS P2.
- D8 exception, recorded so "no logic change in a security milestone" stays true: the codemem owners blame swallow now logs a warning (6fe1770, L-1319). It is the only logic change in the D8 pay-down; it is tested and mutation-checked.
- TDD audit WARNING accepted: 964e5b7 and db3c46a rewrote their tests in the same commit as the behaviour change. Every later hook change had a RED commit first.

## [2026-10-13] GATE APPROVAL: Milestone 8: SecOps CI baseline (T10)
- Gate: HARD
- Approved by: Ste
- Criteria verified: 8/8 (milestone) + 9/9 sub-steps (8.0–8.8)
- Evidence: pytest 3004 passed/6 skipped/0 failed, bats 505/505 at 0eaa6c9; CI run 38377287777 9/9 green. Criterion 2 via approved deviation (tests/** S101/S108/S110/S603/S607); criterion 3 via 8 approved gitleaks fingerprints. §6.3 MEDIUM (no HIGH). §6.7 ENG gate PASS; DIAGRAM_VERIFIED edges=25 phantom=0. §6.8 PASS_WITH_WARNINGS (0 CRITICAL / 16 WARNING / 19 INFO; A–G fixed, 2 deferred to TODOS). Double-check Partially verified (F1 stale CPR) → remediated by the CRITICAL_PATH_REVIEW addendum at 5c44a49.
- Decision: APPROVED

## [2026-10-13] Milestone Completion: Milestone 8: SecOps CI baseline (T10)
- Status: COMPLETE
- Key outcome: bandit replaced by Ruff S in CI and the commit hook (whole-file, forge-pinned, best-effort guardrail per the ADR-0022 amendment); gitleaks over full history plus pre-commit; pip-audit over the hashed lock with expiring ignores; Dependabot for actions and uv; senior-secops replaced by the secops router skill.
- Artifacts: claude-code/hooks/security-static-check.sh, .github/workflows/security.yml, .github/dependabot.yml, .gitleaksignore, .pip-audit-ignore, tests/security/ (4 files), claude-code/skills/secops/, docs/adr/0022-secops-baseline.md, sole-dev-merge Stage C/D references.
- Tests: bats 505/505, pytest 3004 passed/6 skipped/0 failed.
- Post-merge (outside the milestone): scripts/install.sh; local CLAUDE.md BANDIT_BIN→RUFF_BIN row, CI section and 39-skill count; remove the M8 worktree.

## [2026-10-13] SCOPE CHANGE: Milestone 9 — `Test-Command-Pass-Regex:` un-deferred (Ste)
- Source: checkmeplans review, ooh_ideas/research/04-work-priorities-roadmap.md decisions G2 + G9; handover .claude/handovers/2026-10-13-m9-scope-change-and-m10-stop.md (evidence E1–E17 re-run and matching).
- Why: plan.md:732 deferred the override as "YAGNI until a non-pytest plan appears". G2 confirms Ste will ship R (testthat), Nextflow (nf-test) and others, so fence 3 as planned can never PASS those plans.
- Change (small): optional `Test-Command-Pass-Regex: <ERE; group 1 = pass count>` in reference.md (merge-base copy, same as Test-Command). If set: PASS iff rc==0 AND the LAST output line matching it (bottom-up scan; bash `[[ =~ ]]`, no eval) yields an all-digit BASH_REMATCH[1] = N. Invalid ERE (rc 2; bash also prints an error on stderr, which the fence must contain), empty value, or non-numeric group 1 → BLOCKED. The TEST_CMD character-rejection rule does not apply to the regex (never executed). Default pytest path unchanged. Provenance line format unchanged (`passed=N cmd=…`).
- Why "last matching line", not "final line": real testthat 3.2.3 via Rscript ended with a praise line in 1 of 8 passing runs (handover E16).
- Not added: exit-code-only mode (KISS).
- Flaky tests (plan Risk 3, raised by the pre-execution validator): no auto-rerun. A failing run is BLOCKED; fix the test or re-run the gate by hand (Ste).
- Tests: +4 bats cases in tests/hooks/test_tests_verified.bats (custom Pass-Regex honoured; trailing praise line; rc 0 + FAIL>0 summary → BLOCKED; invalid regex → BLOCKED). The handover's P1 said +3; its P4 lists 4.
- 9.5: counted as met by reference.md:7 `Test-Command: uv run pytest` (Ste).
- Approved by: Ste (session m9tostart, 2026-10-13, AskUserQuestion)

## [2026-10-13] ADR APPROVAL: ADR-0023 Tests-verified gate (§6.7 fence 3)
- Approved by: Ste (AskUserQuestion, session m9tostart)
- Decision: APPROVED — Status Accepted (ADR + INDEX)
- Records: thin fence + skill script (500-line cap); merge-base Test-Command / optional Pass-Regex (bash ERE, last matching line, numeric group 1); argv via shlex, metacharacters rejected, 540 s timeout; no auto-rerun; opt-out `Test-Command: none — <reason>` with `GATE APPROVAL: Test-Command none — <heading>` + `Decision: APPROVED` (HEAD context-log, §7.1 convention; Ste kept it); symlinked provenance path refused; other appenders → TODOS P1.

## [2026-10-13] Milestone 9 boundary: §6.3 impact analysis and §6.6 review (Ste decisions)
- §6.3 consolidated impact (main...HEAD, 21 files): Overall MEDIUM, no HIGH.
  - `scripts/tests-verified.sh` (new): one caller, the §6.7 fence 3 block. LOW.
  - `SKILL.md` §6.7/§7.1: §7.1's approval check is now STRICTER (block-scoped, exact title, last block decides). It could reject an approval that only passed through the old `grep -A8` bleed. Checked against this plan's real context-log: all 7 HARD approvals (M1–M3, M5–M8) still pass; M9 correctly does not yet. MEDIUM (contract tightened on purpose).
  - `hooks/lib/aa-ma-parse.sh`: +`aa_ma_has_gate_approval` (Exports header updated); no existing function changed; sourced by every hook. LOW.
  - `plan_parsers.py`: `CANONICAL_TDD_WAIVERS` keeps the same 5 values (187 consumer tests pass). LOW.
  - `engineering-standards.md` (auto-loaded rule): the generated TDD block and the §5 "Tests written and passing" row. LOW.
  - Three skill files now point the TDD skip rule at §2 instead of the retired "infrastructure-only" list (guarded by `test_no_skill_restates_the_retired_skip_list`). LOW.
  - Docs, ADR, spec, template, scribe, pyproject comments, `regen-generated.sh`, `TOC_ALLOWLIST` −1. LOW.
  - Post-merge: `install.sh` (the spec is copied, not symlinked).
- §6.6: three reviews (reuse, quality, efficiency). 0 CRITICAL. Verified WARNINGs fixed.
  - A (Ste: shared helper, fix both): approval bleed in fence 3 and the existing §7.1 → `aa_ma_has_gate_approval`. RED 6769f2c, GREEN 774ee15. Passes under mawk 1.3.4.
  - B (Ste: HEAD fallback): a reference.md new on the branch now uses its HEAD copy (or the uncommitted working-tree copy), with a notice. Existing plans keep the merge-base guard.
  - C–F (Ste: fix now), RED 6f9992e, GREEN d5ae802:
    - the provenance append is checked, and the symlink is re-checked at append time;
    - the Pass-Regex scan is filtered by grep (also sees a last line with no newline);
    - `timeout -k ${AA_MA_TEST_KILL_AFTER:-30}`, and 137 counts as a timeout;
    - rc 126/127 is named as "could not run";
    - the overclaim is reworded;
    - the gate-fences.md backtick and "above" wording are fixed;
    - the §5 checklist row is updated;
    - the count loop is unstringly-typed.
  - G → TODOS: process-group kill, `setsid` children, comment/fence-aware reference.md parsing, a shared default-branch helper. The generator in a test module is acknowledged as the existing repo pattern (test_plugin_surface.py).
  - Also fixed under §6.3: the stale TDD skip list in three skills (RED/GREEN a58c5a4), and a TOC for the touched SKILL_INTEGRATION.md.
- Tests: test_tests_verified.bats 35/35; aa-ma-gate-approval.bats 10/10; mutation 11/11 killed (one false kill from an unescaped sed `&` was caught and re-run as a valid mutant); full bats 555/555, pytest 3010/6/0, `draw --check` OK.

## [2026-10-13] §6.8 OVERRIDE: Milestone 9 — C1 (future-proofing) Accept
- Approved by: Ste (AskUserQuestion)
- Decision: ACCEPT — ADR-0023 drifting counts removed (449cb14). WARNINGs 1–6 fixed now (Ste: "Fix 1–6 now"); remaining INFOs → TODOS or accepted (impl-review.md).

## [2026-10-13] GATE APPROVAL: Milestone 9: Testing gate `TESTS_VERIFIED` (T11 §5)
- Gate: HARD
- Approved by: Ste
- Criteria verified: 7/7 (milestone) + 8/8 sub-steps (9.0–9.7)
- Evidence: test_tests_verified.bats 39/39; aa-ma-gate-python.bats + test_diagram_verified.bats green and unchanged vs 1ff3178; test_tdd_waiver_doc_sync.py 5/5 (the 5th, retired-skip-list, added RED 3ff786f → GREEN a58c5a4 after the 4/4 in 9.4); pyproject clean of coverage/perf claims; ADR-0023 Accepted + INDEX row; reference.md Test-Command: uv run pytest; CRITICAL_PATH_REVIEW addendum at 036319d. Full bats 561/561, pytest 3010 passed/6 skipped/0 failed; CI run 38418957143 9/9 green. §6.3 MEDIUM, no HIGH. §6.6 C–F fixed, G → TODOS. §6.7 fences 1–3 PASS (DIAGRAM_VERIFIED edges=25 phantom=0; TESTS_VERIFIED passed=3010, merge-base 1ff3178 — fence 3 dogfooded). §6.8 PASS_WITH_WARNINGS (1 CRITICAL accepted + fixed in 449cb14; WARNINGs 1–6 fixed).
- Decision: APPROVED
- Correction (validator, after approval): the approval prompt said §6.3 LOW; the record (provenance §6.3 IMPACT) says MEDIUM, no HIGH. Corrected above; reported to Ste.
- Correction (recount): full bats at 036319d was 543/543, not 561/561 (`bats --count` on `git archive 036319d`); every test passed either way.
- Re-confirmed: Ste reviewed the §6.3 detail (MEDIUM, no HIGH) and the approval stands (2026-10-13).

## [2026-10-13] Milestone Completion: Milestone 9: Testing gate `TESTS_VERIFIED` (T11 §5)
- Status: COMPLETE
- Key outcome: §6.7 fence 3 runs the plan's Test-Command (merge-base reference.md) and refuses COMPLETE without a parsed pass count, writing `TESTS_VERIFIED — <heading> — passed=N cmd=…`; §7.1 and fence 3 share the block-scoped `aa_ma_has_gate_approval`; TDD-waiver list single-sourced.
- Artifacts: claude-code/skills/execute-aa-ma-milestone/{SKILL.md,scripts/tests-verified.sh,references/gate-fences.md,references/context-and-todos.md}, claude-code/hooks/lib/aa-ma-parse.sh, src/aa_ma/plan_parsers.py, claude-code/rules/engineering-standards.md, scripts/regen-generated.sh, docs/adr/0023-tests-verified-gate.md (+INDEX), docs/spec/aa-ma-specification.md, docs/templates/reference-template.md, claude-code/agents/aa-ma-scribe.md, execute-aa-ma-full/SKILL.md, aa-ma-plan-workflow/references/SKILL_INTEGRATION.md, pyproject.toml (comments), TODOS.md; tests/hooks/test_tests_verified.bats, tests/hooks/aa-ma-gate-approval.bats, tests/test_tdd_waiver_doc_sync.py, tests/test_prompt_size.py.
- Tests: bats 561/561, pytest 3010 passed/6 skipped/0 failed; CI run 38418957143 9/9 green.
- Commits: CRITICAL_PATH_REVIEW addendum f99dd5a; §6.7 evidence 55d4f61; completion 5e5325e.
- Next (handover Part C): STOP before Milestone 10 — Q1 roadmap re-baseline, Q2 codemem freshness (B1 as Milestone 15 vs separate plan), Q3 pull T9 forward (addendum §11).

## [2026-10-13] PR #37 sole-dev-merge Stage C/D (Ste decisions)
- Stage C: C1 code-reviewer 1 MEDIUM / 3 LOW; C2 security-auditor 1 MEDIUM / 2 LOW (its fence LOW = C1's MEDIUM); C3 Ruff S 0; C4 ShellCheck 0.
- MEDIUM 1 (Ste: Apply): `aa_ma_has_gate_approval` flipped fence state on any ``` / ~~~ line, so a nested fence let a pasted APPROVED example after a real REJECTED block pass §7.1 and the fence-3 opt-out (reproduced). Fix: a fence closes only on its own character at >= its own length with nothing after (CommonMark), counted by hand for mawk. RED ee80fe3 → GREEN 705413b; gawk + mawk 15/15.
- MEDIUM 2 (Ste: Apply NOTE + ADR wording, no BLOCK): with no origin/HEAD the merge-base guard reads a local ref this session can change (on main, the plan is self-authored). Refined trigger, evidence-led: the approved "merge-base == HEAD" condition fires on every fresh clean branch and misses nothing origin/HEAD does not already cover, so the NOTE keys on the local fallback instead. The line gains `inputs: local <ref> (no origin/HEAD) — ` before `passed=`; ADR-0023 + gate-fences.md reworded.
- LOW x5 → PR body reviewer notes (coloured pytest output BLOCKs a pass; trailing empty argv dropped; 124/137 'timed out' wording; rename-plan → HEAD fallback; fence LOW dup).
- All 8 real HARD approvals in this plan still pass. Pre-existing, not a regression: completed understand-codebase-skill M3 writes `Decision: **APPROVED**` (bold value), which neither the old grep nor the helper accepts; archived, never re-gated.

## [2026-10-13] DECISION: Part C stop after Milestone 9 (handover 2026-10-13, Q1–Q3) — Ste
- Q2: **B1** — codemem freshness (report 03 T2–T6) folds into CCI as `## Milestone 15: Codemem freshness (report 03 T2–T6)`; M10 `Dependencies: Milestone 9, Milestone 15`. Precondition: prove with a fixture that a dependency on a higher-numbered milestone passes `aa-ma-gate` and `tests/test_active_plans_canonical.py` before editing plan/tasks (else B2 renumber).
- Q3: **T9 and T8** pulled forward into Milestone 15 (T9 user-scope codemem MCP via stable symlink + global git excludes; T8 routing rule). Evidence (addendum §11, verified): `which codemem` empty; plan.md:792 M10 hook "codemem absent from PATH → one notice". M10's contract decides how the hook resolves codemem.
- Q1: **re-baseline** the roadmap week targets from actuals (CCI M1–M9 in ~6 calendar days vs ~1 day/week planned).
- T12 (X4 → TODOS.md) runs at the start of Milestone 15. M10 not started.

## [2026-10-13] SCOPE CHANGE: Milestone 15 — Codemem freshness (report 03 T2–T6) added before Milestone 10 (Ste)
- Why: G13 — M10/M11 build `IMPACT_VERIFIED` on codemem; its index was 263 commits stale and `codemem refresh` is a placeholder (report 03 §2; verified `cli.py:80-94` "M2 placeholder"). A gate computed from a stale index gives confidently wrong answers.
- What: `## Milestone 15: Codemem freshness (report 03 T2–T6)` appended (B1, never "9b"); sub-steps 15.0–15.9 = M9 post-merge + T12, PROTOTYPE (refresh cap), T2, T3, T4, T5, T6, T7 (Ste added), T9, T8 (Ste: both). Gate HARD, Audit-Profile full, Critical-Path hook-modification, Prototype-Required YES, 6 days, 75%.
- M10: `Dependencies: Milestone 9, Milestone 15`; 10.0 becomes "Post-merge of M15"; its TESTS_VERIFIED AC no longer claims the first live run (fence 3 ran live at the M9 gate). plan.md: M15 Contract, regenerated Milestone graph (15 edges), effort row (total 25 → 31 days), §8 N.0 mapping.
- B1 precondition proven before the edit (fixture: M10 → Milestone 15): aa-ma-gate reads M10 and M15; `aa_ma.deps check` rc 0; graph edge M15 → M10; advisory "Milestone 10 is ACTIVE but Milestone 15 … PENDING"; canonical lint 0 violations. After the edit: gate reads M15 (HARD, hook-modification, YES, 10 PENDING), deps check rc 0, test_active_plans_canonical 26/26, aa-ma-lint-views edges=25 checked=25 phantom=0.
- Excluded: T10 (Python parity), T11 (X3 evals) — later work.

## [2026-10-14] DECISION: M15 scope-change PR review (sole-dev-merge Stage D, Ste)
- Stage C findings (SLUG 1791951220): code-reviewer 2 HIGH / 6 MEDIUM / 8 LOW; security-auditor 0 CRITICAL / 3 MEDIUM / 4 LOW. All HIGH/MEDIUM verified against the files before the panel.
- Applied (HIGH): Sub-step 15.10 CRITICAL_PATH_REVIEW added (§8 standing rule; every Critical-Path milestone ends with one). The live `CODE_INTEL_REFRESH` check moves from M15 to M10's gate and 10.0; M15's evidence is 15.6's dry run (D7: the executor gains the step after merge + install.sh — the TESTS_VERIFIED M9→M10 reasoning).
- Applied (MEDIUM, plan consistency): §2a M15 row; §13 draws incremental.py, codemem post-commit.sh, codemem.md and the codemem README (`aa-ma-lint-views --coverage` 4 → 0 UNDRAWN_PATH); 10.0 greps the skill directory, not SKILL.md; 15.5 also depends on 15.3, 15.8 on 15.5; §7 rollback row for M15's outside-repo moves.
- Applied (MEDIUM, security): 15.5 uses a sidecar SHA only when it matches `^[0-9a-f]{40}$`, after `--end-of-options` (sidecars are repo-controlled); a codemem result with `stale` ≠ `false` never satisfies M11 fence 4 (G13).
- Applied (MEDIUM, security, D13 refined): `~/.local/share/codemem-plugin` targets a dedicated forge worktree on `main`, never the working checkout; session-start checks the link target.
- Applied (cheap LOWs): Engineering Standards counts (12 hook-modification milestones, 4 prototypes, 15 milestones); Flow preamble; tasks.md N.0 numbering note; superseded note on M9's "first to write TESTS_VERIFIED"; exact greps for the codemem.md placeholder and the graphify description. Citation correction: G13 is in the ooh_ideas roadmap (report 04), not report 03 (also in the 2026-10-13 SCOPE CHANGE entry above).
- Reviewer notes (LOW, not applied): milestone title "(report 03 T2–T6)" understates T2–T9 + T12 (kept: renaming is cheap only before 15.1 writes a token — decide at 15.0); refresh.pid kill on a repo-writable PID (pre-existing; 15.4 rewrites the file); flock lock location; post-commit `graphify update` code-only; private paths named in a public repo.

## [2026-10-14] M15 start — title rename + pre-exec validator (Ste)
- 15.0 HITL: Proceed. Title renamed `(report 03 T2–T6)` → `(report 03 T2–T9)` (Ste), before any milestone token exists; sites: tasks.md heading + 15.1/15.10 ACs, plan.md §13 node + §M15 heading. Context-log entries above keep the old title as history.
- Pre-exec validator: WARN, 0 FAIL, 7 WARN. Applied: (1) 15.10 depends on 15.6, 15.7, 15.9 (its evidence); (2) report-03 decision ids prefixed `R03-` inside M15 (they clashed with this plan's D7/D10/D12; D13/D14 were undefined here); (3) 15.2 AC names the stale `cli.py` "placeholder" docstrings; (4) reference.md gains M15 facts; (5) provenance gains the scope-change line; (6) plan.md counts/order (fifteen milestones; M1 → M9, M15, M10 → M14); (7) Contract rationale for install.sh (15.8 link) and SKILL.md (pointer line only).

## [2026-10-14] M15.1 PROTOTYPE verdict — bounded refresh (Ste: Accept both)
- Decision: subprocess cap (not a thread): `lockf` is per-process, so threads in one MCP server do not exclude each other; a thread cannot be killed; refresh parsing holds the GIL. Spawn only when an in-process pre-check (`last_sha` vs HEAD + `git status --porcelain -uno`, ~10 ms on the forge) says stale, so the 125 ms subprocess start is not paid per query.
- Kill safety holds today (3 kill points, all recover to cold-build counts). No new lock or WAL code needed for the kill AC.
- Plan change (verdict-changes-plan: YES): the full-rebuild fallback unlinks `index.db` in place and every concurrent reader raises for the whole rebuild. 15.2 builds to a temp DB and swaps with `os.replace`. Open risk owned by 15.2: a long-lived reader holding the old `-wal` across the swap.
- Alternatives rejected: thread + in-process mutex (GIL contention, no kill); defer the swap to TODOS (readers keep failing during every full rebuild, which the cap would now trigger more often).

## [2026-10-14] M15.2 security review — fixes and a Contract deviation
- Background security review of the pushed 15.2 commits: (1) `python -m codemem.cli` with cwd = repo root imports a repo's own `codemem/` (code execution in the MCP refresh); (2) `tree_sig`/`last_sha` writes follow a committed symlink; (3) `git status` runs a repo's `core.fsmonitor` / clean filters. Probe added: `git ls-files` also runs `core.fsmonitor` (pre-existing, every build); `rev-parse`/`cat-file` run nothing.
- Decision (KISS, prior art `src/aa_ma/analysis/stamp.py`): drop `git status` for a stat signature of the indexed files; pin fsmonitor/hooksPath at command scope on the index path (`indexer.SAFE_GIT`); atomic sidecar writes; `python -I`. Full stamp-style allowlist for codemem's other git calls → TODOS P1, not M15.
- Contract deviation: `packages/codemem-mcp/src/codemem/indexer.py` modified (not in the M15 Files rows): `ls-files` and the `last_sha` write live there. §13 coverage to re-check at the boundary.

## [2026-10-14] DECISION: codemem kill Signal 4 fired — consolidate under AA-MA (Ste)
- 15.7's overdue kill-criteria review found repowise (AGPL, 7.7k stars, MCP) matching co_changes + owners + layers (hotspots partial). Ste chose the pre-committed 2026-05-08 rule over "also evaluate repowise" and "decide later": codemem is AA-MA's internal code-intelligence engine; the standalone framing is dropped; M15/M10/M11 scope unchanged. Positioning edits are in TODOS (P2).

## [2026-10-14] Milestone 15 boundary: §6.3 impact analysis
- Overall MEDIUM, no HIGH; 22 non-test files. Contract changes: X2 fields added to every codemem MCP response (additive); `codemem refresh` exit codes 0/75/1 (callers: post-commit worker, mcp_tools — both updated); `ensure_built` keeps None-or-error and now also refreshes.
- MEDIUM items: (1) the post-commit worker gains refresh-commits + graphify + .built_sha — 0 repos have it wired (scan of ~/projects, ~/dev); (2) §6.0 is a new gate for every plan once installed: BLOCKED only when an existing codemem index cannot reach HEAD; `graphify update .` runs at each boundary wherever graphify is installed (code-only per R03-D14; `graphify-out/` globally excluded since 15.8). Only aa-ma-forge holds a `.codemem/` today.
- Contract as built: rows added for indexer.py, aa-ma-parse.sh and scripts/code-intel-refresh.sh (all drawn by existing §13 nodes; coverage clean). journal/lock.py changed its docstring only (refresh.pid → post-commit queue lock) and is left out of the Contract rather than drawn.

## [2026-10-14] Milestone 15 boundary: §6.6 review (Ste decisions)
- 3 agents: reuse (1 W / 3 I), quality (4 W / 13 I), efficiency (2 W / 4 I); 0 CRITICAL. Verified the efficiency headline myself: fresh-path `check_freshness` ~55 ms, `discover_files` 52 ms (resolve() on all 1,049 tracked files before the suffix filter).
- Ste: apply the proposed fix set (fbcb720). Storm coalescing NOT applied: it would contradict the approved 15.4 race AC ("A released last → .built_sha == A"); cost recorded in TODOS.
- Side effect found: the 15.8 global excludes (`.codemem/`) made `tests/analysis/test_measure.py` commit nothing locally; the test now force-adds its planted index (CI has no global excludes, so it never saw this).

## [2026-10-14] Milestone 15 boundary: §6.8 fix pass + re-run 1 (Ste decisions)
- C1/C2 fixed TDD (fb7dd2a→4ad019c, a794c69→c896eb7). A background security review then showed a name list in check_db_path misses SQLite's `-journal` → any-symlink rule (8a34d54→71e78ab).
- Re-run 1: security-auditor 0 C / 4 W / 5 I (C1 closed in 35 hostile cases; C2 closed); code-reviewer 1 C (my regression: a regular-file `.codemem` raised through every MCP tool) / 8 W / 7 I. Ste: accept the CRITICAL; move the boundary into `storage.db.connect` (chokepoint); refuse a git-tracked `.codemem` (a committed index was served as fresh); fix `aa_ma_context`'s linked-path append now.
- Two follow-up background reviews pushed toward one rule for readers and writers: it now lives in `codemem.safety` and `connect()` applies it; `aa_ma.render.graph` carries a twin, because the §13 diagram fence must not vouch for a committed graph.
- Contract changes (intended, tests updated with a docstring note): a linked sidecar is refused instead of replaced (15.2 test); a linked `graphify-out/.built_sha` skips graphify instead of being replaced (15.4 test). New X2 `stale_reason`: `unsafe_db_path`.
- Ceiling recorded in code (ponytail): with no git binary, a tracked index cannot be detected; freshness is then stale "unknown" (leads only).

## [2026-10-14] Milestone 15 boundary: §6.8 re-run 2 → trust-token redesign (Ste)
- Re-run 2: code-reviewer 0 C / 4 W / 9 I; security-auditor 1 C (a committed embedded git repo inside `.codemem/` made `git -C .codemem ls-files` consult the attacker's repo → a poisoned index served stale:false; graph.py vouched for a planted edge) / 1 W (case alias on WSL drvfs) / 7 I.
- Ste: redesign, not patch (L-049: 4th bypass of git-based detection). codemem serves only an index it built here — a per-user nonce per DB dir outside the repo, stamped into every DB file codemem creates, checked on every read-only open and by the graph.py twin. Git detection dropped (removes the GIT_* env, case-alias, dubious-ownership and timeout classes with it). All WARNINGs/INFOs folded.
- Contract changes: a garbage/corrupt/foreign index is rebuilt, not served stale-error (3 tests moved to a trusted-but-broken trigger); a git-tracked `.codemem` is rebuilt, not refused; new X2 `stale_reason: untrusted` (error, nothing served).
- Verified live: the auditor's 4 exploit repos (ebv, eb2v, ci2v, supv) no longer return the phantom caller; the committed index blob is refused by `open_graph` ("not built by codemem here").
- Known limit (TODOS): `codemem replay --from-wal` trusts its journal, which a repo can commit; replay is manual recovery only.

## [2026-10-14] Milestone 15 boundary: §6.8 re-run 3 (Ste decisions)
- security-auditor 1 C / 1 W / 7 I: a committed regular `.codemem/index.db-wal` beside a stamped index replays forged pages (the stamp page is untouched) — reproduced end to end, also through graph.py. Ste: defer the root fix (move the index out of the repo) to a new Milestone 16 before M10; M15 closes with it documented (SECURITY.md, README, commands doc, TODOS P1). M10 now depends on M16. Numbered 16, not "15b": the canonical grammar takes digits only (`## Milestone \d+:`).
- code-reviewer 0 C / 4 W / 9 I. Folded: trust-store faults named (TrustStoreError, reproduced silent-rebuild loop fixed), outcome-specific untrusted errors, README exception list, NONCE_BYTES; plus Ste's fold-ins (byte compare, atomic nonce file, XDG docs) and INFOs (refused dir propagates from check_freshness, one import source in cli, parity foreign-nonce case, mode rationale, format artefact).

## [2026-10-14] Milestone 15 boundary: double-check (Ste decisions)
- `Skill(double-check)` (standard, fresh challenger) → Partially verified: F1 committed-own-index nonce leak (reproduced), F2 fold-in code unreviewed by §6.8, F3 graph.py twin misreports a broken trust store.
- Ste: F1 → known limit (SECURITY.md, README, commands doc) + Milestone 16 acceptance criterion; F2 → targeted §6.8 re-run 4 on 4981491..HEAD; F3 → fixed now (15bc257 → 542ef67).

## [2026-10-14] Milestone 15 boundary: §6.8 re-run 4 (targeted)
- security-auditor 0 C / 1 W / 6 I; code-reviewer 0 C / 4 W / 9 I on 4981491..bd10921. All WARNINGs and the useful INFOs folded (30e7f8d → c1df21f): atomic create in `connect`; private trust dir + O_NOFOLLOW strict records + fsync'd temp-and-link writes with a no-hard-link fallback; empty records heal; `stale_reason: trust_store`; `draw --check` UNKNOWN on a broken store (ADR-0016). New X2 `stale_reason` value `trust_store` (documented in the ensure_fresh docstring, commands doc, impact-analysis skill).

## [2026-10-15] GATE APPROVAL: Milestone 15: Codemem freshness (report 03 T2–T9)
- Gate: HARD
- Approved by: Ste
- Criteria verified: 10/10
- Decision: APPROVED
- Evidence (code at 31afa8a, fences recorded in f0a7f2f): pytest 3136, bats 633, DIAGRAM_VERIFIED edges=25 checked=25 phantom=0, TESTS_VERIFIED passed=3136; §6.8 PASS_WITH_WARNINGS (planted-WAL and committed-own-index limits deferred to Milestone 16). Later background-review findings route to Milestone 16 / TODOS (Ste).

## [2026-10-15] Milestone Completion: Milestone 15: Codemem freshness (report 03 T2–T9)
- Status: COMPLETE (§7.3 authorised by Ste 2026-10-15)
- Key outcome: codemem refreshes itself (bounded 5 s refresh, post-commit worker, §6.0 CODE_INTEL_REFRESH, X2 freshness fields, session `Code-intel:` line) and refuses repo-controlled `.codemem/` inputs (link rule at every opener; trust token so only an index built here is read). Two repo-controlled-index limits are deferred to Milestone 16 (move the index out of the repo).
- Artifacts: packages/codemem-mcp/src/codemem/{safety,cli,indexer,incremental}.py, storage/db.py, journal/lock.py, mcp_tools/__init__.py; claude-code/codemem/hooks/post-commit.sh; claude-code/hooks/{aa-ma-session-start.sh,lib/aa-ma-parse.sh}; claude-code/skills/execute-aa-ma-milestone/scripts/code-intel-refresh.sh; src/aa_ma/render/graph.py; scripts/install.sh; docs (SECURITY.md, codemem README/commands, kill-criteria, architecture regen); tests (codemem, hooks bats, skills, render).
- Tests: pytest 3136 passed / 5 skipped; bats 633/633; DIAGRAM_VERIFIED edges=25 checked=25 phantom=0; TESTS_VERIFIED passed=3136 (at f0a7f2f).

## [2026-10-15] Milestone 15 finalization: §7.2.5 validator
- Verdict WARNINGS_BUT_USABLE (0 FAIL / 13 WARN), back-filled inline: post-merge chain re-pointed (16.0 ← M15 post-merge incl. 15.4's deferred `--wire-git-hook` and 15.8's user-scope check; 10.0 ← M16; the first live CODE_INTEL_REFRESH is M16's — M15 AC5's wording and M10's AC updated to match); plan §2a/§6 M16 rows, counts, order, Last Updated; §13 milestone graph regenerated (`aa_ma_deps graph`); §13 nodes for safety.py, journal/lock.py, render/graph.py, analysis/measure.py, codemem README and docs/ (`--coverage` 0 undrawn; sigils still 25/25) — this also supersedes the §6.3 note that lock.py was left out of the Contract; reference Last Updated, the TOCTOU fact and superseded markers; 15.2's RED SHA (dfdc00f); provenance back-fill (re-run 4 POST_IMPL_REVIEW, F3 and TOCTOU fixes, M16 SCOPE CHANGE, 15.10 COMPLETE, final evidence SHA).

## [2026-10-15] M15 PR sole-dev-merge Stage C/D (Ste decisions)
- Stage C on `main...HEAD` (d0febe6, 58 files): C1 code-reviewer 2 MEDIUM / 5 LOW; C2 security-auditor 1 HIGH / 2 LOW; C3 Ruff S 0; C4 ShellCheck 0. Stage B: pytest 3136 passed / 5 skipped; L-007 guard clean.
- HIGH (planted `index.db-journal` rolled back into a stamped index; cleanups omit `-journal`, confirmed at `incremental.py:418`, `indexer.py:150` vs `db.py:208`): Ste **Defer to M16**. Same root cause as the re-run 3 WAL limit. SECURITY.md known limit widened; M16 AC added.
- MEDIUM relative `CODEMEM_DB`/`CODEMEM_REPO_ROOT` (confirmed `server.py:82-91` returns `Path(env)`; refresh runs with cwd = DB dir): Ste **Defer to M16**; M16 AC added.
- MEDIUM §6.0 gate cold-builds instead of `skipped(no index)` (confirmed: worker runs `codemem refresh` whenever the binary exists, `post-commit.sh:107`): Ste **Defer to M16**; M16 AC added.
- LOW x7 → PR body reviewer notes and TODOS (P3). M15 not reopened (gate rule).

## [2026-10-15] M15 merged to main (PR #41)

- Rebase-merged at 6ae8974; CI 9/9 green (run 38697841996); branch, worktree removed. Ste OK'd this direct record commit to main.

- Rebase-merge rewrote SHAs; the M15 records name branch SHAs. Map (branch→main): 778259f→fed6551, 30bfed2→0129233, 86f1b57→fed4091, d0febe6→ed267e9, 4ad1eb6→6ae8974, 31afa8a→63b38b8, f0a7f2f→011c96e.

- Next: Sub-step 16.0 (install.sh from main, optional --wire-git-hook, M16 worktree, codemem build, plan the move). Not started.

## [2026-10-23] M16.0 — resume + plan the move (Ste decisions)
- Resumed from `.claude/handovers/2026-10-23-code-conventions-impact-resume.md`; E1–E10 re-run: all held except E1's command as written (`git rev-parse --short` takes one rev; run per ref, both 7d3c1265) and E3 (the merged fix/sdm-skill-recovery worktree is gone). Ste chose option A (M16 before M10). Session-start "AA-MA ACTIVE … Milestone 10" is the first-PENDING fallback; the gate is the source of truth.
- Location: `${XDG_CACHE_HOME:-~/.cache}/codemem/<sha256(realpath root)>/` (cache, not state: the index is rebuildable). Rejected: XDG_STATE_HOME (survives wipes, wrong class of data); git-toplevel in Python (an extra git call and a no-git fallback for no gain — cwd is codemem's default today).
- Migration: ignore and rebuild. Rejected: move-on-first-run (new code reading a repo-controlled dir — the trust problem M16 removes); a one-time notice (YAGNI; only this repo has a `.codemem/`).
- Trust token: kept. Out of the repo, a repo can no longer plant a WAL/journal/stamp beside the default index; the token still guards a `CODEMEM_DB` pointed into a repo. Rejected: drop (300+ lines of Critical-Path churn); refuse CODEMEM_DB inside a repo (git detection, retired by L-049). Deviation from the M16 AC wording: SECURITY.md's known-limit paragraph is replaced by one line, not removed outright, because the CODEMEM_DB-in-repo case remains.
- §6.0 (`code-intel-refresh.sh`, M15 pre-merge MEDIUM): always build/refresh; `skipped(codemem not installed)` only with no codemem binary; otherwise last_sha ≠ HEAD is BLOCKED (Ste agreed).
- Deferred: `--wire-git-hook` → 10.0 (`.git/hooks` is shared by all worktrees). Kept: `prototype/codemem-refresh-cap`. TODOS: session-start mislabel. sole-dev-merge TODOS stay out of M16.
- Found at 16.0: `.mcp.json` pins `CODEMEM_DB=${PWD}/.codemem/index.db` (Contract row added); `measure.py` uses an explicit `--db` (comment only); re-count 17 code / 31 test / 56 doc (was 14/31/53). Pre-exec validator WARN (W1–W5) folded: CODE_INTEL_REFRESH in the M16 AC, Contract paths listed, risks + rollback row, CPR sub-step 16.5, reference.md M16 Facts.

## [2026-10-23] Milestone 16 boundary: §6.0 + §6.3 impact analysis
- §6.0 (installed copy = main's pre-M16 script): first live `CODE_INTEL_REFRESH` for M16, codemem = graphify = 6b6e4396. The installed gate refreshed the old in-repo index; the new-location index was built separately (`codemem build`, 341 files) for the §13 fence. From 10.0's install on, §6.0 runs the M16 script.
- §6.3 overall MEDIUM, no HIGH. Intended contract changes: codemem default DB → XDG cache (cli + MCP server), cli honours `CODEMEM_DB`, `.mcp.json` drops it, `open_graph` reads the cache dir, §6.0 value `skipped(no index)` → `skipped(codemem not installed)` (no reader). All in-repo callers cascaded; signatures of `_capped_refresh`, `_discard_untrusted`, `open_graph` unchanged. Downstream: other repos need one `codemem build` after merge before their §13 fence passes (BLOCKED names the remedy); the user-scope MCP picks up M16 at 10.0's install.

## [2026-10-23] GATE APPROVAL: Milestone 16: Move the codemem index out of the repo (M15b; §6.8 re-run 3 deferral)
- Gate: HARD
- Approved by: Ste
- Criteria verified: 9/9
- Decision: APPROVED
- Evidence (code at 4066fca8, fences recorded in 25242b1f): pytest 3177 passed / 5 skipped; bats 781 ok; DIAGRAM_VERIFIED edges=25 checked=25 phantom=0; TESTS_VERIFIED passed=3177; CRITICAL_PATH_REVIEW; CODE_INTEL_REFRESH (first live 6b6e4396, final 4066fca8); §6.8 PASS_WITH_WARNINGS (CRITICAL bench rmtree accepted + fixed cd6b695c→5c4c9f9d; round 2 clean).

## [2026-10-23] Milestone Completion: Milestone 16: Move the codemem index out of the repo (M15b; §6.8 re-run 3 deferral)
- Status: COMPLETE (§7.3 authorised by Ste 2026-10-23)
- Key outcome: codemem's default index lives in `${XDG_CACHE_HOME:-~/.cache}/codemem/<sha256(realpath root)>/`, so a repo can no longer plant a WAL, rollback journal or stamped index beside it (M15 §6.8 re-run 3, double-check F1, pre-merge HIGH). One resolver per language (codemem.paths, aa_ma.render.graph twin, aa_ma_codemem_dir) pinned by a parity test; trust token kept for a CODEMEM_DB inside a repo; §6.0 blocks a failed build.
- Side work: format-only PRs #63, #64 (L-031); lessons L-064, L-065; TODOS P3 ×3.
- Next: Milestone 10 — Dependencies: Milestone 9, Milestone 15, Milestone 16. 10.0 = post-merge of M16 (install.sh from main, --wire-git-hook per Ste's 16.0 deferral).

## [2026-10-25] SCOPE CHANGE: Milestone 10 / Sub-step 10.0 — live worktree replaces worktree-per-milestone (amends D7; ADR-0025)
- Source: handover `2026-10-23-cci-m10-resume.md` §9 Q3 (Ste, 2026-10-23: "sole developer, milestones sequential").
- Decision (Ste, 2026-10-25): option C. `~/.claude` links into the live worktree (the existing `codemem-plugin-wt`, not a second one), refreshed to main by `install.sh` before linking; milestones from M10 run on plain branches in the main checkout. Rejected: A keep worktrees (per-milestone `uv sync`/`codemem build`/cleanup); B plain branches with links on the checkout (a half-edited hook is live in every session); a second live worktree (two to refresh).
- Sequence (Ste approved at the 10.0 checkpoint): style PR (L-065) → 10.0 PR from a worktree (old D7 holds until it merges) → install from main switches the links → `--wire-git-hook` → M10 branch in the main checkout.
- Also (Ste): wire `--wire-git-hook` in 10.0 (deferred from 16.0), from the live worktree after the switch, because the stanza bakes in its checkout's absolute path. Remove the merged worktrees feat/cci-m16, style ×2 (done; `git cherry` showed none held commits off main). Ste: force-with-lease OK for style/m10-contract-lint (rebase onto 9d51aaa4); operator cleanup after each sdm finish this session.
- Validator W1–W5 folded into plan/tasks/reference (10.0 AC, 10.6 index + binary lookup, Contract rows, ADR 0026 for 10.8). W6: gate semantics unchanged.
- Side fix: filelock CVEs broke every PR's deps job → PR #67 (merged 9d51aaa4).
- Approved by: Ste

## [2026-10-25] M16 merged to main (PR #65) — post-merge record (L-037)
- PR #65 rebase-merged 2026-10-23 at 38a5f179 via sdm.sh (STATUS OK); 29 branch SHAs rewritten — SHA MAP line in provenance (2026-10-23T16:07). Format PRs #63 (8ce73388), #64 (45d08ba0).
- PR #65 MEDIUM/LOW notes → one P3 TODOS entry ("PR #65 review notes").

## [2026-10-25] 10.1 PROTOTYPE verdict — impact pre-edit hook (verdict-changes-plan: YES)
- Evidence: prototype/impact-hook @ 576cd693 (`prototype-notes/impact-hook-10.1.md`). p95 72–77 ms; A1 live; callers carry the signal; co-changes noisy; skills/hooks blank until 10.3.
- Decision (Ste): add a large-commit filter to `co_changes` — `max_commit_files`, used by the hook and `file_impact` at `CO_CHANGE_MAX_COMMIT_FILES = 10`; the MCP tool default stays unfiltered. First proposed N=20; measured before writing the delta: the noise came from 12–19-file sweep commits (format, lint pay-down, Ruff-S swap), so N=20 filtered none — Ste chose N=10 (rejected: 1/size weighting, a new scoring rule to design).
- Angle-3 check on the delta (R3): callers of `mcp_tools.co_changes` are `codemem/cli.py:287` and `claude-code/codemem/mcp/server.py:181`; the new keyword-only arg defaults to None (no filter), so neither changes behaviour. `aa_ma.analysis.measure._co_changes` is a separate function (unaffected). No per-commit file cap exists in git_mining (max seen 37 files/commit), so the filter sees true commit sizes. Risk: a real coupling inside an 11+-file commit is hidden from the hook — accepted (callers still shown; `Skill(impact-analysis)` uses the unfiltered tool).
- Also: no captured PreToolUse Edit/Write fixture existed — 10.6 adds them from live captures.

## [2026-10-26] 10.5–10.7 decisions (Ste)
- Doctrine: the engineering-standards §1 Critical-Path table names every `CRITICAL_PATH_GLOBS` path (hook-modification extras incl. `scripts/lib/aa-ma-install-lib.sh`; version-pipeline `scripts/release.sh`, `VERSION`); the test asserts exact equality. Rejected: keep the table a summary with a PLAN_EXTENSIONS pin (two sources of truth).
- griffe pinned 2.3.2, the newest release past the repo's 7-day Dependabot cooldown (2.4.1 was 3 days old). Rejected: latest.
- commit-drift's co-change advisory also fires on `[ad-hoc]` commits during an active plan (agent extension, kept): the unplanned commit is the one most likely to miss a co-changing file.
- 10.6 marker deviation accepted: `set -C` (O_EXCL) instead of `mkdir` — uutils mkdir 0.10.0 is not test-and-set (119/300 races doubled; GNU 0/300). L-070.

## [2026-10-26] ADR APPROVAL: ADR-0026 — impact pre-edit hook, callees, plugin edges
- Approved by: Ste
- Decision: APPROVED (Status: Accepted)
- Scope: hook (once per file per session, ≤5 lines, untrusted framing, fail-open), trust model + Unicode-category sanitizer, `set -C` marker (L-070), `callees` + deprecated `blast_radius` alias (TODO(ADR-0026)), defect-1 fix, co_changes min_ratio / max_commit_files (N=10), plugin_edges (schema v4). Rejected: skill wording only; a blocking per-edit gate.

## [2026-10-26] Milestone 10 boundary: §6.0 + §6.3 impact analysis
- §6.0: CODE_INTEL_REFRESH codemem = graphify = f8e91e0c (installed copy, M16 script).
- §6.3 predicted-vs-actual (new 10.7 script, advisory): changed=72 predicted=47 cochange=10 unpredicted=31 — tests named in shorthand Contract rows, doc-count sites (README, foundations, migration-from-index), 10.0-era files (docs/lessons.md, aa-ma-install-lib.sh), regenerated views; no unpredicted production module.
- Contract changes (all intended, cascaded in-repo): (1) codemem `blast_radius` payload gains `callees` + `deprecated` (its `downstream` kept) — MCP/CLI/skill wording updated; removal after v0.18.x (TODO(ADR-0026)). (2) `co_changes` entries gain `ratio`, payload gains `target_commits` (additive; new kwargs default to old behaviour). (3) `who_calls` gains plugin entries `{name, kind, file=<node id>, via}` after code callers — consumers are the CLI and MCP server passthrough only. (4) codemem schema v3 → v4 (`plugin_edges`): forward migration; `aa_ma.render.graph` requires `user_version >= 3` (unaffected; §13 lint PASS edges=25); a pre-v4 index logs a warning and returns no plugin callers until `codemem build`. (5) `AA_MA_HOOKS` +1 row (hooks 9→10); uninstall table-driven. (6) commit-drift prints one advisory line on ad-hoc commits. (7) engineering-standards §1 table text (auto-loaded doctrine) lists the glob paths.
- Downstream outside the repo: other repos' codemem indexes upgrade on next build; the live MCP server and hooks pick up M10 only at 11.0's install (ADR-0025).
- Overall risk: MEDIUM (additive contract changes + one forward schema migration); no HIGH; cascades done in-branch.

## [2026-10-26] Milestone 10 boundary: §6.6 simplification review (Ste decisions)
- 3 agents (reuse, quality, efficiency): 0 CRITICAL, 7 WARNING, 13 INFO. Ste: fix W1–W5, W7 + small INFOs; W6 and efficiency/reuse INFOs → TODOS.
- Fixes (test-first, a8830ad4 → b21ad499): W1 commit-drift logs every fail-open path; W2 `aa_ma_cochange_partners` (T7 constants + query + jq in one helper, rc 0/2/3/4/5/6); W3 coverage reads `aa_ma.grammar.PLAN_MILESTONE_RE` (new constant, levels 2–4, same number/separator rules as MILESTONE_RE; one completed-plan heading "### Milestone 5 (Optional polish…)" no longer read); W4 hook notices via `fail_open_notice` (masked; text now prefixed `aa-ma-impact-preedit:`); W5 `aa_ma_default_base_ref` (adds origin/main to tests-verified's base chain — intended); W7 claim before git (repeat edit ~40 → ~30 ms); INFOs: plural, `via` tag, sanitizer debug log, threshold comment.
- Pyright "possibly unbound" on coverage.py:116 is a false positive (level set with start); cli.py:493 and mcp_tools:255 are pre-M10.

## [2026-10-26] GATE APPROVAL: Milestone 10: Impact tooling: codemem `callees`, pre-edit hook, wiring (T6, T13 git helper)
- Gate: HARD
- Approved by: Ste
- Criteria verified: 7/7
- Decision: APPROVED
- Evidence (code at f8783074): pytest 3401 passed / 2 skipped; bats 855 ok; perf 4/4; CODE_INTEL_REFRESH f8e91e0c; DIAGRAM_VERIFIED edges=25 checked=25 phantom=0; TESTS_VERIFIED passed=3401; PROTOTYPE (verdict-changes-plan: YES); CRITICAL_PATH_REVIEW (12 hook-modification files); §6.8 PASS_WITH_WARNINGS (round 1 0C/8W/16I → W1/W7/W8 fixed; round 2 clean).

## [2026-10-26] Milestone Completion: Milestone 10: Impact tooling: codemem `callees`, pre-edit hook, wiring (T6, T13 git helper)
- Status: COMPLETE (HARD gate approved by Ste 2026-10-26)
- Key outcome: before the first Edit/Write of a file, the model now sees ≤5 sanitized lines of who depends on it (code, plugin and test callers; filtered co-changes), from a codemem that knows `callees`, plugin edges and renames; §6.3 lists unpredicted files for the §6.8 reviewer. Live from 11.0's install.
- Artifacts: hook aa-ma-impact-preedit.sh; codemem mcp_tools/cli/git_mining/storage (schema v4)/plugin_surface/sanitizers/gitutil; aa_ma gitutil/plan_parsers/grammar/render.coverage; predicted-vs-actual.sh; aa-ma-parse.sh helpers; commit-drift + session-end hooks; install-lib row; ADR-0025, ADR-0026; doctrine table; 5 skills name Skill(impact-analysis).
- Tests: pytest 3401 passed / 2 skipped; bats 855 ok; perf 4/4. Side PRs merged before the branch: #66 style, #67 filelock CVEs, #68 live worktree (10.0).
- Next: Milestone 11 — Dependencies: Milestone 10. 11.0 = post-merge of M10 (git pull, live install → hook live; verify A1 with the shipped hook).

## [2026-10-26] Milestone 10 §6.8 decisions (Ste) + §7.2.5 validator back-fill
- §6.8 round 1 (5 agents): 0 CRITICAL / 8 WARNING / 16 INFO. Ste: fix W1 (who_calls plugin entries `line: null`), W7 (repo paths sanitised for Unicode Cc/Cf/Co/Cs/Zl/Zp via `aa_ma_sanitize_lines`; `<unpredicted-files>` framed untrusted), W8 (rc-4 docstring) — d350019b..f8783074; defer the other 5 WARNINGs + M11 carry-overs to TODOS ("M10 §6.8: 5 deferred WARNINGs + carry-overs"). Round 2 (fix only) clean → PASS_WITH_WARNINGS.
- Validator (§7.2.5): WARNINGS_BUT_USABLE (0 FAIL, 4 WARN). Back-filled: this entry (W1); CRITICAL_PATH_REVIEW addendum for hook-path files changed after 15890d3f (W2); CODE_INTEL_REFRESH addendum at b48859fc (W3, manual — the script needs an ACTIVE milestone).
- W4 (recorded, not fixed): the 10.2 AC "co_changes … returns its pre-move partners" holds only with `refresh-commits --limit 2000`; at the default 500-commit window the M3 rename (660 commits back) is out of range. Accepted as a known limit (Result Log 10.2, ADR-0026 Consequences); M11's co-change gate should state its window.
- I2 (recorded): 10.6's "out-of-repo path ignored" and "codemem absent → one notice" are covered by tests/hooks/aa-ma-impact-preedit.bats cases of those names (bats 855/0).

## [2026-10-26] M10 double-check F1 — decision (Ste)
- F1: the 10.2 AC "co_changes returns pre-move partners" holds only at `refresh-commits --limit 2000`; at the default 500-commit window the M3 rename (660 commits back) is out of range.
- Decision: accepted as a known limit of M10 (ADR-0026 Consequences already states it). M11 declares the window: Sub-step 11.1 AC now requires the gate's `--limit` to be chosen with the threshold and recorded in reference.md.

## [2026-10-27] 11.1 complexity-router verdict — Milestone 11
- Factors: scope 62, architectural 65, technical risk 55, dependencies 50, uncertainty 45 → weighted 57%.
- Auto-triggers: contract change for every post-cutover plan (`Impact-Explained:`, `API-Break:`); shipped enforcement surface (hook-modification). Final 85% (Critical) = plan estimate.
- Routing: deep review — Ste at the HITL points (11.1 threshold/window, 11.6 ADR, §7.1), Chain-of-Thought on 11.3/11.5, §6.8 with 5 agents.

## [2026-10-27] 11.1 PROTOTYPE verdict — co-change threshold (verdict-changes-plan: NO)
- Data: `prototype/m11-cochange-threshold` @ a51abd50; replay of codemem co_changes at each milestone PR head over the last 3 completed plans (15 milestones) and this plan (12, reference). Co-change Impact-Explained lines at window 500: 5/50% 5|11, 3/50% 29|43, 5/30% 16|15; window 2000: 14|14, 48|46, 36|55; ≤10-file sweep filter @500: 2|6, 11|25, 11|7.
- Decision (Ste): **5 shared / 50%** (T7 default), **window 500** (`COCHANGE_WINDOW_COMMITS`, passed as `refresh-commits --limit`), **no sweep filter**. Why: hits at 5/50%@500 are real couplings; looser thresholds add churn pairs, 2000 adds stale ones; the sweep filter needs a new codemem CLI flag and drops real signal. Rejected: 3/50%, 5/30%, 2000, max-commit-files 10.
- Limits stated: counts cover the co-change component only (unpredicted files come on top; M10 had 31); "linked" exclusion used today's index; the M3 renames stay outside the 500 window (F1, accepted 2026-10-26).

## [2026-10-27] SCOPE CLARIFICATION: Milestone 11 — validator W1–W3 + M10 carry-overs (Ste)
- W1: plan.md M11 Contract text corrected — coverage.py imports the row helpers from `aa_ma.contract_rows` (tasks.md already said so).
- W2: Contract rows added for paths tasks 11.2–11.6 already change: `.importlinter`, `docs/templates/plan-template.md`, `claude-code/agents/aa-ma-scribe.md`, `references/impact-gate.md`, `docs/adr/INDEX.md`, `tests/test_contract_rows.py`, `tests/render/test_leaf_contract.py`; plus codemem cli.py + mcp_tools (nits folded into 11.3). install-lib/doc-count rows NOT added pre-emptively: a predicted-unchanged row is itself an explanation cost; add one when 11.x actually touches it.
- W3: 11.3 AC — `COCHANGE_WINDOW_COMMITS = 500`; `refresh-commits --limit` receives it (test asserts the argv).
- Carry-over placement: aa_ma.gitutil + derive_critical_paths callers in impact.py (11.3); shell↔Python T7 constant contract test (11.3); coverage row regexes from one verb tuple (11.2); griffe Context7 lookup (11.4); codemem FILE_IMPACT_BUDGET + co_changes threshold default (11.3, Ste "fold in"); codemem.gitutil adoption deferred (TODOS, Ste).
- W4 (reference facts) applied at 11.0; W5 (§13 edges for milestone_base/verify-impl) and W6 (cosmetic step order) left as recorded.

## [2026-10-27] 11.2 decisions (agent, within AC)
- `# file:` template lines read as `Modify` (AC lists row verbs only; the verb only matters to fence 4 for Delete/Move).
- `→` / `->` in Move/Merge rows are separators, not paths (the M3 Contract writes `old → new`); prose after a Merge arrow still reads as paths — fail closed, kept.
- Explanations fail closed the other way: `read_text_field_lines` drops non-canonical-bullet and empty lines (an untrusted line explains nothing → the gate reports the file).
- coverage's all-verb `_ANY_ROW_RE` removed (no reader after delegation) rather than kept as a dead twin.

## [2026-10-27] 11.3 decisions
- Staleness source (agent, within AC 11.5 / G13): the codemem CLI had no `stale` — only the MCP envelope did. `codemem query co_changes` now adds per-path `stale` (true/false/"unknown") + `stale_reason` from `check_freshness` (additive; `aa_ma_cochange_partners` reads `.files` only). aa-ma-impact runs `codemem refresh` first, so a stale answer means a race or an untrusted index → exit 1. Rejected: a Python freshness twin in aa_ma (third copy of tree_sig logic).
- Index required even with nothing changed (agent): `status`/`refresh`/`refresh-commits` always run; an unindexed repo never passes fence 4.
- Cochange-Threshold override approval title (agent): `GATE APPROVAL: Cochange-Threshold <n> <ratio> — <milestone heading>` (binds the values, like `Test-Command none — <heading>`); Python reader `enforce.has_gate_approval` is pinned to the shell `aa_ma_has_gate_approval` by 14 parity cases.
- Derived Critical-Path review (agent): a CRITICAL_PATH_REVIEW line for the milestone covers a triggering file when it names the file or a `CRITICAL_PATH_GLOBS` glob the file matches.
- `--head` (agent): non-HEAD compares `base..head` only, for the 11.7 retro on merged history; HEAD includes the working tree.
- Contract row prose (Ste, after the live run on M11: ~55 prose tokens read as predicted-unchanged): keep the fail-closed "every token is a path" grammar (one grammar with coverage); 11.6 runbook/templates/scribe tell authors paths only, prose after `#`. Rejected: gate-only stop-at-first-non-path (drops a 2nd extensionless root path); changing coverage too (reverses the diagram-generation §6.8 decision).
- Live findings for M11 itself (grandfathered, informational): tests/test_enforce.py unpredicted; codemem incremental.py/indexer.py co-change with cli.py; enforce.py/impact.py derive hook-modification — 11.9's CRITICAL_PATH_REVIEW names them.

## [2026-10-27] 11.4 decisions (agent, within AC)
- `API-Break:` lives in the plan's milestone Contract (as the 11.6 template AC says), read by `contract_rows.milestone_contract_lines`; `<dotted.path> — <reason>`, reason required; a module path covers its members.
- Every griffe BreakageKind counts (incl. attribute value and parameter-default changes): griffe compares source expressions, so `2_000` → `FILE_IMPACT_BUDGET` (same value) is a break to declare. Fail closed; the runbook (11.6) says so. Rejected: a kind allowlist (a silent hole).
- Only packages the change touches are loaded (cost: ~0.5 s per package); griffe failures are `skipped(<pkg>: <type>: <first line>)` + a WARNING log, never a pass by silence.

## [2026-10-27] 11.5 decisions (agent, within AC)
- Fence 4 logic lives in `scripts/impact-verified.sh` (bats-tested), the SKILL.md block only locates it — fence 3's shape. Contract rows added for it and for gate-fences.md (scope clarification, no new work).
- Grandfather-first with no window: `aa-ma-impact --base` is optional; the fence passes `--base` only when `aa_ma_milestone_base` succeeds, so a grandfathered plan on main (M14) reads "not applicable" and a plan in force reports the window error.
- `aa_ma_milestone_base` reads origin only (origin/HEAD → origin/main → origin/master); `aa_ma_default_base_ref`'s local main/master fallback is not used: a branch this session can move is not a certifiable base.
- SKILL.md 500-line cap: fence-1 rationale comments moved verbatim-in-substance to references/gate-fences.md rather than raising the ratchet.
- Bats fixtures make a plan "in force" with `Created: 9999-12-31` (= the sentinel), not an env knob — a cutover override env var would be a bypass.

## [2026-10-27] ADR APPROVAL: ADR-0027 — gate-computed IMPACT_VERIFIED (§6.7 fence 4)
- Approved by: Ste
- Decision: APPROVED (Status: Accepted)
- Scope: fence 4 via `aa-ma-impact` (window = merge-base with origin's default; Contract rows paths-only; Impact-Explained for unpredicted / predicted-unchanged / co-change 5/50%@500; griffe API-Break for aa_ma + codemem; derived Critical-Path reviews; fail closed; post-cutover plans only, grandfather check first). Callers are who_calls/§6.3/§6.8's domain, not fence 4. Rejected: advisory only; block on callers.

## [2026-10-27] 11.7 retro-check: aa-ma-impact on Milestone 10 (evidence only; grandfathered plan)
- Command: `aa-ma-impact <plan> <tasks> --milestone 10 --base f0bfbd8b --head 169e4e81 --ignore-cutover` (PR #69 window, 56 commits). rc 1: changed=80 predicted=47 cochange=1 unexplained=48 (40 unpredicted, 7 predicted-unchanged, 1 co-change) api_breaks=3 api_diff=aa_ma,codemem; 11 unreviewed hook-modification files. Co-change and linked-file exclusion use today's index (approximation).
- Dispositions (one line per file):
  - README.md — doc-count site (MCP tools 13→14, hooks 9→10); Contract should name doc-count files (TODOS carry-over, now runbook).
  - TODOS.md — §6.6/§6.8 deferrals recorded; process file, should be named or explained.
  - claude-code/hooks/lib/aa-ma-parse.sh — §6.6 W2/W5 helpers (aa_ma_cochange_partners, aa_ma_default_base_ref, aa_ma_sanitize_lines): real missed impact.
  - claude-code/rules/engineering-standards.md — 10.5 doctrine: §1 table lists every CRITICAL_PATH_GLOBS path (Ste); missed in Contract.
  - claude-code/skills/FORKS.json — md5 refresh of forked skills edited by 10.8 wording; mechanical cascade.
  - claude-code/skills/aa-ma-plan/references/phase-2-brainstorm.md — PROTOTYPE `verdict-changes-plan` token cascade (10.7).
  - claude-code/skills/execute-aa-ma-milestone/references/boundary-checks.md — §6.3 predicted-vs-actual step (10.7): planned work, row missing.
  - claude-code/skills/execute-aa-ma-milestone/references/post-impl-review.md — `<unpredicted-files>` to the §6.8 reviewer (10.7): planned, row missing.
  - claude-code/skills/execute-aa-ma-milestone/scripts/predicted-vs-actual.sh — new 10.7 script: planned, row missing.
  - claude-code/skills/execute-aa-ma-milestone/scripts/tests-verified.sh — §6.6 W5 (aa_ma_default_base_ref): fix-pass impact.
  - claude-code/skills/plan-verification/references/angles-1-5.md — `verdict-changes-plan: YES` → Angle-3 check (10.7 doctrine): cascade.
  - docs/adr/0026-impact-preedit-hook-and-callees.md — the ADR the Contract named as `NNNN-…` (placeholder; same file).
  - docs/adr/INDEX.md — ADR row; always changes with an ADR (runbook: name it).
  - docs/adr/NNNN-impact-preedit-hook-and-callees.md (predicted-unchanged) — placeholder for 0026; same file.
  - docs/codemem/migration-from-index.md — doc-count site (14 MCP tools).
  - docs/lessons.md — L-067..L-070 written during M10: process file.
  - docs/spec/claude-code-foundations.md — doc-count site (hooks 10).
  - packages/codemem-mcp/src/codemem/incremental.py — `_refresh_plugin_edges` on every refresh (10.3): real missed impact.
  - scripts/install.sh (predicted-unchanged) — the hook row lives in the AA_MA_HOOKS table (M3, scripts/lib/aa-ma-install-lib.sh); Contract named the wrong file.
  - scripts/lib/aa-ma-install-lib.sh — the file the row actually needed (see install.sh).
  - scripts/uninstall.sh (predicted-unchanged) — table-driven since M3; no change needed; wrong Contract row.
  - src/aa_ma/grammar.py — §6.6 W3 `PLAN_MILESTONE_RE`: fix-pass impact.
  - src/aa_ma/render/coverage.py — `milestone_contract_paths` (10.7): planned, row missing.
  - src/aa_ma/render/graph.py (co-change with codemem storage/db.py) — schema v4 needs no change here (graph requires user_version ≥ 3; §13 lint PASS): explained, true negative.
  - test_aa_ma_context.py / test_co_changes.py / test_file_impact.py / test_plugin_surface_index.py (predicted-unchanged, 4) — Contract shorthand names; the real files are the tests/codemem/ entries below (row-writing defect).
  - tests/codemem/test_aa_ma_context.py, test_co_changes.py, test_file_impact.py, test_plugin_surface_index.py — the same 4 tests under their real paths.
  - tests/codemem/test_file_edges.py, test_git_mining.py, test_install_and_cli.py, test_mcp_server_integration.py, test_plugin_surface.py, test_sanitize_context_line.py — tests of the codemem changes (schema v4, renames, 14 tools, sanitizer); Contract named only new tests.
  - tests/fixtures/hook-payloads/PreToolUse-Edit.json, PreToolUse-Write.json — real payload fixtures for the new PreToolUse hook (M7 convention): planned, rows missing.
  - tests/hooks/aa-ma-parse.bats, commit-drift.bats, install-live-worktree.bats, predicted-vs-actual.bats, session-end-dirty.bats — bats for the hook-lib helpers, commit-drift advisory, install row, 10.7 script, SessionEnd marker cleanup.
  - tests/render/test_leaf_contract.py — gitutil-is-self-contained contract (10.4).
  - tests/render/test_milestone_contract_paths.py — 10.7 coverage reader tests.
  - tests/skills/test_unpredicted_files_untrusted.py — §6.8 W7 untrusted framing test.
- API breaks (3), all intended and listed in the M10 §6.3 contract changes: codemem.cli.QUERY_TOOLS (+callees), codemem.storage.db.CURRENT_SCHEMA_VERSION (3→4), codemem.storage.db.MIGRATIONS (+v4).
- Unreviewed derived Critical-Path (11 files): M10's CRITICAL_PATH_REVIEW lines named files by basename (`aa-ma-commit-drift.sh`, `hooks/lib/aa-ma-parse.sh`) — fence 4 requires the repo path or a glob; reviews did happen (provenance 15890d3f + addendum). Runbook covers it.
- Reading: 40 of 48 are Contract-writing defects (missing rows, shorthand names, placeholders, wrong file), 2 real missed impact (aa-ma-parse.sh helpers, codemem incremental.py), 1 true-negative co-change, the rest process/doc-count files. Fence 4 would have forced each to be named or explained — the intended pressure; the threshold (1 co-change line) did not add noise.

## [2026-10-27] Milestone 11 boundary: §6.0 + §6.3 impact analysis
- §6.0: CODE_INTEL_REFRESH codemem = graphify = 4eab2864.
- §6.3 predicted-vs-actual (installed copy): changed=31 predicted=86 unpredicted=4 — docs/adr/0027 (Contract said NNNN), docs/lessons.md (L-071), tests/codemem/test_critical_path_globs.py (11.3 tripwire), tests/test_enforce.py (enforce tests; Contract omitted). Its co-change step skipped (rc 5): M11's Contract prose tokens (`==`, `(fixture`, `5/50%`…) fail codemem's arg allowlist — the 11.3 decision (rows paths-only) is the cure for new plans; this plan's Contract is historical.
- Contract changes (all additive): codemem `query co_changes` results gain `stale`/`stale_reason`; `--threshold` and `impact --budget` default to the library's (same values); `mcp_tools.FILE_IMPACT_BUDGET`; aa-ma-parse.sh +`aa_ma_milestone_base`, +`aa_ma_impact`; §6.7 gains fence 4; verify-impl Step 1 window; new CLI `aa-ma-impact`. Consumers checked: aa_ma_cochange_partners (explicit threshold, reads .files), predicted-vs-actual.sh / render cli / tests (coverage public API unchanged), cli the only file_impact caller.
- Overall risk MEDIUM (shared lib + a new fence for every session after the next install); no HIGH.
- Finding (deferred to TODOS): codemem's `sanitize_symbol_arg` allowlist `[A-Za-z0-9_./-]` (≤256, no `..`) rejects legal paths (spaces, `+`, `@`); a changed file like that makes fence 4 exit 3 with no fix but a rename. 0 such tracked files here.

## [2026-10-27] Milestone 11 boundary: §6.6 simplification review (Ste decisions)
- 3 agents (reuse, quality, efficiency): 0 CRITICAL, 9 WARNING, 18 INFO.
- Ste: fix all four groups now, test-first — (A) gate correctness: milestone as str (`2a`), verbatim heading, exact heading-field + whole-token file match for CRITICAL_PATH_REVIEW, guarded provenance read, codemem result-key check, `relative_to` guard, directory row vs excluded changes; (B) shared code: one `plan_created` (fence-stripped) for coverage + impact, `grammar.H2_RE`, one uv kv launcher for aa_ma_gate/aa_ma_impact, `fence-common.sh` for fences 3/4 scaffolding, `_codemem_bin` executable check + parity with shell, one `covers()`, one sibling-path helper; (C) griffe: one `git archive` extraction per ref (no temp worktree/branch); (D) kv/cleanups: no `_kind` re-derivation, per-file derived Critical-Path kv lines, `_compute` args object, one constant per line.
- Kept (Ste): griffe-skipped stays `api_diff=skipped(reason)` + WARN, not a failure (11.4 AC). Fence 3 vs fence 4 base: documented in gate-fences.md, not aligned (fence 3 reads inputs, fence 4 certifies a window).
- Not taken: codemem 4-process consolidation and per-path SQLite connection (INFO; once per milestone, ~1.5 s); plain `refresh` "skipped" on stdout (refresh rc 75 is already non-zero → exit 3).

## [2026-10-27] M11 fence 4 dogfood (Ste)
- The shipped fence 4 printed `IMPACT-GATE: not applicable (grandfathered)` for this plan (Created 2026-10-08 < IMPACT_CUTOVER sentinel), as designed. Ste chose to make M11 pass its own gate with `--ignore-cutover`.
- Forced run before: unexplained=64 (58 predicted-unchanged prose tokens from M11's own Contract Test rows + `SKILL.md §6.7` + `NNNN` ADR, 6 unpredicted), 1 API break, 3 unreviewed Critical-Path files.
- Fixes (scope clarification of the plan Contract, no new work): rows paths-only (prose after `#`), ADR row → 0027, `Test` rows for tests/test_enforce.py and tests/skills/test_fence_scaffolding_shared.py, `API-Break: codemem.mcp_tools.file_impact — …`; tasks.md `Impact-Explained:` for TODOS.md, docs/lessons.md, tests/codemem/test_critical_path_globs.py; CRITICAL_PATH_REVIEW addendum naming impact-gate.md, fence-common.sh, tests-verified.sh by repo path.
- After: exit 0, changed=35 predicted=32 cochange=0 unexplained=0 api_breaks=0 → `IMPACT_VERIFIED … via --ignore-cutover` in provenance. The gate's first real run did its job on the milestone that built it: the cost of a clean pass was one Contract tidy-up and three one-line explanations.

## [2026-10-27] GATE APPROVAL: Milestone 11: Gate-computed `IMPACT_VERIFIED` (T7)
- Gate: HARD
- Approved by: Ste
- Criteria verified: 6/6
- Evidence: pytest 3504 passed (fence 3 TESTS_VERIFIED); bats 655/655; fence 1 PASS; DIAGRAM_VERIFIED edges=25; IMPACT_VERIFIED unexplained=0 (--ignore-cutover dogfood); §6.8 PASS_WITH_WARNINGS (2 rounds); lint-imports 9/0; branch at f93be576
- Decision: APPROVED
- [2026-10-27] Note to the M11 GATE APPROVAL above: its "bats 655/655" was a non-recursive tests/hooks run; the full suite at 3517241b is 875 ok / 0 not ok (provenance CORRECTION). §7.2.5 validator: PASS_WITH_WARNINGS (W1 heading-less §6.8 lines → addendum; W2 → corrected; W3 refresh re-run at 3517241b + fence 2 PASS).

## [2026-10-27] Milestone Completion: Milestone 11: Gate-computed `IMPACT_VERIFIED` (T7)
- Delivered: `aa-ma-impact` CLI (src/aa_ma/impact.py) + §6.7 fence 4 (impact-verified.sh, fence-common.sh), `contract_rows.py`, codemem co_changes `stale`, `aa_ma_milestone_base`, ADR-0027 Accepted, runbook impact-gate.md.
- Evidence at 3517241b+: pytest 3504 passed (TESTS_VERIFIED); bats 875/0; DIAGRAM_VERIFIED edges=25; IMPACT_VERIFIED unexplained=0 (dogfood --ignore-cutover; shipped fence: not applicable until M14.1 sets IMPACT_CUTOVER); §6.8 PASS_WITH_WARNINGS; HARD gate approved (Ste); §7.2.5 validator PASS_WITH_WARNINGS (3 W addressed).
- Deferred: TODOS "M11" (impact.py SRP split, §6.3 override parity, codemem arg allowlist rc 3, codemem.gitutil).
- Next: Milestone 12 (handover to be written after the sdm merge).

## [2026-10-28] M12 start: 12.0 post-merge + pre-execution validator (WARN)
- Handover `.claude/handovers/2026-10-28-cci-m12-resume.md` E1–E7 re-run: all as recorded except E5. The live worktree was already at 01acbcea, not the expected 169e4e81. That difference was allowed, and install.sh was re-run anyway.
- `git pull` refused (pull.rebase + dirty tree); used `git fetch` + `git merge --ff-only origin/main` ("Already up to date"), the same result without touching the two by-design uncommitted files.
- HITL 12.0: proceeded on Ste's session brief ("do sub-step 12.0 only"); no separate panel.
- Pre-execution aa-ma-validator: WARN, 0 FAIL.
  - W1 (verified): install.sh rules lines moved (backup :200-201, symlinks :403-406). reference.md:275 corrected; 12.2's AC text still says :145-146/:284-287 — locate by content, AC wording left for Ste.
  - W2: plan step 12.6 still says the live install + L-1315 probe; tasks.md (newer) defers both to 13.0 — tasks.md governs.
  - W3: plan.md:938 tags `tests/test_rule_references.py` as Test, but it does not exist yet (Create). Matters for the §6.8 Contract coverage, not fence 4 (grandfathered).
  - W4: context-log:149 pins llm-output-safety / bash-defensive-patterns as orphans "until M12"; no sub-step un-pins them — decide in 12.2 (routing table), then update pin/golden.
- Ste (2026-10-28, AskUserQuestion): 12.2's AC install.sh line refs updated to :200-201 / :403-406 (line numbers only; the requirement is unchanged). The 10 foreign claude-checkpoint-* tags are left untouched. 12.1 approved; stop before 12.2.

## [2026-10-28] GATE APPROVAL: Sub-step 12.2: coding-standards.md wording
- Gate: HITL (12.2 AC: GATE APPROVAL naming the coding-standards.md blob SHA)
- Approved by: Ste (AskUserQuestion, "Approve as drafted")
- Blob: `claude-code/rules/coding-standards.md` 086b72917083b13d6eddcd2a9d2001d9d0ef5737 (commit d2301da0, 4,416 chars)
- Scope: the rule text and the rule trims in d2301da0 (engineering-standards.md, aa-ma.md)
- Decision: APPROVED

## [2026-10-28] Decision: rules budget met by trimming, not by moving the baseline (Ste)
- 12.4 AC (rules-only total ≤ M1 `rules_chars` 20,249) was unreachable as scoped: rules were already 21,671 (+1,422 from M9–M11 gate doctrine), and the new rule adds ~4.4k.
- Ste chose "Trim existing rules" (AskUserQuestion) over re-basing the ratchet or counting global CLAUDE.md. Rule text already held by the spec, a skill or a research doc became a pointer: Opt-out detail → spec §XI element 12; the 2026-09-22 Skill() measurement → research doc; Prototype routing → Skill(prototype) (the auth/live-records line kept: the skill lacks it); aa-ma.md Verification Report + v0.5.0 grandfathering → spec. Test-pinned text kept (Critical-Path + Diagram-Waiver tables, Audit-Profile sets, "these 13 outputs:", v0.12.0 grandfathering, the heading template).
- Result: 21,671 → 20,066 (183 under). Plugin-surface edges dropped from the rules: engineering-standards → operational-constraints, execute-aa-ma-step; aa-ma → aa-ma-plan (all still reached elsewhere; no new orphan).
- Routing heading renamed from "When X, load Skill(Y)" to "Routing: when X, load the skill": the extractor read `Skill(Y)` as a DANGLING ref.
