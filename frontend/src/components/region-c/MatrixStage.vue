<template>
  <section class="c-matrix">
    <div class="c-matrix__body">
      <div class="c-matrix__colheads" aria-hidden="true">
        <span>c0</span>
        <span>c1</span>
        <span>c2</span>
        <span>c3</span>
      </div>
      <div class="c-matrix__rowheads" aria-hidden="true">
        <span>r0</span>
        <span>r1</span>
        <span>r2</span>
        <span>r3</span>
      </div>
      <div
        ref="gridEl"
        class="c-matrix__grid"
        role="grid"
        aria-rowcount="4"
        aria-colcount="4"
        aria-label="状态矩阵"
        @keydown="onKeydown"
        @keydown.enter.prevent="onCellActivate"
        @click="onCellActivate"
      >
        <StageCanvas ref="canvasEl" />
        <div v-for="row in rows" :key="row.row" class="c-row" role="row">
          <div class="c-row__track">
            <ByteCell
              v-for="slot in row.slots"
              :key="slot.key"
              :index="slot.index"
              :row="slot.row"
              :col="slot.col"
              :active="slot.index >= 0 && activeIndex === slot.index"
              :ghost="slot.ghost"
            />
          </div>
        </div>
      </div>
    </div>

  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, onScopeDispose, ref, watch, watchEffect } from 'vue'
import ByteCell from './ByteCell.vue'
import StageCanvas from './StageCanvas.vue'
import { useMatrixWriter } from '../../composables/useMatrixWriter'
import { useReducedMotion } from '../../composables/useReducedMotion'
import { useRovingGrid } from '../../composables/useRovingGrid'
import { usePlaybackStore } from '../../stores/playback'
import { useUiStore } from '../../stores/ui'
import { useDiagnosisStore } from '../../stores/diagnosis'
import { useQuizStore } from '../../stores/quiz'

const props = defineProps<{
  values: Uint8Array
  op: string
  roundKey: Uint8Array
  changed: readonly number[]
  keyIndices?: readonly number[]
  focusByte?: number | null
}>()

const emit = defineEmits<{
  openDrawer: [byteIndex: number, trigger: HTMLElement]
}>()

const playback = usePlaybackStore()
const ui = useUiStore()
const diagnosis = useDiagnosisStore()
const quiz = useQuizStore()
const { reduced } = useReducedMotion()

const gridEl = ref<HTMLElement | null>(null)
const canvasEl = ref<InstanceType<typeof StageCanvas> | null>(null)
const rows = Array.from({ length: 4 }, (_, row) => ({
  row,
  slots: Array.from({ length: 8 }, (_, slot) => {
    const ghost = slot >= 4
    const col = slot % 4
    return {
      key: `${row}-${slot}`,
      index: ghost ? -1 : col * 4 + row,
      row,
      col,
      ghost,
    }
  }),
}))

function onCellActivate(event: Event): void {
  const target = event.target
  if (!(target instanceof HTMLElement)) return
  const cell = target.closest<HTMLElement>('.c-byte:not([data-ghost="true"])')
  if (!cell) return
  const index = Number(cell.dataset.index)
  if (!Number.isInteger(index) || index < 0 || index > 15) return
  emit('openDrawer', index, cell)
}

const { write, writeColumns, settle, paintFor, clearPaint } = useMatrixWriter(
  () => gridEl.value,
)
const { activeIndex, onKeydown } = useRovingGrid(() => gridEl.value)

let substituteTimer: number | undefined
let substituteAnimations: Animation[] = []
let shiftTimer: number | undefined
let shiftAnimations: Animation[] = []
let mixRaf = 0
let addRoundValueTimer: number | undefined
let addRoundCleanupTimer: number | undefined

function playSubBytes(): void {
  if (reduced.value) return

  const nodes = gridEl.value?.querySelectorAll<HTMLElement>('[data-index]') ?? []
  substituteAnimations.forEach((animation) => animation.cancel())
  substituteAnimations = Array.from(nodes, (cell) => {
    const index = Number(cell.dataset.index ?? 0)
    const col = Math.floor(index / 4)
    return cell.animate(
      [{ transform: 'scaleY(0.94)' }, { transform: 'scaleY(1)' }],
      {
        duration: 60,
        delay: col * 20,
        easing: 'cubic-bezier(0.16, 1, 0.30, 1)',
        fill: 'both',
      },
    )
  })

  window.clearTimeout(substituteTimer)
  substituteTimer = window.setTimeout(() => {
    substituteAnimations.forEach((animation) => animation.cancel())
    substituteAnimations = []
    substituteTimer = undefined
  }, 500)
}

function playShiftRows(values: Uint8Array): void {
  if (reduced.value) {
    write(values)
    return
  }

  const grid = gridEl.value
  const tracks = grid?.querySelectorAll<HTMLElement>('.c-row__track') ?? []
  const cellSize = grid
    ? Number.parseFloat(getComputedStyle(grid).getPropertyValue('--cell-size')) || 62
    : 62
  const gap = grid ? Number.parseFloat(getComputedStyle(grid).gap) || 6 : 6
  const step = cellSize + gap

  shiftAnimations.forEach((animation) => animation.cancel())
  shiftAnimations = []
  const shiftItems: { row: number; animation: Animation }[] = []
  tracks.forEach((track, row) => {
    if (row === 0) return
    const animation = track.animate(
      [
        { transform: 'translateX(0)' },
        { transform: `translateX(-${row * step}px)` },
      ],
      {
        duration: 280,
        delay: row * 40,
        easing: 'cubic-bezier(0.65, 0, 0.35, 1)',
        fill: 'both',
      },
    )
    shiftAnimations.push(animation)
    shiftItems.push({ row, animation })
  })

  shiftItems.forEach(({ row, animation }) => {
    animation.finished
      .then(() => canvasEl.value?.flashRow(row))
      .catch(() => undefined)
  })

  window.clearTimeout(shiftTimer)
  shiftTimer = window.setTimeout(() => {
    shiftAnimations.forEach((animation) => animation.cancel())
    shiftAnimations = []
    write(values)
    shiftTimer = undefined
  }, 280 + 3 * 40 + 30)
}

function playMixColumns(values: Uint8Array): void {
  if (reduced.value) {
    write(values)
    return
  }

  const start = performance.now()
  const written = [false, false, false, false]

  for (let column = 0; column < 4; column++) {
    canvasEl.value?.scanColumn(column, column * 60)
  }

  cancelAnimationFrame(mixRaf)
  const frame = (): void => {
    const elapsed = performance.now() - start
    for (let column = 0; column < 4; column++) {
      if (!written[column] && elapsed >= column * 60 + 280) {
        writeColumns(values, [column])
        written[column] = true
      }
    }

    if (written.some((done) => !done)) {
      mixRaf = requestAnimationFrame(frame)
    } else {
      mixRaf = 0
    }
  }

  mixRaf = requestAnimationFrame(frame)
}

function playAddRoundKey(values: Uint8Array): void {
  const cells = gridEl.value?.querySelectorAll<HTMLElement>('.c-byte:not([data-ghost="true"])') ?? []

  window.clearTimeout(addRoundValueTimer)
  window.clearTimeout(addRoundCleanupTimer)

  if (reduced.value) {
    write(values)
    return
  }

  cells.forEach((cell) => {
    const index = Number(cell.dataset.index ?? 0)
    const key = props.roundKey[index] ?? 0
    const keyEl = cell.querySelector<HTMLElement>('.c-byte__key')
    if (keyEl) keyEl.textContent = key.toString(16).toUpperCase().padStart(2, '0')
    cell.classList.remove('is-add-round')
  })

  requestAnimationFrame(() => {
    cells.forEach((cell) => cell.classList.add('is-add-round'))
  })

  addRoundValueTimer = window.setTimeout(() => {
    write(values)
    addRoundValueTimer = undefined
  }, 280)
  addRoundCleanupTimer = window.setTimeout(() => {
    cells.forEach((cell) => cell.classList.remove('is-add-round'))
    addRoundCleanupTimer = undefined
  }, 480)
}

function clearDiagTarget(): void {
  gridEl.value
    ?.querySelectorAll<HTMLElement>('.c-byte.is-diag-target')
    .forEach((cell) => cell.classList.remove('is-diag-target'))
}

watch(
  () => diagnosis.note,
  (note) => {
    clearDiagTarget()
    if (!note) return
    const cell = gridEl.value?.querySelector<HTMLElement>(
      `.c-byte[data-index="${note.byteIndex}"]`,
    )
    cell?.classList.add('is-diag-target')
  },
)

let gradingPainted = false

const grading = computed(
  () =>
    quiz.overlayArmed &&
    quiz.firstDiff !== null &&
    !quiz.inputMismatch &&
    playback.currentStep === quiz.firstDiff.step_index + 1,
)

watchEffect(
  () => {
    const byte = props.focusByte
    gridEl.value
      ?.querySelectorAll<HTMLElement>('.c-byte.is-selected')
      .forEach((cell) => cell.classList.remove('is-selected'))
    if (byte === null || byte === undefined) return
    gridEl.value
      ?.querySelector<HTMLElement>(`.c-byte[data-index="${byte}"]`)
      ?.classList.add('is-selected')
  },
  { flush: 'post' },
)

watch(
  [grading, () => props.values],
  () => {
    if (grading.value && quiz.firstDiff) {
      gradingPainted = true
      paintFor({
        values: props.values,
        changed: props.changed,
        error: [...quiz.errorBytes],
        downstream: [...quiz.sourceBytes],
        key: props.keyIndices ?? [],
      })
      return
    }
    if (gradingPainted) {
      gradingPainted = false
      clearPaint()
      if (reduced.value) applyStaticCues()
    }
  },
  { immediate: true, flush: 'post' },
)

watch(
  () => playback.currentStep,
  (step) => {
    if (!quiz.overlayArmed || !quiz.firstDiff) return
    if (step !== quiz.firstDiff.step_index + 1) quiz.disarmOverlay()
  },
)

onScopeDispose(() => {
  clearDiagTarget()
  window.clearTimeout(substituteTimer)
  substituteAnimations.forEach((animation) => animation.cancel())
  substituteAnimations = []
  window.clearTimeout(shiftTimer)
  shiftAnimations.forEach((animation) => animation.cancel())
  shiftAnimations = []
  cancelAnimationFrame(mixRaf)
  window.clearTimeout(addRoundValueTimer)
  window.clearTimeout(addRoundCleanupTimer)
})

function clearCues(): void {
  const cells =
    gridEl.value?.querySelectorAll<HTMLElement>('.c-byte:not([data-ghost="true"])') ?? []

  cells.forEach((cell) => {
    cell.classList.remove('is-changed', 'is-cue', 'is-cue-xor')
    cell
      .querySelectorAll<HTMLElement>('.c-byte__corner')
      .forEach((corner) => corner.setAttribute('data-corner', ''))

    const hint = cell.querySelector<HTMLElement>('.c-byte__hint')
    if (hint) hint.textContent = '←1'

    const xor = cell.querySelector<HTMLElement>('.c-byte__sup--xor')
    if (xor) xor.setAttribute('data-active', 'false')
  })
}

function applyStaticCues(): void {
  clearCues()
  if (!reduced.value) return

  const changed = new Set(props.changed)
  const cells =
    gridEl.value?.querySelectorAll<HTMLElement>('.c-byte:not([data-ghost="true"])') ?? []

  cells.forEach((cell) => {
    const index = Number(cell.dataset.index ?? 0)
    const row = Number(cell.dataset.row ?? 0)
    const hint = cell.querySelector<HTMLElement>('.c-byte__hint')

    if (changed.has(index)) {
      cell.classList.add('is-changed')
      cell
        .querySelector<HTMLElement>('.c-byte__corner')
        ?.setAttribute('data-corner', 'tr')
    }

    if (props.op === 'shift_rows' && row > 0) {
      cell.classList.add('is-cue')
      if (hint) hint.textContent = `←${row}`
    }

    if (props.op === 'mix_columns') {
      cell.classList.add('is-cue')
      if (hint) hint.textContent = 'MIX'
    }

    if (props.op === 'add_round_key') {
      cell.classList.add('is-cue-xor')
      cell
        .querySelector<HTMLElement>('.c-byte__sup--xor')
        ?.setAttribute('data-active', 'true')
    }
  })
}

onMounted(() => {
  write(props.values)
  applyStaticCues()
})

watch(
  () => props.values,
  (values) => {
    if (ui.activeChannel === 'tutor') {
      write(values)
      return
    }

    if (reduced.value) {
      write(values)
      applyStaticCues()
      return
    }

    if (props.op === 'shift_rows') {
      playShiftRows(values)
      return
    }
    if (props.op === 'mix_columns') {
      playMixColumns(values)
      return
    }
    if (props.op === 'add_round_key') {
      playAddRoundKey(values)
      return
    }
    write(values)
    if (props.op === 'sub_bytes') playSubBytes()
  },
)

watch(reduced, () => {
  applyStaticCues()
})

function settleCurrentStep(): void {
  const active =
    substituteAnimations.length > 0 ||
    shiftAnimations.length > 0 ||
    mixRaf !== 0 ||
    addRoundValueTimer !== undefined ||
    addRoundCleanupTimer !== undefined
  if (!active) return

  window.clearTimeout(substituteTimer)
  substituteTimer = undefined
  substituteAnimations.forEach((animation) => animation.cancel())
  substituteAnimations = []

  window.clearTimeout(shiftTimer)
  shiftTimer = undefined
  shiftAnimations.forEach((animation) => animation.cancel())
  shiftAnimations = []

  cancelAnimationFrame(mixRaf)
  mixRaf = 0

  window.clearTimeout(addRoundValueTimer)
  window.clearTimeout(addRoundCleanupTimer)
  addRoundValueTimer = undefined
  addRoundCleanupTimer = undefined

  gridEl.value
    ?.querySelectorAll<HTMLElement>('.c-byte.is-add-round')
    .forEach((cell) => cell.classList.remove('is-add-round'))

  canvasEl.value?.clear()
  settle(props.values)
}

watch(
  () => playback.isPlaying,
  (playing) => {
    if (!playing) settleCurrentStep()
  },
)

watch(
  () => ui.activeChannel,
  (channel) => {
    if (channel === 'tutor') settleCurrentStep()
  },
)
</script>

<style scoped>
.c-matrix {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--sp-3);
}

.c-matrix__body {
  display: grid;
  grid-template-columns: auto auto;
  grid-template-rows: auto auto;
  gap: var(--sp-1) var(--sp-2);
}

.c-matrix__colheads {
  grid-column: 2;
  grid-row: 1;
  display: grid;
  grid-template-columns: repeat(4, var(--cell-size));
  gap: var(--cell-gap);
}

.c-matrix__rowheads {
  grid-column: 1;
  grid-row: 2;
  display: grid;
  grid-template-rows: repeat(4, var(--cell-size));
  gap: var(--cell-gap);
}

.c-matrix__colheads span,
.c-matrix__rowheads span {
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  letter-spacing: var(--ls-label);
  color: var(--ink-3);
}

.c-matrix__grid {
  grid-column: 2;
  grid-row: 2;
  position: relative;
  display: flex;
  flex-direction: column;
  gap: var(--cell-gap);
  width: calc(4 * var(--cell-size) + 3 * var(--cell-gap));
  height: calc(4 * var(--cell-size) + 3 * var(--cell-gap));
}

.c-row {
  width: calc(4 * var(--cell-size) + 3 * var(--cell-gap));
  overflow: hidden;
}

.c-row__track {
  display: flex;
  gap: var(--cell-gap);
  width: max-content;
}

/* 演示态：C 区容器 ≥720px 才到 88px；1024 视口回落到 72px。
   档位由容器决定，不由视口媒体查询决定。 */
[data-mode="present"] .c-matrix {
  width: 100%;
  container-type: inline-size;
}

[data-mode="present"] .c-matrix__grid {
  --cell-size: 72px;
}

@container (min-width: 720px) {
  [data-mode="present"] .c-matrix__grid {
    --cell-size: 88px;
  }
}
</style>