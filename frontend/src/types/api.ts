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