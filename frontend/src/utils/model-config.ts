/**
 * 本地模型配置：只写入浏览器 localStorage，不上传、不落库。
 * 这里只负责校验与存取；表单与网络请求分别见 ModelConfigDialog 与 store。
 */

export type ProviderKey = 'openai' | 'deepseek' | 'moonshot' | 'custom'

export interface ProviderPreset {
  key: ProviderKey
  label: string
  baseUrl: string
  models: readonly string[]
  keyUrl: string
}

export interface ModelConfig {
  provider: ProviderKey
  baseUrl: string
  apiKey: string
  model: string
  displayName: string
}

export interface ConfigErrors {
  provider?: string
  baseUrl?: string
  apiKey?: string
  model?: string
  displayName?: string
}

export interface KeyValueStore {
  getItem: (key: string) => string | null
  setItem: (key: string, value: string) => void
  removeItem: (key: string) => void
}

export const MODEL_CONFIG_KEY = 'cl:model-config'
export const MAX_MODEL_LENGTH = 128
export const MAX_NAME_LENGTH = 64
export const MAX_URL_LENGTH = 500

const CUSTOM_PRESET: ProviderPreset = {
  key: 'custom',
  label: '自定义',
  baseUrl: '',
  models: [],
  keyUrl: '',
}

/** 预设只是快捷方式，不构成对服务商可用性的承诺；自定义页签可填任意 OpenAI 兼容端点。 */
export const PROVIDERS: readonly ProviderPreset[] = [
  {
    key: 'openai',
    label: 'OpenAI',
    baseUrl: 'https://api.openai.com/v1',
    models: ['gpt-4o-mini', 'gpt-4o'],
    keyUrl: 'https://platform.openai.com/api-keys',
  },
  {
    key: 'deepseek',
    label: 'DeepSeek',
    baseUrl: 'https://api.deepseek.com/v1',
    models: ['deepseek-chat', 'deepseek-reasoner'],
    keyUrl: 'https://platform.deepseek.com/api_keys',
  },
  {
    key: 'moonshot',
    label: 'Moonshot',
    baseUrl: 'https://api.moonshot.cn/v1',
    models: ['moonshot-v1-8k', 'moonshot-v1-32k'],
    keyUrl: 'https://platform.moonshot.cn/console/api-keys',
  },
  CUSTOM_PRESET,
]

export function providerPreset(key: ProviderKey): ProviderPreset {
  return PROVIDERS.find((item) => item.key === key) ?? CUSTOM_PRESET
}

/** 去掉尾部斜杠：拼接 /chat/completions 时不会出现双斜杠。 */
export function normalizeBaseUrl(raw: string): string {
  return raw.trim().replace(/\/+$/, '')
}

export function isValidBaseUrl(url: string): boolean {
  if (!url || url.length > MAX_URL_LENGTH) return false
  if (!/^https?:\/\//i.test(url)) return false
  try {
    const parsed = new URL(url)
    return Boolean(parsed.hostname)
  } catch {
    return false
  }
}

/** 掩码只用于回显，不用于请求。 */
export function maskApiKey(key: string): string {
  const trimmed = key.trim()
  if (!trimmed) return ''
  if (trimmed.length <= 4) return '•'.repeat(trimmed.length)
  return `••••••${trimmed.slice(-4)}`
}

function asText(value: unknown): string {
  return typeof value === 'string' ? value.trim() : ''
}

/**
 * 保存与读取共用的校验。
 * provider 不在预设里时归为自定义，避免以后调整预设导致旧配置直接失效。
 */
export function validateModelConfig(
  candidate: Partial<ModelConfig> | null | undefined,
): { config: ModelConfig | null; errors: ConfigErrors } {
  const errors: ConfigErrors = {}
  const source = candidate ?? {}

  const providerValue = asText(source.provider)
  const provider = PROVIDERS.some((item) => item.key === providerValue)
    ? (providerValue as ProviderKey)
    : 'custom'

  const baseUrl = normalizeBaseUrl(asText(source.baseUrl))
  if (!isValidBaseUrl(baseUrl)) {
    errors.baseUrl = '请填写以 http:// 或 https:// 开头的模型地址'
  }

  const apiKey = asText(source.apiKey)
  if (!apiKey) errors.apiKey = '请填写 API Key'
  else if (apiKey.length > MAX_URL_LENGTH) errors.apiKey = 'API Key 过长'

  const model = asText(source.model)
  if (!model) errors.model = '请填写模型 ID'
  else if (model.length > MAX_MODEL_LENGTH) errors.model = `模型 ID 最多 ${MAX_MODEL_LENGTH} 个字符`

  const rawName = asText(source.displayName)
  const displayName = rawName || model
  if (displayName.length > MAX_NAME_LENGTH) {
    errors.displayName = `展示名称最多 ${MAX_NAME_LENGTH} 个字符`
  }

  if (Object.keys(errors).length > 0) return { config: null, errors }
  return { config: { provider, baseUrl, apiKey, model, displayName }, errors }
}

function browserStore(): KeyValueStore | null {
  try {
    if (typeof window === 'undefined' || !window.localStorage) return null
    return window.localStorage
  } catch {
    // 隐私模式等场景禁用 localStorage 时，配置功能降级为「本次不可用」
    return null
  }
}

export function readModelConfig(store?: KeyValueStore | null): ModelConfig | null {
  const target = store === undefined ? browserStore() : store
  if (!target) return null
  try {
    const raw = target.getItem(MODEL_CONFIG_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as Partial<ModelConfig>
    return validateModelConfig(parsed).config
  } catch {
    return null
  }
}

export function saveModelConfig(
  config: ModelConfig,
  store?: KeyValueStore | null,
): boolean {
  const target = store === undefined ? browserStore() : store
  if (!target) return false
  const validated = validateModelConfig(config)
  if (!validated.config) return false
  try {
    target.setItem(MODEL_CONFIG_KEY, JSON.stringify(validated.config))
    return true
  } catch {
    return false
  }
}

export function clearModelConfig(store?: KeyValueStore | null): void {
  const target = store === undefined ? browserStore() : store
  if (!target) return
  try {
    target.removeItem(MODEL_CONFIG_KEY)
  } catch {
    // 清不掉也不影响当前页面，忽略
  }
}

/** 随请求发给本地后端的字段；后端只用本次请求，不保存。 */
export function toRequestPayload(config: ModelConfig): Record<string, string> {
  return {
    provider: config.provider,
    base_url: config.baseUrl,
    api_key: config.apiKey,
    model: config.model,
    display_name: config.displayName,
  }
}