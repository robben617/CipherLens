<template>
  <div class="shell">
    <ShellBar />

    <div class="shell__main">
      <slot />
    </div>

    <AiFab v-if="!ai.panelOpen" @open="openAi" />
    <GlobalAiPanel />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ShellBar from './ShellBar.vue'
import AiFab from '../shared/AiFab.vue'
import GlobalAiPanel from './GlobalAiPanel.vue'
import { useAiStore } from '../../stores/ai'
import type { PageKey } from '../../utils/ai-context'

const route = useRoute()
const router = useRouter()
const ai = useAiStore()

const pageKey = computed<PageKey>(() => {
  if (route.name === 'sbox') return 'sbox'
  if (route.name === 'avalanche') return 'avalanche'
  return 'home'
})

function openAi(): void {
  void router.isReady().then(() => ai.openPanel(pageKey.value))
}

// 路由变化时 AI 会话按页保留，但当前流中止、面板关闭
watch(
  () => route.fullPath,
  () => {
    ai.switchPage(pageKey.value)
  },
)

onMounted(() => {
  ai.switchPage(pageKey.value)
})
</script>

<style scoped>
.shell {
  min-height: 100vh;
  min-height: 100dvh;
  background: var(--paper-0);
}

.shell__main {
  min-height: calc(100dvh - var(--nav-h));
}
</style>