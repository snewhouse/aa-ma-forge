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
