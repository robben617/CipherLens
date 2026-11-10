export interface QuizItem {
  id: string
  question: string
  plaintext_hex: string
  key_hex: string
  key_bits: 128 | 192 | 256
  design_tag?: 'key_timing' | 'mix_coefficient' | null
  tag_label?: string | null
}

export const QUIZ_ITEMS: readonly QuizItem[] = [
  {
    id: 'q_042',
    design_tag: 'key_timing',
    tag_label: '轮密钥时机',
    question:
      '轮密钥专项：使用给定明文与密钥，完成 AES-128 加密，填入 32 位十六进制密文。',
    plaintext_hex: '00112233445566778899aabbccddeeff',
    key_hex: '000102030405060708090a0b0c0d0e0f',
    key_bits: 128,
  },
  {
    id: 'q_043',
    design_tag: 'mix_coefficient',
    tag_label: '列混合系数',
    question:
      '列混合专项：使用给定明文与密钥，完成 AES-128 加密，填入 32 位十六进制密文。',
    plaintext_hex: '3243f6a8885a308d313198a2e0370734',
    key_hex: '2b7e151628aed2a6abf7158809cf4f3c',
    key_bits: 128,
  },
  {
    id: 'q_044',
    design_tag: null,
    tag_label: null,
    question: '使用给定明文与密钥，完成 AES-192 加密，填入 32 位十六进制密文。',
    plaintext_hex: '00112233445566778899aabbccddeeff',
    key_hex: '000102030405060708090a0b0c0d0e0f1011121314151617',
    key_bits: 192,
  },
  {
    id: 'q_045',
    design_tag: 'mix_coefficient',
    tag_label: '列混合系数',
    question:
      '列混合专项：使用给定明文与密钥，完成 AES-192 加密，填入 32 位十六进制密文。',
    plaintext_hex: '3243f6a8885a308d313198a2e0370734',
    key_hex: '8e73b0f7da0e6452c810f32b809079e562f8ead2522c6b7b',
    key_bits: 192,
  },
  {
    id: 'q_046',
    design_tag: 'key_timing',
    tag_label: '轮密钥时机',
    question:
      '轮密钥专项：使用给定明文与密钥，完成 AES-256 加密，填入 32 位十六进制密文。',
    plaintext_hex: '00112233445566778899aabbccddeeff',
    key_hex:
      '000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f',
    key_bits: 256,
  },
  {
    id: 'q_047',
    design_tag: null,
    tag_label: null,
    question: '使用给定明文与密钥，完成 AES-256 加密，填入 32 位十六进制密文。',
    plaintext_hex: '3243f6a8885a308d313198a2e0370734',
    key_hex:
      '000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f',
    key_bits: 256,
  },
  {
    id: 'q_048',
    design_tag: 'mix_coefficient',
    tag_label: '列混合系数',
    question:
      '列混合专项：使用给定明文与密钥，完成 AES-128 加密，填入 32 位十六进制密文。',
    plaintext_hex: '00112233445566778899aabbccddeeff',
    key_hex: '2b7e151628aed2a6abf7158809cf4f3c',
    key_bits: 128,
  },
  {
    id: 'q_049',
    design_tag: null,
    tag_label: null,
    question: '使用给定明文与密钥，完成 AES-192 加密，填入 32 位十六进制密文。',
    plaintext_hex: '00112233445566778899aabbccddeeff',
    key_hex: '8e73b0f7da0e6452c810f32b809079e562f8ead2522c6b7b',
    key_bits: 192,
  },
]