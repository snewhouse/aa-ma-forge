# AA-MA Operational Rules

The **Advanced Agentic Memory Architecture** provides structured external memory for long-horizon tasks.
Full specification: [docs/aa-ma-specification.md](../docs/aa-ma-specification.md) | Quick ref: [docs/aa-ma-quick-reference.md](../docs/aa-ma-quick-reference.md)

## File System (5 standard + 2 optional)

| File | Purpose |
|------|---------|
| `[task]-plan.md` | Strategy, rationale, high-level constraints |
| `[task]-reference.md` | **Immutable facts** — APIs, paths, constants (high-priority memory) |
| `[task]-context-log.md` | Decision history, trade-offs, compaction summaries, **gate approvals** |
| `[task]-tasks.md` | HTP execution roadmap, dependencies, state tracking |
| `[task]-provenance.log` | Execution telemetry, commit history, **session checkpoints** |
| `[task]-verification.md` | **Optional** — adversarial verification audit trail (via `/verify-plan` or Phase 4.5) |
| `[task]-tests.yaml` | **Optional** — machine-executable test definitions linked to milestone acceptance criteria |

**Task directory:** `.claude/dev/active/[task-name]/`

## Sync Discipline

After completing every task and milestone, **immediately**:
1. Mark task COMPLETE in `tasks.md`, extract facts to `reference.md`
2. Document decisions in `context-log.md`, log to `provenance.log`
3. Commit and push all changes

**Never proceed to next task until current task is fully synced and pushed.**

> **Note:** `plan.md` is NOT part of the post-task sync. It is a historical record set once during planning. Only 4 files are synced: `tasks.md`, `reference.md`, `context-log.md`, and `provenance.log`. Update `plan.md` only for scope changes.

### Verification Report (Optional)

When plan verification is run (via Phase 4.5 or `/verify-plan`), persist results as `[task]-verification.md`. This file:
- Documents all findings from the 6 adversarial verification angles
- Tracks CRITICAL/WARNING/INFO severity classifications
- Records revision history if plan was revised based on findings
- Is **optional** — only created when user chooses automated or interactive verification (not skip)

### Sub-Step Sync Rule (L-080, L-081, L-082)

**The Result Log is mandatory regardless of who executes — lead orchestrator or agent.**

When the lead orchestrator executes steps directly (not via agent dispatch):
1. **After EACH sub-step**: immediately write `Status: COMPLETE` and a concise `Result Log:` with specific evidence (IDs, counts, pass/fail verdicts) in tasks.md
2. **Before marking any milestone COMPLETE**: verify zero `Status: PENDING` sub-steps remain within that milestone. Run: `grep -c "Status: PENDING"` within the milestone section.
3. **NEVER batch Result Log updates** to "end of milestone" — this is the #1 cause of sub-step drift.

**Why this matters:** Agents auto-populate Result Logs via their prompt contract. The lead orchestrator has no forcing function — results exist in conversation context but never reach tasks.md unless explicitly written. Direct-execution steps are the high-risk ones for drift.

## Commit Signature

When an AA-MA plan is active, ALL commits must include as the last footer line:
```
[AA-MA Plan] {task-name} .claude/dev/active/{task-name}
```

## Key Protocols

- **Finalization**: 4-step protocol (integrity check, doc update, user approval, confirmation). See [spec](../docs/aa-ma-specification.md#vii-finalization-protocol).
- **Context Injection**: Load files in XML delimiters; prioritise REFERENCE and TASKS. See [spec](../docs/aa-ma-specification.md#iv-context-injection-standard).
- **Archival**: When all milestones complete, run `/archive-aa-ma {task-name}`

## Task Execution Mode (HITL / AFK)

Every task entry in `tasks.md` MUST include a `Mode:` field:

| Mode | Meaning | Execution Behavior |
|------|---------|-------------------|
| `HITL` | Human In The Loop | Pauses for user input, review, or decision before proceeding |
| `AFK` | Away From Keyboard | Can be fully auto-dispatched to agents without user intervention |

**Classification guidance:**
- **HITL** when: architectural decisions, client-facing language, scope changes, irreversible actions, external API credential setup
- **AFK** when: implementation from clear specs, test writing, file creation, mechanical refactoring, documentation generation

**Format in tasks.md:**
```
### Task 1.1: [Title]
- Status: PENDING
- Mode: AFK
- Acceptance Criteria: [...]
```

The `/execute-aa-ma-milestone` command uses this field to auto-dispatch AFK tasks while pausing for HITL tasks.

## Milestone Gate Classification (HARD / SOFT)

Every milestone in `tasks.md` SHOULD include a `Gate:` field:

| Gate | Enforcement | When to Use |
|------|-------------|-------------|
| `SOFT` (default) | Convention-based — agent instructed to seek approval | Reversible changes, low-risk milestones |
| `HARD` | Artifact-enforced — `/execute-aa-ma-milestone` **refuses to advance** without signed approval in `context-log.md` | Irreversible actions, architectural decisions, production deployments |

**HARD gate approval artifact** (must exist in `context-log.md` before finalization):
```markdown
## [YYYY-MM-DD] GATE APPROVAL: [Milestone Title]
- Gate: HARD
- Approved by: [user]
- Criteria verified: [X/X]
- Decision: APPROVED
```

## Session Checkpoints

When context compaction occurs or a session ends mid-task, write a CHECKPOINT to `provenance.log`:
```
[TIMESTAMP] CHECKPOINT — ActiveStep: [step-id] — NextAction: "[description]" — ContextLoaded: [files] — TokenUsage: [%]
```

This enables reliable session resume without relying solely on context-log.md summaries.

## Planning Standard

Every plan **MUST** include these 11 outputs:

1. Executive summary (1-3 lines) | 2. Stepwise implementation plan | 3. Milestones with measurable goals | 4. Acceptance criteria per step | 5. Required artefacts | 6. Tests to validate | 7. Rollback strategy | 8. Dependencies & assumptions | 9. Effort estimate & Complexity (0-100%) | 10. Risks & mitigations (top 3 per milestone) | 11. Next action + AA-MA file to update

Steps with **Complexity >= 80%** require human review or Chain-of-Thought deep reasoning.

Full standard with prompt template: [docs/aa-ma-specification.md#xi-planning-standard](../docs/aa-ma-specification.md#xi-planning-standard)
