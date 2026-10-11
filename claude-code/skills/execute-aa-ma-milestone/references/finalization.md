# Finalization after the integrity check — the doc auto-update, validator dispatch, user approval and status change that follow §7.1.

### 7.2 Documentation Auto-Update

Automatically update all 5 AA-MA files:

| File | Auto-Update Action |
|------|-------------------|
| `tasks.md` | Mark milestone `Status: COMPLETE`, fill `Result Log:` |
| `reference.md` | Add any new immutable facts discovered during execution |
| `context-log.md` | Append completion summary (template below) |
| `provenance.log` | Append completion entry with timestamp + commit hash |
| `plan.md` | No change (historical record) |

**Context-log.md template:**
```markdown
## [YYYY-MM-DD] Milestone Completion: [Title]
- Status: COMPLETE
- Key outcome: [1-2 sentence summary]
- Artifacts: [list of files created/modified]
- Tests: [pass/fail summary]
```

**Provenance.log template:**
```
[TIMESTAMP] MILESTONE COMPLETE — [Milestone ID] — Commit: [hash] — Criteria: [X/X] verified
```

### 7.2.5 Post-Completion Validator Dispatch (RECOMMENDED)

After auto-updating docs (7.2) and before requesting user approval (7.3), dispatch `aa-ma-validator` agent to audit the just-updated artifacts. This catches drift WHILE the user is reviewing, so issues get remediated in-flight rather than post-archive.

**Spawn the validator** with `subagent_type: "aa-ma-validator"`, prompt focused on these 6 dimensions:

1. **Existence** — all files present and non-empty
2. **Plan completeness** — 11 AA-MA planning standard elements present
3. **Reference completeness** — immutable facts extracted
4. **HTP structure** — milestone COMPLETE, all sub-steps COMPLETE with Result Logs
5. **Cross-file consistency** — no contradictions
6. **Completeness-claim accuracy** — every COMPLETE status backed by evidence:
   - Result Logs populated (no `[pending at commit time]` placeholders)
   - Commit SHAs recorded in both tasks.md and provenance.log
   - provenance.log terminates with `MILESTONE_N COMPLETE` entry
   - All acceptance criteria verified with cited evidence

**Verdict handling:**
- **READY_FOR_ARCHIVE** → proceed to 7.3 User Authorization
- **WARNINGS_BUT_USABLE** → back-fill inline (Edit artifact files: replace placeholders, append missing events), then proceed to 7.3. Inline back-fill avoids a separate post-archive audit commit.
- **GAPS_REQUIRE_FIX** → HALT. Present findings to user. Remediate or defer archive.

**Rationale:** Catching placeholders and missing events during finalization is one commit cheaper than post-archive remediation. Confirmed by `go-biological-process-disease-support` 2026-04-20 sprint audit (3 WARN items that required back-fill commit `d424ef8`).

**If agent spawning unavailable:** skip this step, log `validator dispatch skipped — agent unavailable` to provenance.log, continue to 7.3. Do NOT block finalization on validator unavailability.

### 7.3 User Authorization (Approval Gate)

Use AskUserQuestion to get explicit user approval before changing status to COMPLETE:

**Question format:**
```
📋 Finalization Review

Milestone: [Title]
Acceptance Criteria: [X/X] verified ✓

Ready to mark this milestone COMPLETE?
```

**Options:**
- **Approve** → "Proceed with status change and commit"
- **Review First** → "Show me the detailed verification before approving"
- **Reject** → "Do not mark complete, keep as ACTIVE"

**Behavior by choice:**
- **Approve**: Proceed to Step 7.4 and git commit
- **Review First**: Display full integrity checklist with evidence, then re-prompt
- **Reject**: HALT execution, keep `Status: ACTIVE`, ask user what needs fixing

### 7.4 Transparent Status Change

After approval, display minimal confirmation:

```
✅ Milestone marked COMPLETE: [Title]
```

Then proceed to git commit.

**Archive Reminder** (only if this is the FINAL milestone):
If ALL milestones in tasks.md now have `Status: COMPLETE`, add:
```
💡 All milestones complete! Run: /archive-aa-ma [task-name]
```
