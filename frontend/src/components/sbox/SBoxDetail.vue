<template>
  <aside class="sbox-detail" data-sbox-detail>
    <header class="sbox-detail__head">
      <h2 class="sbox-detail__title">{{ inverse ? '反向查表' : '查表详情' }}</h2>
      <span class="sbox-detail__dir">{{ inverse ? 'S⁻¹' : 'S' }}</span>
    </header>

    <div class="sbox-detail__io">
      <div class="sbox-detail__row">
        <span class="sbox-detail__key">输入</span>
        <label class="sbox-detail__field">
          <span class="sbox-detail__prefix">0x</span>
          <input
            v-model="draft"
            class="sbox-detail__input"
            name="sbox-input"
            inputmode="text"
            spellcheck="false"
            autocomplete="off"
            maxlength="4"
            :aria-invalid="invalid"
            aria-label="输入字节（十六进制）"
            @change="commit"
            @keydown.enter.prevent="commit"
            @blur="commit"
          />
        </label>
      </div>
      <div class="sbox-detail__row sbox-detail__row--sub">
        <span class="sbox-detail__key">二进制</span>
        <span class="sbox-detail__bits">{{ bits(value) }}</span>
      </div>

      <p class="sbox-detail__arrow">{{ inverse ? '↓ 反查 S⁻¹' : '↓ 查表 S' }}</p>

      <div class="sbox-detail__row">
        <span class="sbox-detail__key">输出</span>
        <span class="sbox-detail__out" data-sbox-output>{{ hex(output) }}</span>
      </div>
      <div class="sbox-detail__row sbox-detail__row--sub">
        <span class="sbox-detail__key">二进制</span>
        <span class="sbox-detail__bits">{{ bits(output) }}</span>
      </div>

      <p v-if="invalid" class="sbox-detail__error" role="alert">
        只接受 1–2 位十六进制（0–FF），已退回上一个值。
      </p>
    </div>

    <section v-if="!inverse" class="sbox-detail__why">
      <h3 class="sbox-detail__why-title">为什么是 {{ hex(output) }}？</h3>
      <ol class="sbox-detail__steps">
        <li>
          <span class="sbox-detail__step-name">求逆</span>
          <p v-if="value === 0" class="sbox-detail__step-text">
            0 在 GF(2⁸) 里没有乘法逆元，FIPS-197 直接规定它取
            <span class="sbox-detail__mono">00</span>。
          </p>
          <p v-else class="sbox-detail__step-text">
            在 GF(2⁸) 里找 <span class="sbox-detail__mono">{{ hex(value) }} · x = 01</span>，
            得到逆元 <span class="sbox-detail__mono">{{ hex(inverseOf(value)) }}</span>。
          </p>
        </li>
        <li>
          <span class="sbox-detail__step-name">仿射</span>
          <p class="sbox-detail__step-text">
            逆元做一次固定的位混合，再异或 <span class="sbox-detail__mono">63</span>：
          </p>
          <p class="sbox-detail__formula">
            <span class="sbox-detail__formula-body">{{ affineBody }}</span>
            <span class="sbox-detail__formula-result">= {{ hex(output) }}</span>
          </p>
        </li>
        <li>
          <span class="sbox-detail__step-name">结果</span>
          <p class="sbox-detail__step-text">
            得到 <span class="sbox-detail__mono">{{ hex(output) }}</span>，与表里第
            {{ value >> 4 }} 行第 {{ value & 15 }} 列一致。
          </p>
        </li>
      </ol>
      <p class="sbox-detail__note">
        <template v-if="value === 0">
          所以 S(00) = 63 完全来自仿射那一步的常数项：0 异或任何数都不变，最后异或
          63 才把它推到 63 —— 顺带避开了 0 映射到 0 的固定点。
        </template>
        <template v-else>
          「<<<」是 8 位循环左移：移出去的位绕回最低位，不是普通左移。<br />
          例子取自 FIPS-197 §5.1.1（输入 53，逆元 CA，输出 ED）。
        </template>
      </p>
    </section>

    <section v-else class="sbox-detail__why">
      <h3 class="sbox-detail__why-title">为什么能反查？</h3>
      <ol class="sbox-detail__steps">
        <li>
          <span class="sbox-detail__step-name">双射</span>
          <p class="sbox-detail__step-text">
            256 个输入正好铺满 256 个输出，没有两个输入撞到同一个值。
          </p>
        </li>
        <li>
          <span class="sbox-detail__step-name">唯一</span>
          <p class="sbox-detail__step-text">
            {{ hex(value) }} 在正向表里只出现一次，来源只能是
            <span class="sbox-detail__mono">{{ hex(output) }}</span>。
          </p>
        </li>
        <li>
          <span class="sbox-detail__step-name">成表</span>
          <p class="sbox-detail__step-text">
            逆向表由正向表倒着写一遍程序生成，不手抄第二张表 —— 手抄才是 bug 的来源。
          </p>
        </li>
      </ol>
      <p class="sbox-detail__note">
        SubBytes 解密时用 S⁻¹；密钥扩展只用正向 S。
      </p>
    </section>
  </aside>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { affineTerms, gfInverse } from '../../engine/gf'
import { INV_SBOX, SBOX } from '../../engine/sbox'

const props = defineProps<{
  value: number
  inverse: boolean
}>()

const emit = defineEmits<{
  'update:value': [value: number]
}>()

const hex = (value: number): string =>
  value.toString(16).toUpperCase().padStart(2, '0')

const bits = (value: number): string => {
  const text = (value & 0xff).toString(2).padStart(8, '0')
  return `${text.slice(0, 4)} ${text.slice(4)}`
}

const draft = ref(hex(props.value))
const invalid = ref(false)

watch(
  () => props.value,
  (value) => {
    draft.value = hex(value)
    invalid.value = false
  },
)

const output = computed(() => (props.inverse ? INV_SBOX[props.value] ?? 0 : SBOX[props.value] ?? 0))

const inverseOf = (value: number): number => gfInverse(value)

// 把「求逆 → 仿射」的每一项都摊开，读者能自己对着算一遍（末尾 63 是仿射常数项）
const affineBody = computed(
  () =>
    `${affineTerms(gfInverse(props.value))
      .map((term) => hex(term))
      .join(' ⊕ ')} ⊕ 63`,
)

/** 只认 1–2 位十六进制；填错就退回上一个合法值，不静默改数。 */
function commit(): void {
  const clean = draft.value.trim().replace(/^0x/i, '')
  if (!/^[0-9a-f]{1,2}$/i.test(clean)) {
    draft.value = hex(props.value)
    invalid.value = true
    return
  }
  const next = Number.parseInt(clean, 16)
  invalid.value = false
  draft.value = hex(next)
  if (next !== props.value) emit('update:value', next)
}
</script>

<style scoped>
.sbox-detail {
  position: sticky;
  top: calc(var(--nav-h) + var(--sp-6));
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
  width: 320px;
  max-width: 100%;
  padding: var(--sp-4);
  border: var(--rule-region-w) solid var(--line-default);
  border-radius: var(--card-r);
  background: var(--surface-raised);
}

.sbox-detail__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--sp-2);
  padding-bottom: var(--sp-2);
  border-bottom: var(--rule-region-w) solid var(--line-hairline);
}

.sbox-detail__title {
  font-family: var(--font-display);
  font-size: var(--fs-h3);
  font-weight: 600;
  color: var(--ink-1);
}

.sbox-detail__dir {
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  letter-spacing: var(--ls-label);
  color: var(--accent-strong);
}

.sbox-detail__io {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
}

.sbox-detail__row {
  display: grid;
  grid-template-columns: 56px minmax(0, 1fr);
  align-items: center;
  gap: var(--sp-2);
  min-height: 32px;
}

.sbox-detail__row--sub {
  min-height: 20px;
}

.sbox-detail__key {
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

.sbox-detail__field {
  display: flex;
  align-items: center;
  gap: 2px;
  width: 132px;
  padding: 0 var(--sp-2);
  height: 32px;
  border: var(--rule-region-w) solid var(--line-default);
  border-radius: var(--r-control);
  background: var(--paper-0);
}

.sbox-detail__field:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-ring);
}

.sbox-detail__prefix {
  font-family: var(--font-mono);
  font-size: var(--fs-ui);
  color: var(--ink-3);
}

.sbox-detail__input {
  width: 100%;
  min-width: 0;
  border: 0;
  background: transparent;
  font-family: var(--font-mono);
  font-size: var(--fs-body);
  letter-spacing: var(--ls-hex-cell);
  text-transform: uppercase;
  color: var(--ink-1);
}

.sbox-detail__input:focus {
  outline: none;
}

.sbox-detail__bits {
  font-family: var(--font-mono);
  font-size: var(--fs-ui);
  letter-spacing: 0.10em;
  color: var(--ink-2);
}

.sbox-detail__out {
  font-family: var(--font-mono);
  font-size: var(--fs-h2);
  letter-spacing: var(--ls-hex-cell);
  color: var(--accent-strong);
}

.sbox-detail__arrow {
  margin: var(--sp-1) 0 var(--sp-1) 56px;
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

.sbox-detail__error {
  margin-top: var(--sp-2);
  font-size: var(--fs-micro);
  color: var(--st-error);
}

.sbox-detail__why {
  padding-top: var(--sp-3);
  border-top: var(--rule-region-w) solid var(--line-hairline);
}

.sbox-detail__why-title {
  font-family: var(--font-display);
  font-size: var(--fs-ui);
  font-weight: 600;
  color: var(--ink-1);
}

.sbox-detail__steps {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  margin: var(--sp-3) 0 0;
  padding: 0;
  list-style: none;
  counter-reset: why;
}

.sbox-detail__steps li {
  position: relative;
  padding-left: var(--sp-6);
  counter-increment: why;
}

.sbox-detail__steps li::before {
  content: counter(why);
  position: absolute;
  left: 0;
  top: 1px;
  width: 16px;
  height: 16px;
  border: var(--rule-region-w) solid var(--line-default);
  border-radius: 50%;
  font-family: var(--font-mono);
  font-size: 10px;
  line-height: 14px;
  text-align: center;
  color: var(--ink-3);
}

.sbox-detail__step-name {
  display: block;
  font-size: var(--fs-label);
  font-weight: 600;
  color: var(--ink-2);
}

.sbox-detail__step-text {
  margin-top: 2px;
  font-size: var(--fs-micro);
  line-height: var(--lh-body);
  color: var(--ink-2);
}

.sbox-detail__mono {
  font-family: var(--font-mono);
  color: var(--ink-1);
}

.sbox-detail__formula {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0 var(--sp-2);
  margin-top: var(--sp-1);
  padding: var(--sp-2);
  border-radius: var(--r-control);
  background: var(--surface-inset);
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  line-height: 1.5;
  letter-spacing: 0.02em;
  color: var(--ink-1);
}

/* 逐项换行，但每一项本身不许被拆开 —— 否则 "ED" 会被断成 "E / D" */
.sbox-detail__formula-body {
  flex: 1 1 100%;
  min-width: 0;
  word-spacing: 0.08em;
}

.sbox-detail__formula-result {
  color: var(--accent-strong);
  font-weight: 600;
  white-space: nowrap;
}

.sbox-detail__note {
  margin-top: var(--sp-3);
  font-size: var(--fs-micro);
  line-height: var(--lh-body);
  color: var(--ink-3);
}

@media (max-width: 71.9375rem) {
  .sbox-detail {
    position: static;
    /* 掉到网格下方后不拉满：320 的卡铺成 960 宽只剩一片空白 */
    width: 100%;
    max-width: 640px;
  }
}
</style>
