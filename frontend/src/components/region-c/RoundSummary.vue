<template>
  <aside
    class="rs"
    :class="{ 'is-floating': floating }"
    :aria-labelledby="titleId"
    data-round-summary
    :data-round="round"
  >
    <header class="rs__head">
      <span :id="titleId" class="rs__title" data-summary-title>{{ copy.title(round) }}</span>
      <button
        type="button"
        class="rs__close"
        data-action="summary-close"
        aria-label="关闭本轮小结"
        @click="emit('close')"
      >
        ×
      </button>
    </header>

    <p class="rs__lead">{{ copy.lead }}</p>

    <ol class="rs__list" role="list">
      <li v-for="(item, index) in copy.items" :key="item.term" class="rs__item">
        <span class="rs__no" aria-hidden="true">{{ ROUND_SUMMARY_MARKS[index] }}</span>
        <span class="rs__text">
          {{ item.lead }} —— 这一步叫<strong class="rs__term">{{ item.term }}</strong
          >{{ item.tail }}
        </span>
      </li>
    </ol>

    <p class="rs__foot">{{ copy.footer }}</p>

    <div class="rs__actions">
      <button
        type="button"
        class="rs__go"
        data-action="summary-continue"
        @click="emit('close')"
      >
        继续
      </button>
      <button
        type="button"
        class="rs__key"
        data-action="summary-key"
        @click="emit('open-key')"
      >
        看这一轮的密钥
      </button>
      <label class="rs__never">
        <input
          type="checkbox"
          class="rs__check"
          data-action="summary-never"
          @change="emit('disable')"
        />
        <span>不再提示</span>
      </label>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  ROUND_SUMMARY_COPY,
  ROUND_SUMMARY_MARKS,
} from '../../data/round-summary'
import type { TraceDirection } from '../../engine/trace'

const props = defineProps<{
  round: number
  direction: TraceDirection
  /** E 区塞不下（演示态折叠成 48px）时改为贴视口底部 */
  floating?: boolean
}>()

const emit = defineEmits<{
  close: []
  disable: []
  'open-key': []
}>()

const copy = computed(() => ROUND_SUMMARY_COPY[props.direction])
const titleId = computed(() => `round-summary-title-${props.round}`)
</script>

<style scoped>
.rs {
  /* 落在 E 区（右侧 360）：那里本来就是「读字」的位置。
     放 C 区会压在矩阵上 —— 矩阵四周没有够宽的空地，320 的卡必然盖住右列。 */
  position: absolute;
  top: var(--sp-2);
  left: var(--sp-2);
  right: var(--sp-2);
  max-height: calc(100% - var(--sp-4));
  z-index: 6;
  overflow-y: auto;
  padding: var(--sp-3);
  border: var(--rule-region-w) solid var(--line-strong);
  border-radius: var(--r-float);
  background: var(--paper-0);
  box-shadow: var(--shadow-float);
  animation: rs-in 140ms ease-out both;
}

@keyframes rs-in {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
}

.rs__head {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  margin-bottom: var(--sp-2);
  padding-bottom: var(--sp-2);
  border-bottom: var(--rule-region-w) solid var(--line-hairline);
}

.rs__title {
  flex: 1;
  min-width: 0;
  font-family: var(--font-display);
  font-size: var(--fs-ui);
  font-weight: 600;
  color: var(--ink-1);
}

.rs__close {
  flex: none;
  width: 20px;
  height: 20px;
  padding: 0;
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-cell);
  background: transparent;
  font-family: var(--font-ui);
  font-size: var(--fs-label);
  line-height: 1;
  color: var(--ink-3);
  cursor: pointer;
}

.rs__close:hover {
  border-color: var(--line-strong);
  color: var(--ink-1);
}

.rs__lead {
  margin: 0 0 var(--sp-2);
  font-size: var(--fs-label);
  color: var(--ink-3);
}

.rs__list {
  margin: 0 0 var(--sp-2);
  padding: 0;
  list-style: none;
}

.rs__item {
  display: flex;
  gap: var(--sp-1);
  margin-bottom: var(--sp-2);
  font-size: var(--fs-ui);
  line-height: 1.6;
  color: var(--ink-2);
}

.rs__item:last-child {
  margin-bottom: 0;
}

.rs__no {
  flex: none;
  font-family: var(--font-mono);
  font-size: var(--fs-label);
  color: var(--ink-3);
}

.rs__text {
  min-width: 0;
}

.rs__term {
  font-weight: 600;
  color: var(--ink-1);
}

.rs__foot {
  margin: 0 0 var(--sp-3);
  padding-top: var(--sp-2);
  border-top: var(--rule-region-w) dashed var(--line-hairline);
  font-size: var(--fs-ui);
  line-height: 1.6;
  color: var(--ink-2);
}

.rs__actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--sp-2);
}

.rs__go {
  height: 26px;
  padding: 0 var(--sp-3);
  border: var(--rule-region-w) solid var(--accent);
  border-radius: var(--r-control);
  background: var(--accent);
  font-family: var(--font-ui);
  font-size: var(--fs-label);
  color: var(--paper-0);
  cursor: pointer;
  white-space: nowrap;
}

.rs__key {
  height: 26px;
  padding: 0 var(--sp-2);
  border: var(--rule-region-w) solid var(--line-strong);
  border-radius: var(--r-control);
  background: transparent;
  font-family: var(--font-ui);
  font-size: var(--fs-label);
  color: var(--accent-strong);
  cursor: pointer;
  white-space: nowrap;
}

.rs__key:hover {
  border-color: var(--accent);
}

.rs__never {
  display: flex;
  align-items: center;
  gap: var(--sp-1);
  margin-left: auto;
  font-size: var(--fs-micro);
  color: var(--ink-3);
  cursor: pointer;
  white-space: nowrap;
}

.rs__check {
  width: 13px;
  height: 13px;
  margin: 0;
  accent-color: var(--accent);
  cursor: pointer;
}

/* 演示态：E 区被压成 48px 的竖条，塞不下任何句子 —— 改贴视口底部。
   同一组声明在下面的窄屏媒体查询里再写一遍：一个是状态驱动、一个是视口驱动，
   合并进一个选择器会让 `.rs` 在宽屏非演示态也 fixed，不行。 */
.rs.is-floating {
  position: fixed;
  inset: auto 0 calc(var(--transport-h) + var(--sp-3));
  /* 投屏时一行排满 1400px 反而难读：限宽居中，两侧留白 */
  width: min(720px, calc(100% - var(--sp-6)));
  margin-inline: auto;
  max-height: 56vh;
}

/* E 区折叠成 48px（窄屏）时同理。不用 container query ——
   E 区一旦设 container-type 就会成为 fixed 后代的包含块，卡片仍旧只有 48px 宽。 */
@media (max-width: 69.9375rem) {
  .rs {
    position: fixed;
    inset: auto 0 calc(var(--transport-h) + var(--sp-3));
    width: min(720px, calc(100% - var(--sp-6)));
    margin-inline: auto;
    max-height: 56vh;
  }
}

@media (prefers-reduced-motion: reduce) {
  .rs {
    animation: none;
  }
}
</style>
