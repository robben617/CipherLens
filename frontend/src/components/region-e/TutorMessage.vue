<template>
  <article class="msg" :data-source="source">
    <header class="msg__src">
      <span class="msg__dot" aria-hidden="true"></span>
      <span class="msg__src-text" :title="sourceTitle">{{ sourceLabel }}</span>
      <span v-if="streaming" class="msg__live">生成中</span>
    </header>

    <template v-for="(block, index) in blocks" :key="index">
      <p v-if="block.type === 'conclusion'" class="msg__conclusion">
        {{ block.text }}<span v-if="caret(index, -1)" class="msg__caret" aria-hidden="true"></span>
      </p>

      <section v-else-if="block.type === 'why'" class="msg__section">
        <h4 class="msg__h">为什么</h4>
        <ul class="msg__list">
          <li v-for="(item, i) in block.items" :key="i">
            {{ item }}<span v-if="caret(index, i)" class="msg__caret" aria-hidden="true"></span>
          </li>
        </ul>
      </section>

      <section v-else-if="block.type === 'next'" class="msg__section">
        <h4 class="msg__h">下一步</h4>
        <p class="msg__next">
          {{ block.text }}<span v-if="caret(index, -1)" class="msg__caret" aria-hidden="true"></span>
          <button
            v-if="block.action"
            type="button"
            class="msg__act"
            data-action="tutor-goto"
            @click="emit('action', block.action)"
          >
            {{ block.action.label }} <span aria-hidden="true">→</span>
          </button>
        </p>
      </section>

      <section v-else class="msg__section">
        <h4 class="msg__h">依据</h4>
        <div class="msg__chips">
          <button
            v-for="byte in block.bytes"
            :key="byte"
            type="button"
            class="msg__chip"
            data-action="tutor-cite"
            :title="`打开第 ${byte} 格的详情`"
            :aria-label="`打开第 ${byte} 格的详情`"
            @click="onCite(byte, $event)"
          >
            #{{ byte }}
          </button>
          <span v-if="moreCount(block)" class="msg__more">共 {{ block.total }} 格</span>
        </div>
      </section>
    </template>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { TutorAction, TutorBlock } from '../../utils/tutor-message'

const props = defineProps<{
  blocks: TutorBlock[]
  source: 'llm' | 'local'
  model?: string | null
  streaming?: boolean
}>()

const emit = defineEmits<{
  cite: [byte: number, trigger: HTMLElement]
  action: [action: TutorAction]
}>()

const sourceLabel = computed(() => {
  if (props.source === 'llm') return props.model ? `AI · ${props.model}` : 'AI'
  return '本地讲解'
})

const sourceTitle = computed(() =>
  props.source === 'llm'
    ? `回答来自 ${props.model ?? '在线模型'}`
    : '未配置模型时使用内置讲解，内容由当前步的数值生成',
)

/**
 * 光标只跟在「正在写的那一处」：最后一块的最后一条。
 * 前面已经写完的块不该继续闪，那会让读者以为整段还在变。
 */
function caret(blockIndex: number, itemIndex: number): boolean {
  if (!props.streaming) return false
  if (blockIndex !== props.blocks.length - 1) return false
  const block = props.blocks[blockIndex]
  if (!block) return false
  if (block.type === 'why') return itemIndex === block.items.length - 1
  return itemIndex === -1
}

/** 依据只列前几格；不写总数，读者会以为整步只变了这几格 */
function moreCount(block: { bytes: number[]; total?: number }): boolean {
  return typeof block.total === 'number' && block.total > block.bytes.length
}

function onCite(byte: number, event: MouseEvent): void {
  emit('cite', byte, event.currentTarget as HTMLElement)
}
</script>

<style scoped>
.msg {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
}

.msg__src {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  margin-bottom: var(--sp-1);
}

.msg__dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--accent);
}

.msg[data-source='local'] .msg__dot {
  background: var(--ink-4);
}

.msg__src-text {
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  letter-spacing: var(--ls-label);
  color: var(--ink-3);
}

.msg__live {
  font-size: var(--fs-micro);
  color: var(--accent-strong);
}

.msg__conclusion {
  margin: 0;
  padding-left: var(--sp-3);
  border-left: 3px solid var(--accent);
  font-size: var(--fs-body);
  font-weight: 600;
  line-height: var(--lh-snug);
  color: var(--ink-1);
}

.msg__section {
  margin-top: var(--sp-3);
}

.msg__h {
  margin: 0 0 var(--sp-1);
  font-family: var(--font-ui);
  font-size: var(--fs-micro);
  font-weight: 500;
  letter-spacing: var(--ls-label);
  color: var(--ink-3);
}

.msg__list {
  margin: 0;
  padding-left: var(--sp-4);
  list-style: disc;
}

.msg__list li {
  margin-bottom: 2px;
  font-size: var(--fs-ui);
  line-height: var(--lh-body);
  color: var(--ink-2);
}

.msg__list li::marker {
  color: var(--line-strong);
}

.msg__next {
  margin: 0;
  font-size: var(--fs-ui);
  line-height: var(--lh-body);
  color: var(--ink-2);
}

.msg__act {
  margin-left: var(--sp-1);
  padding: 0;
  border: 0;
  border-bottom: var(--rule-region-w) solid var(--accent);
  background: transparent;
  font-family: var(--font-ui);
  font-size: var(--fs-ui);
  color: var(--accent-strong);
  white-space: nowrap;
  cursor: pointer;
}

.msg__act:hover {
  background: var(--accent-soft);
}

.msg__chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-1);
}

.msg__chip {
  padding: 2px var(--sp-2);
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  background: var(--surface-inset);
  font-family: var(--font-mono);
  font-size: var(--fs-label);
  font-variant-numeric: tabular-nums;
  color: var(--ink-2);
  cursor: pointer;
}

.msg__more {
  align-self: center;
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

.msg__chip:hover {
  border-color: var(--accent);
  color: var(--accent-strong);
}

.msg__caret {
  display: inline-block;
  width: 2px;
  height: 1em;
  margin-left: 2px;
  vertical-align: text-bottom;
  background: var(--accent);
  animation: msg-blink 1s steps(2, end) infinite;
}

@keyframes msg-blink {
  50% {
    opacity: 0;
  }
}

[data-motion='reduced'] .msg__caret {
  animation: none;
}

@media (prefers-reduced-motion: reduce) {
  .msg__caret {
    animation: none;
  }
}
</style>
