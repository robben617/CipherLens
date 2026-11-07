// 性能探针：单步耗时、长帧、长任务与写批次数。
// 只在 DEV 或 ?perf=1 时暴露 window.__perf；生产默认不挂全局。

const stepDurations: number[] = []
const longFrames: number[] = []
const longTasks: number[] = []

let stepStart = 0
let stepPending = false
let rafId = 0
let prevFrame = 0
let frameCount = 0
let idleTimer: ReturnType<typeof setTimeout> | undefined
let observer: PerformanceObserver | null = null
let installed = false

function percentile(values: readonly number[], ratio: number): number {
  if (values.length === 0) return 0
  const sorted = [...values].sort((a, b) => a - b)
  const index = Math.min(sorted.length - 1, Math.ceil(ratio * sorted.length) - 1)
  return Math.round(sorted[index]! * 100) / 100
}

function frameTick(timestamp: number): void {
  if (prevFrame !== 0 && timestamp - prevFrame > 20) {
    longFrames.push(Math.round((timestamp - prevFrame) * 10) / 10)
  }
  prevFrame = timestamp
  frameCount += 1
  rafId = requestAnimationFrame(frameTick)
}

export function startFrameSampling(): void {
  if (rafId !== 0) return
  prevFrame = 0
  rafId = requestAnimationFrame(frameTick)
}

export function stopFrameSampling(): void {
  if (rafId !== 0) cancelAnimationFrame(rafId)
  rafId = 0
  prevFrame = 0
}

function armIdleStop(): void {
  if (idleTimer !== undefined) clearTimeout(idleTimer)
  idleTimer = setTimeout(() => {
    stopFrameSampling()
    idleTimer = undefined
  }, 3000)
}

export function beginStep(): void {
  stepStart = performance.now()
  stepPending = true
  startFrameSampling()
  armIdleStop()
}

export function endStep(): void {
  if (!stepPending) return
  stepPending = false
  const duration = performance.now() - stepStart
  stepDurations.push(Math.round(duration * 100) / 100)
  if (stepDurations.length > 200) stepDurations.shift()
  armIdleStop()
}

function matrixBatches(): number[] {
  const probe = window as Window & { __MATRIX_BATCHES__?: number[] }
  return probe.__MATRIX_BATCHES__ ?? []
}

function batchStats(): { samples: number[]; max: number; allOne: boolean } {
  const samples = matrixBatches().slice(-30)
  return {
    samples,
    max: samples.length ? Math.max(...samples) : 0,
    allOne: samples.length > 0 && samples.every((value) => value === 1),
  }
}

export function perfStats(): Record<string, unknown> {
  const batches = batchStats()
  return {
    steps: stepDurations.length,
    p50: percentile(stepDurations, 0.5),
    p95: percentile(stepDurations, 0.95),
    max: stepDurations.length ? Math.max(...stepDurations) : 0,
    longFrames: longFrames.length,
    maxLongFrame: longFrames.length ? Math.max(...longFrames) : 0,
    longTasks: longTasks.length,
    maxLongTask: longTasks.length ? Math.max(...longTasks) : 0,
    frames: frameCount,
    batches: batches.samples,
    maxBatch: batches.max,
    allBatchesOne: batches.allOne,
  }
}

export function installPerfProbe(): void {
  if (installed) return
  installed = true

  if (typeof PerformanceObserver !== 'undefined') {
    try {
      observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          longTasks.push(Math.round(entry.duration * 10) / 10)
        }
      })
      observer.observe({ entryTypes: ['longtask'] })
    } catch {
      observer = null
    }
  }

  const target = window as Window & { __perf?: Record<string, unknown> }
  target.__perf = {
    stats: () => perfStats(),
    frames: () => ({
      count: frameCount,
      longFrames: longFrames.length,
      longTaskCount: longTasks.length,
    }),
    reset: () => {
      stepDurations.length = 0
      longFrames.length = 0
      longTasks.length = 0
      frameCount = 0
      stepPending = false
      stopFrameSampling()
      const probe = window as Window & { __MATRIX_BATCHES__?: number[] }
      probe.__MATRIX_BATCHES__ = []
    },
    start: startFrameSampling,
    stop: () => {
      stopFrameSampling()
      if (idleTimer !== undefined) clearTimeout(idleTimer)
      idleTimer = undefined
    },
  }
}

export function disposePerfProbe(): void {
  stopFrameSampling()
  if (idleTimer !== undefined) clearTimeout(idleTimer)
  idleTimer = undefined
  observer?.disconnect()
  observer = null
}