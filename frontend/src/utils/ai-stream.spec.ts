import { afterEach, describe, expect, it, vi } from 'vitest'
import { startAiStream } from './ai-stream'

function responseFrom(frames: readonly string[]): Response {
  const encoder = new TextEncoder()
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const frame of frames) controller.enqueue(encoder.encode(frame))
      controller.close()
    },
  })
  return new Response(stream)
}

afterEach(() => {
  vi.useRealTimers()
  vi.unstubAllGlobals()
})

describe('startAiStream', () => {
  it('dispatches meta → block → token → done and settles', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve(
          responseFrom([
            'event: meta\ndata: {"source":"local"}\n\n',
            'event: block\ndata: {"type":"conclusion","text":"x"}\n\n',
            'event: token\ndata: {"t":"a"}\n\n',
            'event: done\ndata: {"finish":"stop"}\n\n',
          ]),
        ),
      ),
    )
    const events: string[] = []
    const stream = startAiStream({
      url: '/api/ai/ask',
      payload: { page: 'home' },
      handlers: {
        onMeta: () => events.push('meta'),
        onBlock: () => events.push('block'),
        onToken: () => events.push('token'),
        onDone: () => events.push('done'),
        onError: () => events.push('error'),
      },
    })

    await stream.promise
    expect(events).toEqual(['meta', 'block', 'token', 'done'])
    expect(stream.settled()).toBe(true)
  })

  it('reports timeout once when only meta arrives', () => {
    vi.useFakeTimers()
    vi.stubGlobal('fetch', vi.fn(() => new Promise<Response>(() => {})))
    const errors: string[] = []
    const stream = startAiStream({
      url: '/api/ai/ask',
      payload: { page: 'home' },
      tokenTimeoutMs: 100,
      handlers: {
        onError: (code) => errors.push(code),
      },
    })

    vi.advanceTimersByTime(100)
    expect(errors).toEqual(['timeout'])
    expect(stream.settled()).toBe(true)
  })

  it('abort is idempotent and never reports an error', () => {
    vi.useFakeTimers()
    vi.stubGlobal('fetch', vi.fn(() => new Promise<Response>(() => {})))
    const errors: string[] = []
    const stream = startAiStream({
      url: '/api/ai/ask',
      payload: { page: 'sbox' },
      tokenTimeoutMs: 100,
      handlers: {
        onError: (code) => errors.push(code),
      },
    })

    stream.abort('interrupted')
    stream.abort('again')
    vi.advanceTimersByTime(1000)
    expect(errors).toEqual([])
    expect(stream.settled()).toBe(true)
  })

  it('maps non-2xx responses to network_error once', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve(new Response('', { status: 500 }))),
    )
    const errors: string[] = []
    const stream = startAiStream({
      url: '/api/ai/ask',
      payload: { page: 'home' },
      handlers: {
        onError: (code) => errors.push(code),
      },
    })

    await stream.promise
    expect(errors).toEqual(['network_error'])
    expect(stream.settled()).toBe(true)
  })

  it('does not duplicate an error event', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve(
          responseFrom([
            'event: error\ndata: {"code":"llm_unavailable","message":"bad"}\n\n',
          ]),
        ),
      ),
    )
    const errors: string[] = []
    const stream = startAiStream({
      url: '/api/ai/ask',
      payload: { page: 'avalanche' },
      handlers: {
        onError: (code) => errors.push(code),
      },
    })

    await stream.promise
    expect(errors).toEqual(['llm_unavailable'])
  })
})