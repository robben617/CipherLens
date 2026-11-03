// 全量 AES 加密 trace。
// 输出字段对齐《前端实现规格》§11.2 的接口契约（snake_case），
// 手册 F3 中的 step_index / changed_idx / round_key_idx / keySchedule 分别对应
// index / changed / key_indices / key_schedule。
//
// 状态约定：16 字节 Uint8Array，列优先，index = col * 4 + row。
// trace 只生成一次；返回类型全部 readonly，调用方不得修改。
// engine 层：零 Vue 依赖，输出可直接 JSON 序列化。

import {
  addRoundKey,
  keyExpansion,
  mixColumns,
  shiftRows,
  type AesKeyBits,
} from './aes'
import { diffState } from './diff'
import { subBytes } from './sbox'

export type TraceOp = 'add_round_key' | 'sub_bytes' | 'shift_rows' | 'mix_columns'

export interface TraceStep {
  readonly index: number
  readonly round: number
  readonly op: TraceOp
  readonly state_before: readonly number[]
  readonly state_after: readonly number[]
  readonly changed: readonly number[]
  readonly key_indices: readonly number[]
  readonly key_words: readonly number[]
  readonly label: string
}

export interface TraceMeta {
  readonly source: 'local-engine'
}

export interface AesTrace {
  readonly trace_id: string
  readonly ciphertext: string
  readonly key_bits: AesKeyBits
  readonly direction: 'encrypt'
  readonly rounds: number
  readonly step_count: number
  readonly key_schedule: readonly (readonly number[])[]
  readonly steps: readonly TraceStep[]
  readonly meta: TraceMeta
}

export interface BuildTraceInput {
  readonly plaintext: string
  readonly key: string
  readonly mode?: 'encrypt' | 'decrypt'
}

function parseHex(hex: string, field: string): Uint8Array {
  const text = hex.trim().toLowerCase()
  if (text.length === 0 || text.length % 2 !== 0 || !/^[0-9a-f]+$/.test(text)) {
    throw new Error(`${field} must be a non-empty hex string`)
  }
  const out = new Uint8Array(text.length / 2)
  for (let i = 0; i < out.length; i++) {
    out[i] = Number.parseInt(text.slice(i * 2, i * 2 + 2), 16)
  }
  return out
}

function bytesToHex(bytes: Uint8Array): string {
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, '0')).join('')
}

function hashText(text: string): string {
  let hash = 0x811c9dc5
  for (let i = 0; i < text.length; i++) {
    hash ^= text.charCodeAt(i)
    hash = Math.imul(hash, 0x01000193)
  }
  return (hash >>> 0).toString(16).padStart(8, '0')
}

function traceIdFor(plaintext: string, key: string, mode: string): string {
  const content = `${plaintext.trim().toLowerCase()}|${key.trim().toLowerCase()}|${mode}`
  return `t_${hashText(content)}`
}

function roundKey(words: readonly Uint8Array[], round: number): Uint8Array {
  const out = new Uint8Array(16)
  for (let word = 0; word < 4; word++) {
    out.set(words[round * 4 + word]!, word * 4)
  }
  return out
}

function appendStep(
  steps: TraceStep[],
  round: number,
  op: TraceOp,
  before: Uint8Array,
  after: Uint8Array,
  keyWords: readonly number[],
  label: string,
): void {
  const { changed } = diffState(before, after)
  steps.push({
    index: steps.length,
    round,
    op,
    state_before: Array.from(before),
    state_after: Array.from(after),
    changed,
    key_indices: keyWords.length > 0 ? Array.from({ length: 16 }, (_, i) => i) : [],
    key_words: Array.from(keyWords),
    label,
  })
}

export function buildTrace(input: BuildTraceInput): AesTrace {
  const mode = input.mode ?? 'encrypt'
  if (mode !== 'encrypt') {
    throw new Error('F3 only supports encrypt trace')
  }

  const plaintext = parseHex(input.plaintext, 'plaintext')
  const key = parseHex(input.key, 'key')

  if (plaintext.length !== 16) {
    throw new Error(`plaintext must be 16 bytes, got ${plaintext.length}`)
  }
  if (key.length !== 16 && key.length !== 24 && key.length !== 32) {
    throw new Error(`key must be 16, 24 or 32 bytes, got ${key.length}`)
  }

  const keyBits = (key.length * 8) as AesKeyBits
  const rounds = key.length / 4 + 6
  const words = keyExpansion(key)
  const steps: TraceStep[] = []

  let state = plaintext.slice()

  const initialAfter = addRoundKey(state, roundKey(words, 0))
  appendStep(steps, 0, 'add_round_key', state, initialAfter, [0, 1, 2, 3], '初始轮密钥加')
  state = initialAfter

  for (let round = 1; round <= rounds; round++) {
    const afterSubBytes = subBytes(state)
    appendStep(steps, round, 'sub_bytes', state, afterSubBytes, [], `第 ${round} 轮 字节代换`)
    state = afterSubBytes

    const afterShiftRows = shiftRows(state)
    appendStep(steps, round, 'shift_rows', state, afterShiftRows, [], `第 ${round} 轮 行移位`)
    state = afterShiftRows

    if (round !== rounds) {
      const afterMixColumns = mixColumns(state)
      appendStep(steps, round, 'mix_columns', state, afterMixColumns, [], `第 ${round} 轮 列混合`)
      state = afterMixColumns
    }

    const keyWords = [round * 4, round * 4 + 1, round * 4 + 2, round * 4 + 3]
    const afterAddRoundKey = addRoundKey(state, roundKey(words, round))
    appendStep(steps, round, 'add_round_key', state, afterAddRoundKey, keyWords, `第 ${round} 轮 轮密钥加`)
    state = afterAddRoundKey
  }

  return {
    trace_id: traceIdFor(input.plaintext, input.key, mode),
    ciphertext: bytesToHex(state),
    key_bits: keyBits,
    direction: 'encrypt',
    rounds,
    step_count: steps.length,
    key_schedule: words.map((word) => Array.from(word)),
    steps,
    meta: { source: 'local-engine' },
  }
}