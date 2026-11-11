# TypeScript / JavaScript card

Source: `docs/research/code-conventions-impact-language-cards.md` (Card 1, state of sources 2026-10-08).

| Slot | Convention |
|------|-----------|
| Compiler | Set `strict: true` explicitly (the default since TS 6.0) and add `noUncheckedIndexedAccess` and `exactOptionalPropertyTypes`, which `strict` does not include. |
| Formatter | Prettier *or* Biome, never both. Prettier is the default; Biome only for TS/JSON-only repos that want one tool (it deliberately diverges from Prettier output). |
| Linter | ESLint 10, flat config, typescript-eslint `recommendedTypeChecked` with `parserOptions.projectService: true`. Pin the version if you adopt `strict-type-checked` (not semver-stable). |
| Security lint | `eslint-plugin-security` as review prompts only — it is false-positive heavy; never a hard gate. |
| Doc comments | `/** … */` with `@param`, `@returns`, `@throws` on exported symbols; TSDoc syntax in `.ts`, the JSDoc tags TS understands in `.js` with `// @ts-check`. Do not repeat types in tags. |
| Suppressions | `// eslint-disable-next-line <rule> -- why: …`; prefer `// @ts-expect-error -- why: …` over `@ts-ignore`. |
| Logging | pino. It defaults to **stdout**, so a CLI or hook must log to stderr: `pino(pino.destination(2))`. Log errors as `logger.error({ err }, "msg")`; `redact: [...]` for secrets and PII; never pass an untrusted object as the first argument — nest it under a key. A library takes a logger (or a child of its caller's); only the entrypoint creates and configures pino. |
| Tests | Vitest 5; `node:test` for zero-dependency libraries and scripts. |
| Supply chain | Commit the lockfile. CI runs `npm audit --audit-level=high` (or `pnpm audit --prod --audit-level=high`) and `npm audit signatures`. Add a release-age delay (`min-release-age` / pnpm `minimumReleaseAge`); on npm set `ignore-scripts=true`. |
| Secrets | Env only; `node --env-file=.env` in dev with `.env` git-ignored. |

## Pitfalls the tools miss

1. Without `noUncheckedIndexedAccess`, `arr[i]` is typed non-null.
2. Floating promises and `any` flow are caught only by the *type-checked* lint configs.
3. `catch (e)` is `unknown` (`useUnknownInCatchVariables`): narrow before use.
4. SQL: `$1` placeholders for values; identifiers cannot be bound — allow-list them or use `pg-format`.
5. A CLI whose stdout is data must keep every log line off stdout.
