# 0003. Adopt `prototype` from mattpocock/skills (LOGIC + UI branches)

**Status:** Implemented (2026-05-10)
**Date:** 2026-05-10
**Deciders:** Stephen Newhouse, Claude (planning + execution sessions)
**Tags:** `workflow`, `aa-ma`, `skills`, `release-v0.6.0`, `external-fork`, `engineering-standards-theme-1`

## Context and Problem Statement

ADR-0001 introduced the [Engineering Standards](../../claude-code/rules/engineering-standards.md) doctrine, which includes Theme 1 ("Verification & Truth") with a per-task `Prototype-Required:` field. Plans that mark a task `Prototype-Required: YES` declare that the change carries enough design uncertainty that a throwaway proof-of-concept must be built and a `[ts] PROTOTYPE — <verdict>` provenance entry written before milestone close.

The doctrine declares **when** to prototype but is silent on **how**. An agent confronted with `Prototype-Required: YES` has no canonical procedure — it must improvise the prototype shape, scope, and lifecycle. Improvisation is fine for trivial cases but expensive when the question being answered is structurally complex (a state machine vs. a UI layout — radically different artifacts).

[`mattpocock/skills/skills/engineering/prototype`](https://github.com/mattpocock/skills/tree/main/skills/engineering/prototype) ships a battle-tested two-branch protocol:

- **LOGIC branch** — interactive terminal application that drives a state model by hand. Right shape when the question is "does this state machine handle case X then Y?"
- **UI branch** — multiple structurally different UI variants on a single route, switchable via `?variant=` URL search param + floating bottom bar. Right shape when the question is "what should this page look like?"

Both branches share six common rules (throwaway, one-command-runnable, no persistence, no polish, surface-the-state, delete-or-absorb).

**Question:** how do we operationalise the existing `Prototype-Required:` flag so agents have a canonical "how" — without writing the procedure ourselves and without taking on a cross-language UI-framework dependency we can't sustain?

## Decision Drivers

- **Operationalise existing doctrine** — Theme 1 declares `Prototype-Required:` exists; ADR-0003 must answer "given this flag, what does the agent actually do?"
- **Cross-language fit** — aa-ma-forge has Python (codemem), Bash (hooks/installer), and may grow TypeScript / Java / Go consumers. The skill must work for at least the LOGIC case across languages; the UI case may be more constrained.
- **No reinventing the wheel** — mattpocock's prototype skill is well-tested (68k repo stars, mature) and matches our needs exactly.
- **Single source of truth on disk** — same as ADR-0002: install.sh symlinks plugin skills; we cannot rely on consumers having mattpocock/skills installed.
- **Constraint disclosure** — the LOGIC branch is fully cross-language but the UI branch presupposes a web frontend (TSX, `searchParams`, `process.env.NODE_ENV`). This boundary must be documented so agents don't try to UI-prototype a backend service.
- **Strict additivity** — the existing `Prototype-Required:` enforcement (Engineering Standards Section 6.7 condition 5) must continue to work unchanged. Skill(prototype) becomes the "how" without altering the "when".
- **Drift surface awareness** — same drift cost as ADR-0002. Three small files that have been stable upstream.

## Considered Options

1. **Write our own prototype skill** — author `claude-code/skills/prototype/` with original content tailored to aa-ma-forge's languages.
2. **Reference upstream — no fork** — Theme 1 cross-reference points at `Skill(mattpocock/skills:engineering/prototype)`.
3. **Fork upstream + Theme 1 cross-reference (chosen)** — Lift the 3-file skill into `claude-code/skills/prototype/` AND extend Theme 1's `Prototype-Required:` paragraph to invoke `Skill(prototype)`.
4. **Skip — no operational guidance** — Leave `Prototype-Required:` as a flag with no associated procedure.

## Decision Outcome

**Chosen:** Option 3 — Fork + Theme 1 cross-reference.

**Rationale:**

- Option 1 (write our own) reinvents a battle-tested 3-file artefact for marginal customisation value. The two-branch dispatcher (LOGIC/UI) is the strongest design choice in the upstream skill — there is no obvious "aa-ma-forge variant" that improves on it. We would also bear the maintenance cost.
- Option 2 (reference upstream) repeats the failure mode caught by ADR-0002: install.sh cannot deploy out-of-tree skills, so the cross-reference would silently fail for any consumer without mattpocock/skills installed. Violates "code is truth".
- Option 4 (skip) leaves the `Prototype-Required:` flag a structural dead-letter — agents can satisfy it however they want, including with token-rich freeform "I prototyped this conceptually" commentary. That defeats the doctrinal intent.
- Option 3 captures the upstream value, satisfies the install.sh deployment constraint, and converts a passive flag into an active workflow.

## Pros and Cons of the Options

### Option 3: Fork + Theme 1 cross-reference (chosen)

- ✅ Theme 1 `Prototype-Required:` becomes actionable — agents have a canonical "how"
- ✅ Two-branch dispatcher (LOGIC/UI) covers both common prototype questions
- ✅ install.sh auto-discovers; zero installer change
- ✅ LOGIC branch is fully cross-language (verified during planning: SKILL.md says "Pick the language: use whatever the host project uses"; LOGIC.md shows ANSI escape examples for JS/Python; one-command runners for `pnpm`/`python`/`bun`/`Makefile`/`justfile`/`pyproject.toml`)
- ✅ Provenance comment makes the upstream lineage explicit
- ❌ UI branch is web-frontend-specific (uses TSX, `searchParams.get('variant')`, `process.env.NODE_ENV !== 'production'`); does not apply to backend services or pure data pipelines — must be explicitly documented as a constraint (handled in this ADR's Consequences and in the cross-reference text)
- ❌ Drift cost: 3 files (mitigated by upstream stability + provenance comment + per-fork diff verification at fork time, which already caught a transcription typo in M2.2)

### Option 1: Write our own prototype skill

- ✅ Custom-fitted to aa-ma-forge's languages
- ❌ Reinvents a battle-tested 3-file artefact for marginal value
- ❌ Maintenance cost shifts to us forever
- ❌ Cannot match 68k-star credibility of upstream

### Option 2: Reference upstream — no fork

- ✅ Zero file duplication
- ❌ Silent failure for consumers without mattpocock/skills installed (same defect class as ADR-0002 Option 1)

### Option 4: Skip — no operational guidance

- ✅ Zero work
- ❌ `Prototype-Required:` stays a flag with no procedure — agents satisfy it however they want
- ❌ Engineering Standards Section 6.7 condition 5 has nothing concrete to check ("PROTOTYPE — <verdict>" provenance entry) other than the verdict text itself

## Sub-Decisions

| ID | Sub-decision | Rationale |
|----|-------|---|
| **D1** | Fork-not-reference (above) | install.sh deploy semantics; reference fails silently for some consumers |
| **D2** | Theme 1 cross-reference is **SOFT** (descriptive, not enforcing) | The HARD enforcement (Section 6.7 condition 5) already exists; ADR-0003 just plugs in the procedure agents follow when the flag fires. No change to gate behaviour. |
| **D3** | Document UI-branch constraint (web-frontend only) explicitly | LOGIC fits cross-language; UI presupposes a browser-renderable surface. Without this disclosure, agents may try to UI-prototype a backend service. |
| **D4** | Provenance comment matches ADR-0002 format | Cross-skill consistency; future readers see the same "<!-- Forked from URL on date — aa-ma-forge vN.N.N -->" pattern across all forked skills. |
| **D5** | Cross-reference happens in `claude-code/rules/engineering-standards.md` Theme 1 paragraph (one-line addition) | Doctrine + procedure stay co-located; future readers of the rule see the skill they should invoke. |

## Consequences

**Positive:**
- `Prototype-Required: YES` is now operational — agents have a canonical procedure.
- LOGIC branch generalises across Python (codemem and future packages), TypeScript, Java, Go, Rust — wherever the host project has a one-command task runner.
- UI branch covers web-frontend prototyping for any consumer that builds web surfaces (current Galactic Agent UI work, future Biorelate dashboards).
- Engineering Standards Section 6.7 condition 5 ("PROTOTYPE — <verdict>" provenance evidence) gains a structured procedure to point at, rather than relying on freeform agent verdict text.
- Skill(prototype) becomes a reusable artefact for any aa-ma-forge consumer once they `scripts/install.sh`.

**Negative:**
- ~3 files of drift exposure (mitigated as in ADR-0002).
- UI branch ships TSX-flavoured pseudo-code; teams using non-React frameworks (Vue, Svelte, Angular, raw HTML) must adapt the patterns. The branch doesn't cleanly cover non-web-UI cases at all.
- Adds 2 new files (LOGIC.md, UI.md) per skill — `write-a-skill` 100-line guidance is exceeded by SKILL.md (31 lines) + LOGIC.md (80 lines) + UI.md (113 lines) = 224 lines split across files. Consistent with progressive-disclosure pattern; SKILL.md alone stays under 50 lines.

**Neutral:**
- `Prototype-Required: NO` remains the silent default. ADR-0003 only changes what happens when the flag fires.

## Implementation Notes

**Files added:**

| Path | Source |
|------|--------|
| `claude-code/skills/prototype/SKILL.md` | Forked from upstream + provenance comment (M2.1) |
| `claude-code/skills/prototype/LOGIC.md` | Forked from upstream + provenance comment (M2.1) |
| `claude-code/skills/prototype/UI.md` | Forked from upstream + provenance comment (M2.1) |
| `tests/skills/test_prototype_frontmatter.py` | New — frontmatter assertion test (M2.8) |

**Files modified:**

| Path | Change |
|------|--------|
| `claude-code/rules/engineering-standards.md` | Theme 1 `Prototype-Required: YES` paragraph extended with `Skill(prototype)` cross-reference + LOGIC-vs-UI dispatch hint (M2.5) |
| `CLAUDE.md` | Skill list 14 → 16 (M2.6, gitignored) |
| `docs/spec/claude-code-foundations.md` | Skill table extended with prototype row + heading 14 → 16 (M2.6) |
| `SECURITY.md` | Skill count line 14 → 16 with prototype alphabetised (M2.7) |
| `docs/adr/INDEX.md` | This ADR registered as row 3 |

**Provenance verification at fork time:**
- Upstream URL: https://github.com/mattpocock/skills (68715 stars, default_branch=main, fetched 2026-05-10T14:55:45Z)
- MD5 verification (canonical, byte-for-byte match modulo provenance comment):
  - `SKILL.md` — `10ace9b5d79140b25d115bb8d840106d`
  - `LOGIC.md` — `d57721452aacaa04caacd0bc7c5c2f49`
  - `UI.md` — `c1eaad6437c90d5660b2ffc9ff91ffb4`

**Status transition:** `Implemented` once Tasks 2.1, 2.5, 2.8 are COMPLETE and M2 HARD gate (Task 2.10) closes.

## References

- AA-MA plan (skill-ecosystem-integration v1.2): `.claude/dev/active/skill-ecosystem-integration/`
- Upstream skill: https://github.com/mattpocock/skills/tree/main/skills/engineering/prototype
- ADR-0001 (engineering standards architecture): `docs/adr/0001-engineering-standards-architecture.md`
- ADR-0002 (grill-with-docs adoption — companion fork): `docs/adr/0002-grill-with-docs-adoption.md`
- Engineering Standards rule (Theme 1): `claude-code/rules/engineering-standards.md`
- Lessons learned referenced during planning: `docs/lessons.md` L-001 (External URL First Principle)
