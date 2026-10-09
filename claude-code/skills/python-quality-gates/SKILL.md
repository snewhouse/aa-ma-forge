---
name: python-quality-gates
description: "Python quality gates: zero tolerance for failing tests (no \"pre-existing failure\" excuse), and the pre-commit documentation-maintenance checklist. Use when finishing Python work, running a test suite, or preparing a Python commit."
---

# Python Quality Gates

Universal principles for Python projects. Project-specific commands and tools belong in the project's own `.claude/rules/` files.

## Zero Tolerance for Failing Tests

The test suite must be GREEN when you finish. No exceptions.

The "pre-existing failure" excuse is banned. These rationalizations are NOT acceptable:

- "This failure is from previous work" — You are the current work. Fix it.
- "This test was already broken when I got here" — Then you're the one who found it. Fix it.
- "This isn't related to my change" — Doesn't matter. The suite must be green when you leave.
- "I'll note it for later" — There is no later. Fix it now.
- "Fixing this is out of scope" — A red test suite is always in scope.

If a fix would take >30 min and derail the current task, you may `@pytest.mark.skip(reason="BROKEN: ...")` but you MUST tell the user. Skipped is not failed.

## Document Maintenance

Documentation drift is now **automatically enforced** by the commit workflows. See `Skill(doc-drift-detection)` — its `CHECK-DEFINITIONS.md` holds the full check definitions, severity levels, and enforcement matrix.

**Quick mental checklist** (still useful as a pre-commit habit):
1. Did I add/rename/remove a module? → README update needed
2. Did I change architecture or deps? → README update needed
3. Feature, fix, or breaking change? → CHANGELOG entry needed

**Automated enforcement:**
- `/commit-and-push` — advisory warnings for version + CHANGELOG drift
- `/pre-commit-full` — blocks on stale versions, breaking changes without CHANGELOG, AA-MA stale
- `/release-prep` — blocks on all documentation drift (full `/doc-sync --fix`)

**Quick repair:** Run `/doc-fix` to auto-fix version strings and CHANGELOG entries.

## Logging & Comment Lint

New Python projects copy [`../logging-and-comments/references/ruff-baseline.toml`](../logging-and-comments/references/ruff-baseline.toml) into `pyproject.toml` (Ruff LOG, G, T20, BLE, S110/S112, TRY400/401, D1, TD, ERA). Existing repos adopt it with noisy pre-existing codes parked in `extend-ignore` tagged `# TODO(logging-std): burn down`. Standard: `Skill(logging-and-comments)`.
