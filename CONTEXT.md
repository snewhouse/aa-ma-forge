# aa-ma-forge

The plugin's domain is *Claude Code skill ecosystems and plan-driven adoption of third-party skills*. This file captures the canonical vocabulary used in plans, ADRs, and research notes.

Implementation-level vocabulary (Plugin / Skill / Command / Rule / Agent / Hook) is canonical in [`docs/spec/claude-code-foundations.md`](docs/spec/claude-code-foundations.md). This file does not duplicate those — it captures the *plan-authoring* terms that emerged during skill-ecosystem-integration v1.2 (M3.3 grill-with-docs glossary check, ADR-0002).

## Language

### Source identity

**Repo**:
A specific git repository at a canonical URL (e.g., `https://github.com/mattpocock/skills`). Repos are immutable identifiers; their content shifts over time.
_Avoid_: "the matt repo" (use "mattpocock/skills"), "upstream" without qualification.

**Catalog**:
A curated published list of items derivable from a Repo. May be a subset, superset, or rearrangement of the Repo's contents (e.g., "Anthropic's agent-skills catalog" curates from multiple repos). Catalogs and Repos are not interchangeable — a Catalog can outlast a Repo or precede a Repo's creation.
_Avoid_: "registry" (overloaded with package-registry semantics), "marketplace".

**Ecosystem**:
The broader artifact landscape around a Repo, including the Repo plus supporting tools, integrations, binaries, browser extensions, and adjacent infrastructure (e.g., "the gstack ecosystem" includes 34 commands + Chrome extension + compiled binaries; "the mattpocock ecosystem" is essentially just the Repo).
_Avoid_: "stack" when meaning the broader landscape (use "ecosystem"); "platform" (overloaded).

### Adoption verbs

**Fork**:
The file-level operation of lifting upstream files into our tree with a provenance comment (`<!-- Forked from URL on YYYY-MM-DD — aa-ma-forge vN.N.N -->`) at the top. Mechanical and atomic; one task per fork.
_Avoid_: "vendor" (ambiguous: dependency vendoring vs producer entity), "import" (overloaded with code imports), "copy" (lacks the provenance contract).

**Adoption**:
The milestone-level workflow that wraps a Fork: fork + ADR + frontmatter test + cross-references + skill-count update. An Adoption produces a published artifact accountable for in `docs/research/skill-ecosystem-audit.md`.
_Avoid_: "integration" (overloaded with system integrations), "import" (same as Fork avoid).

**Upstream**:
The producer of a Repo from which we Fork. Always a specific organization or person (e.g., "the upstream is mattpocock", "the gstack upstream is garrytan").
_Avoid_: "the vendor" (ambiguous), "the source" (acceptable but less precise).

### Evaluation states

**Candidate**:
A Skill (or other artifact) under consideration for Adoption. Subject of evaluation in `docs/research/skill-ecosystem-audit.md`. Has exactly one Status from the canonical enum below.
_Avoid_: "potential adoption" (verbose), "option" (too generic).

**Proposal**:
The documented case for adopting a Candidate — typically the audit-doc row + a future ADR. "Proposed" is also the adjective form of the status tag (`Status: PROPOSED-M3+`).
_Avoid_: using "proposal" for the Candidate itself; the Proposal is the *case for*, not the Candidate.

**Status enum** (canonical values for audit-doc rows):
- `ADOPTED-M<N>` — already shipped in milestone N
- `PROPOSED-M3+` — recommended for future plan; priority HIGH/MEDIUM/LOW
- `DEFERRED-DIFF` — must be diffed against existing aa-ma-forge artefact before deciding
- `DEFERRED-CONFLICT` — has a likely terminology or behavior conflict; needs verify-plan
- `SUPERSEDED-BY-EXISTING` — already covered by an existing aa-ma-forge skill (do not re-fork)
- `DERIVED-FROM-UPSTREAM` — aa-ma-forge already has a derivative extension (do not re-fork)
- `EXCLUDED-DEPRECATED` — upstream marked deprecated
- `EXCLUDED-IN-PROGRESS` — upstream not stable yet
- `EXCLUDED-PERSONAL` — upstream is producer-specific (not portable)
- `EXCLUDED-CONFLICT` — explicit conflict with aa-ma-forge release pipeline (e.g., gstack `/ship`)

## Relationships

- A **Repo** has one or more **Skills** (and possibly other artifacts).
- A **Skill** in a **Repo** can be a **Candidate** for **Adoption**.
- An **Adoption** is composed of: one **Fork** + one ADR + frontmatter test(s) + cross-references + skill-count update.
- A **Candidate** has exactly one **Status** at any given time; the **Status** can transition (e.g., `PROPOSED-M3+` → `ADOPTED-M3` after a future plan).
- A **Catalog** can index multiple **Repos**; an **Ecosystem** wraps one **Repo** plus its adjacent infrastructure.
- An **Upstream** is the producer of a **Repo**.

## Example dialogue

> **Plan author:** "Should we adopt the gstack `/freeze` command?"
> **Reviewer:** "It's a **Candidate**, status currently **PROPOSED-M3+ MEDIUM** per `docs/research/skill-ecosystem-audit.md`. To **Adopt** it, you'd **Fork** the upstream gstack file into `claude-code/skills/freeze/`, write an ADR, add a frontmatter test, update the skill count. The **Repo** (`garrytan/gstack`) is the source; the broader **Ecosystem** also includes a Chrome extension we wouldn't fork."
> **Plan author:** "What about gsd's ROADMAP.md template?"
> **Reviewer:** "Not a **Candidate**. The audit's DO-NOT-BORROW list excludes ROADMAP.md as a root artifact because AA-MA already has `[task]-plan.md` and the lexicon would fragment. gsd is **Inspiration only** — a pattern source, not a Repo we Fork from."

## Flagged ambiguities

- **"vendor"** was used informally during planning to mean both (a) Adoption and (b) Upstream. Resolved: split into `Fork` (mechanical), `Adoption` (workflow), `Upstream` (producer). `vendor` is now banned vocabulary in plans.
- **"the catalog"** vs **"the repo"** was the failure mode that produced L-001 (External URL First Principle): a research agent confused Anthropic's `agent-skills` Catalog with mattpocock's Repo. Resolved: a Catalog is not a Repo; always name the Repo explicitly when fetching ground truth.
- **"M3+ candidate"** is a tagged Status, not a separate noun. The audit doc uses "M3+ candidates" as the heading of Section D — that's the *list of Candidates with Status PROPOSED-M3+*.

## Provenance

Created 2026-05-10 during M3.3 of skill-ecosystem-integration v1.2 — invocation of `Skill(grill-with-docs)` (M1 deliverable, see ADR-0002) against `docs/research/skill-ecosystem-audit.md`. Crystallised the 3 fuzzy clusters from the M3.3 acceptance criteria: ecosystem/catalog/repo, adoption/vendor/fork, candidate/proposal.
