<template>
  <section class="cmp" :data-step="stepIndex">
    <Transition name="cmp-swap" mode="out-in">
      <!-- 起点：只给一个 4×4，不提前拆成两栏 -->
      <div v-if="stepIndex === 0" key="single" class="cmp__single">
        <p class="cmp__side-title">你的明文</p>
        <div class="cmp__grid" aria-label="起点 4×4 矩阵">
          <span
            v-for="cell in beforeCells"
            :key="`s-${cell.slot}`"
            class="cmp__cell"
          >{{ hex(cell.value) }}</span>
        </div>
        <p class="cmp__step">第 0 步 · 起点</p>
        <p class="cmp__hint">按“下一步”或空格开始：矩阵会分成“变换前 → 变换后”两栏。</p>
      </div>

      <!-- 每一步：左边上一步、右边当前步，中间箭头 + 逐格说明 -->
      <div v-else key="pair" class="cmp__stepview">
        <div class="cmp__pair">
          <div class="cmp__side">
            <p class="cmp__side-title">变换前</p>
            <div class="cmp__grid" :aria-label="`第 ${stepIndex - 1} 步的 4×4 矩阵`">
              <span
                v-for="cell in beforeCells"
                :key="`b-${cell.slot}`"
                class="cmp__cell"
                :class="{ 'is-source': changedSet.has(cell.index) }"
              >{{ hex(cell.value) }}</span>
            </div>
            <p class="cmp__step">第 {{ stepIndex - 1 }} 步</p>
          </div>

          <div class="cmp__arrow">
            <span class="cmp__arrow-label">{{ arrowLabel }}</span>
            <span class="cmp__arrow-glyph" aria-hidden="true">→</span>
          </div>

          <div class="cmp__side">
            <p class="cmp__side-title">变换后</p>
            <div class="cmp__grid" :aria-label="`第 ${stepIndex} 步的 4×4 矩阵`">
              <span
                v-for="cell in afterCells"
                :key="`a-${cell.slot}`"
                class="cmp__cell"
                :class="{ 'is-changed': changedSet.has(cell.index) }"
              >{{ hex(cell.value) }}</span>
            </div>
            <p class="cmp__step">第 {{ stepIndex }} 步<span v-if="isLast"> · 结果</span></p>
          </div>
        </div>

        <div class="cmp__explain">
          <p class="cmp__explain-title">这一步怎么变</p>
          <ul>
            <li v-for="(line, index) in explainLines" :key="index">{{ line }}</li>
          </ul>
        </div>
      </div>
    </Transition>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  before: readonly number[]
  after: readonly number[]
  stepIndex: number
  total: number
  op: string
  changed: readonly number[]
  roundKey?: ArrayLike<number>
  direction?: 'encrypt' | 'decrypt'
}>()

const NAMES: Record<string, string> = {
  sub_bytes: '字节代换（SubBytes）',
  shift_rows: '行移位（ShiftRows）',
  mix_columns: '列混合（MixColumns）',
  add_round_key: '轮密钥加（AddRoundKey）',
}

const changedSet = computed(() => new Set(props.changed))
const isLast = computed(() => props.stepIndex >= props.total)

const arrowLabel = computed(() => {
  const name = NAMES[props.op] ?? '这一步的变换'
  if (props.direction === 'decrypt' && props.op !== 'add_round_key') return `逆${name}`
  return name
})

function cells(values: readonly number[]): { slot: number; index: number; value: number }[] {
  return Array.from({ length: 16 }, (_, slot) => {
    const row = Math.floor(slot / 4)
    const col = slot % 4
    const index = col * 4 + row
    return { slot, index, value: values[index] ?? 0 }
  })
}

function rowOf(values: readonly number[], row: number): number[] {
  return [0, 1, 2, 3].map((col) => values[col * 4 + row] ?? 0)
}

function colOf(values: readonly number[], col: number): number[] {
  return [0, 1, 2, 3].map((row) => values[col * 4 + row] ?? 0)
}

function cellLabel(index: number): string {
  const row = index % 4
  const col = Math.floor(index / 4)
  return `第 ${row + 1} 行第 ${col + 1} 列`
}

const beforeCells = computed(() => cells(props.before))
const afterCells = computed(() => cells(props.after))

const explainLines = computed(() => {
  if (props.stepIndex === 0) return []
  const before = props.before
  const after = props.after
  const decrypt = props.direction === 'decrypt'

  switch (props.op) {
    case 'sub_bytes': {
      const index = props.changed[0] ?? 0
      const box = decrypt ? '逆 S 盒' : 'S 盒'
      return [
        `举例：${cellLabel(index)}，${hex(before[index] ?? 0)} → ${hex(after[index] ?? 0)}。把这个字节的高 4 位当行、低 4 位当列，在 ${box}里查表。`,
        `其余 15 格用同一张 ${box}，只换输入，所以不逐格重复。`,
      ]
    }
    case 'shift_rows': {
      return [0, 1, 2, 3].map((row) => {
        const move = row === 0 ? '不动' : decrypt ? `右移 ${row} 格` : `左移 ${row} 格`
        return `第 ${row + 1} 行${move}：${rowOf(before, row).map(hex).join(' ')} → ${rowOf(after, row).map(hex).join(' ')}。`
      })
    }
    case 'mix_columns': {
      const matrix = decrypt ? '逆矩阵' : '固定矩阵'
      return [
        `举例：第 1 列 ${colOf(before, 0).map(hex).join(' ')} → ${colOf(after, 0).map(hex).join(' ')}。每列 4 个字节都要和${matrix}相乘，列内互相混合。`,
        `其余 3 列用同一套${matrix}，只换输入，所以不逐列重复。`,
      ]
    }
    case 'add_round_key': {
      const index = props.changed[0] ?? 0
      const key = props.roundKey?.[index] ?? 0
      return [
        `举例：${cellLabel(index)}，${hex(before[index] ?? 0)} ⊕ ${hex(key)} = ${hex(after[index] ?? 0)}。⊕ 是异或：两位不同得 1，相同得 0。`,
        '其余 15 格都和对应位置的轮密钥字节异或，规则相同，所以只举这一格。',
      ]
    }
    default:
      return []
  }
})

function hex(value: number): string {
  return value.toString(16).padStart(2, '0')
}
</script>

<style scoped>
.cmp {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 100%;
  /* 顶部让出解说条：第 3 步说明变 4 行时矩阵会上移，不能让解说条压住 */
  padding: clamp(104px, 13vh, 128px) 16px 20px;
}

.cmp__single,
.cmp__stepview {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 28px;
  width: 100%;
}

.cmp__side {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.cmp__side-title {
  margin: 0;
  font-family: var(--font-ui);
  font-size: var(--fs-label);
  letter-spacing: var(--ls-label);
  color: var(--ink-3);
}

.cmp__grid {
  --cmp-cell: clamp(64px, 6.4vw, 96px);
  display: grid;
  grid-template-columns: repeat(4, var(--cmp-cell));
  grid-template-rows: repeat(4, var(--cmp-cell));
  gap: 6px;
  width: calc(4 * var(--cmp-cell) + 18px);
  height: calc(4 * var(--cmp-cell) + 18px);
}

.cmp__single .cmp__grid {
  --cmp-cell: clamp(72px, 8vw, 116px);
}

.cmp__cell {
  display: flex;
  align-items: center;
  justify-content: center;
  border: var(--rule-region-w) solid var(--line-default);
  border-radius: var(--r-cell);
  background: var(--paper-1);
  font-family: var(--font-mono);
  font-size: 17px;
  line-height: 1;
  color: var(--ink-1);
}

.cmp__single .cmp__cell {
  font-size: 20px;
}

.cmp__cell.is-changed {
  border-color: var(--st-changed-bar);
  background: var(--st-changed);
  box-shadow: inset 3px 0 0 var(--st-changed-bar);
  font-weight: 600;
}

.cmp__cell.is-source {
  border-style: dashed;
  border-color: var(--st-changed-bar);
  color: var(--ink-2);
}

.cmp__step {
  margin: 0;
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  letter-spacing: var(--ls-hex-long);
  color: var(--ink-3);
}

.cmp__hint {
  margin: 0;
  font-family: var(--font-ui);
  font-size: var(--fs-micro);
  line-height: var(--lh-snug);
  color: var(--ink-3);
}

.cmp__pair {
  display: flex;
  align-items: center;
  gap: var(--sp-16);
}

.cmp__arrow {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-width: 140px;
  text-align: center;
}

.cmp__arrow-label {
  font-family: var(--font-ui);
  font-size: var(--fs-ui);
  line-height: var(--lh-snug);
  color: var(--ink-2);
}

.cmp__arrow-glyph {
  font-family: var(--font-mono);
  font-size: 24px;
  line-height: 1;
  color: var(--accent-strong);
}

.cmp__explain {
  width: min(820px, 100%);
  padding: 10px 0 0 14px;
  border-top: var(--rule-region-w) solid var(--line-hairline);
  border-left: 2px solid var(--accent);
}

.cmp__explain-title {
  margin: 0 0 6px;
  font-family: var(--font-ui);
  font-size: var(--fs-label);
  letter-spacing: var(--ls-label);
  color: var(--ink-3);
}

.cmp__explain ul {
  display: flex;
  flex-direction: column;
  gap: 3px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.cmp__explain li {
  font-size: var(--fs-ui);
  line-height: 1.7;
  color: var(--ink-1);
}

/* 起点 → 第一步：单矩阵淡出、双矩阵淡入，避免突然多出一块 */
.cmp-swap-enter-active,
.cmp-swap-leave-active {
  transition:
    opacity var(--d-2) var(--e-out-quart),
    transform var(--d-2) var(--e-out-quart);
}

.cmp-swap-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.cmp-swap-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

@media (max-width: 1200px) {
  .cmp__grid {
    --cmp-cell: clamp(48px, 4.8vw, 68px);
  }

  .cmp__single .cmp__grid {
    --cmp-cell: clamp(64px, 7.4vw, 96px);
  }

  .cmp__pair {
    gap: var(--sp-8);
  }

  .cmp__arrow {
    min-width: 100px;
  }
}

@media (max-width: 900px) {
  .cmp__pair {
    flex-direction: column;
    gap: var(--sp-2);
  }

  .cmp__arrow {
    min-width: 0;
    flex-direction: row;
    gap: var(--sp-2);
  }

  .cmp__arrow-glyph {
    transform: rotate(90deg);
  }

  .cmp__grid {
    --cmp-cell: 40px;
  }

  .cmp__single .cmp__grid {
    --cmp-cell: 60px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .cmp-swap-enter-active,
  .cmp-swap-leave-active {
    transition: none;
  }
}
</style>