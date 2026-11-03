<template>
  <div
    class="c-byte"
    role="gridcell"
    :tabindex="active ? 0 : -1"
    :aria-label="initialLabel"
    :data-row="row"
    :data-col="col"
    data-bd="idle"
    data-txr="none"
  >
    <span class="c-byte__stage">
      <span class="c-byte__val is-current">—</span>
      <span class="c-byte__val is-incoming" aria-hidden="true">—</span>
    </span>
    <span class="c-byte__corner" data-corner="" aria-hidden="true"></span>
    <span class="c-byte__corner" data-corner="" aria-hidden="true"></span>
    <span class="c-byte__sup c-byte__sup--neq" data-active="false" aria-hidden="true">≠</span>
    <span class="c-byte__sup c-byte__sup--xor" data-active="false" aria-hidden="true">⊕</span>
    <span class="c-byte__hint" aria-hidden="true">←1</span>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  index: number
  row: number
  col: number
  active: boolean
}>()

const initialLabel = `第 ${props.row + 1} 行第 ${props.col + 1} 列，字节 ${props.index}，值 —`
</script>

<style scoped>
.c-byte {
  position: relative;
  box-sizing: border-box;
  width: var(--cell-size);
  height: var(--cell-size);
  display: flex;
  align-items: center;
  justify-content: center;
  border: var(--rule-region-w) solid var(--rule-region-ink);
  border-radius: var(--r-cell);
  background: var(--st-idle-fill);
  color: var(--ink-1);
  font-family: var(--font-mono);
  font-size: var(--fs-byte);
  font-weight: 500;
  letter-spacing: var(--ls-hex-cell);
  font-variant-numeric: tabular-nums;
}

.c-byte__stage {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.c-byte__val {
  position: absolute;
  line-height: 1;
}

.c-byte__val.is-incoming {
  opacity: 0;
}

.c-byte__corner,
.c-byte__sup,
.c-byte__hint {
  display: none;
}
</style>