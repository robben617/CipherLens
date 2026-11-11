<template>
  <div class="quick" :aria-label="`针对${opLabel}的快捷提问`">
    <button
      v-for="item in questions"
      :key="item"
      type="button"
      class="quick__item"
      data-action="quick-ask"
      :disabled="disabled"
      :title="`点击直接提问：${item}`"
      @click="emit('pick', item)"
    >
      {{ item }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { OP_LABEL } from '../../data/glossary'

const props = defineProps<{
  op: string
  stepIndex: number
  stepAfter: readonly number[]
  disabled?: boolean
}>()

const emit = defineEmits<{
  pick: [question: string]
}>()

const opLabel = computed(() => (props.stepIndex === 0 ? '初始状态' : OP_LABEL[props.op] ?? props.op))

function hex(value: number | undefined): string {
  return (value ?? 0).toString(16).toUpperCase().padStart(2, '0')
}

/**
 * 问题跟着这一步的操作走：在列混合那一屏问「S 盒为什么能反查」，
 * 等于答非所问。第一格的实际输出值也嵌进去，问的和屏幕上看到的是同一个数。
 */
const questions = computed<string[]>(() => {
  if (props.stepIndex === 0) {
    return ['这 16 个字节怎么排成矩阵？', '明文长度必须 16 字节吗？']
  }

  const head = hex(props.stepAfter[0])

  if (props.op === 'sub_bytes') {
    return [`为什么第 1 格变成 0x${head}？`, 'S 盒为什么能反查？', '如果输入改成 0x00 会怎样？']
  }
  if (props.op === 'shift_rows') {
    return ['为什么要按行移位？', '移完之后哪 4 个字节会混在一起？', '最后一轮为什么不移？']
  }
  if (props.op === 'mix_columns') {
    return ['为什么整列都变了？', 'GF(2⁸) 乘法怎么算？', '这一步能跳过吗？']
  }
  return ['密钥是怎么参与进来的？', '为什么异或就能解密？', '轮密钥和原始密钥什么关系？']
})
</script>

<style scoped>
.quick {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-1);
}

.quick__item {
  max-width: 100%;
  padding: 3px var(--sp-2);
  border: var(--rule-region-w) dashed var(--line-default);
  border-radius: var(--r-control);
  background: transparent;
  font-family: var(--font-ui);
  font-size: var(--fs-micro);
  line-height: 1.4;
  text-align: left;
  color: var(--ink-2);
  cursor: pointer;
}

.quick__item:hover:not(:disabled) {
  border-color: var(--accent);
  border-style: solid;
  color: var(--accent-strong);
}

.quick__item:disabled {
  color: var(--ink-4);
  border-color: var(--line-hairline);
  cursor: default;
}
</style>
