import { expect, test, type Page } from '@playwright/test'

const SLIDER = '[aria-label="播放进度"]'

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('cl:onboarded', '1')
  })
})

function trackErrors(page: Page): string[] {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(`pageerror: ${error.message}`))
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(`console: ${message.text()}`)
  })
  return errors
}

function overflowX(page: Page): Promise<number> {
  return page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  )
}

test('9. 首页入口直达工作台与闯关记，返回不丢导航', async ({ page }) => {
  const errors = trackErrors(page)

  await page.goto('/')
  await expect(page.locator('#hero-title')).toContainText('把 AES 拆开给你看')
  await expect(page.locator('.hm__cell')).toHaveCount(16)

  await page.getByRole('link', { name: '看一次真实的加密' }).click()
  await expect(page).toHaveURL(/\/workbench/)
  await expect(page.locator('.cmp__grid')).toBeVisible()
  await expect(page.locator(SLIDER)).toHaveAttribute('aria-valuemax', '40')

  await page.getByRole('link', { name: '首页', exact: true }).click()
  await expect(page).toHaveURL(/\/$/)

  await page.getByRole('link', { name: '进入像素闯关记' }).click()
  await expect(page).toHaveURL(/\/aes-quest\/index\.html$/)
  await expect(page.locator('#startScreen')).toBeVisible()

  expect(errors, errors.join('\n')).toEqual([])
})

test('10. 工作台主流程：播放、步进、整体视图与密钥抽屉', async ({ page }) => {
  const errors = trackErrors(page)
  await page.goto('/workbench')
  await expect(page.locator(SLIDER)).toHaveAttribute('aria-valuemax', '40')

  const play = page.locator('[data-action="play"]')
  await expect(play).toHaveAttribute('aria-pressed', 'false')
  await page.keyboard.press('Space')
  await expect(play).toHaveAttribute('aria-pressed', 'true')
  await expect
    .poll(async () => Number(await page.locator(SLIDER).getAttribute('aria-valuenow')), {
      timeout: 6000,
    })
    .toBeGreaterThan(0)
  await page.keyboard.press('Space')
  await expect(play).toHaveAttribute('aria-pressed', 'false')

  await page.keyboard.press('Home')
  await expect(page.locator(SLIDER)).toHaveAttribute('aria-valuenow', '0')
  await page.keyboard.press('ArrowRight')
  await expect(page.locator(SLIDER)).toHaveAttribute('aria-valuenow', '1')
  await expect(page.locator('.cmp__cell')).toHaveCount(32)

  await page.locator('[data-action="toggle-compare"]').click()
  await expect(page.locator('.c-matrix__grid')).toBeVisible()
  await expect(page.locator('.c-byte:not([data-ghost="true"])')).toHaveCount(16)
  await page.locator('[data-action="toggle-compare"]').click()
  await expect(page.locator('.cmp__grid').first()).toBeVisible()

  await page.keyboard.press('Home')
  await page.getByRole('button', { name: '密钥', exact: true }).click()
  await expect(page.locator('[data-key-drawer]')).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(page.locator('[data-key-drawer]')).toHaveCount(0)

  expect(errors, errors.join('\n')).toEqual([])
})

test('11. 工作台 AI：工具状态、S 盒结论、就地动作与模型弹窗', async ({ page }) => {
  const errors = trackErrors(page)
  await page.goto('/workbench?step=6')
  await expect(page.locator('.cmp__pair')).toBeVisible()

  await page.locator('[data-action="toggle-tutor"]').click()
  const ask = page.getByLabel('向 AI 提问')
  await expect(ask).toBeEnabled()
  await ask.fill(`全流程 S 盒 ${Date.now()}：S 盒里 0x4C 换成什么？`)
  await page.locator('[data-action="ask"]').click()

  await expect(page.locator('[data-tool-trace]')).toBeVisible({ timeout: 15000 })
  await expect(page.locator('[data-tool-trace]')).toHaveAttribute('data-state', 'ok')
  await expect(page.locator('.tutor .msg__conclusion')).toContainText('0x29')
  await expect(page.locator('.tutor .msg__act')).toContainText('S 盒')

  const urlBefore = await page.evaluate(() => location.href)
  await page.locator('.tutor .msg__act').click()
  await expect(page.locator('[data-drawer]')).toBeVisible()
  expect(await page.evaluate(() => location.href)).toBe(urlBefore)
  await page.keyboard.press('Escape')
  await expect(page.locator('[data-drawer]')).toHaveCount(0)

  await page.locator('[data-model-status-btn]').click()
  await expect(page.locator('#mcd-title')).toHaveText('添加模型')
  await page.locator('[data-mcd-tab="custom"]').click()
  await expect(page.locator('[data-mcd-base-url]')).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(page.locator('#mcd-title')).toHaveCount(0)

  expect(errors, errors.join('\n')).toEqual([])
})

test('12. S 盒：定位、选中与 AI 问答一致', async ({ page }) => {
  const errors = trackErrors(page)
  await page.goto('/sbox')
  await expect(page.locator('.sbox-grid__cell')).toHaveCount(256)

  await page.locator('[data-sbox-search]').fill('0x53')
  await page.locator('[data-action="sbox-locate"]').click()
  await expect(page.locator('[data-sbox-resolved]')).toContainText('0x53')

  const selected = page.locator('.sbox-grid__cell.is-selected')
  await expect(selected).toHaveCount(1)
  await expect(selected).toHaveText('ED')

  await page.locator('.ai-fab').click()
  await expect(page.locator('.gai__welcome')).toBeVisible()
  await page.locator('.gai__compose textarea').fill('S 盒里 0x53 换成什么？')
  await page.locator('.gai__send').click()
  await expect(page.locator('[data-tool-trace]')).toBeVisible({ timeout: 15000 })
  await expect(page.locator('.gai__assistant .msg__conclusion')).toContainText('0xED')

  expect(errors, errors.join('\n')).toEqual([])
})

test('13. 雪崩：现算、换字节复算、定稿文案与 AI 一致', async ({ page }) => {
  const errors = trackErrors(page)
  await page.goto('/avalanche')
  const run = page.locator('[data-action="run"]')
  await expect(run).toBeEnabled()
  await run.click()

  await expect(page.locator('[data-stat="changed-bits"]')).toBeVisible({ timeout: 15000 })
  const first = Number(await page.locator('[data-stat="changed-bits"]').innerText())
  expect(first).toBeGreaterThan(0)
  expect(first).toBeLessThan(128)
  await expect(page.locator('.av__bit')).toHaveCount(128)
  await expect(page.locator('.av__note').last()).toContainText('扩散设计的直观体现')

  await page.locator('[data-action="sweep"]').click()
  await expect(page.locator('.av__sweep')).toBeVisible({ timeout: 20000 })
  await expect(page.locator('.av__sweep-foot')).toContainText('两轮之内')

  await page.locator('.av__byte').nth(1).click()
  await page.waitForTimeout(600)
  const second = Number(await page.locator('[data-stat="changed-bits"]').innerText())
  expect(second).toBeGreaterThan(0)
  expect(second).not.toBe(first)

  const pageBits = Number(await page.locator('[data-stat="changed-bits"]').innerText())
  await page.locator('.ai-fab').click()
  await page.locator('.gai__compose textarea').fill('改 1 位明文，雪崩会变多少位？')
  await page.locator('.gai__send').click()
  await expect(page.locator('[data-tool-trace]')).toBeVisible({ timeout: 15000 })
  await expect(page.locator('.gai__assistant .msg__conclusion')).toContainText(
    new RegExp(`${pageBits}\\s*\\/\\s*128`),
    { timeout: 15000 },
  )

  expect(errors, errors.join('\n')).toEqual([])
})

test('14. 闯关记：故事背景、开始与退出', async ({ page }) => {
  const errors = trackErrors(page)
  await page.goto('/aes-quest/index.html')
  await expect(page.locator('#startScreen')).toBeVisible()
  const story = page.locator('[data-start-story]')
  await expect(story).toContainText('窃听蝙蝠')
  await expect(story).toContainText('AES 石碑')
  await expect(story).toContainText('黑匣子')

  await page.locator('#startBtn').click()
  await expect(page.locator('#startScreen')).toBeHidden({ timeout: 8000 })

  await page.locator('.btn--exit').click()
  await expect(page).toHaveURL(/\/$/)

  expect(errors.filter((item) => !item.includes('NotAllowedError'))).toEqual([])
})

test('15. 390 窄屏：四个栏目无横向溢出、格子不少列', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })

  await page.goto('/')
  await expect(page.locator('.hm__cell')).toHaveCount(16)
  expect(await overflowX(page)).toBe(0)

  await page.goto('/sbox')
  await expect(page.locator('.sbox-grid__cell')).toHaveCount(256)
  expect(await overflowX(page)).toBe(0)

  await page.goto('/avalanche')
  await page.locator('[data-action="run"]').click()
  await expect(page.locator('[data-stat="changed-bits"]')).toBeVisible({ timeout: 15000 })
  expect(await overflowX(page)).toBe(0)

  await page.goto('/workbench?step=6')
  await expect(page.locator('.cmp__cell')).toHaveCount(32)
  expect(await overflowX(page)).toBe(0)
})

test('16. 联网搜索开关与来源展示', async ({ page }) => {
  test.setTimeout(90000)
  const errors = trackErrors(page)

  await page.goto('/')
  await page.locator('.ai-fab').click()
  await expect(page.locator('.gai__welcome')).toBeVisible()
  await page.locator('.gai__web').click()
  await expect(page.locator('.gai__web')).toHaveAttribute('aria-pressed', 'true')

  await page.locator('.gai__compose textarea').fill('FIPS 197 里 AES 的 S 盒是什么？')
  await page.locator('.gai__send').click()
  await expect(page.locator('.msg__sources')).toBeVisible({ timeout: 45000 })
  const sources = page.locator('.msg__source')
  expect(await sources.count()).toBeGreaterThan(0)
  await expect(page.locator('.gai__assistant .msg__conclusion')).not.toBeEmpty()

  await page.locator('.gai__web').click()
  await expect(page.locator('.gai__web')).toHaveAttribute('aria-pressed', 'false')

  expect(errors, errors.join('\n')).toEqual([])
})