export type Consistency = 'checking' | 'ok' | 'mismatch' | 'offline'

export interface TracePayload {
  trace_id?: string
  output?: string
  ciphertext?: string
}

export type TraceOutcome =
  | { kind: 'response'; ok: boolean; payload: TracePayload }
  | { kind: 'network-error' }

export interface TraceVerdict {
  state: Exclude<Consistency, 'checking'>
  /** 仅 state === 'ok' 时存在，用于回写 traceId */
  traceId?: string
}

export function judgeTraceResult(outcome: TraceOutcome, localOutput: string): TraceVerdict {
  if (outcome.kind === 'network-error') return { state: 'offline' }
  if (!outcome.ok) return { state: 'offline' }

  const remote = outcome.payload.output ?? outcome.payload.ciphertext
  if (!outcome.payload.trace_id || remote !== localOutput) return { state: 'mismatch' }
  return { state: 'ok', traceId: outcome.payload.trace_id }
}

export function recheckVisible(state: Consistency, sticky: boolean): boolean {
  return state === 'mismatch' || state === 'offline' || (state === 'checking' && sticky)
}

export function recheckDisabled(state: Consistency): boolean {
  return state === 'checking'
}