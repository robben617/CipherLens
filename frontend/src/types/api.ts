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