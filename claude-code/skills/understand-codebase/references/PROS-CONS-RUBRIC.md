# PROS-CONS-RUBRIC — the honest verdict

Dimension 14. The goal: a newcomer reads this and knows, honestly, what they're walking into.
**Every cell needs evidence** — a file path, a metric, a git fact, a count. Banned: "clean code",
"well-architected", "needs work", "could be better" with nothing behind them.

## Step 1 — score the 10 axes

For each axis: **Strong / OK / Weak / Unknown**, plus a one-line evidence-cited justification.
"Unknown" is allowed and honest — say *why* it's unknown (e.g. "no coverage report; not run").

| # | Axis | Strong looks like | Weak looks like | Evidence to cite |
|---|---|---|---|---|
| 1 | **Architecture clarity** | Named, consistent pattern; clear layer boundaries; new code obviously goes somewhere | "Big ball of mud"; circular deps; no obvious place for new code | the pattern name + `PROJECT_INDEX.json` dir purposes + any `import` cycles found |
| 2 | **Modularity / coupling** | Small focused modules; dependency direction respected; few god-files | A handful of 1000+-line files do everything | `git ls-files | xargs wc -l | sort -rn | head`; fan-in/fan-out from the index |
| 3 | **Test safety net** | Fast suite runs in seconds; meaningful coverage; CI gates on it | Few/no tests; coverage unknown; tests don't run | test-file count vs source-file count; `pytest`/`go test` runs; coverage % if available; CI test step |
| 4 | **Build / run ergonomics** | `git clone && make dev` just works; devcontainer; documented | Undocumented; many manual steps; "works on my machine" | the actual quick-start commands; presence of `Makefile`/`docker-compose`/`.devcontainer` + README setup section quality |
| 5 | **Dependency health** | Recent, pinned, scanned (Dependabot/Renovate + audit in CI) | Many years-old deps; no lockfile; no scanning; known CVEs | lockfile presence & age; `dependabot.yml`/`renovate.json`; `pip-audit`/`npm audit`/`govulncheck` in CI; outdated count |
| 6 | **Documentation quality** | README + ARCHITECTURE + ADRs + inline docstrings, all current | Stale README; no architecture doc; no ADRs; drift everywhere | `Skill(doc-drift-detection)` findings; ADR count; docstring sampling; README last-modified vs code |
| 7 | **Conventions consistency** | Linter+formatter+typecheck enforced in CI; code actually follows them | Configs exist but code violates them; mixed styles | "claimed vs observed" table from dimension 9; CI lint step; sampling results |
| 8 | **Operational maturity** | Logging/metrics/tracing; runbooks; clear deploy + rollback; health checks | `print()` debugging; no metrics; deploy is tribal knowledge; no rollback story | observability deps (dimension 12); `runbooks/`; deploy workflow; `/healthz` endpoint |
| 9 | **Security posture** | Clear auth model; input validation; secrets in a vault; vuln scanning; SECURITY.md | Hardcoded secrets risk; ad-hoc auth; no validation layer; no scanning | `/codebase-deep-dive` `05-security-analysis.md` if present; auth code (dimension 12); `SECURITY.md`; secret-management mechanism |
| 10 | **Onboarding friction** | A new dev is productive in < a day; this very doc would have been easy to write | Took a long, painful crawl to understand anything | how hard *this* analysis was; missing docs; tribal-knowledge signals; bus-factor from `git shortlog` |

## Step 2 — derive the three columns

From the axis scores, write **≥3 evidence-cited items per column**:

- **Pros** — genuine strengths a newcomer benefits from. (Strong axes; pleasant surprises.)
- **Cons** — genuine weaknesses that will bite. (Weak axes; missing safety nets; drift.)
- **Watch-outs** — not necessarily bad, but you must know: trade-offs, surprising choices, fragile
  zones, "this looks wrong but it's intentional". ("Here be dragons" from dimension 13 lives here.)

Each item: `**<headline>** — <evidence> (<file:line / command / count>)`.

## Step 3 — name the trade-off(s)

One or two sentences: "This codebase is optimised for **X** at the cost of **Y**." Examples:
- "Optimised for fast iteration (monorepo, no service boundaries) at the cost of clear ownership and blast-radius control."
- "Optimised for type safety and explicitness (heavy Pydantic, strict mypy) at the cost of verbosity and onboarding speed."
- "Optimised for operational simplicity (one process, SQLite) at the cost of horizontal scalability."

## Step 4 — the bottom line

2–3 sentences for a newcomer: *Is this a pleasant codebase to work in? Where will you spend your
first frustrating afternoon? What should you read first?* Be honest but fair — most codebases are
neither pristine nor dumpster fires; say where on the spectrum this one sits and why.

## Output shape (into `.claude/onboarding/09-repo-health-and-verdict.md` + a condensed version in `ONBOARDING.md`)

```markdown
## Pros / Cons / Watch-outs

### Axis scores
| Axis | Score | Evidence |
|---|:--:|---|
| Architecture clarity | Strong | Hexagonal; `domain/`, `adapters/`, `app/` cleanly split (PROJECT_INDEX dir_purposes); no import cycles found |
| Modularity / coupling | OK | Mostly small modules; `services/report.py` is 1,240 lines and does too much |
| Test safety net | Weak | 38 test files vs 210 source files; no coverage report; `pytest -m fast` passes in 4s but CI only runs unit tests |
| … | | |

### Pros
- **Reproducible dev env** — `make dev` + `.devcontainer/devcontainer.json`; README "Getting started" is accurate (verified by running it).
- **Strict typing enforced** — `mypy --strict` in CI (`.github/workflows/ci.yml:42`); sampled files all type-clean.
- **Conventional Commits + automated CHANGELOG** — `release-please-config.json`; `git log` confirms.

### Cons
- **Thin test net on the report pipeline** — `src/report/` has 1 test file for 14 modules; the highest-churn area (`git log --since=6mo` top hit) is the least tested.
- **Doc drift** — README says "Python 3.10+" but `.python-version` is `3.12` and `pyproject.toml requires-python = ">=3.11"` (3-way mismatch).
- **No SECURITY.md, no vuln scanning** — no `dependabot.yml`/`renovate.json`; no `pip-audit` in CI.

### Watch-outs
- **`src/legacy/` is vendored & frozen** — `.gitattributes` marks it `linguist-vendored`; `# DO NOT EDIT` headers; touch only with maintainer sign-off.
- **`*_pb2.py` are generated** — regenerate via `make proto`, never hand-edit.
- **Async/sync split** — `app/` is async, `worker/` is sync Celery; mixing them is the #1 source of past bugs (`git log --grep=async`).

### Trade-off
Optimised for type safety and release automation at the cost of test depth in the youngest, fastest-moving subsystem.

### Bottom line
A tidy, well-tooled codebase with a soft underbelly: the report pipeline. A new dev will be productive in a day for most areas; budget extra care (and tests) when touching `src/report/`. Read `ARCHITECTURE.md` and `CONTRIBUTING.md` first, then trace one request through `app/` → `domain/` → `adapters/`.
```
