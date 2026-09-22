# Plugin Surface Extraction — How Reliably Can Regex Recover the commands → skills → agents → hooks → rules Graph?

**Created:** 2026-09-22
**Author:** Claude (aa-ma-researcher), charting effort diagram-generation Ticket 4
**Reviewed-Through-Date:** 2026-09-22
**Valid-Through:** 2026-Q4 (invalidated by any skill/command/agent rename, or a change to how skills are invoked in prose)
**Sources:** repo at commit `75f5491`; `grep -rnoE` / `grep -P` over `claude-code/**/*.{md,sh}` (excluding `claude-code/codemem/`); a 60-line throwaway extractor run via `uv run python` (scratchpad only, not committed); `~/.claude/skills/` listing for external-skill resolution; `scripts/install.sh:314-323` for hook wiring; `CLAUDE.md:113` for the manual cross-ref rule.

## Answer

Regex is sufficient for a `Plugin surface` View, with one non-negotiable design choice: **node identity comes from the filesystem (dir/file stem), never from frontmatter `name:`**, and **edges come from four curated syntaxes** — `Skill(x)`, `/x` filtered against `commands/*.md`, `subagent_type=x`, and `<hook>.sh` literals. That set yields 163 edges from 42 source files and reaches 52/59 on-disk nodes with zero observed false positives after filtering. The residual problems are not extraction problems: 24 of 41 `Skill()` targets are *external* skills (gstack, global `~/.claude/skills`), and the 7 orphans are reached only by bare backtick mentions. A codemem markdown parser rule is not needed for the View; it would only add value for the intra-skill `references/*.md` sub-graph, which the View should not draw anyway.

## Reference syntaxes

All hit counts are over `claude-code/` excluding `claude-code/codemem/` (88 markdown files + 11 shell files). "Curated" = after dropping targets not on disk.

| Syntax | Regex | Hits (raw → curated) | True-positive example | False-positive / false-negative example |
|---|---|---|---|---|
| `Skill(name)` | `Skill\(([A-Za-z0-9_-]+)\)` | 159 → 108 (41 distinct names; 17 on disk, 20 external, 4 dangling) | `claude-code/rules/engineering-standards.md:80` → `first-principles-framework` (external); `claude-code/commands/execute-aa-ma-milestone.md:432` → `browse` (gstack) | **FP-external:** 11× `Skill(doc-drift-detection)` (e.g. `claude-code/agents/codebase-onboarding-health.md:37` — "you don't run the skill — borrow the checks") resolves to `~/.claude/skills/`, not this repo. **FP-wrong-kind:** `claude-code/skills/understand-codebase/SKILL.md:296` `Skill(aa-ma-plan)` — `aa-ma-plan` is a *command*. **FP-hypothetical:** `claude-code/skills/aa-ma-execution/SKILL.md:976` `Skill(haiku-eval)` ("or aa-ma-forge defines its own … wrapper"). **FN:** 4 on-disk skills have zero `Skill()` refs (see orphans). |
| `/command` mention | `(?<![A-Za-z0-9_./~-])/([a-z][a-z0-9-]+)(?![A-Za-z0-9_./-])` then keep iff `commands/<name>.md` exists | 369 → 181 (13/13 commands mentioned ≥1×; `aa-ma-plan` 53, `execute-aa-ma-milestone` 33, `verify-plan` 23) | `claude-code/skills/plan-verification/SKILL.md:370` → `/verify-plan`; `claude-code/commands/execute-aa-ma-milestone.md` → `/aa-ma-plan` (53 mentions repo-wide) | **FP-unfiltered:** `/goal` 41× (Claude Code built-in, `claude-code/skills/aa-ma-execution/SKILL.md:963`), `/index` 32×, `/healthz` (`…/DEEPDIVE-TEMPLATES.md:260`), `/endpoint` (`claude-code/skills/system-mapping/SKILL.md:118`), `/tmp` — all removed by the on-disk filter. **FP-path-fragment:** `claude-code/hooks/aa-ma-plan-marker.sh:84` `…/aa-ma-plan-${SLUG}.log` — the lookbehind stops it matching `aa-ma-plan` but a laxer regex would count it; `claude-code/commands/sole-dev-merge.md:48` `/tmp/sole-dev-merge-banner-shown` matches `sole-dev-merge` under `grep -w` (hyphen is a word boundary). **FN-glob:** `/execute-aa-ma-*` at `claude-code/skills/aa-ma-execution/SKILL.md:1291` and `…/aa-ma-plan-workflow/SKILL.md:303` names three commands and matches none. **FP-self:** 12 of `sole-dev-merge`'s 13 mentions and all 3 of `aa-ma-search`'s are inside their own file. |
| `subagent_type=x` | `subagent_type\s*[=:]\s*"?([A-Za-z0-9_-]+)"?` | 32 → 18 (12/12 agents reached) | `claude-code/skills/understand-codebase/SKILL.md:200` → `codebase-onboarding-conventions`; `…SKILL.md:207` → `codebase-onboarding-synthesizer` | **FP-builtin:** `Explore` 6×, `general-purpose` 6× (`claude-code/skills/understand-codebase/SKILL.md:78`) — Claude Code built-ins, not repo nodes. **FP-external:** `gsd-codebase-mapper` 2× (`…SKILL.md:196`). |
| `Agent(` call | `\bAgent\(` | 16 | all 16 co-occur with `subagent_type=` on the same line (`claude-code/skills/understand-codebase/SKILL.md:78,79,156,196-213`) | Redundant with the row above — carries no extra edges. |
| Bare agent name | `\b(aa-ma-scribe\|…\|security-auditor)\b` (12 alternatives) | 116 lines outside the owning file; `code-reviewer` 26, `aa-ma-validator` 19 | `claude-code/agents/codebase-onboarding-runbook.md:16` "Spawned by …" | Prose-only; `code-reviewer` collides with the generic phrase in `…SKILL.md:213` (`comprehensive-review:code-reviewer`). Use only as a fallback for orphan detection, not for edges. |
| `"Spawned by" / "Dispatched by"` | `spawned by\|dispatched by` (case-insensitive) | 16 (4 in `description:` frontmatter, e.g. `claude-code/agents/security-auditor.md:3`) | describes the *reverse* edge (agent ← skill/command) | Free prose; target name is not on the same line in 3 of 4 agent cases. Not worth a regex. |
| `agents/<x>.md` path | `agents/([a-z0-9-]+)\.md` | 4 | `aa-ma-validator.md` 2×, `security-auditor.md`, `aa-ma-scribe.md` | Too sparse to matter; subsumed by `subagent_type`. |
| Hook script literal | `\b((aa-ma-\|pre-compact-aa-ma\|security-static-check)[a-z0-9-]*\.sh)\b` | 91 → 89 (10/11 hooks reached; `aa-ma-parse.sh` 56, `aa-ma-plan-marker.sh` 8) | `claude-code/hooks/aa-ma-commit-drift.sh:25` `HELPER="${SCRIPT_DIR}/lib/aa-ma-parse.sh"` (real `source` edge, `:34`); `claude-code/commands/execute-aa-ma-milestone.md` 9× `aa-ma-parse.sh` | **FP-out-of-tree:** `aa-ma-share-allow.sh` 2× (`claude-code/commands/aa-ma-share.md:35`) lives in `scripts/`, not `hooks/`. **FN-wiring:** hook → event registration (`SessionStart`, `PreToolUse|Bash`) is *only* in `scripts/install.sh:314-323`, outside `claude-code/`. `aa-ma-session-end-dirty.sh` is referenced nowhere in `claude-code/` — only `scripts/install.sh:319`, `scripts/uninstall.sh:224`. |
| Rule file | `rules/([a-z-]+)\.md` | 21 → 18 (2/2 rules) | `claude-code/rules/engineering-standards.md` 15× (all from skills/commands citing themes) | **FP-external:** `rules/env-var-drift.md` 7×, `rules/plan-authoring-standards.md` 2×, `rules/python-quality-gates.md`, `rules/doc-drift-checks.md` — global `~/.claude/rules/`, not shipped here (`claude-code/skills/understand-codebase/references/DIMENSIONS.md:119`). |
| `claude-code/…` path | `claude-code/[A-Za-z0-9_./*-]+` | 51 (24 distinct) | `claude-code/hooks/lib/aa-ma-parse.sh` 5×; `claude-code/rules/engineering-standards.md` 15× | 7 of 24 are globs/dirs (`claude-code/skills/**`, `claude-code/hooks/`) — policy scope, not edges; `claude-code/codemem/mcp/server.py` 5× points outside the plugin surface; one trailing-dot artefact `…aa-ma-footer.sh.`. |
| `uv run aa-ma-*` | `uv run aa-ma-[a-z-]+` | 1 (`aa-ma-gate`) | bare `aa-ma-gate` 13×, `aa-ma-lint-views` 3× without the `uv run` prefix | 4 entry points exist (`pyproject.toml:32-37`); `aa-ma-tui`, `aa-ma-render` have 0 mentions in `claude-code/`. Prefix-anchored regex misses 15/16. |
| `Bash(...)` | `Bash\(` | 0 | — | Syntax is not used in this repo's plugin files; drop it. |
| Intra-skill `references/x.md` | `(references\|templates)/[A-Za-z0-9_-]+\.(md\|yaml\|json)` in `SKILL.md` | 77 | e.g. `claude-code/skills/aa-ma-plan-workflow/SKILL.md` → `references/PHASE_3_RESEARCH.md` | **FP-prefix-strip:** `claude-code/skills/verify-impl/SKILL.md:157` `docs/templates/impl-review-template.md` — regex captures `templates/impl-review-template.md`, which does not exist under the skill dir (the file is at `docs/templates/`). Path regexes must keep the full prefix. |

**Frontmatter as node identity — do not.** 6/21 `SKILL.md` files open with an HTML fork-provenance comment, so `^---` on line 1 fails (`claude-code/skills/prototype/SKILL.md:1`, `grilling`, `aa-ma-research`, `grill-with-docs`, `understand-codebase`, `write-a-skill`); `dispatching-parallel-agents/SKILL.md:2` has `name: Dispatching Parallel Agents` (≠ dirname); 2/13 commands carry no `name:` (`ops-mode.md`, `sole-dev-merge.md`). Agents are clean (12/12 `name:` == stem, 12/12 `tools:`). `description:` is 100% present on agents and commands and is the right label source; `tools:` gives an agent → built-in-tool edge (e.g. `tools: Read, Glob, Grep, Bash, Write` 2×) if the View wants it.

## Node coverage

On-disk inventory (`ls claude-code/*/`, commit `75f5491`): **13 commands, 21 skills (+ `FORKS.json`), 12 agents, 8 hooks + 3 `hooks/lib/` helpers, 2 rules = 59 nodes.** (README/CHANGELOG counts are 13/21/12/8/2 — matches.)

Curated extractor (four syntaxes, on-disk filter, self-edges dropped): **163 edges, 42 source files.**

| Kind | On disk | Reached | Orphans (no inbound edge from another node) | Reached by bare backtick mention instead |
|---|---|---|---|---|
| command | 13 | 11 | `aa-ma-search`, `sole-dev-merge` | `sole-dev-merge` via comment `claude-code/hooks/lib/aa-ma-footer.sh:5`; `aa-ma-search` genuinely unreferenced |
| skill | 21 | 17 | `aa-ma-execution`, `complexity-router`, `debugging-strategies`, `write-a-skill` | `aa-ma-execution` 3× (`…goal-condition-synthesis/SKILL.md:276`), `complexity-router` 5× (`…aa-ma-plan-workflow/SKILL.md:87`), `debugging-strategies` 10× (`…SKILL.md:94`); `write-a-skill` only in `FORKS.json:38` |
| agent | 12 | 12 | — | — |
| hook | 11 | 10 | `aa-ma-session-end-dirty.sh` | wired at `scripts/install.sh:319` only |
| rule | 2 | 2 | — | — |

The skill orphans are a real signal: `aa-ma-plan-workflow` names `complexity-router` and `debugging-strategies` in tables as `` `name` `` (`claude-code/skills/aa-ma-plan-workflow/SKILL.md:87,94`), never as `Skill(name)`. Whether that is a doc bug or an intentional "mentioned, not invoked" is a Ticket-4 policy call; the extractor should surface them as `orphan (backtick-only)` rather than silently add the edge.

**Dangling refs** (referenced from `claude-code/`, not on disk in this repo), 41 `Skill()` names split three ways:

- **External, resolvable in `~/.claude/skills/` (20):** `doc-drift-detection` 11, `ast-grep` 6, `code-intelligence` 6, `test-driven-development` 3, `code-intelligence-index` 2, `gsd-map-codebase` 2, `gsd-scan` 2, and 13 singletons incl. gstack `browse`, `qa-only`, `plan-{ceo,eng,design}-review` (`claude-code/commands/aa-ma-plan.md`). These are not broken references — they are cross-ecosystem edges and the View should render them as a distinct `external` node kind.
- **Truly dangling (4):** `aa-ma-plan` (wrong kind, `…understand-codebase/SKILL.md:296`), `haiku-eval` (hypothetical, `…aa-ma-execution/SKILL.md:976`), `index` and `codebase-deep-dive` (`…understand-codebase/references/REUSE-MAP.md:48,67` — these are *commands* in other ecosystems, mis-tagged as skills).
- **Agents:** `Explore`, `general-purpose` (built-ins), `gsd-codebase-mapper` (external). **Rules:** 4 global rule files. **Hooks:** `aa-ma-share-allow.sh` (`scripts/`).

**Versus the CLAUDE.md manual check** (`CLAUDE.md:113`: "grep -r "skill-name" claude-code/ docs/"): that check is per-name and answers "is this name still mentioned anywhere?"; it cannot find the 4 truly-dangling refs above (they *are* mentioned — that is the problem), does not distinguish external from missing, and does not detect orphans. The regex extractor answers all three in one pass; the manual check remains useful only for the docs/ side it already covers.

## Verdict

**Regex is sufficient; a codemem markdown parser rule is not required for this View.**

- **Precision with the curated set:** effectively 100% on the 163 emitted edges — every `Skill()`, filtered `/command`, `subagent_type`, and hook-literal hit inspected resolves to the intended node; the only prose-negation case found (`execute-aa-ma-milestone.md:427` "NEVER full `/qa`") targets an off-disk name and is filtered anyway. No "do not use `Skill(on-disk-name)`" sentences exist at `75f5491`.
- **Recall:** 52/59 nodes (88%). The 7 misses are all backtick-only or out-of-tree wiring, which a markdown AST would not recover either — it is a vocabulary gap, not a parsing gap.
- **Per-file allowlists needed (3, small):**
  1. Hook → event edges: read `scripts/install.sh` `AA_MA_HOOKS=(…)` table (`:314-323`) — the single place hooks are wired; regex `"([A-Za-z]+)\|([A-Za-z|]*)\|([a-z0-9-]+\.sh)\|`.
  2. External-skill resolution: an explicit list (or `ls ~/.claude/skills` at render time) to tag the 20 external names; without it they look identical to the 4 dangling ones.
  3. Self-reference and glob suppression: drop edges whose source == target; expand `/execute-aa-ma-*` (2 sites) to the three `execute-aa-ma-{full,milestone,step}` nodes.
- **When a parser rule *would* pay off:** only if the View grows to include the 77 intra-skill `SKILL.md → references/*.md` edges (a codemem rule could scope link resolution to the skill directory and avoid the `docs/templates/` prefix-strip FP shown above). Recommend keeping those out of the `Plugin surface` View — they are implementation detail of one node.
- **docs/ is OUT of the graph.** `docs/` is the plugin's *documentation of* the surface, not the surface: 58 markdown files carrying historical names (`Skill(research)` in `docs/adr/0012-research-skill-adoption.md:38,75,92` for what is now `aa-ma-research`; `CHANGELOG.md:51` records the rename; `CHANGELOG.md:29` records `write-a-skill` reclassification), 74× `/index`, 33× `/goal`, gstack `/ship`, `/freeze`, `/careful`. Including it would double the FP surface for zero new plugin edges. `docs/lessons.md` contains no deprecated-skill mentions at `75f5491`, but the point stands: docs describe history, `claude-code/` describes the shipped surface, and the View is of the latter. A separate "doc drift" check (Tier 6) already owns docs ↔ code consistency.

## Not pursued

- `claude-code/codemem/` (its own `commands/codemem.md`, `hooks/post-commit.sh`, `README.md`) — excluded; it is a separately-installed MCP sub-surface (`scripts/install.sh:463-475`, opt-in `--wire-git-hook`). Decide whether it is a second View.
- Agent → tool edges from `tools:` frontmatter (12 agents, 7 distinct tool sets) — counted, not graphed; trivial to add.
- `uv run aa-ma-*` CLI nodes — 16 bare mentions found but the View question was markdown surface; CLI belongs to the Python component view.
- Skill-to-skill edges via bare backtick names (e.g. `agent-teams` 10×, `debugging-strategies` 10×) — measured for orphan detection only; adding them as edges needs a policy on "mention vs invoke".
- Whether the 4 truly-dangling `Skill()` refs should be fixed — outside this ticket; flagged with file:line above.
- Reverse-edge prose ("Spawned by", "Dispatched by") — 16 hits, not machine-parsable; skipped.
