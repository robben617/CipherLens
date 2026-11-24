import { describe, expect, it } from 'vitest'
import {
  MODEL_CONFIG_KEY,
  clearModelConfig,
  isValidBaseUrl,
  maskApiKey,
  normalizeBaseUrl,
  readModelConfig,
  saveModelConfig,
  toRequestPayload,
  validateModelConfig,
  type KeyValueStore,
  type ModelConfig,
} from './model-config'

function memoryStore(seed: Record<string, string> = {}): KeyValueStore & { data: Record<string, string> } {
  const data: Record<string, string> = { ...seed }
  return {
    data,
    getItem: (key) => (key in data ? data[key] ?? null : null),
    setItem: (key, value) => {
      data[key] = value
    },
    removeItem: (key) => {
      delete data[key]
    },
  }
}

const valid: ModelConfig = {
  provider: 'deepseek',
  baseUrl: 'https://api.deepseek.com/v1',
  apiKey: 'sk-test-123456',
  model: 'deepseek-chat',
  displayName: '我的 DeepSeek',
}

describe('model-config', () => {
  it('没有配置时返回 null', () => {
    expect(readModelConfig(memoryStore())).toBeNull()
  })

  it('保存后能读回来', () => {
    const store = memoryStore()
    expect(saveModelConfig(valid, store)).toBe(true)
    expect(readModelConfig(store)).toEqual(valid)
  })

  it('遇到非法 JSON 或缺失字段时返回 null，不抛错', () => {
    expect(readModelConfig(memoryStore({ [MODEL_CONFIG_KEY]: '{oops' }))).toBeNull()
    expect(readModelConfig(memoryStore({ [MODEL_CONFIG_KEY]: '{"provider":"custom"}' }))).toBeNull()
  })

  it('Base URL 去掉尾部斜杠，展示名默认取模型 ID', () => {
    const result = validateModelConfig({
      provider: 'custom',
      baseUrl: 'https://example.com/v1///',
      apiKey: ' key ',
      model: ' my-model ',
      displayName: '',
    })
    expect(result.errors).toEqual({})
    expect(result.config?.baseUrl).toBe('https://example.com/v1')
    expect(result.config?.apiKey).toBe('key')
    expect(result.config?.displayName).toBe('my-model')
  })

  it('缺少必填项时给出对应错误', () => {
    const result = validateModelConfig({ provider: 'openai', baseUrl: '', apiKey: '', model: '' })
    expect(result.config).toBeNull()
    expect(result.errors.baseUrl).toBeTruthy()
    expect(result.errors.apiKey).toBeTruthy()
    expect(result.errors.model).toBeTruthy()
  })

  it('只接受 http/https 地址', () => {
    expect(isValidBaseUrl('https://api.openai.com/v1')).toBe(true)
    expect(isValidBaseUrl('http://127.0.0.1:8099/v1')).toBe(true)
    expect(isValidBaseUrl('ftp://example.com')).toBe(false)
    expect(isValidBaseUrl('api.openai.com')).toBe(false)
    expect(normalizeBaseUrl(' https://a.test/v1/ ')).toBe('https://a.test/v1')
  })

  it('API Key 掩码只保留末四位', () => {
    expect(maskApiKey('sk-abcdefgh')).toBe('••••••efgh')
    expect(maskApiKey('ab')).toBe('••')
    expect(maskApiKey('')).toBe('')
  })

  it('清除配置后读不到', () => {
    const store = memoryStore()
    saveModelConfig(valid, store)
    clearModelConfig(store)
    expect(readModelConfig(store)).toBeNull()
  })

  it('localStorage 不可用时安全降级', () => {
    expect(readModelConfig(null)).toBeNull()
    expect(saveModelConfig(valid, null)).toBe(false)
    expect(() => clearModelConfig(null)).not.toThrow()
  })

  it('请求体只带白名单字段', () => {
    expect(toRequestPayload(valid)).toEqual({
      provider: 'deepseek',
      base_url: 'https://api.deepseek.com/v1',
      api_key: 'sk-test-123456',
      model: 'deepseek-chat',
      display_name: '我的 DeepSeek',
    })
  })
})