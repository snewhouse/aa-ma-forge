# [task-name] Reference

<!-- Copy this template to .claude/dev/active/[task-name]/[task-name]-reference.md -->
<!-- Replace all [bracketed-values] with actual content -->
<!-- -->
<!-- PURPOSE: This file stores IMMUTABLE FACTS extracted from the plan and codebase. -->
<!-- It is the highest-priority file for context injection — load this first when -->
<!-- context is constrained. -->
<!-- -->
<!-- RULES: -->
<!--   - Only store verified, factual information — never opinions or decisions -->
<!--   - Facts must come from the plan, codebase, API docs, or research — never from memory -->
<!--   - Update this file whenever a new fact is discovered during execution -->
<!--   - Never delete facts — if a fact becomes obsolete, mark it as such -->
<!--   - This file is the SINGLE SOURCE OF TRUTH for all constants and paths in the task -->

**Immutable facts and constants for this task.**

_Last Updated: [YYYY-MM-DD HH:MM]_

---

## API Endpoints

<!-- EXTRACTION RULE: Any URL with a path component found in the plan or research. -->
<!-- Include: base URL, environment variants, authentication scheme, and header names. -->
<!-- Verify against OpenAPI spec or official docs — never infer from memory. -->

<!-- Example entries: -->
<!-- - Production: https://api.example.com/v1/ -->
<!-- - Staging: https://staging-api.example.com/v1/ -->
<!-- - Auth: X-API-Key header (not Bearer token) -->
<!-- - Rate limit: 100 req/min -->

| Endpoint | URL | Auth | Notes |
|----------|-----|------|-------|
| [name] | [full URL] | [auth scheme] | [rate limits, versioning] |

## File Paths

<!-- EXTRACTION RULE: Any string matching src/, tests/, .claude/, or containing / -->
<!-- with a file extension. Separate "files to create" from "files to modify". -->

### Files to Create

<!-- Files that do not yet exist and will be created by this task. -->

- `[path/to/new/file.py]` — [purpose]

### Files to Modify

<!-- Existing files that will be changed by this task. -->

- `[path/to/existing/file.py]` — [what changes]

### Key Directories

<!-- Important directory paths referenced across the task. -->

- `[path/to/directory/]` — [purpose]

## Configuration

<!-- EXTRACTION RULE: Any KEY=value pattern, environment variable reference, -->
<!-- or configuration setting. NEVER store actual secrets here. -->

### Environment Variables

<!-- List every env var the task reads or sets. Each must have a corresponding -->
<!-- os.getenv() call somewhere in the source code. -->

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| [VAR_NAME] | [default or "none"] | [yes/no] | [what it controls] |

### Config Files

<!-- Configuration files and their key settings. -->

- `[path/to/config.yaml]`:
  - `[key]`: [value] — [purpose]

## Dependencies

<!-- EXTRACTION RULE: Any package==version or package>=version pattern. -->
<!-- Classify each: Required | Optional extra | Dev-only -->
<!-- Test: "Can a user use the library's core value without this package?" -->
<!--   If yes → Optional. If no → Required. -->

| Package | Version | Class | Purpose |
|---------|---------|-------|---------|
| [package-name] | [>=version or ==version] | [Required/Optional/Dev-only] | [why needed] |

## Constants

<!-- EXTRACTION RULE: Any numeric threshold, limit, timeout, or magic number -->
<!-- mentioned as a design decision in the plan. -->

| Constant | Value | Context |
|----------|-------|---------|
| [NAME] | [value] | [where used and why this value] |

## Schema Definitions

<!-- EXTRACTION RULE: Data models, API response shapes, database schemas. -->
<!-- Before documenting: count fields in the actual source (golden file, OpenAPI spec). -->
<!-- The documentation must cover ALL fields. -->
<!-- If the full schema is unknown, mark: > INCOMPLETE — verify against golden data -->

### [Schema Name]

<!-- Document all fields. State field count explicitly: -->
<!-- "Source has N fields — N documented below." -->

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| [field_name] | [type] | [yes/no] | [purpose] |

## Temporal Validity Convention

<!-- OPTIONAL: Facts may include date markers to express when they were established -->
<!-- or when they became obsolete. Entries without markers are assumed always-valid. -->
<!-- -->
<!-- Three formats: -->
<!--   [valid: YYYY-MM-DD]                    — fact valid from this date onward -->
<!--   [valid: YYYY-MM-DD to YYYY-MM-DD]      — fact valid within a date range -->
<!--   [superseded: YYYY-MM-DD by task-name]   — fact replaced by a newer task -->
<!-- -->
<!-- The AA-MA Scribe applies [valid: date] when extracting new facts. -->
<!-- When a fact becomes obsolete, add [superseded: ...] rather than deleting. -->

**Examples:**

| Fact | Marker |
|------|--------|
| Auth API: `https://api.example.com/v1/auth` | `[valid: 2026-04-10]` |
| Legacy API: `https://old.example.com/v1/` | `[superseded: 2026-04-10 by api-migration]` |
| Max retries: 3 | `[valid: 2026-03-01 to 2026-04-15]` |
| Max retries: 5 | `[valid: 2026-04-15]` |

## External References

<!-- URLs to documentation, specs, or resources that agents need during execution. -->
<!-- These are READ-ONLY references — not endpoints the code calls. -->

- [Description]: [URL]

## Glossary

<!-- Domain-specific terms used in this task that might be ambiguous. -->
<!-- Especially important for cross-team or cross-domain tasks. -->

| Term | Definition |
|------|-----------|
| [term] | [precise definition in context of this task] |

---

<!-- WHEN TO UPDATE THIS FILE: -->
<!-- -->
<!--   - After plan approval: initial extraction from plan.md -->
<!--   - After each task completion: add any new facts discovered during implementation -->
<!--   - After research: add verified findings (API responses, schema discoveries) -->
<!--   - After bug fixes: add corrected facts (wrong paths, changed endpoints) -->
<!--   - NEVER during speculative planning — only add facts you have evidence for -->
<!-- -->
<!-- WHAT DOES NOT BELONG HERE: -->
<!-- -->
<!--   - Decisions (those go in context-log.md) -->
<!--   - Status or progress (those go in tasks.md) -->
<!--   - Opinions or trade-off analysis (those go in context-log.md) -->
<!--   - Secrets, passwords, or tokens (those go in .env, never in AA-MA files) -->
