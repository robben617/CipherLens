import { describe, expect, it } from 'vitest'
import { buildTrace } from '../engine/trace'
import { FIPS_197_VECTORS } from '../engine/vectors'
import { roundBoundaries, roundSegments, roundSummaryAt } from './rounds'

const VECTOR = FIPS_197_VECTORS[0]!

function encryptTrace() {
  return buildTrace({ plaintext: VECTOR.plaintext_hex, key: VECTOR.key_hex })
}

function decryptTrace() {
  return buildTrace({
    plaintext: VECTOR.ciphertext_hex,
    key: VECTOR.key_hex,
    mode: 'decrypt',
  })
}

describe('roundSegments', () => {
  it('labels encryption rounds 初, 1 … 10', () => {
    const segments = roundSegments(encryptTrace().steps)
    expect(segments.map((segment) => segment.label)).toEqual([
      '初',
      '1',
      '2',
      '3',
      '4',
      '5',
      '6',
      '7',
      '8',
      '9',
      '10',
    ])
    expect(segments.reduce((sum, segment) => sum + segment.span, 0)).toBe(40)
  })

  it('labels decryption rounds 10 → 1 then 终 (no 初)', () => {
    const segments = roundSegments(decryptTrace().steps, 'decrypt')
    expect(segments.map((segment) => segment.label)).toEqual([
      '10',
      '9',
      '8',
      '7',
      '6',
      '5',
      '4',
      '3',
      '2',
      '1',
      '终',
    ])
    expect(segments.reduce((sum, segment) => sum + segment.span, 0)).toBe(40)
    // 第 0 组是收尾轮密钥加，只有 3 步（逆列混合在加密的末轮不存在）
    expect(segments[segments.length - 1]!.span).toBe(3)
  })

  it('puts boundaries strictly inside (0, 1) and keeps them ascending', () => {
    const segments = roundSegments(encryptTrace().steps)
    const boundaries = roundBoundaries(segments, 40)
    expect(boundaries).toHaveLength(10)
    expect(boundaries[0]).toBeGreaterThan(0)
    expect(boundaries[boundaries.length - 1]).toBeLessThan(1)
    expect([...boundaries].sort((a, b) => a - b)).toEqual(boundaries)
  })
})

describe('roundSummaryAt', () => {
  it('fires only on the last step of a complete 4-step round (encrypt)', () => {
    const steps = encryptTrace().steps
    // 第 1 步是初始轮密钥加（单独 1 步）：循环还没开始，不该讲「下一轮」
    expect(roundSummaryAt(steps, 1)).toBeNull()
    // 第 1 轮四步 = 第 2~5 步，走到第 4 步还没完
    expect(roundSummaryAt(steps, 4)).toBeNull()
    expect(roundSummaryAt(steps, 5)).toEqual({ round: 1 })
    expect(roundSummaryAt(steps, 9)).toEqual({ round: 2 })
    // 第 40 步是最后一轮（只有 3 步，没有列混合）的收尾：整条链路走完，
    // 不是「还有下一轮」，交给末步结论
    expect(roundSummaryAt(steps, 40)).toBeNull()
  })

  it('gives 9 summaries for a 128-bit key, rounds 1→9', () => {
    const steps = encryptTrace().steps
    const rounds = steps
      .map((_, index) => roundSummaryAt(steps, index + 1))
      .flatMap((hit) => (hit ? [hit.round] : []))
    expect(rounds).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9])
  })

  it('works the same on decryption, walking rounds 9→1', () => {
    const steps = decryptTrace().steps
    const rounds = steps
      .map((_, index) => roundSummaryAt(steps, index + 1))
      .flatMap((hit) => (hit ? [hit.round] : []))
    expect(rounds).toEqual([9, 8, 7, 6, 5, 4, 3, 2, 1])
    // 解密首步是「轮密钥加（第 10 轮密钥）」单独一步，末步是收尾轮密钥加
    expect(roundSummaryAt(steps, 1)).toBeNull()
    expect(roundSummaryAt(steps, 40)).toBeNull()
  })

  it('scales to 192/256-bit keys (11 / 13 summaries)', () => {
    const [, c2, c3] = FIPS_197_VECTORS
    const count = (vector: NonNullable<typeof c2>): number => {
      const steps = buildTrace({
        plaintext: vector.plaintext_hex,
        key: vector.key_hex,
      }).steps
      return steps.filter((_, index) => roundSummaryAt(steps, index + 1) !== null).length
    }
    expect(count(c2!)).toBe(11)
    expect(count(c3!)).toBe(13)
  })

  it('returns null at step 0 and on an empty trace', () => {
    expect(roundSummaryAt(encryptTrace().steps, 0)).toBeNull()
    expect(roundSummaryAt([], 3)).toBeNull()
  })
})
