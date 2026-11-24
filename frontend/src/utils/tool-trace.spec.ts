import { describe, expect, it } from 'vitest'
import {
  applyToolEnd,
  applyToolResult,
  pushToolStart,
  toolLabel,
  toolStatusText,
  type ToolTrace,
} from './tool-trace'

describe('tool-trace', () => {
  it('tool_start 插入正在查的标签', () => {
    const traces: ToolTrace[] = []
    pushToolStart(traces, { name: 'lookup_sbox', label: 'S 盒' })
    expect(traces).toHaveLength(1)
    expect(traces[0]?.state).toBe('running')
    expect(toolStatusText(traces[0]!)).toBe('正在查S 盒…')
  })

  it('tool_result 成功后给出摘要', () => {
    const traces: ToolTrace[] = []
    pushToolStart(traces, { name: 'lookup_sbox' })
    applyToolResult(traces, { name: 'lookup_sbox', ok: true, summary: '输入 0x4C 输出 0x29' })
    expect(traces[0]?.state).toBe('ok')
    expect(toolStatusText(traces[0]!)).toContain('0x29')
  })

  it('tool_result 失败给出可读说明，不留在 running', () => {
    const traces: ToolTrace[] = []
    pushToolStart(traces, { name: 'compute_avalanche' })
    applyToolResult(traces, { name: 'compute_avalanche', ok: false, message: '缺少完整明文与密钥' })
    expect(traces[0]?.state).toBe('fail')
    expect(toolStatusText(traces[0]!)).toContain('缺少完整明文')
  })

  it('tool_end 兜底把异常结束标成失败', () => {
    const traces: ToolTrace[] = []
    pushToolStart(traces, { name: 'get_round_key' })
    applyToolEnd(traces, { name: 'get_round_key', ok: false })
    expect(traces[0]?.state).toBe('fail')
    expect(toolStatusText(traces[0]!)).toContain('这次没查到')
  })

  it('未知工具名有回退标签', () => {
    expect(toolLabel('mystery')).toBe('mystery')
  })
})