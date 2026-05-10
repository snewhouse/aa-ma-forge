# 0004. Adopt `write-a-skill` from mattpocock/skills

**Status:** Implemented (2026-05-10)
**Date:** 2026-05-10
**Deciders:** Stephen Newhouse, Claude (planning + execution sessions)
**Tags:** `workflow`, `aa-ma`, `skills`, `release-v0.6.0`, `external-fork`, `meta-tooling`

## Context and Problem Statement

aa-ma-forge ships **14 skills as of v0.5.0 + grill-with-docs in M1 = 15 pre-M2** that are reusable procedures Claude invokes via `Skill('<name>')`. New skills get added as the plugin evolves — `complexity-router` and `token-compression` were added in v0.5.0; `grill-with-docs` was added in v0.6.0 M1; `prototype` is being added in v0.6.0 M2.

There is no native skill-authoring procedure. When a new skill is needed, the author improvises the structure (frontmatter shape, SKILL.md layout, when to add reference files, when to add scripts, how to write the description so Claude routes to it correctly). The plugin's own [`skill-developer`] guidance and `gstack:/skillify` exist in adjacent ecosystems but neither is bundled with this plugin.

[`mattpocock/skills/skills/productivity/write-a-skill`](https://github.com/mattpocock/skills/tree/main/skills/productivity/write-a-skill) ships a single 3KB SKILL.md with a tight, opinionated procedure:

1. **Gather requirements** — task/domain, use cases, executable scripts vs instructions, reference materials
2. **Draft the skill** — SKILL.md with concise instructions; additional files if content > 500 lines; utility scripts if deterministic
3. **Review with user** — does it cover use cases, anything missing, sections that need more/less detail
4. **Skill structure** — `SKILL.md` (required), `REFERENCE.md`/`EXAMPLES.md`/`scripts/` (optional)
5. **SKILL.md template** — tight YAML frontmatter + Quick start + Workflows + Advanced features
6. **Description requirements** — 1024 char max, third person, "what it does. Use when [triggers]" pattern
7. **When to add scripts** vs **when to split files** decision rules
8. **Review checklist** — 6 explicit pre-publish checks

**Question:** how do we give the next person who adds a skill to this plugin (or to any aa-ma-forge consumer) a canonical authoring procedure — without inventing one ourselves and without adding heavy machinery for what is fundamentally a 100-line authoring task?

## Decision Drivers

- **Meta-tooling completeness** — skills are how the plugin extends itself. The plugin should ship guidance for adding new skills.
- **Lightweight default** — write-a-skill is a single 3KB file; minimal cognitive overhead at adoption time.
- **Pattern-source for skill review** — agents reviewing this plugin's existing 14 skills (or a consumer's new skill) need a canonical authoring rubric to evaluate against.
- **Single source of truth on disk** — same as ADR-0002 / ADR-0003: install.sh symlinks plugin skills.
- **Authoring guidance is genuinely cross-cutting** — `aa-ma-plan` Phase 4 (writing plans), `aa-ma-execution` (executing plans), and any future skill addition all benefit from a canonical "how do you write a skill" reference.

## Considered Options

1. **Rely on `document-skills:skill-creator`** — Anthropic ships a skill-creator skill in the document-skills marketplace; reference it instead of forking.
2. **Reference gstack `/skillify`** — gstack ecosystem has a skillify command; reference it instead of forking.
3. **Write our own** — author `claude-code/skills/write-a-skill/` from scratch with aa-ma-forge-specific guidance.
4. **Fork mattpocock write-a-skill (chosen)** — Lift the 3KB SKILL.md into `claude-code/skills/write-a-skill/` with provenance comment.
5. **Skip** — no canonical authoring procedure; let authors improvise.

## Decision Outcome

**Chosen:** Option 4 — Fork mattpocock write-a-skill.

**Rationale:**

- Option 1 (`document-skills:skill-creator`) is in a separate marketplace plugin; not all aa-ma-forge consumers have it installed. Same install-asymmetry risk as ADR-0002 / ADR-0003 reference-upstream variants.
- Option 2 (`gstack /skillify`) is ad-hoc to the gstack ecosystem and not packaged for general distribution; also a different command-style abstraction (slash command, not Skill()).
- Option 3 (write our own) reinvents a battle-tested 3KB single-file skill for negligible customisation gain. The opinionated rules in mattpocock's version (1024-char description, "Use when" trigger phrasing, 100-line SKILL.md cap, when-to-split-files heuristics) are sound and we have nothing to add.
- Option 5 (skip) lets authoring drift continue; future skills get inconsistent shapes and descriptions.
- Option 4 captures the canonical procedure with the same fork-with-provenance pattern established in ADR-0002 and ADR-0003.

## Pros and Cons of the Options

### Option 4: Fork mattpocock write-a-skill (chosen)

- ✅ Zero install dependency — install.sh auto-discovers
- ✅ 3KB single-file skill — minimal drift surface
- ✅ Establishes a canonical "Use when" description pattern visible across all aa-ma-forge skills
- ✅ Rules in the upstream skill (100-line SKILL.md, when-to-split, when-to-script) are exactly what aa-ma-forge needs
- ✅ Pattern-source for agent-driven review of existing 14 skills (could surface inconsistencies for future polish)
- ❌ Drift cost: 1 file (much smaller than ADR-0002's 3 or ADR-0003's 3)

### Option 1: Rely on document-skills:skill-creator

- ✅ Maintained by Anthropic
- ❌ Lives in a separate marketplace plugin; not bundled
- ❌ Consumers without document-skills get a silent missing-Skill() failure

### Option 2: Reference gstack /skillify

- ✅ Familiar to gstack users
- ❌ Slash command, not Skill — different invocation pattern from rest of plugin
- ❌ Bound to gstack ecosystem; not packaged for redistribution

### Option 3: Write our own

- ✅ Could embed aa-ma-forge-specific patterns (commit signatures, AA-MA file references)
- ❌ Reinvents a tight 3KB artefact for marginal value
- ❌ Maintenance cost forever

### Option 5: Skip

- ✅ Zero work
- ❌ Future skills shape-drift; no canonical description format; no SKILL.md size discipline

## Sub-Decisions

| ID | Sub-decision | Rationale |
|----|-------|---|
| **D1** | Fork-not-reference | Same install-asymmetry concern as ADR-0002 / ADR-0003 |
| **D2** | Single SKILL.md (no LOGIC/UI/REFERENCE companion files) | Upstream is single-file; the skill itself counsels "split when SKILL.md exceeds 100 lines" — current SKILL.md is 117 lines and still single-file in upstream, so we ship as-is |
| **D3** | Provenance comment matches ADR-0002 / ADR-0003 format | Cross-skill consistency; one pattern for "here's a forked skill" |
| **D4** | No engineering-standards.md cross-reference (unlike ADR-0003) | write-a-skill is meta-tooling — it doesn't operationalise a doctrine flag, it just provides authoring guidance. SOFT pointer from CLAUDE.md / foundations.md is sufficient. |
| **D5** | Description-format guidance in upstream (1024 char, "Use when" pattern) does NOT retro-edit existing aa-ma-forge skill descriptions | Out of scope for M2 — establishes the pattern going forward. Agent-driven review of existing 14 skills against these rules is a future optional pass. |

## Consequences

**Positive:**
- New skill authors (human or agent) have a canonical procedure: gather → draft → review.
- Description format is anchored ("what it does. Use when [triggers]"); future skills route correctly because their descriptions tell Claude when to invoke them.
- 100-line SKILL.md cap + when-to-split rules give a cheap discipline against monolithic SKILL.md files.
- Skill(write-a-skill) becomes self-bootstrapping — Claude can invoke it when the user asks "create a new skill".

**Negative:**
- 1 file of drift exposure (smallest of the 3 forks in this plan).
- Existing aa-ma-forge skill descriptions weren't authored under these rules; some may be inconsistent with the new pattern. A retro audit is possible but out of scope.

**Neutral:**
- write-a-skill is purely additive — no existing artefact references an "authoring framework" that this skill replaces.

## Implementation Notes

**Files added:**

| Path | Source |
|------|--------|
| `claude-code/skills/write-a-skill/SKILL.md` | Forked from upstream + provenance comment (M2.2; transcription typo "forks"→"forms" caught and fixed by per-fork diff verification) |
| `tests/skills/test_write_a_skill_frontmatter.py` | New — frontmatter assertion test (M2.8) |

**Files modified:**

| Path | Change |
|------|--------|
| `CLAUDE.md` | Skill list 14 → 16 (M2.6, gitignored) |
| `docs/spec/claude-code-foundations.md` | Skill table extended with write-a-skill row + heading update (M2.6) |
| `SECURITY.md` | Skill count line 14 → 16 with write-a-skill alphabetised at end (M2.7) |
| `docs/adr/INDEX.md` | This ADR registered as row 4 |

**Provenance verification at fork time:**
- Upstream URL: https://github.com/mattpocock/skills (68715 stars, default_branch=main, fetched 2026-05-10T14:55:45Z)
- MD5 verification (canonical, byte-for-byte match modulo provenance comment):
  - `SKILL.md` — `492ef034b4fc9e497cc69b8fed78a742`
- Transcription typo caught at fork time: line 79 of the good-example block was initially mis-typed as "PDFs, forks" (should be "PDFs, forms"). Per-fork diff verification surfaced the regression immediately and it was fixed inline before commit (see M2.2 Result Log).

**Status transition:** `Implemented` once Tasks 2.2, 2.8 are COMPLETE and M2 HARD gate (Task 2.10) closes.

## References

- AA-MA plan (skill-ecosystem-integration v1.2): `.claude/dev/active/skill-ecosystem-integration/`
- Upstream skill: https://github.com/mattpocock/skills/tree/main/skills/productivity/write-a-skill
- ADR-0001 (engineering standards architecture): `docs/adr/0001-engineering-standards-architecture.md`
- ADR-0002 (grill-with-docs adoption — sibling fork pattern): `docs/adr/0002-grill-with-docs-adoption.md`
- ADR-0003 (prototype adoption — sibling fork pattern): `docs/adr/0003-prototype-adoption.md`
- Lessons learned referenced during planning: `docs/lessons.md` L-001 (External URL First Principle)
