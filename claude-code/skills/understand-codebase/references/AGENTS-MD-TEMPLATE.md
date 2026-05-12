# AGENTS-MD-TEMPLATE — author / review / improve an AGENTS.md

Dimension 19. `understand-codebase` already learns everything an `AGENTS.md` needs (tech stack,
build/test commands, conventions, where-things-go, dragons, secret handling). This file says how
to turn that into an `AGENTS.md` — **safely**.

`AGENTS.md` is the open, tool-agnostic convention for "instructions to coding agents", a sibling
of `CLAUDE.md` (Claude-Code-specific). It must be **small and high-signal** — an agent reads it
every session. It is a *distillation* that points to `ONBOARDING.md` for depth, never a copy of it.
(In Deep tier, do a quick `WebSearch "AGENTS.md convention"` to confirm the current expected
structure before writing — the convention evolves.)

---

## SAFETY PROTOCOL — this is the part that matters

| Situation | What the skill does | Never |
|---|---|---|
| **No `AGENTS.md` and no `CLAUDE.md`** | After the analysis, `AskUserQuestion` (header "AGENTS.md"): *Author one now? · Yes, write `AGENTS.md` · Yes, but write it as `AGENTS.draft.md` for me to review · No*. On "yes" → write it from the template below. | Don't write it without asking. |
| **`AGENTS.md` exists** | **NEVER overwrite or edit it.** Instead write `AGENTS.review.md` next to it containing: (1) an accuracy review — for each section, "matches what we found / stale / missing / contradicts the code" with evidence; (2) a gaps list; (3) a complete *proposed* rewrite. Surface a 5-line summary in chat + in `ONBOARDING.md`. Tell the user: "review `AGENTS.review.md`; to apply the rewrite, say so explicitly." | Don't touch the original. Don't `Edit` it. |
| **Only `CLAUDE.md` exists (no `AGENTS.md`)** | Note both files' relationship. `AskUserQuestion`: *Create `AGENTS.md`? · Yes — a thin pointer (`AGENTS.md` → "see CLAUDE.md") · Yes — a standalone AGENTS.md (some content will overlap CLAUDE.md) · No, keep CLAUDE.md as the single source*. Respect the choice. Do NOT modify `CLAUDE.md` — that's `/init`'s job; just flag any drift between it and the code. | Don't auto-create or auto-edit `CLAUDE.md`. |
| **Quick tier (any of the above)** | Do nothing except note it: "no `AGENTS.md` — run `/understand-codebase --standard` to generate one." | Don't author from a Quick-tier analysis — too thin. |

Rationale: `AGENTS.md` is team-owned and outward-facing. A missing one is safe to create *with
consent* (nothing to clobber). An existing one must be treated as authoritative-until-the-owner-
says-otherwise — we propose, the owner disposes. Mirrors the global rule: "Before deleting or
overwriting, look at the target — if you didn't create it, surface that instead of proceeding."

---

## TEMPLATE — `AGENTS.md` (keep it under ~120 lines; trim ruthlessly)

```markdown
# AGENTS.md

> Instructions for AI coding agents working in this repository. For the full human-oriented
> walkthrough see `ONBOARDING.md`. Last reviewed: <date> · <short-SHA> · by understand-codebase.

## What this is
<one or two sentences: what the project does, the main tech>

## Setup & run
- Install: `<command>`
- Run (dev): `<command>`
- Run (prod-like): `<command>`
- Requires: `<Node X / Python Y / Docker / ... — from toolchain pins>`

## Test
- Fast/unit: `<command>` — run this before every commit
- Full: `<command>` — run before pushing
- Integration/live: `<command>` (needs `<services>`)
- The suite must be green before you finish. <coverage expectation if any>

## Lint / format / type check
- Lint: `<command>` (config: `<file>`)
- Format: `<command>`
- Type check: `<command>`
- Pre-commit hooks run: `<list>` — `pre-commit run --all-files` to check ahead.

## Project layout (where things go)
- `<dir/>` — <purpose>
- `<dir/>` — <purpose>
- New <thing> goes in `<dir/>`, named `<pattern>`. <repeat for the 3-5 most common additions>

## Conventions (observed in the code, not just the linter)
- <naming / style / imports / error handling / logging — the dominant patterns, terse>
- Commit messages: `<Conventional Commits / project style>`. <attribution rule, e.g. "no AI co-authored-by">
- Branch from `<base>`, name `<pattern>`.

## Architecture (one paragraph)
<pattern + the layers + how a request flows>. Diagram: `<.claude/onboarding/diagrams/architecture.mmd or link>`.

## Don't touch / be careful (here be dragons)
- `<vendored/generated/frozen path>` — <why; how to regenerate if generated, e.g. `make proto`>
- <other fragile zones / async-sync split / etc.>

## Secrets & config
- Config via `<mechanism>`; env vars documented in `.env.example` (names only).
- **Never** commit secrets; never read `.env` (no suffix), `*.key`, `*.pem`, credential files.
- Secrets in production come from `<vault / SSM / sealed-secrets / ...>`.

## Releases & deploy
- Version lives in `<file>`; tags `<pattern>`; CHANGELOG `<policy>`.
- Release: `<how>`. Deploy: `<how>`. Rollback: `<how>`.

## Before you open a PR
- [ ] Tests added & green  [ ] Lint/format/typecheck clean  [ ] CHANGELOG/conventional commit
- [ ] New env vars in `.env.example` + config loader  [ ] Docs updated if user-facing
- [ ] Impact analysis run if you changed shared/core code  [ ] CODEOWNERS reviewers requested
- CI checks that block merge: `<list>`

## See also
- `ONBOARDING.md` — full walkthrough · `CONTRIBUTING.md` — <if present> · `CLAUDE.md` — <if present, "Claude-Code-specific overrides">
```

---

## REVIEW CHECKLIST — for an existing `AGENTS.md` (→ `AGENTS.review.md`)

For each row: verdict = ✅ accurate / ⚠️ stale / ❌ wrong/missing — with **evidence**.

| Section | Check against | Verdict + evidence |
|---|---|---|
| Setup/run/test commands | actually run them (or check `Makefile`/`package.json` scripts they reference still exist) | |
| Required tool versions | `.nvmrc`/`.python-version`/`.tool-versions`/`Dockerfile` | |
| Lint/format/typecheck commands & configs | the config files exist; commands still valid | |
| Project layout | current `find . -maxdepth 3 -type d` / `PROJECT_INDEX.json dir_purposes` | |
| Conventions | sampled source files (dimension 9 "claimed vs observed") | |
| Architecture description | dimension 3 findings | |
| Dragons / don't-touch | `.gitattributes` vendored/generated marks, `# DO NOT EDIT`, dimension 13 | |
| Secrets/config guidance | dimension 8/12 | |
| Releases/deploy | dimension 10 | |
| PR checklist & CI gates | dimension 7 | |
| Stale references | any file/dir/command mentioned that no longer exists | |
| Missing sections | anything in the template above that's absent and would help | |
| Contradictions with `CLAUDE.md` / `CONTRIBUTING.md` | cross-check | |

Then: `## Proposed rewrite` — the full new `AGENTS.md` per the template, ready to copy over **if
the owner approves**.

`AGENTS.review.md` shape:
```markdown
# AGENTS.md — review (<date> · <short-SHA> · by understand-codebase)

## Summary
<3-5 lines: overall is it accurate? what's the worst staleness? recommend keep/refresh/rewrite?>

## Section-by-section accuracy
| Section | Verdict | Evidence |
|---|:--:|---|
| ... | ⚠️ | "says `make test`; there is no `Makefile` — tests run via `pytest`" |

## Gaps (present in our analysis, absent from AGENTS.md)
- ...

## Proposed rewrite
<full AGENTS.md per the template>

> To apply: copy the "Proposed rewrite" block over `AGENTS.md`, or tell me "apply the AGENTS.md rewrite".
```
