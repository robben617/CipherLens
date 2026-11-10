<template>
  <div class="inp">
    <div class="inp__head">
      <h2 class="inp__title">输入</h2>

      <div class="seg" role="radiogroup" aria-label="输入方式">
        <button
          type="button"
          role="radio"
          class="seg__btn"
          :aria-checked="mode === 'hex'"
          @click="setMode('hex')"
        >
          十六进制
        </button>
        <button
          type="button"
          role="radio"
          class="seg__btn"
          :aria-checked="mode === 'text'"
          @click="setMode('text')"
        >
          文本
        </button>
      </div>
    </div>

    <!-- 明文 -->
    <div class="inp__field">
      <label class="inp__label" for="in-plain">明文</label>

      <textarea
        v-if="mode === 'hex'"
        id="in-plain"
        class="inp__area"
        rows="2"
        spellcheck="false"
        autocomplete="off"
        autocapitalize="off"
        :value="plainDraft"
        :aria-describedby="plainCountId"
        @input="onPlainInput"
      />
      <textarea
        v-else
        id="in-plain"
        class="inp__area inp__area--text"
        rows="2"
        spellcheck="false"
        autocomplete="off"
        :value="textDraft"
        :aria-describedby="plainCountId"
        @input="onTextInput"
      />

      <p :id="plainCountId" class="inp__count" :class="plainState.cls">
        {{ plainState.text }}
      </p>
      <p v-if="plainState.hint" class="inp__hint" role="status">{{ plainState.hint }}</p>
    </div>

    <!-- 密钥 -->
    <div class="inp__field">
      <label class="inp__label" for="in-key">密钥</label>

      <textarea
        id="in-key"
        class="inp__area"
        rows="3"
        spellcheck="false"
        autocomplete="off"
        autocapitalize="off"
        :value="keyDraft"
        :aria-describedby="keyCountId"
        @input="onKeyInput"
      />

      <p :id="keyCountId" class="inp__count" :class="keyState.cls">{{ keyState.text }}</p>

      <div class="seg seg--wide" role="radiogroup" aria-label="密钥长度">
        <button
          v-for="b in BITS"
          :key="b"
          type="button"
          role="radio"
          class="seg__btn"
          :aria-checked="bits === b"
          @click="setBits(b)"
        >
          {{ b }}
        </button>
      </div>
    </div>

    <div class="inp__field">
      <label class="inp__label" for="in-demo">示例</label>
      <select id="in-demo" class="inp__select" :value="''" @change="onDemoPick">
        <option value="" disabled>选一组标准向量</option>
        <option v-for="v in DEMOS" :key="v.id" :value="v.id">
          {{ v.id }}（{{ v.key_bits }} 位）
        </option>
      </select>
    </div>

    <div class="inp__actions">
      <button type="button" class="inp__go" :disabled="!canApply" @click="apply">
        生成演示
      </button>
      <button type="button" class="inp__rand" @click="randomize">随机</button>
    </div>

    <p v-if="notice" class="inp__notice" role="alert">{{ notice }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, useId, watch } from 'vue'
import { FIPS_197_VECTORS } from '../../engine/vectors'

/** 明文固定 16 字节；密钥随位数 16/24/32 字节 */
const PLAIN_BYTES = 16
const BITS = [128, 192, 256] as const
type Bits = (typeof BITS)[number]

const props = defineProps<{
  /** 当前生效的明文 hex（父组件的真值） */
  plaintext: string
  /** 当前生效的密钥 hex。**不叫 key**——key 是 Vue 保留属性，做 prop 名会失效 */
  keyHex: string
}>()

const emit = defineEmits<{
  apply: [plaintext: string, key: string]
  notice: [text: string]
}>()

const uid = useId()
const plainCountId = `plain-count-${uid}`
const keyCountId = `key-count-${uid}`

const DEMOS = FIPS_197_VECTORS

const mode = ref<'hex' | 'text'>('hex')
const plainDraft = ref(props.plaintext)
const keyDraft = ref(props.keyHex)
const textDraft = ref('')
const notice = ref('')

const bits = computed<Bits>(() => {
  const len = keyDraft.value.length
  if (len > 48) return 256
  if (len > 32) return 192
  return 128
})

/** 密钥字节数：128 位 = 16 字节……（**不是 bits/4**，那是字符数） */
const keyBytes = computed(() => bits.value / 8)

/** 只保留十六进制字符；返回清洗结果与被丢弃的字符数 */
function cleanHex(raw: string): { hex: string; dropped: number } {
  const stripped = raw.replace(/0x/gi, '')
  const hex = stripped.replace(/[^0-9a-fA-F]/g, '').toLowerCase()
  return { hex, dropped: stripped.length - hex.length }
}

function toHex(text: string): string {
  return Array.from(new TextEncoder().encode(text))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
}

const textHex = computed(() => toHex(textDraft.value))

const plainState = computed(() => {
  if (mode.value === 'text') {
    const bytes = textHex.value.length / 2
    if (bytes === 0) {
      return { cls: 'is-warn', text: '0 / 16 字节', hint: '输入任意文字，按 UTF-8 编成字节' }
    }
    if (bytes < PLAIN_BYTES) {
      return {
        cls: 'is-warn',
        text: `${bytes} / 16 字节`,
        hint: `已用 ${bytes} 字节，其余位置补 0`,
      }
    }
    return {
      cls: 'is-ok',
      text: '16 / 16 字节',
      hint: bytes > PLAIN_BYTES ? `超出 ${bytes - PLAIN_BYTES} 字节，已截断` : '',
    }
  }

  const chars = plainDraft.value.length
  if (chars === 0) return { cls: 'is-warn', text: '0 / 16 字节', hint: '' }
  if (chars < 32) {
    return {
      cls: 'is-warn',
      text: `${chars} / 32 字符`,
      hint: `还差 ${32 - chars} 个十六进制字符`,
    }
  }
  return { cls: 'is-ok', text: '16 / 16 字节', hint: '' }
})

const keyState = computed(() => {
  const need = keyBytes.value * 2
  const chars = keyDraft.value.length
  if (chars === need) {
    return { cls: 'is-ok', text: `${keyBytes.value} / ${keyBytes.value} 字节` }
  }
  return {
    cls: 'is-warn',
    text: `${chars} / ${need} 字符`,
    hint: '',
  }
})

const canApply = computed(() => {
  const plainHex = mode.value === 'text' ? textHex.value : plainDraft.value
  return plainHex.length >= 32 && keyDraft.value.length === keyBytes.value * 2
})

watch(
  () => [props.plaintext, props.keyHex] as const,
  ([pt, k]) => {
    plainDraft.value = pt
    keyDraft.value = k
  },
)

function flash(text: string): void {
  notice.value = text
  emit('notice', text)
  window.setTimeout(() => {
    if (notice.value === text) notice.value = ''
  }, 2400)
}

function onPlainInput(event: Event): void {
  const el = event.target as HTMLTextAreaElement
  const { hex, dropped } = cleanHex(el.value)
  const clipped = hex.slice(0, 32)
  plainDraft.value = clipped
  // 受控回写：清掉非法字符后必须把 DOM 值同步回去，否则光标后会出现「幽灵字符」
  if (el.value !== clipped) el.value = clipped
  if (dropped > 0) flash(`已忽略 ${dropped} 个非十六进制字符`)
}

function onTextInput(event: Event): void {
  textDraft.value = (event.target as HTMLTextAreaElement).value
}

function onKeyInput(event: Event): void {
  const el = event.target as HTMLTextAreaElement
  const { hex, dropped } = cleanHex(el.value)
  const clipped = hex.slice(0, 64)
  keyDraft.value = clipped
  if (el.value !== clipped) el.value = clipped
  if (dropped > 0) flash(`已忽略 ${dropped} 个非十六进制字符`)
}

function setMode(next: 'hex' | 'text'): void {
  if (next === mode.value) return
  if (next === 'text') {
    // 从 hex 切文本：保留空文本，由用户重新输入（hex 无法反解成有意义的文本）
    textDraft.value = ''
  }
  mode.value = next
}

function setBits(next: Bits): void {
  const need = next / 8
  let hex = keyDraft.value
  if (hex.length < need * 2) {
    hex = hex.padEnd(need * 2, '0')
    flash(`密钥已用 0 补齐到 ${need} 字节`)
  } else if (hex.length > need * 2) {
    hex = hex.slice(0, need * 2)
    flash(`密钥已截断到 ${need} 字节`)
  }
  keyDraft.value = hex
}

function onDemoPick(event: Event): void {
  const id = (event.target as HTMLSelectElement).value
  const vector = DEMOS.find((v) => v.id === id)
  if (!vector) return
  mode.value = 'hex'
  plainDraft.value = vector.plaintext_hex
  keyDraft.value = vector.key_hex
  apply()
}

function randomize(): void {
  const bytes = new Uint8Array(16)
  crypto.getRandomValues(bytes)
  plainDraft.value = Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')

  const keyLen = keyBytes.value
  const keyBytesArr = new Uint8Array(keyLen)
  crypto.getRandomValues(keyBytesArr)
  keyDraft.value = Array.from(keyBytesArr)
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
  mode.value = 'hex'
  flash('已生成随机明文与密钥（仅用于演示，不是安全密钥）')
}

function apply(): void {
  if (!canApply.value) return
  let plainHex = mode.value === 'text' ? textHex.value : plainDraft.value
  if (plainHex.length < 32) plainHex = plainHex.padEnd(32, '0')
  plainHex = plainHex.slice(0, 32)
  emit('apply', plainHex, keyDraft.value)
}
</script>

<style scoped>
.inp {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  height: 100%;
  min-height: 0;
}

.inp__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-2);
}

.inp__title {
  margin: 0;
  font-family: var(--font-ui);
  font-size: var(--fs-label);
  font-weight: 600;
  letter-spacing: var(--ls-label);
  color: var(--ink-3);
}

/* ---- segmented ---- */
.seg {
  display: inline-flex;
  padding: 1px;
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
}

.seg--wide {
  display: flex;
  width: 100%;
}

.seg__btn {
  flex: 1;
  height: 24px;
  padding: 0 var(--sp-2);
  border: 0;
  border-radius: calc(var(--r-control) - 1px);
  background: transparent;
  font-family: var(--font-ui);
  font-size: var(--fs-micro);
  color: var(--ink-3);
  cursor: pointer;
  white-space: nowrap;
}

.seg__btn[aria-checked='true'] {
  background: var(--surface-inset);
  color: var(--ink-1);
}

/* ---- field ---- */
.inp__field {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
  min-width: 0;
}

.inp__label {
  font-family: var(--font-ui);
  font-size: var(--fs-label);
  color: var(--ink-2);
}

.inp__area {
  width: 100%;
  padding: var(--sp-2);
  border: var(--rule-region-w) solid var(--line-default);
  border-radius: var(--r-control);
  background: var(--paper-0);
  color: var(--ink-1);
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  line-height: var(--lh-mono);
  letter-spacing: var(--ls-hex-long);
  resize: none;
  word-break: break-all;
}

.inp__area--text {
  font-family: var(--font-ui);
  letter-spacing: normal;
}

.inp__area:focus-visible {
  outline: var(--focus-ring-w) solid var(--focus-ring-color);
  outline-offset: var(--focus-ring-offset);
}

.inp__count {
  margin: 0;
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  line-height: var(--lh-tight);
  color: var(--ink-3);
}

.inp__count.is-warn {
  color: var(--warn);
}

.inp__count.is-ok {
  color: var(--ink-3);
}

.inp__hint {
  margin: 0;
  font-size: var(--fs-micro);
  line-height: var(--lh-snug);
  color: var(--ink-3);
}

.inp__select {
  height: 26px;
  padding: 0 var(--sp-2);
  border: var(--rule-region-w) solid var(--line-default);
  border-radius: var(--r-control);
  background: var(--paper-0);
  font-family: var(--font-ui);
  font-size: var(--fs-micro);
  color: var(--ink-1);
}

/* ---- actions ---- */
.inp__actions {
  display: flex;
  gap: var(--sp-2);
  margin-top: auto;
  padding-top: var(--sp-2);
}

.inp__go {
  flex: 1;
  height: 32px;
  border: var(--rule-region-w) solid var(--accent);
  border-radius: var(--r-control);
  background: var(--accent);
  font-family: var(--font-ui);
  font-size: var(--fs-label);
  color: var(--paper-0);
  cursor: pointer;
}

.inp__go:hover:not(:disabled) {
  border-color: var(--accent-strong);
  background: var(--accent-strong);
}

.inp__go:disabled {
  border-color: var(--line-default);
  background: transparent;
  color: var(--ink-4);
  cursor: not-allowed;
}

.inp__rand {
  height: 32px;
  padding: 0 var(--sp-3);
  border: var(--rule-region-w) solid var(--line-strong);
  border-radius: var(--r-control);
  background: transparent;
  font-family: var(--font-ui);
  font-size: var(--fs-label);
  color: var(--ink-1);
  cursor: pointer;
}

.inp__rand:hover {
  border-color: var(--ink-2);
}

.inp__notice {
  margin: 0;
  font-family: var(--font-ui);
  font-size: var(--fs-micro);
  line-height: var(--lh-snug);
  color: var(--ink-2);
}
</style>
