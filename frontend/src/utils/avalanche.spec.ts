import { describe, expect, it } from 'vitest'
import { barHeight, bitColumns, diffLevel, percentOf } from './avalanche'

describe('diffLevel', () => {
  it('keeps 0 as 0 so unchanged cells stay untouched', () => {
    expect(diffLevel(0)).toBe(0)
  })

  it('covers 1–8 bits in four buckets without gaps', () => {
    expect([1, 2].map(diffLevel)).toEqual([1, 1])
    expect([3, 4].map(diffLevel)).toEqual([2, 2])
    expect([5, 6].map(diffLevel)).toEqual([3, 3])
    expect([7, 8].map(diffLevel)).toEqual([4, 4])
  })

  it('is monotonic — a byte never looks lighter after changing more bits', () => {
    const levels = Array.from({ length: 9 }, (_, bits) => diffLevel(bits))
    expect(levels).toEqual([...levels].sort((a, b) => a - b))
  })
})

describe('percentOf', () => {
  it('rounds to whole percent instead of faking precision', () => {
    expect(percentOf(0.4844)).toBe(48)
    expect(percentOf(0.5)).toBe(50)
    expect(percentOf(0)).toBe(0)
  })
})

describe('barHeight', () => {
  it('normalises against the block size', () => {
    expect(barHeight(64, 128)).toBe(50)
    expect(barHeight(62, 128)).toBe(48)
  })

  it('never returns zero height for a visible bar', () => {
    expect(barHeight(0, 128)).toBe(4)
  })

  it('survives a zero total instead of dividing by zero', () => {
    expect(barHeight(12, 0)).toBe(0)
  })
})

describe('bitColumns', () => {
  const flags = Array.from({ length: 128 }, (_, index) => index < 5)

  it('splits 128 bits into 16 columns of 8', () => {
    const columns = bitColumns(flags)
    expect(columns).toHaveLength(16)
    expect(columns.every((column) => column.length === 8)).toBe(true)
  })

  it('keeps the hex order: byte 0 first, and no bit lost', () => {
    const columns = bitColumns(flags)
    expect(columns[0]!.filter(Boolean)).toHaveLength(5)
    expect(columns.slice(1).flat().some(Boolean)).toBe(false)
    expect(columns.flat()).toEqual(flags)
  })

  it('returns empty columns for missing data instead of throwing', () => {
    expect(bitColumns([]).every((column) => column.length === 0)).toBe(true)
  })
})
