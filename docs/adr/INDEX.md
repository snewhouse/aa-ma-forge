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

## Statuses

- **Proposed** — under discussion, not yet adopted
- **Accepted** — agreed upon, currently in force
- **Implemented** — agreed upon AND shipped to the codebase
- **Deprecated** — no longer recommended; kept for historical context
- **Superseded by NNNN** — replaced by a newer ADR (link to it)
