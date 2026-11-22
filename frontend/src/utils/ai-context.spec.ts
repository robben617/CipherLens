import { describe, expect, it } from 'vitest'
import {
  contextFingerprint,
  describeContext,
  hasAvalancheResult,
  hasSboxContext,
  normalizeQuestion,
  toWireContext,
} from './ai-context'


describe('toWireContext', () => {
  it('keeps only the sbox whitelist and never leaks plaintext/key', () => {
    const context = toWireContext('sbox', {
      mode: 'forward',
      input: 0x53,
      output: 0xed,
      selected_hex: '0x53',
      plaintext_hex: '3243f6a8885a308d313198a2e0370734',
      key_hex: '2b7e151628aed2a6abf7158809cf4f3c',
      input_byte_before: 0x53,
      trace: { steps: new Array(40) },
    })
    expect(context).toEqual({
      page: 'sbox',
      mode: 'forward',
      input: 0x53,
      output: 0xed,
      selected_hex: '0x53',
    })
    expect(JSON.stringify(context)).not.toContain('3243f6')
    expect(JSON.stringify(context)).not.toContain('2b7e15')
  })

  it('requires sbox input/output as a pair and drops invalid or out-of-range values', () => {
    expect(toWireContext('sbox', { mode: 'forward', input: 0x53 })).toEqual({
      page: 'sbox',
      mode: 'forward',
    })
    expect(
      toWireContext('sbox', { input: 0x53, output: 0x1ff, selected_hex: '53' }),
    ).toEqual({ page: 'sbox' })
  })

  it('keeps avalanche location and result numbers without secrets', () => {
    expect(
      toWireContext('avalanche', {
        target: 'plaintext',
        byte_index: 0,
        bit_index: 7,
        key_bits: 128,
        changed_bits: 62,
        total_bits: 128,
        rate: 0.484375,
        sweep_mean: 63.5,
        plaintext_hex: '3243f6a8885a308d313198a2e0370734',
        key_hex: '2b7e151628aed2a6abf7158809cf4f3c',
      }),
    ).toEqual({
      page: 'avalanche',
      target: 'plaintext',
      byte_index: 0,
      bit_index: 7,
      key_bits: 128,
      changed_bits: 62,
      total_bits: 128,
      rate: 0.484375,
      sweep_mean: 63.5,
    })
  })

  it('drops invalid avalanche fields and keeps position-only context', () => {
    expect(
      toWireContext('avalanche', {
        target: 'plaintext',
        byte_index: 32,
        bit_index: 8,
        key_bits: 192,
        changed_bits: 300,
      }),
    ).toEqual({ page: 'avalanche', target: 'plaintext', key_bits: 192 })
  })

  it('returns null for workbench and only page for home', () => {
    expect(toWireContext('workbench', { traceId: 't_1' })).toBeNull()
    expect(toWireContext('home', { question: 'x' })).toEqual({ page: 'home' })
  })
})

describe('context helpers', () => {
  it('detects paired sbox context and avalanche result', () => {
    expect(hasSboxContext(toWireContext('sbox', { input: 1, output: 2 }))).toBe(true)
    expect(hasSboxContext(toWireContext('sbox', { input: 1 }))).toBe(false)
    expect(
      hasAvalancheResult(
        toWireContext('avalanche', {
          target: 'key',
          byte_index: 1,
          bit_index: 0,
          key_bits: 128,
          changed_bits: 62,
          total_bits: 128,
          rate: 0.484375,
        }),
      ),
    ).toBe(true)
    expect(
      hasAvalancheResult(
        toWireContext('avalanche', {
          target: 'key',
          byte_index: 1,
          bit_index: 0,
          key_bits: 128,
        }),
      ),
    ).toBe(false)
  })

  it('describes context without inventing values', () => {
    expect(describeContext('home', { page: 'home' })).toContain('通用讲解')
    expect(
      describeContext(
        'sbox',
        toWireContext('sbox', { mode: 'forward', input: 0x53, output: 0xed }),
      ),
    ).toContain('0x53')
    expect(
      describeContext(
        'avalanche',
        toWireContext('avalanche', { target: 'plaintext', byte_index: 0 }),
      ),
    ).toContain('先跑一次实验')
  })
})

describe('normalizeQuestion / contextFingerprint', () => {
  it('NFKC-normalizes, trims and collapses whitespace without changing case', () => {
    expect(normalizeQuestion('  ＡＥＳ\t 是什么？\n\n')).toBe('AES 是什么?')
    expect(normalizeQuestion('  Why   AES?  ')).toBe('Why AES?')
  })

  it('is stable for equal context and question regardless of object key order', async () => {
    const contextA = toWireContext('sbox', {
      mode: 'forward',
      input: 0x53,
      output: 0xed,
      selected_hex: '0x53',
    })
    const contextB = toWireContext('sbox', {
      selected_hex: '0x53',
      output: 0xed,
      input: 0x53,
      mode: 'forward',
    })
    const a = await contextFingerprint('sbox', contextA, '为什么是 ED？')
    const b = await contextFingerprint('sbox', contextB, ' 为什么是 ED？ ')
    expect(a).toBe(b)
    expect(a).toMatch(/^[0-9a-f]{16}$/)
  })

  it('differs by page, context value and question', async () => {
    const sbox = toWireContext('sbox', { input: 0x53, output: 0xed })
    const base = await contextFingerprint('sbox', sbox, '为什么？')
    const otherPage = await contextFingerprint(
      'avalanche',
      toWireContext('avalanche', { target: 'plaintext' }),
      '为什么？',
    )
    const otherValue = await contextFingerprint(
      'sbox',
      toWireContext('sbox', { input: 0x54, output: 0xed }),
      '为什么？',
    )
    const otherQuestion = await contextFingerprint('sbox', sbox, '为什么是 ED？')
    expect(new Set([base, otherPage, otherValue, otherQuestion]).size).toBe(4)
  })
})