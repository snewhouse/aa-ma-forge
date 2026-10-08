# Impact analysis now: what has changed since the 2026-09-24 review, and which code-writing skills use it

**Created:** 2026-10-08
**Author:** aa-ma-researcher (Claude), for chart effort `code-conventions-impact` (ticket 4)
**Reviewed-Through-Date:** 2026-10-08 (repo at HEAD `4ad4619`; `~/.claude` skills/commands/plugin cache as installed today; web sources fetched today)
**Valid-Through:** 2026-Q4 (invalidated by any commit touching `claude-code/skills/impact-analysis/`, `execute-aa-ma-*.md` §6.3/§C, `plan-verification` Angle 3, `src/aa_ma/gate.py`, or codemem's `blast_radius`/`aa_ma_context`; plugin rows by a plugin update)
**Sources:**
- `docs/research/impact-analysis-lifecycle-review.md:79-98` — baseline gaps 1–7 and R1–R6
- `git log --oneline c0ec3f2..HEAD`, commits `33465fe`, `1fbd62b`, `500f364`, `30b5b4f` — what changed since the baseline
- `claude-code/skills/impact-analysis/SKILL.md:26,34-40,198-237` — current skill text
- `claude-code/commands/execute-aa-ma-{step,milestone,full}.md` — where execution calls the skill
- `claude-code/skills/plan-verification/SKILL.md:160-200`, `claude-code/skills/aa-ma-plan-workflow/references/PHASE_3_RESEARCH.md:157-165` — plan-time checks
- `src/aa_ma/gate.py:9-21`, `claude-code/rules/engineering-standards.md:108-111,139` — what the gate enforces and what the doctrine claims
- `packages/codemem-mcp/src/codemem/mcp_tools/__init__.py:10-11,212-259,510-525,1183,1287` — codemem tool semantics; live calls against `.codemem/index.db` (built at `75efd73`, 2026-10-05)
- `~/.claude/skills/*`, `~/.claude/commands/*`, `~/.claude/plugins/cache/{claude-plugins-official/superpowers/6.4.1, claude-plugins-official/mattpocock-skills/1.2.3, claude-code-plugins/feature-dev/1.0.0}`, `~/.agents/skills/*` — the code-writing skill inventory
- https://www.st.cs.uni-saarland.de/papers/icse2004/ — co-change mining (Zimmermann et al., ICSE 2004)
- https://arxiv.org/abs/2103.00587 — static Python call graphs (PyCG, ICSE 2021)
- https://testing.googleblog.com/2011/06/testing-at-speed-and-scale-of-google.html, https://research.google/pubs/taming-google-scale-continuous-testing/ — Google's dependency-based test selection (TAP)
- https://arxiv.org/abs/1810.05286 — Facebook's predictive test selection
- https://pypi.org/project/pytest-testmon/ — Python test selection based on what each test executes
- https://mkdocstrings.github.io/griffe/guide/users/checking/ — Python API breakage check (`griffe check`)
- https://api-extractor.com/pages/overview/demo_api_report/ — TS API report diffing
- https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners — path-based ownership and review routing

## Answer

Since the 2026-09-24 review, impact analysis has only changed in which tool it names. M13 (`33465fe`) and the follow-up `1fbd62b` made codemem the default index in `impact-analysis`, `system-mapping`, `/aa-ma-plan` and the §6.3 pre-check. That **partly fixes gap 3** and **partly fixes gap 7**: the documentation now asks `who_calls` for callers, but codemem's `blast_radius` still returns callees under the same name as project-index's caller-returning tool. Gaps 1, 2, 4, 5 and 6 and recommendations R1, R2, R3, R4 and R6 are **open**; R5 is **partly done**. Of the code-writing skills, only the AA-MA execution commands and a handful of global skills (`safe-refactoring`, `api-spec-workflow`, `triage-issue`, `please_proceed`, `rigor`) invoke impact analysis, and almost always in prose. The everyday writers (superpowers TDD / executing-plans / subagent-driven-development / systematic-debugging, mattpocock `tdd` / `implement`, both `prototype` skills, the gsd executors) never invoke it. The cheapest established practices to add are co-change mining and pre-edit caller checks, because codemem already ships `co_changes` and `who_calls`. Next cheapest is path-based sensitivity tagging (CODEOWNERS-like). API diffing (`griffe check`) and test selection cost more.

## Evidence

### Part A — status of gaps 1–7 and R1–R6 at HEAD `4ad4619`

What changed on the impact surfaces since `c0ec3f2`: `git diff c0ec3f2..HEAD --stat` over `impact-analysis`, `verify-impl`, `gate.py` and `prototype` shows 24+/24− lines. The impact-analysis change is the "Index-Enhanced Analysis" table only (`33465fe`, `500f364`). `verify-impl` is untouched. The `gate.py` edits (`0cec49e`, `ff47970`) do not add an impact question. The `prototype` edit is two lines unrelated to impact.

| Item | Status | Evidence |
|---|---|---|
| **Gap 1** — nothing compares predicted with actual changed files | **Open** | `grep -rn "Expected-Blast\|unpredicted\|predicted"` over `claude-code/ src/ docs/spec docs/templates` returns nothing. §6.3 still asks for a self-reported consolidated tree (`execute-aa-ma-milestone.md:341-367`). The nearest mechanical checks are adjacent, not this one: the §6.7 diagram fence checks drawn `@import/@call` edges against the code (`execute-aa-ma-milestone.md:657-661`, `adc3a0c`), and Angle 6 check 8 checks that Contract paths are drawn in §13 (`plan-verification/SKILL.md:431`, `9aaebf1`). Neither diffs `git diff --name-only` against a predicted set. |
| **Gap 2** — HARD claim, no enforcement | **Open** | The doctrine is unchanged: "Verified at milestone HARD gate via `Skill(impact-analysis)`" (`engineering-standards.md:108-111`) and the "Non-breaking constraint verified \| HARD" row (`engineering-standards.md:139`). The gate is still a comment: `# 4. Impact-analysis evidence (already enforced in 6.3; …)` (`execute-aa-ma-milestone.md:605`). `gate.py:9-21` lists seven questions, none about impact. |
| **Gap 3** — skill ignores codemem | **Partly fixed** | Fixed in: `impact-analysis/SKILL.md:225-235` (codemem `who_calls` / `blast_radius` / `diagram` / `file_summary` / `search_symbols`, `33465fe`); `system-mapping` (same commit); `/aa-ma-plan` Step 1.2 (`aa-ma-plan.md:181-188`, `1fbd62b`); §6.3 pre-check (`execute-aa-ma-milestone.md:333-336`, `1fbd62b`). Still Grep-only: plan-verification Angle 3 ("Use Grep to search for imports", `plan-verification/SKILL.md:181-182`); Phase 3.5 (`PHASE_3_RESEARCH.md:157-165`); `/execute-aa-ma-full` §C, which has no index pre-check (`execute-aa-ma-full.md:327-333`); the step command (`execute-aa-ma-step.md:179-183`); the skill's own 5-point checklist body ("Use `Grep` to find imports", `impact-analysis/SKILL.md:37-40`). `co_changes`, `hot_spots` and `owners` (the history tools the review singled out) appear nowhere in the skill's table (`impact-analysis/SKILL.md:229-235`). |
| **Gap 4** — blind to the markdown / `Skill()` graph | **Open** | The skill still exempts "Documentation-only changes" (`impact-analysis/SKILL.md:26`) and has no rule for counting `Skill()` / `/command` references as callers. The extractor exists (`packages/codemem-mcp/src/codemem/draw/plugin_surface.py:86`, output `docs/architecture/plugin-surface.md`), but the lint states "plugin-surface edges are not in the codemem index" (`src/aa_ma/render/mermaid_lint.py:101`), so `who_calls` cannot answer for markdown. A live `co_changes` result partly stands in for it: `claude-code/commands/execute-aa-ma-milestone.md` co-changes with `execute-aa-ma-full.md` (6 commits), `execute-aa-ma-step.md` (6) and `skills/aa-ma-execution/SKILL.md` (5). Those are its markdown "callers". |
| **Gap 5** — author grades own work | **Open** | §6.3 is unchanged in shape (`execute-aa-ma-milestone.md:328-367`). The §6.8 `verify-impl` skill is unchanged since `c0ec3f2` (empty diff) and receives no impact input; its code-reviewer is dispatched on the diff alone (`execute-aa-ma-milestone.md:784-789`). |
| **Gap 6** — no link to prototypes | **Open** | `grep -n -i "impact\|caller\|blast"` on `claude-code/skills/prototype/SKILL.md` returns nothing. The verdict-capture rule (`prototype/SKILL.md:27`) has no plan-delta check. |
| **Gap 7** — `blast_radius` means callees in codemem, callers in project-index | **Partly fixed (docs only)** | Fixed in the docs: the skill states the asymmetry and routes callers to `who_calls` (`impact-analysis/SKILL.md:225-232`), and so does §6.3 (`execute-aa-ma-milestone.md:334-336`, commit message `1fbd62b`: "the old wording would have measured the wrong direction"). Not fixed at the tool: codemem still documents "blast_radius — downstream callees" (`mcp_tools/__init__.py:11,219`). A live call on `_read_milestone` returned 8 callees under key `downstream`, while `who_calls` returned `answer`, `main` and test functions. Both servers are live here: codemem via the project `.mcp.json` and project-index globally (`~/.claude.json`). Leftover wrong wording: `claude-code/codemem/README.md:63` ("Downstream transitive callees — what breaks if you change `name`"; callees are not what breaks) and global `~/.claude/skills/code-intelligence-index/SKILL.md:49` ("What breaks if I change this? \| `blast_radius`", true only for project-index). **New defect found:** `aa_ma_context` reads `blast.get("callees", [])` (`mcp_tools/__init__.py:1287`), but `blast_radius` returns its list under `"downstream"` (`:224,257`; key confirmed live). Every symbol's "blast-radius: N downstream" line therefore renders as 0. This comes from reading the code; I did not run `aa_ma_context` because there is no active task. |
| **R1** predicted-vs-actual | **Open** | See gap 1. |
| **R2** persist + honest enforcement | **Open** | The §7.2 context-log template still has only Key outcome / Artifacts, with no Impact line (`execute-aa-ma-milestone.md:952-953`). No `IMPACT_ANALYSIS` provenance token exists anywhere (grep returns nothing). The doctrine is neither enforced nor downgraded (gap 2). |
| **R3** prototype verdict delta | **Open** | No `verdict-changes-plan` field anywhere (grep returns nothing). |
| **R4** pre-edit step check | **Open** | The step command is still "Impact awareness (lightweight, no blocking) … Full impact analysis verification runs at milestone boundary" (`execute-aa-ma-step.md:179-183`), with no codemem call. |
| **R5** teach codemem + markdown graph | **Partly done** | codemem is the default and each tool's direction is now stated (gap 3/7 rows). Missing: `co_changes` / `hot_spots` rows, and `Skill()` references as callers (gap 4). |
| **R6** remove self-grading | **Open** | See gap 5. |

**Did `33465fe` (M13) fix gaps 3 and 7?** Partly. It covered only `impact-analysis` and `system-mapping`, and changed the §6.3 pre-check text not at all. That pre-check still said `blast_radius` until `1fbd62b` the next day, which also fixed `/aa-ma-plan`. Neither commit touched plan-verification Angle 3, Phase 3.5, `/execute-aa-ma-full` §C or the step command (gap 3 remainder). Neither renamed codemem's `blast_radius` or fixed `aa_ma_context` (gap 7 remainder).

### Part B — code-writing skills and commands: do they invoke impact analysis?

Legend: **pre-edit** = before the code is written; **post-edit** = after it exists, by the author; **review** = by a separate reviewer; **plan** = against a plan, not code.

**Forge (`claude-code/`)**

| Skill / command | Writes code? | Invokes impact analysis? | Point | How |
|---|---|---|---|---|
| `/execute-aa-ma-step` | yes | no (prose "awareness") | pre-edit, non-blocking | prose only (`execute-aa-ma-step.md:179-183`) |
| `/execute-aa-ma-milestone` | yes | **yes** | post-edit (§6.3 runs after §5.2 sub-steps) | `Skill(impact-analysis)` + advisory codemem `who_calls` pre-check (`execute-aa-ma-milestone.md:328-367`); gate check #4 is only a comment (`:605`) |
| `/execute-aa-ma-full` | yes | **yes** | post-edit, per milestone | `Skill(impact-analysis)` only, no index pre-check (`execute-aa-ma-full.md:327-353`) |
| `aa-ma-execution` skill | yes (orchestrates) | yes | post-edit, milestone boundary | `Skill()` reference (`aa-ma-execution/SKILL.md:172-182`) |
| `/ops-mode`, `operational-constraints` | mode switch, not a writer | yes, "for ALL code changes … Before and after" | pre + post-edit | prose `Skill()` (`ops-mode.md:60-62`; `operational-constraints/SKILL.md:153-156,246`) |
| `prototype` | yes (throwaway) | no | none | — (`prototype/SKILL.md`, no mention) |
| `debugging-strategies` | yes (fixes) | no | none (finds callers to diagnose, not to assess the change) | grep (`debugging-strategies/SKILL.md:328`) |
| `defense-in-depth` | yes (adds validation layers) | no | none | — |
| `dispatching-parallel-agents` | yes (agents fix problems) | no | none | — |
| `write-a-skill` | yes (skills are this repo's product) | no | none | — |
| `/sole-dev-merge` | yes (Stage B `ruff format` / `ruff check --fix` auto-fixes, Stage D auto-fix of CRITICALs) | no | review (Stage C code-reviewer on `git diff`, no impact input) | — (`sole-dev-merge.md:144,229-255,260-275,440`) |
| `verify-impl` (§6.8) | no (review) | no impact input | review | — |
| `plan-verification` Angle 3 / Phase 3.5 | no (plan) | yes | plan | fresh agent + Grep (`plan-verification/SKILL.md:160-200`); grep (`PHASE_3_RESEARCH.md:157-165`) |
| `understand-codebase` PLAYBOOK-CONTRIBUTE | no (docs) | recommends it to contributors | pre-edit (advice) | prose `Skill()` / codemem `who_calls` (`understand-codebase/references/PLAYBOOK-CONTRIBUTE.md:38`) |

**Global (`~/.claude/skills`, `~/.claude/commands`, `~/.agents/skills`, plugins)**

| Skill / command | Writes code? | Invokes impact analysis? | Point | How |
|---|---|---|---|---|
| `/please_proceed` | yes | yes | pre-edit ("Before ANY code changes") | prose pointer to `~/.claude/docs/impact-analysis.md`, not `Skill()` (`commands/please_proceed.md:118-120`) |
| `rigor` | meta | yes, "for shared code" | pre-edit | prose `Skill()` (`skills/rigor/SKILL.md:29`) |
| `safe-refactoring` | yes | **yes, required** | pre-edit (Phase 1) | `sg` occurrence count + `Skill(impact-analysis)` (`skills/safe-refactoring/SKILL.md:52-59,215`) |
| `api-spec-workflow` | yes | yes | pre-edit + final | `Skill()` (`skills/api-spec-workflow/SKILL.md:91,164`) |
| `triage-issue` | yes (fix) | yes | after choosing the fix approach, pre-edit | `Skill()` (`skills/triage-issue/SKILL.md:251`) |
| gstack `investigate` | yes | partial | pre-fix: asks the user if the fix touches >5 files | file-count prose (`skills/investigate/SKILL.md:619-621,691`) |
| gstack `review` / `qa` | yes (auto-fixes) | partial | review | "grep the callers" prose (`skills/review/SKILL.md:325,662`; `skills/qa/SKILL.md:327`) |
| superpowers `test-driven-development` (+ `~/.claude/skills` copy) | yes | no | none; "All tests pass" is the only regression net | — (`superpowers/6.4.1/skills/test-driven-development/SKILL.md:301`; `~/.claude/skills/test-driven-development/SKILL.md:338`) |
| superpowers `executing-plans` | yes | no | none (one final reviewer) | — (`executing-plans/SKILL.md:9-18`) |
| superpowers `subagent-driven-development` (+ copy) | yes | no | review (spec compliance + code quality per task; no impact input) | — (`subagent-driven-development/SKILL.md:8,55`) |
| superpowers `systematic-debugging` (+ copy) | yes (fix) | no | none ("Understand Dependencies" asks what the broken code *needs*, not who calls the fix) | — (`systematic-debugging/SKILL.md:138-141`) |
| superpowers `requesting-code-review` | no (review) | no | review | — |
| mattpocock `tdd` (plugin `engineering/tdd`, `~/.agents/skills/tdd`) | yes | no | none | — |
| mattpocock `implement` | yes | no | none; typecheck + full suite at the end | — (`mattpocock-skills/1.2.3/skills/engineering/implement/SKILL.md:11`) |
| mattpocock `prototype` | yes (throwaway) | no | none | — |
| mattpocock `diagnosing-bugs` / `~/.agents/skills/diagnose` | yes | no | post-fix architectural hand-off only | — (`engineering/diagnosing-bugs/SKILL.md:140`) |
| mattpocock `code-review` | no (review) | no (Standards + Spec axes) | review | — |
| `feature-dev` plugin | yes | partial | pre-edit exploration (code-explorer agents map dependencies, Phase 2); review (3 code-reviewers, Phase 6) | agents, no call-graph tool (`feature-dev/1.0.0/commands/feature-dev.md:36-41,106`; `agents/code-explorer.md:24`) |
| gsd `execute-phase` / `quick` / `fast` / `code-review-fix` / `debug` | yes | no mention in SKILL.md (0 hits) | none | — (workflow files not read, see Not pursued) |
| `code-intelligence-index` | no (tool hub) | supplies impact-analysis | — | maps `blast_radius` to "What breaks if I change this?", which is correct for project-index and wrong for codemem (`skills/code-intelligence-index/SKILL.md:13,49`) |

Pattern: impact analysis runs **post-edit, inside AA-MA milestone execution**, and **pre-edit only in refactor/API/triage skills**. Outside AA-MA, the high-traffic writers (TDD, plan executors, debuggers, prototypes) never call it. Every invocation is prose-instructed, with no hook, token or gate behind it.

### Part C — established author-time change-impact practice

1. **Static call graphs.** Before an edit, resolve which callers can reach the changed symbol. PyCG builds Python call graphs statically at about 0.38 s per 1k LoC with about 99.2% precision and 69.9% recall, and the authors show it supporting dependency impact analysis (https://arxiv.org/abs/2103.00587). The recall figure matters: a static graph under-reports in a dynamic language, so a zero-caller result is not proof of safety. *We have:* codemem `who_calls` (`mcp_tools/__init__.py:162-203`).
2. **Co-change / logical coupling.** Mine version history for files that change together. Zimmermann et al. report that such rules "suggest and predict likely further changes", reveal coupling that program analysis cannot detect, and "prevent errors due to incomplete changes" (https://www.st.cs.uni-saarland.de/papers/icse2004/). *We have:* codemem `co_changes`, which keeps only pairs with no import/call edge (`mcp_tools/__init__.py:510-525`). Live on this repo: `README.md` co-changes with `docs/spec/claude-code-foundations.md` (13), `SECURITY.md` (10) and `docs/spec/aa-ma-quick-reference.md` (7). That is exactly the stale-count file set CLAUDE.md lists by hand.
3. **Test impact analysis / test selection.** Google's TAP keeps an in-memory, multi-GB "graph of coarse-grained dependencies between various tests and build rules" and runs only the tests a change transitively affects (https://testing.googleblog.com/2011/06/testing-at-speed-and-scale-of-google.html; also Memon et al., ICSE-SEIP 2017, https://research.google/pubs/taming-google-scale-continuous-testing/). Facebook learns a selector from historical outcomes. It reports catching over 95% of individual test failures and over 99.9% of faulty changes at about half the infrastructure cost (https://arxiv.org/abs/1810.05286). For Python, pytest-testmon "selects and re-executes only tests affected by recent changes" using a `.testmondata` dependency database (https://pypi.org/project/pytest-testmon/, v2.2.0). *We have:* `who_calls` already returns test functions. Of the callers of `_read_milestone`, all but `answer` and `main` were `test_*` functions, which gives a static, zero-cost "tests to run first" list. testmon is not in `uv.lock`.
4. **API / contract diffing.** `griffe check` compares the current code against the latest git tag (or `--against <ref>`). It reports removed or moved parameters, changed defaults, newly required parameters, removed objects and removed base classes, and fails CI on any breakage (https://mkdocstrings.github.io/griffe/guide/users/checking/). It does not yet detect return-type or attribute-type changes. For TypeScript, API Extractor keeps a committed `etc/<pkg>.api.md` report. The PR build fails if the report is stale, and a branch policy can require approval when it changes (https://api-extractor.com/pages/overview/demo_api_report/). *We have:* layer contracts only. import-linter runs in CI (`.importlinter:31-45`, `.github/workflows/security.yml:147`). griffe is not in `uv.lock`, and the Contract block in plans (`docs/templates/plan-template.md:82-87`) is prose that nothing diffs.
5. **Security-sensitive path tagging.** CODEOWNERS uses gitignore-style patterns to request reviews automatically, and branch protection can require approval from a code owner (https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners). *We have:* no CODEOWNERS file. We do have the `Critical-Path:` enum, whose `hook-modification` value is already defined by path globs (`claude-code/hooks/**`, `.github/workflows/**`, `src/aa_ma/{gate,enforce,grammar,plan_parsers}.py`; `engineering-standards.md` Critical-Path table). But the plan author declares it by hand, and nothing derives it from the files a change touches.

**Cheapest to add, in order:**
1. **`co_changes` in §6.3 and the skill table.** Report files that historically co-change with the diff but are missing from it. No new dependency, already measured useful here, and it partly covers gap 4 (markdown callers) and the stale-count rule. Effort: S.
2. **`who_calls` at step pre-edit (R4), with test callers as the test-selection list.** No new dependency; it reuses gap 7's corrected direction. Effort: S.
3. **Path-glob → `Critical-Path` derivation (CODEOWNERS-like).** A static map from changed paths to required evidence. The `hook-modification` globs already exist in doctrine. Effort: S–M, and it is itself `hook-modification`.
4. **`griffe check -s src --against <last tag>`** as an advisory §6.3 line for Python repos. One dev dependency, and it is Python-only. Effort: S, but the value depends on the public-API surface: `aa_ma` is mostly CLIs.
5. **Coverage-based or ML test selection (testmon, predictive).** The most setup for the least gain at this repo's size: the default suite already runs in full. Effort: M+.

## Not pursued
- Running `aa_ma_context` live to confirm the `callees`/`downstream` key bug renders 0. It needs an active task, and `.claude/dev/active/` is empty.
- Whether to rename codemem's `blast_radius` (e.g. to `callees`) and the compatibility cost. That is a design decision, not research.
- gsd workflow files (`~/.claude/get-shit-done/workflows/*`, gsd agents). Only the SKILL.md entry points were grepped.
- The other ~40 installed plugins (e.g. `tdd-workflows`, `code-refactoring`, `code-simplifier`, `ralph-loop`, `typesafe`, `ponytail`) were not read for impact steps.
- Domain-specific global skills that write code (`fastapi-*`, `alembic-migrations`, `dbt-development`, etc.).
- Re-measuring the baseline's empirical counts (79 milestones, 0 HIGH) over plans completed since 2026-09-24.
- The full PDF of Memon et al. 2017. Its exact test-selection method was taken from Google's 2011 TAP blog, not the paper.
- Whether codemem's `co_changes` should exclude `.claude/dev/**` artefacts. They dominate the `execute-aa-ma-milestone.md` and `gate.py` results.
- The codemem index was 3 commits behind HEAD (`75efd73` vs `4ad4619`); live co-change counts were not re-run after a rebuild.
- Bazel/Buck `rdeps`-style build-graph test selection, and Microsoft Azure DevOps Test Impact Analysis. Both are secondary to the sources above.
