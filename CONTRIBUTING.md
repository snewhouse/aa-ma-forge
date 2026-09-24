# Contributing

Thanks for your interest. This is a one-person project maintained in my own time, so pull requests are welcome but response times will vary.

## Before you start

1. Check [open issues](https://github.com/snewhouse/aa-ma-forge/issues) to see if someone's already working on it
2. For anything beyond a typo fix, open an issue first to discuss the approach

## Making changes

1. Fork the repo and create a branch from `main`
2. Run `scripts/install.sh --dry-run` to verify the installer still picks up your changes
3. Use [Conventional Commits](https://conventionalcommits.org) for your commit messages
4. Keep changes focused. One PR per concern.

## Generated files

Two artifacts are generated and checked for drift in CI; never hand-edit them:

- `docs/architecture/` — the living architecture doc ([ADR-0016](docs/adr/0016-living-architecture-doc.md)), checked by the `architecture-drift` job.
- `tests/golden/plugin-surface.json` — the plugin-surface snapshot, checked by `tests/codemem/test_plugin_surface.py`.

After changing imports or calls, a reference in `claude-code/`, the hook table in `scripts/install.sh`, or `docs/architecture.captions.json`, run:

```bash
scripts/regen-generated.sh
```

It rebuilds the codemem index first (a stale index disagrees with CI), regenerates both, and runs `codemem draw --check`. Review the `git diff` — it is the architecture change — and commit it with your change. Caption prose edits never count as drift.

## What I'll review for

- Does it work? (install.sh --dry-run is the smoke test)
- Does it follow the existing patterns? (skills have SKILL.md, commands are markdown, etc.)
- Is it documented? (README, CHANGELOG, and SECURITY.md should stay accurate)
- No leaked credentials, client names, or personal information

## Reporting issues

Use [GitHub Issues](https://github.com/snewhouse/aa-ma-forge/issues). Include what you expected, what happened, and your environment (OS, Claude Code version).

## Security issues

See [SECURITY.md](SECURITY.md) for responsible disclosure.
