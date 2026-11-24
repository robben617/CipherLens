<template>
  <section class="tutor" :class="{ 'is-minimal': minimal }" :data-phase="phase">
    <header v-if="!minimal" class="tutor__head">
      <span class="tutor__ctx">第 {{ stepIndex }} 步 · {{ stepLabel }}</span>
      <span class="tutor__meta">
        <span
          v-if="health.checked"
          class="tutor__llm"
          :data-on="llmActive"
          :title="llmTitle"
          :aria-label="llmTitle"
        >
          <span class="tutor__llm-dot" aria-hidden="true"></span>{{ llmActive ? 'AI' : '本地' }}
        </span>
        <span class="tutor__phase">{{ phaseLabel }}</span>
      </span>
    </header>

    <select
      v-if="debugTutor && !minimal"
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

      <p v-if="degradedLabel" class="tutor__degraded">
        {{ degradedLabel }}
        <button
          v-if="retryable"
          type="button"
          data-action="retry-tutor"
          @click="retry"
        >
          重试
        </button>
      </p>

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
        :tools="tools"
        :search-state="searchState || undefined"
        :search-message="searchMessage"
        :sources="sources"
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

      <p v-if="askBlocked && !minimal" class="tutor__hint" data-disabled-reason>
        {{ disabledText }}
      </p>
      <template v-else-if="!hasContent && !error && !slowHint">
        <p v-if="!minimal" class="tutor__hint">问一句关于当前这一步的问题，比如：这几格为什么一起变？</p>
        <QuickAsk
          :op="op"
          :step-index="stepIndex"
          :step-after="stepAfter"
          :disabled="busy || askBlocked"
          @pick="onQuickPick"
        />
      </template>
    </div>

    <p class="sr-only" aria-live="polite">{{ announcement }}</p>

    <ModelStatusBar class="tutor__model" />

    <div class="tutor__compose">
      <textarea
        v-model="question"
        rows="2"
        aria-label="向 AI 提问"
        :disabled="askBlocked"
        :placeholder="composePlaceholder"
        @keydown.enter.exact.prevent="send"
        @keydown.ctrl.enter.prevent="send"
      ></textarea>
      <div class="tutor__toolbar">
        <button
          type="button"
          class="tutor__web"
          :aria-pressed="webSearch"
          data-action="tutor-web-search"
          title="联网搜索（Tavily）"
          @click="toggleWebSearch"
        >
          <svg viewBox="0 0 16 16" aria-hidden="true" width="12" height="12">
            <circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" stroke-width="1.4" />
            <path d="M2 8h12M8 2c2 2.2 2 9.8 0 12M8 2c-2 2.2-2 9.8 0 12" fill="none" stroke="currentColor" stroke-width="1.2" />
          </svg>
          联网
        </button>
        <span class="tutor__toolbar-spacer"></span>
        <button v-if="busy" type="button" data-action="stop" @click="stop">停止</button>
        <button
          data-action="ask"
          type="button"
          class="tutor__send"
          :disabled="busy || askBlocked"
          @click="send"
        >
          {{ askBlocked ? '先走一步' : busy ? '生成中…' : '发送' }}
        </button>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, onScopeDispose, ref, watch } from 'vue'
import { useSSE } from '../../composables/useSSE'
import { useHealth } from '../../composables/useHealth'
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
import ModelStatusBar from '../shared/ModelStatusBar.vue'
import { useModelConfigStore } from '../../stores/model-config'
import { applyToolEnd, applyToolResult, pushToolStart, type ToolTrace } from '../../utils/tool-trace'
import { readWebSearchEnabled, saveWebSearchEnabled, type SearchSource } from '../../utils/web-search'

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
  /** 极简模式：只保留问题推荐和输入框，隐藏步骤状态/本地标记/提示 */
  minimal?: boolean
}>()

const emit = defineEmits<{
  cite: [byte: number, trigger: HTMLElement]
  goto: [step: number]
  sbox: [byte: number]
}>()

const playback = usePlaybackStore()
const ui = useUiStore()
const modelStore = useModelConfigStore()
const { start, abort } = useSSE()
const { health, probe, refresh } = useHealth()

const params = import.meta.env.DEV ? new URLSearchParams(window.location.search) : null
const debugTutor = params?.get('debug') === 'tutor'
const timingDebug = params?.get('debug') === 'tutor-timing'

const question = ref(props.minimal ? '' : '这一步为什么这么做？')
const tools = ref<ToolTrace[]>([])
const webSearch = ref(readWebSearchEnabled())
const searchState = ref<'searching' | 'done' | 'fail' | ''>('')
const searchMessage = ref('')
const sources = ref<SearchSource[]>([])
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
const retryable = ref(false)
/** 这次会话里模型已经掉过链子：状态点跟着退回「本地」，别让界面自相矛盾 */
const fellBack = ref(false)
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

const composePlaceholder = computed(() => {
  if (props.minimal) return askBlocked.value ? '先走一步再提问' : '问这一步…'
  return askBlocked.value ? disabledText.value : '问这一步…（Enter 发送，Shift+Enter 换行）'
})

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

const hasContent = computed(
  () => blocks.value.length > 0 || tools.value.length > 0 || searchState.value !== '',
)
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

/** 状态点说的是「这一路现在会用什么」，不是「AI 好不好用」 */
const llmActive = computed(() => health.value.llm && !fellBack.value)

const llmTitle = computed(() => {
  if (fellBack.value) {
    return '刚才连不上模型，这一路已退回本地讲解；配置恢复后点「重试」会重新探测'
  }
  return health.value.llm
    ? `回答由 ${health.value.model ?? '在线模型'} 生成；连不上时自动降级为本地讲解`
    : '未配置模型：回答由本地模板按当前步的数值生成，功能完整'
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
  // 模型这条路要留出「首字 20s + 重试 30s」，和后端 LLM_DEADLINE_S 对齐；
  // 本地模板是纯内存拼装，20 秒还没讲完一定是卡住了。
  const totalWait = health.value.llm ? 55000 : 20000
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
    degradedLabel.value = `本地讲解（${Math.round(totalWait / 1000)} 秒没有回应）`
    blocks.value = fallbackBlocks()
    announcement.value = answer.value
    finished.value = true
    ui.setChannel('idle')
    clearTimers()
  }, totalWait)
}

function toggleWebSearch(): void {
  webSearch.value = !webSearch.value
  saveWebSearchEnabled(webSearch.value)
}

function resetView(): void {
  blocks.value = []
  tools.value = []
  searchState.value = ''
  searchMessage.value = ''
  sources.value = []
  error.value = ''
  errorCode.value = ''
  source.value = 'local'
  model.value = null
  announcement.value = ''
  collapsed.value = false
  slowHint.value = false
  generic.value = false
  degradedLabel.value = ''
  retryable.value = false
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
  question.value = ''
  resetView()
  phase.value = 'waiting'
  armTimers()

  if (timingDebug) return

  const llm = modelStore.requestPayload()
  start(
    '/api/tutor/ask',
    {
      trace_id: props.traceId,
      step_index: traceStepIndex.value,
      question: text,
      ...(llm ? { llm } : {}),
      web_search: webSearch.value,
    },
    {
      onMeta: (data) => {
        instant.value = data.cache === true
        generic.value = data.quotes_values === false
        source.value = data.source === 'llm' ? 'llm' : 'local'
        if (source.value === 'llm') fellBack.value = false
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
      onToolStart: (data) => {
        pushToolStart(tools.value, data)
      },
      onToolResult: (data) => {
        applyToolResult(tools.value, data)
      },
      onToolEnd: (data) => {
        applyToolEnd(tools.value, data)
      },
      onSearchStart: () => {
        searchState.value = 'searching'
        searchMessage.value = ''
      },
      onSearchResult: (data) => {
        if (data.ok === true && Array.isArray(data.sources)) {
          sources.value = (data.sources as SearchSource[]).filter(
            (item) => typeof item?.url === 'string' && typeof item?.title === 'string',
          )
          searchState.value = 'done'
        } else {
          searchState.value = 'fail'
          searchMessage.value =
            typeof data.message === 'string' ? data.message : '联网搜索失败'
          sources.value = []
        }
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
      onError: (code, message, payload) => {
        clearTimers()
        finished.value = true
        if (code === 'llm_unavailable' && hasContent.value) {
          // 内容已经推到屏幕上了（本地模板顶上 / 模型写了一半）：
          // 不推翻重来，只说清「这段从哪来」「还能不能再试」。
          const partial = payload?.partial === true
          if (!partial) source.value = 'local'
          fellBack.value = true
          phase.value = 'done'
          retryable.value = payload?.retryable !== false
          degradedLabel.value = partial
            ? '模型中途断开，这段回答不完整'
            : '模型暂时不可用，这段是本地讲解'
          announcement.value = answer.value
          ui.setChannel('idle')
          return
        }
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

/** 降级后点「重试」：先重探一次能力（后端可能刚配好 key），再原样重问 */
function retry(): void {
  if (busy.value) return
  retryable.value = false
  fellBack.value = false
  void refresh()
  send()
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
  // 能力探测不阻塞任何交互：结果回来才点亮状态点
  void probe()
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

.tutor.is-minimal {
  gap: var(--sp-3);
}

.tutor.is-minimal .tutor__body {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.tutor.is-minimal .tutor__compose {
  margin-top: auto;
}

.tutor__head {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--sp-1) var(--sp-2);
}

.tutor__meta {
  display: flex;
  align-items: baseline;
  gap: var(--sp-2);
  flex: none;
}

.tutor__llm {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  letter-spacing: var(--ls-label);
  color: var(--ink-3);
  cursor: help;
}

.tutor__llm-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--ink-4);
}

.tutor__llm[data-on='true'] {
  color: var(--accent-strong);
}

.tutor__llm[data-on='true'] .tutor__llm-dot {
  background: var(--accent);
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

.tutor__degraded button {
  margin-left: var(--sp-1);
  padding: 0;
  border: 0;
  border-bottom: var(--rule-region-w) solid currentColor;
  background: transparent;
  font-family: var(--font-ui);
  font-size: var(--fs-micro);
  color: var(--accent-strong);
  cursor: pointer;
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
  gap: var(--sp-1);
  padding: 6px;
  border: var(--rule-region-w) solid var(--line-default);
  border-radius: 12px;
  background: var(--paper-0);
  box-shadow: var(--shadow-float);
}

.tutor__compose textarea {
  width: 100%;
  resize: none;
  min-height: 44px;
  padding: 6px 8px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  font-family: var(--font-ui);
  font-size: var(--fs-ui);
  line-height: var(--lh-body);
  color: var(--ink-1);
}

.tutor__compose textarea:focus {
  outline: none;
}

.tutor__toolbar {
  display: flex;
  align-items: center;
  gap: var(--sp-1);
  padding: 0 2px;
}

.tutor__toolbar-spacer {
  flex: 1;
}

.tutor__web {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 24px;
  padding: 0 9px;
  border: var(--rule-region-w) solid var(--line-default);
  border-radius: 999px;
  background: transparent;
  font-size: var(--fs-micro);
  color: var(--ink-3);
  cursor: pointer;
}

.tutor__web[aria-pressed='true'] {
  border-color: var(--accent);
  background: var(--accent-soft);
  color: var(--accent-strong);
}

.tutor__toolbar button[data-action='stop'] {
  height: 28px;
  padding: 0 10px;
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  background: transparent;
  font-size: var(--fs-label);
  color: var(--ink-3);
  cursor: pointer;
}

.tutor__send {
  height: 28px;
  min-width: 56px;
  padding: 0 12px;
  border: 0;
  border-radius: 14px;
  background: var(--accent);
  font-family: var(--font-ui);
  font-size: var(--fs-label);
  color: var(--paper-0);
  cursor: pointer;
}

.tutor__send:disabled {
  background: var(--surface-inset);
  color: var(--ink-3);
  cursor: default;
}

/* 用户提问：右侧气泡，AI 回答保持无气泡长文 */
.tutor__question {
  align-self: flex-end;
  max-width: 86%;
  margin: 0 0 var(--sp-2);
  padding: 6px 10px;
  border-radius: 10px 10px 2px 10px;
  background: var(--accent-soft);
  font-size: var(--fs-ui);
  line-height: var(--lh-snug);
  color: var(--ink-1);
  overflow-wrap: anywhere;
}

</style>
