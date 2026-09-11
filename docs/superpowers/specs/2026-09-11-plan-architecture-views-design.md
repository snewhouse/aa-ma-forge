# plan-architecture-views — Design Spec

**Date:** 2026-09-11
**Status:** Approved for planning (brainstorm sections 1–3 approved by Ste)
**Target release:** v0.11.0 (current `pyproject.toml` version 0.10.0)
**Sequencing:** execute AFTER `milestone-grammar-ssot` M5 lands (both touch `src/aa_ma/plan_parsers.py`)
**Vocabulary:** `CONTEXT.md` §"Plan artefact views" — Architecture View, View, Contract block, Render, Share, Diagram-Waiver

## 1. Problem

AA-MA plans and ADRs contain no diagrams (0 of 10 completed plans, 0 of 8 ADRs) and
no pinned interface contracts. `plan-verification`'s fresh-agent simulation keeps
failing plans for exactly the gap a contract closes ("signatures unpinned, 5.0 named
no file" — grammar-ssot M5 review). There is no way to hand a plan or ADR to someone
outside the repo. `docs/spec/aa-ma-specification.md:583` lists diagrams as optional
artefacts; nothing produces or checks them.

## 2. Decisions (from grill-with-docs, 8 questions / 10 branches)

| Decision | Choice | Rejected |
|---|---|---|
| Audience | fresh agents, Ste reviewing, external people | hand-editable diagrams |
| Enforcement | required with canonical waiver, grandfathered by `Created:` | always / soft-only |
| Notation | Mermaid, text-only | ASCII dual-source, C4/Structurizr, draw.io, D2 (no GitHub/VS Code/Artifact render) |
| Mandated views | Component (always), Flow (iff `Critical-Path:` present) | Data/State optional; Milestone graph derived, never hand-authored |
| Code blocks | pinned Contract blocks per code-touching milestone | illustrative snippets, implementation drafts |
| Location | `plan.md` §13 + one pointer line in `reference.md` | split across files; 9th AA-MA file |
| HTML | Python exporter (markdown-it-py + mermaid.js) + Artifact Share | Artifact-only, committed HTML, MkDocs |
| HTML scope | plan.md, ADRs, `docs/spec/*` | whole task bundle |
| Validation | pure-Python structural lint always; `mmdc` render optional, UNKNOWN when absent | Node mandatory; no render check |
| Backfill | none; ADR-0009 is the exemplar; spec gets one canonical flow diagram | backfill ADRs / everything |

Precedent (research, `scratchpad/research-standard-practice.md`): no major standard
mandates diagrams themselves — MADR 4.x is silent, arc42 mandates the Building Block
*view* and accepts a table, superpowers `writing-plans` is opt-in, Spec Kit mandates
Mermaid. This design is deliberately stricter than MADR/arc42 because the consumer is
a cold agent that needs dependency *edges*, which a table carries poorly.

## 3. Architecture

Two independent pipelines share one contract: the mermaid fences in `plan.md` §13.
`plan.md` is the only source; nothing writes back to it.

```mermaid
flowchart LR
  subgraph authoring [M1 Standard — prompt/doc surface]
    SPEC[docs/spec/aa-ma-specification.md §XI]
    TPL[docs/templates/plan-template.md\ndocs/adr/TEMPLATE.md]
    P4[claude-code/skills/aa-ma-plan-workflow/references/PHASE_4_PLAN_GENERATION.md]
    SCRIBE[claude-code/agents/aa-ma-scribe.md]
    PV[claude-code/skills/plan-verification/SKILL.md Angle 6]
    SPEC --> TPL --> P4 --> SCRIBE
    SPEC --> PV
  end
  subgraph lint [M2 Lint — Python]
    PP[src/aa_ma/plan_parsers.py]
    ML[src/aa_ma/render/mermaid_lint.py (new)]
    MMDC{{MMDC_BIN resolvable?}}
    ML --> MMDC -- yes --> OK[render PASS/FAIL]
    MMDC -- no --> UNK[render UNKNOWN]
  end
  subgraph render [M3 Render — Python]
    HTML[src/aa_ma/render/html.py (new)]
    CLI[aa-ma-render → build/render/*.html]
    HTML --> CLI
  end
  subgraph share [M4 Share — prompt]
    CMD[claude-code/commands/aa-ma-share.md (new)]
  end
  PLAN[(plan.md §13)] --> PV
  PLAN --> ML
  PLAN --> HTML
  CLI --> CMD
  PP -. after grammar-ssot M5 .-> ML
```

Boundaries:
- `src/aa_ma/render/` is a leaf package: imports `plan_parsers` and `grammar`; nothing
  in `src/aa_ma` imports it. Enforced with the existing `import-linter` config.
- `Diagram-Waiver:` is **plan-level** (front matter), because `Audit-Profile` is
  per-milestone: the View is required iff any milestone has
  `Audit-Profile ∈ {full, code-only, infra}`; otherwise a waiver is required.
- Grandfathering mirrors element #12: Angle 6 checks fire only for plans
  `Created:` on-or-after the v0.11.0 release date.

## 4. Contracts

### 4.1 Plan surface (element #13)

```markdown
**Created:** 2026-09-11
**Diagram-Waiver:** none        ← canonical: none | docs-only | config-only | single-file

## 13. Architecture View
### Component view                 ← REQUIRED unless waived
```mermaid
flowchart LR
  A[src/aa_ma/plan_parsers.py] --> B[src/aa_ma/render/mermaid_lint.py (new)]
```
### Flow view                      ← REQUIRED iff any milestone carries Critical-Path:
```mermaid
sequenceDiagram
  ...
```
### Data/State view                ← optional; only when a schema or state machine is introduced
```

- A node label containing a repo path (`[A-Za-z0-9_./-]+/[A-Za-z0-9_.-]+\.(md|py|sh|yaml|yml|toml|json|bats)`)
  is a **claim**: the lint checks the path exists unless the label ends with `(new)`.
- `reference.md` carries exactly one line: `Architecture View: see plan.md §13`.
- Milestone dependency graph is out of scope (derivable from `tasks.md`; future tooling).

### 4.2 Contract block

Every milestone with `Audit-Profile ∈ {full, code-only, infra}` carries, in `plan.md`:

```markdown
#### Contract
```python
# file: src/aa_ma/render/mermaid_lint.py
def lint_plan(plan_path: Path, repo_root: Path) -> LintReport: ...
# exit codes: 0 clean, 1 findings, 2 usage/error
```
```

Content: file paths, function/CLI signatures, exit codes, field grammar. Purpose is
cold-executability; illustrative examples are not Contract blocks.

### 4.3 ADR template

`docs/adr/TEMPLATE.md` gains two *recommended* sections: `## Architecture View`
(Component only) and `## Example` (one fenced block showing the decision in use).
Not machine-verified. ADR-0009 (this feature) is written with both and is the exemplar.

### 4.4 Diagram-Waiver parser (M2)

```python
# file: src/aa_ma/plan_parsers.py
DIAGRAM_WAIVER_VALUES: frozenset[str] = frozenset({"none", "docs-only", "config-only", "single-file"})
def parse_diagram_waiver(text: str) -> tuple[str | None, bool, str | None]
# same (value, is_valid, error) contract as parse_tdd_waiver; bold-pair form accepted,
# mid-line/backtick-wrapped rejected (L-011); novel value -> is_valid=False
```

### 4.5 Lint (M2)

```python
# file: src/aa_ma/render/mermaid_lint.py
@dataclass(frozen=True)
class Finding: code: str; line: int; message: str
    # codes: NO_SECTION, NO_COMPONENT_VIEW, NO_FLOW_VIEW, EMPTY_FENCE, UNKNOWN_TYPE,
    #        STALE_PATH, WAIVER_INVALID, WAIVER_NOT_ALLOWED
@dataclass(frozen=True)
class LintReport: findings: tuple[Finding, ...]; render_status: str  # PASS | FAIL | UNKNOWN
def lint_plan(plan_path: Path, repo_root: Path) -> LintReport
# CLI: aa-ma-lint-views <plan.md> [--repo-root .]   exit 0 clean / 1 findings / 2 usage
# env: MMDC_BIN (default "mmdc"). Unresolvable, rc>1, or empty output -> render_status=UNKNOWN.
```

Known mermaid types accepted on fence line 1: `flowchart`, `graph`, `sequenceDiagram`,
`classDiagram`, `stateDiagram-v2`, `erDiagram`, `C4Context`, `C4Container`, `C4Component`.

### 4.6 Render (M3)

```python
# file: src/aa_ma/render/html.py
def render_markdown(text: str, *, title: str, inline_svg: bool = False) -> str
# markdown-it-py "gfm-like" preset (tables ON); fence hook: ```mermaid -> <pre class="mermaid">;
# mermaid@11.x pinned ESM from cdn.jsdelivr.net; prefers-color-scheme init; print CSS;
# inline_svg=True shells to MMDC_BIN and embeds SVG (offline-viewable); no syntax highlighting (v1).
# CLI: aa-ma-render <md>... [--out build/render] [--inline-svg]   exit 0 / 2 usage
```

`build/` is added to `.gitignore`. `markdown-it-py>=4,<5` is promoted from transitive
(via `rich`) to an explicit dependency (L-055 pattern).

### 4.7 Share (M4)

`claude-code/commands/aa-ma-share.md`: `aa-ma-render` the target → publish with the
Artifact tool (mermaid renders natively there) → append
`[ts] SHARE — <doc> <url>` to the task's `provenance.log`. Failure writes no SHARE line.

## 5. Data flow

```mermaid
sequenceDiagram
  participant P as /aa-ma-plan Phase 4
  participant V as plan-verification Angle 6
  participant S as aa-ma-scribe
  participant L as aa-ma-lint-views
  participant R as aa-ma-render
  participant A as /aa-ma-share
  P->>P: author §13 + Contract blocks
  P->>V: plan text
  V-->>P: CRITICAL if #13 missing and no valid waiver (Created ≥ v0.11.0)
  P->>S: approved plan
  S->>S: write plan.md §13; reference.md pointer
  L->>L: fences → findings → mmdc? PASS/FAIL : UNKNOWN
  R->>R: markdown-it-py → self-contained HTML → build/render/
  A->>R: render
  A->>A: Artifact publish → provenance SHARE line
```

## 6. Error handling (fail-closed; L-011, L-012)

| Situation | Behaviour |
|---|---|
| `Diagram-Waiver:` novel, backtick-wrapped or mid-line | `is_valid=False` + error → Angle 6 CRITICAL |
| Waiver present but a milestone has code `Audit-Profile` | `WAIVER_NOT_ALLOWED` |
| §13 present, fence empty or unknown type | finding, exit 1 |
| Path claim absent on disk and not `(new)` | `STALE_PATH`, exit 1 |
| `MMDC_BIN` unresolvable / rc>1 / empty output | `render_status=UNKNOWN` in the report — never PASS |
| Render input has no `## 13.` (ADR, spec) | renders normally; §13 is a plan-only rule |
| Artifact publish fails | command reports failure; no SHARE line |

## 7. Milestones

| M | Title | Audit-Profile | Ships alone? |
|---|---|---|---|
| 1 | Standard: spec §XI #13, templates, PHASE_4, scribe, Angle 6, engineering-standards table, ADR-0009, spec flow diagram, counts | docs-only | yes |
| 2 | Lint: `parse_diagram_waiver`, `mermaid_lint.py`, `aa-ma-lint-views` CLI, tests | code-only | yes |
| 3 | Render: `html.py`, `aa-ma-render` CLI, dep promotion, `.gitignore`, golden tests | code-only | yes |
| 4 | Share: `/aa-ma-share` command, frontmatter test, `/browse` check, command count | docs-only | yes |

Critical-Path: M1 `doc-count-drift` (commands 11→12 after M4; plan elements 12→13);
M2 `data-xform` (parser contract). Prototype-Required: M3 YES (fence hook + mermaid
ESM + theme init verified in a browser before the golden is frozen).

## 8. Testing

- M1: bats asserts Angle 6 text names #13 and `Diagram-Waiver`; cross-reference grep
  finds no dangling names; doc-drift Tier 6 counts updated.
- M2: pytest table-driven forms for `parse_diagram_waiver` (reuse the 18-form table
  from grammar-ssot reference.md); lint fixtures: valid / empty fence / unknown type /
  stale path / `(new)` path / waiver-not-allowed; `MMDC_BIN=/bin/false`, `=true`,
  `=/nonexistent` all → UNKNOWN (mutation-guarded).
- M3: golden HTML in `tests/golden/`; asserts `<pre class="mermaid">`, `<table>`,
  pinned CDN URL, no external stylesheet; `--inline-svg` reports UNKNOWN/skip when
  mmdc absent.
- M4: frontmatter test; `/browse` on the published Artifact — diagram renders, no
  console errors.
- TDD sequence enforced by `tdd-sequence-auditor` on M2/M3.

## 9. Rollback

Each milestone is one revertable commit group. M1/M4 revert = docs/prompt only.
M2/M3 revert = delete `src/aa_ma/render/`, the two `[project.scripts]` entries and
the dep promotion. `build/` is ignored — nothing to clean.

## 10. Risks

1. `mmdc` needs Puppeteer + Chromium; WSL2 may need extra libs. Mitigation: optional
   with UNKNOWN; CI uses `npx -y` in a separate non-blocking job.
2. gstack `plan-eng-review` prefers ASCII diagrams. Mitigation: Phase 4.2 output is
   illustrative; the canonical View is mermaid in §13 — stated in PHASE_4 reference.
3. Diagrams rot. Mitigation: `STALE_PATH` lint + "diagram maintenance is part of the
   change" rule added to the execution checklist.
4. Mermaid version churn (ELK bundling, gitGraph breaks). Mitigation: pin `mermaid@11.x`
   exact in `html.py`; a single constant.

## 11. Out of scope

Milestone dependency graph generation; backfilling ADRs 0001–0008 or completed plans;
syntax highlighting; MkDocs/site; hand-editable diagram formats; TUI HTML export.
