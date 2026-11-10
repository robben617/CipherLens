<template>
  <StatesDebugView v-if="isStatesDebug" />
  <ErrorBoundary v-else @reset="resetFromError">
    <CrashProbe v-if="crashInjected" />
    <WorkbenchLayout
      v-else
    :plaintext="input.plaintext"
    :key-hex="input.key"
    :values="values"
    :op="currentOp"
    :round-key="currentRoundKey"
    :changed="currentChanged"
    :steps="steps"
    :step-index="stepIndex"
    :step-label="currentStepLabel"
    :step-before="currentStepBefore"
    :step-after="currentStepAfter"
    :trace-id="traceId"
    :markers="markers"
    :key-indices="currentKeyIndices"
    :focus-byte="focusByte"
      :table-view="tableView"
      :announcement="announcement"
      :present="presentMode"
      :consistency="consistency"
      :ask-disabled="askDisabled"
      :disabled-reason="disabledReason"
      @commit="commitStep"
      @toggle-table="toggleTable"
      @toggle-present="presentMode = !presentMode"
      @recheck="checkTrace"
      @open-drawer="onOpenDrawer"
      @open-mark="onOpenMark"
      @apply="applyInput"
      @notice="announcement = $event"
    />
  </ErrorBoundary>

  <AppDrawer
    :open="drawer !== null"
    :byte-index="drawer?.byteIndex ?? 0"
    :row="drawer?.row ?? 0"
    :col="drawer?.col ?? 0"
    :value="drawer?.value ?? 0"
    :before="drawer?.before ?? 0"
    :after="drawer?.after ?? 0"
    :step-label="drawer?.stepLabel ?? ''"
    :title="drawer?.title ?? ''"
    @close="closeDrawer"
  />

  <div
    v-if="helpOpen"
    class="c-help"
    role="dialog"
    aria-modal="true"
    aria-labelledby="help-title"
    data-help
  >
    <h2 id="help-title">快捷键与约定</h2>
    <ul>
      <li>Space：播放 / 暂停；← / →：上一步 / 下一步</li>
      <li>Shift + ← / →：上一轮 / 下一轮第一步；Home / End：首步 / 末步</li>
      <li>[ / ]：上一个 / 下一个有标记的步；Enter：单元格 / 标记详情</li>
      <li>A：聚焦 AI 输入；Esc：中断生成 &gt; 关抽屉 &gt; 退出播放</li>
      <li>V：载入标准向量；J：聚焦时间轴；P：演示模式；E：导出 trace</li>
      <li>字节下标从 0 开始，矩阵按列优先 index = col × 4 + row</li>
    </ul>
    <button type="button" data-action="help-close" @click="helpOpen = false">关闭</button>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onScopeDispose, ref, shallowRef, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import WorkbenchLayout from '../components/layout/WorkbenchLayout.vue'
import AppDrawer from '../components/shared/AppDrawer.vue'
import CrashProbe from '../components/shared/CrashProbe.vue'
import ErrorBoundary from '../components/shared/ErrorBoundary.vue'
import { useHotkeys } from '../composables/useHotkeys'
import { buildTrace, type AesTrace } from '../engine/trace'
import { FIPS_197_VECTORS } from '../engine/vectors'
import { usePlaybackStore } from '../stores/playback'
import { useUiStore } from '../stores/ui'
import {
  beginStep,
  disposePerfProbe,
  installPerfProbe,
  startFrameSampling,
  stopFrameSampling,
} from '../composables/usePerfProbe'
import StatesDebugView from './StatesDebugView.vue'

const route = useRoute()
const router = useRouter()
const isStatesDebug = computed(() => route.query.debug === 'states')
const playback = usePlaybackStore()
const ui = useUiStore()

interface DrawerState {
  byteIndex: number
  row: number
  col: number
  value: number
  before: number
  after: number
  stepLabel: string
  title: string
}

const tableView = ref(route.query.view === 'table')
const presentMode = ref(route.query.present === '1')
type Consistency = 'checking' | 'ok' | 'offline' | 'mismatch'
const consistency = ref<Consistency>('checking')
const crashInjected = ref(route.query.debug === 'crash')
const askDisabled = computed(() => consistency.value !== 'ok')
const disabledReason = computed(() => {
  if (consistency.value === 'mismatch') return '前后端数值不一致，请重新校验后再提问'
  if (consistency.value === 'offline') return '后端离线，先恢复连接再提问'
  if (consistency.value === 'checking') return '正在校验前后端数值…'
  return ''
})

const announcement = ref('')
const helpOpen = ref(false)
const drawer = ref<DrawerState | null>(null)
let drawerTrigger: HTMLElement | null = null
let urlTimer: ReturnType<typeof setTimeout> | undefined
const perfEnabled =
  import.meta.env.DEV ||
  new URLSearchParams(window.location.search).get('perf') === '1'

const DEFAULT_VECTOR = FIPS_197_VECTORS[0]!

function isHexOf(value: string, byteLengths: readonly number[]): boolean {
  if (value.length % 2 !== 0 || !/^[0-9a-f]+$/.test(value)) return false
  return byteLengths.includes(value.length / 2)
}

/**
 * 初始输入：优先读 URL 的 ?pt=&key=（可分享、刷新可复现），
 * 其次兼容旧链接的 ?vector=c3，最后退回 FIPS-197 C.1。
 */
function readInitialInput(): { plaintext: string; key: string } {
  const vector = FIPS_197_VECTORS[route.query.vector === 'c3' ? 2 : 0]!
  const ptRaw = typeof route.query.pt === 'string' ? route.query.pt.toLowerCase() : ''
  const keyRaw = typeof route.query.key === 'string' ? route.query.key.toLowerCase() : ''
  // pt 与 key 各自独立回退：只改密钥（明文保持默认）时，URL 里只有 key，
  // 若要求两者同时存在就会整组退回默认向量，等于密钥丢失。
  return {
    plaintext: isHexOf(ptRaw, [16]) ? ptRaw : vector.plaintext_hex,
    key: isHexOf(keyRaw, [16, 24, 32]) ? keyRaw : vector.key_hex,
  }
}

const input = ref(readInitialInput())
const trace = shallowRef(buildTrace({ plaintext: input.value.plaintext, key: input.value.key }))
const stepIndex = computed(() => playback.currentStep)
const steps = computed(() => trace.value.steps)
const traceId = ref(trace.value.trace_id)

/** B 区提交新输入 → 重建 trace → 回到第 0 步 */
function applyInput(plaintext: string, key: string): void {
  let next: AesTrace
  try {
    next = buildTrace({ plaintext, key })
  } catch (error) {
    announcement.value = error instanceof Error ? error.message : '这组输入无法生成演示'
    return
  }

  playback.pause()
  input.value = { plaintext, key }
  trace.value = next
  traceId.value = next.trace_id
  playback.setStep(0)
  announcement.value = `已生成新的演示，共 ${next.steps.length} 步`

  const query = { ...route.query }
  if (plaintext !== DEFAULT_VECTOR.plaintext_hex) query.pt = plaintext
  else delete query.pt
  if (key !== DEFAULT_VECTOR.key_hex) query.key = key
  else delete query.key
  delete query.vector
  delete query.step
  void router.replace({ query })

  void checkTrace()
}

watch(
  () => playback.currentStep,
  () => {
    if (perfEnabled) beginStep()
  },
  { flush: 'pre' },
)

watch(
  () => playback.isPlaying,
  (playing) => {
    if (!perfEnabled) return
    if (playing) startFrameSampling()
    else stopFrameSampling()
  },
)

watch(presentMode, (value) => {
  document.documentElement.dataset.mode = value ? 'present' : ''
})

function resetFromError(): void {
  crashInjected.value = false
  playback.pause()
  playback.setStep(0)
  presentMode.value = false
  tableView.value = false
  const query = { ...route.query }
  delete query.debug
  delete query.step
  delete query.view
  delete query.present
  void router.replace({ query })
}

function syncUrl(): void {
  const currentStep = route.query.step === undefined ? 0 : Number(route.query.step)
  const currentView = route.query.view === 'table'
  const currentPresent = route.query.present === '1'
  if (
    currentStep === playback.currentStep &&
    currentView === tableView.value &&
    currentPresent === presentMode.value
  ) {
    return
  }
  const query = { ...route.query }
  if (playback.currentStep > 0) query.step = String(playback.currentStep)
  else delete query.step
  if (tableView.value) query.view = 'table'
  else delete query.view
  if (presentMode.value) query.present = '1'
  else delete query.present
  void router.replace({ query })
}

function scheduleUrlSync(): void {
  if (urlTimer !== undefined) clearTimeout(urlTimer)
  urlTimer = setTimeout(() => {
    urlTimer = undefined
    syncUrl()
  }, 300)
}

watch(
  [() => playback.currentStep, tableView, presentMode],
  scheduleUrlSync,
  { flush: 'post' },
)

async function checkTrace(): Promise<void> {
  consistency.value = 'checking'
  try {
    const response = await fetch('/api/aes/trace', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        plaintext_hex: input.value.plaintext,
        key_hex: input.value.key,
        key_bits: input.value.key.length * 4,
        direction: 'encrypt',
      }),
    })
    if (!response.ok) {
      consistency.value = 'offline'
      return
    }
    const data = (await response.json()) as {
      trace_id?: string
      ciphertext?: string
    }
    if (!data.trace_id || data.ciphertext !== trace.value.ciphertext) {
      consistency.value = 'mismatch'
      return
    }
    consistency.value = 'ok'
    traceId.value = data.trace_id
  } catch {
    consistency.value = 'offline'
  }
}

onMounted(() => {
  document.documentElement.dataset.mode = presentMode.value ? 'present' : ''
  if (perfEnabled) installPerfProbe()
  window.addEventListener('online', checkTrace)
  void checkTrace()
})

watch(
  () => trace.value.steps.length,
  (count) => {
    playback.setStepCount(count)
    const requested = Number(route.query.step)
    if (Number.isInteger(requested) && requested >= 0 && requested <= count) {
      playback.setStep(requested)
    }
  },
  { immediate: true },
)

const markers: Record<number, { diag: number; ask: number }> = {
  3: { diag: 1, ask: 0 },
  13: { diag: 1, ask: 2 },
  27: { diag: 0, ask: 1 },
}

const values = computed(() => {
  const steps = trace.value.steps
  if (stepIndex.value === 0) {
    return Uint8Array.from(steps[0]!.state_before)
  }
  const step = steps[stepIndex.value - 1]
  return Uint8Array.from(
    step ? step.state_after : steps[steps.length - 1]!.state_after,
  )
})

const currentOp = computed(() => {
  if (stepIndex.value === 0) return 'none'
  return trace.value.steps[stepIndex.value - 1]?.op ?? 'none'
})

const currentChanged = computed(() => {
  if (stepIndex.value === 0) return []
  return [...(trace.value.steps[stepIndex.value - 1]?.changed ?? [])]
})

const currentStepLabel = computed(() => {
  if (stepIndex.value === 0) return '初始状态'
  return trace.value.steps[stepIndex.value - 1]?.label ?? '未知步骤'
})

const currentTraceStep = computed(() => {
  const steps = trace.value.steps
  return stepIndex.value === 0 ? steps[0] : steps[stepIndex.value - 1]
})

const currentStepBefore = computed(() => [...(currentTraceStep.value?.state_before ?? [])])
const currentStepAfter = computed(() => [...(currentTraceStep.value?.state_after ?? [])])

const currentKeyIndices = computed(() => currentTraceStep.value?.key_indices ?? [])

const focusByte = computed(() => {
  const requested = Number(route.query.step)
  if (!Number.isInteger(requested) || playback.currentStep !== requested) return null
  const byte = Number(route.query.byte)
  return Number.isInteger(byte) && byte >= 0 && byte < 16 ? byte : null
})

const currentRoundKey = computed(() => {
  const steps = trace.value.steps
  const step = stepIndex.value === 0 ? steps[0] : steps[stepIndex.value - 1]
  if (!step || step.op !== 'add_round_key') return new Uint8Array(16)

  const out = new Uint8Array(16)
  step.key_words.forEach((wordIndex, position) => {
    const word = trace.value.key_schedule[wordIndex]
    if (word) out.set(word, position * 4)
  })
  return out
})

const OP_LABELS: Record<string, string> = {
  sub_bytes: '字节代换',
  shift_rows: '行移位',
  mix_columns: '列混合',
  add_round_key: '轮密钥加',
  none: '初始状态',
}

const markerSteps = computed(() =>
  Object.entries(markers)
    .filter(([, value]) => value.diag > 0 || value.ask > 0)
    .map(([key]) => Number(key))
    .sort((a, b) => a - b),
)

watch(
  () => playback.currentStep,
  (step) => {
    if (step === 0) {
      announcement.value = '第 0 步，初始状态'
      return
    }
    const current = trace.value.steps[step - 1]
    if (!current) return
    const roundText =
      current.round === 0
        ? '初始轮密钥加'
        : `${current.round} 轮${OP_LABELS[current.op] ?? current.op}`
    announcement.value = `第 ${step} 步，${roundText}，${current.changed.length} 个字节变化`
  },
  { flush: 'post' },
)

function stepAt(index: number): (typeof trace.value.steps)[number] {
  return index === 0 ? trace.value.steps[0]! : trace.value.steps[index - 1]!
}

function onOpenDrawer(index: number, trigger: HTMLElement): void {
  const step = stepAt(playback.currentStep)
  const value =
    playback.currentStep === 0
      ? step.state_before[index] ?? 0
      : step.state_after[index] ?? 0
  drawer.value = {
    byteIndex: index,
    row: index % 4,
    col: Math.floor(index / 4),
    value,
    before: step.state_before[index] ?? 0,
    after: step.state_after[index] ?? 0,
    stepLabel: playback.currentStep === 0 ? '初始状态' : step.label,
    title: `字节 ${index} · 第 ${index % 4 + 1} 行第 ${Math.floor(index / 4) + 1} 列`,
  }
  drawerTrigger = trigger
}

function onOpenMark(index: number, trigger: HTMLElement): void {
  playback.pause()
  playback.setStep(index)
  const step = stepAt(index)
  drawer.value = {
    byteIndex: 0,
    row: 0,
    col: 0,
    value: index === 0 ? step.state_before[0] ?? 0 : step.state_after[0] ?? 0,
    before: step.state_before[0] ?? 0,
    after: step.state_after[0] ?? 0,
    stepLabel: `第 ${index} 步 · 标记详情`,
    title: `第 ${index} 步 · 标记详情`,
  }
  drawerTrigger = trigger
}

function closeDrawer(): void {
  drawer.value = null
  const trigger = drawerTrigger
  drawerTrigger = null
  void nextTick(() => trigger?.focus({ preventScroll: true }))
}

function toggleTable(): void {
  tableView.value = !tableView.value
  announcement.value = tableView.value ? '已切换到表格视图' : '已切换到矩阵视图'
  void nextTick(() => {
    document
      .querySelector<HTMLElement>('[data-action="table-view"]')
      ?.focus({ preventScroll: true })
  })
}

function roundStep(direction: 1 | -1): void {
  const current = playback.currentStep
  const currentRound = stepAt(current).round
  if (direction > 0) {
    const target = trace.value.steps.findIndex(
      (step, index) => index + 1 > current && step.round > currentRound,
    )
    if (target >= 0) playback.setStep(target + 1)
    return
  }
  for (let index = current - 2; index >= 0; index--) {
    const step = trace.value.steps[index]!
    const next = trace.value.steps[index + 1]
    if (!next || next.round !== step.round) {
      playback.setStep(index + 1)
      return
    }
  }
  playback.setStep(0)
}

function jumpMark(direction: 1 | -1): void {
  const current = playback.currentStep
  const steps = markerSteps.value
  if (steps.length === 0) {
    announcement.value = '本会话还没有标记'
    return
  }
  const target =
    direction > 0
      ? steps.find((step) => step > current)
      : [...steps].reverse().find((step) => step < current)
  if (target === undefined) {
    announcement.value = direction > 0 ? '已是最后一个标记' : '已是第一个标记'
    return
  }
  playback.pause()
  playback.setStep(target)
  void nextTick(() => {
    document
      .querySelector<HTMLElement>(`.c-mark[data-step="${target}"]`)
      ?.focus({ preventScroll: true })
  })
}

function focusAsk(): void {
  document
    .querySelector<HTMLTextAreaElement>('textarea[aria-label="向 AI 提问"]')
    ?.focus({ preventScroll: true })
}

function loadVector(): void {
  applyInput(DEFAULT_VECTOR.plaintext_hex, DEFAULT_VECTOR.key_hex)
  announcement.value = '已载入 FIPS-197 C.1 向量'
  void nextTick(() => {
    document
      .querySelector<HTMLElement>('.c-byte[data-index="0"]')
      ?.focus({ preventScroll: true })
  })
}

function exportTrace(): void {
  const blob = new Blob([JSON.stringify(trace.value, null, 2)], {
    type: 'application/json',
  })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `${trace.value.trace_id}.json`
  anchor.click()
  URL.revokeObjectURL(url)
  announcement.value = '已导出当前 trace'
}

function onEscape(): void {
  if (helpOpen.value) {
    helpOpen.value = false
    return
  }
  if (drawer.value) {
    closeDrawer()
    return
  }
  if (ui.activeChannel === 'tutor') {
    window.dispatchEvent(new CustomEvent('cipherlens:stop-tutor'))
    return
  }
  if (document.querySelector('.c-annotation')) {
    window.dispatchEvent(new CustomEvent('cipherlens:dismiss-diagnosis'))
    return
  }
  if (presentMode.value) {
    presentMode.value = false
    return
  }
  if (playback.isPlaying) playback.pause()
}

function next(): void {
  playback.pause()
  playback.next()
}

function commitStep(index: number): void {
  playback.pause()
  playback.setStep(index)
}

function prev(): void {
  playback.pause()
  playback.prev()
}

function first(): void {
  playback.pause()
  playback.first()
}

function last(): void {
  playback.pause()
  playback.last()
}

function togglePlay(): void {
  playback.toggle()
}

useHotkeys({
  onPlayPause: togglePlay,
  onPrev: prev,
  onNext: next,
  onFirst: first,
  onLast: last,
  onRoundPrev: () => roundStep(-1),
  onRoundNext: () => roundStep(1),
  onPrevMark: () => jumpMark(-1),
  onNextMark: () => jumpMark(1),
  onFocusAsk: focusAsk,
  onEscape,
  onJump: () => {
    document
      .querySelector<HTMLElement>('.c-timeline')
      ?.focus({ preventScroll: true })
  },
  onVector: loadVector,
  onHelp: () => {
    helpOpen.value = true
  },
  onPresent: () => {
    presentMode.value = !presentMode.value
  },
  onExport: exportTrace,
  onSBox: () => {
    void router.push('/sbox')
  },
  onKeyBits: (bits) => {
    // 切密钥位数：hex 字符数 = bits / 4（128 位 → 32 字符）
    const need = bits / 4
    const hex = input.value.key.slice(0, need).padEnd(need, '0')
    if (hex === input.value.key) {
      announcement.value = `密钥已经是 ${bits} 位`
      return
    }
    applyInput(input.value.plaintext, hex)
  },
  onToggleDirection: () => {
    announcement.value = '解密演示未接入'
  },
  onToggleAi: () => {
    announcement.value = 'AI 栏折叠未接入'
  },
  onKeyDrawer: () => {
    announcement.value = '密钥扩展抽屉未接入'
  },
})

onScopeDispose(() => {
  window.removeEventListener('online', checkTrace)
  if (urlTimer !== undefined) clearTimeout(urlTimer)
  document.documentElement.dataset.mode = ''
  if (perfEnabled) disposePerfProbe()
})

if (perfEnabled) {
  const w = window as Window & {
    __CIPHERLENS_TRACE__?: AesTrace
    __CIPHERLENS_PLAYBACK__?: typeof playback
  }
  // 必须跟随 trace 更新：输入换一组数据后，调试钩子还要指向「当前」的 trace
  watch(
    trace,
    (value) => {
      w.__CIPHERLENS_TRACE__ = value
    },
    { immediate: true },
  )
  w.__CIPHERLENS_PLAYBACK__ = playback
}
</script>
<style scoped>
.c-help {
  position: fixed;
  top: 50%;
  left: 50%;
  z-index: 40;
  width: min(560px, 92vw);
  padding: var(--sp-4);
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  background: var(--paper-0);
  box-shadow: 0 12px 40px rgb(0 0 0 / 0.16);
  transform: translate(-50%, -50%);
}

.c-help h2 {
  margin: 0 0 var(--sp-3);
  font-size: var(--fs-body);
  color: var(--ink-1);
}

.c-help ul {
  margin: 0 0 var(--sp-3);
  padding-left: var(--sp-4);
  font-size: var(--fs-ui);
  line-height: var(--lh-body);
  color: var(--ink-2);
}

.c-help button {
  height: 30px;
  padding: 0 var(--sp-3);
  border: var(--rule-region-w) solid var(--accent);
  border-radius: var(--r-control);
  background: transparent;
  font-family: var(--font-ui);
  font-size: var(--fs-label);
  color: var(--accent-strong);
  cursor: pointer;
}
</style>
