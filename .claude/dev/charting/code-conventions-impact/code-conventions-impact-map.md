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
- Biorelate `galactic-*` material is pattern reference only (`~/.claude/_archive/biorelate/`); never contact Biorelate remotes (L-1289).

## Decisions so far

<!-- one line per RESOLVED ticket, newest last -->

## Tickets

### Ticket 1: Where is every coding convention stated today, and where is each one enforced?
- Type: research
- Mode: AFK
- Status: CLAIMED
- Claimed-at: 2026-10-08T10:49
- Blocked-by: —
#### Question
Inventory every source that states a coding convention for Claude or for code in Ste's projects: `claude-code/rules/*.md`, `~/.claude/CLAUDE.md`, `~/.claude/rules/*.md`, forge skills (`operational-constraints`, `defense-in-depth`, `system-mapping`, `impact-analysis`) and global-only skills (`logging-and-comments` + `references/ruff-baseline.toml`, `python-quality-gates`, `bash-defensive-patterns`, `secrets-management`, `senior-secops`, `deslop-shared-libs`, `ponytail`), plus the mechanical layer (`pyproject.toml` ruff config, `.github/workflows/*`, `claude-code/hooks/security-static-check.sh`, pre-commit if any). For each topic — comments, docstrings, logging, security/SecOps, KISS/DRY/SOLID/SoC, testing — record: where it is stated (file:line), whether it is auto-loaded or on-demand, whether anything enforces it (lint rule / CI job / hook / gate / nothing), and every duplication or contradiction between sources. Count auto-loaded tokens for the rule files. Output: `docs/research/code-conventions-impact-inventory.md`.

### Ticket 2: How do our Python, Bash and Markdown-skill conventions compare with current best practice?
- Type: research
- Mode: AFK
- Status: CLAIMED
- Claimed-at: 2026-10-08T10:49
- Blocked-by: —
#### Question
Against primary sources, state current best practice and gap-check what we ship, per topic. Python: PEP 8/257, Google Python Style Guide, numpydoc, the logging HOWTO and "logging in libraries" guidance, Ruff rule families (D, S, BLE, G, T20, LOG, TRY), Bandit, pip-audit/uv audit. Bash: Google Shell Style Guide, ShellCheck, `set -euo pipefail` caveats. Markdown skills/commands: Anthropic's skill-authoring guidance and Claude Code docs on skills/commands/hooks (prompt-as-code: frontmatter, progressive disclosure, testability). SecOps: OWASP ASVS / Top 10, NIST SSDF (SP 800-218), OpenSSF Scorecard, secret scanning (gitleaks), dependency pinning and supply chain. Design principles: KISS/DRY/SOLID/SoC, rule of three, YAGNI — including published critiques (e.g. DRY's wrong-abstraction cost). Use the Ticket 1 sources list if resolved; otherwise read the skills directly. Output: `docs/research/code-conventions-impact-best-practice.md` with a strengths / weaknesses / trade-offs table per topic.

### Ticket 3: What should the short TS/JS, R and SQL convention cards contain?
- Type: research
- Mode: AFK
- Status: CLAIMED
- Claimed-at: 2026-10-08T10:49
- Blocked-by: —
#### Question
For each of TS/JS, R and SQL, find the de-facto standard tooling and idiom from primary sources: formatter, linter and its security rules, doc-comment format (TSDoc/JSDoc, roxygen2, SQL comment conventions), logging idiom, test runner, dependency audit. Candidates to verify, not assume: TypeScript + typescript-eslint + Prettier/Biome, TSDoc, pino; tidyverse style guide + lintr + styler + roxygen2 + logger; sqlfluff + dialect choice. Keep each card to what a one-page reference can carry. Output: `docs/research/code-conventions-impact-language-cards.md`.

### Ticket 4: What is the state of impact analysis now, and which code-writing skills invoke it?
- Type: research
- Mode: AFK
- Status: CLAIMED
- Claimed-at: 2026-10-08T10:49
- Blocked-by: —
#### Question
Update `docs/research/impact-analysis-lifecycle-review.md` to today without rewriting it: for each gap 1–7 and recommendation R1–R6, is it fixed, partly fixed or open as of HEAD (git log since c0ec3f2; M13 commit 33465fe made codemem the default in impact-analysis/system-mapping — did that fix gap 3 and gap 7?). Then list every skill or command that writes or edits code (forge and global: `test-driven-development`, `superpowers:*`, `subagent-driven-development`, `executing-plans`, `please_proceed`, `execute-aa-ma-step/milestone/full`, `systematic-debugging`, `prototype`, …) and say whether each invokes impact analysis, at which point (pre-edit, post-edit, review) and how. Finally, summarise how established practice handles change-impact analysis at author time (static call graphs, co-change mining, test impact analysis / test selection, API/contract diffing, security-sensitive-path tagging) with primary sources. Output: `docs/research/code-conventions-impact-impact-status.md`.

### Ticket 5: What reusable code exists today, and how do others curate and graduate it?
- Type: research
- Mode: AFK
- Status: CLAIMED
- Claimed-at: 2026-10-08T10:49
- Blocked-by: —
#### Question
Find what already exists: global skills that hold code (`pharma-use-case-library`, `terraform-module-library`, `deslop-shared-libs`, others), any snippet/utility directories under `~/.claude`, `~/dev/carmen-provenance-labs/*` and this repo (e.g. helpers duplicated across `src/` and `packages/`), and duplicated functions across Carmen projects (name and file, never client data). Then prior art for curation and graduation: rule of three, internal packages via uv workspaces or a private index, copier/cookiecutter templates, git subtree vs package, GitHub gists, "inner source" practice, semantic versioning for internal libs, and what keeps a snippet collection from rotting (tests, provenance, ownership). Output: `docs/research/code-conventions-impact-reuse-prior-art.md`.

### Ticket 6: Should impact analysis be an explicit step inside the coding skills, and at which points?
- Type: grilling
- Mode: HITL
- Status: OPEN
- Blocked-by: 4
#### Question
Given Ticket 4: does impact analysis become a named step in every code-writing skill (pre-edit caller check, post-edit predicted-vs-actual diff, review input), or stay centralised in the AA-MA execution commands? Which of R1–R6 are adopted, and how does it cover dependencies, interfaces/contracts, tests (test impact), security-sensitive paths and downstream behaviour, including the markdown `Skill()` graph?

### Ticket 7: Is the impact check HARD-enforced in the gate or downgraded to SOFT?
- Type: grilling
- Mode: HITL
- Status: OPEN
- Blocked-by: 6
#### Question
engineering-standards §5 claims HARD; the gate does not enforce it (review gap 2). Enforce via a milestone-scoped provenance token like `CRITICAL_PATH_REVIEW` (Critical-Path: hook-modification, needs an ADR), or downgrade the doctrine to SOFT?

### Ticket 8: What is the comments and docstrings standard per language?
- Type: grilling
- Mode: HITL
- Status: OPEN
- Blocked-by: 1, 2, 3
#### Question
Docstring style per language (Google vs numpydoc for Python; Bash header-comment format; TSDoc; roxygen2), which symbols require one (public API only?), why-not-what comment rule, `# why:` on suppressions, TODO format, constant rationale — which survive as written, which change, and which are lint-enforced.

### Ticket 9: Is `logging-and-comments` adopted into the forge as the logging standard, and what changes?
- Type: grilling
- Mode: HITL
- Status: OPEN
- Blocked-by: 1, 2
#### Question
Adopt the global `logging-and-comments` skill (library vs app logging, stderr/stdout split, no silent failures, run-level context, hook `systemMessage` rule from L-1319) into the forge as is, revise it, or split logging from comments? Structured (JSON) logging: required, optional, or out?

### Ticket 10: What is the SecOps baseline, and where does each check run?
- Type: grilling
- Mode: HITL
- Status: OPEN
- Blocked-by: 1, 2
#### Question
Which security checks are mandatory for touched code (secret scanning, SAST, dependency audit, shell lint, input validation at trust boundaries, LLM-output safety), and at which layer each runs — authoring skill, PreToolUse hook, pre-commit, CI, milestone gate? What happens to `secrets-management` and `senior-secops`?

### Ticket 11: How are the design principles stated so they are checkable, and how is the YAGNI-vs-SOLID tension resolved?
- Type: grilling
- Mode: HITL
- Status: OPEN
- Blocked-by: 1, 2
#### Question
engineering-standards §2 lists KISS/DRY/SOLID/SoC as slogans. Rewrite as concrete, reviewable heuristics (e.g. rule of three before extracting; no interface with one implementation; the ponytail ladder), and decide which wins when "depend on abstractions" (SOLID) meets "no unrequested abstractions" (ponytail/YAGNI).

### Ticket 12: How is the coding doctrine packaged — one rule, per-topic skills, language cards — within an auto-load token budget?
- Type: grilling
- Mode: HITL
- Status: OPEN
- Blocked-by: 1, 8, 9, 10, 11
#### Question
What is auto-loaded (rules) vs on-demand (skills, cards), how large the auto-loaded part may be, how global-only skills migrate into the forge (move, symlink, declared-external) and get tests, and how the language cards from Ticket 3 are reached.

### Ticket 13: Where does the reusable-code collection live?
- Type: grilling
- Mode: HITL
- Status: OPEN
- Blocked-by: 5
#### Question
Forge (a `uv` workspace member or skill references), a dedicated private repo in the carmen-provenance-labs org, or split (generic in one place, biomedical/client-derived in a private one)? Given that genericized client code is in scope, what is the confidentiality gate before code enters?

### Ticket 14: When does shared code graduate from snippet to module to library?
- Type: grilling
- Mode: HITL
- Status: OPEN
- Blocked-by: 5, 13
#### Question
Concrete graduation criteria (reuse count, test coverage, API stability, number of consuming projects), the minimum metadata a snippet carries (provenance, licence, tests, owner), versioning for the library tier, and how Claude finds and reuses entries while coding (skill, search, index).

## Not yet specified

- Migration mechanics for global-only skills into the forge (tests, FORKS.json rows, install.sh changes) — sharpens once Ticket 12 decides packaging.
- Impact analysis over the markdown/`Skill()` dependency graph (review gap 4) — likely a sub-question of Ticket 6 once Ticket 4 says what the plugin-surface extractor already gives.
- Prompt-as-code conventions for Markdown skills vs the existing skill-authoring guidance (`write-a-skill` / `writing-for-agents` outcome) — revisit after Ticket 2.

## Out of scope

- Backfilling existing code to the new conventions — touched-code-only rule (decided 2026-10-08); a lint baseline freezes current debt.
- Languages beyond Python, Bash, Markdown skills, TS/JS, R and SQL.
