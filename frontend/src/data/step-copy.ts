/**
 * 单步文案表 —— 全站唯一数据源。
 *
 * 四件套结构（对应"看得懂一步"的四个层次）：
 *   plain   人话：这一步在做什么，一句能读完
 *   analogy 类比：用日常经验建立直觉
 *   math    规则：真正发生了什么，精确到可以手算
 *   pitfall 常见误解：中文译名最容易骗人的地方，必须逐条拆穿
 *
 * 纪律：不要在组件里写文案。组件只负责渲染顺序和折叠状态。
 */

export interface StepCopy {
  /** 人话：做什么 */
  readonly plain: string
  /** 类比：像什么 */
  readonly analogy: string
  /** 规则：精确描述 */
  readonly math: string
  /** 常见误解：拆穿字面误导 */
  readonly pitfall: string
  /** 涉及的术语 key（指向 glossary.ts） */
  readonly terms: readonly string[]
}

/** 按 op 取值，初始步与末步单独给 */
export const STEP_COPY: Record<string, StepCopy> = {
  sub_bytes: {
    plain: '16 个字节，每个都拿自己的值去 S 盒里查一次，查到什么就是什么。',
    analogy: '像一本 256 页的密码本，翻到第 n 页抄下那个字。人人查的都是同一本。',
    math: '先在 GF(2⁸) 里求乘法逆元（0 的逆元定义为 0），再做一次固定的仿射变换，最后异或 0x63。',
    pitfall:
      '不是「随便换个数」。表是固定的、公开的，任何人查同一张表都得到同样结果——它的作用不是保密，是打乱输入与输出的关系。',
    terms: ['sub_bytes', 'sbox', 'confusion'],
  },
  shift_rows: {
    plain: '第 1 行不动，第 2、3、4 行分别循环左移 1、2、3 个字节。',
    analogy:
      '四排人站队，第一排不动，第二排往前挪一步，第三排挪两步，第四排挪三步，挪出去的人绕回排头。',
    math: '第 r 行的第 c 个字节移到第 (c + r) mod 4 列，r 从 0 开始数。',
    pitfall:
      '不是「随便错位」。位移量由行号唯一决定，而且必须循环——移出去的要接到行尾，不然字节就丢了。',
    terms: ['shift_rows', 'diffusion'],
  },
  mix_columns: {
    plain: '每一列 4 个字节，一起乘一个固定的 4×4 矩阵，算出新的 4 个字节。',
    analogy:
      '4 个人互相抄笔记，每人新笔记里都掺了另外 3 人的内容。改一个人的，四本都会变。',
    math: '在 GF(2⁸) 上做矩阵乘法，矩阵是 [2 3 1 1 / 1 2 3 1 / 1 1 2 3 / 3 1 1 2]，加法就是异或。',
    pitfall:
      '不是「把列里的顺序打乱」。顺序一动不动，变的是每一格的值——1 个字节变了，整列 4 个都跟着变。',
    terms: ['mix_columns', 'gf_xor', 'diffusion'],
  },
  add_round_key: {
    plain: '把当前 16 个字节和这一轮的 16 个密钥字节，一对一异或。',
    analogy: '像给每个字节盖一枚章。盖两次能擦干净，因为同一个章盖第二遍就抵消了。',
    math: 'c = s ⊕ k，逐字节进行。因为 a ⊕ a = 0，所以同一个操作再做一次就还原——这正是解密的基础。',
    pitfall:
      '不是算术加法，没有进位。1 + 1 = 0。名字里的「加」是历史遗留，它实际是按位异或。',
    terms: ['add_round_key', 'round_key', 'gf_xor'],
  },
}

/** 第 0 步 · 初始状态 */
export const INITIAL_COPY: StepCopy = {
  plain: '这是你的明文，16 个字节按列填进 4×4 的格子。',
  analogy: '像往方格里竖着一列一列倒水，先灌满第一列，再灌第二列。',
  math: '第 i 个字节放在第 (i mod 4) 列、第 ⌊i / 4⌋ 行。文本里的前 4 个字节是竖着的第一列。',
  pitfall:
    '不是按行从左到右读。很多人以为 00 11 22 33 是第一行，其实它是第一行到第四行的第一格。',
  terms: ['state'],
}

/** 末步 · 输出密文 */
export const FINAL_COPY: StepCopy = {
  plain: '这就是密文。把 4×4 按列读回来，就是那 32 位十六进制。',
  analogy: '倒水的逆过程：一列一列抽出来，接成一条线。',
  math: '最后一轮没有列混合，所以每个密文字节只由上一状态的 1 个字节决定。',
  pitfall:
    '末步之后没有「收尾处理」。第 40 步的输出就是最终密文，不存在额外一轮。',
  terms: ['state'],
}

/** 按步骤序号与 op 取文案 */
export function copyFor(stepIndex: number, op: string | undefined, total: number): StepCopy {
  if (stepIndex <= 0) return INITIAL_COPY
  if (stepIndex >= total - 1) return FINAL_COPY
  return STEP_COPY[op ?? ''] ?? INITIAL_COPY
}
