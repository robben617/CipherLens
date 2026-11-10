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
  expected: string
}

export interface QuizSubmitResponse {
  summary: { total_bytes: number; wrong_count: number }
  first_diff: QuizFirstDiff | null
  diff_bytes?: number[] | null
  source_bytes?: number[] | null
  source_step_index?: number | null
  source_round?: number | null
  source_step?: string | null
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
  id: number
  item_id: string
  submitted: string
  is_correct: boolean
  first_diff_round: number | null
  first_diff_step: string | null
  first_diff_step_index: number | null
  first_diff_byte: number | null
  misconception: string | null
  created_at: string
}

export interface RecordsSummary {
  total: number
  correct: number
  accuracy: number | null
  misconceptions: RecordsMisconception[]
  most_stuck: {
    round: number
    step: string
    byte: number
    count: number
    label: string
  } | null
  trend: { index: number; is_correct: boolean; created_at: string }[]
  wrong: RecordsAttempt[]
  sample_threshold: number
}
