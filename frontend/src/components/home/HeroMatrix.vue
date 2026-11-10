<template>
  <!-- 装饰性图示：真实信息在 Hero 标题与副标里，对辅助技术隐藏 -->
  <figure class="hm" aria-hidden="true">
    <figcaption class="hm__cap">最后一步的结果</figcaption>

    <div class="hm__grid">
      <span v-for="(b, i) in CIPHER" :key="i" class="hm__cell">{{ b }}</span>
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
 * 首页静态矩阵（F02 交付）。
 *
 * FIPS-197 附录 C.1 向量：
 *   明文 00 11 22 33 44 55 66 77 88 99 aa bb cc dd ee ff
 *   密钥 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
 *   密文 69 c4 e0 d8 6a 7b 04 30 d8 cd b7 80 70 b4 c5 5a
 *
 * **本轮不起定时器、不写 keyframes**——动画属 F14，届时在同一 DOM 上加，
 * 尺寸与栅格一律不动（这是把动画放到最后的原因）。
 */
const CIPHER = [
  '69', 'c4', 'e0', 'd8',
  '6a', '7b', '04', '30',
  'd8', 'cd', 'b7', '80',
  '70', 'b4', 'c5', '5a',
] as const
</script>

<style scoped>
.hm {
  /* 局部尺寸：随视口微调，不污染 --cell-size（工作台 62px）。
     下限 44px 保证窄屏可读，上限 58px 让 1920 宽屏上矩阵有主角感。
     F14 加动画时尺寸公式不变，因此不会返工。 */
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
