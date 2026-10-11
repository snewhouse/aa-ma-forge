# AA-MA commit signature — the footer every commit carries while a plan is active, with examples.

## V. AA-MA Commit Signature — MANDATORY

**CRITICAL**: ALL commits during AA-MA execution MUST include the plan signature as the LAST line of the commit message footer.

### Signature Format

```
[AA-MA Plan] {task-name} .claude/dev/active/{task-name}
```

### Example Commits

**Step completion:**
```
feat(auth): implement JWT token generation

- Add token service with RS256 signing
- Configure 1-hour expiry

[AA-MA Plan] auth-system .claude/dev/active/auth-system
```

**Milestone completion:**
```
feat(auth-system): complete milestone 1 - authentication core

Acceptance criteria:
- ✅ JWT tokens generated correctly
- ✅ Token validation works
- ✅ All tests passing (8/8)

[AA-MA Plan] auth-system .claude/dev/active/auth-system
```

### Why This Matters

- **Traceability**: Every commit can be traced back to its originating plan
- **Provenance**: Clear audit trail for complex multi-session work
- **Context**: When reviewing git history, immediately know which plan drove each change

### Applies To

- All commits during AA-MA plan execution
- All commits from `/execute-aa-ma-step`, `/execute-aa-ma-milestone`, `/execute-aa-ma-full`
- Commits from any other helper command or pre-commit auto-fix while a plan is active
- Manual commits during plan execution
