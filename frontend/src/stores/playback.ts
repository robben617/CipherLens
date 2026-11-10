// 播放控制：高频小标量，与 trace 大数据分开。
// 倍速只改步间隔（1600 / 800 / 400ms），单步动效时长不变。
// 播放到末步自动停，不循环。

import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export type PlaybackSpeed = 0.5 | 1 | 2

const BASE_INTERVAL = 800

export const usePlaybackStore = defineStore('playback', () => {
  const currentStep = ref(0)
  const isPlaying = ref(false)
  const speed = ref<PlaybackSpeed>(1)
  const stepCount = ref(0)

  let timer: ReturnType<typeof setTimeout> | undefined

  const canPrev = computed(() => currentStep.value > 0)
  const canNext = computed(() => currentStep.value < stepCount.value)
  const intervalMs = computed(() => BASE_INTERVAL / speed.value)

  function stopTimer(): void {
    if (timer !== undefined) {
      clearTimeout(timer)
      timer = undefined
    }
  }

  function schedule(): void {
    stopTimer()
    if (!isPlaying.value) return

    timer = setTimeout(() => {
      if (!isPlaying.value) return
      if (currentStep.value >= stepCount.value) {
        pause()
        return
      }

      currentStep.value = Math.min(currentStep.value + 1, stepCount.value)
      if (currentStep.value >= stepCount.value) {
        pause()
      } else {
        schedule()
      }
    }, intervalMs.value)
  }

  function play(): void {
    if (stepCount.value === 0 || isPlaying.value) return
    if (currentStep.value >= stepCount.value) currentStep.value = 0
    isPlaying.value = true
    schedule()
  }

  function pause(): void {
    isPlaying.value = false
    stopTimer()
  }

  function toggle(): void {
    if (isPlaying.value) pause()
    else play()
  }

  function next(): void {
    if (currentStep.value < stepCount.value) currentStep.value += 1
  }

  function prev(): void {
    if (currentStep.value > 0) currentStep.value -= 1
  }

  function first(): void {
    currentStep.value = 0
  }

  function last(): void {
    currentStep.value = stepCount.value
  }

  function setStep(index: number): void {
    currentStep.value = Math.min(Math.max(index, 0), stepCount.value)
  }

  function setSpeed(value: PlaybackSpeed): void {
    speed.value = value
    // 不重排当前 timer：正在播放的那一步不被打断，下一步才使用新间隔。
  }

  function setStepCount(count: number): void {
    stepCount.value = Math.max(0, count)
    if (currentStep.value > stepCount.value) currentStep.value = stepCount.value
    if (stepCount.value === 0) pause()
  }

  return {
    currentStep,
    isPlaying,
    speed,
    stepCount,
    canPrev,
    canNext,
    intervalMs,
    play,
    pause,
    toggle,
    next,
    prev,
    first,
    last,
    setStep,
    setSpeed,
    setStepCount,
  }
})