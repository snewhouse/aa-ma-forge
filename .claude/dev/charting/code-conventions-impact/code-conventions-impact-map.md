# Charting: code-conventions-impact

## Destination

A plan-ready spec for one `/aa-ma-plan` that (1) wires impact analysis into the coding workflow at author time and at review, (2) sets forge-canonical coding conventions — comments, docstrings, logging, SecOps, design principles — for Python, Bash, Markdown skills, TS/JS and R/SQL, and (3) defines how reusable code is captured and when it graduates from snippet to module to library.

## Notes

Domain: aa-ma-forge coding doctrine (`claude-code/rules/engineering-standards.md`, ADR-0001) and the skills that apply it while code is written. Prior evidence: `docs/research/impact-analysis-lifecycle-review.md` (2026-09-24; gaps 1–7, R1–R6, two open questions).

Skills every session should consult: `aa-ma-research`, `grill-with-docs`, `impact-analysis`, `logging-and-comments`, `python-quality-gates`, `deslop-shared-libs`, `ponytail`.

Standing decisions from the chart session (Ste, 2026-10-08):
- **Forge is canonical.** The coding doctrine and its skills ship from aa-ma-forge; global-only skills (`logging-and-comments`, `python-quality-gates`, `secrets-management`, `senior-secops`, `bash-defensive-patterns`, …) either move in or are declared-external (engineering-standards §1 three-valued references).
- **One plan.** All three themes are milestones of a single plan.
- **Tiered language depth.** Full conventions for Python, Bash and Markdown skills/commands; TS/JS and R/SQL get the language-neutral core plus a short per-language card.
- **Touched code only.** New and modified code must comply; a lint baseline freezes existing debt; backfill is out of scope.
- **Reuse scope** covers generic utilities, biomedical helpers, genericized client code and templates/scaffolds. Client-derived code is confidential until genericized — this constrains where the collection may live.
- **Defects carried to the plan** (found by T2/T4 research, deferred by Ste 2026-10-08; charting does not fix them): (1) `packages/codemem-mcp/src/codemem/mcp_tools/__init__.py:1287` — `aa_ma_context` reads `callees` but `blast_radius` returns `downstream` (line 252), so its count is always 0; (2) `~/.claude/skills/senior-secops/scripts/security_scanner.py` — stub `analyze()` always returns no findings; (3) `.github/workflows/security.yml:39` — Bandit `|| true` can never fail CI.
- Biorelate `galactic-*` material is pattern reference only (`~/.claude/_archive/biorelate/`); never contact Biorelate remotes (L-1289).

## Decisions so far

<!-- one line per RESOLVED ticket, newest last -->

- [Ticket 1: Where is every coding convention stated today, and where is each one enforced?](#ticket-1-where-is-every-coding-convention-stated-today-and-where-is-each-one-enforced): ~8.8k auto-loaded tokens; real standard is global-only; enforcement thin (bandit `|| true`, D1xx ignored); ponytail↔SOLID/TDD and debug-env-var contradictions.
- [Ticket 4: What is the state of impact analysis now, and which code-writing skills invoke it?](#ticket-4-what-is-the-state-of-impact-analysis-now-and-which-code-writing-skills-invoke-it): most gaps still open; `aa_ma_context` callees/downstream key bug; no general coding skill invokes it; cheapest wins = co_changes, who_calls pre-edit, path tagging.
- [Ticket 3: What should the short TS/JS, R and SQL convention cards contain?](#ticket-3-what-should-the-short-tsjs-r-and-sql-convention-cards-contain): cards drafted (TS strict+typescript-eslint+pino, R Air/lintr/roxygen2/logger/renv, SQLFluff+dbt style); conflicts = pino stdout, @param vs Args:, SQL keyword case.
- [Ticket 5: What reusable code exists today, and how do others curate and graduate it?](#ticket-5-what-reusable-code-exists-today-and-how-do-others-curate-and-graduate-it): nothing packaged; ~3k untested snippet fences in skills; git-HEAD helper ×6 is the first real graduation candidate; copier + uv workspaces are the viable distribution paths.
- [Ticket 2: How do our Python, Bash and Markdown-skill conventions compare with current best practice?](#ticket-2-how-do-our-python-bash-and-markdown-skill-conventions-compare-with-current-best-practice): text is strong, enforcement is not — 4 silent-pass security checks, no supply-chain layer, 6 oversized skills, no skill evals; 19 prioritised actions.
- [Ticket 6: Should impact analysis be an explicit step inside the coding skills, and at which points?](#ticket-6-should-impact-analysis-be-an-explicit-step-inside-the-coding-skills-and-at-which-points): global index-gated PreToolUse hook (once/file/session) + forge skills name it; all of R1/R3/R4/R6; callers+tests, co-change, API diff, path-tag dimensions; plugin-surface edges into codemem; `callees` rename + alias; blocking left to T7.
- [Ticket 7: Is the impact check HARD-enforced in the gate or downgraded to SOFT?](#ticket-7-is-the-impact-check-hard-enforced-in-the-gate-or-downgraded-to-soft): HARD, gate-computed (DIAGRAM_VERIFIED pattern); unpredicted / predicted-unchanged / co-change (≥5 & ≥50%) misses need `Impact-Explained:`; undeclared API breaks block; derived path tags add CRITICAL_PATH_REVIEW; new plans only.
- [Ticket 8: What is the comments and docstrings standard per language?](#ticket-8-what-is-the-comments-and-docstrings-standard-per-language): native doc format for public API in every language; full Ruff D (google, D417) on touched files; `# why:` on justified suppressions only, RUF100 removes the rest; `TODO(#N|ADR-NNNN)`; code docs exempt from ponytail; reviewer WARNs on comment substance.
- [Ticket 9: Is `logging-and-comments` adopted into the forge as the logging standard, and what changes?](#ticket-9-is-logging-and-comments-adopted-into-the-forge-as-the-logging-standard-and-what-changes): moves into forge as one revised skill; NullHandler optional; JSON for services (opt-in elsewhere); ruff hook feeds findings back; `LOG_LEVEL` + `HOOK_DEBUG`; one hook log + shared `lib/log.sh`; `-euo` + BashFAQ/105 caveats.
- [Ticket 10: What is the SecOps baseline, and where does each check run?](#ticket-10-what-is-the-secops-baseline-and-where-does-each-check-run): 4-layer fail-loud baseline (edit/commit/CI/gate) incl. gitleaks, uv --locked + audit, osv-scanner, Dependabot; Ruff S replaces Bandit after a pinned coverage comparison (gap fallback); secops → router, secrets-management adopted, log redaction helpers; boundary validation + asserts; LLM output untrusted; rollout via template.
- [Ticket 11: How are the design principles stated so they are checkable, and how is the YAGNI-vs-SOLID tension resolved?](#ticket-11-how-are-the-design-principles-stated-so-they-are-checkable-and-how-is-the-yagni-vs-solid-tension-resolved): start concrete, earn abstractions by evidence (Ste's policy); knowledge-DRY now, code ~3rd occurrence; C901/PLR0913 + `# why:`; §2 as heuristic/check table; testing folded in — risk-proportionate TDD, code waiver enum canonical, gate runs tests (TESTS_VERIFIED).
- [Ticket 13: Where does the reusable-code collection live?](#ticket-13-where-does-the-reusable-code-collection-live): private Carmen uv repo (tag-pinned git source) for library + tested PEP 723 snippets; public-forge router skill with runtime index (ships no names); public copier template repo; forge-canonical generic helpers vendored with drift check; provenance header + denylist/gitleaks/approval gate for client-derived code.
- [Ticket 14: When does shared code graduate from snippet to module to library?](#ticket-14-when-does-shared-code-graduate-from-snippet-to-module-to-library): snippet → `_experimental` module on evidenced, same-contract reuse; → public API after 2 stable minors + 2 repos; rising tests (griffe at library); SemVer 0.y→1.0; one package + extras; header+licence+test metadata; fix-or-delete in 30 days; router check before new helpers.
- [Ticket 15: What conventions govern Markdown skills and commands as prompt-as-code?](#ticket-15-what-conventions-govern-markdown-skills-and-commands-as-prompt-as-code): fold writing-for-agents-eval in; 500-line cap + ratchet; strict frontmatter schema test; ≥3 `claude plugin eval` cases for gate skills (scheduled, not gating); all 14 commands → skills now; why-or-pointer on MUST rules; declared hook contract + real-payload bats.

## Tickets

### Ticket 1: Where is every coding convention stated today, and where is each one enforced?
- Type: research
- Mode: AFK
- Status: RESOLVED
- Blocked-by: —
#### Question
Inventory every source that states a coding convention for Claude or for code in Ste's projects: `claude-code/rules/*.md`, `~/.claude/CLAUDE.md`, `~/.claude/rules/*.md`, forge skills (`operational-constraints`, `defense-in-depth`, `system-mapping`, `impact-analysis`) and global-only skills (`logging-and-comments` + `references/ruff-baseline.toml`, `python-quality-gates`, `bash-defensive-patterns`, `secrets-management`, `senior-secops`, `deslop-shared-libs`, `ponytail`), plus the mechanical layer (`pyproject.toml` ruff config, `.github/workflows/*`, `claude-code/hooks/security-static-check.sh`, pre-commit if any). For each topic — comments, docstrings, logging, security/SecOps, KISS/DRY/SOLID/SoC, testing — record: where it is stated (file:line), whether it is auto-loaded or on-demand, whether anything enforces it (lint rule / CI job / hook / gate / nothing), and every duplication or contradiction between sources. Count auto-loaded tokens for the rule files. Output: `docs/research/code-conventions-impact-inventory.md`.
#### Answer
Seven files auto-load every session (~8.8k tokens; ~12.2k here with project CLAUDE.md + ponytail's SessionStart injection). The real comments/docstring/logging standard lives only in global `logging-and-comments`. Mechanical enforcement is thin: ruff on `src/` only with D101–D107 ignored (`pyproject.toml:83`), `packages/` unchecked by CI; ShellCheck; a 5-pattern commit hook; bandit runs with `|| true` so it can never fail CI (`security.yml:39`); pytest/bats; import-linter. Unenforced: why-comments, `# why:` on suppressions, secrets-in-logs, KISS justification; "tests passing — HARD" is a comment in the §6.7 gate. Contradictions: ponytail vs SOLID and TDD depth; TDD-Waiver enum vs the rule's skip list; 4 debug env-var names, log formats and hook-log paths disagree; the ruff edit hook discards findings the skill says it reports. See [docs/research/code-conventions-impact-inventory.md](../../../../docs/research/code-conventions-impact-inventory.md). Two claims spot-checked by hand 2026-10-08.

### Ticket 2: How do our Python, Bash and Markdown-skill conventions compare with current best practice?
- Type: research
- Mode: AFK
- Status: RESOLVED
- Blocked-by: —
#### Question
Against primary sources, state current best practice and gap-check what we ship, per topic. Python: PEP 8/257, Google Python Style Guide, numpydoc, the logging HOWTO and "logging in libraries" guidance, Ruff rule families (D, S, BLE, G, T20, LOG, TRY), Bandit, pip-audit/uv audit. Bash: Google Shell Style Guide, ShellCheck, `set -euo pipefail` caveats. Markdown skills/commands: Anthropic's skill-authoring guidance and Claude Code docs on skills/commands/hooks (prompt-as-code: frontmatter, progressive disclosure, testability). SecOps: OWASP ASVS / Top 10, NIST SSDF (SP 800-218), OpenSSF Scorecard, secret scanning (gitleaks), dependency pinning and supply chain. Design principles: KISS/DRY/SOLID/SoC, rule of three, YAGNI — including published critiques (e.g. DRY's wrong-abstraction cost). Use the Ticket 1 sources list if resolved; otherwise read the skills directly. Output: `docs/research/code-conventions-impact-best-practice.md` with a strengths / weaknesses / trade-offs table per topic.
#### Answer
On paper our conventions match or beat current guidance (logging/comments standard aligns with the Python logging docs, PEP 8, Google style, Claude Code hooks docs). Four places break our own no-silent-failure rule: CI Bandit runs `|| true`; the `secrets-management` TruffleHog example lacks `--fail` so cannot block; `senior-secops/scripts/security_scanner.py` is a stub whose `analyze()` hard-codes `findings = []` (always clean); CI Ruff checks `src/` only (all three spot-checked 2026-10-08). Biggest best-practice gaps: no supply-chain checks (no `uv sync --locked`, dependency audit, Dependabot or repo secret scan); bash skills omit `set -e` pitfalls; the documented `TODO(ADR-0014)` format fails Ruff TD003; 6 skill/command files exceed the 500-line guideline (aa-ma-execution 1295, execute-aa-ma-milestone 1244, aa-ma-plan 1154, sole-dev-merge 1054, execute-aa-ma-full 757, plan-verification 608); unknown frontmatter keys (`triggers`) silently ignored; `dispatching-parallel-agents` misuses `context:`; no skill has behavioural evals. Ends with 19 prioritised keep/change/add/drop actions, each naming its enforcing tool (Ruff S/D/RUF100/PGH, ShellCheck optional checks, `uv sync --locked`, `uv audit`, gitleaks, Dependabot, extended frontmatter pytest). See [docs/research/code-conventions-impact-best-practice.md](../../../../docs/research/code-conventions-impact-best-practice.md).

### Ticket 3: What should the short TS/JS, R and SQL convention cards contain?
- Type: research
- Mode: AFK
- Status: RESOLVED
- Blocked-by: —
#### Question
For each of TS/JS, R and SQL, find the de-facto standard tooling and idiom from primary sources: formatter, linter and its security rules, doc-comment format (TSDoc/JSDoc, roxygen2, SQL comment conventions), logging idiom, test runner, dependency audit. Candidates to verify, not assume: TypeScript + typescript-eslint + Prettier/Biome, TSDoc, pino; tidyverse style guide + lintr + styler + roxygen2 + logger; sqlfluff + dialect choice. Keep each card to what a one-page reference can carry. Output: `docs/research/code-conventions-impact-language-cards.md`.
#### Answer
Three one-page cards, 68 primary-source URLs. **TS/JS:** `strict` (default since TS 6.0) + `noUncheckedIndexedAccess`; typescript-eslint type-checked config on ESLint v10; Prettier *or* Biome, never both; TSDoc (.ts) / JSDoc (.js); pino to stderr; Vitest; `npm`/`pnpm audit` + minimum release age; eslint-plugin-security advisory only (false positives). **R:** tidyverse style, Air formatter (pre-1.0; styler fallback), lintr, roxygen2, logger (stderr, JSON layout), testthat 3e, renv, osv-scanner on `renv.lock` (riskmetric is quality scoring, not audit). **SQL:** SQLFluff with explicit dialect, dbt style (lowercase, trailing commas, CTEs), parameterised queries + allow-listed identifiers, docs in the catalogue (`COMMENT ON` / dbt `persist_docs`), dbt unit tests or pgTAP. Conflicts with the Python conventions: pino defaults to stdout (vs logs→stderr); Google `Args:` vs `@param` tag vocabularies; ruff TODO check has no equivalent elsewhere; SQL guides disagree on keyword case (sqlstyle.guide — Simon Holywell, not Mazur — wants UPPERCASE). Repo has no pre-commit config; Air and SQLFluff ship pre-commit hooks; one osv-scanner CI job covers JS lockfiles and `renv.lock`. See [docs/research/code-conventions-impact-language-cards.md](../../../../docs/research/code-conventions-impact-language-cards.md).

### Ticket 4: What is the state of impact analysis now, and which code-writing skills invoke it?
- Type: research
- Mode: AFK
- Status: RESOLVED
- Blocked-by: —
#### Question
Update `docs/research/impact-analysis-lifecycle-review.md` to today without rewriting it: for each gap 1–7 and recommendation R1–R6, is it fixed, partly fixed or open as of HEAD (git log since c0ec3f2; M13 commit 33465fe made codemem the default in impact-analysis/system-mapping — did that fix gap 3 and gap 7?). Then list every skill or command that writes or edits code (forge and global: `test-driven-development`, `superpowers:*`, `subagent-driven-development`, `executing-plans`, `please_proceed`, `execute-aa-ma-step/milestone/full`, `systematic-debugging`, `prototype`, …) and say whether each invokes impact analysis, at which point (pre-edit, post-edit, review) and how. Finally, summarise how established practice handles change-impact analysis at author time (static call graphs, co-change mining, test impact analysis / test selection, API/contract diffing, security-sensitive-path tagging) with primary sources. Output: `docs/research/code-conventions-impact-impact-status.md`.
#### Answer
Since the 2026-09-24 review: gap 3 partly fixed (M13 `33465fe` + `1fbd62b` put codemem into impact-analysis, system-mapping, aa-ma-plan and the §6.3 pre-check; Angle 3, Phase 3.5, execute-full §C and execute-step still grep). Gap 7 fixed in docs only: codemem `blast_radius` still returns callees, and `aa_ma_context` reads `blast.get("callees")` (`packages/codemem-mcp/src/codemem/mcp_tools/__init__.py:1287`) while the tool returns key `downstream` (line 252) — so it always reports 0 (verified by reading 2026-10-08; a bug outside charting scope, carried to the plan). Gaps 1, 2, 4, 5, 6 and R1–R4, R6 open; R5 partial. Invokers: only AA-MA milestone/full (post-edit) and global safe-refactoring, api-spec-workflow, triage-issue, please_proceed, rigor (pre-edit), all as prose; superpowers TDD/executing-plans/subagent-driven-development/systematic-debugging, mattpocock tdd, both prototype skills and gsd executors never invoke it. Cheapest additions: codemem `co_changes` in §6.3 (README co-changes with stale-count docs), a `who_calls` pre-edit check whose test callers become tests-to-run-first, path-glob tagging to Critical-Path; `griffe check` and testmon cost more. See [docs/research/code-conventions-impact-impact-status.md](../../../../docs/research/code-conventions-impact-impact-status.md).

### Ticket 5: What reusable code exists today, and how do others curate and graduate it?
- Type: research
- Mode: AFK
- Status: RESOLVED
- Blocked-by: —
#### Question
Find what already exists: global skills that hold code (`pharma-use-case-library`, `terraform-module-library`, `deslop-shared-libs`, others), any snippet/utility directories under `~/.claude`, `~/dev/carmen-provenance-labs/*` and this repo (e.g. helpers duplicated across `src/` and `packages/`), and duplicated functions across Carmen projects (name and file, never client data). Then prior art for curation and graduation: rule of three, internal packages via uv workspaces or a private index, copier/cookiecutter templates, git subtree vs package, GitHub gists, "inner source" practice, semantic versioning for internal libs, and what keeps a snippet collection from rotting (tests, provenance, ownership). Output: `docs/research/code-conventions-impact-reuse-prior-art.md`.
#### Answer
Nothing reusable is packaged or versioned: ~3,037 untested Python fences live as prose in global skill `references/`; retry/rate-limit helpers recur in ~14 skills, logging setup in 6, Ensembl/ID mapping in 3–4. The three named library skills hold no executable code. Only 2 Carmen repos exist (1 with Python), so cross-Carmen duplication is not yet measurable. Strongest real duplicate: a git-HEAD/provenance helper written ~6 times (5 across this repo's `src/` and `packages/`, 1 in Carmen; spot-check found 6 forge files calling `rev-parse HEAD`), only one with a timeout and env scrubbing; placement is constrained because codemem must stay installable without `aa_ma`. Prior art: rule of three vs Metz's wrong abstraction; 10 distribution options compared (copier and uv workspaces have real update paths; gists and submodules weak); InnerSource, SemVer, rot evidence; Skills/MCP for AI discovery. Graduation criteria listed as options, not decided. Names only recorded for Carmen repos (confidentiality). See [docs/research/code-conventions-impact-reuse-prior-art.md](../../../../docs/research/code-conventions-impact-reuse-prior-art.md).

### Ticket 6: Should impact analysis be an explicit step inside the coding skills, and at which points?
- Type: grilling
- Mode: HITL
- Status: RESOLVED
- Blocked-by: 4
#### Question
Given Ticket 4: does impact analysis become a named step in every code-writing skill (pre-edit caller check, post-edit predicted-vs-actual diff, review input), or stay centralised in the AA-MA execution commands? Which of R1–R6 are adopted, and how does it cover dependencies, interfaces/contracts, tests (test impact), security-sensitive paths and downstream behaviour, including the markdown `Skill()` graph?
#### Answer
**Mechanism: hook + forge skills.** A global, non-blocking PreToolUse hook on Edit/Write injects impact context for the target file; forge-owned writers (`execute-aa-ma-*`, `prototype`, `defense-in-depth`, `write-a-skill` successor) name `Skill(impact-analysis)` explicitly. Rejected: forking third-party writers (superpowers, mattpocock, gsd) to add a step; AA-MA-only (ad-hoc coding gets nothing); a prose rule line (nothing behind it — T4 found every current invocation is prose).
- **Hook behaviour:** index-gated — acts where a codemem index exists; otherwise one `systemMessage` per session ("no index — run codemem build"), never a silent fail-open (L-1319). Fires once per file per session, silent at 0 external callers and 0 co-changes, output capped at ~5 lines.
- **Points (all four):** pre-edit caller check (R4; test callers listed as tests-to-run-first); post-edit predicted-vs-actual at §6.3 (R1: `git diff --name-only` vs the plan's Expected-Blast-Radius + `co_changes` misses, one line per unpredicted file); ad-hoc commits outside a plan get an advisory co_changes-at-commit check instead; review input — the unpredicted-file list goes to the fresh §6.8 code-reviewer, §6.3 stops self-grading (R6); prototype verdict delta — `PROTOTYPE` entry gains `verdict-changes-plan: YES/NO`, YES triggers an Angle-3 check on the decision delta (R3).
- **Dimensions (all four):** callers + tests (codemem `who_calls`); co-change/downstream (`co_changes`); contract/API diff (`griffe check` for Python, API Extractor for TS — new dev deps); security path tagging — a path-glob map derives `Critical-Path` from touched files, alongside hand declaration.
- **Markdown graph:** load `plugin_surface.py`'s `Skill()`/command edges into the codemem index so `who_calls` answers for skills and commands (graduates review gap 4 / former fog bullet).
- **Gap 7:** codemem gains an honestly named `callees` tool; `blast_radius` stays one minor release as a deprecated alias with a notice in its output; the `aa_ma_context` key bug is fixed in the same change.
- **Left to T7:** whether any of these signals blocks (gate, commit, CI). The plan owns the ADR for the hook (changes `claude-code/hooks/**` → `Critical-Path: hook-modification`).
Evidence: [docs/research/code-conventions-impact-impact-status.md](../../../../docs/research/code-conventions-impact-impact-status.md). Decided with Ste 2026-10-08 (grilling, 3 rounds).

### Ticket 7: Is the impact check HARD-enforced in the gate or downgraded to SOFT?
- Type: grilling
- Mode: HITL
- Status: RESOLVED
- Blocked-by: 6
#### Question
engineering-standards §5 claims HARD; the gate does not enforce it (review gap 2). Enforce via a milestone-scoped provenance token like `CRITICAL_PATH_REVIEW` (Critical-Path: hook-modification, needs an ADR), or downgrade the doctrine to SOFT?
#### Answer
**HARD, computed by the gate** — the `DIAGRAM_VERIFIED` pattern (`execute-aa-ma-milestone.md:661-727`: the fence run is the check, the provenance line its record), not the `CRITICAL_PATH_REVIEW` pattern (`:611-630`: the gate only greps for a line the agent wrote — self-attestation). Rejected: self-attested token (theatre); downgrade to SOFT (keeps the doctrine honest but leaves R1 unenforced).
- **What blocks milestone COMPLETE:** each of (a) changed file not in Expected-Blast-Radius, (b) predicted file not changed, (c) co-change partner missing from the diff, unless the milestone's tasks.md block carries `Impact-Explained: <path> — <reason>` (read via `aa_ma.enforce`). Co-change threshold: a pair counts only with ≥5 shared commits AND the partner changed in ≥50% of the file's commits (configurable). On pass the gate writes `[ts] IMPACT_VERIFIED — <milestone heading> — changed=N predicted=P cochange=C unexplained=0`.
- **API diff** (`griffe` / API Extractor): an undeclared breaking change blocks; a break declared in the milestone's Contract block passes; ad-hoc commits get an advisory only.
- **Derived path tags:** path-glob-derived Critical-Path values join the declared ones, so the existing HARD `CRITICAL_PATH_REVIEW` evidence applies to them; the gate names the files that triggered each derived value.
- **Never blocks:** the pre-edit hook (T6) and the ad-hoc co_changes-at-commit check.
- **Grandfathering:** only plans `Created:` on or after the release that ships this (v0.5.0 / v0.12.0 precedent).
- **Plan owns:** the ADR, the engineering-standards §5 row rewrite, and `gate.py` changes — all `Critical-Path: hook-modification` (ADR-0009 scope).
Decided with Ste 2026-10-08 (grilling, 3 rounds).

### Ticket 8: What is the comments and docstrings standard per language?
- Type: grilling
- Mode: HITL
- Status: RESOLVED
- Blocked-by: 1, 2, 3
#### Question
Docstring style per language (Google vs numpydoc for Python; Bash header-comment format; TSDoc; roxygen2), which symbols require one (public API only?), why-not-what comment rule, `# why:` on suppressions, TODO format, constant rationale — which survive as written, which change, and which are lint-enforced.
#### Answer
1. **Core rule (all languages):** every exported/public symbol gets a doc block in its language's native format — Python Google style (`Args:`/`Returns:`/`Raises:`), Bash function header (Globals/Arguments/Outputs/Returns), TSDoc (.ts) / JSDoc (.js), roxygen2 `#'`, SQL in the catalogue (`COMMENT ON` / dbt `description` + `persist_docs`; never sensitive data — readable by any connected user in Postgres 18). No single cross-language syntax (T3 conflict: Google `Args:` vs `@param`).
2. **Python enforcement:** full Ruff `D` with `convention = "google"` (incl. D417 undocumented-param) on touched files — pre-commit on staged files, CI on the diff (touched-code-only Note). D107 ignored permanently with a `# why:` (class docstring documents `__init__` args). The parked D101–D104 list and its ownerless `TODO(logging-std)` are deleted, not burned down.
3. **Suppressions (Ste's scoping, verbatim intent):** `# why:` is required for deliberate lint/type-check suppressions, ignored command failures (`|| true`) and discarded stderr (`2>/dev/null`) in maintained source code. Specific diagnostic codes where the tool supports them (no blanket `noqa` / `type: ignore`). **Remove an unnecessary suppression before documenting it** — that is Ruff RUF100's role (plus PGH003/PGH004 for blanket forms). Enforced on added or modified lines; existing sites migrate when touched. The check must not match suppression-like text in documentation, strings or examples; a grep is a starting proposal, not a complete code-aware validator. Review judges whether a suppression is justified, not merely whether the comment exists.
4. **TODO format:** `TODO(#N): …` or `TODO(ADR-NNNN): …` in every language; Ruff TD003 ignored (it rejects the ADR form — T2 measured), TD002 kept; a grep check requires the reference to match `#\d+|ADR-\d{4}`.
5. **Judgement rules:** code documentation (docstrings, why-comments, constant rationale, `ponytail:` ceiling notes) is required documentation, exempt from ponytail's "no unrequested prose" rule, but proportionate (summary + sections, no tutorials) — this reconciliation is written into the doctrine. Magic constants (name + unit + reason) stay review-only; PLR2004 off. The §6.8 `code-reviewer` keeps its ban on style nits (`code-reviewer.md:91`) but WARNs (never CRITICAL) on substance: what-comments that restate code, missing why on non-obvious logic, docstrings claiming behaviour the code lacks, unjustified suppressions, and unnamed constants at any occurrence count (today 3+). Bash headers: Google rule (any function not both obvious and short) plus every function in a sourced library.
Evidence: [best-practice](../../../../docs/research/code-conventions-impact-best-practice.md) §1–2, [inventory](../../../../docs/research/code-conventions-impact-inventory.md) §2–3, [language cards](../../../../docs/research/code-conventions-impact-language-cards.md). Decided with Ste 2026-10-08 (grilling, 3 rounds; Q3 scope written by Ste).

### Ticket 9: Is `logging-and-comments` adopted into the forge as the logging standard, and what changes?
- Type: grilling
- Mode: HITL
- Status: RESOLVED
- Blocked-by: 1, 2
#### Question
Adopt the global `logging-and-comments` skill (library vs app logging, stderr/stdout split, no silent failures, run-level context, hook `systemMessage` rule from L-1319) into the forge as is, revise it, or split logging from comments? Structured (JSON) logging: required, optional, or out?
#### Answer
- **Adoption:** `logging-and-comments` moves into `claude-code/skills/` as **one** revised skill (T8 + T9 changes applied, plus a test), symlinked back by `install.sh`. Kept as one because both halves fire on the same triggers (try/except, `|| true`, writing a CLI or hook). The five non-negotiables stay. Rejected: split into two skills; declared-external.
- **Python:** `NullHandler` becomes optional, used only for deliberate silence with a `# why:` (T2: the mandatory form hides library warnings, against the Python logging HOWTO's default and our own no-silent-failure rule). JSON logs are required for long-running services and opt-in for CLIs and pipelines (`--log-format json` / `LOG_FORMAT=json`); hooks stay plain text.
- **Edit-time ruff hook:** `~/.claude/hooks/ruff-format.sh` (global-only today) moves into the forge. On PostToolUse it returns `ruff check` findings for the edited file as `additionalContext` (capped at ~10 lines; never blocks; its own failures log one line), fixing the claim/mechanism mismatch (`ruff-format.sh:14` discards output; skill `:105` says findings are reported).
- **Debug settings:** Python CLIs/apps use `-v`/`-q` + `LOG_LEVEL`. Hooks use one `HOOK_DEBUG=1` (already read by `lib/aa-ma-parse.sh:68`). `AA_MA_PLAN_MARKER_DEBUG` stays one release as a deprecated alias that prints a notice. `VERBOSE` and `DEBUG` are removed from the skills. The CLAUDE.md bypass table is updated.
- **Bash format and path:** line `<date -Is> LEVEL <hook-name>: msg`; one persistent log `~/.claude/logs/hooks.log` (`compaction.log` folds in); `bash-defensive-patterns`' bracketed example is rewritten to match.
- **Shared helper:** `aa_ma_debug` grows into `claude-code/hooks/lib/log.sh`: `log_info`/`log_warn`/`log_error`/`log_debug` plus `fail_open_notice` (systemMessage JSON + hook-log line, per L-1319). Hooks adopt it as they are touched; a bats test pins the format and the stderr/stdout split.
- **Strict mode:** `set -euo pipefail` (`-E` only where an ERR trap exists), `shopt -s inherit_errexit`, never `local x=$(cmd)`, plus a BashFAQ/105 caveats block in the skills. ShellCheck optional checks `check-extra-masked-returns,check-set-e-suppressed` run on touched files.
- **Other languages:** the TS/JS and R cards apply the stderr rule, so pino is configured to write to fd 2.
- **Handed on:** secrets in logs → Ticket 10.
Evidence: [inventory](../../../../docs/research/code-conventions-impact-inventory.md) §4, [best-practice](../../../../docs/research/code-conventions-impact-best-practice.md) §1–3. Decided with Ste 2026-10-08 (grilling, 3 rounds).

### Ticket 10: What is the SecOps baseline, and where does each check run?
- Type: grilling
- Mode: HITL
- Status: RESOLVED
- Blocked-by: 1, 2
#### Question
Which security checks are mandatory for touched code (secret scanning, SAST, dependency audit, shell lint, input validation at trust boundaries, LLM-output safety), and at which layer each runs — authoring skill, PreToolUse hook, pre-commit, CI, milestone gate? What happens to `secrets-management` and `senior-secops`? Includes secrets in logs (handed on from Ticket 9: enforced today only by the §6.8 `security-auditor`).
#### Answer
1. **Baseline: 4 layers, fail-loud** (no `|| true` anywhere in a security check):
   - **Edit:** security-guidance plugin warnings + Ruff `S` findings through the T9 ruff hook (advisory).
   - **Commit:** gitleaks on staged changes + the forge regex hook (`security-static-check.sh`), narrowed to what Ruff cannot catch (path traversal, secret literals); classes Ruff `S` covers (shell=True, eval/exec, pickle, SQL string-building) retire once Ruff `S` gates in pre-commit/CI.
   - **CI (must fail on findings):** Ruff `S`; gitleaks over history; `uv sync --locked`; `uv audit --locked` (pip-audit if `uv audit` is still preview); ShellCheck + optional checks; Dependabot (github-actions, uv, npm); one osv-scanner job for JS lockfiles and `renv.lock`; npm release-age delay; eslint-plugin-security advisory only.
   - **Gate/review:** §6.8 `security-auditor` + T7's derived Critical-Path tags.
2. **Bandit → Ruff S (Ste's conditions):** run a coverage comparison at our pinned Ruff and Bandit versions first; remove Bandit only after confirming no required Bandit-specific checks or custom plugins are lost. Ruff `S` is then the blocking security check in CI and `/sole-dev-merge` Stage C; `BANDIT_BIN` is retired. Rule selection, exclusions and justified suppressions are defined centrally. Touched files are scanned for change validation and a full-repository scan is retained (on push to main + weekly). A known security violation (canary) must be shown to fail the gate. **Fallback** if the comparison finds needed gaps: Bandit stays as a gate restricted to those test IDs (`bandit -t B<ids> -ll`, pinned in `uv.lock`), re-checked on each Ruff upgrade.
3. **Skills:** `senior-secops` is rewritten as a thin router to the real tools (Ruff `S`, gitleaks, `uv audit`, ShellCheck, osv-scanner) citing ASVS 5.0 / OWASP Top 10:2025 / NIST SSDF (no SSDF 1.2 practice IDs until final); its stub scanner is deleted (carried defect 2). `secrets-management` moves into the forge: gitleaks primary, TruffleHog `--fail` + digest pin as alternative. **Secrets in logs:** a shared Python `logging.Filter` that masks known secret patterns/keys and a masking step in T9's `lib/log.sh`; services and pipelines must install it; the `security-auditor` still judges. No grep heuristic.
4. **Validation:** parse/validate once at each trust boundary into a typed value (pydantic / dataclass / enum); deeper layers rely on the type and add only cheap invariant asserts where a bug is dangerous (paths, SQL, shell). `defense-in-depth` is rewritten to say this, with Python/Bash examples (resolves the "every layer" vs ponytail "trust boundaries" contradiction, T1 §5). **LLM/agent output is untrusted input** at shell, SQL, file-path and HTML boundaries, via `llm-output-safety` (adopt or declare-external under T12).
5. **Rollout:** the forge doctrine states the baseline; the project template from T13/T14 carries ready CI, pre-commit, gitleaks and Dependabot config; existing repos adopt when touched.
Out of baseline: CodeQL and per-release SBOM (Maximal option declined); SLSA provenance deferred until a built artefact ships (T2).
Evidence: [best-practice](../../../../docs/research/code-conventions-impact-best-practice.md) §4, [inventory](../../../../docs/research/code-conventions-impact-inventory.md) §5, [language cards](../../../../docs/research/code-conventions-impact-language-cards.md). Decided with Ste 2026-10-08 (grilling, 4 rounds; Bandit conditions written by Ste).

### Ticket 11: How are the design principles stated so they are checkable, and how is the YAGNI-vs-SOLID tension resolved?
- Type: grilling
- Mode: HITL
- Status: RESOLVED
- Blocked-by: 1, 2
#### Question
engineering-standards §2 lists KISS/DRY/SOLID/SoC as slogans. Rewrite as concrete, reviewable heuristics (e.g. rule of three before extracting; no interface with one implementation; the ponytail ladder), and decide which wins when "depend on abstractions" (SOLID) meets "no unrequested abstractions" (ponytail/YAGNI).
#### Answer
1. **Conflict-resolution policy (Ste's wording):** default to the simplest concrete implementation that meets current requirements. Introduce abstractions when they solve an evidenced problem: a real alternate implementation, an actively used test seam, a necessary dependency boundary, an ongoing migration, or repeated shared knowledge. A single production implementation does not automatically disqualify an abstraction. Preserve separation of concerns without requiring a separate file for every responsibility; minimise unnecessary indirection and fragmentation, not file count at the expense of clarity. Treat the rule of three as a heuristic, not a mandatory threshold. YAGNI must not be used to reject necessary tests, refactoring or maintainability work. Import checks (import-linter) enforce configured boundaries; review still assesses cohesion and design. Review questions: *What current problem does this structure solve? What simpler alternative exists? What would break if we removed it? What would introducing it later cost?*
2. **DRY:** knowledge-DRY (Thomas) — one authoritative source per fact (schema, grammar, constant, count); a duplicated fact is a defect at once. Code duplication is tolerated until about the third occurrence (heuristic, per 1); prefer duplication to a parameter-and-conditional abstraction (Metz). Cross-repo extraction thresholds → T14 (supersedes `deslop-shared-libs`' "2 verified sources" for in-repo code).
3. **KISS made checkable:** Ruff `C901` (max-complexity 10) and `PLR0913` (max-args 6) on touched files; exceeding requires `# noqa: <code>  # why: …` (T8 rule), which *is* the justification. The unchecked "justification recorded in context-log" clause is dropped.
4. **Form (Ste's wording):** rewrite engineering-standards §2 as a concise table retaining KISS, DRY, YAGNI, SoC and SOLID as findable labels. For each principle state the concrete heuristic and distinguish automated checks from reviewer rules and contextual judgement. Name only checks that are actually configured, and state their scope. Include the conflict-resolution policy (start concrete, earn abstractions through evidence, preserve necessary boundaries, never treat required tests or refactoring as YAGNI violations). CUPID may inform the review questions, but terminology does not change in this effort.
5. **Testing (folded in, Ste 2026-10-08):** TDD — a failing test first for every behaviour change. Depth is risk-proportionate: branches, parsers, security and data paths cover happy + edge + the regression; trivial glue may rely on a higher-level test. Ponytail's "one runnable check" is the floor for throwaway/prototype code only. No fixtures or frameworks beyond pytest/bats unless they earn their place. **Waivers:** `plan_parsers.CANONICAL_TDD_WAIVERS` is canonical and the rule text is regenerated from it; `refactor` requires existing tests to stay green; `hotfix-emergency` requires a follow-up test task; "infrastructure-only" maps to `tooling-config`. **Tests gate:** the milestone gate runs the project's test command (from the plan/reference; default `uv run pytest`) and writes `TESTS_VERIFIED — <milestone> — passed=N` (DIAGRAM_VERIFIED pattern, as T7) — replaces the bare comment at `execute-aa-ma-milestone.md:604`. Unbacked `pyproject.toml` claims (perf CI job `:121`, ≥90% coverage gate `:49`) are implemented or deleted, decided in the plan.
Evidence: [best-practice](../../../../docs/research/code-conventions-impact-best-practice.md) §5, [inventory](../../../../docs/research/code-conventions-impact-inventory.md) §6–7. Decided with Ste 2026-10-08 (grilling, 3 rounds; policy and form written by Ste).

### Ticket 12: How is the coding doctrine packaged — one rule, per-topic skills, language cards — within an auto-load token budget?
- Type: grilling
- Mode: HITL
- Status: OPEN
- Blocked-by: 1, 8, 9, 10, 11, 15
#### Question
What is auto-loaded (rules) vs on-demand (skills, cards), how large the auto-loaded part may be, how global-only skills migrate into the forge (move, symlink, declared-external) and get tests, and how the language cards from Ticket 3 are reached.

### Ticket 13: Where does the reusable-code collection live?
- Type: grilling
- Mode: HITL
- Status: RESOLVED
- Blocked-by: 5
#### Question
Forge (a `uv` workspace member or skill references), a dedicated private repo in the carmen-provenance-labs org, or split (generic in one place, biomedical/client-derived in a private one)? Given that genericized client code is in scope, what is the confidentiality gate before code enters? Also: where the **project template** lives that carries the T10 SecOps baseline (CI, pre-commit, gitleaks, Dependabot) to Carmen and client repos.
#### Answer
Facts checked 2026-10-08: `snewhouse/aa-ma-forge` is **PUBLIC** (`gh repo view`); both carmen-provenance-labs repos are private; `codemem-mcp` is only a dev dependency of `aa_ma` (`pyproject.toml:56`).
- **Library tier:** a **private** repo in carmen-provenance-labs (working name `carmen-kit`; final name chosen in the plan), packaged with uv and consumed by git source pinned to a tag (`{ git = …, tag = … }`); a private index only if consumers outgrow tags. Holds generic, biomedical and genericized-client helpers. The public forge never depends on it. Rejected: public/private split; a forge workspace member (public repo cannot hold client-derived code).
- **Snippet tier:** PEP 723 single-file scripts, each with a test, in the kit's `snippets/`. A **forge router skill** reads the index at runtime from a local checkout (`CARMEN_KIT_PATH`), ships no entry names, paths or descriptions in the public forge, and prints a one-line notice when the checkout is missing (no silent fail). The ~3k untested prose fences in skills migrate only when touched.
- **Project template:** a **public** copier template repo in the Carmen org (config only: CI, pre-commit, lint, gitleaks, Dependabot from T8/T9/T10; `.copier-answers.yml` tracked; `copier update` path), with the denylist grep and gitleaks in its own CI.
- **Shared generic helpers** the forge itself uses (logging setup, T10 redaction filter, `lib/log.sh`): canonical in the public forge; the kit vendors them with a FORKS.json-style provenance pin and drift check reusing `src/aa_ma/forks.py` (knowledge-DRY, no private dependency in the forge).
- **In-repo git-HEAD helper:** one hardened copy per package (`src/aa_ma` and `packages/codemem-mcp`; timeout + env scrubbing) sharing one contract test — no new package for one function (T11 evidence rule).
- **Confidentiality gate:** every entry carries a provenance header (`origin: generic | biomedical | client-derived`, source, date); CI fails an entry without one. Client-derived entries additionally pass a genericization checklist, a client-term denylist grep (denylist kept outside every repo, e.g. `~/.config/carmen/denylist`), gitleaks, and Ste's explicit `approved-by: Ste YYYY-MM-DD`.
- **Plan implication:** the plan creates two new GitHub repos (private kit, public template) — outward-facing actions that need Ste's confirmation at execution time (HITL).
Evidence: [reuse prior art](../../../../docs/research/code-conventions-impact-reuse-prior-art.md) B2–B6. Decided with Ste 2026-10-08 (grilling, 3 rounds).

### Ticket 14: When does shared code graduate from snippet to module to library?
- Type: grilling
- Mode: HITL
- Status: RESOLVED
- Blocked-by: 5, 13
#### Question
Concrete graduation criteria (reuse count, test coverage, API stability, number of consuming projects), the minimum metadata a snippet carries (provenance, licence, tests, owner), versioning for the library tier, and how Claude finds and reuses entries while coding (skill, search, index).
#### Answer
- **Tiers (one kit package, T13):** *snippet* = `snippets/` PEP 723 script (copy or `uv run`); *module* = importable under `kit._experimental` (no SemVer promise, may change any release); *library* = the declared public API (SemVer, griffe-checked).
- **Snippet → module:** evidenced reuse — about the third occurrence or use in 2 different repos (heuristic, per T11) — and every caller wants the same contract (near-fit callers stay snippets; deslop's "reject incompatible contracts"). Each public function gets a pytest.
- **Module → library:** the contract has held for 2 consecutive minor releases with ≥2 consuming repos.
- **Tests per tier:** snippet — one runnable test beside the script; module — unit tests per public function + T8 docstring rules; library — those + `griffe check` against the last tag in CI (blocks undeclared breaks, as T7) + CI across supported Pythons + T10's weekly full scan. Network-dependent validators (e.g. `validate_ot_queries.py` pattern) are marked and run on schedule, never as gates.
- **Versioning:** SemVer via commitizen + conventional commits (the forge's pipeline); 0.y.z until two production repos depend on it, then 1.0.0; deprecations last ≥1 minor release; consumers pin tags.
- **Granularity:** one package — stdlib-only core (logging, retry, config, provenance) with heavy/domain deps behind extras (e.g. `kit[bio]`, `kit[http]`); split a package out only when an extra's dependencies conflict.
- **Metadata (every entry):** T13 provenance header (origin, source, date, `approved-by` for client-derived) + licence and upstream URL/SHA when derived from third-party code + path of its test. CI parses the header and fails on a missing field. Owner is implicitly Ste (no field).
- **Rot:** the weekly scheduled CI opens an issue on a failing test; fix within 30 days or delete — no skip markers. **Demotion (Metz):** a library helper that accretes option flags for near-fit callers is inlined back into those callers and removed.
- **Reuse-first while coding:** before writing a new generic helper (logging setup, retry, config, ID mapping, API client) Claude consults the router skill, then reuses or vendors an entry, or records "none fits" in one line. A helper written twice is flagged as a snippet candidate by the §6.8 code-reviewer (WARN).
Evidence: [reuse prior art](../../../../docs/research/code-conventions-impact-reuse-prior-art.md) B1–B6 and "Candidate graduation criteria". Decided with Ste 2026-10-08 (grilling, 3 rounds).

### Ticket 15: What conventions govern Markdown skills and commands as prompt-as-code?
- Type: grilling
- Mode: HITL
- Status: RESOLVED
- Blocked-by: 2
#### Question
T2 found 6 skill/command files over the 500-line guideline (aa-ma-execution 1295, execute-aa-ma-milestone 1244, aa-ma-plan 1154, sole-dev-merge 1054, execute-aa-ma-full 757, plan-verification 608), unknown frontmatter keys silently ignored (`triggers`), `context:` misused, and no behavioural evals. Decide: size cap and split rule, frontmatter schema validation (test), whether skills need evals and of what shape, and how this relates to the `write-a-skill` → `writing-for-agents` adoption already decided in the writing-for-agents-eval map. Touched-files-only applies.
#### Answer
Facts checked 2026-10-08: the writing-for-agents-eval map is cleared (4/4 RESOLVED, no fog) but was never planned — `claude-code/skills/write-a-skill/` still ships. `claude plugin eval` exists in Claude Code 2.1.294 (`evals/**/case.yaml` + graders, no-plugin baseline arm; skills-dir targets resolve). The forge has no `plugin.json`. Command/skill name collisions: `assess-codebase`, `understand-codebase`.
1. **Fold in writing-for-agents-eval:** this plan executes that map's 4 decisions as one milestone — fork `writing-for-agents` @ c55ee46 verbatim + FORKS.json row + ADR, retire `write-a-skill` (ADR-0004 superseded), keep it out of the AA-MA Phase 5 writers. T15's conventions live in the fork's `## In this repo` block. That map is cited as an input; the guard imports only this map.
2. **Size:** SKILL.md/command bodies ≤500 lines; overflow moves to `references/` one level deep, with a TOC on any reference over 100 lines. The six current offenders (aa-ma-execution 1295, execute-aa-ma-milestone 1244, aa-ma-plan 1154, sole-dev-merge 1054, execute-aa-ma-full 757, plan-verification 608) are allowlisted at their current size as a ceiling; a test blocks growth; each is split when next touched.
3. **Frontmatter:** `test_frontmatter_at_top.py` extended to every skill and command — only documented keys plus `metadata:`; name ≤64 chars + charset; description ≤1,024, no XML, third person; description + `when_to_use` ≤1,536; unknown keys fail. Fixes applied now: `triggers` → `when_to_use`, `version` → `metadata`, misused `context:` dropped (`dispatching-parallel-agents:7`), the one imperative description rewritten.
4. **Evals:** ≥3 `claude plugin eval` cases per gate-bearing or high-traffic skill (execute-aa-ma-*, aa-ma-plan, plan-verification, impact-analysis, logging-and-comments); new skills write their 3 cases first (eval-first). Run on a schedule and before release; never a CI gate (cost, nondeterminism). The plan first proves `plugin eval` can target the forge's skills directory, falling back to a `claude -p` harness (L-1322 prompt-first, L-1315 isolated live-load).
5. **Commands → skills, all now (Ste):** all 14 `claude-code/commands/*.md` become skill directories, every `/name` unchanged (`disable-model-invocation: true` where user-only). `assess-codebase` and `understand-codebase` merge into their existing skills (the wrapper's unique text moves in, then the wrapper is deleted). A test asserts no name exists as both command and skill. `install.sh`/`uninstall.sh` remove stale command symlinks; hardcoded counts (README, CHANGELOG, SECURITY, foundations, quick-reference, CLAUDE.md) update. The size allowlist carries over to the converted files.
6. **Rationale:** every MUST/NEVER/ALWAYS rule in skills, commands and rules carries a one-line why or a pointer (L-nnn, ADR, doc URL); §6.8 code-reviewer WARNs on touched markdown; no regex gate.
7. **Hooks:** each hook header declares event, blocking vs advisory, exit-code meaning (0 / 2; never 1 for a policy), and fail-open behaviour (systemMessage + `lib/log.sh` line). Each hook has a bats test fed a real captured payload (L-1319). Real security gates live in CI/permissions (T10); `security-static-check.sh` is relabelled advisory.
Evidence: [best-practice](../../../../docs/research/code-conventions-impact-best-practice.md) §3; [writing-for-agents-eval map](../writing-for-agents-eval/writing-for-agents-eval-map.md). Decided with Ste 2026-10-08 (grilling, 3 rounds).

## Not yet specified

- Migration mechanics for global-only skills into the forge (tests, FORKS.json rows, install.sh changes) — sharpens once Ticket 12 decides packaging.

## Out of scope

- Backfilling existing code to the new conventions — touched-code-only rule (decided 2026-10-08); a lint baseline freezes current debt.
- Languages beyond Python, Bash, Markdown skills, TS/JS, R and SQL.
