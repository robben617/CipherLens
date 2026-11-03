<template>
  <section class="tutor" :data-phase="phase">
    <header class="tutor__head">
      <span class="tutor__ctx">第 {{ stepIndex }} 步 · {{ stepLabel }}</span>
      <span class="tutor__phase">{{ phaseLabel }}</span>
    </header>

    <div class="tutor__body">
      <p v-if="questionSubmitted" class="tutor__question">{{ questionSubmitted }}</p>

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
      <p v-if="!answer && !error" class="tutor__hint">数字会高亮；点击可引用本步数值。</p>
    </div>

    <p class="sr-only" aria-live="polite">{{ announcement }}</p>

    <div class="tutor__compose">
      <textarea
        v-model="question"
        rows="2"
        aria-label="向 AI 提问"
        placeholder="问这一步…（Ctrl+Enter 发送）"
        @keydown.ctrl.enter.prevent="send"
      ></textarea>
      <button data-action="ask" type="button" :disabled="busy" @click="send">
        {{ busy ? '生成中…' : '发送' }}
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onScopeDispose, ref, watch } from 'vue'
import { useSSE } from '../../composables/useSSE'
import { usePlaybackStore } from '../../stores/playback'
import { useUiStore } from '../../stores/ui'

const props = defineProps<{
  traceId: string
  stepIndex: number
  stepLabel: string
}>()

const playback = usePlaybackStore()
const ui = useUiStore()
const { start, abort } = useSSE()

const question = ref('这一步为什么这么做？')
const questionSubmitted = ref('')
const answer = ref('')
const phase = ref<'idle' | 'waiting' | 'streaming' | 'done' | 'error'>('idle')
const error = ref('')
const meta = ref<Record<string, unknown> | null>(null)
const announcement = ref('')
const collapsed = ref(false)
const quoted = ref('')

const busy = computed(() => phase.value === 'waiting' || phase.value === 'streaming')

// UI 的 currentStep=0 是明文初始态，1 才对应 trace.steps[0]。
// 提问取“当前显示态的终态”，因此送 stepIndex-1，不能直接送 stepIndex。
const traceStepIndex = computed(() => Math.max(0, props.stepIndex - 1))

const phaseLabel = computed(() => {
  if (phase.value === 'waiting') return '等待首字…'
  if (phase.value === 'streaming') return '讲解中…'
  if (phase.value === 'done') return meta.value?.cache ? '缓存命中' : '已完成'
  if (phase.value === 'error') return '出错'
  return '待提问'
})

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

function quote(value: string): void {
  quoted.value = value
}

function send(): void {
  if (busy.value) return
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
  answer.value = ''
  error.value = ''
  meta.value = null
  announcement.value = ''
  collapsed.value = false
  quoted.value = ''
  phase.value = 'waiting'

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
        phase.value = 'streaming'
      },
      onToken: (token) => {
        answer.value += token
        phase.value = 'streaming'
      },
      onDone: () => {
        phase.value = 'done'
        announcement.value = answer.value
        ui.setChannel('idle')
      },
      onError: (code, message) => {
        phase.value = 'error'
        error.value = message || code
        ui.setChannel('idle')
      },
    },
  )
}

watch(
  () => props.stepIndex,
  () => {
    if (phase.value === 'waiting' || phase.value === 'streaming') {
      abort()
      phase.value = 'idle'
      announcement.value = ''
      ui.setChannel('idle')
    }
    if (answer.value) collapsed.value = true
  },
)

onScopeDispose(() => {
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

.tutor__compose button {
  align-self: flex-end;
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

.tutor__compose button:disabled {
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