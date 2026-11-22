import type { ApiPageContext, PageKey } from '../utils/ai-context'
import { hasAvalancheResult, hasSboxContext } from '../utils/ai-context'

const hex = (value: number): string =>
  value.toString(16).toUpperCase().padStart(2, '0')

export function promptsFor(
  page: PageKey,
  context: ApiPageContext | null,
): string[] {
  if (page === 'workbench') return []

  if (page === 'home') {
    return [
      'AES 是什么？',
      '为什么按 16 字节分组？',
      '密钥和加密结果是什么关系？',
    ]
  }

  if (page === 'sbox') {
    if (hasSboxContext(context)) {
      return [
        `0x${hex(context.input)} 为什么查表得到 0x${hex(context.output)}？`,
        '逆 S 盒为什么能还原？',
        '为什么 S 盒不是随机的？',
      ]
    }
    return [
      '先在网格里选中一个字节，再问我',
      '正向和逆向 S 盒有什么区别？',
      '为什么 S 盒能反查？',
    ]
  }

  if (hasAvalancheResult(context)) {
    return [
      '为什么改 1 位会变一半？',
      `为什么不是正好 ${Math.floor(context.total_bits / 2)} 位？`,
      '连做平均说明了什么？',
    ]
  }
  return [
    '先跑一次实验，才能引用真实数字',
    '为什么改 1 位会变一半？',
    '雪崩效应和扩散有什么关系？',
  ]
}