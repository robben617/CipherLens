<template>
  <section class="sba" aria-labelledby="sba-title" :data-phase="phase">
    <header class="sba__head">
      <p class="sba__eyebrow">S 盒怎么工作</p>
      <h2 id="sba-title" class="sba__title">取一个字节，查一次表，换回一个新字节。</h2>
      <p class="sba__hint">点任意格子可以指定字节；不点就自动演示 3 次。</p>
    </header>

    <div class="sba__stage">
      <div class="sba__side">
        <p class="sba__label">待加密的 4×4 明文</p>
        <div class="sba__matrix" role="grid" aria-label="待加密的 16 个字节">
          <button
            v-for="cell in cells"
            :key="cell.index"
            type="button"
            class="sba__cell"
            :class="{ 'is-picked': cell.index === selected }"
            :aria-label="`第 ${cell.row + 1} 行第 ${cell.col + 1} 列，字节 ${hex(cell.value)}`"
            @click="pick(cell.index)"
          >
            <span class="sba__old">{{ hex(cell.value) }}</span>
            <span v-if="cell.index === selected && phase === 'writeback'" class="sba__new">
              {{ hex(outputByte) }}
            </span>
          </button>
        </div>
        <p class="sba__note">选中：第 {{ selectedRow + 1 }} 行第 {{ selectedCol + 1 }} 列</p>
      </div>

      <div class="sba__flow" aria-hidden="true">
        <span class="sba__arrow sba__arrow--out" :class="{ 'is-on': phase === 'lookup' }">
          <span class="sba__arrow-glyph" aria-hidden="true">→</span>
          <span class="sba__arrow-word">查表</span>
        </span>
        <span
          class="sba__token sba__token--out"
          :class="{ 'is-on': phase === 'lookup' }"
        >{{ hex(inputByte) }}</span>
        <span class="sba__arrow sba__arrow--back" :class="{ 'is-on': phase === 'writeback' }">
          <span class="sba__arrow-glyph" aria-hidden="true">←</span>
          <span class="sba__arrow-word">写回</span>
        </span>
        <span
          class="sba__token sba__token--back"
          :class="{ 'is-on': phase === 'writeback' }"
        >{{ hex(outputByte) }}</span>
        <span class="sba__flow-label">{{ phaseLabel }}</span>
      </div>

      <div class="sba__side">
        <p class="sba__label">S 盒 · 256 项</p>
        <div class="sba__sboxgrid" aria-hidden="true">
          <div class="sba__colidx">
            <span
              v-for="n in 16"
              :key="`c-${n}`"
              class="sba__idx"
              :class="{ 'is-active': showResult && n - 1 === column }"
            >{{ (n - 1).toString(16).toUpperCase() }}</span>
          </div>
          <div class="sba__rowidx">
            <span
              v-for="n in 16"
              :key="`r-${n}`"
              class="sba__idx"
              :class="{ 'is-active': showResult && n - 1 === row }"
            >{{ (n - 1).toString(16).toUpperCase() }}</span>
          </div>
          <div class="sba__table">
            <span
              v-for="dot in 256"
              :key="dot"
              class="sba__dot"
              :class="{
                'is-row': showResult && Math.floor((dot - 1) / 16) === row,
                'is-col': showResult && (dot - 1) % 16 === column,
                'is-hit': showResult && dot - 1 === row * 16 + column,
              }"
            ></span>
          </div>
        </div>
        <div class="sba__readout" aria-live="polite">
          <span>{{ hex(inputByte) }} → 行 {{ row }} · 列 {{ column }} →</span>
          <strong>{{ showResult ? hex(outputByte) : '—' }}</strong>
        </div>
      </div>
    </div>

    <footer class="sba__foot">
      <p class="sba__status" aria-live="polite">{{ status }}</p>
      <button type="button" class="sba__replay" @click="restart">
        {{ finished ? '再看一次' : '换一个字节' }}
      </button>
    </footer>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { SBOX } from '../../engine/sbox'

type Phase = 'idle' | 'pick' | 'lookup' | 'writeback' | 'settle' | 'done' | 'static'

const ORIGINAL = new Uint8Array([
  0x53, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77,
  0x88, 0x99, 0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0xff,
])
const AUTO_CYCLES = 3
const PICK_MS = 900
const LOOKUP_MS = 1600
const WRITEBACK_MS = 1600
const SETTLE_MS = 900
const PAUSE_MS = 1200

const plain = ref<Uint8Array>(new Uint8Array(ORIGINAL))
const selected = ref(0)
const phase = ref<Phase>('idle')
const inputByte = ref(ORIGINAL[0] ?? 0)
const outputByte = ref(SBOX[ORIGINAL[0] ?? 0] ?? 0)
const cycle = ref(0)
const finished = ref(false)
const reduced = ref(false)

const timers = new Set<number>()
let mediaQuery: MediaQueryList | undefined

const cells = computed(() =>
  Array.from({ length: 16 }, (_, slot) => {
    const row = Math.floor(slot / 4)
    const col = slot % 4
    const index = col * 4 + row
    return { index, row, col, value: plain.value[index] ?? 0 }
  }),
)

const row = computed(() => inputByte.value >> 4)
const column = computed(() => inputByte.value & 0x0f)
const selectedRow = computed(() => selected.value % 4)
const selectedCol = computed(() => Math.floor(selected.value / 4))
const showResult = computed(() =>
  ['lookup', 'writeback', 'settle', 'done'].includes(phase.value),
)

const phaseLabel = computed(() => {
  if (phase.value === 'pick') return '取出字节'
  if (phase.value === 'lookup') return '查表'
  if (phase.value === 'writeback') return '写回'
  if (phase.value === 'settle') return '完成'
  return '4×4 明文'
})

const status = computed(() => {
  if (phase.value === 'pick') {
    return `第 ${selectedRow.value + 1} 行第 ${selectedCol.value + 1} 列的 ${hex(inputByte.value)} 被选中了。`
  }
  if (phase.value === 'lookup') {
    return `${hex(inputByte.value)} 的高 4 位是 ${row.value}，低 4 位是 ${column.value}；到 S 盒第 ${row.value} 行、第 ${column.value} 列取表。`
  }
  if (phase.value === 'writeback') {
    return `S 盒这一格是 ${hex(outputByte.value)}，沿箭头写回第 ${selectedRow.value + 1} 行第 ${selectedCol.value + 1} 列。`
  }
  if (phase.value === 'settle') return '换完了：只换值，位置不动。'
  if (phase.value === 'done') return 'S 盒只做一件事：一个字节进，一个字节出；输入和输出的规律被打乱。'
  return `示例：${hex(inputByte.value)} 在 S 盒第 ${row.value} 行第 ${column.value} 列，得到 ${hex(outputByte.value)}。`
})

function hex(value: number): string {
  return value.toString(16).toUpperCase().padStart(2, '0')
}

function clearTimers(): void {
  timers.forEach((id) => window.clearTimeout(id))
  timers.clear()
}

function schedule(fn: () => void, delay: number): void {
  const id = window.setTimeout(() => {
    timers.delete(id)
    fn()
  }, delay)
  timers.add(id)
}

function pickRandom(exclude: number): number {
  let next = Math.floor(Math.random() * 16)
  if (next === exclude) next = (next + 1 + Math.floor(Math.random() * 15)) % 16
  return next
}

function begin(index: number, auto: boolean): void {
  clearTimers()
  finished.value = false
  selected.value = index
  inputByte.value = plain.value[index] ?? 0
  outputByte.value = SBOX[inputByte.value] ?? 0
  phase.value = 'pick'

  schedule(() => {
    phase.value = 'lookup'
    schedule(() => {
      phase.value = 'writeback'
      schedule(() => {
        const next = new Uint8Array(plain.value)
        next[selected.value] = outputByte.value
        plain.value = next
        phase.value = 'settle'
        schedule(() => {
          cycle.value += 1
          if (auto && cycle.value < AUTO_CYCLES) {
            schedule(() => begin(pickRandom(selected.value), true), PAUSE_MS)
          } else {
            phase.value = 'done'
            finished.value = true
          }
        }, SETTLE_MS)
      }, WRITEBACK_MS)
    }, LOOKUP_MS)
  }, PICK_MS)
}

function pick(index: number): void {
  if (reduced.value) return
  cycle.value = 0
  begin(index, false)
}

function restart(): void {
  plain.value = new Uint8Array(ORIGINAL)
  cycle.value = 0
  selected.value = 0
  inputByte.value = ORIGINAL[0] ?? 0
  outputByte.value = SBOX[inputByte.value] ?? 0
  finished.value = false
  if (reduced.value) {
    phase.value = 'static'
    return
  }
  begin(pickRandom(-1), true)
}

function applyMotionPreference(): void {
  reduced.value = mediaQuery?.matches ?? false
  if (reduced.value) {
    clearTimers()
    phase.value = 'static'
    return
  }
  if (phase.value === 'static') restart()
}

onMounted(() => {
  mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
  mediaQuery.addEventListener('change', applyMotionPreference)
  if (mediaQuery.matches) {
    reduced.value = true
    phase.value = 'static'
    return
  }
  schedule(() => begin(pickRandom(-1), true), 350)
})

onBeforeUnmount(() => {
  clearTimers()
  mediaQuery?.removeEventListener('change', applyMotionPreference)
})
</script>

<style scoped>
.sba {
  max-width: 1000px;
  margin: var(--sp-6) auto 0;
  padding: var(--sp-6);
  border: var(--rule-region-w) solid var(--line-hairline);
  background: var(--paper-1);
}

.sba__head {
  display: grid;
  gap: var(--sp-1);
  margin-bottom: var(--sp-6);
}

.sba__eyebrow {
  margin: 0;
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  letter-spacing: var(--ls-label);
  color: var(--ink-3);
}

.sba__title {
  margin: 0;
  font-family: var(--font-display);
  font-size: var(--fs-h2);
  font-weight: 600;
  line-height: var(--lh-snug);
  color: var(--ink-1);
}

.sba__hint {
  margin: 0;
  font-size: var(--fs-ui);
  color: var(--ink-3);
}

.sba__stage {
  display: grid;
  grid-template-columns: auto 96px auto;
  justify-content: center;
  align-items: center;
  gap: var(--sp-4);
}

.sba__side {
  display: grid;
  justify-items: center;
  gap: var(--sp-2);
  min-width: 0;
}

.sba__label,
.sba__note {
  margin: 0;
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  letter-spacing: var(--ls-label);
  color: var(--ink-3);
}

.sba__matrix {
  display: grid;
  grid-template-columns: repeat(4, clamp(40px, 5.2vw, 64px));
  grid-template-rows: repeat(4, clamp(40px, 5.2vw, 64px));
  gap: 8px;
}

.sba__cell {
  position: relative;
  display: grid;
  place-items: center;
  border: var(--rule-region-w) solid var(--line-default);
  border-radius: var(--r-cell);
  background: var(--paper-0);
  color: var(--ink-1);
  font-family: var(--font-mono);
  font-size: var(--fs-ui);
  font-variant-numeric: tabular-nums;
  cursor: pointer;
  transform-origin: center;
  transition:
    transform 700ms var(--e-out-quart),
    border-color 360ms var(--e-out-quart),
    box-shadow 360ms var(--e-out-quart);
}

.sba__cell:hover {
  border-color: var(--ink-2);
}

.sba__cell.is-picked {
  z-index: 1;
  transform: scale(1.14);
  border-color: var(--accent);
  background: var(--paper-0);
  box-shadow: 0 0 0 2px var(--accent-ring);
}

.sba__old {
  line-height: 1;
}

.sba__new {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  border-radius: inherit;
  background: var(--paper-0);
  line-height: 1;
  color: var(--accent-strong);
  font-weight: 600;
  animation: sba-write 600ms var(--e-out-quart) both;
}

.sba__flow {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--sp-2);
  height: 190px;
}

.sba__arrow {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--accent);
  opacity: 0.35;
  /* 与 token 淡出同为 280ms：箭头和数字同进同出 */
  transition: opacity 280ms var(--e-out-quart);
}

.sba__arrow.is-on {
  opacity: 1;
  /* 亮起跟数字淡入同步（160ms），退场沿用 280ms 与数字淡出一致 */
  transition-duration: 160ms;
}

.sba__arrow-glyph {
  font-family: var(--font-mono);
  font-size: 18px;
  line-height: 1;
}

.sba__arrow-word {
  display: none;
  font-size: var(--fs-micro);
  letter-spacing: 0.04em;
}

.sba__token {
  position: absolute;
  top: 50%;
  left: 50%;
  padding: 2px 6px;
  border-radius: 2px;
  background: var(--accent);
  color: var(--paper-0);
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  letter-spacing: 0.04em;
  opacity: 0;
  pointer-events: none;
  /* 消失：原地淡出 280ms，淡出完成后才不可见地归位，避免数字往回流 */
  transition:
    opacity 280ms var(--e-out-quart),
    transform 0ms linear 280ms;
}

.sba__token--out {
  transform: translate(calc(-50% - 18px), -50%);
}

.sba__token--out.is-on {
  opacity: 1;
  transform: translate(calc(-50% + 34px), -50%);
  transition:
    opacity 160ms var(--e-out-quart),
    transform 900ms cubic-bezier(0.22, 1, 0.36, 1);
}

.sba__token--back {
  background: var(--accent-strong);
  transform: translate(calc(-50% + 18px), -50%);
}

.sba__token--back.is-on {
  opacity: 1;
  transform: translate(calc(-50% - 34px), -50%);
  transition:
    opacity 160ms var(--e-out-quart),
    transform 900ms cubic-bezier(0.22, 1, 0.36, 1);
}

.sba__flow-label {
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  letter-spacing: var(--ls-label);
  color: var(--ink-3);
}

.sba__sboxgrid {
  display: grid;
  grid-template-columns: 12px auto;
  grid-template-rows: 12px auto;
  gap: 3px;
  align-items: center;
  justify-items: center;
}

.sba__colidx {
  grid-column: 2;
  grid-row: 1;
  display: grid;
  grid-template-columns: repeat(16, 8px);
  gap: 1px;
  width: 143px;
}

.sba__rowidx {
  grid-column: 1;
  grid-row: 2;
  display: grid;
  grid-template-rows: repeat(16, 8px);
  gap: 1px;
  height: 143px;
  align-items: center;
  justify-items: end;
}

.sba__idx {
  font-family: var(--font-mono);
  font-size: 6px;
  line-height: 1;
  color: var(--ink-3);
  transition: color 600ms var(--e-out-quart);
}

.sba__idx.is-active {
  color: var(--accent-strong);
  font-weight: 700;
}

.sba__table {
  grid-column: 2;
  grid-row: 2;
  display: grid;
  grid-template-columns: repeat(16, 8px);
  grid-template-rows: repeat(16, 8px);
  gap: 1px;
  padding: 4px;
  border: var(--rule-region-w) solid var(--line-hairline);
  background: var(--paper-0);
}

.sba__dot {
  width: 8px;
  height: 8px;
  background: var(--line-hairline);
  transition: background 600ms var(--e-out-quart), transform 600ms var(--e-out-quart);
}

.sba__dot.is-row,
.sba__dot.is-col {
  background: var(--accent-soft);
}

.sba__dot.is-hit {
  background: var(--accent);
  transform: scale(1.4);
}

.sba__readout {
  display: flex;
  align-items: baseline;
  gap: var(--sp-2);
  min-height: 22px;
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

.sba__readout strong {
  font-size: var(--fs-ui);
  color: var(--accent-strong);
}

.sba__foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-4);
  margin-top: var(--sp-6);
  padding-top: var(--sp-4);
  border-top: var(--rule-region-w) solid var(--line-hairline);
}

.sba__status {
  margin: 0;
  max-width: 52rem;
  font-size: var(--fs-ui);
  line-height: 1.65;
  color: var(--ink-2);
}

.sba__replay {
  flex: none;
  height: 32px;
  padding: 0 var(--sp-3);
  border: var(--rule-region-w) solid var(--line-strong);
  border-radius: var(--r-control);
  background: transparent;
  font-size: var(--fs-ui);
  color: var(--ink-1);
  cursor: pointer;
}

.sba__replay:hover {
  border-color: var(--accent);
  color: var(--accent-strong);
}

@keyframes sba-write {
  from {
    opacity: 0;
    transform: translateY(7px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 900px) {
  .sba {
    padding: var(--sp-4);
  }

  .sba__stage {
    grid-template-columns: minmax(0, 1fr);
    gap: var(--sp-2);
  }

  .sba__flow {
    height: 84px;
    gap: 4px;
  }

  .sba__arrow {
    flex-direction: column;
    gap: 1px;
  }

  .sba__arrow-glyph {
    transform: rotate(90deg);
    font-size: 16px;
  }

  .sba__arrow-word {
    display: inline;
  }

  .sba__token {
    display: none;
  }

  .sba__foot {
    align-items: flex-start;
    flex-direction: column;
  }
}

@media (prefers-reduced-motion: reduce) {
  .sba__cell,
  .sba__arrow,
  .sba__token,
  .sba__dot {
    transition: none;
  }
}
</style>