import { onScopeDispose } from 'vue'
import { consumeSSE, type SSEHandlers } from '../utils/sse'
const controllers = new Set<AbortController>()
let activeCount = 0
function publish(): void {
  window.__sse = { active: activeCount }
}
declare global {
  interface Window {
    __sse?: { active: number }
  }
}

export function useSSE() {
  function abort(): void {
    controllers.forEach((controller) => controller.abort())
    controllers.clear()
    activeCount = 0
    publish()
  }

  function start(
    url: string,
    payload: Record<string, unknown>,
    handlers: SSEHandlers,
  ): void {
    abort()
    const controller = new AbortController()
    controllers.add(controller)
    activeCount += 1
    publish()

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
        await consumeSSE(response, handlers)
      } catch (error) {
        if ((error as Error).name !== 'AbortError') {
          handlers.onError?.('network_error', (error as Error).message)
        }
      } finally {
        if (controllers.delete(controller)) {
          activeCount = Math.max(0, activeCount - 1)
          publish()
        }
      }
    })()
  }

  onScopeDispose(abort)
  return { start, abort }
}