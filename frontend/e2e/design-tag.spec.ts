import { expect, test } from '@playwright/test'

test('记录页分开显示未归类错因与题目设计意图', async ({ page, request }) => {
  const clientId = `c_${'3'.repeat(32)}`
  const body = {
    item_id: 'q_042',
    answer_hex: '3925841d02dc09fadc118597196a0b32',
    plaintext_hex: '3243f6a8885a308d313198a2e0370734',
    key_hex: '2b7e151628aed2a6abf7158809cf4f3c',
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
  await expect(page.locator('[data-stat="total"] strong')).toHaveText('3')
  await expect(page.locator('[data-bucket="unattributed"]')).toContainText('3 次')
  await expect(page.locator('[data-panel="design-tags"]')).toContainText(
    '题目设计意图（不是算法诊断）',
  )
  await expect(page.locator('[data-design-tag="key_timing"]')).toContainText(
    '轮密钥时机 · 3 次',
  )
})