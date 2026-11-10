<template>
  <div class="shell">
    <header class="shell__bar">
      <RouterLink class="shell__brand" to="/" @click="closeMenu">
        <span class="shell__name">CipherLens</span>
        <span class="shell__cn">密码透镜</span>
      </RouterLink>

      <div class="shell__navwrap" :class="{ 'is-open': menuOpen }">
        <NavLinks @navigate="closeMenu" />
      </div>

      <button
        class="shell__toggle"
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

      <span class="shell__ver" aria-hidden="true">v0.1</span>
    </header>

    <div class="shell__main">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onScopeDispose, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import NavLinks from './NavLinks.vue'

const route = useRoute()
const menuOpen = ref(false)

function closeMenu(): void {
  menuOpen.value = false
}

function onKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape' && menuOpen.value) closeMenu()
}

// 路由变化时收起移动端菜单，避免点完链接面板还挂着
watch(() => route.fullPath, closeMenu)

onMounted(() => window.addEventListener('keydown', onKeydown))
onScopeDispose(() => window.removeEventListener('keydown', onKeydown))
</script>

<style scoped>
.shell {
  min-height: 100vh;
  min-height: 100dvh;
  background: var(--paper-0);
}

.shell__bar {
  position: sticky;
  top: 0;
  z-index: 30;
  display: flex;
  align-items: center;
  gap: var(--sp-4);
  height: var(--nav-h);
  padding: 0 var(--sp-4);
  border-bottom: var(--rule-region-w) solid var(--line-hairline);
  background: var(--paper-0);
}

.shell__brand {
  display: inline-flex;
  align-items: baseline;
  gap: var(--sp-2);
  color: var(--ink-1);
  text-decoration: none;
}

.shell__name {
  font-family: var(--font-display);
  font-size: var(--fs-h3);
  font-weight: 600;
  letter-spacing: 0.01em;
}

.shell__cn {
  font-family: var(--font-ui);
  font-size: var(--fs-micro);
  letter-spacing: var(--ls-label);
  color: var(--ink-3);
}

.shell__navwrap {
  display: flex;
  align-items: center;
  height: 100%;
  margin-left: var(--sp-4);
}

.shell__ver {
  margin-left: auto;
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-4);
}

.shell__toggle {
  display: none;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  margin-left: auto;
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  background: transparent;
  color: var(--ink-2);
  cursor: pointer;
}

.shell__main {
  min-height: calc(100dvh - var(--nav-h));
}

@media (max-width: 720px) {
  .shell__bar {
    gap: var(--sp-2);
    padding: 0 var(--sp-3);
  }

  .shell__cn {
    display: none;
  }

  .shell__toggle {
    display: inline-flex;
  }

  .shell__ver {
    display: none;
  }

  .shell__navwrap {
    position: absolute;
    top: var(--nav-h);
    left: 0;
    right: 0;
    display: none;
    height: auto;
    margin-left: 0;
    padding: var(--sp-2) var(--sp-3);
    border-bottom: var(--rule-region-w) solid var(--line-hairline);
    background: var(--paper-0);
    box-shadow: var(--shadow-1);
  }

  .shell__navwrap.is-open {
    display: block;
  }

  /* 移动端竖排，点击目标 44px */
  .shell__navwrap :deep(.navlinks) {
    flex-direction: column;
    align-items: stretch;
    gap: 0;
  }

  .shell__navwrap :deep(.navlinks__link) {
    height: 44px;
    border-bottom: var(--rule-region-w) solid var(--line-hairline);
  }

  .shell__navwrap :deep(.navlinks__link:last-child) {
    border-bottom: 0;
  }
}
</style>
