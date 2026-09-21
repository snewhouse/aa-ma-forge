# Charting: open-effort

## Destination

A spec for the thing.

## Notes

Skills: grill-with-docs, prototype.

## Decisions so far

- [Ticket 2: Does the API paginate?](#ticket-2-does-the-api-paginate): yes, cursor-based.

## Tickets

### Ticket 1: Which storage shape?
- Type: grilling
- Mode: HITL
- Status: OPEN
- Blocked-by: —
#### Question
SQLite or JSON?

### Ticket 2: Does the API paginate?
- Type: research
- Mode: AFK
- Status: RESOLVED
- Blocked-by: —
#### Question
Check the docs.
#### Answer
Yes — see docs/research/open-effort-pagination.md

### Ticket 3: Which query API shape feels right?
- Type: prototype
- Mode: HITL
- Status: OPEN
- Blocked-by: 1
#### Question
Build two stubs and react.

## Not yet specified

- migration of existing data (depends on Ticket 1)

## Out of scope

- federation
