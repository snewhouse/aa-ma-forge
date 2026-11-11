---
name: defense-in-depth
description: Use when invalid or untrusted data (user input, files, API or LLM output) causes failures deep in execution - validate once at the trust boundary into a typed value, keep cheap invariant asserts deeper, guard dangerous operations, and log for forensics
---

# Defense-in-Depth Validation

> **Origin:** Derived from a debugging session where an empty-string bug propagated through 4 validation layers, proving that single-point validation is insufficient.

## Overview

When you fix a bug caused by invalid data, adding validation at one place feels sufficient. But that single check can be bypassed by different code paths, refactoring, or mocks.

**Core principle:** Validate ONCE, at the trust boundary, and turn the input into a typed value (parse, don't validate). Inner layers then receive that type, so they need only cheap asserts on invariants, not a second validation. Guard the dangerous operations and log enough to trace a failure. Make the bug structurally impossible.

## Why Multiple Layers

Single validation: "We fixed the bug"
Multiple layers: "We made the bug impossible"

Different layers catch different cases:
- Entry validation catches most bugs
- Business logic catches edge cases
- Environment guards prevent context-specific dangers
- Debug logging helps when other layers fail

## The Four Layers

### Layer 1: Trust-Boundary Parsing
**Purpose:** Reject invalid input where it enters, and hand inner code a value that cannot be invalid

```typescript
function parseProjectDir(workingDirectory: string): ProjectDir {
  if (!workingDirectory || workingDirectory.trim() === '') {
    throw new Error('workingDirectory cannot be empty');
  }
  if (!existsSync(workingDirectory)) {
    throw new Error(`workingDirectory does not exist: ${workingDirectory}`);
  }
  if (!statSync(workingDirectory).isDirectory()) {
    throw new Error(`workingDirectory is not a directory: ${workingDirectory}`);
  }
  return workingDirectory as ProjectDir;   // a branded type: only this function makes one
}
```

Every check that needs I/O or parsing happens here, once. Code past the boundary takes `ProjectDir`, not `string`.

### Layer 2: Cheap Invariant Asserts
**Purpose:** Catch a broken invariant (a mock, a refactor, a second entry point) without re-validating

```typescript
function initializeWorkspace(projectDir: string, sessionId: string) {
  if (!projectDir) {
    throw new Error('projectDir required for workspace initialization');
  }
  // ... proceed
}
```

### Layer 3: Environment Guards
**Purpose:** Prevent dangerous operations in specific contexts

```typescript
async function gitInit(directory: string) {
  // In tests, refuse git init outside temp directories
  if (process.env.NODE_ENV === 'test') {
    const normalized = normalize(resolve(directory));
    const tmpDir = normalize(resolve(tmpdir()));

    if (!normalized.startsWith(tmpDir)) {
      throw new Error(
        `Refusing git init outside temp dir during tests: ${directory}`
      );
    }
  }
  // ... proceed
}
```

### Layer 4: Debug Instrumentation
**Purpose:** Capture context for forensics

```typescript
async function gitInit(directory: string) {
  const stack = new Error().stack;
  logger.debug('About to git init', {
    directory,
    cwd: process.cwd(),
    stack,
  });
  // ... proceed
}
```

## Applying the Pattern

When you find a bug:

1. **Trace the data flow** - Where does bad value originate? Where used?
2. **Map all checkpoints** - List every point data passes through
3. **Parse at the boundary, assert inside** - one validating parse where data enters; cheap asserts, guards and debug logging further in. Before adding them to existing code, run `Skill(impact-analysis)` on it: a new guard changes what its callers may pass
4. **Test each layer** - Try to bypass layer 1, verify layer 2 catches it

## Example from Session

Bug: Empty `projectDir` caused `git init` in source code

**Data flow:**
1. Test setup → empty string
2. `Project.create(name, '')`
3. `WorkspaceManager.createWorkspace('')`
4. `git init` runs in `process.cwd()`

**Four layers added:**
- Layer 1: `Project.create()` parses the path into a `ProjectDir` (not empty, exists, writable)
- Layer 2: `WorkspaceManager` asserts the `ProjectDir` it got is non-empty (cheap; catches mocks)
- Layer 3: `WorktreeManager` refuses git init outside tmpdir in tests
- Layer 4: Stack trace logging before git init

**Result:** All 1847 tests passed, bug impossible to reproduce

## Key Insight

All four layers were necessary. During testing, each layer caught bugs the others missed:
- Different code paths bypassed entry validation
- Mocks bypassed business logic checks
- Edge cases on different platforms needed environment guards
- Debug logging identified structural misuse

**Don't stop at one check.** Parse once at the boundary, then keep a cheap check at every layer the value passes through.

## Untrusted Model Output

LLM output is untrusted input, like a request body. Parse it at the boundary into a typed value (a
schema-validated object, an allow-listed enum) before it reaches a shell, a query, a file path or a
client-facing document. For text that reaches clients, see `Skill(llm-output-safety)`.
