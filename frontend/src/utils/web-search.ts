export interface SearchSource {
  title: string
  url: string
  domain: string
}

export const WEB_SEARCH_KEY = 'cl:web-search'

export function readWebSearchEnabled(): boolean {
  try {
    if (typeof localStorage === 'undefined') return false
    return localStorage.getItem(WEB_SEARCH_KEY) === '1'
  } catch {
    return false
  }
}

export function saveWebSearchEnabled(enabled: boolean): void {
  try {
    localStorage.setItem(WEB_SEARCH_KEY, enabled ? '1' : '0')
  } catch {
    // 隐私模式禁用存储时，开关只在当前会话生效
  }
}

/** 只允许 http/https，防止搜索结果显示 javascript: 链接。 */
export function safeSourceUrl(url: string): string | null {
  try {
    const parsed = new URL(url)
    if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') return null
    return parsed.toString()
  } catch {
    return null
  }
}

export function sourceLabel(source: SearchSource): string {
  return source.domain || source.title
}