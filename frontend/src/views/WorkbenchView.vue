<template>
  <WorkbenchLayout :values="values" @next="next" />
</template>

<script setup lang="ts">
import { computed, ref, shallowRef } from 'vue'
import WorkbenchLayout from '../components/layout/WorkbenchLayout.vue'
import { buildTrace } from '../engine/trace'
import { FIPS_197_VECTORS } from '../engine/vectors'

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
</script>