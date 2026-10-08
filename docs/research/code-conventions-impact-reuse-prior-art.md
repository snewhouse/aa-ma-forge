# What reusable code exists today, and how do others curate and graduate it?

**Created:** 2026-10-08
**Author:** aa-ma-researcher (Claude), for chart effort `code-conventions-impact` (Ticket 5)
**Reviewed-Through-Date:** 2026-10-08 (local trees read at aa-ma-forge `4ad4619`, one private Carmen repo, medical-research-skills; web sources fetched the same day)
**Valid-Through:** 2026-Q4 (invalidated by: new Carmen repos under `~/dev/carmen-provenance-labs/`, a bulk skill install/sync into `~/.claude/skills/`, extraction of any helper listed in Part A, or a uv/copier major release)
**Sources:**
- `~/.claude/skills/*` (local, 324 entries; `gstack/` and `synced/` treated as third-party) — inventory of code-carrying skills
- `~/.claude/skills/deslop-shared-libs/SKILL.md:26-28,159-185` (lines 160, 167, 171-174, 184 quoted) — gstack's existing extraction rubric (prove 2 callers, reuse first, keep small)
- `~/.claude/bin/*.sh`, `~/.claude/hooks/lib/` — local utility directories
- `~/dev/carmen-provenance-labs/` — the two private Carmen repos (confidential: neither names nor contents are recorded here)
- `src/aa_ma/**`, `packages/codemem-mcp/src/codemem/**`, `tests/**`, `scripts/*.sh` (this repo) — in-repo duplication
- `src/aa_ma/forks.py:1-29`, `claude-code/skills/FORKS.json`, `scripts/fork-drift.sh:6` — existing provenance/drift mechanism
- https://docs.astral.sh/uv/concepts/projects/workspaces/ — uv workspaces
- https://docs.astral.sh/uv/concepts/indexes/ — uv private/explicit indexes, dependency-confusion default
- https://docs.astral.sh/uv/concepts/projects/dependencies/ — uv git/path sources
- https://copier.readthedocs.io/en/stable/updating/ — copier update mechanism
- https://cruft.github.io/cruft/ — cookiecutter + cruft update/check
- https://git-scm.com/book/en/v2/Git-Tools-Submodules — submodule model and pitfalls
- https://github.com/git/git/blob/master/contrib/subtree/git-subtree.adoc — git subtree
- https://docs.github.com/en/get-started/writing-on-github/editing-and-sharing-content-with-gists/creating-gists — gists
- https://patterns.innersourcecommons.org/p/{30-day-warranty,trusted-committer,base-documentation,innersource-portal}.md — InnerSource patterns
- https://semver.org/ — SemVer rules 1, 4, 8 and FAQ
- https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction — counterweight to early extraction
- https://www.hyrumslaw.com/ — Hyrum's Law
- https://en.wikipedia.org/wiki/Rule_of_three_(computer_programming) — **secondary**; rule of three (primary is Fowler, *Refactoring*, ch. 2, not read online)
- https://arxiv.org/abs/1903.12282 — snippet obsolescence evidence (Stack Overflow)
- https://docs.python.org/3/library/doctest.html — executable examples
- https://packaging.python.org/en/latest/specifications/inline-script-metadata/ — PEP 723 single-file scripts
- https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview — skill progressive disclosure, scripts run without entering context
- https://modelcontextprotocol.io/specification/2025-06-18/server/resources — MCP resources

## Answer

Reusable code today lives almost entirely as **prose snippets inside global skill `references/*.md`** (3,037 Python fences across non-vendored skills; 65 skills carry ≥10) plus a few executable `scripts/`. None of it is packaged, versioned or shared by import. The same helpers recur: HTTP retry/rate-limiter in ~14 skills, logging setup in 6, Ensembl/ID validation in 3–4, NCBI/Open Targets/UniProt clients in 3–4 each. A git-HEAD/provenance helper is hand-rolled 6 times across this repo and the one Carmen Python repo, with inconsistent safety. Prior art agrees on three things. Don't extract before 2–3 real callers (rule of three; Metz's warning about the wrong abstraction). Pick a distribution mechanism that has an update story: uv workspace or git/index source for libraries, copier for scaffolds; gists, submodules and plain copies have none. Keep a collection alive with executable tests, provenance pins and a named owner. The candidate graduation criteria below list options and trade-offs; nothing is decided.

## Evidence

### Part A — Inventory

#### A1. Global skills that carry code (`~/.claude/skills/`)

- **The three named skills hold no executable code.**
  - `pharma-use-case-library` is SKILL.md plus 4 `references/*.md` with about 160 code fences, mostly untagged and some `graphql` (`~/.claude/skills/pharma-use-case-library/references/pharma-target-discovery.md`, `…/pharma-literature-biomarkers.md`).
  - `terraform-module-library` is SKILL.md (249 lines: 4 `hcl` fences, 1 `go`) plus `references/aws-modules.md`, which has no fences.
  - `deslop-shared-libs` is a gstack-owned procedure (`.gstack-owned` marker), not a library. It is an AI *finder* of extraction candidates and itself prior art: "Find up to five new opportunities to share code, then recommend the best three" (`~/.claude/skills/deslop-shared-libs/SKILL.md:26`). Its rubric "Require at least two verified, first-party authored source locations" (`:160`). It says "Reuse before extracting" (`:167`) and "Keep the helper small … describe the blast radius of a shared failure" (`:171-174`).
- **Skills with executable `scripts/`** (own or forked, excluding gstack/synced):
  - biomedical: `biomedical-database-mashup/scripts/{clinvar_gene_summary,verify_live}.py`, `opentargets-platform/scripts/validate_ot_queries.py`, `clinicaltrials-database/scripts/query_clinicaltrials.py`, `literature-review/scripts/{search_databases,verify_citations,generate_pdf}.py`
  - docs/reporting: `templated-reports/scripts/{ingest,render,_brandkit}.py`, `doc-auto-render/scripts/render-docs.py` (+ `tests/test_render.sh`), `markitdown/scripts/batch_convert.py`
  - generic: `prompt-factory/scripts/*.py`, `senior-{devops,architect,fullstack,secops}/scripts/*.py`, `mcp-builder/scripts/{evaluation,connections}.py`, `webapp-testing/scripts/with_server.py`, `root-cause-tracing/find-polluter.sh`, `doc-drift-detection/scripts/analyze-skip-history.sh`
  - template-style: `chunking-strategies-rag/{templates,examples}/**.py` (10 files), `slack-app-development/templates/*.py`, `glab-gitlab-cli/templates/aa-ma-sync/*`
- **Code-heavy references** (most Python fences): `gseapy` 140, `pydantic-ai-development` 117, `alembic-migrations` 115, `sqlalchemy-orm` 98, `opensearch-elasticsearch` 97, `markitdown` 94, `justhtml` 87, `fastmcp-development` 81, `langchain-development` 76, `python-testing-patterns` 75. Biomedical: `biomart` 58, `arangodb-biomedical` 54 (count via `grep -c '^```python'`, 2026-10-08).
- **Two skills already self-test their embedded code against live APIs.**
  - `biomedical-database-mashup/scripts/verify_live.py` describes itself as a "Live check: every helper added to biomedical-database-mashup, and every call site that uses them". It is a PEP 723 script with `dependencies = ["httpx"]`.
  - `opentargets-platform/scripts/validate_ot_queries.py` will "Validate every GraphQL document embedded in markdown files against the live Open Targets schema … Exit 1 if any document fails".
- **Vendored copies inside the Anthropic-synced skills.** `~/.claude/skills/synced/<uuid>/{docx,pptx,xlsx}/scripts/office/{validate.py,soffice.py,helpers/*,validators/*}` are byte-identical in 3 places (md5, 11 file groups).
  - `mcp-builder/scripts/{evaluation,connections}.py` is byte-identical to its `synced/` twin.
  - `xlsx/recalc.py` **differs** from `synced/<uuid>/xlsx/scripts/recalc.py`. That is copy drift.

#### A2. Snippet/utility directories under `~/.claude`

- `~/.claude/bin/`: backup and restore shell scripts. `restore-lib.sh:15-18` is already an extracted shared lib (`log_ok/log_warn/log_step/log_err`) used by `restore-{linux,macos,wsl}.sh` and shipped by `claude-migrate-capture.sh:616`. However, `claude-migrate-capture.sh:122-124` re-defines the same `log_ok/log_warn/log_step`, and `claude-backup.sh:130-142`, `claude-restore.sh:62-74`, `claude-mem-backup.sh:55-57` and `fix-claude-mem-pm2.sh:60-78` each define their own `log_info/log_warn/log_error/log_debug`.
- `~/.claude/hooks/lib/`: `aa-ma-parse.sh` and `aa-ma-chart-guard.sh` are symlinks into this repo's `claude-code/hooks/lib/` (`readlink`, byte-identical). This is a working "graduated shell module" distributed by `scripts/install.sh`, and is sourced by 8 hooks/scripts (`grep -l aa-ma-parse.sh claude-code/hooks scripts`).
- `~/.claude/mods/aa-ma-band`, `~/.claude/dev-mods/`: not code libraries (not inspected further).
- No dedicated snippet directory (`snippets/`, `lib/` for Python) exists under `~/.claude`.

#### A3. Carmen Provenance repos (`~/dev/carmen-provenance-labs/`)

- Two private repos; one contains Python. Their contents are confidential and are not recorded in this public repo. Its utility-type helpers (a git-HEAD/status provenance call, a config hash, config loading, argparse CLIs) are counted below as "Carmen" without paths.
- **One Python Carmen repo means cross-Carmen duplication cannot yet be measured.** Cross-project duplication shows up between this repo, Carmen and the skills instead.

#### A4. This repo (`src/` vs `packages/`)

- Layout: `pyproject.toml:59-65` declares a uv workspace with member `packages/codemem-mcp`, sourced `{ workspace = true }`.
- Dependency direction: `codemem` imports `aa_ma` only behind `try/except ImportError` "so standalone pip install codemem-mcp works without the parent framework" (`packages/codemem-mcp/src/codemem/aa_ma_integration.py:14-20`). A helper shared by both can therefore not live in `aa_ma` without breaking codemem's standalone contract.
- No `logging.basicConfig` anywhere in `src/` or `packages/`. Five modules use `getLogger(__name__)` (`src/aa_ma/gate.py:63` and others).

#### A5. Duplicated utilities

| Utility | Where (paths) | Copies | Notes |
|---|---|---|---|
| Run `git` / read HEAD SHA (provenance stamp) | `src/aa_ma/analysis/stamp.py:160 run_git`; `packages/codemem-mcp/src/codemem/analysis/git_mining.py:80 _git`; `…/codemem/indexer.py:481` (inline); `…/codemem/incremental.py:302 _write_last_sha`; `…/codemem/draw/views.py:202 _head_sha`; 1 private Carmen helper | 6 | **Divergent safety**: only `stamp.py` uses `safe_env()` + `GIT_TIMEOUT_S = 300` (`stamp.py:66,107,168`). `git_mining` uses a 30 s timeout. The other four have no timeout or env scrubbing. Strongest real-code candidate, but crosses the codemem standalone boundary (A4). |
| Content / config hash (sha256) | `src/aa_ma/goal_synthesis.py:152`, `src/aa_ma/analysis/ids.py:21`, `src/aa_ma/render/html.py:29`, `codemem/parser/python_ast.py:160`, `codemem/incremental.py:265`, `codemem/indexer.py:162,193`; 1 private Carmen helper | 8 | Stdlib one-liners with different normalisation. Likely *not* worth extracting (Metz, B1). |
| CLI scaffold `main(argv) -> int` + argparse | `src/aa_ma/{gate.py:452,deps.py:142,analysis/cli.py:388,tui/__main__.py:121}`, `src/aa_ma/render/cli.py`, `codemem/cli.py:358 build_parser,:447 main`; 4 private Carmen CLIs | ~11 | A pattern, not shared code. Better served by a template (copier) than a library. |
| Shell log helpers `info/warn/error/header` | `scripts/install.sh:33-36`, `scripts/uninstall.sh:32-35` (same text); `~/.claude/bin/` 6 scripts (A2) | 8 | One local precedent of extraction (`restore-lib.sh`) that was only partly adopted. |
| YAML frontmatter split (tests) | `tests/test_frontmatter_at_top.py:41`, `tests/skills/_helpers.py:20`, `tests/agents/_helpers.py:10`, `tests/commands/test_understand_codebase_command.py:23`, `tests/agents/test_codebase_onboarding_agents.py:34`, `tests/commands/test_aa_ma_share_command.py:22` | 6 | Two per-directory `_helpers.py` already exist but disagree on signature (`text`→`(str,dict)` vs `path`→`(dict,str)`). |
| Python logging setup | `logging-and-comments/references/python.md:13 configure_logging` (canonical standard); `bgee/references/production-patterns.md:513`; `hpa/references/production-patterns.md:300 setup_hpa_logging`; `biomart/…/production-patterns.md`; `web-scraper/…/production-patterns.md`; `professional-jupyterlab/references/notebook-architecture.md` | 6 (snippets) | Per-skill variants of the canonical one. No code repo copy found. |
| HTTP retry/backoff + rate limiter | `fetch_with_retry` at `biomart/…/production-patterns.md:32`, `bgee/…/production-patterns.md:188`; `class RateLimiter` at `bgee:330`, `hpa:477`, `biomart:627`, `ols-api/references/query-patterns.md:411`, `api-design-principles/references/rest-best-practices.md`, `justhtml/references/web_scraping_patterns.md`, `web-scraper/SKILL.md`; executable `biomedical-database-mashup/scripts/clinvar_gene_summary.py:36-47 eutil` (exponential backoff) | 14 skills mention retry; 7 `RateLimiter` classes | Only the clinvar script is executable and self-tested (`_selftest`). The rest are untested prose. |
| NCBI E-utilities / PubMed client | `biomedical-database-mashup/scripts/clinvar_gene_summary.py:21`, `pharma-use-case-library/references/*`, `chainlit-chat-apps`; third-party fork `~/projects/github_private/medical-research-skills` (AIPOCH, `README.md:4`) has `def search_pubmed(` **10×** and `esearch` 3× | 3 skills + 10 forked | The AIPOCH fork shows the end state of copy-per-skill vendoring. |
| Open Targets GraphQL | `opentargets-platform/scripts/validate_ot_queries.py:16`, `biomedical-database-mashup`, `streamlit-data-apps` | 3 | The validator could cover all three. Today it runs per file given. |
| UniProt / Ensembl REST, ID mapping/validation | UniProt: `bgee`, `biomart`, `biomedical-database-mashup`, `pharma-use-case-library`. Ensembl REST: `biomart`, `biomedical-database-mashup`, `pharma-use-case-library`. ID-map defs: `biomart`, `biomedical-database-mashup`, `hpa`, `opentargets-platform`. Ensembl-ID validators: `bgee/…:482`, `hpa/…:257`, `hpa/references/python-api.md`. AIPOCH fork: `string_map_ids`, `map_ids`, `map_identifiers`, `map_id` | 3–4 skills each | Biomedical "ID mapping" is the domain helper most often reinvented. |
| Config loading (`BaseSettings`/`load_dotenv`) | `dspy-development`, `fastapi-templates`, `hpa`, `system-mapping` (snippets); 1 private Carmen helper | 4 + 1 | Low reuse in real code. |
| Office (docx/pptx/xlsx) helpers | `~/.claude/skills/synced/<uuid>/{docx,pptx,xlsx}/scripts/office/**` | 3× per file | Upstream (Anthropic) chose to vendor rather than share. `xlsx/recalc.py` already drifted from its synced twin. |

#### A6. Internal prior art already in place

- **Provenance + drift classification for vendored content.**
  - `claude-code/skills/FORKS.json` is "the SSoT for every forked skill". Each row has `upstream`, `upstream_sha`, `forked_at`, `adr`, `state`, `files` and `upstream_md5` (`src/aa_ma/forks.py:1,21-29`).
  - Verdicts are `SAME | DRIFT | ORPHAN` (`forks.py:17`).
  - `scripts/fork-drift.sh` is "the ONLY place" that fetches upstream (`scripts/fork-drift.sh:6`).
  - The same schema could carry snippet provenance.
- **Symlinked shell lib**: `claude-code/hooks/lib/aa-ma-parse.sh` deployed to `~/.claude/hooks/lib/` (A2).
- **Workspace member**: `packages/codemem-mcp` (`pyproject.toml:59-65`).
- **Live validators of embedded snippets**: `verify_live.py`, `validate_ot_queries.py` (A1).

### Part B — Prior art

#### B1. When to extract

- **Rule of three** (**secondary source**): the rule is attributed to Don Roberts and popularised in Fowler's *Refactoring*. "Two instances of similar code do not require refactoring, but when similar code is used three times, it should be extracted" (https://en.wikipedia.org/wiki/Rule_of_three_(computer_programming)). The primary text (Fowler, *Refactoring*, 2nd ed. 2018, ch. 2 "When Should We Refactor?") was not read online. The only full-text hits were unauthorised PDFs and were not used.
- **Counterweight**: "duplication is far cheaper than the wrong abstraction". The remedy: "Re-introduce duplication by inlining the abstracted code back into every caller" (https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction). The failure mode is a shared helper accreting parameters and conditionals for near-fit callers.
- **Hyrum's Law** says shared code's real contract is wider than its declared one: "all observable behaviors of your system will be depended on by somebody" (https://www.hyrumslaw.com/).
- **Local tooling uses 2, not 3.** `deslop-shared-libs` requires "at least two verified, first-party authored source locations" and to "Reject similarities with incompatible contracts" (`~/.claude/skills/deslop-shared-libs/SKILL.md:160,184`).

#### B2. Distribution mechanisms and their update story

| Mechanism | How consumers get updates | Trade-offs | Cite |
|---|---|---|---|
| Copy-paste snippet (skill `references/`) | None. Manual re-copy. | Zero setup; drift is invisible (A5 office/recalc) | A1, A5 |
| PEP 723 single-file script | Re-copy, but deps are declared in-file (`# /// script … dependencies`) and runnable with `uv run` | Self-contained and testable; still a copy | https://packaging.python.org/en/latest/specifications/inline-script-metadata/ |
| GitHub gist | Each gist "is a Git repository, which means that it can be forked and cloned". Updates are pulled manually. | "Secret gists aren't private": **unsuitable for client-derived code**. Public ones are searchable. | https://docs.github.com/en/get-started/writing-on-github/editing-and-sharing-content-with-gists/creating-gists |
| git submodule | Superproject pins a commit. Clone needs `--recurse-submodules`. Pull "does not **update** the submodules". | Detached-HEAD lost commits, forgotten pushes, branch-switch surprises | https://git-scm.com/book/en/v2/Git-Tools-Submodules |
| git subtree | `subtree pull/merge` into a prefix. `split/push` sends changes back. "subtrees do not need any special constructions". | Consumers need no tooling. History noise (`--rejoin`), split consistency caveats. | https://github.com/git/git/blob/master/contrib/subtree/git-subtree.adoc |
| uv path / git source | `{ path = "../x", editable = true }`, or `{ git = …, tag = "0.27.0", subdirectory = … }`. Bump the tag to update. | "Sources are only respected by uv". Publish with `uv build --no-sources`. | https://docs.astral.sh/uv/concepts/projects/dependencies/ |
| uv workspace | Shared lockfile, editable members, `{ workspace = true }` | Single `requires-python`. "uv cannot stop one member from importing another member's undeclared dependencies". Poor fit when members conflict. | https://docs.astral.sh/uv/concepts/projects/workspaces/ |
| Private index | `[[tool.uv.index]]` with `explicit = true` pins a package to it. Version-range upgrades. | Default `first-index` strategy prevents "dependency confusion". Credentials via `UV_INDEX_<NAME>_*` and never in `uv.lock`. Needs hosting. | https://docs.astral.sh/uv/concepts/indexes/ |
| copier template | `copier update` regenerates from the latest git tag, diffs, reapplies your diff, and marks conflicts `inline` or `.rej`. "**Never** update `.copier-answers.yml` manually." | Real update path for scaffolds. Needs a tagged template repo and a clean git destination. | https://copier.readthedocs.io/en/stable/updating/ |
| cookiecutter (+ cruft) | Cookiecutter alone: regenerate (per cruft's framing). `cruft update` records the template commit in `.cruft.json`. `cruft check` exits 1 when behind, for CI. | Bolt-on update. Cookiecutter docs not checked directly. | https://cruft.github.io/cruft/ |

#### B3. InnerSource Commons patterns relevant to a one-person-plus-AI library

- **Standard Base Documentation**: README with a mission so contributors can "make a good first guess whether a suggested feature will likely be in scope", plus CONTRIBUTING and COMMUNICATION (https://patterns.innersourcecommons.org/p/base-documentation.md).
- **InnerSource Portal**: an index of reusable projects. Metadata comes from each repo, and SAP's implementation uses GitHub topics for self-registration (https://patterns.innersourcecommons.org/p/innersource-portal.md).
- **30 Day Warranty**: the contributor fixes bugs for a period after contributed code reaches production (https://patterns.innersourcecommons.org/p/30-day-warranty.md). The analogue here is "the project that donates a helper keeps it green for N days".
- **Trusted Committer**: named, documented owners. "What a Trusted Committer handles is up to each project and its maintainers" (https://patterns.innersourcecommons.org/p/trusted-committer.md).

#### B4. Versioning the library tier

- SemVer: "Software using Semantic Versioning MUST declare a public API". "Major version zero (0.y.z) is for initial development. Anything MAY change at any time." Major "MUST be incremented if any backward incompatible changes are introduced".
- FAQ: "If your software is being used in production, it should probably already be 1.0.0". Deprecation needs "at least one minor release that contains the deprecation" (https://semver.org/).
- This repo already owns versioning via commitizen (`scripts/release.sh`, per `CLAUDE.md`). A workspace member could reuse that pipeline.

#### B5. What keeps a snippet collection from rotting

- **Evidence of rot.** In Stack Overflow, "More than half of the obsolete answers (58.4%) were probably already obsolete when they were first posted". When obsolescence is observed, "only a small proportion (20.5%) of such answers are ever updated" (https://arxiv.org/abs/1903.12282). Untested prose snippets behave the same way. In A5, ~14 skill copies of retry code have no test.
- **Executable examples**: doctest exists "To check that a module's docstrings are up-to-date by verifying that all interactive examples still work as documented" (https://docs.python.org/3/library/doctest.html). There are local equivalents for markdown fences (`verify_live.py`, `validate_ot_queries.py`, A1).
- **Provenance pins**: upstream + SHA + per-file md5 + drift verdict (`src/aa_ma/forks.py:21-29`). For client-derived code, the chart's own constraint says it is "confidential until genericized" (`.claude/dev/charting/code-conventions-impact/code-conventions-impact-map.md:18`). The gist privacy caveat (B2) rules gists out for it.
- **Ownership**: Trusted Committer / 30-day warranty (B3) and gstack's `.gstack-owned` marker (`~/.claude/skills/gstack/bin/gstack-relink:100`), which records who may delete or relink an entry.
- **Discoverability**: an index with metadata (InnerSource Portal, B3) and the AI-facing mechanisms in B6.

#### B6. How an AI coding assistant discovers and reuses a curated collection

- **Skill with references/scripts.** Metadata costs "~100 tokens per Skill" and is always loaded. SKILL.md loads on trigger. References load only when read. Scripts "run through bash, and only their output enters context". The doc calls this "far more efficient than having Claude generate equivalent code on the fly". Skills can be "shared through Claude Code Plugins" (https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview).
  - Implication: an executable, tested helper in `scripts/` is cheaper and more reliable than a prose snippet. But when code is meant to be *imported*, Claude must read it into context or install it as a package.
- **MCP resources.** Servers expose URI-identified context via `resources/list` and `resources/read`, with annotations such as `priority` and `lastModified`. Resources are "application-driven", so the host decides inclusion (https://modelcontextprotocol.io/specification/2025-06-18/server/resources). A snippet library could be served as `snippet://` resources, or as a search tool.
- **Search index.** This environment already has `project-index` (`who_calls`, `search_symbols`) and codemem for symbol search within a repo (`~/.claude/rules/project-index-awareness.md`). Neither indexes across repos or skills today; this was not verified beyond its tool list.

### Candidate graduation criteria (options only, not decided)

**Tiers.**
- **Snippet**: a fenced block in a skill reference, or a PEP 723 script.
- **Module**: a file inside one repo, or a symlinked shell lib, with tests.
- **Library**: a versioned package (workspace member, git-tag source or index).

| Gate | Option | Trade-off |
|---|---|---|
| Snippet → module: reuse count | (a) 2 verified callers (deslop rubric) | (a) catches drift earlier, but risks the wrong abstraction (Metz) |
| | (b) 3 callers (rule of three) | (b) is safer on abstraction, but tolerates more drift (A5 git helper already at 6) |
| Snippet → module: test | (a) doctest/pytest on the snippet | (a) is cheap, but tests prose not callers |
| | (b) live validator over all markdown fences (`validate_ot_queries.py` pattern) | (b) catches API drift, but needs network and is flaky |
| | (c) caller-integration test (deslop `:173-174`) | (c) is strongest and costliest |
| Snippet → module: confidentiality | (a) explicit "genericized" attestation field | (a) is auditable, but manual |
| | (b) lives only in a private repo until genericized | (b) is simpler, but limits discoverability |
| Snippet → module: provenance metadata | (a) FORKS.json-style row (origin, SHA, md5, owner, licence, date) | (a) supports drift detection (`forks.py` verdicts) at extra maintenance cost |
| | (b) header comment only | (b) is zero tooling, but unverifiable |
| Module → library: consumer count | (a) ≥2 *repos* (not callers) | (a) avoids packaging single-repo code; Carmen has only 1 Python repo today (A3), so few items qualify |
| | (b) ≥1 repo + skills | (b) allows earlier publishing |
| Module → library: contract stability | (a) public API declared, 0.y.z until used in production (SemVer rule 4/FAQ) | (a) is honest about churn |
| | (b) start at 1.0.0 | (b) commits early to deprecation discipline |
| Module → library: dependency weight / boundary | (a) stdlib-only helpers go in a tiny core package | (a) respects boundaries such as codemem's standalone contract (A4) |
| | (b) domain helpers (biomedical clients, ID mapping) in separate packages | (b) adds packages to version |
| Module → library: ownership | (a) named owner + N-day warranty for donor (InnerSource) | (a) is overhead for a solo consultant |
| | (b) owner = repo maintainer, implicit | (b) is invisible when projects end |
| Distribution per tier | Snippet: skill refs / PEP 723 | Weakest update story |
| | Scaffold: copier | Real 3-way update |
| | Library: uv workspace (same repo) → git-tag source → private index | Rising set-up cost, rising isolation. Gists and submodules are the weakest on privacy and ergonomics respectively (B2). |
| AI discoverability | (a) one `snippets`/`reuse` skill whose references index the collection | (a) is cheapest and works today |
| | (b) scripts executed via bash | (b) costs no context but is not importable |
| | (c) MCP server exposing resources/search | (c) works across repos, at the cost of running a server |
| | (d) rely on codemem/project-index | (d) is per-repo only |

**Demotion path (Metz):** a library helper that gains option flags for near-fit callers is inlined back to callers. This is a graduation criterion in reverse.

## Not pursued

- `~/.claude/_archive/biorelate/**` (archived galactic-* skills): skipped per caller's confidentiality instruction.
- Other personal repos under `~/projects/github_private/` (e.g. `repowise`; others not named): only `medical-research-skills` was sampled. A wider cross-repo duplicate scan is a follow-up.
- `gstack/` (11,787 code files) and `synced/` internals beyond md5 duplicate detection: these are third-party and not curated by Ste.
- Near-duplicate (non-identical) detection by AST similarity (e.g. codemem or `jscpd`): only name/grep and md5 matching were used, so near-copies with different names are under-counted.
- Fowler *Refactoring* primary text: not available online legitimately. Secondary source used and flagged.
- Copier `_commit`/`_src_path` answers-file keys: the updating page does not document them, so the template-version tracking detail was left uncited.
- Cookiecutter's own docs on (lack of) update: only cruft's framing was read.
- InnerSource "Service vs. Library" and "Maturity Model" patterns: URLs found (https://patterns.innersourcecommons.org/p/service-vs-library.md), not read.
- Private index hosting options (devpi, GitHub Packages for Python, Gemfury, AWS CodeArtifact): not compared.
- SPDX/REUSE licence metadata for snippets: not fetched.
- MCP servers already connected in this environment (ChEMBL, ClinicalTrials.gov, bioRxiv, Amass) as a *substitute* for hand-written biomedical clients: not inventoried.
- Page contained instructions: the MCP resources page and the InnerSource introduction both told agents to fetch an `llms.txt` index. The MCP one was ignored. The InnerSource `llms.txt` was fetched once, by my own choice, only to resolve pattern URLs.
