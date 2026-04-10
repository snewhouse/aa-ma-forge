---
name: aa-ma-search
description: Search across active and completed AA-MA task files for keywords. Returns ranked results from reference.md, context-log.md, and tasks.md files.
---

# /aa-ma-search — Cross-Task Search

Search across all AA-MA task files to find past decisions, facts, and task state.

## Usage

```
/aa-ma-search <query> [--active|--completed|--all]
```

- `<query>` — keyword or phrase to search for
- `--active` — search only `.claude/dev/active/` (default)
- `--completed` — search only `.claude/dev/completed/`
- `--all` — search both active and completed tasks

## Instructions for AI

### Step 1: Parse Arguments

Extract the search query and scope from the user's input.

```
QUERY = [everything after /aa-ma-search except flags]
SCOPE = --active (default) | --completed | --all
```

If no query provided, use `AskUserQuestion` to prompt: "What would you like to search for across AA-MA tasks?"

### Step 2: Determine Search Directories

```bash
# Build list of directories to search
SEARCH_DIRS=""

case "$SCOPE" in
    --active|"")
        # Check project-level first, then HOME
        if [ -d ".claude/dev/active" ]; then
            SEARCH_DIRS=".claude/dev/active"
        elif [ -d "$HOME/.claude/dev/active" ]; then
            SEARCH_DIRS="$HOME/.claude/dev/active"
        fi
        ;;
    --completed)
        if [ -d ".claude/dev/completed" ]; then
            SEARCH_DIRS=".claude/dev/completed"
        elif [ -d "$HOME/.claude/dev/completed" ]; then
            SEARCH_DIRS="$HOME/.claude/dev/completed"
        fi
        ;;
    --all)
        # Combine both, checking project-level first
        for subdir in active completed; do
            if [ -d ".claude/dev/$subdir" ]; then
                SEARCH_DIRS="$SEARCH_DIRS .claude/dev/$subdir"
            elif [ -d "$HOME/.claude/dev/$subdir" ]; then
                SEARCH_DIRS="$SEARCH_DIRS $HOME/.claude/dev/$subdir"
            fi
        done
        ;;
esac
```

If no directories found, report: "No AA-MA task directories found. Nothing to search."

### Step 3: Execute Search

Search across `reference.md`, `context-log.md`, and `tasks.md` files within each task directory. Use Grep tool for efficient searching.

**Target files** (in each task directory):
- `*-reference.md` — immutable facts
- `*-context-log.md` — decisions and trade-offs
- `*-tasks.md` — execution state and acceptance criteria

**Do NOT search:**
- `*-provenance.log` — machine telemetry, not human-readable knowledge
- `*-plan.md` — duplicates content in tasks.md and reference.md

### Step 4: Rank and Present Results

Present results grouped by task, with match count for basic relevance ranking:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AA-MA Search: "[query]"
Scope: [active|completed|all]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 [task-name-1] (N matches)
  📄 reference.md:
    - [matching line with context]
  📄 context-log.md:
    - [matching line with context]

📁 [task-name-2] (N matches)
  📄 tasks.md:
    - [matching line with context]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total: N matches across M tasks
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Step 5: Handle Empty Results

If no matches found:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AA-MA Search: "[query]"
Scope: [scope]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
No matches found.

Suggestions:
- Try broader search terms
- Use --all to include completed tasks
- For semantic search (concept matching), see future roadmap
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Limitations

This is a **keyword search** command. It finds exact word matches, not conceptual similarity. For example, searching "authentication" will NOT find entries about "OAuth2 PKCE flow" unless the word "authentication" appears in the text.

Semantic/vector search is planned as a future enhancement when task volume warrants it (see specification Section XIII).
