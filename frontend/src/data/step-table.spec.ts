import { describe, expect, it } from 'vitest'
import { STEP_TABLE } from './step-table'
import { OP_LABEL } from './glossary'

describe('STEP_TABLE · 40 步对照表', () => {
  it('正好 40 步，编号从 1 连续到 40', () => {
    expect(STEP_TABLE).toHaveLength(40)
    expect(STEP_TABLE.map((row) => row.no)).toEqual(
      Array.from({ length: 40 }, (_, index) => index + 1),
    )
  })

  it('第 1 步是加密前的轮密钥加（轮号 0）', () => {
    expect(STEP_TABLE[0]).toMatchObject({ no: 1, round: 0, label: OP_LABEL['add_round_key'] })
  })

  it('1–9 轮每轮四步，顺序是 代换 → 移位 → 混合 → 轮密钥加', () => {
    for (let round = 1; round <= 9; round += 1) {
      const rows = STEP_TABLE.filter((row) => row.round === round)
      expect(rows.map((row) => row.label)).toEqual([
        OP_LABEL['sub_bytes'],
        OP_LABEL['shift_rows'],
        OP_LABEL['mix_columns'],
        OP_LABEL['add_round_key'],
      ])
    }
  })

  it('末轮只有 3 步，且没有列混合', () => {
    const last = STEP_TABLE.filter((row) => row.round === 10)
    expect(last.map((row) => row.label)).toEqual([
      OP_LABEL['sub_bytes'],
      OP_LABEL['shift_rows'],
      OP_LABEL['add_round_key'],
    ])
    expect(last.map((row) => row.no)).toEqual([38, 39, 40])
  })

  it('每一步都有说明，且不残留内部的 op 名（如 sub_bytes）', () => {
    for (const row of STEP_TABLE) {
      expect(row.what.length).toBeGreaterThan(0)
      expect(row.label).not.toMatch(/[a-z_]{3,}/)
    }
  })
})
