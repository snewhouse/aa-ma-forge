---
name: token-compression
description: >
  Output token compression for AA-MA workflows. Reduces response tokens by 40-75%
  while preserving full technical accuracy. Three intensity levels mapped to execution
  modes: lite (HITL), full (general), ultra (AFK). Auto-activates during AA-MA
  execution based on task Mode field. Manual activation via /compress lite|full|ultra.
---

# Token Compression

Reduce output tokens while preserving technical substance. Inspired by
[caveman](https://github.com/JuliusBrussee/caveman) prompt compression patterns,
adapted for AA-MA execution mode integration.

## Activation

- **Automatic:** During AA-MA execution, intensity is set by task Mode field
  - `Mode: HITL` → lite (preserve clarity for human review)
  - `Mode: AFK` → ultra (maximum compression for autonomous execution)
- **Manual:** `/compress lite|full|ultra` to override during any session
- **Default:** `full` when activated outside AA-MA execution context

## Rules

Drop: articles (a/an/the), filler (just/really/basically/actually/simply),
pleasantries (sure/certainly/of course/happy to), hedging (it might be worth,
you could consider). Fragments OK. Short synonyms (big not extensive, fix not
"implement a solution for"). Technical terms exact. Code blocks unchanged.
Errors quoted exact.

Pattern: `[thing] [action] [reason]. [next step].`

Not: "Sure! I'd be happy to help you with that. The issue you're experiencing is likely caused by..."
Yes: "Bug in auth middleware. Token expiry check use `<` not `<=`. Fix:"

## Intensity Levels

| Level | Rules | When |
|-------|-------|------|
| **lite** | No filler/hedging. Keep articles + full sentences. Professional but tight. | HITL tasks, complex explanations, user-facing content |
| **full** | Drop articles, fragments OK, short synonyms. | General use, default level |
| **ultra** | Abbreviate (DB/auth/config/req/res/fn/impl), strip conjunctions, arrows for causality (X → Y), one word when one word enough. | AFK tasks, autonomous execution, subagent output |

### Examples

**"Why does the test fail?"**
- lite: "The test fails because the mock returns an empty list instead of the expected user objects. Update the mock fixture to return test data."
- full: "Mock returns empty list, not expected user objects. Update mock fixture with test data."
- ultra: "Mock → empty list. Need test data in fixture."

**"Explain the deployment pipeline."**
- lite: "The pipeline runs lint, tests, and builds a Docker image. On merge to main, it deploys to staging automatically. Production requires manual approval."
- full: "Pipeline: lint → test → Docker build. Merge to main = auto-deploy staging. Prod needs manual approval."
- ultra: "lint→test→Docker→staging(auto). Prod=manual."

## Auto-Clarity Exceptions

Drop compression for:
- Security warnings and vulnerability disclosures
- Irreversible action confirmations (DELETE, DROP, force-push)
- Multi-step sequences where fragment order risks misinterpretation
- User appears confused or asks for clarification

Resume compression after the clear section is complete.

**Example — destructive operation:**
> **Warning:** This will permanently delete all rows in the `users` table and cannot be undone.
> ```sql
> DROP TABLE users;
> ```
> Compression resume. Verify backup first.

## Boundaries

- Code blocks: always rendered normally, never compressed
- Commit messages: follow Conventional Commits format, never compressed
- PR descriptions: write normally
- Error messages: quote exact, never paraphrase
- `/compress off` or "normal mode": deactivate compression
- Level persists until changed or session end

## Integration with AA-MA Execution

When the `aa-ma-execution` skill detects a task's `Mode:` field:

```
Mode: AFK  → Skill(token-compression) at ultra
Mode: HITL → Skill(token-compression) at lite
No Mode    → Skill(token-compression) at full (default)
```

This mapping ensures autonomous agents produce minimal output (saving tokens
for reasoning), while human-interactive sessions preserve enough context for
the user to follow along.
