<template>
  <aside
    v-if="open"
    ref="panelEl"
    class="c-drawer"
    role="dialog"
    aria-modal="true"
    aria-labelledby="byte-drawer-title"
    data-drawer
    tabindex="-1"
    @keydown="onKeydown"
  >
    <header class="c-drawer__head">
      <h2 id="byte-drawer-title" class="c-drawer__title">
        {{ title }}
      </h2>
      <button
        ref="closeEl"
        type="button"
        class="c-drawer__close"
        aria-label="关闭字节详情"
        data-action="drawer-close"
        @click="emit('close')"
      >
        ×
      </button>
    </header>

    <dl class="c-drawer__body">
      <div>
        <dt>当前步</dt>
        <dd>{{ stepLabel }}</dd>
      </div>
      <div>
        <dt>当前值</dt>
        <dd class="c-drawer__hex">{{ hex(value) }}</dd>
      </div>
      <div>
        <dt>本步变化</dt>
        <dd class="c-drawer__hex">{{ hex(before) }} → {{ hex(after) }}</dd>
      </div>
      <div>
        <dt>位置</dt>
        <dd>index {{ byteIndex }}（列优先）</dd>
      </div>
    </dl>

    <button
      v-if="sboxPair"
      type="button"
      class="c-drawer__sbox"
      data-action="drawer-sbox"
      @click="emit('sbox', sboxPair.from)"
    >
      在 S 盒中查看 0x{{ hex(sboxPair.from) }} → 0x{{ hex(sboxPair.to) }}
    </button>

    <p class="c-drawer__hint">Esc 关闭；Tab 在抽屉内循环。</p>
  </aside>
</template>

<script setup lang="ts">
import { nextTick, onMounted, ref, watch } from 'vue'

const props = defineProps<{
  open: boolean
  byteIndex: number
  row: number
  col: number
  value: number
  before: number
  after: number
  stepLabel: string
  title: string
  /** SubBytes 步才给值：抽屉里出现「在 S 盒中查看 输入 → 输出」，其余步为 null */
  sboxPair: { from: number; to: number } | null
}>()

const emit = defineEmits<{
  close: []
  sbox: [value: number]
}>()

const panelEl = ref<HTMLElement | null>(null)
const closeEl = ref<HTMLButtonElement | null>(null)

const hex = (value: number): string =>
  (value ?? 0).toString(16).toUpperCase().padStart(2, '0')

function focusables(): HTMLElement[] {
  if (!panelEl.value) return []
  return Array.from(
    panelEl.value.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
    ),
  ).filter((element) => !element.hasAttribute('disabled'))
}

function onKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape') {
    event.preventDefault()
    event.stopPropagation()
    emit('close')
    return
  }
  if (event.key !== 'Tab') return

  const items = focusables()
  if (items.length === 0) return
  const current = document.activeElement as HTMLElement | null
  const index = current ? items.indexOf(current) : -1

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

watch(
  () => props.open,
  async (open) => {
    if (!open) return
    await nextTick()
    closeEl.value?.focus({ preventScroll: true })
  },
)

onMounted(() => {
  if (props.open) closeEl.value?.focus({ preventScroll: true })
})
</script>

<style scoped>
.c-drawer {
  position: fixed;
  top: var(--topbar-h);
  right: 0;
  bottom: 0;
  z-index: 30;
  width: min(var(--ai-col), 100vw);
  padding: var(--sp-4);
  border-left: var(--rule-region-w) solid var(--line-hairline);
  background: var(--paper-0);
  box-shadow: -8px 0 24px rgb(0 0 0 / 0.08);
}

.c-drawer__head {
  display: flex;
  align-items: baseline;
  gap: var(--sp-2);
  padding-bottom: var(--sp-2);
  border-bottom: var(--rule-region-w) solid var(--line-hairline);
}

.c-drawer__title {
  flex: 1;
  min-width: 0;
  font-size: var(--fs-body);
  font-weight: 600;
  color: var(--ink-1);
}

.c-drawer__close {
  width: 28px;
  height: 28px;
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  background: transparent;
  font-size: var(--fs-body);
  color: var(--ink-2);
  cursor: pointer;
}

.c-drawer__body {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  margin: var(--sp-4) 0 0;
}

.c-drawer__body div {
  display: grid;
  grid-template-columns: 64px minmax(0, 1fr);
  gap: var(--sp-2);
}

.c-drawer__body dt {
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

.c-drawer__body dd {
  margin: 0;
  font-size: var(--fs-ui);
  color: var(--ink-1);
}

.c-drawer__hex {
  font-family: var(--font-mono);
  letter-spacing: var(--ls-hex-cell);
  color: var(--ink-2);
}

.c-drawer__sbox {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-2);
  width: 100%;
  margin-top: var(--sp-4);
  padding: var(--sp-2) var(--sp-3);
  border: var(--rule-region-w) solid var(--accent);
  border-radius: var(--r-control);
  background: var(--step-sub-tint);
  font-size: var(--fs-ui);
  color: var(--step-sub-ink);
  cursor: pointer;
}

.c-drawer__sbox:hover {
  background: var(--accent-soft);
}

.c-drawer__hint {
  margin-top: var(--sp-4);
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

[data-mode="present"] .c-drawer {
  width: min(var(--ai-col), 100vw);
}

@media (max-width: 69.9375rem) {
  .c-drawer {
    width: min(360px, 100vw);
  }
}
</style>