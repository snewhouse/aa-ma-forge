# Charting: codebase-analysis-skills

## Destination

A plan-ready spec — every design decision settled — for shipping and maintaining two codebase-analysis
capabilities in aa-ma-forge: a clean-room **whole-repo assessment** skill (successor to the local
`/codebase-deep-dive`) and an improved **`understand-codebase`** onboarding skill. Handoff: `/aa-ma-plan --from-map codebase-analysis-skills`.

## Notes

- **Source report:** `.claude/dev/report-2026-09-27-codebase-deep-dive-vs-understand-codebase.md` (untracked, v2) —
  facts F1–F12, residuals R1–R6 + N1. Chart session added **R7**: `claude-code/commands/understand-codebase.md:31`
  still says `--deep` "runs … `/codebase-deep-dive`, `/index`" (not caught by `ROUTES_TO_UNSHIPPED`).
- **Settled at chart time (Ste, 2026-09-27):**
  - Destination = plan-ready spec; charting builds nothing.
  - Relationship between the two was left undecided at chart time → resolved in Ticket 5.
  - Ticket 12 (codemem bare-`sg`): in the Ticket 5 session Ste chose to fix it now as a separate bugfix — background
    agent, isolated worktree, branch `fix/codemem-ast-grep-binary`, TDD, PR, no merge. Ticket 12 stays OPEN until a
    `work … 12` session records the outcome (one grilling ticket per session). **Outcome (2026-09-27):** PR
    https://github.com/snewhouse/aa-ma-forge/pull/3 — `de37d6d` RED + `6861c50` fix; resolves `ast-grep` first, `sg`
    only if `--version` says ast-grep, else logs a warning; pytest 1658→1667 passed (5 skipped), ruff clean, bats
    231/231; all 7 CI checks green, MERGEABLE, **not merged**; worktree `.claude/worktrees/agent-a07f8ae0149b93c3a`.
    **Review (2026-09-27, `/code-review high` on `main...fix/codemem-ast-grep-binary`):** 7 findings — (1) HIGH
    "not parsed" indistinguishable from "zero symbols" → refresh deletes existing symbols (mechanism verified:
    `ast_grep.py:437-460` + `incremental.py:337-392`; pre-existing on main, not fixed by the PR); (2) PATH `ast-grep`
    beats the pinned interpreter-adjacent one; (3) E2BIG logged as missing binary; (4) `_invoker` seam selects bare
    `sg` (`ast_grep.py:438`, verified); (5) resolver uncached; (6) tests use `shutil.which` not the resolver;
    (7) `sg` fallback probes only the first PATH hit. **Ste: fix all 7 on the branch before merge** — dispatched to the
    same worktree agent.
    **Follow-ups done (2026-09-27):** `87fb2f2` RED + `f3f1550` fix — all 7 fixed, none disputed; pytest 1667→1676,
    ruff clean, bats 231/231; PR head `f3f1550`, 7/7 CI green, MERGEABLE, not merged (re-checked). Refresh trigger is
    `claude-code/codemem/hooks/post-commit.sh`, but `codemem refresh` is still a log-only placeholder, so finding 1 was
    latent.
    **Merged (2026-09-27T14:12Z):** PR #3 merged by Ste's instruction as merge commit `80caae7` (merge commit, per the
    PR #2 precedent; keeps the RED→GREEN history). Local `main` fast-forwarded; `uv run pytest` 1676 passed, 5 skipped.
    Worktree and local branches removed; remote branch `fix/codemem-ast-grep-binary` left in place.
  - v1 improvement scope includes all four: fix the report's residuals; harden deep-dive for shipping;
    reuse forge assets; new capability.
  - **Clean-room rewrite.** The forge repo is PUBLIC (`snewhouse/aa-ma-forge`); the local deep-dive originated
    in prior employment. In CONTEXT.md terms this is an **Adaptation** (concept only, no files forked), not a
    Fork → no FORKS.json entry. **Never paste text from `~/.claude/commands/codebase-deep-dive.md` into forge
    files**; take ideas (phases, report set, grading concept) only.
  - **Forge becomes the single source.** Existing copies (`~/.claude/commands/codebase-deep-dive.md`,
    `~/claude-config/commands/…`) are retired once the forge version ships; `scripts/install.sh` backs up a real
    file at the same path before symlinking (`install.sh:119-124,157-185,209-221`).
  - Evaluation starting position: old vs new on 2–3 real repos, rubric-compared (Ticket 10).
- **Chart-session fact base** (sub-agent reports, 2026-09-27, verified spot-checks):
  - Local deep-dive: 1216 lines; tracked copy `~/claude-config` (origin `snewhouse/claude-config`); 6 phases,
    parallel agents in 2–4 only; ~80 `sg run` calls — **`/usr/bin/sg` is a symlink to `newgrp` (package
    `util-linux-extra`), not ast-grep** (works only when an ast-grep `sg` precedes it on PATH, e.g. a conda env or
    this repo's `.venv/bin`); `subagent_type="debugger"` has no active definition; forge `code-reviewer` and
    `security-auditor` are **milestone-diff-scoped** (need base/head SHAs) but deep-dive hands them whole-repo
    prompts; no secret-safety rule (its hard-coded-secret search can copy values into reports); Context7 promised,
    never called; model-tier contradictions (lines 66/1108 vs 344+).
  - Shipping mechanics: auto-discovered by `install.sh` glob; counts pinned by tests (13 commands / 21 skills /
    12 agents in SECURITY.md + `docs/spec/claude-code-foundations.md`; `tests/test_doc_counts.py`,
    `tests/commands/test_aa_ma_share_command.py`); `tests/hooks/install_dry_run.bats` counts skills;
    `scripts/regen-generated.sh` (git add first — L-026) regenerates golden + `docs/architecture/`;
    `tests/codemem/test_plugin_surface.py` pins dangling `{aa-ma-plan, haiku-eval}` and 7 orphans;
    next ADR number 0017; only `understand-codebase` is a skill + thin-command pair today.
  - Shipping `claude-code/commands/codebase-deep-dive.md` would turn the existing `/codebase-deep-dive`
    mentions into ON_DISK edges (extractor keeps `/x` only when `commands/x.md` exists).
- **Skills to consult each session:** `Skill(grill-with-docs)` (grilling), `Skill(prototype)` (Ste prefers
  prototyping — offer it where a shape is uncertain), `Skill(impact-analysis)` before any plan touches shared files.
- Write scope: default rule 4 only (`.claude/dev/charting/`, `docs/research/`, `prototype/*`).

## Decisions so far

<!-- one line per RESOLVED ticket, newest last -->

- [Ticket 1: Prior art](#ticket-1-prior-art--what-do-public-codebase-assessment-and-onboarding-skills-do-well-and-badly): best models are Anthropic `claude-security` / `code-modernization` (scripts measure, model judges, refute panel, directory coverage ledger, MD+JSONL/SARIF, SHA-stamped, secrets masked) and wiki generators (graph → modules → grounded pages, per-commit refresh); composing an existing plugin is a live option.
- [Ticket 3: Whole-repo agent scope](#ticket-3-whole-repo-agent-scope--can-forge-audit-agents-run-against-a-whole-repo): forge audit agents are diff-only and `verify-impl` needs a milestone — whole-repo needs shape A (mode flag), B (new agents), C (prompt override) or D (chunked); onboarding workers already repo-wide.
- [Ticket 2: codemem coverage](#ticket-2-codemem-coverage--which-assessment-needs-can-codemem-already-answer): graph/co-change/owners covered; layering, imports (Python-only), hot spots, dead code partial; complexity, duplication, coverage, structural search missing; `ast-grep` (not codemem) replaces `sg`; codemem's own bare-`sg` call fails silently → Ticket 12.
- [Ticket 4: Measurement tools](#ticket-4-measurement-tools--which-portable-tools-give-real-metrics-and-how-to-degrade-without-them): one optional tool per metric (lizard, jscpd, osv-scanner, semgrep/ast-grep, gitleaks), none universal; degrade by the `/sole-dev-merge` report-based `UNKNOWN` rule; git + codemem + Python stdlib cover size/churn/hot spots/ownership/coupling/dead code with zero installs.
- [Ticket 5: Shape](#ticket-5-shape--two-skills-one-skill-with-two-lenses-or-a-shared-core-with-two-thin-skills): two independent skills (assess = measure → judge → refute; onboard = graph → pages) + one shared contract file in `understand-codebase/references/`; understand only reads fresh (SHA) assess output, Deep offers to run it once; assess may reuse onboarding agents (details T7).
- [Ticket 6: Names and entry points](#ticket-6-names-and-entry-points--skill-names-command-wrappers-and-the-local-copy-collision): `assess-codebase` skill + thin command (14 commands / 22 skills); local `/codebase-deep-dive` kept through evaluation, then deleted by Ste by hand; 27 mentions repointed with one flagged legacy-absorb rule; legacy reports absorbed as "legacy, unverified".
- [Ticket 7: Assessment content](#ticket-7-assessment-content--which-reports-what-is-measured-vs-judged-and-how-grading-works): 4 dimensions; tools measure (UNKNOWN when absent), model judges with file:line; per-dimension Strong/Adequate/Weak/UNKNOWN + confidence, no overall grade; High+ refutation; scanners + triage, `claude-security` optional Deep pass; built-in agents + coverage ledger, no new agents; tests run only on ask; Quick/Standard/Deep tiers.
- [Ticket 12: codemem bare-`sg`](#ticket-12-codemems-bare-sg-silent-failure--fix-before-the-plan-inside-it-or-out-of-this-effort): fixed outside the plan in PR #3 (not merged); hard precondition — PR #3 merged to main before the plan executes.
- [Ticket 8: Output contract](#ticket-8-output-contract--location-secret-safety-provenance-machine-readable-output-re-runs): `.claude/reports/assess-codebase/<sha12>[-dirty]/`, self-ignoring; summary.json + findings.jsonl + SARIF + Markdown, versioned; SHA freshness + new/fixed/persisting diff (incremental → TODOS); shared `ANALYSIS-CONTRACT.md` = NO-SECRETS, output secret gate, provenance, injection rule, schemas.
- [Ticket 9: Residual cleanup](#ticket-9-residual-cleanup--what-happens-to-r1r7-and-n1): R1/R2/R5/R7/R8/N1 fixed test-first inside the plan; R4 extractor learns unshipped `/x` → DANGLING (measure noise first); `/deep-analysis` refs dropped; ADR-0017 new + ADR-0006 amended; R6 → Ticket 10 eval.
- [Ticket 10: Evaluation](#ticket-10-evaluation--how-do-we-know-the-new-versions-are-better): forge + a private Python repo (154 files) + a pinned public TS/JS repo; two blinded fresh LLM judges per repo with ~20-claim checks; pass = new >= old on accuracy/evidence everywhere, zero secret leaks, zero failed Critical/High, justified UNKNOWNs, R6 absorbed; CI contract tests on a fixture repo, eval one-off.
- [Ticket 11: understand-codebase v1](#ticket-11-understand-codebase-improvements-beyond-the-residuals--what-goes-in-v1): all 8 — code grounding check, build/test/lint currency check (no installs/network), coverage ledger, 10-claim check in Standard, codemem hot_spots/co_changes/owners/layers, `onboarding.json`, leaner AGENTS.md, incremental regeneration (understand only); one plan, ordered milestones.

## Tickets

### Ticket 1: Prior art — what do public codebase-assessment and onboarding skills do well and badly?
- Type: research
- Mode: AFK
- Status: RESOLVED
- Blocked-by: —
#### Question
Survey public prior art for LLM-agent codebase **assessment** and **onboarding** workflows (e.g. `gsd-map-codebase`,
`improve-codebase-architecture`, Anthropic/community Claude Code skills, other agent frameworks' repo-analysis
flows). For each: what it produces, how it gathers evidence (measured vs model-judged), how it handles scale,
secrets, staleness/re-runs, and output reuse. Distil ideas and pitfalls relevant to a clean-room design.
Output: `docs/research/codebase-analysis-skills-prior-art.md`.
#### Answer
**Assessment:** the strongest prior art is Anthropic's `claude-security` (v0.12.0) and `code-modernization` (v1.0.0)
plugins — both installed locally under `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/` (re-checked).
Pattern: scripts *measure* (size, revision, verification tallies), the model only *judges*; every finding must survive
a refute panel before it is reported; every top-level directory is either assessed or explicitly set aside with a
reason; output is Markdown + JSONL/SARIF with stable finding IDs, stamped with commit SHA and a `-dirty` flag,
credentials masked, report dir gitignored. **Onboarding:** CodeWiki / DeepWiki / Code Wiki build a dependency graph,
split it into modules, write leaf pages from code and parent pages from children, and update per commit;
`modernize-map` adds a code-side grounding check (every name/number in prose must appear in its source excerpt).
`gsd-map-codebase` is the nearest Claude Code analogue but is fully model-judged, dates (not SHAs) its staleness and
commits its output. **Pitfalls:** gap-finding reviewers always find gaps; secrets leak into reports; `head -N` caps
silently truncate large repos; date-based staleness; diff-scoped reviewers (Anthropic `code-review`/`security-review`,
forge `code-reviewer`) misapplied to whole repos; unpinned CDN scripts with mermaid `securityLevel: "loose"` over model
output. Clean-room: the survey did not read the local deep-dive or `~/claude-config/` (file `:25`).
Implication for Ticket 5/7: composing or delegating to an existing plugin (e.g. `claude-security`) is a live option
alongside building. See `docs/research/codebase-analysis-skills-prior-art.md`.

### Ticket 2: codemem coverage — which assessment needs can codemem already answer?
- Type: research
- Mode: AFK
- Status: RESOLVED
- Blocked-by: —
#### Question
Map the evidence a whole-repo assessment needs (structure, layering, call/dependency graph, hot spots, ownership /
bus factor, co-change coupling, dead code, complexity, duplication, test coverage, anti-pattern search) against what
codemem ships today (`packages/codemem-mcp/`: CLI + MCP tools — `layers`, `hot_spots`, `owners`, `co_changes`,
`dead_code`/`find_dead_code`, `who_calls`, `blast_radius`, `dependency_chain`, `search_symbols`, `file_summary`,
`diagram`, `symbol_history`, `find_references`, `aa_ma_context`). For each need: covered / partial / missing, with
file:line evidence and a live call on this repo. Also: can codemem (or `ast-grep` by that binary name) replace the
local deep-dive's non-portable `sg` calls? Output: `docs/research/codebase-analysis-skills-codemem-coverage.md`.
#### Answer
**Covered:** call graph, co-change coupling (per file), owners, small-repo scale. **Partial:** directory structure,
layering (in-degree tertiles only), import graph (Python only; visible only via `draw`), hot spots (commits × function
count, tests included), dead code (live run flagged 1356, 1256 of them in tests). **Missing:** cyclomatic complexity,
duplication, test coverage, structural/anti-pattern search. CLI `codemem query` reaches 6 of 13 MCP tools. Budget is
JSON-chars/4 with prefix truncation + `truncated` flag, but `layers` and `aa_ma_context` flag without trimming
(`layers(budget=100)` returned ~10k chars); `diagram` collapses a level before truncating. **codemem cannot replace
`sg`; the `ast-grep` binary (shipped in `.venv`) can.** Side finding → Ticket 12: codemem itself shells out to bare
`sg` (`packages/codemem-mcp/src/codemem/parser/ast_grep.py:356`), silences stderr and returns empty stdout on failure
(`:165-187`), so on a PATH where `sg` resolves to `/usr/bin/sg` → `newgrp` (`util-linux-extra`) non-Python files index
to zero symbols silently (researcher's live probe; mechanism re-checked in code 2026-09-27).
See `docs/research/codebase-analysis-skills-codemem-coverage.md`.

### Ticket 3: Whole-repo agent scope — can forge audit agents run against a whole repo?
- Type: research
- Mode: AFK
- Status: RESOLVED
- Blocked-by: —
#### Question
Read the contracts of forge agents `claude-code/agents/code-reviewer.md`, `security-auditor.md`,
`future-proofing-auditor.md` and the 4 `codebase-onboarding-*` agents, and `Skill(verify-impl)` which dispatches the
audit agents. Facts only: what inputs each requires, whether a whole-repo run is possible within the current contract
(e.g. base = git empty tree `4b825dc642cb6eb9a060e54bf8d69288fbee4904`), what would break or be misleading (severity
gating, diff-only reasoning, token budget), and what a whole-repo variant would need (new agent vs mode flag).
Output: `docs/research/codebase-analysis-skills-agent-scope.md`.
#### Answer
**Not as-is.** `Skill(verify-impl)` cannot run whole-repo: it needs an active task and a gate-resolvable milestone,
halts on any gate failure, and has no base-SHA input (`verify-impl/SKILL.md:27-30,73-96`). The 5 audit agents can be
dispatched directly with the empty-tree base (git accepts it: 659 files / 122,334 insertions, ~7.7 MB on this repo —
re-measured 2026-09-27), but their added-lines-only contracts then mislead: nothing is "pre-existing", so
code-reviewer's scope-discipline raises ~1 CRITICAL per file (each opening the accept/dispute/defer panel),
tdd-sequence is a guaranteed FAIL (`446e3a8` adds first `tests/` and `src/` together — re-checked), context7 flags
every dependency. Four whole-repo shapes mapped to the contract lines each touches, no pick: (A) mode flag in existing
agents, (B) new agent(s), (C) caller-prompt override (precedent: `sole-dev-merge`, `understand-codebase`),
(D) directory-chunked review. The 3 onboarding workers (conventions, runbook, health) already run repo-wide and are
reusable; the synthesizer less so (`agents_md_action` input, writes root `ONBOARDING.md`).
See `docs/research/codebase-analysis-skills-agent-scope.md`.

### Ticket 4: Measurement tools — which portable tools give real metrics, and how to degrade without them?
- Type: research
- Mode: AFK
- Status: RESOLVED
- Blocked-by: —
#### Question
For the metrics an assessment grade would lean on — cyclomatic complexity, duplication, test coverage, dependency
vulnerability / outdatedness, lint/security static findings, licence — identify portable, optional, multi-language
tools (e.g. `lizard`, `jscpd`, `radon`, `pip-audit`, `npm audit`, `osv-scanner`, `semgrep`, `bandit`, `ast-grep`),
their install footprint, exit/format contracts, runtime on a mid-size repo, and the graceful-degradation shape when
absent (the forge precedent: `SHELLCHECK_BIN`/`BANDIT_BIN`, "degraded scanner writes UNKNOWN rather than zero").
Output: `docs/research/codebase-analysis-skills-measurement-tools.md`.
#### Answer
**A portable optional tool exists per metric; none covers all.** Candidates: `lizard` (complexity), `jscpd` (duplication;
MIT, now a Rust binary via npx), `osv-scanner` (vulns + licences; only one with real `--offline` and an rc that separates
error from findings), `semgrep` CE / `ast-grep` (static rules), `gitleaks` (secrets). Coverage always means running the
tests; `scancode` (~105 MB wheel) is too heavy as a default. **On BATS today** (re-checked `command -v`, 2026-09-27):
`gitleaks`, `semgrep` (`~/.local/bin`) and `pip-audit` (conda env) present; `lizard`, `jscpd`, `osv-scanner` absent —
so a consumer machine cannot be assumed to have any of them. **Degradation precedent:** `/sole-dev-merge` Stage C judges
the *report*, not the binary (`rc>1 || ! -s`) and writes a `[HIGH] … UNKNOWN` sentinel into `$FINDINGS`
(`claude-code/commands/sole-dev-merge.md:342-431`, re-checked `:349-361`); gitleaks, semgrep and pip-audit overload exit
codes, so that report-based rule transfers unchanged. **Zero-install metrics:** size, churn, hot spots, ownership,
coupling, dead code (codemem) + Python-only complexity, crude duplication, Python dependency licences
(`importlib.metadata`); everything else needs a tool. See `docs/research/codebase-analysis-skills-measurement-tools.md`.

### Ticket 5: Shape — two skills, one skill with two lenses, or a shared core with two thin skills?
- Type: grilling
- Mode: HITL
- Status: RESOLVED
- Blocked-by: 1, 2, 3
#### Question
Given the overlap map (report §3: architecture, quality, security, deps, recommendations) and Tickets 1–3, how should
the assessment capability and `understand-codebase` relate once both ship? Options on the table: (a) two independent
skills with a documented boundary and one-way reuse; (b) one skill with `assess` / `onboard` lenses sharing
dimensions and agents; (c) a shared core (dimensions, agents, references, NO-SECRETS constraint) under two thin entry
skills. Decide, with the maintenance cost of each named.
#### Answer
**Two independent skills plus one shared contract file.**
1. **Two skills, two pipelines.** Assessment = measure → judge → refute (Ticket 1's `claude-security` /
   `code-modernization` pattern); onboarding = graph → pages. Rejected: one skill with two lenses (tier × lens matrix,
   345-line `SKILL.md` grows, pinned inventory tests churn, the name misfits an audit); shared core + thin skills
   (+1 asset in the counts, cross-skill file edges the plugin-surface extractor does not track); fully independent
   (duplicated NO-SECRETS / provenance rules drift).
2. **Shared contract** — NO-SECRETS, provenance stamp, output contract — lives in
   `claude-code/skills/understand-codebase/references/` (where the rules already are: `SKILL.md:267-270` Hard
   constraints, `references/DIMENSIONS.md` §8). The assessment skill links it by relative path; sibling skill dirs
   resolve through install symlinks (checked: `~/.claude/skills/understand-codebase/../verify-impl/SKILL.md` exists).
   A test asserts both skills reference it. No new asset, no count change. Its *contents* are Ticket 8.
3. **One-way, read-first coupling.** `understand-codebase` READS fresh assessment output (freshness by commit SHA),
   never runs it silently; in the Deep tier, when no fresh output exists, it asks the user once whether to run the
   assessment first.
4. **Agent reuse allowed in principle** — the repo-wide onboarding workers (health, conventions, runbook; Ticket 3);
   which agents and how is Ticket 7.
Decided with Ste 2026-09-27.

### Ticket 6: Names and entry points — skill names, command wrappers, and the local-copy collision
- Type: grilling
- Mode: HITL
- Status: RESOLVED
- Blocked-by: 5
#### Question
What are the shipped names (keep `codebase-deep-dive`, or rename for the clean-room version)? Skill only, or skill +
thin command (the `understand-codebase` precedent)? How is the existing `~/.claude/commands/codebase-deep-dive.md`
retired (install.sh only backs up a file at the *same* path it symlinks)? What happens to the existing
`/codebase-deep-dive` mentions and the plugin-surface golden when the name becomes ON_DISK?
#### Answer
1. **Name: `assess-codebase`** — skill dir `claude-code/skills/assess-codebase/`; pairs with `understand-codebase`
   (verb + codebase) and marks a new clean-room asset. Rejected: `codebase-deep-dive` (blurs the clean-room line; old
   mentions would silently point at new behaviour), `audit-codebase` (wording collides with `security-auditor` /
   `/security-review`), `codebase-assessment`.
2. **Skill + thin command** `claude-code/commands/assess-codebase.md` (parses path + flags, invokes
   `Skill(assess-codebase)`), following `commands/understand-codebase.md:9`. Makes `/assess-codebase` ON_DISK to the
   plugin-surface extractor (it keeps `/x` only when `commands/x.md` exists). Counts: 13→14 commands, 21→22 skills
   (pinned in SECURITY.md + `docs/spec/claude-code-foundations.md`; regen golden + `docs/architecture/`).
3. **Local copy retired by hand, after evaluation.** `~/.claude/commands/codebase-deep-dive.md` stays through Ticket
   10's old-vs-new comparison; a final plan step is a checklist for Ste to delete it and `~/claude-config/commands/…`.
   No forge tombstone (install.sh never touches a differently named file; only Ste has the local copy).
4. **The 27 existing mentions** (10 files: understand-codebase `SKILL.md`, 6 references/template, command,
   2 agents — counted 2026-09-27) are repointed to `/assess-codebase` and its new output (location = Ticket 8), keeping
   **exactly one** flagged "legacy deep-dive output" absorb rule in Step 0 / `REUSE-MAP.md`. Pinned guard tests
   (`KEPT`, `ROUTES_TO_UNSHIPPED` in `tests/skills/test_understand_codebase_rewire.py`) are updated to match.
5. **Legacy `.claude/reports/codebase-deep-dive-*`** (present in 14 projects) is still absorbed, marked
   "legacy, unverified" in Provenance.
Decided with Ste 2026-09-27.

### Ticket 7: Assessment content — which reports, what is measured vs judged, and how grading works
- Type: grilling
- Mode: HITL
- Status: RESOLVED
- Blocked-by: 2, 3, 4, 5
#### Question
For the clean-room assessment: which dimensions/reports ship in v1; for each, which evidence is measured (tool/codemem)
vs model-judged; whether a grade exists at all, and if so its scheme (the local version averages five letter grades,
several of which it never measures); how findings carry file:line evidence and confidence; and how the audit
delegates to forge agents (per Ticket 3).
#### Answer
1. **v1 dimensions:** Architecture & structure · Maintainability · Security · Tests & dependencies.
2. **Measured vs judged** (Ticket 1 pattern): tools/scripts measure — git, codemem (Ticket 2 coverage), and optional
   tools when present (`lizard`, `jscpd`, `gitleaks`, `semgrep`, `osv-scanner`, `pip-audit`; Ticket 4). A missing or
   failed tool yields **UNKNOWN, never zero**, by the `/sole-dev-merge` report-based rule
   (`claude-code/commands/sole-dev-merge.md:342-431`). The model only judges; every judged finding cites `file:line`.
3. **Rating:** per dimension `Strong / Adequate / Weak / UNKNOWN` + confidence `High / Med / Low`, listing the measured
   inputs behind it. **No overall grade**; areas ranked relatively (no effort/cost/date numbers).
4. **Refutation:** Critical/High findings must survive a refuter (built-in agent prompted to disprove) before being
   reported; Medium/Low ship with capped confidence.
5. **Security:** scanners + model triage. If Anthropic's `claude-security` plugin is installed *and* enabled, the Deep
   tier offers it as the deep pass — a **declared-external** reference (call, never copy: its `LICENSE` reads
   "All rights reserved"; it is installed but not enabled on BATS, checked 2026-09-27) → add to
   `surface_allowlist.EXTERNAL` if referenced as `Skill(...)`.
6. **Agents:** inventory step builds a **coverage ledger** (every top-level dir assessed or set aside with a reason),
   then per-component dispatch to **built-in** Explore / general-purpose agents with prompts kept in
   `assess-codebase/references/` (precedent: understand-codebase Standard tier); reuse `codebase-onboarding-health`.
   **No new agent assets; verify-impl's audit agents untouched** (Ticket 3 shape C/D, not A/B).
7. **Tests:** ask once (showing the detected command), run with a timeout; declined / failed / timed out → coverage
   UNKNOWN.
8. **Tiers:** Quick = measured only, no agents · Standard (default) = measured + judged + High+ refutation ·
   Deep = + security deep pass + test run. Ask once with a real file count; large repos default to hot-spot focus.
**Carried into the plan (not decided here):** model choice per agent (haiku vs sonnet), skill size / progressive
disclosure into `references/`, exact thresholds behind Strong/Adequate/Weak. Decided with Ste 2026-09-27.

### Ticket 8: Output contract — location, secret safety, provenance, machine-readable output, re-runs
- Type: grilling
- Mode: HITL
- Status: RESOLVED
- Blocked-by: 5
#### Question
Where outputs land and whether they are gitignored; the contents and filename of the shared contract file in
`understand-codebase/references/` (Ticket 5) — one NO-SECRETS constraint for both skills (the local
deep-dive has none and can copy secret values into reports), incl. masking rules (Ticket 1 prior art); provenance stamp (date · SHA · tier · tools, the
`understand-codebase` precedent); a machine-readable summary other skills can consume (replacing today's prose-path
absorption, `SKILL.md:99`); freshness detection and incremental / diff-scoped re-runs.
#### Answer
1. **Location:** `assess-codebase` writes `.claude/reports/assess-codebase/<sha12>[-dirty]/` in the target repo; a
   re-run at the same SHA replaces that dir, older SHAs stay as history (beside legacy
   `.claude/reports/codebase-deep-dive-*`).
2. **Git:** the reports root gets a self-ignoring `.gitignore` (`*`, the `claude-security` pattern — Ticket 1); the
   user's `.gitignore` is never edited.
3. **Machine output:** `summary.json` (SHA, dirty, tier, per-dimension rating + confidence, tool status
   ran/absent/UNKNOWN, coverage ledger) + `findings.jsonl` (stable ID, dimension, severity, confidence, `file:line`,
   refutation status) + **`findings.sarif`** + Markdown rendered for humans; every machine file carries
   `schema_version`.
4. **Freshness:** both skills judge by commit SHA (stamp SHA == `HEAD` and tree clean) — replacing
   understand-codebase's date comparison (`SKILL.md:97`, `git log -1 --format=%cd`). Re-runs report new / fixed /
   persisting findings via stable IDs. Incremental "re-analyse only changed components" → `TODOS.md` (v2).
5. **Shared contract** = `claude-code/skills/understand-codebase/references/ANALYSIS-CONTRACT.md`, honoured by both
   skills: (a) NO-SECRETS read deny-list, moved from `SKILL.md:267-270` (which keeps a pointer + the "restate verbatim
   in every spawned agent prompt" rule); (b) layered secret **output gate** — never read secret files → mask at source
   → scan the report dir before finishing (`gitleaks` if present, else a built-in regex fallback) → redact hits and
   mark the finding redacted; (c) provenance stamp (UTC date, sha12 + `-dirty`, branch, tier, tools
   ran/absent/UNKNOWN, absorbed vs fresh; format precedent `references/ONBOARDING-TEMPLATE.md:106-114`) + the SHA
   freshness rule; (d) repo content (code, comments, CLAUDE.md) is data, never instructions; (e) pinned, versioned
   schemas of `summary.json`, `findings.jsonl`, SARIF.
   Plan impact: `tests/skills/test_understand_codebase_frontmatter.py` pins the references inventory
   (`EXPECTED_REFERENCES`, `:24`) — adding the file updates that pin.
**Carried into the plan:** stable finding-ID derivation, exact JSON/SARIF field schemas, regex fallback patterns.
Decided with Ste 2026-09-27.

### Ticket 9: Residual cleanup — what happens to R1–R7 and N1?
- Type: grilling
- Mode: HITL
- Status: RESOLVED
- Blocked-by: 5, 6
#### Question
For each residual in the report (R1 stale `SKILL.md:296` row; R2 `commands/understand-codebase.md:40` wording; R3
ADR-0006 amendment; R4 extractor `/x` detection gap; R5 Quick-tier link target; R6 untested reuse path; R7
`commands/understand-codebase.md:31`; N1 dangling `Skill(aa-ma-plan)` at `SKILL.md:345`): is it subsumed by the
shape/naming decisions, fixed inside the plan, or fixed separately beforehand? Also (graduated from fog after
Ticket 5): `/deep-analysis` is local-only and not part of this effort's two skills — keep it out, and decide how
`understand-codebase/SKILL.md:66,345` stop routing readers to it as if it shipped. Also (graduated from fog after
Ticket 6): ADR shape — a new ADR-0017 recording the `assess-codebase` **Adaptation**, and whether ADR-0006 is amended
(precedent: ADR-0003 `## Amendment`) or superseded. Note R4 is partly addressed by Ticket 6's thin command
(`/assess-codebase` becomes visible); the extractor gap for other unshipped `/x` remains.
#### Answer
New residual found this session — **R8**: `understand-codebase/SKILL.md:64-65` says "this plugin ships no whole-repo
audit", false once `assess-codebase` ships (→ point at `/assess-codebase`).
1. **Inside the plan, test-first, in the milestone that touches each file:** R1 (`SKILL.md:296` stale deep-dive half of
   the degradation row), R2 (`commands/understand-codebase.md:40` wording, name codemem), R5 (Quick-tier link target),
   R7 (`commands/understand-codebase.md:31`), R8, N1 (`Skill(aa-ma-plan)` at `SKILL.md:345` → `/aa-ma-plan`). Not
   fixed separately now: the plan rewrites the same lines (Ticket 6 repoint, Ticket 8 NO-SECRETS move).
2. **R4 in the plan:** the plugin-surface extractor (`packages/codemem-mcp/src/codemem/draw/plugin_surface.py:9-13,40,
   104-109`) learns to see `/x` references with no `commands/x.md` and classifies them DANGLING unless allowlisted.
   **Measure the noise against the current golden first**; the exact rule (e.g. backticked-only) is plan-owned. Regenerate
   `tests/golden/plugin-surface.json`, the pinned dangling set (`tests/codemem/test_plugin_surface.py:66-68`) and
   `docs/architecture/` via `scripts/regen-generated.sh` (git add first — L-026). Partly delivers `TODOS.md:5`.
3. **`/deep-analysis`:** references at `SKILL.md:66` and `:345` are dropped; planning points only at `/aa-ma-plan`.
4. **ADRs:** new **ADR-0017** records the `assess-codebase` Adaptation (clean-room, two-skill shape, `ANALYSIS-CONTRACT.md`,
   `claude-security` as declared-external); **ADR-0006** gets a dated `## Amendment` pointing to 0017 (precedent
   `docs/adr/0003-prototype-adoption.md:139`) — resolves R3. `docs/adr/INDEX.md` gains the 0017 row.
5. **R6** (reuse path never exercised) → folded into Ticket 10: the evaluation must run understand-codebase absorbing a
   real `assess-codebase` output.
Decided with Ste 2026-09-27.

### Ticket 10: Evaluation — how do we know the new versions are better?
- Type: grilling
- Mode: HITL
- Status: RESOLVED
- Blocked-by: 7
#### Question
Starting position (Ste, chart time): run old vs new on 2–3 real repos and compare against a rubric. Decide which repos
(candidates: aa-ma-forge; a private Python repo of Ste's, which has a 2026-09-17
deep-dive report), the rubric (accuracy of claims vs code, evidence density, actionability, false positives, secret
leakage, runtime/cost), the pass bar, and whether any of it becomes an automated test. Must include (Ticket 9, R6):
one run of understand-codebase absorbing a real `assess-codebase` output, checked in its Provenance.
#### Answer
1. **Evaluation set:** aa-ma-forge (659 tracked files, mixed Python/bash/md/JS); a private Python repo of Ste's
   (154 files — its `.claude/reports/codebase-deep-dive-20260917-1040` is the
   old side, no re-run); one mid-size **public TS/JS repo** cloned to scratch (exercises the non-Python ast-grep path
   fixed by PR #3, and scale — the plan picks it and pins its SHA). Old side = Ste's local `/codebase-deep-dive` (kept
   through evaluation, Ticket 6); new side = `assess-codebase` + improved `understand-codebase`. Outputs stay local
   (self-ignored report dirs).
2. **Scoring — LLM judge only** (Ste does not score by hand): two fresh-context judges per repo, **blinded** (reports
   anonymised A/B, random order); each samples ~20 claims per report and checks them against the code
   (true / false / unverifiable) before scoring the rubric — accuracy, evidence density, actionability, false
   positives, secret leakage, runtime. Judge disagreements are listed. Verdict file lands in `docs/research/`.
3. **Pass bar (v1 ships only if):** new >= old on claim accuracy and evidence density on **every** repo; zero secret
   values in any output; zero Critical/High findings that fail the claim check; every UNKNOWN justified (tool really
   absent); `understand-codebase` absorbs a real assess output, visible in its Provenance (R6, Ticket 9). Runtime
   recorded, not gated.
4. **Automation:** deterministic contract tests in CI on a **tiny fixture repo** in the forge's tests — schema_version
   + JSON/SARIF validity, planted fake secrets redacted, self-ignoring report dir, `<sha12>[-dirty]` naming, UNKNOWN
   when a tool is absent, stable IDs across two runs (for the script-measured findings; model-judged findings are
   nondeterministic). The LLM-quality evaluation is a documented **one-off before release**; no harness script.
Decided with Ste 2026-09-27.

### Ticket 11: understand-codebase improvements beyond the residuals — what goes in v1?
- Type: grilling
- Mode: HITL
- Status: RESOLVED
- Blocked-by: 1, 2, 5
#### Question
Beyond the report's residuals, where is `understand-codebase` (2067 lines across SKILL.md, 9 references, 1 template,
4 agents, 1 command) weak or improvable — e.g. what it re-derives that codemem already answers, tier cost vs value,
the untested absorb path, output reuse? Pick the v1 set; the rest goes to `TODOS.md`.
#### Answer
Facts behind the choice (checked 2026-09-27): the runbook agent is read-only and never runs documented commands
(`claude-code/agents/codebase-onboarding-runbook.md:28`); claims are fact-checked only by the Deep-tier reviewer
(`understand-codebase/SKILL.md:214-215`); codemem `layers`/`owners` are used (13 mentions each) but `hot_spots` and
`co_changes` never; no machine-readable output. **All 8 improvements are in v1:**
1. **Grounding check in code** (prior art: `modernize-map`, Ticket 1): every identifier/number in generated prose must
   occur in the source it cites; re-ask once, then drop the claim. Every tier.
2. **Command currency check:** ask once, then run documented **build/test/lint** commands with a timeout — **never
   installs, never network**; each marked verified / failed / not run (needs setup) in `ONBOARDING.md`.
3. **Coverage ledger:** every top-level dir described or set aside with a reason (same mechanism as assess, Ticket 7).
4. **Claim check in Standard:** 10 sampled claims; Deep keeps ~20; failed claims fixed or removed before finishing.
5. **Lean on codemem:** `hot_spots`, `co_changes`, `owners`, `layers` feed dimension 4 (structure) and 13 (repo
   health) instead of Explore agents re-deriving them.
6. **Machine-readable companion** `.claude/onboarding/onboarding.json`, versioned under `ANALYSIS-CONTRACT.md`
   (Ticket 8): commands + currency status, entry points, codemem-ranked key modules, rules files, SHA stamp.
7. **Leaner AGENTS.md:** revise `references/AGENTS-MD-TEMPLATE.md` so a generated `AGENTS.md` holds only what cannot
   be inferred from code.
8. **Incremental regeneration** — understand-codebase only: regenerate sections whose files changed since the stamped
   SHA. assess-codebase stays deferred (Ticket 8).
**Plan shape (carried into the plan):** one plan, milestones in order — PR #3 merged (Ticket 12 precondition) →
`ANALYSIS-CONTRACT.md` → `assess-codebase` → understand-codebase improvements + residuals (Ticket 9) → extractor R4 →
evaluation (Ticket 10) → ADRs / counts / release. Each milestone lands green on its own.
Decided with Ste 2026-09-27.

### Ticket 12: codemem's bare-`sg` silent failure — fix before the plan, inside it, or out of this effort?
- Type: grilling
- Mode: HITL
- Status: RESOLVED
- Blocked-by: —
#### Question
codemem's ast-grep parser defaults to `sg_bin="sg"` (`packages/codemem-mcp/src/codemem/parser/ast_grep.py:356`),
discards stderr and treats failure as empty output (`:165-187`); on a machine where `sg` resolves to `/usr/bin/sg`
(`newgrp`, `util-linux-extra`) every non-Python file indexes to zero symbols with no warning. Both skills in this
effort lean on codemem (understand-codebase's Deep tier, Standard's index; the assessment's structure evidence).
Decide: (a) separate bugfix now, outside charting (e.g. resolve `ast-grep` before `sg`, fail loudly / mark UNKNOWN);
(b) a prerequisite milestone inside the plan; (c) out of scope → `TODOS.md`.
#### Answer
**(a) Fixed separately, outside this effort's plan, via PR https://github.com/snewhouse/aa-ma-forge/pull/3**
(branch `fix/codemem-ast-grep-binary`: `de37d6d` RED test, `6861c50` fix — resolve `ast-grep` first, `sg` only if its
`--version` says ast-grep, otherwise log a warning instead of indexing to a silent zero; details in Notes). PR state
re-checked 2026-09-27: OPEN, MERGEABLE, 7/7 CI checks green, no review yet.
**Plan precondition (hard) — MET 2026-09-27, merge commit `80caae7`:** PR #3 merged to `main` before `/aa-ma-plan --from-map codebase-analysis-skills` starts
execution — both skills rely on codemem indexing non-Python files. Ste reviews and merges; a read-only code review of
PR #3 was requested after this ticket was recorded. The agent worktree `.claude/worktrees/agent-a07f8ae0149b93c3a`
is cleaned up after the merge. Decided with Ste 2026-09-27.

## Not yet specified


## Out of scope

- Copying any text from the local `/codebase-deep-dive` (clean-room Adaptation, Ste 2026-09-27).
- Deleting `~/claude-config/commands/codebase-deep-dive.md` — Ste's manual action outside this repo, after the forge version ships.
- `scripts/uninstall.sh` deregisters 5 hooks while `install.sh` registers 8 (`uninstall.sh:220-226` vs `install.sh:314-323`) — unrelated finding; `TODOS.md` candidate.
