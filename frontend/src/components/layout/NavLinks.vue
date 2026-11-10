<template>
  <nav class="navlinks" :class="{ 'navlinks--compact': compact }" aria-label="主导航">
    <RouterLink
      v-for="item in NAV_ITEMS"
      :key="item.key"
      class="navlinks__link"
      :class="{ 'is-active': isNavActive(route.path, item.to) }"
      :to="item.to"
      :aria-current="isNavActive(route.path, item.to) ? 'page' : undefined"
      @click="$emit('navigate')"
    >
      {{ item.label }}
    </RouterLink>
  </nav>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import { NAV_ITEMS, isNavActive } from '../../data/nav'

defineProps<{ compact?: boolean }>()
defineEmits<{ navigate: [] }>()

const route = useRoute()
</script>

<style scoped>
.navlinks {
  display: flex;
  align-items: center;
  gap: var(--sp-4);
  height: 100%;
}

.navlinks__link {
  position: relative;
  display: inline-flex;
  align-items: center;
  height: 100%;
  padding: 0 2px;
  border-bottom: 2px solid transparent; /* 宽度恒定，只换颜色，避免切换时跳动 */
  font-family: var(--font-ui);
  font-size: var(--fs-ui);
  line-height: 1;
  color: var(--ink-2);
  text-decoration: none;
  white-space: nowrap;
}

.navlinks__link:hover {
  color: var(--ink-1);
}

.navlinks__link.is-active {
  border-bottom-color: var(--accent);
  color: var(--ink-1);
  font-weight: 500;
}

.navlinks--compact {
  gap: var(--sp-3);
}

.navlinks--compact .navlinks__link {
  font-size: var(--fs-label);
  color: var(--ink-3);
}

.navlinks--compact .navlinks__link.is-active {
  color: var(--accent-strong);
  font-weight: 500;
}
</style>
