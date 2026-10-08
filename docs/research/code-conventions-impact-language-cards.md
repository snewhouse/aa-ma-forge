# What should the short TS/JS, R and SQL convention cards contain?

**Created:** 2026-10-08
**Author:** aa-ma-researcher (Claude), for chart effort `code-conventions-impact` (Ticket 3)
**Reviewed-Through-Date:** 2026-10-08 (state of sources on this date)
**Valid-Through:** 2027-Q1 (invalidated by: a TypeScript 7.x defaults change, ESLint 11, Biome 3, Vitest 6, Air 1.0 or a lintr/Air merge, SQLFluff 5, or pnpm/npm supply-chain default changes)
**Sources:**
- https://devblogs.microsoft.com/typescript/announcing-typescript-6-0/ — TS 6.0 (2026-03-23) makes `strict: true` the default
- https://devblogs.microsoft.com/typescript/?p=5246 — TS 7.0 (Go-native) GA 2026-07-08 (official post, seen via search snippet only)
- https://www.typescriptlang.org/tsconfig/#strict — strict family; `noUncheckedIndexedAccess` / `exactOptionalPropertyTypes` are outside it
- https://typescript-eslint.io/users/configs — recommended / strict / *-type-checked configs; strict not semver-stable
- https://eslint.org/blog/ — ESLint v10.12.0 current; v9 EOL 2026-08-06
- https://github.com/eslint-community/eslint-plugin-security , https://registry.npmjs.org/eslint-plugin-security — 15 rules, false-positive warning, v4.2.0 published 2026-10-01
- https://prettier.io/blog , https://biomejs.dev/blog/ , https://biomejs.dev/internals/language-support/ , https://biomejs.dev/formatter/differences-with-prettier/ — Prettier 3.9; Biome 2.5; language coverage; intentional Prettier divergence
- https://tsdoc.org/ , https://registry.npmjs.org/@microsoft/tsdoc , https://www.typescriptlang.org/docs/handbook/jsdoc-supported-types.html — TSDoc status; JSDoc tags TS checks in .js
- https://github.com/pinojs/pino , https://github.com/pinojs/pino/blob/main/docs/api.md , https://github.com/pinojs/pino/blob/main/docs/redaction.md — pino 10.4.0; stdout default; `err` serializer; redaction
- https://vitest.dev/blog , https://vitest.dev/blog/vitest-5 , https://nodejs.org/api/test.html — Vitest 5.0 (2026-09-03); `node:test` stable since Node 20
- https://docs.npmjs.com/cli/v11/commands/npm-audit , https://docs.npmjs.com/cli/v11/using-npm/config , https://pnpm.io/cli/audit , https://pnpm.io/settings/dependency-resolution , https://pnpm.io/supply-chain-security — audit, signatures, `min-release-age`, `minimumReleaseAge`, build-script blocking
- https://nodejs.org/api/cli.html — `--env-file` no longer experimental (v24.10.0 / v22.21.0)
- https://style.tidyverse.org/ , https://style.tidyverse.org/functions.html , https://style.tidyverse.org/pipes.html — tidyverse style guide; why-not-what comments; base `|>`
- https://www.tidyverse.org/blog/2025/02/air/ , https://posit-dev.github.io/air/formatter.html , https://github.com/posit-dev/air/releases , https://posit-dev.github.io/air/integration-pre-commit.html — Air formatter, 0.12.0 (2026-10-01), pre-commit hook
- https://cran.r-project.org/package=lintr , https://raw.githubusercontent.com/r-lib/lintr/main/NEWS.md , https://lintr.r-lib.org/reference/index.html , https://lintr.r-lib.org/reference/undesirable_function_linter.html — lintr 3.4.0 (2026-07-16); no security tag
- https://cran.r-project.org/package=styler — styler 1.11.0 (2025-10-13)
- https://roxygen2.r-lib.org/articles/roxygen2.html — `#'` blocks, tags, generates `man/*.Rd` + NAMESPACE
- https://daroczig.github.io/logger/ , https://daroczig.github.io/logger/reference/index.html , https://daroczig.github.io/logger/articles/r_packages.html , https://cran.r-project.org/package=logger — logger 0.4.3 (2026-08-24); `layout_json`; namespaces
- https://testthat.r-lib.org/articles/third-edition.html — testthat 3e activation
- https://rstudio.github.io/renv/articles/renv.html — renv lockfile workflow
- https://google.github.io/osv-scanner/supported-languages-and-lockfiles/ , https://github.com/RConsortium/r-advisory-database , https://cran.r-project.org/package=oysteR , https://cran.r-project.org/package=riskmetric — R/JS lockfile scanning; CRAN advisories in OSV
- https://httr2.r-lib.org/articles/wrapping-apis.html — R secrets idiom
- https://dbi.r-dbi.org/reference/dbBind.html — DBI parameter binding
- https://docs.sqlfluff.com/en/stable/reference/dialects.html , https://github.com/sqlfluff/sqlfluff/releases , https://docs.sqlfluff.com/en/stable/production/pre_commit.html , https://docs.sqlfluff.com/en/stable/configuration/rule_configuration.html , https://docs.sqlfluff.com/en/stable/reference/rules.html , https://docs.sqlfluff.com/en/stable/reference/rules/ambiguous.html — SQLFluff 4.4.0, 28 dialects, hooks, `core` group, AM04
- https://docs.getdbt.com/best-practices/how-we-style/2-how-we-style-our-sql , https://www.sqlstyle.guide/ , https://github.com/mattm/sql-style-guide — the three SQL style guides
- https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html , https://www.psycopg.org/psycopg3/docs/basic/params.html , https://node-postgres.com/features/queries — injection defences, identifier handling
- https://www.postgresql.org/docs/current/sql-comment.html , https://docs.getdbt.com/reference/resource-configs/persist_docs — catalog comments
- https://docs.getdbt.com/docs/build/unit-tests , https://pgtap.org/ — SQL test runners
- pyproject.toml:71-95 , .github/workflows/security.yml:16-55 , ~/.claude/CLAUDE.md:63 — current forge Python conventions and CI surface

## Answer

Each card should pin one tool per slot and the 3–5 failure modes that tool cannot catch. **TS/JS:** TS `strict` (the default since 6.0) plus `noUncheckedIndexedAccess`, typescript-eslint `recommended-type-checked` (and `strict-type-checked` only if pinned), Prettier *or* Biome (pick one per repo), TSDoc for `.ts` / JSDoc for `.js`, pino to stderr, Vitest, and `pnpm`/`npm audit` with release-age delay. **R:** tidyverse style formatted by Air (styler as the fallback), lintr, roxygen2, logger, testthat 3e, renv, and osv-scanner on `renv.lock`. **SQL:** SQLFluff with an explicit dialect, the dbt SQL style (lowercase, trailing commas, CTEs), parameterised queries plus allow-listed identifiers, and catalog comments (`COMMENT ON` / dbt `description` + `persist_docs`). The fit with the Python conventions is mostly clean. The real conflicts are pino's stdout default against the forge's "logs → stderr" rule, the docstring tag vocabularies (Google `Args:` vs `@param`), and SQL keyword case, where the published guides disagree.

## Evidence

### Card 1 — TypeScript / JavaScript

| Slot | Convention | Cite |
|---|---|---|
| Compiler | `strict: true` is the default since TS 6.0 (2026-03-23). Still set it explicitly in `tsconfig.json`. Also add `noUncheckedIndexedAccess` and `exactOptionalPropertyTypes`: both are **not** part of `strict`. TS 6.0 also defaults `module: esnext`, `types: []` and `noUncheckedSideEffectImports: true`. TS 7.0, the Go-native compiler, went GA on 2026-07-08 and uses the same `tsc` entrypoint. | https://devblogs.microsoft.com/typescript/announcing-typescript-6-0/ ; https://www.typescriptlang.org/tsconfig/#strict ; https://devblogs.microsoft.com/typescript/?p=5246 (search snippet) |
| Formatter | One per repo, never both. **Prettier 3.9** (2026-06-27) is the conservative default. **Biome 2.5** (2026-06-05) formats *and* lints JS/TS/JSON/CSS/GraphQL. Its HTML/Vue/Svelte support is experimental and YAML/Markdown are unfinished, and it "intentionally" diverges from Prettier output. Choose Biome only for TS/JSON-only repos that want one fast tool. | https://prettier.io/blog ; https://biomejs.dev/blog/ ; https://biomejs.dev/internals/language-support/ ; https://biomejs.dev/formatter/differences-with-prettier/ |
| Linter | ESLint **v10** with flat config. v9 reached end of life on 2026-08-06. Add typescript-eslint `recommendedTypeChecked` with `parserOptions.projectService: true`. `strict` / `strict-type-checked` are "not considered stable under semver", so pin the version if you adopt them. If Biome is chosen, its linter replaces ESLint for style, but typed rules still need typescript-eslint. | https://eslint.org/blog/ ; https://typescript-eslint.io/users/configs |
| Security lint | `eslint-plugin-security` is maintained: v4.2.0 shipped 2026-10-01, with 15 rules such as `detect-eval-with-expression`, `detect-child-process`, `detect-non-literal-fs-filename`, `detect-unsafe-regex` and `detect-bidi-characters`. The README warns it "finds a lot of false positives which need triage by a human", so treat findings as review prompts, not a hard gate. | https://github.com/eslint-community/eslint-plugin-security ; https://registry.npmjs.org/eslint-plugin-security |
| Doc comments | Use `/** … */` with `@param`, `@returns` and `@throws` on exported symbols. In `.ts`, follow TSDoc syntax: still a "proposal" with the reference parser `@microsoft/tsdoc` at 0.17.1, lintable with `eslint-plugin-tsdoc`. Do not repeat types in tags. In `.js` with `// @ts-check`, use the JSDoc tags TS understands (`@type`, `@param {T}`, `@returns`, `@typedef`, `@template`). | https://tsdoc.org/ ; https://registry.npmjs.org/@microsoft/tsdoc ; https://www.typescriptlang.org/docs/handbook/jsdoc-supported-types.html |
| Comments | The language-neutral core applies: comments say *why*, not *what*. Every `eslint-disable-next-line <rule>` and `// @ts-expect-error` carries a `-- why:` reason. Prefer `@ts-expect-error` over `@ts-ignore`. *(The house rule mirrors `# why:` in ~/.claude/CLAUDE.md. The TS directive preference is not verified here.)* | ~/.claude/CLAUDE.md:63 (house rule) |
| Logging | Use **pino** (10.4.0). It writes JSON lines and defaults to **stdout**, so CLIs and hooks must pass `pino.destination(2)`. Log errors as `logger.error({ err }, 'msg')` so the `err` serializer captures the stack. Never pass untrusted objects as the merging object. Use `redact: [...]` for secrets and PII; it costs about 2% without wildcards. Run transports in a worker via `pino.transport`. | https://github.com/pinojs/pino/blob/main/docs/api.md ; https://github.com/pinojs/pino/blob/main/docs/redaction.md ; https://github.com/pinojs/pino |
| Tests | Use **Vitest 5** (2026-09-03), which needs Vite ≥ 6.4 and Node ≥ 22.12. It now fails on un-awaited `resolves`/`rejects` and defaults to `clearMocks: true`. For zero-dependency libs or scripts, `node:test` is stable since Node 20, with stable snapshots and experimental coverage. | https://vitest.dev/blog ; https://vitest.dev/blog/vitest-5 ; https://nodejs.org/api/test.html |
| Supply chain | Commit the lockfile. Run `npm audit --audit-level=high` (non-zero exit fails CI) or `pnpm audit --prod --audit-level=high`; pnpm 11 queries the bulk advisory endpoint and matches by GHSA. Run `npm audit signatures` to verify registry signatures and provenance. Add a release-age delay: npm `min-release-age=<days>`, or pnpm `minimumReleaseAge`, which defaults to 1440 min since pnpm 11. pnpm ≥ 10 does not run dependency `postinstall` scripts; allow-list them via `allowBuilds`. On npm, set `ignore-scripts=true` (default false). | https://docs.npmjs.com/cli/v11/commands/npm-audit ; https://docs.npmjs.com/cli/v11/using-npm/config ; https://pnpm.io/cli/audit ; https://pnpm.io/settings/dependency-resolution ; https://pnpm.io/supply-chain-security |
| Secrets | Read secrets from env only. Use `node --env-file=.env` in dev, which is no longer experimental since v24.10.0 / v22.21.0; real env vars override the file. `.env` is git-ignored, and secrets never go into `pino` fields unless they are redacted. | https://nodejs.org/api/cli.html |

**Top idioms / pitfalls**
1. Indexed access returns `T | undefined` only under `noUncheckedIndexedAccess`. Without it, `arr[i]` is typed non-null. (tsconfig ref above.)
2. Floating promises and unsafe `any` flow: these are what the *type-checked* configs exist to catch, so untyped `recommended` is not enough. (https://typescript-eslint.io/users/configs)
3. Treat `catch (e)` as `unknown`. This is in the strict family via `useUnknownInCatchVariables`. Narrow before use. (https://www.typescriptlang.org/tsconfig/#strict)
4. SQL from JS: use `$1` placeholders. "PostgreSQL does not support parameters for identifiers", so allow-list or `pg-format` them. (https://node-postgres.com/features/queries)
5. Do not log untrusted objects as pino's first argument; nest them under a key. (https://github.com/pinojs/pino/blob/main/docs/api.md)

### Card 2 — R

| Slot | Convention | Cite |
|---|---|---|
| Style | Follow the **tidyverse style guide**. Use the base pipe `\|>` rather than `%>%`; since R 4.3.0 it covers the magrittr features the guide recommends. Function names are verbs. Use `return()` only for early returns. | https://style.tidyverse.org/pipes.html ; https://style.tidyverse.org/functions.html |
| Formatter | Use **Air** (Posit; Rust; built on Biome's formatter infrastructure). Latest is 0.12.0 (2026-10-01), still pre-1.0. 0.10.0 changed the default assignment style to `<-`. It takes its rules from the tidyverse guide but "occasionally deviate[s]", uses an 80-column default, removes non-persistent line breaks, and supports `# fmt: skip` and `# fmt: skip file`. It is used in dplyr and tidyr. **styler** 1.11.0 (2025-10-13) remains the configurable fallback; the style guide itself still names only styler and lintr. | https://www.tidyverse.org/blog/2025/02/air/ ; https://posit-dev.github.io/air/formatter.html ; https://github.com/posit-dev/air/releases ; https://cran.r-project.org/package=styler ; https://style.tidyverse.org/ |
| Linter | **lintr** 3.4.0 (2026-07-16, R ≥ 4.1). Start from `linters_with_defaults()`. 3.4.0 tracks the updated tidyverse indentation rule and `assignment_linter()` now allows only `<-`. 3.3.0 made `pipe_consistency_linter()` default to `\|>`. The lintr NEWS does not mention Air, so check that lintr's layout linters do not fight Air's output. | https://cran.r-project.org/package=lintr ; https://raw.githubusercontent.com/r-lib/lintr/main/NEWS.md |
| Security lint | lintr has **no security tag**. The closest groups are `executing_linters` and `undesirable_function_linter()`, whose defaults include `setwd`, `source`, `library` (inside functions), `Sys.setenv`, `sink`, `attach` and `browser`. `eval`/`system` are *not* in the default list, so add them explicitly. | https://lintr.r-lib.org/reference/index.html ; https://lintr.r-lib.org/reference/undesirable_function_linter.html |
| Doc comments | Use **roxygen2** `#'` blocks: a title line, then `@param`, `@returns`, `@export` and `@examples`, with Markdown allowed. `devtools::document()` generates `man/*.Rd` and `NAMESPACE`. Plain `#` stays free for ordinary comments. | https://roxygen2.r-lib.org/articles/roxygen2.html |
| Comments | "use comments to explain the 'why' not the 'what' or 'how'" — the same rule as the core. | https://style.tidyverse.org/functions.html |
| Logging | Use **logger** 0.4.3 (2026-08-24): `log_info()`, `log_warn()` and friends with glue formatting. `appender_console` / `appender_stderr` write to **stderr**, and `layout_json()` gives structured lines. A package sets only `log_formatter` and logs under its own namespace. Thresholds, layouts and appenders belong to the end user, which matches the Python "configure only at the entrypoint" rule. | https://cran.r-project.org/package=logger ; https://daroczig.github.io/logger/reference/index.html ; https://daroczig.github.io/logger/articles/r_packages.html ; ~/.claude/CLAUDE.md:63 |
| Tests | **testthat 3rd edition**: set `Config/testthat/edition: 3` in `DESCRIPTION` and create files with `usethis::use_test()`. 3e stops silently swallowing messages and compares via waldo. | https://testthat.r-lib.org/articles/third-edition.html |
| Dependencies / audit | Use **renv**: `init` → `snapshot` → commit `renv.lock` → `restore`. renv does not pin R itself or system libraries. For audit, **osv-scanner** reads `renv.lock`, and the R Consortium advisory DB publishes OSV records under ecosystem `CRAN`. **oysteR** 0.1.4 (2025-10-09, Sonatype OSS Index) is an alternative. **riskmetric** 0.2.7 measures package robustness, not CVEs, so use it for package selection rather than as a CI gate. | https://rstudio.github.io/renv/articles/renv.html ; https://google.github.io/osv-scanner/supported-languages-and-lockfiles/ ; https://github.com/RConsortium/r-advisory-database ; https://cran.r-project.org/package=oysteR ; https://cran.r-project.org/package=riskmetric |
| Secrets | Read keys with `Sys.getenv()` from the user-level `.Renviron` (`usethis::edit_r_environ()`), never typed at the console, because they leak into `.Rhistory`. httr2 `secret_encrypt()` allows committing only ciphertext. Keys in query strings are not redacted by httr2; Authorization headers are. | https://httr2.r-lib.org/articles/wrapping-apis.html |

**Top idioms / pitfalls**
1. Use `<-` for assignment, which Air and lintr 3.4 now both default to. (https://github.com/posit-dev/air/releases ; lintr NEWS)
2. Do not call `library()`, `setwd()` or `source()` inside package or function code; they are lintr undesirable defaults. (https://lintr.r-lib.org/reference/undesirable_function_linter.html)
3. Avoid `sapply`, which is in the default undesirable list because of its unstable return type. Use `vapply` or `purrr::map_*`. (same cite)
4. Bind DB parameters rather than pasting them into the SQL string: "Separation of query syntax and parameters protects against SQL injection." Placeholders are backend-specific (`?`, `$1`, `:name`). (https://dbi.r-dbi.org/reference/dbBind.html)
5. renv does not freeze R, pandoc or system libraries; record those separately, e.g. with rig or Docker. (https://rstudio.github.io/renv/articles/renv.html)

### Card 3 — SQL

| Slot | Convention | Cite |
|---|---|---|
| Style guide | Adopt the **dbt SQL style**: lowercase keywords and identifiers, trailing commas, 4-space indent, ≤ 80 chars, explicit `as`, explicit `inner join`, column prefixes in multi-table joins, `union all` unless de-duplication is intended, import CTEs at the top, single-purpose CTEs, and `select * from <final_cte>` last. Mazur's guide agrees on lowercase, CTEs over subqueries and explicit joins. **sqlstyle.guide is Simon Holywell's guide, not Mazur's**, and it mandates UPPERCASE keywords and "river" alignment, so it conflicts with both. | https://docs.getdbt.com/best-practices/how-we-style/2-how-we-style-our-sql ; https://github.com/mattm/sql-style-guide ; https://www.sqlstyle.guide/ |
| Formatter + linter | **SQLFluff** 4.4.0 (2026-10-02). 4.x adds a Rust parser and the first Rust-native rules. It has 79 rules in 11 categories, and `rules = core` selects the core set. Always set `dialect` explicitly; the 28 dialects include `postgres`, `duckdb` (inherits from postgres), `bigquery`, `snowflake`, `sqlite`, `databricks`, `sparksql` and `tsql`. For dbt, install `sqlfluff-templater-dbt`. 4.2.0 raised `render_variant_limit` to 5, which can surface new violations in Jinja branches. | https://github.com/sqlfluff/sqlfluff/releases ; https://docs.sqlfluff.com/en/stable/reference/rules.html ; https://docs.sqlfluff.com/en/stable/configuration/rule_configuration.html ; https://docs.sqlfluff.com/en/stable/reference/dialects.html |
| "Security" lint | SQLFluff has no injection rules; injection is a host-language concern. The nearest safety rules are AM04 `ambiguous.column_count` (flags `select *`, whose output shape changes when upstream schemas change) and AM05 (fully qualified joins). | https://docs.sqlfluff.com/en/stable/reference/rules/ambiguous.html |
| Doc comments | Persist documentation in the **catalog**, not just the file. Use `COMMENT ON TABLE/COLUMN … IS '…'`; in Postgres 18 *any* connected user can read comments, so never put sensitive data in them. In dbt, write `description:` in YAML plus `+persist_docs: {relation: true, columns: true}`, supported on Postgres, Redshift, Snowflake, BigQuery, Databricks, Spark and Trino. | https://www.postgresql.org/docs/current/sql-comment.html ; https://docs.getdbt.com/reference/resource-configs/persist_docs |
| Comments | Inline comments use `--` per the dbt example. Holywell prefers `/* */`. In dbt models, use Jinja `{# #}` for comments that must not reach compiled SQL. Explain *why*: business rule, grain, de-duplication intent. | https://docs.getdbt.com/best-practices/how-we-style/2-how-we-style-our-sql ; https://www.sqlstyle.guide/ |
| Logging | SQL has no logging idiom of its own. The host language logs query *name/purpose* and row counts, not bound values, which may hold PII. *(Derived from the core rule; no SQL-specific primary source fetched.)* | — |
| Tests | **dbt unit tests** (dbt ≥ 1.8): YAML `given`/`expect` on static fixtures, defined under `models/`, run with `dbt test --select "test_type:unit"` in dev/CI. Data tests check built data. For plain Postgres, use **pgTAP** run via `pg_prove`. | https://docs.getdbt.com/docs/build/unit-tests ; https://pgtap.org/ |
| Injection | Use parameterised queries / prepared statements (OWASP option 1). Escaping is "strongly discouraged". Identifiers cannot be bound: use an allow-list from code, `psycopg.sql.Identifier`, or `pg-format`. Use least-privilege DB accounts and never DBA rights for applications. | https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html ; https://www.psycopg.org/psycopg3/docs/basic/params.html ; https://node-postgres.com/features/queries |
| Supply chain | For dbt, pin packages in `packages.yml` and adapters in `additional_dependencies`. Not otherwise applicable. | https://docs.sqlfluff.com/en/stable/production/pre_commit.html |
| Secrets | Connection credentials live in env vars or the profile, never in `.sql` files or `COMMENT`s. (Postgres comments are world-readable within a DB.) | https://www.postgresql.org/docs/current/sql-comment.html |

**Top idioms / pitfalls**
1. Avoid `select *` in models and views (AM04). Downstream column drift is silent. (sqlfluff ambiguous rules)
2. Never build SQL with string concatenation or `%`/`+`/f-strings; bind values and allow-list identifiers. (OWASP; psycopg)
3. Pin the dialect. DuckDB inherits from postgres in SQLFluff, so Postgres-valid rules can mislead on DuckDB-only syntax. (dialects page)
4. Use `union all` by default; an accidental `union` hides duplicates *and* costs a sort. (dbt style)
5. Use one grain per CTE and name it for what it produces (`events_joined_to_users`). (dbt style)

### CI / pre-commit wiring

The repo has no `.pre-commit-config.yaml` today. Its only CI is `.github/workflows/security.yml:16-55` (ShellCheck, Bandit, `ruff check src/`), so every item below is new surface.

| Language | pre-commit (fast, local) | CI (authoritative) |
|---|---|---|
| TS/JS | `prettier --check` or `biome ci`; `eslint --cache` | `tsc --noEmit`; `eslint` with type-checked config; `vitest run`; `npm audit --audit-level=high` / `pnpm audit --prod`; `npm audit signatures` (https://docs.npmjs.com/cli/v11/commands/npm-audit) |
| R | `posit-dev/air-pre-commit` hook `air-format` (https://posit-dev.github.io/air/integration-pre-commit.html) | `air format --check` (https://posit-dev.github.io/air/); `lintr::lint_dir()`; testthat via `R CMD check`; `osv-scanner` on `renv.lock` |
| SQL | `sqlfluff/sqlfluff` hooks `sqlfluff-lint` / `sqlfluff-fix`; `sqlfluff-fix` skips files with templating errors (https://docs.sqlfluff.com/en/stable/production/pre_commit.html) | `sqlfluff lint`; `dbt test --select "test_type:unit"`; `pg_prove` |
| All | — | `osv-scanner` covers `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lock` and `renv.lock` in one job (https://google.github.io/osv-scanner/supported-languages-and-lockfiles/). This is a candidate single dependency-audit job alongside the Python audit (Ticket 10). |

Do **not** hard-gate on `eslint-plugin-security` (false-positive-heavy, per its README) or on riskmetric (not a vulnerability tool).

### Conflicts with the Python conventions

1. **Docstring vocabulary.** The forge Python standard is Google style (`pyproject.toml:86`, `convention = "google"`: `Args:` / `Returns:` / `Raises:`). TSDoc/JSDoc and roxygen2 use `@param` / `@returns` / `@throws`. The core should require "public API documented in the language-native format" rather than one cross-language syntax. The shared rule is *which* symbols need a doc block: exported/public only, mirroring ruff `D1` at `pyproject.toml:77`.
2. **Logging stream.** The house rule is "Logs → stderr, data → stdout" (`~/.claude/CLAUDE.md:63`). pino defaults to stdout, a 12-factor service convention, so the TS card must require `pino.destination(2)` for CLIs and hooks or carve out an exception for long-running services (a decision for Ticket 9). R logger's console appender already writes to stderr.
3. **TODO format.** Python enforces `TODO(owner/issue): text` via ruff `TD` (`pyproject.toml:78`). I did not verify an equivalent lint for ESLint, lintr or SQLFluff, so it stays convention-only outside Python.
4. **Line length.** Air and the dbt style both use 80 columns. `pyproject.toml` sets no `line-length` (ruff default applies), so the core should not state one cross-language number.
5. **SQL keyword case.** This is not a Python conflict but an inter-guide one: dbt and Mazur say lowercase, Holywell (sqlstyle.guide) says UPPERCASE. Pick lowercase, which matches dbt and SQLFluff's dbt-centric ecosystem, and enforce it via the SQLFluff capitalisation rules.
6. **Suppression rationale.** The `# why:` rule on `noqa` (`~/.claude/CLAUDE.md`) carries over directly as `// eslint-disable-next-line rule -- why: …`, `# nolint: why: …` and `-- noqa: why: …`. The lintr `# nolint` and SQLFluff `-- noqa` syntaxes were not verified in this pass.

## Not pursued
- GitLab Data SQL style guide — three WebFetch passes returned only handbook navigation; body not retrieved.
- SQLFluff capitalisation rule codes (CP01–CP05) and `-- noqa` syntax — rule-category pages other than "ambiguous" not fetched.
- lintr `# nolint` syntax and any `todo_comment_linter` equivalent — not verified.
- ESLint core `no-warning-comments` for TODO format, and the `@ts-expect-error` over `@ts-ignore` preference (typescript-eslint `ban-ts-comment`) — not verified.
- TS 7.0 GA announcement full text — seen only via search snippet of the official devblogs post; not fetched.
- `sqruff` (Rust SQLFluff alternative) and `sqlfmt` (mentioned by dbt) — not evaluated.
- `squawk` / migration linters for Postgres DDL safety — out of card scope.
- JS alternatives (oxlint, Deno/Bun built-in toolchains, Jest) — not compared; Vitest/ESLint/Prettier/Biome chosen as candidates per ticket.
- npm trusted publishing / provenance for packages *we* publish — publisher-side, not consumer card content.
- `.github/workflows/security.yml:39` runs `bandit … || true` (non-gating, with no `# why:`) — outside this question; relevant to Ticket 10.
- Bioconductor ecosystem coverage in OSV — R advisory DB shows only a topic tag; not verified.
- Python-host SQL with DuckDB prepared statements — psycopg/node-postgres/DBI covered; DuckDB client not fetched.
