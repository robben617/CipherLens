// 4×4 矩阵的 roving tabindex。
// AES 索引仍为列优先 index = col * 4 + row；DOM 按行轨道组织，通过 data-index 查找。
// 方向键语义按视觉方向：上/下改 row（±1），左/右改 col（±4）。
// 到边界不环绕、不跨行；移动焦点不滚动页面；不改变选中态。

import { ref, type Ref } from 'vue'

export interface RovingGrid {
  activeIndex: Ref<number>
  focusIndex(index: number): void
  onKeydown(event: KeyboardEvent): void
}

export function useRovingGrid(getGrid: () => HTMLElement | null): RovingGrid {
  const activeIndex = ref(0)

  function focusIndex(index: number): void {
    if (index < 0 || index > 15) return
    const cell = getGrid()?.querySelector<HTMLElement>(`[data-index="${index}"]`)
    if (!cell) return
    activeIndex.value = index
    cell.focus({ preventScroll: true })
  }

  function onKeydown(event: KeyboardEvent): void {
    const index = activeIndex.value
    const row = index % 4
    const col = Math.floor(index / 4)
    let next = index

    switch (event.key) {
      case 'ArrowUp':
        event.preventDefault()
        if (row > 0) next = index - 1
        break
      case 'ArrowDown':
        event.preventDefault()
        if (row < 3) next = index + 1
        break
      case 'ArrowLeft':
        event.preventDefault()
        if (col > 0) next = index - 4
        break
      case 'ArrowRight':
        event.preventDefault()
        if (col < 3) next = index + 4
        break
      default:
        return
    }

    if (next !== index) focusIndex(next)
  }

  return { activeIndex, focusIndex, onKeydown }
}