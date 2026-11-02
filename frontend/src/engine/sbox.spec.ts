import { describe, expect, it } from 'vitest'
import { INV_SBOX, SBOX, invSubBytes, subBytes } from './sbox'

// 独立的数学参考实现：GF(2^8) 乘法逆 + FIPS-197 §5.1.1 仿射变换。
// 它与产品代码里的手写表来自不同来源，用来交叉验证 256 项。
function xtime(value: number): number {
  return ((value << 1) ^ (value & 0x80 ? 0x1b : 0)) & 0xff
}

function multiply(a: number, b: number): number {
  let product = 0
  let left = a
  let right = b
  while (right > 0) {
    if (right & 1) product ^= left
    left = xtime(left)
    right >>= 1
  }
  return product & 0xff
}

function inverseOf(value: number): number {
  if (value === 0) return 0
  for (let candidate = 1; candidate < 256; candidate++) {
    if (multiply(value, candidate) === 1) return candidate
  }
  return 0
}

function affine(value: number): number {
  let result = 0x63
  for (let bit = 0; bit < 8; bit++) {
    const rotated =
      ((value >> bit) & 1) ^
      ((value >> ((bit + 4) % 8)) & 1) ^
      ((value >> ((bit + 5) % 8)) & 1) ^
      ((value >> ((bit + 6) % 8)) & 1) ^
      ((value >> ((bit + 7) % 8)) & 1)
    if (rotated) result ^= 1 << bit
  }
  return result
}

function referenceSBox(value: number): number {
  return affine(inverseOf(value))
}

describe('AES S-box', () => {
  it('matches the FIPS-197 anchors', () => {
    expect(SBOX[0x00]).toBe(0x63)
    expect(SBOX[0x53]).toBe(0xed)
    expect(INV_SBOX[0x63]).toBe(0x00)
  })

  it('matches the mathematical definition for all 256 entries', () => {
    for (let value = 0; value < 256; value++) {
      expect(SBOX[value], `SBOX[0x${value.toString(16)}]`).toBe(referenceSBox(value))
    }
  })

  it('keeps S-box and inverse S-box mutually inverse', () => {
    for (let value = 0; value < 256; value++) {
      expect(INV_SBOX[SBOX[value]!], `INV_SBOX[SBOX[0x${value.toString(16)}]]`).toBe(value)
    }
  })

  it('subBytes returns a new array and leaves the input untouched', () => {
    const input = Uint8Array.from([0x00, 0x01, 0x53, 0xff])
    const snapshot = input.slice()
    const output = subBytes(input)

    expect(output).not.toBe(input)
    expect(input).toEqual(snapshot)
    expect(Array.from(output)).toEqual([0x63, 0x7c, 0xed, 0x16])
  })

  it('invSubBytes reverses subBytes', () => {
    const input = Uint8Array.from([0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77])
    expect(invSubBytes(subBytes(input))).toEqual(input)
  })
})