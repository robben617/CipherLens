import { describe, expect, it } from 'vitest'
import { appendBlock, appendToken, blocksToText, isComplete, type TutorBlock } from './tutor-message'

describe('结构化回答拼装', () => {
  it('空壳块 + token 逐段填成结论', () => {
    const blocks: TutorBlock[] = []
    appendBlock(blocks, { type: 'conclusion', text: '' })
    appendToken(blocks, '这一步把整列')
    appendToken(blocks, ' 4 个字节都改了。')

    expect(blocks).toEqual([{ type: 'conclusion', text: '这一步把整列 4 个字节都改了。' }])
  })

  it('why 块按 item 标记分条，不标记就续写当前条', () => {
    const blocks: TutorBlock[] = []
    appendBlock(blocks, { type: 'why', items: [] })
    appendToken(blocks, 'S 盒是', true)
    appendToken(blocks, '一张固定表')
    appendToken(blocks, '非线性才是目的', true)
    appendToken(blocks, '，不是加密强度', true)

    expect(blocks[0]).toEqual({
      type: 'why',
      items: ['S 盒是一张固定表', '非线性才是目的', '，不是加密强度'],
    })
  })

  it('缓存命中时块自带全文，不需要 token', () => {
    const blocks: TutorBlock[] = []
    appendBlock(blocks, { type: 'conclusion', text: '这一步把整列 4 个字节都改了。' })
    appendBlock(blocks, { type: 'why', items: ['一', '二', '三'] })

    expect(blocks[0]).toEqual({ type: 'conclusion', text: '这一步把整列 4 个字节都改了。' })
    expect(blocks[1]).toEqual({ type: 'why', items: ['一', '二', '三'] })
  })

  it('cite 只收 0–15 的整数下标', () => {
    const blocks: TutorBlock[] = []
    appendBlock(blocks, { type: 'cite', bytes: [0, 3, 15, 16, -1, 2.5, 'x'] })

    expect(blocks[0]).toEqual({ type: 'cite', bytes: [0, 3, 15] })
  })

  it('next 的 action 缺失或被写坏时不渲染按钮', () => {
    const blocks: TutorBlock[] = []
    appendBlock(blocks, { type: 'next', text: '下一句' })
    appendBlock(blocks, { type: 'next', text: '下一句', action: { label: '看第 3 步', kind: 'goto-step' } })
    appendBlock(blocks, {
      type: 'next',
      text: '下一句',
      action: { label: '看第 3 步', kind: 'goto-step', value: 3 },
    })

    expect(blocks[0]).toEqual({ type: 'next', text: '下一句', action: undefined })
    expect(blocks[1]).toEqual({ type: 'next', text: '下一句', action: undefined })
    expect(blocks[2]).toEqual({
      type: 'next',
      text: '下一句',
      action: { label: '看第 3 步', kind: 'goto-step', value: 3 },
    })
  })

  it('没有块时 token 被丢弃，不会凭空造出空块', () => {
    const blocks: TutorBlock[] = []
    appendToken(blocks, '孤立增量')
    expect(blocks).toHaveLength(0)
  })

  it('未知块类型被忽略，旧字段名不炸', () => {
    const blocks: TutorBlock[] = []
    appendBlock(blocks, { type: 'figure', src: 'x.png' })
    expect(blocks).toHaveLength(0)
  })

  it('文本视图按块顺序拼接，包含依据字节', () => {
    const blocks: TutorBlock[] = []
    appendBlock(blocks, { type: 'conclusion', text: '结论。' })
    appendBlock(blocks, { type: 'why', items: ['甲', '乙'] })
    appendBlock(blocks, {
      type: 'next',
      text: '下一步。',
      action: { label: '看第 2 步', kind: 'goto-step', value: 2 },
    })
    appendBlock(blocks, { type: 'cite', bytes: [0, 15] })

    expect(blocksToText(blocks)).toBe('结论。 甲 乙 下一步。 依据：0x00、0x0F')
    expect(isComplete(blocks)).toBe(true)
    expect(isComplete(blocks.slice(0, 2))).toBe(false)
  })
})

describe('cite refs 与页面动作', () => {
  it('解析白名单 refs 并丢弃未知 kind', () => {
    const blocks: TutorBlock[] = []
    appendBlock(blocks, {
      type: 'cite',
      bytes: [],
      refs: [
        { label: '输入', value: '0x53', kind: 'byte' },
        { label: '输出', value: '0xED', kind: 'byte' },
        { label: '坏引用', value: 'x', kind: 'unknown' },
      ],
    })

    expect(blocks[0]).toEqual({
      type: 'cite',
      bytes: [],
      refs: [
        { label: '输入', value: '0x53', kind: 'byte' },
        { label: '输出', value: '0xED', kind: 'byte' },
      ],
    })
  })

  it('refs 最多保留 6 条', () => {
    const blocks: TutorBlock[] = []
    appendBlock(blocks, {
      type: 'cite',
      bytes: [],
      refs: Array.from({ length: 8 }, (_, index) => ({
        label: `L${index}`,
        value: String(index),
        kind: 'stat',
      })),
    })
    expect(blocks[0]).toMatchObject({ type: 'cite' })
    expect((blocks[0] as Extract<TutorBlock, { type: 'cite' }>).refs).toHaveLength(6)
  })

  it('接受新的页面动作类型，未知动作丢弃', () => {
    const blocks: TutorBlock[] = []
    appendBlock(blocks, {
      type: 'next',
      text: '去工作台',
      action: { label: '去工作台', kind: 'open-workbench', value: 0 },
    })
    appendBlock(blocks, {
      type: 'next',
      text: '未知动作',
      action: { label: '未知', kind: 'delete-file', value: 0 },
    })

    expect(blocks[0]).toMatchObject({
      type: 'next',
      action: { label: '去工作台', kind: 'open-workbench', value: 0 },
    })
    expect(blocks[1]).toEqual({ type: 'next', text: '未知动作', action: undefined })
  })

  it('blocksToText 包含 refs 的 label 与 value', () => {
    const blocks: TutorBlock[] = []
    appendBlock(blocks, {
      type: 'cite',
      bytes: [],
      refs: [
        { label: '输入', value: '0x53', kind: 'byte' },
        { label: '输出', value: '0xED', kind: 'byte' },
      ],
    })
    expect(blocksToText(blocks)).toBe('输入 0x53 输出 0xED')
  })
})
