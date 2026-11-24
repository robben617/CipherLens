import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import {
  clearModelConfig,
  readModelConfig,
  saveModelConfig,
  toRequestPayload,
  type ModelConfig,
} from '../utils/model-config'

/** 全站唯一的一份本地模型配置状态；弹窗与各 AI 面板共用。 */
export const useModelConfigStore = defineStore('modelConfig', () => {
  const config = ref<ModelConfig | null>(readModelConfig())
  const dialogOpen = ref(false)

  const configured = computed(() => config.value !== null)
  const label = computed(() => config.value?.displayName ?? '')

  function openDialog(): void {
    dialogOpen.value = true
  }

  function closeDialog(): void {
    dialogOpen.value = false
  }

  function refresh(): void {
    config.value = readModelConfig()
  }

  function save(next: ModelConfig): boolean {
    if (!saveModelConfig(next)) return false
    refresh()
    dialogOpen.value = false
    return true
  }

  function clear(): void {
    clearModelConfig()
    config.value = null
    dialogOpen.value = false
  }

  /** 请求时附带；没有配置就完全不传，后端继续走本地讲解。 */
  function requestPayload(): Record<string, string> | null {
    return config.value ? toRequestPayload(config.value) : null
  }

  return {
    config,
    dialogOpen,
    configured,
    label,
    openDialog,
    closeDialog,
    refresh,
    save,
    clear,
    requestPayload,
  }
})