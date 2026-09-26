# Architecture Decision Records (ADRs)

This directory captures architectural decisions made for aa-ma-forge using the [MADR](https://adr.github.io/madr/) format.

## What is an ADR?

An ADR is a short document that records an architecturally significant decision: the context that made it necessary, the alternatives considered, the choice made, and the consequences accepted. Use ADRs when a decision is:

1. **Hard to reverse** — the cost of changing your mind later is meaningful
2. **Surprising without context** — a future reader will wonder "why did they do it this way?"
3. **The result of a real trade-off** — there were genuine alternatives and you picked one for specific reasons

If any of those three is missing, skip the ADR and put the decision in a comment, commit message, or `docs/plans/` design doc.

## Authoring

Copy [`TEMPLATE.md`](TEMPLATE.md) to `NNNN-short-title.md` (zero-padded, sequential). Fill it in. Add an entry to the index below.

## Index

| ID | Title | Status | Date |
|----|-------|--------|------|
| [0001](0001-engineering-standards-architecture.md) | Engineering Standards Architecture for aa-ma-plan Workflows | Implemented | 2026-05-09 |
| [0002](0002-grill-with-docs-adoption.md) | Adopt `grill-with-docs` from mattpocock/skills and wire into /aa-ma-plan Phase 1.3 | Implemented | 2026-05-10 |
| [0003](0003-prototype-adoption.md) | Adopt `prototype` from mattpocock/skills (LOGIC + UI branches) | Implemented | 2026-05-10 |
| [0004](0004-write-a-skill-adoption.md) | Adopt `write-a-skill` from mattpocock/skills | Implemented | 2026-05-10 |
| [0005](0005-post-impl-adversarial-review.md) | Post-Impl Adversarial Review (Phase 6.8 + /verify-impl) | Implemented | 2026-05-11 |
| [0006](0006-understand-codebase-adoption.md) | Adopt `understand-codebase` onboarding skill + 4 worker agents + `/understand-codebase` into the AA-MA Forge ecosystem | Implemented | 2026-05-12 |
| [0007](0007-aa-ma-tui-tracker.md) | `aa-ma-tui` — Read-Only Textual TUI + Rich Snapshot for AA-MA Task Tracking | Implemented | 2026-05-18 |
| [0008](0008-sole-dev-merge-pr-workflow.md) | `/sole-dev-merge` — PR/MR Workflow with 3-Source Security + Idempotent Auto-Merge | Implemented | 2026-05-18 |
| [0009](0009-gate-enforcement-python-ssot.md) | Gate enforcement reads the Python SSoT; bash keeps display readers only | Implemented | 2026-09-11 |
| [0010](0010-architecture-views-and-render.md) | Architecture Views (element #13), Contract blocks, mermaid lint, Artifact Share and HTML Render | Implemented | 2026-09-11 |
| [0011](0011-prototype-resync-and-planning-gate.md) | Re-sync `prototype` to upstream 1.2.3 and make the prototype decision explicit in planning | Implemented | 2026-09-20 |
| [0012](0012-research-skill-adoption.md) | Adopt `research` from mattpocock/skills and give `/aa-ma-plan` Phase 3 a file destination | Implemented | 2026-09-20 |
| [0013](0013-charting-wayfinder-lite.md) | Charting — a pre-plan decision map adapted from `wayfinder` (no issue tracker) | Proposed | 2026-09-20 |
| [0014](0014-derived-architecture-views.md) | Derived architecture views: `aa_ma` reads codemem's graph through a stdlib-sqlite3 seam | Accepted | 2026-09-24 |
| [0015](0015-diagram-as-acceptance-criterion.md) | The diagram as an acceptance criterion: a HARD §6.7 item, not a gate question | Implemented | 2026-09-25 |
| [0016](0016-living-architecture-doc.md) | The living architecture doc: generated `docs/architecture/` checked for drift in CI | Accepted | 2026-09-24 |

## Statuses

- **Proposed** — under discussion, not yet adopted
- **Accepted** — agreed upon, currently in force
- **Implemented** — agreed upon AND shipped to the codebase
- **Deprecated** — no longer recommended; kept for historical context
- **Superseded by NNNN** — replaced by a newer ADR (link to it)
