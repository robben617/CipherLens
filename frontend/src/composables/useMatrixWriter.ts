// 16 个字节格的唯一写值通道：一个 rAF 内批量写 DOM。
// 值节点在 ensure() 中按列优先顺序缓存，DOM 下标 === AES 字节下标。
// 本轮只写静态值；滚动替换与状态通道留给后续功能点。

import { onScopeDispose } from 'vue'

const HEX = Array.from({ length: 256 }, (_, value) =>
  value.toString(16).toUpperCase().padStart(2, '0'),
)

export interface MatrixWriter {
  write(values: Uint8Array): void
}

export function useMatrixWriter(getGrid: () => HTMLElement | null): MatrixWriter {
  let roots: HTMLElement[] = []
  let curVals: HTMLElement[] = []
  let nextVals: HTMLElement[] = []
  let rafId = 0
  let batches = 0
  const pending = new Uint8Array(16)

  function ensure(): void {
    if (roots.length === 16 && roots.every((root) => root.isConnected)) return

    const grid = getGrid()
    roots = grid ? Array.from(grid.querySelectorAll<HTMLElement>('.c-byte')) : []
    curVals = roots.map(
      (root) => root.querySelector<HTMLElement>('.c-byte__val.is-current')!,
    )
    nextVals = roots.map(
      (root) => root.querySelector<HTMLElement>('.c-byte__val.is-incoming')!,
    )
  }

  function flush(): void {
    rafId = 0
    ensure()

    for (let i = 0; i < 16; i++) {
      const root = roots[i]
      const current = curVals[i]
      const incoming = nextVals[i]
      if (!root || !current || !incoming) continue

      const value = pending[i]!
      const hex = HEX[value]!
      current.textContent = hex
      incoming.textContent = hex

      const row = i % 4
      const col = Math.floor(i / 4)
      const aria = `第 ${row + 1} 行第 ${col + 1} 列，字节 ${i}，值 0x${hex}，十进制 ${value}`
      if (root.getAttribute('aria-label') !== aria) root.setAttribute('aria-label', aria)
    }

    if (import.meta.env.DEV) {
      const probe = window as Window & { __MATRIX_BATCHES__?: number[] }
      probe.__MATRIX_BATCHES__ ??= []
      probe.__MATRIX_BATCHES__.push(batches)
      if (batches > 1) console.error('[MULTI-BATCH] %d', batches)
    }

    batches = 0
  }

  function write(values: Uint8Array): void {
    if (values.length !== 16) {
      throw new Error(`matrix values must be 16 bytes, got ${values.length}`)
    }
    pending.set(values)
    batches++
    if (!rafId) rafId = requestAnimationFrame(flush)
  }

  onScopeDispose(() => {
    if (rafId) cancelAnimationFrame(rafId)
  })

  return { write }
}