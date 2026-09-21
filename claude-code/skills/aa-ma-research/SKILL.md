<!-- Derived from https://github.com/mattpocock/skills/skills/engineering/research @ c55ee46 (forked 2026-09-21; renamed aa-ma-research, AA-MA dispatch rules appended) — aa-ma-forge v0.13.0 -->
---
name: aa-ma-research
description: Investigate a question against high-trust primary sources and capture the findings as a Markdown file in the repo. Use when the user wants a topic researched, docs or API facts gathered, or reading legwork delegated to a background agent.
---

Spin up a **background agent** to do the research, so you keep working while it reads.

Its job:

1. Investigate the question against **primary sources** (official docs, source code, specs, first-party APIs), not a secondary write-up of them. Follow every claim back to the source that owns it.
2. Write the findings to a single Markdown file, citing each claim's source.
3. Save it where the repo already keeps such notes; match the existing convention, and if there is none, put it somewhere sensible and say where.
## In this repo
- Dispatch the background agent as `aa-ma-researcher` (Agent tool, `subagent_type: aa-ma-researcher`). It has no Agent tool, so it cannot re-delegate.
- Answer the stated question only. List threads you saw but did not follow under `## Not pursued`.
- "Where the repo already keeps such notes" is `docs/research/<plan-slug>-<topic>.md`, with the header used by `docs/research/skill-ecosystem-audit.md` (Created / Author / Reviewed-Through-Date / Valid-Through / Sources). Pass slug and topic as `[a-z0-9-]+` — no path separators — so the agent's single Write stays a direct child of `docs/research/`.
