import { expect, test } from '@playwright/test'

test('记录页分开显示未归类错因与题目设计意图', async ({ page, request }) => {
  const clientId = `c_${'3'.repeat(32)}`
  const baseline = (
    await (await request.get('/api/records/summary', { headers: { 'X-Client-Id': clientId } })).json()
  ).total as number

  const body = {
    item_id: 'q_042',
    answer_hex: '3925841d02dc09fadc118597196a0b32',
    plaintext_hex: '00112233445566778899aabbccddeeff',
    key_hex: '000102030405060708090a0b0c0d0e0f',
    key_bits: 128,
  }
  for (let index = 0; index < 3; index++) {
    await request.post('/api/quiz/submit', {
      headers: { 'X-Client-Id': clientId },
      data: body,
    })
  }

  await page.addInitScript((id) => {
    localStorage.setItem('cipherlens.client_id', id)
  }, clientId)
  await page.goto('/records')
  await expect(page.locator('[data-stat="total"] strong')).toHaveText(String(baseline + 3))
  await expect(page.locator('[data-bucket="unattributed"]')).toContainText(`${baseline + 3} 次`)
  await expect(page.locator('[data-panel="design-tags"]')).toContainText(
    '题目设计意图（不是算法诊断）',
  )
  await expect(page.locator('[data-design-tag="key_timing"]')).toContainText(
    `轮密钥时机 · ${baseline + 3} 次`,
  )
})