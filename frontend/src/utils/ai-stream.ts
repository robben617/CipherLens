import { consumeSSE, type SSEHandlers } from './sse'

export interface AiStreamOptions {
  url: string
  payload: Record<string, unknown>
  handlers: SSEHandlers
  tokenTimeoutMs?: number
}

export interface AiStream {
  abort: (reason?: string) => void
  promise: Promise<void>
  settled: () => boolean
}

const DEFAULT_TOKEN_TIMEOUT_MS = 30000

export function startAiStream({
  url,
  payload,
  handlers,
  tokenTimeoutMs = DEFAULT_TOKEN_TIMEOUT_MS,
}: AiStreamOptions): AiStream {
  const controller = new AbortController()
  let settled = false
  let aborted = false
  let timedOut = false
  let timer: ReturnType<typeof setTimeout> | undefined

  const clearTimer = (): void => {
    if (timer !== undefined) {
      clearTimeout(timer)
      timer = undefined
    }
  }

  const settle = (): void => {
    if (settled) return
    settled = true
    clearTimer()
  }

  const armTimer = (): void => {
    if (settled) return
    clearTimer()
    timer = setTimeout(() => {
      if (settled) return
      timedOut = true
      controller.abort()
      settle()
      handlers.onError?.('timeout', `超过 ${tokenTimeoutMs}ms 未收到 token`)
    }, tokenTimeoutMs)
  }

  const wrapped: SSEHandlers = {
    onMeta: (data) => {
      armTimer()
      handlers.onMeta?.(data)
    },
    onBlock: (block) => {
      armTimer()
      handlers.onBlock?.(block)
    },
    onToken: (text, data) => {
      armTimer()
      handlers.onToken?.(text, data)
    },
    onToolStart: (data) => {
      armTimer()
      handlers.onToolStart?.(data)
    },
    onToolResult: (data) => {
      armTimer()
      handlers.onToolResult?.(data)
    },
    onToolEnd: (data) => {
      armTimer()
      handlers.onToolEnd?.(data)
    },
    onSearchStart: (data) => {
      armTimer()
      handlers.onSearchStart?.(data)
    },
    onSearchResult: (data) => {
      armTimer()
      handlers.onSearchResult?.(data)
    },
    onDone: (data) => {
      settle()
      handlers.onDone?.(data)
    },
    onError: (code, message, data) => {
      if (timedOut) return
      settle()
      handlers.onError?.(code, message, data)
    },
  }

  armTimer()

  const promise = (async () => {
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'text/event-stream',
        },
        body: JSON.stringify(payload),
        signal: controller.signal,
      })
      if (!response.ok) {
        if (!aborted && !timedOut) {
          settle()
          handlers.onError?.('network_error', `HTTP ${response.status}`)
        }
        return
      }
      await consumeSSE(response, wrapped)
    } catch (error) {
      if (!aborted && !timedOut) {
        settle()
        handlers.onError?.('network_error', (error as Error).message)
      }
    } finally {
      settle()
    }
  })()

  function abort(_reason?: string): void {
    if (settled) return
    aborted = true
    controller.abort()
    settle()
  }

  return {
    abort,
    promise,
    settled: () => settled,
  }
}