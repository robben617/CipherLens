// 系统偏好 + 页内开关合并成一个布尔。
// 开启时立即取消所有正在运行的动画，并给根节点挂 data-motion="reduced"。

import { ref } from 'vue'

const reduced = ref(false)
let initialized = false
let mediaQuery: MediaQueryList | undefined

function apply(value: boolean): void {
  reduced.value = value
  document.documentElement.dataset.motion = value ? 'reduced' : ''

  if (value) {
    document.getAnimations().forEach((animation) => {
      try {
        animation.cancel()
      } catch {
        // ignore already-finished animations
      }
    })
  }
}

function init(): void {
  if (initialized || typeof window === 'undefined') return
  initialized = true

  mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
  apply(
    mediaQuery.matches ||
      document.documentElement.dataset.motion === 'reduced',
  )
  mediaQuery.addEventListener('change', (event) => apply(event.matches))
}

export function useReducedMotion() {
  init()
  return {
    reduced,
    setReduced: apply,
    toggle: () => apply(!reduced.value),
  }
}