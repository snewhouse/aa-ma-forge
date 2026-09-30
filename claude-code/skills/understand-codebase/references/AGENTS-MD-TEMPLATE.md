# AGENTS-MD-TEMPLATE — author / review / improve an AGENTS.md

Dimension 19. `understand-codebase` learns far more than an `AGENTS.md` should hold. An agent can
read the stack, the layout, the architecture and the conventions from the code itself; `AGENTS.md`
keeps **only what the code cannot tell it**: the exact commands (with their checked status), the
gotchas that bite, and pointers to the rules files. This file says how to write it — **safely**.

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

## TEMPLATE — `AGENTS.md` (three sections; keep it under ~60 lines)

Nothing an agent can infer from the code goes in (stack, layout, architecture, style the linter
enforces). Every command carries the currency-check status from `onboarding.json`; every gotcha
cites a path.

```markdown
# AGENTS.md

> Instructions for AI coding agents working in this repository. The full walkthrough is
> `ONBOARDING.md`. Last reviewed: <date> · <short-SHA> · by understand-codebase.

## Commands
- Install: `<command>` — <verified | failed | timeout | not_run | refused>
- Test (fast, before every commit): `<command>` — <status>
- Test (full, before pushing): `<command>` — <status>
- Lint / format / type check: `<command>` — <status>
- Tool versions this needs: `<from .python-version / .nvmrc / .tool-versions>`

## Gotchas
- `<generated/vendored/frozen path>` — never hand-edit; regenerate with `<command>`
- <a trap the code does not announce: the async/sync split, a required service, an order of steps> (`<path:line>`)
- Never commit secrets or read `.env`, `*.key`, `*.pem` or credential files; env var names are in `<.env.example>`.

## Rules pointers
- `CLAUDE.md` / `CONTRIBUTING.md` / `.cursorrules` / `CODEOWNERS` — <one line: what each mandates>
- Commit convention: <Conventional Commits / project style>; CI checks that block merge: `<list>`
```

---

## REVIEW CHECKLIST — for an existing `AGENTS.md` (→ `AGENTS.review.md`)

For each row: verdict = ✅ accurate / ⚠️ stale / ❌ wrong/missing — with **evidence**.

| Section | Check against | Verdict + evidence |
|---|---|---|
| Commands | the currency-check status in `onboarding.json` (the main thread ran them via `aa-ma-analysis run`, or they are `not_run`); the `Makefile`/`package.json` scripts they reference still exist | |
| Required tool versions | `.nvmrc`/`.python-version`/`.tool-versions`/`Dockerfile` | |
| Lint/format/typecheck commands & configs | the config files exist; commands still valid | |
| Gotchas | `.gitattributes` vendored/generated marks, `# DO NOT EDIT`, dimension 13 | |
| Secrets/config guidance | dimension 8/12 | |
| Rules pointers & CI gates | dimensions 7 and 11 | |
| Stale references | any file/dir/command mentioned that no longer exists | |
| Missing sections | Commands / Gotchas / Rules pointers absent | |
| Inferable content | layout, architecture or style an agent can read from the code — propose cutting it | |
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
