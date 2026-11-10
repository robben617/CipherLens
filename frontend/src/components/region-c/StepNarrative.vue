<template>
  <div class="nar" :class="{ 'is-open': open || Boolean(activeTerm) }">
    <div class="nar__head">
      <span class="nar__step">第 {{ stepIndex }} 步 / {{ total }}</span>
      <span v-if="roundNo > 0" class="nar__chip">第 {{ roundNo }} 轮</span>
      <span v-if="opName" class="nar__chip nar__chip--op">{{ opName }}</span>
      <span class="nar__impact">{{ impactText }}</span>
    </div>

    <p class="nar__plain">{{ copy.plain }}</p>

    <div class="nar__foot">
      <button type="button" class="nar__why" :aria-expanded="open" @click="toggleWhy">
        为什么
        <span class="nar__caret" :class="{ 'is-open': open }" aria-hidden="true">▾</span>
      </button>
      <ul v-if="terms.length" class="nar__terms">
        <li v-for="term in terms" :key="term.key">
          <button
            type="button"
            class="nar__term"
            :class="{ 'is-on': active === term.key }"
            :aria-expanded="active === term.key"
            @click="toggleTerm(term.key)"
          >
            {{ term.name }}
          </button>
        </li>
      </ul>
    </div>

    <div v-if="open" class="nar__body">
      <p><span class="nar__tag">类比</span>{{ copy.analogy }}</p>
      <p><span class="nar__tag">规则</span>{{ copy.math }}</p>
      <p class="nar__row--warn">
        <span class="nar__tag nar__tag--warn">常见误解</span>{{ copy.pitfall }}
      </p>
    </div>

    <GlossaryCard
      v-if="activeTerm"
      class="nar__card"
      :term="activeTerm"
      @close="active = ''"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import GlossaryCard from './GlossaryCard.vue'
import { copyFor } from '../../data/step-copy'
import { GLOSSARY_MAP, termsOf } from '../../data/glossary'

const props = defineProps<{
  stepIndex: number
  total: number
  roundNo: number
  op: string
  changedCount: number
}>()

/** 只在本次会话的第一屏示范一次术语卡，之后交给用户主动点 */
let demoed = false

const open = ref(false)
const active = ref('')

const copy = computed(() => copyFor(props.stepIndex, props.op, props.total))
const terms = computed(() => termsOf(copy.value.terms))
const activeTerm = computed(() => (active.value ? GLOSSARY_MAP[active.value] : undefined))

/** op 的中文名直接从术语表取，避免第二份映射 */
const opName = computed(() => GLOSSARY_MAP[props.op]?.name ?? '')

const impactText = computed(() => {
  if (props.stepIndex <= 0) return '初始状态'
  if (props.changedCount <= 0) return '本步无字节变化'
  return `影响 ${props.changedCount} 格`
})

function toggleWhy(): void {
  open.value = !open.value
  if (open.value) active.value = ''
}

function toggleTerm(key: string): void {
  const next = active.value === key ? '' : key
  active.value = next
  // 「为什么」与术语卡讲的是同一层意思，同时展开会重复两遍
  if (next) open.value = false
}

// 换步时：收起「为什么」，并只在第一次示范一张术语卡
watch(
  () => [props.stepIndex, props.op] as const,
  () => {
    open.value = false
    const first = terms.value[0]
    if (!demoed && first) {
      demoed = true
      active.value = first.key
    } else {
      active.value = ''
    }
  },
  { immediate: true },
)
</script>

<style scoped>
/* 绝对定位：不参与 C 区布局，矩阵中心位置不因解说条出现而位移 */
.nar {
  position: absolute;
  top: var(--sp-3);
  left: 50%;
  z-index: 3;
  width: min(620px, calc(100% - var(--sp-6)));
  padding: var(--sp-2) var(--sp-3) var(--sp-2);
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-float);
  background: var(--paper-0);
  box-shadow: var(--shadow-1);
  transform: translateX(-50%);
  /* 矮屏（如 1280×800）时不让解说条溢出 C 区压住矩阵，超出部分自身滚动 */
  max-height: calc(100% - var(--sp-6));
  overflow-y: auto;
}

.nar.is-open {
  z-index: 4;
  box-shadow: var(--shadow-float);
}

.nar__head {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  height: 20px;
  margin-bottom: var(--sp-1);
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  letter-spacing: var(--ls-hex-long);
  color: var(--ink-3);
}

.nar__step {
  color: var(--ink-2);
  font-variant-numeric: tabular-nums;
}

.nar__chip {
  padding: 1px var(--sp-2);
  border-radius: var(--r-cell);
  background: var(--paper-1);
  color: var(--ink-2);
  letter-spacing: 0;
}

.nar__chip--op {
  background: var(--step-sub-tint);
  color: var(--step-sub-ink);
}

.nar__impact {
  margin-left: auto;
  color: var(--ink-3);
}

.nar__plain {
  margin: 0 0 var(--sp-2);
  overflow: hidden;
  font-size: var(--fs-ui);
  line-height: 1.6;
  color: var(--ink-1);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.nar__foot {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  height: 20px;
}

.nar__why {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 0;
  border: 0;
  background: none;
  font-size: var(--fs-micro);
  letter-spacing: 0.02em;
  color: var(--ink-2);
  cursor: pointer;
}

.nar__why:hover {
  color: var(--ink-1);
  text-decoration: underline;
  text-underline-offset: 2px;
}

.nar__caret {
  display: inline-block;
  transition: transform 120ms ease;
}

.nar__caret.is-open {
  transform: rotate(180deg);
}

.nar__terms {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-2);
  margin: 0;
  padding: 0;
  list-style: none;
}

.nar__term {
  padding: 0;
  border: 0;
  border-bottom: 1px dashed var(--line-strong);
  background: none;
  font-size: var(--fs-micro);
  color: var(--ink-2);
  cursor: pointer;
}

.nar__term:hover,
.nar__term.is-on {
  color: var(--ink-1);
  border-bottom-color: var(--ink-1);
}

.nar__why:focus-visible,
.nar__term:focus-visible {
  outline: 2px solid var(--rule-scope-ink);
  outline-offset: 2px;
}

.nar__body {
  margin-top: var(--sp-2);
  padding-top: var(--sp-2);
  border-top: var(--rule-region-w) solid var(--line-hairline);
}

.nar__body p {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: var(--sp-2);
  margin: 0 0 var(--sp-1);
  font-size: var(--fs-micro);
  line-height: 1.7;
  color: var(--ink-2);
}

.nar__tag {
  color: var(--ink-3);
  white-space: nowrap;
}

.nar__row--warn {
  padding-left: var(--sp-2);
  border-left: 2px solid var(--warn);
  color: var(--ink-1);
}

.nar__tag--warn {
  color: var(--ink-1);
}

.nar__card {
  margin-top: var(--sp-2);
}

/* 矮屏（1280×800 等）C 区上下余量只有约 150px，
   展开态必须再压一档，否则会压住矩阵上边框 */
@media (max-height: 900px) {
  .nar__body {
    margin-top: var(--sp-1);
    padding-top: var(--sp-1);
  }

  .nar__body p {
    margin-bottom: 2px;
    line-height: 1.5;
  }

  .gc {
    padding: var(--sp-2);
  }

  .gc__list {
    gap: 2px var(--sp-2);
  }

  .gc__list dd {
    line-height: 1.5;
  }
}
</style>
