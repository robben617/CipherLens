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

/** 解密第 0 步 · 输入的密文 */
export const DECRYPT_INITIAL_COPY: StepCopy = {
  plain: '这是密文，16 个字节按列填进 4×4 的格子。解密就从这里往回走。',
  analogy: '照着加密的脚印倒着走：最后盖上去的那枚章，要第一个擦掉。',
  math: '第 1 步先和第 10 轮密钥异或——它对应的正是加密的最后一步。',
  pitfall:
    '不是「把加密的四步各自反过来做一遍」就行。顺序要整体倒过来，轮密钥也要从第 10 组开始倒着用。',
  terms: ['state', 'round_key'],
}

/** 解密末步 · 输出明文 */
export const DECRYPT_FINAL_COPY: StepCopy = {
  plain: '这就是明文。解密走完，32 位十六进制和当初加密前的一模一样。',
  analogy: '倒着走完全程，回到出发点。',
  math: '第 0 组轮密钥异或完就结束，所以这一步的输出直接就是明文。',
  pitfall:
    '解密不是另一套算法。密钥扩展完全一样，44 个字一个都没变，只是取用顺序倒过来了。',
  terms: ['state', 'round_key'],
}

/**
 * 逆操作的文案。
 *
 * 直接复用加密那四段会写错方向：「第 1 行不动，其余行循环左移」在解密时是右移。
 * 教学产品上把方向说反，比不说还糟。
 */
export const INV_STEP_COPY: Record<string, StepCopy> = {
  sub_bytes: {
    plain: '16 个字节，每个都拿自己的值去逆 S 盒里查一次。',
    analogy: '同一本密码本，这次拿着「字」倒查页码。',
    math: '逆 S 盒是正 S 盒的反查表：S⁻¹(S(x)) = x。等价于先撤掉仿射变换，再在 GF(2⁸) 里求逆元。',
    pitfall:
      '不是把 S 盒「倒着念」。S⁻¹ 是另一张表，每个值在正表里只出现一次，所以能从结果反查出输入，而不是把数组顺序掉个头。',
    terms: ['sub_bytes', 'sbox'],
  },
  shift_rows: {
    plain: '第 1 行不动，第 2、3、4 行分别循环右移 1、2、3 个字节。',
    analogy: '四排人倒着挪回去：刚才往前走的，现在退回同样的步数。',
    math: '第 r 行的第 c 个字节移到第 (c − r) mod 4 列，正好抵消加密时的 +r。',
    pitfall:
      '不是「继续左移」。方向必须反过来，否则挪出去的位置回不来；位移量仍然由行号决定。',
    terms: ['shift_rows', 'diffusion'],
  },
  mix_columns: {
    plain: '每列 4 个字节，一起乘逆矩阵 [14 11 13 9 / 9 14 11 13 / 13 9 14 11 / 11 13 9 14]。',
    analogy: '4 个人互相抄完笔记后，按同样的比例把各自多出来的内容减回去。',
    math: '在 GF(2⁸) 上乘逆矩阵，两个矩阵相乘得到单位矩阵，所以它是列混合的反操作。',
    pitfall:
      '不是「除以 2 3 1 1」。GF(2⁸) 里没有除法，逆矩阵的系数是 14 / 11 / 13 / 9，得靠 xtime 叠乘算出来。',
    terms: ['mix_columns', 'gf_xor', 'diffusion'],
  },
}

/** 按步骤序号、op 与方向取文案 */
export function copyFor(
  stepIndex: number,
  op: string | undefined,
  total: number,
  direction: 'encrypt' | 'decrypt' = 'encrypt',
): StepCopy {
  const decrypt = direction === 'decrypt'
  if (stepIndex <= 0) return decrypt ? DECRYPT_INITIAL_COPY : INITIAL_COPY
  if (stepIndex >= total - 1) return decrypt ? DECRYPT_FINAL_COPY : FINAL_COPY
  if (decrypt) {
    // 轮密钥加是自己的逆操作，文案与加密一致，不需要另写一份
    const inverse = INV_STEP_COPY[op ?? '']
    if (inverse) return inverse
  }
  return STEP_COPY[op ?? ''] ?? (decrypt ? DECRYPT_INITIAL_COPY : INITIAL_COPY)
}
