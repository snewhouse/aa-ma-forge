# Tasks: two-active (fixture)

Two milestones left ACTIVE — a stale status from an abandoned or resumed
milestone. The loose derivation returns the FIRST one, so the gate evaluates
Milestone 2 (0 pending, SOFT) while certifying Milestone 4 (1 pending, HARD):
a silent false PASS. This is the only failure direction that lets a milestone
through, rather than blocking one that should pass.

## Milestone 2: Older milestone left ACTIVE

- Status: ACTIVE
- Gate: SOFT

### Sub-step 2.1: Finished

- Status: COMPLETE

## Milestone 4: The one actually being gated

- Status: ACTIVE
- Gate: HARD

### Sub-step 4.1: Not finished

- Status: PENDING
