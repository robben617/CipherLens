// 两次 16 字节状态之间的差分。changed / unchanged 都是升序索引。
// engine 层：零 Vue 依赖。

export interface StateDiff {
  readonly changed: number[]
  readonly unchanged: number[]
}

export function diffState(before: Uint8Array, after: Uint8Array): StateDiff {
  if (before.length !== after.length) {
    throw new Error(`state length mismatch: ${before.length} vs ${after.length}`)
  }

  const changed: number[] = []
  const unchanged: number[] = []

  for (let i = 0; i < before.length; i++) {
    if (before[i] === after[i]) unchanged.push(i)
    else changed.push(i)
  }

  return { changed, unchanged }
}