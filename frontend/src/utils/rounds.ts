// 轮次分段：控制条进度条与时间轴轮次带共用同一套分段结果，
// 避免两处各算一遍导致刻度错位（F05 验收第 6 条：对齐误差 ≤ 1px）。

import type { TraceDirection, TraceStep } from '../engine/trace'

export interface RoundSegment {
  readonly round: number
  /** 该轮包含的步数 */
  readonly span: number
  /** 该轮在整条 trace 中的起始步（含），0 表示初始轮密钥加 */
  readonly start: number
  /** 该轮的显示名：初始轮用「初」，解密收尾那组用「终」，其余直接给轮号 */
  readonly label: string
}

/**
 * 轮次分段：控制条进度条与时间轴轮次带共用同一套分段结果，
 * 避免两处各算一遍导致刻度错位（F05 验收第 6 条：对齐误差 ≤ 1px）。
 *
 * 解密时轮次是 10 → 0 递减的，第 0 组是「收尾轮密钥加」，不能标成「初」。
 */
export function roundSegments(
  steps: readonly TraceStep[],
  direction: TraceDirection = 'encrypt',
): RoundSegment[] {
  const list: RoundSegment[] = []
  let cursor = 0

  for (const step of steps) {
    const last = list[list.length - 1]
    if (last && last.round === step.round) {
      list[list.length - 1] = { ...last, span: last.span + 1 }
    } else {
      list.push({
        round: step.round,
        span: 1,
        start: cursor,
        label:
          step.round === 0
            ? direction === 'decrypt'
              ? '终'
              : '初'
            : String(step.round),
      })
    }
    cursor += 1
  }

  return list
}

/** 轮次边界在 [0,1] 上的位置，用于进度条分段线 */
export function roundBoundaries(segments: readonly RoundSegment[], total: number): number[] {
  if (total <= 0) return []
  const out: number[] = []
  let acc = 0
  for (const segment of segments) {
    acc += segment.span
    if (acc < total) out.push(acc / total)
  }
  return out
}
