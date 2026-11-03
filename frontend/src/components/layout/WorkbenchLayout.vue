<template>
  <main class="workbench">
    <section data-region="a" class="workbench__region">
      <p class="workbench__label">A · 上下文条</p>
    </section>
    <section data-region="b" class="workbench__region">
      <p class="workbench__label">B · 输入区</p>
    </section>
    <section data-region="c" class="workbench__region">
      <p class="workbench__label">C · 舞台区</p>
      <MatrixStage :values="values" :op="op" :round-key="roundKey" @next="$emit('next')" />
    </section>
    <section data-region="d" class="workbench__region workbench__region--transport">
      <Timeline
        :steps="steps"
        :current="stepIndex"
        :markers="markers"
        @commit="$emit('commit', $event)"
      />
    </section>
    <section data-region="e" class="workbench__region">
      <p class="workbench__label workbench__label--full">E · AI 辅导栏</p>
      <p class="workbench__label workbench__label--rail" aria-hidden="true">E</p>
    </section>
  </main>
</template>

<script setup lang="ts">
import MatrixStage from '../region-c/MatrixStage.vue'
import Timeline from '../region-d/Timeline.vue'
import type { TraceStep } from '../../engine/trace'

defineProps<{
  values: Uint8Array
  op: string
  roundKey: Uint8Array
  steps: readonly TraceStep[]
  stepIndex: number
  markers: Record<number, { diag: number; ask: number }>
}>()

defineEmits<{
  next: []
  commit: [index: number]
}>()
</script>

<style scoped>
.workbench {
  display: grid;
  grid-template-columns: var(--input-col) minmax(0, 1fr) var(--ai-col);
  grid-template-rows: var(--topbar-h) minmax(0, 1fr) var(--transport-h);
  grid-template-areas:
    "a a a"
    "b c e"
    "d d d";
  height: 100vh;
  height: 100dvh;
}

.workbench__region {
  min-width: 0;
  padding: var(--sp-3);
}

.workbench__label {
  font-family: var(--font-mono);
  font-size: var(--fs-label);
  letter-spacing: var(--ls-label);
  line-height: var(--lh-tight);
  color: var(--ink-3);
}

.workbench__label--rail {
  display: none;
}

[data-region="a"] {
  grid-area: a;
  min-height: 0;
  border-bottom: var(--rule-region-w) solid var(--line-hairline);
}

[data-region="b"] {
  grid-area: b;
  overflow: hidden;
  border-right: var(--rule-region-w) solid var(--line-hairline);
}

[data-region="c"] {
  grid-area: c;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 0;
}

[data-region="c"] > .workbench__label {
  position: absolute;
  top: var(--sp-3);
  left: var(--sp-3);
}

[data-region="d"] {
  grid-area: d;
  min-height: 0;
  padding: 0;
  display: flex;
  align-items: flex-end;
  border-top: var(--rule-region-w) solid var(--line-hairline);
}

[data-region="e"] {
  grid-area: e;
  overflow: hidden;
  border-left: var(--rule-region-w) solid var(--line-hairline);
}

/* 低于 70rem（即窄于 1120 CSS 像素）：E 区折叠为 48 CSS 像素 */
@media (max-width: 69.9375rem) {
  .workbench {
    grid-template-columns: var(--input-col) minmax(0, 1fr) var(--sp-12);
  }

  [data-region="e"] .workbench__label--full {
    display: none;
  }

  [data-region="e"] .workbench__label--rail {
    display: block;
    text-align: center;
  }
}
</style>