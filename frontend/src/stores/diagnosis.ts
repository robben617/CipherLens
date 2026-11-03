import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useUiStore } from './ui'

export type DiagnosisType = 'idle' | 'toggle'

export interface DiagnosisPayload {
  question: string
  byteIndex: number
  row: number
  col: number
}

export interface DiagnosisNote extends DiagnosisPayload {
  id: number
  type: DiagnosisType
  createdAt: number
}

const IDLE_MS = 20000
const COOLDOWN_MS = 45000
const DWELL_MS = 3000
const WINDOW_MAX = 2
const TRAIL_LENGTH = 7

export const useDiagnosisStore = defineStore('diagnosis', () => {
  const ui = useUiStore()

  const note = ref<DiagnosisNote | null>(null)
  const history = ref<DiagnosisNote[]>([])
  const lastFiredAt = ref(0)
  const lastActivityAt = ref(Date.now())
  const lastBlocked = ref('')
  const pendingType = ref<DiagnosisType>('idle')
  const pendingFrom = ref(0)
  const pendingTo = ref(0)

  let seq = 0
  let lastStep = -1
  let trail: { step: number; at: number }[] = []

  function noteActivity(): void {
    lastActivityAt.value = Date.now()
  }

  function recordStep(step: number): void {
    const now = Date.now()
    lastActivityAt.value = now
    if (step === lastStep) return

    if (
      pendingType.value === 'toggle' &&
      (step < pendingFrom.value || step > pendingTo.value)
    ) {
      pendingType.value = 'idle'
    }

    lastStep = step
    trail.push({ step, at: now })
    if (trail.length > TRAIL_LENGTH) trail.shift()
    detectToggle()
  }

  function detectToggle(): void {
    if (trail.length < TRAIL_LENGTH) return

    const a = trail[0]!.step
    const b = trail[1]!.step
    if (a === b) return

    const gap = Math.abs(a - b)
    if (gap < 1 || gap > WINDOW_MAX) return

    for (let index = 0; index < trail.length; index++) {
      const expected = index % 2 === 0 ? a : b
      if (trail[index]!.step !== expected) return
    }

    for (let index = 1; index < trail.length; index++) {
      if (trail[index]!.at - trail[index - 1]!.at >= DWELL_MS) return
    }

    pendingType.value = 'toggle'
    pendingFrom.value = Math.min(a, b)
    pendingTo.value = Math.max(a, b)
  }

  function ready(now: number): boolean {
    if (note.value) return false
    if (ui.activeChannel !== 'idle') return false
    if (now - lastActivityAt.value < IDLE_MS) return false
    if (lastFiredAt.value > 0 && now - lastFiredAt.value < COOLDOWN_MS) return false
    return true
  }

  function fire(type: DiagnosisType, payload: DiagnosisPayload): boolean {
    const now = Date.now()
    if (note.value) {
      lastBlocked.value = 'visible'
      return false
    }
    if (ui.activeChannel !== 'idle') {
      lastBlocked.value = 'channel'
      return false
    }
    if (lastFiredAt.value > 0 && now - lastFiredAt.value < COOLDOWN_MS) {
      lastBlocked.value = 'cooldown'
      return false
    }

    const item: DiagnosisNote = {
      id: ++seq,
      type,
      createdAt: now,
      ...payload,
    }
    note.value = item
    history.value.push(item)
    lastFiredAt.value = now
    lastActivityAt.value = now
    lastBlocked.value = ''
    pendingType.value = 'idle'
    return true
  }

  function dismiss(): void {
    note.value = null
  }

  function resetCooldown(): void {
    lastFiredAt.value = 0
    lastBlocked.value = ''
  }

  return {
    note,
    history,
    lastFiredAt,
    lastActivityAt,
    lastBlocked,
    pendingType,
    pendingFrom,
    pendingTo,
    noteActivity,
    recordStep,
    ready,
    fire,
    dismiss,
    resetCooldown,
  }
})