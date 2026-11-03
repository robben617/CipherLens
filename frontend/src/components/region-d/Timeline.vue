<template>
  <div
    ref="timelineEl"
    class="c-timeline"
    role="slider"
    tabindex="0"
    aria-valuemin="0"
    :aria-valuemax="total"
    :aria-valuenow="preview"
    :aria-valuetext="`第 ${preview} 步，共 ${total} 步`"
    aria-describedby="timeline-legend"
    :class="{ 'is-dragging': dragging }"
    :style="{ '--i': preview, '--steps': total }"
    @pointerdown="onPointerDown"
    @pointermove="onPointerMove"
    @pointerup="onPointerUp"
    @pointercancel="onPointerUp"
    @keydown="onKeydown"
  >
    <div class="c-timeline__rounds" aria-hidden="true">
      <div
        v-for="segment in segments"
        :key="segment.round"
        class="c-timeline__round"
        :style="{ flexGrow: segment.span }"
      >
        <span>{{ segment.label }}</span>
      </div>
    </div>

    <div class="c-timeline__ticks" aria-hidden="true">
      <span
        v-for="tick in ticks"
        :key="tick.index"
        class="c-timeline__tick"
        :class="{ 'is-boundary': tick.boundary }"
        :style="{ '--i': tick.index }"
      ></span>
    </div>

    <div class="c-timeline__marks" role="group" aria-label="学习足迹标记">
      <button
        v-for="(mark, markIndex) in markerList"
        :key="mark.index"
        type="button"
        class="c-mark"
        :style="{ '--i': mark.index - 1 }"
        :data-kinds="mark.kinds"
        :tabindex="markIndex === activeMark ? 0 : -1"
        :aria-label="mark.label"
        @focus="activeMark = markIndex"
      >
        <i class="c-mark__shape" data-kind="diag" aria-hidden="true"></i>
        <i class="c-mark__shape" data-kind="ask" aria-hidden="true"></i>
      </button>
    </div>

    <div class="c-timeline__cursor" aria-hidden="true"></div>
    <div class="c-timeline__stepno" aria-hidden="true">{{ preview }} / {{ total }}</div>
    <div v-if="dragging" class="c-timeline__browse">浏览中</div>

    <div id="timeline-legend" class="c-timeline__legend">
      <span class="c-legend__item">
        <span class="c-legend__box">
          <i class="c-mark__shape" data-kind="diag" aria-hidden="true"></i>
        </span>
        <span class="c-legend__text">系统推测</span>
      </span>
      <span class="c-legend__item">
        <span class="c-legend__box">
          <i class="c-mark__shape" data-kind="ask" aria-hidden="true"></i>
        </span>
        <span class="c-legend__text">我的提问</span>
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { TraceStep } from '../../engine/trace'

export interface TimelineMark {
  diag: number
  ask: number
}

const props = defineProps<{
  steps: readonly TraceStep[]
  current: number
  markers: Record<number, TimelineMark>
}>()

const emit = defineEmits<{
  commit: [index: number]
}>()

const OP_LABEL: Record<string, string> = {
  sub_bytes: '字节代换',
  shift_rows: '行移位',
  mix_columns: '列混合',
  add_round_key: '轮密钥加',
}

const timelineEl = ref<HTMLElement | null>(null)
const preview = ref(props.current)
const dragging = ref(false)
const activeMark = ref(0)
let dragPointer: number | null = null

const total = computed(() => props.steps.length)

const segments = computed(() => {
  const list: { round: number; span: number; label: string }[] = []
  for (const step of props.steps) {
    const last = list[list.length - 1]
    if (last && last.round === step.round) {
      last.span += 1
    } else {
      list.push({
        round: step.round,
        span: 1,
        label: step.round === 0 ? 'INIT' : `R${step.round}`,
      })
    }
  }
  return list
})

const ticks = computed(() => {
  const boundary = new Set<number>()
  let cursor = 0
  for (const segment of segments.value) {
    boundary.add(cursor)
    cursor += segment.span
  }
  return Array.from({ length: total.value }, (_, index) => ({
    index: index + 1,
    boundary: boundary.has(index + 1),
  }))
})

const markerList = computed(() => {
  const list: { index: number; kinds: string; label: string }[] = []

  for (const [key, value] of Object.entries(props.markers)) {
    const index = Number(key)
    if (index < 1 || index > total.value) continue
    if (value.diag <= 0 && value.ask <= 0) continue

    const step = props.steps[index - 1]
    const round = step?.round ?? 0
    const roundText = round === 0 ? 'INIT' : `第 ${round} 轮`
    const op = OP_LABEL[step?.op ?? ''] ?? ''
    const kinds = [value.diag > 0 ? 'diag' : '', value.ask > 0 ? 'ask' : '']
      .filter(Boolean)
      .join(' ')

    list.push({
      index,
      kinds,
      label: `第 ${index} 步，共 ${total.value} 步，${roundText} ${op}，${value.diag} 条系统推测、${value.ask} 次提问，按回车打开标记详情`,
    })
  }

  return list.sort((a, b) => a.index - b.index)
})

watch(
  () => props.current,
  (current) => {
    if (!dragging.value) preview.value = Math.min(Math.max(current, 0), total.value)
  },
)

watch(total, () => {
  preview.value = Math.min(preview.value, total.value)
})

function indexFromEvent(event: PointerEvent): number {
  const rect = timelineEl.value?.getBoundingClientRect()
  if (!rect || rect.width === 0) return preview.value
  const ratio = (event.clientX - rect.left) / rect.width
  return Math.max(0, Math.min(total.value, Math.round(ratio * total.value)))
}

function commit(index: number): void {
  preview.value = index
  emit('commit', index)
}

function onPointerDown(event: PointerEvent): void {
  if (event.target instanceof HTMLElement && event.target.closest('.c-mark')) return
  dragPointer = event.pointerId
  dragging.value = true
  preview.value = indexFromEvent(event)
  ;(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId)
  event.preventDefault()
}

function onPointerMove(event: PointerEvent): void {
  if (!dragging.value || event.pointerId !== dragPointer) return
  preview.value = indexFromEvent(event)
}

function onPointerUp(event: PointerEvent): void {
  if (!dragging.value || event.pointerId !== dragPointer) return
  preview.value = indexFromEvent(event)
  dragging.value = false
  dragPointer = null
  commit(preview.value)
}

function jumpRound(direction: number): number {
  let start = 0
  for (const segment of segments.value) {
    const end = start + segment.span
    if (preview.value >= start && preview.value < end) {
      return direction < 0 ? start : end
    }
    start = end
  }
  return preview.value
}

function moveMark(offset: number): void {
  if (markerList.value.length === 0) return
  const next = Math.max(0, Math.min(markerList.value.length - 1, activeMark.value + offset))
  activeMark.value = next
  const buttons = timelineEl.value?.querySelectorAll<HTMLButtonElement>('.c-mark')
  buttons?.[next]?.focus()
}

function onKeydown(event: KeyboardEvent): void {
  if (event.key === '[' || event.key === ']') {
    event.preventDefault()
    moveMark(event.key === ']' ? 1 : -1)
    return
  }

  let next = preview.value
  switch (event.key) {
    case 'ArrowLeft':
      next = Math.max(0, preview.value - 1)
      break
    case 'ArrowRight':
      next = Math.min(total.value, preview.value + 1)
      break
    case 'Home':
      next = 0
      break
    case 'End':
      next = total.value
      break
    case 'PageUp':
      next = jumpRound(-1)
      break
    case 'PageDown':
      next = jumpRound(1)
      break
    default:
      return
  }

  event.preventDefault()
  commit(next)
}
</script>

<style scoped>
.c-timeline {
  --control-h: 40px;
  --step-w: calc(100% / var(--steps));
  position: relative;
  width: 100%;
  height: 64px;
  padding: 2px 0;
  box-sizing: border-box;
  user-select: none;
  touch-action: none;
}

.c-timeline__rounds {
  position: absolute;
  top: 2px;
  left: 0;
  right: 0;
  height: 16px;
  display: flex;
}

.c-timeline__round {
  flex-basis: 0;
  min-width: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-right: 2px solid var(--line-strong);
  background: var(--paper-0);
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  letter-spacing: var(--ls-label);
  color: var(--ink-3);
  overflow: hidden;
}

.c-timeline__round:nth-child(even) {
  background: var(--surface-inset);
}

.c-timeline__ticks {
  position: absolute;
  top: 18px;
  left: 0;
  right: 0;
  height: 10px;
}

.c-timeline__tick {
  position: absolute;
  bottom: 0;
  left: calc(var(--i) * var(--step-w));
  width: 1px;
  height: 6px;
  background: var(--line-default);
  z-index: 1;
}

.c-timeline__tick.is-boundary {
  width: 2px;
  height: 10px;
  background: var(--line-strong);
}

.c-timeline__marks {
  position: absolute;
  top: 28px;
  left: 0;
  right: 0;
  height: var(--tl-mark-band);
}

.c-mark {
  position: absolute;
  top: 0;
  left: calc(var(--i) * var(--step-w));
  width: var(--step-w);
  height: 100%;
  padding: 0;
  border: 0;
  background: transparent;
  z-index: 3;
  cursor: pointer;
}

.c-mark:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
  box-shadow: 0 0 0 4px var(--paper-0);
}

.c-mark__shape {
  display: block;
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  border-radius: 0;
}

.c-mark__shape[data-kind="diag"] {
  top: 2px;
  width: var(--tl-mark-diag);
  height: var(--tl-mark-diag);
  border-radius: 50%;
  background: var(--tl-mark-diag-ink);
}

.c-mark__shape[data-kind="ask"] {
  bottom: 2px;
  width: var(--tl-mark-ask);
  height: var(--tl-mark-ask);
  background: var(--accent);
}

.c-mark[data-kinds] .c-mark__shape {
  display: none;
}

.c-mark[data-kinds~="diag"] .c-mark__shape[data-kind="diag"] {
  display: block;
}

.c-mark[data-kinds~="ask"] .c-mark__shape[data-kind="ask"] {
  display: block;
}

.c-timeline__cursor {
  position: absolute;
  top: 2px;
  left: calc(var(--i) * var(--step-w));
  width: 2px;
  height: var(--tl-cursor-h);
  margin-left: -1px;
  background: var(--accent);
  z-index: 2;
}

.c-timeline.is-dragging .c-timeline__cursor {
  background: transparent;
  box-shadow: inset 0 0 0 2px var(--accent);
}

.c-timeline__stepno {
  position: absolute;
  top: calc(2px + var(--tl-cursor-h) + 4px);
  left: calc(var(--i) * var(--step-w) + 6px);
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  line-height: 1;
  color: var(--ink-3);
  white-space: nowrap;
}

.c-timeline__browse {
  position: absolute;
  top: 4px;
  right: 12px;
  padding: 2px var(--sp-1);
  border: var(--rule-region-w) solid var(--line-hairline);
  background: var(--surface-raised);
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

.c-timeline__legend {
  position: absolute;
  top: calc(-1 * var(--control-h));
  right: 12px;
  height: var(--control-h);
  min-width: var(--tl-hint-slot);
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 16px;
}

.c-legend__item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 4px;
  height: var(--tl-mark-band);
}

.c-legend__box {
  position: relative;
  width: 20px;
  height: var(--tl-mark-band);
}

.c-legend__text {
  font-family: var(--font-ui);
  font-size: var(--fs-micro);
  color: var(--ink-3);
  white-space: nowrap;
}

@media (max-height: 780px) {
  .c-timeline {
    --control-h: 36px;
    height: 56px;
  }

  .c-timeline__rounds {
    top: 2px;
    height: 14px;
  }

  .c-timeline__ticks {
    top: 16px;
    height: 8px;
  }

  .c-timeline__marks {
    top: 24px;
  }

  .c-timeline__cursor {
    top: 2px;
  }

  .c-timeline__stepno {
    top: 44px;
  }
}

[data-mode="present"] .c-timeline {
  --control-h: 52px;
  height: 84px;
}

[data-mode="present"] .c-timeline__rounds {
  top: 4px;
  height: 18px;
}

[data-mode="present"] .c-timeline__ticks {
  top: 24px;
  height: 10px;
}

[data-mode="present"] .c-timeline__marks {
  top: 36px;
}

[data-mode="present"] .c-timeline__cursor {
  top: 4px;
}

[data-mode="present"] .c-timeline__stepno {
  top: 62px;
}
</style>