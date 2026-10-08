# Where is every coding convention stated today, and where is each one enforced?

**Created:** 2026-10-08
**Author:** aa-ma-researcher (Claude), for chart effort `code-conventions-impact` (Ticket 1, `.claude/dev/charting/code-conventions-impact/code-conventions-impact-map.md:27`)
**Reviewed-Through-Date:** 2026-10-08 (repo at `cb129c1` on `feature/engineering-standards`; `~/.claude` and plugin cache as on disk this date; ruff 0.15.9)
**Valid-Through:** 2026-Q4 (invalidated by any edit to `claude-code/rules/*.md`, `~/.claude/CLAUDE.md`, `~/.claude/skills/logging-and-comments/`, `pyproject.toml [tool.ruff]`, `.github/workflows/security.yml`, `~/.claude/settings.json` hooks, or a ponytail / security-guidance plugin upgrade)
**Sources:**
- `claude-code/rules/engineering-standards.md:81-93,130-146` — auto-loaded statement of TDD/KISS/DRY/SOLID/SoC and the HARD/SOFT checklist
- `~/.claude/CLAUDE.md:23-25,60-67,97-100` — auto-loaded statement of comments, docstrings, logging, impact analysis
- `~/.claude/skills/logging-and-comments/SKILL.md:17-109` + `references/{python,bash}.md` + `references/ruff-baseline.toml:5-26` — the full comments/docstring/logging standard
- `~/.claude/plugins/cache/ponytail/ponytail/4.7.0/skills/ponytail/SKILL.md:28-92` + `hooks/hooks.json` + `hooks/ponytail-instructions.js:9,82` — YAGNI/minimal-code doctrine, injected at SessionStart
- `claude-code/skills/operational-constraints/SKILL.md:136-162,230` — duplicate statement of KISS/DRY/SOLID/SoC/TDD/comments
- `pyproject.toml:67-95` — the only lint config; `.github/workflows/security.yml:16-182` — the only CI
- `claude-code/hooks/security-static-check.sh:20-32,157-194` — commit-time mechanical security check
- `~/.claude/hooks/lib/ruff-format.sh:6-15` + `~/.claude/settings.json` PostToolUse — the global edit-time ruff hook
- `claude-code/agents/{code-reviewer,security-auditor,tdd-sequence-auditor}.md` + `claude-code/commands/execute-aa-ma-milestone.md:521-607,766-798` — LLM/gate enforcement layer
- `src/aa_ma/plan_parsers.py:47-58` — canonical `TDD-Waiver` values
- `.importlinter:31-60` — layer contracts (SoC enforcement)

## Answer

Conventions are stated in **seven auto-loaded places** (two forge-shipped rules, four global-only rules, global `CLAUDE.md`, plus ponytail's SessionStart injection — ~11.2k tokens per session in this repo once the project `CLAUDE.md` is added) and **about a dozen on-demand skills**. The real standard for comments, docstrings and logging lives in the global-only `logging-and-comments` skill. Mechanical enforcement covers only a thin slice: ruff on `src/` (logging, prints, blind except, TODO format, commented-out code, module docstrings only), ShellCheck, a regex commit hook for five Python security patterns, pytest/bats in CI, and import-linter layering. Everything else (why-comments, magic-number rationale, `# why:` on suppressions, secrets-in-logs, KISS/DRY/SOLID, test-first) is enforced only by LLM review agents in Phase 6.8 or by nothing. Several sources contradict each other: ponytail vs TDD/SOLID, the TDD-Waiver enum vs the rule's skip list, the docstring rule vs `extend-ignore`, the "HARD" tests gate vs a gate that is just a comment, and three different debug env vars.

## Evidence

### 0. Source map: forge-shipped vs global-only (resolved with `readlink -f`)

| Source | Resolves to | Class | Load |
|---|---|---|---|
| `~/.claude/rules/aa-ma.md`, `engineering-standards.md` | `aa-ma-forge/claude-code/rules/*.md` (symlinks) | forge-shipped | auto |
| `~/.claude/rules/git-conventions.md`, `project-index-awareness.md`, `self-improvement-loop.md`, `token-efficiency.md` | regular files | global-only | auto |
| `~/.claude/CLAUDE.md` | regular file | global-only | auto |
| `aa-ma-forge/CLAUDE.md` | gitignored (`.gitignore:2`) | project-local, unshipped | auto in this repo only |
| skills `operational-constraints`, `defense-in-depth`, `system-mapping`, `impact-analysis` | `aa-ma-forge/claude-code/skills/*` | forge-shipped | on-demand |
| skills `logging-and-comments`, `python-quality-gates`, `bash-defensive-patterns`, `secrets-management`, `senior-secops`, `deslop-shared-libs` | regular dirs under `~/.claude/skills/` | global-only (`deslop-shared-libs` is gstack-origin, `SKILL.md:4`) | on-demand |
| ponytail 4.7.0 | `~/.claude/plugins/cache/ponytail/ponytail/4.7.0` (`enabledPlugins` `ponytail@ponytail: true`) | third-party plugin | **auto**: the SessionStart hook injects `skills/ponytail/SKILL.md` body (`hooks/ponytail-instructions.js:9,82`); mode `full` (`~/.claude/.ponytail-active`, `ponytail-config.js:16`) |
| security-guidance 2.0.11 | `~/.claude/plugins/cache/claude-plugins-official/security-guidance/2.0.11` | third-party plugin | hooks (PostToolUse on Edit/Write and on `git commit`/`git push`, `hooks/hooks.json`) |
| hooks `security-static-check.sh`, `pre-compact-aa-ma.sh`, `aa-ma-*` | `~/.claude/hooks/lib/*` → `aa-ma-forge/claude-code/hooks/*` (symlinks) | forge-shipped | PreToolUse etc., wired in `~/.claude/settings.json` |
| hooks `ruff-format.sh`, `guard-protected-dirs.sh` | regular files in `~/.claude/hooks/lib/` | global-only | PostToolUse(Edit\|Write) / PreToolUse(Bash) |
| `pyproject.toml [tool.ruff]`, `.github/workflows/security.yml`, `.importlinter` | repo files | forge-local (not shipped to other projects) | mechanical |
| pre-commit | **none**: no `.pre-commit-config.yaml`; `.git/hooks` holds only `*.sample`; `core.hooksPath` unset | — | — |
| `packages/codemem-mcp/pyproject.toml` | has no `[tool.ruff]` section (lines 1-55), so the root config governs it | — | not linted in CI |

### 1. Auto-loaded token cost (chars / 4)

| File | chars | ≈ tokens |
|---|---|---|
| `claude-code/rules/engineering-standards.md` | 12,372 | 3,093 |
| `~/.claude/CLAUDE.md` | 8,246 | 2,062 |
| `claude-code/rules/aa-ma.md` | 7,877 | 1,969 |
| `~/.claude/rules/token-efficiency.md` | 2,589 | 647 |
| `~/.claude/rules/self-improvement-loop.md` | 1,813 | 453 |
| `~/.claude/rules/git-conventions.md` | 1,608 | 402 |
| `~/.claude/rules/project-index-awareness.md` | 735 | 184 |
| **Global subtotal (every project)** | 35,240 | **≈ 8,810** |
| ponytail SessionStart injection (mode `full`, measured via `getPonytailInstructions('full')`) | 4,030 | ≈ 1,008 |
| `aa-ma-forge/CLAUDE.md` (this repo only) | 9,454 | 2,364 |
| **Total in this repo** | 48,724 | **≈ 12,180** |

On-demand bodies for comparison: `logging-and-comments/SKILL.md` is 8,595 chars (≈2,150 tok); with its `references/` (9,744 chars) the total is ≈4,580 tok. `operational-constraints` 9,548; `impact-analysis` 9,051; `system-mapping` 11,906; `deslop-shared-libs` 13,084; `bash-defensive-patterns` 9,957 chars.

Only a small share of the auto-loaded budget is coding convention. It is `engineering-standards.md:81-93` (§2), `CLAUDE.md:60-67`, and the ponytail injection. Most of the rest is AA-MA process.

### 2. Comments (why-not-what, suppression reasons, TODO format, commented-out code, magic constants)

**Stated**
- `~/.claude/CLAUDE.md:62` (auto): "comments only for *why*, never for *what*… every magic constant gets a unit + rationale; `# why:` on every `noqa`/`|| true`/`2>/dev/null`."
- `logging-and-comments/SKILL.md:31` (on-demand): "Comments explain *why*, never *what*." `:90-100` covers magic numbers (name + unit + reason), the suppression format `# noqa: S105  # why: …`, `TODO(#123)`, ADR pointers, delete commented-out code, and `# ponytail: <ceiling>, <upgrade path>`.
- `operational-constraints/SKILL.md:160-161` (on-demand, forge): "Self-documenting code… Comments explain WHY, not WHAT". This duplicates `CLAUDE.md:62`.
- ponytail `SKILL.md:50` (auto via injection): mark deliberate simplifications with `ponytail:` comments. `logging-and-comments/SKILL.md:99` adopts the same marker (consistent duplication).
- `bash-defensive-patterns/SKILL.md` (on-demand) gives no comment rule.

**Enforced**
- Ruff `ERA` (commented-out code) and `TD` (TODO format), `pyproject.toml:78-79`. CI runs this on `src/` only (`security.yml:55`). Measured today: `src/` passes clean. `claude-code/ scripts/ tests/` carry **10 ERA001** (plus 23 F811, 1 BLE001, 1 F541) that no CI job checks.
- Edit-time: `~/.claude/hooks/lib/ruff-format.sh:14` runs `ruff check --fix` on every edited `.py`, in any project, using that project's config. Its output goes to `>/dev/null 2>&1`, so unfixable findings are never shown.
- `code-reviewer` agent (Phase 6.8): it WARNs on commented-out blocks of 3+ lines (`code-reviewer.md:68-69`) and on magic numbers only at **3+ occurrences** (1-2 are INFO) (`:71-75`). It "MUST NOT flag… comment style" (`:91`).
- `future-proofing-auditor` flags magic numbers (`execute-aa-ma-milestone.md:797-798`).
- **Nothing enforces** why-not-what, constant rationale, or `# why:` on suppressions. Ruff `PLR2004` and `RUF100` are not selected (`pyproject.toml:70-80`).

**Contradictions and drift**
- Suppression format. Stated: `# noqa: S105  # why: enum value…` (`logging-and-comments/SKILL.md:95`; `CLAUDE.md:62`). Practice: all 10 `noqa` in `src/`+`packages/` carry an em-dash reason and **none** uses a literal `# why:`. Example: `src/aa_ma/gate.py:479` `# noqa: BLE001 — last resort: …`.
- `|| true` without `# why:`. CI itself breaks the rule: `security.yml:39` `bandit -r src/ -f json || true` has no reason comment. The forge hooks contain 28 `2>/dev/null` / `|| true` sites with **zero** literal `# why:` markers. A heuristic found 9 with no comment within 3 lines, e.g. `security-static-check.sh:139`, `aa-ma-commit-drift.sh:83-84`, `lib/aa-ma-footer.sh:27`.
- `bash-defensive-patterns/SKILL.md:295-302` teaches `kill … 2>/dev/null || true` with no `# why:`, which contradicts `CLAUDE.md:62`.
- Magic numbers. "every magic constant" (`CLAUDE.md:62`) vs the reviewer's "3+ occurrences → WARNING" threshold (`code-reviewer.md:73-75`).

### 3. Docstrings

**Stated**
- `~/.claude/CLAUDE.md:62` (auto): "Docstrings on public API".
- `logging-and-comments/SKILL.md:89` (on-demand): "Docstrings on every public module, class and function, in Google style (`Args:`, `Returns:`, `Raises:`)", plus units, side effects and idempotency. `references/python.md:120`: docstrings must not claim behaviour that does not exist ("review" only).
- `ruff-baseline.toml:13,18-19`: `D1` + `convention = "google"`. `python-quality-gates/SKILL.md:42` restates the baseline adoption.

**Enforced**
- `pyproject.toml:77` selects `D1`, but `pyproject.toml:81-83` **ignores D101, D102, D103, D104, D107** ("Pre-existing docstring gaps at adoption… TODO(logging-std): burn down"). Only D100 (module), D105 and D106 bite, on `src/` only. `tests/**` are exempt (`:95`).
- Docstring accuracy and Google sections: nothing (no `D4xx` selected beyond `convention`).

**Contradictions**
- "Docstrings on public API" (`CLAUDE.md:62`) and "every public… class and function" (`logging-and-comments/SKILL.md:89`) vs `pyproject.toml:83` `extend-ignore = ["D101","D102","D103","D104","D107"]`. This is a sanctioned burn-down per `logging-and-comments/SKILL.md:104`, but today the rule on classes, methods and functions is unenforced.
- ponytail `SKILL.md:54-56`: "No essays, no feature tours, no design notes… every paragraph defending a simplification is complexity smuggled back in as prose." This pulls against rich Google docstrings and constant rationale. The skill limits it to "unrequested prose" (`:57-59`), and the docstring rule *is* a request, but the conflict is not resolved in writing anywhere.

### 4. Logging (and silent failures)

**Stated**
- `~/.claude/CLAUDE.md:63` (auto): no silent failures; logs → stderr, data → stdout; `getLogger(__name__)`; configure at entrypoint.
- `logging-and-comments/SKILL.md:17-31` (five non-negotiables), `:33-68` (Python levels, CLI `-v/-q`/`LOG_LEVEL`, run manifests, JSON logs for services), `:70-85` (Bash/hook rules), and `references/bash.md:9-41`.
- `bash-defensive-patterns/SKILL.md:249-279` (on-demand) gives a second Bash logging pattern.
- `system-mapping/SKILL.md:186-216` (forge, on-demand) is an inventory checklist for logger config and coverage. It states no convention.
- `defense-in-depth/SKILL.md:25,85` (forge): "Debug logging helps when other layers fail".

**Enforced**
- Ruff `LOG`, `G`, `T20`, `BLE`, `S110`, `S112`, `TRY400`, `TRY401` (`pyproject.toml:71-76`). CI covers `src/` only (`security.yml:55`), which is clean. **`packages/codemem-mcp` has 4 live violations that CI never sees**: `io_sinks.py:168,174` T201 and `mcp_tools/__init__.py:754`, `parser/python_ast.py:272` BLE001.
- The edit-time ruff hook (`ruff-format.sh:14`) applies the same rules but discards their output.
- `security-auditor` agent covers log leaks (`security-auditor.md:55-61`), Phase 6.8 only.
- Bash logging and stderr discipline: **nothing**. ShellCheck (`security.yml:22-23`) does not check either.

**Contradictions and drift**
- Debug env var: four names. `HOOK_DEBUG=1` (`logging-and-comments/SKILL.md:85`, `references/bash.md:41`, `claude-code/hooks/lib/aa-ma-parse.sh:68`); `AA_MA_PLAN_MARKER_DEBUG=1` (`claude-code/hooks/aa-ma-plan-skip-warn.sh:30`, `aa-ma-forge/CLAUDE.md:127`); `VERBOSE=1` (`references/bash.md:9,14`); `DEBUG=1` (`bash-defensive-patterns/SKILL.md:269`).
- Log line format. `ISO-ts LEVEL msg` via `date -Is` (`logging-and-comments/SKILL.md:74`, `references/bash.md:13`) vs `[YYYY-MM-DD HH:MM:SS] INFO: msg` (`bash-defensive-patterns/SKILL.md:257`).
- Persistent hook log path. `~/.claude/logs/hooks.log` (`logging-and-comments/SKILL.md:84`, `references/bash.md:41`) vs `~/.claude/hooks/cache/compaction.log` (`claude-code/hooks/pre-compact-aa-ma.sh:135`).
- Claim vs mechanism. `logging-and-comments/SKILL.md:105` says T201 prints "are reported, never deleted… Hook failures are logged to `~/.claude/logs/hooks.log`". But `ruff-format.sh:14` sends `ruff check` output to `/dev/null`, so nothing is reported, and only `ruff format` failures are logged (`ruff-format.sh:10-13`).
- Strict mode. `set -Eeuo pipefail` is prescribed (`references/bash.md:11`, `bash-defensive-patterns/SKILL.md:28`), but 6 of 9 forge hooks use `set -euo pipefail` (no `-E`), e.g. `security-static-check.sh:38`. `lib/aa-ma-chart-guard.sh:36` uses `set -u` only.
- `senior-secops/scripts/security_scanner.py:44-69` prints diagnostics and its report to stdout, against `logging-and-comments/SKILL.md:25`.

### 5. Security / SecOps

**Stated**
- `logging-and-comments/SKILL.md:30`: never log secrets or PII.
- `secrets-management/SKILL.md:209-217`: never commit secrets, mask them in logs, use secret scanning (GitGuardian/TruffleHog). `:309-321` gives an example TruffleHog pre-commit.
- `senior-secops/SKILL.md:6-40`: a toolkit wrapper only, with no concrete conventions.
- `defense-in-depth/SKILL.md:14`: "Validate at EVERY layer data passes through".
- ponytail `SKILL.md:78-79`: "Never simplify away: input validation at trust boundaries… security measures".
- `engineering-standards.md:104`: delegate security audit to subagents.
- `security.yml:9-11`: least-privilege token and SHA-pinned actions, stated in a workflow comment.
- **No auto-loaded file states a security convention.** `CLAUDE.md` and the rules are silent except `engineering-standards.md:104`.

**Enforced**
- `security-static-check.sh` (forge, PreToolUse Bash). It covers five regex classes in **added lines of staged `.py` files** (`:20-26,157-194`): hardcoded secret literal, `shell=True` / dynamic-code builtins, `../` in `open`/`Path`, SQL f-string or `+`, and pickle `loads`. It blocks with exit 2 (`:217`). Bypasses: `AA_MA_HOOKS_DISABLE=1`, `[security-bypass: <reason>]`, editor-form commits, and `-F` message files (`:10-15`; `aa-ma-forge/CLAUDE.md` "Known scope limits").
- security-guidance plugin: PostToolUse pattern warnings on Edit/Write, plus an async LLM review on `git commit`/`git push` (`hooks/hooks.json`). Its rule list overlaps the forge hook: `pickle_deserialization`, `python_subprocess_shell`, `eval_injection` (`hooks/patterns.py:104,135,151`).
- Bandit in CI (`security.yml:38-39`) on `src/` only, with `|| true` and JSON to the log. **It can never fail the build.** `aa-ma-forge/CLAUDE.md:140` describes it as a "Bandit security scan", implying a gate.
- bats CI asserts that bandit and shellcheck are present for `/sole-dev-merge` Stage C (`security.yml:72-80,103-107`).
- `security-auditor` agent (Phase 6.8, Audit-Profile `full|code-only|infra`): OWASP, credential flow, log leaks (`security-auditor.md:3-7,55-61`).
- Secrets in logs, secret scanning (gitleaks/TruffleHog), and dependency audit: **nothing mechanical**. No pre-commit, no CI secret scan, no `pip-audit`/`uv audit`.
- `senior-secops/scripts/security_scanner.py:47-55` is a **stub**: `analyze()` always sets `findings = []`.

**Duplication**
- Three overlapping layers for the same Python patterns: the forge hook (`security-static-check.sh:170-194`), the security-guidance plugin (`patterns.py:104-151`), and bandit (non-blocking). `security-auditor.md:12,74` explicitly defers to the forge hook.
- Contradiction: "Validate at EVERY layer" (`defense-in-depth/SKILL.md:14`) vs ponytail's ladder, "Does this need to exist at all?… minimum code that works" (`ponytail/SKILL.md:32-37`), which keeps validation only "at trust boundaries" (`:78-79`).

### 6. KISS / DRY / SOLID / SoC (and YAGNI)

**Stated**
- `engineering-standards.md:86-93` (auto): KISS "complexity requires justification recorded in `context-log.md`"; DRY "extract shared logic"; SOLID "depend on abstractions; favor composition"; SOC "separate business logic, data access, API integration, and presentation".
- `~/.claude/CLAUDE.md:61` (auto) points to that rule "§2; also follow 12-Factor App". `:24-25`: "Don't fix what isn't broken… Function over perfection."
- `operational-constraints/SKILL.md:140-145` (forge, on-demand) repeats KISS/DRY/SOLID/SOC/12-Factor while claiming at `:138` that it "names it without duplicating content".
- ponytail `SKILL.md:28-50` (auto via injection): YAGNI ladder; "No unrequested abstractions: no interface with one implementation"; "Fewest files possible".
- `deslop-shared-libs/SKILL.md:160-162` (on-demand): extraction requires "at least two verified, first-party authored source locations".

**Enforced**
- import-linter contracts for codemem layers and `aa_ma.render` / `aa_ma.analysis` leaf rules (`.importlinter:36-60`), run in CI (`security.yml:144-147`). This is the only mechanical SoC check, and it covers only those packages.
- `code-reviewer` agent (Phase 6.8): KISS = function >50 lines with nested conditionals; SRP = class doing IO + logic + presentation; SOC = logic mixed with IO; DRY = 3+ near-identical blocks (`code-reviewer.md:77-86`). It is skipped when `AA_MA_AUDIT_BUDGET=low` (`:124`) or `=off` (`execute-aa-ma-milestone.md:766-768`).
- "Complexity requires justification in context-log": **nothing** checks it. No ruff `C901`/`PLR09xx` rules are selected (`pyproject.toml:70-80`).

**Contradictions**
- SOLID "depend on abstractions" (`engineering-standards.md:90`) vs ponytail "no interface with one implementation, no factory for one product" (`ponytail/SKILL.md:44`).
- SOLID/SoC "single responsibility per module" (`engineering-standards.md:90-93`) vs ponytail "Fewest files possible. Shortest working diff wins." (`ponytail/SKILL.md:47`).
- DRY threshold: "extract shared logic" with no threshold (`engineering-standards.md:88`) vs **2** verified callers (`deslop-shared-libs/SKILL.md:160`) vs **3+** blocks (`code-reviewer.md:84`) vs ponytail "Deletion over addition" (`:46`).

### 7. Testing / TDD

**Stated**
- `engineering-standards.md:83-85` (auto): "write failing tests before implementation; cover happy path, edge cases, regressions. Skip only for docs-only, config-only, or infrastructure-only milestones."
- `engineering-standards.md:137-138`: "Tests written and passing | HARD | `uv run pytest` exit 0".
- `~/.claude/CLAUDE.md:23` (auto): "Never mark a task complete without proving it works. Run tests".
- `operational-constraints/SKILL.md:147-151`: TDD via `Skill(test-driven-development)` (superpowers plugin 6.4.1, declared-external), "No rationalizations for skipping tests". `:230`: "TDD applicable?"
- `python-quality-gates/SKILL.md:12-22`: zero tolerance for red suites; `@pytest.mark.skip(reason="BROKEN: …")` is allowed if the fix takes more than 30 min, with the user told.
- ponytail `SKILL.md:87-92` (auto via injection): "ONE runnable check… `assert`-based `demo()` or one small `test_*.py`. No frameworks, no fixtures, no per-function suites unless asked. Trivial one-liners need no test."

**Enforced**
- CI pytest: `security.yml:167-182` (everything except `perf`/`slow` markers, `pyproject.toml:127`). CI bats: `security.yml:109-120`. Both fire on push to main and PRs only (`:3-7`).
- `tdd-sequence-auditor` (Phase 6.8) is a git-log check that the first `tests/` commit precedes the first `src/` commit, with verdict PASS/FAIL/WAIVED (`tdd-sequence-auditor.md:3,56`). It can be waived by the canonical `TDD-Waiver` (`src/aa_ma/plan_parsers.py:47-58`).
- §6.4 of `/execute-aa-ma-milestone` runs listed tests "(if specified)" (`execute-aa-ma-milestone.md:369-375`). This is agent prose, not code.
- §6.7 HARD gate conditions 3 ("Tests-pass evidence") and 4 ("Impact-analysis evidence") are **bare comments with no code** (`execute-aa-ma-milestone.md:604-605`). `src/aa_ma/gate.py` never invokes pytest (0 occurrences).

**Contradictions and drift**
- Skip list. Rule: "Skip only for docs-only, config-only, or infrastructure-only" (`engineering-standards.md:84-85`). Code: `CANONICAL_TDD_WAIVERS = {"refactor", "docs-only", "prototype", "hotfix-emergency", "tooling-config"}` (`plan_parsers.py:47-48`). The code adds three waivers the rule does not allow, renames config-only, and omits infrastructure-only.
- Depth. "cover happy path, edge cases, regressions" (`engineering-standards.md:83-84`) and "No rationalizations for skipping tests" (`operational-constraints/SKILL.md:151`) vs "ONE runnable check… no per-function suites unless asked. Trivial one-liners need no test" (`ponytail/SKILL.md:88-92`).
- "Tests written and passing" is tagged **HARD** (`engineering-standards.md:138`), but the gate checks nothing mechanically (`execute-aa-ma-milestone.md:604`).
- Unbacked comments. `pyproject.toml:121` says "CI's perf job opts in with `-m perf`", but no perf job exists in `security.yml` (only the exclusion at `:180-182`). `pyproject.toml:49` says "coverage gate ≥90% on parser.py + model.py", but no `--cov`/`fail_under` exists in `pyproject.toml`, CI or `tests/conftest.py`.

### 8. Adjacent: impact analysis / pre-flight (a stated coding convention with three versions)

- `~/.claude/CLAUDE.md:99` (auto): required for shared modules, signatures and multi-file edits; "Skip for single-file local edits, docs, config and test-only changes."
- `operational-constraints/SKILL.md:154`: "Use `Skill(impact-analysis)` for ALL code changes". `:230`: "For code changes, always". This contradicts `CLAUDE.md:99`.
- `impact-analysis/SKILL.md:12-27`: required for milestone/shared/signature changes; RECOMMENDED for any edit; not used for docs, tests or config. This agrees with `CLAUDE.md:99`.
- Enforced: agent prose at §6.3 (`execute-aa-ma-milestone.md:328`). The §6.7 condition 4 is a comment only (`:605`).

## Summary matrix

| Topic | Stated where (auto / on-demand) | Enforced by | Contradictions / drift |
|---|---|---|---|
| Comments | auto: `CLAUDE.md:62`; on-demand: `logging-and-comments:31,90-100`, `operational-constraints:160-161`; auto-injected: ponytail `:50` | ruff ERA+TD on `src/` (CI); code-reviewer (≥3-line blocks, magic numbers ≥3×); **nothing** for why-not-what, `# why:`, constant rationale | `# why:` format unused in code (10/10 noqa use em-dash); CI `|| true` (`security.yml:39`) and hook suppressions lack `# why:`; "every" magic constant vs reviewer's 3× threshold |
| Docstrings | auto: `CLAUDE.md:62`; on-demand: `logging-and-comments:89`, `ruff-baseline.toml:13,18` | ruff D100/D105/D106 on `src/` only | D101/2/3/4/7 ignored (`pyproject.toml:83`) vs "every public class and function"; ponytail "no design notes" tension |
| Logging / silent failure | auto: `CLAUDE.md:63`; on-demand: `logging-and-comments:17-85`, `bash-defensive-patterns:249-279` | ruff LOG/G/T20/BLE/S110/S112/TRY on `src/` only; edit hook (output discarded); security-auditor for leaks; **nothing** for Bash | 4 debug env vars; 2 log formats; 2 hook-log paths; skill says prints "reported" but hook discards them; `set -E` drift; `packages/` has 4 unlinted violations |
| Security / SecOps | auto: only `engineering-standards.md:104`; on-demand: `logging-and-comments:30`, `secrets-management:209-217`, `defense-in-depth:14`, ponytail `:78` | `security-static-check.sh` (5 Python regex classes, blocking); security-guidance plugin (warn + async LLM); bandit CI (**non-blocking**); security-auditor; **nothing** for secret scanning, dependency audit, secrets-in-logs | 3-way duplicate pattern detection; "Bandit security scan" (`aa-ma-forge/CLAUDE.md:140`) vs `|| true`; senior-secops scanner is a stub; defense-in-depth "every layer" vs ponytail ladder |
| KISS/DRY/SOLID/SoC | auto: `engineering-standards.md:86-93`, `CLAUDE.md:24-25,61`, ponytail `:28-50`; on-demand: `operational-constraints:140-145`, `deslop-shared-libs:160` | import-linter (codemem + aa_ma leaves, CI); code-reviewer heuristics (Phase 6.8, budget-skippable); **nothing** for the "complexity justification" rule | ponytail vs SOLID abstractions and file count; DRY thresholds none / 2 / 3+; operational-constraints duplicates the rule while saying it does not |
| Testing / TDD | auto: `engineering-standards.md:83-85,137-138`, `CLAUDE.md:23`, ponytail `:87-92`; on-demand: `operational-constraints:147-151`, `python-quality-gates:12-22` | CI pytest + bats (main/PR); tdd-sequence-auditor (waivable); §6.4 prose; **§6.7 tests condition is a comment** | TDD-Waiver enum ≠ rule skip list; ponytail "one check" vs edge-case coverage; HARD tag with no mechanical gate; phantom perf job and coverage gate |

## Biggest gaps

**Stated but unenforced**
1. Why-comments, constant rationale, and `# why:` on suppressions (`CLAUDE.md:62`). No lint exists, the reviewer is told not to flag comment style (`code-reviewer.md:91`), and CI violates the rule itself (`security.yml:39`).
2. Docstrings on public classes and functions. They are ignored in `pyproject.toml:83` pending burn-down.
3. "Tests written and passing — HARD" (`engineering-standards.md:138`). The gate has only a comment (`execute-aa-ma-milestone.md:604`). The perf job and coverage gate exist only in comments (`pyproject.toml:49,121`).
4. Secrets in logs and secret scanning (`logging-and-comments:30`, `secrets-management:209-216`). Only the LLM auditor checks them; there is no gitleaks or pre-commit, and bandit cannot fail.
5. The KISS "complexity requires justification" rule (`engineering-standards.md:86-87`). Nothing checks it.
6. All Bash conventions (logging, `set -E`, `# why:`). ShellCheck checks none of them.

**Enforced but unstated (or stated only in a non-loaded place)**
1. The ruff rule set itself (`pyproject.toml:70-95`), the global edit-time ruff hook (`ruff-format.sh`), and the security-guidance plugin hooks. No auto-loaded rule mentions any of them. `CLAUDE.md:63` names only the skill.
2. `security-static-check.sh` patterns and the `[security-bypass:]` marker. They are documented in the project `CLAUDE.md`, which is gitignored and therefore unshipped, and in the agent files. No auto-loaded rule states the security conventions they enforce.
3. import-linter layering (`.importlinter`). It is forge-local and absent from `engineering-standards.md` §2's SoC text.
4. The `TDD-Waiver` enum's extra waivers (`refactor`, `prototype`, `hotfix-emergency`), which the rule does not list.
5. Ponytail's YAGNI doctrine. It is auto-injected every session (~1k tokens) by a third-party plugin and appears in no forge or global rule.

**Contradictory**
1. Ponytail vs `engineering-standards.md` §2 on abstractions, file count and test depth.
2. TDD skip list in the rule vs the code (`engineering-standards.md:84-85` vs `plan_parsers.py:47-48`).
3. Impact analysis "ALL code changes" (`operational-constraints:154`) vs "skip single-file/docs/config/tests" (`CLAUDE.md:99`).
4. Debug env var (4 names), log format (2), and hook-log path (2) across the logging skill, `bash-defensive-patterns`, and the forge hooks.
5. Ruff hook "reports" prints (`logging-and-comments:105`) vs `>/dev/null` (`ruff-format.sh:14`).

## Not pursued
- `~/.claude/skills/logging-and-comments/references/python.md` was only spot-read (lines 23-33, 119-120). A full read may hold more conventions or conflicts.
- Superpowers `test-driven-development` and mattpocock `tdd` skill bodies: located but not read, so their conflicts with the rule are unknown.
- security-guidance plugin: neither the full `patterns.py` rule list nor its LLM-review prompt was read for overlap with `security-auditor`.
- `future-proofing-auditor.md` and `context7-evidence-auditor.md` thresholds were not read beyond the `execute-aa-ma-milestone.md:797-798` summary.
- Conventional Commits enforcement (`git-conventions.md:3`, commitizen, `aa-ma-commit-signature.sh`) is outside the six requested topics.
- Whether `scripts/install.sh` writes the `~/.claude/settings.json` hook wiring was not checked.
- Global `~/.claude/docs/lessons.md` and project `.claude/docs/lessons.md` may state code conventions as lessons; they were not scanned.
- ShellCheck pass/fail status of the current tree (whether CI is green) was not run.
- Other global skills that may state conventions (e.g. `llm-output-safety`, `env-var-drift`, `doc-drift-detection` named at `CLAUDE.md:100`) are outside the caller's list.
- `~/.claude/hooks/lib/guard-protected-dirs.sh` (the logging skill's reference pattern) was not read.
- This report was written despite a generic environment note discouraging report `.md` files. The caller's ticket and the agent contract explicitly require this one file.
