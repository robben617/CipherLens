<template>
  <main class="records" :data-state="state">
    <header class="records__head">
      <h1 class="records__title">学习记录</h1>
      <span class="records__badge" data-badge>本机数据（未同步）</span>
      <RouterLink class="records__link" to="/practice" data-action="practice">去练习</RouterLink>
    </header>

    <p v-if="loading" class="records__hint">正在读取记录…</p>

    <section v-else-if="error" class="records__error">
      <p>{{ error }}</p>
      <button type="button" data-action="retry" @click="load">重试</button>
    </section>

    <section v-else-if="state === 'empty'" class="records__empty" data-empty>
      <p>还没有记录。做一道练习题就会开始记。</p>
      <RouterLink class="records__cta" to="/practice" data-action="first">
        去做第一题
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
      </div>

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
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import type { RecordsAttempt, RecordsSummary } from '../types/api'

const OP_LABELS: Record<string, string> = {
  sub_bytes: '字节代换',
  shift_rows: '行移位',
  mix_columns: '列混合',
  add_round_key: '轮密钥加',
}

const router = useRouter()
const summary = ref<RecordsSummary | null>(null)
const loading = ref(true)
const error = ref('')

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
    const res = await fetch('/api/records/summary')
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

onMounted(load)
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

.records__link {
  margin-left: auto;
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-3);
  text-decoration: none;
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
  grid-template-columns: repeat(4, minmax(0, 1fr));
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