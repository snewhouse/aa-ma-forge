# Prior art: what do public LLM-agent codebase-assessment and onboarding workflows do well and badly?

**Created:** 2026-09-27
**Author:** aa-ma-researcher (Claude), for charting effort `codebase-analysis-skills`, Ticket 1
**Reviewed-Through-Date:** 2026-09-27 (local skill/plugin copies as installed on BATS this day; web sources fetched this day)
**Valid-Through:** 2026-Q4 (claude-plugins-official ships fast — `claude-security` is at 0.12.0; re-read the local plugin copies and re-fetch the web sources if you use this after 2026-12-31 or after any plugin update)
**Sources:**
- `~/.claude/skills/gsd-map-codebase/SKILL.md`, `~/.claude/get-shit-done/workflows/{map-codebase,scan}.md`, `~/.claude/agents/{gsd-codebase-mapper,gsd-intel-updater}.md`, `~/.claude/skills/gsd-intel/SKILL.md` (GSD 1.36.0 per `~/.claude/get-shit-done/VERSION`): GSD's map, scan and intel flows
- `~/.claude/plugins/cache/claude-plugins-official/mattpocock-skills/1.2.3/skills/engineering/improve-codebase-architecture/{SKILL.md,HTML-REPORT.md}` (current) and `~/.agents/skills/improve-codebase-architecture/SKILL.md` (older 2026-05-05 copy): Pocock's architecture review
- `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/claude-security/` (v0.12.0): Anthropic's whole-repo security scan
- `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/code-modernization/` (v1.0.0): Anthropic's legacy-system assessment and topology map
- `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/{code-review,claude-md-management,feature-dev}/`: Anthropic's diff review, CLAUDE.md audit and code-explorer
- https://github.com/anthropics/claude-code/blob/main/plugins/code-review/commands/code-review.md: upstream diff-only review
- https://github.com/anthropics/claude-code-security-review and its `.claude/commands/security-review.md`: the `/security-review` method
- https://code.claude.com/docs/en/best-practices: `/init`, CLAUDE.md scope, the claim that a gap-finding reviewer always finds gaps
- https://aider.chat/docs/repomap.html, https://aider.chat/2023/10/22/repomap.html, https://raw.githubusercontent.com/Aider-AI/aider/main/aider/repomap.py: Aider repo map
- https://sourcegraph.com/docs/cody/core-concepts/context: Cody context retrieval
- https://docs.openhands.dev/openhands/usage/microagents/microagents-overview, https://github.com/OpenHands/OpenHands/issues/8976: OpenHands repo instructions
- https://docs.devin.ai/work-with-devin/deepwiki, https://docs.devin.ai/work-with-devin/deepwiki-mcp: DeepWiki
- https://developers.googleblog.com/introducing-code-wiki-accelerating-your-code-understanding/: Google Code Wiki
- https://arxiv.org/abs/2510.24428, https://github.com/FSoft-AI4Code/CodeWiki: CodeWiki (paper and tool)
- https://github.com/AsyncFuncAI/deepwiki-open/blob/main/api/README.md: deepwiki-open
- This repo: `claude-code/skills/understand-codebase/SKILL.md`, `packages/codemem-mcp/README.md`, `packages/codemem-mcp/src/codemem/incremental.py`, `src/aa_ma/render/html.py`, `claude-code/agents/code-reviewer.md`: the forge assets that already exist

Clean-room note: this survey used public and third-party sources only. It did not read `~/.claude/commands/codebase-deep-dive.md` or anything under `~/claude-config/`.

## Answer

The strongest public prior art for whole-repo **assessment** is Anthropic's `claude-security` and `code-modernization` plugins. Tools measure the facts: size, complexity, the revision, and a verification tally computed in code. Every model-judged finding must survive adversarial verification. Every top-level directory is either scanned or set aside with a reason. Output comes in both human and machine-readable form (MD + JSONL/SARIF/JSON), stamped with the commit it describes, with credentials masked and the report directory git-ignored.

The strongest **onboarding** prior art is the wiki generators (DeepWiki, Google Code Wiki, CodeWiki). They build a dependency graph, decompose it into modules, write leaf pages from code and parent pages from child pages, and update incrementally per commit. GSD's `map-codebase` is the closest Claude Code-native analogue. It writes 7 prescriptive markdown docs from 4 parallel agents, but it is model-judged throughout, keeps no commit stamp, uses only date-based staleness, and commits its output.

The recurring pitfalls:
- output padded by model judgement ("asked for gaps, finds gaps")
- secret leakage into committed reports
- silent truncation on large repos
- staleness keyed to dates, not commits
- diff-scoped reviewers applied to whole repos

## Evidence

### 1. Per-source findings

Each entry covers: what it produces · how it gathers evidence (M = measured by a tool, J = model-judged) · how it scales · secrets · staleness and re-runs · whether the output is machine-readable · pitfalls.

#### 1.1 GSD `gsd-map-codebase` / `gsd-scan` / `gsd-intel` (onboarding + light assessment)
- **Produces:** 7 markdown docs in `.planning/codebase/`: STACK, INTEGRATIONS, ARCHITECTURE, STRUCTURE, CONVENTIONS, TESTING, CONCERNS (`~/.claude/get-shit-done/workflows/map-codebase.md:79-86`). They come from 4 parallel mapper agents (tech / arch / quality / concerns) that write the files themselves and return only confirmations (`map-codebase.md:4`, `:101-189`). `gsd-scan` is the one-agent, one-focus variant (`~/.claude/get-shit-done/workflows/scan.md:1-3`, `:17-25`).
- **Written for downstream agents, not humans:** a phase-type → docs table routes each doc into `/gsd-plan-phase`. The docs are told to be "prescriptive, not descriptive", to always give file paths, and to "write current state only" (`~/.claude/agents/gsd-codebase-mapper.md:40-71`, `:77-84`).
- **Evidence:** mostly J. The mapper runs grep/find/`wc -l` recipes, each capped with `head -N` (for example `| head -50` for imports and `| head -20` for the largest files), then "Read key files" (`gsd-codebase-mapper.md:106-154`). Nothing is computed-and-stored as a metric. The only acceptance check is "each doc >20 lines" (`map-codebase.md:269-271`).
- **Scale:** per-agent fresh context (`map-codebase.md:14-19`). Subagent timeout defaults to 300000 ms and "Increase for large codebases" (`map-codebase.md:205`). The `head -N` caps truncate evidence silently, and there is no coverage ledger.
- **Secrets:** a `<forbidden_files>` deny-list (`.env*`, `*.pem`, `*secret*`, `.npmrc`, …) with "note their EXISTENCE only" (`gsd-codebase-mapper.md:736-756`, also `:108-110`). This is followed by a post-hoc regex grep over the generated docs for known token shapes (`sk-`, `ghp_`, `AKIA`, JWT, PEM), which pauses before commit on a hit (`map-codebase.md:278-306`).
- **Staleness / re-run:** asks Refresh / Update-selected-docs / Skip when the map exists (`map-codebase.md:42-66`). `gsd-scan` shows file modification dates (`scan.md:53-62`). The docs carry an `Analysis Date` but no commit SHA (`gsd-codebase-mapper.md:196`).
- **Commits its output by default** (`map-codebase.md:313-318`; `~/.claude/skills/gsd-map-codebase/SKILL.md:62`).
- **`gsd-intel` is the machine-readable sibling:**
  - JSON files, each with `_meta.updated_at` and `version`, told to be "machine-parseable, evidence-based … Prefer structured JSON over prose" (`~/.claude/agents/gsd-intel-updater.md:35`, `:92`).
  - Counts must be derived with Glob, "not from memory or CLAUDE.md" (`:74-76`).
  - A tool-written snapshot carries hashes (`:254-258`).
  - Partial updates are keyed on changed paths (`:260-266`).
  - Hard per-file token budgets apply ("the most important 50-100 source files", `:268-279`).
  - Staleness is age-based: "stale if older than 24 hours" (`~/.claude/skills/gsd-intel/SKILL.md:102`).
- **Pitfall observed:** the skill tells the agent to write `api-map.json, dependency-graph.json, file-roles.json, arch-decisions.json` (`gsd-intel/SKILL.md:145`), but the agent's schemas are `files.json, apis.json, deps.json, stack.json, arch.md` (`gsd-intel-updater.md:94`, `:113`, `:130`, `:149`). The skill has drifted from its own agent.

#### 1.2 Pocock `improve-codebase-architecture` (architecture assessment, interactive)
- **Produces:** a self-contained HTML report of "deepening opportunities". Each card lists Files / Problem / Solution / Benefits / before-after diagram / recommendation strength (`Strong`, `Worth exploring`, `Speculative`), and the report ends with a top recommendation. The user then picks a candidate and a grilling loop follows (`…/1.2.3/skills/engineering/improve-codebase-architecture/SKILL.md:37-64`). It is user-invoked only (`SKILL.md:4`, `disable-model-invocation: true`).
- **Evidence:** J, deliberately. "Don't follow rigid heuristics — explore organically and note where you experience friction". The judgement tool is a thought experiment, the "deletion test" (`SKILL.md:27-35`). There is one measured-ish input: hot spots taken from `git log --oneline` to scope the scan ("Scope before you scan — YAGNI", `SKILL.md:20-23`).
- **Scale:** scoping to hot spots, or to a direction the user names, is the scaling strategy (`SKILL.md:20-23`).
- **Domain / ADR awareness:** reads `CONTEXT.md` and `docs/adr/`, and does not re-litigate ADRs unless the friction is real (`SKILL.md:14`, `:56`). When the user rejects a candidate for a load-bearing reason, it offers an ADR "so future architecture reviews don't re-suggest it" (`SKILL.md:70`). That is a memory mechanism against repeated findings.
- **Output location:** OS temp dir, "so nothing lands in the repo" (`SKILL.md:39`). No machine-readable output. There is no secret handling beyond staying out of the repo, and not found: there is no staleness mechanism.
- **Pitfalls:** the report loads Tailwind and `mermaid@11` from CDNs, unpinned and without SRI, with `securityLevel: "loose"`, over model-generated content (`HTML-REPORT.md:13-16`). By contrast, the forge renderer pins mermaid `11.17.2` with an SRI hash and `securityLevel: "strict"` (`src/aa_ma/render/html.py:15`, `:20-23`, `:99-100`). The older local copy presented candidates in chat and spawned `subagent_type=Explore` (`~/.agents/skills/improve-codebase-architecture/SKILL.md:37`, `:47-60`), which shows that upstream changes shape between versions.

#### 1.3 Anthropic `code-review` (diff review, not whole-repo)
- **Installed copy** (`~/.claude/plugins/marketplaces/claude-plugins-official/plugins/code-review/commands/code-review.md`): Haiku agents run the eligibility check, collect CLAUDE.md paths and summarise the change (`:11-13`). Then 5 parallel Sonnet reviewers (`:14`), a per-issue Haiku confidence score from 0 to 100 (`:20-25`), and "Filter out any issues with a score less than 80" (`:26`). Explicit false-positive classes include pre-existing issues, anything a linter/typechecker would catch, and general quality "unless explicitly required in CLAUDE.md" (`:33-38`).
- **Upstream current** (https://github.com/anthropics/claude-code/blob/main/plugins/code-review/commands/code-review.md): 4 reviewers (2 CLAUDE.md compliance, 2 bug/security) plus a parallel validation subagent per flagged issue, and it is "Diff-focused only: … Only look for issues that fall within the changed code". Its high-signal bar is "The code will fail to compile or parse" / "will definitely produce wrong results".
- **Relevance:** the scope is structurally the diff. Handing a diff-scoped reviewer a whole-repo prompt is a category error. The forge's own `code-reviewer` agent is also milestone-diff-scoped: it takes `<milestone-base-sha>`/`<milestone-head-sha>`, and "Pre-existing patterns are out of scope" (`claude-code/agents/code-reviewer.md:3`, `:14`, `:21`).

#### 1.4 Anthropic `/security-review` / `claude-code-security-review` action
- **Produces:** PR comments plus JSON results with `findings-count` / `results-file` outputs (https://github.com/anthropics/claude-code-security-review).
- **Method** (https://github.com/anthropics/claude-code-security-review/blob/main/.claude/commands/security-review.md):
  - Phase 1 is "Repository Context Research" (existing security frameworks and patterns).
  - Then comparative analysis of new code against those patterns, then vulnerability assessment.
  - Confidence bands where "Below 0.7: Don't report", plus a parallel false-positive-filter sub-task per finding, dropping anything the sub-task scores below 8.
  - A hard-exclusions list that includes DoS, rate limiting, and "Vulnerabilities related to outdated third-party libraries". Dependency CVEs are left to deterministic SCA.
  - Output is markdown `file:line`, severity, category, exploit scenario, recommendation.
- **Scope:** "For PRs, only analyzes changed files."
- **Pitfall stated by Anthropic:** "not hardened against prompt injection attacks and should only be used to review trusted PRs" (repo README).

#### 1.5 Anthropic `claude-security` plugin v0.12.0 (whole-repo security assessment) — the most complete design
- **Produces** a timestamped `CLAUDE-SECURITY-<ts>/` directory in the repo containing:
  - `RESULTS.md` (human-readable)
  - `RESULTS.jsonl`, whose `claudeSecurityPluginFindingId` is "designed to stay the same from scan to scan so tooling can tell a known finding from a new one"
  - a SARIF 2.1.0 log
  - a `REVISION-<sha12>.json` stamp: commit, effort, severity counts, verification thoroughness, with `-dirty` when uncommitted changes were scanned (`plugins/claude-security/README.md:55-60`)
- **Evidence:**
  - The revision is captured by a script (`write_scan_meta.py`), not the model (`skills/claude-security/jobs/scan-codebase.md:70`).
  - A findings-to-products renderer is a script (`scan-codebase.md:92-102`).
  - "the record of how thoroughly a run was verified is computed in code rather than asserted by the model" (`README.md:72`).
  - Every candidate goes to independent verifiers "told to call it a false positive unless they can confirm a real path to exploitation" (`README.md:70`). The panel is fixed at 3 voters (2-of-3) at every tier, because confidence figures are calibrated against it (`scan-codebase.md:24`, `:29`).
- **Coverage accounting:** "Every top-level directory has to be either scanned or explicitly set aside with a reason … checked before the search begins", and the report's Coverage section names what was left out (`README.md:66`). The `scan-inventory` agent (Read/Glob/Grep only, no shell) returns two ledgers, `components` and `securityScanSkippedComponents`, under a "completeness contract" (`agents/scan-inventory.md:7`, `:14-24`). Researchers that did not return must be reported, not papered over (`scan-codebase.md:112-116`).
- **Scale:**
  - Effort tiers: `low` = 1 researcher + panel; `medium` = inventory + threat model + one researcher per component×category, with components of ~25 files; `high` = up to 48 components, 2 researchers per cell (`scan-codebase.md:21-25`).
  - A whole-repo scan is "never launched without one confirming question" and is sized with the real file count (`scan-codebase.md:41-45`). Large repos get `focus: "attack-surface"` (`:86`).
  - Tests, fixtures and generated code are background. Vendored and installed code is ignored (`README.md:49`).
- **Secrets:**
  - A dedicated secrets pass still checks fixtures for real committed keys (`README.md:49`).
  - JSONL/SARIF never quote the source line of a hard-coded-credential finding (`README.md:58`).
  - A post-write `scan-redactor` agent (Read/Edit only) replaces values with `[REDACTED]` and must "never write a value or any part of one" (`agents/scan-redactor.md:7`, `:12`, `:16`). Anthropic calls this "a model's best effort, not a guarantee" (`README.md:62`).
  - The report directory carries its own `.gitignore` (`README.md:64`).
- **Injection:** "what the repository says is evidence rather than instruction … it is not a defense against a hostile repository" (`README.md:74`, and `agents/scan-inventory.md:26-28`). The recommendation for untrusted repos is to run inside sandbox-runtime (`README.md:17`).
- **Staleness:** patching refuses a report "gone stale" against current code (`README.md:80`). "Scans are nondeterministic … running scans regularly builds coverage" (`README.md:76`).

#### 1.6 Anthropic `code-modernization` v1.0.0 (whole-system assessment + onboarding-grade map)
- **Produces:**
  - `analysis/<system>/ASSESSMENT.md`: Executive Summary · Inventory · Architecture at a Glance · Runtime Profile · Technical Debt top-10 · CWE Security table · Documentation Gaps top-5 · Relative Scale · Recommended pattern (`plugins/code-modernization/commands/modernize-assess.md:133-148`)
  - `ARCHITECTURE.mmd` (`:150`)
  - a portfolio heat-map across many systems (`:16-55`)
- **Evidence:**
  - Inventory is M: `scc` / `scc --by-file -s complexity`, falling back to `cloc`, then `find`+`wc -l`, and the command must "Say which tool you used" (`modernize-assess.md:64-74`).
  - In portfolio mode "the workflow computes the COCOMO index in code, so every row uses the same formula" (`:35-36`).
  - Deep analysis is J, by 3 parallel subagents (structure map, top-10 debt with `file:line`, CWE security table) (`:83-100`).
  - A "Documentation gaps" step compares what code does with what README and docs say (`:110-113`), which is an onboarding-relevant output.
- **Anti-misuse rule:** the COCOMO figure is "a relative size measure for ranking systems, never a timeline or a cost … never print person-months, a date or a duration" (`modernize-assess.md:45-48`, `:66-69`).
- **Secrets ("Secrets first"):**
  - Credential values never appear in the shared assessment. They go to a `SECRETS.local.md` whose ignore status is verified with `git check-ignore -q` before any finding is written.
  - Non-git VCS (`.svn`, `.hg`, `CVS`) is detected, and `--show-secrets` is refused there.
  - Masking is `file:line` + a 2–4 char preview (`modernize-assess.md:93-98`, `:117-131`; `agents/legacy-analyst.md:35-41`).
- **Map (`modernize-map`):**
  - "Do not reinvent a dependency graph". Import an existing export or the stack's own tooling (`jdeps`, `madge`, `pydeps`, `go list -deps`, `cargo metadata`), reading "*machine-readable* output … never pretty-printed text", and "Spot-check about ten edges against the source" (`commands/modernize-map.md:13-28`).
  - Big estates (>~2,000 files or 500k lines) are mapped in chunks written to `map/<chunk>.json`. "A rerun skips chunks whose file exists, so an interrupted map resumes" (`:31-36`).
  - The extractor is saved as a rerunnable, auditable script producing `topology.json` against a fixed schema (`:68-72`).
  - Leaf-node prose comes from per-node "packets" (~150 source lines). "Every name and number in the paragraph must appear in the packet", and this is **checked** by the orchestrator, with one re-ask and then the description dropped (`:128-146`).
  - Untrusted JSON is escaped before HTML injection (`:164-168`).

#### 1.7 Anthropic onboarding-adjacent: `/init`, best practices, `claude-md-improver`, `feature-dev` code-explorer
- **`/init`** generates a starter CLAUDE.md from project structure. The same page says CLAUDE.md should *exclude* "File-by-file descriptions of the codebase", "Information that changes frequently", and "Anything Claude can figure out by reading code" (https://code.claude.com/docs/en/best-practices). A human onboarding doc and an agent memory file are therefore different artefacts.
- The same page recommends Q&A as the onboarding workflow ("Ask Claude questions you'd ask a senior engineer"). It also warns: "A reviewer prompted to find gaps will usually report some, even when the work is sound … Chasing every finding leads to over-engineering" (same URL).
- **`claude-md-improver`** scores CLAUDE.md on a rubric that includes **Currency** ("Commands work as documented · File references accurate") and prints the report before any edit (`plugins/claude-md-management/skills/claude-md-improver/SKILL.md:41-59`; `references/quality-criteria.md:63-74`). Its currency check is "Run documented commands (mentally or actually)" (`quality-criteria.md:93`), which is weak evidence when done "mentally".
- **`feature-dev` `code-explorer`** returns entry points with `file:line`, the execution flow, and "a list of files … absolutely essential to get an understanding" (`plugins/feature-dev/agents/code-explorer.md:39-51`). The orchestrator launches 2–3 in parallel and then reads the listed files itself (`plugins/feature-dev/commands/feature-dev.md:41-52`). This is a per-feature onboarding pattern.

#### 1.8 Aider repo map (structural context, not a report)
- **Produces:** a token-budgeted map of files plus "the most important classes and functions along with their types and call signatures", sent with each request (https://aider.chat/docs/repomap.html).
- **Evidence:** M. It is built with tree-sitter (https://aider.chat/2023/10/22/repomap.html) and ranked with `nx.pagerank` over a file-dependency graph, personalised toward chat files and mentioned identifiers (https://raw.githubusercontent.com/Aider-AI/aider/main/aider/repomap.py, around the `nx.pagerank` call).
- **Scale:** `--map-tokens` defaults to 1k and is adjusted dynamically (repomap.html). A binary search fits the map to the budget (repomap.py).
- **Staleness:** a tags cache `.aider.tags.cache.v{N}` keyed on file mtime, and refresh modes `auto` / `always` / `files` / `manual` (repomap.py).
- **Relevance:** codemem already uses the same idea: "SQLite-canonical storage with PageRank-budgeted JSON projection" (`packages/codemem-mcp/README.md:28`).

#### 1.9 Sourcegraph Cody
- Per-query context only, drawn from keyword search, Sourcegraph Search and "Code Graph". Admins can tune the context window, and too small a window gives "You've selected too much code" (https://sourcegraph.com/docs/cody/core-concepts/context). Not found: any persistent assessment or onboarding artefact.

#### 1.10 OpenHands
- Repo instructions live in `AGENTS.md`, which is loaded in full into the system prompt, plus progressively-disclosed skills in `.agents/skills/`. "Microagents" were renamed to skills (https://docs.openhands.dev/openhands/usage/microagents/microagents-overview).
- Issue #8976 (closed, PR #8977 merged) documented asking OpenHands to analyse the repo and write `.openhands/microagents/repo.md` (purpose, setup, structure, CI checks). The motivation was that repeated targeted searches in large repos led to "incomplete context and incorrect solutions" (https://github.com/OpenHands/OpenHands/issues/8976). This is onboarding-as-agent-memory, model-judged, with no staleness mechanism found.

#### 1.11 DeepWiki (Cognition)
- **Produces:** auto-generated wiki pages with "architecture diagrams, documentation, and source links". Effort levels are Low / Medium / High, and the higher ones are billed in ACUs (https://docs.devin.ai/work-with-devin/deepwiki).
- **Steering:** `.devin/wiki.json` with `repo_notes` (max 100 notes, 10,000 chars each) and `pages` (max 30, or 80 for enterprise). "Only the pages you define in the JSON will be generated, no more, no less" (same URL). A user-owned spec of the page set is a good fit for large repos.
- **Reuse:** a public, no-auth MCP server with `read_wiki_structure`, `read_wiki_contents` and `ask_question`. Private repos need a Devin account and API key (https://docs.devin.ai/work-with-devin/deepwiki-mcp).
- Not found in the docs fetched: its refresh / incremental policy.

#### 1.12 Google Code Wiki
- "scans the full codebase and regenerates the documentation after each change". It generates architecture, class and sequence diagrams plus a Gemini chat grounded on the wiki. It covers public repos. Private repos need a Gemini CLI extension, which is on a waitlist (https://developers.googleblog.com/introducing-code-wiki-accelerating-your-code-understanding/, 2025-11-13).

#### 1.13 CodeWiki (FSoft-AI4Code, ACL 2026) — the best-documented scaling design for onboarding docs
- **Method:**
  - Hierarchical decomposition of the dependency graph into a module tree.
  - Recursive multi-agent generation: one agent per leaf module, with "dynamic task delegation".
  - Parent pages are synthesised from child pages.
  - Diagrams are synthesised alongside the prose (https://arxiv.org/abs/2510.24428, v6 2026-04-04).
- **Evaluation:** CodeWikiBench uses rubric plus LLM-judge scoring. CodeWiki scores 68.79% vs DeepWiki's 64.06% (same URL). Even the best generator therefore misses about a third of rubric items. Model judgement also scores the output.
- **Tool** (https://github.com/FSoft-AI4Code/CodeWiki):
  - Outputs: one markdown page per module, `overview.md`, `module_tree.json`, `metadata.json`, and an optional HTML viewer.
  - `--update` "diffs the saved graph against the current code, repairs the module tree, and sends one agent per affected module to patch its page". `--compare-to <commit>` covers CI and squash merges, with fallback to a full rebuild over a threshold.
  - `update_record.json` logs every decision of the last update.
  - Scaling claim: "a 1.4M-line repository gets the same treatment as a 10k-line one".
  - Language count differs between the abstract ("seven") and the README (11 listed). Treat it as version drift.

#### 1.14 deepwiki-open (AsyncFuncAI)
- Clones repos to `~/.adalflow/repos/`, stores embeddings in `~/.adalflow/databases/`, and caches wikis in `~/.adalflow/wikicache/`. `OPENAI_API_KEY` is "required for embeddings" unless Ollama is used (https://github.com/AsyncFuncAI/deepwiki-open/blob/main/api/README.md). The code, and any secrets in it, leave the machine unless run fully local. The README fetch returned no detail on refresh or private-token handling.

### 2. Ideas for a clean-room design

#### (a) Whole-repo assessment skill
1. **Split measured from judged, and let code own the measured half.** Inventory, size, complexity, churn and hot spots, lint/scan counts, the revision stamp and the verification tally all come from tools and scripts. The model only interprets, and every claim cites `file:line` (claude-security `README.md:72`, `scan-codebase.md:70`; code-modernization `modernize-assess.md:35-36`, `:64-74`). Codemem already provides the measured structural half: `hot_spots`, `co_changes`, `layers`, `dead_code`, `blast_radius` (`packages/codemem-mcp/README.md:16-21`).
2. **Completeness ledger.** Every top-level directory is either assessed or set aside with a reason, checked before analysis. The report has a Coverage section, and lost agents are named (`scan-inventory.md:14-24`; `scan-codebase.md:112-116`).
3. **Adversarial verification before a finding is reported.** Fixed-size refute panel, confidence capped by verification, and an explicit "do not flag" list (claude-security `README.md:70-72`; code-review `code-review.md:26`, `:33-38`; security-review hard exclusions). Leave dependency CVEs to deterministic SCA rather than model judgement (security-review exclusion list).
4. **Stamp and diff.** Record the commit SHA plus a `-dirty` flag. Give findings stable IDs and emit JSONL (and optionally SARIF) beside the markdown, so a re-run reports new, fixed and persisting findings (claude-security `README.md:58-60`).
5. **Cost-aware tiers.** Ask once with a real file count before a whole-repo run. On large repos, default to an attack-surface or hot-spot focus. Chunk and resume the work (claude-security `scan-codebase.md:21-25`, `:41-45`, `:86`; modernize-map `:31-36`; Pocock `SKILL.md:20-23`).
6. **Relative indices only.** Size and complexity scores rank areas. Never print effort, dates or cost (`modernize-assess.md:45-48`).
7. **Respect recorded decisions.** Read ADRs and don't re-litigate them. Offer to record a rejected finding so later runs don't repeat it (Pocock `SKILL.md:56`, `:70`). The forge already ships ADRs and `CONTEXT.md`.

#### (b) Onboarding skill
1. **Graph-first, hierarchical.** Build or reuse the dependency graph (codemem, or the stack's own tooling read as machine-readable output), decompose it into modules, write leaf pages from code packets and parent pages from children (CodeWiki; modernize-map `:13-28`).
2. **Grounding check in code.** Every identifier and number in generated prose must occur in its source packet. Re-ask once, then drop the prose (`modernize-map.md:128-146`). This is a cheap, deterministic anti-hallucination gate.
3. **Commit-keyed staleness and incremental update.** Stamp each page with the commit SHA and regenerate only modules whose files changed since then (CodeWiki `--update` / `--compare-to`; codemem already tracks `.codemem/last_sha`, `packages/codemem-mcp/src/codemem/incremental.py:9-10`). The current `understand-codebase` compares against `git log -1 --format=%cd`, a date (`claude-code/skills/understand-codebase/SKILL.md:97`), which is the weaker form GSD also uses.
4. **User-owned steering file** listing the pages and notes to generate, with hard caps (DeepWiki `.devin/wiki.json`).
5. **Separate the human doc from agent memory.** Keep the onboarding doc rich. Keep any generated CLAUDE.md or AGENTS.md short and limited to what cannot be inferred from code (best-practices page). Check currency by *running* the documented build and test commands, not "mentally" (`quality-criteria.md:93`).
6. **Budgeted, machine-readable companion.** A JSON index with per-file token budgets and PageRank-ranked importance, next to the prose (gsd-intel `:268-279`; Aider; codemem `README.md:28`), so planners can consume it without reading prose (GSD `why_this_matters`, `gsd-codebase-mapper.md:40-71`).
7. **Q&A beats a static doc for depth.** Pair a thin orientation doc with a queryable surface. DeepWiki `ask_question` and Code Wiki chat both do this, and the forge's equivalent is the codemem MCP tools.

### 3. Pitfalls to design against
- **Gap-finding reviewers always find gaps.** Without a refute step and a "do not flag" list, the output pads itself (best-practices page; code-review `:33-38`).
- **Secret leakage.** A deny-list plus a regex grep over the output catches only known token shapes (`map-codebase.md:285`). Redaction by a model is "best effort, not a guarantee" (claude-security `README.md:62`). Use layers: don't read secret files, mask at source, write any credential inventory only to a verified-ignored file (`modernize-assess.md:117-131`), then redact and regex-gate. Never commit reports by default: GSD commits (`map-codebase.md:313-318`), while claude-security writes its own `.gitignore` (`README.md:64`).
- **Silent truncation.** `head -N` caps (`gsd-codebase-mapper.md:106-151`) and "top 50-100 files" budgets (`gsd-intel-updater.md:279`) hide unexamined code unless a coverage ledger names it.
- **Date or age staleness.** "Analysis Date" and "older than 24 hours" (`gsd-intel/SKILL.md:102`) do not say whether the code changed. Use the commit SHA.
- **Diff-scoped agents on a whole repo.** Anthropic's code-review and security-review are diff-only by design, and so is the forge `code-reviewer` (`claude-code/agents/code-reviewer.md:14`, `:21`). A whole-repo skill needs its own whole-repo reviewers or an inventory → per-component dispatch (claude-security shape).
- **Prompt injection from the repo under review.** Treat code, comments and CLAUDE.md as data (`scan-inventory.md:26-28`). Escape untrusted strings before HTML injection (`modernize-map.md:164-168`). Avoid unpinned CDN scripts and mermaid `securityLevel: "loose"` over model output (Pocock `HTML-REPORT.md:13-16`, versus the forge's pinned, strict `html.py:15-23`).
- **Nondeterminism.** Two runs differ (claude-security `README.md:76`). Stable finding IDs and a run-over-run diff turn that into coverage instead of noise.
- **Misread metrics.** COCOMO and similar numbers get read as schedules or cost (`modernize-assess.md:45-48`).
- **Code leaves the machine.** Hosted or embedding-based generators need public repos or third-party API keys (DeepWiki MCP public-only; deepwiki-open requires `OPENAI_API_KEY`; Code Wiki is public-repo only).
- **The skill drifts from its own agents.** gsd-intel's skill/agent file-name mismatch (`gsd-intel/SKILL.md:145` vs `gsd-intel-updater.md:94-149`). Pin skill↔agent contracts with a test, as the forge already does for counts.

## Not pursued
- claude-security `scan-changes`, `suggest-patches`, `specs/report-spec.md` internals (JSONL field schema, finding-ID derivation) — read only README, scan-codebase job, inventory and redactor agents; the ID derivation is worth a follow-up if (a) adopts stable IDs.
- code-modernization's other commands (`modernize-brief`, `-harden`, `-extract-rules`, `-preflight`) and the `workflows/portfolio-assess.js` script — outside assess/map.
- The divergence between upstream `anthropics/claude-code` code-review (4 agents + validators) and the installed `claude-plugins-official` copy (5 Sonnet + score ≥80) — not reconciled; both cited as-is.
- deepwiki-open refresh behaviour and private-token handling — the README fetch returned no detail.
- DeepWiki refresh cadence — not in the docs page fetched.
- CodeWikiBench rubric contents and per-language scores — abstract only.
- Academic evaluations of doc-generation hallucination (arXiv 2606.09852, 2409.20550) — seen in search results, not read.
- AGENTS.md cross-tool standard (agents.md) — not fetched; OpenHands docs cover its loading semantics.
- `claude-code-setup` automation recommender and the official LSP "code intelligence" plugins — adjacent (tooling setup and navigation), not assessment or onboarding.
- Local `code-intelligence` / `code-intelligence-index` / `gsd-graphify` skills — read headers only; they answer structural queries rather than produce assessments, and graphify is config-gated.
- GitNexus / Axon code-graph MCPs (named in `docs/codemem/kill-criteria.md:58`) — code-intel competitors, not assessment or onboarding flows.
- Repomix / gitingest-style context packers — not surveyed.
- `cc-marketplace` `enterprise-onboarding-specialist` — a false friend: customer or organisational onboarding, with no codebase content (`~/.claude/plugins/marketplaces/cc-marketplace/plugins/enterprise-onboarding-specialist/agents/enterprise-onboarding-specialist.md:1-3`).
- Google Code Wiki's Gemini CLI extension for private repos — waitlist only, no docs.
