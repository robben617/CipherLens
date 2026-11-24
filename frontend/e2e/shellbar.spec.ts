import { expect, test } from '@playwright/test'

const VIEWPORTS = [
  { width: 1440, height: 900 },
  { width: 1280, height: 800 },
  { width: 1024, height: 768 },
  { width: 390, height: 844 },
]

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem('cl:onboarded', '1'))
})

const ROUTES = [
  ['home', '/', '#hero-title'],
  ['workbench', '/workbench?step=6', '.workbench'],
  ['sbox', '/sbox', '.sbox__title'],
] as const

type BarSnapshot = {
  height: number
  brand: string | null
  nameSize: string | null
  nameWeight: string | null
  navSize: string | null
  navWeight: string | null
  navSpacing: string | null
  activeWeight: string | null
  nameSpacing: string | null
  cnSize: string | null
  cnSpacing: string | null
  linkGap: number | null
  navVisible: boolean
  navGap: number | null
  versionVisible: boolean
  guide: boolean
  key: boolean
  docOverflow: number
}

async function snapshot(page: import('@playwright/test').Page): Promise<BarSnapshot> {
  return page.evaluate(() => {
    const bar = document.querySelector('.shellbar')
    const name = document.querySelector('.shellbar__name')
    const links = [...document.querySelectorAll('.navlinks__link')]
    const inactive = links.find((item) => !item.classList.contains('is-active'))
    const active = links.find((item) => item.classList.contains('is-active'))
    const navWrap = document.querySelector('.shellbar__navwrap')
    const nav = document.querySelector('.navlinks')
    const ver = document.querySelector('.shellbar__ver')
    const brand = document.querySelector('[data-shell-brand]')
    const cs = (el: Element | null) => (el ? getComputedStyle(el) : null)
    const barRect = bar?.getBoundingClientRect()
    const brandRect = brand?.getBoundingClientRect()
    const navRect = nav?.getBoundingClientRect()
    const navVisible = Boolean(navWrap && navWrap.getBoundingClientRect().width > 0)
    const cn = document.querySelector('.shellbar__cn')
    const first = links[0]
    const second = links[1]
    return {
      height: barRect ? +barRect.height.toFixed(1) : 0,
      brand: name?.textContent?.trim() ?? null,
      nameSize: cs(name)?.fontSize ?? null,
      nameWeight: cs(name)?.fontWeight ?? null,
      navSize: cs(inactive ?? null)?.fontSize ?? null,
      navWeight: cs(inactive ?? null)?.fontWeight ?? null,
      navSpacing: cs(first ?? null)?.letterSpacing ?? null,
      activeWeight: cs(active ?? null)?.fontWeight ?? null,
      nameSpacing: cs(name)?.letterSpacing ?? null,
      cnSize: cs(cn)?.fontSize ?? null,
      cnSpacing: cs(cn)?.letterSpacing ?? null,
      linkGap:
        navVisible && first && second
          ? +(second.getBoundingClientRect().left - first.getBoundingClientRect().right).toFixed(1)
          : null,
      navVisible,
      navGap:
        navVisible && brandRect && navRect
          ? +(navRect.left - brandRect.right).toFixed(1)
          : null,
      versionVisible: Boolean(
        ver && getComputedStyle(ver).display !== 'none' && ver.getBoundingClientRect().width > 0,
      ),
      guide: Boolean(document.querySelector('.shellbar [data-action="tour"]')),
      key: Boolean(document.querySelector('.shellbar [data-action="key-schedule"]')),
      docOverflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    }
  })
}

test('三页顶栏视觉契约一致（四档视口）', async ({ page }) => {
  test.setTimeout(180000)
  for (const viewport of VIEWPORTS) {
    await page.setViewportSize(viewport)
    const rows: Record<string, BarSnapshot> = {}

    for (const [name, path, ready] of ROUTES) {
      await page.goto(path)
      await page.locator(ready).waitFor({ timeout: 15000 })
      await page.locator('.shellbar').waitFor()
      rows[name] = await snapshot(page)
      expect(rows[name].docOverflow, `${name} ${viewport.width}x${viewport.height} 横向溢出`).toBe(0)
      await page.screenshot({
        path: `../output/shellbar/${viewport.width}x${viewport.height}-${name}.png`,
      })
    }

    const home = rows.home!
    for (const name of ['workbench', 'sbox'] as const) {
      const row = rows[name]!
      expect(row.height, `${name} 顶栏高度`).toBe(home.height)
      expect(row.nameSize, `${name} 品牌字号`).toBe(home.nameSize)
      expect(row.nameWeight, `${name} 品牌字重`).toBe(home.nameWeight)
      expect(row.navSize, `${name} 导航字号`).toBe(home.navSize)
      expect(row.navWeight, `${name} 导航字重`).toBe(home.navWeight)
      expect(row.navSpacing, `${name} 导航字间隔`).toBe(home.navSpacing)
      expect(row.activeWeight, `${name} 导航激活字重`).toBe(home.activeWeight)
      expect(row.nameSpacing, `${name} 品牌字间隔`).toBe(home.nameSpacing)
      expect(row.cnSize, `${name} 中文副标题字号`).toBe(home.cnSize)
      expect(row.cnSpacing, `${name} 中文副标题字间隔`).toBe(home.cnSpacing)
      expect(row.navVisible, `${name} 导航可见性`).toBe(home.navVisible)
      expect(row.versionVisible, `${name} 版本号可见性`).toBe(home.versionVisible)
      if (home.navVisible) expect(row.navGap, `${name} 品牌到导航间距`).toBe(home.navGap)
      if (home.navVisible) expect(row.linkGap, `${name} 导航项间距`).toBe(home.linkGap)
    }

    expect(rows.workbench!.guide, `工作台引导按钮 ${viewport.width}x${viewport.height}`).toBe(true)
    expect(rows.workbench!.key, `工作台密钥按钮 ${viewport.width}x${viewport.height}`).toBe(true)
  }
})

test('工作台顶栏操作仍可用：引导、密钥、K 快捷键', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 })
  await page.goto('/workbench?step=6')
  await page.locator('.workbench').waitFor({ timeout: 15000 })
  await page.locator('.shellbar').waitFor()

  await page.locator('.shellbar [data-action="tour"]').click()
  await expect(page.locator('[data-tour]')).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(page.locator('[data-tour]')).toHaveCount(0)

  await page.locator('.shellbar [data-action="key-schedule"]').click()
  await expect(page.locator('[data-key-drawer]')).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(page.locator('[data-key-drawer]')).toHaveCount(0)

  await page.keyboard.press('k')
  await expect(page.locator('[data-key-drawer]')).toBeVisible()
  await page.keyboard.press('Escape')

  await expect(page.locator('.shellbar__ver')).toHaveText('v0.1')
})