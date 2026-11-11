export interface SSEHandlers {
  onMeta?: (data: Record<string, unknown>) => void
  /** 结构化回答的分块边界；没有这个回调的服务端不会发 block 事件 */
  onBlock?: (block: Record<string, unknown>) => void
  /** payload 携带 `item: true` 表示这个 token 是一条新列表项的开头 */
  onToken?: (text: string, payload?: Record<string, unknown>) => void
  onDone?: (data: Record<string, unknown>) => void
  onError?: (code: string, message: string) => void
}

export interface ParsedEvent {
  event: string
  data: string
}

/**
 * 解析单个 SSE 帧。
 * 支持 `data:value` / `data: value`、多行 data（用 \n 连接）、注释行与未知字段。
 * 没有 event 字段的帧返回 null（本协议只处理命名事件）。
 */
export function parseEventFrame(frame: string): ParsedEvent | null {
  let event = ''
  const data: string[] = []

  for (const line of frame.split('\n')) {
    if (line.length === 0 || line.startsWith(':')) continue

    const colon = line.indexOf(':')
    const field = colon === -1 ? line : line.slice(0, colon)
    let value = colon === -1 ? '' : line.slice(colon + 1)
    if (value.startsWith(' ')) value = value.slice(1)

    if (field === 'event') event = value
    else if (field === 'data') data.push(value)
  }

  if (!event) return null
  return { event, data: data.join('\n') }
}

function dispatch(frame: string, handlers: SSEHandlers): void {
  const parsed = parseEventFrame(frame)
  if (!parsed) return

  let payload: Record<string, unknown> = {}
  try {
    payload = parsed.data ? JSON.parse(parsed.data) : {}
  } catch {
    return
  }

  if (parsed.event === 'meta') handlers.onMeta?.(payload)
  else if (parsed.event === 'block') handlers.onBlock?.(payload)
  else if (parsed.event === 'token') {
    const text = payload.text ?? payload.t
    handlers.onToken?.(String(text ?? ''), payload)
  } else if (parsed.event === 'done') handlers.onDone?.(payload)
  else if (parsed.event === 'error') {
    handlers.onError?.(String(payload.code ?? 'error'), String(payload.message ?? ''))
  }
}

export async function consumeSSE(response: Response, handlers: SSEHandlers): Promise<void> {
  const reader = response.body?.getReader()
  if (!reader) throw new Error('response body is not readable')
  const decoder = new TextDecoder()
  let buffer = ''

  function drain(flush: boolean): void {
    let index = buffer.indexOf('\n\n')
    while (index >= 0) {
      const frame = buffer.slice(0, index)
      buffer = buffer.slice(index + 2)
      dispatch(frame, handlers)
      index = buffer.indexOf('\n\n')
    }
    if (flush && buffer.trim().length > 0) {
      dispatch(buffer, handlers)
      buffer = ''
    }
  }

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      // 在拼接后的缓冲区上归一化，避免 \r 与 \n 分属两个 chunk 时漏判。
      buffer = buffer.replace(/\r\n/g, '\n')
      drain(false)
    }
    buffer += decoder.decode()
    buffer = buffer.replace(/\r\n/g, '\n')
    drain(true)
  } finally {
    reader.releaseLock?.()
  }
}