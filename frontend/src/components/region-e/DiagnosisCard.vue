<template>
  <div ref="slotEl" class="c-diagslot" aria-live="polite">
    <p class="c-diagslot__idle" :class="{ 'is-hidden': note }">DIAGNOSTIC —</p>

    <aside
      v-if="note"
      class="c-annotation"
      :class="{ 'is-closing': closing, 'is-answered': answered }"
      role="note"
      data-state="expanded"
      :style="{ '--tick-y': `${tickY}px` }"
    >
      <span class="c-annotation__bar" aria-hidden="true"></span>

      <svg class="c-annotation__bracket" viewBox="0 0 10 26" aria-hidden="true">
        <path ref="bracketEl" d="M9 1 L2 1 L2 25 L9 25" pathLength="100" />
      </svg>

      <div class="c-annotation__text">
        <p class="c-annotation__q" :title="note.question">{{ note.question }}</p>
        <p v-if="history.length === 1" class="c-annotation__disclaimer">
          这是系统的推测，不是判错
        </p>
      </div>

      <div class="c-annotation__acts">
        <button class="c-annotation__act" type="button" @click="answer">是</button>
        <button class="c-annotation__act" type="button" @click="answer">不是</button>
        <button class="c-annotation__act" type="button" @click="answer">这提示不对</button>
      </div>

      <span class="c-annotation__count" aria-hidden="true">{{ history.length }}</span>
      <button
        class="c-annotation__close"
        type="button"
        aria-label="关闭提示"
        @click="dismiss"
      >
        ×
      </button>
      <span class="c-annotation__tick" aria-hidden="true"></span>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onScopeDispose, ref, watch } from 'vue'
import { usePlaybackStore } from '../../stores/playback'
import { useUiStore } from '../../stores/ui'
import {
  useDiagnosisStore,
  type DiagnosisPayload,
  type DiagnosisType,
} from '../../stores/diagnosis'
import { useReducedMotion } from '../../composables/useReducedMotion'

const props = defineProps<{
  stepIndex: number
  stepLabel: string
  stepBefore: readonly number[]
  stepAfter: readonly number[]
  changed: readonly number[]
}>()

const playback = usePlaybackStore()
const ui = useUiStore()
const diagnosis = useDiagnosisStore()
const { reduced } = useReducedMotion()

const DEBUG =
  import.meta.env.DEV &&
  new URLSearchParams(window.location.search).get('debug') === 'diagnosis'

const note = computed(() => diagnosis.note)
const history = computed(() => diagnosis.history)

const slotEl = ref<HTMLElement | null>(null)
const bracketEl = ref<SVGPathElement | null>(null)
const tickY = ref(0)
const closing = ref(false)
const answered = ref(false)

let bracketAnimation: Animation | undefined
let tickTimer: ReturnType<typeof setInterval> | undefined
let closeTimer: ReturnType<typeof setTimeout> | undefined

const hex = (value: number | undefined): string =>
  (value ?? 0).toString(16).toUpperCase().padStart(2, '0')

function buildPayload(type: DiagnosisType): DiagnosisPayload {
  const before = props.stepBefore
  const after = props.stepIndex === 0 ? props.stepBefore : props.stepAfter
  const candidates = props.changed.length ? props.changed : [0]
  const byteIndex =
    type === 'toggle'
      ? candidates[Math.min(7, candidates.length - 1)] ?? 0
      : candidates[0] ?? 0
  const row = byteIndex % 4
  const col = Math.floor(byteIndex / 4)

  const question =
    type === 'toggle'
      ? `你在第 ${diagnosis.pendingFrom} 步和第 ${diagnosis.pendingTo} 步之间来回看了 3 次。第 ${row + 1} 行第 ${col + 1} 列从 ${hex(before[byteIndex])} 变成 ${hex(after[byteIndex])}，这一步你盯住了吗？`
      : `这一步停在「${props.stepLabel}」超过 20 秒。第 ${row + 1} 行第 ${col + 1} 列：${hex(before[byteIndex])} → ${hex(after[byteIndex])}，你觉得它是先变，还是跟着别的字节被带过去的？`

  return { question, byteIndex, row, col }
}

function fire(type: DiagnosisType = 'idle'): boolean {
  return diagnosis.fire(type, buildPayload(type))
}

function measureTick(): void {
  const slot = slotEl.value
  const current = diagnosis.note
  if (!slot || !current) {
    tickY.value = 0
    return
  }
  const cell = document.querySelector<HTMLElement>(
    `.c-byte[data-index="${current.byteIndex}"]`,
  )
  if (!cell) {
    tickY.value = 0
    return
  }
  const slotRect = slot.getBoundingClientRect()
  const cellRect = cell.getBoundingClientRect()
  tickY.value = Math.round(cellRect.top + cellRect.height / 2 - slotRect.top)
}

function animateBracket(): void {
  const path = bracketEl.value
  if (!path) return

  bracketAnimation?.cancel()
  bracketAnimation = undefined
  path.style.strokeDasharray = '100'

  if (reduced.value) {
    path.style.strokeDashoffset = '0'
    return
  }

  path.style.strokeDashoffset = '100'
  bracketAnimation = path.animate(
    [
      { strokeDashoffset: 100, offset: 0 },
      { strokeDashoffset: 66.6, offset: 140 / 420 },
      { strokeDashoffset: 33.3, offset: 300 / 420 },
      { strokeDashoffset: 0, offset: 1 },
    ],
    { duration: 420, easing: 'ease-out', fill: 'both' },
  )
}

function dismiss(): void {
  if (!diagnosis.note) return
  closing.value = true
  window.clearTimeout(closeTimer)
  closeTimer = window.setTimeout(() => {
    closing.value = false
    answered.value = false
    diagnosis.dismiss()
  }, 200)
}

function answer(): void {
  answered.value = true
  dismiss()
}

function onActivity(): void {
  diagnosis.noteActivity()
}

function onResize(): void {
  measureTick()
}

function tick(): void {
  const now = Date.now()
  if (!diagnosis.ready(now)) return
  fire(diagnosis.pendingType)
}

function exposeDebug(): void {
  const target = window as Window & { __diag?: Record<string, unknown> }
  target.__diag = {
    forceFire: (type: DiagnosisType = 'idle') => fire(type),
    state: () => ({
      note: diagnosis.note,
      history: diagnosis.history.length,
      lastFiredAt: diagnosis.lastFiredAt,
      lastActivityAt: diagnosis.lastActivityAt,
      lastBlocked: diagnosis.lastBlocked,
      pendingType: diagnosis.pendingType,
      pendingFrom: diagnosis.pendingFrom,
      pendingTo: diagnosis.pendingTo,
      tickY: tickY.value,
    }),
    setChannel: (channel: 'idle' | 'tutor') => ui.setChannel(channel),
    reset: () => diagnosis.resetCooldown(),
    dismiss: () => {
      closing.value = false
      answered.value = false
      diagnosis.dismiss()
    },
  }
}

watch(
  () => playback.currentStep,
  (step) => {
    diagnosis.recordStep(step)
  },
)

watch(
  () => playback.isPlaying,
  (playing) => {
    if (playing) diagnosis.noteActivity()
  },
)

watch(
  () => ui.activeChannel,
  (channel) => {
    if (channel === 'tutor') diagnosis.dismiss()
    diagnosis.noteActivity()
  },
)

watch(
  () => diagnosis.note,
  async (current) => {
    if (!current) {
      bracketAnimation?.cancel()
      bracketAnimation = undefined
      tickY.value = 0
      return
    }
    closing.value = false
    answered.value = false
    await nextTick()
    measureTick()
    animateBracket()
  },
)

onMounted(() => {
  tickTimer = window.setInterval(tick, 500)
  window.addEventListener('pointerdown', onActivity, { passive: true })
  window.addEventListener('keydown', onActivity, true)
  window.addEventListener('wheel', onActivity, { passive: true })
  window.addEventListener('scroll', onActivity, { passive: true, capture: true })
  window.addEventListener('resize', onResize)
  if (DEBUG) exposeDebug()
})

onScopeDispose(() => {
  window.clearInterval(tickTimer)
  window.clearTimeout(closeTimer)
  bracketAnimation?.cancel()
  window.removeEventListener('pointerdown', onActivity)
  window.removeEventListener('keydown', onActivity, true)
  window.removeEventListener('wheel', onActivity)
  window.removeEventListener('scroll', onActivity, true)
  window.removeEventListener('resize', onResize)
  if (DEBUG) {
    delete (window as Window & { __diag?: unknown }).__diag
  }
})
</script>

<style scoped>
.c-diagslot {
  position: relative;
  flex: 0 0 var(--diag-row-h);
  height: var(--diag-row-h);
  margin: calc(-1 * var(--sp-3)) calc(-1 * var(--sp-3)) 0;
  padding: 0 var(--sp-3);
  box-sizing: border-box;
  border-bottom: var(--rule-region-w) solid var(--line-hairline);
  background: var(--paper-0);
}

.c-diagslot__idle {
  margin: 0;
  line-height: var(--diag-row-h);
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  letter-spacing: var(--ls-label);
  color: var(--ink-2);
}

.c-diagslot__idle.is-hidden {
  display: none;
}

.c-annotation {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  height: 100%;
  padding: 4px var(--sp-2);
  box-sizing: border-box;
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  background: var(--surface-raised);
  animation: c-annotation-in 140ms var(--e-out-quint) 280ms both;
}

.c-annotation.is-closing {
  animation: none;
  opacity: 0;
  transition: opacity 200ms linear;
}

@keyframes c-annotation-in {
  from {
    opacity: 0;
    transform: translateY(2px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .c-annotation {
    animation: none;
  }
}

[data-motion="reduced"] .c-annotation {
  animation: none;
}

.c-annotation__bar {
  flex: 0 0 2px;
  align-self: stretch;
  margin: 2px 0;
  background: var(--st-error);
}

.c-annotation__bracket {
  flex: 0 0 10px;
  width: 10px;
  height: 26px;
}

.c-annotation__bracket path {
  fill: none;
  stroke: var(--st-error);
  stroke-width: 1.5;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.c-annotation__text {
  flex: 1;
  min-width: 0;
}

.c-annotation__q {
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: var(--fs-micro);
  line-height: 1.2;
  color: var(--ink-1);
}

.c-annotation__disclaimer {
  margin: 2px 0 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: var(--fs-micro);
  line-height: 1.1;
  color: var(--ink-4);
}

.c-annotation__acts {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  gap: var(--sp-1);
}

.c-annotation__act {
  padding: 0;
  border: 0;
  background: transparent;
  font-family: var(--font-ui);
  font-size: var(--fs-micro);
  line-height: 1;
  color: var(--accent-strong);
  cursor: pointer;
  white-space: nowrap;
}

.c-annotation__count {
  display: flex;
  flex: 0 0 14px;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
  border: var(--rule-region-w) solid var(--st-error);
  border-radius: 50%;
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  line-height: 1;
  color: var(--st-error);
}

.c-annotation__close {
  flex: 0 0 auto;
  padding: 0;
  border: 0;
  background: transparent;
  font-family: var(--font-ui);
  font-size: var(--fs-label);
  line-height: 1;
  color: var(--ink-3);
  cursor: pointer;
}

.c-annotation__tick {
  position: absolute;
  left: calc(-1 * var(--sp-3) - 1px);
  top: calc(var(--tick-y) - 1px);
  width: 12px;
  height: 2px;
  background: var(--st-error);
}

[data-mode="present"] .c-diagslot {
  display: none;
}

@media (max-width: 69.9375rem) {
  .c-diagslot {
    display: none;
  }
}
</style>