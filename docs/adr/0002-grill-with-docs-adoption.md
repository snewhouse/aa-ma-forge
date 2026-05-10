# 0002. Adopt `grill-with-docs` from mattpocock/skills and wire into /aa-ma-plan Phase 1.3

**Status:** Implemented (2026-05-10)
**Date:** 2026-05-10
**Deciders:** Stephen Newhouse, Claude (planning + execution sessions)
**Tags:** `workflow`, `aa-ma`, `skills`, `release-v0.6.0`, `external-fork`

## Context and Problem Statement

The aa-ma-forge plugin has its own `/grill-me` command (`claude-code/commands/grill-me.md`, 42 lines) — a structured interview protocol used in `/aa-ma-plan` Phase 1.3 to surface unresolved assumptions before plan generation. It is a derivative extension of the upstream short-form skill at `mattpocock/skills/skills/productivity/grill-me` (frontmatter + 4 lines).

A more capable sibling skill exists upstream: [`mattpocock/skills/skills/engineering/grill-with-docs`](https://github.com/mattpocock/skills/tree/main/skills/engineering/grill-with-docs) — a 3-file skill (SKILL.md + CONTEXT-FORMAT.md + ADR-FORMAT.md) that goes beyond the simple-interview protocol to:

- **Challenge against the existing glossary** (`CONTEXT.md`) — flag terms used inconsistently with the project's lexicon
- **Sharpen fuzzy language** by proposing precise canonical terms with cross-references to existing docs
- **Update `CONTEXT.md` inline** as terms resolve (lazy-create if absent)
- **Offer ADRs sparingly** using a three-test rule (hard-to-reverse, surprising-without-context, real-trade-off) and lazy-create `docs/adr/` if absent

aa-ma-forge has been accumulating `docs/adr/` records since v0.5.0 (ADR-0001 shipped) and is on a trajectory toward more domain-rich planning. The simple `/grill-me` protocol does not engage with this surface. **Question:** how do we adopt the richer `grill-with-docs` skill without breaking the existing `/grill-me` workflow, without forcing it on greenfield projects, and without creating drift between two divergent grill protocols?

## Decision Drivers

- **Strict additivity** — existing `/grill-me` and v0.5.0 Phase 1.3 behaviour must remain available unchanged for any project that lacks `CONTEXT.md` or `docs/adr/`. Greenfield users see zero behaviour change.
- **Single source of truth on disk** — install.sh symlinks plugin skills into `~/.claude/skills/`. We must ship a copy that install.sh can deploy unambiguously. Referencing an upstream that consumers may not have installed is fragile.
- **Minimal install.sh diff** — `scripts/install.sh:266` already auto-discovers all `claude-code/skills/*/` directories. Forking just adds a directory; no installer change required.
- **Drift surface awareness** — every fork is a drift point. We must accept ~3 small files of drift cost in exchange for guaranteed availability.
- **Project-state aware default** — auto-detect `CONTEXT.md` / `docs/adr/` presence to decide which protocol applies. Forcing one or the other globally would either break greenfield projects (force `with-docs`) or under-serve mature projects (force `simple`).
- **Override mechanism** — users must be able to force a specific mode via flag or env var without modifying the command file (testability + ad-hoc workflow flexibility).
- **Testability** — the resolver logic must be unit-testable with controlled project states (`mktemp -d`-style isolation), not just covered by manual smoke runs.

## Considered Options

1. **Reference upstream — no fork** — Phase 1.3 invokes `Skill(grill-with-docs)` and relies on the consumer having installed mattpocock/skills separately.
2. **Replace /grill-me entirely** — Drop the existing `/grill-me` command + v0.5.0 prose; route Phase 1.3 unconditionally through grill-with-docs.
3. **Fork + Phase 1.3 wire (chosen)** — Lift the 3 upstream files into `claude-code/skills/grill-with-docs/`, leave `/grill-me` unchanged, add conditional dispatch in Phase 1.3 via a new `--grill-mode` flag (default `auto`).
4. **Skip — do not adopt** — Decide grill-with-docs is out of scope; keep only `/grill-me`.

## Decision Outcome

**Chosen:** Option 3 — Fork + Phase 1.3 wire.

**Rationale:**

- Option 1 would silently fail for any user who has not separately installed mattpocock/skills. install.sh in this plugin only inventories the plugin's own `claude-code/skills/` tree; it cannot deploy a sibling project's skills. A reference would violate the "code is truth" principle by depending on out-of-tree state.
- Option 2 would break the strict-additivity driver. The existing `/grill-me` command is referenced (verbatim wording) inside Phase 1.3's `simple` branch — preserving it is what gives greenfield projects a zero-behaviour-change upgrade path.
- Option 4 leaves the existing `/grill-me` short-protocol as the only grilling mechanism, missing the value of CONTEXT.md/ADR-aware grilling for the growing class of mature projects with `docs/adr/`.
- Option 3 captures the upstream value, preserves backward compat, isolates the new functionality behind a flag with sensible default, and keeps install.sh free of changes.

## Pros and Cons of the Options

### Option 3: Fork + Phase 1.3 wire (chosen)

- ✅ install.sh requires zero changes — `for d in claude-code/skills/*/` auto-discovers the new directory
- ✅ Greenfield projects unaffected — auto-detection falls through to `simple` → existing `/grill-me` protocol
- ✅ Mature projects (`CONTEXT.md` or `docs/adr/`) get the richer skill automatically
- ✅ `--grill-mode={auto,with-docs,simple,skip}` + `AA_MA_GRILL_MODE` env var give explicit override paths for tests, CI, and ad-hoc workflows
- ✅ Standalone resolver script `scripts/grill-mode-resolver.sh` enables unit-test coverage of all 8 branches via `mktemp -d`
- ✅ Each forked file carries an explicit provenance comment so future readers see the upstream source and fork date
- ❌ ~3 files of drift cost — upstream changes won't auto-propagate; mitigated by infrequent upstream churn (3 files, stable since first commit)
- ❌ Resolver logic exists in two places (markdown inline + standalone script) — mitigated by parity rule documented in both files

### Option 1: Reference upstream — no fork

- ✅ Zero file duplication; upstream changes propagate
- ❌ Silent failure mode: consumers without mattpocock/skills installed get an unresolved Skill() call
- ❌ install.sh cannot deploy out-of-tree skills
- ❌ Violates "code is truth" — depends on global filesystem state outside the plugin

### Option 2: Replace /grill-me entirely

- ✅ Single grill protocol; lower mental overhead
- ❌ Breaks v0.5.0 backward compatibility for greenfield projects
- ❌ The existing `/grill-me` command (42-line derivative) carries protocol numbering, constraint list, and "Resolve don't just surface" rule that grill-with-docs does not have
- ❌ Forces all projects into a CONTEXT.md/ADR workflow regardless of fit

### Option 4: Skip — do not adopt

- ✅ Zero work, zero drift surface
- ❌ Forfeits the value of glossary-aware grilling for the growing population of projects with `docs/adr/`
- ❌ aa-ma-forge itself (this repo) would not benefit from its own ADR-aware grilling skill

## Sub-Decisions

| ID | Sub-decision | Rationale |
|----|-------|---|
| **D1** | Fork-not-reference (above) | install.sh cannot deploy out-of-tree skills; reference would silently fail for some consumers |
| **D2** | Conditional dispatch with `auto` default rather than always-with-docs | Greenfield projects must retain v0.5.0 behaviour; auto-detect ensures progressive enhancement |
| **D3** | `--grill-mode={auto,with-docs,simple,skip}` flag + `AA_MA_GRILL_MODE` env var (CLI > env > default) | Standard precedence pattern matching `--skip-lessons`/`AA_MA_SKIP_LESSONS` in Phase 1.5 |
| **D4** | Standalone resolver at `scripts/grill-mode-resolver.sh` + inline equivalent in markdown | Standalone enables subprocess-based testing; inline guarantees portability across user projects (no install.sh change) |
| **D5** | Provenance comment at top of each forked file (`<!-- Forked from URL on YYYY-MM-DD — aa-ma-forge vN.N.N -->`) | Future-reader signal: "this is forked, not original" — answers "why is this here?" without reading git history |
| **D6** | Unreadable `docs/adr/` falls back to `simple` with stderr WARN (not an error) | Permissions misconfigurations (e.g. NFS, container mounts) should not break planning; degrade gracefully |
| **D7** | Invalid `--grill-mode` value exits 2 with stderr ERROR but emits `skip` to stdout | Caller can honour exit code OR rely on safe-default stdout; matches "fail loudly but degrade gracefully" pattern |

## Consequences

**Positive:**
- Mature projects (with CONTEXT.md or docs/adr/) get glossary-aware grilling automatically — this includes aa-ma-forge itself.
- New `--grill-mode` flag composes with existing `--skip-lessons` flag for fast-iteration and CI use cases.
- Resolver script is a reusable testing target — Task 1.7a covers all 8 branches with `mktemp -d` isolation, raising the "29% paths tested" baseline (from plan-eng-review) to >80% for this surface.
- ADR-0002 is itself a demonstration of the three-test rule: hard-to-reverse (cross-refs everywhere), surprising-without-context ("why is mattpocock's skill in our tree?"), real-trade-off (alternatives existed).

**Negative:**
- ~3 files of drift exposure. Mitigated by: (a) upstream stability (the skill has not changed in months), (b) provenance comment makes the relationship explicit, (c) Task 1.2 verification command in `provenance.log` enables a future drift check.
- Resolver logic in two places (inline + standalone script). Mitigated by parity rule documented in both files; drift is detectable via Task 1.7a unit tests if the standalone script behaviour diverges from documented intent.
- Skill count touchpoint: 13 → 14, hitting `SECURITY.md`, `CLAUDE.md`, and any prose with hardcoded counts. Handled by `Critical-Path: doc-count-drift` on Tasks 1.5 and 1.6.

**Neutral:**
- The existing `/grill-me` command remains exactly as it was — no edits to `claude-code/commands/grill-me.md`. The `simple` branch in Phase 1.3 just preserves its prose verbatim.

## Implementation Notes

**Files added:**

| Path | Source |
|------|--------|
| `claude-code/skills/grill-with-docs/SKILL.md` | Forked from upstream + provenance comment |
| `claude-code/skills/grill-with-docs/CONTEXT-FORMAT.md` | Forked from upstream + provenance comment |
| `claude-code/skills/grill-with-docs/ADR-FORMAT.md` | Forked from upstream + provenance comment |
| `scripts/grill-mode-resolver.sh` | New — canonical resolver implementation, executable, 8-branch coverage |
| `tests/skills/test_grill_with_docs_frontmatter.py` | New — frontmatter assertion test (Task 1.7) |
| `tests/commands/test_grill_mode_resolver.py` | New — 8-branch resolver coverage test (Task 1.7a) |

**Files modified:**

| Path | Change |
|------|--------|
| `claude-code/commands/aa-ma-plan.md` | Phase 1.3 expanded from 4-line single-protocol to ~75-line mode-aware dispatcher |
| `claude-code/rules/aa-ma.md` | Phase 1.3 reference updated to mention grill-with-docs (Task 1.5) |
| `CLAUDE.md` | Skill list 13 → 14 (Task 1.5) |
| `SECURITY.md` | Skill count line 13 → 14 with grill-with-docs alphabetised (Task 1.6) |
| `docs/adr/INDEX.md` | This ADR registered |

**Provenance verification at fork time:**
- Upstream URL: https://github.com/mattpocock/skills (68666 stars, default_branch=main, fetched 2026-05-10T14:11:44Z)
- MD5 verification: each forked file matches upstream byte-for-byte (only addition: provenance comment line)
  - `SKILL.md` — `5ad241e49d5ffcd394eeff3a5ca46953`
  - `CONTEXT-FORMAT.md` — `57e7e26a1a46884f8f952c67fb233af2`
  - `ADR-FORMAT.md` — `bb327bab674f400796f64b6e2ef5850c`

**Status transition:** ADR is `Implemented` once Tasks 1.2–1.8 are COMPLETE and M1 HARD gate (Task 1.9) closes.

## References

- AA-MA plan (skill-ecosystem-integration v1.2): `.claude/dev/active/skill-ecosystem-integration/`
- Upstream skill: https://github.com/mattpocock/skills/tree/main/skills/engineering/grill-with-docs
- Upstream repo metadata: https://api.github.com/repos/mattpocock/skills (stars: 68666, updated 2026-05-10)
- Lessons learned that informed planning: `docs/lessons.md` L-001 (External URL First Principle)
- ADR-0001 (engineering standards architecture): `docs/adr/0001-engineering-standards-architecture.md`
- Resolver script: `scripts/grill-mode-resolver.sh`
- Phase 1.3 dispatcher: `claude-code/commands/aa-ma-plan.md` Step 1.3
