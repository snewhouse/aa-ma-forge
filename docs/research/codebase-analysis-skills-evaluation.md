# Do `/assess-codebase` + `/understand-codebase` beat the local `/codebase-deep-dive`?

**Created:** 2026-10-01
**Author:** M7 evaluation (Ticket 10) of AA-MA plan `codebase-analysis-skills`
**Verdict:** **CONDITIONAL PASS** (accepted by Ste, 2026-10-01). AC2–AC7 pass. AC1 passes on 2 of 3 repos and
fails on the private repo by a small, consistent citation-density margin. Two rounds were run; round 1 failed AC3
and led to a fix (below).

## Setup

| | |
|---|---|
| Repos | aa-ma-forge at `26ba674` (751 tracked files); honojs/hono at `6abd35b` (583 tracked); a private Python repo (154 tracked files, 47 `.py`; never named here, L-029) |
| Old side | the local `/codebase-deep-dive` command, run verbatim on forge and hono; the private repo used its existing 2026-09-17 report (6 files) |
| New side | `/assess-codebase` Standard, then `/understand-codebase` Standard absorbing that report (R6) |
| Where | scratch clones outside this repo; nothing was written to the targets' remotes |
| Judges | 2 fresh general-purpose agents per repo per round. Old and new sets were anonymised as A/B in seeded random order (round 1 seed `20261001`, round 2 seed `20261002`). Tool names were masked. Each judge sampled 21–25 claims per set (judge 2 from the end of each file), checked them against the code, and scored them. |

## Round 1 — pass bar not met

| Repo · judge | Accuracy new / old | Density new / old | New Crit/High that fail (checked) |
|---|---|---|---|
| forge J1 | 0.955 / 0.909 | 0.870 / 0.455 | 10/10 of 30 |
| forge J2 | 0.957 / 0.909 | 0.826 / 0.455 | 10/10 of 30 |
| hono J1 | 0.958 / 1.000 | 0.792 / 0.625 | 10/10 of 204 |
| hono J2 | 1.000 / 1.000 | 0.714 / 0.619 | 10/10 of 204 |
| private J1 | 1.000 / 0.870 | 0.760 / 0.680 | 10/10 of 2565 |
| private J2 | 1.000 / 1.000 | 0.739 / 0.783 | 10/10 of 2565 |

**AC3 failed on every repo.** Every measured secret-pattern match was reported as `high`
(`src/aa_ma/analysis/measure.py` `_secret`), and the refuter only sees judged findings. So test fixtures,
placeholders, sha1 keys and variable names shipped as unrefuted High findings: 60 of 60 sampled failed.

**Fix (sub-steps 7.5–7.6, refined after the §6.8 review):**
- A measured hit is `high` only for a precise provider rule (AWS, GitHub, Slack, private key, JWT …) outside test and fixture paths. That keeps a real key in shipped code at High, even in Quick, which runs no judge.
- Every other hit (generic rules, or any hit in a test or fixture path) is `medium` "possible secret (…, unverified)".
- The security judge is given the measured hit locations, never values, and reports each live-looking hit once as a judged `security.live-secret` at high/critical, so the refuter checks it. It treats a "fixture", "example" or "dummy" label as a claim to verify.
- Re-applying the refined rule to every round-2 finding still gives 0 High on all 3 repos. Every provider-rule hit (hono: 49 `jwt`, 2 `private-key`) is in a test file, so the judged reports are unchanged in severity.
- Fidelity note: in round 2 I gave the security judges the measure.json path myself. That input now ships in the skill (SKILL.md Step 5).
- A target's own `.gitleaks.toml` is still never obeyed, so a target cannot hide its own secrets.
- Tests were written first. The full suite is green.

## Round 2 — after the fix

Assess was re-run on all 3 repos. The understand packs were not touched or hand-edited.

| Repo · judge | Accuracy new / old | Density new / old | New Crit/High that fail | Preference |
|---|---|---|---|---|
| forge J1 | 0.957 / 0.875 | 0.875 / 0.480 | 0 (none) | new |
| forge J2 | 0.957 / 0.920 | 0.792 / 0.480 | 0 (none) | new |
| hono J1 | 1.000 / 1.000 | 0.958 / 0.609 | 0 (none) | old |
| hono J2 | 1.000 / 0.955 | 0.773 / 0.636 | 0 (none) | old |
| private J1 | 1.000 / 0.952 | **0.773 / 0.826** | 0 (none) | new |
| private J2 | **0.920 / 0.960** | **0.760 / 0.840** | 0 (none) | old |

### Disagreements

- Private J2 counted the claim "44 commits carry a session trailer" as false. A `git log` count gives 44, so the claim is true.
  - Rescored, new accuracy would be 0.958, still under 0.960.
  - The recorded judge scores stand.
- Preferences split 3–3. The judges who preferred old gave two reasons:
  - the volume of `medium` secret matches (204 and 2565) buries the real findings in the assessment report;
  - the old reports had sharper code-level findings.

  Accuracy and density still favour new on forge and hono.

## Pass bar

| # | Criterion | Result | Evidence |
|---|---|---|---|
| AC1 | new ≥ old on accuracy and density, both judges, all 3 repos | **FAIL on the private repo** (3 of 4 comparisons); PASS on forge and hono | Round 2 table. The density gap (−0.05, −0.08) also showed in round 1, so it is systematic. |
| AC2 | zero secret values in any new output | PASS | gitleaks 8.18.0 (`detect --no-git --redact`) and a regex pass over every new report dir, ONBOARDING.md, `.claude/onboarding/` and AGENTS.* found 0. `scan-secrets` exited 0 on all 6 report dirs (both rounds). All 12 judges counted 0 secret values in new outputs. The old private report reprints a dev-default placeholder. |
| AC3 | zero Critical/High findings that fail the claim check | PASS (round 2) | New side has 0 critical/high on all 3 repos. Round 1 failed 60/60; fixed in `419751f`. |
| AC4 | ABSENT/UNKNOWN tools record `command -v` / rc | PASS | Table below |
| AC5 | the understand Provenance block shows the fresh assess report absorbed, on all 3 repos (R6) | PASS | "assess-codebase report — absorbed (fresh, sha12 …)" with `26ba674208d5`, `6abd35b0a5f3` and the private repo's own sha12 |
| AC6 | runtime per repo per side | recorded | Table below |
| AC7 | L-029 name gate before every commit | PASS | `git diff --cached \| grep -F -i -f names.txt` exited 1 before each M7 commit; the names file lives outside the repo |

### Tools (AC4)

| Tool | `command -v` | Status in Standard runs |
|---|---|---|
| lizard | rc=1 | absent |
| jscpd | rc=1 | absent |
| osv-scanner | rc=1 | skipped (Standard never runs network tools) |
| semgrep | found | skipped (Standard) |
| pip-audit | found | skipped (Standard) |
| gitleaks | found | ran |
| codemem (hot spots, co-changes, owners, layers, dead code) | — | ran |

### Runtime (AC6, not gated)

| Repo | Old deep-dive | New assess (round 1) | New understand |
|---|---|---|---|
| forge | 458 s | 262 s | 510 s |
| hono | 495 s | 255 s | 393 s |
| private | not recorded (existing report) | 435 s | 514 s |

Round-2 assess ran on all 3 repos concurrently, taking about 336 s wall-clock each. That figure includes repairing a
prompt-generation slip in the evaluation harness, not in the skill.

## Known gaps carried forward

1. **Citation density on small repos.** The new understand pack cites less densely than a short, terse legacy
   report. Candidate fix: require a `path:line` per factual unit in the understand templates.
2. **Measured-secret volume.** `medium` is the right severity, but thousands of rows (sha1 artefact keys, test
   fixtures) still bury real findings. Candidate fix: collapse measured secret hits to one finding per file and
   rule, with a count.
3. **Other measured HIGH sources** (semgrep ERROR, lizard CCN, fixable vulns, and now provider-rule secrets in
   shipped code) bypass the refuter by design. None fired in these runs; review them before Deep is evaluated.
4. **Path heuristic ceiling.** A real key committed under a test or fixture path ships as `medium`. The security
   judge, which now sees every hit location, is the net.

Raw judge JSON, blind keys, fidelity notes and both rounds' reports are kept outside the repo (scratch). The
private repo's material never enters this repo.
