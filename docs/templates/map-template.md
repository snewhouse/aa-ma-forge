# Charting: [effort]

<!--
Template for `[effort]-map.md` — the pre-plan decision map written by `/aa-ma-chart`.
Lives at `.claude/dev/charting/[effort]/[effort]-map.md` while charting; `/aa-ma-plan
--from-map [effort]` moves it to `.claude/dev/active/[task]/[task]-map.md` (optional
AA-MA file type; ADR-0013). Concept adapted from mattpocock/skills `wayfinder`.

The map is an INDEX, not a store: a decision lives in exactly one ticket; the map
gists it and links. Delete these comments once the map is populated.

Grammar the guard (`claude-code/hooks/lib/aa-ma-chart-guard.sh`) reads:
  `### Ticket N: Title`  — one block per ticket, N unique, ends at the next `###`/`##`
  `- Type:`   research | prototype | grilling | task        (default grilling)
  `- Mode:`   HITL | AFK    (research → AFK; prototype/grilling → HITL; task → either)
  `- Status:` OPEN | CLAIMED | RESOLVED | RULED_OUT
  `- Claimed-at: YYYY-MM-DDTHH:MM`   present iff CLAIMED (the guard writes it)
  `- Reclaimed: YYYY-MM-DDTHH:MM`    appended by `reclaim`; may repeat
  `- Blocked-by: N, N | —`            ticket numbers; `—` when unblocked
  `#### Question` / `#### Answer`     Answer present only when RESOLVED
Fog = bullets under `## Not yet specified`. `## Out of scope` never graduates.
Headings deliberately never match `## Milestone N:` / `### Sub-step N.M:` so the
gate and TUI ignore maps.
-->

## Destination

[What reaching the end of this map looks like — the spec, decision, or change this effort is finding its way to. One or two lines; every session orients to it before choosing a ticket.]

## Notes

[Domain; skills every session should consult; standing preferences for this effort. Charting never edits files outside `.claude/dev/charting/`, `docs/research/` and `prototype/*` branches unless a Note here says otherwise.]

## Decisions so far

<!-- one line per RESOLVED ticket, newest last: enough to judge relevance, then follow the link -->

- [Ticket 1: [title]](#ticket-1-title): [one-line gist of the answer]

## Tickets

### Ticket 1: [Title — the decision this ticket resolves, as a question]
- Type: grilling
- Mode: HITL
- Status: OPEN
- Blocked-by: —
#### Question
[The decision or investigation this ticket resolves, sized to one agent session.]

### Ticket 2: [Title]
- Type: research
- Mode: AFK
- Status: RESOLVED
- Blocked-by: —
#### Question
[What fact does a later decision wait on?]
#### Answer
[Gist + link: see docs/research/[effort]-[topic].md]

### Ticket 3: [Title]
- Type: prototype
- Mode: HITL
- Status: OPEN
- Blocked-by: 1
#### Question
[Which shape feels right? Resolved by Skill(prototype) on branch prototype/[effort]-3.]

## Not yet specified

<!-- fog: in-scope questions you can sense but cannot yet phrase sharply enough to ticket. Coarser than a ticket; graduates into tickets as the frontier advances. Empty here + every ticket RESOLVED/RULED_OUT = the way is clear → /aa-ma-plan --from-map -->

- [suspected question / area to revisit once Ticket N resolves]

## Out of scope

<!-- work consciously ruled beyond the destination; closed, never graduates. If an existing ticket turns out to sit past the destination, mark it RULED_OUT and leave one line here. -->

- [gist + why it is beyond this destination]
