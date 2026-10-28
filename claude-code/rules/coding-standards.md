# Coding Standards (auto-loaded)

New and modified code complies; existing code is not backfilled. Detail lives in the skills below; the rule holds with ponytail on or off. Process doctrine: [`engineering-standards.md`](engineering-standards.md).

## Non-negotiables

- No silent failures: every `except`, skip or fail-open path logs one line or bumps a reported counter. Logs go to stderr, data to stdout.
- `# why:` on every deliberate suppression (`noqa`, `type: ignore`, `|| true`, `2>/dev/null`) in maintained source. Name the code; blanket forms hide errors. Remove an unneeded suppression, don't document it.
- Public API carries a doc block in its language's native format; comments say why, not what.
- `TODO(#N): …` or `TODO(ADR-NNNN): …`; no ownerless TODOs.
- Secrets come from the environment; input is validated at trust boundaries; model output is untrusted input.

## Principles

| Principle | Heuristic | Automated check (configured) | Reviewer rule |
|-----------|-----------|------------------------------|---------------|
| KISS | the simplest concrete code that meets current requirements | Ruff `C901`/`PLR0913` (`pyproject.toml` limits) on touched files; exceeding needs `# noqa: <code>  # why: …` | could it be simpler? |
| DRY | one authoritative source per fact (schema, grammar, constant, count); code duplication tolerated until about the third occurrence; prefer duplication to a parameter-and-conditional abstraction | none | a duplicated fact is a defect at once |
| YAGNI | build for current requirements | none | never a reason to reject tests, refactoring or maintainability work |
| SoC | separate logic, data access, integration and presentation, without a file per responsibility | import-linter contracts in CI (`.importlinter`, where configured) | is each unit cohesive? |
| SOLID | depend on an abstraction when evidence earns it (policy below) | none | the review questions below |

## When principles conflict

Default to the simplest concrete implementation that meets current requirements. Introduce abstractions when they solve an evidenced problem: a real alternate implementation, an actively used test seam, a necessary dependency boundary, an ongoing migration, or repeated shared knowledge. A single production implementation does not automatically disqualify an abstraction. Preserve separation of concerns without requiring a separate file for every responsibility; minimise unnecessary indirection and fragmentation, not file count at the expense of clarity. Treat the rule of three as a heuristic, not a mandatory threshold. YAGNI must not be used to reject necessary tests, refactoring or maintainability work. Import checks (import-linter) enforce configured boundaries; review still assesses cohesion and design. Review questions: *What current problem does this structure solve? What simpler alternative exists? What would break if we removed it? What would introducing it later cost?*

## Code documentation and ponytail

Docstrings, why-comments, constant rationale (name, unit, reason) and `ponytail:` ceiling notes are required documentation. They are exempt from ponytail's "no unrequested prose" rule, but stay proportionate: a summary and needed sections, no tutorials.

## Testing floor

TDD: a failing test first for every behaviour change. Depth is risk-proportionate: branches, parsers, security and data paths cover the happy path, the edge cases and the regression; trivial glue may rely on a higher-level test. Ponytail's "one runnable check" is the floor for throwaway or prototype code only. No fixtures or frameworks beyond pytest and bats unless they earn their place. Milestone waivers: `TDD-Waiver:` in `engineering-standards.md` §2.

## Routing: when X, load the skill

| When | Load |
|------|------|
| logging, comments or docstrings | `Skill(logging-and-comments)` |
| finishing Python work or running its tests | `Skill(python-quality-gates)` |
| writing shell scripts | `Skill(bash-defensive-patterns)` |
| TS/JS, R or SQL — or any language's tooling | `Skill(language-conventions)` |
| security checks or a dependency audit | `Skill(secops)` |
| storing or injecting secrets | `Skill(secrets-management)` |
| LLM text in client-facing output | `Skill(llm-output-safety)` |
| changing shared code or a signature | `Skill(impact-analysis)` |
| writing a skill, `AGENTS.md` or `CLAUDE.md` | `Skill(writing-for-agents)` |
