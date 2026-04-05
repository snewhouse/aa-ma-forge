# aa-ma-forge Ecosystem Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Scaffold the aa-ma-forge repository with all AA-MA ecosystem artifacts, install scripts, Python package skeleton, README, and origin story narrative.

**Architecture:** Monorepo with three pillars: `docs/` (specs + narrative), `claude-code/` (operational artifacts), `src/aa_ma/` (Python tooling skeleton). Install scripts symlink `claude-code/` into `~/.claude/`.

**Tech Stack:** Python 3.11+, uv, Pydantic (future), Bash (install scripts)

---

### Task 1: Scaffold directory structure and foundational files

**Files:**
- Create: `LICENSE`
- Create: `pyproject.toml`
- Create: `src/aa_ma/__init__.py`
- Create: `src/aa_ma/validators/__init__.py`
- Create: `src/aa_ma/schemas/__init__.py`
- Create: `src/aa_ma/cli/__init__.py`
- Create: `tests/__init__.py`

**Step 1: Create all directories**

```bash
mkdir -p docs/{narrative,spec,architecture,images}
mkdir -p src/aa_ma/{validators,schemas,cli}
mkdir -p claude-code/{commands,skills/aa-ma-execution,agents,rules,hooks}
mkdir -p examples/aa-ma-team-guide
mkdir -p scripts
mkdir -p tests
```

**Step 2: Create LICENSE file**

Apache-2.0 licence. Use the standard text with "Stephen J Newhouse" as copyright holder, year 2025 (when AA-MA work began).

**Step 3: Create pyproject.toml**

```toml
[project]
name = "aa-ma"
version = "0.1.0"
description = "Advanced Agentic Memory Architecture - structured external memory for AI coding agents"
readme = "README.md"
license = "Apache-2.0"
requires-python = ">=3.11"
authors = [
    { name = "Stephen J Newhouse", email = "stephen.j.newhouse@gmail.com" },
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest>=8.0",
    "ruff>=0.4",
]
```

**Step 4: Create Python package skeleton**

`src/aa_ma/__init__.py`:
```python
"""Advanced Agentic Memory Architecture (AA-MA)."""

__version__ = "0.1.0"
```

Empty `__init__.py` for `validators/`, `schemas/`, `cli/`, and `tests/`.

**Step 5: Commit**

```bash
git add LICENSE pyproject.toml src/ tests/
git commit -m "feat: scaffold project structure with Apache-2.0 licence and Python package skeleton"
```

---

### Task 2: Import specification documents

**Files:**
- Copy: `~/.claude/docs/aa-ma-specification.md` → `docs/spec/aa-ma-specification.md`
- Copy: `~/.claude/docs/aa-ma-quick-reference.md` → `docs/spec/aa-ma-quick-reference.md`
- Copy: `~/.claude/docs/aa-ma-team-guide.md` → `docs/spec/aa-ma-team-guide.md`

**Step 1: Copy spec files**

```bash
cp ~/.claude/docs/aa-ma-specification.md docs/spec/
cp ~/.claude/docs/aa-ma-quick-reference.md docs/spec/
cp ~/.claude/docs/aa-ma-team-guide.md docs/spec/
```

**Step 2: Verify line counts match source**

```bash
wc -l docs/spec/*.md
# Expected: 454 + 222 + 1022 = 1698 total
```

**Step 3: Commit**

```bash
git add docs/spec/
git commit -m "docs: import AA-MA specification v2.1, quick reference, and team guide"
```

---

### Task 3: Import Claude Code commands

**Files:**
- Copy: `~/.claude/commands/execute-aa-ma-full.md` → `claude-code/commands/`
- Copy: `~/.claude/commands/execute-aa-ma-milestone.md` → `claude-code/commands/`
- Copy: `~/.claude/commands/execute-aa-ma-step.md` → `claude-code/commands/`
- Copy: `~/.claude/commands/archive-aa-ma.md` → `claude-code/commands/`
- Copy: `~/.claude/commands/ultraplan.md` → `claude-code/commands/`
- Copy: `~/.claude/commands/verify-plan.md` → `claude-code/commands/`

**Step 1: Copy all 6 command files**

```bash
cp ~/.claude/commands/execute-aa-ma-full.md claude-code/commands/
cp ~/.claude/commands/execute-aa-ma-milestone.md claude-code/commands/
cp ~/.claude/commands/execute-aa-ma-step.md claude-code/commands/
cp ~/.claude/commands/archive-aa-ma.md claude-code/commands/
cp ~/.claude/commands/ultraplan.md claude-code/commands/
cp ~/.claude/commands/verify-plan.md claude-code/commands/
```

**Step 2: Verify line counts**

```bash
wc -l claude-code/commands/*.md
# Expected: 654 + 778 + 333 + 214 + 762 + 149 = 2890 total
```

**Step 3: Commit**

```bash
git add claude-code/commands/
git commit -m "feat: import 6 AA-MA commands (execute-full, execute-milestone, execute-step, archive, ultraplan, verify-plan)"
```

---

### Task 4: Import Claude Code skill, agents, rules, and hooks

**Files:**
- Copy: `~/.claude/skills/aa-ma-execution/SKILL.md` → `claude-code/skills/aa-ma-execution/SKILL.md`
- Copy: `~/.claude/agents/aa-ma-scribe.md` → `claude-code/agents/`
- Copy: `~/.claude/agents/aa-ma-validator.md` → `claude-code/agents/`
- Copy: `~/.claude/rules/aa-ma.md` → `claude-code/rules/`
- Copy: `~/.claude/hooks/lib/pre-compact-aa-ma.sh` → `claude-code/hooks/`

**Step 1: Copy all operational artifacts**

```bash
cp ~/.claude/skills/aa-ma-execution/SKILL.md claude-code/skills/aa-ma-execution/
cp ~/.claude/agents/aa-ma-scribe.md claude-code/agents/
cp ~/.claude/agents/aa-ma-validator.md claude-code/agents/
cp ~/.claude/rules/aa-ma.md claude-code/rules/
cp ~/.claude/hooks/lib/pre-compact-aa-ma.sh claude-code/hooks/
```

**Step 2: Verify line counts**

```bash
wc -l claude-code/skills/aa-ma-execution/SKILL.md claude-code/agents/*.md claude-code/rules/aa-ma.md claude-code/hooks/pre-compact-aa-ma.sh
# Expected: 1187 + 210 + 207 + 119 + 62 = 1785 total
```

**Step 3: Commit**

```bash
git add claude-code/skills/ claude-code/agents/ claude-code/rules/ claude-code/hooks/
git commit -m "feat: import AA-MA execution skill, agents (scribe + validator), rules, and compaction hook"
```

---

### Task 5: Import example completed task

**Files:**
- Copy: `~/.claude/dev/completed/aa-ma-team-guide/*` → `examples/aa-ma-team-guide/`

**Step 1: Copy all 5 artifact files**

```bash
cp ~/.claude/dev/completed/aa-ma-team-guide/aa-ma-team-guide-plan.md examples/aa-ma-team-guide/
cp ~/.claude/dev/completed/aa-ma-team-guide/aa-ma-team-guide-reference.md examples/aa-ma-team-guide/
cp ~/.claude/dev/completed/aa-ma-team-guide/aa-ma-team-guide-context-log.md examples/aa-ma-team-guide/
cp ~/.claude/dev/completed/aa-ma-team-guide/aa-ma-team-guide-tasks.md examples/aa-ma-team-guide/
cp ~/.claude/dev/completed/aa-ma-team-guide/aa-ma-team-guide-provenance.log examples/aa-ma-team-guide/
```

**Step 2: Verify line counts**

```bash
wc -l examples/aa-ma-team-guide/*
# Expected: 46 + 92 + 65 + 84 + 12 = 299 total
```

**Step 3: Commit**

```bash
git add examples/
git commit -m "docs: import completed aa-ma-team-guide as reference example of the 5-file artifact set"
```

---

### Task 6: Write install.sh

**Files:**
- Create: `scripts/install.sh`

**Step 1: Write the install script**

The script must:
1. Detect the repo root (where this script lives)
2. Back up existing AA-MA files in `~/.claude/` to `~/.claude/backups/aa-ma-forge-YYYYMMDD-HHMMSS/`
3. Symlink commands, skill, agents, rules, hooks from repo → `~/.claude/`
4. Copy (not symlink) spec docs to `~/.claude/docs/`
5. Print a summary of what was linked/copied
6. Be idempotent (safe to run multiple times)

Key mappings:
```
claude-code/commands/*.md        → ~/.claude/commands/
claude-code/skills/aa-ma-execution/ → ~/.claude/skills/aa-ma-execution/
claude-code/agents/*.md          → ~/.claude/agents/
claude-code/rules/aa-ma.md      → ~/.claude/rules/
claude-code/hooks/*.sh           → ~/.claude/hooks/lib/
docs/spec/*.md                   → ~/.claude/docs/ (copy)
```

**Step 2: Make executable**

```bash
chmod +x scripts/install.sh
```

**Step 3: Test the script (dry run)**

Run with a `--dry-run` flag that prints what would happen without doing it.

**Step 4: Commit**

```bash
git add scripts/install.sh
git commit -m "feat: add install.sh with symlink deployment and backup-first strategy"
```

---

### Task 7: Write uninstall.sh

**Files:**
- Create: `scripts/uninstall.sh`

**Step 1: Write the uninstall script**

The script must:
1. Remove all symlinks created by install.sh (only if they point to this repo)
2. Restore the most recent backup from `~/.claude/backups/aa-ma-forge-*/`
3. Print a summary of what was restored
4. Be safe (never delete non-symlink files)

**Step 2: Make executable**

```bash
chmod +x scripts/uninstall.sh
```

**Step 3: Commit**

```bash
git add scripts/uninstall.sh
git commit -m "feat: add uninstall.sh to restore backups and remove symlinks"
```

---

### Task 8: Write README.md

**Files:**
- Create: `README.md`

**CRITICAL: Must be written in Stephen Newhouse Voice. UK English, no em dashes, no AI vocabulary, conversational, warm but edgy. Run the full voice quality gate before committing.**

**Step 1: Write README with these sections**

1. **Title and one-liner** describing what AA-MA is
2. **The problem** (2-3 sentences on LLM context drift and amnesia)
3. **What's in this repo** (brief structure overview)
4. **Quick start** (clone + install.sh)
5. **The five files** (the core taxonomy, brief)
6. **Inspirations and credits**
7. **Licence**

Keep it under 150 lines. Link to `docs/narrative/how-we-got-here.md` for the full story and `docs/spec/aa-ma-specification.md` for the technical details.

**Step 2: Voice quality gate**

Run the 3-step gate from stephen-newhouse-voice:
1. Voice check: sounds like Stephen?
2. De-AI check: scan 24 patterns
3. Clarity check: Strunk's 6 rules

**Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add README with project overview and quick start"
```

---

### Task 9: Write the origin story narrative

**Files:**
- Create: `docs/narrative/how-we-got-here.md`

**CRITICAL: This is the most important prose document in the repo. Must be written in Stephen Newhouse Voice throughout. Warm, edgy, journalistic. First person. Like telling the story to a sharp colleague.**

**Step 1: Research the timeline**

Gather facts from:
- claude-mem observations (AA-MA sessions from Nov 2025 onwards)
- `~/.claude/dev/completed/` directory timestamps
- The AA-MA specification changelog
- Memory about inspirations (Reddit, Matt Pocock, Helix.ml)

Key dates to establish:
- Nov 2025: Earliest AA-MA completed tasks (ultraplan-enhancement, agent-token-optimization)
- Dec 2025: Further refinements
- Feb 2026: Matt Pocock's skills repo appears (AA-MA already exists)
- Mar 2026: Team guide, workflow hardening, project index integration
- Apr 2026: Helix.ml research, v2.1 features, design principles audit

**Step 2: Write the narrative**

Structure:
1. **The problem I was trying to solve** — context drift, LLM amnesia, losing state across sessions. The frustration of starting every conversation from scratch.
2. **Early experiments** — playing with Claude Code, trying different approaches. What stuck, what didn't.
3. **The five-file taxonomy** — how each file earned its place. Why five, not three or ten.
4. **The Reddit spark** — the agentic memory concept that crystallised the approach (link TBD).
5. **Building the operational layer** — commands, skills, agents. Making it usable day-to-day.
6. **Refinements and inspiration** — Matt Pocock's skills repo (Feb 2026), Helix.ml research (Apr 2026). What we borrowed, what's original.
7. **Where we are now** — v2.1, 18 files, battle-tested across real projects. What works, what's still rough.
8. **What's next** — Python tooling, skill activation architecture, framework potential.

Target: 800-1500 words. Readable in 5-10 minutes.

**Step 3: Voice quality gate**

Full stephen-newhouse-voice 3-step gate.

**Step 4: Commit**

```bash
git add docs/narrative/how-we-got-here.md
git commit -m "docs: add origin story narrative — how AA-MA came to be"
```

---

### Task 10: Final verification and push

**Step 1: Verify repo structure matches design**

```bash
find . -not -path './.git/*' -not -path './.git' | sort
```

Compare against the design document structure.

**Step 2: Verify line counts**

```bash
echo "=== Specs ===" && wc -l docs/spec/*.md
echo "=== Commands ===" && wc -l claude-code/commands/*.md
echo "=== Skill ===" && wc -l claude-code/skills/aa-ma-execution/SKILL.md
echo "=== Agents ===" && wc -l claude-code/agents/*.md
echo "=== Rules ===" && wc -l claude-code/rules/*.md
echo "=== Hooks ===" && wc -l claude-code/hooks/*.sh
echo "=== Examples ===" && wc -l examples/aa-ma-team-guide/*
echo "=== Total ===" && find . -name '*.md' -o -name '*.py' -o -name '*.toml' -o -name '*.sh' -o -name '*.log' | grep -v .git | xargs wc -l | tail -1
```

**Step 3: Run Python package check**

```bash
cd aa-ma-forge
uv run python -c "import aa_ma; print(aa_ma.__version__)"
# Expected: 0.1.0
```

**Step 4: Push everything**

```bash
git push origin main
```

**Step 5: Verify on GitHub**

Check https://github.com/snewhouse/aa-ma-forge shows all files and README renders correctly.
