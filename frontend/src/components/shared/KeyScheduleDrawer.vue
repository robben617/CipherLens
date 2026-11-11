<template>
  <Teleport to="body">
    <div v-if="open" class="ks" data-key-drawer @keydown="onKeydown">
      <div class="ks__scrim" data-action="ks-scrim" @click="emit('close')"></div>

      <aside
        ref="panelEl"
        class="ks__panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="ks-title"
        tabindex="-1"
      >
        <header class="ks__head">
          <div class="ks__head-row">
            <h2 id="ks-title" class="ks__title">密钥扩展</h2>
            <button
              ref="closeEl"
              type="button"
              class="ks__close"
              aria-label="关闭密钥扩展"
              data-action="ks-close"
              @click="emit('close')"
            >
              ×
            </button>
          </div>

          <p class="ks__meta" data-ks-meta>
            AES-{{ keyBits }} · {{ groups.length }} 组轮密钥 · {{ words.length }} 个字
          </p>

          <p class="ks__formula">
            w[i] = w[i−{{ nk }}] ⊕ g(w[i−1])
            <span class="ks__formula-sub">g = SubWord(RotWord(w)) ⊕ Rcon</span>
          </p>

          <p class="ks__lede">
            轮密钥不是另一把钥匙，是把同一把钥匙按规则抻长：每 4 个字一组，
            第 i 个字由 <b>w[i−{{ nk }}]</b> 和 <b>w[i−1]</b> 两个已知字推出来。
            只有 i 是 {{ nk }} 的倍数时才先过 g 函数——把 w[i−1] 转一下、查 S 盒、再异或一个轮常数。
            这么绕的目的只有一个：让每轮用的密钥都不一样，否则「轮密钥加」等于没加。
          </p>
        </header>

        <div ref="bodyEl" class="ks__body">
          <section
            v-for="group in groups"
            :key="group.round"
            class="ks__group"
            :class="{ 'is-active': group.round === activeRound }"
            :data-round="group.round"
          >
            <header class="ks__group-head">
              <span class="ks__rk">RK{{ group.round }}</span>
              <span class="ks__rk-name">{{ group.label }}</span>
              <span v-if="group.round === activeRound" class="ks__now">当前</span>
              <button
                type="button"
                class="ks__jump"
                data-action="ks-jump"
                :title="`跳到第 ${group.step} 步（第 ${group.round} 轮轮密钥加）`"
                @click="emit('goto-round', group.round)"
              >
                第 {{ group.step }} 步 →
              </button>
            </header>

            <template v-for="word in group.words" :key="word.index">
              <button
                type="button"
                class="ks__word"
                :class="{
                  'is-g': word.rule === 'g' || word.rule === 'subword',
                  'is-open': expanded === word.index,
                  'is-here': word.index === activeWordIndex,
                }"
                :aria-expanded="expanded === word.index"
                :aria-controls="`ks-deriv-${word.index}`"
                :data-word="word.index"
                @click="toggle(word.index)"
              >
                <span class="ks__i">w{{ word.index }}</span>
                <span class="ks__bytes">
                  <span v-for="(byte, k) in word.word" :key="k" class="ks__byte">
                    {{ hex(byte!) }}
                  </span>
                </span>
                <span class="ks__rule">{{ ruleLabel(word) }}</span>
              </button>

              <div
                v-if="expanded === word.index"
                :id="`ks-deriv-${word.index}`"
                class="ks__deriv"
                data-ks-deriv
              >
                <p class="ks__deriv-head">{{ derivHead(word) }}</p>
                <ol class="ks__deriv-list">
                  <li v-for="(row, k) in derivRows(word)" :key="k" class="ks__deriv-row">
                    <span class="ks__deriv-label">{{ row.label }}</span>
                    <span class="ks__deriv-from">
                      <template v-if="row.from">
                        <span v-for="(byte, j) in row.from" :key="j" class="ks__byte">
                          {{ hex(byte!) }}
                        </span>
                      </template>
                      <span v-else class="ks__deriv-dash">—</span>
                    </span>
                    <span class="ks__deriv-arrow" aria-hidden="true">→</span>
                    <span class="ks__deriv-to">
                      <span v-for="(byte, j) in row.to" :key="j" class="ks__byte is-out">
                        {{ hex(byte!) }}
                      </span>
                    </span>
                  </li>
                </ol>
                <p v-if="word.rule === 'g'" class="ks__deriv-note">
                  Rcon[{{ word.rconIndex! + 1 }}] = {{ hex(word.rcon![0]!) }} 00 00 00。
                  规范从 Rcon[1] 数起（代码里数组下标从 0 开始）；每轮翻倍，
                  越过 0x80 时先左移一位再异或 0x11B。
                </p>
              </div>
            </template>
          </section>
        </div>

        <footer class="ks__foot">
          点任意一行展开它的推导；点组标题的步号直接跳到那一轮的轮密钥加。
        </footer>
      </aside>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { keyWordTrace, nkFromSchedule, type KeyWordTrace } from '../../engine/keyschedule'

const props = defineProps<{
  open: boolean
  /** trace.key_schedule：44 / 52 / 60 个字，每字 4 字节 */
  words: readonly (readonly number[])[]
  keyBits: number
  /** 当前步属于第几轮的轮密钥加；不在该步时为 null */
  activeRound: number | null
  /** 当前步正在用的字下标（-1 表示不在轮密钥加步） */
  activeWordIndex: number
  /** 每轮轮密钥加对应的 UI 步号，下标 = 轮次 */
  roundSteps: readonly number[]
}>()

const emit = defineEmits<{
  close: []
  'goto-round': [round: number]
}>()

const panelEl = ref<HTMLElement | null>(null)
const bodyEl = ref<HTMLElement | null>(null)
const closeEl = ref<HTMLButtonElement | null>(null)
const expanded = ref<number | null>(null)

const hex = (value: number): string => (value ?? 0).toString(16).toUpperCase().padStart(2, '0')

const nk = computed(() => nkFromSchedule(props.words))

interface Group {
  round: number
  label: string
  step: number
  words: readonly KeyWordTrace[]
}

const groups = computed<Group[]>(() => {
  const out: Group[] = []
  for (let i = 0; i < props.words.length; i += 4) {
    const round = i / 4
    const words: KeyWordTrace[] = []
    for (let k = 0; k < 4 && i + k < props.words.length; k++) {
      words.push(keyWordTrace(props.words, i + k))
    }
    out.push({
      round,
      label: round === 0 ? '初始轮密钥加（明文 ⊕ 这里）' : `第 ${round} 轮`,
      step: props.roundSteps[round] ?? 0,
      words,
    })
  }
  return out
})

function ruleLabel(word: KeyWordTrace): string {
  switch (word.rule) {
    case 'original':
      return '原始密钥'
    case 'g':
      return `g(w${word.index - 1}) ⊕ w${word.index - nk.value}`
    case 'subword':
      return `SubWord(w${word.index - 1}) ⊕ w${word.index - nk.value}`
    default:
      return `w${word.index - nk.value} ⊕ w${word.index - 1}`
  }
}

function derivHead(word: KeyWordTrace): string {
  if (word.rule === 'original') return `w${word.index} 直接来自输入密钥的第 ${word.index + 1} 个字`
  if (word.rule === 'g') return `w${word.index} 要过 g 函数：转、代换、加轮常数、再异或`
  if (word.rule === 'subword') return `w${word.index} 只做字节代换（AES-256 每 8 个字一次）`
  return `w${word.index} 只有异或：两个已知字逐字节相加`
}

interface DerivRow {
  label: string
  from: readonly number[] | null
  to: readonly number[]
}

const xor4 = (a: readonly number[], b: readonly number[]): number[] => [
  a[0]! ^ b[0]!,
  a[1]! ^ b[1]!,
  a[2]! ^ b[2]!,
  a[3]! ^ b[3]!,
]

/** 每一步的 from/to 串成链条：上一行的「结果」就是下一行的「输入」 */
function derivRows(word: KeyWordTrace): DerivRow[] {
  if (word.rule === 'original') return []

  if (word.rule === 'g') {
    const afterRcon = xor4(word.substituted!, word.rcon!)
    return [
      { label: 'RotWord', from: word.previousWord!, to: word.rotated! },
      { label: 'SubWord', from: word.rotated!, to: word.substituted! },
      { label: `⊕ Rcon[${word.rconIndex! + 1}]`, from: word.substituted!, to: afterRcon },
      { label: `⊕ w${word.index - nk.value}`, from: word.baseWord!, to: word.word },
    ]
  }

  if (word.rule === 'subword') {
    return [
      { label: 'SubWord', from: word.previousWord!, to: word.substituted! },
      { label: `⊕ w${word.index - nk.value}`, from: word.baseWord!, to: word.word },
    ]
  }

  // 单条异或：把两个操作数都写进标签，读者不用回头数 w 的下标
  return [
    {
      label: `w${word.index - nk.value} ⊕ w${word.index - 1}`,
      from: word.baseWord!,
      to: word.word,
    },
  ]
}

function toggle(index: number): void {
  expanded.value = expanded.value === index ? null : index
}

function focusables(): HTMLElement[] {
  if (!panelEl.value) return []
  return Array.from(
    panelEl.value.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
    ),
  ).filter((element) => !element.hasAttribute('disabled'))
}

function onKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape') {
    event.preventDefault()
    event.stopPropagation()
    emit('close')
    return
  }
  if (event.key !== 'Tab') return

  const items = focusables()
  if (items.length === 0) return
  const current = document.activeElement as HTMLElement | null
  const index = current ? items.indexOf(current) : -1

  if (event.shiftKey) {
    if (index <= 0) {
      event.preventDefault()
      items[items.length - 1]?.focus()
    }
  } else if (index === items.length - 1 || index === -1) {
    event.preventDefault()
    items[0]?.focus()
  }
}

/** 打开时滚到当前轮那一组：44 行全渲染，一进来就该停在正在用的那组 */
function scrollToActive(): void {
  const round = props.activeRound
  const body = bodyEl.value
  if (!body || round === null) return
  const target = body.querySelector<HTMLElement>(`[data-round="${round}"]`)
  if (!target) return
  // offsetTop 的参照系不一定是滚动容器（祖先没有定位元素时会一路找到 body），
  // 用两个 rect 相减才是稳的。
  const delta = target.getBoundingClientRect().top - body.getBoundingClientRect().top
  body.scrollTop = Math.max(0, body.scrollTop + delta)
}

watch(
  () => props.open,
  async (open) => {
    if (!open) {
      expanded.value = null
      return
    }
    await nextTick()
    closeEl.value?.focus({ preventScroll: true })
    // 默认展开当前正在用的那个字，直接看到「它是怎么来的」
    expanded.value = props.activeWordIndex >= 0 ? props.activeWordIndex : null
    await nextTick()
    scrollToActive()
  },
)

onMounted(() => {
  if (!props.open) return
  closeEl.value?.focus({ preventScroll: true })
  scrollToActive()
})
</script>

<style scoped>
.ks {
  position: fixed;
  inset: 0;
  z-index: 34;
}

.ks__scrim {
  position: absolute;
  inset: 0;
  background: var(--scrim-drawer);
  animation: ks-fade var(--d-2) var(--e-out-quart);
}

.ks__panel {
  position: absolute;
  /* 让开工作台 A 区顶栏：按钮还在，抽屉不能盖住它 */
  top: var(--topbar-h);
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  width: min(520px, 100vw);
  border-left: var(--rule-region-w) solid var(--line-hairline);
  background: var(--paper-0);
  box-shadow: -8px 0 24px rgb(0 0 0 / 0.08);
  animation: ks-slide var(--d-3) var(--e-out-quart);
}

@keyframes ks-slide {
  from {
    transform: translateX(16px);
    opacity: 0.4;
  }
}

@keyframes ks-fade {
  from {
    opacity: 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .ks__panel,
  .ks__scrim {
    animation: none;
  }
}

.ks__head {
  flex: none;
  padding: var(--sp-4) var(--sp-4) var(--sp-3);
  border-bottom: var(--rule-region-w) solid var(--line-hairline);
}

.ks__head-row {
  display: flex;
  align-items: baseline;
  gap: var(--sp-2);
}

.ks__title {
  flex: 1;
  min-width: 0;
  font-family: var(--font-display);
  font-size: var(--fs-h3);
  font-weight: 600;
  color: var(--ink-1);
}

.ks__close {
  width: 28px;
  height: 28px;
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  background: transparent;
  font-size: var(--fs-body);
  line-height: 1;
  color: var(--ink-2);
  cursor: pointer;
}

.ks__close:hover {
  border-color: var(--line-default);
  color: var(--ink-1);
}

.ks__meta {
  margin-top: var(--sp-1);
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  letter-spacing: var(--ls-label);
  color: var(--ink-3);
}

.ks__formula {
  margin-top: var(--sp-3);
  padding: var(--sp-2) var(--sp-3);
  border-radius: var(--r-control);
  background: var(--surface-inset);
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  line-height: 1.7;
  color: var(--ink-1);
}

.ks__formula-sub {
  display: block;
  color: var(--ink-3);
}

.ks__lede {
  margin-top: var(--sp-3);
  font-size: var(--fs-label);
  line-height: var(--lh-snug);
  color: var(--ink-2);
}

.ks__lede b {
  font-family: var(--font-mono);
  font-weight: 500;
  color: var(--accent-strong);
}

.ks__body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding: 0 var(--sp-4) var(--sp-4);
}

.ks__group {
  border-bottom: var(--rule-region-w) solid var(--line-hairline);
  padding-bottom: var(--sp-2);
}

.ks__group.is-active {
  background: color-mix(in oklch, var(--accent-soft) 42%, transparent);
}

.ks__group-head {
  position: sticky;
  top: 0;
  z-index: 1;
  display: flex;
  align-items: baseline;
  gap: var(--sp-2);
  padding: var(--sp-2) 0;
  background: var(--paper-0);
  border-bottom: var(--rule-region-w) solid var(--line-hairline);
}

.ks__group.is-active .ks__group-head {
  background: var(--accent-soft);
}

.ks__rk {
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  font-weight: 600;
  letter-spacing: var(--ls-label);
  color: var(--ink-1);
}

.ks__rk-name {
  flex: 1;
  min-width: 0;
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

.ks__now {
  padding: 0 4px;
  border-radius: 2px;
  background: var(--accent);
  font-size: var(--fs-micro);
  line-height: 1.5;
  color: var(--paper-0);
}

.ks__jump {
  flex: none;
  padding: 0;
  border: 0;
  background: transparent;
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--accent-strong);
  cursor: pointer;
}

.ks__jump:hover {
  text-decoration: underline;
}

.ks__word {
  display: grid;
  grid-template-columns: 40px 112px minmax(0, 1fr);
  align-items: center;
  gap: var(--sp-2);
  width: 100%;
  padding: 3px var(--sp-1);
  border: 0;
  border-left: 2px solid transparent;
  border-radius: 0 var(--r-control) var(--r-control) 0;
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.ks__word:hover {
  background: var(--surface-inset);
}

.ks__word.is-g {
  border-left-color: var(--accent);
}

.ks__word.is-open {
  background: var(--surface-inset);
}

.ks__word.is-here {
  background: var(--accent-soft);
}

.ks__i {
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

.ks__bytes {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 2px;
}

.ks__byte {
  font-family: var(--font-mono);
  font-size: var(--fs-sbox);
  letter-spacing: var(--ls-hex-cell);
  color: var(--ink-1);
}

.ks__byte.is-out {
  color: var(--accent-strong);
}

.ks__rule {
  min-width: 0;
  overflow: hidden;
  font-size: var(--fs-micro);
  color: var(--ink-3);
  white-space: nowrap;
  text-overflow: ellipsis;
}

.ks__deriv {
  margin: 0 0 var(--sp-2) 42px;
  padding: var(--sp-2) var(--sp-3);
  border-left: 2px solid var(--line-default);
  border-radius: 0 var(--r-control) var(--r-control) 0;
  background: var(--surface-raised);
}

.ks__deriv-head {
  margin-bottom: var(--sp-2);
  font-size: var(--fs-micro);
  color: var(--ink-2);
}

.ks__deriv-list {
  display: flex;
  flex-direction: column;
  gap: 3px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.ks__deriv-row {
  display: grid;
  grid-template-columns: 86px 92px 12px 92px;
  align-items: center;
  gap: var(--sp-1);
}

.ks__deriv-label {
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-3);
  white-space: nowrap;
}

.ks__deriv-from,
.ks__deriv-to {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 2px;
}

.ks__deriv-arrow {
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

.ks__deriv-dash {
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-4);
}

.ks__deriv-note {
  margin-top: var(--sp-2);
  font-size: var(--fs-micro);
  line-height: var(--lh-snug);
  color: var(--ink-3);
}

.ks__foot {
  flex: none;
  padding: var(--sp-2) var(--sp-4);
  border-top: var(--rule-region-w) solid var(--line-hairline);
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

@media (max-width: 33rem) {
  .ks__word {
    grid-template-columns: 34px 104px minmax(0, 1fr);
  }

  .ks__deriv {
    margin-left: 0;
  }

  .ks__deriv-row {
    grid-template-columns: 78px 84px 12px 84px;
  }
}
</style>
