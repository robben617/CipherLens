/**
 * 术语表 —— 全站唯一数据源（12 条）。
 *
 * 三条纪律：
 * 1. 只解释「挡路」的词。看到它走不下去才收；不挡路的不进这张表。
 * 2. 每条必须有 pitfall。中文译名会制造虚假熟悉感（"移位"像随便挪、"加"像算术加法），
 *    不拆穿这一层，用户会以为自己懂了，然后卡在后一步。
 * 3. 界面与 AI 回答都读这一份。同一套术语出现两个版本，用户会以为是两回事。
 *
 * 分级：L1 挡路（不认识就读不懂任何一步）、L2 支撑（解释"为什么是这四步"）。
 * 轮常数 / 逆 S 盒 / 分组模式归 L3，只在用到处给一句话，不进表。
 */

export interface GlossaryTerm {
  /** 内部 key，与 step-copy 的 terms 对应 */
  readonly key: string
  /** 中文名 */
  readonly name: string
  /** 英文原名（决定是否让用户意识到"这是个我没见过的词"） */
  readonly en: string
  /** L1 挡路 / L2 支撑 */
  readonly layer: 'L1' | 'L2'
  /** 做什么：一句具体动作，不是同义词替换 */
  readonly action: string
  /** 类比 */
  readonly analogy: string
  /** 常见误解：拆穿字面给人的错误印象 */
  readonly pitfall: string
}

export const GLOSSARY: readonly GlossaryTerm[] = [
  {
    key: 'state',
    name: '状态矩阵',
    en: 'State',
    layer: 'L1',
    action: '当前这 16 个字节，排成 4 行 4 列的样子。四步操作全都在它身上做，做完就变成下一步的状态。',
    analogy: '像一块可以反复擦写的白板，四步操作是四次改写，每次改写都基于上一次的结果。',
    pitfall: '不是"数据的副本"或"中间缓存"。它就是这个算法此刻的全部内容，改完它没有别的地方存着原文。',
  },
  {
    key: 'round',
    name: '轮',
    en: 'Round',
    layer: 'L1',
    action: '四步走一遍叫一轮。AES-128 走 10 轮，AES-192 走 12 轮，AES-256 走 14 轮。',
    analogy: '像揉面团，同样的四个动作重复十次，每重复一次面团就更均匀一点。',
    pitfall: '不是"四步各走一次就结束"。轮数由密钥长度决定，而且最后一轮少做一次列混合。',
  },
  {
    key: 'sub_bytes',
    name: '字节代换',
    en: 'SubBytes',
    layer: 'L1',
    action: '每个字节拿自己的值当索引，去 S 盒里查出一个新字节，16 个字节各查一次。',
    analogy: '一本 256 页的密码本，翻到第 n 页抄下那个字。',
    pitfall: '不是"换个值"。查的是一张 256 项的固定表，公开的，谁查都一样——它防的是关系可分析，不是防偷看。',
  },
  {
    key: 'shift_rows',
    name: '行移位',
    en: 'ShiftRows',
    layer: 'L1',
    action: '第 1 行不动，第 2、3、4 行分别循环左移 1、2、3 个字节。',
    analogy: '四排人往前挪，第一排不动，后面每排多挪一步，挪出去的绕回排头。',
    pitfall: '不是"随便挪位置"。位移量等于行号，而且是循环移位——移出去的必须接回行尾。',
  },
  {
    key: 'mix_columns',
    name: '列混合',
    en: 'MixColumns',
    layer: 'L1',
    action: '每一列 4 个字节乘一个固定的 4×4 矩阵，算出新的 4 个字节，四列分别做。',
    analogy: '4 个人互相抄笔记，每人新笔记里都有另外 3 人的内容。',
    pitfall: '不是"把列里顺序打乱"。顺序完全不变，是每一格的值全变了，而且 1 格变动会传到整列。',
  },
  {
    key: 'add_round_key',
    name: '轮密钥加',
    en: 'AddRoundKey',
    layer: 'L1',
    action: '当前 16 个字节和这一轮的 16 个密钥字节，一对一按位异或。',
    analogy: '给每个字节盖一枚章，同一个章盖第二遍就抵消了。',
    pitfall: '不是算术加法，没有进位，1 + 1 = 0。叫"加"是历史遗留，实际是异或。',
  },
  {
    key: 'sbox',
    name: 'S 盒',
    en: 'S-Box',
    layer: 'L1',
    action: '一张 16×16 的查找表，共 256 项。输入一个字节，输出另一个字节，同一个输入永远得到同一个输出。',
    analogy: '像一张固定的对照表，不是随机数表——随机数表没法反查，它必须能反查才能解密。',
    pitfall: '不是"随机打乱"。它是由 GF(2⁸) 求逆加仿射变换算出来的规则表，所以能构造逆表用于解密。',
  },
  {
    key: 'key_expansion',
    name: '密钥扩展',
    en: 'Key Expansion',
    layer: 'L1',
    action: '把 16 字节的原始密钥，一步步推成 11 组、每组 16 字节的轮密钥，供每一轮使用。',
    analogy: '一根主钥匙，按固定规则锉出十把不同的副钥匙，每把只开一轮的锁。',
    pitfall: '不是"把密钥复制十份"。每一组都是从前一组算出来的，改动主密钥任何一位，后面所有轮密钥全变。',
  },
  {
    key: 'round_key',
    name: '轮密钥',
    en: 'Round Key',
    layer: 'L1',
    action: '某一轮专门用到的那 16 个字节，由密钥扩展产生，每一轮都不一样。',
    analogy: '每一轮换一把副钥匙，十轮用十把不同的。',
    pitfall: '不是"原始密钥重复使用"。第 0 轮到第 10 轮用的都不同，否则一轮被破全套失效。',
  },
  {
    key: 'confusion',
    name: '混淆',
    en: 'Confusion',
    layer: 'L2',
    action: '让密文和密钥之间的关系变得无法用简单公式表达。字节代换主要负责这件事。',
    analogy: '把钥匙和锁孔之间的联系搅浑，改钥匙一点点，结果看起来毫无规律。',
    pitfall: '不是"把数据加密得看不懂"。它是一个明确的设计目标：切断密钥位与密文位之间的线性关系。',
  },
  {
    key: 'diffusion',
    name: '扩散',
    en: 'Diffusion',
    layer: 'L2',
    action: '让输入的 1 个字节变化影响到输出的一大片。行移位负责摊开，列混合负责混合。',
    analogy: '一滴墨落进水里，搅几圈之后整杯水都变了色。',
    pitfall: '不是"数据被打散"。方向是反的：它是让局部变化传播到全局，这正是雪崩效应的来源。',
  },
  {
    key: 'gf_xor',
    name: 'GF(2⁸) 与异或',
    en: 'Galois Field / XOR',
    layer: 'L2',
    action: '字节做运算的规则。加法就是异或（不进位），乘法是特殊定义的，结果仍然是一个字节。',
    analogy: '像只有 0 和 1 的算术：1+1=0，1+0=1。没有 2，也没有进位。',
    pitfall: '不是普通的整数加减乘。GF(2⁸) 里的乘法不是 3×7=21，而是一套查表和移位的结果，永远不超过 0xFF。',
  },
]

/** 按 key 快速取值 */
export const GLOSSARY_MAP: Readonly<Record<string, GlossaryTerm>> = Object.fromEntries(
  GLOSSARY.map((term) => [term.key, term]),
)

/** 四步的中文名 —— 全前端唯一来源（与后端 services/glossary.py 的 OP_LABEL 对应） */
export const OP_LABEL: Readonly<Record<string, string>> = Object.fromEntries(
  ['sub_bytes', 'shift_rows', 'mix_columns', 'add_round_key'].map((key) => [
    key,
    GLOSSARY_MAP[key]?.name ?? key,
  ]),
)

/** 按 key 列表批量取，忽略不存在的 key */
export function termsOf(keys: readonly string[]): readonly GlossaryTerm[] {
  return keys.map((k) => GLOSSARY_MAP[k]).filter((t): t is GlossaryTerm => Boolean(t))
}
