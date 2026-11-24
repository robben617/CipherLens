<template>
  <Teleport to="body">
    <div v-if="ai.panelOpen" class="gai" data-global-ai-panel>
      <div class="gai__scrim" @click="close"></div>
      <section
        ref="panelEl"
        class="gai__panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="global-ai-title"
        tabindex="-1"
        @keydown="onKeydown"
      >
        <header class="gai__head">
          <div>
            <h2 id="global-ai-title">AI 助手 · {{ ai.pageLabel(ai.activePage) }}</h2>
            <p class="gai__context">{{ contextLine }}</p>
          </div>
          <button ref="closeEl" type="button" class="gai__close" aria-label="关闭 AI 助手" @click="close">
            ×
          </button>
        </header>

        <div class="gai__stream" data-global-ai-stream>
          <div v-if="conversation.messages.length === 0" class="gai__welcome">
            <h3 class="gai__welcome-title">可以这样问</h3>
            <div v-if="prompts.length" class="gai__prompts" aria-label="推荐问题">
              <button
                v-for="(prompt, index) in prompts"
                :key="prompt"
                type="button"
                class="gai__prompt"
                @click="ask(prompt)"
              >
                <span class="gai__no">{{ index + 1 }}</span>
                <span class="gai__prompt-text">{{ prompt }}</span>
              </button>
            </div>
          </div>
          <template v-for="message in conversation.messages" :key="message.id">
            <p v-if="message.role === 'user'" class="gai__user">{{ message.text }}</p>
            <div v-else class="gai__assistant">
              <p
                v-if="!message.blocks?.length && !message.tools?.length && !message.searchState && message.streaming"
                class="gai__thinking"
              >正在组织讲解…</p>
              <TutorMessage
                v-else-if="message.blocks?.length || message.tools?.length || message.searchState"
                :blocks="message.blocks ?? []"
                :tools="message.tools ?? []"
                :search-state="message.searchState"
                :search-message="message.searchMessage"
                :sources="message.sources ?? []"
                :source="message.source ?? 'local'"
                :model="message.model"
                :streaming="message.streaming"
                @action="onAction"
                @cite="() => undefined"
              />
            </div>
          </template>
          <p v-if="conversation.phase === 'error'" class="gai__error">
            {{ errorText }}<button type="button" @click="retry">重试</button>
          </p>
          <p v-if="conversation.phase === 'offline'" class="gai__error">
            后端离线，暂时只能看本地讲解。恢复后点重试。
            <button type="button" @click="retry">重试</button>
          </p>
        </div>

        <ModelStatusBar class="gai__model" />

        <div class="gai__compose">
          <textarea
            v-model="conversation.draft"
            rows="2"
            aria-label="向 AI 提问"
            placeholder="问这一页的问题…"
            :disabled="busy"
            @keydown.enter.exact.prevent="send"
          ></textarea>
          <div class="gai__actions">
            <button
              type="button"
              class="gai__web"
              :aria-pressed="conversation.webSearch"
              data-action="web-search"
              title="联网搜索（Tavily）"
              @click="toggleWebSearch"
            >
              <svg viewBox="0 0 16 16" aria-hidden="true" width="13" height="13">
                <circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" stroke-width="1.4" />
                <path
                  d="M2 8h12M8 2c2 2.2 2 9.8 0 12M8 2c-2 2.2-2 9.8 0 12"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.2"
                />
              </svg>
              联网搜索
            </button>
            <span class="gai__spacer"></span>
            <button type="button" class="gai__clear" :disabled="busy" @click="clear">清空</button>
            <button v-if="busy" type="button" class="gai__stop" @click="stop">停止</button>
            <button v-else type="button" class="gai__send" :disabled="!conversation.draft.trim()" @click="send">
              发送
            </button>
          </div>
        </div>

        <p class="gai__live sr-only" aria-live="polite" aria-atomic="true">
          {{ conversation.announcement }}
        </p>
      </section>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import TutorMessage from '../region-e/TutorMessage.vue'
import ModelStatusBar from '../shared/ModelStatusBar.vue'
import { useAiStore } from '../../stores/ai'
import { describeContext } from '../../utils/ai-context'
import { promptsFor } from '../../data/ai-prompts'
import type { TutorAction } from '../../utils/tutor-message'

const ai = useAiStore()
const router = useRouter()
const panelEl = ref<HTMLElement | null>(null)
const closeEl = ref<HTMLButtonElement | null>(null)

const conversation = computed(() => ai.conversations[ai.activePage])
const contextLine = computed(() =>
  describeContext(ai.activePage, conversation.value.context),
)
const prompts = computed(() => promptsFor(ai.activePage, conversation.value.context))
const busy = computed(
  () => conversation.value.phase === 'waiting' || conversation.value.phase === 'streaming',
)

const ERROR_TEXT: Record<string, string> = {
  timeout: '这次回答超时了，可以重试。',
  network_error: '连接不上后端，可以重试。',
  interrupted: '上次生成已中断。',
  internal_error: '讲解生成失败，可以重试。',
}

const errorText = computed(
  () => ERROR_TEXT[conversation.value.errorCode] ?? '回答失败，可以重试。',
)

function send(): void {
  const text = conversation.value.draft.trim()
  if (!text || busy.value) return
  ai.submit(ai.activePage, text)
  void nextTick(() => panelEl.value?.querySelector<HTMLTextAreaElement>('textarea')?.focus())
}

function ask(question: string): void {
  if (busy.value) return
  ai.submit(ai.activePage, question)
}

function stop(): void {
  ai.abort(ai.activePage)
}

function toggleWebSearch(): void {
  ai.setWebSearch(!conversation.value.webSearch)
}

function retry(): void {
  ai.retry(ai.activePage)
}

function clear(): void {
  ai.clear(ai.activePage)
}

function close(): void {
  ai.closePanel()
  void nextTick(() => document.querySelector<HTMLElement>('.ai-fab')?.focus())
}

function onAction(action: TutorAction): void {
  if (action.kind === 'open-workbench') {
    void router.push({ path: '/workbench', query: { ai: '1' } })
  } else if (action.kind === 'open-sbox') {
    void router.push({ path: '/sbox', query: { b: `0x${action.value.toString(16).padStart(2, '0')}` } })
  }
}

function focusables(): HTMLElement[] {
  if (!panelEl.value) return []
  return Array.from(
    panelEl.value.querySelectorAll<HTMLElement>(
      'button, textarea, [href], input, select, [tabindex]:not([tabindex="-1"])',
    ),
  ).filter((element) => !element.hasAttribute('disabled'))
}

function onKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape') {
    event.preventDefault()
    event.stopPropagation()
    close()
    return
  }
  if (event.key !== 'Tab') return
  const items = focusables()
  if (!items.length) return
  const index = items.indexOf(document.activeElement as HTMLElement)
  if (event.shiftKey) {
    if (index <= 0) {
      event.preventDefault()
      items[items.length - 1]?.focus()
    }
  } else if (index === items.length - 1 || index === -1) {
    event.preventDefault()
    items[0]?.focus()
  }
}

function onGlobalKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape' && ai.panelOpen) {
    event.preventDefault()
    close()
  }
}

watch(
  () => ai.panelOpen,
  async (open) => {
    document.body.style.overflow = open ? 'hidden' : ''
    if (!open) return
    await nextTick()
    closeEl.value?.focus()
  },
  { immediate: true },
)

onMounted(() => {
  window.addEventListener('keydown', onGlobalKeydown, true)
  if (ai.panelOpen) closeEl.value?.focus()
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onGlobalKeydown, true)
  document.body.style.overflow = ''
})
</script>

<style scoped>
.gai {
  position: fixed;
  inset: 0;
  z-index: 65;
}

.gai__scrim {
  position: fixed;
  inset: 0;
  z-index: 70;
  background: rgb(24 28 33 / 0.12);
}

.gai__panel {
  position: fixed;
  top: var(--nav-h);
  right: 0;
  bottom: 0;
  z-index: 71;
  display: flex;
  flex-direction: column;
  width: min(380px, 100vw);
  border-left: var(--rule-region-w) solid var(--line-hairline);
  background: var(--paper-0);
  box-shadow: -10px 0 30px rgb(0 0 0 / 0.12);
}

.gai__head {
  display: flex;
  align-items: flex-start;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  border-bottom: var(--rule-region-w) solid var(--line-hairline);
}

.gai__head h2 {
  margin: 0;
  font-size: var(--fs-body);
  color: var(--ink-1);
}

.gai__context {
  margin: 3px 0 0;
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-3);
  overflow-wrap: anywhere;
}

.gai__close {
  flex: 0 0 28px;
  width: 28px;
  height: 28px;
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  background: transparent;
  font-size: 18px;
  color: var(--ink-2);
  cursor: pointer;
}

.gai__stream {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: var(--sp-3) var(--sp-4);
}

.gai__empty,
.gai__thinking {
  margin: 0;
  font-size: var(--fs-ui);
  line-height: var(--lh-body);
  color: var(--ink-3);
}

.gai__welcome {
  display: grid;
  gap: var(--sp-2);
  padding: var(--sp-3) 0 var(--sp-2);
}

.gai__welcome-title {
  margin: 0;
  font-family: var(--font-ui);
  font-size: var(--fs-label);
  font-weight: 600;
  letter-spacing: var(--ls-label);
  color: var(--ink-3);
}

.gai__user {
  max-width: 82%;
  margin: 0 0 var(--sp-2) auto;
  padding: 8px 12px;
  border-radius: 12px 12px 2px 12px;
  background: var(--accent-soft);
  font-size: var(--fs-ui);
  line-height: var(--lh-snug);
  color: var(--ink-1);
  overflow-wrap: anywhere;
}

.gai__assistant {
  margin-bottom: var(--sp-3);
}

.gai__error {
  margin: var(--sp-2) 0;
  font-size: var(--fs-ui);
  color: var(--st-error);
}

.gai__error button {
  margin-left: var(--sp-2);
  border: 0;
  background: transparent;
  color: var(--accent-strong);
  cursor: pointer;
}

.gai__prompts {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: var(--sp-1);
  margin-top: var(--sp-1);
}

.gai__prompt {
  display: flex;
  gap: var(--sp-2);
  align-items: flex-start;
  padding: 8px 10px;
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: 10px;
  background: var(--paper-1);
  font-family: var(--font-ui);
  font-size: var(--fs-label);
  line-height: 1.45;
  color: var(--ink-2);
  text-align: left;
  cursor: pointer;
}

.gai__prompt:hover {
  border-color: var(--accent);
  color: var(--ink-1);
}

.gai__prompt-text {
  min-width: 0;
}

.gai__no {
  flex: none;
  display: inline-grid;
  place-items: center;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--paper-0);
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--ink-3);
}

/* 状态行的根节点同时带着 .msb（有自己的 padding），这里用更高特异性对齐到面板内容 */
.gai__panel .gai__model {
  padding-left: var(--sp-4);
  padding-right: var(--sp-4);
}

.gai__panel .gai__model :deep(.msb__dot) {
  display: none;
}

.gai__compose {
  margin: var(--sp-2) var(--sp-4) calc(var(--sp-3) + env(safe-area-inset-bottom));
  padding: 8px;
  border: var(--rule-region-w) solid var(--line-default);
  border-radius: 14px;
  background: var(--paper-0);
  box-shadow: var(--shadow-float);
}

.gai__compose textarea {
  width: 100%;
  box-sizing: border-box;
  min-height: 52px;
  resize: none;
  padding: 6px 8px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  font-family: var(--font-ui);
  font-size: 16px;
  line-height: var(--lh-body);
  color: var(--ink-1);
}

.gai__compose textarea:focus {
  outline: none;
}

.gai__actions {
  display: flex;
  align-items: center;
  gap: var(--sp-1);
  margin-top: 4px;
  padding: 0 2px;
}

.gai__spacer {
  flex: 1;
}

.gai__web {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 26px;
  padding: 0 10px;
  border: var(--rule-region-w) solid var(--line-default);
  border-radius: 999px;
  background: transparent;
  font-size: var(--fs-micro);
  color: var(--ink-3);
  cursor: pointer;
}

.gai__web[aria-pressed='true'] {
  border-color: var(--accent);
  background: var(--accent-soft);
  color: var(--accent-strong);
}

.gai__send,
.gai__stop {
  min-width: 64px;
  height: 32px;
  border: 0;
  border-radius: 16px;
  background: var(--accent);
  color: var(--paper-0);
  font-family: var(--font-ui);
  font-size: var(--fs-label);
  cursor: pointer;
}

.gai__stop {
  background: var(--surface-inset);
  color: var(--ink-2);
}

.gai__send:disabled {
  background: var(--surface-inset);
  color: var(--ink-3);
  cursor: default;
}

.gai__clear {
  border: 0;
  background: transparent;
  font-size: var(--fs-micro);
  color: var(--ink-3);
  cursor: pointer;
}

@media (max-width: 48rem) {
  .gai__panel {
    top: 0;
    width: 100vw;
    max-width: 100vw;
  }

  .gai__head,
  .gai__stream,
  .gai__prompts,
  .gai__compose {
    padding-left: var(--sp-3);
    padding-right: var(--sp-3);
  }
}
</style>