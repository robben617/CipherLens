// 全量 AES 加/解密 trace。
// 输出字段对齐《前端实现规格》§11.2 的接口契约（snake_case），
// 手册 F3 中的 step_index / changed_idx / round_key_idx / keySchedule 分别对应
// index / changed / key_indices / key_schedule。
//
// 状态约定：16 字节 Uint8Array，列优先，index = col * 4 + row。
// trace 只生成一次；返回类型全部 readonly，调用方不得修改。
// engine 层：零 Vue 依赖，输出可直接 JSON 序列化。

import {
  addRoundKey,
  invMixColumns,
  invShiftRows,
  keyExpansion,
  mixColumns,
  shiftRows,
  type AesKeyBits,
} from './aes'
import { diffState } from './diff'
import { invSubBytes, subBytes } from './sbox'
// 四步的中文名只维护在 data/glossary（纯数据模块，不依赖 Vue）；
// 后端 services/glossary.py 是同一份清单，compare_trace.py 会逐字比对 label。
import { OP_LABEL } from '../data/glossary'

export type TraceOp = 'add_round_key' | 'sub_bytes' | 'shift_rows' | 'mix_columns'

/** 加密：明文 → 密文；解密：密文 → 明文 */
export type TraceDirection = 'encrypt' | 'decrypt'

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
  /** 加密=密文，解密=明文（与 output 同值，保留旧字段名） */
  readonly ciphertext: string
  /** 这一路算完得到什么：加密密文 / 解密明文 */
  readonly output: string
  readonly key_bits: AesKeyBits
  readonly direction: TraceDirection
  readonly rounds: number
  readonly step_count: number
  readonly key_schedule: readonly (readonly number[])[]
  readonly steps: readonly TraceStep[]
  readonly meta: TraceMeta
}

export interface BuildTraceInput {
  readonly plaintext: string
  readonly key: string
  readonly mode?: TraceDirection
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

/**
 * 步骤中文名 —— 与后端 `_step_label` 逐字一致（tools/compare_trace.py 会比对 label）。
 *
 * 轮密钥加是自己的逆操作（a ⊕ k ⊕ k = a），解密时它不加「逆」字，
 * 否则会让人以为要多做一次反转。
 */
function stepLabel(round: number, op: TraceOp, rounds: number, direction: TraceDirection): string {
  const name = OP_LABEL[op] ?? op
  if (direction !== 'decrypt') {
    return round === 0 ? '初始轮密钥加' : `第 ${round} 轮 ${name}`
  }
  if (op === 'add_round_key' && round === rounds) {
    return `初始轮密钥加（第 ${rounds} 轮密钥）`
  }
  if (op === 'add_round_key' && round === 0) {
    return '收尾轮密钥加（第 0 轮密钥）'
  }
  const prefix = op === 'add_round_key' ? '' : '逆'
  return `第 ${round} 轮 ${prefix}${name}`
}

function wordIndices(round: number): readonly number[] {
  return [round * 4, round * 4 + 1, round * 4 + 2, round * 4 + 3]
}

function buildEncryptSteps(
  steps: TraceStep[],
  words: readonly Uint8Array[],
  rounds: number,
  plaintext: Uint8Array,
): void {
  let state = plaintext
  const initialAfter = addRoundKey(state, roundKey(words, 0))
  appendStep(
    steps,
    0,
    'add_round_key',
    state,
    initialAfter,
    wordIndices(0),
    stepLabel(0, 'add_round_key', rounds, 'encrypt'),
  )
  state = initialAfter

  for (let round = 1; round <= rounds; round++) {
    const afterSubBytes = subBytes(state)
    appendStep(steps, round, 'sub_bytes', state, afterSubBytes, [], stepLabel(round, 'sub_bytes', rounds, 'encrypt'))
    state = afterSubBytes

    const afterShiftRows = shiftRows(state)
    appendStep(steps, round, 'shift_rows', state, afterShiftRows, [], stepLabel(round, 'shift_rows', rounds, 'encrypt'))
    state = afterShiftRows

    if (round !== rounds) {
      const afterMixColumns = mixColumns(state)
      appendStep(steps, round, 'mix_columns', state, afterMixColumns, [], stepLabel(round, 'mix_columns', rounds, 'encrypt'))
      state = afterMixColumns
    }

    const afterAddRoundKey = addRoundKey(state, roundKey(words, round))
    appendStep(
      steps,
      round,
      'add_round_key',
      state,
      afterAddRoundKey,
      wordIndices(round),
      stepLabel(round, 'add_round_key', rounds, 'encrypt'),
    )
    state = afterAddRoundKey
  }
}

/**
 * FIPS-197 §5.3 InvCipher：轮次倒着走，每轮里四步也倒着做。
 * 步数与加密相同（128 位 = 40 步），时间轴能直接看出方向。
 */
function buildDecryptSteps(
  steps: TraceStep[],
  words: readonly Uint8Array[],
  rounds: number,
  ciphertext: Uint8Array,
): void {
  let state = ciphertext

  const initialAfter = addRoundKey(state, roundKey(words, rounds))
  appendStep(
    steps,
    rounds,
    'add_round_key',
    state,
    initialAfter,
    wordIndices(rounds),
    stepLabel(rounds, 'add_round_key', rounds, 'decrypt'),
  )
  state = initialAfter

  for (let round = rounds - 1; round > 0; round--) {
    const afterInvShift = invShiftRows(state)
    appendStep(steps, round, 'shift_rows', state, afterInvShift, [], stepLabel(round, 'shift_rows', rounds, 'decrypt'))
    state = afterInvShift

    const afterInvSub = invSubBytes(state)
    appendStep(steps, round, 'sub_bytes', state, afterInvSub, [], stepLabel(round, 'sub_bytes', rounds, 'decrypt'))
    state = afterInvSub

    const afterAddRoundKey = addRoundKey(state, roundKey(words, round))
    appendStep(
      steps,
      round,
      'add_round_key',
      state,
      afterAddRoundKey,
      wordIndices(round),
      stepLabel(round, 'add_round_key', rounds, 'decrypt'),
    )
    state = afterAddRoundKey

    const afterInvMix = invMixColumns(state)
    appendStep(steps, round, 'mix_columns', state, afterInvMix, [], stepLabel(round, 'mix_columns', rounds, 'decrypt'))
    state = afterInvMix
  }

  const afterFinalShift = invShiftRows(state)
  appendStep(steps, 0, 'shift_rows', state, afterFinalShift, [], stepLabel(0, 'shift_rows', rounds, 'decrypt'))
  state = afterFinalShift

  const afterFinalSub = invSubBytes(state)
  appendStep(steps, 0, 'sub_bytes', state, afterFinalSub, [], stepLabel(0, 'sub_bytes', rounds, 'decrypt'))
  state = afterFinalSub

  const afterFinalKey = addRoundKey(state, roundKey(words, 0))
  appendStep(steps, 0, 'add_round_key', state, afterFinalKey, wordIndices(0), stepLabel(0, 'add_round_key', rounds, 'decrypt'))
}

export function buildTrace(input: BuildTraceInput): AesTrace {
  const mode: TraceDirection = input.mode ?? 'encrypt'
  if (mode !== 'encrypt' && mode !== 'decrypt') {
    throw new Error(`unknown direction: ${String(mode)}`)
  }

  const plaintext = parseHex(input.plaintext, mode === 'decrypt' ? 'ciphertext' : 'plaintext')
  const key = parseHex(input.key, 'key')

  if (plaintext.length !== 16) {
    throw new Error(`${mode === 'decrypt' ? 'ciphertext' : 'plaintext'} must be 16 bytes, got ${plaintext.length}`)
  }
  if (key.length !== 16 && key.length !== 24 && key.length !== 32) {
    throw new Error(`key must be 16, 24 or 32 bytes, got ${key.length}`)
  }

  const keyBits = (key.length * 8) as AesKeyBits
  const rounds = key.length / 4 + 6
  const words = keyExpansion(key)
  const steps: TraceStep[] = []

  if (mode === 'decrypt') buildDecryptSteps(steps, words, rounds, plaintext)
  else buildEncryptSteps(steps, words, rounds, plaintext)

  const last = steps[steps.length - 1]
  const output = bytesToHex(Uint8Array.from(last ? last.state_after : Array.from(plaintext)))

  return {
    trace_id: traceIdFor(input.plaintext, input.key, mode),
    ciphertext: output,
    output,
    key_bits: keyBits,
    direction: mode,
    rounds,
    step_count: steps.length,
    key_schedule: words.map((word) => Array.from(word)),
    steps,
    meta: { source: 'local-engine' },
  }
}