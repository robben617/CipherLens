import { describe, expect, it } from 'vitest'
import { affine, gfInverse, gfMul, rotl8, sboxByHand } from './gf'
import { INV_SBOX, SBOX } from './sbox'

describe('GF(2⁸) 乘法', () => {
  it('单位元与零元', () => {
    expect(gfMul(0, 0x3f)).toBe(0)
    expect(gfMul(1, 0x3f)).toBe(0x3f)
    expect(gfMul(0x3f, 1)).toBe(0x3f)
  })

  it('溢出时按 0x11B 约简', () => {
    // 0x80 · 0x02 = 0x100 → 约简为 0x1B
    expect(gfMul(0x80, 0x02)).toBe(0x1b)
    expect(gfMul(0x57, 0x83)).toBe(0xc1) // FIPS-197 §4.2 示例
  })

  it('交换律对全部 256 个值成立', () => {
    for (let a = 0; a < 256; a += 1) {
      for (let b = 0; b < 256; b += 1) {
        if (gfMul(a, b) !== gfMul(b, a)) throw new Error(`不可交换：${a} × ${b}`)
      }
    }
  })
})

describe('GF(2⁸) 求逆', () => {
  it('a · a⁻¹ = 1，且 a⁻¹ 唯一', () => {
    for (let a = 1; a < 256; a += 1) {
      const inverse = gfInverse(a)
      expect(gfMul(a, inverse)).toBe(1)
      expect(gfInverse(inverse)).toBe(a)
    }
  })

  it('0 的逆元定义为 0（FIPS-197）', () => {
    expect(gfInverse(0)).toBe(0)
  })
})

describe('循环左移与仿射变换', () => {
  it('rotl8 是循环移，不是普通左移', () => {
    expect(rotl8(0x80, 1)).toBe(0x01)
    expect(rotl8(0x81, 1)).toBe(0x03)
    expect(rotl8(0x3f, 4)).toBe(0xf3)
    expect(rotl8(0xaa, 8)).toBe(0xaa)
  })

  it('affine 常量项 0x63 让 S(0) = 0x63', () => {
    expect(affine(0)).toBe(0x63)
  })
})

describe('手算 S 盒与常量表一致', () => {
  it('sboxByHand(x) === SBOX[x]，256 个全部成立', () => {
    const mismatched: string[] = []
    for (let input = 0; input < 256; input += 1) {
      const byHand = sboxByHand(input)
      if (byHand !== SBOX[input]) {
        mismatched.push(
          `0x${input.toString(16).padStart(2, '0')}: 手算 0x${byHand
            .toString(16)
            .padStart(2, '0')} / 表 0x${SBOX[input]!.toString(16).padStart(2, '0')}`,
        )
      }
    }
    expect(mismatched).toEqual([])
  })

  // 注意：0x3F 的输出是 0x75，不是 0xC6。0xC6 来自 0xC7（旧设计稿此处写错，已改文档）。
  it('抽查 FIPS-197 的已知点', () => {
    expect(sboxByHand(0x00)).toBe(0x63)
    expect(sboxByHand(0x3f)).toBe(0x75)
    expect(sboxByHand(0xff)).toBe(0x16)
    expect(sboxByHand(0x53)).toBe(0xed) // FIPS-197 §5.1.1 的官方示例
  })

  it('0x53 的求逆中间量与 FIPS-197 一致（0xCA）', () => {
    expect(gfInverse(0x53)).toBe(0xca)
    expect(gfMul(0x53, 0xca)).toBe(1)
  })

  it('逆盒按定义反查：INV_SBOX[SBOX[x]] === x', () => {
    for (let input = 0; input < 256; input += 1) {
      expect(INV_SBOX[SBOX[input]!]).toBe(input)
    }
  })
})
