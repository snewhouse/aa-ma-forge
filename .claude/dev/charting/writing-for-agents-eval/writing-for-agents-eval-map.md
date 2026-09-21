# Charting: writing-for-agents-eval

## Destination

A locked decision — fork verbatim, derive, or skip mattpocock/skills `writing-for-agents` @ c55ee46 — and, if adopted, which local surfaces it replaces or feeds (`write-a-skill`, `skill-developer`, `/aa-ma-plan` artefact writers). A decision to lock before `/aa-ma-plan`, not a build.

## Notes

Domain: aa-ma-forge skill adoption (ADR-0004 `write-a-skill` is a Derived orphan of this very skill's ancestor). Skills to consult: aa-ma-research, grill-with-docs. Standing preferences: verbatim forks are recorded in `claude-code/skills/FORKS.json` with an ADR; Ste prefers prototypes over speculation; no rewrite of existing skills in this effort.

## Decisions so far

- [Ticket 1: What does writing-for-agents contain at c55ee46, and how much overlaps what we ship?](#ticket-1-what-does-writing-for-agents-contain-at-c55ee46-and-how-much-overlaps-what-we-ship): mostly new rules, 3 direct conflicts with skill-developer/write-a-skill, zero text overlap with our fork (lineage rewritten upstream at 1.0.0) — research file linked.
- [Ticket 2: Fork verbatim, derive, or skip?](#ticket-2-fork-verbatim-derive-or-skip): fork verbatim, model-invoked; conflicts go in `## In this repo`, never into the fork.
- [Ticket 3: What happens to `write-a-skill` if we adopt?](#ticket-3-what-happens-to-write-a-skill-if-we-adopt): retire it; surviving sections fold into the fork's `## In this repo`; ADR-0004 superseded.
- [Ticket 4: Should `/aa-ma-plan` Phase 5 writers and `aa-ma-scribe` invoke writing-for-agents?](#ticket-4-should-aa-ma-plan-phase-5-writers-and-aa-ma-scribe-invoke-writing-for-agents): no — AA-MA templates + grammar own that shape; the skill stays scoped to skills/CLAUDE.md/AGENTS.md.

## Tickets

### Ticket 1: What does writing-for-agents contain at c55ee46, and how much overlaps what we ship?
- Type: research
- Mode: AFK
- Status: RESOLVED
- Blocked-by: —
#### Question
Read `skills/productivity/writing-for-agents/SKILL.md` and `SKILL-MECHANICS.md` at mattpocock/skills `c55ee46` (primary source: the files themselves). Summarise the rules they state. Compare against local `claude-code/skills/write-a-skill/SKILL.md`, `~/.claude/skills/skill-developer`, and `writing-clearly-and-concisely`: which rules are new, which duplicate, which conflict. Record file sizes, md5 of each upstream file, and the upstream CHANGELOG entries that renamed `write-a-skill` → `writing-great-skills` → `writing-for-agents`.
#### Answer
See [docs/research/writing-for-agents-eval-overlap.md](../../../../docs/research/writing-for-agents-eval-overlap.md). Upstream at c55ee46 = `SKILL.md` (10 886 B, md5 `9663b04e…`, 7 all-reference sections) + `SKILL-MECHANICS.md` (2 629 B, md5 `f3648a8f…`) + `agents/openai.yaml`; model-invoked. **Zero text overlap** with our Derived `write-a-skill` — upstream rewrote the lineage from scratch at 1.0.0 (`47bde84`, → writing-great-skills) and renamed again at 1.2.0 (`77d207e`, → writing-for-agents), so nothing is byte-comparable to re-fork. Most rules are new to us; a minority partially overlap `write-a-skill`/`skill-developer`; Strunk rules duplicate `writing-clearly-and-concisely`; **three direct conflicts** with local text: skill-developer's "include ALL trigger keywords" vs one-trigger-per-branch, 100/500-line split caps vs the branch test, and write-a-skill's mandatory "Use when" vs stripped descriptions for user-invoked skills (exact tallies: the file's overlap table). ADR-0004 misdates the lineage ("removed in 1.0.0" — only renamed).

### Ticket 2: Fork verbatim, derive, or skip?
- Type: grilling
- Mode: HITL
- Status: RESOLVED
- Blocked-by: 1
#### Question
Given Ticket 1's overlap table: fork the two files verbatim (FORKS.json row + ADR), derive a local variant, or skip and keep `write-a-skill` as is? What is the invocation model — model-invoked (fires on skill/CLAUDE.md edits) or user-invoked only?
#### Answer
**Fork verbatim** — `SKILL.md` + `SKILL-MECHANICS.md` (+ `agents/openai.yaml`) @ c55ee46 into `claude-code/skills/writing-for-agents/`, `FORKS.json` row, new ADR; the three conflicts (trigger-keyword maximalism, line-count split caps, mandatory "Use when") are resolved in an `## In this repo` block appended below the verbatim text, never by editing the fork. **Model-invoked as upstream** (no `disable-model-invocation`): firing on skill/CLAUDE.md/AGENTS.md edits is the point. Rejected: derive (would hide the conflicts instead of forcing decisions; no drift tracking), skip (leaves 15-ish new rules unused). Decided with Ste 2026-09-21 (grilling, 2 questions).

### Ticket 3: What happens to `write-a-skill` if we adopt?
- Type: grilling
- Mode: HITL
- Status: RESOLVED
- Blocked-by: 2
#### Question
Retire `write-a-skill` (ADR-0004 superseded), keep it as a Derived sibling, or fold its progressive-disclosure sections into the fork's `## In this repo` block?
#### Answer
**Retire `write-a-skill`, fold its surviving sections in.** Delete `claude-code/skills/write-a-skill/`; ADR-0004 → Superseded by the writing-for-agents ADR; the progressive-disclosure and directory-structure guidance upstream dropped moves into the fork's `## In this repo` block; `FORKS.json` row removed; skill count unchanged (one out, one in). Rejected: keep as Derived sibling (two skills answering "how do I write a skill" with different rules), defer to the rewrite effort (retirement is a scoping decision, not a rewrite). Decided with Ste 2026-09-21.

### Ticket 4: Should `/aa-ma-plan` Phase 5 writers and `aa-ma-scribe` invoke writing-for-agents?
- Type: grilling
- Mode: HITL
- Status: RESOLVED
- Blocked-by: 1
#### Question
AA-MA artefacts are documents agents consume. Should the Phase 5 writers (and the scribe agent) call `Skill(writing-for-agents)` before writing plan/reference/tasks — or do the AA-MA templates and the gate's grammar already own that shape? (Graduated from *Not yet specified* after Ticket 1.)
#### Answer
**No.** AA-MA artefacts have their own templates (`docs/templates/`) and a grammar the gate/TUI read (`src/aa_ma/grammar.py`); a prose-style skill firing inside Phase 5 adds tokens with no reader that benefits. writing-for-agents applies to skills, `CLAUDE.md`/`AGENTS.md` and pointer-reached docs — which is exactly its upstream trigger. Decided with Ste 2026-09-21.

## Not yet specified


## Out of scope

- rewriting the existing 21 shipped skills to writing-for-agents' rules — a separate effort with its own destination
