# PLAYBOOK-ADD-FEATURE — "how to add a new feature" template

Dimension 16. This teaches a newcomer the *shape* of a change in this codebase by walking one
feature end-to-end through every layer. It must be **codebase-specific**: pick a real, recent
feature from `git log` as the worked example (or, if none is clean, a plausible representative
one), and for each layer name the actual directory, the actual naming convention, the actual
conventions that bind, and the actual verification command.

Fill the template; the **vertical slice** (one feature cutting through all layers) beats a
horizontal one (all models, then all endpoints). Pull facts from dimensions 3 (architecture &
data flow), 4 (directory map), 5 (run/debug), 6 (tests), 9 (conventions), 10 (changelog).

---

```markdown
## Add a feature

> Worked example: **<a real recent feature, e.g. "add `GET /reports/{id}/export` endpoint">** (from commit `<short-SHA>`, "`<commit subject>`"). Architecture pattern: `<from dimension 3>`. The same shape applies to most features here.

### The layers a feature touches (in this codebase)
`<Draw the actual layering, e.g.:>`
```
HTTP route  →  request schema  →  service / use-case  →  domain logic  →  repository  →  DB / migration
   ↘ (UI)  →  component        →  state/store        →  api client
   ↘ tests at each layer        ↘ docs / CHANGELOG
```

### Step-by-step (vertical slice)

**1. Data model / persistence** — *if your feature needs new data*
- Where: `<e.g. `src/<pkg>/models/` or `prisma/schema.prisma` or `app/entity/`>`
- Naming: `<convention>`
- Migration: `<tool — alembic / prisma migrate / goose / Flyway>`; create with `<command>`, apply with `<command>`.
- Conventions that bind: `<e.g. "all models inherit `Base`; timestamps via `TimestampMixin`; no business logic in models">`
- Example to imitate: `<file:line>`

**2. Domain / business logic**
- Where: `<e.g. `src/<pkg>/domain/` or `services/` or `usecases/`>`
- Naming: `<convention>`
- Conventions: `<e.g. "pure functions, no I/O; raise domain exceptions from `errors.py`; one use-case per file">`
- Example to imitate: `<file:line>`

**3. API surface (or UI)** — *backend route / GraphQL resolver / CLI command / UI component*
- Where: `<e.g. `src/<pkg>/api/routes/` / `schema/resolvers/` / `cmd/` / `web/src/features/`>`
- Naming & wiring: `<how a new route/resolver/command/component gets registered — the router include, the resolver map, the CLI subcommand registration, the route table>`
- Request/response schema: `<Pydantic / zod / proto / serializer — where, naming, validation conventions>`
- Auth: `<how to require auth on the new endpoint — the decorator/middleware from dimension 12>`
- Conventions: `<e.g. "thin controllers — delegate to a service; return DTOs not models; version under `/v1/`">`
- Example to imitate: `<file:line>`

**4. Tests** — *at every layer you touched*
- Where & framework: `<from dimension 6>`
- What to write: unit test for the domain logic; integration test for the route/repo; (e2e only if the area has them).
- Run: `<fast cmd>` then `<full cmd>`; if your feature touches `<integration area>`, also `<live cmd + what it needs>`.
- Coverage: `<expectation from dimension 6/13>`
- Example test to imitate: `<file:line>`

**5. Wire-up checklist** — *the easily-forgotten bits in this repo*
- `<e.g. "register the route in `app/router.py`">`
- `<e.g. "add the new env var to `.env.example` AND to the config loader" — per `rules/env-var-drift.md`>`
- `<e.g. "add a feature flag in `flags.py` if it's not GA yet">`
- `<e.g. "regenerate the OpenAPI spec: `make openapi`">`
- `<e.g. "add an entry to `CHANGELOG.md` (or write a Conventional Commit and let release-please do it)">`
- `<e.g. "update `docs/` if it's user-facing">`

**6. Verify end-to-end**
- Run it locally: `<run command>`; hit the feature: `<curl / UI step / CLI invocation>`; expected: `<result>`.
- Run the suite: `<test command>` — must be green.
- Lint/format/typecheck: `<commands>` — must be clean (CI will check).
- (Touched shared/core code? → run `Skill(impact-analysis)`.)

### Pre-PR checklist
- [ ] Tests added at every layer touched, all green
- [ ] Lint + format + type check clean
- [ ] New env vars in `.env.example` + config loader
- [ ] CHANGELOG entry (or Conventional Commit)
- [ ] Docs updated if user-facing
- [ ] OpenAPI/schema regenerated if API changed
- [ ] Feature flag in place if not GA
- [ ] Impact analysis run if shared/core code changed
- [ ] PR template filled; CODEOWNERS reviewers requested

### Common kinds of feature → where they go (quick lookup)
| Kind of addition | Goes in | Named | Also touch |
|---|---|---|---|
| New API endpoint | `<...>` | `<...>` | router, schema, service, tests, OpenAPI |
| New background job | `<...>` | `<...>` | scheduler/queue registration, tests |
| New CLI command | `<...>` | `<...>` | command registration, tests, `--help` |
| New config option | `<...>` | `<...>` | `.env.example`, config loader, docs |
| New external integration | `<...>` | `<...>` | dep in manifest, config, INTEGRATIONS doc, tests with mocks |
| New UI screen/component | `<...>` | `<...>` | route, store/state, api client, tests, styles |
```
