// FIPS-197 附录 C 的三组标准向量。
// 字段使用接口契约的 hex 写法：小写、无 0x、无空格。

import type { AesKeyBits } from './aes'

export interface FipsVector {
  readonly id: string
  readonly key_bits: AesKeyBits
  readonly plaintext_hex: string
  readonly key_hex: string
  readonly ciphertext_hex: string
}

export const FIPS_197_VECTORS: readonly FipsVector[] = [
  {
    id: 'C.1',
    key_bits: 128,
    plaintext_hex: '00112233445566778899aabbccddeeff',
    key_hex: '000102030405060708090a0b0c0d0e0f',
    ciphertext_hex: '69c4e0d86a7b0430d8cdb78070b4c55a',
  },
  {
    id: 'C.2',
    key_bits: 192,
    plaintext_hex: '00112233445566778899aabbccddeeff',
    key_hex: '000102030405060708090a0b0c0d0e0f1011121314151617',
    ciphertext_hex: 'dda97ca4864cdfe06eaf70a0ec0d7191',
  },
  {
    id: 'C.3',
    key_bits: 256,
    plaintext_hex: '00112233445566778899aabbccddeeff',
    key_hex: '000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f',
    ciphertext_hex: '8ea2b7ca516745bfeafc49904b496089',
  },
]