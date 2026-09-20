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

### Fork lifecycle (added 2026-09-20, mattpocock-trio-adoption grill)

**Re-fork**:
A Fork applied to an existing fork directory: content replaced from Upstream, the provenance line's date and the ADR's recorded MD5s updated, the original ADR amended (no new ADR number). Same mechanical/atomic contract as Fork.
_Avoid_: "sync"/"re-sync" (implies bidirectional), "update" (too generic), "refresh".

**Drift**:
A fork state: the Upstream file's MD5 no longer matches the MD5 recorded in the fork's ADR. Detected, not judged — Drift may be benign; the decision is Re-fork, keep as Derived, or retire.
_Avoid_: "stale" (judgemental; reserve for docs that are wrong), "out of date".

**Orphan**:
A fork state: the Upstream path no longer exists (deleted or renamed). Forces a decision: Re-fork from the successor path, keep as **Derived** (`DERIVED-FROM-UPSTREAM`), or retire. An Orphan cannot Drift because there is nothing to compare against.
_Avoid_: "abandoned" (implies neglect on our side), "dead".

**Adaptation**:
A concept borrowed from an Upstream with **no** files forked: we write our own files and an ADR; attribution reads "concept adapted from". Sits beside Adoption, not inside it — an Adaptation has no Fork, no provenance comment, no MD5, and cannot Drift or be Orphaned.
_Avoid_: "port", "inspired by" (too weak for an ADR-backed decision), "adopt" (reserved for Fork-wrapping Adoption).

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

### Plan artefact views (added 2026-09-11, plan-architecture-views grill)

**Architecture View**:
Plan element #13 of the AA-MA Planning Standard: the mermaid diagrams a plan carries so a cold agent can see the mechanism before reading the steps. Lives in `plan.md` §13 only; `reference.md` carries a one-line pointer. Required when `Audit-Profile` ∈ {full, code-only, infra}; absent otherwise via a canonical `Diagram-Waiver:` value.
_Avoid_: "diagrams" unqualified (say which **View**), "architecture doc" (there is no separate file).

**View**:
One named mermaid block inside an **Architecture View**. Canonical kinds: **Component view** (what files/modules/hooks the plan touches and their dependencies — mandated), **Flow view** (the critical execution path being added or changed — mandated when `Critical-Path:` is present), **Data/State view** (only when the plan introduces a schema or state machine), **Milestone graph** (derived mechanically from `tasks.md` `Dependencies:` — never hand-authored).
_Avoid_: "picture", "chart".

**Contract block**:
A fenced code block that pins the interface a milestone will produce or consume: file paths, function/CLI signatures, exit codes, field grammar. Required per code-touching milestone. Its purpose is cold-executability, not illustration — an implementer must not need to guess a signature.
_Avoid_: "snippet", "example code" (those are illustrative, not binding), "implementation draft".

**Render**:
A derived, disposable HTML file produced from a markdown source (plan, ADR, spec doc) by the exporter. Never hand-edited, never committed; regenerated on demand. Markdown is the only source of truth.
_Avoid_: "HTML version" (implies a peer source), "export" as a noun (it is the verb).

**Share**:
Publishing a **Render** as a private claude.ai Artifact link for someone outside the repo. A **Share** is a snapshot; it does not track later markdown edits.
_Avoid_: "publish" (overloaded with release), "site".

**Diagram-Waiver**:
Canonical field on a plan (parallel to `TDD-Waiver:`) stating why no **Architecture View** is required. Accepted values are enumerated in the spec; novel values are rejected by `Skill(plan-verification)`.

## Relationships

- A **Repo** has one or more **Skills** (and possibly other artifacts).
- A **Skill** in a **Repo** can be a **Candidate** for **Adoption**.
- An **Adoption** is composed of: one **Fork** + one ADR + frontmatter test(s) + cross-references + skill-count update.
- A **Candidate** has exactly one **Status** at any given time; the **Status** can transition (e.g., `PROPOSED-M3+` → `ADOPTED-M3` after a future plan).
- A **Catalog** can index multiple **Repos**; an **Ecosystem** wraps one **Repo** plus its adjacent infrastructure.
- An **Upstream** is the producer of a **Repo**.
- A **Plan** carries at most one **Architecture View**, composed of one or more **Views**; a **Milestone** carries zero or more **Contract blocks**.
- A **Render** is derived from exactly one markdown source; a **Share** is a snapshot of one **Render**.
- A **Fork** is in exactly one lifecycle state at a time: current, **Drift**, or **Orphan**; a **Re-fork** returns it to current. An **Adaptation** has no lifecycle state.

## Example dialogue

> **Plan author:** "Should we adopt the gstack `/freeze` command?"
> **Reviewer:** "It's a **Candidate**, status currently **PROPOSED-M3+ MEDIUM** per `docs/research/skill-ecosystem-audit.md`. To **Adopt** it, you'd **Fork** the upstream gstack file into `claude-code/skills/freeze/`, write an ADR, add a frontmatter test, update the skill count. The **Repo** (`garrytan/gstack`) is the source; the broader **Ecosystem** also includes a Chrome extension we wouldn't fork."
> **Plan author:** "What about gsd's ROADMAP.md template?"
> **Reviewer:** "Not a **Candidate**. The audit's DO-NOT-BORROW list excludes ROADMAP.md as a root artifact because AA-MA already has `[task]-plan.md` and the lexicon would fragment. gsd is **Inspiration only** — a pattern source, not a Repo we Fork from."

## Flagged ambiguities

- **"vendor"** was used informally during planning to mean both (a) Adoption and (b) Upstream. Resolved: split into `Fork` (mechanical), `Adoption` (workflow), `Upstream` (producer). `vendor` is now banned vocabulary in plans.
- **"the catalog"** vs **"the repo"** was the failure mode that produced L-001 (External URL First Principle): a research agent confused Anthropic's `agent-skills` Catalog with mattpocock's Repo. Resolved: a Catalog is not a Repo; always name the Repo explicitly when fetching ground truth.
- **"M3+ candidate"** is a tagged Status, not a separate noun. The audit doc uses "M3+ candidates" as the heading of Section D — that's the *list of Candidates with Status PROPOSED-M3+*.

- **"sync" / "re-sync"** was used in ADR-0011 to mean bringing the `prototype` fork current. Resolved: that is a **Re-fork**; "sync" is banned (AA-MA already uses "sync" for artifact discipline — `Sync Discipline` in `rules/aa-ma.md`).
- **"adopt wayfinder"** was ambiguous between forking files and borrowing the concept. Resolved: charting is an **Adaptation**, not an Adoption.

## Provenance

Extended 2026-09-20 during Phase 1.3 (`grill-with-docs`) of `mattpocock-trio-adoption`: Re-fork / Drift / Orphan / Adaptation.

Extended 2026-09-11 during Phase 1.3 (`grill-with-docs`) of `plan-architecture-views`: Architecture View / View / Contract block / Render / Share / Diagram-Waiver.

Created 2026-05-10 during M3.3 of skill-ecosystem-integration v1.2 — invocation of `Skill(grill-with-docs)` (M1 deliverable, see ADR-0002) against `docs/research/skill-ecosystem-audit.md`. Crystallised the 3 fuzzy clusters from the M3.3 acceptance criteria: ecosystem/catalog/repo, adoption/vendor/fork, candidate/proposal.
