<template>
  <article class="step" :class="`step--${tone}`">
    <span class="step__bar" aria-hidden="true" />

    <div class="step__head">
      <span class="step__no" aria-hidden="true">{{ no }}</span>
      <div class="step__names">
        <h3 class="step__name">{{ name }}</h3>
        <span class="step__en">{{ en }}</span>
      </div>
    </div>

    <p class="step__body">{{ body }}</p>

    <RouterLink class="step__link" :to="{ path: '/workbench', query: { step } }">
      在工作台看这一步 →
    </RouterLink>
  </article>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'

defineProps<{
  /** 序号：01–04 */
  no: string
  name: string
  en: string
  body: string
  /** 色相族：只在 CSS 里映射到 token，组件内不出现色值字面量 */
  tone: 'sub' | 'shift' | 'mix' | 'ark'
  /** 跳到工作台的步序（0 起算），对应第 1 轮四步 */
  step: number
}>()
</script>

<style scoped>
.step {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  padding: var(--sp-4);
  padding-top: calc(var(--sp-4) + 3px);
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--card-r);
  /* 极浅色相底：四步各一色，读起来「有色彩」但不刺眼。
     tint 是设计给极浅底用的 token，不落到任何字节格。 */
  background: var(--tone-tint);
  overflow: hidden;
}

/* 顶部 3px 色条：四步唯一的分类色落点之一，不进字节格 */
.step__bar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--tone-ink);
}

.step--sub   { --tone-tint: var(--step-sub-tint);   --tone-ink: var(--step-sub-ink); }
.step--shift { --tone-tint: var(--step-shift-tint); --tone-ink: var(--step-shift-ink); }
.step--mix   { --tone-tint: var(--step-mix-tint);   --tone-ink: var(--step-mix-ink); }
.step--ark   { --tone-tint: var(--step-ark-tint);   --tone-ink: var(--step-ark-ink); }

.step__head {
  display: flex;
  align-items: baseline;
  gap: var(--sp-2);
}

.step__no {
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  line-height: 1;
  letter-spacing: var(--ls-label);
  color: var(--tone-ink);
}

.step__names {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.step__name {
  margin: 0;
  font-family: var(--font-display);
  font-size: var(--fs-h3);
  font-weight: 600;
  line-height: var(--lh-snug);
  color: var(--tone-ink);
}

.step__en {
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  letter-spacing: var(--ls-hex-long);
  color: var(--ink-4);
}

.step__body {
  margin: 0;
  flex: 1;
  font-size: var(--fs-ui);
  line-height: var(--lh-body);
  color: var(--ink-2);
}

.step__link {
  font-size: var(--fs-ui);
  color: var(--tone-ink);
  text-decoration: none;
  border-bottom: var(--rule-region-w) solid transparent;
  align-self: flex-start;
  /* 触屏最小目标：文字下方用 padding 撑到 44px 不必，键盘可达即可 */
  padding-block: var(--sp-1);
}

.step__link:hover {
  border-bottom-color: currentColor;
}

.step__link:focus-visible {
  outline: var(--focus-ring-w) solid var(--focus-ring-color);
  outline-offset: var(--focus-ring-offset);
}
</style>
