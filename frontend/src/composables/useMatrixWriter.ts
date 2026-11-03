// 16 个实格 + 16 个鬼格的唯一写值通道：一个 rAF 内批量写 DOM。
// DOM 按行轨道组织（行优先）；AES 值仍按列优先 index = col * 4 + row 映射。
// 鬼格复制同一行的值，供 ShiftRows 回绕使用。
// 本轮只写静态值；滚动替换与状态通道留给后续功能点。

import { onScopeDispose } from 'vue'

const HEX = Array.from({ length: 256 }, (_, value) =>
  value.toString(16).toUpperCase().padStart(2, '0'),
)

export interface MatrixWriter {
  write(values: Uint8Array): void
}

export function useMatrixWriter(getGrid: () => HTMLElement | null): MatrixWriter {
  let realRoots: HTMLElement[] = []
  let realCur: HTMLElement[] = []
  let realNext: HTMLElement[] = []
  let ghostRoots: HTMLElement[] = []
  let ghostCur: HTMLElement[] = []
  let ghostNext: HTMLElement[] = []
  let rafId = 0
  let batches = 0
  const pending = new Uint8Array(16)

  function ensure(): void {
    if (
      realRoots.length === 16 &&
      realRoots.every((root) => root.isConnected) &&
      ghostRoots.length === 16 &&
      ghostRoots.every((root) => root.isConnected)
    ) {
      return
    }

    const grid = getGrid()
    realRoots = grid
      ? Array.from(grid.querySelectorAll<HTMLElement>('.c-byte:not([data-ghost="true"])'))
      : []
    ghostRoots = grid
      ? Array.from(grid.querySelectorAll<HTMLElement>('.c-byte[data-ghost="true"]'))
      : []

    const values = (roots: HTMLElement[], selector: string): HTMLElement[] =>
      roots.map((root) => root.querySelector<HTMLElement>(selector)!)
    realCur = values(realRoots, '.c-byte__val.is-current')
    realNext = values(realRoots, '.c-byte__val.is-incoming')
    ghostCur = values(ghostRoots, '.c-byte__val.is-current')
    ghostNext = values(ghostRoots, '.c-byte__val.is-incoming')
  }

  function flush(): void {
    rafId = 0
    ensure()

    for (let i = 0; i < 16; i++) {
      const row = i % 4
      const col = Math.floor(i / 4)
      const position = row * 4 + col
      const value = pending[i]!
      const hex = HEX[value]!

      const realRoot = realRoots[position]
      const current = realCur[position]
      const incoming = realNext[position]
      if (realRoot && current && incoming) {
        current.textContent = hex
        incoming.textContent = hex

        const aria = `第 ${row + 1} 行第 ${col + 1} 列，字节 ${i}，值 0x${hex}，十进制 ${value}`
        if (realRoot.getAttribute('aria-label') !== aria) {
          realRoot.setAttribute('aria-label', aria)
        }
      }

      const ghostCurNode = ghostCur[position]
      const ghostNextNode = ghostNext[position]
      if (ghostCurNode && ghostNextNode) {
        ghostCurNode.textContent = hex
        ghostNextNode.textContent = hex
      }
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