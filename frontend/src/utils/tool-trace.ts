export type ToolState = 'running' | 'ok' | 'fail'

export interface ToolTrace {
  name: string
  label: string
  state: ToolState
  summary?: string
  message?: string
}

const TOOL_LABELS: Record<string, string> = {
  lookup_sbox: 'S 盒',
  get_trace_step: '当前步轨迹',
  compute_avalanche: '雪崩现算',
  get_round_key: '轮密钥',
}

export function toolLabel(name: string): string {
  return TOOL_LABELS[name] ?? name
}

/** tool_start：在气泡里插入一条「正在查什么」。 */
export function pushToolStart(traces: ToolTrace[], payload: Record<string, unknown>): void {
  const name = typeof payload.name === 'string' && payload.name ? payload.name : 'tool'
  const label =
    typeof payload.label === 'string' && payload.label ? payload.label : toolLabel(name)
  traces.push({ name, label, state: 'running' })
}

function findRunning(traces: ToolTrace[], payload: Record<string, unknown>): ToolTrace | undefined {
  const name = typeof payload.name === 'string' ? payload.name : ''
  return [...traces].reverse().find((item) => item.name === name && item.state === 'running')
}

/** tool_result：成功给摘要，失败给人话；空白转圈不允许。 */
export function applyToolResult(
  traces: ToolTrace[],
  payload: Record<string, unknown>,
): void {
  const trace = findRunning(traces, payload)
  if (!trace) return
  if (payload.ok === true) {
    trace.state = 'ok'
    trace.summary = typeof payload.summary === 'string' ? payload.summary : ''
    return
  }
  trace.state = 'fail'
  trace.message =
    typeof payload.message === 'string' && payload.message ? payload.message : '这次没查到'
}

export function applyToolEnd(
  traces: ToolTrace[],
  payload: Record<string, unknown>,
): void {
  const trace = findRunning(traces, payload)
  if (!trace) return
  if (payload.ok === true) {
    trace.state = 'ok'
    return
  }
  trace.state = 'fail'
  trace.message = trace.message || '这次没查到'
}

export function toolStatusText(trace: ToolTrace): string {
  if (trace.state === 'running') return `正在查${trace.label}…`
  if (trace.state === 'fail') return `查${trace.label}失败：${trace.message ?? '这次没查到'}`
  return trace.summary || `已查${trace.label}`
}