# zero-config install

The minimum viable path from a clean clone of aa-ma-forge to a Claude Code session that can answer `who_calls`, `co_changes`, and `aa_ma_context` queries against your repo.

Three commands and one paste.

## Prerequisites

- [`uv`](https://docs.astral.sh/uv/) on your PATH (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- `git` on your PATH
- Claude Code installed and configured (see [Claude Code docs](https://docs.anthropic.com/en/docs/claude-code))
- Python 3.11+ (3.13 is what we test against)

## The four steps

### 1. Install the plugin into `~/.claude/`

Clone aa-ma-forge once anywhere on disk; the install script symlinks the plugin layer into `~/.claude/`.

```bash
git clone https://github.com/snewhouse/aa-ma-forge.git
cd aa-ma-forge
bash scripts/install.sh
```

Run with `--dry-run` first to preview symlinks. The script backs up any existing `~/.claude/{commands,skills,agents,hooks}` files it would overwrite.

### 2. Drop a project-scope `.mcp.json` into your target repo

This is the file Claude Code reads to discover the codemem MCP server. Put it at the **root** of whichever repo you want codemem to index. You can use the same snippet across every repo — Claude Code substitutes `${PWD}` at config-load time, so the spawned subprocess gets the absolute path of whichever repo you opened the session in.

```bash
cd /path/to/your-target-repo

cat > .mcp.json <<'EOF'
{
  "mcpServers": {
    "codemem": {
      "command": "uv",
      "args": [
        "--directory", "${PWD}",
        "run", "python",
        "/ABSOLUTE/PATH/TO/aa-ma-forge/claude-code/codemem/mcp/server.py"
      ],
      "env": {
        "CODEMEM_REPO_ROOT": "${PWD}",
        "CODEMEM_DB": "${PWD}/.codemem/index.db"
      }
    }
  }
}
EOF
```

Replace `/ABSOLUTE/PATH/TO/aa-ma-forge/` with the path you cloned into in step 1.

The portable bits — `${PWD}` for the target repo's root, plus `CODEMEM_REPO_ROOT` and `CODEMEM_DB` env vars pointing at the same — mean this same `.mcp.json` works in any repo without per-machine edits.

### 3. Open a fresh Claude Code session in the target repo and approve

```bash
cd /path/to/your-target-repo
claude
```

On first use Claude Code prompts you to approve the codemem MCP server. After approval, the **first MCP tool call triggers an auto-build** of the codemem index — typically under one second on a small-to-medium repo. Run `/mcp` to confirm `codemem` shows as connected; the deferred-tools list will include `mcp__codemem__search_symbols`, `mcp__codemem__hot_spots`, `mcp__codemem__aa_ma_context`, and the rest.

If you ever need to re-trigger the approval prompt, run `claude mcp reset-project-choices` and start a new session.

### 4. Light up the git-mining tools (one-off)

The auto-build creates the SQLite index but does **not** populate the git-mining cache (`commits` and `commit_files` tables). Until you run this command once, `co_changes`, `hot_spots`, and the cached portions of `owners` and `symbol_history` return empty.

```bash
cd /path/to/your-target-repo
uv --directory /ABSOLUTE/PATH/TO/aa-ma-forge run codemem refresh-commits
```

Output:
```
codemem refresh-commits: inserted 128 commits (cap=500) — /path/to/your-target-repo/.codemem/index.db
```

The cache caps at the most recent 500 commits by `author_time` (`--limit N` to override). Subsequent runs are incremental — they pick up only commits added since the last call.

To keep the cache fresh automatically, install the opt-in post-commit hook:

```bash
bash /ABSOLUTE/PATH/TO/aa-ma-forge/scripts/install.sh --wire-git-hook
```

This appends a single sentinel-marked line to your repo's `.git/hooks/post-commit` that runs `codemem refresh` in the background after every commit. (As of M3 the post-commit hook still calls the M2-placeholder `refresh`, not `refresh-commits` — the wiring upgrade is tracked as post-M4 work; for now, run `refresh-commits` manually after batches of commits.)

## What you get

After the four steps above, Claude Code has access to **12 codemem MCP tools** in any session opened from your target repo:

- 6 ports of `/index` semantics (`who_calls`, `blast_radius`, `dead_code`, `dependency_chain`, `search_symbols`, `file_summary`)
- 6 git-mining + AA-MA-native (`hot_spots`, `co_changes`, `owners`, `symbol_history`, `layers`, `aa_ma_context`)

For a real example of what `co_changes` returns and how to read the output, see [`docs/demo/codemem-co-changes-transcript.md`](../demo/codemem-co-changes-transcript.md).

For the longer install walkthrough, alternate user-scope install (no per-repo `.mcp.json`), and the full tool reference, see [`claude-code/codemem/README.md`](../../claude-code/codemem/README.md).

## What can break

Five public kill-criteria signals would cause us to abandon or pivot codemem — see [`docs/codemem/kill-criteria.md`](kill-criteria.md). As of April 2026 none have fired.

## End-to-end smoke target

On aa-ma-forge itself, the entire sequence (steps 1–4 plus a first `co_changes` query) returns an answer in under five seconds: install once, drop `.mcp.json`, open Claude Code, run `refresh-commits`, ask the agent "what changes alongside README.md?". The answer comes back as structured JSON the agent can reason over.
