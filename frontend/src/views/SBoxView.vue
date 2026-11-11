<template>
  <main class="sbox" :style="{ '--sbox-cell': `${cellPx}px` }">
    <header class="sbox__head">
      <div class="sbox__intro">
        <h1 class="sbox__title">S 盒浏览器</h1>
        <p class="sbox__lede">
          AES 的 256 个字节替换规则：一个字节进，一个字节出，没有两个输入得到同一个输出。
        </p>
      </div>

      <div class="sbox__tools">
        <div class="sbox__modes" role="group" aria-label="查表方向" data-sbox-modes>
          <button
            type="button"
            class="sbox__mode"
            data-mode-btn="forward"
            :aria-pressed="!inverse"
            @click="setMode(false)"
          >
            正向 S 盒
          </button>
          <button
            type="button"
            class="sbox__mode"
            data-mode-btn="inverse"
            :aria-pressed="inverse"
            @click="setMode(true)"
          >
            逆向 S 盒
          </button>
        </div>

        <form class="sbox__search" role="search" @submit.prevent="locate">
          <input
            v-model="query"
            class="sbox__search-input"
            name="sbox-search"
            data-sbox-search
            placeholder="3f / 0x3f / 63"
            aria-label="搜索字节：十六进制写 3f 或 0x3f，纯数字按十进制"
            spellcheck="false"
            autocomplete="off"
          />
          <button type="submit" class="sbox__search-go" data-action="sbox-locate">定位</button>
          <span v-if="resolved" class="sbox__resolved" data-sbox-resolved>{{ resolved }}</span>
        </form>

        <RouterLink
          class="sbox__back"
          :class="{ 'is-from': fromWorkbench }"
          to="/workbench"
          data-action="back-workbench"
        >
          {{ fromWorkbench ? '← 回到工作台' : '返回工作台' }}
        </RouterLink>
      </div>
    </header>

    <p v-if="searchError" class="sbox__error" role="alert">
      没法定位「{{ query.trim() }}」。写 1–2 位十六进制（3f / 0x3f），或 0–255 的十进制。
    </p>

    <div class="sbox__body">
      <section class="sbox__gridwrap" aria-labelledby="sbox-grid-caption">
        <p id="sbox-grid-caption" class="sbox__caption">
          {{ inverse ? '逆向表：行是输出的高位，列是输出的低位' : '正向表：行是输入的高位，列是输入的低位' }}
        </p>

        <div class="sbox__scroll">
          <SBoxGrid v-model:selected="selected" :values="values" :inverse="inverse" />
        </div>

        <div class="sbox__foot">
          <p class="sbox__hint">方向键移动 · Home / End 行首行尾 · 也可以直接点格子</p>
          <div class="sbox__zoom" role="group" aria-label="网格缩放" data-sbox-zoom>
            <button
              v-for="level in ZOOM_LEVELS"
              :key="level"
              type="button"
              class="sbox__zoom-btn"
              :aria-pressed="zoom === level"
              :data-zoom="level"
              @click="zoom = level"
            >
              {{ level }}×
            </button>
          </div>
        </div>
      </section>

      <SBoxDetail v-model:value="selected" :inverse="inverse" />
    </div>

    <section class="sbox__props" aria-label="S 盒的三条性质">
      <article v-for="item in PROPERTIES" :key="item.name" class="sbox__prop">
        <h2 class="sbox__prop-name">{{ item.name }}</h2>
        <p class="sbox__prop-text">{{ item.text }}</p>
      </article>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import SBoxGrid from '../components/sbox/SBoxGrid.vue'
import SBoxDetail from '../components/sbox/SBoxDetail.vue'
import { INV_SBOX, SBOX } from '../engine/sbox'

const ZOOM_LEVELS = [0.75, 1, 1.25] as const
const BASE_CELL = 40

const PROPERTIES = [
  {
    name: '非线性',
    text: '没有任何线性函数能拟合它，这是抵抗线性密码分析的关键。',
  },
  {
    name: '无固定点',
    text: '对任意 x，S(x) ≠ x，也不存在 S(x) = ¬x —— 没有哪个字节会原地不动。',
  },
  {
    name: '差分均匀',
    text: '任意输入差分的输出差分分布高度均匀（最大 4/256），抵抗差分分析。',
  },
] as const

const route = useRoute()
const inverse = ref(false)
const selected = ref(0x53) // 默认落在 FIPS-197 §5.1.1 的示例字节上
const zoom = ref(1)
const query = ref('')
const searchError = ref(false)
const resolved = ref('')
const fromWorkbench = ref(false)

const values = computed(() => (inverse.value ? INV_SBOX : SBOX))
const cellPx = computed(() => BASE_CELL * zoom.value)

const hex = (value: number): string => value.toString(16).toUpperCase().padStart(2, '0')

/**
 * 搜索框接受三种写法，规则写死并把解析结果回显，不让用户猜：
 *   0x3f → 十六进制；3f（含 a–f）→ 十六进制；63（纯数字）→ 十进制。
 * 纯数字按十进制是刻意的：这样「63」就是 0x3F，与设计稿一致；
 * 想输十六进制的 63 请写 0x63，右侧回显会立刻告诉你解析成了什么。
 */
function parseSearch(raw: string): { value: number; label: string } | null {
  const text = raw.trim().toLowerCase()
  if (!text) return null

  if (/^0x[0-9a-f]{1,2}$/.test(text)) {
    const value = Number.parseInt(text.slice(2), 16)
    return { value, label: `十六进制 ${text.slice(2).toUpperCase()} → 0x${hex(value)}` }
  }
  if (/^[0-9a-f]{1,2}$/.test(text) && /[a-f]/.test(text)) {
    const value = Number.parseInt(text, 16)
    return { value, label: `十六进制 ${text.toUpperCase()} → 0x${hex(value)}` }
  }
  if (/^\d{1,3}$/.test(text)) {
    const value = Number.parseInt(text, 10)
    if (value > 255) return null
    return { value, label: `十进制 ${value} → 0x${hex(value)}` }
  }
  return null
}

watch(query, () => {
  searchError.value = false
  const parsed = parseSearch(query.value)
  resolved.value = parsed ? parsed.label : ''
})

function locate(): void {
  const parsed = parseSearch(query.value)
  if (!parsed) {
    searchError.value = true
    resolved.value = ''
    return
  }
  searchError.value = false
  selected.value = parsed.value
}

/** 切方向时保持「同一对字节」：53 → ED 切过去就变成 ED → 53，不把用户丢到另一个数上。 */
function setMode(next: boolean): void {
  if (next === inverse.value) return
  const table = next ? SBOX : INV_SBOX
  selected.value = table[selected.value] ?? 0
  inverse.value = next
  // 搜索框跟着走，否则它还会挂着切换前的字节和解析结果，和网格对不上
  query.value = `0x${hex(selected.value)}`
}

onMounted(() => {
  fromWorkbench.value = route.query.from === 'workbench'
  const raw = typeof route.query.b === 'string' ? route.query.b : ''
  if (!raw) return
  const parsed = parseSearch(raw)
  if (!parsed) return
  selected.value = parsed.value
  query.value = raw
})
</script>

<style scoped>
.sbox {
  min-height: calc(100dvh - var(--nav-h));
  padding: var(--sp-6);
  background: var(--paper-0);
}

.sbox__head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--sp-6);
  flex-wrap: wrap;
  padding-bottom: var(--sp-3);
  border-bottom: var(--rule-region-w) solid var(--line-hairline);
}

.sbox__title {
  font-family: var(--font-display);
  font-size: var(--fs-h1);
  font-weight: 600;
  letter-spacing: 0.01em;
  color: var(--ink-1);
}

.sbox__lede {
  margin-top: var(--sp-1);
  max-width: 52ch;
  font-size: var(--fs-ui);
  line-height: var(--lh-snug);
  color: var(--ink-2);
}

.sbox__tools {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  flex-wrap: wrap;
}

.sbox__modes {
  display: flex;
  border: var(--rule-region-w) solid var(--line-default);
  border-radius: var(--r-control);
  overflow: hidden;
}

.sbox__mode {
  height: 32px;
  padding: 0 var(--sp-3);
  border: 0;
  background: var(--paper-0);
  font-size: var(--fs-ui);
  color: var(--ink-2);
  cursor: pointer;
}

.sbox__mode + .sbox__mode {
  border-left: var(--rule-region-w) solid var(--line-default);
}

.sbox__mode[aria-pressed='true'] {
  background: var(--step-sub-tint);
  color: var(--step-sub-ink);
  font-weight: 600;
}

.sbox__search {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  height: 32px;
  padding: 0 var(--sp-2);
  border: var(--rule-region-w) solid var(--line-default);
  border-radius: var(--r-control);
  background: var(--paper-0);
}

.sbox__search:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-ring);
}

.sbox__search-input {
  width: 15ch;
  border: 0;
  background: transparent;
  font-family: var(--font-mono);
  font-size: var(--fs-ui);
  color: var(--ink-1);
}

.sbox__search-input:focus {
  outline: none;
}

.sbox__search-go {
  height: 22px;
  padding: 0 var(--sp-2);
  border: var(--rule-region-w) solid var(--line-default);
  border-radius: var(--r-control);
  background: var(--paper-1);
  font-size: var(--fs-micro);
  color: var(--ink-2);
  cursor: pointer;
}

.sbox__resolved {
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-3);
  white-space: nowrap;
}

.sbox__back {
  font-size: var(--fs-ui);
  color: var(--ink-2);
  text-decoration: none;
  border-bottom: var(--rule-region-w) solid var(--line-default);
}

.sbox__back:hover {
  color: var(--accent-strong);
  border-color: var(--accent);
}

.sbox__back.is-from {
  display: inline-flex;
  align-items: center;
  height: 32px;
  padding: 0 var(--sp-2);
  border: var(--rule-region-w) solid var(--accent);
  border-radius: var(--r-control);
  color: var(--accent-strong);
}

.sbox__error {
  margin-top: var(--sp-3);
  font-size: var(--fs-micro);
  color: var(--st-error);
}

.sbox__body {
  display: flex;
  align-items: flex-start;
  gap: var(--sp-8);
  margin-top: var(--sp-6);
}

.sbox__gridwrap {
  /* 不拉伸：网格是定宽表（16×40px + 间隙），拉宽只会把详情卡推远、中间留一条空白 */
  flex: none;
  min-width: 0;
}

.sbox__caption {
  margin-bottom: var(--sp-3);
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  letter-spacing: var(--ls-label);
  color: var(--ink-3);
}

.sbox__scroll {
  overflow-x: auto;
  padding-bottom: var(--sp-2);
}

.sbox__foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-4);
  margin-top: var(--sp-3);
  flex-wrap: wrap;
}

.sbox__hint {
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

.sbox__zoom {
  display: none;
  gap: 2px;
}

.sbox__zoom-btn {
  height: 26px;
  padding: 0 var(--sp-2);
  border: var(--rule-region-w) solid var(--line-default);
  border-radius: var(--r-control);
  background: var(--paper-0);
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-2);
  cursor: pointer;
}

.sbox__zoom-btn[aria-pressed='true'] {
  background: var(--step-sub-tint);
  border-color: var(--step-sub-ink);
  color: var(--step-sub-ink);
}

.sbox__props {
  display: grid;
  /* 三列是常态，宽 1024 也还放得下；到手机宽度自然收成一列 */
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: var(--sp-4);
  margin-top: var(--sp-8);
}

.sbox__prop {
  padding: var(--sp-3) var(--sp-4);
  border-top: 2px solid var(--step-sub-ink);
  border-radius: 0 0 var(--card-r) var(--card-r);
  background: var(--step-sub-tint);
}

.sbox__prop-name {
  font-family: var(--font-display);
  font-size: var(--fs-ui);
  font-weight: 600;
  color: var(--step-sub-ink);
}

.sbox__prop-text {
  margin-top: var(--sp-1);
  font-size: var(--fs-micro);
  line-height: var(--lh-body);
  color: var(--ink-2);
}

@media (max-width: 71.9375rem) {
  .sbox {
    padding: var(--sp-4);
  }

  .sbox__body {
    flex-direction: column;
    gap: var(--sp-6);
  }

  .sbox__gridwrap {
    width: 100%;
  }

  .sbox__zoom {
    display: flex;
  }
}
</style>
