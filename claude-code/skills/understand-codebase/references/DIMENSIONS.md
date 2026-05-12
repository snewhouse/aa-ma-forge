# DIMENSIONS — the onboarding dimension catalogue

Single source of truth for **what** `understand-codebase` covers and **how**. Each dimension
below gives: *what to look for · reuse (which existing tool/agent to lean on) · inspect
(files/globs/commands) · evidence (what must end up in the docs) · owner (Deep-tier agent)*.

Owners (Deep tier): **S&S** = Structure & Stack (Explore agent / `gsd-codebase-mapper:arch+tech`),
**RUN** = `codebase-onboarding-runbook`, **CONV** = `codebase-onboarding-conventions`,
**HEALTH** = `codebase-onboarding-health`, **SYN** = `codebase-onboarding-synthesizer`.
In Standard tier the four Explore agents (S1 Structure&Stack, S2 Build/Run/Test/CI/Config,
S3 How-the-team-works, S4 Repo-health) map onto the same owners; the main thread is SYN.

> **Hard rule for every dimension:** capture *evidence* — a file path, a command, a git fact, a
> count — or write `not found — gap`. No vague assessments. **Never read or echo a secret value.**

---

## 1 — Read it / understand it / map it
- **What:** what the project *is* and *does*; the repo tour; ASCII directory tree (top 3 levels);
  entry points; the 3–5 critical execution paths a newcomer must trace.
- **Reuse:** `PROJECT_INDEX.json` (`dir_purposes`, ASCII tree, `symbol_importance`); `/index` if
  absent; `.planning/codebase/STRUCTURE.md` & `ARCHITECTURE.md`; `Skill(system-mapping)` step 1–2;
  `Skill(code-intelligence)` patterns for entry points.
- **Inspect:** `README*`; `git ls-files | head -200`; `find . -maxdepth 3 -type d`; entry-point
  globs — `main.*`, `index.*`, `cmd/*/main.go`, `**/__main__.py`, `manage.py`, `app.py`,
  `src/index.ts`, `bin/*`, `Procfile`, route decorators (`@app.route`, `@router.get`,
  `app.get(`), `if __name__ == "__main__"`.
- **Evidence:** one-paragraph "what it is"; ASCII tree; table of entry points (`file:line → what`);
  3–5 named critical paths ("HTTP request → router → service → repo → DB").
- **Owner:** S&S → SYN.

## 2 — Tech stack & versions
- **What:** languages (with % share), runtimes & required versions, frameworks & libraries (with
  versions), package managers, lockfiles, build tools; **currency** vs upstream (latest, EOL,
  migration notes).
- **Reuse:** `.planning/codebase/STACK.md`; `.planning/intel/stack.json`/`deps.json`;
  `/codebase-deep-dive` `07-dependencies-tech-stack.md`. **Deep tier:** WebSearch + Context7 MCP
  (`resolve-library-id` → `query-docs` / `get-library-docs`) for each major framework — "current
  stable version? EOL date? known breaking changes from <pinned>?".
- **Inspect:** `package.json`+lockfile, `pyproject.toml`/`requirements*.txt`/`Pipfile`/`uv.lock`/`poetry.lock`,
  `go.mod`/`go.sum`, `Cargo.toml`/`Cargo.lock`, `pom.xml`/`build.gradle*`, `Gemfile`/`Gemfile.lock`,
  `composer.json`, `*.csproj`/`packages.lock.json`, `.nvmrc`/`.node-version`/`.python-version`/`.ruby-version`/`.tool-versions`/`mise.toml`/`.sdkmanrc`,
  `Dockerfile`/`*.Dockerfile`, `flake.nix`/`shell.nix`. Language share: `git ls-files | sed 's/.*\.//' | sort | uniq -c | sort -rn` or `tokei`/`cloc` if available.
- **Evidence:** table `Layer | Tech | Version | Pinned? | Status (current/outdated/EOL/unknown)`.
  Deep tier adds a "Version currency" subsection with the WebSearch/Context7 findings + dates.
- **Owner:** S&S + (Deep) SYN/HEALTH for the currency pass.

## 3 — Architecture & data flow
- **What:** architectural pattern (layered / hexagonal-ports&adapters / clean / MVC / MVVM /
  microservices / event-driven / pipeline / monolith / serverless); layers & their responsibilities;
  core components & inter-component comms (sync calls / queues / events / RPC); the data model &
  migration story; a diagram.
- **Reuse:** `.planning/codebase/ARCHITECTURE.md`; `/codebase-deep-dive` `01-architecture-overview.md`,
  `03-data-flow-analysis.md`, `06-design-patterns.md`, and its `diagrams/*.mmd` (link them — don't
  redraw). If no diagram exists, generate Mermaid (`graph TD`/`flowchart LR`/`sequenceDiagram`) into
  `.claude/onboarding/diagrams/architecture.mmd`. `Skill(code-intelligence)` for class/interface
  hierarchies, DB-query/HTTP-client patterns.
- **Inspect:** module/package boundaries; ORM models (`models.py`, `*/entity/*`, `schema.prisma`,
  `*.sql` migrations, `migrations/`, `alembic/`); message brokers (`kafka`, `rabbitmq`, `sqs`,
  `pubsub`, `celery`, `sidekiq`, `bullmq` in deps/config); API surface (OpenAPI/`*.proto`/GraphQL SDL).
- **Evidence:** named pattern + 2-sentence justification; layer table; component diagram (Mermaid or
  link); data-model summary + migration tool & how to run a migration; "where state lives".
- **Owner:** S&S → SYN.

## 4 — Directory map & structure
- **What:** what every top-level (and key nested) directory is *for*; naming conventions for files
  and modules; **where new code goes** (prescriptive).
- **Reuse:** `PROJECT_INDEX.json` `dir_purposes`; `.planning/codebase/STRUCTURE.md`.
- **Inspect:** `find . -maxdepth 3 -type d -not -path '*/.*' -not -path '*/node_modules/*'`; a
  sample of files in each dir to infer purpose; existing `CONTRIBUTING.md`/`docs/` for stated layout.
- **Evidence:** annotated tree (`dir/ — purpose`); "to add X, put it in `path/` named `pattern`"
  for the 3–5 most common kinds of addition.
- **Owner:** S&S → SYN.

## 5 — Build / run / debug locally
- **What:** the *exact commands* to: clone-to-running. Install deps, build, run (dev + prod),
  debug, lint, type-check, format. Devcontainer/Docker-compose path. Toolchain version pins.
- **Reuse:** `.planning/codebase/STACK.md` (build/dev tools section); `Makefile`/`Justfile`/`Taskfile`
  targets; `package.json` `scripts`; `pyproject.toml` `[tool.*]`/`[project.scripts]`;
  `tox.ini`/`nox`; `.devcontainer/devcontainer.json`; `docker-compose*.yml`; README "Getting started".
- **Inspect:** `Makefile`, `Justfile`, `Taskfile.yml`, `package.json` scripts, `scripts/`, `bin/`,
  `setup.sh`/`bootstrap.sh`, `docker-compose*.yml`, `.devcontainer/`, `.vscode/launch.json`,
  `.vscode/tasks.json`, README/CONTRIBUTING setup sections.
- **Evidence:** a copy-pasteable "Quick start" block (`git clone … && <install> && <run>`); a table
  `Action | Command`; the debug entry point; "if it doesn't work, check …".
- **Owner:** RUN.

## 6 — Tests
- **What:** test framework(s); how to run — **fast vs full vs live/integration tiers** (markers,
  env, services needed); test pyramid shape (unit/integration/e2e ratio, roughly); fixtures &
  mocking patterns; coverage level & how it's measured; **known flaky tests**.
- **Reuse:** `.planning/codebase/TESTING.md`; `/codebase-deep-dive` `04-code-quality-assessment.md`
  (test-coverage section); `Skill(python-testing-patterns)` / `developer-essentials:e2e-testing-patterns`
  for what "good" looks like (don't impose — just frame).
- **Inspect:** `pytest.ini`/`pyproject.toml [tool.pytest.ini_options]`/`tox.ini`/`conftest.py`,
  `jest.config.*`/`vitest.config.*`/`playwright.config.*`/`cypress.config.*`, `*_test.go`/`go test`,
  `*Test.java`/`*.spec.ts`/`*.test.tsx`, `tests/`/`test/`/`spec/`/`__tests__/`, `.coveragerc`/`codecov.yml`,
  CI workflow test steps, `@pytest.mark.*`/`describe.skip`/`it.only`/`xfail`/`@Disabled`, grep for
  `flaky`/`skip`/`xfail`/`@Flaky`/`retries`.
- **Evidence:** framework + run commands per tier; rough pyramid (counts of test files by kind);
  fixture/mock convention with one example file; coverage % if discoverable + how to check; flaky-test list.
- **Owner:** RUN.

## 7 — CI gates
- **What:** what runs on a PR / push / tag; required checks that **block a merge**; the pipeline
  stages; where build artifacts/images go.
- **Reuse:** `Skill(doc-drift-detection)` doesn't apply here, but its philosophy does; `.planning/codebase/`
  doesn't cover CI well — this is largely fresh.
- **Inspect:** `.github/workflows/*.yml`, `.gitlab-ci.yml` + `.gitlab/`, `Jenkinsfile`,
  `.circleci/config.yml`, `azure-pipelines.yml`, `bitbucket-pipelines.yml`, `.drone.yml`,
  `buildkite/`, `.pre-commit-config.yaml` (runs locally + often in CI), branch-protection hints in
  `CONTRIBUTING.md`, status-check badges in README.
- **Evidence:** table `Trigger | Job | What it does | Blocking?`; "to get a PR merged you must pass: …".
- **Owner:** RUN.

## 8 — Env & config (NO SECRETS)
- **What:** what environment variables / config files the app needs — **names and shape only**.
  Config precedence (defaults < file < env < flags). Feature flags / config-driven behaviour.
- **Reuse:** `rules/env-var-drift.md` philosophy (code's `os.getenv`/`process.env` calls are truth);
  `.env.example`/`.env.sample`/`.env.template` as the *documented* contract.
- **Inspect:** `.env.example`/`.env.sample`/`.env.template`/`.env.ci` (read **only** for variable
  *names*); `config/`, `settings.py`/`settings/*.py`, `*.config.js`, `application*.yml`/`*.properties`,
  `appsettings*.json`, `*.toml` config, `helm/values*.yaml`, `terraform/*.tfvars` (names only);
  grep code for `getenv`/`environ`/`process.env`/`Deno.env`/`os.Getenv`/`viper.`/`config.get`;
  feature flags — `LaunchDarkly`/`unleash`/`flipper`/`flags.`/`if config.feature_`.
  **NEVER open `.env` (no suffix), `*.key`, `*.pem`, `*.p12`, `id_rsa*`, `credentials*`, `secrets*`, `*.tfstate`, service-account JSON.**
- **Evidence:** table `Var | Purpose (inferred) | Required? | Default | Source (file:line)`; list of
  config files + what each governs; feature-flag inventory; an explicit "secrets are handled via: …"
  line (vault / env / sealed-secrets / SSM / etc., from config — not values).
- **Owner:** RUN.

## 9 — Conventions
- **What:** code style; naming (files, modules, classes, funcs, vars, constants, branches);
  import organisation; error-handling pattern; logging pattern; comment policy; function/module
  size norms — **validated by reading 5–10 representative source files**, not just inferred from a
  linter config.
- **Reuse:** `.planning/codebase/CONVENTIONS.md`; `Skill(code-intelligence)` for structural sampling;
  linter/formatter configs as *claimed* conventions to verify.
- **Inspect:** `.editorconfig`, `.prettierrc*`, `.eslintrc*`/`eslint.config.*`, `ruff.toml`/`[tool.ruff]`,
  `.flake8`, `.pylintrc`, `setup.cfg`, `.rubocop.yml`, `.golangci.yml`, `clippy.toml`, `checkstyle.xml`,
  `.editorconfig`; then **actually read** a handful of core source files in different layers and note
  what they *do*, not what the config *says*.
- **Evidence:** "claimed (linter) vs observed (code)" table; the dominant patterns with one cited
  example each (`see src/foo/bar.py:NN`); any inconsistency flagged (→ feeds the "cons").
- **Owner:** CONV.

## 10 — Versioning & releases · git workflow
- **What:** versioning scheme (semver / calver / commit-hash / none); where the version string lives
  (single source of truth); tag pattern (`v1.2.3`?); `CHANGELOG` discipline (kept? generated?
  Conventional-Commits-driven?); branching strategy (trunk-based / GitHub-flow / git-flow /
  release branches); commit-message conventions; how a release is cut; how a deploy happens;
  rollback path.
- **Reuse:** `Skill(doc-drift-detection)` (version-string + CHANGELOG drift heuristics);
  `git` itself is the source of truth.
- **Inspect:** `git tag --sort=-creatordate | head`, `git describe --tags --abbrev=0`,
  `git log --oneline -30` (commit-message style), `git branch -a` (branch naming),
  `CHANGELOG*`/`HISTORY*`/`NEWS*`, version in `pyproject.toml`/`package.json`/`Cargo.toml`/`__version__`/`VERSION`,
  release tooling — `release-please`, `semantic-release`, `changesets/`, `bumpversion`/`bump2version`/`commitizen`,
  `goreleaser.yml`, GitHub release workflows; deploy — `helm/`, `k8s/`, `argocd`, `flux`, `Dockerfile`+registry,
  `fly.toml`, `vercel.json`, `Procfile`, `serverless.yml`, `cloudbuild.yaml`, deploy workflows;
  rollback hints in `runbooks/`/`docs/`/`RUNBOOK*`.
- **Evidence:** "version lives in `<file>`"; tag pattern; CHANGELOG policy; named branching strategy
  + branch-naming rule; commit-message convention (with one cited example); "to cut a release: …";
  "deploys happen via: …"; "to roll back: …" (or `not found — gap`).
- **Owner:** CONV.

## 11 — Rules & agent instructions
- **What:** detect and summarise **every** file in `references/RULES-FILES.md` — `CLAUDE.md`,
  `AGENTS.md`, `.cursorrules`/`.cursor/rules/*`, `.windsurfrules`, `.github/copilot-instructions.md`,
  `.aider.conf.yml`, `.editorconfig`, `.gitattributes`, `CODEOWNERS`, `CONTRIBUTING.md`, `SECURITY.md`,
  `CODE_OF_CONDUCT.md`, `.pre-commit-config.yaml`, `renovate.json`/`.github/dependabot.yml`,
  toolchain pins, **project `.claude/{skills,agents,commands,rules,hooks}/`**, `.vscode/`,
  `.devcontainer/`, plus repo `Makefile`/`Justfile` as "the contract".
- **Reuse:** for project `.claude/skills/*/SKILL.md` — read the lightweight SKILL.md headers (~130
  lines each), NOT full `AGENTS.md` (100KB+); surface skill-defined patterns.
- **Inspect:** the glob list in `RULES-FILES.md`.
- **Evidence:** a table `File | Exists? | One-line summary of what it mandates` covering the whole
  list; for any large `AGENTS.md`/`CLAUDE.md`, a 3–5-bullet digest of the *binding* rules (commit
  conventions, test gates, no-AI-attribution, secret handling, etc.); call out conflicts between
  rules files.
- **Owner:** CONV.

## 12 — Integrations · observability · security posture
- **What:** external systems consumed (third-party APIs, DBs, caches, queues, object stores, auth
  providers, payment/email/SMS providers, search engines, LLM APIs); observability — logging
  library & format, metrics (Prometheus/StatsD/OTel), tracing (OTel/Jaeger/Zipkin/Sentry), dashboards;
  security posture — auth/authz model (sessions/JWT/OAuth/OIDC/API-keys/mTLS), input-validation
  approach, dependency-vuln signal, how secrets/credentials are managed.
- **Reuse:** `.planning/codebase/INTEGRATIONS.md`; `/codebase-deep-dive` `05-security-analysis.md`;
  `Skill(defense-in-depth)` / `Skill(secrets-management)` philosophy for framing (don't audit — describe).
- **Inspect:** SDK deps in the manifest (`stripe`, `boto3`/`@aws-sdk`, `@google-cloud/*`, `redis`,
  `psycopg`/`pg`, `kafka`, `elasticsearch`/`opensearch`, `openai`/`anthropic`, `sendgrid`/`twilio`,
  `auth0`/`okta`/`firebase-admin`); base URLs / hostnames in config; `requirements`/`package.json`
  for `sentry-sdk`/`@sentry/*`, `opentelemetry-*`, `prometheus-client`/`prom-client`, `structlog`/`winston`/`pino`/`zap`/`logrus`;
  auth code — middleware, decorators (`@login_required`, `@requires_auth`, `passport.`, `spring-security`),
  `jwt`/`oauthlib`/`authlib`; vuln tooling — `dependabot.yml`, `renovate.json`, `pip-audit`/`npm audit`/`govulncheck`/`trivy`/`snyk` in CI;
  secrets — `vault`, `sops`, `sealed-secrets`, `aws secretsmanager`/`ssm`, `gcp secret-manager`,
  `doppler`, `.env` strategy in docs.
- **Evidence:** table of external dependencies (`Service | Used for | SDK/version | Config location`);
  observability summary (logging lib + format, metrics backend, tracing backend, error tracker);
  auth model in 2–3 sentences; "vuln scanning: <tool> in <CI job>" or `not found — gap`; "secrets:
  managed via <mechanism>".
- **Owner:** RUN (integrations + observability) + HEALTH (vuln signal) → SYN.

## 13 — Repo health snapshot
- **What:** churn hotspots (files changed most over the last N months — likely complex/fragile);
  active contributors & bus-factor; ownership (`CODEOWNERS`); doc-drift signals; `TODO`/`FIXME`/`HACK`/`XXX`
  inventory; known-issue backlog; dependency health (count outdated/deprecated); test-coverage gaps;
  "here be dragons" (generated code, vendored code, `// DO NOT EDIT`, huge files, files with no tests).
- **Reuse:** `Skill(doc-drift-detection)` heuristics for stale version strings / CHANGELOG /
  README / CLAUDE.md / ADR index; `.planning/codebase/CONCERNS.md`; `/codebase-deep-dive`
  `04-code-quality-assessment.md` & `08-recommendations.md`; `Skill(retro)` philosophy for the
  git-history breakdown (don't run it — borrow the approach).
- **Inspect (read-only git/grep):**
  - Churn: `git log --since='6 months ago' --name-only --pretty=format: | sort | uniq -c | sort -rn | head -25`
  - Contributors: `git shortlog -sne --since='6 months ago'` and `git log --since='12 months ago' --format='%an' | sort -u | wc -l`
  - Recency: `git log -1 --format=%cd` (is the repo alive?)
  - Ownership: `CODEOWNERS` (`.github/`, root, `docs/`)
  - TODOs: `git grep -nE 'TODO|FIXME|HACK|XXX|BUG' -- '*.py' '*.js' '*.ts' '*.go' '*.java' '*.rb' '*.rs' | wc -l` + a sample
  - Big files: `git ls-files | xargs -I{} sh -c 'wc -l "{}" 2>/dev/null' | sort -rn | head -15`
  - Generated/vendored: `vendor/`, `node_modules/` (gitignored?), `*_pb2.py`, `*.pb.go`, `generated/`, `dist/`, `.gen.`, `# Code generated`, `@generated`
  - Outdated deps: lockfile dates / `npm outdated`/`pip list --outdated` only if cheap & offline; otherwise note "run X"
- **Evidence:** churn-hotspot table; contributor count + top 5 + bus-factor note; ownership map (or
  `no CODEOWNERS`); doc-drift findings; TODO count + 3-line sample; outdated-dep count or "unknown —
  run X"; "here be dragons" list with paths.
- **Owner:** HEALTH.

## 14 — Pros / cons / watch-outs
- **What:** an honest verdict per `references/PROS-CONS-RUBRIC.md`. ≥3 evidence-cited items per
  column (Pros / Cons / Watch-outs). Explicit trade-offs ("optimised for X at the cost of Y").
- **Reuse:** synthesis of dimensions 3, 6, 9, 12, 13 + `/codebase-deep-dive` health grade if present.
- **Evidence:** the filled rubric table; the three columns each with cited evidence; a 2-3 sentence
  "bottom line for a newcomer".
- **Owner:** HEALTH gathers evidence → SYN writes the verdict.

## 15 — Contribute safely
- **What:** the codebase-specific playbook per `references/PLAYBOOK-CONTRIBUTE.md`. Branch from
  where & named how; the local pre-commit/test gauntlet; the CI checks you must pass; the
  impact-analysis ritual (`Skill(impact-analysis)`) before touching shared/core modules; what's
  fragile/generated/vendored ("don't touch"); review norms & who reviews; commit conventions; a
  concrete "good first PR" suggestion grounded in this repo's actual TODOs/issues.
- **Reuse:** dimensions 7, 9, 10, 13; `CONTRIBUTING.md`; `Skill(impact-analysis)`.
- **Evidence:** the filled playbook — every step cites a real command/file from this repo.
- **Owner:** SYN (using CONV + RUN + HEALTH outputs).

## 16 — Add a feature
- **What:** the codebase-specific playbook per `references/PLAYBOOK-ADD-FEATURE.md`. Pick a
  *representative* recent feature (or a plausible one) and walk it end-to-end: data model → business
  logic → API/UI → tests → docs/changelog; for each layer, *which directory*, *what naming*, *what
  conventions bind*, *how to wire it up*, *how to verify*.
- **Reuse:** dimensions 3, 4, 5, 6, 9; `git log` for a recent feature commit to use as the worked
  example; `Skill(feature-dev:feature-dev)` philosophy.
- **Evidence:** the filled playbook with a concrete worked example citing real files; "checklist
  before you open the PR".
- **Owner:** SYN (using S&S + CONV + RUN outputs).

## 17 — Glossary
- **What:** the domain ubiquitous language — acronyms, domain nouns, project-specific terms a
  newcomer must know to read the code & PRs.
- **Reuse:** `Skill(ubiquitous-language)` philosophy; README/docs glossary if present; class/module
  names; `git grep` for repeated capitalised domain terms.
- **Evidence:** alphabetical `Term — meaning (where it appears)` table; 8–25 entries typical.
- **Owner:** HEALTH/S&S → SYN.

## 18 — Provenance (every file gets this block)
- **What:** when this onboarding was generated, against which commit, at which tier, with which
  tools, what was *absorbed* (prior artifacts reused) vs *freshly run*, and a "known limitations /
  gaps" list (anything the run couldn't determine).
- **Inspect:** `date -u +%Y-%m-%dT%H:%M:%SZ`, `git rev-parse --short HEAD`, `git rev-parse --abbrev-ref HEAD`.
- **Evidence:** the Provenance block (see `references/ONBOARDING-TEMPLATE.md`).
- **Owner:** SYN.

## 19 — Author / review / improve AGENTS.md  *(Standard & Deep only — never Quick; consent-gated)*
- **What:** the agent-facing distillation. If the repo has no `AGENTS.md`: offer (via
  `AskUserQuestion`) to author one from the analysis. If it has one: **never overwrite** — write
  `AGENTS.review.md` (section-by-section accuracy verdict + gaps + a proposed rewrite the owner
  applies). If it has only `CLAUDE.md`: offer a thin pointer-`AGENTS.md` or a standalone one;
  never edit `CLAUDE.md` (that's `/init`'s job — just flag drift between it and the code).
- **Reuse:** **`references/AGENTS-MD-TEMPLATE.md` — its SAFETY PROTOCOL is binding; read it before
  any `AGENTS.md` action.** Source material = dimensions 1–18 (the distillation: what it is, setup/run,
  test, lint/format/typecheck, project layout, conventions, architecture-in-one-paragraph, dragons,
  secrets/config, releases/deploy, pre-PR checklist). Deep tier: `WebSearch "AGENTS.md convention"`
  to confirm the current expected structure first.
- **Inspect:** `ls AGENTS.md CLAUDE.md AGENTS.review.md AGENTS.draft.md 2>/dev/null`; the dimension outputs.
- **Evidence:** which action was taken (authored / drafted / reviewed-via-sidecar / declined / N/A);
  the `AGENTS.md` or `AGENTS.review.md` file; a 5-line summary in chat + in `ONBOARDING.md`.
- **Owner:** orchestrator runs the `AskUserQuestion` gate; SYN writes the file. **HITL** — never act without consent on an existing file.

---

## Standard-tier agent ↦ dimension assignment (no overlap)

| Explore agent | Dimensions owned |
|---|---|
| **S1 — Structure & Stack** | 1, 2 (basic), 3, 4, 12-integrations(list), 17 |
| **S2 — Build / run / test / CI / config** | 5, 6, 7, 8, 12-observability |
| **S3 — How this team works** | 9, 10, 11 |
| **S4 — Repo health & verdict inputs** | 2-currency(if offline-cheap), 12-security/vuln, 13, 14-evidence |
| **Main thread (SYN)** | 14-verdict, 15, 16, 18 + reconcile all of the above |

## Deep-tier agent ↦ dimension assignment

| Agent | Dimensions owned | Writes |
|---|---|---|
| `gsd-codebase-mapper:tech` | 2, 12-integrations | `.planning/codebase/STACK.md`, `INTEGRATIONS.md` |
| `gsd-codebase-mapper:arch` | 1, 3, 4 | `.planning/codebase/ARCHITECTURE.md`, `STRUCTURE.md` |
| `gsd-codebase-mapper:quality` | 9, 6 | `.planning/codebase/CONVENTIONS.md`, `TESTING.md` |
| `gsd-codebase-mapper:concerns` | 13 (partial) | `.planning/codebase/CONCERNS.md` |
| `/codebase-deep-dive` | 3, 6, 9, 12-security, 13 (quality grade) | `.claude/reports/codebase-deep-dive-*/` + diagrams |
| `codebase-onboarding-conventions` | 9, 10, 11, 17 | `.claude/onboarding/06-conventions-versioning-git.md`, `07-rules-and-agent-instructions.md` |
| `codebase-onboarding-runbook` | 5, 6, 7, 8, 12-observability, 3-datamodel | `.claude/onboarding/04-build-run-debug.md`, `05-tests-ci.md`, `08-integrations-observability-security.md` |
| `codebase-onboarding-health` | 13, 14-evidence, 12-vuln | `.claude/onboarding/09-repo-health-and-verdict.md` (evidence part) |
| (enrichment, any) | 2-currency | adds "Version currency" subsection to `01-stack.md` |
| `codebase-onboarding-synthesizer` | 1, 2, 3, 4, 14-verdict, 15, 16, 17, 18, 19 | `ONBOARDING.md`, `.claude/onboarding/00-index.md`, `01-stack.md`, `02-architecture.md`, `03-structure.md`; + `AGENTS.md` / `AGENTS.review.md` / `AGENTS.draft.md` per `AGENTS-MD-TEMPLATE.md` (consent-gated; never overwrites an existing `AGENTS.md`) |
| `code-reviewer` (review) | — (verifies all) | corrections + QA verdict comment |
