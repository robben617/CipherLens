import { describe, expect, it } from 'vitest'
import { diffState } from './diff'
import { SBOX } from './sbox'
import { buildTrace } from './trace'
import { FIPS_197_VECTORS } from './vectors'

describe('diffState', () => {
  it('returns ascending changed and unchanged indices', () => {
    const before = Uint8Array.from([1, 2, 3, 4])
    const after = Uint8Array.from([1, 9, 3, 8])
    expect(diffState(before, after)).toEqual({ changed: [1, 3], unchanged: [0, 2] })
  })

  it('reports all indices unchanged for equal states', () => {
    const state = Uint8Array.from([0, 1, 2, 3])
    expect(diffState(state, state.slice())).toEqual({
      changed: [],
      unchanged: [0, 1, 2, 3],
    })
  })

  it('rejects length mismatch', () => {
    expect(() => diffState(new Uint8Array(16), new Uint8Array(15))).toThrow()
  })
})

describe('buildTrace', () => {
  it('matches all three FIPS-197 Appendix C vectors', () => {
    for (const vector of FIPS_197_VECTORS) {
      const trace = buildTrace({ plaintext: vector.plaintext_hex, key: vector.key_hex })
      expect(trace.ciphertext, vector.id).toBe(vector.ciphertext_hex)
      expect(trace.key_bits).toBe(vector.key_bits)
      expect(trace.step_count).toBe(4 * trace.rounds)
    }
  })

  it('uses 40 / 48 / 56 steps for 128 / 192 / 256-bit keys', () => {
    for (const vector of FIPS_197_VECTORS) {
      const trace = buildTrace({ plaintext: vector.plaintext_hex, key: vector.key_hex })
      expect(trace.steps.length).toBe(4 * trace.rounds)
      expect(trace.step_count).toBe(trace.steps.length)
    }
    expect(buildTrace({ plaintext: FIPS_197_VECTORS[0]!.plaintext_hex, key: FIPS_197_VECTORS[0]!.key_hex }).steps.length).toBe(40)
    expect(buildTrace({ plaintext: FIPS_197_VECTORS[1]!.plaintext_hex, key: FIPS_197_VECTORS[1]!.key_hex }).steps.length).toBe(48)
    expect(buildTrace({ plaintext: FIPS_197_VECTORS[2]!.plaintext_hex, key: FIPS_197_VECTORS[2]!.key_hex }).steps.length).toBe(56)
  })

  it('follows the real round order and omits MixColumns in the final round', () => {
    const trace = buildTrace({
      plaintext: FIPS_197_VECTORS[0]!.plaintext_hex,
      key: FIPS_197_VECTORS[0]!.key_hex,
    })

    expect(trace.steps[0]!.round).toBe(0)
    expect(trace.steps[0]!.op).toBe('add_round_key')
    expect(trace.steps[1]!.round).toBe(1)
    expect(trace.steps[1]!.op).toBe('sub_bytes')
    expect(trace.steps[2]!.op).toBe('shift_rows')
    expect(trace.steps[3]!.op).toBe('mix_columns')
    expect(trace.steps[4]!.op).toBe('add_round_key')

    const finalRoundOps = trace.steps
      .filter((step) => step.round === trace.rounds)
      .map((step) => step.op)
    expect(finalRoundOps).toEqual(['sub_bytes', 'shift_rows', 'add_round_key'])

    const lastStep = trace.steps[trace.steps.length - 1]!
    expect(lastStep.round).toBe(10)
    expect(lastStep.op).toBe('add_round_key')
  })

  it('computes step 13 changed bytes with diffState and S-box values', () => {
    const trace = buildTrace({
      plaintext: FIPS_197_VECTORS[0]!.plaintext_hex,
      key: FIPS_197_VECTORS[0]!.key_hex,
    })
    const step = trace.steps[13]!

    expect(step.round).toBe(4)
    expect(step.op).toBe('sub_bytes')
    expect(step.changed).toEqual(
      diffState(Uint8Array.from(step.state_before), Uint8Array.from(step.state_after)).changed,
    )
    expect(step.changed.length).toBeGreaterThan(0)
    for (let i = 0; i < 16; i++) {
      expect(step.state_after[i]).toBe(SBOX[step.state_before[i]!])
    }
  })

  it('keeps addRoundKey key metadata and leaves it empty for other operations', () => {
    const trace = buildTrace({
      plaintext: FIPS_197_VECTORS[0]!.plaintext_hex,
      key: FIPS_197_VECTORS[0]!.key_hex,
    })

    const addRoundKeyStep = trace.steps.find((step) => step.op === 'add_round_key')!
    expect(addRoundKeyStep.key_indices).toHaveLength(16)
    expect(addRoundKeyStep.key_words).toHaveLength(4)

    const subBytesStep = trace.steps.find((step) => step.op === 'sub_bytes')!
    expect(subBytesStep.key_indices).toEqual([])
    expect(subBytesStep.key_words).toEqual([])
  })

  it('emits the expanded key schedule as words', () => {
    const trace = buildTrace({
      plaintext: FIPS_197_VECTORS[0]!.plaintext_hex,
      key: FIPS_197_VECTORS[0]!.key_hex,
    })
    expect(trace.key_schedule).toHaveLength(44)
    expect(trace.key_schedule.every((word) => word.length === 4)).toBe(true)
  })

  it('returns the same trace_id for identical input', () => {
    const input = {
      plaintext: FIPS_197_VECTORS[0]!.plaintext_hex,
      key: FIPS_197_VECTORS[0]!.key_hex,
    }
    const first = buildTrace(input)
    const second = buildTrace(input)
    expect(first.trace_id).toBe(second.trace_id)
    expect(first.trace_id.startsWith('t_')).toBe(true)

    const different = buildTrace({
      plaintext: input.plaintext,
      key: FIPS_197_VECTORS[1]!.key_hex,
    })
    expect(different.trace_id).not.toBe(first.trace_id)
  })

  it('is JSON serializable', () => {
    const trace = buildTrace({
      plaintext: FIPS_197_VECTORS[0]!.plaintext_hex,
      key: FIPS_197_VECTORS[0]!.key_hex,
    })
    const parsed = JSON.parse(JSON.stringify(trace)) as typeof trace
    expect(parsed.step_count).toBe(40)
    expect(parsed.steps[13]!.state_before).toEqual(trace.steps[13]!.state_before)
    expect(parsed.ciphertext).toBe('69c4e0d86a7b0430d8cdb78070b4c55a')
  })

  it('rejects invalid input and decrypt mode', () => {
    expect(() => buildTrace({ plaintext: '00', key: FIPS_197_VECTORS[0]!.key_hex })).toThrow()
    expect(() => buildTrace({ plaintext: FIPS_197_VECTORS[0]!.plaintext_hex, key: '00' })).toThrow()
    expect(() =>
      buildTrace({
        plaintext: FIPS_197_VECTORS[0]!.plaintext_hex,
        key: FIPS_197_VECTORS[0]!.key_hex,
        mode: 'decrypt',
      }),
    ).toThrow()
  })
})