// 学习行为上报：只记「看了哪一步、停多久、切了什么」，不记内容。
//
// 三条规则：
// 1. 播放时按采样记（默认 10 秒一条），否则一秒钟 2 步会把表刷满；
//    「其余事件全记」—— 手动跳步、方向切换这类动作才是数据。
// 2. 攒批 + 定时冲洗，失败静默丢弃：这是埋点，不是业务请求，不能挡用户。
// 3. 关页面时用 keepalive 补一发，否则最后十几步全丢。

import { getClientId } from '../utils/clientId'

export interface PendingEvent {
  type: string
  step_index?: number
  at: number
  dwell_ms?: number
}

/** 播放中两次采样之间的最小间隔 */
export const SAMPLE_MS = 10000
const FLUSH_MS = 5000
const MAX_BATCH = 40

/** 采样判定抽成纯函数，单测不用起浏览器 */
export function shouldSample(lastAt: number | null, now: number, min = SAMPLE_MS): boolean {
  if (lastAt === null) return true
  return now - lastAt >= min
}

let queue: PendingEvent[] = []
let flushTimer: ReturnType<typeof setInterval> | undefined
let lastSampleAt: number | null = null
let listenersBound = false

function post(items: PendingEvent[]): void {
  if (items.length === 0) return
  // 失败就当没发生：这里 block 或弹错只会让用户困惑
  void fetch('/api/events', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Client-Id': getClientId(),
    },
    body: JSON.stringify({ items }),
    keepalive: true,
  }).catch(() => undefined)
}

export function flush(): void {
  if (queue.length === 0) return
  const batch = queue.splice(0, queue.length)
  post(batch)
}

function onHide(): void {
  if (document.visibilityState === 'hidden') flush()
}

function bindListeners(): void {
  if (listenersBound) return
  listenersBound = true
  document.addEventListener('visibilitychange', onHide)
  window.addEventListener('pagehide', flush)
}

/**
 * 记一条事件。
 * `sample: true` 表示「播放中的步进」—— 同一类事件 10 秒内只留一条。
 */
export function track(
  type: string,
  options: { step?: number; dwellMs?: number; sample?: boolean } = {},
): void {
  const now = Date.now()
  if (options.sample && !shouldSample(lastSampleAt, now)) return
  if (options.sample) lastSampleAt = now

  queue.push({
    type,
    at: now,
    ...(options.step === undefined ? {} : { step_index: options.step }),
    ...(options.dwellMs === undefined ? {} : { dwell_ms: Math.round(options.dwellMs) }),
  })

  if (queue.length >= MAX_BATCH) flush()
}

/** 工作台挂载时调用：起定时器和页面隐藏监听 */
export function startEventReporter(): void {
  bindListeners()
  if (flushTimer !== undefined) return
  flushTimer = setInterval(flush, FLUSH_MS)
}

/** 离开工作台时停表（页面级单例，重复调用安全） */
export function stopEventReporter(): void {
  if (flushTimer !== undefined) {
    clearInterval(flushTimer)
    flushTimer = undefined
  }
  lastSampleAt = null
  flush()
}

/** 单测用：把队列清空，避免用例之间互相污染 */
export function __resetEvents(): void {
  queue = []
  lastSampleAt = null
}
