// 密钥扩展的逐字推导（FIPS-197 §5.2）。
//
// keyExpansion() 只给结果；这里回答「w[i] 是怎么来的」，供密钥扩展抽屉逐行展开。
// 四种规则：
//   original  原始密钥的 Nk 个字，直接来自输入
//   g         i % Nk == 0：RotWord → SubWord → ⊕Rcon → ⊕ w[i−Nk]
//   subword   Nk > 6 且 i % Nk == 4：只做 SubWord，不旋转、不加 Rcon
//   xor       其余：w[i] = w[i−Nk] ⊕ w[i−1]
//
// 除数 Nk 从字总数反推：words.length = 4 × (Nr + 1)，Nr = Nk + 6。
// engine 层：零 Vue 依赖。

import { RCON } from './aes'
import { subBytes } from './sbox'

export type WordRule = 'original' | 'g' | 'subword' | 'xor'

export interface KeyWordTrace {
  readonly index: number
  readonly rule: WordRule
  /** w[i] 本身 */
  readonly word: readonly number[]
  /** w[i−1]，g 与 xor 的输入 */
  readonly previousWord: readonly number[] | null
  /** w[i−Nk]，最后一步异或的另一半 */
  readonly baseWord: readonly number[] | null
  /** RotWord 之后（只有 g 有） */
  readonly rotated: readonly number[] | null
  /** SubWord 之后（g 与 subword 有） */
  readonly substituted: readonly number[] | null
  /** Rcon 向量，形如 [01,00,00,00]（只有 g 有） */
  readonly rcon: readonly number[] | null
  /** RCON 数组下标，界面上写 Rcon[1] 用（只有 g 有） */
  readonly rconIndex: number | null
}

/** 由密钥扩展结果反推 Nk：44 字 → 4，52 字 → 6，60 字 → 8 */
export function nkFromSchedule(words: readonly (readonly number[])[]): number {
  const nk = words.length / 4 - 7
  if (nk !== 4 && nk !== 6 && nk !== 8) {
    throw new Error(`key schedule must have 44/52/60 words, got ${words.length}`)
  }
  return nk
}

function rot(word: readonly number[]): number[] {
  return [word[1]!, word[2]!, word[3]!, word[0]!]
}

function xor4(a: readonly number[], b: readonly number[]): number[] {
  return [a[0]! ^ b[0]!, a[1]! ^ b[1]!, a[2]! ^ b[2]!, a[3]! ^ b[3]!]
}

/**
 * 推导第 i 个字。`alreadyExpanded` 用来校验：传进来时若与推出来的结果不符，
 * 说明上游数据有问题，直接抛错——界面宁可不显示，也不显示错的推导。
 */
export function keyWordTrace(
  words: readonly (readonly number[])[],
  index: number,
): KeyWordTrace {
  const nk = nkFromSchedule(words)
  const word = words[index]
  if (!word || word.length !== 4) {
    throw new Error(`word ${index} missing or malformed`)
  }

  if (index < nk) {
    return {
      index,
      rule: 'original',
      word,
      previousWord: null,
      baseWord: null,
      rotated: null,
      substituted: null,
      rcon: null,
      rconIndex: null,
    }
  }

  const previousWord = words[index - 1]!
  const baseWord = words[index - nk]!

  if (index % nk === 0) {
    const rconIndex = index / nk - 1
    const rotated = rot(previousWord)
    const substituted = Array.from(subBytes(Uint8Array.from(rotated)))
    const rcon = [RCON[rconIndex]!, 0, 0, 0]
    const temp = xor4(substituted, rcon)
    const derived = xor4(baseWord, temp)
    if (derived.some((byte, k) => byte !== word[k])) {
      throw new Error(`word ${index} derivation mismatch`)
    }
    return {
      index,
      rule: 'g',
      word,
      previousWord,
      baseWord,
      rotated,
      substituted,
      rcon,
      rconIndex,
    }
  }

  if (nk > 6 && index % nk === 4) {
    const substituted = Array.from(subBytes(Uint8Array.from(previousWord)))
    const derived = xor4(baseWord, substituted)
    if (derived.some((byte, k) => byte !== word[k])) {
      throw new Error(`word ${index} derivation mismatch`)
    }
    return {
      index,
      rule: 'subword',
      word,
      previousWord,
      baseWord,
      rotated: null,
      substituted,
      rcon: null,
      rconIndex: null,
    }
  }

  const derived = xor4(baseWord, previousWord)
  if (derived.some((byte, k) => byte !== word[k])) {
    throw new Error(`word ${index} derivation mismatch`)
  }
  return {
    index,
    rule: 'xor',
    word,
    previousWord,
    baseWord,
    rotated: null,
    substituted: null,
    rcon: null,
    rconIndex: null,
  }
}

/** 第 round 轮的轮密钥（16 字节，列优先：w[4r..4r+3] 依次是第 0–3 列） */
export function roundKeyBytes(
  words: readonly (readonly number[])[],
  round: number,
): number[] {
  const out: number[] = []
  for (let i = 0; i < 4; i++) {
    const word = words[round * 4 + i]
    if (!word) throw new Error(`round ${round} out of range`)
    out.push(...word)
  }
  return out
}
