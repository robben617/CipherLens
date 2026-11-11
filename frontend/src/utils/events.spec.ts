import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { __resetEvents, flush, SAMPLE_MS, shouldSample, track } from './events'

interface SentBody {
  items: { type: string; step_index?: number; dwell_ms?: number; at: number }[]
}

function sentBodies(): SentBody[] {
  const mock = fetch as unknown as { mock: { calls: unknown[][] } }
  return mock.mock.calls.map(
    (call) => JSON.parse((call[1] as { body: string }).body) as SentBody,
  )
}

describe('events 采样判定', () => {
  it('第一次一定采', () => {
    expect(shouldSample(null, 1000)).toBe(true)
  })

  it('间隔不足 10 秒丢掉', () => {
    expect(shouldSample(1000, 1000 + SAMPLE_MS - 1)).toBe(false)
  })

  it('刚好到 10 秒就采', () => {
    expect(shouldSample(1000, 1000 + SAMPLE_MS)).toBe(true)
  })
})

describe('events 攒批上报', () => {
  beforeEach(() => {
    __resetEvents()
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve({ ok: true, status: 204 })),
    )
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
    __resetEvents()
  })

  it('一次 flush 把队列整批发走', () => {
    track('step', { step: 3, dwellMs: 1200.4 })
    track('step', { step: 4 })

    flush()

    expect(fetch).toHaveBeenCalledTimes(1)
    const [body] = sentBodies()
    expect(body!.items).toHaveLength(2)
    expect(body!.items[0]).toMatchObject({ type: 'step', step_index: 3, dwell_ms: 1200 })
    expect(body!.items[1]).not.toHaveProperty('dwell_ms')
  })

  it('队列空时不发请求', () => {
    flush()
    expect(fetch).not.toHaveBeenCalled()
  })

  it('采样事件 10 秒内只留一条', () => {
    const now = 1_700_000_000_000
    vi.spyOn(Date, 'now').mockReturnValue(now)
    track('step', { step: 1, sample: true })

    vi.spyOn(Date, 'now').mockReturnValue(now + 2000)
    track('step', { step: 2, sample: true })

    vi.spyOn(Date, 'now').mockReturnValue(now + SAMPLE_MS)
    track('step', { step: 3, sample: true })

    flush()

    const [body] = sentBodies()
    expect(body!.items.map((item) => item.step_index)).toEqual([1, 3])
  })

  it('手动跳步（不采样）每一下都记', () => {
    const now = 1_700_000_000_000
    vi.spyOn(Date, 'now').mockReturnValue(now)
    track('step', { step: 1, sample: true })
    track('jump', { step: 20 })
    track('jump', { step: 21 })

    flush()

    const [body] = sentBodies()
    expect(body!.items).toHaveLength(3)
  })
})
