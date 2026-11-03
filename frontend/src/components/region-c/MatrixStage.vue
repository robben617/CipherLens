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
        <ByteCell
          v-for="cell in cells"
          :key="cell.index"
          :index="cell.index"
          :row="cell.row"
          :col="cell.col"
          :active="activeIndex === cell.index"
        />
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
const cells = Array.from({ length: 16 }, (_, index) => ({
  index,
  row: index % 4,
  col: Math.floor(index / 4),
}))

const { write } = useMatrixWriter(() => gridEl.value)
const { activeIndex, onKeydown } = useRovingGrid(() => gridEl.value)

let substituteTimer: number | undefined
let substituteAnimations: Animation[] = []

function prefersReducedMotion(): boolean {
  return (
    window.matchMedia('(prefers-reduced-motion: reduce)').matches ||
    document.documentElement.dataset.motion === 'reduced'
  )
}

function playSubBytes(): void {
  if (prefersReducedMotion()) return

  const nodes = gridEl.value?.querySelectorAll<HTMLElement>('.c-byte') ?? []
  substituteAnimations.forEach((animation) => animation.cancel())
  substituteAnimations = Array.from(nodes, (cell, index) =>
    cell.animate(
      [{ transform: 'scaleY(0.94)' }, { transform: 'scaleY(1)' }],
      {
        duration: 60,
        delay: Math.floor(index / 4) * 20,
        easing: 'cubic-bezier(0.16, 1, 0.30, 1)',
        fill: 'both',
      },
    ),
  )

  window.clearTimeout(substituteTimer)
  substituteTimer = window.setTimeout(() => {
    substituteAnimations.forEach((animation) => animation.cancel())
    substituteAnimations = []
  }, 500)
}

onScopeDispose(() => {
  window.clearTimeout(substituteTimer)
  substituteAnimations.forEach((animation) => animation.cancel())
  substituteAnimations = []
})

onMounted(() => {
  write(props.values)
})

watch(
  () => props.values,
  (values) => {
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
  display: grid;
  grid-template-columns: repeat(4, var(--cell-size));
  grid-template-rows: repeat(4, var(--cell-size));
  grid-auto-flow: column;
  gap: var(--cell-gap);
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