---
name: understand-codebase
description: Onboard to a new/inherited/shared codebase — read it, map it, learn conventions/versioning/tests/tech-stack/rules (AGENTS.md/CLAUDE.md), assess pros & cons, and produce a "contribute safely" + "add a feature" playbook. Writes ONBOARDING.md at the repo root + .claude/onboarding/ deep-dives. Tiered (--quick / --standard / --deep). Optionally authors/reviews AGENTS.md.
argument-hint: "[path] [--quick | --standard | --deep]"
---

# /understand-codebase

Thin wrapper — this command **invokes `Skill(understand-codebase)`**. All behaviour, tiers, the
reuse-and-absorb protocol, the dimension catalogue, the AGENTS.md safety protocol, and the output
contract live in that skill and its `references/`.

## What it does (summary)

Produces a human-readable **`ONBOARDING.md`** at the repo root (publishable via `ShareOnboardingGuide`)
backed by a **`.claude/onboarding/`** directory of per-dimension deep-dives, covering: what the
repo is · tech stack & versions · architecture & data flow · directory map & entry points ·
build/run/debug locally · tests & CI gates · env & config (names only, no secrets) · conventions
(validated against code) · versioning/releases/git workflow · rules & agent-instruction files
(`CLAUDE.md`/`AGENTS.md`/`.cursorrules`/`CODEOWNERS`/…) · integrations · observability · security
posture · repo-health snapshot (churn hotspots, ownership, doc drift, tech-debt backlog) · an
honest **pros/cons/watch-outs verdict** · a **"contribute safely" playbook** · an **"add a feature"
playbook** · a glossary · provenance. Optionally **authors an `AGENTS.md`** if one is missing
(consent-gated; never in `--quick`) or **reviews an existing one** via an `AGENTS.review.md`
sidecar (never overwrites it).

## Arguments

`$ARGUMENTS` — optional, in any order:
- a **path** to the repo to analyse (default: current working directory).
- a **tier flag**: `--quick` (~5 min, one-page `ONBOARDING.md` only), `--standard` (default; ~15–30 min, 4 parallel Explore agents + the full pack), `--deep` (~45 min+; a `TeamCreate` agent-team that also runs `gsd-map-codebase`, `/codebase-deep-dive`, `/index`, and WebSearch+Context7 version-currency checks).

If no tier is given, the skill asks (defaulting to Standard) and also confirms target path + the
reader's intent (just understand · planning to contribute · planning to add a feature).

## Instructions for Claude

1. Parse `$ARGUMENTS` for a path and/or a tier flag.
2. Invoke `Skill(understand-codebase)`, passing the path and tier (or letting the skill prompt).
3. Follow the skill exactly — especially: **Step 0 reuse-and-absorb** (don't redo `gsd-map-codebase`/`/codebase-deep-dive`/`/index` if fresh outputs exist), the **NO-SECRETS** hard constraint, and the **`references/AGENTS-MD-TEMPLATE.md` SAFETY PROTOCOL** for anything `AGENTS.md`-related (author only if absent + with consent; never overwrite an existing one; never edit `CLAUDE.md`).
4. On completion, report the concise summary the skill specifies (tools run vs absorbed, the `AGENTS.md` action taken, the bottom-line verdict, and where the docs landed).

## When to use vs. not

**Use** when joining a new/inherited/shared codebase, or when asked "explain this repo / how do I
contribute / how do I add a feature / is this codebase any good / write me an onboarding doc".

**Don't use** — use the named alternative: editing code you already understand → `Skill(impact-analysis)`/`Skill(system-mapping)`; pure quality/security audit with no onboarding deliverable → `/codebase-deep-dive`; implementation planning → `/aa-ma-plan` or `/deep-analysis`; just a structural index → `/index`; trivial repo (< ~5 files) → just read it.
