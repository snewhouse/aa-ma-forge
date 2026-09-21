# What does mattpocock/skills `writing-for-agents` contain at c55ee46, and how much overlaps what aa-ma-forge already ships?

**Created:** 2026-09-21
**Author:** aa-ma-researcher (Claude), for charting `writing-for-agents-eval` Ticket 1
**Reviewed-Through-Date:** 2026-09-21 (state of sources on this date)
**Valid-Through:** 2026-12-21 (invalidated by any upstream commit touching `skills/productivity/writing-for-agents/`, or by edits to the three local skills compared)
**Sources:**
- https://github.com/mattpocock/skills/blob/c55ee46/skills/productivity/writing-for-agents/SKILL.md — upstream body (10886 B); fetched via `gh api …?ref=c55ee46`, cited below as `SKILL.md:L`
- https://github.com/mattpocock/skills/blob/c55ee46/skills/productivity/writing-for-agents/SKILL-MECHANICS.md — skill-only branch (2629 B); cited as `SKILL-MECHANICS.md:L`
- https://github.com/mattpocock/skills/blob/c55ee46/skills/productivity/writing-for-agents/agents/openai.yaml — Codex interface metadata (102 B)
- https://github.com/mattpocock/skills/blob/c55ee46/CHANGELOG.md — rename entries (1.0.0, 1.2.0, 1.2.2) and the 1.1.0 Negation entry; cited as `CHANGELOG.md:L`
- https://github.com/mattpocock/skills/blob/c55ee46/skills/productivity/README.md — line 20 lists `writing-for-agents` (model-invoked list)
- GitHub commits API (`gh api repos/mattpocock/skills/commits/<sha>`) — dates for 47bde84, 77d207e, 4aaccb5, af6d692, c55ee46 and the six release-tag commits
- `claude-code/skills/write-a-skill/SKILL.md` (118 lines) — local Derived skill
- `/home/sjnewhouse/.claude/skills/skill-developer/SKILL.md` (426 lines) — global skill
- `/home/sjnewhouse/.claude/skills/writing-clearly-and-concisely/SKILL.md` (72 lines) — global skill, deprecated for direct use
- `docs/adr/0004-write-a-skill-adoption.md` — fork history and the 2026-09-21 amendment
- `claude-code/skills/FORKS.json:38-48` — `write-a-skill` row (state `derived`, `upstream_md5.SKILL.md: null`)

## Answer

At c55ee46 `writing-for-agents` is a two-file, all-reference (no steps) skill: `SKILL.md` (7 sections, 8 named levers/failure modes: context pointer, the two loads, information hierarchy, completion criteria, split-by-sequence, leading words, negation, pruning/cache/no-op) plus `SKILL-MECHANICS.md` (invocation choice, split-by-invocation, router skills). Tallied over the 25 rule rows in the overlap table (one verdict per row): 12 are new (no local counterpart), 9 are partial overlaps with `write-a-skill`/`skill-developer`/`writing-clearly-and-concisely` on a different criterion or scope, 1 is duplicated locally (prompt the positive = Strunk rule 11 via `writing-clearly-and-concisely`), and 3 conflict with local text (trigger-keyword maximalism, line-count split thresholds, "Use when" mandated for every description). It shares no text with our `write-a-skill` — the upstream lineage was rewritten from scratch at 1.0.0, so there is nothing byte-comparable to re-fork.

## Evidence

### 1. Rules stated, section by section

Frontmatter: `name: writing-for-agents`; `description: Writing documents for agents. Use when creating or editing skills, or modifying AGENTS.md or CLAUDE.md.` — no `disable-model-invocation`, so model-invoked (`SKILL.md:1-4`; README listing `skills/productivity/README.md:20`).

**SKILL.md**

| # | Section | Rule (one line) | Cite |
|---|---------|-----------------|------|
| S0 | Preamble | Scope is any document an agent consumes (skill, `AGENTS.md`/`CLAUDE.md`, pointer-reached doc); the levers make the agent take the same *process* each run, not the same output. | `SKILL.md:6` |
| S0b | Preamble | When the document is a skill, also read `SKILL-MECHANICS.md`. | `SKILL.md:8` |
| S1 | Context pointers | A pointer's *wording*, not its target, decides when material is reached; a must-have target behind a weak pointer is a variance bug — sharpen wording first, inline only if that fails. | `SKILL.md:12` |
| S1b | Context pointers | A pointer states what the material is and lists the trigger **branches**; always-loaded pointers are pruned harder than the body. | `SKILL.md:14` |
| S1c | Context pointers | Front-load the leading word; one trigger per branch (collapse synonyms); cut identity the body already carries. | `SKILL.md:16-18` |
| S2 | The two loads | Every doc/pointer spends **context load** (always-loaded tokens, every turn) or **cognitive load** (the human as index); cognitive load is not to be minimised — spend it where human judgement matters. | `SKILL.md:22-27` |
| S3 | Information hierarchy | Content is **steps** or **reference**; place each on a three-rung ladder: in-file step → in-file reference → disclosed reference behind a pointer. | `SKILL.md:31-37` |
| S3b | Information hierarchy | **Progressive disclosure** is the move down the ladder; it is not primarily token optimisation; branching is the test — inline what every branch needs, disclose what only some branches reach; undisclosed reference buries steps (a variance lever). | `SKILL.md:39` |
| S3c | Information hierarchy | **Co-location**: keep a concept's definition, rules and caveats under one heading; distinct from duplication. | `SKILL.md:41` |
| S3d | Information hierarchy | **Sprawl** (too long even when every line is live) is cured by the ladder: disclose reference, split by branch or sequence. | `SKILL.md:43` |
| S4 | Completion criteria | Every step ends on a completion criterion; **clarity** guards against premature completion — sharpen the bound first, hide later steps only across a real context boundary (hand-off/subagent). | `SKILL.md:47-49` |
| S4b | Completion criteria | **Demand** drives legwork; "every rule applied" binds flat reference just as "every step done" binds a sequence; strongest criteria are checkable and exhaustive. | `SKILL.md:50-52` |
| S5 | When to split | Splitting spends one of the two loads; split **by sequence** when post-completion steps tempt rushing; merging sequences invites premature completion; split by invocation → MECHANICS. | `SKILL.md:56-59` |
| S6 | Leading words | A pretrained compact concept repeated as a token (never a sentence) anchors behaviour cheaply; prefer an existing word over coining one. | `SKILL.md:63` |
| S6b | Leading words | It anchors execution (in the body) and invocation (in the pointer, when the word is shared across prompts/docs/codebase). | `SKILL.md:65` |
| S6c | Leading words | Hunt restatements to collapse into one token (e.g. "fast, deterministic, low-overhead" → *tight*); assume every document carries some. | `SKILL.md:67-72` |
| S6d | Negation | Steering by prohibition makes the forbidden behaviour *more* available; prompt the positive; a prohibition earns its place only as a hard guardrail and even then paired with the positive target. | `SKILL.md:74` |
| S7 | Pruning | Single source of truth per meaning; duplication costs maintenance/tokens and inflates rank on the ladder. | `SKILL.md:78` |
| S7b | Pruning | The **environment** (`package.json` scripts, config, layout, `--help`) is a source of truth; a doc restating it is a **cache** — cache only what the agent cannot find by looking (unwritten conventions, reasons, gotchas). | `SKILL.md:79` |
| S7c | Pruning | Check every line for **relevance**; stale layers accumulate as **sediment**; shorter documents stay relevant more easily. | `SKILL.md:80` |
| S7d | Pruning | Hunt **no-ops** sentence by sentence; the test is model-relative and settled by running the document; delete the whole sentence; a too-weak leading word is a no-op fixed by a stronger word. | `SKILL.md:80` |

**SKILL-MECHANICS.md**

| # | Section | Rule (one line) | Cite |
|---|---------|-----------------|------|
| M1 | Invocation | **Model-invoked** keeps a `description` (the skill's always-loaded context pointer; permanent context load for discoverability); other skills can reach it; a model-invoked all-reference skill is the home for shared reference. | `SKILL-MECHANICS.md:9` |
| M1b | Invocation | **User-invoked** sets `disable-model-invocation: true`; the description becomes human-facing, trigger lists stripped; zero context load, spends cognitive load. | `SKILL-MECHANICS.md:10` |
| M1c | Invocation | Pick model-invocation only when the agent or another skill must reach it; otherwise user-invoke and pay no context load. | `SKILL-MECHANICS.md:12` |
| M1d | Invocation | Shared reference needed by two user-invoked skills lives in a plain file outside the skill system. | `SKILL-MECHANICS.md:14` |
| M2 | Splitting by invocation | Split off a model-invoked skill only when a distinct leading word you actually use should trigger it, or another skill must reach it. | `SKILL-MECHANICS.md:18` |
| M3 | Router skills | When user-invoked skills outgrow memory, one user-invoked **router skill** names the others and when to reach each; it can hint, never fire them. | `SKILL-MECHANICS.md:22` |

`agents/openai.yaml` carries only `interface.display_name` / `short_description` (no `policy` block) — the Codex metadata fixed in 1.2.2 (`CHANGELOG.md:21-25`).

### 2. Overlap table

Local files abbreviated: **WAS** = `claude-code/skills/write-a-skill/SKILL.md`; **SD** = `~/.claude/skills/skill-developer/SKILL.md`; **WCC** = `~/.claude/skills/writing-clearly-and-concisely/SKILL.md`. "Partial" = same concern, different criterion or narrower scope.

| Rule | Verdict | Local cite / note |
|------|---------|-------------------|
| S0 scope: any agent-consumed doc incl. CLAUDE.md | **new** | WAS and SD are skill-only; WCC is human-prose-only (`WCC:8,26`) |
| S1 pointer wording decides reach; sharpen before inlining | **new** | WAS says the description is "the only thing your agent sees" (`WAS:63`) but gives no sharpen-vs-inline rule |
| S1b pointer = what + trigger branches | partial — duplicated by WAS | `WAS:65-68` ("what capability … when/why to trigger it") |
| S1c one trigger per branch, collapse synonyms | **conflicts with SD** and with WAS's own practice | `SD:136` "Include ALL trigger keywords/phrases"; `SD:385` "Rich descriptions: Include all trigger keywords"; WAS's own description lists "create, write, or build" — one branch written three times (`WAS:4`); WAS good-example stacks "PDFs, forms, or document extraction" (`WAS:80`) |
| S1c front-load the leading word | **new** | not found locally |
| S2 context load vs cognitive load | **new** | not found in the three files (adjacent: `~/.claude/rules/token-efficiency.md` three-tier table — see Not pursued) |
| S3 steps vs reference; three-rung ladder | partial — duplicated by WAS/SD as "progressive disclosure" | `WAS:4,101-107`; `SD:137,186,382` name the concept without the steps/reference distinction |
| S3b disclosure test is branching, not line count | **conflicts with WAS and SD on criterion** | `WAS:19` (>500 lines → extra files), `WAS:105,114` (SKILL.md ≤100 lines); `SD:137,185,287,381` (500-line rule). Upstream: "Not primarily a token optimisation" (`SKILL.md:39`) |
| S3c co-location | partial — duplicated by WCC | `WCC:55` rule 8 "One paragraph per topic"; `WCC:63` rule 16 "Keep related words together" (sentence-level, not document-level) |
| S3d sprawl | partial — WAS/SD express it only as line caps | `WAS:105,114`; `SD:381` |
| S4 completion criterion on every step; clarity vs premature completion | **new** | not found in the three files (adjacent: AA-MA `Acceptance Criteria:` per sub-step — see Not pursued) |
| S4b demand / legwork / exhaustive bound | **new** | not found |
| S5 split by sequence | **new** | WAS splits by size/domain/rarity only (`WAS:103-107`); SD by size (`SD:137`) |
| S6–S6c leading words | partial — WAS "Consistent terminology" | `WAS:116` is a checklist item, not the pretrained-token mechanism; SD's "gerund naming" (`SD:135,387`) is a naming convention, not a leading word |
| S6d negation → prompt the positive | **duplicated by WCC** | `WCC:58` rule 11 "Put statements in positive form" (Strunk; human-reader rationale, not the availability argument). Note WAS's own checklist item "No time-sensitive info" (`WAS:115`) is a prohibition |
| S7 single source of truth / duplication | partial — repo-level only | no rule in the three skills; the repo practises it via `FORKS.json` MD5s and the "no broken references" constraint (`CLAUDE.md` Key Constraints), not as a writing rule |
| S7b environment is SoT; docs are caches | **new** | not found |
| S7c relevance / sediment | partial — duplicated by WAS | `WAS:115` "No time-sensitive info" (narrower: time-sensitivity only) |
| S7d no-op hunt, model-relative, delete whole sentence | partial — duplicated by WCC | `WCC:60` rule 13 "Omit needless words" (reader-relative; no run-the-document test). SD "Test with 3+ real scenarios" (`SD:189,386`) is a trigger test, not a no-op test |
| M1 model-invoked = description as always-loaded pointer | partial — duplicated by WAS/SD | `WAS:63` (description surfaced in system prompt); `SD:119` — neither names the cost as context load |
| M1b `disable-model-invocation: true`; human-facing description | **conflicts with WAS checklist** (the flag itself is also new locally; counted once, as a conflict) | `WAS:113` "Description includes triggers ('Use when…')" and `WAS:75` mandate a trigger sentence for every skill; upstream strips triggers from user-invoked descriptions (`SKILL-MECHANICS.md:10`). Flag is absent from all 21 shipped skills (grep `claude-code/`: 0 hits) and from SD |
| M1c choose invocation by who must reach it | **new** | not found |
| M1d shared reference for user-invoked skills → plain file | **new** | not found |
| M2 split by invocation | **new** | not found |
| M3 router skills | **new** | not found (SD's `skill-rules.json`/hook activation system is orthogonal — a different routing mechanism, `SD:28-58`) |

Rules local files have that upstream dropped (no counterpart at c55ee46): WAS process gather → draft → review (`WAS:9-25`); skill directory structure and SKILL.md template (`WAS:27-59`); when to add scripts (`WAS:91-99`); 1024-char description cap and third-person voice (`WAS:72-73`, `SD:136`); references one level deep (`WAS:118`, `SD:384`); SD's whole hook/`skill-rules.json`/enforcement-level apparatus (`SD:28-58,194-267`).

Counts (one verdict per row): new 12 · partial 9 · duplicated 1 (S6d) · conflicts 3 (S1c, S3b, M1b) — total 25 rule rows above.

### 3. Upstream file identity at c55ee46

Decoded content from `gh api "repos/mattpocock/skills/contents/skills/productivity/writing-for-agents/<file>?ref=c55ee46" --jq .content | base64 -d`; c55ee46 committed 2026-09-18T10:12:29Z.

| File | Bytes | md5 (decoded content) | git blob SHA |
|------|-------|-----------------------|--------------|
| `SKILL.md` | 10886 | `9663b04e7529a8d72e82a6fd088d336d` | `a37608daf6e835e767deecfb498facecaaba82ba` |
| `SKILL-MECHANICS.md` | 2629 | `f3648a8f71f8672f89c23dc0dbafc43c` | `9cdbdb22aadc438755392216e75ad9a14cc9832e` |
| `agents/openai.yaml` | 102 | `1ec4866a3ad2fba3e9a44c6db860efd7` | (listed in `agents/` tree, sha `1a0e4610…` for the dir) |

For comparison the local `write-a-skill/SKILL.md` MD5 on record is `492ef034b4fc9e497cc69b8fed78a742` (`FORKS.json:45`; ADR-0004 line 135) — no byte overlap with either upstream file.

### 4. CHANGELOG rename entries, verbatim

Changesets CHANGELOGs carry no dates; dates below are from the GitHub commits API (release-tag merge commit, and the changeset's linked commit).

**1.0.0** (tag `v1.0.0` → bddb833, 2026-06-17T14:46:32Z; linked commit 47bde84, 2026-06-17T14:39:06Z) — `CHANGELOG.md:254-260`, under `### Major Changes`:

> - [`47bde84`](https://github.com/mattpocock/skills/commit/47bde84da032afb2e5058f997f3bbca47d321dbd) Thanks [@mattpocock](https://github.com/mattpocock)! - Replace **`write-a-skill`** with **`writing-great-skills`**.
>
>   - Removed `write-a-skill`.
>   - Added `writing-great-skills` (plus its `GLOSSARY.md`) — a reference for writing and editing skills well: the vocabulary and principles that make a skill predictable, hunting no-ops down to the sentence level.
>   - Exposed `grilling` as a model-invoked skill — the reusable interview loop behind `grill-me` and `grill-with-docs`.
>
>   **Breaking:** `write-a-skill` has been removed; use `writing-great-skills` instead.

**1.2.0** (tag `v1.2.0` → 2ffb184, 2026-08-05T12:37:24Z; linked commit 77d207e, 2026-08-05T12:07:04Z) — `CHANGELOG.md:88-92`, under `### Minor Changes`:

> - [#763](https://github.com/mattpocock/skills/pull/763) [`77d207e`](https://github.com/mattpocock/skills/commit/77d207ef03219cc603e2832e1159cbdd1c91818e) Thanks [@mattpocock](https://github.com/mattpocock)! - **Breaking:** rename **`writing-great-skills`** → **`writing-for-agents`**, restructure it, and add a new leading word.
>
>   The reference now covers any document an agent consumes — skills, `AGENTS.md` / `CLAUDE.md`, docs reached by a pointer — not just skills. `GLOSSARY.md` is merged into `SKILL.md` (one authoritative treatment per term; the `_Avoid_` synonym lists and the standalone Predictability definition are gone); the skill-only mechanics (frontmatter, model- vs user-invoked, router skills, the invocation cut of splitting) are disclosed to a new `SKILL-MECHANICS.md`. The skill is now **model-invoked**: it fires when creating or editing skills or modifying `AGENTS.md`/`CLAUDE.md`. `ask-matt`'s pointer updated. Reinstall under the new name; the old name is gone (no alias).
>
>   The pruning section gains **cache**. Single source of truth now reaches past the document into the environment — `package.json` scripts, config files, directory layout, `--help` output are themselves authoritative, so a doc that restates them is a cache of a lookup, earning its load only when the lookup is expensive. The positive target: cache what the agent cannot find by looking (unwritten conventions, the reason behind a choice, gotchas no config confesses), and leave one-file, one-command lookups to the environment, where they cannot go stale.

**1.2.2** (tag `v1.2.2` → 8b36d4f, 2026-08-05T18:09:58Z; linked commit 4aaccb5, 2026-08-05T15:53:54Z) — `CHANGELOG.md:21-25`, under `### Patch Changes`:

> - [#766](https://github.com/mattpocock/skills/pull/766) [`4aaccb5`](https://github.com/mattpocock/skills/commit/4aaccb58d40559d7e3c59a029b2290ae5ba538de) Thanks [@mattpocock](https://github.com/mattpocock)! - Make `writing-for-agents` model-invokable in Codex again.
>
>   - Drop `policy.allow_implicit_invocation: false` from `agents/openai.yaml`. Codex filtered the skill out of the model-visible skills list, so its description could not trigger it — only an explicit `$writing-for-agents` mention worked.
>   - Update the stale `interface.display_name` and `interface.short_description`, which still named the old `writing-great-skills` skill.
>   - Move the skill from the **User-invoked** list to the **Model-invoked** list in `README.md` and `skills/productivity/README.md`.

Related, not a rename: **1.1.0** (`CHANGELOG.md:173`, tag `v1.1.0` → d574778, 2026-07-08T13:20:40Z) records adding *two* Steering failure modes to `writing-great-skills` — **Negation** and **Negative Space** — yet its linked commit af6d692 (2026-07-06T12:57:05Z) is titled "Drop Negative Space; keep Negation only", and c55ee46 `SKILL.md` carries Negation only (`SKILL.md:74`). Treat the 1.1.0 entry as over-describing what shipped.

### 5. Accuracy notes on local records

- ADR-0004 Amendment (`docs/adr/0004-write-a-skill-adoption.md:142-144`) says the skill was "renamed `writing-great-skills`, then `writing-for-agents`, and removed from mattpocock/skills in 1.0.0 (2026-06-17)". Per the entries above: the *name* `write-a-skill` was removed in 1.0.0 and replaced by a rewrite; the `writing-for-agents` rename landed in 1.2.0 (2026-08-05); the lineage is alive at c55ee46. "No upstream file to re-fork from" holds only in the byte-for-byte sense (the rewrite shares no text with our copy).
- ADR-0004 rationale (`:51`, `:62`) that the 100-line cap and "Use when" phrasing are "exactly what aa-ma-forge needs" now describes rules upstream has abandoned (S3b, M1b).
- `docs/research/mattpocock-trio-2026-09.md:79` correctly flags `write-a-skill` as "deleted upstream (→ `writing-for-agents`). Orphan."

## Not pursued

- `~/.claude/rules/token-efficiency.md` three-tier context architecture (always/auto/on-demand) vs upstream's "two loads" and ladder — outside the three files named in the ticket; a Ticket 2 input if the fork is meant to feed `/aa-ma-plan`.
- Mapping S4 completion criteria onto AA-MA `Acceptance Criteria:` / `Result Log:` per sub-step and the `aa-ma-scribe` agent's writers — the "Not yet specified" item in the charting map; needs a decision, not research.
- Auditing the 21 shipped skills' descriptions against S1c (one trigger per branch) — explicitly out of scope in the map.
- Whether Codex's `agents/openai.yaml` matters to a Claude-Code-only plugin — not asked.
- Upstream `docs/invocation.md` (1.0.0 taxonomy) and `ask-matt`'s pointer to this skill — not fetched; secondary to the two files.
- Diffing `writing-great-skills` at v1.1.0 (with `GLOSSARY.md`) against c55ee46 to see what the 1.2.0 merge dropped (`_Avoid_` lists, Predictability) — not asked.
