export interface QuizItem {
  id: string
  question: string
  plaintext_hex: string
  key_hex: string
  key_bits: 128 | 192 | 256
}

export const QUIZ_ITEMS: readonly QuizItem[] = [
  {
    id: 'q_042',
    question: '使用给定明文与密钥，完成 AES-128 加密，填入 32 位十六进制密文。',
    plaintext_hex: '3243f6a8885a308d313198a2e0370734',
    key_hex: '2b7e151628aed2a6abf7158809cf4f3c',
    key_bits: 128,
  },
]