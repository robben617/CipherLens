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
    <button class="c-matrix__debug" data-debug-next type="button" @click="$emit('next')">
      →
    </button>
  </section>
</template>

<script setup lang="ts">
import { onMounted, onScopeDispose, ref, watch } from 'vue'
import ByteCell from './ByteCell.vue'
import StageCanvas from './StageCanvas.vue'
import { useMatrixWriter } from '../../composables/useMatrixWriter'
import { useRovingGrid } from '../../composables/useRovingGrid'

const props = defineProps<{
  values: Uint8Array
  op: string
}>()

defineEmits<{
  next: []
}>()

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

const { write, writeColumns } = useMatrixWriter(() => gridEl.value)
const { activeIndex, onKeydown } = useRovingGrid(() => gridEl.value)

let substituteTimer: number | undefined
let substituteAnimations: Animation[] = []
let shiftTimer: number | undefined
let shiftAnimations: Animation[] = []
let mixRaf = 0

function prefersReducedMotion(): boolean {
  return (
    window.matchMedia('(prefers-reduced-motion: reduce)').matches ||
    document.documentElement.dataset.motion === 'reduced'
  )
}

function playSubBytes(): void {
  if (prefersReducedMotion()) return

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
  }, 500)
}

function playShiftRows(values: Uint8Array): void {
  if (prefersReducedMotion()) {
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
  }, 280 + 3 * 40 + 30)
}

function playMixColumns(values: Uint8Array): void {
  if (prefersReducedMotion()) {
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

onScopeDispose(() => {
  window.clearTimeout(substituteTimer)
  substituteAnimations.forEach((animation) => animation.cancel())
  substituteAnimations = []
  window.clearTimeout(shiftTimer)
  shiftAnimations.forEach((animation) => animation.cancel())
  shiftAnimations = []
  cancelAnimationFrame(mixRaf)
})

onMounted(() => {
  write(props.values)
})

watch(
  () => props.values,
  (values) => {
    if (props.op === 'shift_rows') {
      playShiftRows(values)
      return
    }
    if (props.op === 'mix_columns') {
      playMixColumns(values)
      return
    }
    write(values)
    if (props.op === 'sub_bytes') playSubBytes()
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

.c-matrix__debug {
  font-family: var(--font-ui);
  font-size: var(--fs-label);
  color: var(--ink-2);
  background: transparent;
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  padding: var(--sp-1) var(--sp-3);
}
</style>