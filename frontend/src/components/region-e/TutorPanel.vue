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

      <div v-if="collapsed && answer" class="tutor__collapsed">
        <span class="tutor__collapsed-text">{{ firstLine }}</span>
        <button type="button" @click="collapsed = false">展开</button>
      </div>
      <p v-else-if="answer" class="tutor__answer">
        <template v-for="(segment, index) in segments" :key="index">
          <button
            v-if="segment.numeric"
            class="tutor__num"
            type="button"
            :title="`引用本步数值：${segment.text}`"
            :aria-label="`引用本步数值：${segment.text}`"
            @click="quote(segment.text)"
          >
            {{ segment.text }}
          </button>
          <span v-else>{{ segment.text }}</span>
        </template>
      </p>

      <p v-if="quoted" class="tutor__quoted">引用本步数值：{{ quoted }}</p>
      <p v-if="error" class="tutor__error">
        {{ error }}
        <button type="button" @click="send">重试</button>
      </p>
      <p v-if="askBlocked" class="tutor__hint" data-disabled-reason>
        {{ disabledText }}
      </p>
      <p v-else-if="!answer && !error && !slowHint" class="tutor__hint">
        数字会高亮；点击可引用本步数值。
      </p>
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
  stepBefore: readonly number[]
  stepAfter: readonly number[]
  changed: readonly number[]
  askDisabled?: boolean
  disabledReason?: string
}>()

const playback = usePlaybackStore()
const ui = useUiStore()
const { start, abort } = useSSE()

const params = import.meta.env.DEV ? new URLSearchParams(window.location.search) : null
const debugTutor = params?.get('debug') === 'tutor'
const timingDebug = params?.get('debug') === 'tutor-timing'

const question = ref('这一步为什么这么做？')
const questionSubmitted = ref('')
const answer = ref('')
const phase = ref<Phase>('idle')
const error = ref('')
const meta = ref<Record<string, unknown> | null>(null)
const announcement = ref('')
const collapsed = ref(false)
const quoted = ref('')
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
    offline: '离线讲解',
    error: '出错',
    interrupted: '已中断',
    collapsed: '已折叠',
  }
  return labels[phase.value]
})

const hex = (values: readonly number[]): string =>
  values.map((value) => value.toString(16).toUpperCase().padStart(2, '0')).join(' ')

const localPoints = computed(
  () =>
    `输入：${hex(props.stepBefore)}；输出：${hex(props.stepAfter)}；变化：${props.changed.length ? props.changed.join(',') : '无'}`,
)

const localTemplate = computed(
  () =>
    `模型 20s 未返回，以下为本地要点。第 ${props.stepIndex} 步 ${props.stepLabel}。输入状态：${hex(props.stepBefore)}。输出状态：${hex(props.stepAfter)}。变化字节：${props.changed.join(',') || '无'}。数值来自服务端 trace。`,
)

interface Segment {
  text: string
  numeric: boolean
}

const segments = computed<Segment[]>(() =>
  answer.value
    .split(/(\b[0-9A-Fa-f]{2}\b|\b\d{1,3}\b)/g)
    .filter(Boolean)
    .map((text) => ({
      text,
      numeric: /^(?:[0-9A-Fa-f]{2}|\d{1,3})$/.test(text),
    })),
)

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
    degradedLabel.value = '离线讲解'
    answer.value = localTemplate.value
    announcement.value = answer.value
    finished.value = true
    ui.setChannel('idle')
    clearTimers()
  }, 20000)
}

function resetView(): void {
  answer.value = ''
  error.value = ''
  meta.value = null
  announcement.value = ''
  collapsed.value = false
  quoted.value = ''
  slowHint.value = false
  generic.value = false
  degradedLabel.value = ''
  instant.value = false
  finished.value = false
}

function quote(value: string): void {
  quoted.value = value
}

function send(): void {
  if (busy.value || askBlocked.value) return
  const text = question.value.trim()
  if (!text) return
  if (!props.traceId) {
    phase.value = 'error'
    error.value = '缺少 trace_id，无法提问'
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
        meta.value = data
        instant.value = data.cache === true
        generic.value = data.quotes_values === false
        if (firstTimer !== undefined) clearTimeout(firstTimer)
        firstTimer = undefined
        slowHint.value = false
        if (instant.value) phase.value = 'cache'
        else if (generic.value) phase.value = 'generic'
        else phase.value = 'streaming'
      },
      onToken: (token) => {
        answer.value += token
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
        error.value = message || code
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

const DEMO_ANSWER = '这一步是第 3 轮 轮密钥加。示例：4C 9C 1E 66 F7 71 F0 76 2C 3F 86 8E 53 4D F2 56。'

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
    answer.value = '这一步是第 3 轮 轮密钥加。'
    ui.setChannel('tutor')
  } else if (state === 'done') {
    answer.value = DEMO_ANSWER
    announcement.value = answer.value
    ui.setChannel('idle')
  } else if (state === 'cache') {
    instant.value = true
    answer.value = DEMO_ANSWER
    announcement.value = answer.value
    ui.setChannel('idle')
  } else if (state === 'generic') {
    generic.value = true
    answer.value = '这是未引用当前数值的通用讲解。'
    ui.setChannel('idle')
  } else if (state === 'offline') {
    degradedLabel.value = '离线讲解'
    answer.value = localTemplate.value
    announcement.value = answer.value
    ui.setChannel('idle')
  } else if (state === 'error') {
    error.value = '网络连接失败，请重试。'
    ui.setChannel('idle')
  } else if (state === 'interrupted') {
    degradedLabel.value = '已中断'
    answer.value = '回答已中断，可重试。'
    announcement.value = answer.value
    ui.setChannel('idle')
  } else if (state === 'collapsed') {
    collapsed.value = true
    answer.value = DEMO_ANSWER
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
    if (answer.value) {
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

.tutor__answer {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: var(--fs-body);
  line-height: var(--lh-body);
  color: var(--ink-1);
}

.tutor__num {
  padding: 0 2px;
  border: 0;
  border-bottom: var(--rule-region-w) solid var(--accent);
  background: var(--accent-soft);
  font-family: var(--font-mono);
  font-size: inherit;
  font-variant-numeric: tabular-nums;
  color: var(--accent-strong);
  cursor: pointer;
}

.tutor__quoted {
  margin: var(--sp-2) 0 0;
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-3);
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

.tutor__error {
  margin: var(--sp-2) 0 0;
  font-size: var(--fs-ui);
  color: var(--st-error);
}

.tutor__hint {
  margin: 0;
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