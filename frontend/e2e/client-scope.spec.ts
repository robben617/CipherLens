import { expect, test } from '@playwright/test'

const A = `c_${'1'.repeat(32)}`
const B = `c_${'2'.repeat(32)}`
const answer = {
  item_id: 'q_042',
  answer_hex: '3925841d02dc09fadc118597196a0b32',
  plaintext_hex: '3243f6a8885a308d313198a2e0370734',
  key_hex: '2b7e151628aed2a6abf7158809cf4f3c',
  key_bits: 128,
}

test('A/B 匿名客户端隔离，刷新不换 ID，legacy 入口可读', async ({ page, request, browser }) => {
  const baselineA = (
    await (await request.get('/api/records/summary', { headers: { 'X-Client-Id': A } })).json()
  ).total as number
  const baselineB = (
    await (await request.get('/api/records/summary', { headers: { 'X-Client-Id': B } })).json()
  ).total as number

  for (let index = 0; index < 2; index++) {
    await request.post('/api/quiz/submit', {
      headers: { 'X-Client-Id': A },
      data: answer,
    })
  }
  for (let index = 0; index < 3; index++) {
    await request.post('/api/quiz/submit', {
      headers: { 'X-Client-Id': B },
      data: answer,
    })
  }

  await page.addInitScript((id) => {
    localStorage.setItem('cipherlens.client_id', id)
  }, A)
  await page.goto('/records')
  await expect(page.locator('[data-stat="total"] strong')).toHaveText(String(baselineA + 2))
  expect(await page.evaluate(() => localStorage.getItem('cipherlens.client_id'))).toBe(A)

  await page.reload()
  expect(await page.evaluate(() => localStorage.getItem('cipherlens.client_id'))).toBe(A)
  await expect(page.locator('[data-stat="total"] strong')).toHaveText(String(baselineA + 2))

  await page.locator('[data-action="legacy"]').click()
  await expect(page).toHaveURL(/scope=legacy/)
  await expect(page.locator('[data-badge]')).toHaveText('迁移前记录（只读）')

  const contextB = await browser.newContext({ baseURL: 'http://127.0.0.1:8080' })
  const pageB = await contextB.newPage()
  await pageB.addInitScript((id) => {
    localStorage.setItem('cipherlens.client_id', id)
  }, B)
  await pageB.goto('/records')
  await expect(pageB.locator('[data-stat="total"] strong')).toHaveText(String(baselineB + 3))
  await contextB.close()
})