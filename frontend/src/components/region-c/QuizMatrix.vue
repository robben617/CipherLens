<template>
  <div class="c-quiz">
    <div class="c-quiz__frame">
      <div
        ref="gridEl"
        class="c-quiz__grid"
        role="grid"
        aria-rowcount="4"
        aria-colcount="4"
        aria-label="判分定位矩阵"
      >
        <ByteCell
          v-for="cell in cells"
          :key="cell.key"
          :index="cell.index"
          :row="cell.row"
          :col="cell.col"
          :active="false"
        />
      </div>

      <div v-if="rangeLabel" class="c-range" aria-hidden="true">
        <span class="c-range__corner c-range__corner--tl"></span>
        <span class="c-range__corner c-range__corner--tr"></span>
        <span class="c-range__corner c-range__corner--bl"></span>
        <span class="c-range__corner c-range__corner--br"></span>
        <span class="c-range__label">{{ rangeLabel }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watchEffect } from 'vue'
import ByteCell from './ByteCell.vue'
import { useMatrixWriter } from '../../composables/useMatrixWriter'

const props = defineProps<{
  values: readonly number[]
  changed: readonly number[]
  error: readonly number[]
  downstream: readonly number[]
  keyIndices: readonly number[]
  rangeLabel?: string
}>()

const gridEl = ref<HTMLElement | null>(null)
const { paintFor } = useMatrixWriter(() => gridEl.value)

const cells = Array.from({ length: 4 }, (_, row) =>
  Array.from({ length: 4 }, (_, col) => ({
    key: `${row}-${col}`,
    index: col * 4 + row,
    row,
    col,
  })),
).flat()

watchEffect(() => {
  if (props.values.length !== 16) return
  paintFor({
    values: Uint8Array.from(props.values),
    changed: props.changed,
    error: props.error,
    downstream: props.downstream,
    key: props.keyIndices,
  })
})
</script>

<style scoped>
.c-quiz {
  padding-top: 20px;
}

.c-quiz__frame {
  position: relative;
}

.c-quiz__grid {
  --cell-size: 52px;
  --cell-gap: 4px;
  display: grid;
  grid-template-columns: repeat(4, var(--cell-size));
  grid-template-rows: repeat(4, var(--cell-size));
  gap: var(--cell-gap);
  width: calc(4 * var(--cell-size) + 3 * var(--cell-gap));
  height: calc(4 * var(--cell-size) + 3 * var(--cell-gap));
}

.c-range {
  position: absolute;
  inset: 6px;
  pointer-events: none;
}

.c-range__corner {
  position: absolute;
  width: 28px;
  height: 28px;
  border: 2px solid var(--ink-2);
}

.c-range__corner--tl {
  top: 0;
  left: 0;
  border-right: 0;
  border-bottom: 0;
}

.c-range__corner--tr {
  top: 0;
  right: 0;
  border-left: 0;
  border-bottom: 0;
}

.c-range__corner--bl {
  bottom: 0;
  left: 0;
  border-top: 0;
  border-right: 0;
}

.c-range__corner--br {
  right: 0;
  bottom: 0;
  border-top: 0;
  border-left: 0;
}

.c-range__label {
  position: absolute;
  top: -18px;
  left: 50%;
  transform: translateX(-50%);
  padding: 0 4px;
  background: var(--paper-0);
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  line-height: 1.2;
  white-space: nowrap;
  color: var(--ink-3);
}
</style>