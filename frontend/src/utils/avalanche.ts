/**
 * 雪崩实验的纯计算。抽出来是为了能测：位图分列、色阶、百分比都是
 * 「错一位就整页读错」的东西，不该只靠肉眼截图确认。
 */

/** 差异强度分四档：0 = 没变，1 = 1–2 位，4 = 7–8 位。只表达强度，不表达对错。 */
export function diffLevel(bits: number): 0 | 1 | 2 | 3 | 4 {
  if (bits <= 0) return 0
  if (bits <= 2) return 1
  if (bits <= 4) return 2
  if (bits <= 6) return 3
  return 4
}

/** 0.4844 → 48。四舍五入到整百分点，避免出现「48.44%」这种假精度。 */
export function percentOf(rate: number): number {
  return Math.round(rate * 100)
}

/** 柱高百分比。最小 4% 是留白下限：变了 0 位时也得留一条能看见的基线。 */
export function barHeight(bits: number, total: number): number {
  if (total <= 0) return 0
  return Math.max(4, Math.round((bits / total) * 100))
}

/**
 * 128 个位标志 → 16 列 × 8 行。
 * 一列对应一个字节，列内从上到下是 bit7 → bit0，正好对上这个字节的两位十六进制数。
 */
export function bitColumns(flags: readonly boolean[]): boolean[][] {
  return Array.from({ length: 16 }, (_, index) => flags.slice(index * 8, index * 8 + 8))
}
