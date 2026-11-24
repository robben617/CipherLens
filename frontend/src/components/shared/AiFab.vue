<template>
  <button
    class="ai-fab"
    type="button"
    aria-label="打开 AI 答疑小助手"
    title="打开 AI 答疑小助手"
    @click="$emit('open')"
  >
    <span class="ai-fab__mark">AI</span>
  </button>
</template>

<script setup lang="ts">
defineEmits<{ open: [] }>()
</script>

<style scoped>
.ai-fab {
  position: fixed;
  top: calc(var(--nav-h) + 12px);
  right: var(--fab-offset);
  bottom: auto;
  z-index: 40;
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border: var(--rule-region-w) solid var(--line-strong);
  border-radius: var(--r-control);
  background: var(--paper-0);
  box-shadow: 0 2px 12px rgb(0 0 0 / 0.16);
  color: var(--ink-1);
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 0.06em;
  cursor: pointer;
  transition:
    border-color var(--d-2) var(--e-out-quart),
    color var(--d-2) var(--e-out-quart),
    transform var(--d-2) var(--e-out-quart);
}

.ai-fab:hover {
  border-color: var(--accent);
  color: var(--accent-strong);
  transform: translateY(-1px);
}

.ai-fab__mark {
  line-height: 1;
}

@media (max-width: 720px) {
  .ai-fab {
    top: calc(var(--nav-h) + 12px);
    right: var(--fab-offset-sm);
  }
}
</style>