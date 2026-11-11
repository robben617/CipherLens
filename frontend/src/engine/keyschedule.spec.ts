import { describe, expect, it } from 'vitest'
import { keyExpansion } from './aes'
import { keyWordTrace, nkFromSchedule, roundKeyBytes } from './keyschedule'

const hex = (bytes: readonly number[]): string =>
  bytes.map((b) => b.toString(16).padStart(2, '0')).join('')

const wordsOf = (key: string): readonly (readonly number[])[] =>
  keyExpansion(
    Uint8Array.from(key.match(/../g)!.map((byte) => parseInt(byte, 16))),
  ).map((word) => Array.from(word))

/** FIPS-197 附录 A.1 的密钥 */
const A1 = wordsOf('2b7e151628aed2a6abf7158809cf4f3c')
/** 设计稿表格里的那组：000102…0f */
const SEQ = wordsOf('000102030405060708090a0b0c0d0e0f')

const dump = (bytes: readonly number[]): string => hex(bytes)

describe('nkFromSchedule', () => {
  it('由字总数反推 Nk', () => {
    expect(nkFromSchedule(Array.from({ length: 44 }, () => [0, 0, 0, 0]))).toBe(4)
    expect(nkFromSchedule(Array.from({ length: 52 }, () => [0, 0, 0, 0]))).toBe(6)
    expect(nkFromSchedule(Array.from({ length: 60 }, () => [0, 0, 0, 0]))).toBe(8)
  })

  it('字总数不对时报错', () => {
    expect(() => nkFromSchedule(Array.from({ length: 40 }, () => [0, 0, 0, 0]))).toThrow()
  })
})

describe('keyWordTrace · FIPS-197 附录 A.1（密钥 2b7e1516…）', () => {
  it('前 Nk 个字就是原始密钥', () => {
    expect(A1.slice(0, 4).map(dump)).toEqual([
      '2b7e1516',
      '28aed2a6',
      'abf71588',
      '09cf4f3c',
    ])
    expect(keyWordTrace(A1, 0).rule).toBe('original')
    expect(keyWordTrace(A1, 3).rule).toBe('original')
  })

  it('w4 的 g 三步逐步对得上', () => {
    const trace = keyWordTrace(A1, 4)
    expect(trace.rule).toBe('g')
    expect(dump(trace.previousWord!)).toBe('09cf4f3c')
    expect(dump(trace.rotated!)).toBe('cf4f3c09')
    expect(dump(trace.substituted!)).toBe('8a84eb01')
    expect(trace.rcon).toEqual([0x01, 0, 0, 0])
    expect(trace.rconIndex).toBe(0)
    expect(dump(trace.baseWord!)).toBe('2b7e1516')
    expect(dump(trace.word)).toBe('a0fafe17')
  })

  it('末字 w43 与第 10 组轮密钥', () => {
    expect(dump(keyWordTrace(A1, 43).word)).toBe('b6630ca6')
    expect(dump(roundKeyBytes(A1, 10))).toBe('d014f9a8c9ee2589e13f0cc8b6630ca6')
  })

  it('44 个字的推导全部自洽（校验失败会抛错）', () => {
    expect(() => A1.forEach((_, i) => keyWordTrace(A1, i))).not.toThrow()
  })
})

describe('keyWordTrace · 设计稿表格用的 000102…0f', () => {
  it('w4 = d6 aa 74 fd', () => {
    expect(dump(keyWordTrace(SEQ, 4).substituted!)).toBe('d7ab76fe')
    expect(dump(keyWordTrace(SEQ, 4).word)).toBe('d6aa74fd')
  })
})

describe('keyWordTrace · 其他位数', () => {
  it('AES-192：52 字，w6 起才算出来，w6 = fe0c91f7', () => {
    const words = wordsOf('8e73b0f7da0e6452c810f32b809079e562f8ead2522c6b7b')
    expect(words).toHaveLength(52)
    expect(keyWordTrace(words, 5).rule).toBe('original')
    expect(keyWordTrace(words, 6).rule).toBe('g')
    expect(dump(keyWordTrace(words, 6).word)).toBe('fe0c91f7')
  })

  it('AES-256：60 字，i%8==4 只做 SubWord（不旋转、不加 Rcon）', () => {
    const words = wordsOf(
      '603deb1015ca71be2b73aef0857d77811f352c073b6108d72d9810a30914dff4',
    )
    expect(words).toHaveLength(60)
    const sub = keyWordTrace(words, 12)
    expect(sub.rule).toBe('subword')
    expect(sub.rotated).toBeNull()
    expect(sub.rcon).toBeNull()

    // 不经 keyExpansion，独立验算一遍：sub = SubWord(w11)，w12 = w4 ⊕ sub
    const substituted = Array.from(sub.substituted!)
    const expectWord = sub.baseWord!.map((byte, k) => byte ^ substituted[k]!)
    expect(dump(sub.word)).toBe(dump(expectWord))
  })
})

describe('keyWordTrace · 数据不一致时拒绝显示', () => {
  it('篡改一个字，推导校验直接抛错', () => {
    const words = A1.map((word) => [...word])
    words[4] = [0, 0, 0, 0]
    expect(() => keyWordTrace(words, 4)).toThrow(/derivation mismatch/)
  })
})
