# demo-task Tasks (HTP)

## Milestone 1: Add a greeting CLI
- Status: ACTIVE
- Dependencies: None
- Complexity: 20%
- Gate: SOFT
- Mode: AFK
- Acceptance Criteria:
  - `python greet.py Ada` prints `Hello, Ada!`.
  - `tests/test_greet.py` passes.

### Sub-step 1.1: Write greet()
- Status: COMPLETE
- Mode: AFK
- Dependencies: None
- Acceptance Criteria:
  - `greet("Ada")` returns `Hello, Ada!`.
- Result Log: greet() added in greet.py; tests/test_greet.py 1 passed (commit abc1234).

### Sub-step 1.2: Add the CLI entry point
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 1.1
- Acceptance Criteria:
  - `python greet.py Ada` prints `Hello, Ada!`.
- Result Log:

### Sub-step 1.3: Choose the default greeting language
- Status: PENDING
- Mode: HITL
- Dependencies: Sub-step 1.2
- Acceptance Criteria:
  - The user picks the default language; it is recorded in reference.md.
- Result Log:

## Milestone 2: Publish to PyPI
- Status: PENDING
- Dependencies: Milestone 1
- Complexity: 40%
- Gate: HARD
- Mode: HITL
- Acceptance Criteria:
  - `pip install demo-greet` installs version 0.1.0 from PyPI.

### Sub-step 2.1: Upload the release
- Status: PENDING
- Mode: HITL
- Dependencies: None
- Acceptance Criteria:
  - The PyPI page for demo-greet shows version 0.1.0.
- Result Log:
