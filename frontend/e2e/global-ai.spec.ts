import { expect, test } from '@playwright/test'

const SSE = [
  'event: meta\ndata: {"source":"local","quotes_values":false,"cache":false,"structured":true}\n\n',
  'event: block\ndata: {"type":"conclusion","text":"AES 是 16 字节分组的对称加密。"}\n\n',
  'event: block\ndata: {"type":"why","items":["分组固定 16 字节。","密钥决定轮密钥。","四步变换各管一件事。"]}\n\n',
  'event: block\ndata: {"type":"next","text":"去工作台逐步看。"}\n\n',
  'event: block\ndata: {"type":"cite","bytes":[],"refs":[{"label":"通用讲解","value":"未引用本页数值","kind":"stat"}]}\n\n',
  'event: done\ndata: {"finish":"stop","degraded":false}\n\n',
].join('')

async function mockAsk(page) {
  await page.route('**/api/ai/ask', (route) =>
    route.fulfill({
      status: 200,
      headers: { 'Content-Type': 'text/event-stream; charset=utf-8' },
      body: SSE,
    }),
  )
}

test('首页点 AI 就地打开，不改变 URL', async ({ page }) => {
  await mockAsk(page)
  await page.goto('/')
  await expect(page.locator('.ai-fab')).toBeVisible()
  const before = await page.evaluate(() => location.href)

  await page.locator('.ai-fab').click()
  await expect(page.locator('[data-global-ai-panel]')).toBeVisible()
  expect(await page.evaluate(() => location.href)).toBe(before)
  await expect(page.locator('#global-ai-title')).toContainText('AI 助手 · 首页')

  await page.locator('.gai__prompt').first().click()
  await expect(page.locator('.gai__user')).toContainText('AES 是什么?')
  await expect(page.locator('.gai__assistant .msg')).toContainText('AES 是 16 字节分组')
})

test('S 盒 / 雪崩各自打开，问题不串页', async ({ page }) => {
  await mockAsk(page)
  await page.goto('/sbox')
  await page.locator('.ai-fab').click()
  await expect(page.locator('#global-ai-title')).toContainText('AI 助手 · S 盒')
  await expect(page.locator('.gai__user')).toHaveCount(0)
  await page.locator('.gai__prompt').first().click()
  const sboxQuestion = await page.locator('.gai__user').innerText()

  await page.goto('/avalanche')
  await expect(page).toHaveURL(/avalanche/)
  await page.waitForTimeout(600)
  await page.locator('.ai-fab').click()
  await expect(page.locator('#global-ai-title')).toContainText('AI 助手 · 雪崩')
  await expect(page.locator('.gai__user')).toHaveCount(0)
})

test('工作台保留 E 区，不出现全局抽屉入口', async ({ page }) => {
  await page.goto('/workbench')
  await expect(page.locator('[data-region="e"]')).toBeVisible()
  await expect(page.locator('.ai-fab')).toHaveCount(0)
  await expect(page.locator('[data-global-ai-panel]')).toHaveCount(0)
})