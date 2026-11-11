export interface QuizFirstDiff {
  step_index: number
  round: number
  step: string
  byte_index: number
  expected?: number
  actual?: number
}

export interface QuizInputMismatch {
  field: 'plaintext' | 'key' | 'both'
  char_index: number
  /** hex：写了非十六进制字符；item：和题目给定的值不一致 */
  expected: string
}

export interface QuizItemRecord {
  id: string
  difficulty: 'entry' | 'basic' | 'advanced' | 'challenge' | string
  difficulty_label?: string
  design_tag: 'key_timing' | 'mix_coefficient' | 'key_schedule' | null
  tag_label: string | null
  question: string
  plaintext_hex: string
  key_hex: string
  key_bits: 128 | 192 | 256
}

export interface QuizItemsResponse {
  count: number
  items: QuizItemRecord[]
}

export interface QuizSubmitResponse {
  summary: { total_bytes: number; wrong_count: number }
  first_diff: QuizFirstDiff | null
  diff_bytes?: number[] | null
  source_bytes?: number[] | null
  source_step_index?: number | null
  source_round?: number | null
  source_step?: string | null
  design_tag?: string | null
  design_tag_label?: string | null
  design_tag_hint?: string | null
  propagated?: number[] | null
  input_mismatch: QuizInputMismatch | null
  expected_ciphertext?: string
}

export interface QuizTraceStep {
  index: number
  round: number
  op: string
  label: string
  state_before: number[]
  state_after: number[]
  changed: number[]
  key_indices: number[]
}

export interface QuizTrace {
  trace_id: string
  ciphertext: string
  steps: QuizTraceStep[]
}

export interface RecordsMisconception {
  key: 'key_timing' | 'mix_coefficient' | 'key_schedule' | 'unattributed'
  label: string
  hint: string
  count: number
}

export interface RecordsAttempt {
  /** a<id> 来自 attempts，p<id> 来自迁移前的 practice_attempts */
  id: number | string
  item_id: string
  submitted: string
  is_correct: boolean
  first_diff_round: number | null
  first_diff_step: string | null
  first_diff_step_index: number | null
  first_diff_byte: number | null
  misconception: string | null
  design_tag?: string | null
  source_bytes?: number[]
  created_at: string
  table?: 'attempts' | 'practice_attempts'
}

export interface RecordsRecent {
  id: number | string
  item_id: string
  is_correct: boolean
  first_diff_byte: number | null
  created_at: string
}

export interface RecordsSummary {
  total: number
  correct: number
  accuracy: number | null
  streak?: number
  misconceptions: RecordsMisconception[]
  design_tags?: { tag: string; label: string; count: number }[]
  most_stuck: {
    round: number
    step: string
    byte: number
    count: number
    label: string
  } | null
  trend: { index: number; is_correct: boolean; created_at: string }[]
  recent?: RecordsRecent[]
  wrong: RecordsAttempt[]
  sample_threshold: number
  scope?: 'client' | 'legacy' | 'none'
  /** 学习时长（毫秒），事件不足两条时为 null */
  study_ms?: number | null
  /** 本机上报的事件条数 */
  event_count?: number
}
