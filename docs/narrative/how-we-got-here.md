# How We Got Here

> The origin story of the Advanced Agentic Memory Architecture (AA-MA), a structured external memory system for LLM agents. Written by Stephen Newhouse, April 2026.

---

## The problem I was trying to solve

I run professional services at a biomedical company. The work is regulatory, technical, and long-running: evidence chains across multiple databases, pharmacovigilance signal validation, data pipelines touching half a dozen APIs. These are not afternoon projects. They stretch across weeks, sometimes months, and they demand precision.

In late 2025 I started using Claude Code seriously. Not casually, not for one-off scripts. Properly. Multi-session projects with real complexity and real consequences.

The first thing I noticed: Claude forgets everything.

Every new session started from zero. I'd explain the same architecture, re-establish the same constraints, re-state the same decisions. Context drift was constant. I'd watch Claude confidently propose something we'd already rejected two sessions ago, with no memory of the rejection or the reasons behind it. For someone with MS who has to manage cognitive fatigue carefully, repeating myself is not just annoying. It's expensive.

The longer the project, the worse it got. Short tasks were fine. Anything spanning more than two or three sessions became an exercise in re-orientation rather than forward progress.

## Early experiments

I started with the obvious approach: a big `CLAUDE.md` instruction file. Project context, architectural decisions, API details, constraints, preferences. One massive file loaded at the start of every session.

It helped. A bit. But it had problems.

First, the file grew unwieldy. Past a certain size, Claude couldn't prioritise what mattered. Immutable facts (this API endpoint uses this exact header) got buried alongside stale decisions and obsolete context. Second, there was no separation between "what is true right now" and "what we decided last week." Everything was equally weighted, equally flat.

I experimented with the `.claude/` directory structure, with rules files, with different ways of organising instructions. Some of it stuck. The tiered loading model (always-loaded, auto-loaded, on-demand) was an early win. But the core problem remained: there was no structured memory for the work itself. I had a well-configured tool with amnesia.

## The 3am spark

MS messes with sleep. Some nights you lie there and the brain won't switch off. One of those nights, early November 2025, I was scrolling through r/ClaudeCode at 3am instead of staring at the ceiling. I found a post linking to a dev.to article by [Diet-Coder](https://dev.to/diet-code103/claude-code-is-a-beast-tips-from-6-months-of-hardcore-use-572n): "Claude Code is a Beast: Tips from 6 Months of Hardcore Use."

I read it, thought "that's smart," and parked it.

A few days later, I was back in the same frustrated loop with Claude Code. Re-explaining the same architecture, re-stating the same constraints, watching context evaporate between sessions. I pulled Diet-Coder's article back up. The bit that grabbed me was the **Dev Docs System**: three files per task (`plan.md`, `context.md`, `tasks.md`), generated via a slash command, updated as work progressed. Simple. Practical. It was already solving the problem I kept hitting.

That was the seed. Full credit to Diet-Coder for planting it.

## The five-file taxonomy

The following Sunday night, I sat down with Claude Code and Gemini both open, a coffee, and Diet-Coder's three files as a starting point. What followed was a few hours of trial and error, bouncing ideas between two LLMs and my own tired brain.

Diet-Coder had three files. I ended up with five. The jump was immediate, driven by intuition and a bit of brainstorming rather than weeks of gradual discovery. Three files weren't enough separation for the kind of work I do.

Each of the five earned its place through a specific failure mode I'd experienced.

**plan.md** exists because strategy and execution kept getting tangled. When the plan was embedded in the task list, Claude would lose sight of the "why" while grinding through the "what." Separating strategy from execution meant you could re-read the rationale without wading through status checkboxes.

**reference.md** was the biggest win. Immutable facts: API endpoints, file paths, constants, confirmed specifications. Loaded first, never modified during execution. Before this file existed, Claude would hallucinate API details or subtly alter a base URL between sessions. Making facts immutable and high-priority eliminated an entire class of errors.

**context-log.md** captures decisions, trade-offs, and the reasoning behind them. This one prevents re-litigation. When you record "we chose approach X over Y because of Z," future sessions read the decision instead of re-debating it. It also serves as the compaction target: when context windows fill up, summaries go here rather than disappearing.

**tasks.md** is the execution state. Where are we right now? What's done, what's pending, what's blocked? Dependencies, acceptance criteria, status tracking. This is the file Claude reads to know what to do next.

**provenance.log** is the audit trail. Commit hashes, timestamps, session checkpoints. It sounds like overhead until the third time you need to figure out exactly when and why something changed. In regulated environments, provenance is not optional.

Why five and not three or ten? Three isn't enough separation. Plans and references serve fundamentally different purposes, and collapsing them recreates the "big flat memory" problem. Ten would be fragmentation: too many files to load, too much overhead to maintain. Five hits a sweet spot where each file has a clear, non-overlapping purpose and the total context cost stays manageable.

The separation principle is the core of it: different types of knowledge have different lifecycles and different access patterns. Treat them differently.

## Building the operational layer

A taxonomy is useless without tooling to enforce it. Over the following weeks I built the operational layer: Claude Code commands, skills, and agents that make the five-file system usable day-to-day.

The `/ultraplan` command produces structured plans with 11 mandatory outputs, from executive summary through milestones, acceptance criteria, artefacts, tests, rollback strategy, to risks and next actions. Overkill for a one-off script. Essential for anything that runs longer than a single session.

Two specialised agents emerged. The **scribe agent** handles file maintenance: provenance entries, context-log updates, keeping the main conversation focussed on actual work. The **validator agent** checks plan quality against the specification. Separate agents for bookkeeping means the primary interaction isn't constantly interrupted by administrative overhead.

The compaction hook was a quiet but critical piece. Claude Code auto-compacts the context window when it fills up. Without intervention, that compaction destroys whatever working memory the agent has accumulated. The `pre-compact-aa-ma.sh` hook intercepts that moment and writes a session checkpoint to `provenance.log` before compaction happens. It's a small thing. It prevents a catastrophic failure mode.

The execution commands (`/execute-aa-ma-milestone`, `/execute-aa-ma-step`, `/execute-aa-ma-full`) formalised the workflow. They enforce sync discipline: after every task, update the files, commit, push. No proceeding until the current state is recorded. This sounds bureaucratic. It's what keeps multi-week projects coherent.

## Refinements and inspiration

AA-MA was already three months old and battle-tested across multiple real projects when I started encountering related work from others.

In February 2026, Matt Pocock published his Claude Code skills repository. His skills structure influenced how I organised the `skills/` directory. His "grill-me" approach, relentlessly interrogating a plan before executing it, became the basis for the `/verify-plan` command. Good ideas travel fast, and there's no point reinventing what someone else has already nailed.

In April 2026, I researched Helix.ml's approach to spec-driven workflows. That research pushed me to formalise several things that had been informal: the HARD/SOFT gate classification for milestones (some gates are suggestions, some are hard stops requiring explicit approval), the optional `tests.yaml` file for machine-executable acceptance criteria, and the CHECKPOINT format for session recovery. These were v2.1 additions, refinements to an architecture that was already working.

I want to be clear about provenance here. Diet-Coder's Dev Docs System gave me the starting point: three files, a slash command, and the idea that Claude needs structured memory, not just a big instruction file. The jump from three files to five, the separation principle, the sync discipline, the compaction hook, the operational commands, the agent architecture: that's my work, built from real frustrations with real projects. Matt Pocock and Helix.ml refined what was already running. But without Diet-Coder's post at 3am, I might still be fighting the same battle with a bloated CLAUDE.md.

## Where we are now

Version 2.1 of the specification. Eighteen files across the ecosystem: specification, quick reference, team guide, six commands, one skill, two agents, one rule set, one hook, and the supporting documentation. Eight completed AA-MA tasks spanning November 2025 through April 2026, across domains including token optimisation, documentation workflows, Playwright testing, security remediation, and application development.

What works well: the five-file separation holds up. Reference files genuinely prevent fact drift. The sync discipline catches state that would otherwise evaporate. The compaction hook saves sessions that would otherwise lose continuity. Complex, multi-week projects stay coherent in ways they simply didn't before.

What's still rough: the operational overhead is real. Maintaining five files per task is more work than maintaining zero. The sync discipline depends on the agent actually following instructions, and sometimes it doesn't. There's no automated validation that the files are internally consistent. The whole system lives as Claude Code configuration, which means it's tied to one tool and one vendor.

## What's next

This repository, `aa-ma-forge`, is the first step towards making the system portable and verifiable. A Python package with Pydantic schemas for the five file types, validators that can check plan quality programmatically, and CLI tools that don't depend on Claude Code.

There's a skill activation architecture problem I haven't solved yet: how to let external skills declare their own AA-MA integration points without requiring manual registration. That's design work, not coding.

Other people building with LLM agents hit the same memory problem. Whether AA-MA becomes a distributable framework or stays a personal system depends on whether I can make the onboarding cost low enough to justify the benefit. That's an open question.

For now, it works. It solves the problem I built it to solve. Everything else follows from that.
