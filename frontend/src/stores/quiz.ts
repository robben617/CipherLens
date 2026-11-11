import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import type { QuizSubmitResponse } from '../types/api'
import { getClientId } from '../utils/clientId'

export type QuizPhase = 'idle' | 'submitting' | 'graded' | 'error'

export interface QuizSubmitPayload {
  item_id: string
  answer_hex: string
  plaintext_hex: string
  key_hex: string
  key_bits: 128 | 192 | 256
}

export const useQuizStore = defineStore('quiz', () => {
  const phase = ref<QuizPhase>('idle')
  const response = ref<QuizSubmitResponse | null>(null)
  const error = ref('')
  const counted = ref(false)
  const overlayArmed = ref(false)
  const stats = ref({ done: 0, correct: 0 })

  const firstDiff = computed(() => response.value?.first_diff ?? null)
  const errorBytes = computed(() => {
    const diff = firstDiff.value
    return new Set<number>(diff ? [diff.byte_index] : [])
  })
  const diffBytes = computed(() => new Set<number>(response.value?.diff_bytes ?? []))
  const propagated = computed(() => new Set<number>(response.value?.propagated ?? []))
  let warnedSourceFallback = false
  const sourceBytes = computed(() => {
    const raw = response.value?.source_bytes
    if (Array.isArray(raw)) return new Set<number>(raw)
    const fallback = response.value?.propagated
    if (response.value && !warnedSourceFallback && Array.isArray(fallback)) {
      console.warn('[QUIZ] source_bytes 缺失，回退 propagated')
      warnedSourceFallback = true
    }
    return new Set<number>(fallback ?? [])
  })
  const inputMismatch = computed(() => response.value?.input_mismatch ?? null)
  const allCorrect = computed(
    () => response.value !== null && firstDiff.value === null && !inputMismatch.value,
  )

  function normalize(raw: QuizSubmitResponse): QuizSubmitResponse {
    const next: QuizSubmitResponse = { ...raw }
    if (!Array.isArray(next.propagated)) {
      console.warn('[QUIZ] propagated 缺失或非数组，按空数组降级', raw.propagated)
      next.propagated = []
    } else {
      next.propagated = next.propagated.filter(
        (value): value is number =>
          typeof value === 'number' && Number.isInteger(value) && value >= 0 && value < 16,
      )
    }
    return next
  }

  function applyResponse(raw: QuizSubmitResponse, options?: { count?: boolean }): void {
    const next = normalize(raw)
    response.value = next
    phase.value = 'graded'
    error.value = ''

    const shouldCount = options?.count ?? next.input_mismatch === null
    counted.value = shouldCount
    if (shouldCount) {
      stats.value.done += 1
      if (next.first_diff === null && next.input_mismatch === null) {
        stats.value.correct += 1
      }
    }
  }

  async function submit(payload: QuizSubmitPayload): Promise<void> {
    phase.value = 'submitting'
    error.value = ''
    try {
      const res = await fetch('/api/quiz/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Client-Id': getClientId(),
        },
        body: JSON.stringify(payload),
      })
      const data = (await res.json().catch(() => null)) as
        | QuizSubmitResponse
        | { error?: { message?: string } }
        | null

      if (!res.ok) {
        phase.value = 'error'
        error.value =
          (data as { error?: { message?: string } } | null)?.error?.message ??
          `判分失败（HTTP ${res.status}）`
        return
      }

      if (!data || !('summary' in data) || !('first_diff' in data)) {
        phase.value = 'error'
        error.value = '判分响应格式不正确'
        return
      }

      applyResponse(data as QuizSubmitResponse)
    } catch {
      phase.value = 'error'
      // 判分在后端做，连不上就没有成绩 —— 不能显示成功
      error.value = '后端未连接，本次不计入记录；作答已保留，恢复连接后可重新提交'
    }
  }

  function clear(): void {
    phase.value = 'idle'
    response.value = null
    error.value = ''
    counted.value = false
    overlayArmed.value = false
  }

  function armOverlay(): void {
    overlayArmed.value = true
  }

  function disarmOverlay(): void {
    overlayArmed.value = false
  }

  return {
    phase,
    response,
    error,
    counted,
    overlayArmed,
    stats,
    firstDiff,
    errorBytes,
    diffBytes,
    sourceBytes,
    propagated,
    inputMismatch,
    allCorrect,
    applyResponse,
    submit,
    clear,
    armOverlay,
    disarmOverlay,
  }
})