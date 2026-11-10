import { expect, test } from '@playwright/test'

test('source_bytes 驱动 1 error + 4 downstream，并显示其余差异', async ({ page }) => {
  await page.goto('/practice?debug=quiz')
  await page.waitForFunction(() => window.__quiz?.ready?.() === true)
  await page.evaluate(() => window.__quiz.contract())

  await expect(page.locator('.c-byte.is-error')).toHaveCount(1)
  await expect(page.locator('.c-byte.is-downstream')).toHaveCount(4)
  await expect(page.locator('[data-propagated]')).toContainText('来源候选字节：4 个')
  await expect(page.locator('[data-extra-diffs]')).toContainText('还有 2 个差异字节')
})

test('旧响应缺 source_bytes 时回退 propagated 且只 warn 一次', async ({ page }) => {
  const warnings: string[] = []
  page.on('console', (message) => {
    if (message.type() === 'warning') warnings.push(message.text())
  })

  await page.goto('/practice?debug=quiz')
  await page.waitForFunction(() => window.__quiz?.ready?.() === true)
  await page.evaluate(() => window.__quiz.legacy())

  await expect(page.locator('.c-byte.is-error')).toHaveCount(1)
  await expect(page.locator('.c-byte.is-downstream')).toHaveCount(8)
  expect(warnings.filter((text) => text.includes('source_bytes 缺失')).length).toBe(1)
})