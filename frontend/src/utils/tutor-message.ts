/**
 * 结构化回答的数据模型与增量拼装。
 *
 * 服务端把「这一步发生了什么」拆成四块发过来：先 `block` 开块（正文为空壳），
 * 再若干 `token` 往当前块里填字。这里只负责把事件流拼成可渲染的块数组，
 * 不做任何文案判断 —— 讲什么由服务端决定，前端只决定怎么摆。
 */

export type TutorBlockType = 'conclusion' | 'why' | 'next' | 'cite'

export interface TutorAction {
  label: string
  kind: 'goto-step' | 'open-sbox'
  value: number
}

export type TutorBlock =
  | { type: 'conclusion'; text: string }
  | { type: 'why'; items: string[] }
  | { type: 'next'; text: string; action?: TutorAction }
  | { type: 'cite'; bytes: number[]; total?: number }

function normalizeAction(raw: unknown): TutorAction | undefined {
  if (!raw || typeof raw !== 'object') return undefined
  const value = raw as Record<string, unknown>
  const kind = value.kind === 'open-sbox' ? 'open-sbox' : 'goto-step'
  const target = Number(value.value)
  if (!Number.isFinite(target)) return undefined
  return { label: String(value.label ?? ''), kind, value: target }
}

/** 追加一个块；未知类型直接忽略，保证旧服务端也能被新前端吞下 */
export function appendBlock(blocks: TutorBlock[], raw: Record<string, unknown>): TutorBlock[] {
  const type = String(raw.type ?? '')

  if (type === 'conclusion') {
    blocks.push({ type: 'conclusion', text: String(raw.text ?? '') })
  } else if (type === 'why') {
    const items = Array.isArray(raw.items) ? raw.items.map((item) => String(item)) : []
    blocks.push({ type: 'why', items })
  } else if (type === 'next') {
    blocks.push({
      type: 'next',
      text: String(raw.text ?? ''),
      action: normalizeAction(raw.action),
    })
  } else if (type === 'cite') {
    const bytes = Array.isArray(raw.bytes)
      ? raw.bytes.map(Number).filter((byte) => Number.isInteger(byte) && byte >= 0 && byte < 16)
      : []
    const total = Number(raw.total)
    blocks.push({ type: 'cite', bytes, ...(Number.isFinite(total) ? { total } : {}) })
  }

  return blocks
}

/**
 * 往最后一块里追加一段文字。
 * `newItem` 为真表示这是一条新列表项的开头 —— 服务端每发一条 `why` 都会带上。
 */
export function appendToken(blocks: TutorBlock[], text: string, newItem = false): TutorBlock[] {
  const last = blocks[blocks.length - 1]
  if (!last) return blocks

  if (last.type === 'conclusion' || last.type === 'next') {
    last.text += text
  } else if (last.type === 'why') {
    if (newItem || last.items.length === 0) last.items.push(text)
    else last.items[last.items.length - 1] += text
  }

  return blocks
}

/** 纯文本视图：给读屏播报与折叠摘要用，不是渲染源 */
export function blocksToText(blocks: TutorBlock[]): string {
  const parts: string[] = []
  for (const block of blocks) {
    if (block.type === 'conclusion') parts.push(block.text)
    else if (block.type === 'why') parts.push(...block.items)
    else if (block.type === 'next') parts.push(block.text)
    else if (block.type === 'cite' && block.bytes.length) {
      parts.push(`依据：${block.bytes.map((byte) => `0x${byte.toString(16).toUpperCase().padStart(2, '0')}`).join('、')}`)
    }
  }
  return parts.join(' ')
}

/** 四块齐了才算讲完；流式过程里用于判断要不要显示光标 */
export function isComplete(blocks: TutorBlock[]): boolean {
  return blocks.some((block) => block.type === 'cite')
}
