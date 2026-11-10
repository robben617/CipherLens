<template>
  <div class="app" :data-density="density">
    <RouterView v-if="bare" />
    <AppShell v-else>
      <RouterView />
    </AppShell>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import AppShell from './components/layout/AppShell.vue'

const route = useRoute()

// 工作台自带五区（含 A 区顶栏），再套壳会多出一条导航，挤掉舞台高度
const bare = computed(() => route.meta.bare === true)
const density = computed(() => (route.name === 'workbench' ? 'compact' : 'roomy'))
</script>