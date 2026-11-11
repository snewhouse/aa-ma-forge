# SQL card

Source: `docs/research/code-conventions-impact-language-cards.md` (Card 3, state of sources 2026-10-08).

| Slot | Convention |
|------|-----------|
| Style | dbt SQL style: lowercase keywords and identifiers, trailing commas, explicit `as`, explicit `inner join` (no comma joins), column prefixes in multi-table joins, `union all` unless de-duplication is intended, import CTEs at the top, single-purpose CTEs, `select * from <final_cte>` last. |
| Formatter + linter | SQLFluff with the `dialect` always set explicitly (`postgres`, `duckdb`, `bigquery`, `snowflake`, …); `rules = core` to start; `sqlfluff-templater-dbt` for dbt. Pre-commit hooks `sqlfluff-lint` / `sqlfluff-fix`. |
| "Security" lint | SQLFluff has no injection rules; injection is the host language's job. AM04 flags `select *` (output shape drifts silently with upstream schemas). |
| Doc comments | Persist docs in the catalog: `COMMENT ON TABLE/COLUMN … IS '…'`, or dbt `description:` plus `+persist_docs`. Comments are readable by any connected user: no sensitive data. |
| Comments | `--` inline; Jinja `{# #}` in dbt for comments that must not reach compiled SQL. Explain the grain, business rule or de-duplication intent. |
| Suppressions | `-- noqa: <rule>  why: …` (syntax not verified in the research pass). |
| Logging | The host language logs the query's name and row counts, never bound values. |
| Tests | dbt unit tests (`dbt test --select "test_type:unit"`); pgTAP via `pg_prove` for plain Postgres. |
| Injection | Parameterised queries only; identifiers from an allow-list, `psycopg.sql.Identifier` or `pg-format`; least-privilege DB accounts. |
| Secrets | Credentials in env vars or the profile, never in `.sql` files or `COMMENT`s. |

## Pitfalls the tools miss

1. `select *` in a model or view: downstream column drift is silent.
2. SQL built by concatenation, `%` or f-strings.
3. Rules pass for the wrong dialect: DuckDB inherits postgres in SQLFluff, so pin the real one.
4. A bare `union` hides duplicates and costs a sort.
5. One grain per CTE, named for what it produces (`events_joined_to_users`).
