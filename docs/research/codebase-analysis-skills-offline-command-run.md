# Which env vars / flags make each ecosystem's runner work offline or fail fast, and how should an approved command be run safely?

**Created:** 2026-09-27
**Author:** aa-ma-researcher (Claude), for codebase-analysis-skills (offline command-run step)
**Reviewed-Through-Date:** 2026-09-27 (official docs fetched and local probes run on this date)
**Valid-Through:** 2027-Q1 (invalidated by a major release of uv, npm, pnpm, Yarn, Go or Cargo that renames or removes an offline switch; pnpm moves fastest, at v12 now)
**Sources:**
- https://docs.astral.sh/uv/reference/environment/ — `UV_OFFLINE` / `UV_NO_SYNC` / `UV_FROZEN` / `UV_LOCKED` / `UV_PYTHON_DOWNLOADS`, with the version each was added
- https://docs.astral.sh/uv/reference/cli/ — `uv run --offline/--no-sync/--frozen/--no-python-downloads` text
- https://docs.astral.sh/uv/concepts/projects/sync/ — `uv run` locks and syncs by default
- https://docs.astral.sh/uv/reference/settings/ — `python-downloads` values `automatic|manual|never`
- https://pip.pypa.io/en/stable/topics/configuration/ — `PIP_<UPPER_LONG_NAME>` env mapping
- https://pip.pypa.io/en/stable/cli/pip_install/ — `--no-index` / `PIP_NO_INDEX`
- https://python-poetry.org/docs/cli/ — no offline option; `poetry run` does not install
- https://docs.npmjs.com/cli/v10/using-npm/config — `offline`, `prefer-offline`, `fetch-timeout`, `npm_config_*` mapping
- https://docs.npmjs.com/cli/v11/commands/npm-exec — npx auto-install; `--yes` assumed when stdin is not a TTY / CI
- https://pnpm.io/cli/install , https://pnpm.io/cli/dlx , https://pnpm.io/settings/cli , https://pnpm.io/settings/network — pnpm `--offline`, `dlx`, `pmOnFail`, fetch timeouts
- https://classic.yarnpkg.com/en/docs/cli/install , https://yarnpkg.com/configuration/yarnrc , https://yarnpkg.com/cli/dlx — Yarn v1 `--offline`; Berry `YARN_ENABLE_NETWORK`, `YARN_ENABLE_OFFLINE_MODE`
- https://github.com/nodejs/corepack/blob/main/README.md — `COREPACK_ENABLE_NETWORK=0`; Corepack ships with Node 14.19 up to (not including) 25
- https://doc.rust-lang.org/cargo/reference/config.html , https://doc.rust-lang.org/cargo/commands/cargo-build.html — `CARGO_NET_OFFLINE`, `--offline`, `--frozen`, `--locked`
- https://rust-lang.github.io/rustup/environment-variables.html — `RUSTUP_AUTO_INSTALL=0`
- https://go.dev/ref/mod , https://go.dev/doc/toolchain , https://raw.githubusercontent.com/golang/go/master/src/cmd/go/internal/help/helpdoc.go — `-mod`, `GOPROXY=off`, `GOFLAGS`, `GOTOOLCHAIN=local`
- https://maven.apache.org/ref/current/maven-embedder/cli.html , https://maven.apache.org/configure.html , https://maven.apache.org/tools/wrapper/ — `-o`, `MAVEN_ARGS` (3.9.0+), mvnw downloads
- https://docs.gradle.org/current/userguide/command_line_interface.html , https://docs.gradle.org/current/userguide/dependency_caching.html , https://docs.gradle.org/current/userguide/gradle_wrapper.html — `--offline` fails on a cache miss; the wrapper downloads its distribution
- https://docs.python.org/3/library/subprocess.html , https://docs.python.org/3/library/os.html#os.killpg — `start_new_session`, `process_group`, timeout semantics, `os.killpg`
- https://github.com/python/cpython/blob/3.12/Lib/subprocess.py — `run()` timeout path (local copy lines 551-563)
- https://man7.org/linux/man-pages/man1/unshare.1.html , https://man7.org/linux/man-pages/man7/network_namespaces.7.html — `unshare -r -n` semantics
- Local probes on BATS, 2026-09-27 (uv 0.12.3, npm 11.17.0, cargo 1.88.0, pip 26.2.1, util-linux 2.41.3, Python 3.12.13, WSL2 kernel 6.6.114.1) — fail-fast timings, `.venv` side effect, netns behaviour, killpg test

## Answer
Every ecosystem except Poetry has a documented offline switch. Five can be set purely through the environment, so the tool can apply them without rewriting the approved command: `UV_OFFLINE=1`, `PIP_NO_INDEX=1`, `npm_config_offline=true`, `CARGO_NET_OFFLINE=true` and `GOPROXY=off`. Yarn Berry adds a sixth, `YARN_ENABLE_NETWORK=0`. On a cache miss, each one I probed fails in under 0.5 s rather than hanging. Maven (`-o`, or `MAVEN_ARGS=-o` on 3.9+), Gradle (`--offline`) and Yarn v1 (`--offline`) need a flag. None of these switches stops a toolchain self-download (uv Python, Corepack, rustup, Go toolchain, mvnw, gradlew, pnpm `pmOnFail`). Each of those needs its own switch, listed below.

A denylist is necessary but not sufficient, because `make test` can wrap `npm install`. For the timeout, use `Popen(start_new_session=True)` plus `os.killpg` on the process group. Plain `subprocess.run(timeout=)` leaks grandchildren (reproduced locally). `unshare -rn` works on this WSL2 box as optional hardening, but it also brings loopback down.

**Correction to the brief:** `GOFLAGS=-mod=mod` is the wrong direction. It *permits* `go.mod` updates. Use `-mod=readonly` (already the default) or `-mod=vendor` (https://go.dev/ref/mod).

## Evidence

### Per-ecosystem offline / fail-fast switches

| Ecosystem | Exact variable / flag | Effect (docs) | Fail-fast or hang | Version introduced |
|---|---|---|---|---|
| **uv** | `UV_OFFLINE=1` (= `--offline`) | "If set, uv will disable network access" and it "will only use locally cached data and locally available files" (https://docs.astral.sh/uv/reference/environment/, https://docs.astral.sh/uv/reference/cli/) | **Fail-fast**. Probe: `UV_OFFLINE=1 uvx <uncached>` fails in 0.18 s ("Packages were unavailable because the network was disabled") | env var 0.5.9 |
| uv | `UV_NO_SYNC=1` (= `uv run --no-sync`) | "Avoid syncing the virtual environment. Implies `--frozen`" (cli ref). Needed because by default "the project is locked and synced before invoking the requested command" (https://docs.astral.sh/uv/concepts/projects/sync/) | n/a (skips the work). **Side effect:** the probe still created `.venv/` in the project dir ("Creating virtual environment at: .venv") | 0.4.18 |
| uv | `UV_FROZEN=1` / `UV_LOCKED=1` | FROZEN: "run without updating the `uv.lock` file". LOCKED: "assert that the `uv.lock` remains unchanged" (env ref) | LOCKED errors if the lock is stale | 0.4.25 (both) |
| uv | `UV_PYTHON_DOWNLOADS=never` | `never`: "Do not ever allow Python downloads" (https://docs.astral.sh/uv/reference/settings/) | **Fail-fast**. Probe: "No interpreter found for Python ==3.7.*" in 0.13 s | 0.3.2 |
| **pip** | `PIP_NO_INDEX=1` (= `--no-index`) | "Ignore package index (only looking at --find-links URLs instead)" (https://pip.pypa.io/en/stable/cli/pip_install/). Env form follows `PIP_<UPPER_LONG_NAME>` (https://pip.pypa.io/en/stable/topics/configuration/) | **Fail-fast**. Probe: "No matching distribution found" in 0.43 s | not stated in the docs |
| **Poetry** | **none** | The CLI reference documents no offline/no-network option. `poetry run` "executes the given command inside the project's virtualenv" and does not install (https://python-poetry.org/docs/cli/) | n/a | n/a |
| **npm** | `npm_config_offline=true` (= `--offline`) | "Force offline mode: no network requests will be done during install" (https://docs.npmjs.com/cli/v10/using-npm/config). Any `npm_config_*` env var is read as config (same page) | **Fail-fast**. Probe: `npx --yes <uncached>` returns `ENOTCACHED` ("cache mode is 'only-if-cached'") in 0.37 s | not stated |
| npm | `npm_config_prefer_offline=true` | "staleness checks ... bypassed, but missing data will be requested from the server" (config page) | **Not offline.** It still fetches on a miss, so don't use it for this goal | not stated |
| npm | `npm_config_fetch_timeout` | Default 300000 ms (5 min), with `fetch-retries` default 2 (config page) | This is the hang risk if offline is not set | — |
| **npx** | (behaviour) | "If any requested packages are not present in the local project dependencies, then a prompt is printed ... When standard input is not a TTY or a CI environment is detected, `--yes` is assumed" (https://docs.npmjs.com/cli/v11/commands/npm-exec; same text in local `npm help exec`) | A subprocess with no TTY therefore **auto-installs silently**. `npm_config_offline=true` turns that into ENOTCACHED. A package that is already cached still runs | npx folded into npm exec at npm 7 (same page) |
| **pnpm** | `--offline` | "use only packages already available in the store. If a package won't be found locally, the installation will fail" (https://pnpm.io/cli/install) | **Fail-fast** (docs: "will fail"; not probed, pnpm not installed) | not stated. Env-var mapping on pnpm 11/12 unverified, see Not pursued |
| pnpm | `pmOnFail=error` | Default `download`; values `download/error/warn/ignore` (https://pnpm.io/settings/cli). The default downloads the pnpm version the project pins | Default = download | v11.0.0 (also `runtimeOnFail`) |
| pnpm | `fetchTimeout` | Default 60000 ms, `fetchRetries` 2 (https://pnpm.io/settings/network) | ~1 min per stalled request | — |
| **Yarn v1 (classic)** | `--offline` | "Run yarn install in offline mode" (https://classic.yarnpkg.com/en/docs/cli/install) | Docs don't say | not stated |
| **Yarn Berry (2+)** | `YARN_ENABLE_NETWORK=0` | "Yarn will never make any request to the network by itself, and will throw an exception rather than let it happen" (https://yarnpkg.com/configuration/yarnrc) | **Fail-fast** (throws) | not stated |
| Yarn Berry | `YARN_ENABLE_OFFLINE_MODE=1` | "replace any network requests by reads from its local caches" (yarnrc page) | Uses the cache; `ENABLE_NETWORK=0` is the stricter switch | not stated |
| **Corepack** (yarn/pnpm shims) | `COREPACK_ENABLE_NETWORK=0` | "prevent Corepack from accessing the network". Otherwise the `packageManager` field triggers a download (https://github.com/nodejs/corepack/blob/main/README.md) | Error instead of download | Bundled with Node 14.19 up to (not including) 25 (README) |
| **Cargo** | `CARGO_NET_OFFLINE=true` (= `--offline`) | "Cargo will avoid accessing the network, and attempt to proceed with locally cached data" (https://doc.rust-lang.org/cargo/reference/config.html). `--frozen` = `--locked` + `--offline` (https://doc.rust-lang.org/cargo/commands/cargo-build.html) | **Fail-fast**. Probe: "no matching package ... you're using offline mode" in 0.10 s | not stated on the pages fetched |
| rustup | `RUSTUP_AUTO_INSTALL=0` | Default 1 "installs the active toolchain when it is absent". "Set this value to `0` to disable automatic installation" (https://rust-lang.github.io/rustup/environment-variables.html) | Stops the `rust-toolchain.toml` self-download | not stated |
| **Go** | `GOPROXY=off` | "`off` indicates that no communication should be attempted". The error is "module lookup disabled by GOPROXY=off" (https://go.dev/ref/mod) | **Fail-fast** (docs; Go not installed, not probed) | not stated |
| Go | `GOFLAGS=-mod=readonly` (or `-mod=vendor`) | readonly: "report an error if `go.mod` needs to be updated". vendor: "will not use the network or the module cache". `mod`: "automatically update `go.mod`" (https://go.dev/ref/mod). `GOFLAGS` is "a space-separated list of -flag=value settings" (helpdoc.go) | readonly is the default unless `vendor/` exists and `go ≥ 1.14` | — |
| Go | `GOTOOLCHAIN=local` | "the `go` command always runs the bundled Go toolchain". Toolchains that are too old "report an error and exit". The default `auto` = `local+auto` downloads (https://go.dev/doc/toolchain) | **Fail-fast** instead of downloading a toolchain | Go 1.21 |
| **Maven** | `-o` / `--offline`, or `MAVEN_ARGS=-o` | "Work offline" (https://maven.apache.org/ref/current/maven-embedder/cli.html). `MAVEN_ARGS` is passed "before CLI arguments", starting with Maven 3.9.0 (https://maven.apache.org/configure.html). Add `-B` (batch, non-interactive) | Docs don't say; build fails on a missing artifact (unverified) | `MAVEN_ARGS` 3.9.0 |
| mvnw | (behaviour) | If the pinned Maven "is not available ... it will be downloaded", via curl/wget (https://maven.apache.org/tools/wrapper/). `-o` does not cover this | Download | — |
| **Gradle** | `--offline` | "Gradle will not attempt to access the network for dependency resolution". "If the required modules are not in the dependency cache, the build will fail" (https://docs.gradle.org/current/userguide/dependency_caching.html) | **Fails** on a cache miss | not stated |
| gradlew | (behaviour) | "If the Gradle distribution was not provisioned to `GRADLE_USER_HOME` before, the Wrapper will download it". `networkTimeout` default 10000 ms (https://docs.gradle.org/current/userguide/gradle_wrapper.html). The docs don't say whether `--offline` covers this | Download | — |

Proposed env block to inject (every item is cited above; unknown vars are ignored by tools that don't read them):
`UV_OFFLINE=1 UV_NO_SYNC=1 UV_PYTHON_DOWNLOADS=never PIP_NO_INDEX=1 npm_config_offline=true COREPACK_ENABLE_NETWORK=0 YARN_ENABLE_NETWORK=0 CARGO_NET_OFFLINE=true RUSTUP_AUTO_INSTALL=0 GOPROXY=off GOFLAGS=-mod=readonly GOTOOLCHAIN=local MAVEN_ARGS="-o -B"`.
Gradle and Yarn v1 have no env equivalent in the fetched docs. For those, the tool must add `--offline` itself or rely on the denylist and timeout.
Caveat: `UV_NO_SYNC` still writes `.venv/` into the target repo (local probe). Offline still executes code that is already cached (npx, uv cache).

### 1. Install/fetch subcommands a denylist should refuse
Each entry is grounded in a doc saying the command downloads or installs.
- **Python:** `pip install|download` and `python -m pip install|download` (pip_install page). `uv sync|add|lock|pip install|tool install|tool run|python install` and `uvx` (uv run locks and syncs, see the sync page). `poetry install|add|update|sync|lock` (poetry CLI). `pipx install|run`.
- **Node:** `npm install|i|ci|add|update|exec` and `npx` without offline set (npm-exec page: packages "are installed to a folder in the npm cache"). `pnpm install|i|add|update|dlx` (dlx "Fetches a package from the registry", https://pnpm.io/cli/dlx). `yarn install|add|up|dlx` (dlx "install a package within a temporary environment", https://yarnpkg.com/cli/dlx). **Bare `yarn`** as well: it runs install in v1 and Berry (not verified in docs this session, see Not pursued). `corepack enable|prepare|install`.
- **Rust:** `cargo install|fetch|update` ("cargo-fetch ... download dependencies", cargo-build page). `rustup install|toolchain install|update`.
- **Go:** `go get`; `go install pkg@version`; `go run pkg@version`; `go mod download|tidy|vendor` (go.dev/ref/mod: `go install` with version suffix "builds packages in module-aware mode"; `go mod download` "downloads the named modules").
- **JVM:** `mvn dependency:go-offline|resolve`, `mvn -U`, `gradle --refresh-dependencies`. `./mvnw` and `./gradlew` when their distribution is not cached (wrapper pages).
- **Generic:** `curl … | sh|bash`, `wget -O- … | sh`, and `sudo`/`apt`/`brew`/`conda|mamba install`/`gem install`/`bundle install`.
- **Limit:** a denylist only sees the literal argv. `make test`, `just`, `tox`/`nox` and npm lifecycle scripts can call any of the above indirectly. The env block and the timeout are the backstop, and a netns (section 3) is the only hard guarantee.

### 2. Python stdlib timeout that kills the whole process group
- Docs basis: `start_new_session=True` makes "the `setsid()` system call ... in the child process prior to the execution" (POSIX, since 3.2). `process_group=0` is the 3.11+ alternative (`setpgid`). `Popen.communicate(timeout)`: "The child process is not killed if the timeout expires". `preexec_fn` is "NOT SAFE ... in the presence of threads", so prefer `start_new_session` (all from https://docs.python.org/3/library/subprocess.html). `os.killpg(pgid, sig, /)`: "Send the signal sig to the process group pgid" (https://docs.python.org/3/library/os.html#os.killpg, extracted by curl).
- Why plain `subprocess.run(timeout=…)` is not enough: on POSIX it does `process.kill()` then `process.wait()`, which kills only the direct child (https://github.com/python/cpython/blob/3.12/Lib/subprocess.py, local lines 551-563). Local probe: `run(["sh","-c","sleep 312 & sleep 312"], timeout=1)` returned in 1.01 s and **left both `sleep 312` processes alive**. The pattern below left **none**.

```python
import os, signal, subprocess

def run_bounded(argv, timeout, cwd, env, grace=5):
    p = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         start_new_session=True, text=True)  # child = new session + pgid == p.pid
    try:
        out, _ = p.communicate(timeout=timeout)
        return p.returncode, out, False
    except subprocess.TimeoutExpired:
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(p.pid, sig)           # whole group, not just the child
            except ProcessLookupError:
                pass
            try:
                out, _ = p.communicate(timeout=grace)
                break
            except subprocess.TimeoutExpired:
                continue
        return p.returncode, out, True
```
`stdin=DEVNULL` matters because npx treats a non-TTY stdin as `--yes` (npm-exec page). The offline env block is what turns that into a fast failure. Known gap: a grandchild that calls `setsid()` itself escapes the group. A cgroup or netns wrapper is the only full fix.

### 3. `unshare -rn` as optional hardening (note only, not chosen)
- Semantics: `-n` "Create a new network namespace"; `-r` maps the caller "to the superuser UID and GID in the newly created user namespace" (https://man7.org/linux/man-pages/man1/unshare.1.html). A netns isolates "network devices, IPv4 and IPv6 protocol stacks, IP routing tables ..." (https://man7.org/linux/man-pages/man7/network_namespaces.7.html).
- Works on BATS/WSL2 (local probe, util-linux 2.41.3). `unshare -rn id` gives uid=0 with rc 0, and the only device is `lo DOWN`. `curl` fails in 0.01 s. `/proc/sys/user/max_user_namespaces` = 79971. `/proc/sys/kernel/apparmor_restrict_unprivileged_userns` is absent here. On stock Ubuntu 23.10+ desktops with AppArmor, that sysctl can block this (not verified this session).
- **Gotcha:** with `lo` down, even localhost tests fail. The probe got `OSError: [Errno 101] Network is unreachable` binding and connecting to 127.0.0.1. `unshare -rn sh -c 'ip link set lo up && …'` fixed it (probe: "ok"). Wrapping argv this way also runs the target as fake-root, which changes `id -u`-sensitive tests.
- Verdict: viable, gives a hard guarantee, and fails fast. It is Linux-only and needs a fallback for when the namespace is refused (EPERM). Keep it as an opt-in flag.

## Not pursued
- Context7 — no Context7 tool was surfaced in this agent's toolset. Official doc pages were fetched directly instead.
- pnpm env-var mapping (`npm_config_offline` vs `pnpm_config_*` on v11/v12) — the settings page didn't state it. Needs a probe with pnpm installed.
- pnpm `verifyDepsBeforeRun` (can `pnpm run` auto-install?) — not found on the settings/cli page.
- `poetry run` creating a virtualenv when none exists — not verified in the docs. It may write to `{cache}/virtualenvs` or `.venv`.
- Bare `yarn` = install (v1 and Berry) — from memory, not re-cited this session.
- Version-introduced for npm `offline`, cargo `--offline`, `GOPROXY=off`, Gradle/Maven `-o` — the fetched pages don't state it.
- Go, Maven, Gradle, pnpm and Yarn fail-fast timing — not probed (tools not installed on BATS).
- Bun (`bun install`, `bunx`), Ruby/Bundler, conda/mamba offline switches — outside the brief's ecosystem list.
- AppArmor unprivileged-userns restriction on native Ubuntu 24.04+/26.04 (non-WSL) — not verified.
- cgroup/systemd-run scope kill as a stronger alternative to killpg — out of scope.
