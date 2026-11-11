<template>
  <main class="practice">
    <header class="practice__head">
      <h1 class="practice__title">练习 · 密文判分</h1>
      <span v-if="item" class="practice__count" data-count>
        第 {{ itemIndex }} / {{ items.length }} 题
      </span>
      <span class="practice__meta">{{ item ? `AES-${item.key_bits} · 16 字节` : '题库' }}</span>
    </header>

    <p v-if="loadingItems" class="practice__hint" data-items-loading>正在读取题库…</p>

    <section v-else-if="itemsError" class="practice__blocked" data-items-error>
      <p>{{ itemsError }}</p>
      <p class="practice__hint">
        判分在后端做，题目也由后端给；后端没起来时先别答题，免得多算一遍错。
      </p>
      <button type="button" data-action="reload-items" @click="loadItems">重新加载</button>
    </section>

    <div v-else-if="item" class="practice__body">
      <section class="practice__form">
        <p class="practice__ladder" data-ladder>{{ ladderText }}</p>

        <div class="practice__picker" role="group" aria-label="选择练习题" data-item-picker>
          <button
            v-for="entry in items"
            :key="entry.id"
            type="button"
            class="practice__pick"
            :class="{ 'is-active': entry.id === item.id }"
            :aria-pressed="entry.id === item.id"
            :data-item="entry.id"
            :title="`${entry.difficulty_label ?? ''} · ${entry.tag_label ?? '综合题'}`"
            @click="selectItem(entry.id)"
          >
            {{ entry.id }} · AES-{{ entry.key_bits }}
          </button>
        </div>

        <p class="practice__tags">
          <span class="practice__level" data-level>{{ item.difficulty_label ?? '未分级' }}</span>
          <span v-if="item.tag_label" class="practice__tag" data-tag>{{ item.tag_label }}</span>
        </p>

        <p class="practice__question">{{ item.question }}</p>

        <label class="practice__field">
          <span>明文（32 位十六进制 · 题目给定）</span>
          <input
            v-model="plaintext"
            name="plaintext"
            spellcheck="false"
            autocomplete="off"
            readonly
            data-given
          />
        </label>

        <label class="practice__field">
          <span>密钥（{{ item.key_bits / 4 }} 位十六进制 · 题目给定）</span>
          <input
            v-model="key"
            name="key"
            spellcheck="false"
            autocomplete="off"
            readonly
            data-given
          />
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

        <p v-if="formError" class="practice__error" data-form-error>{{ formError }}</p>
        <p v-if="quiz.error" class="practice__error" data-submit-error>{{ quiz.error }}</p>
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
            <p v-if="extraDiffCount > 0" class="practice__hint" data-extra-diffs>
              还有 {{ extraDiffCount }} 个差异字节
            </p>
            <button type="button" data-action="jump" class="practice__jump" @click="jump">
              去工作台看这一步
            </button>
          </div>

          <div
            v-if="quiz.response.design_tag_hint && !quiz.inputMismatch"
            class="practice__layer"
            data-design-hint
          >
            <p class="practice__label">③ 这道题在考什么</p>
            <p class="practice__summary">
              {{ quiz.response.design_tag_label ?? '综合题' }}
            </p>
            <p class="practice__hint">{{ quiz.response.design_tag_hint }}</p>
          </div>

          <div v-if="showMatrix" class="practice__layer practice__layer--matrix">
            <QuizMatrix
              :key="`${item.id}:${quiz.firstDiff?.step_index ?? 'none'}`"
              :values="matrixValues"
              :changed="matrixChanged"
              :error="matrixError"
              :downstream="matrixDownstream"
              :key-indices="matrixKey"
              :range-label="rangeLabel"
            />
            <p class="practice__hint" data-propagated>{{ sourceText }}</p>
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
import { useRoute, useRouter } from 'vue-router'
import QuizMatrix from '../components/region-c/QuizMatrix.vue'
import { useQuizStore } from '../stores/quiz'
import type {
  QuizItemRecord,
  QuizItemsResponse,
  QuizSubmitResponse,
  QuizTrace,
} from '../types/api'

import { OP_LABEL as OP_LABELS } from '../data/glossary'

const DEBUG =
  import.meta.env.DEV &&
  new URLSearchParams(window.location.search).get('debug') === 'quiz'

const route = useRoute()
const router = useRouter()
const quiz = useQuizStore()

const items = ref<QuizItemRecord[]>([])
const loadingItems = ref(true)
const itemsError = ref('')
const item = ref<QuizItemRecord | null>(null)

const plaintext = ref('')
const key = ref('')
const answer = ref('')
const formError = ref('')
const trace = ref<QuizTrace | null>(null)
const traceError = ref('')
const showExpected = ref(false)

const itemIndex = computed(() => {
  const found = items.value.findIndex((entry) => entry.id === item.value?.id)
  return found < 0 ? 1 : found + 1
})

/** 四级梯度一句话说清：按难度分组计数，顺序就是出题顺序 */
const ladderText = computed(() => {
  if (items.value.length === 0) return ''
  const groups: { label: string; count: number }[] = []
  for (const entry of items.value) {
    const label = entry.difficulty_label ?? '未分级'
    const last = groups[groups.length - 1]
    if (last && last.label === label) last.count += 1
    else groups.push({ label, count: 1 })
  }
  return `难度从低到高：${groups.map((g) => `${g.label} ${g.count}`).join(' · ')}`
})

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
const matrixDownstream = computed(() => [...quiz.sourceBytes])
const extraDiffCount = computed(() => {
  const data = quiz.response
  if (!data || data.input_mismatch) return 0
  const count = data.diff_bytes?.length ?? data.summary.wrong_count
  return Math.max(0, count - 1)
})
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

/**
 * 「上一轮列混合的 4 个来源字节」：把下标换成真实字节值。
 * 原来只写「4 个（source_bytes）」，等于把内部字段名丢给用户看。
 */
const sourceText = computed(() => {
  const data = quiz.response
  const indexes = data?.source_bytes ?? []
  if (!data || indexes.length === 0) return '来源候选字节：0 个'

  const stepIndex = data.source_step_index
  const step =
    stepIndex === null || stepIndex === undefined ? null : trace.value?.steps[stepIndex]
  if (!step) return `来源候选字节：${indexes.length} 个（同一列）`

  const hex = indexes
    .map((index) => {
      const value = step.state_before[index] ?? 0
      return `0x${value.toString(16).padStart(2, '0').toUpperCase()}`
    })
    .join(' ')

  return `上一轮列混合的 4 个来源字节：${hex}`
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

  // expected='item'：改了题目给定的输入，不是写错了十六进制
  if (mismatch.expected === 'item') {
    const tail =
      mismatch.char_index >= 0 ? `（第 ${mismatch.char_index + 1} 个字符起）` : ''
    return `${fieldLabel}和题目给定的值不一致${tail}`
  }

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
  if (!item.value || quiz.phase === 'submitting') return
  const value = answer.value.trim()
  if (value.length !== 32) {
    formError.value = '答案需为 32 位十六进制'
    return
  }
  formError.value = ''
  showExpected.value = false
  quiz.disarmOverlay()
  void quiz.submit({
    item_id: item.value.id,
    answer_hex: value,
    plaintext_hex: plaintext.value.trim(),
    key_hex: key.value.trim(),
    key_bits: item.value.key_bits,
  })
}

/** 带 pt/key 跳过去，工作台才是这道题的这一状态，而不是默认向量的同一格 */
function jump(): void {
  if (!item.value) return
  const diff = quiz.firstDiff
  if (!diff) return
  quiz.armOverlay()
  void router.push({
    path: '/workbench',
    query: {
      step: String(diff.step_index + 1),
      byte: String(diff.byte_index),
      pt: item.value.plaintext_hex,
      key: item.value.key_hex,
    },
  })
}

function selectItem(id: string): void {
  const next = items.value.find((entry) => entry.id === id)
  if (!next || next.id === item.value?.id) return
  quiz.disarmOverlay()
  quiz.clear()
  applyItem(next)
  void router.replace({ query: { ...route.query, item: next.id } })
  void loadTrace()
}

function applyItem(next: QuizItemRecord): void {
  item.value = next
  plaintext.value = next.plaintext_hex
  key.value = next.key_hex
  answer.value = ''
  formError.value = ''
  showExpected.value = false
  trace.value = null
  traceError.value = ''
}

async function loadItems(): Promise<void> {
  loadingItems.value = true
  itemsError.value = ''
  try {
    const res = await fetch('/api/quiz/items')
    if (!res.ok) {
      itemsError.value = `题库加载失败（HTTP ${res.status}）`
      return
    }
    const data = (await res.json()) as QuizItemsResponse
    if (!Array.isArray(data.items) || data.items.length === 0) {
      itemsError.value = '题库是空的：后端还没灌题，重启一次后端即可'
      return
    }
    items.value = data.items
    const requested = typeof route.query.item === 'string' ? route.query.item : ''
    const picked = data.items.find((entry) => entry.id === requested) ?? data.items[0]!
    applyItem(picked)
    void loadTrace()
  } catch {
    itemsError.value = '题库加载失败，后端可能没启动'
  } finally {
    loadingItems.value = false
  }
}

async function loadTrace(): Promise<void> {
  if (!item.value) return
  try {
    const res = await fetch('/api/aes/trace', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        plaintext_hex: item.value.plaintext_hex,
        key_hex: item.value.key_hex,
        key_bits: item.value.key_bits,
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
    diff_bytes: [7, 9, 15],
    source_bytes: [8, 9, 10, 11],
    source_step_index: 15,
    source_round: 4,
    source_step: 'mix_columns',
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
    legacy: () => {
      const base: QuizSubmitResponse = {
        summary: { total_bytes: 16, wrong_count: 1 },
        first_diff: {
          step_index: 39,
          round: 10,
          step: 'add_round_key',
          byte_index: 7,
          expected: 0x76,
          actual: 0x75,
        },
        propagated: [8, 9, 10, 11, 12, 13, 14, 15],
        input_mismatch: null,
        expected_ciphertext: '3925841d02dc09fbdc118597196a0b32',
      }
      quiz.applyResponse(base, { count: false })
      return true
    },
    reset: () => reset(),
    submit: () => submit(),
    items: () => items.value.map((entry) => entry.id),
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
      itemIndex: itemIndex.value,
      itemsTotal: items.value.length,
      stats: { ...quiz.stats },
      summary: summaryText.value,
      locator: locText.value,
      mismatch: mismatchText.value,
      firstDiff: quiz.firstDiff,
      propagated: [...quiz.propagated],
      diffBytes: [...quiz.diffBytes],
      sourceBytes: [...quiz.sourceBytes],
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
  void loadItems()
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
  min-height: calc(100dvh - var(--nav-h));
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

.practice__title {
  font-size: var(--fs-title);
  font-weight: 600;
  letter-spacing: var(--ls-title);
  color: var(--ink-1);
}

.practice__count {
  padding: 1px var(--sp-2);
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-3);
  white-space: nowrap;
}

.practice__meta {
  margin-left: auto;
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-3);
  white-space: nowrap;
}

/* 窄屏：标题单独一行，题号与位长各占一行的一半，别挤成竖排 */
@media (max-width: 40rem) {
  .practice__head {
    flex-wrap: wrap;
    row-gap: var(--sp-2);
  }

  .practice__title {
    flex: 1 1 100%;
  }
}

.practice__blocked {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--sp-2);
  margin-top: var(--sp-6);
  padding: var(--sp-4);
  border: var(--rule-region-w) solid var(--line-hairline);
  border-left: var(--rule-scope-w) solid var(--warn);
  border-radius: var(--r-control);
  background: var(--paper-1);
}

.practice__blocked p {
  margin: 0;
  font-size: var(--fs-ui);
  color: var(--ink-1);
}

.practice__blocked button {
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

.practice__tags {
  display: flex;
  gap: var(--sp-1);
  margin: 0;
}

.practice__ladder {
  margin: 0;
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

.practice__level,
.practice__tag {
  padding: 1px var(--sp-2);
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-2);
}

.practice__level {
  border-color: var(--accent);
  color: var(--accent-strong);
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

/* 题目给定的输入：明确「不可改」，否则用户会以为改两下就能换题 */
.practice__field input[data-given] {
  background: var(--surface-inset);
  color: var(--ink-2);
  cursor: default;
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

.practice__picker {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-1);
}

.practice__pick {
  height: 26px;
  padding: 0 var(--sp-2);
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  background: transparent;
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-3);
  cursor: pointer;
}

.practice__pick.is-active {
  border-color: var(--accent);
  color: var(--accent-strong);
}
</style>
