<template>
  <div class="app" :data-density="density">
    <RouterView />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { RouterView, useRoute } from 'vue-router'

const route = useRoute()
const density = computed(() => (route.name === 'workbench' ? 'compact' : 'roomy'))
</script>