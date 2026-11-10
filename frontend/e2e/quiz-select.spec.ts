import { expect, test } from '@playwright/test'

test('切换 192/256 题：页头、密钥长度与输入同步', async ({ page }) => {
  await page.goto('/practice?item=q_044')
  await expect(page.locator('.practice__meta')).toHaveText('AES-192 · 16 字节')
  await expect(page.locator('.practice__field').nth(1)).toContainText('密钥（48 位十六进制）')
  await expect(page.locator('input[name="key"]')).toHaveValue(/^[0-9a-f]{48}$/)

  await page.locator('[data-item="q_046"]').click()
  await expect(page).toHaveURL(/item=q_046/)
  await expect(page.locator('.practice__meta')).toHaveText('AES-256 · 16 字节')
  await expect(page.locator('.practice__field').nth(1)).toContainText('密钥（64 位十六进制）')
  await expect(page.locator('input[name="key"]')).toHaveValue(/^[0-9a-f]{64}$/)
})

test('切题清空上一题判分叠加', async ({ page }) => {
  await page.goto('/practice')
  await page.locator('input[name="answer"]').fill('3925841d02dc09fadc118597196a0b32')
  await page.locator('[data-action="submit"]').click()
  await expect(page.locator('.c-byte.is-error')).toHaveCount(1)

  await page.locator('[data-item="q_043"]').click()
  await expect(page).toHaveURL(/item=q_043/)
  await expect(page.locator('.c-byte.is-error')).toHaveCount(0)
  await expect(page.locator('.practice__question')).toContainText('列混合专项')
})