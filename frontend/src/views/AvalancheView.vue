<template>
  <main class="av">
    <header class="av__head">
      <div class="av__intro">
        <h1 class="av__title">雪崩实验</h1>
        <p class="av__lede">
          改 1 位，密文变一半。这不是巧合，是列混合和行移位叠了 10 轮之后必然的结果。
        </p>
      </div>

      <RouterLink class="av__back" to="/workbench" data-action="back-workbench">
        返回工作台
      </RouterLink>
    </header>

    <section class="av__panel" aria-labelledby="av-setup">
      <h2 id="av-setup" class="av__panel-title">设置</h2>

      <div class="av__row">
        <span class="av__label">改哪一块</span>
        <div class="av__seg" role="radiogroup" aria-label="改明文还是改密钥">
          <button
            v-for="option in TARGETS"
            :key="option.key"
            type="button"
            role="radio"
            class="av__seg-btn"
            :aria-checked="target === option.key"
            :data-target="option.key"
            @click="setTarget(option.key)"
          >
            {{ option.label }}
          </button>
        </div>
      </div>

      <div class="av__fields">
        <label class="av__field">
          <span>明文（32 位十六进制）</span>
          <input
            v-model="plaintext"
            name="plaintext"
            data-input="plaintext"
            spellcheck="false"
            autocomplete="off"
            autocapitalize="off"
          />
        </label>

        <label class="av__field">
          <span>密钥（32 / 48 / 64 位十六进制）</span>
          <input
            v-model="keyHex"
            name="key"
            data-input="key"
            spellcheck="false"
            autocomplete="off"
            autocapitalize="off"
          />
        </label>
      </div>

      <div class="av__row av__row--picker">
        <span class="av__label">改哪个字节</span>
        <p class="av__hint">点一下，翻它的最低位（第 0 位）</p>
      </div>

      <div class="av__bytes" role="group" aria-label="选择要翻转的字节" data-byte-picker>
        <button
          v-for="(value, index) in targetBytes"
          :key="index"
          type="button"
          class="av__byte"
          :class="{ 'is-active': index === byteIndex }"
          :aria-pressed="index === byteIndex"
          :data-byte="index"
          @click="byteIndex = index"
        >
          <span class="av__byte-no">{{ String(index).padStart(2, '0') }}</span>
          <span class="av__byte-val">{{ hex(value) }}</span>
        </button>
      </div>

      <div class="av__actions">
        <button type="button" class="av__go" data-action="run" :disabled="!ready || running" @click="run(true)">
          {{ running ? '正在算…' : '改 1 位看看' }}
        </button>
        <button
          type="button"
          class="av__sweep-btn"
          data-action="sweep"
          :disabled="!ready || sweeping"
          @click="runSweep"
        >
          {{ sweeping ? '正在算…' : `连做 ${targetBytes.length || 16} 次` }}
        </button>
        <p v-if="!ready" class="av__warn" role="status" data-input-warn>
          明文要正好 32 位十六进制，密钥要 32 / 48 / 64 位（对应 AES-128 / 192 / 256）。
        </p>
        <p v-else-if="sweepNote" class="av__warn" data-sweep-note>{{ sweepNote }}</p>
      </div>

      <p v-if="error" class="av__error" role="alert" data-error>{{ error }}</p>
    </section>

    <section v-if="result" ref="resultRef" class="av__result" aria-labelledby="av-verdict">
      <h2 id="av-verdict" class="av__panel-title">结果</h2>

      <p class="av__verdict-line" data-flip>
        改了 {{ targetLabel }}第 <b>{{ result.byte_index }}</b> 字节的
        <b>{{ hex(result.input_byte_before) }}</b> → <b>{{ hex(result.input_byte_after) }}</b>
      </p>

      <!-- 先给数字，再给证据：62 / 128 是结论，位图是支撑它的东西。
           反过来（先画一百多个格子）读者要自己数，数完才敢信。 -->
      <div class="av__stats">
        <p class="av__big">
          <b data-stat="changed-bits">{{ result.changed_bits }}</b>
          <span class="av__big-unit">/ {{ result.total_bits }} 位变了</span>
          <em data-stat="rate">{{ percent }}%</em>
        </p>

        <div class="av__meter" aria-hidden="true">
          <span class="av__meter-fill" :style="{ width: `${percent}%` }"></span>
          <i class="av__meter-ideal"></i>
        </div>

        <p class="av__verdict-line">
          {{ result.total_bytes }} 个字节里，<b data-stat="changed-bytes">{{ result.changed_bytes }}</b>
          个变了。
          <span class="av__verdict-soft">
            一半的位翻转，就是「密文和明文之间没有可用的相似性」的量化说法。
          </span>
        </p>
      </div>

      <div class="av__compare" data-compare>
        <div class="av__line">
          <span class="av__rowlabel">原密文</span>
          <div class="av__track">
            <span v-for="(cell, index) in result.before.cells" :key="index" class="av__cell">
              {{ hex(cell) }}
            </span>
          </div>
        </div>

        <div class="av__line">
          <span class="av__rowlabel">改 1 位后</span>
          <div class="av__track">
            <span
              v-for="(cell, index) in result.after.cells"
              :key="index"
              class="av__cell av__cell--diff"
              :class="`is-l${diffLevel(result.byte_bits[index] ?? 0)}`"
              :title="`这个字节变了 ${result.byte_bits[index] ?? 0} 位`"
            >
              {{ hex(cell) }}
            </span>
          </div>
        </div>

        <div class="av__line av__line--bits">
          <span class="av__rowlabel">哪一位变了</span>
          <div class="av__track av__track--bits" data-bitmap>
            <div
              v-for="(column, columnIndex) in bitColumns"
              :key="columnIndex"
              class="av__bitcol"
              :data-byte="columnIndex"
            >
              <span
                v-for="(on, bitIndex) in column"
                :key="bitIndex"
                class="av__bit"
                :class="{ 'is-on': on }"
              ></span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section v-if="sweep" class="av__sweep" aria-labelledby="av-sweep-title">
      <div class="av__sweep-head">
        <h2 id="av-sweep-title" class="av__panel-title">连做 {{ sweep.trials }} 次</h2>
        <p class="av__sweep-lede">
          {{ targetLabel }}的每个字节各翻一次最低位，平均
          <b data-stat="sweep-mean">{{ sweep.mean }}</b> / {{ sweep.total_bits }} 位变了（理论值
          {{ sweep.ideal_bits }}）。
        </p>
      </div>

      <div class="av__bars" data-sweep-bars>
        <div
          v-for="sample in sweep.samples"
          :key="sample.byte_index"
          class="av__bar"
          :title="`第 ${sample.byte_index} 字节：${hex(sample.byte_before)} → ${hex(sample.byte_after)}，变了 ${sample.changed_bits} 位`"
        >
          <span
            class="av__bar-fill"
            :style="{ height: `${barHeight(sample.changed_bits, sweep.total_bits)}%` }"
          >
            <span class="av__bar-no">{{ sample.changed_bits }}</span>
          </span>
        </div>
        <div class="av__bars-ideal" aria-hidden="true"><span>理论中位 {{ sweep.ideal_bits }}</span></div>
      </div>

      <p class="av__sweep-foot">
        最低 {{ sweep.min_bits }} 位，最高 {{ sweep.max_bits }} 位。
        没有一次落在「只变了一点点」—— 改 1 位的影响，从第一轮列混合就扩散到整列，再被行移位摊到四列，
        第 2 轮之后已经找不到原来的结构。
      </p>
    </section>

    <section class="av__notes" aria-label="为什么是一半">
      <article class="av__note">
        <h3>为什么是 50%</h3>
        <p>
          理想的块密码对明文的作用接近随机置换：输入差 1 位，输出的每一位都该有 50% 的概率翻转，
          也就是 128 位里 64 位。AES 不是随机函数，但它被设计得足够接近。
        </p>
      </article>

      <article class="av__note">
        <h3>扩散从哪来</h3>
        <p>
          字节代换只改自己那一个字节；行移位把字节搬到别的列；
          <RouterLink to="/workbench?step=3">列混合</RouterLink>
          让一列 4 个字节互相纠缠。两轮就能覆盖整个状态，10 轮之后彻底分不清。
        </p>
      </article>

      <article class="av__note">
        <h3>所以「差一点」没有意义</h3>
        <p>
          明文或密钥差 1 位，密文就换掉一半。攻击者拿不到「接近正确答案」的线索，
          只能穷举。这是 AES 抵抗差分分析的基础，也是它敢用这么简单的四步反复 10 轮的原因。
        </p>
      </article>
    </section>

    <p class="av__foot">
      数值由后端 AES 引擎现算，与工作台用的是同一份实现（FIPS-197 附录 C 向量已校验）。
    </p>
  </main>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { barHeight, bitColumns as splitBits, diffLevel, percentOf } from '../utils/avalanche'

interface CipherSide {
  cipher_hex: string
  cells: number[]
}

interface AvalancheResult {
  target: 'plaintext' | 'key'
  byte_index: number
  bit_index: number
  key_bits: number
  input_byte_before: number
  input_byte_after: number
  before: CipherSide
  after: CipherSide
  changed_bits: number
  changed_bytes: number
  total_bits: number
  total_bytes: number
  ideal_bits: number
  rate: number
  bit_flags: boolean[]
  byte_bits: number[]
}

interface SweepSample {
  byte_index: number
  byte_before: number
  byte_after: number
  changed_bits: number
}

interface SweepResult {
  target: 'plaintext' | 'key'
  bit_index: number
  key_bits: number
  trials: number
  total_bits: number
  ideal_bits: number
  mean: number
  min_bits: number
  max_bits: number
  samples: SweepSample[]
}

const TARGETS = [
  { key: 'plaintext', label: '改明文' },
  { key: 'key', label: '改密钥' },
] as const

const FIPS_PLAINTEXT = '00112233445566778899aabbccddeeff'
const FIPS_KEY = '000102030405060708090a0b0c0d0e0f'

const route = useRoute()
const plaintext = ref(FIPS_PLAINTEXT)
const keyHex = ref(FIPS_KEY)
const target = ref<'plaintext' | 'key'>('plaintext')
const byteIndex = ref(0)
const result = ref<AvalancheResult | null>(null)
const resultRef = ref<HTMLElement | null>(null)
const sweep = ref<SweepResult | null>(null)
const running = ref(false)
const sweeping = ref(false)
const error = ref('')
const sweepNote = ref('')

const HEX = /^[0-9a-fA-F]+$/

function bytesOf(value: string): number[] | null {
  const text = value.trim()
  if (!text || text.length % 2 !== 0 || !HEX.test(text)) return null
  const out: number[] = []
  for (let i = 0; i < text.length; i += 2) out.push(parseInt(text.slice(i, i + 2), 16))
  return out
}

const targetBytes = computed(() => {
  if (target.value === 'plaintext') return bytesOf(plaintext.value)?.length === 16 ? bytesOf(plaintext.value)! : []
  const key = bytesOf(keyHex.value)
  return key && [16, 24, 32].includes(key.length) ? key : []
})

const ready = computed(() => {
  const plain = bytesOf(plaintext.value)
  const key = bytesOf(keyHex.value)
  return (
    plain?.length === 16 &&
    !!key &&
    [16, 24, 32].includes(key.length) &&
    byteIndex.value < targetBytes.value.length
  )
})

const targetLabel = computed(() => (result.value?.target === 'key' ? '密钥' : '明文'))
const percent = computed(() => percentOf(result.value?.rate ?? 0))

/** 16 列 × 8 行：一列正好对应密文行的 16 个字节，上下对齐。 */
const bitColumns = computed(() => splitBits(result.value?.bit_flags ?? []))

function hex(value: number): string {
  return value.toString(16).toUpperCase().padStart(2, '0')
}

function setTarget(next: 'plaintext' | 'key'): void {
  if (target.value === next) return
  target.value = next
  byteIndex.value = 0
}

async function run(scrollToResult = false): Promise<void> {
  if (!ready.value || running.value) return
  running.value = true
  error.value = ''
  try {
    const response = await fetch('/api/aes/avalanche', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        plaintext_hex: plaintext.value.trim(),
        key_hex: keyHex.value.trim(),
        target: target.value,
        byte_index: byteIndex.value,
        bit_index: 0,
      }),
    })
    const data = await response.json().catch(() => null)
    if (!response.ok) {
      error.value = data?.error?.message ?? `后端拒绝了这次请求（HTTP ${response.status}）`
      result.value = null
      return
    }
    result.value = data as AvalancheResult
    if (scrollToResult) {
      // 只有「点了按钮」才滚：自动重算（改输入、点字节）滚来滚去会很烦。
      // 移动端首屏塞不下结果区，不滚的话点完像没反应。
      await nextTick()
      resultRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  } catch {
    error.value = '连不上后端。雪崩数值由后端 AES 引擎现算，服务没起来时算不了。'
    result.value = null
  } finally {
    running.value = false
  }
}

async function runSweep(): Promise<void> {
  if (!ready.value || sweeping.value) return
  sweeping.value = true
  error.value = ''
  sweepNote.value = ''
  try {
    const response = await fetch('/api/aes/avalanche/sweep', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        plaintext_hex: plaintext.value.trim(),
        key_hex: keyHex.value.trim(),
        target: target.value,
        bit_index: 0,
      }),
    })
    const data = await response.json().catch(() => null)
    if (!response.ok) {
      error.value = data?.error?.message ?? `后端拒绝了这次请求（HTTP ${response.status}）`
      return
    }
    sweep.value = data as SweepResult
    sweepNote.value = `连做 ${sweep.value.trials} 次跑完了，平均 ${sweep.value.mean} 位。`
  } catch {
    error.value = '连不上后端，连做实验需要后端算完再返回。'
  } finally {
    sweeping.value = false
  }
}

let timer: number | undefined

watch([plaintext, keyHex, target, byteIndex], () => {
  sweep.value = null
  sweepNote.value = ''
  window.clearTimeout(timer)

  // 输入一非法就把旧结果撤掉：数字挂在那儿但对应的已经不是这组输入，
  // 比空着更容易被读错（尤其答辩时有人顺手改了一位问「那这个呢」）。
  if (!ready.value) {
    result.value = null
    error.value = ''
    return
  }

  // 输入停手 220ms 再打后端：16 个字节连着点不该发 16 次请求
  timer = window.setTimeout(() => {
    void run()
  }, 220)
})

onMounted(() => {
  const queryPlain = route.query.pt
  const queryKey = route.query.key
  const queryTarget = route.query.target
  const queryByte = route.query.byte

  if (typeof queryPlain === 'string' && bytesOf(queryPlain)?.length === 16) {
    plaintext.value = queryPlain
  }
  if (typeof queryKey === 'string') {
    const parsed = bytesOf(queryKey)
    if (parsed && [16, 24, 32].includes(parsed.length)) keyHex.value = queryKey
  }
  if (queryTarget === 'key' || queryTarget === 'plaintext') target.value = queryTarget
  if (typeof queryByte === 'string') {
    const index = Number.parseInt(queryByte, 10)
    if (Number.isInteger(index) && index > 0 && index < 32) byteIndex.value = index
  }

  void run()
})
</script>

<style scoped>
.av {
  min-height: calc(100dvh - var(--nav-h));
  max-width: 1180px;
  margin: 0 auto;
  padding: var(--sp-6);
  background: var(--paper-0);
}

.av__head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--sp-6);
  flex-wrap: wrap;
  padding-bottom: var(--sp-3);
  border-bottom: var(--rule-region-w) solid var(--line-hairline);
}

.av__title {
  font-family: var(--font-display);
  font-size: var(--fs-h1);
  font-weight: 600;
  letter-spacing: 0.01em;
  color: var(--ink-1);
}

.av__lede {
  margin-top: var(--sp-1);
  max-width: 56ch;
  font-size: var(--fs-ui);
  line-height: var(--lh-snug);
  color: var(--ink-2);
}

.av__back {
  display: inline-flex;
  align-items: center;
  height: 32px;
  padding: 0 var(--sp-3);
  border: var(--rule-region-w) solid var(--line-default);
  border-radius: var(--r-control);
  font-size: var(--fs-ui);
  color: var(--ink-2);
  text-decoration: none;
  white-space: nowrap;
}

.av__back:hover {
  border-color: var(--accent);
  color: var(--accent-strong);
}

/* ---------- 设置 ---------- */

.av__panel {
  margin-top: var(--sp-4);
  padding: var(--sp-4);
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-float);
  background: var(--surface-raised);
}

.av__panel-title {
  font-family: var(--font-ui);
  font-size: var(--fs-label);
  font-weight: 600;
  letter-spacing: var(--ls-label);
  color: var(--ink-3);
}

.av__row {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  margin-top: var(--sp-3);
  flex-wrap: wrap;
}

.av__label {
  font-size: var(--fs-ui);
  color: var(--ink-2);
}

.av__hint {
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

.av__seg {
  display: inline-flex;
  border: var(--rule-region-w) solid var(--line-default);
  border-radius: var(--r-control);
  overflow: hidden;
}

.av__seg-btn {
  height: 30px;
  padding: 0 var(--sp-3);
  border: 0;
  background: var(--paper-0);
  font-family: var(--font-ui);
  font-size: var(--fs-ui);
  color: var(--ink-2);
  cursor: pointer;
}

.av__seg-btn + .av__seg-btn {
  border-left: var(--rule-region-w) solid var(--line-default);
}

.av__seg-btn[aria-checked='true'] {
  background: var(--accent-soft);
  color: var(--accent-strong);
  font-weight: 600;
}

.av__fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--sp-3);
  margin-top: var(--sp-3);
}

.av__field {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
  font-size: var(--fs-label);
  color: var(--ink-3);
}

.av__field input {
  height: 34px;
  padding: 0 var(--sp-2);
  border: var(--rule-region-w) solid var(--line-default);
  border-radius: var(--r-control);
  background: var(--paper-0);
  font-family: var(--font-mono);
  font-size: var(--fs-ui);
  letter-spacing: var(--ls-hex-long);
  color: var(--ink-1);
}

.av__field input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-ring);
}

.av__row--picker {
  margin-top: var(--sp-4);
}

.av__bytes {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-1);
  margin-top: var(--sp-2);
}

.av__byte {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1px;
  min-width: 46px;
  padding: 3px 0 4px;
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-cell);
  background: var(--paper-0);
  font-family: var(--font-mono);
  cursor: pointer;
}

.av__byte:hover {
  border-color: var(--line-strong);
}

.av__byte.is-active {
  border-color: var(--accent);
  background: var(--accent-soft);
}

.av__byte-no {
  font-size: var(--fs-micro);
  color: var(--ink-4);
  line-height: 1;
}

.av__byte-val {
  font-size: var(--fs-ui);
  color: var(--ink-1);
  line-height: 1.1;
}

.av__byte.is-active .av__byte-val {
  color: var(--accent-strong);
  font-weight: 600;
}

.av__actions {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  flex-wrap: wrap;
  margin-top: var(--sp-4);
  padding-top: var(--sp-3);
  border-top: var(--rule-region-w) solid var(--line-hairline);
}

.av__go,
.av__sweep-btn {
  height: 34px;
  padding: 0 var(--sp-4);
  border-radius: var(--r-control);
  font-family: var(--font-ui);
  font-size: var(--fs-ui);
  cursor: pointer;
}

.av__go {
  border: var(--rule-region-w) solid var(--accent);
  background: var(--accent);
  color: var(--paper-0);
  font-weight: 500;
}

.av__go:disabled,
.av__sweep-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.av__sweep-btn {
  border: var(--rule-region-w) solid var(--line-default);
  background: transparent;
  color: var(--ink-1);
}

.av__sweep-btn:hover:not(:disabled) {
  border-color: var(--accent);
  color: var(--accent-strong);
}

.av__warn {
  font-size: var(--fs-micro);
  color: var(--warn);
}

.av__error {
  margin-top: var(--sp-3);
  padding: var(--sp-2) var(--sp-3);
  border-left: 2px solid var(--st-error);
  background: var(--st-error-fill);
  font-size: var(--fs-ui);
  color: var(--ink-1);
}

/* ---------- 结果 ---------- */

.av__result {
  margin-top: var(--sp-6);
}

.av__verdict-line {
  margin-top: var(--sp-2);
  font-size: var(--fs-body);
  line-height: var(--lh-body);
  color: var(--ink-2);
}

.av__verdict-line b {
  font-family: var(--font-mono);
  font-weight: 600;
  color: var(--ink-1);
}

.av__verdict-soft {
  color: var(--ink-3);
}

.av__compare {
  margin-top: var(--sp-4);
  padding: var(--sp-3) var(--sp-4) var(--sp-4);
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-float);
  background: var(--surface-raised);
}

.av__line {
  display: grid;
  grid-template-columns: 84px minmax(0, 1fr);
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-1) 0;
}

.av__rowlabel {
  font-size: var(--fs-micro);
  color: var(--ink-3);
  white-space: nowrap;
}

.av__track {
  display: grid;
  grid-template-columns: repeat(16, minmax(0, 1fr));
  gap: var(--sp-1);
}

.av__cell {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 34px;
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-cell);
  background: var(--paper-0);
  font-family: var(--font-mono);
  font-size: var(--fs-ui);
  letter-spacing: var(--ls-hex-cell);
  color: var(--ink-1);
}

/* 差异强度色阶：只表达「这个字节变了几位」，不是对错，也不复用 is-changed */
.av__cell--diff.is-l1 {
  border-color: oklch(0.885 0.030 205);
  background: oklch(0.962 0.018 205);
}

.av__cell--diff.is-l2 {
  border-color: oklch(0.845 0.045 205);
  background: oklch(0.936 0.032 205);
}

.av__cell--diff.is-l3 {
  border-color: oklch(0.790 0.060 205);
  background: oklch(0.906 0.046 205);
}

.av__cell--diff.is-l4 {
  border-color: oklch(0.735 0.072 205);
  background: oklch(0.872 0.058 205);
  font-weight: 600;
}

.av__line--bits {
  align-items: start;
  padding-top: var(--sp-2);
}

.av__track--bits {
  gap: var(--sp-1);
}

.av__bitcol {
  display: grid;
  grid-template-rows: repeat(8, 1fr);
  gap: 2px;
  justify-items: center;
}

/* 每个「位」是小方块，不跟着列宽拉长：拉长就变成条形码，
   读不出「第 3 字节的第 5 位翻转了」这种粒度。 */
.av__bit {
  width: min(100%, 18px);
  height: 6px;
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: 1px;
  background: transparent;
}

.av__bit.is-on {
  border-color: var(--accent);
  background: var(--accent);
}

.av__stats {
  margin-top: var(--sp-3);
}

.av__big {
  display: flex;
  align-items: baseline;
  gap: var(--sp-2);
  flex-wrap: wrap;
}

.av__big b {
  font-family: var(--font-mono);
  font-size: clamp(2rem, 1.4rem + 1.6vw, 2.75rem);
  font-weight: 600;
  line-height: 1;
  color: var(--ink-1);
}

.av__big-unit {
  font-size: var(--fs-ui);
  color: var(--ink-3);
}

.av__big em {
  font-family: var(--font-mono);
  font-style: normal;
  font-size: var(--fs-body);
  color: var(--accent-strong);
}

.av__meter {
  position: relative;
  height: 8px;
  margin-top: var(--sp-2);
  border-radius: 1px;
  background: var(--surface-inset);
  overflow: hidden;
}

.av__meter-fill {
  position: absolute;
  inset: 0 auto 0 0;
  background: var(--accent);
}

.av__meter-ideal {
  position: absolute;
  top: -2px;
  bottom: -2px;
  left: 50%;
  width: 1px;
  background: var(--ink-4);
}

/* ---------- 连做 ---------- */

.av__sweep {
  margin-top: var(--sp-6);
  padding-top: var(--sp-4);
  border-top: var(--rule-region-w) solid var(--line-hairline);
}

.av__sweep-lede {
  margin-top: var(--sp-1);
  font-size: var(--fs-ui);
  line-height: var(--lh-snug);
  color: var(--ink-2);
}

.av__sweep-lede b {
  font-family: var(--font-mono);
  color: var(--ink-1);
}

.av__bars {
  position: relative;
  display: flex;
  align-items: flex-end;
  gap: var(--sp-1);
  height: 132px;
  margin-top: var(--sp-6);
  border-bottom: var(--rule-region-w) solid var(--line-default);
}

.av__bar {
  position: relative;
  z-index: 1;
  flex: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  align-items: center;
}

.av__bar-fill {
  position: relative;
  width: 100%;
  max-width: 34px;
  background: var(--accent);
  border-radius: 1px 1px 0 0;
  opacity: 0.85;
}

/* 数字挂在柱顶，不挂在容器顶：16 根柱一样高的时候，
   数字才会自己说明「其实不一样高」。 */
.av__bar-no {
  position: absolute;
  bottom: calc(100% + 2px);
  left: 50%;
  transform: translateX(-50%);
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  line-height: 1;
  color: var(--ink-3);
  white-space: nowrap;
}

.av__bars-ideal {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 50%;
  border-top: 1px dashed var(--line-strong);
  pointer-events: none;
}

.av__bars-ideal span {
  position: absolute;
  right: 0;
  bottom: 2px;
  font-size: var(--fs-micro);
  color: var(--ink-3);
  background: var(--paper-0);
  padding-left: var(--sp-1);
}

.av__sweep-foot {
  margin-top: var(--sp-3);
  font-size: var(--fs-ui);
  line-height: var(--lh-body);
  color: var(--ink-2);
}

/* ---------- 解释 ---------- */

.av__notes {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--sp-4);
  margin-top: var(--sp-8);
  padding-top: var(--sp-4);
  border-top: var(--rule-region-w) solid var(--line-hairline);
}

.av__note h3 {
  font-family: var(--font-display);
  font-size: var(--fs-h3);
  font-weight: 600;
  color: var(--ink-1);
}

.av__note p {
  margin-top: var(--sp-1);
  font-size: var(--fs-ui);
  line-height: var(--lh-body);
  color: var(--ink-2);
}

.av__note a {
  color: var(--accent-strong);
  text-decoration: none;
  border-bottom: var(--rule-region-w) solid var(--accent);
}

.av__foot {
  margin-top: var(--sp-6);
  padding-top: var(--sp-3);
  border-top: var(--rule-region-w) solid var(--line-hairline);
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

@media (max-width: 900px) {
  .av {
    padding: var(--sp-4);
  }

  .av__fields {
    grid-template-columns: 1fr;
  }

  .av__notes {
    grid-template-columns: 1fr;
    gap: var(--sp-3);
  }

  .av__line {
    grid-template-columns: 72px minmax(0, 1fr);
  }

  .av__cell {
    height: 30px;
    font-size: var(--fs-label);
  }
}

/* 窄屏不砍字节：16 列必须完整，否则「哪一位变了」的位图对不上密文。
   整块横向滚动，密文与位图一起走，对齐关系不破。 */
@media (max-width: 700px) {
  .av__compare {
    overflow-x: auto;
  }

  .av__line {
    min-width: 620px;
  }

  .av__cell {
    height: 28px;
    font-size: var(--fs-micro);
    letter-spacing: 0;
  }

  /* 32 个十六进制字符在 390 下差一点点放不下，降一档字号省掉横向滚动 */
  .av__field input {
    font-size: var(--fs-label);
    letter-spacing: 0;
  }
}
</style>
