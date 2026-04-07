# AA-MA Templates

Starter templates for every file in the AA-MA (Advanced Agentic Memory Architecture) system. Copy, rename with your task-name prefix, and fill in.

## Template Index

| File | AA-MA Role | Standard / Optional | Description |
|------|-----------|---------------------|-------------|
| `plan-template.md` | `[task]-plan.md` | Standard | Strategy, rationale, high-level constraints, all 11 planning elements |
| `reference-template.md` | `[task]-reference.md` | Standard | Immutable facts: APIs, file paths, config, dependencies, constants |
| `context-log-template.md` | `[task]-context-log.md` | Standard | Decision history, trade-offs, compaction summaries, gate approvals |
| `tasks-template.md` | `[task]-tasks.md` | Standard | HTP execution roadmap with milestones, sub-steps, and state tracking |
| `provenance-template.md` | `[task]-provenance.log` | Standard | Audit trail: commits, checkpoints, milestone completions, session resume |
| `verification-template.md` | `[task]-verification.md` | Optional | Adversarial verification report from 6 independent review angles |
| `tests-template.yaml` | `[task]-tests.yaml` | Optional | Machine-executable test definitions linked to milestone acceptance criteria |
| `README.md` | — | — | This index page |

## How to Use

1. **Copy** the templates you need into your task directory at `.claude/dev/active/[task-name]/`
2. **Rename** each file with your task-name prefix (e.g., `plan-template.md` becomes `my-feature-plan.md`)
3. **Fill in** the bracketed placeholders (`[task-name]`, `[YYYY-MM-DD]`, etc.) and follow the HTML comment instructions inside each template
4. **Delete** the HTML comments once the file is populated with real content

The 5 standard files are required for every AA-MA task. The 2 optional files are created only when verification is run or when acceptance criteria benefit from executable test definitions.

For full documentation, see the [AA-MA Specification](../spec/aa-ma-specification.md).
