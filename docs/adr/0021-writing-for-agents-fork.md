# 0021. Fork `writing-for-agents`; retire `write-a-skill`

**Status:** Accepted
**Date:** 2026-10-09
**Deciders:** Stephen Newhouse (sole maintainer)
**Tags:** `skills`, `external-fork`, `conventions`, `evals`
**Supersedes:** [0004](0004-write-a-skill-adoption.md)

## Context and Problem Statement

The forge ships `write-a-skill` (ADR-0004), a Derived fork of a mattpocock/skills skill that
upstream deleted at 1.0.0. Upstream replaced that lineage with `writing-for-agents`, written from
scratch: a reference for writing any document an agent consumes (a skill, `CLAUDE.md`,
`AGENTS.md`, a doc reached by a pointer). It shares no text with our fork.

The writing-for-agents-eval map (4/4 resolved, 2026-09-21) compared the two. Of 25 rules upstream
states, 12 are new to the forge, 9 partly overlap, 1 duplicates, and 3 conflict with local text:
trigger-keyword maximalism, line-count split caps, and "Use when" on every description
([docs/research/writing-for-agents-eval-overlap.md](../research/writing-for-agents-eval-overlap.md)).
The code-conventions-impact map (Ticket 15) folded that map in and added the forge's own
prompt-as-code conventions, which need a home a skill author will read.

**Which skill tells an author how to write a forge skill, and where do the forge's conventions live?**

## Decision Drivers

- **One answer to "how do I write a skill".** Two skills with different rules would make the
  agent pick one at random.
- **Drift stays visible.** A fork pinned to an upstream SHA can be compared with upstream
  (`scripts/fork-drift.sh`); a rewrite cannot.
- **Local conventions are checkable.** They sit beside the tests that enforce them
  (`tests/test_frontmatter_at_top.py`, `tests/test_prompt_size.py`, `evals/`).

## Considered Options

1. **Fork `writing-for-agents` verbatim, append `## In this repo`, retire `write-a-skill`** (chosen).
2. **Derive a local variant.** Rejected: it hides the three conflicts instead of deciding them,
   and loses drift tracking.
3. **Skip; keep `write-a-skill`.** Rejected: leaves 12 new rules unused and keeps guidance that
   upstream itself abandoned.
4. **Keep both.** Rejected: two skills answering one question with different rules.

## Decision Outcome

Chosen option: **1**.

- `claude-code/skills/writing-for-agents/` holds `SKILL.md` and `SKILL-MECHANICS.md` from
  mattpocock/skills `skills/productivity/writing-for-agents` @
  `c55ee46073ed923f86ce59a5eb3b6d895095d1b7`, fetched with
  `gh api repos/mattpocock/skills/contents/…?ref=<sha>` (never from the plugin cache, which lags
  upstream), plus the upstream MIT `LICENSE`. sha256 at fetch: `SKILL.md`
  `551adca9…a896a74a`, `SKILL-MECHANICS.md` `c768e630…0a0059`, `LICENSE` `0e7ac423…07dbb5`.
  Upstream's `agents/openai.yaml` (Codex display metadata) is not taken: Claude Code does not read
  it.
- The upstream text is not edited. `SKILL.md` gains a provenance comment on line 2 and an
  appended `## In this repo` block; `FORKS.json` records the row as `derived`, with both the local
  and upstream md5. `tests/skills/test_writing_for_agents_fork.py` checks that the text above the
  block still hashes to upstream.
- The three conflicts are decided in that block: upstream wins on one trigger per branch and on a
  human-facing summary for user-invoked skills; the 500-line cap stays as a backstop beside
  upstream's branching test.
- The block also states the forge's conventions: the tested frontmatter schema, the size cap and
  TOC rule, the layout guidance carried over from `write-a-skill`, slash entry points as skills
  (ADR-0020), a reason on every MUST/NEVER/ALWAYS rule, and evals.
- `write-a-skill` is deleted and ADR-0004 is superseded. The skill count is unchanged.
- The skill stays model-invoked, as upstream: firing when a skill, `CLAUDE.md` or `AGENTS.md` is
  edited is the point. `/aa-ma-plan` Phase 5 and `aa-ma-scribe` do not invoke it: AA-MA artefacts
  follow `docs/templates/` and the gate grammar (writing-for-agents-eval map, Ticket 4).

### Skill evals

Gate-bearing and high-traffic skills keep advisory eval cases under `evals/<skill>/<case>/`, run
by `scripts/run-evals.sh` with `claude plugin eval` (proved in code-conventions-impact M4.3,
recorded in its context-log): repo-root target, each case naming `plugins: ["../../../claude-code"]`,
always `--no-publish --runs 1 --ablation none`. Every case has `max_turns: 12` (one Skill load, up to ~10 reads or greps, the answer); `tests/test_eval_cases.py` keeps the copies equal. Every case carries a `tool_used: Skill` grader:
in the proof run an LLM judge passed a case in which the skill had never loaded. Evals never gate
CI (cost, nondeterminism).

## Consequences

- **Good:** one skill-authoring reference, tracked against upstream; the forge's conventions sit
  next to the rules they refine, each pointing at its test.
- **Good:** the three conflicts are decided once, in writing.
- **Bad:** `SKILL.md` is `derived`, so `fork-drift.sh` reports a local md5 that differs from
  upstream by design; the hash test above the block is what proves the upstream text is intact.
- **Neutral:** an existing install keeps a dangling `~/.claude/skills/write-a-skill` link until
  `scripts/install.sh` runs again from main (its stale-link sweep removes it).

## References

- [ADR-0004](0004-write-a-skill-adoption.md) (superseded), [ADR-0020](0020-commands-become-skills.md)
- `.claude/dev/charting/writing-for-agents-eval/writing-for-agents-eval-map.md` (Tickets 1–4)
- [docs/research/writing-for-agents-eval-overlap.md](../research/writing-for-agents-eval-overlap.md)
- code-conventions-impact map, Ticket 15; plan M4
- Claude Code docs: skills frontmatter reference, plugin evals
