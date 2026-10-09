# demo-plan Plan

Created: 2026-10-01

## Executive summary
Add a `--shout` flag to `greet.py` that upper-cases the greeting.

## Milestone 1: Shout flag
- Critical-Path: database
- Acceptance Criteria:
  - `python greet.py --shout Ada` prints `HELLO, ADA!`.
  - `tests/test_greet.py` covers both cases.

## Milestone 2: Document the flag
- Acceptance Criteria:
  - README.md shows a `--shout` example.

## Rollback
Revert the milestone commit.

## Risks
- Argument parsing breaks the positional name. Mitigation: a test for each form.
