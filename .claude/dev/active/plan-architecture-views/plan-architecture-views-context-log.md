# plan-architecture-views Context Log

## [2026-09-11] Initial Context

**Feature Request:** "Add System Architecture Diagrams and code blocks to the plans and ADRs produced by the AA-MA workflows; include HTML versions of key plans, docs, diagrams for easy review, sharing, editing; research what has been done and standard practice; break nothing."

**Grill (grill-with-docs, 8 questions / 10 branches) — decisions:**
- Audience: fresh agents, Ste reviewing, external people. NOT hand-editable after generation → markdown is the only source; HTML is derived and disposable.
- Enforcement: required with canonical waiver (`Diagram-Waiver: none|docs-only|config-only|single-file`), grandfathered by `Created:`.
- Notation: mermaid, text-only. Rejected: ASCII dual-source, C4/Structurizr/PlantUML (JVM), draw.io/Excalidraw (opaque blobs), D2 (no GitHub/VS Code/Artifact render).
- Views: Component (always) + Flow (iff `Critical-Path:`) mandated; Data/State optional; Milestone graph derived, never hand-authored (TODOS.md).
- Code blocks = pinned Contract blocks per code milestone (targets the fresh-agent "signatures unpinned" failure class).
- Location: plan.md §13 + one pointer line in reference.md.
- HTML: Python exporter (markdown-it-py, already transitive via rich) + Artifact Share. Scope: plan.md, ADRs, docs/spec.
- Validation: pure-Python structural lint always; `mmdc` optional, UNKNOWN when absent (L-012). "Let's add mmdc" — installed as dev tooling, never a CI blocker.
- Sequencing: after milestone-grammar-ssot M5. Backfill: none; ADR is the exemplar.
- Task name: plan-architecture-views. CONTEXT.md gained: Architecture View, View, Contract block, Render, Share, Diagram-Waiver.

**Brainstorm:** 3 approaches (A standard→lint→render→share; B docs-only; C TUI-centric). User chose A (after a mis-click on B, corrected: "I meant A!").

**Research (2 agents):** footprint — zero diagrams in 10 completed plans / 8 ADRs, spec line 583 lists diagrams as optional, no HTML path. Standard practice — MADR 4.x silent on diagrams; arc42 mandates the *view* with a table accepted; superpowers writing-plans opt-in; Spec Kit mandates mermaid; MermaidSeqBench (NeurIPS 2025, arXiv:2511.14967) shows LLM mermaid syntax errors are real and semantically-wrong-but-valid diagrams exist. mmdc needs Puppeteer+Chromium; `mermaid.parse()` needs jsdom; no maintained pure-Python validator. markdown-it-py fence hook is the documented mechanism; GFM tables are not on by default. Notes: `scratchpad/research-standard-practice.md` (session-local).

**Spec:** `docs/superpowers/specs/2026-09-11-plan-architecture-views-design.md` (commit 21b338f). Superseded in part by plan rev 2–4 (see below).

**Engineering Standards Declaration:** all six themes (rationale in plan §12).

## [2026-09-11] Plan review — plan-eng-review (12 decisions) + outside voice

- D1 dropped `--inline-svg` (second mmdc path, unrequested offline mode).
- D2 global commands/skills resolve the checkout via `readlink -f` on their own installed symlink → `uv run --project`.
- D3 no raw-HTML passthrough in the renderer.
- D4 `.importlinter` `root_packages` must include `aa_ma`, contract mutation-checked.
- D5 lint reuses `grammar.split_milestones` + `parse_audit_profile`/`parse_critical_path` — no private field grammar (L-011 class).
- D6 `is_file` guards; `--tasks` override.
- D7 all test gaps closed; `render_check` timeout injectable.
- D8 outside voice run (fresh Claude subagent; Codex not installed): 12 findings, several measured on BATS.
- D9 **`/aa-ma-share` publishes markdown** — the Artifact tool wraps files in its own skeleton and renders mermaid natively; HTML-in would nest documents and double-init mermaid. M3 now depends on M1 only.
- D10 Render kept but moved last and optional (M4); droppable via documented scope reduction.
- D11 `Diagram-Waiver` owned by `plan_parsers` (planning-time); the gate (`enforce.py`, grammar-ssot M5) never reads it — follows the pinned "two mechanisms, two concerns" contract in grammar-ssot reference.md. Sequencing premise corrected: M5 does not edit `plan_parsers.py`; the dependency is the `split_milestones` fix.
- D12 eight measured corrections: mmdc exits 1 for every error (missing Chromium included) → rc≠0 is UNKNOWN unless a parse signature; literal cutover date 2026-09-11 (tag does not exist yet; "release date" would have grandfathered this very plan); import contract vacuous without `aa_ma` root + mutation step; `.venv` markdown-it-py is 4.0.0 (conda env 4.2.0 was inspected earlier); mermaid pin = latest 11.x at prototype; comment stripping fence-aware via `html_block`/`html_inline` render rules; `(new)` exemption per label; tests never reach a real `mmdc` (autouse fixture).
- `/bin/false` is not a degraded-mode sentinel for mmdc: rc 1 with a parse signature is a legitimate FAIL; rc 1 without one is UNKNOWN.
- TODOS.md created: milestone-graph generation; aa-ma-tui distribution.

## [2026-09-11] Verification (automated, 3 passes) — PASS WITH WARNINGS

Pass 1: 6 CRITICAL — ADR-0009 collision (→ 0010); `[x (new)]` unquoted label is a mermaid parse error (→ quoted form everywhere + quote-stripping lint); `test_contracts_kept` asserts "2 kept" (→ 3); element-count drift sites beyond the 1.5 grep (→ 29 sites pinned in reference.md, gate scoped to live surface); missing `import pytest`; lint blind to `### Milestone` in plan.md (→ H3→H2 promotion, fixtures use the real template form).
Pass 2: the plan's own Flow view failed to parse (`;` in a sequence message — caught by rendering §13 in headless Chromium); widened grep hit frozen docs; allowlist `case` rejected relative paths (→ `scripts/aa-ma-share-allow.sh` + bats, 10 cases).
Pass 3: 3/3 resolved, 0 new. Residual accepted warnings: first Artifact-publishing command in repo; golden calibration is a one-time human step; `render: UNKNOWN` on BATS until Chromium exists.

**Assumptions declared (Theme 4):** listed in plan §8; all VERIFIED by Angle 2 except the Artifact-precedent one.

**Remaining Questions:** none blocking. Open choice at M4 gate: build Render or drop it via scope reduction.

_This log will be updated via context compaction as the task progresses._

## [2026-09-12] Decision: target release is v0.12.0, not v0.11.0

v0.11.0 was tagged at `758f125` (2026-09-12 06:21) by milestone-grammar-ssot before M1 started, and does not contain element #13. All new prose from this plan labels the feature `v0.12.0+`; the grandfathering cutover stays the literal date **2026-09-11** (plans `Created:` on-or-after it are checked — this plan included; grammar-ssot, Created 2026-08, is not). `CHANGELOG.md` `## Unreleased` must be re-created in 1.8 (cz bump consumed it).

## [2026-09-12] Decision: `custom` is not a code Audit-Profile for element #13

§6.8 future-proofing audit flagged that "Audit-Profile ∈ {full, code-only, infra}" is inlined at 8 prose sites while the enum also has `custom`. Decision: `CODE_AUDIT_PROFILES` (plan §M2 Contract, `plan_parsers.py`) stays `{full, code-only, infra}`; a `custom` milestone that dispatches code-reviewer via `Audit-Run:` is expected to declare its View/Contract voluntarily, and `custom` + `Diagram-Waiver` is not a lint error. Revisit via ADR if a `custom` code milestone ships without a View. Pinning the set against prose is deferred to Sub-step 2.7 (named there).

## [2026-09-12] GATE APPROVAL: Milestone 1: Standard — element #13, Contract blocks, verification, exemplar ADR
- Gate: HARD
- Approved by: Ste (Stephen J Newhouse)
- Criteria verified: 5/5
- Decision: APPROVED

## [2026-09-12] Milestone Completion: Milestone 1 — Standard
- Status: COMPLETE
- Key outcome: Planning standard gained element #13 (Architecture View + Contract blocks, `Diagram-Waiver` canonical values, literal cutover 2026-09-11) across spec, rules, templates, Phase 4/scribe/validator prompts and plan-verification Angle 6 (#6/#7); ADR-0010 is the exemplar; all 29 live element-count sites read 13 and are now pinned by a test.
- Artifacts: docs/spec/aa-ma-specification.md (§XI item 13, §II diagram); claude-code/rules/{aa-ma,engineering-standards}.md; docs/templates/plan-template.md; docs/adr/{TEMPLATE,INDEX,0010-architecture-views-and-render}.md; plan-verification SKILL.md; 12 workflow/agent/command prose files; README/CLAUDE/foundations counts; CHANGELOG Unreleased; tests/commands/test_plan_verification_angle6.py, test_planning_standard_count.py; impl-review.md.
- Tests: pytest 978 passed / 2 skipped; bats tests/hooks 165 ok; 7/7 mermaid fences render; mutation checks on both new tests.
- Reviews: Tier 2 validator WARN (5 → all fixed); §6.8 PASS_WITH_WARNINGS (0 CRITICAL; W1 fixed by test, W2 + 2 INFO deferred by name to Sub-step 2.7).

## [2026-09-12] Decision: ADRs are in the lint's remit (Component view only)

Running `aa-ma-lint-views` on ADR-0010 (its own exemplar) reported NO_COMPONENT_VIEW: the ADR template had `## Architecture View` with a bare mermaid fence and no `### Component view` subheading. Rather than special-case ADRs in the lint, the template and ADR-0010 gained the subheading (one line each, outside the M2 `Files:` list — recorded here per L-007). Consequence: `/aa-ma-share` (M3) can pre-lint an ADR with the same tool; the `(recommended)` suffix on the template heading is deliberately not matched (a template is not a document). No Flow view is ever required of an ADR (no milestones → no Critical-Path).

## [2026-09-12] Decision: the lint's fence view is `scan_fences(plan_text)`, not `has_unterminated_fence`

`grammar.has_unterminated_fence` strips HTML comments before scanning — correct for the gate, whose `sanitize` does the same. The lint never strips comments (a `<!-- -->` in §13 is content), and this plan's M4 Contract contains a literal `"<!--"` inside a Python fence that pairs with a `-->` 22 lines later under comment-stripping, eating a fence closer → false UNTERMINATED_FENCE. One `scan_fences` call now answers both "unterminated?" and "stripped?" so the lint cannot disagree with itself. The gate's behaviour is unchanged and out of scope.

## [2026-09-12] GATE APPROVAL: Milestone 2: Lint — Diagram-Waiver parser, mermaid structural lint, aa-ma-lint-views
- Gate: HARD
- Approved by: Ste (Stephen J Newhouse)
- Criteria verified: 4/4
- Decision: APPROVED

## [2026-09-12] Milestone Completion: Milestone 2 — Lint
- Status: COMPLETE
- Key outcome: `parse_diagram_waiver` (canonical enum via `_parse_canonical_field`), `src/aa_ma/render/` leaf package (structural lint reusing grammar + plan_parsers; fence-aware; mmdc seam UNKNOWN-unless-parse-error), `aa-ma-lint-views` CLI (0/1/2), `render-is-leaf` import contract (mutation-checked, pinned to the module set), Angle 6 check #6 runs the lint. Two lint bugs found by running it on this plan (quoted §13 in a fence; comment-stripped fence view) and fixed TDD. §6.8 found 4 CRITICAL / 8 WARNING — all fixed with tests before approval.
- Artifacts: src/aa_ma/plan_parsers.py (+), src/aa_ma/grammar.py (+H2_RE alias), src/aa_ma/render/{__init__,mermaid_lint,cli}.py, .importlinter, pyproject.toml, tests/render/** (23 fixtures, 49 tests), tests/codemem/test_diagram_waiver_parser.py (15), tests/commands/test_plan_verification_angle6.py (6), plan-verification SKILL.md, docs/adr/{TEMPLATE,0010}.md, impl-review.md.
- Tests: pytest 1046 passed / 2 skipped; bats 165 ok; lint-imports 3 kept; bandit 0; ruff clean.
- Deferred M1 items (2.7 a/b/c): all closed.

## [2026-09-12] Decision: CLAUDE.md is local-only; count pins live in SECURITY.md/README

`CLAUDE.md` is gitignored (`.gitignore:2`) and untracked — a fresh clone has none. The plan's "CLAUDE.md:48" count site is therefore a local convenience, not a shipped artefact; tests skip it when absent and pin the shipped surfaces (SECURITY.md counts + name lists, README command rows) to the files on disk. Found by M3 §6.8; the same audit found CI ran neither tests/commands nor tests/render — both added to `security.yml`.

## [2026-09-12] GATE APPROVAL: Milestone 3: Share — /aa-ma-share publishes markdown as a private Artifact
- Gate: HARD
- Approved by: Ste (Stephen J Newhouse)
- Criteria verified: 7/7
- Decision: APPROVED

## [2026-09-12] Milestone Completion: Milestone 3 — Share
- Status: COMPLETE
- Key outcome: `/aa-ma-share` (command #12) publishes a plan/ADR/spec markdown as a private Artifact; the allowlist is a tested script (11 bats, `..` refused); live publish of ADR-0010 from another repo renders the Component view (1 flowchart-v2 svg, 0 errors). ADR-0010 Implemented. §6.8 surfaced two repo-level gaps fixed here: CLAUDE.md is gitignored (pins skip it), and CI never ran tests/commands or tests/render (now does).
- Artifacts: claude-code/commands/aa-ma-share.md, scripts/aa-ma-share-allow.sh, tests/commands/aa-ma-share-allow.bats, tests/commands/test_aa_ma_share_command.py, SECURITY.md/README.md/CHANGELOG.md (+CLAUDE.md local), docs/adr/{0010,INDEX}.md, .github/workflows/security.yml, impl-review.md.
- Tests: pytest 1050 passed; bats hooks 165 + share 11 ok; shellcheck clean.
- Artifact: https://claude.ai/code/artifact/454ea963-09c1-4870-90ce-7c11324c6eed (private)

## [2026-09-12T12:31:38Z] Compaction Summary (auto-generated by hook)
- Active step at compaction: Sub-step 4.1: Prototype (UI branch) — fence hook + html rules + mermaid ESM + theme
- Snapshot saved to: /home/sjnewhouse/.claude/hooks/cache/compaction-snapshots/plan-architecture-views-snapshot.md
- Note: Context compacted. Reload AA-MA files to resume.

## [2026-09-12] Decision: build M4 (Render) — not dropped
- Context: M3 checkpoint left "build or drop" open. `/execute-aa-ma-milestone … -> M4` invoked; at the 4.1 HITL gate the user chose **Proceed — build**.
- Rationale: `/aa-ma-share` covers "read it as a link"; Render covers "attach a file" (offline reviewers, PDF via print). Cost was bounded (Contract pinned the whole surface; ~3.5 h). Prototype (4.1) returned GO with measured evidence before any production code.
- Mermaid pin: `MERMAID_VERSION = "11.17.2"` — latest 11.x on jsDelivr, re-measured 2026-09-12. The Artifact viewer's 11.16.1 is noted but irrelevant to a self-contained file; the plan rule "latest 11.x at prototype time, never keep an older pin" wins.
- Tier 2 (pre-execution, WARN 3/0): plan.md:1065 `/release-prep v0.11.0` → v0.12.0 (scope-change-class edit to plan.md, Last Updated bumped); tasks.md Summary Counts 23 → 24 sub-steps (2.8 added at M2); M4 test/golden paths pinned in reference.md. All fixed in the M4 sync commit.

## [2026-09-12] Decision: mermaid via SRI-pinned UMD bundle + CSP, not the ESM import (Contract deviation)
- Trigger: §6.8 security-auditor WARNING (A08) — the plan Contract's `import mermaid from ".../mermaid.esm.min.mjs"` had no integrity check, and SRI on the ESM entry cannot cover the ~10 chunks it lazily imports.
- Decision: `<script src=".../dist/mermaid.min.js" integrity="sha384-…" crossorigin="anonymous">` (one file → the hash covers every byte that runs) + `<meta http-equiv="Content-Security-Policy">` with the inline init script hashed. `MERMAID_SRI` lives beside `MERMAID_VERSION`; both bump together (command in the comment).
- Evidence: 1 CDN request (3.5 MB) instead of 11; 2 svg / 1 table / 0 console errors under CSP; tampered hash → refused. Trade-off accepted: the UMD bundle is ~3.5 MB vs ~600 KB of ESM chunks — one-off download per open, cached by the browser; correctness of the attestation wins for a file whose purpose is sharing.
- Not done (YAGNI): inlining the bundle for offline/no-beacon use (~3.5 MB per HTML file). Add if a reviewer ever needs a fully offline file.

## [2026-09-12] GATE APPROVAL: Milestone 4: Render (optional, last) — markdown to self-contained HTML, aa-ma-render
- Gate: HARD
- Approved by: Stephen Newhouse (user)
- Criteria verified: 7/7
- Decision: APPROVED

## [2026-09-12] Milestone Completion: Milestone 4: Render (optional, last) — markdown to self-contained HTML, aa-ma-render
- Status: COMPLETE
- Key outcome: `aa-ma-render <md>... [--out build/render]` writes one self-contained HTML file per source — markdown-it-py commonmark + tables, mermaid fences drawn by an SRI-pinned mermaid 11.17.2 UMD bundle behind a CSP meta, light/dark via prefers-color-scheme, raw HTML escaped, comments outside fences dropped, no partial output on any OSError. Prototype (4.1) GO before any production code; §6.6 + §6.8 found 3 CRITICAL / 8 WARNING across 8 agents — every one fixed with a test before this gate.
- Artifacts: src/aa_ma/render/html.py (new), src/aa_ma/render/cli.py (render_main), pyproject.toml (markdown-it-py>=4,<5 explicit; aa-ma-render script), uv.lock, tests/render/{test_html,test_cli,test_hostile_input}.py, tests/golden/render_plan_ok.html, README.md (Sharing and rendering plans), CHANGELOG.md, docs/adr/0010 (M4 shipped), impl-review.md M4 section; CLAUDE.md local.
- Tests: pytest 1068 passed / 2 skipped; tests/render 67; lint-imports 3 kept; bats 176 ok; shellcheck/ruff clean; bandit 0 in render/.
- /browse: ADR-0010 render svg=1, spec render svg=1 table=6, golden svg=2 — console errors 0 everywhere; tampered SRI hash refused.
