import { describe, expect, it } from 'vitest'
import { promptsFor } from './ai-prompts'

describe('promptsFor', () => {
  it('returns three prompts for every non-workbench page', () => {
    expect(promptsFor('home', { page: 'home' })).toHaveLength(3)
    expect(promptsFor('sbox', { page: 'sbox' })).toHaveLength(3)
    expect(promptsFor('avalanche', { page: 'avalanche' })).toHaveLength(3)
    expect(promptsFor('workbench', null)).toEqual([])
  })

  it('uses the selected S-box pair in the first prompt', () => {
    const prompts = promptsFor('sbox', {
      page: 'sbox',
      mode: 'forward',
      input: 0x53,
      output: 0xed,
    })
    expect(prompts[0]).toBe('0x53 为什么查表得到 0xED？')
    expect(prompts.join(' ')).not.toContain('plaintext')
  })

  it('falls back to no-selection prompts without context', () => {
    const prompts = promptsFor('sbox', { page: 'sbox' })
    expect(prompts[0]).toContain('先在网格里选中一个字节')
  })

  it('uses total_bits for the avalanche half prompt and no-result hint', () => {
    const withResult = promptsFor('avalanche', {
      page: 'avalanche',
      target: 'plaintext',
      byte_index: 0,
      bit_index: 7,
      key_bits: 128,
      changed_bits: 62,
      total_bits: 128,
      rate: 0.484375,
    })
    expect(withResult[1]).toContain('64 位')

    const noResult = promptsFor('avalanche', {
      page: 'avalanche',
      target: 'plaintext',
      byte_index: 0,
    })
    expect(noResult[0]).toContain('先跑一次实验')
  })
})