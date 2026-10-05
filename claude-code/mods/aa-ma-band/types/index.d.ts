export type Variant = 'compact' | 'detailed' | 'off'

export type Snap = {
  repo: boolean
  task?: string
  others: number
  milestone?: string
  pending?: number
  gate?: string
  criticalPath?: string
  prototype?: boolean
  gateError?: string
  branch?: string
  ahead: number
  behind: number
  mainAhead: number
  dirty: number
  ctx?: number
  at: number
}

declare module 'claude-code' {
  interface PluginState {
    'aa-ma-band': { snap: Snap | null; variant: Variant; lastNote: string }
  }
}
