import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { effectScope } from 'vue'
import { useSSE } from './useSSE'

type SSEApi = ReturnType<typeof useSSE>

const windowStub: { __sse?: { active: number } } = {}

function createSSE(): { scope: ReturnType<typeof effectScope>; api: SSEApi } {
  const scope = effectScope()
  const api = scope.run(() => useSSE())
  if (!api) throw new Error('failed to create useSSE in effect scope')
  return { scope, api }
}

function active(): number {
  return windowStub.__sse?.active ?? 0
}

beforeEach(() => {
  vi.useFakeTimers()
  vi.stubGlobal('window', windowStub)
  windowStub.__sse = undefined
})

afterEach(() => {
  vi.useRealTimers()
  vi.unstubAllGlobals()
})

describe('useSSE scope isolation', () => {
  it('K1-K2: aborting one scope does not touch another', () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise<Response>(() => {})))
    const a = createSSE()
    const b = createSSE()

    a.api.start('/a', {}, {})
    b.api.start('/b', {}, {})
    expect(active()).toBe(2)

    a.api.abort()
    expect(active()).toBe(1)

    a.scope.stop()
    expect(active()).toBe(1)

    b.scope.stop()
    expect(active()).toBe(0)
  })

  it('K2: repeated start only replaces streams in its own scope', () => {
    const fetchMock = vi.fn(() => new Promise<Response>(() => {}))
    vi.stubGlobal('fetch', fetchMock)
    const a = createSSE()
    const b = createSSE()

    a.api.start('/a1', {}, {})
    b.api.start('/b1', {}, {})
    a.api.start('/a2', {}, {})
    expect(active()).toBe(2)

    a.api.abort()
    expect(active()).toBe(1)

    b.scope.stop()
    expect(active()).toBe(0)
  })

  it('K3: 30s without token reports timeout once and aborts the stream', () => {
    const fetchMock = vi.fn(() => new Promise<Response>(() => {}))
    vi.stubGlobal('fetch', fetchMock)
    const a = createSSE()
    const errors: string[] = []

    a.api.start('/slow', {}, { onError: (code) => errors.push(code) }, {
      tokenTimeoutMs: 100,
    })
    expect(active()).toBe(1)

    vi.advanceTimersByTime(100)
    expect(errors).toEqual(['timeout'])
    expect(active()).toBe(0)
    const calls = fetchMock.mock.calls as unknown as [string, RequestInit][]
    expect(calls[0]?.[1]?.signal?.aborted).toBe(true)
  })

  it('K4: an active abort never reports timeout', () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise<Response>(() => {})))
    const a = createSSE()
    const errors: string[] = []

    a.api.start('/abort', {}, { onError: (code) => errors.push(code) }, {
      tokenTimeoutMs: 100,
    })
    a.api.abort()
    vi.advanceTimersByTime(1000)

    expect(errors).toEqual([])
    expect(active()).toBe(0)
  })
})