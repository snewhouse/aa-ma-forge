# R card

Source: `docs/research/code-conventions-impact-language-cards.md` (Card 2, state of sources 2026-10-08).

| Slot | Convention |
|------|-----------|
| Style | tidyverse style guide; base pipe `\|>` over `%>%`; function names are verbs; `return()` only for early returns. |
| Formatter | Air (`air format`, pre-commit hook `air-format`); styler as the configurable fallback. Air is pre-1.0: check that lintr's layout linters agree with its output. |
| Linter | lintr from `linters_with_defaults()`; `assignment_linter()` allows only `<-`. |
| Security lint | lintr has no security tag: add `eval` and `system` to `undesirable_function_linter()` explicitly. |
| Doc comments | roxygen2 `#'` blocks (title, `@param`, `@returns`, `@export`, `@examples`); `devtools::document()` generates `man/` and `NAMESPACE`. |
| Suppressions | `# nolint: why: …` (syntax not verified in the research pass). |
| Logging | logger: `log_info()`, `log_warn()`; `appender_stderr`, `layout_json()` for structured lines. A package sets only its formatter and namespace; thresholds and appenders belong to the caller. |
| Tests | testthat 3rd edition (`Config/testthat/edition: 3` in `DESCRIPTION`). |
| Dependencies / audit | renv (`snapshot`, commit `renv.lock`, `restore`); CI runs `osv-scanner scan -L renv.lock`. riskmetric measures robustness, not CVEs — not a gate. |
| Secrets | `Sys.getenv()` from the user-level `.Renviron`; never typed at the console (it lands in `.Rhistory`). |

## Pitfalls the tools miss

1. Assignment is `<-`, not `=`.
2. No `library()`, `setwd()` or `source()` inside package or function code.
3. `sapply` has an unstable return type: use `vapply` or `purrr::map_*`.
4. Bind DB parameters (`DBI::dbBind`), never paste values into SQL.
5. renv does not pin R, pandoc or system libraries: record those separately.
