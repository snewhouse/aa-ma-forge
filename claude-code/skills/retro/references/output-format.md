### Step 13: Save Retro History

After computing all metrics (including streak) and loading any prior history for comparison, save a JSON snapshot:

```bash
mkdir -p .context/retros
```

Determine the next sequence number for today (substitute the actual date for `$(date +%Y-%m-%d)`):
```bash
# Count existing retros for today to get next sequence number
today=$(TZ=America/Los_Angeles date +%Y-%m-%d)
existing=$(ls .context/retros/${today}-*.json 2>/dev/null | wc -l | tr -d ' ')
next=$((existing + 1))
# Save as .context/retros/${today}-${next}.json
```

Use the Write tool to save the JSON file with this schema:
```json
{
  "date": "2026-03-08",
  "window": "7d",
  "metrics": {
    "commits": 47,
    "contributors": 3,
    "prs_merged": 12,
    "insertions": 3200,
    "deletions": 800,
    "net_loc": 2400,
    "test_loc": 1300,
    "test_ratio": 0.41,
    "active_days": 6,
    "sessions": 14,
    "deep_sessions": 5,
    "avg_session_minutes": 42,
    "loc_per_session_hour": 350,
    "feat_pct": 0.40,
    "fix_pct": 0.30,
    "peak_hour": 22,
    "ai_assisted_commits": 32
  },
  "authors": {
    "Garry Tan": { "commits": 32, "insertions": 2400, "deletions": 300, "test_ratio": 0.41, "top_area": "browse/" },
    "Alice": { "commits": 12, "insertions": 800, "deletions": 150, "test_ratio": 0.35, "top_area": "app/services/" }
  },
  "version_range": ["1.16.0.0", "1.16.1.0"],
  "streak_days": 47,
  "tweetable": "Week of Mar 1: 47 commits (3 contributors), 3.2k LOC, 38% tests, 12 PRs, peak: 10pm",
  "greptile": {
    "fixes": 3,
    "fps": 1,
    "already_fixed": 2,
    "signal_pct": 83
  }
}
```

**Note:** Only include the `greptile` field if `~/.gstack/greptile-history.md` exists and has entries within the time window. Only include the `backlog` field if `TODOS.md` exists. Only include the `test_health` field if test files were found (command 10 returns > 0). If any has no data, omit the field entirely.

Include test health data in the JSON when test files exist:
```json
  "test_health": {
    "total_test_files": 47,
    "tests_added_this_period": 5,
    "regression_test_commits": 3,
    "test_files_changed": 8
  }
```

Include backlog data in the JSON when TODOS.md exists:
```json
  "backlog": {
    "total_open": 28,
    "p0_p1": 2,
    "p2": 8,
    "completed_this_period": 3,
    "added_this_period": 1
  }
```

### Step 14: Write the Narrative

Structure the output as:

---

**Tweetable summary** (first line, before everything else):
```
Week of Mar 1: 47 commits (3 contributors), 3.2k LOC, 38% tests, 12 PRs, peak: 10pm | Streak: 47d
```

## Engineering Retro: [date range]

### Summary Table
(from Step 2)

### Trends vs Last Retro
(from Step 11, loaded before save — skip if first retro)

### Time & Session Patterns
(from Steps 3-4)

Narrative interpreting what the team-wide patterns mean:
- When the most productive hours are and what drives them
- Whether sessions are getting longer or shorter over time
- Estimated hours per day of active coding (team aggregate)
- Notable patterns: do team members code at the same time or in shifts?

### Shipping Velocity
(from Steps 5-7)

Narrative covering:
- Commit type mix and what it reveals
- PR size discipline (are PRs staying small?)
- Fix-chain detection (sequences of fix commits on the same subsystem)
- Version bump discipline

### Code Quality Signals
- Test LOC ratio trend
- Hotspot analysis (are the same files churning?)
- Any XL PRs that should have been split
- Greptile signal ratio and trend (if history exists): "Greptile: X% signal (Y valid catches, Z false positives)"

### Test Health
- Total test files: N (from command 10)
- Tests added this period: M (from command 12 — test files changed)
- Regression test commits: list `test(qa):` and `test(design):` and `test: coverage` commits from command 11
- If prior retro exists and has `test_health`: show delta "Test count: {last} → {now} (+{delta})"
- If test ratio < 20%: flag as growth area — "100% test coverage is the goal. Tests make vibe coding safe."

### Focus & Highlights
(from Step 8)
- Focus score with interpretation
- Ship of the week callout

### Your Week (personal deep-dive)
(from Step 9, for the current user only)

This is the section the user cares most about. Include:
- Their personal commit count, LOC, test ratio
- Their session patterns and peak hours
- Their focus areas
- Their biggest ship
- **What you did well** (2-3 specific things anchored in commits)
- **Where to level up** (1-2 specific, actionable suggestions)

### Team Breakdown
(from Step 9, for each teammate — skip if solo repo)

For each teammate (sorted by commits descending), write a section:

#### [Name]
- **What they shipped**: 2-3 sentences on their contributions, areas of focus, and commit patterns
- **Praise**: 1-2 specific things they did well, anchored in actual commits. Be genuine — what would you actually say in a 1:1? Examples:
  - "Cleaned up the entire auth module in 3 small, reviewable PRs — textbook decomposition"
  - "Added integration tests for every new endpoint, not just happy paths"
  - "Fixed the N+1 query that was causing 2s load times on the dashboard"
- **Opportunity for growth**: 1 specific, constructive suggestion. Frame as investment, not criticism. Examples:
  - "Test coverage on the payment module is at 8% — worth investing in before the next feature lands on top of it"
  - "3 of the 5 PRs were 800+ LOC — breaking these up would catch issues earlier and make review easier"
  - "All commits land between 1-4am — sustainable pace matters for code quality long-term"

**AI collaboration note:** If many commits have `Co-Authored-By` AI trailers (e.g., Claude, Copilot), note the AI-assisted commit percentage as a team metric. Frame it neutrally — "N% of commits were AI-assisted" — without judgment.

### Top 3 Team Wins
Identify the 3 highest-impact things shipped in the window across the whole team. For each:
- What it was
- Who shipped it
- Why it matters (product/architecture impact)

### 3 Things to Improve
Specific, actionable, anchored in actual commits. Mix personal and team-level suggestions. Phrase as "to get even better, the team could..."

### 3 Habits for Next Week
Small, practical, realistic. Each must be something that takes <5 minutes to adopt. At least one should be team-oriented (e.g., "review each other's PRs same-day").

### Week-over-Week Trends
(if applicable, from Step 10)

---

## Compare Mode

When the user runs `/retro compare` (or `/retro compare 14d`):

1. Compute metrics for the current window (default 7d) using `--since="7 days ago"`
2. Compute metrics for the immediately prior same-length window using both `--since` and `--until` to avoid overlap (e.g., `--since="14 days ago" --until="7 days ago"` for a 7d window)
3. Show a side-by-side comparison table with deltas and arrows
4. Write a brief narrative highlighting the biggest improvements and regressions
5. Save only the current-window snapshot to `.context/retros/` (same as a normal retro run); do **not** persist the prior-window metrics.

## Tone

- Encouraging but candid, no coddling
- Specific and concrete — always anchor in actual commits/code
- Skip generic praise ("great job!") — say exactly what was good and why
- Frame improvements as leveling up, not criticism
- **Praise should feel like something you'd actually say in a 1:1** — specific, earned, genuine
- **Growth suggestions should feel like investment advice** — "this is worth your time because..." not "you failed at..."
- Never compare teammates against each other negatively. Each person's section stands on its own.
- Keep total output around 3000-4500 words (slightly longer to accommodate team sections)
- Use markdown tables and code blocks for data, prose for narrative
- Output directly to the conversation — do NOT write to filesystem (except the `.context/retros/` JSON snapshot)

## Important Rules

- ALL narrative output goes directly to the user in the conversation. The ONLY file written is the `.context/retros/` JSON snapshot.
- Use `origin/<default>` for all git queries (not local main which may be stale)
- Convert all timestamps to Pacific time for display (use `TZ=America/Los_Angeles`)
- If the window has zero commits, say so and suggest a different window
- Round LOC/hour to nearest 50
- Treat merge commits as PR boundaries
- Do not read CLAUDE.md or other docs — this skill is self-contained
- On first run (no prior retros), skip comparison sections gracefully
