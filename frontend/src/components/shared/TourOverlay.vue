<template>
  <Teleport to="body">
    <div
      v-if="isOpen"
      class="tour"
      data-tour
      @keydown="onKeydown"
      @click.stop
    >
      <div
        v-for="(mask, i) in layout.masks"
        :key="i"
        class="tour__mask"
        :style="mask"
        aria-hidden="true"
      ></div>

      <div class="tour__ring" :style="layout.ring" aria-hidden="true"></div>

      <div
        ref="bubbleEl"
        class="tour__bubble"
        :style="layout.bubble"
        role="dialog"
        aria-modal="true"
        aria-labelledby="tour-title"
        aria-describedby="tour-body"
      >
        <p class="tour__count" aria-hidden="true">{{ stepNo }} / {{ total }}</p>
        <h2 id="tour-title" class="tour__title">{{ step?.title }}</h2>
        <p id="tour-body" class="tour__body">{{ step?.body }}</p>

        <div class="tour__foot">
          <button type="button" class="tour__link" data-action="tour-skip" @click="close">
            跳过引导
          </button>
          <div class="tour__actions">
            <button
              v-if="isOpen && stepNo > 1"
              type="button"
              class="tour__ghost"
              data-action="tour-prev"
              @click="prev"
            >
              上一步
            </button>
            <button
              ref="primaryEl"
              type="button"
              class="tour__primary"
              data-action="tour-next"
              @click="next"
            >
              {{ step?.cta }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, onScopeDispose, ref, watch } from 'vue'
import { useTour } from '../../composables/useTour'

const emit = defineEmits<{
  /** 进入某一关；prevKey 用于让宿主收起上一关的副作用（例如暂停播放） */
  change: [key: string, prevKey: string | null]
  close: []
}>()

const { isOpen, step, stepNo, total, next, prev, close } = useTour()

const BUBBLE_W = 300
const GAP = 12
const PAD = 6
const EDGE = 12

const bubbleEl = ref<HTMLElement | null>(null)
const primaryEl = ref<HTMLButtonElement | null>(null)
const bubbleH = ref(176)
const vw = ref(typeof window === 'undefined' ? 1280 : window.innerWidth)
const vh = ref(typeof window === 'undefined' ? 800 : window.innerHeight)

interface Box {
  top: number
  left: number
  width: number
  height: number
}

const rect = ref<Box | null>(null)
let lastFocus: HTMLElement | null = null

function clampBox(top: number, left: number, right: number, bottom: number): Box {
  const t = Math.max(0, Math.min(top, bottom))
  const l = Math.max(0, Math.min(left, right))
  return {
    top: t,
    left: l,
    width: Math.max(0, right - l),
    height: Math.max(0, bottom - t),
  }
}

function measure(): void {
  const anchor = step.value?.anchor
  const el = anchor ? document.querySelector<HTMLElement>(anchor) : null
  if (!el) {
    // 锚点不在（例如表格视图下结构变了）：退化为居中提示，绝不静默失败
    rect.value = clampBox(
      vh.value / 2 - 1,
      vw.value / 2 - 1,
      vw.value / 2 + 1,
      vh.value / 2 + 1,
    )
    return
  }
  const r = el.getBoundingClientRect()
  rect.value = clampBox(r.top - PAD, r.left - PAD, r.right + PAD, r.bottom + PAD)
}

function syncViewport(): void {
  vw.value = window.innerWidth
  vh.value = window.innerHeight
  measure()
}

const layout = computed(() => {
  const box = rect.value ?? { top: 0, left: 0, width: 0, height: 0 }
  const W = vw.value
  const H = vh.value
  const h = bubbleH.value

  const masks = [
    { top: '0px', left: '0px', width: '100%', height: `${box.top}px` },
    {
      top: `${box.top + box.height}px`,
      left: '0px',
      width: '100%',
      height: `${Math.max(0, H - box.top - box.height)}px`,
    },
    {
      top: `${box.top}px`,
      left: '0px',
      width: `${box.left}px`,
      height: `${box.height}px`,
    },
    {
      top: `${box.top}px`,
      left: `${box.left + box.width}px`,
      width: `${Math.max(0, W - box.left - box.width)}px`,
      height: `${box.height}px`,
    },
  ]

  const ring = {
    top: `${box.top}px`,
    left: `${box.left}px`,
    width: `${box.width}px`,
    height: `${box.height}px`,
  }

  // 四向翻转：下 → 上 → 右 → 左，都放不下就贴底居中
  const need = h + GAP + 8
  const below = H - (box.top + box.height)
  const above = box.top
  const rightRoom = W - (box.left + box.width)
  const leftRoom = box.left

  const centerX = Math.min(
    Math.max(box.left + box.width / 2 - BUBBLE_W / 2, EDGE),
    Math.max(EDGE, W - BUBBLE_W - EDGE),
  )
  const clampY = Math.min(Math.max(box.top, EDGE), Math.max(EDGE, H - h - EDGE))

  let top: number
  let left: number

  if (below >= need) {
    top = box.top + box.height + GAP
    left = centerX
  } else if (above >= need) {
    top = box.top - h - GAP
    left = centerX
  } else if (rightRoom >= BUBBLE_W + GAP) {
    top = clampY
    left = box.left + box.width + GAP
  } else if (leftRoom >= BUBBLE_W + GAP) {
    top = clampY
    left = box.left - BUBBLE_W - GAP
  } else {
    top = Math.max(EDGE, H - h - EDGE)
    left = centerX
  }

  return {
    masks,
    ring,
    bubble: {
      top: `${Math.round(top)}px`,
      left: `${Math.round(left)}px`,
      width: `${BUBBLE_W}px`,
    },
  }
})

async function settle(): Promise<void> {
  measure()
  await nextTick()
  if (bubbleEl.value) bubbleH.value = bubbleEl.value.offsetHeight
}

watch(
  isOpen,
  async (open) => {
    if (open) {
      lastFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null
      window.addEventListener('resize', syncViewport)
      await settle()
      primaryEl.value?.focus({ preventScroll: true })
    } else {
      window.removeEventListener('resize', syncViewport)
      emit('close')
      lastFocus?.focus({ preventScroll: true })
      lastFocus = null
    }
  },
  { flush: 'post' },
)

watch(
  () => step.value?.key,
  async (key, previous) => {
    if (!key) return
    await settle()
    primaryEl.value?.focus({ preventScroll: true })
    emit('change', key, previous ?? null)
  },
  { flush: 'post' },
)

// 视口变化后若气泡变高（换行），重新算一次高度
watch(bubbleEl, async (el) => {
  if (!el) return
  await nextTick()
  bubbleH.value = el.offsetHeight
})

function onKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape') {
    event.preventDefault()
    event.stopPropagation()
    close()
    return
  }
  if (event.key !== 'Tab' || !bubbleEl.value) return

  const nodes = Array.from(
    bubbleEl.value.querySelectorAll<HTMLElement>('button:not([disabled])'),
  )
  if (nodes.length === 0) return
  const first = nodes[0]
  const last = nodes[nodes.length - 1]
  if (!first || !last) return
  const active = document.activeElement

  if (event.shiftKey && active === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && active === last) {
    event.preventDefault()
    first.focus()
  }
}

onScopeDispose(() => window.removeEventListener('resize', syncViewport))
</script>

<style scoped>
.tour {
  position: fixed;
  inset: 0;
  z-index: 80;
}

.tour__mask {
  position: fixed;
  background: var(--scrim-tour);
}

.tour__ring {
  position: fixed;
  border: 2px solid var(--accent);
  border-radius: 2px;
  box-shadow: 0 0 0 3px var(--accent-ring);
  pointer-events: none;
}

.tour__bubble {
  position: fixed;
  box-sizing: border-box;
  padding: var(--sp-3) var(--sp-4) var(--sp-3);
  border: var(--rule-region-w) solid var(--line-default);
  border-radius: var(--card-r);
  background: var(--paper-0);
  box-shadow: var(--shadow-float);
  animation: tour-in var(--d-2) var(--e-out-quart);
}

.tour__count {
  margin: 0 0 var(--sp-1);
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  letter-spacing: var(--ls-label);
  color: var(--ink-3);
}

.tour__title {
  margin: 0 0 var(--sp-2);
  font-family: var(--font-display);
  font-size: var(--fs-ui);
  font-weight: 600;
  line-height: 1.4;
  color: var(--ink-1);
}

.tour__body {
  margin: 0 0 var(--sp-4);
  font-family: var(--font-ui);
  font-size: var(--fs-label);
  line-height: var(--lh-body);
  color: var(--ink-2);
}

.tour__foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-2);
}

.tour__actions {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}

.tour__link {
  padding: 0;
  border: 0;
  background: transparent;
  font-family: var(--font-ui);
  font-size: var(--fs-micro);
  color: var(--ink-3);
  text-decoration: underline;
  text-underline-offset: 3px;
  cursor: pointer;
}

.tour__link:hover {
  color: var(--ink-1);
}

.tour__ghost,
.tour__primary {
  height: 30px;
  padding: 0 var(--sp-3);
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  background: transparent;
  font-family: var(--font-ui);
  font-size: var(--fs-label);
  color: var(--ink-2);
  cursor: pointer;
}

.tour__ghost:hover {
  border-color: var(--line-default);
  color: var(--ink-1);
}

.tour__primary {
  border-color: var(--accent);
  background: var(--accent);
  color: var(--paper-0);
}

.tour__primary:hover {
  background: var(--accent-strong);
  border-color: var(--accent-strong);
}

.tour__link:focus-visible,
.tour__ghost:focus-visible,
.tour__primary:focus-visible {
  outline: var(--focus-ring-w) solid var(--focus-ring-color);
  outline-offset: var(--focus-ring-offset);
}

@keyframes tour-in {
  from {
    opacity: 0;
    transform: translateY(4px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

[data-motion="reduced"] .tour__bubble {
  animation: none;
}

@media (prefers-reduced-motion: reduce) {
  .tour__bubble {
    animation: none;
  }
}
</style>
