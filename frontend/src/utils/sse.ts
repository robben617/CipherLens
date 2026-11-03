export interface SSEHandlers {
  onMeta?: (data: Record<string, unknown>) => void
  onToken?: (text: string) => void
  onDone?: (data: Record<string, unknown>) => void
  onError?: (code: string, message: string) => void
}

function dispatch(frame: string, handlers: SSEHandlers): void {
  let event = ''
  let data = ''
  for (const line of frame.split('\n')) {
    if (line.startsWith('event: ')) event = line.slice(7).trim()
    else if (line.startsWith('data: ')) data += line.slice(6)
  }
  if (!event) return
  let payload: Record<string, unknown> = {}
  try {
    payload = data ? JSON.parse(data) : {}
  } catch {
    return
  }
  if (event === 'meta') handlers.onMeta?.(payload)
  else if (event === 'token') handlers.onToken?.(String(payload.t ?? ''))
  else if (event === 'done') handlers.onDone?.(payload)
  else if (event === 'error') {
    handlers.onError?.(String(payload.code ?? 'error'), String(payload.message ?? ''))
  }
}

export async function consumeSSE(response: Response, handlers: SSEHandlers): Promise<void> {
  const reader = response.body?.getReader()
  if (!reader) throw new Error('response body is not readable')
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n')
    let index = buffer.indexOf('\n\n')
    while (index >= 0) {
      dispatch(buffer.slice(0, index), handlers)
      buffer = buffer.slice(index + 2)
      index = buffer.indexOf('\n\n')
    }
  }
}