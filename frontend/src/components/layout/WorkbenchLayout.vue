<template>
  <main class="workbench" :data-ai="tutorCollapsed ? 'collapsed' : 'expanded'">
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
      </div>
    </section>
    <section data-region="b" class="workbench__region workbench__region--input">
      <InputPanel
        :plaintext="plaintext"
        :key-hex="keyHex"
        :direction="direction"
        :apply-notice="applyNotice"
        :tour-open="tourOpen"
        @apply="onApplyInput"
        @notice="$emit('notice', $event)"
        @key-schedule="$emit('key-schedule')"
        @direction="$emit('direction', $event)"
      />
    </section>
    <section data-region="c" class="workbench__region">
      <StepNarrative
        :step-index="stepIndex"
        :total="steps.length"
        :round-no="roundNo"
        :op="op"
        :changed-count="changed.length"
        :direction="direction"
      />
      <button
        v-if="!tableView"
        class="workbench__viewtoggle"
        type="button"
        data-action="toggle-compare"
        @click="compare = !compare"
      >
        {{ compare ? '整体视图' : '前后对照' }}
      </button>

      <TableView v-if="tableView" :values="values" :step-index="stepIndex" />
      <StepCompare
        v-else-if="compare"
        :before="stepBefore"
        :after="stepAfter"
        :step-index="stepIndex"
        :total="steps.length"
        :op="op"
        :changed="changed"
        :round-key="roundKey"
        :direction="direction"
      />
      <MatrixStage
        v-else
        :values="values"
        :op="op"
        :round-key="roundKey"
        :changed="changed"
        :key-indices="keyIndices"
        :focus-byte="focusByte"
        :direction="direction"
        @open-drawer="onOpenDrawer"
      />
    </section>
    <section data-region="d" class="workbench__region workbench__region--transport">
      <TransportBar :steps="steps" :direction="direction" />
      <Timeline
        :steps="steps"
        :current="stepIndex"
        :markers="markers"
        :direction="direction"
        @commit="$emit('commit', $event)"
        @open-mark="onOpenMark"
      />
    </section>
    <p class="sr-only" aria-live="polite" data-live>{{ announcement }}</p>

    <section data-region="e" class="workbench__region" :data-ai-state="tutorCollapsed ? 'collapsed' : 'expanded'">
      <div class="workbench__ehead">
        <template v-if="tutorCollapsed">
          <button
            class="workbench__aitoggle"
            type="button"
            data-action="toggle-tutor"
            aria-controls="ai-panel-body"
            :aria-expanded="false"
            aria-label="展开 AI 答疑小助手"
            @click="$emit('toggleTutor')"
          >
            AI
          </button>
          <span class="workbench__aitoggle-name" aria-hidden="true">答疑小助手</span>
        </template>
        <template v-else>
          <span class="workbench__etitle">AI答疑小助手</span>
          <button
            class="workbench__aitoggle workbench__aitoggle--open"
            type="button"
            data-action="toggle-tutor"
            aria-controls="ai-panel-body"
            :aria-expanded="true"
            aria-label="收起 AI 答疑小助手"
            @click="$emit('toggleTutor')"
          >
            ×
          </button>
        </template>
      </div>

      <div v-show="!tutorCollapsed" id="ai-panel-body" class="workbench__ebody">
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
      </div>
      <!-- 一轮小结盖在 E 区上：轮末用户该读整轮结构，而不是接着提问 -->
      <RoundSummary
        v-if="summaryRound !== null"
        :round="summaryRound"
        :direction="direction"
        :floating="present || tutorCollapsed"
        @close="$emit('summary-close')"
        @disable="$emit('summary-disable')"
        @open-key="$emit('key-schedule')"
      />
    </section>
  </main>
</template>

<script setup lang="ts">
import MatrixStage from '../region-c/MatrixStage.vue'
import StepCompare from '../region-c/StepCompare.vue'
import RoundSummary from '../region-c/RoundSummary.vue'
import StepNarrative from '../region-c/StepNarrative.vue'
import TableView from '../shared/TableView.vue'
import TransportBar from '../region-d/TransportBar.vue'
import Timeline from '../region-d/Timeline.vue'
import DiagnosisCard from '../region-e/DiagnosisCard.vue'
import TutorPanel from '../region-e/TutorPanel.vue'
import InputPanel from '../region-b/InputPanel.vue'
import NavLinks from './NavLinks.vue'
import { computed, ref } from 'vue'
import { RouterLink } from 'vue-router'
import type { TraceStep } from '../../engine/trace'

const props = defineProps<{
  /** 当前生效的明文 hex，透传给 B 区输入面板 */
  plaintext: string
  /** 当前生效的密钥 hex */
  keyHex: string
  /** 加密还是解密：矩阵提示、轮次带、四步 chip 都要跟着翻 */
  direction: 'encrypt' | 'decrypt'
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
  /** 刚走完的那一轮；null = 不弹小结卡（不在轮末、被关掉、或引导中） */
  summaryRound: number | null
  /** AI 答疑栏初始收起，F 键或右上角方块按钮切换 */
  tutorCollapsed: boolean
  /** 生成演示后的可见提示，显示在输入区与舞台 */
  applyNotice: string
  /** 引导层打开时，生成按钮明确不可用，避免「高亮却无反应」 */
  tourOpen: boolean
}>()

const emit = defineEmits<{
  commit: [index: number]
  toggleTable: []
  'summary-close': []
  'summary-disable': []
  openDrawer: [index: number, trigger: HTMLElement]
  openMark: [index: number, trigger: HTMLElement]
  togglePresent: []
  toggleTutor: []
  recheck: []
  apply: [plaintext: string, key: string, direction: 'encrypt' | 'decrypt']
  notice: [text: string]
  tour: []
  'key-schedule': []
  cite: [byte: number, trigger: HTMLElement]
  goto: [step: number]
  sbox: [byte: number]
  direction: [direction: 'encrypt' | 'decrypt']
}>()

function onApplyInput(
  plaintext: string,
  key: string,
  direction: 'encrypt' | 'decrypt',
): void {
  emit('apply', plaintext, key, direction)
}

/**
 * 当前状态所属轮次 = 刚刚执行完的那一步的轮次。
 * 第 0 步还没算任何一步，记 0（隐藏轮次 chip）。
 * 不能读 steps[stepIndex]：那是「下一步」，解密时会提前显示第 10 轮。
 */
const roundNo = computed(() => {
  if (props.stepIndex === 0) return 0
  return props.steps[props.stepIndex - 1]?.round ?? 0
})

/** 舞台默认显示「变换前 → 变换后」双矩阵；整体视图保留原单矩阵与四步动效 */
const compare = ref(true)

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

.workbench[data-ai="collapsed"] {
  --ai-col: 48px;
}

.workbench[data-ai="expanded"] {
  --ai-col: 360px;
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
  /* 极窄视口下 C 区可能只剩几十像素：内部滚动，不撑破文档宽度 */
  overflow-x: auto;
  overflow-y: hidden;
}

[data-region="c"] > .workbench__label {
  position: absolute;
  top: var(--sp-3);
  left: var(--sp-3);
}

.workbench__viewtoggle {
  position: absolute;
  right: var(--sp-3);
  bottom: var(--sp-3);
  z-index: 2;
  height: 26px;
  padding: 0 var(--sp-2);
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  background: var(--paper-0);
  font-family: var(--font-ui);
  font-size: var(--fs-label);
  color: var(--ink-2);
  cursor: pointer;
  white-space: nowrap;
}

.workbench__viewtoggle:hover {
  border-color: var(--ink-2);
  color: var(--ink-1);
}


[data-region="d"] {
  grid-area: d;
  min-height: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  background: var(--paper-0);
  box-shadow: inset 0 var(--rule-region-w) 0 var(--line-hairline);
}

[data-region="e"] {
  grid-area: e;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 0;
  padding: 0;
  border-left: var(--rule-region-w) solid var(--line-hairline);
}

.workbench[data-ai="expanded"] [data-region="e"] {
  gap: var(--sp-2);
  padding: var(--sp-3);
}

.workbench__ehead {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex: none;
  gap: var(--sp-2);
}

.workbench[data-ai="collapsed"] .workbench__ehead {
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  gap: 6px;
}

.workbench__aitoggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: none;
  width: 28px;
  height: 28px;
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  background: transparent;
  font-family: var(--font-mono);
  font-size: var(--fs-label);
  letter-spacing: 0.06em;
  color: var(--ink-1);
  cursor: pointer;
}

.workbench[data-ai="collapsed"] .workbench__aitoggle {
  width: 100%;
  height: 48px;
  border-color: var(--line-strong);
  font-size: 13px;
}

.workbench__aitoggle:hover {
  border-color: var(--accent);
  color: var(--accent-strong);
}

.workbench__aitoggle--open {
  width: 28px;
  height: 28px;
  border-color: var(--line-hairline);
  font-size: 18px;
  line-height: 1;
  color: var(--ink-2);
}

.workbench__aitoggle-name {
  writing-mode: vertical-rl;
  text-orientation: upright;
  font-family: var(--font-ui);
  font-size: 11px;
  line-height: 1.2;
  letter-spacing: 1px;
  color: var(--ink-3);
  user-select: none;
}

.workbench__etitle {
  font-family: var(--font-ui);
  font-size: var(--fs-label);
  font-weight: 600;
  letter-spacing: var(--ls-label);
  color: var(--ink-3);
}

.workbench__ebody {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: var(--sp-2);
  min-height: 0;
}

.workbench__tutor {
  flex: 1;
  min-height: 0;
}

/* 宽屏默认收起：E 区就是 48px rail，按钮在右上角 */
@media (max-width: 69.9375rem) {
  .workbench {
    grid-template-columns: var(--input-col) minmax(0, 1fr) var(--sp-12);
  }

  /* 窄屏展开不挤压 C 区，改为覆盖浮层 */
  .workbench[data-ai="expanded"] [data-region="e"] {
    position: fixed;
    top: var(--topbar-h);
    right: 0;
    bottom: var(--transport-h);
    width: 360px;
    z-index: 20;
    padding: var(--sp-3);
    border-left: var(--rule-region-w) solid var(--line-strong);
    background: var(--paper-0);
    box-shadow: -8px 0 24px rgb(0 0 0 / 0.1);
  }
}

/* 演示态同理：默认 48px，展开走浮层，不改 C 区格径 */
[data-mode="present"] .workbench[data-ai="expanded"] {
  grid-template-columns: var(--input-col) minmax(0, 1fr) var(--sp-12);
}

[data-mode="present"] .workbench[data-ai="expanded"] [data-region="e"] {
  position: fixed;
  top: var(--topbar-h);
  right: 0;
  bottom: var(--transport-h);
  width: 420px;
  z-index: 20;
  padding: var(--sp-3);
  border-left: var(--rule-region-w) solid var(--line-strong);
  background: var(--paper-0);
  box-shadow: -8px 0 24px rgb(0 0 0 / 0.1);
}
</style>