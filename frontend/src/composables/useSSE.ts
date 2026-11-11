import { onScopeDispose } from 'vue'
import { consumeSSE, type SSEHandlers } from '../utils/sse'

declare global {
  interface Window {
    __sse?: { active: number }
  }
}

export interface SSEOptions {
  tokenTimeoutMs?: number
}

const DEFAULT_TOKEN_TIMEOUT_MS = 30000
let activeCount = 0

function publish(): void {
  if (typeof window !== 'undefined') {
    window.__sse = { active: activeCount }
  }
}

export function useSSE() {
  const controllers = new Set<AbortController>()
  const timers = new Map<AbortController, ReturnType<typeof setTimeout>>()

  function abort(): void {
    const count = controllers.size
    controllers.forEach((controller) => {
      const timer = timers.get(controller)
      if (timer !== undefined) clearTimeout(timer)
      timers.delete(controller)
      controller.abort()
    })
    timers.clear()
    controllers.clear()
    activeCount = Math.max(0, activeCount - count)
    publish()
  }

  function start(
    url: string,
    payload: Record<string, unknown>,
    handlers: SSEHandlers,
    options: SSEOptions = {},
  ): void {
    abort()

    const controller = new AbortController()
    controllers.add(controller)
    activeCount += 1
    publish()

    const timeoutMs = options.tokenTimeoutMs ?? DEFAULT_TOKEN_TIMEOUT_MS
    let settled = false
    let timedOut = false

    const clearTimer = (): void => {
      const timer = timers.get(controller)
      if (timer !== undefined) {
        clearTimeout(timer)
        timers.delete(controller)
      }
    }

    const settle = (): void => {
      if (settled) return
      settled = true
      clearTimer()
      if (controllers.delete(controller)) {
        activeCount = Math.max(0, activeCount - 1)
        publish()
      }
    }

    const armTokenTimeout = (): void => {
      clearTimer()
      const timer = setTimeout(() => {
        timedOut = true
        clearTimer()
        controller.abort()
        settle()
        handlers.onError?.('timeout', `超过 ${timeoutMs}ms 未收到 token`)
      }, timeoutMs)
      timers.set(controller, timer)
    }

    const wrapped: SSEHandlers = {
      onMeta: handlers.onMeta,
      onBlock: (block) => {
        // 结构帧也算「有进展」：四块之间可能隔几秒，别让它被当成卡死
        armTokenTimeout()
        handlers.onBlock?.(block)
      },
      onToken: (text, payload) => {
        armTokenTimeout()
        handlers.onToken?.(text, payload)
      },
      onDone: (data) => {
        settle()
        handlers.onDone?.(data)
      },
      onError: (code, message) => {
        if (timedOut) return
        settle()
        handlers.onError?.(code, message)
      },
    }

    armTokenTimeout()

    void (async () => {
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
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        await consumeSSE(response, wrapped)
      } catch (error) {
        if ((error as Error).name !== 'AbortError' && !timedOut) {
          settle()
          handlers.onError?.('network_error', (error as Error).message)
        }
      } finally {
        settle()
      }
    })()
  }

  onScopeDispose(abort)
  return { start, abort }
}