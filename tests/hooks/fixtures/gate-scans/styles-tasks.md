# Gate-scan fixture — one milestone per heading style in the corpus

Every style below is one the tolerant reader accepts (see `src/aa_ma/grammar.py`
and the 14-plan census in the milestone-grammar-ssot reference). The §6.7 and
§7.1 gate scans must find the same fields in all of them.

## Milestone 1: Canonical form

- Status: COMPLETE
- Gate: SOFT

### Sub-step 1.1: Already done
- Status: COMPLETE

## M2: Bare-M form

- Status: ACTIVE
- Gate: HARD
- **Critical-Path:** data-xform

### Sub-step 2.1: Not yet started
- Status: PENDING

## Milestone M3: Milestone-M form

- Status: ACTIVE
- Gate: SOFT
- **Prototype-Required:** YES

### Sub-step 3.1: Not yet started
- Status: PENDING

## Milestone 4 — Em-dash form

- Status: ACTIVE
- Gate: HARD
- **Critical-Path:** hook-modification
- **Prototype-Required:** YES

### Sub-step 4.1: Not yet started
- Status: PENDING

### Sub-step 4.2: Also not started
- Status: PENDING

## Summary Counts

Negative control. This is an ordinary prose heading, not a milestone — the
tolerant reader must not treat it as one. It deliberately contains the literal
strings a naive scan would latch onto:

- Status: PENDING
- Gate: HARD
- **Critical-Path:** auth-flow

## Milestone Gate Types

Second negative control: begins with the word "Milestone" but carries no number,
so it is prose, not a heading the grammar recognises.
