<template>
  <main class="workbench">
    <section data-region="a" class="workbench__region workbench__region--topbar">
      <div class="workbench__left">
        <p class="workbench__label">A · 上下文条</p>
        <span v-if="offline" class="workbench__offline" data-offline>
          离线演示：内置向量 + 本地引擎
        </span>
      </div>
      <div class="workbench__actions">
        <button
          class="workbench__mode"
          data-action="table-view"
          type="button"
          :aria-pressed="tableView"
          @click="$emit('toggleTable')"
        >
          表格视图
        </button>
        <button
          class="workbench__mode"
          data-action="present"
          type="button"
          :aria-pressed="present"
          @click="$emit('togglePresent')"
        >
          演示模式
        </button>
      </div>
    </section>
    <section data-region="b" class="workbench__region">
      <p class="workbench__label">B · 输入区</p>
    </section>
    <section data-region="c" class="workbench__region">
      <p class="workbench__label">C · 舞台区</p>
      <TableView v-if="tableView" :values="values" :step-index="stepIndex" />
      <MatrixStage
        v-else
        :values="values"
        :op="op"
        :round-key="roundKey"
        :changed="changed"
        :key-indices="keyIndices"
        :focus-byte="focusByte"
        @open-drawer="onOpenDrawer"
      />
    </section>
    <section data-region="d" class="workbench__region workbench__region--transport">
      <TransportBar :step-count="steps.length" />
      <Timeline
        :steps="steps"
        :current="stepIndex"
        :markers="markers"
        @commit="$emit('commit', $event)"
        @open-mark="onOpenMark"
      />
    </section>
    <p class="sr-only" aria-live="polite" data-live>{{ announcement }}</p>

    <section data-region="e" class="workbench__region">
      <p class="workbench__label workbench__label--rail" aria-hidden="true">E</p>
      <DiagnosisCard
        :step-index="stepIndex"
        :step-label="stepLabel"
        :step-before="stepBefore"
        :step-after="stepAfter"
        :changed="changed"
      />
      <div class="workbench__tutor">
        <TutorPanel
          :trace-id="traceId"
          :step-index="stepIndex"
          :step-label="stepLabel"
          :step-before="stepBefore"
          :step-after="stepAfter"
          :changed="changed"
        />
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import MatrixStage from '../region-c/MatrixStage.vue'
import TableView from '../shared/TableView.vue'
import TransportBar from '../region-d/TransportBar.vue'
import Timeline from '../region-d/Timeline.vue'
import DiagnosisCard from '../region-e/DiagnosisCard.vue'
import TutorPanel from '../region-e/TutorPanel.vue'
import type { TraceStep } from '../../engine/trace'

defineProps<{
  values: Uint8Array
  op: string
  roundKey: Uint8Array
  changed: readonly number[]
  steps: readonly TraceStep[]
  stepIndex: number
  stepLabel: string
  stepBefore: readonly number[]
  stepAfter: readonly number[]
  traceId: string
  markers: Record<number, { diag: number; ask: number }>
  keyIndices: readonly number[]
  focusByte: number | null
  tableView: boolean
  announcement: string
  present: boolean
  offline: boolean
}>()

const emit = defineEmits<{
  commit: [index: number]
  toggleTable: []
  openDrawer: [index: number, trigger: HTMLElement]
  openMark: [index: number, trigger: HTMLElement]
  togglePresent: []
}>()

function onOpenDrawer(index: number, trigger: HTMLElement): void {
  emit('openDrawer', index, trigger)
}

function onOpenMark(index: number, trigger: HTMLElement): void {
  emit('openMark', index, trigger)
}


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
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-2);
  border-bottom: var(--rule-region-w) solid var(--line-hairline);
}

.workbench__left {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  min-width: 0;
}

.workbench__offline {
  padding: 2px var(--sp-2);
  border: var(--rule-region-w) dashed var(--line-hairline);
  border-radius: var(--r-control);
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-2);
  white-space: nowrap;
}

.workbench__actions {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}

.workbench__mode {
  height: 26px;
  padding: 0 var(--sp-2);
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  background: transparent;
  font-family: var(--font-ui);
  font-size: var(--fs-label);
  color: var(--ink-2);
  cursor: pointer;
}

.workbench__mode[aria-pressed="true"] {
  border-color: var(--accent);
  color: var(--accent-strong);
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
  flex-direction: column;
  align-items: stretch;
  box-shadow: inset 0 var(--rule-region-w) 0 var(--line-hairline);
}

[data-region="e"] {
  grid-area: e;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  border-left: var(--rule-region-w) solid var(--line-hairline);
}

.workbench__tutor {
  flex: 1;
  min-height: 0;
}

/* 演示态 E 区默认收为 48px，标签切成竖条 */
[data-mode="present"] [data-region="e"] .workbench__label--full {
  display: none;
}

[data-mode="present"] [data-region="e"] .workbench__label--rail {
  display: block;
  text-align: center;
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