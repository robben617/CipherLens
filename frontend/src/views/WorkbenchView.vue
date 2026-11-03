<template>
  <StatesDebugView v-if="isStatesDebug" />
  <WorkbenchLayout v-else :values="values" @next="next" />
</template>

<script setup lang="ts">
import { computed, ref, shallowRef } from 'vue'
import { useRoute } from 'vue-router'
import WorkbenchLayout from '../components/layout/WorkbenchLayout.vue'
import { useHotkeys } from '../composables/useHotkeys'
import { buildTrace } from '../engine/trace'
import { FIPS_197_VECTORS } from '../engine/vectors'
import StatesDebugView from './StatesDebugView.vue'

const route = useRoute()
const isStatesDebug = computed(() => route.query.debug === 'states')

const vector = FIPS_197_VECTORS[0]!
const trace = shallowRef(
  buildTrace({ plaintext: vector.plaintext_hex, key: vector.key_hex }),
)
const stepIndex = ref(0)

const values = computed(() => {
  const steps = trace.value.steps
  if (stepIndex.value === 0) {
    return Uint8Array.from(steps[0]!.state_before)
  }
  const step = steps[stepIndex.value - 1]
  return Uint8Array.from(
    step ? step.state_after : steps[steps.length - 1]!.state_after,
  )
})

function next(): void {
  stepIndex.value = Math.min(stepIndex.value + 1, trace.value.steps.length)
}

function prev(): void {
  stepIndex.value = Math.max(stepIndex.value - 1, 0)
}

function first(): void {
  stepIndex.value = 0
}

function last(): void {
  stepIndex.value = trace.value.steps.length
}

function togglePlayPlaceholder(): void {
  // F13 接入播放/暂停；本轮只保留键盘入口。
}

useHotkeys({
  onPlayPause: togglePlayPlaceholder,
  onPrev: prev,
  onNext: next,
  onFirst: first,
  onLast: last,
})
</script>