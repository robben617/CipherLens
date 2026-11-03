// 工作台键盘骨架：Space / ArrowLeft / ArrowRight / Home / End。
// 输入框、文本域、下拉框、contenteditable 聚焦时全部失效。
// 矩阵内的方向键由 useRovingGrid 先处理并 preventDefault，这里通过
// event.defaultPrevented 让位，避免"矩阵内按右键变成下一步"。

import { onMounted, onScopeDispose } from 'vue'

export interface HotkeyHandlers {
  onPlayPause?: () => void
  onPrev?: () => void
  onNext?: () => void
  onFirst?: () => void
  onLast?: () => void
}

const EDITABLE = 'input, textarea, select, [contenteditable=""], [contenteditable="true"]'

function isEditable(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false
  return target.matches(EDITABLE) || target.isContentEditable
}

export function useHotkeys(handlers: HotkeyHandlers): void {
  function onKeydown(event: KeyboardEvent): void {
    if (event.defaultPrevented) return
    if (isEditable(event.target)) return

    switch (event.key) {
      case ' ':
        event.preventDefault()
        handlers.onPlayPause?.()
        break
      case 'ArrowLeft':
        event.preventDefault()
        handlers.onPrev?.()
        break
      case 'ArrowRight':
        event.preventDefault()
        handlers.onNext?.()
        break
      case 'Home':
        event.preventDefault()
        handlers.onFirst?.()
        break
      case 'End':
        event.preventDefault()
        handlers.onLast?.()
        break
      default:
        break
    }
  }

  onMounted(() => window.addEventListener('keydown', onKeydown))
  onScopeDispose(() => window.removeEventListener('keydown', onKeydown))
}