---
name: assess-codebase
description: Whole-repo quality and risk assessment — tools measure, model agents judge with file:line evidence, a refuter attacks every Critical/High claim. Rates architecture, maintainability, security and tests & dependencies (no overall grade) into a SHA-stamped, secret-gated report with SARIF under .claude/reports/assess-codebase/. Tiered (--quick / --standard / --deep).
argument-hint: "[path] [--quick | --standard | --deep]"
---

# /assess-codebase

Thin wrapper — this command **invokes `Skill(assess-codebase)`**. Tiers, the measure → judge →
refute → finalize steps, the rating rubric and the agent prompts live in that skill and its
`references/`.

## Arguments

`$ARGUMENTS` — optional, in any order:
- a **path** to the repo to assess (default: current working directory);
- a **tier flag**: `--quick` (measure only, no agents), `--standard` (default; judges + refuter,
  offline), `--deep` (adds the network tools, a test run, and the optional claude-security pass).

With no tier flag the skill asks once, showing the tracked-file count.

## Instructions for Claude

1. Parse `$ARGUMENTS` for a path and/or a tier flag.
2. Invoke `Skill(assess-codebase)` with them and follow it exactly — Step 0's preflight first; no
   agent runs if it refuses.
3. Report what the skill's Step 7 specifies: report dir, per-dimension ratings with inputs and
   confidence, counts, tools missing, wall-clock.

## When to use vs. not

**Use** for "is this codebase any good", a pre-acquisition or pre-adoption review, a tech-debt
inventory, or a SARIF baseline to track findings over time.

**Don't use** — reviewing a change → `Skill(verify-impl)`; onboarding → `/understand-codebase`;
a single file → just read it.
