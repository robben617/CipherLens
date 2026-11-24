<template>
  <div class="msb" :class="{ 'msb--on': modelStore.configured }" data-model-status>
    <span class="msb__dot" aria-hidden="true"></span>
    <span class="msb__text" data-model-status-text>
      {{ modelStore.configured ? `模型：${modelStore.label}` : '当前使用本地讲解' }}
    </span>
    <button type="button" class="msb__btn" data-model-status-btn @click="modelStore.openDialog()">
      {{ modelStore.configured ? '模型设置' : '添加模型' }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { useModelConfigStore } from '../../stores/model-config'

const modelStore = useModelConfigStore()
</script>

<style scoped>
.msb {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  min-width: 0;
  padding: var(--sp-2) 0;
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

.msb__dot {
  flex: none;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--ink-3);
}

.msb--on .msb__dot {
  background: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-ring);
}

.msb__text {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.msb__btn {
  flex: none;
  height: 26px;
  margin-left: auto;
  padding: 0 10px;
  border: var(--rule-region-w) solid var(--accent);
  border-radius: var(--r-control);
  background: transparent;
  font-size: var(--fs-micro);
  color: var(--accent-strong);
  cursor: pointer;
  white-space: nowrap;
}

.msb__btn:hover {
  border-color: var(--accent-strong);
}
</style>