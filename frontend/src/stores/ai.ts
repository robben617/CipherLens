import { defineStore } from 'pinia'
import { reactive, ref } from 'vue'
import { startAiStream, type AiStream } from '../utils/ai-stream'
import {
  toWireContext,
  type ApiPageContext,
  type PageKey,
} from '../utils/ai-context'
import {
  appendBlock,
  appendToken,
  type TutorBlock,
} from '../utils/tutor-message'
import { getClientId } from '../utils/clientId'
import { applyToolEnd, applyToolResult, pushToolStart, type ToolTrace } from '../utils/tool-trace'
import { useModelConfigStore } from './model-config'

type AiPhase =
  | 'idle'
  | 'waiting'
  | 'streaming'
  | 'done'
  | 'error'
  | 'offline'

interface AiMessage {
  id: string
  role: 'user' | 'assistant'
  text?: string
  blocks?: TutorBlock[]
  source?: 'local' | 'llm'
  model?: string | null
  streaming?: boolean
  tools?: ToolTrace[]
}

export interface AiConversation {
  page: PageKey
  conversationId: string
  messages: AiMessage[]
  draft: string
  phase: AiPhase
  errorCode: string
  errorMessage: string
  degraded: boolean
  context: ApiPageContext | null
  announcement: string
}

const PAGE_LABEL: Record<PageKey, string> = {
  home: '首页',
  workbench: '工作台',
  sbox: 'S 盒',
  avalanche: '雪崩',
}

function initialContext(page: PageKey): ApiPageContext | null {
  if (page === 'home') return { page: 'home' }
  if (page === 'workbench') return null
  return { page }
}

function newConversation(page: PageKey): AiConversation {
  return {
    page,
    conversationId: `conv_${page}_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`,
    messages: [],
    draft: '',
    phase: 'idle',
    errorCode: '',
    errorMessage: '',
    degraded: false,
    context: initialContext(page),
    announcement: '',
  }
}

export const useAiStore = defineStore('ai', () => {
  const conversations = reactive<Record<PageKey, AiConversation>>({
    home: newConversation('home'),
    workbench: newConversation('workbench'),
    sbox: newConversation('sbox'),
    avalanche: newConversation('avalanche'),
  })
  const panelOpen = ref(false)
  const activePage = ref<PageKey>('home')
  const activeAbort = new Map<PageKey, AiStream>()
  const modelStore = useModelConfigStore()

  function pageLabel(page: PageKey): string {
    return PAGE_LABEL[page]
  }

  function openPanel(page: PageKey): void {
    if (page === 'workbench') return
    activePage.value = page
    panelOpen.value = true
    conversations[page].announcement = ''
  }

  function closePanel(): void {
    panelOpen.value = false
  }

  function setContext(page: PageKey, context: unknown): void {
    const wire = toWireContext(
      page as 'home' | 'sbox' | 'avalanche' | 'workbench',
      (context ?? {}) as Record<string, unknown>,
    )
    if (wire) conversations[page].context = wire
  }

  function abort(page: PageKey, reason = 'interrupted'): void {
    const stream = activeAbort.get(page)
    if (!stream) return
    stream.abort(reason)
    activeAbort.delete(page)
    const conversation = conversations[page]
    conversation.phase = 'error'
    conversation.errorCode = 'interrupted'
    conversation.errorMessage = '上次生成已中断'
    conversation.announcement = '上次生成已中断'
  }

  function switchPage(next: PageKey): void {
    if (activePage.value !== next) abort(activePage.value)
    activePage.value = next
    panelOpen.value = false
  }

  function submit(page: PageKey, rawQuestion: string): void {
    if (page === 'workbench') return
    const question = rawQuestion.normalize('NFKC').trim()
    if (!question) return
    abort(page, 'replaced')

    const conversation = conversations[page]
    const assistant: AiMessage = {
      id: `a_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`,
      role: 'assistant',
      blocks: [],
      source: 'local',
      model: null,
      streaming: true,
      tools: [],
    }
    conversation.messages.push(
      { id: `u_${Date.now().toString(36)}`, role: 'user', text: question },
      assistant,
    )
    conversation.phase = 'waiting'
    conversation.errorCode = ''
    conversation.errorMessage = ''
    conversation.degraded = false
    conversation.announcement = ''
    conversation.draft = ''

    const wire = conversation.context ?? { page }
    const llm = modelStore.requestPayload()
    const stream = startAiStream({
      url: '/api/ai/ask',
      payload: {
        page: conversation.page,
        question,
        context: wire,
        conversation_id: conversation.conversationId,
        client_id: getClientId(),
        ...(llm ? { llm } : {}),
      },
      tokenTimeoutMs: 30000,
      handlers: {
        onMeta: (meta) => {
          conversation.phase = 'streaming'
          assistant.source = meta.source === 'llm' ? 'llm' : 'local'
          assistant.model = typeof meta.model === 'string' ? meta.model : null
          if (meta.cache === true) {
            conversation.announcement = '缓存命中'
          }
        },
        onBlock: (block) => {
          if (!assistant.blocks) assistant.blocks = []
          appendBlock(assistant.blocks, block)
        },
        onToken: (text, payload) => {
          if (!assistant.blocks) assistant.blocks = []
          appendToken(assistant.blocks, text, payload?.item === true)
          conversation.phase = 'streaming'
        },
        onToolStart: (data) => {
          if (!assistant.tools) assistant.tools = []
          pushToolStart(assistant.tools, data)
        },
        onToolResult: (data) => {
          if (!assistant.tools) assistant.tools = []
          applyToolResult(assistant.tools, data)
        },
        onToolEnd: (data) => {
          if (!assistant.tools) assistant.tools = []
          applyToolEnd(assistant.tools, data)
        },
        onDone: () => {
          assistant.streaming = false
          conversation.phase = 'done'
          conversation.announcement = '回答完成'
          activeAbort.delete(page)
        },
        onError: (code, message) => {
          assistant.streaming = false
          activeAbort.delete(page)
          if (code === 'llm_unavailable' && assistant.blocks?.length) {
            conversation.phase = 'done'
            conversation.degraded = true
            conversation.announcement = '已切换本地讲解'
            return
          }
          conversation.phase = code === 'network_error' ? 'offline' : 'error'
          conversation.errorCode = code
          conversation.errorMessage = message
          conversation.announcement =
            conversation.phase === 'offline'
              ? '后端离线，先看本地讲解'
              : '回答失败，可重试'
        },
      },
    })
    activeAbort.set(page, stream)
  }

  function clear(page: PageKey): void {
    abort(page, 'cleared')
    conversations[page] = newConversation(page)
  }

  function retry(page: PageKey): void {
    const conversation = conversations[page]
    const lastUser = [...conversation.messages].reverse().find((message) => message.role === 'user')
    if (!lastUser?.text) return
    const lastIndex = conversation.messages.findIndex((message) => message === lastUser)
    conversation.messages.splice(lastIndex + 1)
    submit(page, lastUser.text)
  }

  return {
    conversations,
    panelOpen,
    activePage,
    pageLabel,
    openPanel,
    closePanel,
    setContext,
    abort,
    switchPage,
    submit,
    retry,
    clear,
  }
})