---
name: language-conventions
description: "Per-language convention cards: which formatter, linter, doc-comment format, logger, test runner, dependency audit and secrets idiom to use, and the pitfalls those tools miss. TypeScript/JavaScript, R and SQL have full cards; Python, Bash and Markdown point to their topic skills. Use when writing or reviewing code in one of these languages, setting up its tooling, or asking what its conventions are."
---

# Language conventions

Read the card for the file's language, then apply it to touched code only (no backfill). Each card pins one tool per slot and lists the failure modes that tool cannot catch.

| Language | Card | Depth |
|----------|------|-------|
| TypeScript / JavaScript | [references/typescript.md](references/typescript.md) | card |
| R | [references/r.md](references/r.md) | card |
| SQL | [references/sql.md](references/sql.md) | card |
| Python | [references/python.md](references/python.md) | pointer to topic skills |
| Bash | [references/bash.md](references/bash.md) | pointer to topic skills |
| Markdown | [references/markdown.md](references/markdown.md) | pointer to topic skills |

## Rules every card shares

- Comments say *why*, not *what*. Every suppression carries its reason: `# noqa: X  # why: …`, `// eslint-disable-next-line rule -- why: …`, `# nolint: why: …`, `-- noqa: why: …`.
- Logs go to stderr and data to stdout. A library never configures logging; the entrypoint does.
- Public API is documented in the language-native format (Google `Args:` in Python, TSDoc/JSDoc `@param` in TS/JS, roxygen2 in R). The shared rule is *which* symbols need a doc block (exported/public), not one syntax.
- No silent failures: every caught error logs one line or bumps a reported counter.
- Commit the lockfile and audit it in CI; secrets come from the environment, never from source, comments or logs.
- One formatter per repo. Do not state a cross-language line length; use each formatter's default.

## Related

- `Skill(secops)` — which security scanner runs where (osv-scanner covers JS and R lockfiles).
- `Skill(logging-and-comments)` — the full logging and comment standard (Python and Bash).
