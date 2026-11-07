<template>
  <div v-if="failed" class="error-boundary" role="alert" data-error-boundary>
    <h2>这一步出错了，页面还在。</h2>
    <p class="error-boundary__message">{{ message }}</p>
    <button type="button" data-action="error-reset" @click="reset">回到第一步</button>
  </div>
  <slot v-else />
</template>

<script setup lang="ts">
import { onErrorCaptured, ref } from 'vue'

const emit = defineEmits<{
  reset: []
}>()

const failed = ref(false)
const message = ref('')

function reset(): void {
  failed.value = false
  message.value = ''
  emit('reset')
}

onErrorCaptured((error) => {
  failed.value = true
  message.value =
    error instanceof Error && error.message
      ? error.message
      : '组件渲染失败，已保留其余页面。'
  console.error('[BOUNDARY]', error)
  return false
})

defineExpose({ reset })
</script>

<style scoped>
.error-boundary {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--sp-3);
  max-width: 560px;
  margin: 12vh auto 0;
  padding: var(--sp-5);
  border: var(--rule-region-w) solid var(--st-error);
  border-radius: var(--r-control);
  background: var(--paper-1);
}

.error-boundary h2 {
  margin: 0;
  font-size: var(--fs-title);
  color: var(--ink-1);
}

.error-boundary__message {
  margin: 0;
  font-family: var(--font-mono);
  font-size: var(--fs-ui);
  color: var(--ink-2);
  word-break: break-word;
}

.error-boundary button {
  height: 32px;
  padding: 0 var(--sp-4);
  border: var(--rule-region-w) solid var(--accent);
  border-radius: var(--r-control);
  background: transparent;
  font-family: var(--font-ui);
  font-size: var(--fs-label);
  color: var(--accent-strong);
  cursor: pointer;
}
</style>