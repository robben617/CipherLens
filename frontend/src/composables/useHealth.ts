/**
 * 后端能力探测：这一路的回答到底是模型给的，还是本地模板？
 *
 * 这个问题的答案在**提问之前**就该知道 —— 否则学生看到一个漂亮的回答，
 * 会以为「AI 在辅导」，而实际上只是 if-else。E 区用它点一颗状态点。
 *
 * 三条纪律：
 * 1. 只探一次。用模块级单例，多个组件共享一个结果，不给后端添无谓的请求。
 * 2. 失败等于「本地」。探不到就按本地讲，绝不让 UI 卡在「检测中」。
 * 3. 不阻塞渲染。探针异步跑，结果回来再点亮状态点。
 */

import { readonly, ref } from 'vue'

export interface HealthStatus {
  checked: boolean
  online: boolean
  llm: boolean
  model: string | null
}

const state = ref<HealthStatus>({ checked: false, online: false, llm: false, model: null })

let pending: Promise<void> | null = null

function apply(patch: Partial<HealthStatus>): void {
  state.value = { ...state.value, ...patch }
}

async function probeOnce(): Promise<void> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), 3000)
  try {
    const response = await fetch('/api/health', { signal: controller.signal })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const data = (await response.json()) as {
      llm?: { enabled?: boolean; model?: string | null }
    }
    apply({
      checked: true,
      online: true,
      llm: data.llm?.enabled === true,
      model: typeof data.llm?.model === 'string' ? data.llm.model : null,
    })
  } catch {
    // 后端没起、代理没通、超时 —— 都按「本地」处理，不弹错
    apply({ checked: true, online: false, llm: false, model: null })
  } finally {
    clearTimeout(timer)
  }
}

export function useHealth() {
  function probe(): Promise<void> {
    if (!pending) pending = probeOnce()
    return pending
  }

  /** 用户点了「重试」时重新探一次 —— 后端可能刚配好 key。 */
  function refresh(): Promise<void> {
    pending = probeOnce()
    return pending
  }

  return { health: readonly(state), probe, refresh }
}
