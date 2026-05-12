<!-- Maintained in aa-ma-forge as of v0.9.0 — see docs/adr/0006-understand-codebase-adoption.md -->
---
name: understand-codebase
description: >-
  Onboard to a new, inherited, or shared codebase. Read it, understand it, map it, and learn
  its conventions, versioning, tests, tech stack, rules (AGENTS.md / CLAUDE.md / .cursorrules /
  etc.), build/run/CI, integrations, security posture, and repo health — then produce an honest
  pros/cons verdict, a "contribute safely" playbook, and an "add a feature" playbook, written to
  ONBOARDING.md at the repo root plus a .claude/onboarding/ set of deep-dives — and optionally
  author an AGENTS.md if one is missing, or review and propose improvements to an existing one.
  Tiered (Quick / Standard / Deep). Reuses /index, gsd-map-codebase, /codebase-deep-dive,
  system-mapping, code-intelligence, impact-analysis rather than re-implementing them; Deep tier
  runs a TeamCreate agent-team. Keywords: new codebase, shared codebase, inherited code, onboard,
  understand this repo, how do I contribute, how do I add a feature, ramp up, get oriented,
  ONBOARDING.md, AGENTS.md, codebase walkthrough, joining a project.
allowed-tools:
  - Read
  - Bash
  - Glob
  - Grep
  - Write
  - Edit
  - Agent
  - AskUserQuestion
  - WebSearch
  - WebFetch
  - TeamCreate
  - SendMessage
  - TaskCreate
  - TaskList
  - TaskUpdate
---

# Understand a Codebase (onboarding)

> **Core principle:** code and git history are the single source of truth. Every claim in the
> output must be backed by a file path, a command, a git fact, or "not found — gap". Never
> assert a convention you have not seen in the actual code.

## What this produces

A **human-readable `ONBOARDING.md` at the repo root** (which the `ShareOnboardingGuide` tool can
publish), backed by **`.claude/onboarding/`** — a directory of per-dimension deep-dives. The
exact sections and files are the *output contract* in `references/ONBOARDING-TEMPLATE.md` and
`references/DEEPDIVE-TEMPLATES.md`. Always stamp every file with **date · `git rev-parse --short HEAD` · tier · tools used** (the Provenance block).

**Optionally (Standard/Deep, with consent):** an **`AGENTS.md`** if the repo has none — a concise,
agent-facing distillation of the analysis (build/test commands, conventions, dragons, secret
handling) that points to `ONBOARDING.md` for depth. If an `AGENTS.md` already exists it is
**never overwritten** — instead the skill writes `AGENTS.review.md` (an accuracy review + gaps +
a proposed rewrite the owner applies). See `references/AGENTS-MD-TEMPLATE.md` — read it before
touching anything `AGENTS.md`-related; its **SAFETY PROTOCOL** is binding.

## When to use / when NOT to use

**Use this skill when:**
- Joining a new, inherited, acquired, or shared codebase and you need to get oriented.
- Someone asks "explain this repo", "how do I contribute here", "how do I add a feature to X",
  "what are the conventions", "is this codebase any good", "write me an onboarding doc".
- Before a first contribution to a repo you don't own.

**Do NOT use this skill — use the named alternative instead:**
- About to edit code you already understand → `Skill(impact-analysis)` / `Skill(system-mapping)`.
- Pure quality/security audit with no onboarding deliverable → `/codebase-deep-dive`.
- Implementation planning for a specific change → `/aa-ma-plan` or `/deep-analysis`.
- You only need a structural index for tooling → `/index`.
- Trivial repo (< ~5 source files) → just read it; this skill is overkill.

## Tier selection (ask the user, default = Standard)

Use `AskUserQuestion` (header "Onboarding depth") unless the invocation already specifies
`--quick` / `--standard` / `--deep`. Also confirm: **target path** (default = cwd) and the
reader's **intent** (just understand · planning to contribute · planning to add a feature) —
intent shapes how much weight the playbooks get.

| Tier | ~Time | Agents | Reuses | Output |
|---|---|---|---|---|
| **Quick** | ~5 min | none (or 1 `Agent(subagent_type=Explore)`) | `/index` if no `PROJECT_INDEX.json`; read README, `CLAUDE.md`/`AGENTS.md`, package manifest, CI config, CHANGELOG, LICENSE | one-page `ONBOARDING.md` = the "10-minute orientation" only (≤ ~150 lines), no `.claude/onboarding/` |
| **Standard** *(default)* | ~15–30 min | ~4 parallel `Agent(subagent_type=Explore)` + main-thread synthesis | `code-intelligence` / `PROJECT_INDEX.json`, `system-mapping`, `impact-analysis` heuristics; **absorbs** any prior `.planning/codebase/` or `.claude/reports/codebase-deep-dive-*/` | full `ONBOARDING.md` + `.claude/onboarding/00-index.md` … `09-*.md` + pros/cons verdict + both playbooks |
| **Deep** | ~45 min+ | formal `TeamCreate` agent-team (see below) | **everything**: full `gsd-map-codebase` (`.planning/codebase/`), `/codebase-deep-dive` (`.claude/reports/` + Mermaid), `/index`; **WebSearch + Context7** for version-currency / EOL / CVE / framework best-practice checks | all of Standard + diagrams + version-currency report + reviewer-verified synthesis |

`--deep` is opt-in. If `TeamCreate` is unavailable or the team fails to spawn, **fall back to an
"enhanced Standard"** run (still invoke `gsd-map-codebase`, `/codebase-deep-dive`, web/Context7
via the worker agents directly) and note the downgrade in the Provenance block.

---

## Step 0 — Reuse-and-absorb (ALWAYS, every tier)

Before doing any analysis, detect and **absorb** prior work — do not redo it. Full recipes in
`references/REUSE-MAP.md`. Quick version:

| If present | Do |
|---|---|
| `PROJECT_INDEX.json` (repo root) | Read it first — directory purposes, ASCII tree, symbol importance, call graph. Don't re-derive structure. If missing and tier ≥ Standard, run `/index` (`~/.claude-code-project-index/scripts/project_index.py`) first. |
| `.planning/codebase/*.md` (gsd-map-codebase output) | Read `STACK.md ARCHITECTURE.md STRUCTURE.md INTEGRATIONS.md CONVENTIONS.md TESTING.md CONCERNS.md` and treat as authoritative for those dimensions; only refresh if stale (compare against `git log -1 --format=%cd`). |
| `.planning/intel/*.json` (gsd-intel output) | Use `stack.json files.json apis.json deps.json` as fast lookups. |
| `.claude/reports/codebase-deep-dive-*/` | Reuse `01-architecture-overview.md`, `04-code-quality-assessment.md`, `05-security-analysis.md`, `06-design-patterns.md`, the `diagrams/*.mmd`. Link them from `.claude/onboarding/`. |
| Existing root `README.md`, `CONTRIBUTING.md`, `ARCHITECTURE.md`, `docs/` | Read and quote them; cross-check against the code (note drift as a "con"). |

Record what was absorbed in the Provenance block. **Only run a heavy tool (`gsd-map-codebase`,
`/codebase-deep-dive`) when its output is absent or stale.**

---

## The dimensions (single source of truth: `references/DIMENSIONS.md`)

Every dimension below has, in `DIMENSIONS.md`: *what to look for · which existing tool/agent to
reuse · which files/globs to inspect · what evidence to capture · which owner agent (Deep tier)*.
Coverage must include **all** of these:

1. **Read it / understand it / map it** — repo tour, ASCII tree, entry points, critical execution paths.
2. **Tech stack & versions** — languages, runtimes, frameworks, package managers, lockfiles, pinned versions; currency vs. upstream (Deep: WebSearch + Context7 for EOL / latest / migration notes).
3. **Architecture & data flow** — pattern (layered / hexagonal / MVC / microservices / event-driven / monolith), layers, abstractions, inter-component comms, data model & migrations; reuse `/codebase-deep-dive` diagrams or generate Mermaid.
4. **Directory map & structure** — what lives where, naming conventions, where new code goes.
5. **Build / run / debug locally** — exact commands to install, build, run, debug; devcontainer/Docker; toolchain pins (`.nvmrc` / `.python-version` / `.tool-versions` / `mise` / `asdf`).
6. **Tests** — framework(s), how to run (fast / full / live tiers), test pyramid shape, fixtures/mocking patterns, coverage level, known flaky tests.
7. **CI gates** — what runs on a PR (`.github/workflows/`, `.gitlab-ci.yml`, etc.), required checks, what blocks a merge.
8. **Env & config (NO SECRETS)** — `.env.example` and config files: their **existence and variable names only** — never read or echo a secret value.
9. **Conventions** — code style, naming, import organisation, error handling, logging, comment policy — **validated against actual code**, not just asserted from a linter config.
10. **Versioning & releases · git workflow** — semver policy, tag scheme, `CHANGELOG` discipline, branching strategy (trunk-based / gitflow / PR-based), commit conventions, release & deploy & rollback path.
11. **Rules & agent instructions** — detect and summarise every file in `references/RULES-FILES.md`: `CLAUDE.md`, `AGENTS.md`, `.cursorrules` / `.cursor/rules/*`, `.windsurfrules`, `.github/copilot-instructions.md`, `.editorconfig`, `.gitattributes`, `CODEOWNERS`, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `.pre-commit-config.yaml`, `renovate.json` / `dependabot.yml`, project `.claude/{skills,agents,commands}/`, `.vscode/`, `.devcontainer/`. For each: one-line summary of what it mandates.
12. **Integrations · observability · security posture** — external APIs/DBs/queues/auth providers consumed; logging/metrics/tracing conventions; auth/authz model; dependency-vuln / known-CVE signals; how secrets are handled.
13. **Repo health snapshot** — git-churn hotspots (`git log` over last N months), active contributors & bus-factor, ownership (`CODEOWNERS`), doc-drift signals (reuse `Skill(doc-drift-detection)` heuristics), `TODO`/`FIXME`/`HACK` & known-issue backlog, dependency health (outdated/deprecated), test-coverage gaps.
14. **Pros / cons / watch-outs** — honest verdict per `references/PROS-CONS-RUBRIC.md`; ≥3 evidence-cited items per column; explicit trade-offs.
15. **Contribute safely** — codebase-specific playbook per `references/PLAYBOOK-CONTRIBUTE.md`: branch from where, the CI/test gauntlet, the impact-analysis ritual, what's fragile/generated/vendored ("here be dragons"), review norms, commit conventions, a concrete "first PR" suggestion.
16. **Add a feature** — codebase-specific playbook per `references/PLAYBOOK-ADD-FEATURE.md`: a representative end-to-end slice (data model → logic → API/UI → tests → docs), where each layer's files live, the conventions that bind, how to verify.
17. **Glossary** — domain ubiquitous language a newcomer must learn to read the code & PRs.
18. **Provenance** — date · short SHA · tier · tools used · what was absorbed vs. freshly run · known limitations/gaps.
19. **AGENTS.md authoring/review** (Standard/Deep, with consent — never Quick) — if the repo has no `AGENTS.md`, offer to author one (`references/AGENTS-MD-TEMPLATE.md`) distilled from the analysis; if it exists, **never overwrite** — write `AGENTS.review.md` (accuracy review + gaps + proposed rewrite); if only `CLAUDE.md` exists, offer a thin pointer-`AGENTS.md` or a standalone one. **Read `references/AGENTS-MD-TEMPLATE.md` first — its SAFETY PROTOCOL is binding.** Never modify `CLAUDE.md` (that's `/init`'s job — just flag drift).

---

## Tier workflows

### Quick (~5 min)

1. Step 0 (absorb). If no `PROJECT_INDEX.json` — *optionally* run `/index` (skip if it would
   take too long on a huge repo).
2. Read: `README*`, `CLAUDE.md`/`AGENTS.md` (head only if huge), the package manifest
   (`package.json` / `pyproject.toml` / `go.mod` / `Cargo.toml` / `pom.xml` / `Gemfile`),
   the primary CI file, `CHANGELOG*`, `LICENSE*`, top-level dir listing.
3. `git log --oneline -15`, `git log --format='%an' | sort | uniq -c | sort -rn | head`,
   `git remote -v`, `git branch -a | head`, `git describe --tags --abbrev=0` (if any).
4. Write **only** `ONBOARDING.md` at the repo root using the "10-minute orientation" section of
   `references/ONBOARDING-TEMPLATE.md` — tech stack, what it does, how to run it, how to test it,
   the rules files that exist, the obvious pros/cons, and a "for the full picture, run
   `/understand-codebase --standard`" footer. ≤ ~150 lines. No `.claude/onboarding/`. **Do not
   touch `AGENTS.md` in Quick tier** — just note "no `AGENTS.md` — run `--standard` to generate one"
   if it's absent.

### Standard (~15–30 min) — DEFAULT

1. Step 0 (absorb). Ensure `PROJECT_INDEX.json` exists (run `/index` if not).
2. Detect languages present (gate `sg`/ast-grep patterns accordingly; fall back to `Grep`).
3. Launch **4 parallel `Agent(subagent_type=Explore)` calls in one message** — each owns a
   cluster and writes a structured summary back (NOT to disk; the main thread synthesizes):
   - **Agent S1 — Structure & Stack:** dimensions 1–4 + 12-integrations. Bootstrap from
     `PROJECT_INDEX.json` / `.planning/codebase/STACK.md|ARCHITECTURE.md|STRUCTURE.md`. Use `sg`
     for entry points, class/struct defs, route decorators (patterns from `Skill(code-intelligence)`).
   - **Agent S2 — Build / run / test / CI / config:** dimensions 5–8. Find install/build/run/debug
     commands, test commands & tiers & pyramid, CI workflow contents, `.env.example` variable
     **names** only. **Never read a secret value.**
   - **Agent S3 — How this team works:** dimensions 9–11. Conventions validated against actual
     code (sample 5–10 files), versioning & release & git workflow (`git log`, tags,
     `CHANGELOG`, branch names, commit message patterns), and **every rules/agent-instruction
     file** in `references/RULES-FILES.md` with a one-line summary each.
   - **Agent S4 — Repo health & verdict inputs:** dimensions 12-observability/security, 13, 14,
     17. `git log` churn hotspots, contributor stats, `CODEOWNERS`, `Skill(doc-drift-detection)`
     heuristics, `TODO`/`FIXME` inventory, outdated-deps signal, test-coverage gaps, "here be
     dragons", glossary terms, and the raw pros/cons evidence.
   Each agent prompt MUST restate the **hard "no secrets" constraint** (see below) and ask for
   evidence (file paths, commands, counts, git facts), not vibes.
4. **Synthesize** (main thread): reconcile the four reports, cross-check claims against the
   absorbed artifacts, fill the dimension catalogue, build the pros/cons verdict
   (`references/PROS-CONS-RUBRIC.md`) and the two playbooks (`PLAYBOOK-CONTRIBUTE.md`,
   `PLAYBOOK-ADD-FEATURE.md`) — both must cite **real files/commands from this repo**, not boilerplate.
5. **Write**: `ONBOARDING.md` at the repo root (`references/ONBOARDING-TEMPLATE.md`) and
   `.claude/onboarding/00-index.md` … `09-repo-health-and-verdict.md`
   (`references/DEEPDIVE-TEMPLATES.md`). If a `.claude/reports/codebase-deep-dive-*/` exists,
   link its diagrams; otherwise generate a Mermaid architecture sketch into
   `.claude/onboarding/diagrams/architecture.mmd`.
6. **AGENTS.md decision** (dimension 19) — read `references/AGENTS-MD-TEMPLATE.md`; follow its
   SAFETY PROTOCOL: no `AGENTS.md` & no `CLAUDE.md` → `AskUserQuestion` to author one (or write
   `AGENTS.draft.md`); `AGENTS.md` exists → write `AGENTS.review.md`, never overwrite; only
   `CLAUDE.md` exists → `AskUserQuestion` (thin pointer / standalone / leave it). Never edit `CLAUDE.md`.
7. **Self-check** against the acceptance criteria (below) and the secret-leak grep gate. Report a
   concise summary to chat (not the full docs) — including which `AGENTS.md` action was taken.

### Deep (~45 min+) — opt-in, `TeamCreate` agent-team

Use `Skill(agent-teams)` machinery. Team template: `templates/onboarding-team.md`. Shape:

- **Orchestrator** (you): create the team (`TeamCreate`, name `understand-codebase-<repo-slug>`),
  build the task list, dispatch, collect confirmations only (keep your context lean).
- **Mappers (reuse the known-working agent):** spawn `Agent(subagent_type="gsd-codebase-mapper")`
  ×4 focuses (`tech`, `arch`, `quality`, `concerns`) → they write `.planning/codebase/*.md`.
  Also run `/codebase-deep-dive` (or its Phase 2–4 agents directly) → `.claude/reports/...` +
  `diagrams/*.mmd`. Ensure `/index` has run.
- **Human-layer workers (new agents):** spawn `Agent(subagent_type="codebase-onboarding-conventions")`,
  `Agent(subagent_type="codebase-onboarding-runbook")`, `Agent(subagent_type="codebase-onboarding-health")`
  in parallel — each writes its `.claude/onboarding/NN-*.md` deep-dive directly.
- **Enrichment:** the workers (and/or you) use **WebSearch + Context7 MCP** for: framework
  version currency / EOL dates, known CVEs in the dependency set, and "current best-practice"
  patterns for the detected stack. Write findings into `.claude/onboarding/01-stack.md` (a
  "Version currency" subsection).
- **Synthesizer:** `Agent(subagent_type="codebase-onboarding-synthesizer")` — reads ALL
  per-dimension docs + absorbed artifacts + enrichment, writes the root `ONBOARDING.md`, the
  `00-index.md`, the pros/cons verdict, both playbooks, the "10-minute orientation" and "first
  PR" sections, and handles the **AGENTS.md decision** per `references/AGENTS-MD-TEMPLATE.md`
  (the SAFETY PROTOCOL is binding — the orchestrator runs the `AskUserQuestion` gate, the
  synthesizer writes `AGENTS.md` only on consent, or `AGENTS.review.md` if one exists).
- **Reviewer:** spawn `Agent(subagent_type=code-reviewer)` (or `comprehensive-review:code-reviewer`)
  pointed at `ONBOARDING.md` + `.claude/onboarding/` with the brief: "verify every factual claim
  against the codebase; flag boilerplate not grounded in this repo; run the secret-leak grep."
  Apply its corrections, then `SendMessage` shutdown and clean up the team.

If any reused tool/agent is missing → skip that input, note it in Provenance, continue. Never hard-fail.

---

## Hard constraints (restate verbatim in every spawned agent prompt)

- **NO SECRETS.** Never read, open, or echo the *contents* of `.env`, `.env.*`, `*.key`, `*.pem`,
  `*.p12`, `*.keystore`, `id_rsa*`, `credentials*`, `secrets*`, `*.tfstate`, service-account JSON,
  or anything matching a credential pattern. You may report that such a file *exists* and the
  *names* of variables declared in `.env.example` / committed config templates. (Mirrors the
  `gsd-codebase-mapper` rule.)
- **Evidence or it didn't happen.** Every claim → a file path, a command, a git fact, a count, or
  an explicit "not found — gap". No vague assessments.
- **Reuse before rebuild.** If `.planning/codebase/`, `.claude/reports/codebase-deep-dive-*/`, or
  `PROJECT_INDEX.json` exist and are fresh, absorb them; do not re-run the heavy tool.
- **Read-only on the target's code.** This skill writes only `ONBOARDING.md`, `.claude/onboarding/**`,
  and (via reused tools) `PROJECT_INDEX.json` / `.planning/codebase/**` / `.claude/reports/**`.
  It may *additionally* write `AGENTS.md` — **only if absent and only with explicit consent** —
  or `AGENTS.review.md` / `AGENTS.draft.md` (sidecars that never touch an existing `AGENTS.md`).
  It **never** edits an existing `AGENTS.md`, never edits `CLAUDE.md`, and never edits the target's source.
- **Language-agnostic.** Lean on globs + `git` + `sg` (ast-grep), falling back to `Grep`. Don't
  assume Python/JS.

## Error handling / graceful degradation

| Situation | Behaviour |
|---|---|
| `AskUserQuestion` declined | Default: target = cwd, tier = Standard. Note assumptions in Provenance. |
| `/index` unavailable or too slow | Skip; agents discover structure directly. Note in Provenance. |
| `gsd-codebase-mapper` / `/codebase-deep-dive` unavailable | Deep → enhanced-Standard. Note. |
| `TeamCreate` unavailable / team spawn fails | Deep → enhanced-Standard. Note. |
| Context7 / WebSearch unavailable | Skip version-currency/CVE enrichment; note as a limitation. |
| Not a git repo | Skip dimension 13 churn/contributors; note. Other dimensions still run. |
| Huge repo (>100k LOC) | Warn; offer to scope to a subtree; if continuing, prefer Haiku for Explore agents. |
| An Explore agent fails | Mark that cluster's sections "Incomplete — agent failed"; continue with the rest. |

## Acceptance criteria (self-check before reporting done)

- Repo with a `CLAUDE.md` and a `.cursorrules` → `ONBOARDING.md` "Rules & agent instructions"
  section names **both** with one-line summaries.
- Repo with semver tags + a `CHANGELOG.md` → "Versioning & releases" states the scheme, tag
  pattern, and release command (or "not found — gap").
- `.claude/onboarding/` (Standard/Deep) contains the templated file set, each with its
  date + short-SHA stamp.
- `ONBOARDING.md` has a "Pros / Cons / Watch-outs" section with ≥3 evidence-cited items per column.
- `ONBOARDING.md` has a "Contribute safely" section and an "Add a feature" section, each
  referencing **real files/commands from this repo**.
- `grep -rEi 'api[_-]?key\s*=\s*\S|BEGIN [A-Z ]*PRIVATE KEY|password\s*=\s*\S|secret\s*=\s*["\x27]\S' ONBOARDING.md .claude/onboarding/`
  → zero hits in skill-written files.
- `--quick` → only `ONBOARDING.md`, ≤ ~150 lines, no `.claude/onboarding/`, `AGENTS.md` untouched.
- Repo with **no** `AGENTS.md` (Standard/Deep) → user was asked before any `AGENTS.md`/`AGENTS.draft.md`
  was written; if consent given, the file follows `references/AGENTS-MD-TEMPLATE.md` and is ≤ ~120 lines.
- Repo **with** an existing `AGENTS.md` → it is byte-for-byte unchanged; an `AGENTS.review.md`
  sidecar exists with a section-by-section accuracy verdict + a proposed rewrite. `CLAUDE.md` (if present) byte-for-byte unchanged.
- Deep → a team dir appeared under `~/.claude/teams/`; task list shows mapper tasks → synthesis →
  review with the right `blockedBy` edges; reviewer posted a verdict.
- Re-run on the same repo (Standard) → `ONBOARDING.md` updated in place, fresh Provenance stamp,
  no duplicate files.

## References (load on demand — don't inline)

- `references/DIMENSIONS.md` — the dimension catalogue with per-dimension "what / reuse / inspect / evidence / owner".
- `references/RULES-FILES.md` — exhaustive detection list for rules / agent-instruction / convention files.
- `references/REUSE-MAP.md` — exact invocation recipes for the composed tools + how to detect & absorb their prior outputs.
- `references/PROS-CONS-RUBRIC.md` — the honest-verdict rubric.
- `references/PLAYBOOK-CONTRIBUTE.md` — "contribute safely" playbook template.
- `references/PLAYBOOK-ADD-FEATURE.md` — "add a feature" playbook template.
- `references/AGENTS-MD-TEMPLATE.md` — author / review / improve `AGENTS.md` — **read before any `AGENTS.md` action; its SAFETY PROTOCOL is binding.**
- `references/ONBOARDING-TEMPLATE.md` — the root `ONBOARDING.md` skeleton.
- `references/DEEPDIVE-TEMPLATES.md` — skeletons for each `.claude/onboarding/NN-*.md`.
- `templates/onboarding-team.md` — the Deep-tier `TeamCreate` composition.

## Related skills / commands (compose, don't duplicate)

`/index` · `/codebase-deep-dive` · `Skill(gsd-map-codebase)` (+ `Skill(gsd-scan)`, `Skill(gsd-intel)`) ·
`Skill(system-mapping)` · `Skill(code-intelligence)` / `Skill(code-intelligence-index)` ·
`Skill(impact-analysis)` · `Skill(doc-drift-detection)` · `Skill(agent-teams)` ·
`Skill(improve-codebase-architecture)` (follow-on, once you understand it) ·
`Skill(aa-ma-plan)` / `/deep-analysis` (follow-on, when you go to change it).
