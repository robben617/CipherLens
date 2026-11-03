import { defineStore } from 'pinia'
import { ref } from 'vue'

export type ActiveChannel = 'idle' | 'tutor'

export const useUiStore = defineStore('ui', () => {
  const activeChannel = ref<ActiveChannel>('idle')

  function setChannel(channel: ActiveChannel): void {
    activeChannel.value = channel
  }

  return { activeChannel, setChannel }
})