<template>
  <div class="c-transport" :style="{ '--step-interval': `${playback.intervalMs}ms` }">
    <div class="c-transport__ctrl" role="group" aria-label="播放控制">
      <button
        class="c-transport__btn"
        data-action="first"
        type="button"
        aria-label="首步"
        :aria-disabled="!playback.canPrev"
        :class="{ 'is-off': !playback.canPrev }"
        @click="jumpFirst"
      >
        <svg viewBox="0 0 20 20" aria-hidden="true" focusable="false">
          <path d="M5.75 5.25v9.5" />
          <path d="M15 5.5 7.5 10 15 14.5Z" />
        </svg>
      </button>

      <button
        class="c-transport__btn"
        data-action="prev"
        type="button"
        aria-label="上一步"
        :aria-disabled="!playback.canPrev"
        :class="{ 'is-off': !playback.canPrev }"
        @click="stepPrev"
      >
        <svg viewBox="0 0 20 20" aria-hidden="true" focusable="false">
          <path d="M13.25 5.5 5.75 10l7.5 4.5Z" />
        </svg>
      </button>

      <button
        class="c-transport__btn c-transport__btn--play"
        data-action="play"
        type="button"
        :aria-label="playback.isPlaying ? '暂停' : '播放'"
        :aria-pressed="playback.isPlaying"
        :aria-disabled="total === 0"
        :class="{ 'is-off': total === 0, 'is-playing': playback.isPlaying }"
        @click="playback.toggle()"
      >
        <svg v-if="playback.isPlaying" viewBox="0 0 20 20" aria-hidden="true" focusable="false">
          <path d="M7.4 5.2v9.6M12.6 5.2v9.6" stroke-width="2.2" />
        </svg>
        <svg v-else viewBox="0 0 20 20" aria-hidden="true" focusable="false">
          <path d="M7.3 4.85 15.7 10 7.3 15.15Z" fill="currentColor" stroke="none" />
        </svg>
      </button>

      <button
        class="c-transport__btn"
        data-action="next"
        type="button"
        aria-label="下一步"
        :aria-disabled="!playback.canNext"
        :class="{ 'is-off': !playback.canNext }"
        @click="stepNext"
      >
        <svg viewBox="0 0 20 20" aria-hidden="true" focusable="false">
          <path d="M6.75 5.5 14.25 10l-7.5 4.5Z" />
        </svg>
      </button>

      <button
        class="c-transport__btn"
        data-action="last"
        type="button"
        aria-label="末步"
        :aria-disabled="!playback.canNext"
        :class="{ 'is-off': !playback.canNext }"
        @click="jumpLast"
      >
        <svg viewBox="0 0 20 20" aria-hidden="true" focusable="false">
          <path d="M4.9 5.5 12.4 10 4.9 14.5Z" />
          <path d="M14.25 5.25v9.5" />
        </svg>
      </button>
    </div>

    <div
      ref="trackEl"
      class="c-progress"
      data-action="seek"
      role="slider"
      tabindex="0"
      aria-label="播放进度"
      aria-valuemin="0"
      :aria-valuemax="total"
      :aria-valuenow="playback.currentStep"
      :aria-valuetext="progressText"
      :class="{ 'is-dragging': dragging }"
      @pointerdown="onSeekDown"
      @pointermove="onSeekMove"
      @pointerup="onSeekUp"
      @pointercancel="onSeekUp"
      @pointerleave="onSeekLeave"
      @keydown="onSeekKey"
    >
      <div class="c-progress__track" aria-hidden="true">
        <span class="c-progress__fill" :style="{ width: ratio }"></span>
        <span
          v-for="boundary in boundaries"
          :key="boundary"
          class="c-progress__split"
          :style="{ left: `${boundary * 100}%` }"
        ></span>
        <span class="c-progress__cursor" :style="{ left: ratio }"></span>
      </div>
      <span v-if="hoverIndex !== null" class="c-progress__tip" :style="{ left: tipPos }">
        {{ tipText }}
      </span>
    </div>

    <div class="c-transport__stepno">
      <b>{{ playback.currentStep }}</b><span>/ {{ total }}</span>
    </div>

    <div class="c-speed" role="group" aria-label="播放倍速">
      <button
        v-for="option in SPEEDS"
        :key="option"
        type="button"
        class="c-speed__opt"
        :data-speed="option"
        :aria-pressed="playback.speed === option"
        @click="playback.setSpeed(option)"
      >
        {{ option }}×
      </button>
    </div>

    <button
      class="c-transport__ghost"
      data-action="motion"
      type="button"
      :aria-pressed="reduced"
      :aria-label="reduced ? '恢复动效' : '减少动效'"
      :title="reduced ? '恢复动效' : '减少动效'"
      @click="toggleReduced"
    >
      动效
    </button>

    <div id="timeline-legend" class="c-transport__legend">
      <span class="c-legend__item">
        <span class="c-legend__box">
          <i class="c-mark__shape" data-kind="diag" aria-hidden="true"></i>
        </span>
        <span class="c-legend__text">系统推测</span>
        <span class="c-legend__text c-legend__text--short">推测</span>
      </span>
      <span class="c-legend__item">
        <span class="c-legend__box">
          <i class="c-mark__shape" data-kind="ask" aria-hidden="true"></i>
        </span>
        <span class="c-legend__text">我的提问</span>
        <span class="c-legend__text c-legend__text--short">提问</span>
      </span>
    </div>

    <div class="c-hint" :class="{ 'is-open': hintOpen }">
      <button
        type="button"
        class="c-hint__line"
        data-action="hotkeys"
        :aria-expanded="hintOpen"
        aria-describedby="hotkey-panel"
        @click="hintOpen = !hintOpen"
      >
        <span class="c-hint__label">空格 播放 · ←→ 逐步 ·</span><kbd>?</kbd><span class="c-hint__label"> 全部</span>
      </button>
      <ul id="hotkey-panel" class="c-hint__panel" role="list">
        <li v-for="item in HOTKEYS" :key="item.keys">
          <kbd>{{ item.keys }}</kbd><span>{{ item.text }}</span>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import { usePlaybackStore, type PlaybackSpeed } from '../../stores/playback'
import { useReducedMotion } from '../../composables/useReducedMotion'
import { OP_LABEL } from '../../data/glossary'
import type { TraceStep } from '../../engine/trace'
import { roundBoundaries, roundSegments } from '../../utils/rounds'

const props = defineProps<{
  steps: readonly TraceStep[]
}>()

const playback = usePlaybackStore()
const { reduced, toggle: toggleReduced } = useReducedMotion()

/** 倍速只改步间隔（1600 / 800 / 400ms），不改单步动效时长 */
const SPEEDS: readonly PlaybackSpeed[] = [0.5, 1, 2]

/** 悬停展开的 8 条快捷键；完整清单仍在 `?` 弹窗里 */
const HOTKEYS = [
  { keys: '空格', text: '播放 / 暂停' },
  { keys: '← →', text: '上一步 / 下一步' },
  { keys: 'Shift + ← →', text: '上一轮 / 下一轮' },
  { keys: 'Home / End', text: '首步 / 末步' },
  { keys: '[ ]', text: '上一个 / 下一个标记' },
  { keys: 'Enter', text: '单元格 / 标记详情' },
  { keys: 'A', text: '聚焦提问框' },
  { keys: 'P / E', text: '演示模式 / 导出 trace' },
] as const

const trackEl = ref<HTMLElement | null>(null)
const dragging = ref(false)
const hoverIndex = ref<number | null>(null)
const hintOpen = ref(false)

let dragPointer: number | null = null
let frame = 0
let pendingX: number | null = null

const total = computed(() => props.steps.length)
const segments = computed(() => roundSegments(props.steps))
const boundaries = computed(() => roundBoundaries(segments.value, total.value))
const ratio = computed(() =>
  total.value === 0 ? '0%' : `${(playback.currentStep / total.value) * 100}%`,
)

function roundOf(index: number): number {
  return props.steps[index - 1]?.round ?? 0
}

function opOf(index: number): string {
  return OP_LABEL[props.steps[index - 1]?.op ?? ''] ?? ''
}

function describe(index: number): string {
  if (index === 0) return `第 0 步 · 初始状态`
  const round = roundOf(index)
  const op = opOf(index)
  return `第 ${index} 步 · 第 ${round} 轮 ${op}`.trim()
}

const tipText = computed(() => (hoverIndex.value === null ? '' : describe(hoverIndex.value)))

const progressText = computed(() => {
  const index = playback.currentStep
  const head = `第 ${index} 步，共 ${total.value} 步`
  if (index === 0) return `${head}，初始轮密钥加`
  return `${head}，第 ${roundOf(index)} 轮 ${opOf(index)}`.trim()
})

/** tooltip 夹在两端，避免溢出到窗口外 */
const tipPos = computed(() => {
  const index = hoverIndex.value
  if (index === null || total.value === 0) return '0%'
  const ratioNow = index / total.value
  return `${Math.min(Math.max(ratioNow * 100, 9), 91)}%`
})

function indexFromClientX(clientX: number): number {
  const el = trackEl.value
  if (!el) return playback.currentStep
  const rect = el.getBoundingClientRect()
  if (rect.width === 0) return playback.currentStep
  const next = Math.round(((clientX - rect.left) / rect.width) * total.value)
  return Math.max(0, Math.min(total.value, next))
}

function seek(index: number): void {
  playback.setStep(index)
}

function onSeekDown(event: PointerEvent): void {
  if (event.pointerType === 'mouse' && event.button !== 0) return
  // 拖动即暂停：松手后停在目标步，不会继续往前跑
  playback.pause()
  dragging.value = true
  dragPointer = event.pointerId
  hoverIndex.value = indexFromClientX(event.clientX)
  seek(hoverIndex.value)
  ;(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId)
  event.preventDefault()
}

function onSeekMove(event: PointerEvent): void {
  const index = indexFromClientX(event.clientX)
  hoverIndex.value = index
  if (!dragging.value || event.pointerId !== dragPointer) return

  // pointermove 频率远高于渲染：一帧只提交一次
  pendingX = index
  if (frame !== 0) return
  frame = requestAnimationFrame(() => {
    frame = 0
    if (pendingX !== null) seek(pendingX)
    pendingX = null
  })
}

function onSeekUp(event: PointerEvent): void {
  if (!dragging.value || event.pointerId !== dragPointer) return
  if (frame !== 0) {
    cancelAnimationFrame(frame)
    frame = 0
  }
  if (pendingX !== null) {
    seek(pendingX)
    pendingX = null
  }
  dragging.value = false
  dragPointer = null
  const target = event.currentTarget as HTMLElement
  if (target.hasPointerCapture(event.pointerId)) target.releasePointerCapture(event.pointerId)
}

function onSeekLeave(): void {
  if (!dragging.value) hoverIndex.value = null
}

function onSeekKey(event: KeyboardEvent): void {
  let next = playback.currentStep

  switch (event.key) {
    case 'ArrowLeft':
    case 'ArrowDown':
      next -= 1
      break
    case 'ArrowRight':
    case 'ArrowUp':
      next += 1
      break
    case 'PageUp':
      next = segments.value.find((segment) => segment.start < playback.currentStep)?.start ?? 0
      break
    case 'PageDown': {
      const ahead = segments.value.find((segment) => segment.start > playback.currentStep)
      next = ahead ? ahead.start : total.value
      break
    }
    case 'Home':
      next = 0
      break
    case 'End':
      next = total.value
      break
    default:
      return
  }

  event.preventDefault()
  playback.pause()
  seek(next)
}

function jumpFirst(): void {
  playback.pause()
  playback.first()
}

function jumpLast(): void {
  playback.pause()
  playback.last()
}

function stepPrev(): void {
  playback.pause()
  playback.prev()
}

function stepNext(): void {
  playback.pause()
  playback.next()
}

onBeforeUnmount(() => {
  if (frame !== 0) cancelAnimationFrame(frame)
})
</script>

<style scoped>
.c-transport {
  height: 40px;
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: 0 12px;
  box-sizing: border-box;
}

/* ---------- 传输按钮：内联 SVG，投影下也是矢量 ---------- */
.c-transport__ctrl {
  display: flex;
  align-items: center;
  gap: 2px;
  flex: none;
}

.c-transport__btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 28px;
  padding: 0;
  border: var(--rule-region-w) solid transparent;
  border-radius: var(--r-control);
  background: transparent;
  color: var(--ink-2);
  cursor: pointer;
  transition: background-color var(--d-1) var(--e-linear), color var(--d-1) var(--e-linear);
}

.c-transport__btn svg {
  width: 20px;
  height: 20px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.5;
  stroke-linejoin: round;
  stroke-linecap: round;
}

.c-transport__btn:hover {
  background: var(--surface-inset);
  color: var(--ink-1);
}

.c-transport__btn:active {
  background: var(--accent-soft);
}

.c-transport__btn:focus-visible {
  outline: var(--focus-ring-w) solid var(--focus-ring-color);
  outline-offset: var(--focus-ring-offset);
}

.c-transport__btn--play {
  width: 38px;
  border-color: var(--accent);
  color: var(--accent-strong);
  margin: 0 2px;
}

.c-transport__btn--play:hover {
  background: var(--accent-soft);
  color: var(--accent-strong);
}

.c-transport__btn--play.is-playing {
  background: var(--accent-soft);
}

/* 禁用态保持尺寸与边框，只减不透明度：不出现宽度跳动 */
.c-transport__btn.is-off {
  opacity: 0.4;
  pointer-events: none;
}

/* ---------- 进度条 ---------- */
.c-progress {
  position: relative;
  flex: 1 1 auto;
  min-width: 96px;
  height: 20px;
  display: flex;
  align-items: center;
  cursor: pointer;
  touch-action: none;
}

.c-progress__track {
  position: relative;
  width: 100%;
  height: var(--progress-h);
  border-radius: 1px;
  background: var(--surface-inset);
  box-shadow: inset 0 0 0 1px var(--line-hairline);
}

.c-progress__fill {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: var(--accent);
  transition: width var(--d-2) var(--e-out-quart);
}

.c-progress.is-dragging .c-progress__fill {
  transition: none;
}

.c-progress__split {
  position: absolute;
  top: -2px;
  bottom: -2px;
  width: 1px;
  margin-left: -0.5px;
  background: var(--paper-0);
  box-shadow: 0 0 0 0.5px var(--paper-0);
}

.c-progress__cursor {
  position: absolute;
  top: -3px;
  width: 2px;
  height: calc(var(--progress-h) + 6px);
  margin-left: -1px;
  border-radius: 1px;
  background: var(--ink-1);
  /* 白边：游标压在已完成的强调色上时仍然分得清 */
  box-shadow: 0 0 0 1px var(--paper-0);
  transition: left var(--d-2) var(--e-out-quart);
}

.c-progress.is-dragging .c-progress__cursor {
  transition: none;
}

.c-progress:focus-visible {
  outline: none;
}

.c-progress:focus-visible .c-progress__track {
  box-shadow:
    inset 0 0 0 1px var(--line-default),
    0 0 0 var(--focus-ring-w) var(--focus-ring-color);
}

.c-progress__tip {
  position: absolute;
  bottom: calc(100% + 6px);
  z-index: 60;
  padding: 3px var(--sp-2);
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  background: var(--paper-0);
  box-shadow: var(--shadow-float);
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  line-height: 1.2;
  color: var(--ink-1);
  white-space: nowrap;
  transform: translateX(-50%);
  pointer-events: none;
}

/* ---------- 步号 ---------- */
.c-transport__stepno {
  flex: none;
  min-width: 56px;
  display: flex;
  align-items: baseline;
  gap: 3px;
  font-family: var(--font-mono);
  font-size: var(--fs-label);
  font-variant-numeric: tabular-nums;
  color: var(--ink-3);
}

.c-transport__stepno b {
  font-weight: 600;
  color: var(--ink-1);
}

/* ---------- 倍速分段 ---------- */
.c-speed {
  flex: none;
  display: flex;
  align-items: stretch;
  height: 26px;
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  overflow: hidden;
}

.c-speed__opt {
  min-width: 34px;
  padding: 0 var(--sp-1);
  border: 0;
  border-left: var(--rule-region-w) solid var(--line-hairline);
  background: transparent;
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  font-variant-numeric: tabular-nums;
  color: var(--ink-3);
  cursor: pointer;
}

.c-speed__opt:first-child {
  border-left: 0;
}

.c-speed__opt:hover {
  background: var(--surface-inset);
  color: var(--ink-1);
}

.c-speed__opt[aria-pressed="true"] {
  background: var(--accent-soft);
  color: var(--accent-strong);
  font-weight: 600;
}

.c-speed__opt:focus-visible {
  outline: var(--focus-ring-w) solid var(--focus-ring-color);
  outline-offset: -2px;
}

/* ---------- 动效开关 ---------- */
.c-transport__ghost {
  flex: none;
  height: 26px;
  padding: 0 var(--sp-2);
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  background: transparent;
  font-family: var(--font-ui);
  font-size: var(--fs-label);
  color: var(--ink-3);
  cursor: pointer;
}

.c-transport__ghost:hover {
  color: var(--ink-1);
  border-color: var(--line-default);
}

.c-transport__ghost[aria-pressed="true"] {
  border-color: var(--accent);
  color: var(--accent-strong);
}

/* ---------- 图例 ---------- */
.c-transport__legend {
  flex: none;
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding-right: 2px;
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

.c-legend__text--short {
  display: none;
}

/* ---------- 快捷键提示：一行常驻，hover / 点击展开 8 条 ---------- */
.c-hint {
  position: relative;
  flex: none;
}

.c-hint__line {
  height: 26px;
  padding: 0 var(--sp-1);
  border: 0;
  border-radius: var(--r-control);
  background: transparent;
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-4);
  white-space: nowrap;
  cursor: default;
}

.c-hint__line:hover,
.c-hint.is-open .c-hint__line {
  color: var(--ink-2);
}

.c-hint__line:focus-visible {
  outline: var(--focus-ring-w) solid var(--focus-ring-color);
  outline-offset: 2px;
}

.c-hint kbd {
  padding: 0 3px;
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: 2px;
  font-family: var(--font-mono);
  font-size: inherit;
  color: var(--ink-2);
}

.c-hint__panel {
  position: absolute;
  right: 0;
  bottom: calc(100% + 8px);
  z-index: 60;
  display: none;
  min-width: 236px;
  margin: 0;
  padding: var(--sp-2) var(--sp-3);
  list-style: none;
  border: var(--rule-region-w) solid var(--line-default);
  border-radius: var(--r-float);
  background: var(--paper-0);
  box-shadow: var(--shadow-float);
}

.c-hint:hover .c-hint__panel,
.c-hint:focus-within .c-hint__panel,
.c-hint.is-open .c-hint__panel {
  display: block;
}

.c-hint__panel li {
  display: flex;
  align-items: baseline;
  gap: var(--sp-2);
  padding: 2px 0;
  font-family: var(--font-ui);
  font-size: var(--fs-micro);
  color: var(--ink-2);
  white-space: nowrap;
}

.c-hint__panel kbd {
  flex: none;
  width: 92px;
  text-align: right;
  color: var(--ink-1);
}

@media (max-height: 780px) {
  .c-transport {
    height: 36px;
  }
}

/* 1280 以下先收提示文字，再收图例文字：按钮与进度条永不被挤没 */
@media (max-width: 79.9375rem) {
  .c-hint__label {
    display: none;
  }
}

@media (max-width: 71.9375rem) {
  .c-legend__text {
    display: none;
  }

  .c-legend__text--short {
    display: inline;
  }

  .c-transport__legend {
    gap: var(--sp-2);
  }
}

[data-mode="present"] .c-transport {
  height: 52px;
}

[data-mode="present"] .c-transport__btn {
  width: 36px;
  height: 32px;
}

[data-mode="present"] .c-transport__btn--play {
  width: 46px;
}
</style>
