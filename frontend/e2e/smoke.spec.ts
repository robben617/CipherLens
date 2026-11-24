import { expect, test, type Page } from '@playwright/test'

const SLIDER = '[aria-label="播放进度"]'

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

test('1. 载入工作台并播放/暂停', async ({ page }) => {
  await openWorkbench(page)
  const slider = page.locator(SLIDER)
  const play = page.locator('[data-action="play"]')

  await expect(page.locator('.cmp')).toBeVisible()
  await expect(page.locator('.cmp__cell')).toHaveCount(16)
  await expect(slider).toHaveAttribute('aria-valuenow', '0')
  await expect(play).toHaveAttribute('aria-pressed', 'false')

  await page.keyboard.press('Space')
  await expect(play).toHaveAttribute('aria-pressed', 'true')
  await expect
    .poll(async () => Number(await slider.getAttribute('aria-valuenow')), { timeout: 6000 })
    .toBeGreaterThan(0)

  await page.keyboard.press('Space')
  await expect(play).toHaveAttribute('aria-pressed', 'false')
  const paused = Number(await slider.getAttribute('aria-valuenow'))
  await page.waitForTimeout(600)
  expect(Number(await slider.getAttribute('aria-valuenow'))).toBe(paused)
})

test('2. 前后对照步进 0→1→0', async ({ page }) => {
  await openWorkbench(page)
  const slider = page.locator(SLIDER)
  const compare = page.locator('.cmp')

  await expect(slider).toHaveAttribute('aria-valuenow', '0')
  await expect(compare).toHaveAttribute('data-step', '0')
  await expect(page.locator('.cmp__cell')).toHaveCount(16)

  await page.keyboard.press('ArrowRight')
  await expect(slider).toHaveAttribute('aria-valuenow', '1')
  await expect(compare).toHaveAttribute('data-step', '1')
  await expect(page.locator('.cmp__cell')).toHaveCount(32)

  await page.keyboard.press('ArrowLeft')
  await expect(slider).toHaveAttribute('aria-valuenow', '0')
  await expect(compare).toHaveAttribute('data-step', '0')
  await expect(page.locator('.cmp__cell')).toHaveCount(16)
})

test('3. J 聚焦播放进度、标记跳转与抽屉焦点归还', async ({ page }) => {
  await openWorkbench(page)
  const slider = page.locator(SLIDER)

  const before = await page.evaluate(() => ({
    now: document.querySelector('[aria-label="播放进度"]')?.getAttribute('aria-valuenow'),
    pressed: document.querySelector('[data-action="play"]')?.getAttribute('aria-pressed'),
    scrollY: window.scrollY,
    scrollLeft: document.querySelector('[data-region="c"]')?.scrollLeft ?? 0,
  }))

  await page.keyboard.press('j')
  await expect(slider).toBeFocused()
  const after = await page.evaluate(() => ({
    now: document.querySelector('[aria-label="播放进度"]')?.getAttribute('aria-valuenow'),
    pressed: document.querySelector('[data-action="play"]')?.getAttribute('aria-pressed'),
    scrollY: window.scrollY,
    scrollLeft: document.querySelector('[data-region="c"]')?.scrollLeft ?? 0,
  }))
  expect(after).toEqual(before)

  await page.keyboard.press('j')
  await expect(slider).toBeFocused()

  await page.keyboard.press('End')
  await expect(slider).toHaveAttribute('aria-valuenow', '40')
  await page.keyboard.press('[')
  await expect(slider).toHaveAttribute('aria-valuenow', '27')
  await page.keyboard.press(']')
  await expect(slider).toHaveAttribute('aria-valuenow', '27')

  await page.keyboard.press('k')
  await expect(page.locator('[data-key-drawer]')).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(page.locator('[data-key-drawer]')).toHaveCount(0)
  await expect(
    page.getByRole('button', { name: '密钥', exact: true }),
  ).toBeFocused()
})

test('4. 无 D 区视图按 J 静默降级', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))

  await page.goto('/workbench?debug=states')
  await expect(page.locator('[data-action="tour-skip"]')).toHaveCount(0)
  const before = await page.evaluate(() => document.activeElement?.tagName ?? '')

  await page.keyboard.press('j')
  await page.waitForTimeout(200)

  expect(errors).toEqual([])
  expect(await page.evaluate(() => location.search)).toContain('debug=states')
  await expect(page.locator(SLIDER)).toHaveCount(0)
  expect(await page.evaluate(() => document.activeElement?.tagName ?? '')).toBe(before)
})

test('5. 提问 SSE 流式到达', async ({ page }) => {
  await openWorkbench(page)
  const slider = page.locator(SLIDER)

  await page.keyboard.press('ArrowRight')
  await expect(slider).toHaveAttribute('aria-valuenow', '1')

  const toggle = page.locator('[data-action="toggle-tutor"]')
  await expect(toggle).toHaveAttribute('aria-expanded', 'false')
  await toggle.click()
  await expect(toggle).toHaveAttribute('aria-expanded', 'true')
  await expect(page.locator('#ai-panel-body')).toBeVisible()

  await page.evaluate(() => {
    const panel = document.querySelector('.tutor')
    const phases: (string | null)[] = []
    ;(window as Window & { __e2ePhases?: (string | null)[] }).__e2ePhases = phases
    if (!panel) return
    new MutationObserver(() => {
      phases.push(panel.getAttribute('data-phase'))
    }).observe(panel, { attributes: true, attributeFilter: ['data-phase'] })
  })

  const ask = page.getByLabel('向 AI 提问')
  await expect(ask).toBeEnabled()
  await ask.fill(`F24 E2E 流式 ${Date.now()}：这一步为什么这么做？`)
  await ask.press('Enter')

  await expect(page.locator('.tutor')).toHaveAttribute('data-phase', 'done', {
    timeout: 20000,
  })
  const phases = await page.evaluate(
    () => (window as Window & { __e2ePhases?: (string | null)[] }).__e2ePhases ?? [],
  )
  expect(phases).toContain('streaming')
  const answer = await page.locator('.tutor .msg').innerText()
  expect(answer.length).toBeGreaterThan(20)
})