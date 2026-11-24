import { describe, expect, it } from 'vitest'
import {
  readWebSearchEnabled,
  safeSourceUrl,
  saveWebSearchEnabled,
  sourceLabel,
  type SearchSource,
} from './web-search'

describe('web-search', () => {
  it('没有 localStorage 时开关关闭且写入不抛错', () => {
    expect(readWebSearchEnabled()).toBe(false)
    expect(() => saveWebSearchEnabled(true)).not.toThrow()
  })

  it('只放行 http/https 来源链接', () => {
    expect(safeSourceUrl('https://example.com/a')).toBe('https://example.com/a')
    expect(safeSourceUrl('http://example.com')).toBe('http://example.com/')
    expect(safeSourceUrl('javascript:alert(1)')).toBeNull()
    expect(safeSourceUrl('data:text/html,x')).toBeNull()
    expect(safeSourceUrl('not a url')).toBeNull()
  })

  it('来源标签优先用域名', () => {
    const source: SearchSource = {
      title: 'FIPS 197',
      url: 'https://nvlpubs.nist.gov/fips197.pdf',
      domain: 'nvlpubs.nist.gov',
    }
    expect(sourceLabel(source)).toBe('nvlpubs.nist.gov')
    expect(sourceLabel({ ...source, domain: '' })).toBe('FIPS 197')
  })
})