# demo-task Plan

Created: 2026-10-01

## Executive summary
Ship a greeting CLI (`greet.py`), then publish it to PyPI as `demo-greet`.

## Milestones
1. Add a greeting CLI — `python greet.py Ada` prints `Hello, Ada!`.
2. Publish to PyPI — irreversible upload, so it needs a signed HARD-gate approval.

## Rollback
Revert the milestone commit; a PyPI upload cannot be undone (yank only).
