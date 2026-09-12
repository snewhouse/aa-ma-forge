<!-- ARCHIVED: 2026-09-12 16:57 -->
<!-- Plan: plan-architecture-views - COMPLETE -->
<!-- Total Milestones: 4 | Duration: 2026-09-11 to 2026-09-12 -->

# plan-architecture-views Reference

## Immutable Facts and Constants

Architecture View: see plan.md §13

### Release / sequencing
- Current version: `pyproject.toml` **0.11.0** (tagged 2026-09-12 by milestone-grammar-ssot) → target **v0.12.0**. Every "v0.11.0+" label in this plan's new prose is written as v0.12.0; the literal cutover date 2026-09-11 is unchanged.
- `CHANGELOG.md` has no `## Unreleased` section at HEAD (cz bump consumed it) — Sub-step 1.8 re-creates it above `## v0.11.0` (L-003: never edit version headings)
- Angle 6 grandfathering cutover for checks #6/#7: literal date **2026-09-11** (not "release date")
- M2 depends on `milestone-grammar-ssot` M5 (sub-step 5.0 fixes `grammar.split_milestones` trailing-H2; 5.1/5.3 create `src/aa_ma/enforce.py`, `src/aa_ma/gate.py`). M5 never edits `src/aa_ma/plan_parsers.py`.
- ADR number for this plan: **0010** (0009 is reserved by grammar-ssot sub-step 5.8)
- Milestone order: M1 Standard → M2 Lint → M3 Share → M4 Render (optional; dropped only via documented scope reduction — `SKIPPED` is not a `MilestoneStatus`)

### Canonical values (planning-time only)
- `Diagram-Waiver:` ∈ {`none`, `docs-only`, `config-only`, `single-file`}; plan-level front matter; read by `plan_parsers.parse_diagram_waiver`; **never a gate field** (`aa_ma.enforce` does not read it)
- View required iff any milestone `Audit-Profile ∈ {full, code-only, infra}` (`CODE_AUDIT_PROFILES`)
- Flow view required iff any milestone carries `Critical-Path:`
- Contract block: `#### Contract` + ≥1 fence, per code milestone
- `KNOWN_TYPES`: flowchart, graph, sequenceDiagram, classDiagram, stateDiagram-v2, erDiagram, C4Context, C4Container, C4Component
- Lint finding codes: NO_SECTION NO_COMPONENT_VIEW NO_FLOW_VIEW EMPTY_FENCE UNKNOWN_TYPE STALE_PATH WAIVER_INVALID WAIVER_NOT_ALLOWED AUDIT_PROFILE_INVALID
- `render_status`: PASS | FAIL | UNKNOWN. mmdc rc≠0 → UNKNOWN unless stderr contains `Parse error on line` / `UnknownDiagramError` → FAIL. rc 0 with empty/absent SVG → UNKNOWN.
- Mermaid labels containing parentheses MUST be quoted: `B["path (new)"]` — unquoted `(new)` inside `[...]` is a parse error (measured, mermaid 11.17.2)
- Section heading accepted by lint: `^## (?:13\.?[ \t]+)?Architecture View`
- plan.md milestones are `### Milestone N:`; tasks.md milestones are `## Milestone N:`; the lint promotes H3→H2 before `split_milestones`

### Paths / signatures (pinned)
- M1 authoring surface (the seven files the M1 measurable goal greps for "Architecture View"): `docs/spec/aa-ma-specification.md` (§XI item 13, §II diagram), `claude-code/skills/plan-verification/SKILL.md` (Angle 6 checks #6/#7), `docs/templates/plan-template.md` (§12, §13, Contract), `docs/adr/TEMPLATE.md`, `claude-code/agents/aa-ma-scribe.md`, `claude-code/skills/aa-ma-plan-workflow/references/PHASE_4_PLAN_GENERATION.md`, `claude-code/commands/aa-ma-plan.md`; plus `claude-code/rules/{aa-ma,engineering-standards}.md` (auto-loaded) and `docs/adr/0010-architecture-views-and-render.md`
- `src/aa_ma/plan_parsers.py`: `CANONICAL_DIAGRAM_WAIVERS`, `parse_diagram_waiver(text) -> (value, is_valid, error)` via `_parse_canonical_field`
- `src/aa_ma/render/` (new, leaf): `__init__.py`, `mermaid_lint.py`, `cli.py` (M2); `html.py` (M4)
- `lint_text(plan_text, repo_root, *, tasks_text="") -> LintReport`; `lint_plan(plan_path, repo_root, *, tasks_path=None)`; `render_check(sources, *, timeout_s=90.0) -> str`
- CLIs (`pyproject [project.scripts]`): `aa-ma-lint-views = "aa_ma.render.cli:lint_main"` (exit 0/1/2; `--repo-root`, `--tasks`); `aa-ma-render = "aa_ma.render.cli:render_main"` (exit 0/2; `--out build/render`)
- `render_markdown(text, *, title) -> str`; `MERMAID_VERSION` = latest 11.x at prototype (11.17.2 on 2026-09-11); markdown-it-py `commonmark` + `enable(["table","strikethrough"])`, `html: True` + `html_block`/`html_inline` rules (comments → "", else escaped)
- `.importlinter`: `root_packages = codemem, aa_ma` (replaces `root_package`); contract `render-is-leaf` (forbidden; sources tui, grammar, plan_parsers, plan_markers, enforce, gate → forbidden aa_ma.render); `tests/codemem/test_install_and_cli.py::test_contracts_kept` expects `"Contracts: 3 kept, 0 broken."` after M2
- Repo-root resolution for global commands/skills: `AA_MA_ROOT=$(cd "$(dirname "$(readlink -f ~/.claude/commands/aa-ma-share.md)")/../.." && pwd)`; skills use `../../..`
- `scripts/aa-ma-share-allow.sh` pattern: `*-plan.md|*docs/adr/*.md|*docs/spec/*.md` (exit 0 allow / 1 refuse)
- `/aa-ma-share` publishes **markdown** to the Artifact tool (it wraps content in its own skeleton and renders mermaid natively) — never HTML from `aa-ma-render`
- Env seam: `MMDC_BIN` (default `mmdc`); `tests/render/conftest.py` autouse pins `/nonexistent/mmdc`
- `build/` already in `.gitignore:34`; `install.sh:127` globs `claude-code/commands/*.md`; spec docs are **copied** to `~/.claude/docs/` — re-run `scripts/install.sh` after M1

### Environment (BATS, measured 2026-09-11)
- `.venv` markdown-it-py **4.0.0** (conda env on PATH has 4.2.0 — verify with `uv run python -c`, never bare `python3`)
- uv 0.12.3 (`--project` supported); import-linter 2.6 (`root_packages` supported)
- `mmdc` 11.17.0 on PATH via conda env, **no chrome-headless-shell**: valid diagram → rc=1 "Could not find chrome-headless-shell"
- Node 26.5.0 / npm 11.17.0 (conda env)

### Element-count sites (gate grep at HEAD, 29 hits — update all to 13 in Sub-step 1.5; re-run the grep at execution)
Gate: `grep -rnE "\b1[12] (AA-MA |required |mandatory )?(elements|outputs|planning elements)|ALL 12|all 12" claude-code/ docs/spec/ docs/templates/ README.md CLAUDE.md`
- `claude-code/rules/aa-ma.md:115`
- `claude-code/skills/aa-ma-plan-workflow/SKILL.md:65`
- `claude-code/skills/aa-ma-plan-workflow/SKILL.md:222`
- `claude-code/skills/aa-ma-plan-workflow/SKILL.md:229`
- `claude-code/skills/aa-ma-plan-workflow/SKILL.md:415`
- `claude-code/skills/aa-ma-plan-workflow/references/PHASE_5_ARTIFACT_CREATION.md:136`
- `claude-code/skills/aa-ma-plan-workflow/references/PHASE_5_ARTIFACT_CREATION.md:315`
- `claude-code/skills/aa-ma-plan-workflow/references/SKILL_INTEGRATION.md:257`
- `claude-code/skills/aa-ma-plan-workflow/templates/validation-checklist.md:64`
- `claude-code/agents/aa-ma-scribe.md:42`
- `claude-code/agents/aa-ma-scribe.md:237`
- `docs/spec/claude-code-foundations.md:75`
- `docs/spec/claude-code-foundations.md:150`
- `claude-code/skills/aa-ma-plan-workflow/references/PHASE_4_PLAN_GENERATION.md:65`
- `claude-code/skills/aa-ma-plan-workflow/references/PHASE_4_PLAN_GENERATION.md:70`
- `claude-code/skills/aa-ma-plan-workflow/references/PHASE_4_PLAN_GENERATION.md:141`
- `claude-code/skills/aa-ma-plan-workflow/references/PHASE_4_PLAN_GENERATION.md:193`
- `claude-code/skills/aa-ma-plan-workflow/references/PHASE_4_PLAN_GENERATION.md:257`
- `claude-code/skills/aa-ma-plan-workflow/references/PHASE_4_PLAN_GENERATION.md:275`
- `docs/templates/README.md:9`
- `CLAUDE.md:91`
- `README.md:100`
- `claude-code/agents/aa-ma-validator.md:48`
- `claude-code/agents/aa-ma-validator.md:146`
- `claude-code/commands/aa-ma-plan.md:445`
- `claude-code/commands/aa-ma-plan.md:462`
- `claude-code/commands/aa-ma-plan.md:678`
- `docs/templates/plan-template.md:6`
- `docs/templates/plan-template.md:31`
Excluded (frozen history, never edited): `docs/adr/0001-*.md:91`, `docs/narrative/how-we-got-here.md:65,67`, `docs/runbooks/rollback-v0.5.0.md:10`, `docs/plans/*`.

### Hardcoded counts (commands 11 → 12 at M3)
- `CLAUDE.md:48`, `SECURITY.md:11`, `README.md` `### All commands` table (~208-219, add row), `CHANGELOG.md` Unreleased

### Structural context (PROJECT_INDEX.json)
- Key entry points touched: `aa_ma.plan_parsers._parse_canonical_field`, `aa_ma.grammar.split_milestones`, `aa_ma.grammar.strip_fenced_blocks`, `aa_ma.tui.__main__.main` (argparse pattern)
- Directory purposes: `claude-code/` (shipped prompt surface, symlinked), `src/aa_ma/` (Python SSoT: grammar, parsers, TUI), `tests/` (pytest + bats), `docs/spec/` (canonical spec, copied on install)

### M1 facts (landed 2026-09-12)
- Spec §XI item 13 at `docs/spec/aa-ma-specification.md:604`; §II file-flow diagram at `:32`
- Angle 6 checks #6/#7 at `claude-code/skills/plan-verification/SKILL.md:396-409`; grandfathering bullet ~`:432`; auditor remit line `:339`
- `docs/adr/0010-architecture-views-and-render.md` — Status **Accepted** → flip to Implemented at M3 close
- Element-count consistency: `tests/commands/test_planning_standard_count.py` (spec §XI count is the SSoT; supersedes the one-shot `1[12]` grep for future bumps)
- Mermaid parse/render check without mmdc: playwright `chromium_headless_shell-1234` + mermaid 11.17.2 UMD (`$(npm root -g)/@mermaid-js/mermaid-cli/node_modules/mermaid/dist/mermaid.min.js`) — usable as a stronger local seam at M2.5
- `bats` 1.13.0 now installed at `/usr/bin/bats`

### M2 facts (landed 2026-09-12)
- Lint finding codes now **10**: the 9 pinned above + `UNTERMINATED_FENCE` (render UNKNOWN, early return)
- `grammar.H2_RE` is public (alias of `_H2_RE`, `^##(?:[ \t]|$)`); the lint uses it for the front-matter split and section end — never a private `^## `
- Plan H3→H2 promotion: a `###` line is promoted only if `MILESTONE_RE` accepts it once promoted (so `### M1:` and `### Milestone 1:` both count)
- Lint fence view = `scan_fences(plan_text)` (NOT `has_unterminated_fence`, which comment-strips first — this plan's M4 Contract has a literal `"<!--"` in a fence)
- Label coverage: `[...]` family only (incl. `[(...)]`, `[[...]]`, `[/.../]`); `(new)` exemption is `\(new\)\W*$`; path claims must resolve inside repo_root; `_PATH_RE` runs only on whitespace tokens ≤256 chars; labels found by `str.find` (no `\[([^\]]*)\]` regex — quadratic)
- Mermaid fences located by the line-based `_mermaid_fences` (mirrors CommonMark closer rule; no lazy `.*?` regex)
- `%%` directive lines and a leading `---…---` block are skipped before the type word
- `render-is-leaf` `source_modules` must list every top-level `aa_ma` module except `render` — pinned by `tests/render/test_leaf_contract.py`; import-linter refuses `source_modules = aa_ma` ("shared descendants")
- `CODE_AUDIT_PROFILES ⊂ CANONICAL_AUDIT_PROFILES`; complement is exactly `{docs-only, custom}` (test)
- Hostile-input budget: 200 KB flood inputs lint in ≤0.04 s (`tests/render/test_hostile_input.py`, ceiling 2 s)
- Angle 6 check #6 command: `AA_MA_ROOT=$(cd "$(dirname "$(readlink -f ~/.claude/skills/plan-verification/SKILL.md)")/../../.." && pwd); uv run --project "$AA_MA_ROOT" aa-ma-lint-views <plan.md> --repo-root <root>` — verified from /tmp

### M3 facts (landed 2026-09-12)
- `/aa-ma-share` = `claude-code/commands/aa-ma-share.md` (command #12); allowlist `scripts/aa-ma-share-allow.sh` (rc 0/1; `*-plan.md|*docs/adr/*.md|*docs/spec/*.md`, any `..` segment refused); bats `tests/commands/aa-ma-share-allow.bats` (11)
- **CLAUDE.md is gitignored** (`.gitignore:2`) — local-only; never a shipped count site. Shipped count sites: `SECURITY.md:11-13` (counts + name lists, pinned by `test_security_md_asset_lists_match_disk`), README `### All commands` rows (pinned)
- CI (`security.yml`) now runs `uv run pytest tests/commands tests/render` (before M3 it ran only tests/codemem + test_goal_synthesis)
- ADR-0010 Status: **Implemented** (M4 optional, does not gate it)
- Exemplar artifact: https://claude.ai/code/artifact/454ea963-09c1-4870-90ce-7c11324c6eed — ADR-0010 renders 1 `flowchart-v2` svg (Example fences are inside a ````markdown block, so exactly 1)
- Artifact viewer loads mermaid **11.16.1** (observed in the saved frame) — a pin for M4's `MERMAID_VERSION` decision
- gstack `/browse` on BATS: private artifacts 404 when logged out (correct); handoff→resume drops the session on WSL — verify auth-gated pages via the user's saved iframe document (`_files/_t.html`). Playwright build 1208 satisfied by symlinks to 1234 in `~/.cache/ms-playwright`

### M4 facts (landed 2026-09-12)
- `src/aa_ma/render/html.py`: `MERMAID_VERSION = "11.17.2"` (latest 11.x on jsDelivr, re-measured at the 4.1 prototype); `render_markdown(text, *, title) -> str`; rules `_fence` (info == "mermaid" exact, as in mermaid_lint → `<pre class="mermaid">`), `_raw_html` (html_block/html_inline: `html.escape(_strip_comments(content))` — linear `str.find` scanner drops every `<!-- … -->` span, an unterminated `<!--` eats the rest of the block; never a lazy regex), `_md()` is `functools.cache`d and builds `MarkdownIt("commonmark", {"html": True}).enable(["table", "strikethrough"])`
- `render_main` in `src/aa_ma/render/cli.py`: `aa-ma-render <md>... [--out build/render]`; exit 2 (stderr) for no sources, duplicate `<stem>.html` targets, or any `OSError` on read/mkdir/write (all sources are read before anything is written — never a partial set, never a traceback); prints each written path; output name `<stem>.html`; utf-8 explicit
- Mermaid is loaded as the single-file UMD `dist/mermaid.min.js` with `integrity=MERMAID_SRI` (sha384 of that exact file; bump command in html.py) + `crossorigin="anonymous"`, behind a CSP meta (`script-src https://cdn.jsdelivr.net 'sha256-<hash of _INIT_JS>'`). Not the ESM entry: SRI on it would leave its lazily imported chunks unverified. A tampered hash makes the browser refuse the script (measured). Context7 evidence for markdown-it-py: provenance CONTEXT7 line, /executablebooks/markdown-it-py docs/using.md
- `markdown-it-py>=4,<5` is now an explicit dependency (`.venv` 4.0.0; uv.lock unchanged beyond the edge)
- Golden: `tests/golden/render_plan_ok.html` (1972 B after the SRI/CSP fix) — regenerate deliberately with the one-liner in plan Sub-step 4.3 when `_CSS` or the skeleton changes
- `/browse` recipe for rendered HTML: wait on `document.querySelectorAll('svg').length`, **not** `pre.mermaid[data-processed]` (set before paint — a screenshot at that instant showed an empty sequence diagram); dark mode needs playwright `emulateMedia({colorScheme:"dark"})` with `executablePath` = `~/.cache/ms-playwright/chromium_headless_shell-1234/…` (gstack's playwright wants build 1243, not installed)
- ADR-0010 has no markdown table → the `table >= 1` goal is evidenced by the spec render (6 tables); ADR render: 1 svg (Example fences sit inside a ````markdown block)
- Tests: `tests/render/test_html.py` (10), `tests/render/test_cli.py` (13 collected: 6 pre-M4 + 7; the chmod-0 case skips as root), `tests/render/test_hostile_input.py` (+1 comment-flood); `tests/render` total 67. Do not add a `[` flood shape to the hostile tests — measured ~1.8 s at 200 KB, ~90% of BUDGET_S (linear, just markdown-it-py's constant factor)

_Last Updated: 2026-09-12_
