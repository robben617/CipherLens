import { expect, test } from '@playwright/test'

test('1. 载入工作台并播放/暂停', async ({ page }) => {
  await page.goto('/workbench')
  await expect(page.locator('.c-byte[data-index="0"]')).toBeVisible()
  const timeline = page.locator('.c-timeline')
  const start = Number(await timeline.getAttribute('aria-valuenow'))

  await page.keyboard.press('Space')
  await expect
    .poll(async () => Number(await timeline.getAttribute('aria-valuenow')), {
      timeout: 6000,
    })
    .toBeGreaterThan(start)

  await page.keyboard.press('Space')
  const paused = Number(await timeline.getAttribute('aria-valuenow'))
  await page.waitForTimeout(600)
  expect(Number(await timeline.getAttribute('aria-valuenow'))).toBe(paused)
})

test('2. 提问 SSE 流式到达', async ({ page }) => {
  const trace = page.waitForResponse(
    (response) => response.url().includes('/api/aes/trace') && response.ok(),
  )
  await page.goto('/workbench')
  await trace
  await page.evaluate(() => {
    window.__e2ePhases = []
    const panel = document.querySelector('.tutor')
    if (!panel) return
    new MutationObserver(() => {
      window.__e2ePhases.push(panel.getAttribute('data-phase'))
    }).observe(panel, { attributes: true, attributeFilter: ['data-phase'] })
  })

  const question = `F24 E2E 流式 ${Date.now()}：这一步为什么这么做？`
  await page.getByLabel('向 AI 提问').fill(question)
  await page.getByLabel('向 AI 提问').press('Enter')

  await expect(page.locator('.tutor')).toHaveAttribute('data-phase', 'done', {
    timeout: 15000,
  })
  const phases = await page.evaluate(() => window.__e2ePhases)
  expect(phases).toContain('streaming')
  const answer = await page.locator('.tutor__answer').innerText()
  expect(answer.length).toBeGreaterThan(20)
})

test('3. 练习判分与 downstream 灰化', async ({ page }) => {
  await page.goto('/practice')
  await page.locator('input[name="answer"]').fill('3925841d02dc09fadc118597196a0b32')
  await page.locator('[data-action="submit"]').click()

  await expect(page.locator('[data-summary]')).toContainText('1 个不符', {
    timeout: 15000,
  })
  await expect(page.locator('.c-byte.is-error')).toHaveCount(1)
  await expect(page.locator('.c-byte.is-downstream')).toHaveCount(8)
  await expect(page.locator('.c-range__label')).toHaveText('影响范围：16 字节')

  const downstreamBackground = await page
    .locator('.c-byte.is-downstream')
    .first()
    .evaluate((element) => getComputedStyle(element).backgroundColor)
  expect(downstreamBackground).not.toBe('rgba(0, 0, 0, 0)')
})

test('4. 纯键盘标记跳转与抽屉焦点归还', async ({ page }) => {
  await page.goto('/workbench')
  await expect(page.locator('.c-timeline')).toBeVisible()

  await page.keyboard.press('End')
  await expect(page.locator('.c-timeline')).toHaveAttribute('aria-valuenow', '40')

  await page.keyboard.press('[')
  await expect(page.locator('.c-timeline')).toHaveAttribute('aria-valuenow', '27')
  await expect(page.locator('.c-mark[data-step="27"]')).toBeFocused()

  await page.keyboard.press('Enter')
  await expect(page.locator('[data-drawer]')).toBeVisible()
  await expect(page.locator('#byte-drawer-title')).toHaveText('第 27 步 · 标记详情')

  await page.keyboard.press('Escape')
  await expect(page.locator('[data-drawer]')).toHaveCount(0)
  await expect(page.locator('.c-mark[data-step="27"]')).toBeFocused()
})