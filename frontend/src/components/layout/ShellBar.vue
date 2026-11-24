<template>
  <header class="shellbar">
    <RouterLink class="shellbar__brand" to="/" data-shell-brand data-action="home" @click="closeMenu">
      <span class="shellbar__name">CipherLens</span>
      <span class="shellbar__cn">密码透镜</span>
    </RouterLink>

    <div class="shellbar__navwrap" :class="{ 'is-open': menuOpen }">
      <NavLinks @navigate="closeMenu" />
    </div>

    <div v-if="$slots.status" class="shellbar__status">
      <slot name="status" />
    </div>

    <div class="shellbar__actions">
      <slot name="actions" />
    </div>

    <button
      class="shellbar__toggle"
      type="button"
      :aria-expanded="menuOpen"
      :aria-label="menuOpen ? '收起导航菜单' : '打开导航菜单'"
      @click="menuOpen = !menuOpen"
    >
      <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true">
        <path
          d="M3 6h14M3 10h14M3 14h14"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linecap="round"
        />
      </svg>
    </button>

    <span class="shellbar__ver" aria-hidden="true">v0.1</span>
  </header>
</template>

<script setup lang="ts">
import { onMounted, onScopeDispose, ref } from 'vue'
import { RouterLink } from 'vue-router'
import NavLinks from './NavLinks.vue'

const menuOpen = ref(false)

function closeMenu(): void {
  menuOpen.value = false
}

function onKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape' && menuOpen.value) closeMenu()
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onScopeDispose(() => window.removeEventListener('keydown', onKeydown))
</script>

<style scoped>
/* 全站顶栏契约：高度、品牌、导航、右侧操作只用这一份 */
.shellbar {
  position: sticky;
  top: 0;
  z-index: 30;
  display: flex;
  align-items: center;
  gap: var(--nav-gap);
  box-sizing: border-box;
  width: 100%;
  height: var(--topbar-h);
  padding: 0 var(--nav-pad-x);
  border-bottom: var(--rule-region-w) solid var(--line-hairline);
  background: var(--paper-0);
}

.shellbar__brand {
  display: inline-flex;
  align-items: baseline;
  gap: var(--sp-2);
  flex: none;
  color: var(--ink-1);
  text-decoration: none;
}

.shellbar__name {
  font-family: var(--font-display);
  font-size: var(--fs-h3);
  font-weight: 600;
  letter-spacing: 0.01em;
}

.shellbar__cn {
  font-family: var(--font-ui);
  font-size: var(--fs-micro);
  letter-spacing: var(--ls-label);
  color: var(--ink-3);
}

.shellbar__navwrap {
  display: flex;
  align-items: center;
  height: 100%;
  min-width: 0;
}

.shellbar__status {
  display: flex;
  align-items: center;
  gap: var(--nav-action-gap);
  min-width: 0;
  overflow: hidden;
}

.shellbar__actions {
  display: flex;
  align-items: center;
  gap: var(--nav-action-gap);
  margin-left: auto;
}

.shellbar__ver {
  flex: none;
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-4);
}

.shellbar__toggle {
  display: none;
  align-items: center;
  justify-content: center;
  flex: none;
  width: 44px;
  height: 44px;
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  background: transparent;
  color: var(--ink-2);
  cursor: pointer;
}

/* 插槽里的操作按钮统一为顶栏口径：28 高、micro 字号、与导航同一基线 */
:slotted(.shellbar-action) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 28px;
  padding: 0 10px;
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  background: transparent;
  font-family: var(--font-ui);
  font-size: var(--fs-micro);
  line-height: 1;
  color: var(--ink-2);
  white-space: nowrap;
  cursor: pointer;
}

:slotted(.shellbar-action:hover) {
  border-color: var(--line-default);
  color: var(--ink-1);
}

:slotted(.shellbar-action:disabled) {
  border-color: var(--line-hairline);
  color: var(--ink-3);
  cursor: default;
}

/* 插槽里的状态提示也用同一高度与字号，看起来属于顶栏 */
:slotted(.shellbar-status) {
  display: inline-flex;
  align-items: center;
  height: 22px;
  max-width: 100%;
  padding: 0 8px;
  border: var(--rule-region-w) dashed var(--line-hairline);
  border-radius: var(--r-control);
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  line-height: 1;
  color: var(--ink-2);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 45rem) {
  .shellbar {
    gap: var(--nav-gap-sm);
    padding: 0 var(--nav-pad-x-sm);
  }

  .shellbar__navwrap {
    position: absolute;
    top: var(--topbar-h);
    left: 0;
    right: 0;
    display: none;
    height: auto;
    padding: var(--sp-2) var(--sp-3);
    border-bottom: var(--rule-region-w) solid var(--line-hairline);
    background: var(--paper-0);
    box-shadow: var(--shadow-1);
  }

  .shellbar__navwrap.is-open {
    display: block;
  }

  .shellbar__navwrap :deep(.navlinks) {
    flex-direction: column;
    align-items: stretch;
    gap: 0;
  }

  .shellbar__navwrap :deep(.navlinks__link) {
    height: 44px;
    border-bottom: var(--rule-region-w) solid var(--line-hairline);
  }

  .shellbar__navwrap :deep(.navlinks__link:last-child) {
    border-bottom: 0;
  }

  .shellbar__toggle {
    display: inline-flex;
  }

  .shellbar__ver {
    display: none;
  }

  .shellbar__status {
    display: none;
  }
}

@media (max-width: 26rem) {
  .shellbar__cn {
    display: none;
  }
}
</style>