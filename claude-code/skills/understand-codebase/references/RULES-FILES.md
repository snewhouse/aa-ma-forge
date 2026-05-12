# RULES-FILES — agent-instruction & convention file detection list

The "Rules & agent instructions" dimension (DIMENSIONS.md §11). Detect each file/dir below; for
each that exists, write a **one-line summary of what it mandates** into the onboarding doc. For
large `AGENTS.md` / `CLAUDE.md`, add a 3–5-bullet digest of the *binding* rules. **Read these for
the rules they state — never to extract a secret.** Some of these (`.env*` templates) are
explicitly out of bounds for content (names only).

## Detection command (run first)

```bash
# One pass: list which of the known rules/convention files exist at the repo root and common subdirs.
for f in \
  CLAUDE.md AGENTS.md .agentrc AGENT.md GEMINI.md \
  .cursorrules .windsurfrules .clinerules .aider.conf.yml .aiderignore \
  .github/copilot-instructions.md .github/CONTRIBUTING.md .github/CODEOWNERS .github/PULL_REQUEST_TEMPLATE.md \
  .github/dependabot.yml .github/dependabot.yaml renovate.json .renovaterc .renovaterc.json \
  CONTRIBUTING.md CONTRIBUTING.rst DEVELOPING.md DEVELOPMENT.md HACKING.md \
  SECURITY.md SECURITY.rst CODE_OF_CONDUCT.md GOVERNANCE.md MAINTAINERS.md OWNERS CODEOWNERS \
  .editorconfig .gitattributes .gitignore .dockerignore .npmrc .nvmrc .node-version .python-version .ruby-version .tool-versions mise.toml .sdkmanrc .ruby-gemset \
  .pre-commit-config.yaml .pre-commit-config.yml lefthook.yml lefthook.yaml .husky/ .commitlintrc .commitlintrc.json commitlint.config.js .czrc .cz.toml release-please-config.json .release-please-manifest.json .changeset/config.json \
  .prettierrc .prettierrc.json .prettierrc.yml .prettierrc.js prettier.config.js .eslintrc .eslintrc.json .eslintrc.js eslint.config.js eslint.config.mjs .stylelintrc \
  ruff.toml .ruff.toml .flake8 .pylintrc setup.cfg tox.ini mypy.ini .mypy.ini pyrightconfig.json \
  .rubocop.yml .golangci.yml .golangci.yaml rustfmt.toml .rustfmt.toml clippy.toml checkstyle.xml .scalafmt.conf .clang-format \
  Makefile Justfile justfile Taskfile.yml Taskfile.yaml magefile.go \
  .editorconfig README.md README.rst README ARCHITECTURE.md CHANGELOG.md \
  ; do [ -e "$f" ] && echo "FOUND  $f"; done
# Directories worth listing if present:
for d in .cursor/rules .github/workflows .github/ISSUE_TEMPLATE .vscode .devcontainer .claude .agents docs adr docs/adr docs/decisions docs/pdr .idea ; do [ -d "$d" ] && { echo "DIR    $d/"; ls -1 "$d" 2>/dev/null | head -20 | sed 's/^/         /'; }; done
```

## What each implies (summarise accordingly)

### AI / agent instruction files — HIGH PRIORITY
| File / dir | What it is | How to summarise |
|---|---|---|
| `CLAUDE.md` (root, and nested per-dir) | Claude Code project instructions — overrides default behaviour. | Digest the *binding* rules: commit conventions, test gates, no-AI-attribution, secret handling, "always/never" directives, pointers to `rules/`. Note nested CLAUDE.md files exist. |
| `AGENTS.md` | Generic agent-instruction file (cross-tool standard). Often large. | Same as CLAUDE.md — digest binding rules. **Don't load the whole thing if 100KB+**; read the headings + the first ~200 lines + any "MUST/NEVER" sections. |
| `.agentrc`, `AGENT.md`, `GEMINI.md` | Tool-specific agent configs (Gemini CLI etc.). | One line: "Gemini CLI instructions — see file". |
| `.cursorrules`, `.cursor/rules/*.mdc` | Cursor IDE rules (legacy single-file + new per-rule dir). | List the rule files; one line each on scope (e.g. "`*.tsx` → use function components"). |
| `.windsurfrules` | Windsurf IDE rules. | One line summary. |
| `.clinerules`, `.aider.conf.yml`, `.aiderignore` | Cline / Aider configs. | One line summary; note `.aiderignore` excludes files from AI context. |
| `.github/copilot-instructions.md` | GitHub Copilot custom instructions. | Digest the directives. |
| `.claude/` (project) | Project-local skills / agents / commands / rules / hooks / settings. | List `skills/` (read each `SKILL.md` header ~130 lines — surface skill-defined patterns), `agents/`, `commands/`, `rules/`, `hooks/`; note `settings.json` permissions if present (names only). |
| `.agents/` | Alternate location for project agents/skills. | Same treatment as `.claude/`. |

### Contribution & governance
| File | What it is | How to summarise |
|---|---|---|
| `CONTRIBUTING.md` / `.github/CONTRIBUTING.md` / `CONTRIBUTING.rst` / `DEVELOPING.md` / `DEVELOPMENT.md` / `HACKING.md` | The human contribution guide. | This is GOLD for the "Contribute safely" playbook — digest the PR process, branch rules, test requirements, review process, DCO/CLA. |
| `SECURITY.md` | Vulnerability disclosure policy. | One line: "report vulns via …; supported versions: …". |
| `CODE_OF_CONDUCT.md` | Community standards. | One line; note which CoC (Contributor Covenant etc.). |
| `GOVERNANCE.md`, `MAINTAINERS.md`, `OWNERS` | Project governance / maintainer list. | List maintainers / decision process. |
| `CODEOWNERS` / `.github/CODEOWNERS` | Path → required-reviewer mapping. | Table `path glob → owner(s)`; this drives "who reviews X". |
| `.github/PULL_REQUEST_TEMPLATE.md`, `.github/ISSUE_TEMPLATE/*` | PR/issue templates. | One line: "PRs must fill: …". |

### Editor / VCS / toolchain
| File | What it is | How to summarise |
|---|---|---|
| `.editorconfig` | Cross-editor whitespace/charset rules. | "indent: N spaces/tabs; final newline: yes/no; charset: …". |
| `.gitattributes` | Line-ending normalisation, linguist overrides, LFS, merge drivers, `export-ignore`, generated-file marks. | Note: LFS-tracked patterns, `linguist-generated`/`linguist-vendored` paths, `merge=` drivers, `-diff` binary marks. |
| `.gitignore`, `.dockerignore` | Ignored paths. | Note what's ignored (build dirs, secrets, IDE files) — informs "generated/vendored". |
| `.npmrc`, `.yarnrc.yml`, `.pip.conf` | Package-registry config. | "uses private registry at …" or "default registry"; note `save-exact`/`engine-strict`. |
| `.nvmrc`/`.node-version`/`.python-version`/`.ruby-version`/`.tool-versions`/`mise.toml`/`.sdkmanrc` | Toolchain version pins. | "requires Node X / Python Y / …" (these are dimension 5 & 2 too). |

### Hooks / commit / release tooling
| File | What it is | How to summarise |
|---|---|---|
| `.pre-commit-config.yaml` / `lefthook.yml` / `.husky/` | Local git-hook runners. | List the hooks (lint, format, test, secret-scan) — these run before every commit. |
| `.commitlintrc*` / `commitlint.config.js` / `.czrc` / `.cz.toml` | Commit-message linting / Commitizen. | "commits must follow Conventional Commits (enforced)". |
| `release-please-config.json` / `.changeset/` / `.bumpversion.cfg` / `goreleaser.yml` / `semantic-release` config | Release automation. | "releases are cut by <tool>; version bump driven by <commits/changesets>". |

### Linters / formatters / type checkers (= *claimed* conventions — verify against code in dim 9)
`.prettierrc*`, `.eslintrc*`/`eslint.config.*`, `.stylelintrc`, `ruff.toml`/`[tool.ruff]`, `.flake8`,
`.pylintrc`, `setup.cfg`, `tox.ini`, `mypy.ini`/`[tool.mypy]`, `pyrightconfig.json`, `.rubocop.yml`,
`.golangci.yml`, `rustfmt.toml`/`clippy.toml`, `checkstyle.xml`, `.scalafmt.conf`, `.clang-format`.
→ Summarise: "linter: X; formatter: Y; type checker: Z; key rules: …" — then dimension 9 checks
whether the code actually follows them.

### Build/task entry points (= "the contract")
`Makefile`, `Justfile`/`justfile`, `Taskfile.yml`, `magefile.go`, `package.json` `scripts`,
`pyproject.toml` `[project.scripts]`/`[tool.*]`, `tox.ini`/`noxfile.py`.
→ List the targets/scripts and what each does — this is the canonical "how do I X" surface.

### Docs / decision records
`README*`, `ARCHITECTURE.md`, `CHANGELOG*`, `docs/`, `docs/adr/`/`docs/decisions/`/`docs/pdr/` (+ their `INDEX.md`).
→ Note their existence & freshness (dimension 13 doc-drift); link them.

### Out of bounds for *content* (existence + variable names only)
`.env`, `.env.local`, `.env.production`, `.env.*` (any without "example/sample/template"),
`*.key`, `*.pem`, `*.p12`, `*.pfx`, `*.keystore`, `*.jks`, `id_rsa*`, `id_ed25519*`,
`credentials*`, `secrets*`, `*.tfstate`, `*.tfstate.backup`, `secring.*`,
`serviceAccount*.json`/`*-sa.json`/`gcp-key*.json`, `.netrc`, `.pgpass`, `kubeconfig`, `*.kubeconfig`.
→ Report only: "`.env` present (gitignored: yes/no) — NOT inspected"; "`.env.example` declares vars:
A, B, C (names only)".

## Output shape (into `.claude/onboarding/07-rules-and-agent-instructions.md` and a summary in `ONBOARDING.md`)

```markdown
## Rules & agent instructions

| File / dir | Present | What it mandates (one line) |
|---|:--:|---|
| CLAUDE.md | ✅ | Conventional Commits, no AI attribution, run `make test` before commit, secrets via Vault, see `rules/` |
| AGENTS.md | ❌ | — |
| .cursorrules | ✅ | `.tsx` → function components + hooks only; no `any` |
| CONTRIBUTING.md | ✅ | branch from `develop`; PR needs 1 approval + green CI; DCO sign-off required |
| CODEOWNERS | ✅ | `api/**` → @backend-team; `web/**` → @frontend-team |
| .pre-commit-config.yaml | ✅ | ruff, black, mypy, detect-secrets run on commit |
| .editorconfig | ✅ | 4-space indent, LF, UTF-8, trim trailing whitespace |
| .nvmrc | ✅ | Node 20 |
| .env | ⚠️ | present, gitignored — NOT inspected; see `.env.example` for variable names |
| … | | |

### Binding directives digest (from CLAUDE.md / AGENTS.md)
- …
- …

### Conflicts / things to know
- `.editorconfig` says 4 spaces but `.prettierrc` says 2 — Prettier wins for JS/TS; Python is 4. (→ also a "con")
```
