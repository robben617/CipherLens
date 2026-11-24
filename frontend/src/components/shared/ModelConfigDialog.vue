<template>
  <Teleport to="body">
    <div v-if="modelStore.dialogOpen" class="mcd">
      <div class="mcd__scrim" @click="close"></div>
      <section
        ref="panelEl"
        class="mcd__panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="mcd-title"
        tabindex="-1"
        @keydown.esc.stop.prevent="close"
        @keydown.enter.exact.prevent="submit"
      >
        <header class="mcd__head">
          <div>
            <h2 id="mcd-title">添加模型</h2>
            <p class="mcd__sub">接入你自己的 OpenAI 兼容模型，用来讲解当前页面。</p>
          </div>
          <button type="button" class="mcd__close" aria-label="关闭模型配置" @click="close">×</button>
        </header>

        <div class="mcd__body">
          <div class="mcd__tabs" role="tablist" aria-label="配置方式">
            <button
              type="button"
              role="tab"
              class="mcd__tab"
              :aria-selected="tab === 'preset'"
              data-mcd-tab="preset"
              @click="switchTab('preset')"
            >
              模型提供商
            </button>
            <button
              type="button"
              role="tab"
              class="mcd__tab"
              :aria-selected="tab === 'custom'"
              data-mcd-tab="custom"
              @click="switchTab('custom')"
            >
              自定义配置
            </button>
          </div>

          <div v-if="tab === 'preset'" class="mcd__field">
            <label class="mcd__label" for="mcd-provider">模型提供商 <span class="mcd__req">*</span></label>
            <select
              id="mcd-provider"
              v-model="provider"
              class="mcd__input"
              data-mcd-provider
              @change="onProviderChange"
            >
              <option v-for="item in presetProviders" :key="item.key" :value="item.key">
                {{ item.label }}
              </option>
            </select>
          </div>

          <div v-if="tab === 'custom'" class="mcd__field">
            <label class="mcd__label">API 格式</label>
            <p class="mcd__static">OpenAI Chat Completions</p>
          </div>

          <div v-if="tab === 'custom'" class="mcd__field">
            <label class="mcd__label" for="mcd-base">模型 URL <span class="mcd__req">*</span></label>
            <input
              id="mcd-base"
              v-model="baseUrl"
              class="mcd__input"
              data-mcd-base-url
              placeholder="https://example.com/v1"
              spellcheck="false"
              autocomplete="off"
            />
            <p v-if="errors.baseUrl" class="mcd__error">{{ errors.baseUrl }}</p>
            <p v-else class="mcd__hint">不要以斜杠结尾；系统会自动补 /chat/completions 路径。</p>
          </div>

          <div class="mcd__field">
            <label class="mcd__label" for="mcd-model">模型 ID <span class="mcd__req">*</span></label>
            <input
              id="mcd-model"
              v-model="model"
              class="mcd__input"
              data-mcd-model
              :list="tab === 'preset' ? 'mcd-model-options' : undefined"
              placeholder="例如：deepseek-chat"
              spellcheck="false"
              autocomplete="off"
              :maxlength="MAX_MODEL_LENGTH"
            />
            <datalist v-if="tab === 'preset'" id="mcd-model-options">
              <option v-for="name in currentPreset.models" :key="name" :value="name"></option>
            </datalist>
            <p v-if="errors.model" class="mcd__error">{{ errors.model }}</p>
          </div>

          <div class="mcd__field">
            <div class="mcd__labelrow">
              <label class="mcd__label" for="mcd-name">模型展示名称</label>
              <span class="mcd__count">{{ displayName.length }}/{{ MAX_NAME_LENGTH }}</span>
            </div>
            <input
              id="mcd-name"
              v-model="displayName"
              class="mcd__input"
              data-mcd-display-name
              placeholder="留空则使用模型 ID"
              :maxlength="MAX_NAME_LENGTH"
            />
            <p v-if="errors.displayName" class="mcd__error">{{ errors.displayName }}</p>
          </div>

          <div class="mcd__field">
            <div class="mcd__labelrow">
              <label class="mcd__label" for="mcd-key">API Key <span class="mcd__req">*</span></label>
              <a
                v-if="currentPreset.keyUrl"
                class="mcd__link"
                :href="currentPreset.keyUrl"
                target="_blank"
                rel="noopener noreferrer"
              >
                获取 API Key ↗
              </a>
            </div>
            <div class="mcd__keyrow">
              <input
                id="mcd-key"
                v-model="apiKey"
                class="mcd__input"
                data-mcd-api-key
                :type="showKey ? 'text' : 'password'"
                placeholder="粘贴你的 API 密钥"
                spellcheck="false"
                autocomplete="off"
              />
              <button type="button" class="mcd__peek" @click="showKey = !showKey">
                {{ showKey ? '隐藏' : '显示' }}
              </button>
            </div>
            <p v-if="errors.apiKey" class="mcd__error">{{ errors.apiKey }}</p>
          </div>

          <div class="mcd__trust">
            <p class="mcd__trust-title">配置只保存在你的浏览器里</p>
            <ul>
              <li>存于本机 localStorage，不上传到 CipherLens 服务器，也不写入任何数据库。</li>
              <li>
                提问时，API Key 只随本次请求经本地后端转发给你填写的模型服务商；服务端不保存、不记录密钥。
              </li>
              <li>localStorage 是明文存储：请勿在公共电脑上使用；清除浏览器数据或更换设备后需要重新填写。</li>
            </ul>
          </div>

          <div class="mcd__test">
            <button
              type="button"
              class="mcd__testbtn"
              data-mcd-test
              :disabled="testing"
              @click="testConnection"
            >
              {{ testing ? '测试中…' : '连通性测试' }}
            </button>
            <span v-if="testState" class="mcd__testresult" :data-test-state="testState">
              {{ testMessage }}
            </span>
            <p class="mcd__hint">测试会真实请求一次模型，消耗少量 Token。</p>
          </div>

          <p v-if="saveError" class="mcd__error mcd__saveerror">{{ saveError }}</p>
        </div>

        <footer class="mcd__foot">
          <button
            v-if="modelStore.configured"
            type="button"
            class="mcd__danger"
            data-mcd-clear
            @click="clearSaved"
          >
            清除配置
          </button>
          <button type="button" class="mcd__ghost" @click="reset">重置</button>
          <button type="button" class="mcd__save" data-mcd-save @click="submit">保存并使用</button>
        </footer>
      </section>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useModelConfigStore } from '../../stores/model-config'
import {
  MAX_MODEL_LENGTH,
  MAX_NAME_LENGTH,
  PROVIDERS,
  normalizeBaseUrl,
  providerPreset,
  validateModelConfig,
  type ConfigErrors,
  type ModelConfig,
  type ProviderKey,
} from '../../utils/model-config'

type Tab = 'preset' | 'custom'

const modelStore = useModelConfigStore()
const panelEl = ref<HTMLElement | null>(null)

const presetProviders = computed(() => PROVIDERS.filter((item) => item.key !== 'custom'))
const tab = ref<Tab>('preset')
const provider = ref<ProviderKey>('openai')
const baseUrl = ref(PROVIDERS[0]?.baseUrl ?? '')
const apiKey = ref('')
const model = ref('')
const displayName = ref('')
const showKey = ref(false)
const errors = ref<ConfigErrors>({})
const saveError = ref('')
const testing = ref(false)
const testState = ref<'ok' | 'fail' | ''>('')
const testMessage = ref('')

const currentPreset = computed(() => providerPreset(provider.value))

function syncFromStore(): void {
  const saved = modelStore.config
  if (saved) {
    tab.value = saved.provider === 'custom' ? 'custom' : 'preset'
    provider.value = saved.provider
    baseUrl.value = saved.provider === 'custom' ? saved.baseUrl : providerPreset(saved.provider).baseUrl
    apiKey.value = saved.apiKey
    model.value = saved.model
    displayName.value = saved.displayName
  } else {
    tab.value = 'preset'
    provider.value = 'openai'
    baseUrl.value = PROVIDERS[0]?.baseUrl ?? ''
    apiKey.value = ''
    model.value = ''
    displayName.value = ''
  }
  errors.value = {}
  saveError.value = ''
  testState.value = ''
  testMessage.value = ''
  showKey.value = false
}

function customValue(): string {
  return tab.value === 'custom' ? normalizeBaseUrl(baseUrl.value) : providerPreset(provider.value).baseUrl
}

function buildCandidate(): Partial<ModelConfig> {
  return {
    provider: tab.value === 'custom' ? 'custom' : provider.value,
    baseUrl: customValue(),
    apiKey: apiKey.value,
    model: model.value,
    displayName: displayName.value,
  }
}

function switchTab(next: Tab): void {
  if (tab.value === next) return
  if (next === 'custom') {
    tab.value = 'custom'
    provider.value = 'custom'
    if (!baseUrl.value) baseUrl.value = PROVIDERS[0]?.baseUrl ?? ''
    return
  }
  tab.value = 'preset'
  const fallback = provider.value === 'custom' ? 'openai' : provider.value
  provider.value = fallback
  baseUrl.value = providerPreset(fallback).baseUrl
}

function onProviderChange(): void {
  if (provider.value === 'custom') {
    switchTab('custom')
    return
  }
  baseUrl.value = providerPreset(provider.value).baseUrl
  if (!model.value) model.value = providerPreset(provider.value).models[0] ?? ''
}

function reset(): void {
  if (modelStore.config) {
    syncFromStore()
    return
  }
  tab.value = 'preset'
  provider.value = 'openai'
  baseUrl.value = PROVIDERS[0]?.baseUrl ?? ''
  apiKey.value = ''
  model.value = ''
  displayName.value = ''
  errors.value = {}
  saveError.value = ''
  testState.value = ''
  testMessage.value = ''
}

function submit(): void {
  const result = validateModelConfig(buildCandidate())
  errors.value = result.errors
  saveError.value = ''
  if (!result.config) return
  if (!modelStore.save(result.config)) {
    saveError.value = '浏览器没有允许写入本地存储，请检查隐私模式或站点存储权限。'
    return
  }
  modelStore.closeDialog()
}

function clearSaved(): void {
  modelStore.clear()
  syncFromStore()
}

async function testConnection(): Promise<void> {
  const result = validateModelConfig(buildCandidate())
  errors.value = result.errors
  if (!result.config || !result.config.apiKey) return
  testing.value = true
  testState.value = ''
  testMessage.value = ''
  try {
    const response = await fetch('/api/ai/model-test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        base_url: result.config.baseUrl,
        api_key: result.config.apiKey,
        model: result.config.model,
      }),
    })
    const data = (await response.json().catch(() => ({}))) as {
      ok?: boolean
      message?: string
      latency_ms?: number
    }
    if (response.ok && data.ok) {
      testState.value = 'ok'
      testMessage.value = `连接成功${typeof data.latency_ms === 'number' ? ` · ${data.latency_ms}ms` : ''}`
    } else {
      testState.value = 'fail'
      testMessage.value = data.message || `连接失败（HTTP ${response.status}）`
    }
  } catch {
    testState.value = 'fail'
    testMessage.value = '连接不上本地后端，请确认服务已启动。'
  } finally {
    testing.value = false
  }
}

function close(): void {
  modelStore.closeDialog()
}

watch(
  () => modelStore.dialogOpen,
  async (open) => {
    if (!open) return
    syncFromStore()
    await nextTick()
    panelEl.value?.querySelector<HTMLElement>('select, input')?.focus()
  },
)

function onGlobalKey(event: KeyboardEvent): void {
  if (!modelStore.dialogOpen) return
  if (event.key !== 'Escape') return
  event.preventDefault()
  event.stopPropagation()
  close()
}

onMounted(() => window.addEventListener('keydown', onGlobalKey, true))
onBeforeUnmount(() => window.removeEventListener('keydown', onGlobalKey, true))
</script>

<style scoped>
.mcd {
  position: fixed;
  inset: 0;
  z-index: 90;
}

.mcd__scrim {
  position: fixed;
  inset: 0;
  background: rgb(24 28 33 / 0.44);
}

.mcd__panel {
  position: fixed;
  top: 50%;
  left: 50%;
  z-index: 91;
  display: flex;
  flex-direction: column;
  width: min(560px, calc(100vw - 32px));
  max-height: min(760px, calc(100dvh - 48px));
  border: var(--rule-region-w) solid var(--line-strong);
  border-radius: var(--r-float);
  background: var(--paper-0);
  box-shadow: 0 18px 48px rgb(0 0 0 / 0.22);
  transform: translate(-50%, -50%);
}

.mcd__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--sp-3);
  padding: var(--sp-4);
  border-bottom: var(--rule-region-w) solid var(--line-hairline);
}

.mcd__head h2 {
  margin: 0;
  font-family: var(--font-display);
  font-size: var(--fs-body);
  font-weight: 600;
  color: var(--ink-1);
}

.mcd__sub {
  margin: var(--sp-1) 0 0;
  font-size: var(--fs-micro);
  line-height: 1.6;
  color: var(--ink-3);
}

.mcd__close {
  flex: 0 0 28px;
  width: 28px;
  height: 28px;
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  background: transparent;
  font-size: 18px;
  line-height: 1;
  color: var(--ink-2);
  cursor: pointer;
}

.mcd__close:hover {
  border-color: var(--accent);
  color: var(--accent-strong);
}

.mcd__body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: var(--sp-4);
}

.mcd__tabs {
  display: flex;
  gap: 2px;
  margin-bottom: var(--sp-4);
  padding: 2px;
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  background: var(--paper-1);
}

.mcd__tab {
  flex: 1;
  height: 30px;
  border: 0;
  border-radius: 1px;
  background: transparent;
  font-family: var(--font-ui);
  font-size: var(--fs-micro);
  color: var(--ink-2);
  cursor: pointer;
}

.mcd__tab[aria-selected='true'] {
  background: var(--paper-0);
  color: var(--ink-1);
  font-weight: 600;
  box-shadow: 0 0 0 1px var(--line-hairline);
}

.mcd__field {
  margin-bottom: var(--sp-3);
}

.mcd__labelrow {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--sp-2);
}

.mcd__label {
  display: inline-block;
  margin-bottom: 5px;
  font-size: var(--fs-micro);
  color: var(--ink-2);
}

.mcd__req {
  color: var(--st-error);
}

.mcd__count {
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

.mcd__static {
  margin: 0;
  padding: 7px 10px;
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  background: var(--paper-1);
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-2);
}

.mcd__input {
  width: 100%;
  box-sizing: border-box;
  height: 34px;
  padding: 0 10px;
  border: var(--rule-region-w) solid var(--line-default);
  border-radius: var(--r-control);
  background: var(--paper-0);
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-1);
}

select.mcd__input {
  font-family: var(--font-ui);
}

.mcd__input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-ring);
}

.mcd__keyrow {
  display: flex;
  gap: var(--sp-2);
}

.mcd__peek {
  flex: 0 0 auto;
  height: 34px;
  padding: 0 10px;
  border: var(--rule-region-w) solid var(--line-default);
  border-radius: var(--r-control);
  background: var(--paper-1);
  font-size: var(--fs-micro);
  color: var(--ink-2);
  cursor: pointer;
}

.mcd__link {
  font-size: var(--fs-micro);
  color: var(--accent-strong);
  text-decoration: none;
  border-bottom: var(--rule-region-w) solid var(--line-default);
}

.mcd__hint {
  margin: 5px 0 0;
  font-size: var(--fs-micro);
  line-height: 1.6;
  color: var(--ink-3);
}

.mcd__error {
  margin: 5px 0 0;
  font-size: var(--fs-micro);
  color: var(--st-error);
}

.mcd__saveerror {
  margin-top: var(--sp-2);
}

.mcd__trust {
  margin: var(--sp-4) 0 var(--sp-3);
  padding: var(--sp-3);
  border: var(--rule-region-w) dashed var(--line-default);
  border-radius: var(--r-control);
  background: var(--paper-1);
}

.mcd__trust-title {
  margin: 0 0 6px;
  font-size: var(--fs-micro);
  font-weight: 600;
  color: var(--ink-1);
}

.mcd__trust ul {
  margin: 0;
  padding-left: 1.1em;
  display: grid;
  gap: 4px;
  font-size: var(--fs-micro);
  line-height: 1.65;
  color: var(--ink-2);
}

.mcd__test {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--sp-2);
  padding-top: var(--sp-1);
}

.mcd__testbtn {
  height: 28px;
  padding: 0 10px;
  border: var(--rule-region-w) solid var(--line-default);
  border-radius: var(--r-control);
  background: transparent;
  font-size: var(--fs-micro);
  color: var(--ink-2);
  cursor: pointer;
}

.mcd__testbtn:disabled {
  color: var(--ink-3);
  cursor: default;
}

.mcd__testresult {
  font-size: var(--fs-micro);
  color: var(--ink-2);
}

.mcd__testresult[data-test-state='ok'] {
  color: var(--accent-strong);
}

.mcd__testresult[data-test-state='fail'] {
  color: var(--st-error);
}

.mcd__foot {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-3) var(--sp-4);
  border-top: var(--rule-region-w) solid var(--line-hairline);
}

.mcd__foot button {
  height: 32px;
  padding: 0 var(--sp-3);
  border-radius: var(--r-control);
  font-size: var(--fs-micro);
  cursor: pointer;
}

.mcd__danger {
  margin-right: auto;
  border: var(--rule-region-w) solid var(--line-hairline);
  background: transparent;
  color: var(--st-error);
}

.mcd__ghost {
  border: var(--rule-region-w) solid var(--line-default);
  background: transparent;
  color: var(--ink-2);
}

.mcd__save {
  border: var(--rule-region-w) solid var(--accent);
  background: var(--step-sub-tint);
  color: var(--step-sub-ink);
  font-weight: 600;
}

.mcd__save:hover {
  border-color: var(--accent-strong);
}

@media (max-width: 480px) {
  .mcd__panel {
    top: 0;
    left: 0;
    width: 100vw;
    max-height: 100dvh;
    height: 100dvh;
    border: 0;
    border-radius: 0;
    transform: none;
  }
}
</style>