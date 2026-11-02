<template>
  <main class="workbench" data-density="compact">
    <section data-region="a" class="workbench__region">
      <p class="workbench__label">A · 上下文条</p>
    </section>
    <section data-region="b" class="workbench__region">
      <p class="workbench__label">B · 输入区</p>
    </section>
    <section data-region="c" class="workbench__region">
      <p class="workbench__label">C · 舞台区</p>
    </section>
    <section data-region="d" class="workbench__region">
      <p class="workbench__label">D · 步进与时间轴</p>
    </section>
    <section data-region="e" class="workbench__region">
      <p class="workbench__label">E · AI 辅导栏</p>
    </section>
  </main>
</template>

<script setup lang="ts"></script>

<style scoped>
.workbench {
  display: grid;
  grid-template-columns: var(--input-col) minmax(0, 1fr) var(--ai-col);
  grid-template-rows: var(--topbar-h) minmax(0, 1fr) var(--transport-h);
  grid-template-areas:
    "a a a"
    "b c e"
    "d d d";
  height: 100vh;
  height: 100dvh;
}

.workbench__region {
  min-width: 0;
  padding: var(--sp-3);
}

.workbench__label {
  font-family: var(--font-mono);
  font-size: var(--fs-label);
  letter-spacing: var(--ls-label);
  color: var(--ink-3);
}

[data-region="a"] {
  grid-area: a;
  min-height: 0;
  border-bottom: var(--rule-region-w) solid var(--line-hairline);
}

[data-region="b"] {
  grid-area: b;
  overflow: hidden;
  border-right: var(--rule-region-w) solid var(--line-hairline);
}

[data-region="c"] {
  grid-area: c;
  min-height: 0;
}

[data-region="d"] {
  grid-area: d;
  min-height: 0;
  border-top: var(--rule-region-w) solid var(--line-hairline);
}

[data-region="e"] {
  grid-area: e;
  overflow: hidden;
  border-left: var(--rule-region-w) solid var(--line-hairline);
}
</style>