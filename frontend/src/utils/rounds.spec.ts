import { describe, expect, it } from 'vitest'
import { buildTrace } from '../engine/trace'
import { FIPS_197_VECTORS } from '../engine/vectors'
import { roundBoundaries, roundSegments } from './rounds'

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
