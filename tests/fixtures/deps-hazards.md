# deps-hazards Tasks (HTP)

Fixture for `aa_ma.deps` (diagram-generation M7, map Ticket 16). Every heading shape
here is one a naive resolver got wrong during charting: `M`-numbered steps (`M1.0`,
`M2a.1`), a lettered milestone (`2a`), and a cross-plan reference.

## Milestone 1: Foundations
- Status: COMPLETE
- Dependencies: None

### Step M1.0: Scaffold
- Status: COMPLETE
- Dependencies: None

## Milestone 2: Core
- Status: PENDING
- Dependencies: Milestone 1

### Step M2.1: Build
- Status: PENDING
- Dependencies: Step M1.0

## Milestone 2a: Core, lettered
- Status: COMPLETE
- Dependencies: Milestone 1; `milestone-grammar-ssot` M5 merged (grammar.split_milestones trailing-H2 fix)

### Step M2a.1: Lettered step
- Status: PENDING
- Dependencies: Step M2.1

## Milestone 3: Integration
- Status: ACTIVE
- Dependencies: Milestone 2, Milestone 2a

### Step M3.1: Wire "it" up
- Status: PENDING
- Dependencies: Step M2a.1
