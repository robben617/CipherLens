<template>
  <section class="avi" :data-phase="phase" aria-labelledby="avi-title">
    <header class="avi__head">
      <p class="avi__eyebrow">AVALANCHE EFFECT · 4 STEPS</p>
      <h2 id="avi-title" class="avi__title">雪崩效应，四步看懂</h2>
      <p class="avi__lede">明文只改 1 位，密文大约一半的位会变。</p>
    </header>

    <ol class="avi__steps" aria-label="演示步骤">
      <li
        v-for="(label, index) in STEPS"
        :key="label"
        class="avi__step"
        :class="{ 'is-active': activeStep === index, 'is-done': activeStep > index }"
      >
        <span class="avi__step-no">{{ index + 1 }}</span>
        <span class="avi__step-label">{{ label }}</span>
      </li>
    </ol>

    <div class="avi__stage">
      <div class="avi__rain" aria-hidden="true">
        <span
          v-for="(column, index) in rainColumns"
          :key="index"
          :style="{ '--avi-delay': `${(index % 7) * 0.23}s`, '--avi-duration': `${2.8 + (index % 5) * 0.25}s` }"
        >{{ column }}</span>
      </div>

      <div class="avi__panels" :class="{ 'is-running': phase === 'running' }">
        <figure class="avi__panel">
          <figcaption>{{ panelALabel }}</figcaption>
          <canvas ref="canvasA" width="512" height="512" :aria-label="`${panelALabel}的雪花屏`"></canvas>
        </figure>
        <figure class="avi__panel">
          <figcaption>{{ panelBLabel }}</figcaption>
          <canvas ref="canvasB" width="512" height="512" :aria-label="`${panelBLabel}的雪花屏`"></canvas>
        </figure>
      </div>

      <p v-if="phase === 'running'" class="avi__round">
        第 {{ round }} / {{ ROUNDS }} 轮
        <span v-if="round < 4"> · 差异扩散中</span>
        <span v-else> · 差异 {{ roundDiffs[round] ?? 0 }} / 128 位</span>
      </p>
      <p v-if="phase === 'running' && round === 4" class="avi__burst">第 4 轮 · 列混合发力</p>
      <p v-if="phase === 'idle'" class="avi__idle-note">按下 Enter 或点“开始加密”</p>
    </div>

    <p class="avi__narration" :class="{ 'is-final': phase === 'final' }" aria-live="polite">
      {{ narration }}
    </p>
    <p v-if="phase === 'final' || (phase === 'running' && round >= 4)" class="avi__legend">
      青 = 1 · 深灰 = 0 · 红 = 左右不同的位
    </p>

    <footer class="avi__foot">
      <div class="avi__buttons">
        <button
          type="button"
          class="avi__go avi__go--ghost"
          data-avi-action="reset"
          :disabled="phase === 'idle'"
          @click="reset"
        >
          重置
        </button>
        <button
          type="button"
          class="avi__go"
          data-avi-action="start"
          :disabled="phase === 'running'"
          @click="handleAction"
        >
          开始演示
        </button>
      </div>
      <p v-if="phase === 'final'" class="avi__stats" data-avi-stats>
        差异 <b>{{ diffBits }}</b> / 128 位 · <b>{{ rate }}%</b>
      </p>
      <p v-else class="avi__hint">
        {{ phase === 'running' ? '演示中…' : '按 Enter 开始演示' }}
      </p>
    </footer>

    <p class="avi__disclaimer">
      画面为 64×64 放大示意；差异位数由真实 AES-128 对同一密钥、仅改 1 位的两组明文现算。
    </p>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { buildTrace } from '../../engine/trace'

type Phase = 'idle' | 'running' | 'final'

const STEPS = ['静谧初始', '开始加密', '雪崩瞬间', '差异高亮']
const ROUNDS = 10
const ROUND_MS = 420
const GRID = 64
const CANVAS = 512
const CELL = CANVAS / GRID

const PLAIN_HEX = '00112233445566778899aabbccddeeff'
const KEY_HEX = '000102030405060708090a0b0c0d0e0f'

const phase = ref<Phase>('idle')
const round = ref(0)
const canvasA = ref<HTMLCanvasElement | null>(null)
const canvasB = ref<HTMLCanvasElement | null>(null)
let timer: number | undefined
let mediaQuery: MediaQueryList | undefined

function hexBytes(value: string): Uint8Array {
  const out = new Uint8Array(value.length / 2)
  for (let i = 0; i < out.length; i += 1) out[i] = Number.parseInt(value.slice(i * 2, i * 2 + 2), 16)
  return out
}

function bytesToHex(value: Uint8Array): string {
  return Array.from(value, (byte) => byte.toString(16).padStart(2, '0')).join('')
}

const plainA = hexBytes(PLAIN_HEX)
const plainB = plainA.slice()
plainB[15] = (plainB[15] ?? 0) ^ 0x01

const traceA = buildTrace({ plaintext: bytesToHex(plainA), key: KEY_HEX, mode: 'encrypt' })
const traceB = buildTrace({ plaintext: bytesToHex(plainB), key: KEY_HEX, mode: 'encrypt' })

function collectStates(trace: typeof traceA, initial: Uint8Array): Uint8Array[] {
  const states: Uint8Array[] = [initial.slice()]
  for (let roundIndex = 1; roundIndex <= ROUNDS; roundIndex += 1) {
    const endIndex = roundIndex === ROUNDS ? trace.steps.length - 1 : roundIndex * 4
    const step = trace.steps[endIndex]
    states.push(new Uint8Array(step?.state_after ?? initial))
  }
  return states
}

const statesA = collectStates(traceA, plainA)
const statesB = collectStates(traceB, plainB)

function hamming(a: Uint8Array, b: Uint8Array): number {
  let count = 0
  for (let i = 0; i < a.length; i += 1) {
    let value = (a[i] ?? 0) ^ (b[i] ?? 0)
    while (value) {
      value &= value - 1
      count += 1
    }
  }
  return count
}

const diffBits = hamming(statesA[ROUNDS] ?? plainA, statesB[ROUNDS] ?? plainB)
const rate = ((diffBits / 128) * 100).toFixed(1)
const roundDiffs = statesA.map((state, index) => hamming(state, statesB[index] ?? state))

function makeField(state: Uint8Array, salt: number): Uint8Array {
  let seed = 2166136261 ^ salt
  for (const byte of state) {
    seed ^= byte
    seed = Math.imul(seed, 16777619)
  }
  seed ||= 1
  const field = new Uint8Array(GRID * GRID)
  for (let i = 0; i < field.length; i += 1) {
    seed ^= seed << 13
    seed ^= seed >>> 17
    seed ^= seed << 5
    field[i] = (seed >>> 0) & 1
  }
  return field
}

const fieldsA = statesA.map((state, index) => makeField(state, 0x6a09e667 ^ index))
const fieldsB = statesB.map((state, index) => makeField(state, 0xbb67ae85 ^ index))

const ring = (() => {
  const field = new Uint8Array(GRID * GRID)
  const center = (GRID - 1) / 2
  for (let y = 0; y < GRID; y += 1) {
    for (let x = 0; x < GRID; x += 1) {
      const distance = Math.abs(x - center) + Math.abs(y - center)
      if ((distance >= 19 && distance <= 23) || (distance >= 28 && distance <= 29)) {
        field[y * GRID + x] = 1
      }
    }
  }
  return field
})()

function blend(base: Uint8Array, noise: Uint8Array, ratio: number): Uint8Array {
  const out = new Uint8Array(base.length)
  const threshold = Math.round(ratio * 100)
  for (let i = 0; i < out.length; i += 1) {
    out[i] = i % 100 < threshold ? (noise[i] ?? 0) : (base[i] ?? 0)
  }
  return out
}

function canvasContext(canvas: HTMLCanvasElement | null): CanvasRenderingContext2D | null {
  return canvas?.getContext('2d') ?? null
}

function paintField(ctx: CanvasRenderingContext2D | null, field: Uint8Array, initial = false): void {
  if (!ctx) return
  ctx.fillStyle = '#050b14'
  ctx.fillRect(0, 0, CANVAS, CANVAS)
  ctx.fillStyle = initial ? '#6fe8d8' : '#8bf3e6'
  for (let i = 0; i < field.length; i += 1) {
    if (field[i] !== 1) continue
    const x = i % GRID
    const y = Math.floor(i / GRID)
    ctx.fillRect(x * CELL, y * CELL, CELL, CELL)
  }
}

function paintCipher(ctx: CanvasRenderingContext2D | null, field: Uint8Array, compare: Uint8Array | null = null): void {
  if (!ctx) return
  for (let i = 0; i < GRID * GRID; i += 1) {
    const x = i % GRID
    const y = Math.floor(i / GRID)
    if (compare && field[i] !== compare[i]) ctx.fillStyle = '#ff3b6b'
    else if (field[i] === 1) ctx.fillStyle = '#8bf3e6'
    else ctx.fillStyle = '#182234'
    ctx.fillRect(x * CELL, y * CELL, CELL, CELL)
  }
}

function drawInitial(): void {
  paintField(canvasContext(canvasA.value), ring, true)
  paintField(canvasContext(canvasB.value), ring, true)
}

function drawRound(value: number): void {
  const ratios = [0.12, 0.3, 0.55]
  const ratio = value <= 3 ? (ratios[value - 1] ?? 0) : 1
  const a = blend(ring, fieldsA[value] ?? ring, ratio)
  const b = blend(ring, fieldsB[value] ?? ring, ratio)
  if (value >= 4) {
    paintCipher(canvasContext(canvasA.value), fieldsA[value] ?? ring)
    paintCipher(canvasContext(canvasB.value), fieldsB[value] ?? ring, fieldsA[value] ?? ring)
    return
  }
  paintField(canvasContext(canvasA.value), a)
  paintField(canvasContext(canvasB.value), b)
}

function drawFinal(): void {
  const a = fieldsA[ROUNDS] ?? ring
  const b = fieldsB[ROUNDS] ?? ring
  paintCipher(canvasContext(canvasA.value), a)
  paintCipher(canvasContext(canvasB.value), b, a)
}

const activeStep = computed(() => {
  if (phase.value === 'final') return 3
  if (phase.value === 'running') return round.value < 4 ? 1 : 2
  return 0
})

const panelALabel = computed(() => {
  if (phase.value === 'final') return '原始密文（青 = 1）'
  if (phase.value === 'running' && round.value >= 4) return '原始状态（青 = 1）'
  if (phase.value === 'running') return '加密中'
  return '原始明文'
})

const panelBLabel = computed(() => {
  if (phase.value === 'final') return '改 1 位后的密文（红 = 不同）'
  if (phase.value === 'running' && round.value >= 4) return '改 1 位后的状态（红 = 不同）'
  if (phase.value === 'running') return '加密中'
  return '只改 1 位'
})

const narration = computed(() => {
  if (phase.value === 'idle') {
    return '左边是原始明文，右边是仅修改了 1 个比特的明文。肉眼完全看不出任何区别。按下 Enter，开始加密。'
  }
  if (phase.value === 'running' && round.value < 4) {
    return `第 ${round.value} 轮：两边看起来还很相似，但差异已经在扩散……`
  }
  if (phase.value === 'running') {
    return `第 ${round.value} 轮：列混合已经发力，两边崩解成互不重合的雪花屏；右边红点就是两边不同的位。`
  }
  return `这就是雪崩效应：左边的 1 个比特变化，经过 10 轮行移位和列混合，最终有 ${diffBits} / 128 位（${rate}%）彻底不同。哪怕动一粒灰尘，结果也是天翻地覆。`
})


function clearTimer(): void {
  if (timer !== undefined) window.clearTimeout(timer)
  timer = undefined
}

function finish(): void {
  phase.value = 'final'
  round.value = ROUNDS
  drawFinal()
}

function start(): void {
  if (phase.value === 'running') return
  clearTimer()
  if (mediaQuery?.matches) {
    finish()
    return
  }
  phase.value = 'running'
  round.value = 0
  const tick = (): void => {
    round.value += 1
    drawRound(round.value)
    if (round.value >= ROUNDS) {
      timer = window.setTimeout(finish, 650)
      return
    }
    timer = window.setTimeout(tick, ROUND_MS)
  }
  timer = window.setTimeout(tick, 260)
}

function reset(): void {
  clearTimer()
  phase.value = 'idle'
  round.value = 0
  drawInitial()
}

function handleAction(): void {
  if (phase.value === 'running') return
  if (phase.value === 'final') {
    reset()
    start()
    return
  }
  start()
}

function onKey(event: KeyboardEvent): void {
  if (event.key !== 'Enter') return
  const target = event.target as HTMLElement | null
  if (target && ['INPUT', 'TEXTAREA', 'SELECT', 'BUTTON', 'A'].includes(target.tagName)) return
  if (phase.value === 'running') return
  event.preventDefault()
  handleAction()
}

const rainColumns = Array.from({ length: 16 }, (_, column) => {
  let seed = column * 977 + 41
  let text = ''
  for (let i = 0; i < 24; i += 1) {
    seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0
    text += (seed >>> 27) & 1 ? '1' : '0'
  }
  return text
})

onMounted(async () => {
  mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
  await nextTick()
  drawInitial()
  window.addEventListener('keydown', onKey)
})

onBeforeUnmount(() => {
  clearTimer()
  window.removeEventListener('keydown', onKey)
})
</script>

<style scoped>
.avi {
  margin-top: var(--sp-6);
  padding: var(--sp-4);
  border: var(--rule-region-w) solid var(--line-hairline);
  background: #050b14;
  color: #d9e6f2;
}

.avi__head {
  display: grid;
  gap: var(--sp-1);
}

.avi__eyebrow {
  margin: 0;
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.22em;
  color: #2effb0;
}

.avi__title {
  margin: 0;
  font-family: var(--font-display);
  font-size: var(--fs-h2);
  font-weight: 600;
  line-height: var(--lh-snug);
  color: #f1f7ff;
}

.avi__lede {
  margin: 0;
  font-size: var(--fs-ui);
  color: #8fa6c2;
}

.avi__steps {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: var(--sp-4) 0 var(--sp-3);
  padding: 0;
  list-style: none;
}

.avi__step {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border: 1px solid #23334d;
  color: #6f86a5;
  font-family: var(--font-mono);
  font-size: 10px;
  transition: color 240ms, border-color 240ms, background 240ms;
}

.avi__step.is-active {
  border-color: #2effb0;
  background: rgba(46, 255, 176, 0.1);
  color: #d6fff1;
}

.avi__step.is-done {
  border-color: #45607f;
  color: #9bb1c8;
}

.avi__step-no {
  display: grid;
  place-items: center;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #1a293d;
  color: #8fa6c2;
  font-size: 9px;
}

.avi__step.is-active .avi__step-no {
  background: #2effb0;
  color: #04100a;
}

.avi__stage {
  position: relative;
  overflow: hidden;
  padding: var(--sp-4);
  border: 1px solid #17263c;
  background: #040810;
}

.avi__rain {
  position: absolute;
  inset: 0;
  display: flex;
  justify-content: space-around;
  overflow: hidden;
  pointer-events: none;
  opacity: 0.28;
  transition: opacity 500ms;
}

.avi[data-phase="running"] .avi__rain {
  opacity: 0.72;
}

.avi__rain span {
  display: block;
  color: #45ffb4;
  font-family: var(--font-mono);
  font-size: 10px;
  line-height: 1.5;
  white-space: pre;
  text-shadow: 0 0 6px rgba(46, 255, 176, 0.5);
  transform: translateY(-42%);
  animation: avi-rain var(--avi-duration) linear infinite;
  animation-delay: var(--avi-delay);
}

.avi__panels {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: center;
  gap: var(--sp-6);
}

.avi__panels::after {
  content: '';
  position: absolute;
  z-index: 0;
  top: 12%;
  bottom: 12%;
  left: 50%;
  width: 1px;
  background: #23334d;
  pointer-events: none;
}

.avi__panels.is-running {
  animation: avi-jitter 180ms steps(2) infinite;
}

.avi__panel {
  flex: 0 1 280px;
  display: grid;
  gap: 6px;
  margin: 0;
  text-align: center;
}

.avi__panel figcaption {
  display: inline-block;
  justify-self: center;
  padding: 2px 6px;
  background: #040810;
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.08em;
  color: #aac0d8;
}

.avi__panel canvas {
  display: block;
  width: 100%;
  aspect-ratio: 1;
  border: 1px solid #23334d;
  background: #050b14;
  image-rendering: pixelated;
}

.avi[data-phase="running"] .avi__panel canvas {
  border-color: #2effb0;
  box-shadow: 0 0 24px rgba(46, 255, 176, 0.12);
}

.avi[data-phase="final"] .avi__panel canvas {
  border-color: #ff3b6b;
  box-shadow: 0 0 30px rgba(255, 59, 107, 0.28);
}

.avi__round,
.avi__idle-note {
  position: relative;
  z-index: 1;
  margin: 10px 0 0;
  text-align: center;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.12em;
  color: #cfe0f2;
}

.avi__burst {
  position: absolute;
  z-index: 2;
  top: 50%;
  left: 50%;
  margin: 0;
  transform: translate(-50%, -50%);
  padding: 7px 14px;
  border: 2px solid #ff3b6b;
  background: rgba(4, 8, 16, 0.97);
  color: #ff9ab0;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.12em;
  white-space: nowrap;
  box-shadow: 0 0 24px rgba(255, 59, 107, 0.35);
  animation: avi-burst 700ms var(--e-out-quart) both;
}

.avi__narration {
  min-height: 3.4em;
  margin: var(--sp-4) 0 var(--sp-3);
  font-size: var(--fs-ui);
  line-height: 1.8;
  color: #a9bfd6;
}

.avi__narration.is-final {
  color: #e6f0ff;
  font-weight: 500;
}

.avi__legend {
  margin: -4px 0 var(--sp-3);
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.06em;
  color: #9fb6cf;
}

.avi__foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--sp-3);
  padding-top: var(--sp-3);
  border-top: 1px solid #17263c;
}

.avi__buttons {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-2);
}

.avi__go {
  min-height: 40px;
  padding: 0 var(--sp-4);
  border: 1px solid #2effb0;
  border-radius: 2px;
  background: transparent;
  color: #2effb0;
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 0.08em;
  cursor: pointer;
  transition: background 240ms, color 240ms, border-color 240ms;
}

.avi__go--ghost {
  border-color: #45607f;
  color: #9bb1c8;
}

.avi__go:hover:not(:disabled) {
  background: #2effb0;
  color: #04100a;
}

.avi__go--ghost:hover:not(:disabled) {
  border-color: #6d89a8;
  background: #1a293d;
  color: #d9e6f2;
}

.avi__go:disabled {
  border-color: #23334d;
  color: #5b708b;
  cursor: default;
}

.avi__hint {
  margin: 0;
  font-family: var(--font-mono);
  font-size: 10px;
  color: #6f86a5;
}

.avi__stats {
  margin: 0;
  font-family: var(--font-mono);
  font-size: 13px;
  color: #a9bfd6;
}

.avi__stats b {
  color: #ff5c82;
  font-size: 17px;
}

.avi__disclaimer {
  margin: var(--sp-3) 0 0;
  font-size: 10px;
  line-height: 1.6;
  color: #5b708b;
}

@keyframes avi-rain {
  from { transform: translateY(-42%); }
  to { transform: translateY(42%); }
}

@keyframes avi-jitter {
  0% { transform: translate(0, 0); }
  25% { transform: translate(1.5px, -1px); }
  50% { transform: translate(-1.5px, 1px); }
  75% { transform: translate(1px, 1.5px); }
  100% { transform: translate(0, 0); }
}

@keyframes avi-burst {
  from { opacity: 0; transform: translate(-50%, -50%) scale(0.9); }
  to { opacity: 1; transform: translate(-50%, -50%) scale(1); }
}

@media (max-width: 700px) {
  .avi {
    padding: var(--sp-3);
  }

  .avi__rain {
    opacity: 0.12;
  }

  .avi[data-phase="running"] .avi__rain {
    opacity: 0.4;
  }

  .avi__panels {
    gap: var(--sp-3);
  }

  .avi__panel {
    flex-basis: calc(50% - var(--sp-2));
  }

  .avi__foot {
    align-items: flex-start;
    flex-direction: column;
  }
}

@media (prefers-reduced-motion: reduce) {
  .avi__rain span,
  .avi__panels.is-running,
  .avi__burst {
    animation: none;
  }
}
</style>