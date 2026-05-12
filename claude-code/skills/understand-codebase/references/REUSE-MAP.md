# REUSE-MAP — compose the known-working tools, don't reinvent them

`understand-codebase` is a **conductor**. The structural analysis it needs is already implemented
by mature tools in this `~/.claude/` install. The rules below are mandatory:

1. **Detect prior output first.** If a tool's output already exists and is fresh, *absorb* it —
   do not re-run the tool.
2. **Only run a heavy tool when its output is absent or stale.** "Stale" = the artifact's
   timestamp predates the repo's last commit (`git log -1 --format=%cd`), or the artifact's own
   date stamp is > ~30 days old, or the user asked for a fresh run.
3. **Record what was absorbed vs freshly run** in the Provenance block.
4. **Degrade gracefully.** If a tool/agent is unavailable, skip that input and note it — never hard-fail.

---

## A. Detect & absorb prior outputs (Step 0, every tier)

| Artifact (relative to target repo root) | Produced by | If present, absorb as | Freshness check |
|---|---|---|---|
| `PROJECT_INDEX.json` | `/index` (`~/.claude-code-project-index/scripts/project_index.py`) | Directory purposes (`dir_purposes`), ASCII tree, file summaries, `symbol_importance`, call graph, import deps. **Read this first** for dimensions 1, 3, 4. | mtime vs last commit; the file has its own metadata. |
| `.planning/codebase/STACK.md` | `gsd-map-codebase` (tech) | Dimension 2 (tech stack) + 12-integrations partial. Authoritative. | date header in the file vs last commit. |
| `.planning/codebase/INTEGRATIONS.md` | `gsd-map-codebase` (tech) | Dimension 12 integrations. | " |
| `.planning/codebase/ARCHITECTURE.md` | `gsd-map-codebase` (arch) | Dimension 3 (architecture, data flow). | " |
| `.planning/codebase/STRUCTURE.md` | `gsd-map-codebase` (arch) | Dimension 4 (directory map, where-to-add). | " |
| `.planning/codebase/CONVENTIONS.md` | `gsd-map-codebase` (quality) | Dimension 9 (conventions) — but still spot-check 3-5 files to confirm. | " |
| `.planning/codebase/TESTING.md` | `gsd-map-codebase` (quality) | Dimension 6 (tests). | " |
| `.planning/codebase/CONCERNS.md` | `gsd-map-codebase` (concerns) | Dimension 13 (tech debt) partial. | " |
| `.planning/intel/stack.json` `files.json` `apis.json` `deps.json` `arch.md` | `gsd-intel` | Fast structured lookups (file exports, API surface, dependency chains, stack summary). Each has `_meta.updated_at`. | `_meta.updated_at`. |
| `.claude/reports/codebase-deep-dive-*/00-executive-summary.md` (+ `01`…`08` + `diagrams/*.mmd`) | `/codebase-deep-dive` | Dimensions 3 (arch + diagrams), 6 (test coverage), 9 (quality grade), 12-security, 13 (recommendations). **Link the diagrams; quote the grade.** | timestamp in the dir name. |
| `ONBOARDING.md` (root) | a *prior run of this skill* | Compare; this run updates it in place + refreshes Provenance. Don't duplicate. | Provenance block date. |
| `.claude/onboarding/*` | a *prior run of this skill* | Same — update in place. | " |
| `README.md`, `CONTRIBUTING.md`, `ARCHITECTURE.md`, `docs/`, `docs/adr/` | the project itself | Quote them; cross-check vs code; **note drift as a "con"** (use `Skill(doc-drift-detection)` heuristics). | n/a — always read & verify. |

**Step-0 pseudo-procedure:**
```
1. ls PROJECT_INDEX.json .planning/codebase/ .planning/intel/ .claude/reports/codebase-deep-dive-* ONBOARDING.md .claude/onboarding/ 2>/dev/null
2. For each found: check freshness. Fresh → read & absorb. Stale → note "stale, refreshing" and queue a re-run (only if tier permits).
3. If PROJECT_INDEX.json missing and tier >= Standard and repo not huge → run /index.
4. Record absorbed-vs-stale in a scratchpad for the Provenance block.
```

---

## B. Tool invocation recipes (when you DO need to run them)

### `/index` — structural index
- **When:** no `PROJECT_INDEX.json`, tier ≥ Standard, repo not pathologically huge.
- **How:** invoke `Skill(index)` or run `~/.claude-code-project-index/scripts/project_index.py`
  from the repo root (it auto-discovers; supports Python AST, JS/TS, Shell regex, Go/Rust/Java/Ruby via ast-grep).
- **Output:** `PROJECT_INDEX.json` at repo root. Read it immediately after.
- **Fallback:** if the script isn't installed → skip; agents discover structure with `find`/`sg`/`Grep`. Note in Provenance.

### `gsd-codebase-mapper` agent ×4 — structural docs (Deep tier)
- **When:** Deep tier and no fresh `.planning/codebase/`.
- **How:** `Agent(subagent_type="gsd-codebase-mapper", prompt=…)` four times, one per focus
  (`tech`, `arch`, `quality`, `concerns`) — run in parallel (single message, 4 calls), or via
  `Skill(gsd-map-codebase)` which orchestrates them. Each writes its docs directly to
  `.planning/codebase/`; you receive confirmations only (keeps your context lean).
  - In the prompt, include a `<required_reading>` block pointing at `PROJECT_INDEX.json` if it exists.
- **Output:** `STACK.md INTEGRATIONS.md ARCHITECTURE.md STRUCTURE.md CONVENTIONS.md TESTING.md CONCERNS.md` in `.planning/codebase/`.
- **Standard tier:** do NOT run all 4 — the 4 Explore agents (S1–S4) cover the same ground at lower cost.
- **Lightweight alternative:** `Skill(gsd-scan)` runs 1 mapper agent with `--focus tech+arch` (default).
- **Fallback:** unavailable → Deep degrades to enhanced-Standard. Note.

### `/codebase-deep-dive` — quality/security/flow + diagrams (Deep tier)
- **When:** Deep tier and no fresh `.claude/reports/codebase-deep-dive-*/`.
- **How:** invoke `Skill(codebase-deep-dive)` / the `/codebase-deep-dive` command pointed at the
  target path; let it run its 6-phase parallel-agent workflow. It uses Context7 + `sg` already.
- **Output:** `.claude/reports/codebase-deep-dive-<timestamp>/00-..08-.md` + `diagrams/*.mmd` + a health grade.
- **In onboarding:** link `01-architecture-overview.md`, `04-code-quality-assessment.md`,
  `05-security-analysis.md`, `06-design-patterns.md`, `08-recommendations.md`; embed/link the diagrams;
  fold the health grade into the pros/cons verdict.
- **Fallback:** unavailable → workers do a lighter quality/security pass directly. Note.

### `Skill(system-mapping)` — 5-point pre-flight
- **When:** any tier — borrow its 5-point checklist (architecture / execution flows / logging /
  dependencies / environment) as the *structure* of the S1 Explore agent's analysis. You're not
  doing a pre-edit check; you're reusing the checklist shape.

### `Skill(code-intelligence)` / `Skill(code-intelligence-index)` — structural queries
- **When:** S1 (Standard) and the mapper/`/codebase-deep-dive` agents (Deep) — use its `sg`
  pattern library for entry points, class/struct/interface defs, route decorators, async functions,
  DB-query and HTTP-client calls; use its output-formatting templates (caller lists, dependency
  maps, class hierarchies) for consistency. If `PROJECT_INDEX.json` exists, prefer
  `code-intelligence-index` (MCP: `who_calls`, `blast_radius`, `dependency_chain`, `search_symbols`,
  `file_summary`, `dead_code`).

### `Skill(impact-analysis)` — for the "Contribute safely" playbook
- **When:** writing dimension 15 — the playbook's "before you touch shared/core code, run the
  5-point impact check" step references this skill. Don't run it during onboarding; cite it as the ritual.

### `Skill(doc-drift-detection)` — for dimension 13
- **When:** dimension 13 (repo health) — borrow its Tier 1–7 heuristics (stale version strings,
  CHANGELOG completeness, README/CLAUDE.md accuracy, ADR index, hardcoded-count drift, env-var
  drift) to *detect* drift; report findings as "cons" / "watch-outs". Don't run its auto-fix.

### WebSearch + Context7 MCP — version-currency / CVE / best-practice enrichment (Deep tier)
- **When:** Deep tier, dimension 2 currency pass + dimension 12 vuln signal.
- **How:**
  - Context7: `resolve-library-id` for each major framework/library → `query-docs` / `get-library-docs`
    with a focused query: "latest stable version", "is `<pinned-version>` EOL", "breaking changes since `<pinned>`".
  - WebSearch: `"<framework> <version> end of life"`, `"<lib> known CVEs <year>"`, `"<stack> project structure best practices <year>"`.
- **Output:** a "Version currency" subsection in `.claude/onboarding/01-stack.md`: per major dep,
  pinned vs current vs EOL, with the source link & date.
- **Fallback:** unavailable → skip; note "version-currency check skipped — Context7/WebSearch unavailable" in Provenance.

### `Skill(agent-teams)` + `TeamCreate`/`SendMessage`/`TaskCreate` — Deep-tier orchestration
- **When:** Deep tier only. Use the team template `templates/onboarding-team.md`.
- **Fallback:** `TeamCreate` unavailable or team spawn fails → Deep degrades to enhanced-Standard
  (still invoke the heavy tools + workers, just without the formal team/task-list machinery). Note.

### `code-reviewer` agent (or `comprehensive-review:code-reviewer`) — Deep-tier QA
- **When:** Deep tier, final review pass over `ONBOARDING.md` + `.claude/onboarding/`.
- **Brief:** "verify every factual claim against the codebase; flag any boilerplate not grounded
  in THIS repo; run the secret-leak grep gate; check the acceptance criteria in SKILL.md." Apply
  its corrections before declaring done.

---

## C. What this skill writes (the only things it writes)

- `<repo>/ONBOARDING.md` — always.
- `<repo>/.claude/onboarding/**` — Standard & Deep.
- via reused tools: `<repo>/PROJECT_INDEX.json` (`/index`), `<repo>/.planning/codebase/**` (`gsd-map-codebase`, Deep), `<repo>/.claude/reports/codebase-deep-dive-*/**` (`/codebase-deep-dive`, Deep).
- It never edits the target repo's source code.
- Team artifacts (Deep): `~/.claude/teams/understand-codebase-<slug>/` and `~/.claude/tasks/understand-codebase-<slug>/` — cleaned up at team shutdown.
