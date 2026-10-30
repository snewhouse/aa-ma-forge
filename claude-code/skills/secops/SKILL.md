---
name: secops
description: "Security review, dependency audit and scanner choice: routes each artifact to its scanner (Ruff S for Python, gitleaks for secrets, pip-audit for the Python lock, osv-scanner for JS, R and other lockfiles, ShellCheck for shell), names each finding's rule and CWE, and sets the layer each check runs at (edit, commit, CI). Use when reviewing code or a file for security problems (load it before reading the code), auditing dependencies for known vulnerabilities, or choosing a repo's security checks."
---

# SecOps router

Pick the check for the artifact, run it at the earliest layer that can block, and fail loud: a scanner that did not run reports UNKNOWN, never zero findings. This skill routes; the tools do the work.

## Which scanner

| Artifact | Scanner | How |
|----------|---------|-----|
| Python source | Ruff S rules (flake8-bandit) | `ruff check --select S <paths>`; suppress only per site, `# noqa: Sxxx  # why: …` |
| Secrets in any file or commit | gitleaks | `gitleaks detect --redact --exit-code 1 --log-opts="--all"`; ignores are reviewed fingerprints in `.gitleaksignore`, never path or regex allowlists |
| Python dependencies (uv / pip lock) | pip-audit (`uv audit` once it is GA) | `uv export --frozen --no-emit-workspace --no-emit-project -o req.txt` then `pip-audit --disable-pip --require-hashes --strict -r req.txt`; each ignore carries an ID, a why and an expiry date |
| Other lockfiles: JS (`package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lock`), R (`renv.lock`), Go (`go.mod`), Rust (`Cargo.lock`), Java (`pom.xml`, `gradle.lockfile`), Ruby (`Gemfile.lock`), PHP (`composer.lock`), .NET (`packages.lock.json`) | osv-scanner | `osv-scanner scan -L <file>` |
| Shell scripts | ShellCheck | `shellcheck --enable=check-set-e-suppressed <files>` |
| GitHub Actions and the lock itself | Dependabot | `github-actions` + the package ecosystem, weekly, with a cooldown |

## Reviewing a file

1. Run each scanner the table routes the file to: its language scanner, plus gitleaks. If one cannot run here, say so (UNKNOWN) and review by reading.
   For code you did not write, use your config, not the repo's: its config and inline suppressions can hide its own findings. Ruff: `ruff check --isolated --ignore-noqa --select S`. gitleaks: `-c <your config> -i <your ignore dir>`. ShellCheck: `--norc`. No flag turns off an inline `# gitleaks:allow` or `# shellcheck disable=`, so report each one the change adds, and any edit to scanner config, as a finding.
2. Report each finding with its rule and CWE, the line, and the fix at the source. For example, `subprocess.run(cmd, shell=True)` with interpolated input is Ruff S602 (CWE-78, command injection); the fix is an argv list without a shell, not an escape.
3. Then check what scanners miss: validation at trust boundaries (`Skill(defense-in-depth)`), secret handling (`Skill(secrets-management)`) and model output used as input (`Skill(llm-output-safety)`).

## Which layer

| Layer | What runs | Blocks? |
|-------|-----------|---------|
| Edit | the language formatter/linter hook (findings reach the model) | no — advisory |
| Commit | a staged-file check: high-signal Ruff S rules + a secret-literal regex; `gitleaks protect --staged` | yes — exit 2, with an auditable bypass marker; a best-effort guardrail, not a boundary |
| CI | full Ruff S over the gated paths, gitleaks over full history, the hashed dependency audit | yes — the merge gate |
| Weekly | the same CI jobs on a schedule, plus Dependabot | surfaces new advisories without a push |

Pin every scanner (version and checksum, or a commit SHA), take it from the project's locked environment, and never run a binary the scanned repo ships.

## Standards to cite

Cite by name and edition, not by guessed IDs: OWASP ASVS 5.0 for verification requirements, OWASP Top 10:2025 for risk classes, NIST SSDF (SP 800-218) for the practice areas. Do not cite SSDF 1.2 practice IDs: 1.2 was still a draft when this was written (2026-10), so its IDs may change before it is final.

## Related

- `Skill(secrets-management)` — storing, injecting and rotating secrets; secret scanning set-up.
- `Skill(defense-in-depth)` — validation at trust boundaries.
- `Skill(llm-output-safety)` — model output is untrusted input.
