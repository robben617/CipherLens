import { describe, expect, it } from 'vitest'
import {
  RCON,
  addRoundKey,
  invMixColumns,
  invShiftRows,
  keyExpansion,
  mixColumns,
  shiftRows,
} from './aes'

const hex = (bytes: Uint8Array): string =>
  Array.from(bytes, (byte) => byte.toString(16).padStart(2, '0')).join('')

describe('AES key expansion', () => {
  it('matches the FIPS-197 Appendix B AES-128 words', () => {
    const key = Uint8Array.from([
      0x2b, 0x7e, 0x15, 0x16, 0x28, 0xae, 0xd2, 0xa6,
      0xab, 0xf7, 0x15, 0x88, 0x09, 0xcf, 0x4f, 0x3c,
    ])
    const words = keyExpansion(key)

    expect(words.length).toBe(44)
    expect(hex(words[0]!)).toBe('2b7e1516')
    expect(hex(words[1]!)).toBe('28aed2a6')
    expect(hex(words[2]!)).toBe('abf71588')
    expect(hex(words[3]!)).toBe('09cf4f3c')
    expect(hex(words[4]!)).toBe('a0fafe17')
    expect(hex(words[5]!)).toBe('88542cb1')
    expect(hex(words[6]!)).toBe('23a33939')
    expect(hex(words[7]!)).toBe('2a6c7605')
  })

  it('produces 44 / 52 / 60 words for 128 / 192 / 256-bit keys', () => {
    expect(keyExpansion(new Uint8Array(16)).length).toBe(44)
    expect(keyExpansion(new Uint8Array(24)).length).toBe(52)
    expect(keyExpansion(new Uint8Array(32)).length).toBe(60)
  })

  it('keeps the Rcon table at ten entries', () => {
    expect(Array.from(RCON)).toEqual([
      0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36,
    ])
  })

  it('rejects invalid key lengths', () => {
    expect(() => keyExpansion(new Uint8Array(15))).toThrow()
    expect(() => keyExpansion(new Uint8Array(20))).toThrow()
  })
})

describe('AddRoundKey', () => {
  it('XORs state and round key byte by byte', () => {
    const state = Uint8Array.from({ length: 16 }, (_, i) => i)
    const roundKey = Uint8Array.from({ length: 16 }, () => 0xff)
    const result = addRoundKey(state, roundKey)
    expect(result).toEqual(Uint8Array.from({ length: 16 }, (_, i) => i ^ 0xff))
  })

  it('returns a new array and leaves both inputs untouched', () => {
    const state = Uint8Array.from([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])
    const roundKey = Uint8Array.from({ length: 16 }, (_, i) => i)
    const stateSnapshot = state.slice()
    const keySnapshot = roundKey.slice()
    const result = addRoundKey(state, roundKey)

    expect(result).not.toBe(state)
    expect(state).toEqual(stateSnapshot)
    expect(roundKey).toEqual(keySnapshot)
  })
})

describe('ShiftRows', () => {
  it('shifts row r left by r positions on a column-major state', () => {
    const state = Uint8Array.from({ length: 16 }, (_, i) => i)
    const shifted = shiftRows(state)

    // 输入列优先：第 0 列 0,1,2,3；第 1 列 4,5,6,7；第 2 列 8,9,10,11；第 3 列 12,13,14,15
    // row 0 不动；row 1 左移 1；row 2 左移 2；row 3 左移 3。
    expect(Array.from(shifted)).toEqual([
      0, 5, 10, 15,
      4, 9, 14, 3,
      8, 13, 2, 7,
      12, 1, 6, 11,
    ])
  })

  it('is reversed by invShiftRows', () => {
    const state = Uint8Array.from({ length: 16 }, (_, i) => i * 7)
    expect(invShiftRows(shiftRows(state))).toEqual(state)
  })
})

describe('MixColumns', () => {
  it('matches the FIPS-197 column example', () => {
    const state = new Uint8Array(16)
    state.set([0xdb, 0x13, 0x53, 0x45], 0)
    const mixed = mixColumns(state)
    expect(Array.from(mixed.subarray(0, 4))).toEqual([0x8e, 0x4d, 0xa1, 0xbc])
  })

  it('is reversed by invMixColumns', () => {
    const state = Uint8Array.from([
      0x00, 0x11, 0x22, 0x33,
      0x44, 0x55, 0x66, 0x77,
      0x88, 0x99, 0xaa, 0xbb,
      0xcc, 0xdd, 0xee, 0xff,
    ])
    const snapshot = state.slice()
    expect(invMixColumns(mixColumns(state))).toEqual(state)
    expect(state).toEqual(snapshot)
  })

  it('returns a new array and leaves the input untouched', () => {
    const state = Uint8Array.from({ length: 16 }, (_, i) => i)
    const snapshot = state.slice()
    const mixed = mixColumns(state)
    expect(mixed).not.toBe(state)
    expect(state).toEqual(snapshot)
  })
})