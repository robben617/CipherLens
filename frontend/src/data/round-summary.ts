/**
 * 一轮小结卡文案（F15）—— 全站唯一数据源。
 *
 * 位置：每轮四步走完时浮出，把「40 个动作」收成「10 次同样的循环」。
 * 没有这一句，用户看到的是 40 个孤立动画；有了这一句，才看得见结构。
 *
 * 文案来自《初学者学习路径与文案缺口》§2.1「桥一：单步 → 一轮」，做了两处调整：
 *   1. 三件事拆成 lead / term / tail 三段，术语加粗而不是嵌在长句里；
 *   2. 解密单独一套——把「混淆、扩散」原样搬到解密会说反（那一步其实是在拆）。
 *
 * 纪律：组件里不写文案。
 */

export interface RoundSummaryItem {
  /** 术语前面那句：这一轮到底动了什么 */
  readonly lead: string
  /** 术语本身，渲染成加粗 */
  readonly term: string
  /** 术语后面那句：为什么要这么做 */
  readonly tail: string
}

export interface RoundSummaryCopy {
  /** 标题，带轮号 */
  readonly title: (round: number) => string
  /** 引导句 */
  readonly lead: string
  /** 三件事 */
  readonly items: readonly RoundSummaryItem[]
  /** 收尾：下一轮怎么走 */
  readonly footer: string
}

export const ROUND_SUMMARY_COPY: Record<'encrypt' | 'decrypt', RoundSummaryCopy> = {
  encrypt: {
    title: (round) => `第 ${round} 轮结束`,
    lead: '这一轮发生了三件事：',
    items: [
      {
        lead: '16 个字节全部被替换了一次',
        term: '混淆',
        tail: '，输入和输出的关系从此不再是一条直线',
      },
      {
        lead: '每列的 4 个字节现在来自 4 个不同位置',
        term: '扩散',
        tail: '，一个字节的影响被摊到更多格',
      },
      {
        lead: '又叠了一层只有密钥持有者知道的字节',
        term: '轮密钥加',
        tail: '，没有密钥，这一层拆不掉',
      },
    ],
    footer: '下一轮重复同样的四步，只是换一把轮密钥 —— 这就是 AES 的全部节奏。',
  },
  decrypt: {
    title: (round) => `第 ${round} 轮拆完`,
    lead: '这一轮拆掉了三件事：',
    items: [
      {
        lead: '16 个字节全部被逆替换回 S 盒里的原值',
        term: '逆字节代换',
        tail: '，把加密时那次混淆反着做一遍',
      },
      {
        lead: '混合被拆开，字节回到上一轮的位置',
        term: '逆列混合 + 逆行移位',
        tail: '，把扩散摊开的字节收回去',
      },
      {
        lead: '抵消掉这一轮叠上去的密钥字节',
        term: '轮密钥加',
        tail: '，它本身就是自己的逆操作，所以不叫「逆」',
      },
    ],
    footer: '下一轮继续往回走，轮密钥也跟着倒着取 —— 走到第 0 轮，明文就出来了。',
  },
}

/** 三件事的序号：①②③ 固定，不用 CSS 计数器（读屏要念得出来） */
export const ROUND_SUMMARY_MARKS = ['①', '②', '③'] as const
