# PLAYBOOK-CONTRIBUTE — "how to contribute safely" template

Dimension 15. This is the section a newcomer reads before their **first change**. It must be
**codebase-specific**: every step cites a real command, file, or convention from *this* repo. If a
step's answer is "couldn't determine", write `not found — gap` (which is itself useful: it tells
the newcomer the project lacks that guardrail).

Fill the template below; delete anything that genuinely doesn't apply. Pull facts from dimensions
7 (CI), 9 (conventions), 10 (versioning/git), 11 (rules files — especially `CONTRIBUTING.md`),
13 (here-be-dragons), and `Skill(impact-analysis)` for the ritual.

---

```markdown
## Contribute safely

> Provenance: <date> · <short-SHA> · derived from CONTRIBUTING.md / CI config / git history (or "no CONTRIBUTING.md — inferred from CI + git log")

### 0. Before you touch anything
- Read: `<README.md>`, `<CONTRIBUTING.md>` (if present), `<CLAUDE.md>/<AGENTS.md>` (the binding rules), `<ARCHITECTURE.md>` (if present).
- Get it running: `<the quick-start command block from dimension 5>` — confirm the test suite is green *before* you change anything: `<test command>`.
- Know the dragons (don't edit without sign-off): `<list from dimension 13 — vendored/generated/frozen paths, e.g. `vendor/`, `*_pb2.py`, `src/legacy/`>`.

### 1. Branch
- Branch from: `<main / develop / trunk>` (branching model: `<trunk-based / GitHub-flow / git-flow>` — from dimension 10).
- Name it: `<convention, e.g. `feat/<ticket>-short-desc`, `fix/...`>` (observed in `git branch -a`).
- `git checkout <base> && git pull && git checkout -b <your-branch>`.
- (If a sibling AI/human session is active on the same plan/branch → use a git worktree: `git worktree add .worktrees/<branch> <branch>` — per `rules/plan-authoring-standards.md`.)

### 2. Make the change — following the conventions
- Code style / naming / imports / error handling / logging: `<the dominant patterns from dimension 9, with a cited example file to imitate, e.g. "model your module on `src/foo/bar.py`">`.
- Linter / formatter / type checker: run `<lint cmd>`, `<format cmd>`, `<typecheck cmd>` (configs: `<.eslintrc / ruff.toml / .golangci.yml ...>`). These also run in CI — fixing them now saves a round-trip.
- Where the file goes: `<from dimension 4 — "X goes in `path/` named `pattern`">`.
- Pre-commit hooks: `<from .pre-commit-config.yaml / .husky/ — what runs on commit>` (`pre-commit run --all-files` to check ahead of time).

### 3. The impact-analysis ritual (REQUIRED before touching shared/core code)
Before editing anything imported by 2+ other modules (or anything under `<core/ shared/ common/ lib/>`):
- Run `Skill(impact-analysis)` — or manually: who calls this? (`<PROJECT_INDEX.json` MCP `who_calls` / `sg run -p '<fn>($$$)'`> ) what's the blast radius? does the contract change? are the callers tested?
- If the change is non-trivial / multi-file → consider `/aa-ma-plan` first (per `CLAUDE.md` workflow modes).
- Resolve any HIGH-risk impact before opening the PR.

### 4. Test
- Add/extend tests next to the code: `<test layout & framework from dimension 6, with an example test file to imitate>`.
- Run the tiers you can: `<fast: cmd>` always; `<full: cmd>` before pushing; `<live/integration: cmd + what it needs>` if your change touches that area.
- Coverage expectation: `<from dimension 6/13 — or "no enforced threshold; match the surrounding files">`.
- Don't leave the suite red. (`rules/python-quality-gates.md` philosophy — zero tolerance.)

### 5. Commit
- Message format: `<Conventional Commits / project style — from dimension 10 + `.commitlintrc` if present>`. Example from this repo: `<a real recent commit message>`.
- Attribution: `<e.g. "no AI/co-authored-by attribution" if CLAUDE.md says so>`.
- Sign-off: `<DCO `Signed-off-by` / CLA — from CONTRIBUTING.md>` (or "not required").
- Commit small and often; push: `git push -u origin <your-branch>`.

### 6. Open the PR
- Target branch: `<base>`.
- Fill the PR template: `<.github/PULL_REQUEST_TEMPLATE.md fields>` (or "no template").
- CI must pass — these checks block the merge: `<from dimension 7 — the blocking jobs>`.
- Reviewers: `<from CODEOWNERS — which paths route to whom>` (or "no CODEOWNERS — request a maintainer").
- Approvals required: `<N>` (from branch-protection hints / CONTRIBUTING.md, or "unknown").

### 7. After merge
- `<how it gets released — from dimension 10: automatic on tag / release-please PR / manual>`.
- `<how it gets deployed — from dimension 10>`.
- Delete your branch.

### Your suggested "good first PR"
`<A concrete, low-risk task grounded in THIS repo: a real `TODO`/`FIXME` (cite `file:line`), an open issue, a doc-drift fix from dimension 13, or a missing test on a small module. Include the exact files to touch and how to verify. If nothing obvious → suggest "add tests to `<the least-tested small module>`" with the path.>`

### Anti-patterns in this repo (things past PRs got dinged for, if discoverable from `git log`/PR history)
- `<e.g. "mixing async and sync — see `git log --grep=async`">`
- `<...>`
```
