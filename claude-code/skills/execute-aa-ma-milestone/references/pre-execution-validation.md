# Locate the task and validate its artefacts — the Tier 1 existence check and the Tier 2 validator dispatch, with auto-recovery.

## 1. Locate Active Task & Pre-Execution Validation

Check `.claude/dev/active/` for the most recent task directory:

```bash
ls -lt .claude/dev/active/ | head -5
```

**Expected structure**: `.claude/dev/active/[task-name]/`

### Tier 1: Existence Check (Fast)

Verify all 5 required AA-MA files exist and are non-empty:

```bash
TASK_DIR=".claude/dev/active/[task-name]"
TASK_NAME="[task-name]"
MISSING=0
for file in "${TASK_NAME}-plan.md" "${TASK_NAME}-reference.md" "${TASK_NAME}-context-log.md" "${TASK_NAME}-tasks.md" "${TASK_NAME}-provenance.log"; do
  if [[ ! -s "${TASK_DIR}/${file}" ]]; then
    echo "❌ MISSING or EMPTY: ${file}"
    MISSING=$((MISSING + 1))
  fi
done
echo "Tier 1 result: ${MISSING} files missing"
```

**If Tier 1 fails (any files missing or empty):**

```
⚠️ AA-MA ARTIFACTS INCOMPLETE — AUTO-RECOVERY TRIGGERED

Missing/empty files detected: [list]

Auto-recovery: Triggering Phase 5 artifact creation with scribe+validator agents...
```

1. Notify user that auto-recovery is starting
2. Spawn `aa-ma-scribe` agent to create missing files from available plan context
3. Spawn `aa-ma-validator` agent to verify created files (5-dimension check)
4. If validator reports PASS/WARN → continue execution
5. If validator reports FAIL → retry once (re-scribe → re-validate)
6. If still FAIL after retry → HALT and alert user: "Auto-recovery failed. Run `/aa-ma-plan` to recreate artifacts."
7. If agent spawning unavailable → fallback: create files directly inline, then continue

### Tier 2: Content Validation (Thorough)

After Tier 1 passes, spawn the `aa-ma-validator` agent for deep content checks:

```
Spawn aa-ma-validator with:
  subagent_type: "aa-ma-validator"
  prompt: Validate artifacts at [task-dir] in pre-execution context
  Tools: Read, Glob, Grep (NO Write, NO Bash)
```

**Validator checks 5 dimensions:**
1. **Existence** — all 5 files present and non-empty
2. **Plan completeness** — plan.md has the 11 AA-MA required elements
3. **Reference completeness** — reference.md has facts extracted from plan
4. **HTP structure** — tasks.md has proper milestone/step hierarchy with Status fields
5. **Cross-file consistency** — no contradictions between files

**Validator verdict handling:**
- **PASS**: All checks passed → continue to step 2
- **WARN**: Minor issues (non-blocking) → log warnings, continue to step 2
- **FAIL**: Critical issues → attempt remediation:
  1. Spawn `aa-ma-scribe` to fix identified issues
  2. Re-run validator
  3. If still FAIL → HALT and alert user

**If Tier 2 agent spawning unavailable:** Skip Tier 2 (Tier 1 existence check is sufficient to proceed). Log: "Tier 2 validation skipped — agent spawning unavailable."
