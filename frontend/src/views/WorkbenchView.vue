<template>
  <StatesDebugView v-if="isStatesDebug" />
  <WorkbenchLayout
    v-else
    :values="values"
    :op="currentOp"
    :round-key="currentRoundKey"
    :changed="currentChanged"
    :steps="steps"
    :step-index="stepIndex"
    :step-label="currentStepLabel"
    :step-before="currentStepBefore"
    :step-after="currentStepAfter"
    :trace-id="traceId"
    :markers="markers"
    @commit="commitStep"
  />
</template>

<script setup lang="ts">
import { computed, onMounted, ref, shallowRef, watch } from 'vue'
import { useRoute } from 'vue-router'
import WorkbenchLayout from '../components/layout/WorkbenchLayout.vue'
import { useHotkeys } from '../composables/useHotkeys'
import { buildTrace } from '../engine/trace'
import { FIPS_197_VECTORS } from '../engine/vectors'
import { usePlaybackStore } from '../stores/playback'
import StatesDebugView from './StatesDebugView.vue'

const route = useRoute()
const isStatesDebug = computed(() => route.query.debug === 'states')
const playback = usePlaybackStore()

const vector = FIPS_197_VECTORS[route.query.vector === 'c3' ? 2 : 0]!
const trace = shallowRef(
  buildTrace({ plaintext: vector.plaintext_hex, key: vector.key_hex }),
)
const stepIndex = computed(() => playback.currentStep)
const steps = computed(() => trace.value.steps)
const traceId = ref(trace.value.trace_id)

onMounted(async () => {
  try {
    const response = await fetch('/api/aes/trace', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        plaintext_hex: vector.plaintext_hex,
        key_hex: vector.key_hex,
        key_bits: vector.key_bits,
        direction: 'encrypt',
      }),
    })
    if (!response.ok) return
    const data = (await response.json()) as { trace_id?: string }
    if (data.trace_id) traceId.value = data.trace_id
  } catch {
    // 后端离线时保留本地 trace_id；提问会在 TutorPanel 内显示错误态。
  }
})

watch(
  () => trace.value.steps.length,
  (count) => playback.setStepCount(count),
  { immediate: true },
)

const markers: Record<number, { diag: number; ask: number }> = {
  3: { diag: 1, ask: 0 },
  13: { diag: 1, ask: 2 },
  27: { diag: 0, ask: 1 },
}

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

const currentOp = computed(() => {
  if (stepIndex.value === 0) return 'none'
  return trace.value.steps[stepIndex.value - 1]?.op ?? 'none'
})

const currentChanged = computed(() => {
  if (stepIndex.value === 0) return []
  return [...(trace.value.steps[stepIndex.value - 1]?.changed ?? [])]
})

const currentStepLabel = computed(() => {
  if (stepIndex.value === 0) return '初始状态'
  return trace.value.steps[stepIndex.value - 1]?.label ?? '未知步骤'
})

const currentTraceStep = computed(() => {
  const steps = trace.value.steps
  return stepIndex.value === 0 ? steps[0] : steps[stepIndex.value - 1]
})

const currentStepBefore = computed(() => [...(currentTraceStep.value?.state_before ?? [])])
const currentStepAfter = computed(() => [...(currentTraceStep.value?.state_after ?? [])])

const currentRoundKey = computed(() => {
  const steps = trace.value.steps
  const step = stepIndex.value === 0 ? steps[0] : steps[stepIndex.value - 1]
  if (!step || step.op !== 'add_round_key') return new Uint8Array(16)

  const out = new Uint8Array(16)
  step.key_words.forEach((wordIndex, position) => {
    const word = trace.value.key_schedule[wordIndex]
    if (word) out.set(word, position * 4)
  })
  return out
})

function next(): void {
  playback.pause()
  playback.next()
}

function commitStep(index: number): void {
  playback.pause()
  playback.setStep(index)
}

function prev(): void {
  playback.pause()
  playback.prev()
}

function first(): void {
  playback.pause()
  playback.first()
}

function last(): void {
  playback.pause()
  playback.last()
}

function togglePlay(): void {
  playback.toggle()
}

useHotkeys({
  onPlayPause: togglePlay,
  onPrev: prev,
  onNext: next,
  onFirst: first,
  onLast: last,
})

if (import.meta.env.DEV) {
  const w = window as Window & {
    __CIPHERLENS_TRACE__?: typeof trace.value
    __CIPHERLENS_PLAYBACK__?: typeof playback
  }
  w.__CIPHERLENS_TRACE__ = trace.value
  w.__CIPHERLENS_PLAYBACK__ = playback
}
</script>