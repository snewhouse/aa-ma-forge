# Which portable, optional tools measure a whole-repo codebase assessment's metrics, and how should the assessment degrade without them?

**Created:** 2026-09-27
**Author:** aa-ma-researcher (Claude), for charting effort `codebase-analysis-skills`, map Ticket 4
**Reviewed-Through-Date:** 2026-09-27 (tool docs, PyPI and npm registry metadata fetched on this date; local `--help` from the versions installed on BATS)
**Valid-Through:** 2026-Q4 (invalidated by a major CLI change in any of these tools, e.g. gitleaks `detect`→`git`/`dir`, jscpd's move to Rust, `uv audit` leaving its current shape, or a change to `/sole-dev-merge` Stage C)
**Sources:**
- `claude-code/commands/sole-dev-merge.md:334-431` — Stage C scanner contract: `*_BIN` seams, result-based degraded check, `[HIGH] … UNKNOWN` into `$FINDINGS`
- `tests/commands/sole-dev-merge/test_stage_c_dispatch.bats:114-171` — the degraded-scanner test (3 modes × 2 scanners, can never skip)
- `.github/workflows/security.yml:72-80,103-107` — CI installs both scanners and asserts `--version`
- `docs/lessons.md:337-381` (L-012), `docs/lessons.md:78-97` (L-024) — why UNKNOWN is never PASS, and why an always-UNKNOWN check is also a defect
- `src/aa_ma/render/mermaid_lint.py:505-512` — second in-repo precedent (`MMDC_BIN` seam → PASS/FAIL/UNKNOWN)
- `packages/codemem-mcp/src/codemem/mcp_tools/__init__.py:260,442,508,613,777` — codemem `dead_code`, `hot_spots`, `co_changes`, `owners`, `symbol_history`
- `packages/codemem-mcp/pyproject.toml:24`, `pyproject.toml:47,51` — ast-grep-cli pinned as a codemem dependency; pytest-cov and ruff as dev dependencies
- https://github.com/terryyin/lizard, https://raw.githubusercontent.com/terryyin/lizard/master/LICENSE.txt, https://pypi.org/pypi/lizard/json — lizard
- https://radon.readthedocs.io/en/latest/commandline.html, https://pypi.org/pypi/radon/json — radon
- https://github.com/kucherenko/jscpd, https://registry.npmjs.org/jscpd/latest — jscpd
- https://github.com/pypa/pip-audit, https://pypi.org/pypi/pip-audit/json — pip-audit
- https://docs.npmjs.com/cli/v11/commands/npm-audit — npm audit
- https://github.com/google/osv-scanner, https://google.github.io/osv-scanner/output/, https://google.github.io/osv-scanner/usage/offline-mode/ — osv-scanner
- https://docs.semgrep.dev/supported-languages, https://pypi.org/pypi/semgrep/json — semgrep
- https://bandit.readthedocs.io/en/latest/start.html — bandit
- https://github.com/ast-grep/ast-grep, https://ast-grep.github.io/reference/languages.html, https://ast-grep.github.io/guide/quick-start.html — ast-grep
- https://github.com/gitleaks/gitleaks — gitleaks
- https://github.com/trufflesecurity/trufflehog — trufflehog
- https://github.com/aboutcode-org/scancode-toolkit, https://pypi.org/pypi/scancode-toolkit/json — scancode
- https://github.com/licensee/licensee, https://github.com/licensee/licensee/blob/main/docs/command-line-usage.md — licensee
- https://github.com/boyter/scc — scc (added: multi-language LOC, file-level complexity estimate, ULOC/DRYness)
- Local, read-only: `command -v`, `--version`, `--help` for every tool listed below, plus timed runs on this repo (659 tracked files, 180 `.py` / 32,180 Python lines, 731 commits)

## Answer
Every metric has a portable, optional CLI, but no single one covers them all. The best multi-language picks are **lizard** (complexity, 26+ languages), **jscpd** (duplication, 224 formats, MIT, `npx`), **osv-scanner** (vulnerabilities and licences across 11+ ecosystems, the only one with a true `--offline` mode), **semgrep CE** / **ast-grep** (static findings), **gitleaks** (secrets, MIT) and **scancode** (licence, heavy install). For coverage, no tool can measure it statically: it needs the project's own test runner.

Two exit-code contracts lump "findings" and "error" into one code: gitleaks returns 1 for "leaks or error", and mermaid-cli (the repo's own precedent) exits 1 for every error. So the forge rule applies as it stands. Judge the **report**, not the binary or the rc. A scanner that did not run writes a `[HIGH] … UNKNOWN` sentinel into the machine-read findings file (`sole-dev-merge.md:380-401`).

With zero extra installs (git, Python stdlib, codemem), you can measure size, churn, ownership, hotspots, coupling and dead code. You can also get Python-only complexity, crude duplication and the licences of installed Python packages. Vulnerabilities, secrets, real lint findings, multi-language complexity and project-licence compliance all need a tool, and **coverage needs the tests to be executed**.

## Evidence

### 1. Tool matrix (primary sources)

| Tool | Metric | Languages | Install / runnable without install | Licence | Machine output | Exit-code contract | Network | Runtime (mid-size) |
|---|---|---|---|---|---|---|---|---|
| **lizard** 1.24.0 | CCN, NLOC, params, fn length; clones via `-Eduplicate` | 26+: C/C++, C#, Go, Java, JS/JSX, TS/TSX, Kotlin, Python, Ruby, Rust, Swift, PHP, Scala, Lua, … ([README](https://github.com/terryyin/lizard)) | `pip install lizard`; deps pygments, pathspec ([PyPI](https://pypi.org/pypi/lizard/json)); `uvx lizard` | MIT ([LICENSE.txt](https://raw.githubusercontent.com/terryyin/lizard/master/LICENSE.txt); PyPI classifier says "Freeware", but the file is MIT) | `--xml`, `--csv`, `--html`, `--checkstyle` (no JSON) | "none-Zero if there are warnings"; `-i N` tolerates N ([README](https://github.com/terryyin/lizard)) | offline | not measured (absent); `-t` threads for parallelism |
| **radon** 6.0.1 | CC, MI, raw, Halstead | **Python only** ([docs](https://radon.readthedocs.io/en/latest/commandline.html)) | pip; `uvx radon` | MIT | `--json` on cc/mi/raw/hal; `--xml` (cc) | **not documented** | offline | not measured. Last release was 2023-03-26 ([PyPI](https://pypi.org/pypi/radon/json)), so maintenance is stale |
| **jscpd** 5.3.2 | duplication | 224 formats ([npm](https://registry.npmjs.org/jscpd/latest)) | `npx jscpd .`; also pip, cargo, brew, docker. Now a "Rust engine, self-contained binary" (8 platform optional deps); node >=18 for the npm shim | MIT | `json`, `sarif`, `xml`, `csv`, `markdown`, `codeclimate`, … (15 reporters) | exit 1 on unknown format, missing path or unwritable reporter; `--threshold` gates; `--fail-on-empty` ([README](https://github.com/kucherenko/jscpd)) | offline (first `npx` fetch needs network) | vendor claim: 547 files in 84 ms (Apple Silicon); secondary, not reproduced |
| **pip-audit** 2.10.x | Python dep vulns | Python | pip; `uvx pip-audit` | Apache-2.0 | `json`, `cyclonedx-json/xml`, `markdown` (`pip-audit --help`) | 0 = none, 1 = vulns found ([README](https://github.com/pypa/pip-audit)); error rc not distinguished in docs | **needs network** (PyPI or OSV API; `-s osv\|pypi\|esms`) | not measured (network) |
| **uv audit** (uv 0.12.3) | Python dep vulns from `uv.lock` | Python (uv projects) | built into uv, **zero extra install where uv exists** | (uv: not fetched) | `--output-format text\|json\|sarif` (`uv audit --help`) | not found in help | OSV service by default; `--offline` exists, but a vuln lookup offline was not verified | not measured |
| **npm audit** | JS dep vulns | npm lockfiles | ships with npm | (npm) | `--json` | 0 if none; otherwise governed by `--audit-level` ([docs](https://docs.npmjs.com/cli/v11/commands/npm-audit)) | **cannot run offline**; needs a package-lock | — |
| **osv-scanner** v2 | dep vulns, **dep licences** (`--licenses`), container images | C/C++, Dart, Elixir, Go, Java, JS, PHP, Python, R, Ruby, Rust; 19+ lockfile types ([repo](https://github.com/google/osv-scanner)) | Go binary release, `go install`, docker. **No uvx/npx** | Apache-2.0 | `json`, `sarif`, `markdown`, `spdx-2-3`, `cyclonedx-1-5`, `html` ([output](https://google.github.io/osv-scanner/output/)) | 0 clean, 1 vulns, 127 general error, 128 no packages found. The cleanest contract of the set | `--offline` against a pre-downloaded DB; `--download-offline-databases` ([offline](https://google.github.io/osv-scanner/usage/offline-mode/)) | not measured (absent) |
| **semgrep** CE (local 1.156.0; PyPI 1.178.0) | lint / security patterns | 17 GA (C#, Go, Java, JS, Kotlin, Python, TS, C/C++, JSX, Ruby, Scala, Swift, Rust, PHP, Terraform, Generic, JSON); cross-file dataflow is Pro-only ([docs](https://docs.semgrep.dev/supported-languages)) | pip wheel about 24–25 MB ([PyPI](https://pypi.org/pypi/semgrep/json)); `uvx semgrep` | LGPL-2.1-or-later | `--json`, `--sarif` | 0 OK (**also with findings unless `--error`**), 1 findings with `--error`, 2 fatal, 3/4/5/7/8 input errors (`semgrep scan --help` EXIT STATUS) | `--config auto` "will log in to the Semgrep Registry with your project URL"; registry configs send metrics unless `--metrics=off`. Offline only with local rules or `-e` | **1.87 s** here (1 pattern, `src packages`, `--metrics=off`) |
| **bandit** 1.9.4 | Python security | Python | pip; `uvx bandit`; extras `[sarif]`, `[toml]` ([docs](https://bandit.readthedocs.io/en/latest/start.html)) | Apache-2.0 (`importlib.metadata`) | `-f json\|csv\|xml\|yaml\|html\|custom` (`bandit --help`) | 0 clean / 1 findings; `--exit-zero` (`sole-dev-merge.md:340-341`, `bandit --help`) | offline | **0.56 s** here (`-r src packages`, 9,104 LOC, 21 results) |
| **ast-grep** 0.42.1 | custom structural rules | tree-sitter; the reference table lists Bash, C, C++, C#, CSS, Elixir, Go, Haskell, HCL, HTML, Java, JS, JSON, Kotlin, Lua, Markdown, Nix, PHP, Python, Ruby, Rust, Scala, Solidity, Swift, TS, TSX, YAML ([ref](https://ast-grep.github.io/reference/languages.html)) | npm `@ast-grep/cli`, pip `ast-grep-cli`, cargo, brew ([repo](https://github.com/ast-grep/ast-grep)); **already a codemem dependency** (`packages/codemem-mcp/pyproject.toml:24`) | MIT | `--json=stream\|pretty` (others per `--help`); `scan --format github\|sarif` | `scan --error[=RULE]` raises severity; rc contract not stated in `--help` | offline | **0.03 s** here (one pattern over `src packages`) |
| **gitleaks** (local 8.18.0) | secrets | language-agnostic (regex + entropy) | Go binary, brew, docker ([repo](https://github.com/gitleaks/gitleaks)). No uvx/npx | MIT | `json`, `csv`, `junit`, `sarif`, template | 0 none, **1 "leaks or error"**, 126 unknown flag; `--exit-code` configurable | offline | **1.06 s** over git history (731 commits, 2 redacted hits); **11.1 s** with `--no-git` (walks untracked `.venv` etc., 36 hits). Scope matters |
| **trufflehog** v3 | secrets **with live verification** | agnostic | Go binary, brew, docker, curl install script. No uvx/npx | **AGPL-3.0** ([repo](https://github.com/trufflesecurity/trufflehog)) | `--json` | 0 no results, 1 error, **183 results (only with `--fail`)** | **verifies credentials against live APIs by default**; `--no-verification` for offline | not measured (absent) |
| **scancode-toolkit** 32.5.0 | licence + copyright detection per file | agnostic | pip wheel **~104–108 MB**, 71 deps, Python >=3.10 ([PyPI](https://pypi.org/pypi/scancode-toolkit/json)); docker | Apache-2.0 code, CC-BY-4.0 data | JSON (`--json-pp`), YAML, SPDX, CycloneDX, HTML ([repo](https://github.com/aboutcode-org/scancode-toolkit)) | not found | offline | not measured; the install size alone rules it out as a default |
| **licensee** | project licence (LICENSE file) | agnostic | `gem install licensee` (Ruby) | MIT ([repo](https://github.com/licensee/licensee)) | `detect --json` ([CLI doc](https://github.com/licensee/licensee/blob/main/docs/command-line-usage.md)) | not found | offline for local paths; `--remote` uses the GitHub API | not measured |
| **scc** (added) | LOC, file-level complexity estimate, ULOC/DRYness | "large language support" | Go binary, brew, snap, docker ([repo](https://github.com/boyter/scc)) | MIT | `json`, `json2`, `csv`, `sql`, `openmetrics`, … | n/a | offline | vendor benchmarks only. Caveat: its complexity number "is only comparable to files in the same language" |

**Portability note on `uvx`/`npx`.** These need network on first use and populate a cache. They are "no permanent install", not "offline". The Go-binary tools (osv-scanner, gitleaks, trufflehog, scc) have no `uvx`/`npx` path. `docker` is present here (29.7.2) and all four publish images.

### 2. Present on this machine (BATS, `command -v`, read-only)

- **Present:** `pip-audit` 2.10.0, `semgrep` 1.156.0 (`~/.local/bin`), `bandit` 1.9.4, `ast-grep` 0.42.1, `gitleaks` 8.18.0, `shellcheck` 0.11.0, `ruff` 0.15.4, `coverage` 7.10.4, `mypy`, `uv` 0.12.3 (with `uv audit`), `uvx`, `npm` 11.17.0 / `npx` / `node` v26.5.0, `docker` 29.7.2, `cargo` 1.88.
  - Most of these resolve from the **conda env `bio312_07_25`**, which happens to be active. They are not a guaranteed baseline.
  - gitleaks 8.18.0 still uses the deprecated `detect`/`protect` CLI. Current upstream uses `git`/`dir`/`stdin` ([repo](https://github.com/gitleaks/gitleaks)), so a skill must handle both.
- **Absent:** `lizard`, `radon`, `jscpd`, `osv-scanner`, `trufflehog`, `scancode`, `licensee`, `scc`, `cloc`, `tokei`, `trivy`, `syft`, `grype`, `detect-secrets`, `safety`, `reuse`, `go`, `brew`.
- **Project `.venv`** (after `uv sync`): `ast-grep`, `sg`, `ruff`, `pytest`, `coverage`, `codemem`.
- **`sg` is ambiguous.** `/usr/bin/sg` is a symlink to `newgrp`, owned by Debian package **`util-linux-extra`** (`dpkg -S`; the brief said shadow-utils). But `command -v sg` resolves to the conda env's ast-grep first, and `.venv/bin/sg` is ast-grep too. The answer depends on PATH order. ast-grep's own docs say to use the full `ast-grep` name for this reason ([quick-start](https://ast-grep.github.io/guide/quick-start.html)). Probe `ast-grep`, never `sg`.

### 3. Graceful-degradation precedent in this repo

1. **Seam.** The scanner binaries are env-overridable: `BANDIT_BIN="${BANDIT_BIN:-bandit}"` and `SHELLCHECK_BIN="${SHELLCHECK_BIN:-shellcheck}"` (`claude-code/commands/sole-dev-merge.md:342,387`). The seam exists so the degraded path can be tested "without uninstalling anything" (`:385-386`). `CLAUDE.md:129` documents it as "Not a bypass".
2. **Judge the report, not the binary.** The degraded condition is `rc > 1 || ! -s "$OUT"` (`:347,393`). The rationale is at `:380-384`: `command -v` answers a different question, and `true`, `:` and a broken install all resolve.
3. **Write the sentinel where the consumer reads it.** The line `[HIGH]     C3 NOT RUN — '<bin>' unavailable or produced no report (rc=N); Python findings UNKNOWN — (scanner-unavailable)` is appended **into `$FINDINGS`** (`:350`, C4 at `:401`), not just echoed to stdout. Stage D reads `$FINDINGS` only (`:394-398`).
4. **Unparseable output also means UNKNOWN.** If the JSON fails to load, `C3/C4 REPORT UNPARSEABLE … (scanner-output-unparseable)` is written (`:358-361,409-415`).
5. **Zero findings is unrepresentable when a scanner did not run.** The count is `TOTAL=$(grep -cE "^\[(CRITICAL|HIGH|MEDIUM|LOW)\]" "$FINDINGS")` (`:430-431`). The sentinel counts toward it, so Stage D cannot skip triage.
6. **Test.** `C3/C4 record UNKNOWN in findings when a scanner does not run` loops over both scanners × `{/nonexistent/scanner, true, echo}`. It asserts that a `^\[HIGH\]` line and `UNKNOWN` are in `$FINDINGS`, and that stdout never says `aggregate: 0 findings` (`tests/commands/sole-dev-merge/test_stage_c_dispatch.bats:114-171`). It needs no external binary, so "it can never skip" (`:115-116`). The real-scanner test skips on an unusable shellcheck (`:180-181`).
7. **CI.** The pipeline installs and `--version`-asserts both scanners (`.github/workflows/security.yml:72-80,103-107`). Without that, a missing tool turns a security test into `ok N # skip` (`docs/lessons.md:373-374`).
8. **Doctrine.** L-012: UNKNOWN is never PASS (`docs/lessons.md:337-381`). L-024 adds the complement: "A check that has only ever returned UNKNOWN is not a check … prove it can FAIL" (`docs/lessons.md:78-97`).
9. **Second precedent.** `render_check` resolves `MMDC_BIN`, returns `UNKNOWN` when the binary is missing, and returns `FAIL` only on a recognised parse-error signature. The reason is that mermaid-cli "exits 1 for *all* errors" (`src/aa_ma/render/mermaid_lint.py:505-512`).

**Why this shape applies to the new tools.** Several of them overload their exit codes:
- gitleaks: 1 = "leaks or error"
- semgrep: exits 0 with findings unless `--error`
- pip-audit: documents only 0/1

So the rc alone cannot separate "clean" from "didn't run". The portable contract per tool is: `<TOOL>_BIN` seam → run with JSON/SARIF to a file → treat "empty or unparseable" as UNKNOWN → write the sentinel into the findings artefact. osv-scanner is the one tool whose rc does separate the cases (127 = error, 128 = nothing scanned).

### 4. Zero extra installs vs needs a tool

"Zero extra install" here means git + Python stdlib + codemem. codemem ships in this repo as a uv workspace member and brings `ast-grep-cli` with it (`packages/codemem-mcp/pyproject.toml:24`).

| Metric | Zero-install measure | Fidelity | Needs a tool for real measurement |
|---|---|---|---|
| Size / LOC / language mix | `git ls-files` + line counts | exact | — (scc adds comment/blank split) |
| Churn, hotspots, ownership, co-change | codemem `hot_spots` = commits-in-window × function_count (`mcp_tools/__init__.py:442-455`), `owners` (`:613`), `co_changes` (`:508`), `symbol_history` (`:777`); raw `git log --numstat` | good (it is the source data) | — |
| Dead code | codemem `dead_code` = functions with zero incoming call edges (`:260-266`) | heuristic (dynamic dispatch gives false positives) | vulture (not investigated) |
| Cyclomatic complexity | stdlib `ast` branch-node count, **Python only**; codemem's function_count is only a size proxy | Python: adequate; other languages: none | lizard (multi-language), radon (Python), scc (file-level estimate) |
| Duplication | stdlib hashing of normalised line windows | crude | jscpd, `lizard -Eduplicate`, scc ULOC/DRYness |
| Test coverage | **none statically**. Proxy: test-file/source-file ratio, or codemem `who_calls` reachability from `tests/` | proxy only | coverage.py / pytest-cov (this repo has pytest-cov, `pyproject.toml:47`), plus the target's own test runner. Always requires **executing** the suite |
| Dependency vulnerabilities | none offline. `uv audit` (uv ≥ 0.12) and `npm audit` come with the package manager but need network | — | pip-audit, osv-scanner (`--offline` with a pre-fetched DB) |
| Dependency outdatedness | `uv tree --outdated`, `pip list --outdated --format json`, `npm outdated` (package manager built-ins, network) | good where the manager exists | osv-scanner does not do outdatedness |
| Lint / security static | stdlib `ast.parse` / `py_compile` (syntax only); ast-grep custom rules via codemem's dependency | syntax / bespoke rules only | ruff, bandit, shellcheck, semgrep |
| Licence compliance | read the LICENSE file(s) from `git ls-files`; installed Python deps via `importlib.metadata` (e.g. bandit → `Apache-2.0`, checked locally) | project: heuristic; Python deps: installed-env only | licensee (project), osv-scanner `--licenses` (deps), scancode (per-file, heavy) |
| Secret detection | `git grep -E` for high-signal patterns (e.g. private-key headers) | crude, high miss rate | gitleaks (offline, MIT). trufflehog only with `--no-verification` if offline or no network egress is required |

## Not pursued
- Exit-code contracts for radon, scancode, licensee and `ast-grep scan` — not documented in the fetched primary pages. Needs a local run once installed.
- `uv audit` offline behaviour and exit codes — only `--help` was read; no network run was made.
- Mid-size runtimes for lizard, radon, jscpd, osv-scanner, trufflehog, scancode, scc — the tools are absent and must not be installed. The figures above are local timings or labelled vendor claims.
- pip-audit and `npm audit` runtime — they require network calls to an advisory API; not run.
- Other candidates: trivy, syft/grype, detect-secrets, reuse, pip-licenses, vulture, eslint, c8/nyc (JS coverage), gocyclo — seen but not researched.
- Exact ast-grep language count — the fetched page's summary said 31 but its table listed 27.
- scancode's install docs page returned 404 (`/getting-started/install.html`), so its RAM/disk requirements were not found.
- Semgrep CE vs Pro feature split per language beyond cross-file dataflow — the docs page defers to other pages.
- Per-package licence fields in npm lockfiles as a zero-install JS licence source — not verified.
