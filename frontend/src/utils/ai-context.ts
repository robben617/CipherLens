export type PageKey = 'home' | 'sbox' | 'avalanche' | 'workbench'


export type ApiPageContext =
  | { page: 'home' }
  | {
      page: 'sbox'
      mode?: 'forward' | 'inverse'
      input?: number
      output?: number
      selected_hex?: string
    }
  | {
      page: 'avalanche'
      target?: 'plaintext' | 'key'
      byte_index?: number
      bit_index?: number
      key_bits?: 128 | 192 | 256
      changed_bits?: number
      total_bits?: number
      rate?: number
      sweep_mean?: number
    }

type RawContext = Record<string, unknown>

function read(raw: RawContext, ...keys: string[]): unknown {
  for (const key of keys) {
    if (Object.prototype.hasOwnProperty.call(raw, key)) return raw[key]
  }
  return undefined
}

function integerIn(value: unknown, min: number, max: number): number | undefined {
  return typeof value === 'number' &&
    Number.isInteger(value) &&
    value >= min &&
    value <= max
    ? value
    : undefined
}

function finiteIn(value: unknown, min: number, max: number): number | undefined {
  return typeof value === 'number' &&
    Number.isFinite(value) &&
    value >= min &&
    value <= max
    ? value
    : undefined
}

export function toWireContext(
  page: 'home' | 'sbox' | 'avalanche',
  raw: RawContext,
): ApiPageContext
export function toWireContext(
  page: 'workbench',
  raw: RawContext,
): null
export function toWireContext(
  page: PageKey,
  raw: RawContext,
): ApiPageContext | null
export function toWireContext(
  page: PageKey,
  raw: RawContext,
): ApiPageContext | null {
  if (page === 'home') return { page: 'home' }
  if (page === 'workbench') return null

  if (page === 'sbox') {
    const modeValue = read(raw, 'mode')
    const mode =
      modeValue === 'forward' || modeValue === 'inverse' ? modeValue : undefined
    const input = integerIn(read(raw, 'input'), 0, 255)
    const output = integerIn(read(raw, 'output'), 0, 255)
    const paired = input !== undefined && output !== undefined
    const selectedValue = read(raw, 'selected_hex', 'selectedHex')
    const selected =
      typeof selectedValue === 'string' && /^0x[0-9A-Fa-f]{2}$/.test(selectedValue)
        ? selectedValue
        : undefined

    return {
      page: 'sbox',
      ...(mode ? { mode } : {}),
      ...(paired ? { input, output } : {}),
      ...(selected ? { selected_hex: selected } : {}),
    }
  }

  const targetValue = read(raw, 'target')
  const target =
    targetValue === 'plaintext' || targetValue === 'key'
      ? targetValue
      : undefined
  const byteIndex = integerIn(read(raw, 'byte_index', 'byteIndex'), 0, 31)
  const bitIndex = integerIn(read(raw, 'bit_index', 'bitIndex'), 0, 7)
  const keyBitsValue = integerIn(read(raw, 'key_bits', 'keyBits'), 128, 256)
  const keyBits =
    keyBitsValue === 128 || keyBitsValue === 192 || keyBitsValue === 256
      ? keyBitsValue
      : undefined
  const changedBits = integerIn(
    read(raw, 'changed_bits', 'changedBits'),
    0,
    128,
  )
  const totalBits = integerIn(read(raw, 'total_bits', 'totalBits'), 0, 128)
  const rate = finiteIn(read(raw, 'rate'), 0, 1)
  const sweepMean = finiteIn(read(raw, 'sweep_mean', 'sweepMean'), 0, 128)

  return {
    page: 'avalanche',
    ...(target ? { target } : {}),
    ...(byteIndex !== undefined ? { byte_index: byteIndex } : {}),
    ...(bitIndex !== undefined ? { bit_index: bitIndex } : {}),
    ...(keyBits !== undefined ? { key_bits: keyBits } : {}),
    ...(changedBits !== undefined ? { changed_bits: changedBits } : {}),
    ...(totalBits !== undefined ? { total_bits: totalBits } : {}),
    ...(rate !== undefined ? { rate } : {}),
    ...(sweepMean !== undefined ? { sweep_mean: sweepMean } : {}),
  }
}

export function hasSboxContext(
  context: ApiPageContext | null,
): context is Extract<ApiPageContext, { page: 'sbox' }> & {
  input: number
  output: number
} {
  return (
    context?.page === 'sbox' &&
    typeof context.input === 'number' &&
    typeof context.output === 'number'
  )
}

export function hasAvalancheResult(
  context: ApiPageContext | null,
): context is Extract<ApiPageContext, { page: 'avalanche' }> & {
  changed_bits: number
  total_bits: number
  rate: number
} {
  return (
    context?.page === 'avalanche' &&
    typeof context.changed_bits === 'number' &&
    typeof context.total_bits === 'number' &&
    typeof context.rate === 'number'
  )
}

export function normalizeQuestion(question: string): string {
  return question.normalize('NFKC').trim().replace(/\s+/g, ' ')
}

function compactJson(value: Record<string, unknown>): string {
  return JSON.stringify(value)
}

async function sha256Hex(input: string): Promise<string> {
  const bytes = new TextEncoder().encode(input)
  const digest = await crypto.subtle.digest('SHA-256', bytes)
  return Array.from(new Uint8Array(digest), (value) =>
    value.toString(16).padStart(2, '0'),
  ).join('')
}

export async function contextFingerprint(
  page: PageKey,
  context: ApiPageContext | null,
  question: string,
): Promise<string> {
  const normalized = normalizeQuestion(question)
  let ordered: Record<string, unknown>

  if (!context || page === 'workbench') {
    ordered = { page, question: normalized }
  } else if (context.page === 'home') {
    ordered = { page: 'home', question: normalized }
  } else if (context.page === 'sbox') {
    ordered = {
      page: 'sbox',
      mode: context.mode ?? '',
      input: context.input ?? null,
      output: context.output ?? null,
      selected_hex: context.selected_hex ?? '',
      question: normalized,
    }
  } else {
    ordered = {
      page: 'avalanche',
      target: context.target ?? '',
      byte_index: context.byte_index ?? null,
      bit_index: context.bit_index ?? null,
      key_bits: context.key_bits ?? null,
      changed_bits: context.changed_bits ?? null,
      total_bits: context.total_bits ?? null,
      rate: context.rate ?? null,
      sweep_mean: context.sweep_mean ?? null,
      question: normalized,
    }
  }

  const hex = await sha256Hex(compactJson(ordered))
  return hex.slice(0, 16)
}

export function describeContext(
  page: PageKey,
  context: ApiPageContext | null,
): string {
  if (page === 'home') return '通用讲解 · 未引用本页数值'
  if (page === 'workbench') return '工作台当前步 · 已引用 trace'
  if (!context || context.page !== page) return '未提供本页上下文'

  if (context.page === 'sbox') {
    if (!hasSboxContext(context)) return '未选中字节 · 先点一格再问'
    const mode = context.mode === 'inverse' ? '逆向' : '正向'
    return `输入 0x${context.input.toString(16).toUpperCase().padStart(2, '0')} → 输出 0x${context.output.toString(16).toUpperCase().padStart(2, '0')} · ${mode}`
  }

  const position =
    context.target && context.byte_index !== undefined
      ? `${context.target === 'key' ? '密钥' : '明文'}第 ${context.byte_index} 字节${
          context.bit_index !== undefined ? `第 ${context.bit_index} 位` : ''
        }`
      : '未提供实验位置'
  if (!hasAvalancheResult(context)) return `${position} · 先跑一次实验`
  return `${position} · ${context.changed_bits}/${context.total_bits} · ${(context.rate * 100).toFixed(1)}%`
}