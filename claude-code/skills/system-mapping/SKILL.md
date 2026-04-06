---
name: system-mapping
description: Lightweight pre-flight checklist for understanding system context before code changes. Perform 5-point analysis of architecture, execution flows, logging, dependencies, and environment. Use before modifying unfamiliar code or multi-file changes.
triggers:
  - system mapping
  - pre-flight check
  - before modifying
  - understand context
  - code change preparation
---

# System Mapping Skill

A focused, rapid assessment protocol for understanding system context before making code changes. This is a **pre-flight checklist**, not a comprehensive audit.

## Purpose

Prevent "change blindness" by systematically understanding:
- What you're touching
- What depends on it
- What it depends on
- How to observe its behavior

## When to Use

### Decision Tree

```
Making changes to code?
│
├── Quick single-file fix with known context?
│   └── SKIP system mapping
│
├── Changes touch 3+ files?
│   └── PERFORM system mapping
│
├── Unfamiliar code area?
│   └── PERFORM system mapping
│
├── Integrating with external services?
│   └── PERFORM system mapping
│
├── Modifying data pipelines or flows?
│   └── PERFORM system mapping
│
└── Adding new functionality to existing module?
    └── PERFORM system mapping (at least points 1, 4, 5)
```

### Comparison with Other Tools

| Tool | Purpose | Depth | When |
|------|---------|-------|------|
| **system-mapping** | Pre-flight check | Focused | Before code changes |
| `/codebase-deep-dive` | Comprehensive audit | Deep | New codebase, major refactor |
| `Skill(impact-analysis)` | Risk assessment | Moderate | After identifying changes |

**Use system-mapping BEFORE you start, impact-analysis AFTER you plan changes.**

---

## 5-Point Protocol

### Point 1: Architecture Mapping

**Question:** What is the structural context of this code?

**Actions:**
- [ ] Identify all files that will be modified
- [ ] Map the module/package boundaries
- [ ] Find entry points (CLI commands, API endpoints, scheduled jobs)
- [ ] Document component relationships

**Index-enhanced (preferred when PROJECT_INDEX.json exists):**
```
If PROJECT_INDEX.json exists:
  - file_summary(file) → language, functions, classes, imports for each target file
  - Read dir_purposes from index → inferred role of each directory
  - Read tree from index → ASCII directory structure
  - Read _meta.symbol_importance → top entry points by connectivity
  This replaces manual Glob/LS for structural discovery.
```

**Tools (fallback when no index):**
```bash
# Find related files
Glob: pattern="**/[module_name]*.py"

# List directory structure
LS: path="src/[area]/"

# Find entry points
Grep: pattern="@app.route|@click.command|def main|if __name__"
```

**AST-enhanced (preferred when sg available):**
```bash
# Find class definitions structurally
sg run -p 'class $NAME($$$BASES):' -l python src/

# Find decorated entry points (Flask/FastAPI)
sg run -p '@app.route($$$ARGS)
def $NAME($$$PARAMS):' -l python src/

# Find CLI entry points (Click)
sg run -p '@click.command($$$)
def $NAME($$$):' -l python src/

# Find all function definitions in a module
sg run -p 'def $NAME($$$PARAMS):' -l python src/[module]/
```

**Output:**
```markdown
### Architecture
- **Files to modify:** [list]
- **Module:** [package.subpackage]
- **Entry points:** [CLI: cmd_name, API: /endpoint]
- **Related components:** [list with relationships]
```

---

### Point 2: Execution Flow Tracing

**Question:** How does data/control flow through this area?

**Actions:**
- [ ] Trace call chain from entry point to affected code
- [ ] Identify async/sync boundaries
- [ ] Map error propagation paths
- [ ] Note any state mutations

**Index-enhanced (preferred when PROJECT_INDEX.json exists):**
```
If PROJECT_INDEX.json exists:
  - who_calls(target_function, depth=3) → transitive call chain
  - blast_radius(target_function) → callers at each depth level
  This gives the complete call graph without manual Grep.
```

**Tools (fallback when no index):**
```bash
# Find function calls
Grep: pattern="function_name\\(" path="src/"

# Trace async patterns
Grep: pattern="async def|await|asyncio" path="src/[module]/"

# Find error handling
Grep: pattern="except|raise|try:" path="src/[module]/"
```

**AST-enhanced (preferred when sg available):**
```bash
# Find all callers of a function (structural — catches multiline calls)
sg run -p 'target_function($$$ARGS)' -l python src/

# Trace async boundaries
sg run -p 'await $EXPR' -l python src/[module]/

# Map error propagation paths
sg run -p 'raise $EXCEPTION' -l python src/[module]/

# Find all try/except handlers for a specific exception
sg run -p 'except $TYPE as $VAR:' -l python src/

# If sg unavailable, fall back to Grep patterns above
```

**Output:**
```markdown
### Execution Flow
- **Call chain:** entry_point() → handler() → target_function()
- **Async boundaries:** [sync until handler, async after]
- **Error propagation:** [exceptions bubble to handler]
- **State mutations:** [list mutable state touched]
```

---

### Point 3: Logging Inventory

**Question:** What observability exists for this code?

**Actions:**
- [ ] Find logger configuration
- [ ] Document existing log statements in affected area
- [ ] Identify log levels used
- [ ] Note any metrics or tracing

**Tools:**
```bash
# Find logger setup
Grep: pattern="getLogger|logging.config|logger\\s*=" path="src/"

# Find log statements in area
Grep: pattern="logger\\.(debug|info|warning|error|critical)" path="src/[module]/"

# Find structured logging
Grep: pattern="structlog|extra=|LogRecord" path="src/"
```

**Output:**
```markdown
### Logging
- **Logger:** [name, e.g., `__name__` or `app.module`]
- **Config:** [file or inline, format]
- **Current coverage:**
  - Entry: [logged/not logged]
  - Success: [logged/not logged]
  - Errors: [logged/not logged]
- **Gaps:** [what's missing]
```

---

### Point 4: Dependency Analysis

**Question:** What does this code depend on, and what depends on it?

**Actions:**
- [ ] List imports in affected files
- [ ] Identify external service calls (APIs, databases)
- [ ] Check for version-sensitive dependencies
- [ ] Find reverse dependencies (what imports this module)

**Index-enhanced (preferred when PROJECT_INDEX.json exists):**
```
If PROJECT_INDEX.json exists:
  - dependency_chain(file_path, depth=5) → transitive import tree
  - Read deps from index → per-file import list
  This gives the full forward dependency graph instantly.
  For reverse deps (who imports this), still use Grep.
```

**Tools (fallback when no index):**
```bash
# Find imports in file
Grep: pattern="^import|^from" path="src/[file].py"

# Find external calls
Grep: pattern="requests\\.|httpx\\.|aiohttp|client\\." path="src/[module]/"

# Find database usage
Grep: pattern="session\\.|query\\(|execute\\(" path="src/[module]/"

# Find reverse dependencies
Grep: pattern="from [module] import|import [module]" path="src/"
```

**AST-enhanced (preferred when sg available):**
```bash
# Structural import detection (distinguishes import forms)
sg run -p 'from $MODULE import $$$NAMES' -l python src/
sg run -p 'import $MODULE' -l python src/

# Find who imports a specific module
sg run -p 'from [module] import $$$' -l python src/
sg run -p 'import [module]' -l python src/

# Find all external API calls (method calls on known clients)
sg run -p 'self.client.$METHOD($$$ARGS)' -l python src/

# If sg unavailable, fall back to Grep patterns above
```

**Output:**
```markdown
### Dependencies
- **Internal imports:** [list modules]
- **External packages:** [list with versions if critical]
- **Service calls:**
  - Database: [yes/no, which]
  - External APIs: [list]
  - Message queues: [list]
- **Reverse dependencies:** [modules that import this]
```

---

### Point 5: Environment Scan

**Question:** What runtime configuration affects this code?

**Actions:**
- [ ] List environment variables used
- [ ] Find configuration files loaded
- [ ] Identify feature flags
- [ ] Document required secrets/credentials

**Tools:**
```bash
# Find env var usage
Grep: pattern="os\\.environ|getenv|ENV\\[" path="src/[module]/"

# Find config loading
Grep: pattern="load_dotenv|config\\.|settings\\." path="src/[module]/"

# Find feature flags
Grep: pattern="feature_flag|is_enabled|toggle" path="src/[module]/"
```

**Output:**
```markdown
### Environment
- **Env vars:** [VAR_NAME: purpose]
- **Config files:** [list paths]
- **Feature flags:** [list with current states if known]
- **Secrets required:** [list, mark as sensitive]
```

---

## Complete Output Template

After performing system mapping, produce this summary:

```markdown
## System Mapping: [Feature/Component Name]

**Date:** [YYYY-MM-DD]
**Scope:** [Brief description of planned changes]

### 1. Architecture
- **Files:** [list]
- **Module:** [package path]
- **Entry points:** [list]
- **Boundaries:** [component relationships]

### 2. Execution Flow
- **Call chain:** A → B → C
- **Async:** [boundaries noted]
- **Errors:** [propagation path]

### 3. Logging
- **Logger:** [name]
- **Coverage:** [assessment]
- **Gaps:** [what to add]

### 4. Dependencies
- **Internal:** [modules]
- **External:** [services]
- **Reverse:** [dependents]

### 5. Environment
- **Env vars:** [list]
- **Config:** [files]
- **Flags:** [list]

### Risk Assessment
- **Blast radius:** [small/medium/large]
- **Key concerns:** [list]
- **Mitigation:** [approach]

---
*System mapping complete. Ready to proceed with changes.*
```

---

## Integration with AA-MA

When working within an AA-MA plan:

1. **Perform system mapping** at the start of each milestone touching code
2. **Add findings** to `[task]-reference.md` as immutable facts
3. **Log the mapping** in `[task]-context-log.md`
4. **Reference in provenance** if significant discoveries made

**Example reference.md entry:**
```markdown
## System Context: [Module Name]

Entry point: src/cli/main.py:cmd_process
Logger: app.processing (INFO level)
Key env vars: PROCESSING_TIMEOUT, API_KEY
Dependencies: httpx, pydantic, sqlalchemy
```

---

## Quick Reference

```
5-POINT PROTOCOL
│
├── 1. ARCHITECTURE
│   └── Files, modules, entry points, boundaries
│
├── 2. EXECUTION FLOW
│   └── Call chains, async, errors, state
│
├── 3. LOGGING
│   └── Logger config, coverage, gaps
│
├── 4. DEPENDENCIES
│   └── Imports, services, reverse deps
│
└── 5. ENVIRONMENT
    └── Env vars, config, flags, secrets

TRIGGERS (When to Use)
├── 3+ files changing
├── Unfamiliar code
├── External integrations
└── Data pipeline modifications

OUTPUT
└── Summary with risk assessment
```

---

## Cross-References

- `Skill(operational-constraints)` - Parent skill with full operational rules
- `Skill(aa-ma-plan-workflow)` - Invokes system-mapping in Phase 3 when triggers match
- `Skill(impact-analysis)` - Use AFTER system mapping to assess change risk
- `/codebase-deep-dive` - For comprehensive codebase audits
- `Skill(ast-grep)` - For structural code search during flow tracing
