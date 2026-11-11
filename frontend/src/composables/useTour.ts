// 新手引导 3 关：一次性走完，可随时跳过。
// 状态放在模块作用域，顶栏按钮与遮罩共享同一份 —— 不需要 store，也不需要 provide。
// 走完（或跳过）写 localStorage['cl:onboarded']，之后只有 ?tour=1 或手动点「引导」才会再出现。

import { computed, ref } from 'vue'

export type TourStepKey = 'stage' | 'transport' | 'ai'

export interface TourStep {
  readonly key: TourStepKey
  /** 锚点：工作台五区的稳定选择器，不依赖组件内部类名 */
  readonly anchor: string
  readonly title: string
  readonly body: string
  readonly cta: string
}

export const TOUR_STEPS: readonly TourStep[] = [
  {
    key: 'stage',
    anchor: '[data-region="c"]',
    title: '这 16 个格子就是 16 个字节',
    body: '先别管数字含义，只要知道它们就是你要加密的数据。',
    cta: '下一步',
  },
  {
    key: 'transport',
    anchor: '[data-region="d"]',
    title: '按一下空格，看黄色的格子',
    body: '每次只有变了的格子会亮，其他格子不动。',
    cta: '下一步',
  },
  {
    key: 'ai',
    anchor: '[data-region="e"]',
    title: '看不懂就点这里问',
    body: '它会用当前这一步的数据回答你，不会瞎编。',
    cta: '开始用',
  },
]

const STORAGE_KEY = 'cl:onboarded'

// 模块级单例：多次调用 useTour() 拿到的是同一份状态
const index = ref(-1)

export function useTour() {
  const isOpen = computed(() => index.value >= 0)
  const step = computed<TourStep | null>(() => TOUR_STEPS[index.value] ?? null)
  const stepNo = computed(() => index.value + 1)
  const total = computed(() => TOUR_STEPS.length)
  const isLast = computed(() => index.value === TOUR_STEPS.length - 1)

  function hasSeen(): boolean {
    try {
      return localStorage.getItem(STORAGE_KEY) === '1'
    } catch {
      // 隐私模式禁写 localStorage：当作没看过，但关掉后本次会话不会再弹
      return false
    }
  }

  function markSeen(): void {
    try {
      localStorage.setItem(STORAGE_KEY, '1')
    } catch {
      /* 忽略：无存储时不影响引导本身 */
    }
  }

  function open(): void {
    index.value = 0
  }

  function close(): void {
    index.value = -1
    markSeen()
  }

  function next(): void {
    if (index.value < 0) return
    if (index.value >= TOUR_STEPS.length - 1) {
      close()
      return
    }
    index.value += 1
  }

  function prev(): void {
    if (index.value > 0) index.value -= 1
  }

  return { index, isOpen, step, stepNo, total, isLast, hasSeen, open, close, next, prev }
}

/** 测试用：清掉「已看过」标记 */
export function resetTourSeen(): void {
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch {
    /* 忽略 */
  }
}
