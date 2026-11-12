// 40 步对照表的数据源（速查卡用）。
// 编号必须与后端 trace 的 step.index + 1、工作台「第 N 步」完全一致：
//   1 步初始轮密钥加 → 9 轮 × 4 步 → 末轮 3 步（没有列混合）= 40。
// 这里只描述「第几步做什么」，不存任何状态值——值一律来自引擎。

import { OP_LABEL } from './glossary'

export interface StepRow {
  /** 1 起算，与界面右下角播报的步号同源 */
  readonly no: number
  /** 0 是加密前的轮密钥加，1–10 是轮号 */
  readonly round: number
  /** 中文变换名，取自 glossary 的单一来源 */
  readonly label: string
  /** 一句话说明，速查卡第四列 */
  readonly what: string
}

const WHAT: Readonly<Record<string, string>> = {
  add_round_key: '16 个字节与本轮密钥异或',
  sub_bytes: '16 个字节各查一次 S 盒',
  shift_rows: '行 1/2/3 分别左移 1/2/3 格',
  mix_columns: '每列乘固定矩阵（末轮没有）',
}

export const STEP_TABLE: readonly StepRow[] = (() => {
  const rows: StepRow[] = []
  let index = 0

  const push = (round: number, op: string): void => {
    index += 1
    rows.push({ no: index, round, label: OP_LABEL[op] ?? op, what: WHAT[op] ?? '' })
  }

  push(0, 'add_round_key')
  for (let round = 1; round <= 9; round += 1) {
    for (const op of ['sub_bytes', 'shift_rows', 'mix_columns', 'add_round_key']) {
      push(round, op)
    }
  }
  for (const op of ['sub_bytes', 'shift_rows', 'add_round_key']) {
    push(10, op)
  }

  return rows
})()
