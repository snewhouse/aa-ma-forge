# AA-MA execution best practices — habits that keep execution state accurate across sessions.

## XII. Best Practices

### 1. Proactive Detection

**Always check for AA-MA tasks at session start**:
```bash
ls -lt .claude/dev/active/ 2>/dev/null
```

Don't wait for user to mention AA-MA - proactively detect and use.

### 2. Prefer Milestone Mode

**Default to milestone execution** for most work:
- Provides quality gates (strict validation)
- Natural checkpoints (git commits + tags)
- Balanced structure and flexibility

Use Step mode only for exploration. Use Full mode only for well-tested plans.

### 3. Update State Immediately

**Never batch state updates**:
- Update TASKS immediately after task completion
- Extract facts to REFERENCE in real-time
- Document decisions in CONTEXT_LOG as they happen

Batching leads to missed updates and state drift.

### 4. Validate Early and Often

**Don't skip validation checks**:
- Pre-execution: Check dependencies, blockers, resources
- During execution: Verify acceptance criteria continuously
- Post-execution: Run tests, check for regressions

Early validation prevents costly rollbacks.

### 5. Document Decisions, Not Actions

**In CONTEXT_LOG, focus on "why" not "what"**:

Good:
```markdown
**Decision**: Use PostgreSQL instead of SQLite
**Rationale**: Need concurrent writes for multi-agent system
**Trade-off**: More complex deployment, but better scalability
```

Bad:
```markdown
**Decision**: Installed PostgreSQL
**Rationale**: We needed a database
```

### 6. Use Complexity Scores

**High complexity (≥80%) signals need for extra care**:
- Break into smaller sub-tasks
- Add human review checkpoints
- Increase testing coverage
- Document more thoroughly

Don't rush high-complexity tasks.

### 7. Leverage Provenance Log

**Use provenance for debugging**:
- Track when issues were introduced (git bisect)
- Identify patterns (frequent rollbacks on specific tasks)
- Measure velocity (commits per milestone)

Provenance is your audit trail - use it.
