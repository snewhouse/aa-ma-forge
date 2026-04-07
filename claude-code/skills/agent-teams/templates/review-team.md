# Review Team Template

A ready-to-use template for spawning a parallel review team that examines code
through three independent lenses: quality, security, and test coverage.

## Configuration

| Setting        | Value                          |
|----------------|--------------------------------|
| Team name      | `review-{target}`              |
| Team type      | REVIEW                         |
| Debate mode    | No                             |
| Quality gates  | Consolidated findings review   |

## Roles

### Code Quality Reviewer

- **Agent type**: `superpowers:code-reviewer` (fallback: `code-reviewer`)
- **Lens**: Code quality, readability, patterns, maintainability
- **Spawn prompt**:

> Review `{target_files_or_scope}` for code quality issues.
> Checks to perform:
> - Naming conventions and consistency
> - Code organization and module structure
> - DRY violations and duplicated logic
> - Cyclomatic complexity and deep nesting
> - Error handling completeness and consistency
> - API contract adherence and documentation alignment
>
> Report every finding with a severity level (Critical / Important / Minor / Info).
> Use the standard code-reviewer output format.

### Security Reviewer

- **Agent type**: `security-scanning:security-auditor` (fallback: `security-pro:security-auditor`)
- **Lens**: Security vulnerabilities, OWASP, auth, input validation
- **Spawn prompt**:

> Review `{target_files_or_scope}` for security vulnerabilities.
> Checks to perform:
> - Injection vulnerabilities (SQL, command, template)
> - Authentication and authorization bypasses
> - Sensitive data exposure (secrets, PII, tokens in logs)
> - Cross-Site Request Forgery (CSRF) vectors
> - Cross-Site Scripting (XSS) vectors
> - Insecure deserialization and dependency risks
>
> Report findings with CVSS-style severity ratings.
> Reference OWASP Top 10 categories where applicable.

### Test Coverage Reviewer

- **Agent type**: `codebase-cleanup:test-automator` (fallback: `unit-testing:test-automator`)
- **Lens**: Test quality, coverage gaps, missing edge cases
- **Spawn prompt**:

> Review test coverage for `{target_files_or_scope}`.
> Checks to perform:
> - Missing test cases for public functions and methods
> - Edge case coverage (empty inputs, boundary values, error paths)
> - Test quality (meaningful assertions, no tautological tests)
> - Mock and stub appropriateness (over-mocking, missing integration tests)
> - Flaky test indicators (timing, ordering, shared state)
>
> Report coverage gaps with priority (Critical / Important / Minor).
> Suggest specific tests to add, with brief descriptions of each.

## Tasks Setup

```
Task 1: "Code quality review of {target}"    -> assign to Code Quality Reviewer
Task 2: "Security review of {target}"        -> assign to Security Reviewer
Task 3: "Test coverage review of {target}"   -> assign to Test Coverage Reviewer
Task 4: "Consolidate review findings"        -> assign to lead, addBlockedBy: [1, 2, 3]
```

Tasks 1-3 are independent and run in parallel.
Task 4 (consolidation) is blocked until all three reviews complete.

## Finding Severity Levels

| Severity   | Definition                                    | Action Required       |
|------------|-----------------------------------------------|-----------------------|
| Critical   | Security vulnerability, data loss risk, crash | Must fix before merge |
| Important  | Bug potential, significant quality issue       | Should fix before merge |
| Minor      | Style, naming, minor improvement              | Nice to have          |
| Info       | Observation, suggestion, FYI                  | No action needed      |

## Consolidation Protocol

After all three reviewers report back, the lead performs consolidation:

1. **Collect** all findings from the three reviewer reports.
2. **Deduplicate** -- merge identical issues found by multiple reviewers and note
   which reviewers independently flagged each one (stronger signal).
3. **Cross-reference** -- link related findings across lenses (e.g., a missing
   input validation issue flagged by both the security and quality reviewers).
4. **Priority sort** -- order findings: Critical, then Important, then Minor, then Info.
5. **Present** the consolidated report to the user in the format below.

## Expected Deliverable

```markdown
# Review Report: {target}

## Summary
- Reviewers: {count}
- Total findings: {count}
- Critical: {count} | Important: {count} | Minor: {count} | Info: {count}

## Critical Findings
{numbered list with reviewer attribution and file:line references}

## Important Findings
{numbered list with reviewer attribution and file:line references}

## Minor Findings
{numbered list}

## Recommendations
{prioritized action items}

## Scope Reviewed
- Files: {list}
- Reviewers: Code Quality, Security, Test Coverage
```

## Usage Example

```
1. TeamCreate  -> team_name: "review-auth-module"
2. TaskCreate  -> "Code quality review of src/auth/"       (assign: quality-reviewer)
3. TaskCreate  -> "Security review of src/auth/"           (assign: security-reviewer)
4. TaskCreate  -> "Test coverage review of src/auth/"      (assign: test-reviewer)
5. TaskCreate  -> "Consolidate review findings"            (assign: lead, blockedBy: [1,2,3])
6. Spawn three reviewer agents in parallel
7. Wait for all three to complete and mark tasks done
8. Lead runs consolidation protocol and delivers report
```
