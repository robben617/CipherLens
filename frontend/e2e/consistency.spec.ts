import { expect, test } from '@playwright/test'

test('前后端不一致时禁用提问，重新校验后恢复', async ({ page }) => {
  let mismatch = true
  let askRequests = 0

  await page.route('**/api/aes/trace', async (route) => {
    if (!mismatch) {
      await route.continue()
      return
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        trace_id: 't_local',
        ciphertext: '00'.repeat(16),
      }),
    })
  })
  page.on('request', (request) => {
    if (request.url().includes('/api/tutor/ask')) askRequests += 1
  })

  await page.goto('/workbench')
  await expect(page.locator('[data-mismatch]')).toBeVisible()
  await expect(page.getByLabel('向 AI 提问')).toBeDisabled()
  await expect(page.locator('[data-action="ask"]')).toBeDisabled()
  await expect(page.getByLabel('向 AI 提问')).toHaveAttribute(
    'placeholder',
    '前后端数值不一致，请重新校验后再提问',
  )

  await page.locator('[data-action="ask"]').click({ force: true })
  await page.waitForTimeout(300)
  expect(askRequests).toBe(0)

  mismatch = false
  await page.locator('[data-action="recheck-trace"]').click()
  await expect(page.locator('[data-mismatch]')).toHaveCount(0, { timeout: 8000 })
  await expect(page.locator('[data-action="recheck-trace"]')).toHaveCount(0)

  await page.keyboard.press('ArrowRight')
  await expect(page.locator('.c-timeline')).toHaveAttribute('aria-valuenow', '1')
  await expect(page.getByLabel('向 AI 提问')).toBeEnabled()
  expect(askRequests).toBe(0)
})

test('离线时保留本地矩阵与播放，但禁用提问', async ({ page }) => {
  await page.route('**/api/aes/trace', (route) => route.abort())

  await page.goto('/workbench')
  await expect(page.locator('[data-offline]')).toBeVisible()
  await expect(page.getByLabel('向 AI 提问')).toBeDisabled()
  await expect(page.locator('[data-action="ask"]')).toBeDisabled()
  await expect(page.locator('[data-action="recheck-trace"]')).toBeVisible()
  await expect(page.locator('.c-byte[data-index="0"]')).toBeVisible()
  await expect(page.locator('.c-timeline')).toHaveAttribute('aria-valuenow', '0')
})