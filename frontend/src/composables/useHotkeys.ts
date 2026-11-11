// 工作台键盘：播放、步进、轮跳、标记跳转、AI/抽屉/演示/导出等。
// 输入框、文本域、下拉框、contenteditable 聚焦时除 Esc 外全部失效。
// 矩阵内方向键由 useRovingGrid 先处理并 preventDefault，这里通过
// event.defaultPrevented 让位，避免"矩阵内按右键变成下一步"。

import { onMounted, onScopeDispose } from 'vue'

export interface HotkeyHandlers {
  onPlayPause?: () => void
  onPrev?: () => void
  onNext?: () => void
  onFirst?: () => void
  onLast?: () => void
  onRoundPrev?: () => void
  onRoundNext?: () => void
  onPrevMark?: () => void
  onNextMark?: () => void
  onFocusAsk?: () => void
  onEscape?: () => void
  onJump?: () => void
  onVector?: () => void
  onHelp?: () => void
  onPresent?: () => void
  onExport?: () => void
  onSBox?: () => void
  onKeyBits?: (bits: 128 | 192 | 256) => void
  onToggleDirection?: () => void
  onToggleAi?: () => void
  onKeyDrawer?: () => void
  /** 返回 true 时吞掉除 Esc 以外的全部快捷键（引导层打开时用） */
  blocked?: () => boolean
}

const EDITABLE = 'input, textarea, select, [contenteditable=""], [contenteditable="true"]'

function isEditable(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false
  return target.matches(EDITABLE) || target.isContentEditable
}

export function useHotkeys(handlers: HotkeyHandlers): void {
  function onKeydown(event: KeyboardEvent): void {
    if (event.defaultPrevented) return

    if (event.key === 'Escape') {
      handlers.onEscape?.()
      return
    }

    if (handlers.blocked?.()) return

    if (isEditable(event.target)) return

    switch (event.key) {
      case ' ':
        event.preventDefault()
        handlers.onPlayPause?.()
        break
      case 'ArrowLeft':
        event.preventDefault()
        if (event.shiftKey) handlers.onRoundPrev?.()
        else handlers.onPrev?.()
        break
      case 'ArrowRight':
        event.preventDefault()
        if (event.shiftKey) handlers.onRoundNext?.()
        else handlers.onNext?.()
        break
      case 'Home':
        event.preventDefault()
        handlers.onFirst?.()
        break
      case 'End':
        event.preventDefault()
        handlers.onLast?.()
        break
      case '[':
        event.preventDefault()
        handlers.onPrevMark?.()
        break
      case ']':
        event.preventDefault()
        handlers.onNextMark?.()
        break
      case '?':
        event.preventDefault()
        handlers.onHelp?.()
        break
      case 'j':
      case 'J':
        event.preventDefault()
        handlers.onJump?.()
        break
      case 'a':
      case 'A':
        event.preventDefault()
        handlers.onFocusAsk?.()
        break
      case 'v':
      case 'V':
        event.preventDefault()
        handlers.onVector?.()
        break
      case 'p':
      case 'P':
        event.preventDefault()
        handlers.onPresent?.()
        break
      case 'e':
      case 'E':
        event.preventDefault()
        handlers.onExport?.()
        break
      case 's':
      case 'S':
        event.preventDefault()
        handlers.onSBox?.()
        break
      case 'd':
      case 'D':
        event.preventDefault()
        handlers.onToggleDirection?.()
        break
      case 'f':
      case 'F':
        event.preventDefault()
        handlers.onToggleAi?.()
        break
      case 'k':
      case 'K':
      case 'g':
      case 'G':
        event.preventDefault()
        handlers.onKeyDrawer?.()
        break
      case '1':
      case '2':
      case '3':
        event.preventDefault()
        handlers.onKeyBits?.(Number(event.key) * 64 + 64 as 128 | 192 | 256)
        break
      default:
        break
    }
  }

  onMounted(() => window.addEventListener('keydown', onKeydown))
  onScopeDispose(() => window.removeEventListener('keydown', onKeydown))
}