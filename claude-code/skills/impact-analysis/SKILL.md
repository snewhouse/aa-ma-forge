---
name: impact-analysis
description: Enforce dependency awareness before code edits. Use when modifying existing code, changing function signatures, working on AA-MA milestones, or editing shared/core modules. Prevents breaking changes by analyzing upstream callers, downstream dependencies, and contract changes.
---

# Impact Analysis

> **Core Principle:** Code never exists in isolation. Every function, class, and module is part of a dependency graph. Before editing ANY code, understand where it sits in that graph.

## When to Use This Skill

**REQUIRED (must output verification):**
- During AA-MA milestone execution (check `.claude/dev/active/`)
- When modifying shared/core modules imported by 3+ files
- When changing function signatures, class interfaces, or return types
- When editing files that other modules depend on

**RECOMMENDED (should verify mentally, output if risk detected):**
- Any code edit in an established codebase
- When fixing bugs that touch multiple files
- Before refactoring operations

## When NOT to Use

- Creating new isolated files with no callers yet
- Documentation-only changes (README, comments)
- Test file modifications (unless testing shared utilities)
- Configuration file changes (unless API config)

---

## The 5-Point Verification Checklist

Before ANY code edit, verify:

### 1. UPSTREAM (Callers)
What functions/modules call this code?
- Use `Grep` to find imports and function calls
- Will my change break their expectations?
- How many callers exist? (1-2 = low risk, 3+ = investigate)

### 2. DOWNSTREAM (Dependencies)
What does this code call or import?
- Do I need to update those interactions?
- Am I changing how I use a dependency?

### 3. CONTRACTS (Types/Interfaces)
Does my change alter:
- Function signatures (parameters, return types)?
- Class interfaces or method contracts?
- Expected data shapes (adding/removing fields)?
- **If YES → all callers must be updated**

### 4. TEST COVERAGE
Would existing tests catch if this breaks something?
- Check for unit tests covering this code path
- Check for integration tests involving callers
- **If no tests cover this path → flag higher risk**

### 5. SIDE EFFECTS
Does this code mutate state, write files, or touch the database?
- Will my change alter those side effects unexpectedly?
- Am I changing what gets written/stored?

---

## Required Output Format

### Single File Edit

```
📊 Impact Analysis: [file_path]
├─ Upstream: [N] callers ([file:line], [file:line], ...)
├─ Downstream: [N] deps ([module], [module], ...)
├─ Contract: [YES/NO] ([what changed] or "signature preserved")
├─ Tests: [YES/NO/PARTIAL] ([coverage description])
├─ Side effects: [description or "none"]
└─ Risk: [LOW/MEDIUM/HIGH] → [Proceeding/Action Required]
```

**Example:**
```
📊 Impact Analysis: src/auth/service.ts
├─ Upstream: 3 callers (api.ts:42, handler.ts:18, cli.ts:55)
├─ Downstream: 2 deps (utils, config)
├─ Contract: NO (signature preserved)
├─ Tests: YES (unit + integration cover this)
├─ Side effects: DB write (unchanged)
└─ Risk: LOW → Proceeding
```

### Consolidated (AA-MA Milestone)

For milestone completion with multiple files, output ONE consolidated analysis:

```
📊 Impact Analysis: Milestone "[Milestone Title]"
┌─ Files Modified: [N]
│
├─ [file_path_1]
│  ├─ Upstream: [N] callers
│  ├─ Contract: [YES/NO]
│  └─ Risk: [LOW/MEDIUM/HIGH]
│
├─ [file_path_2]
│  ├─ Upstream: [N] callers
│  ├─ Contract: [YES/NO]
│  └─ Risk: [LOW/MEDIUM/HIGH]
│
├─ [additional files...]
│
└─ Overall Risk: [LOW/MEDIUM/HIGH]
   [Summary of required actions if any]
```

### New File (Lighter Analysis)

For creating new files (no upstream callers yet):

```
📊 Impact Analysis: [file_path] (NEW)
├─ Upstream: N/A (new file)
├─ Will be imported by: [expected consumers]
├─ Follows patterns: [YES/NO] ([existing pattern file])
├─ Contract defined: [interface/type definitions]
└─ Risk: LOW → Proceeding
```

---

## Risk Detection & Response

### When Risk is LOW
- No contract changes
- Few callers (1-2)
- Good test coverage
- **Action:** Proceed silently after outputting verification

### When Risk is MEDIUM
- Contract changes with manageable caller count (3-5)
- Partial test coverage
- Some side effect changes

**Action:** Output verification with explicit acknowledgment:
```
📊 Impact Analysis: [file]
...
└─ Risk: MEDIUM
   ⚠️ Note: Updating [N] callers for [change description]
   Proceeding with cascade updates.
```

### When Risk is HIGH
- Contract changes with many callers (6+)
- No test coverage for affected paths
- Critical side effect changes
- Unclear downstream effects

**Action:** STOP and present options:
```
📊 Impact Analysis: [file]
...
└─ Risk: HIGH
   ⚠️ Action Required:

   Option A: Auto-fix cascade
   → Update all [N] callers to match new contract
   → Estimated: [files] files, [changes] changes

   Option B: Warn and wait
   → List affected files for manual review
   → Requires your decision on each

   Option C: Abort
   → Reconsider the approach
   → Change breaks too much

   Which option?
```

---

## Key Principle

**Never leave the codebase in a broken state. Either fix everything or change nothing.**

If you detect that a change would break callers:
1. **Do NOT make a partial change** that leaves callers broken
2. **Either** update all affected code atomically
3. **Or** ask for guidance before proceeding

---

## Integration with AA-MA

### During AA-MA Milestone Execution

Impact analysis is **REQUIRED** at milestone boundaries:

1. Before marking milestone COMPLETE, output consolidated impact analysis
2. Verify all contract changes have been propagated
3. Confirm no downstream milestones are affected negatively
4. Include in finalization protocol before user approval

### Detection

Check for AA-MA context:
```
If directory exists: .claude/dev/active/[task-name]/
→ Impact analysis verification is REQUIRED
→ Must output explicit verification before edits
```

### Cross-Milestone Dependencies

When editing code that later milestones depend on:
- Flag the dependency explicitly
- Verify later milestones' acceptance criteria are not invalidated
- Document in `[task]-context-log.md` if significant

---

## Index-Enhanced Analysis

When `PROJECT_INDEX.json` exists, use structured queries instead of manual Grep for checks 1-4:

| Check | Index Method | Fallback |
|-------|-------------|----------|
| 1. UPSTREAM | `who_calls(symbol, depth=2)` → transitive caller list | Grep for imports/calls |
| 2. DOWNSTREAM | `dependency_chain(file_path)` → import tree by depth | Read imports in file |
| 3. CONTRACTS | `file_summary(file)` → function signatures for comparison | Compare before/after |
| 4. TEST COVERAGE | `search_symbols("test_.*target")` → find test functions | Find test files |
| 5. SIDE EFFECTS | *(manual — not in index)* | Read function body |

**Blast radius shortcut:** `blast_radius(symbol, max_depth=3)` gives callers at each depth level — maps directly to the risk assessment.

**Freshness gate:** Check `_meta.at` timestamp. If >24h old, prepend warning to output but still use the data.

## Quick Reference

| Check | Question | Tool |
|-------|----------|------|
| Upstream | Who calls this? | `who_calls` (index) or `Grep` for imports/calls |
| Downstream | What does this call? | `dependency_chain` (index) or read imports |
| Contract | Signature changed? | `file_summary` (index) or compare before/after |
| Tests | Coverage exists? | `search_symbols` (index) or find test files |
| Side Effects | State/IO changes? | Read function body |

| Risk Level | Callers | Contract Change | Action |
|------------|---------|-----------------|--------|
| LOW | 0-2 | No | Proceed |
| MEDIUM | 3-5 | Yes (manageable) | Proceed + cascade |
| HIGH | 6+ | Yes (complex) | STOP + options |

---

## Common Patterns

### Safe Edits (Usually LOW risk)
- Adding new optional parameters with defaults
- Adding new methods to a class (not changing existing)
- Internal refactoring that preserves interface
- Bug fixes that don't change behavior contract

### Risky Edits (Investigate carefully)
- Changing return types
- Removing or renaming parameters
- Changing function names
- Modifying data shapes (adding/removing fields)
- Altering side effects (new writes, removed writes)

### Always HIGH risk
- Deleting public functions/methods
- Changing database schema
- Modifying API contracts
- Altering authentication/authorization logic
