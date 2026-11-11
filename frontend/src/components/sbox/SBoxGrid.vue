<template>
  <div
    ref="gridEl"
    class="sbox-grid"
    :class="{ 'is-inverse': inverse }"
    role="grid"
    :aria-label="inverse ? '逆向 S 盒：16 行 16 列，行是输入高位、列是输入低位' : '正向 S 盒：16 行 16 列，行是输入高位、列是输入低位'"
    @mouseleave="hover = null"
  >
    <div class="sbox-grid__row sbox-grid__row--head" role="row">
      <span class="sbox-grid__corner" role="columnheader" aria-label="行 / 列">&nbsp;</span>
      <span
        v-for="(_, c) in COLUMNS"
        :key="`h${c}`"
        class="sbox-grid__head"
        role="columnheader"
        :class="{ 'is-lit': hover !== null && (hover & 15) === c }"
      >
        {{ nibble(c) }}
      </span>
    </div>

    <div v-for="(row, r) in grid" :key="`r${r}`" class="sbox-grid__row" role="row">
      <span
        class="sbox-grid__head sbox-grid__head--row"
        role="rowheader"
        :class="{ 'is-lit': hover !== null && (hover >> 4) === r }"
      >
        {{ nibble(r) }}
      </span>
      <button
        v-for="(cell, c) in row"
        :key="cell.input"
        type="button"
        role="gridcell"
        class="sbox-grid__cell"
        :class="{
          'is-selected': cell.input === selected,
          'is-cross':
            hover !== null &&
            (((hover >> 4) === r && (hover & 15) !== c) ||
              ((hover & 15) === c && (hover >> 4) !== r)),
        }"
        :data-index="cell.input"
        :data-cell="hex(cell.output)"
        :tabindex="cell.input === selected ? 0 : -1"
        :aria-label="`行 ${r} 列 ${c}，输入 0x${hex(cell.input)}，输出 0x${hex(cell.output)}`"
        :aria-selected="cell.input === selected"
        @mouseenter="hover = cell.input"
        @focus="hover = cell.input"
        @click="choose(cell.input)"
        @keydown="onKeydown($event, cell.input)"
      >
        {{ hex(cell.output) }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'

const props = defineProps<{
  values: ArrayLike<number>
  selected: number
  inverse: boolean
}>()

const emit = defineEmits<{
  'update:selected': [value: number]
}>()

interface Cell {
  /** 输入字节：决定格子的位置（行 = 高位，列 = 低位），也是键盘与选中状态的坐标 */
  input: number
  /** 格子上印的输出字节 */
  output: number
}

const COLUMNS = 16
const gridEl = ref<HTMLElement | null>(null)
const hover = ref<number | null>(null)

const nibble = (value: number): string => value.toString(16).toUpperCase()
const hex = (value: number): string => value.toString(16).toUpperCase().padStart(2, '0')

const grid = computed<Cell[][]>(() =>
  Array.from({ length: COLUMNS }, (_, row) =>
    Array.from({ length: COLUMNS }, (_, col) => {
      const input = row * COLUMNS + col
      return { input, output: props.values[input] ?? 0 }
    }),
  ),
)

function choose(input: number): void {
  if (input !== props.selected) emit('update:selected', input)
}

function focusCell(input: number): void {
  void nextTick(() => {
    gridEl.value
      ?.querySelector<HTMLElement>(`[data-index="${input}"]`)
      ?.focus({ preventScroll: false })
  })
}

function onKeydown(event: KeyboardEvent, input: number): void {
  const row = input >> 4
  let next: number

  switch (event.key) {
    case 'ArrowUp':
      next = Math.max(0, input - 16)
      break
    case 'ArrowDown':
      next = Math.min(255, input + 16)
      break
    case 'ArrowLeft':
      next = Math.max(row * 16, input - 1)
      break
    case 'ArrowRight':
      next = Math.min(row * 16 + 15, input + 1)
      break
    case 'Home':
      next = row * 16
      break
    case 'End':
      next = row * 16 + 15
      break
    case 'PageUp':
      next = Math.max(0, input - 16)
      break
    case 'PageDown':
      next = Math.min(255, input + 16)
      break
    default:
      return
  }

  event.preventDefault()
  emit('update:selected', next)
  focusCell(next)
}

// 外部（搜索框 / URL / 详情卡输入框）改了选中项时，把它滚进可见区
watch(
  () => props.selected,
  (input) => {
    void nextTick(() => {
      gridEl.value
        ?.querySelector<HTMLElement>(`[data-index="${input}"]`)
        ?.scrollIntoView({ block: 'nearest', inline: 'nearest' })
    })
  },
)
</script>

<style scoped>
.sbox-grid {
  display: flex;
  flex-direction: column;
  gap: 2px;
  width: max-content;
}

.sbox-grid__row {
  display: grid;
  grid-template-columns: 22px repeat(16, var(--sbox-cell, 40px));
  gap: 2px;
}

.sbox-grid__row--head .sbox-grid__head {
  height: 18px;
}

.sbox-grid__corner {
  width: 22px;
}

.sbox-grid__head {
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  letter-spacing: var(--ls-label);
  color: var(--ink-3);
  transition: color var(--d-1) var(--e-out-quart);
}

.sbox-grid__head.is-lit {
  color: var(--accent-strong);
}

.sbox-grid__cell {
  height: var(--sbox-cell, 40px);
  padding: 0;
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: 0;
  background: var(--paper-0);
  font-family: var(--font-mono);
  font-size: var(--fs-sbox);
  letter-spacing: var(--ls-hex-cell);
  color: var(--ink-1);
  cursor: pointer;
  transition: background-color var(--d-1) var(--e-linear), color var(--d-1) var(--e-linear);
}

.sbox-grid__cell.is-cross {
  background: var(--paper-1);
}

.sbox-grid__cell:hover {
  background: var(--accent-soft);
}

.sbox-grid__cell.is-selected {
  /* 内描边：用 inset 阴影不用 border，选中时格子不会涨 4px 把整行挤歪 */
  box-shadow: inset 0 0 0 2px var(--accent);
  color: var(--accent-strong);
  font-weight: 600;
}

.sbox-grid__cell:focus-visible {
  outline-offset: 0;
  z-index: 1;
}

@media (prefers-reduced-motion: reduce) {
  .sbox-grid__cell,
  .sbox-grid__head {
    transition: none;
  }
}
</style>
