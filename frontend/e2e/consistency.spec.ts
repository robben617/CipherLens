import { expect, test, type Page } from '@playwright/test'

const SLIDER = '[aria-label="播放进度"]'
const RECHECK = '[data-action="recheck-trace"]'
const ASK = '[data-action="ask"]'
const C1_OUTPUT = '69c4e0d86a7b0430d8cdb78070b4c55a'

type TraceMode = 'mismatch' | 'ok' | 'abort'

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('cl:onboarded', '1')
  })
})

async function openWorkbench(page: Page): Promise<void> {
  await page.goto('/workbench')
  await expect(page.locator('[data-action="tour-skip"]')).toHaveCount(0)
  await expect(page.locator(SLIDER)).toHaveAttribute('aria-valuemax', '40')
}

async function mockTrace(page: Page, mode: () => TraceMode, count: () => void): Promise<void> {
  await page.route('**/api/aes/trace', async (route) => {
    count()
    await new Promise((resolve) => setTimeout(resolve, 300))
    const current = mode()
    if (current === 'abort') {
      await route.abort()
      return
    }
    const body =
      current === 'mismatch'
        ? { trace_id: 't_local', ciphertext: '00'.repeat(16) }
        : { trace_id: 't_e2e_ok', output: C1_OUTPUT }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(body),
    })
  })
}

test('6. mismatch 禁用、连点防护与重新校验恢复', async ({ page }) => {
  let mode: TraceMode = 'mismatch'
  let traceRequests = 0
  let askRequests = 0
  await mockTrace(
    page,
    () => mode,
    () => {
      traceRequests += 1
    },
  )
  page.on('request', (request) => {
    if (request.url().includes('/api/tutor/ask')) askRequests += 1
  })

  await openWorkbench(page)
  await expect(page.locator('[data-mismatch]')).toBeVisible()
  await expect(page.locator(RECHECK)).toBeVisible()
  await expect(page.locator(RECHECK)).toBeEnabled()
  await expect(page.getByLabel('向 AI 提问')).toBeDisabled()
  await expect(page.locator(ASK)).toBeDisabled()

  await page.locator(ASK).dispatchEvent('click')
  await page.waitForTimeout(300)
  expect(askRequests).toBe(0)

  const stepBefore = await page.locator(SLIDER).getAttribute('aria-valuenow')
  expect(traceRequests).toBe(1)

  mode = 'ok'
  await page.locator(RECHECK).click()
  await expect(page.locator('[data-checking]')).toBeVisible()
  await expect(page.locator(RECHECK)).toBeDisabled()
  const duringRetry = traceRequests
  await page.locator(RECHECK).dispatchEvent('click')

  await expect(page.locator('[data-mismatch]')).toHaveCount(0, { timeout: 8000 })
  await expect(page.locator(RECHECK)).toHaveCount(0)
  expect(traceRequests).toBe(duringRetry)
  await expect(page.locator(SLIDER)).toHaveAttribute('aria-valuenow', stepBefore ?? '0')

  await page.keyboard.press('ArrowRight')
  await expect(page.locator(SLIDER)).toHaveAttribute('aria-valuenow', '1')
  await expect(page.getByLabel('向 AI 提问')).toBeEnabled()
  await expect(page.locator(ASK)).toBeEnabled()
})

test('7. mismatch 持续、重试后仍不一致', async ({ page }) => {
  let traceRequests = 0
  await mockTrace(
    page,
    () => 'mismatch',
    () => {
      traceRequests += 1
    },
  )

  await openWorkbench(page)
  await expect(page.locator('[data-mismatch]')).toBeVisible()
  const before = traceRequests

  await page.locator(RECHECK).click()
  await expect(page.locator('[data-checking]')).toBeVisible()
  await expect(page.locator(RECHECK)).toBeDisabled()

  await expect(page.locator(RECHECK)).toBeEnabled({ timeout: 8000 })
  await expect(page.locator('[data-checking]')).toHaveCount(0)
  await expect(page.locator('[data-mismatch]')).toBeVisible()
  await expect(page.getByLabel('向 AI 提问')).toBeDisabled()
  expect(traceRequests).toBe(before + 1)
})

test('8. offline 本地播放与重试恢复', async ({ page }) => {
  let mode: TraceMode = 'abort'
  await mockTrace(
    page,
    () => mode,
    () => undefined,
  )

  await openWorkbench(page)
  const slider = page.locator(SLIDER)
  await expect(page.locator('[data-offline]')).toBeVisible()
  await expect(page.locator(RECHECK)).toBeVisible()
  await expect(page.locator(RECHECK)).toBeEnabled()
  await expect(page.getByLabel('向 AI 提问')).toBeDisabled()
  await expect(page.locator('.cmp__cell')).toHaveCount(16)

  await page.keyboard.press('ArrowRight')
  await expect(slider).toHaveAttribute('aria-valuenow', '1')

  mode = 'ok'
  await page.locator(RECHECK).click()
  await expect(page.locator('[data-checking]')).toBeVisible()
  await expect(page.locator(RECHECK)).toBeDisabled()
  await expect(page.locator('[data-offline]')).toHaveCount(0, { timeout: 8000 })
  await expect(page.locator(RECHECK)).toHaveCount(0)
})