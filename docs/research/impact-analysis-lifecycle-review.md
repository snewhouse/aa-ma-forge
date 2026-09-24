# Impact Analysis — Lifecycle Review

- Date: 2026-09-24
- Scope: how `Skill(impact-analysis)` and its relatives are wired across plan → prototype → execute → review, and whether their output is used.
- Method: read the shipped surfaces (`claude-code/skills/impact-analysis/SKILL.md`, `commands/execute-aa-ma-{step,milestone,full}.md`, `skills/plan-verification/SKILL.md`, `skills/aa-ma-plan-workflow/references/PHASE_3_RESEARCH.md`, `skills/prototype/SKILL.md`, `src/aa_ma/gate.py`, `docs/templates/*`). Then audited the evidence in 17 completed plans and 1 active plan under `.claude/dev/`. The strongest quotes were spot-checked by hand.
- Status: report only. No code or skill was changed.

## TL;DR

| Question | Answer |
|---|---|
| Do we run impact analysis? | **Yes, at two points.** Once at plan time (Angle 3 of `/verify-plan`, plus Phase 3.5) and once after the code is written (§6.3 of `/execute-aa-ma-milestone`). |
| Do we do anything with the report? | **Plan-time: yes.** Angle 3 found real problems in 8 of 9 plans, and every finding was written back into its plan. **Execution-time: no.** About 35 of 91 completed milestones persisted a report. None was rated HIGH, none stopped a milestone, and none caused a change the plan hadn't already scheduled. |
| Is it run at the right stage? | **Partly.** The skill is written as a check *before* each edit ("Before ANY code edit"). In practice it runs *after* the milestone's code already exists. At step level it is explicitly "lightweight, no blocking". |
| Does it run with prototypes? | **No.** None of the 16 `PROTOTYPE` provenance entries mentions impact. The prototype skill has no hook for it. |
| Anything obvious missing? | Yes. (1) Nothing checks the plan-time prediction against what actually happened. (2) The §6.8 HARD-tier claim isn't enforced. (3) The skill ignores this repo's own `codemem` tools. (4) The skill can't see the markdown/`Skill()` dependency graph, which is most of this repo's product surface. (5) The same agent grades its own finished work. |

## 1. Where it is wired today

```
PLAN                          PROTOTYPE          EXECUTE (step)          EXECUTE (milestone end)          REVIEW
Phase 3.5 impact assessment   (nothing)          "impact awareness"      §6.3 Skill(impact-analysis)      §6.8 verify-impl
Phase 4.5 Angle 3 (fresh              │          lightweight, no block   consolidated report → screen     (5 fresh agents; no
  agent, 5-point check)               │                                  gate check #4 = comment only     impact input)
      │ findings → plan revision ✓    │                                        │ persisted? sometimes
      ▼                               ▼                                        ▼ consumed? never
 verification.md                  provenance PROTOTYPE                  context-log / provenance (ad hoc)
```

Key facts, with sources:

- **The skill says it runs before editing.** `impact-analysis/SKILL.md`: "The 5-Point Verification Checklist — Before ANY code edit, verify…", and the check is REQUIRED "During AA-MA milestone execution".
- **Execution only runs it at the end.** `execute-aa-ma-step.md:179-183`: "Impact awareness (lightweight, no blocking) … Full impact analysis verification runs at **milestone boundary**". §6.3 of `execute-aa-ma-milestone.md` (line 317) runs after all sub-steps (§5.2) are done.
- **The report goes to the screen only.** §6.3 says "Output consolidated impact analysis" and names no file to write it to. The §7.2 context-log completion template (`execute-aa-ma-milestone.md:852`) has fields for Key outcome, Artifacts and Tests, but **no Impact field**.
- **The gate doesn't enforce it.** `execute-aa-ma-milestone.md:592` reads `# 4. Impact-analysis evidence (already enforced in 6.3; double-check Result Log mentions)`. That line is a comment with no code under it. `src/aa_ma/gate.py` answers seven questions, and none of them is about impact. Yet `rules/engineering-standards.md:133` lists "Non-breaking constraint verified | **HARD** | `Skill(impact-analysis)` run". **The doctrine claims an enforcement that doesn't exist.**
- **Plan time checks it twice.** Phase 3.5 (`PHASE_3_RESEARCH.md:157`) runs a grep-based caller assessment. Angle 3 (`plan-verification/SKILL.md:160`) then re-runs the same 5-point check in a fresh agent. Angle 3's output is structured (`[CRITICAL]/[WARNING]/[OK]` per file, plus "files the plan SHOULD modify but doesn't mention") and is written to `verification.md`.

## 2. Empirical evidence (17 completed + 1 active plan)

| Signal | Count |
|---|---|
| Completed milestones | ~91 |
| Milestones with a persisted execution-time impact report (per-file or per-consumer breakdown) | ~18 real + ~17 one-liners ("LOW") |
| Execution-time ratings of **HIGH** | **0** (checked by grepping every provenance.log and context-log.md) |
| Milestones halted, re-planned or given new tasks because of §6.3 | **0** |
| Plans whose Angle 3 produced findings | 8 / 9 with verification.md |
| Plans whose Angle 3 findings were written back into the plan | 8 / 8 |
| PROTOTYPE entries that mention impact / callers / blast radius | 0 / 16 |

Representative quotes:

- Rubber stamp: `skill-ecosystem-integration-provenance.log:91` "Overall Risk: LOW (additive + tested + non-breaking)". The very next line, :92, is the GATE APPROVAL.
- Skill not actually invoked: `fix-drift-release-v0-9-0-context-log.md:48` "Impact Analysis (inline — `Skill(impact-analysis)` not invoked …)". `understand-codebase-skill` contains the same pattern.
- Most thorough report, still no effect: `milestone-grammar-ssot-provenance.log:69` "HIGHEST blast radius: …aa-ma-parse.sh … Overall risk: MEDIUM, resolved". The cascade it reports (:35 `Milestone.number int->str`) was **already in the plan** (plan.md:114-117) because **Angle 3 found it** (verification.md:22).
- Plan-time consumption is concrete: `hooks-hardening-m1-verification.md:72` "Angle 3 CRITICAL-2 (uninstall.sh) | Added M3.3.bis sub-step | RESOLVED". The sub-step exists (tasks.md:239). `diagram-generation-verification.md:44-56` shows 6 CRITICALs, each marked "Fixed".

**Reading the evidence (checking my assumptions).** "Zero HIGHs" has two possible explanations. Either the plans were good, or the check can't produce a HIGH. Three things point to the second:
1. The check runs after the code is written, by the agent that wrote it. Rating your own finished work HIGH means admitting it needs rework, so there is a built-in pull towards a pass.
2. Plan-time Angle 3 already absorbs the real ripples. What reaches §6.3 has mostly been de-risked, so §6.3 largely repeats Angle 3.
3. The risk rule is based on caller count, and the callers are found with grep over imports. Most of this repo's changes are to markdown commands and skills, where "callers" are `Skill(...)` / `/command` references. An import grep can't find those, so the count stays low.

**Conclusion:** plan-time impact analysis does real work. Execution-time impact analysis, as currently designed, is a ceremony: it costs tokens every milestone and produces no decision.

## 3. Answers to the specific questions

### Q1 — Do we do anything with the report?
At plan time, yes. At execution time, no. No file receives the report, no gate reads it, and nothing downstream uses it: §6.8 verify-impl agents don't receive it, the context-log template has no slot for it, and nothing compares it with the plan's prediction.

### Q2 — Do we run it at the planning phase, on the proposed plan and code?
Yes, twice (Phase 3.5 and Angle 3), and this is the stage that works. The gap: **the prediction is thrown away after planning.** Angle 3's list of files it expects to be affected is never carried into `reference.md` or the milestone `#### Contract` block, so execution has nothing to check the actual changes against.

### Q3 — Can it run with prototype skills?
Not today. Running the 5-point check *on the prototype code* would be wasted effort, because that code is throwaway and never merges (prototype rule 1 and rule 6). The thing that does have an impact is **the verdict**: the prototype settles a question, and the answer changes what the real code must do. That change is not assessed at the moment. When a verdict differs from the plan's assumption, the downstream milestones are silently out of date until someone notices.

### Q4 — Not just after the code is produced?
Right. The skill was designed to run before each edit, but it has been wired to run after the milestone. The cheap place for a check before editing is the **step**, where the files the step will touch are known and codemem can answer "who depends on this?" in milliseconds.

## 4. Obvious gaps

1. **Nothing compares the plan's prediction with what actually changed.** This is the most useful signal available, and it's mechanical: `git diff --name-only <milestone-window>` versus the file set Angle 3 predicted. A file that changed but wasn't predicted is the real warning sign (scope creep or an unplanned ripple). A file that was predicted but didn't change means a planned ripple was never handled.
2. **A HARD claim with no enforcement.** engineering-standards §5 says the impact check is HARD. The gate ignores it. Either enforce it like `CRITICAL_PATH_REVIEW` (a milestone-scoped provenance token) or downgrade the doctrine to SOFT. As things stand, the doc overstates what's enforced.
3. **The skill doesn't use this repo's own tooling.** `packages/codemem-mcp` ships `blast_radius`, `who_calls`, `co_changes`, `hot_spots` and `owners`. No skill or command references codemem. `co_changes` in particular finds coupling that no call graph shows, for example "every edit to X historically also edits README/CHANGELOG counts". That is exactly the stale-count drift CLAUDE.md warns about.
4. **The skill can't see markdown/prompt dependencies.** The skill says documentation-only changes don't need it. In this repo, though, the commands and skills are markdown and they are the product. A change to `Skill(impact-analysis)`'s own output format has callers (`execute-aa-ma-milestone.md` §6.3, `execute-aa-ma-full.md` §C, `aa-ma-execution/SKILL.md`), and grep over imports can't find them. The plugin-surface extractor in engineering-standards §1 is the right source for these edges.
5. **The agent grades its own work.** §6.8 uses fresh agents so the reviewer isn't the author. §6.3 doesn't. Its job partly overlaps with the `code-reviewer` agent's remit ("schema-breaking output regressions").
6. **No link to prototypes** (Q3 above).

## 5. Recommendations (ordered by value per unit of effort; nothing implemented)

| # | Change | Effort | Why |
|---|---|---|---|
| R1 | **Predicted-vs-actual check.** Angle 3 writes an `Expected-Blast-Radius:` file list per milestone into the plan's `#### Contract` block (or reference.md). §6.3 becomes: diff actual changed files against that list, and require a one-line explanation for each unpredicted file. | S | Turns §6.3 from a self-report into a mechanical comparison. It reuses the plan-time analysis that already works. |
| R2 | **Persist it and be honest about enforcement.** Add `- Impact: <risk> — <unpredicted files or "none">` to the §7.2 context-log template, plus a `[ts] IMPACT_ANALYSIS — <milestone> — <risk>` provenance token. Then **either** enforce the token in the gate (the same pattern as CRITICAL_PATH_REVIEW) **or** change engineering-standards §5 from HARD to SOFT. | S | Resolves the gap between what the doctrine claims and what the code enforces. It also gives future reviews something to audit. |
| R3 | **Prototype verdict impact.** Add a required field to the `PROTOTYPE` provenance entry: `— verdict-changes-plan: YES/NO`. If YES, run an Angle-3-style check on the *decision delta* (not the throwaway code), and apply any updates to later milestones before the gate. | S | Covers the one place where a plan changes during execution without any review. |
| R4 | **Pre-edit check at step level.** In `execute-aa-ma-step`, for files the step touches that have at least N dependents (codemem `who_calls` / `blast_radius`), print a one-line blast radius *before* editing. It stays non-blocking. | S–M | Puts the skill back at the point it was designed for, at little cost. |
| R5 | **Teach the skill codemem plus the markdown graph.** Add `co_changes` and `hot_spots` rows to the skill's tool table. Treat `Skill()` / `/command` references as callers when changing files under `claude-code/`. | M | Fixes the blind spot that keeps caller counts low in this repo. |
| R6 | **Remove the self-grading.** Fold the §6.3 judgement into §6.8 as input to the fresh `code-reviewer` (pass it the R1 unpredicted-file list), and keep §6.3 as the mechanical diff only. | M | Addresses the pull towards a pass. Only worth doing after R1–R2 show whether the problem persists. |

**Do not:** add another agent or another planning angle. Plan-time coverage is already sufficient; the gap is carrying its output forward.

**Leave alone:** Angle 3 as it is. It is the part that demonstrably works.

## 6. Open questions for Ste

- R2: enforce the impact check as HARD, or downgrade it to SOFT? (This changes the shipped enforcement surface, so it is `Critical-Path: hook-modification` and needs an ADR if enforced.)
- Should R1–R3 be done as one AA-MA plan, or as follow-up milestones to `diagram-generation`? (That plan's codemem `file_edges` work in M1 already supplies the import graph R1/R5 would use.)
