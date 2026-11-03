<template>
  <main class="states">
    <h1 class="states__title">
      ByteCell 七态调试
      <code>?debug=states</code>
    </h1>
    <div class="states__grid">
      <div v-for="item in states" :key="item.key" class="states__item">
        <div class="c-byte" :class="item.classes" :data-bd="item.bd" :data-txr="item.txr">
          <span class="c-byte__stage">
            <span class="c-byte__val is-current">{{ item.value }}</span>
            <span class="c-byte__val is-incoming" aria-hidden="true">{{ item.value }}</span>
          </span>
          <span class="c-byte__corner" :data-corner="item.corner1" aria-hidden="true"></span>
          <span class="c-byte__corner" :data-corner="item.corner2" aria-hidden="true"></span>
          <span class="c-byte__sup c-byte__sup--neq" aria-hidden="true">≠</span>
          <span class="c-byte__sup c-byte__sup--xor" aria-hidden="true">⊕</span>
          <span class="c-byte__hint" aria-hidden="true">←1</span>
        </div>
        <p class="states__label">{{ item.label }}</p>
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
interface StateItem {
  key: string
  label: string
  classes: string[]
  bd: string
  txr: string
  corner1: string
  corner2: string
  value: string
}

const states: StateItem[] = [
  { key: 'idle', label: 'idle', classes: [], bd: 'idle', txr: 'none', corner1: '', corner2: '', value: '3F' },
  { key: 'changed', label: 'changed · is-changed', classes: ['is-changed'], bd: 'idle', txr: 'none', corner1: 'tr', corner2: '', value: '3F' },
  { key: 'selected', label: 'selected · is-selected', classes: ['is-selected'], bd: 'selected', txr: 'none', corner1: '', corner2: '', value: '3F' },
  { key: 'error', label: 'error · is-error', classes: ['is-error'], bd: 'error', txr: 'none', corner1: '', corner2: 'br', value: '3F' },
  { key: 'downstream', label: 'downstream · is-downstream', classes: ['is-downstream'], bd: 'downstream', txr: 'none', corner1: '', corner2: '', value: '3F' },
  { key: 'key', label: 'key · is-key', classes: ['is-key'], bd: 'idle', txr: 'hatch', corner1: '', corner2: '', value: '3F' },
  { key: 'done', label: 'done · is-done', classes: ['is-done'], bd: 'idle', txr: 'none', corner1: '', corner2: 'bl', value: '3F' },
  { key: 'error-selected', label: 'error + selected', classes: ['is-error', 'is-selected'], bd: 'error', txr: 'none', corner1: '', corner2: 'br', value: '3F' },
  { key: 'changed-key', label: 'changed + key', classes: ['is-changed', 'is-key'], bd: 'idle', txr: 'hatch', corner1: 'tr', corner2: '', value: '3F' },
]
</script>

<style scoped>
.states {
  min-height: 100vh;
  padding: var(--sp-6);
  background-color: var(--paper-0);
}

.states__title {
  margin-bottom: var(--sp-6);
  font-family: var(--font-ui);
  font-size: var(--fs-h2);
  font-weight: 600;
  color: var(--ink-1);
}

.states__title code {
  font-family: var(--font-mono);
  font-size: var(--fs-label);
  color: var(--ink-3);
}

.states__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(calc(var(--cell-size) * 2), 1fr));
  gap: var(--sp-4);
}

.states__item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--sp-2);
}

.states__label {
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-3);
  text-align: center;
}
</style>