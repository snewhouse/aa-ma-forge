# Charting: demo-effort

## Destination

A decision to lock before planning.

## Notes

None.

## Decisions so far

- [Ticket 1: Which storage shape?](#ticket-1-which-storage-shape): SQLite.
- [Ticket 2: Does the API paginate?](#ticket-2-does-the-api-paginate): yes, cursor-based.

## Tickets

### Ticket 1: Which storage shape?
- Type: grilling
- Mode: HITL
- Status: RESOLVED
- Blocked-by: —
#### Question
SQLite or JSON?
#### Answer
SQLite — prototype showed 40× faster lookups.

### Ticket 2: Does the API paginate?
- Type: research
- Mode: AFK
- Status: RESOLVED
- Blocked-by: —
#### Question
Check the docs.
#### Answer
Yes — see docs/research/demo-effort-pagination.md

### Ticket 3: Federation
- Type: grilling
- Mode: HITL
- Status: RULED_OUT
- Blocked-by: 1
#### Question
Should v1 federate?

## Not yet specified

## Out of scope

- federation (Ticket 3) — beyond the destination
