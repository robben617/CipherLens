<template>
  <main class="records" :data-state="state">
    <header class="records__head">
      <h1 class="records__title">学习记录</h1>
      <span class="records__badge" data-badge>
        {{ scope === 'legacy' ? '迁移前记录（只读）' : '本机记录 · 未同步' }}
      </span>
      <span class="records__links">
        <button
          v-if="scope === 'client' && state !== 'empty'"
          type="button"
          class="records__clear"
          data-action="clear"
          :disabled="clearing"
          @click="confirmClear = true"
        >
          清空记录
        </button>
        <RouterLink
          v-if="scope === 'client'"
          class="records__link"
          :to="{ path: '/records', query: { scope: 'legacy' } }"
          data-action="legacy"
        >
          迁移前记录
        </RouterLink>
        <RouterLink
          v-else
          class="records__link"
          to="/records"
          data-action="back-client"
        >
          返回本机记录
        </RouterLink>
        <RouterLink class="records__link" to="/practice" data-action="practice">去练习</RouterLink>
      </span>
    </header>

    <div
      v-if="confirmClear"
      class="records__confirm"
      role="alertdialog"
      aria-label="确认清空记录"
      data-clear-confirm
    >
      <p>清空会删掉本机的答题记录、错因统计和学习时长，删了不能恢复。</p>
      <div class="records__confirm-actions">
        <button
          type="button"
          data-action="clear-confirm"
          :disabled="clearing"
          @click="doClear"
        >
          {{ clearing ? '清空中…' : '确认清空' }}
        </button>
        <button type="button" data-action="clear-cancel" @click="confirmClear = false">
          取消
        </button>
      </div>
    </div>

    <p v-if="cleared" class="records__hint" data-cleared>{{ cleared }}</p>

    <p v-if="loading" class="records__hint">正在读取记录…</p>

    <section v-else-if="error" class="records__error">
      <p>{{ error }}</p>
      <button type="button" data-action="retry" @click="load">重试</button>
    </section>

    <section v-else-if="state === 'empty'" class="records__empty" data-empty>
      <p v-if="scope === 'client'">
        还没有记录，去做一道题 → 题号、对错、首错字节和停留时长都会留在这一页。
      </p>
      <p v-else>没有迁移前记录。</p>
      <RouterLink v-if="scope === 'client'" class="records__cta" to="/practice" data-action="first">
        去做一道题
      </RouterLink>
      <RouterLink v-else class="records__cta" to="/records" data-action="back-client-empty">
        返回本机记录
      </RouterLink>
    </section>

    <template v-else-if="summary">
      <div class="records__stats" :class="{ 'is-muted': state === 'insufficient' }">
        <article data-stat="total">
          <span>做题数</span>
          <strong>{{ summary.total }}</strong>
        </article>
        <article data-stat="accuracy">
          <span>正确率</span>
          <strong>{{ state === 'insufficient' ? '样本不足' : accuracyText }}</strong>
        </article>
        <article data-stat="stuck">
          <span>最常卡住</span>
          <strong>{{ state === 'insufficient' ? '样本不足' : mostStuckText }}</strong>
        </article>
        <article data-stat="wrong">
          <span>错题数</span>
          <strong>{{ summary.total - summary.correct }}</strong>
        </article>
        <article data-stat="study">
          <span>学习时长</span>
          <strong>{{ studyText }}</strong>
        </article>
      </div>

      <p v-if="(summary.streak ?? 0) > 0" class="records__hint" data-streak>
        连续答对 {{ summary.streak }} 题。
      </p>

      <p v-if="state === 'insufficient'" class="records__insufficient" data-insufficient>
        再做 {{ remaining }} 道题，就能给你错因分析了。
      </p>

      <template v-else>
        <section class="records__panel" data-panel="misconception">
          <h2>错因分布（含未归类）</h2>
          <div
            v-for="bucket in summary.misconceptions"
            :key="bucket.key"
            class="records__bucket"
            :data-bucket="bucket.key"
          >
            <span class="records__bucket-label">
              {{ bucket.label }}
              <em>{{ bucket.hint }}</em>
            </span>
            <span class="records__bar">
              <span class="records__bar-fill" :style="{ width: barWidth(bucket.count) }"></span>
            </span>
            <span class="records__count" :data-count="bucket.key">{{ bucket.count }} 次</span>
          </div>
        </section>

        <section
          v-if="summary.design_tags?.length"
          class="records__panel"
          data-panel="design-tags"
        >
          <h2>题目设计意图（不是算法诊断）</h2>
          <div
            v-for="tag in summary.design_tags"
            :key="tag.tag"
            class="records__design-tag"
            :data-design-tag="tag.tag"
          >
            {{ tag.label }} · {{ tag.count }} 次
          </div>
        </section>

        <section class="records__panel" data-panel="trend">
          <h2>正确率趋势</h2>
          <svg
            class="records__trend"
            viewBox="0 0 320 64"
            role="img"
            aria-label="正确率趋势：正确在上，错误在下"
          >
            <line x1="8" y1="14" x2="312" y2="14" class="records__guide"></line>
            <line x1="8" y1="50" x2="312" y2="50" class="records__guide"></line>
            <polyline :points="trendPoints" class="records__line"></polyline>
            <circle
              v-for="dot in trendDots"
              :key="dot.index"
              :cx="dot.x"
              :cy="dot.y"
              r="2.5"
              class="records__dot"
            ></circle>
          </svg>
          <p class="records__hint">
            最近 {{ summary.trend.length }} 次 · 正确 {{ summary.correct }} / {{ summary.total }}
          </p>
        </section>

        <section v-if="recent.length" class="records__panel" data-panel="recent">
          <h2>最近 {{ recent.length }} 次</h2>
          <ul class="records__recent">
            <li
              v-for="entry in recent"
              :key="entry.id"
              :data-recent="entry.item_id"
              :data-correct="entry.is_correct"
            >
              <span class="records__recent-time">{{ timeText(entry.created_at) }}</span>
              <span class="records__recent-item">{{ entry.item_id }}</span>
              <span class="records__recent-diff">
                {{ entry.first_diff_byte === null ? '—' : `首错字节 ${entry.first_diff_byte}` }}
              </span>
              <span class="records__recent-ok" :data-ok="entry.is_correct">
                {{ entry.is_correct ? '对' : '错' }}
              </span>
            </li>
          </ul>
        </section>

        <section class="records__panel" data-panel="wrong">
          <h2>错题回看</h2>
          <p v-if="!summary.wrong.length" class="records__hint">暂无错题。</p>
          <button
            v-for="attempt in summary.wrong"
            :key="attempt.id"
            type="button"
            class="records__wrong"
            data-wrong
            @click="jump(attempt)"
          >
            <span class="records__wrong-loc">{{ attemptLabel(attempt) }}</span>
            <span class="records__wrong-answer">提交 {{ attempt.submitted }}</span>
          </button>
        </section>
      </template>
    </template>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import type { RecordsAttempt, RecordsRecent, RecordsSummary } from '../types/api'
import { getClientId } from '../utils/clientId'

const OP_LABELS: Record<string, string> = {
  sub_bytes: '字节代换',
  shift_rows: '行移位',
  mix_columns: '列混合',
  add_round_key: '轮密钥加',
}

const route = useRoute()
const router = useRouter()
const summary = ref<RecordsSummary | null>(null)
const scope = computed(() => (route.query.scope === 'legacy' ? 'legacy' : 'client'))
const loading = ref(true)
const error = ref('')
const confirmClear = ref(false)
const clearing = ref(false)
const cleared = ref('')

const state = computed(() => {
  if (loading.value) return 'loading'
  if (error.value) return 'error'
  if (!summary.value || summary.value.total === 0) return 'empty'
  if (summary.value.total < summary.value.sample_threshold) return 'insufficient'
  return 'full'
})

const accuracyText = computed(() => {
  const value = summary.value?.accuracy
  return value === null || value === undefined ? '—' : `${Math.round(value * 100)}%`
})

const mostStuckText = computed(
  () => summary.value?.most_stuck?.label ?? '暂无错题',
)

const remaining = computed(() =>
  summary.value ? Math.max(0, summary.value.sample_threshold - summary.value.total) : 0,
)

const recent = computed<RecordsRecent[]>(() => summary.value?.recent ?? [])

const studyText = computed(() => {
  const ms = summary.value?.study_ms
  if (ms === null || ms === undefined || ms <= 0) return '—'
  return formatDuration(ms)
})

function formatDuration(ms: number): string {
  const seconds = Math.round(ms / 1000)
  if (seconds < 60) return `${seconds} 秒`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes} 分 ${seconds % 60} 秒`
  return `${Math.floor(minutes / 60)} 小时 ${minutes % 60} 分`
}

/** SQLite 的 CURRENT_TIMESTAMP 是 UTC，直接 new Date 会被当成本地时间 */
function parseUtc(value: string): Date | null {
  const normalized = value.includes('T') ? value : value.replace(' ', 'T')
  const withZone = /[Zz+]/.test(normalized) ? normalized : `${normalized}Z`
  const date = new Date(withZone)
  return Number.isNaN(date.getTime()) ? null : date
}

function timeText(value: string): string {
  const date = parseUtc(value)
  if (!date) return value
  const pad = (input: number) => String(input).padStart(2, '0')
  return `${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(
    date.getMinutes(),
  )}`
}

const maxBucket = computed(() =>
  Math.max(1, ...(summary.value?.misconceptions.map((item) => item.count) ?? [0])),
)

function barWidth(count: number): string {
  return `${Math.round((count / maxBucket.value) * 100)}%`
}

const trendDots = computed(() => {
  const items = summary.value?.trend ?? []
  return items.map((item, index) => ({
    index: item.index,
    x: items.length === 1 ? 160 : 10 + (index * 300) / (items.length - 1),
    y: item.is_correct ? 14 : 50,
  }))
})

const trendPoints = computed(() =>
  trendDots.value.map((dot) => `${dot.x},${dot.y}`).join(' '),
)

function attemptLabel(attempt: RecordsAttempt): string {
  if (attempt.first_diff_round === null || !attempt.first_diff_step) return '未知位置'
  const op = OP_LABELS[attempt.first_diff_step] ?? attempt.first_diff_step
  return `第 ${attempt.first_diff_round} 轮 ${op} · 字节 ${attempt.first_diff_byte}`
}

function jump(attempt: RecordsAttempt): void {
  if (attempt.first_diff_step_index === null) return
  void router.push({
    path: '/workbench',
    query: {
      step: String(attempt.first_diff_step_index + 1),
      byte: String(attempt.first_diff_byte ?? 0),
    },
  })
}

async function load(): Promise<void> {
  loading.value = true
  error.value = ''
  try {
    const url =
      scope.value === 'legacy'
        ? '/api/records/summary?scope=legacy'
        : '/api/records/summary'
    const headers =
      scope.value === 'legacy'
        ? undefined
        : { 'X-Client-Id': getClientId() }
    const res = await fetch(url, { headers })
    if (!res.ok) {
      error.value = `记录加载失败（HTTP ${res.status}）`
      return
    }
    summary.value = (await res.json()) as RecordsSummary
  } catch {
    error.value = '记录加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

async function doClear(): Promise<void> {
  if (clearing.value) return
  clearing.value = true
  cleared.value = ''
  try {
    const res = await fetch('/api/records', {
      method: 'DELETE',
      headers: { 'X-Client-Id': getClientId() },
    })
    if (!res.ok) {
      const data = (await res.json().catch(() => null)) as
        | { error?: { message?: string } }
        | null
      error.value = data?.error?.message ?? `清空失败（HTTP ${res.status}）`
      return
    }
    const data = (await res.json()) as {
      removed: { attempts: number; legacy_attempts: number; events: number }
    }
    const total = data.removed.attempts + data.removed.legacy_attempts
    cleared.value = `已清空 ${total} 条答题记录、${data.removed.events} 条学习事件。`
    confirmClear.value = false
    await load()
  } catch {
    error.value = '清空失败：后端未连接'
  } finally {
    clearing.value = false
  }
}

onMounted(load)
watch(scope, () => {
  confirmClear.value = false
  cleared.value = ''
  void load()
})
</script>

<style scoped>
.records {
  max-width: 1080px;
  margin: 0 auto;
  padding: var(--sp-6);
}

.records__head {
  display: flex;
  align-items: baseline;
  gap: var(--sp-3);
  padding-bottom: var(--sp-3);
  border-bottom: var(--rule-region-w) solid var(--line-hairline);
}

.records__title {
  font-size: var(--fs-title);
  font-weight: 600;
  letter-spacing: var(--ls-title);
  color: var(--ink-1);
}

.records__badge {
  padding: 2px var(--sp-2);
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

.records__links {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  margin-left: auto;
}

.records__link {
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-3);
  text-decoration: none;
}

.records__clear {
  height: 24px;
  padding: 0 var(--sp-2);
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  background: transparent;
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-3);
  cursor: pointer;
}

.records__clear:hover {
  border-color: var(--st-error);
  color: var(--st-error);
}

.records__clear:disabled {
  cursor: default;
  opacity: 0.5;
}

.records__confirm {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  margin-top: var(--sp-4);
  padding: var(--sp-3);
  border: var(--rule-region-w) solid var(--st-error);
  border-radius: var(--r-control);
  background: var(--paper-1);
}

.records__confirm p {
  margin: 0;
  font-size: var(--fs-ui);
  color: var(--ink-1);
}

.records__confirm-actions {
  display: flex;
  gap: var(--sp-2);
}

.records__confirm-actions button {
  height: 30px;
  padding: 0 var(--sp-3);
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  background: transparent;
  font-family: var(--font-ui);
  font-size: var(--fs-label);
  color: var(--ink-2);
  cursor: pointer;
}

.records__confirm-actions button[data-action='clear-confirm'] {
  border-color: var(--st-error);
  color: var(--st-error);
}

.records__recent {
  margin: 0;
  padding: 0;
  list-style: none;
}

.records__recent li {
  display: grid;
  grid-template-columns: 92px 64px minmax(0, 1fr) 24px;
  align-items: baseline;
  gap: var(--sp-2);
  padding: var(--sp-1) 0;
  border-bottom: var(--rule-region-w) solid var(--line-hairline);
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-2);
}

.records__recent li:last-child {
  border-bottom: 0;
}

.records__recent-time {
  color: var(--ink-3);
}

.records__recent-ok[data-ok='true'] {
  color: var(--ok, var(--accent-strong));
}

.records__recent-ok[data-ok='false'] {
  color: var(--st-error);
}

.records__hint {
  margin: var(--sp-2) 0 0;
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

.records__error,
.records__empty {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--sp-3);
  padding-top: var(--sp-6);
}

.records__error p,
.records__empty p {
  font-size: var(--fs-body);
  color: var(--ink-2);
}

.records__cta {
  height: 32px;
  padding: 0 var(--sp-4);
  border: var(--rule-region-w) solid var(--accent);
  border-radius: var(--r-control);
  font-family: var(--font-ui);
  font-size: var(--fs-label);
  line-height: 30px;
  color: var(--accent-strong);
  text-decoration: none;
}

.records__stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: var(--sp-3);
  padding-top: var(--sp-4);
}

.records__stats article {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
  padding: var(--sp-3);
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  background: var(--paper-1);
}

.records__stats article span {
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  letter-spacing: var(--ls-label);
  color: var(--ink-3);
}

.records__stats article strong {
  font-family: var(--font-mono);
  font-size: var(--fs-title);
  font-weight: 500;
  line-height: 1.2;
  color: var(--ink-1);
}

.records__stats.is-muted article {
  border-style: dashed;
  background: transparent;
}

.records__stats.is-muted article strong {
  font-size: var(--fs-ui);
  color: var(--ink-3);
}

.records__insufficient {
  margin: var(--sp-4) 0 0;
  padding: var(--sp-2) var(--sp-3);
  border-left: var(--rule-scope-w) solid var(--warn);
  font-size: var(--fs-ui);
  color: var(--ink-2);
}

.records__panel {
  margin-top: var(--sp-6);
  padding-top: var(--sp-3);
  border-top: var(--rule-region-w) solid var(--line-hairline);
}

.records__panel h2 {
  margin: 0 0 var(--sp-3);
  font-family: var(--font-mono);
  font-size: var(--fs-label);
  font-weight: 500;
  letter-spacing: var(--ls-label);
  color: var(--ink-2);
}

.records__bucket {
  display: grid;
  grid-template-columns: 180px minmax(0, 1fr) 56px;
  align-items: center;
  gap: var(--sp-3);
  margin-bottom: var(--sp-2);
}

.records__bucket-label {
  display: flex;
  flex-direction: column;
  font-size: var(--fs-ui);
  color: var(--ink-1);
}

.records__bucket-label em {
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  font-style: normal;
  color: var(--ink-3);
}

.records__bar {
  height: 10px;
  border: var(--rule-region-w) solid var(--line-hairline);
  background: var(--surface-inset);
}

.records__bar-fill {
  display: block;
  height: 100%;
  background: var(--ink-2);
}

.records__count {
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-2);
  text-align: right;
}

.records__trend {
  display: block;
  width: 100%;
  height: 96px;
}

.records__guide {
  stroke: var(--line-hairline);
  stroke-width: 1;
}

.records__line {
  fill: none;
  stroke: var(--accent);
  stroke-width: 2;
  stroke-linejoin: round;
  stroke-linecap: round;
}

.records__dot {
  fill: var(--accent);
}

.records__design-tag {
  display: inline-block;
  margin: 0 var(--sp-2) var(--sp-2) 0;
  padding: 2px var(--sp-2);
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-2);
}

.records__wrong {
  display: flex;
  justify-content: space-between;
  gap: var(--sp-3);
  width: 100%;
  margin-bottom: var(--sp-2);
  padding: var(--sp-2) var(--sp-3);
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  background: transparent;
  font-family: var(--font-ui);
  font-size: var(--fs-ui);
  color: var(--ink-1);
  text-align: left;
  cursor: pointer;
}

.records__wrong:hover {
  border-color: var(--accent);
}

.records__wrong-answer {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

@media (max-width: 59.9375rem) {
  .records__stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .records__bucket {
    grid-template-columns: 140px minmax(0, 1fr) 48px;
  }
}
</style>