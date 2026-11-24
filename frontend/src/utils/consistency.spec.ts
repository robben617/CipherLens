import { describe, expect, it } from 'vitest'
import {
  judgeTraceResult,
  recheckDisabled,
  recheckVisible,
  type TraceOutcome,
  type TracePayload,
} from './consistency'

const LOCAL = '69c4e0d86a7b0430d8cdb78070b4c55a'

function response(ok: boolean, payload: TracePayload): TraceOutcome {
  return { kind: 'response', ok, payload }
}

describe('judgeTraceResult', () => {
  it('maps a non-2xx response to offline', () => {
    expect(judgeTraceResult(response(false, { trace_id: 't_1', output: LOCAL }), LOCAL)).toEqual({
      state: 'offline',
    })
  })

  it('maps a network error to offline', () => {
    expect(judgeTraceResult({ kind: 'network-error' }, LOCAL)).toEqual({ state: 'offline' })
  })

  it('maps a missing trace_id to mismatch', () => {
    expect(judgeTraceResult(response(true, { output: LOCAL }), LOCAL)).toEqual({ state: 'mismatch' })
  })

  it('maps a different output to mismatch', () => {
    expect(
      judgeTraceResult(response(true, { trace_id: 't_1', output: '00'.repeat(16) }), LOCAL),
    ).toEqual({ state: 'mismatch' })
  })

  it('falls back to ciphertext when output is absent', () => {
    expect(
      judgeTraceResult(response(true, { trace_id: 't_1', ciphertext: LOCAL }), LOCAL),
    ).toEqual({ state: 'ok', traceId: 't_1' })
    expect(
      judgeTraceResult(response(true, { trace_id: 't_1', ciphertext: '00'.repeat(16) }), LOCAL),
    ).toEqual({ state: 'mismatch' })
  })

  it('returns ok with traceId when output matches and trace_id exists', () => {
    expect(judgeTraceResult(response(true, { trace_id: 't_1', output: LOCAL }), LOCAL)).toEqual({
      state: 'ok',
      traceId: 't_1',
    })
  })
})

describe('recheckVisible', () => {
  it('hides the button on initial checking and ok', () => {
    expect(recheckVisible('checking', false)).toBe(false)
    expect(recheckVisible('ok', false)).toBe(false)
    expect(recheckVisible('ok', true)).toBe(false)
  })

  it('keeps the button during manual checking and in abnormal states', () => {
    expect(recheckVisible('checking', true)).toBe(true)
    expect(recheckVisible('mismatch', false)).toBe(true)
    expect(recheckVisible('offline', false)).toBe(true)
  })
})

describe('recheckDisabled', () => {
  it('disables only while checking', () => {
    expect(recheckDisabled('checking')).toBe(true)
    expect(recheckDisabled('ok')).toBe(false)
    expect(recheckDisabled('mismatch')).toBe(false)
    expect(recheckDisabled('offline')).toBe(false)
  })
})