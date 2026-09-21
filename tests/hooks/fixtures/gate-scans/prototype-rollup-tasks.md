# prototype-rollup fixture (mattpocock-trio-adoption M3)

Sub-step `Prototype-Required` rolls up to the selected milestone only (AD-001).
Milestones 3 and 4 carry deliberately bad sub-step tokens: they must refuse
(exit 2) when selected and must NOT poison `--milestone 1` / `--milestone 2`.

## Milestone 1: Roll-up
- Status: PENDING
- Gate: SOFT

### Sub-step 1.1: plain
- Status: PENDING

### Sub-step 1.2: needs prototype
- Status: PENDING
- Prototype-Required: YES

## Milestone 2: No flags
- Status: PENDING

### Sub-step 2.1: plain
- Status: PENDING

## Milestone 3: Invalid sub-step token
- Status: PENDING

### Sub-step 3.1: not a canonical value
- Status: PENDING
- Prototype-Required: maybe

## Milestone 4: Empty template slot
- Status: PENDING

### Sub-step 4.1: the slot tasks-template.md used to emit
- Status: PENDING
- **Prototype-Required:**
