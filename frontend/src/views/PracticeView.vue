<template>
  <main class="practice">
    <header class="practice__head">
      <RouterLink class="practice__back" to="/">← 返回首页</RouterLink>
      <h1 class="practice__title">练习 · 密文判分</h1>
      <span class="practice__meta">AES-128 · 16 字节</span>
    </header>

    <div class="practice__body">
      <section class="practice__form">
        <p class="practice__question">{{ item.question }}</p>

        <label class="practice__field">
          <span>明文（32 位十六进制）</span>
          <input v-model="plaintext" name="plaintext" spellcheck="false" autocomplete="off" />
        </label>

        <label class="practice__field">
          <span>密钥（32 位十六进制）</span>
          <input v-model="key" name="key" spellcheck="false" autocomplete="off" />
        </label>

        <label class="practice__field">
          <span>你的密文答案（32 位十六进制）</span>
          <input v-model="answer" name="answer" spellcheck="false" autocomplete="off" />
        </label>

        <div class="practice__actions">
          <button
            type="button"
            data-action="submit"
            :disabled="quiz.phase === 'submitting'"
            @click="submit"
          >
            {{ quiz.phase === 'submitting' ? '判分中…' : '提交判分' }}
          </button>
          <button
            v-if="quiz.phase === 'graded'"
            type="button"
            data-action="reset"
            class="practice__ghost"
            @click="reset"
          >
            再答一次
          </button>
        </div>

        <p v-if="formError" class="practice__error">{{ formError }}</p>
        <p v-if="quiz.error" class="practice__error">{{ quiz.error }}</p>
        <p v-if="traceError" class="practice__hint">{{ traceError }}</p>

        <p class="practice__stats" data-stats>
          本次会话：已做 {{ quiz.stats.done }} 题 / 正确 {{ quiz.stats.correct }} 题
        </p>
      </section>

      <section class="practice__result" aria-live="polite">
        <p v-if="!quiz.response" class="practice__placeholder">提交后在这里显示三层反馈。</p>

        <template v-else>
          <div class="practice__layer">
            <p class="practice__label">① 结论</p>
            <p class="practice__summary" data-summary>{{ summaryText }}</p>
          </div>

          <div v-if="quiz.inputMismatch" class="practice__layer practice__layer--warn">
            <p class="practice__label">输入不一致</p>
            <p class="practice__summary" data-mismatch>{{ mismatchText }}</p>
            <p class="practice__hint">本题不计入正确率；修正输入后可重新判分。</p>
          </div>

          <div v-if="quiz.firstDiff && !quiz.inputMismatch" class="practice__layer">
            <p class="practice__label">② 首次差异</p>
            <p class="practice__summary" data-locator>{{ locText }}</p>
            <button type="button" data-action="jump" class="practice__jump" @click="jump">
              在工作台对照
            </button>
          </div>

          <div v-if="showMatrix" class="practice__layer practice__layer--matrix">
            <QuizMatrix
              :values="matrixValues"
              :changed="matrixChanged"
              :error="matrixError"
              :downstream="matrixDownstream"
              :key-indices="matrixKey"
              :range-label="rangeLabel"
            />
            <p class="practice__hint" data-propagated>
              受首错污染的下游字节：{{ quiz.propagated.size }} 个（propagated.length）
            </p>
          </div>

          <div v-if="quiz.response && !quiz.inputMismatch" class="practice__layer">
            <button
              v-if="quiz.response.expected_ciphertext"
              type="button"
              data-action="toggle-answer"
              class="practice__ghost"
              @click="showExpected = !showExpected"
            >
              {{ showExpected ? '收起正确答案' : '查看正确答案' }}
            </button>
            <p v-if="showExpected" class="practice__answer" data-expected>
              {{ quiz.response.expected_ciphertext }}
            </p>
          </div>
        </template>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, onScopeDispose, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import QuizMatrix from '../components/region-c/QuizMatrix.vue'
import { QUIZ_ITEMS } from '../data/quizBank'
import { useQuizStore } from '../stores/quiz'
import type { QuizSubmitResponse, QuizTrace } from '../types/api'

const OP_LABELS: Record<string, string> = {
  sub_bytes: '字节代换',
  shift_rows: '行移位',
  mix_columns: '列混合',
  add_round_key: '轮密钥加',
}

const DEBUG =
  import.meta.env.DEV &&
  new URLSearchParams(window.location.search).get('debug') === 'quiz'

const item = QUIZ_ITEMS[0]!
const router = useRouter()
const quiz = useQuizStore()

const plaintext = ref(item.plaintext_hex)
const key = ref(item.key_hex)
const answer = ref('')
const formError = ref('')
const trace = ref<QuizTrace | null>(null)
const traceError = ref('')
const showExpected = ref(false)

const anchor = computed(() => {
  const diff = quiz.firstDiff
  if (!diff || !trace.value) return null
  return trace.value.steps[diff.step_index] ?? null
})

const showMatrix = computed(
  () => quiz.firstDiff !== null && !quiz.inputMismatch && anchor.value !== null,
)

const matrixValues = computed(() => anchor.value?.state_after ?? [])
const matrixChanged = computed(() => anchor.value?.changed ?? [])
const matrixError = computed(() => [...quiz.errorBytes])
const matrixDownstream = computed(() => [...quiz.propagated])
const matrixKey = computed(() => anchor.value?.key_indices ?? [])
const rangeLabel = computed(() => (showMatrix.value ? '影响范围：16 字节' : undefined))

const summaryText = computed(() => {
  const data = quiz.response
  if (!data) return ''
  if (data.input_mismatch) return '输入与题目不一致，本题不计入统计'
  const { total_bytes, wrong_count } = data.summary
  if (data.first_diff === null) return `${total_bytes} 个字节全部一致`
  return `${total_bytes} 个字节中 ${wrong_count} 个不符`
})

const locText = computed(() => {
  const diff = quiz.firstDiff
  if (!diff) return ''
  return `第 ${diff.round} 轮 ${OP_LABELS[diff.step] ?? diff.step} 字节 ${diff.byte_index}`
})

const plaintextBadIndex = computed(() => {
  const value = plaintext.value
  for (let index = 0; index < value.length; index++) {
    if (!/[0-9a-fA-F]/.test(value[index]!)) return index
  }
  return -1
})

const mismatchText = computed(() => {
  const mismatch = quiz.inputMismatch
  if (!mismatch) return ''
  const isBoth = mismatch.field === 'both'
  const fieldLabel = isBoth ? '明文与密钥' : mismatch.field === 'plaintext' ? '明文' : '密钥'
  const index = isBoth ? plaintextBadIndex.value : mismatch.char_index
  if (index < 0) return `${fieldLabel}中有非十六进制字符`
  const source = mismatch.field === 'key' || isBoth ? key.value : plaintext.value
  const char = source[index]
  const suffix = char ? `（你写的是 ${char}）` : ''
  return `${fieldLabel}的第 ${index + 1} 个字符不是十六进制数${suffix}`
})

function reset(): void {
  quiz.disarmOverlay()
  quiz.clear()
  answer.value = ''
  formError.value = ''
  showExpected.value = false
}

function submit(): void {
  if (quiz.phase === 'submitting') return
  const value = answer.value.trim()
  if (value.length !== 32) {
    formError.value = '答案需为 32 位十六进制'
    return
  }
  formError.value = ''
  showExpected.value = false
  quiz.disarmOverlay()
  void quiz.submit({
    item_id: item.id,
    answer_hex: value,
    plaintext_hex: plaintext.value.trim(),
    key_hex: key.value.trim(),
    key_bits: item.key_bits,
  })
}

function jump(): void {
  const diff = quiz.firstDiff
  if (!diff) return
  quiz.armOverlay()
  void router.push({
    path: '/workbench',
    query: { step: String(diff.step_index + 1), byte: String(diff.byte_index) },
  })
}

async function loadTrace(): Promise<void> {
  try {
    const res = await fetch('/api/aes/trace', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        plaintext_hex: item.plaintext_hex,
        key_hex: item.key_hex,
        key_bits: item.key_bits,
        direction: 'encrypt',
      }),
    })
    if (!res.ok) {
      traceError.value = 'trace 加载失败，判分定位矩阵暂不可用'
      return
    }
    trace.value = (await res.json()) as QuizTrace
  } catch {
    traceError.value = 'trace 加载失败，判分定位矩阵暂不可用'
  }
}

function applyFixture(kind: 'contract' | 'missing'): boolean {
  const base: QuizSubmitResponse = {
    summary: { total_bytes: 16, wrong_count: 3 },
    first_diff: {
      step_index: 15,
      round: 4,
      step: 'mix_columns',
      byte_index: 7,
      expected: 0x76,
      actual: 0x75,
    },
    propagated: [8, 9, 10, 11, 12, 13, 14, 15],
    input_mismatch: null,
    expected_ciphertext: '3925841d02dc09fbdc118597196a0b32',
  }
  if (kind === 'missing') {
    delete (base as { propagated?: number[] }).propagated
  }
  quiz.applyResponse(base, { count: false })
  return true
}

function exposeDebug(): void {
  const target = window as Window & { __quiz?: Record<string, unknown> }
  target.__quiz = {
    contract: () => applyFixture('contract'),
    missing: () => applyFixture('missing'),
    reset: () => reset(),
    submit: () => submit(),
    setField: (field: 'plaintext' | 'key' | 'answer', value: string) => {
      if (field === 'plaintext') plaintext.value = value
      else if (field === 'key') key.value = value
      else answer.value = value
    },
    ready: () => trace.value !== null,
    state: () => ({
      phase: quiz.phase,
      error: quiz.error,
      counted: quiz.counted,
      stats: { ...quiz.stats },
      summary: summaryText.value,
      locator: locText.value,
      mismatch: mismatchText.value,
      firstDiff: quiz.firstDiff,
      propagated: [...quiz.propagated],
      errorBytes: [...quiz.errorBytes],
      errorCount: document.querySelectorAll('.is-error').length,
      downstreamCount: document.querySelectorAll('.is-downstream').length,
      keyCount: document.querySelectorAll('.is-key').length,
      rangeLabel: document.querySelector('.c-range__label')?.textContent ?? null,
      expected: document.querySelector('[data-expected]')?.textContent ?? null,
    }),
  }
}

onMounted(() => {
  void loadTrace()
  if (DEBUG) exposeDebug()
})

onScopeDispose(() => {
  if (DEBUG) {
    delete (window as Window & { __quiz?: unknown }).__quiz
  }
})
</script>

<style scoped>
.practice {
  min-height: 100vh;
  padding: var(--sp-6);
  background: var(--paper-0);
}

.practice__head {
  display: flex;
  align-items: baseline;
  gap: var(--sp-3);
  padding-bottom: var(--sp-3);
  border-bottom: var(--rule-region-w) solid var(--line-hairline);
}

.practice__back {
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-3);
  text-decoration: none;
}

.practice__title {
  font-size: var(--fs-title);
  font-weight: 600;
  letter-spacing: var(--ls-title);
  color: var(--ink-1);
}

.practice__meta {
  margin-left: auto;
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

.practice__body {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(280px, 360px);
  gap: var(--sp-6);
  padding-top: var(--sp-5);
}

.practice__form {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  min-width: 0;
}

.practice__question {
  font-size: var(--fs-body);
  line-height: var(--lh-body);
  color: var(--ink-1);
}

.practice__field {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

.practice__field input {
  height: 34px;
  padding: 0 var(--sp-2);
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  background: var(--paper-1);
  font-family: var(--font-mono);
  font-size: var(--fs-ui);
  letter-spacing: var(--ls-hex-cell);
  color: var(--ink-1);
}

.practice__field input:focus-visible {
  border-color: var(--accent);
}

.practice__actions {
  display: flex;
  gap: var(--sp-2);
}

.practice__actions button,
.practice__jump,
.practice__ghost {
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

.practice__actions button:disabled {
  border-color: var(--line-hairline);
  color: var(--ink-3);
  cursor: default;
}

.practice__ghost {
  border-color: var(--line-hairline);
  color: var(--ink-2);
}

.practice__error {
  margin: 0;
  font-size: var(--fs-ui);
  color: var(--st-error);
}

.practice__hint {
  margin: 0;
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

.practice__stats {
  margin-top: var(--sp-2);
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

.practice__result {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  padding: var(--sp-3);
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  background: var(--paper-1);
}

.practice__placeholder {
  font-size: var(--fs-ui);
  color: var(--ink-3);
}

.practice__layer {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--sp-1);
  padding-bottom: var(--sp-2);
  border-bottom: var(--rule-region-w) solid var(--line-hairline);
}

.practice__layer:last-child {
  border-bottom: 0;
  padding-bottom: 0;
}

.practice__layer--warn {
  border-left: var(--rule-scope-w) solid var(--warn);
  padding-left: var(--sp-2);
}

.practice__layer--matrix {
  align-items: center;
}

.practice__label {
  margin: 0;
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  letter-spacing: var(--ls-label);
  color: var(--ink-3);
}

.practice__summary {
  margin: 0;
  font-size: var(--fs-ui);
  line-height: var(--lh-body);
  color: var(--ink-1);
}

.practice__answer {
  margin: var(--sp-1) 0 0;
  font-family: var(--font-mono);
  font-size: var(--fs-ui);
  letter-spacing: var(--ls-hex-cell);
  color: var(--ink-2);
  word-break: break-all;
}

@media (max-width: 59.9375rem) {
  .practice__body {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>