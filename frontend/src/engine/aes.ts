// AES round transforms and key expansion, following FIPS-197 §5.
//
// 状态矩阵约定：长度 16 的 Uint8Array，列优先存储，index = col * 4 + row。
// 例：state[0..3] 是第 0 列的 4 个字节（row 0..3）。
//
// 所有变换返回新的 Uint8Array，不原地修改入参。
// engine 层：零 Vue 依赖，可在 Node 中直接运行。
// 不引入任何加密库；乘 2 用 xtime 位运算，不用查表。

import { subBytes } from './sbox'

export type AesKeyBits = 128 | 192 | 256

export const RCON: Uint8Array = Uint8Array.from([
  0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36,
])

function assertStateLength(state: Uint8Array): void {
  if (state.length !== 16) {
    throw new Error(`AES state must be 16 bytes, got ${state.length}`)
  }
}

function xtime(value: number): number {
  return ((value << 1) ^ (value & 0x80 ? 0x1b : 0)) & 0xff
}

function multiply(a: number, b: number): number {
  let result = 0
  let left = a
  let right = b
  while (right > 0) {
    if (right & 1) result ^= left
    left = xtime(left)
    right >>= 1
  }
  return result & 0xff
}

export function addRoundKey(state: Uint8Array, roundKey: Uint8Array): Uint8Array {
  if (state.length !== roundKey.length) {
    throw new Error(`state and roundKey length mismatch: ${state.length} vs ${roundKey.length}`)
  }
  const out = new Uint8Array(state.length)
  for (let i = 0; i < state.length; i++) {
    out[i] = state[i]! ^ roundKey[i]!
  }
  return out
}

export function shiftRows(state: Uint8Array): Uint8Array {
  assertStateLength(state)
  const out = new Uint8Array(16)
  for (let row = 0; row < 4; row++) {
    for (let col = 0; col < 4; col++) {
      out[col * 4 + row] = state[((col + row) % 4) * 4 + row]!
    }
  }
  return out
}

export function invShiftRows(state: Uint8Array): Uint8Array {
  assertStateLength(state)
  const out = new Uint8Array(16)
  for (let row = 0; row < 4; row++) {
    for (let col = 0; col < 4; col++) {
      out[col * 4 + row] = state[((col - row + 4) % 4) * 4 + row]!
    }
  }
  return out
}

export function mixColumns(state: Uint8Array): Uint8Array {
  assertStateLength(state)
  const out = new Uint8Array(16)
  for (let col = 0; col < 4; col++) {
    const i = col * 4
    const a0 = state[i]!
    const a1 = state[i + 1]!
    const a2 = state[i + 2]!
    const a3 = state[i + 3]!
    out[i] = multiply(a0, 2) ^ multiply(a1, 3) ^ a2 ^ a3
    out[i + 1] = a0 ^ multiply(a1, 2) ^ multiply(a2, 3) ^ a3
    out[i + 2] = a0 ^ a1 ^ multiply(a2, 2) ^ multiply(a3, 3)
    out[i + 3] = multiply(a0, 3) ^ a1 ^ a2 ^ multiply(a3, 2)
  }
  return out
}

export function invMixColumns(state: Uint8Array): Uint8Array {
  assertStateLength(state)
  const out = new Uint8Array(16)
  for (let col = 0; col < 4; col++) {
    const i = col * 4
    const a0 = state[i]!
    const a1 = state[i + 1]!
    const a2 = state[i + 2]!
    const a3 = state[i + 3]!
    out[i] = multiply(a0, 14) ^ multiply(a1, 11) ^ multiply(a2, 13) ^ multiply(a3, 9)
    out[i + 1] = multiply(a0, 9) ^ multiply(a1, 14) ^ multiply(a2, 11) ^ multiply(a3, 13)
    out[i + 2] = multiply(a0, 13) ^ multiply(a1, 9) ^ multiply(a2, 14) ^ multiply(a3, 11)
    out[i + 3] = multiply(a0, 11) ^ multiply(a1, 13) ^ multiply(a2, 9) ^ multiply(a3, 14)
  }
  return out
}

function rotWord(word: Uint8Array): Uint8Array {
  return Uint8Array.from([word[1]!, word[2]!, word[3]!, word[0]!])
}

export function keyExpansion(key: Uint8Array): Uint8Array[] {
  const nk = key.length / 4
  if (nk !== 4 && nk !== 6 && nk !== 8) {
    throw new Error(`AES key must be 16, 24 or 32 bytes, got ${key.length}`)
  }

  const nr = nk + 6
  const totalWords = 4 * (nr + 1)
  const words: Uint8Array[] = []

  for (let i = 0; i < nk; i++) {
    words.push(key.slice(i * 4, i * 4 + 4))
  }

  for (let i = nk; i < totalWords; i++) {
    let temp = words[i - 1]!.slice()
    if (i % nk === 0) {
      temp = subBytes(rotWord(temp))
      temp[0] = temp[0]! ^ RCON[i / nk - 1]!
    } else if (nk > 6 && i % nk === 4) {
      temp = subBytes(temp)
    }

    const previous = words[i - nk]!
    const next = new Uint8Array(4)
    for (let j = 0; j < 4; j++) {
      next[j] = previous[j]! ^ temp[j]!
    }
    words.push(next)
  }

  return words
}