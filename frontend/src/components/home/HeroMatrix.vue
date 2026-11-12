<template>
  <!-- 装饰性图示：真实信息在 Hero 标题与副标里，对辅助技术隐藏 -->
  <figure class="hm" aria-hidden="true">
    <figcaption class="hm__cap">
      <template v-if="still">最后一步的结果</template>
      <span v-else class="hm__chip" :class="`is-${current.tone}`">{{ current.label }}</span>
    </figcaption>

    <div class="hm__grid" :class="still ? '' : `is-p${phase}`">
      <span
        v-for="(b, i) in cells"
        :key="i"
        class="hm__cell"
        :style="{ '--i': String(i), '--r': String(Math.floor(i / 4)), '--c': String(i % 4) }"
        >{{ b }}</span
      >
    </div>

    <p class="hm__flow">
      <span class="hm__tag">明文</span>
      <span class="hm__in">0011 2233 … eeff</span>
      <span class="hm__tag">密文</span>
      <span class="hm__out">69c4 e0d8 … c55a</span>
    </p>
  </figure>
</template>

<script setup lang="ts">
/**
 * 首页活体演示（F14，在 F02 静态版上加动效）。
 *
 * FIPS-197 附录 C.1 向量：
 *   明文 00 11 22 33 44 55 66 77 88 99 aa bb cc dd ee ff
 *   密钥 00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f
 *   密文 69 c4 e0 d8 6a 7b 04 30 d8 cd b7 80 70 b4 c5 5a
 * （密钥不是全零：全零密钥算出来是 c8a3 31ff …，与下方「69c4 e0d8 … c55a」对不上。）
 *
 * 只跑「一轮的四步」，不跑 40 步：40 步 @1.4s 要 56 秒，用户会走。
 * 中间态全部由引擎现算（buildTrace），不手抄中间结果——抄错了没人发现。
 *
 * 尺寸、栅格、DOM 层级与 F02 静态版完全一致：动效只改颜色和 transform，
 * 因此不会推出重排（CLS 保持 0）。
 */
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { buildTrace } from '../../engine/trace'

const PLAINTEXT = '00112233445566778899aabbccddeeff'
const KEY = '000102030405060708090a0b0c0d0e0f'
/** 每步停留时长；四步 5.6 秒，末尾密文再停 1.4 秒，整循环 7 秒 */
const PHASE_MS = 1400

function toCells(hex: string): readonly string[] {
  return Array.from({ length: 16 }, (_, i) => hex.slice(i * 2, i * 2 + 2))
}

const trace = buildTrace({ plaintext: PLAINTEXT, key: KEY })

const PHASES = [
  { label: '你的明文', tone: 'in', cells: toCells(PLAINTEXT) },
  { label: '字节代换', tone: 'sub', cells: toCells(trace.steps[1]!.state_after.map(hex).join('')) },
  { label: '行移位', tone: 'shift', cells: toCells(trace.steps[2]!.state_after.map(hex).join('')) },
  { label: '列混合', tone: 'mix', cells: toCells(trace.steps[3]!.state_after.map(hex).join('')) },
  { label: '轮密钥加 · 密文', tone: 'ark', cells: toCells(trace.output) },
] as const

function hex(value: number): string {
  return value.toString(16).padStart(2, '0')
}

const LAST = PHASES.length - 1
/** 相位：0 明文 → 1 代换 → 2 移位 → 3 混合 → 4 轮密钥加（末态即密文） */
const phase = ref(LAST)
/** 未启动（静态模式）时只渲染 F02 的终态，与静态版逐像素一致 */
const animate = ref(false)

const still = computed(() => !animate.value)
const current = computed(() => PHASES[animate.value ? phase.value : LAST]!)
const cells = computed(() => current.value.cells)

let timer: number | undefined
let media: MediaQueryList | undefined

function tick(): void {
  phase.value = (phase.value + 1) % PHASES.length
}

function start(): void {
  stop()
  timer = window.setInterval(tick, PHASE_MS)
}

function stop(): void {
  if (timer !== undefined) {
    window.clearInterval(timer)
    timer = undefined
  }
}

/** 标签页切走就停：后台标签页里跑定时器既费电又会积压相位 */
function onVisibility(): void {
  if (document.hidden) stop()
  else if (animate.value) start()
}

function onMediaChange(event: MediaQueryListEvent): void {
  if (event.matches) {
    stop()
    animate.value = false
    phase.value = LAST
  } else {
    animate.value = true
    phase.value = 0
    start()
  }
}

onMounted(() => {
  media = window.matchMedia('(prefers-reduced-motion: reduce)')
  if (media.matches) return // 减少动态效果：保持静态终态，一个定时器都不起

  animate.value = true
  phase.value = 0
  start()
  document.addEventListener('visibilitychange', onVisibility)
  media.addEventListener('change', onMediaChange)
})

onBeforeUnmount(() => {
  stop()
  document.removeEventListener('visibilitychange', onVisibility)
  media?.removeEventListener('change', onMediaChange)
})
</script>

<style scoped>
.hm {
  /* 局部尺寸：随视口微调，不污染 --cell-size（工作台 62px）。
     下限 44px 保证窄屏可读，上限 58px 让 1920 宽屏上矩阵有主角感。 */
  --hm-cell: clamp(44px, 3.1vw, 58px);
  /* 矩阵总宽：4 格 + 3 个格距 + 左右各 1 个内边距。
     **必须显式定宽**——否则下方 mono 说明文字会把整块撑宽，
     连带把 Hero 左栏压窄，标题被挤成两行。 */
  --hm-w: calc(var(--hm-cell) * 4 + var(--cell-gap) * 3 + var(--sp-1) * 2);

  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  width: var(--hm-w);
  margin: 0;
}

.hm__cap {
  font-family: var(--font-ui);
  font-size: var(--fs-label);
  letter-spacing: var(--ls-label);
  color: var(--ink-3);
}

/* 相位名：小圆点 + 文字，颜色跟着四步走。
   必须保持 inline（不能用 inline-flex）：行内块会把行盒撑高 1px，
   静态终态与动效态之间就会差 1px，等于每次加载抖一下。 */
.hm__chip {
  color: var(--tone-ink);
  transition: color 160ms ease-out;
}

.hm__chip::before {
  content: '';
  display: inline-block;
  width: 6px;
  height: 6px;
  margin-right: 6px;
  border-radius: 50%;
  background: currentColor;
  vertical-align: 1px;
}

.hm__chip.is-in {
  --tone-ink: var(--ink-3);
}

.hm__chip.is-sub {
  --tone-ink: var(--step-sub-ink);
}

.hm__chip.is-shift {
  --tone-ink: var(--step-shift-ink);
}

.hm__chip.is-mix {
  --tone-ink: var(--step-mix-ink);
}

.hm__chip.is-ark {
  --tone-ink: var(--step-ark-ink);
}

/* 四角括：只表达范围，不用卡片阴影（沿用既有规范） */
.hm__grid {
  position: relative;
  display: grid;
  grid-template-columns: repeat(4, var(--hm-cell));
  gap: var(--cell-gap);
  padding: var(--sp-1);
  justify-content: start;
}

.hm__grid::before,
.hm__grid::after {
  content: '';
  position: absolute;
  width: var(--rule-scope-arm);
  height: var(--rule-scope-arm);
  pointer-events: none;
}

.hm__grid::before {
  top: calc(var(--rule-scope-inset) * -1);
  left: calc(var(--rule-scope-inset) * -1);
  border-top: var(--rule-scope-w) solid var(--rule-scope-ink);
  border-left: var(--rule-scope-w) solid var(--rule-scope-ink);
}

.hm__grid::after {
  right: calc(var(--rule-scope-inset) * -1);
  bottom: calc(var(--rule-scope-inset) * -1);
  border-right: var(--rule-scope-w) solid var(--rule-scope-ink);
  border-bottom: var(--rule-scope-w) solid var(--rule-scope-ink);
}

.hm__cell {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--hm-cell);
  height: var(--hm-cell);
  border: var(--rule-region-w) solid var(--rule-region-ink);
  border-radius: var(--r-cell);
  background: var(--paper-0);
  color: var(--ink-1);
  font-family: var(--font-mono);
  font-size: var(--fs-byte);
  line-height: var(--lh-mono);
  letter-spacing: var(--ls-hex-cell);
}

/* ============ 动效：只动颜色与 transform，不动尺寸 ============ */

/* ① 字节代换：一格一格亮，顺序与矩阵读取顺序一致 */
.is-p1 .hm__cell {
  animation: hm-sub 900ms ease-out both;
  animation-delay: calc(var(--i) * 22ms);
}

/* ② 行移位：第 1–3 行各自左移一小段再回位（6px，不足以改变栅格） */
.is-p2 .hm__cell {
  animation: hm-shift 900ms ease-out both;
  animation-delay: calc(var(--r) * 80ms);
}

/* ③ 列混合：按列整片亮，强调「一整列一起算」 */
.is-p3 .hm__cell {
  animation: hm-mix 900ms ease-out both;
  animation-delay: calc(var(--c) * 90ms);
}

/* ④ 轮密钥加：整片过一遍最暗的底色 */
.is-p4 .hm__cell {
  animation: hm-ark 900ms ease-out both;
  animation-delay: calc(var(--i) * 12ms);
}

@keyframes hm-sub {
  0% {
    background: var(--step-sub-tint);
    border-color: var(--step-sub-ink);
  }
  100% {
    background: var(--paper-0);
    border-color: var(--rule-region-ink);
  }
}

@keyframes hm-shift {
  0%,
  100% {
    transform: translateX(0);
    border-color: var(--rule-region-ink);
  }
  45% {
    transform: translateX(-6px);
    border-color: var(--step-shift-ink);
  }
}

@keyframes hm-mix {
  0% {
    background: var(--step-mix-tint);
    border-color: var(--step-mix-ink);
  }
  100% {
    background: var(--paper-0);
    border-color: var(--rule-region-ink);
  }
}

@keyframes hm-ark {
  0% {
    background: var(--step-ark-tint);
  }
  100% {
    background: var(--paper-0);
  }
}

/* 系统级「减少动态效果」：一律不跑，静态终态（与 F02 一致） */
@media (prefers-reduced-motion: reduce) {
  .is-p1 .hm__cell,
  .is-p2 .hm__cell,
  .is-p3 .hm__cell,
  .is-p4 .hm__cell {
    animation: none;
  }
}

.hm__flow {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 2px var(--sp-2);
  width: 100%;
  margin: 0;
  font-family: var(--font-mono);
  font-size: var(--fs-label);
  line-height: var(--lh-mono);
  letter-spacing: var(--ls-hex-long);
  color: var(--ink-3);
}

.hm__tag {
  font-family: var(--font-ui);
  font-size: var(--fs-micro);
  letter-spacing: var(--ls-label);
  color: var(--ink-4);
}

.hm__in {
  color: var(--ink-4);
}

.hm__out {
  color: var(--ink-2);
}
</style>
