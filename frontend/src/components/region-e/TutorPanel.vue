<template>
  <section class="tutor" :data-phase="phase">
    <header class="tutor__head">
      <span class="tutor__ctx">第 {{ stepIndex }} 步 · {{ stepLabel }}</span>
      <span class="tutor__phase">{{ phaseLabel }}</span>
    </header>

    <select
      v-if="debugTutor"
      class="tutor__debug"
      data-debug-state
      :value="phase"
      @change="onDebugChange"
    >
      <option value="idle">idle</option>
      <option value="waiting">waiting</option>
      <option value="slow">slow</option>
      <option value="streaming">streaming</option>
      <option value="done">done</option>
      <option value="cache">cache</option>
      <option value="generic">generic</option>
      <option value="offline">offline</option>
      <option value="error">error</option>
      <option value="interrupted">interrupted</option>
      <option value="collapsed">collapsed</option>
    </select>

    <div class="tutor__body">
      <p v-if="questionSubmitted" class="tutor__question">{{ questionSubmitted }}</p>

      <p v-if="degradedLabel" class="tutor__degraded">{{ degradedLabel }}</p>

      <div v-if="slowHint" class="tutor__local">
        <strong>先看本地要点</strong>
        <p>{{ localPoints }}</p>
        <button type="button" data-action="reask" @click="send">带上这一步的数据重问</button>
      </div>

      <div v-if="generic" class="tutor__generic">
        通用讲解（未引用当前数值）
        <button type="button" data-action="reask" @click="send">带上这一步的数据重问</button>
      </div>

      <div v-if="collapsed && hasContent" class="tutor__collapsed">
        <span class="tutor__collapsed-text">{{ firstLine }}</span>
        <button type="button" @click="collapsed = false">展开</button>
      </div>
      <TutorMessage
        v-else-if="hasContent"
        :blocks="blocks"
        :source="source"
        :model="model"
        :streaming="streamingNow"
        @cite="onCite"
        @action="onAction"
      />

      <div v-if="error" class="tutor__errcard" data-tutor-error>
        <p class="tutor__errcode">{{ errorCode || 'error' }}</p>
        <p class="tutor__errmsg">{{ error }}</p>
        <div class="tutor__erracts">
          <button type="button" data-action="retry" @click="send">重试</button>
          <button type="button" data-action="local-explain" @click="useFallback">看本地讲解</button>
        </div>
      </div>

      <p v-if="askBlocked" class="tutor__hint" data-disabled-reason>
        {{ disabledText }}
      </p>
      <template v-else-if="!hasContent && !error && !slowHint">
        <p class="tutor__hint">问一句关于当前这一步的问题，比如：这几格为什么一起变？</p>
        <QuickAsk
          :op="op"
          :step-index="stepIndex"
          :step-after="stepAfter"
          :disabled="busy"
          @pick="onQuickPick"
        />
      </template>
    </div>

    <p class="sr-only" aria-live="polite">{{ announcement }}</p>

    <div class="tutor__compose">
      <textarea
        v-model="question"
        rows="2"
        aria-label="向 AI 提问"
        :disabled="askBlocked"
        :placeholder="askBlocked ? disabledText : '问这一步…（Enter 发送，Shift+Enter 换行）'"
        @keydown.enter.exact.prevent="send"
        @keydown.ctrl.enter.prevent="send"
      ></textarea>
      <div class="tutor__actions">
        <button v-if="busy" type="button" data-action="stop" @click="stop">停止</button>
        <button data-action="ask" type="button" :disabled="busy || askBlocked" @click="send">
          {{ askBlocked ? '先走一步' : busy ? '生成中…' : '发送' }}
        </button>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, onScopeDispose, ref, watch } from 'vue'
import { useSSE } from '../../composables/useSSE'
import { usePlaybackStore } from '../../stores/playback'
import { useUiStore } from '../../stores/ui'
import {
  appendBlock,
  appendToken,
  blocksToText,
  type TutorAction,
  type TutorBlock,
} from '../../utils/tutor-message'
import TutorMessage from './TutorMessage.vue'
import QuickAsk from './QuickAsk.vue'

type Phase =
  | 'idle'
  | 'waiting'
  | 'slow'
  | 'streaming'
  | 'done'
  | 'cache'
  | 'generic'
  | 'offline'
  | 'error'
  | 'interrupted'
  | 'collapsed'

const props = defineProps<{
  traceId: string
  stepIndex: number
  stepLabel: string
  op: string
  stepBefore: readonly number[]
  stepAfter: readonly number[]
  changed: readonly number[]
  askDisabled?: boolean
  disabledReason?: string
}>()

const emit = defineEmits<{
  cite: [byte: number, trigger: HTMLElement]
  goto: [step: number]
  sbox: [byte: number]
}>()

const playback = usePlaybackStore()
const ui = useUiStore()
const { start, abort } = useSSE()

const params = import.meta.env.DEV ? new URLSearchParams(window.location.search) : null
const debugTutor = params?.get('debug') === 'tutor'
const timingDebug = params?.get('debug') === 'tutor-timing'

const question = ref('这一步为什么这么做？')
const questionSubmitted = ref('')
const blocks = ref<TutorBlock[]>([])
const phase = ref<Phase>('idle')
const error = ref('')
const errorCode = ref('')
const source = ref<'llm' | 'local'>('local')
const model = ref<string | null>(null)
const announcement = ref('')
const collapsed = ref(false)
const slowHint = ref(false)
const generic = ref(false)
const degradedLabel = ref('')
const instant = ref(false)
const finished = ref(false)

let firstTimer: ReturnType<typeof setTimeout> | undefined
let totalTimer: ReturnType<typeof setTimeout> | undefined

const stepZero = computed(() => props.stepIndex === 0)
const askBlocked = computed(() => props.askDisabled === true || stepZero.value)
const disabledText = computed(
  () =>
    props.disabledReason ||
    '先走一步，我才能讲你看到的东西',
)

const busy = computed(
  () =>
    phase.value === 'waiting' ||
    phase.value === 'slow' ||
    phase.value === 'streaming' ||
    ((phase.value === 'generic' || phase.value === 'cache') && !finished.value),
)

/** 流式光标只在「文字还在进来」时闪，done 之后立刻停 */
const streamingNow = computed(
  () => phase.value === 'waiting' || phase.value === 'slow' || phase.value === 'streaming',
)

const hasContent = computed(() => blocks.value.length > 0)
const answer = computed(() => blocksToText(blocks.value))

const traceStepIndex = computed(() => Math.max(0, props.stepIndex - 1))

const phaseLabel = computed(() => {
  const labels: Record<Phase, string> = {
    idle: '待提问',
    waiting: '等待首字…',
    slow: '首字慢',
    streaming: '讲解中…',
    done: '已完成',
    cache: '缓存命中',
    generic: '通用讲解',
    offline: '本地讲解',
    error: '出错',
    interrupted: '已中断',
    collapsed: '已折叠',
  }
  return labels[phase.value]
})

/** 错误码对人话：界面上「HTTP 500」对初学者等于什么也没说 */
const ERROR_TEXT: Record<string, string> = {
  network_error: '没能连上服务端。检查一下网络，或者确认后端已经启动。',
  timeout: '服务端太久没有回应了。可以重试，也可以先看本地讲解。',
  trace_not_found: '这一步的数据已经过期。重新生成一次演示就能接着问。',
  step_out_of_range: '这一步不在当前演示里，先回到正在看的那一步再问。',
  missing_trace: '缺少这一步的数据，暂时没法提问。',
}

const hex = (values: readonly number[]): string =>
  values.map((value) => value.toString(16).toUpperCase().padStart(2, '0')).join(' ')

const localPoints = computed(
  () =>
    `输入：${hex(props.stepBefore)}；输出：${hex(props.stepAfter)}；变化：${props.changed.length ? props.changed.join(',') : '无'}`,
)

/** 本地兜底：断网 / 主动要「看本地讲解」时用，结构与在线回答一致，只是没有逐条解释 */
function fallbackBlocks(): TutorBlock[] {
  return [
    {
      type: 'conclusion',
      text: '以下是本地讲解：内容由当前步的数值直接生成，没有经过模型。',
    },
    {
      type: 'why',
      items: [
        `这一步的输入状态：${hex(props.stepBefore)}`,
        `这一步的输出状态：${hex(props.stepAfter)}`,
        `变化的字节：${props.changed.length ? props.changed.map((index) => `第 ${index} 格`).join('、') : '无'}`,
      ],
    },
    {
      type: 'next',
      text: '网络恢复后再问一次，会得到逐条解释和可点的依据。',
    },
  ]
}

function demoBlocks(): TutorBlock[] {
  return [
    { type: 'conclusion', text: '这一步把整列 4 个字节都改了。' },
    {
      type: 'why',
      items: [
        '列混合对每列做 GF(2⁸) 上的矩阵乘法',
        '一格里乘了 2 或 3，结果会扩散到同列其他格',
        '所以只要 1 格变，这一列的 4 格都会变',
      ],
    },
    {
      type: 'next',
      text: '下一步会把这一列的结果和轮密钥异或。',
      action: { label: `看第 ${props.stepIndex + 1} 步`, kind: 'goto-step', value: props.stepIndex + 1 },
    },
    { type: 'cite', bytes: props.changed.length ? [...props.changed.slice(0, 3)] : [0, 1, 2] },
  ]
}

const firstLine = computed(() => {
  const line = answer.value.replace(/\s+/g, ' ').trim()
  return line.length > 64 ? `${line.slice(0, 64)}…` : line
})

function clearTimers(): void {
  if (firstTimer !== undefined) clearTimeout(firstTimer)
  if (totalTimer !== undefined) clearTimeout(totalTimer)
  firstTimer = undefined
  totalTimer = undefined
}

function armTimers(): void {
  clearTimers()
  firstTimer = setTimeout(() => {
    if (phase.value === 'waiting') {
      phase.value = 'slow'
      slowHint.value = true
    }
  }, 3000)
  totalTimer = setTimeout(() => {
    if (!busy.value) return
    abort()
    phase.value = 'offline'
    slowHint.value = false
    degradedLabel.value = '本地讲解（20 秒没有回应）'
    blocks.value = fallbackBlocks()
    announcement.value = answer.value
    finished.value = true
    ui.setChannel('idle')
    clearTimers()
  }, 20000)
}

function resetView(): void {
  blocks.value = []
  error.value = ''
  errorCode.value = ''
  source.value = 'local'
  model.value = null
  announcement.value = ''
  collapsed.value = false
  slowHint.value = false
  generic.value = false
  degradedLabel.value = ''
  instant.value = false
  finished.value = false
}

function useFallback(): void {
  error.value = ''
  errorCode.value = ''
  phase.value = 'offline'
  degradedLabel.value = '本地讲解'
  blocks.value = fallbackBlocks()
  announcement.value = answer.value
  finished.value = true
  ui.setChannel('idle')
}

function onQuickPick(text: string): void {
  if (busy.value || askBlocked.value) return
  question.value = text
  send()
}

function onCite(byte: number, trigger: HTMLElement): void {
  emit('cite', byte, trigger)
}

function onAction(action: TutorAction): void {
  if (action.kind === 'open-sbox') emit('sbox', action.value)
  else emit('goto', action.value)
}

function send(): void {
  if (busy.value || askBlocked.value) return
  const text = question.value.trim()
  if (!text) return
  if (!props.traceId) {
    phase.value = 'error'
    errorCode.value = 'missing_trace'
    error.value = ERROR_TEXT.missing_trace ?? '缺少这一步的数据'
    return
  }

  playback.pause()
  ui.setChannel('tutor')
  questionSubmitted.value = text
  resetView()
  phase.value = 'waiting'
  armTimers()

  if (timingDebug) return

  start(
    '/api/tutor/ask',
    {
      trace_id: props.traceId,
      step_index: traceStepIndex.value,
      question: text,
    },
    {
      onMeta: (data) => {
        instant.value = data.cache === true
        generic.value = data.quotes_values === false
        source.value = data.source === 'llm' ? 'llm' : 'local'
        model.value = typeof data.model === 'string' ? data.model : null
        if (firstTimer !== undefined) clearTimeout(firstTimer)
        firstTimer = undefined
        slowHint.value = false
        if (instant.value) phase.value = 'cache'
        else if (generic.value) phase.value = 'generic'
        else phase.value = 'streaming'
      },
      onBlock: (block) => {
        appendBlock(blocks.value, block)
        if (firstTimer !== undefined) clearTimeout(firstTimer)
        firstTimer = undefined
        slowHint.value = false
        if (phase.value === 'waiting' || phase.value === 'slow') phase.value = 'streaming'
      },
      onToken: (token, payload) => {
        appendToken(blocks.value, token, payload?.item === true)
        if (firstTimer !== undefined) clearTimeout(firstTimer)
        firstTimer = undefined
        slowHint.value = false
        if (phase.value === 'waiting' || phase.value === 'slow') phase.value = 'streaming'
      },
      onDone: () => {
        clearTimers()
        slowHint.value = false
        finished.value = true
        if (instant.value) phase.value = 'cache'
        else if (generic.value) phase.value = 'generic'
        else phase.value = 'done'
        announcement.value = answer.value
        ui.setChannel('idle')
      },
      onError: (code, message) => {
        clearTimers()
        finished.value = true
        phase.value = 'error'
        errorCode.value = code
        error.value = ERROR_TEXT[code] ?? (message || code)
        ui.setChannel('idle')
      },
    },
  )
}

function stop(): void {
  abort()
  clearTimers()
  finished.value = true
  phase.value = 'interrupted'
  degradedLabel.value = '已中断'
  slowHint.value = false
  announcement.value = answer.value
  ui.setChannel('idle')
}

function forceState(state: Phase): void {
  abort()
  clearTimers()
  resetView()
  phase.value = state
  finished.value = state !== 'idle' && state !== 'waiting' && state !== 'slow' && state !== 'streaming'

  if (state === 'waiting') {
    ui.setChannel('tutor')
  } else if (state === 'slow') {
    slowHint.value = true
    ui.setChannel('tutor')
  } else if (state === 'streaming') {
    blocks.value = [demoBlocks()[0]!]
    ui.setChannel('tutor')
  } else if (state === 'done' || state === 'cache') {
    instant.value = state === 'cache'
    blocks.value = demoBlocks()
    announcement.value = answer.value
    ui.setChannel('idle')
  } else if (state === 'generic') {
    generic.value = true
    blocks.value = [{ type: 'conclusion', text: '这是未引用当前数值的通用讲解。' }]
    ui.setChannel('idle')
  } else if (state === 'offline') {
    degradedLabel.value = '本地讲解'
    blocks.value = fallbackBlocks()
    announcement.value = answer.value
    ui.setChannel('idle')
  } else if (state === 'error') {
    errorCode.value = 'network_error'
    error.value = ERROR_TEXT.network_error ?? '网络连接失败'
    ui.setChannel('idle')
  } else if (state === 'interrupted') {
    degradedLabel.value = '已中断'
    blocks.value = [{ type: 'conclusion', text: '回答已中断，可以重试。' }]
    announcement.value = answer.value
    ui.setChannel('idle')
  } else if (state === 'collapsed') {
    collapsed.value = true
    blocks.value = demoBlocks()
    ui.setChannel('idle')
  } else {
    ui.setChannel('idle')
  }
}

function onDebugChange(event: Event): void {
  forceState((event.target as HTMLSelectElement).value as Phase)
}

watch(
  () => props.stepIndex,
  () => {
    clearTimers()
    if (busy.value) {
      abort()
      slowHint.value = false
      ui.setChannel('idle')
    }
    if (hasContent.value) {
      phase.value = 'collapsed'
      collapsed.value = true
    } else if (!busy.value) {
      phase.value = 'idle'
    }
  },
)

function onStopRequest(): void {
  if (busy.value) stop()
}

onMounted(() => {
  window.addEventListener('cipherlens:stop-tutor', onStopRequest)
})

onScopeDispose(() => {
  window.removeEventListener('cipherlens:stop-tutor', onStopRequest)
  clearTimers()
  abort()
  ui.setChannel('idle')
})
</script>

<style scoped>
.tutor {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  gap: var(--sp-2);
  font-family: var(--font-ui);
}

.tutor__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--sp-2);
}

.tutor__ctx {
  font-family: var(--font-mono);
  font-size: var(--fs-label);
  color: var(--ink-3);
}

.tutor__phase {
  font-size: var(--fs-micro);
  color: var(--ink-3);
  white-space: nowrap;
}

.tutor__debug {
  align-self: flex-start;
  height: 24px;
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  background: var(--paper-0);
  font-family: var(--font-ui);
  font-size: var(--fs-micro);
  color: var(--ink-2);
}

.tutor__body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding-right: var(--sp-1);
}

.tutor__question {
  margin: 0 0 var(--sp-2);
  font-size: var(--fs-ui);
  color: var(--ink-2);
}

.tutor__degraded {
  margin: 0 0 var(--sp-2);
  padding: 2px var(--sp-2);
  border-left: var(--rule-scope-w) solid var(--warn);
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-2);
}

.tutor__local,
.tutor__generic {
  margin: 0 0 var(--sp-2);
  padding: var(--sp-2);
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  background: var(--surface-inset);
  font-size: var(--fs-ui);
}

.tutor__local p {
  margin: var(--sp-1) 0;
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  line-height: var(--lh-mono);
  color: var(--ink-2);
  word-break: break-all;
}

.tutor__local button,
.tutor__generic button {
  padding: 0;
  border: 0;
  background: transparent;
  font-family: var(--font-ui);
  font-size: var(--fs-micro);
  color: var(--accent-strong);
  cursor: pointer;
}

.tutor__collapsed {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  min-width: 0;
}

.tutor__collapsed-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: var(--fs-ui);
  color: var(--ink-3);
}

.tutor__collapsed button,
.tutor__error button {
  border: 0;
  background: transparent;
  font-family: var(--font-ui);
  font-size: var(--fs-micro);
  color: var(--accent-strong);
  cursor: pointer;
}

.tutor__errcard {
  margin-top: var(--sp-2);
  padding: var(--sp-2);
  border: var(--rule-region-w) solid var(--st-error);
  border-radius: var(--r-control);
  background: var(--st-error-fill);
}

.tutor__errcode {
  margin: 0;
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  letter-spacing: var(--ls-label);
  color: var(--st-error);
}

.tutor__errmsg {
  margin: var(--sp-1) 0 var(--sp-2);
  font-size: var(--fs-ui);
  line-height: var(--lh-body);
  color: var(--ink-1);
}

.tutor__erracts {
  display: flex;
  gap: var(--sp-3);
}

.tutor__erracts button {
  padding: 0;
  border: 0;
  border-bottom: var(--rule-region-w) solid currentColor;
  background: transparent;
  font-family: var(--font-ui);
  font-size: var(--fs-micro);
  color: var(--accent-strong);
  cursor: pointer;
}

.tutor__hint {
  margin: 0 0 var(--sp-2);
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

.tutor__compose {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.tutor__compose textarea {
  width: 100%;
  resize: vertical;
  min-height: 44px;
  padding: var(--sp-2);
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  background: var(--paper-0);
  font-family: var(--font-ui);
  font-size: var(--fs-ui);
  line-height: var(--lh-body);
  color: var(--ink-1);
}

.tutor__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--sp-2);
}

.tutor__actions button {
  height: 28px;
  padding: 0 var(--sp-3);
  border: var(--rule-region-w) solid var(--accent);
  border-radius: var(--r-control);
  background: transparent;
  font-family: var(--font-ui);
  font-size: var(--fs-label);
  color: var(--accent-strong);
  cursor: pointer;
}

.tutor__actions button[data-action="stop"] {
  border-color: var(--line-hairline);
  color: var(--ink-3);
}

.tutor__actions button:disabled {
  border-color: var(--line-hairline);
  color: var(--ink-3);
  cursor: default;
}

@media (max-width: 69.9375rem) {
  .tutor {
    display: none;
  }
}

[data-mode="present"] .tutor {
  display: none;
}
</style>
