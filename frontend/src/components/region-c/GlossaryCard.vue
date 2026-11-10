<template>
  <div class="gc" role="note">
    <div class="gc__head">
      <span class="gc__name">{{ term.name }}</span>
      <span class="gc__en">{{ term.en }}</span>
      <button type="button" class="gc__close" @click="$emit('close')">收起</button>
    </div>
    <dl class="gc__list">
      <dt>做什么</dt>
      <dd>{{ term.action }}</dd>
      <dt>类比</dt>
      <dd>{{ term.analogy }}</dd>
      <dt class="gc__dt--warn">常见误解</dt>
      <dd class="gc__dd--warn">{{ term.pitfall }}</dd>
    </dl>
  </div>
</template>

<script setup lang="ts">
import type { GlossaryTerm } from '../../data/glossary'

defineProps<{ term: GlossaryTerm }>()
defineEmits<{ close: [] }>()
</script>

<style scoped>
.gc {
  padding: var(--sp-3);
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-float);
  background: var(--paper-0);
  box-shadow: var(--shadow-float);
}

.gc__head {
  display: flex;
  align-items: baseline;
  gap: var(--sp-2);
  margin-bottom: var(--sp-2);
  padding-bottom: var(--sp-2);
  border-bottom: var(--rule-region-w) solid var(--line-hairline);
}

.gc__name {
  font-size: var(--fs-ui);
  font-weight: 600;
  color: var(--ink-1);
}

.gc__en {
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  letter-spacing: var(--ls-hex-long);
  color: var(--ink-3);
}

.gc__close {
  margin-left: auto;
  padding: 0;
  border: 0;
  background: none;
  font-size: var(--fs-micro);
  color: var(--ink-3);
  cursor: pointer;
}

.gc__close:hover {
  color: var(--ink-1);
}

.gc__close:focus-visible {
  outline: 2px solid var(--rule-scope-ink);
  outline-offset: 2px;
}

.gc__list {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: var(--sp-1) var(--sp-3);
  margin: 0;
}

.gc__list dt {
  font-size: var(--fs-micro);
  line-height: 1.7;
  color: var(--ink-3);
  white-space: nowrap;
}

.gc__list dd {
  margin: 0;
  font-size: var(--fs-label);
  line-height: 1.7;
  color: var(--ink-2);
}

.gc__dt--warn {
  color: var(--ink-1);
}

/* 「常见误解」是这张卡的重点，用左侧色条强调 */
.gc__dd--warn {
  padding-left: var(--sp-2);
  border-left: 2px solid var(--warn);
  color: var(--ink-1);
}
</style>
