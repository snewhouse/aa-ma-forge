# 0022. SecOps baseline: Ruff S, gitleaks, a hashed dependency audit, and a whole-file commit hook

**Status:** Accepted
**Date:** 2026-10-12
**Deciders:** Stephen Newhouse (sole maintainer)
**Tags:** `security`, `ci`, `hooks`, `skills`

## Context and Problem Statement

Before this decision the forge's security checks could not fail:
- The Bandit CI job ended in `|| true`.
- The global `senior-secops` skill's scanner was a stub that always returned no findings.
- Nothing scanned for secrets or audited the dependency lock.
- The commit hook used five regexes on added lines.

The code-conventions-impact map (Ticket 10) asked: **what is the SecOps baseline, and where does each check run?**

## Decision Drivers

- Every check fails loud. A scanner that did not run is UNKNOWN, never zero findings.
- One tool per job, pinned, and taken from the locked environment; never a binary the scanned repo ships.
- Use what is already installed and fast (Ruff is already the linter).
- Exceptions are per site and auditable: a `# noqa` with a `why`, a fingerprint, or an ID with an expiry date. Never a blanket allowlist.

## Considered Options

1. **Ruff S replaces Bandit** everywhere (CI, commit hook, sole-dev-merge Stage C), plus gitleaks, pip-audit, Dependabot and a `secops` router skill.
2. **Keep Bandit, fix `|| true`** and add gitleaks and pip-audit beside it.
3. **Ruff S plus a narrow Bandit fallback** for the IDs Ruff lacks.

## Decision Outcome

**Chosen:** Option 1.

**Rationale:** A pinned comparison found no Bandit-only hit on this repo
([docs/research/code-conventions-impact-ruff-vs-bandit.md](../research/code-conventions-impact-ruff-vs-bandit.md)).
- Ruff 0.15.9 S reproduces all 39 Bandit 1.9.4 hits, call site for call site.
- 71 of Bandit's 75 tests map to an S rule.
- None of the 4 gaps can fire here (no torch, huggingface_hub or django).
- B404, which Ruff has only in preview, flags imports, and S603/S607 already report every call.

So a fallback would gate nothing (Option 3), and Option 2 keeps a second, slower tool for no coverage.

## Pros and Cons of the Options

### Option 1

- ✅ One fast tool, already locked; per-site `noqa` with a `why`
- ✅ The same rules at commit, in CI and in Stage C
- ❌ B613–B615/B703 have no S rule (revisit if torch, huggingface_hub or django enter the deps)

### Option 2

- ✅ No migration
- ❌ Two Python SAST tools, two suppression syntaxes, and a dependency kept only for itself

### Option 3

- ✅ Covers the gap IDs on paper
- ❌ Gates nothing on this codebase today; `-ll` would even hide B404 (LOW)

## Consequences

**Positive:**
- **CI** gates `ruff-security` (Ruff S over src/packages/scripts), `gitleaks` (full history, verified v8.18.4 tarball, fingerprint ignores) and `deps` (pip-audit over a hashed `uv export`, ignores with expiry). They run on push, on PRs and weekly.
- **Dependabot** covers Actions and uv weekly, with a 7-day cooldown.
- **Every job** uses `setup-uv` and `uv sync --locked`, and drops checkout credentials.
- **The commit hook** (`security-static-check.sh`) runs forge-pinned Ruff S102/S301/S307/S602/S604/S608 on the **whole** staged file, with `--isolated --ignore-noqa`. It fails closed when ruff errors, and the auditable bypass marker is the escape. Secret-literal and path-traversal regexes stay on added lines.
- **`secops`** routes a security question to scanner × layer.

**Negative:**
- Whole-file scanning means a commit that touches a file with a pre-existing site needs the bypass marker (here: 4 S608 sites in codemem). Three review rounds found bypasses in every "introduced lines only" filter, so that is the accepted cost (D8).
- 3 advisories are ignored until 2027-01-12 (fastmcp <3.2, diskcache) pending a fastmcp 3 / watchfiles 1 migration (TODOS).

**Neutral:**
- Bandit leaves the dev group; `BANDIT_BIN` gives way to `RUFF_BIN`; the global `senior-secops` skill is removed.

## Amendment (2026-10-13): the commit hook is a best-effort guardrail

Six background security review rounds kept finding bypasses in `security-static-check.sh`. It
infers what git will commit from the Bash command text, and the command text cannot settle
that: env-var commits (`GIT_INDEX_FILE`, `GIT_DIR`), `--git-dir <path>`, aliases, `cd <dir> && git commit`, `sh -c`,
and scripts all defeat it. **Decision (Ste):** the hook is an early guardrail, not a security
boundary. It fails closed on what it recognises; the forms above are named non-goals and are
not patched case by case. Enforcement lives in CI (`ruff-security`, `gitleaks`, `deps`) and the
repository's own pre-commit. Moving the hook's checks into a git pre-commit hook, which sees
the real index, is the upgrade path (TODOS).

## Example

```bash
uv run ruff check --isolated --select S src packages scripts      # CI gate
./gitleaks detect --redact --exit-code 1 --log-opts="--all"        # CI gate
uv run pip-audit --disable-pip --require-hashes --strict -r req.txt # CI gate
```

## Implementation Notes

The work is code-conventions-impact Milestone 8 (8.1–8.8): `.github/workflows/security.yml`,
`.gitleaksignore`, `.pip-audit-ignore`, `.github/dependabot.yml`,
`claude-code/hooks/security-static-check.sh`, sole-dev-merge Stage C/D, and
`claude-code/skills/{secops,secrets-management,defense-in-depth}`.

## References

- [docs/research/code-conventions-impact-ruff-vs-bandit.md](../research/code-conventions-impact-ruff-vs-bandit.md) — comparison and §deps triage
- [ADR-0018](0018-touched-code-lint-gate.md) — the touched-files harness Ruff S runs inside
