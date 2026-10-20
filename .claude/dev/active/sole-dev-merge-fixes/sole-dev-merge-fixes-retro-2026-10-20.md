# Retro: /sole-dev-merge — the fix → review → new finding loop

- **Date:** 2026-10-20
- **Scope:** `sole-dev-merge-pr-workflow` (May 2026, built v2) and `sole-dev-merge-fixes` M1–M5 (PRs #42–#46, 2026-10-15 → 10-18)
- **Evidence:** five read-only audits (loop forensics with 255 classified findings, plan audit, design audit, workflow audit, external research). They were session scratch and are not kept; their numbers come from this plan's own files, git and `gh`, and the headline numbers were re-checked by hand at main `d834563`.

## 1. What happened (measured)

| | M1 | M2 | M3 | M4 | M5 |
|---|---|---|---|---|---|
| Planned effort | 2 d | 1 d | 1 d | 0.75 d | 1 d |
| Commits in PR | 25 | 18 | 22 | 39 | 40 |
| Commits after the gate | 0 | 5 | 4 | 22 | 14 |
| Live merge runs | 0 | 2 | 2 | 5 | 3 |

- **144 commits** in the "fixes" plan. 55% of them came after the first review, and 40% of code and test insertions were driven by review. In M4/M5 the review-driven insertions were 1.7–1.8× the planned work.
- **17 review rounds** produced 197 findings: §6.8 found 2 CRITICAL / 46 WARNING / 76 INFO, and live Stage D found 0 CRITICAL / 1 HIGH / 10 MEDIUM / 62 LOW.
- **The finding counts never converged.** Live runs found 7, 6, 5, 7, 4 (M4) and 8, 7, 9 (M5). M5 ended only because Ste set a stop rule.
- **Fix-of-fix:** 17 of 28 code commits (61%) rewrote code added earlier in the same PR, and 9 of those rewrote an earlier fix-of-fix.
- **Growth:** the skill went from 1,162 to 1,963 lines (78% of that is bash in markdown) and its tests from 2,363 to 4,002 lines. The pre-compact hook went 192 → 329 → 314 lines, for a fix whose core was about 15 lines.

### The number that matters
**0 of 255 classified review findings were a bug that bit in real use.** Every real bug was found by using the tool:
- `--delete-branch` from a worktree, which recurred on 6 PRs;
- check-conventions exiting with rc 2;
- `gh pr edit` failing silently;
- pre-compact writing into main.

The predecessor's 102 review findings missed all of them, and its stub-based test *asserted* the buggy `--delete-branch` call. In short, review was aimed at hypothetical defects (33%), docs and style (51%) and bugs created by earlier fixes (9%), while reality found the bugs that mattered.

## 2. Root causes (Socratic chain)

**Why did the loop not end?** Fresh LLM reviewers report different findings every run (non-deterministic, arXiv 2502.20747). A MEDIUM held the merge exactly like a HIGH. Every applied fix restarted the run from Stage A on a growing diff. Nothing defined "done": there was no severity bar, no round cap and no memory of the previous run. Stage A even deletes the previous run's findings.

**Why was there no exit?** Neither plan stated a threat model or review exit criteria. The workflow's reviewer prompts have no threat model; the security-auditor asks web-app questions about a local CLI. They also have no impact or likelihood rubric and no round cap. So each round widened the assumed attacker (hostile `.git`, old git, locales, control characters), and nobody decided the scope.

**Why were there so many findings?** Because of the design:
- 1,526 lines of bash are copied by the model out of markdown. Copy-execution forces a state file, and the state file became a security surface (PR #43 added 430 lines).
- The 26-line loader is copied 13 times, and a test enforces that the copies stay identical. Each fix therefore lands in up to 14 places.
- GitLab code (about 10%) serves a remote Ste never uses.
- The diffs were far beyond the 200–400 LOC at which review stays effective.

**Why didn't the plan and prototypes prevent it?**
- Prototypes tested *mechanics* (where stdin cwd points) but never the *decision on the real environment*. Plan dirs are tracked, so every worktree has one, and that fact falsified M5's plan Risk 3.
- A CRITICAL that falsified a plan risk was patched in flight instead of triggering a re-plan.
- The final plain rule was already in the plan (plan:541). Getting back to it took about 2 hours and 14 commits.
- The predecessor verified against PATH stubs, so it certified its own bug.

**Why didn't I stop it?** The answers were already written down:
- Global **L-1299** (2026-09-29): at round 3, ask Ste for the threat model and agree how the loop ends.
- **L-1294**: never write a third patch; redesign instead.

I had read both and applied neither. I recommended "Apply" on nearly every MEDIUM/LOW. I built the GitLab scope the plan had explicitly deferred, until Ste asked "why glab?". I treated thoroughness as quality.

**Why do lessons not fire?**
- Lessons are prose in a 534-entry file with 29 duplicate IDs. Nothing loads the right one at the decision point.
- 22 of 24 project lessons written in that window *add* a check. One limits work: L-060, written on the last day.
- The self-improvement rule only tightens ("stricter … until mistake rate drops to zero"). It has no step that weighs cost or retires a rule.
- Global **L-189** says "stop only when a round finds zero issues". Fresh reviewers never report zero issues, so that lesson guarantees the loop.

**Root cause in one line:** verification had no exit criterion and no threat model, so it optimised for finding things instead of shipping working software. A copy-paste design inflated what there was to find, and the guardrails that already existed lived in lessons files instead of in the skills that run at the decision point.

## 3. Did we follow rigor (KISS, DRY …)?
- **KISS: no.** A merge helper became about 6,000 lines of skill and tests. A ~700-line script design keeps every real requirement.
- **DRY: no.** There are 13 copies, and the tests protect the duplication.
- **YAGNI: no.** The GitLab and dual-remote code, the S602 auto-fix, the banner and the strategy fallback have never been used.
- **"Verify empirically": partly.** The live runs found every real bug, but the stub tests passed the bug, and review effort went where reality did not.
- **"Break nothing": yes.** Nothing broke on main.

The rigor rules were applied one-sidedly: "verify more" was read as an order to add more code, and nothing pushed for less.

## 4. What changes (smallest first)
1. **Wire the stop rule where it runs.** This is the P1 TODO, and it is about 30 lines:
   - Stage D blocks only on CRITICAL/HIGH that show a failure path under the stated threat model. MEDIUM/LOW go to PR notes and TODOS.
   - No restart from Stage A after a fix; the second pass reviews only the fix's lines.
   - At most 2 review rounds per PR.
   - Keep the last run's findings and give them to the reviewers as "already decided".
2. **Threat model at plan time.** Add one `Threat-Model:` line to each milestone Contract, for example "sole dev, own repos, trusted machine; out of scope: hostile repo-local config, concurrent attacker". The security-auditor and Stage C prompts read it.
3. **Reality before review.** For tooling, the first gate is a live run of the smallest working version on the real environment. Never certify against stubs alone.
4. **Re-plan trigger.** A CRITICAL that falsifies a plan risk stops the milestone and goes to Ste. It is not patched in flight.
5. **Lessons that fire.** A lesson meant to change behaviour gets wired into a skill, prompt or gate within the same plan, or it is marked `unwired`. Every new rule says what it costs and what it replaces. Fix L-189.
6. **Simplify /sole-dev-merge**, through its own short plan with a prototype and a live run first:
   - cut GitLab and the dead features;
   - then either share one `lib/state.sh`, or rewrite as one bats-tested script with no state file (~85–90% smaller).

**Irony guard:** the fix for over-engineering must not become another 144-commit plan. Items 1–2 are one small PR under its own rule: at most 2 review rounds, and only CRITICAL/HIGH block.

**Outcome (2026-10-20):** items 1–2 landed as PR #47 (`57897d3`) in one review round with 0C/0H; its 4 MEDIUM + 7 LOW went to one TODOS entry. Lessons: forge L-060 (repeat), L-061, L-062; global L-1358, L-189 corrected, L-1299 (repeat), L-141 corrected (worktrees share `origin/HEAD`). Open TODOs: the threat-model wording for non-tooling repos (P1), install.sh pinned to a live clone then plain branches (P2), the /sole-dev-merge simplification (item 6).

## 5. What went well
- plan-verification caught 17 CRITICAL issues before M1, and M1 shipped clean with 0 commits after its gate.
- Every bug that was actually targeted is fixed and live; main stayed green throughout.
- The live merge runs worked as the reality check; they just came too late and were run too many times.
- Ste's interventions ("why glab?", "have we over engineered …?") were the real circuit breaker. The workflow should have tripped first.
