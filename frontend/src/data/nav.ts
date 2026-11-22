/**
 * 全站导航的单一数据源。
 * AppShell（首页/S 盒/雪崩）与工作台 A 区共用同一份，避免两处各写一套导致文案漂移。
 */
export interface NavItem {
  readonly to: string
  readonly label: string
  readonly key: string
}

export const NAV_ITEMS: readonly NavItem[] = [
  { to: '/', label: '首页', key: 'home' },
  { to: '/workbench', label: '工作台', key: 'workbench' },
  { to: '/sbox', label: 'S 盒', key: 'sbox' },
  { to: '/avalanche', label: '雪崩', key: 'avalanche' },
]

/** 首页只在完全相等时高亮，其余按前缀匹配。 */
export function isNavActive(path: string, to: string): boolean {
  if (to === '/') return path === '/'
  return path === to || path.startsWith(`${to}/`)
}
