// PROTOTYPE — throwaway (prototype/aa-ma-band). Thin view: every AA-MA fact comes
// from aa-ma-gate (the Python SSoT, ADR-0009); this module only draws it.
import { atom, read, update } from 'claude-code'
import type { Register } from 'claude-code'

import type { Snap, Variant } from '../types'

const snap = atom({ plugin: 'aa-ma-band', key: 'snap' } as const, null)
const variant = atom({ plugin: 'aa-ma-band', key: 'variant' } as const, 'compact')
const lastNote = atom({ plugin: 'aa-ma-band', key: 'lastNote' } as const, '')

// ponytail: hardcoded forge path; install.sh would set it (AA_MA_ROOT) in the real mod
const FORGE = '/home/sjnewhouse/projects/github_private/aa-ma-forge'
const CTX_LIMIT = 70 // ~/.claude/rules/token-efficiency.md: compact at 70%
const GATE_ERRORS: Record<number, string> = { 1: 'no ACTIVE milestone', 2: 'tasks.md unreadable', 3: 'ambiguous milestone' }
const REFRESH_ON = /-(tasks\.md|provenance\.log|context-log\.md)$/
const GIT_MOVES = /\bgit\s+(commit|push|pull|reset|switch|checkout|merge|rebase|fetch)\b/

// Security (commit review 2026-10-05): a repo's own config/.gitattributes can make `git status` run
// commands (core.fsmonitor, filter.*.clean), and a repo-local .venv binary is attacker-planted code.
// So: git and aa-ma-gate run only for repos under these roots, git with the user's global/system
// config dropped and stamp.GIT_OVERRIDES applied, and the gate only from the forge's own venv.
// ponytail: hardcoded allowlist; production reads it from options (userConfig).
const TRUSTED_ROOTS = ['/home/sjnewhouse/projects/', '/home/sjnewhouse/dev/']
const GIT_ENV: Record<string, string> = {
  GIT_CONFIG_GLOBAL: '/dev/null',
  GIT_CONFIG_NOSYSTEM: '1',
  GIT_CONFIG_COUNT: '2',
  GIT_CONFIG_KEY_0: 'core.fsmonitor',
  GIT_CONFIG_VALUE_0: 'false',
  GIT_CONFIG_KEY_1: 'core.hooksPath',
  GIT_CONFIG_VALUE_1: '/dev/null',
}
// Repo-controlled text (dir names, gate errors) never reaches the terminal or the model raw.
const clean = (s: string | undefined, max = 60) =>
  s === undefined ? undefined : s.replace(/[\u0000-\u001f\u007f-\u009f‪-‮⁦-⁩]/g, '?').slice(0, max)

const kv = (text: string) =>
  Object.fromEntries(text.split('\n').filter(l => l.includes('=')).map(l => [l.slice(0, l.indexOf('=')), l.slice(l.indexOf('=') + 1)]))

async function run($: any, argv: string[], cwd?: string) {
  try {
    return await $.process.run(argv, { cwd, timeoutMs: 5000, env: argv[0] === 'git' ? GIT_ENV : undefined })
  } catch {
    return { exitCode: 127, stdout: '', stderr: '' }
  }
}

async function gateArgv($: any): Promise<string[]> {
  const bin = `${FORGE}/.venv/bin/aa-ma-gate` // never the target repo's own .venv
  if (await $.fs.exists(bin)) return [bin]
  return ['uv', 'run', '--quiet', '--project', FORGE, 'aa-ma-gate']
}

async function refresh($: any) {
  const s: Snap = { repo: false, others: 0, ahead: 0, behind: 0, mainAhead: 0, dirty: 0, at: await $.clock.now() }
  const usage = await $.session.usage().catch(() => undefined)
  s.ctx = usage?.context?.percent
  const cwd: string = await $.session.cwd()
  const real = (await $.fs.stat(cwd, { resolve: true }).catch(() => undefined))?.realPath ?? ''
  const trusted = TRUSTED_ROOTS.some(r => `${real}/`.startsWith(r))
  if (!trusted) s.gateError = 'repo outside trusted roots: band idle'
  // Second review: a repo's own .git/config can still define filter/diff drivers that `git status`
  // runs. The forge's stamp refuses any local/worktree/submodule key outside SAFE_GIT_CONFIG
  // (stamp.check_git_config, L-1294) — no git runs here until it passes.
  const safe = trusted ? await run($, [`${FORGE}/.venv/bin/aa-ma-analysis`, 'stamp', '--tier', 'quick', '--repo', real]) : { exitCode: 1 }
  if (trusted && safe.exitCode !== 0) s.gateError = safe.exitCode === 2 ? 'repo git config not on the safe list: band idle' : 'not a git repo'
  const top = trusted && safe.exitCode === 0 ? await run($, ['git', 'rev-parse', '--show-toplevel']) : { exitCode: 1, stdout: '' }
  if (top.exitCode === 0 && TRUSTED_ROOTS.some(r => `${top.stdout.trim()}/`.startsWith(r))) {
    const root = top.stdout.trim()
    s.repo = true
    const st = await run($, ['git', 'status', '--porcelain=v2', '--branch'], root)
    for (const line of st.stdout.split('\n')) {
      if (line.startsWith('# branch.head ')) s.branch = clean(line.slice(14))
      else if (line.startsWith('# branch.ab ')) {
        const [a, b] = line.slice(12).split(' ')
        s.ahead = Number(a.slice(1))
        s.behind = Number(b.slice(1))
      } else if (!line.startsWith('#') && line.includes('.claude/dev/active/')) s.dirty += 1
    }
    const main = await run($, ['git', 'rev-list', '--count', 'origin/main..main'], root)
    if (main.exitCode === 0) s.mainAhead = Number(main.stdout.trim()) || 0

    const active = `${root}/.claude/dev/active`
    const dirs = (await $.fs.list(active).catch(() => [])).filter((d: any) => d.kind === 'dir')
    s.others = Math.max(0, dirs.length - 1)
    if (dirs.length > 0) {
      const name = dirs[0].name
      s.task = clean(name, 40)
      const tasks = `${active}/${name}/${name}-tasks.md`
      const g = await run($, [...(await gateArgv($)), tasks, '--format', 'kv'], root)
      const f = kv(g.stdout)
      if (g.exitCode === 0) {
        s.milestone = clean(`M${f.number}`, 8)
        s.pending = Number(f.pending_steps) || 0
        s.gate = clean(f.gate, 4)
        s.criticalPath = clean(f.critical_path || undefined, 24)
        s.prototype = f.prototype_required === 'YES'
      } else {
        s.gateError = GATE_ERRORS[g.exitCode] ?? `aa-ma-gate rc ${g.exitCode}`
      }
    }
  }
  await update($, snap, () => s)
  $.ui.invalidate('ui.render')
}

function summary(s: Snap): string {
  const parts: string[] = []
  if (s.task) {
    parts.push(s.others ? `${s.task} (+${s.others})` : s.task)
    parts.push(s.gateError ?? `${s.milestone} ACTIVE · ${s.pending} pending · ${s.gate}`)
  } else parts.push(s.gateError ?? 'AA-MA: no active plan')
  if (s.dirty) parts.push(`AA-MA dirty ${s.dirty}`)
  if (s.mainAhead) parts.push(`main ↑${s.mainAhead}`)
  if (s.ctx !== undefined) parts.push(`ctx ${s.ctx}%/${CTX_LIMIT}`)
  return parts.join(' · ')
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({ name: 'band-variant', description: 'aa-ma-band: compact | detailed | off' })
    $.clock.every(30_000, () => void refresh($))
    void refresh($)
    return next(e)
  })

  on('command.run', { command: 'band-variant' }, async ($, e) => {
    const v = (['compact', 'detailed', 'off'] as const).find(x => x === e.args.trim())
    if (!v) return { text: `aa-ma-band variant is ${await read($, variant)}; use compact | detailed | off` }
    await update($, variant, () => v)
    $.ui.invalidate('ui.render')
    return { text: `aa-ma-band → ${v}` }
  })

  on('turn.complete', async ($, e, next) => {
    void refresh($)
    return next(e)
  })

  on('tool.call', async ($, e, next) => {
    const ran = await next(e)
    const path = (e as any).file_path ?? ''
    const cmd = (e as any).command ?? ''
    if (REFRESH_ON.test(path) || GIT_MOVES.test(cmd)) void refresh($)
    return ran
  })

  // Off-terminal fallback: one context line per prompt, only when it changed.
  on('classic.UserPromptSubmit', async ($, e, next) => {
    const r = await next(e)
    const surfaces = await $.session.surfaces().catch(() => [])
    const s = await read($, snap)
    if (!s || surfaces.includes('terminal')) return r
    const note = `[aa-ma-band] ${summary(s)}`
    if (note === (await read($, lastNote))) return r
    await update($, lastNote, () => note)
    return { ...r, additionalContext: [...(r.additionalContext ?? []), note] }
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const s = await read($, snap)
    const v: Variant = await read($, variant)
    if (!s || v === 'off' || e.props.hasSurvey) return next(e)
    const { Box, Text } = $.ui.resolve(e)
    const ctxColor = s.ctx === undefined ? undefined : s.ctx >= CTX_LIMIT ? 'red' : s.ctx >= 60 ? 'yellow' : 'green'
    const head = s.task ? (
      <Text>
        <Text bold>{s.others ? `${s.task} (+${s.others})` : s.task}</Text>
        {' · '}
        {s.gateError ? (
          <Text color="red">{s.gateError}</Text>
        ) : (
          <Text>
            {s.milestone} ACTIVE · {s.pending} pending · <Text color={s.gate === 'HARD' ? 'magenta' : undefined}>{s.gate}</Text>
          </Text>
        )}
      </Text>
    ) : (
      <Text dimColor>{s.gateError ?? 'AA-MA: no active plan'}</Text>
    )
    const hygiene = (
      <Text>
        {s.dirty ? <Text color="yellow"> · AA-MA dirty {s.dirty}</Text> : null}
        {s.mainAhead ? <Text color="red"> · main ↑{s.mainAhead}</Text> : null}
        {s.ctx !== undefined ? <Text color={ctxColor}> · ctx {s.ctx}%/{CTX_LIMIT}</Text> : null}
      </Text>
    )
    if (v === 'compact') {
      return (
        <Box>
          <Text wrap="truncate-end">
            {head}
            {hygiene}
          </Text>
        </Box>
      )
    }
    return (
      <Box flexDirection="column">
        <Text wrap="truncate-end">
          {head}
          {hygiene}
        </Text>
        <Text dimColor wrap="truncate-end">
          {s.branch ?? '-'} ↑{s.ahead}↓{s.behind}
          {s.criticalPath ? ` · CP:${s.criticalPath}` : ''}
          {s.prototype ? ' · Prototype-Required' : ''}
          {' · /band-variant compact|detailed|off'}
        </Text>
      </Box>
    )
  })
}
