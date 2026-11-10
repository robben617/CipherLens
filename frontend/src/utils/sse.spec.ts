import { describe, expect, it } from 'vitest'
import { consumeSSE, parseEventFrame, type SSEHandlers } from './sse'

function responseFrom(chunks: readonly string[]): Response {
  const encoder = new TextEncoder()
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(encoder.encode(chunk))
      controller.close()
    },
  })
  return new Response(stream)
}

function collect() {
  const events: string[] = []
  const tokens: string[] = []
  const payloads: Record<string, unknown>[] = []
  const errors: { code: string; message: string }[] = []
  const handlers: SSEHandlers = {
    onMeta: (data) => {
      events.push('meta')
      payloads.push(data)
    },
    onToken: (text) => {
      events.push('token')
      tokens.push(text)
    },
    onDone: (data) => {
      events.push('done')
      payloads.push(data)
    },
    onError: (code, message) => {
      events.push('error')
      errors.push({ code, message })
    },
  }
  return { handlers, events, tokens, payloads, errors }
}

describe('parseEventFrame', () => {
  it('supports data without a leading space and joins multiline data', () => {
    expect(parseEventFrame('event: token\ndata:{"t":"x"}')).toEqual({
      event: 'token',
      data: '{"t":"x"}',
    })
    expect(parseEventFrame('event: token\ndata: {"t":\ndata: "a"}')).toEqual({
      event: 'token',
      data: '{"t":\n"a"}',
    })
  })

  it('ignores comments and frames without an event name', () => {
    expect(parseEventFrame(': keepalive')).toBeNull()
    expect(parseEventFrame('data: {"t":"x"}')).toBeNull()
  })
})

describe('consumeSSE', () => {
  it('parses data: without a space', async () => {
    const result = collect()
    await consumeSSE(responseFrom(['event: token\ndata:{"t":"x"}\n\n']), result.handlers)
    expect(result.tokens).toEqual(['x'])
  })

  it('joins multi-line data before JSON parsing', async () => {
    const result = collect()
    await consumeSSE(
      responseFrom(['event: token\ndata: {"t":\ndata: "a"}\n\n']),
      result.handlers,
    )
    expect(result.tokens).toEqual(['a'])
  })

  it('flushes a trailing frame without a blank line', async () => {
    const result = collect()
    await consumeSSE(responseFrom(['event: done\ndata: {"ok":true}']), result.handlers)
    expect(result.events).toEqual(['done'])
    expect(result.payloads).toEqual([{ ok: true }])
  })

  it('handles CRLF split across chunks', async () => {
    const result = collect()
    await consumeSSE(
      responseFrom(['event: token\r', '\ndata: {"t":"c"}\r\n', '\r\n']),
      result.handlers,
    )
    expect(result.tokens).toEqual(['c'])
  })

  it('ignores comments, unknown events and malformed JSON without crashing', async () => {
    const result = collect()
    await consumeSSE(
      responseFrom([
        ': keepalive\n\n',
        'event: unknown\ndata: {}\n\n',
        'event: token\ndata: {bad\n\n',
        'event: token\ndata: {"t":"ok"}\n\n',
      ]),
      result.handlers,
    )
    expect(result.tokens).toEqual(['ok'])
    expect(result.errors).toEqual([])
  })

  it('dispatches meta, token, done and error in order', async () => {
    const result = collect()
    await consumeSSE(
      responseFrom([
        'event: meta\ndata: {"cache":false}\n\n',
        'event: token\ndata: {"t":"a"}\n\n',
        'event: token\ndata: {"t":"b"}\n\n',
        'event: done\ndata: {"ok":true}\n\n',
        'event: error\ndata: {"code":"x","message":"bad"}\n\n',
      ]),
      result.handlers,
    )
    expect(result.events).toEqual(['meta', 'token', 'token', 'done', 'error'])
    expect(result.tokens).toEqual(['a', 'b'])
    expect(result.errors).toEqual([{ code: 'x', message: 'bad' }])
  })
})