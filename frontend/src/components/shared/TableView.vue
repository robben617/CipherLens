<template>
  <div class="c-table-view">
    <table class="c-table-view__table" data-table-view>
      <caption>
        当前步矩阵（表格视图）{{ stepIndex === 0 ? '初始状态' : `第 ${stepIndex} 步` }}
      </caption>
      <thead>
        <tr>
          <th scope="col">行 / 列</th>
          <th v-for="col in 4" :key="`c${col}`" scope="col">第 {{ col }} 列</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in 4" :key="`r${row}`">
          <th scope="row">第 {{ row }} 行</th>
          <td
            v-for="col in 4"
            :key="`${row}-${col}`"
            :data-index="(col - 1) * 4 + (row - 1)"
          >
            {{ hex(values[(col - 1) * 4 + (row - 1)] ?? 0) }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  values: Uint8Array
  stepIndex: number
}>()

const hex = (value: number): string =>
  value.toString(16).toUpperCase().padStart(2, '0')
</script>

<style scoped>
.c-table-view {
  width: 100%;
  max-width: 520px;
  margin: 0 auto;
}

.c-table-view__table {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--font-mono);
  font-size: var(--fs-label);
  color: var(--ink-1);
}

.c-table-view__table caption {
  padding-bottom: var(--sp-2);
  font-family: var(--font-ui);
  font-size: var(--fs-micro);
  color: var(--ink-3);
  text-align: left;
}

.c-table-view__table th,
.c-table-view__table td {
  padding: var(--sp-2);
  border: var(--rule-region-w) solid var(--line-hairline);
  text-align: center;
  font-weight: 400;
}

.c-table-view__table thead th,
.c-table-view__table tbody th {
  background: var(--surface-inset);
  color: var(--ink-2);
  font-family: var(--font-ui);
  font-size: var(--fs-micro);
}

.c-table-view__table td {
  letter-spacing: var(--ls-hex-cell);
  font-variant-numeric: tabular-nums;
}
</style>