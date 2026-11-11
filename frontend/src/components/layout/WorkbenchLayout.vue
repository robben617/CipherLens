<template>
  <main class="workbench">
    <section data-region="a" class="workbench__region workbench__region--topbar">
      <div class="workbench__left">
        <RouterLink class="workbench__brand" to="/" data-action="home">CipherLens</RouterLink>
        <NavLinks compact />
        <span class="workbench__sep" aria-hidden="true"></span>
        <span v-if="consistency === 'offline'" class="workbench__offline" data-offline>
          离线演示：内置向量 + 本地引擎
        </span>
        <span v-else-if="consistency === 'mismatch'" class="workbench__mismatch" data-mismatch>
          前后端数值不一致
        </span>
        <span v-else-if="consistency === 'checking'" class="workbench__checking" data-checking>
          正在校验前后端数值…
        </span>
      </div>
      <div class="workbench__actions">
        <button
          v-if="consistency !== 'ok'"
          class="workbench__mode"
          data-action="recheck-trace"
          type="button"
          :disabled="consistency === 'checking'"
          @click="$emit('recheck')"
        >
          重新校验
        </button>
        <button
          class="workbench__mode"
          data-action="tour"
          type="button"
          title="重新播放新手引导"
          @click="$emit('tour')"
        >
          引导
        </button>
        <button
          class="workbench__mode"
          data-action="key-schedule"
          type="button"
          title="密钥扩展：本轮 44 个字是怎么长出来的（K）"
          @click="$emit('key-schedule')"
        >
          密钥
        </button>
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
    <section data-region="b" class="workbench__region workbench__region--input">
      <InputPanel
        :plaintext="plaintext"
        :key-hex="keyHex"
        @apply="onApplyInput"
        @notice="$emit('notice', $event)"
        @key-schedule="$emit('key-schedule')"
      />
    </section>
    <section data-region="c" class="workbench__region">
      <StepNarrative
        :step-index="stepIndex"
        :total="steps.length"
        :round-no="roundNo"
        :op="op"
        :changed-count="changed.length"
      />
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
      <TransportBar :steps="steps" />
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
          :op="op"
          :step-before="stepBefore"
          :step-after="stepAfter"
          :changed="changed"
          :ask-disabled="askDisabled"
          :disabled-reason="disabledReason"
          @cite="(byte, trigger) => $emit('cite', byte, trigger)"
          @goto="$emit('goto', $event)"
          @sbox="$emit('sbox', $event)"
        />
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import MatrixStage from '../region-c/MatrixStage.vue'
import StepNarrative from '../region-c/StepNarrative.vue'
import TableView from '../shared/TableView.vue'
import TransportBar from '../region-d/TransportBar.vue'
import Timeline from '../region-d/Timeline.vue'
import DiagnosisCard from '../region-e/DiagnosisCard.vue'
import TutorPanel from '../region-e/TutorPanel.vue'
import InputPanel from '../region-b/InputPanel.vue'
import NavLinks from './NavLinks.vue'
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import type { TraceStep } from '../../engine/trace'

const props = defineProps<{
  /** 当前生效的明文 hex，透传给 B 区输入面板 */
  plaintext: string
  /** 当前生效的密钥 hex */
  keyHex: string
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
  consistency: 'checking' | 'ok' | 'offline' | 'mismatch'
  askDisabled: boolean
  disabledReason: string
}>()

const emit = defineEmits<{
  commit: [index: number]
  toggleTable: []
  openDrawer: [index: number, trigger: HTMLElement]
  openMark: [index: number, trigger: HTMLElement]
  togglePresent: []
  recheck: []
  apply: [plaintext: string, key: string]
  notice: [text: string]
  tour: []
  'key-schedule': []
  cite: [byte: number, trigger: HTMLElement]
  goto: [step: number]
  sbox: [byte: number]
}>()

function onApplyInput(plaintext: string, key: string): void {
  emit('apply', plaintext, key)
}

/** 当前步所属轮次（第 0 步为初始轮密钥加，轮次记 0） */
const roundNo = computed(() => props.steps[props.stepIndex]?.round ?? 0)

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

.workbench__brand {
  font-family: var(--font-display);
  font-size: var(--fs-ui);
  font-weight: 600;
  letter-spacing: 0.01em;
  color: var(--ink-1);
  text-decoration: none;
  white-space: nowrap;
}

.workbench__sep {
  width: 1px;
  height: 18px;
  background: var(--line-hairline);
  flex: none;
}

.workbench__mismatch,
.workbench__checking,
.workbench__offline {
  padding: 2px var(--sp-2);
  border: var(--rule-region-w) dashed var(--line-hairline);
  border-radius: var(--r-control);
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-2);
  white-space: nowrap;
}

.workbench__mismatch {
  border-color: var(--st-error);
  color: var(--st-error);
}

.workbench__checking {
  color: var(--ink-3);
}

.workbench__actions {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}

.workbench__mode {
  height: 26px;
  /* 顶栏拥挤时宁可超出去，也别把「密钥」拆成上下两行 */
  white-space: nowrap;
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
  /* 输入面板内容可能高于一屏（小屏），允许纵向滚动 */
  overflow-x: hidden;
  overflow-y: auto;
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