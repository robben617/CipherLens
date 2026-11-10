<template>
  <article class="why">
    <svg class="why__icon" width="24" height="24" viewBox="0 0 24 24" aria-hidden="true">
      <!-- 黑箱：进得去，出得来，中间没有东西 -->
      <template v-if="icon === 'box'">
        <path d="M2 12h4M18 12h4" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
        <rect x="6.5" y="6.5" width="11" height="11" rx="1" fill="none" stroke="currentColor" stroke-width="1.5" />
        <path d="M9.5 12h5" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-dasharray="2 2" />
      </template>

      <!-- 术语：还没讲清楚就先甩一堆名词 -->
      <template v-else-if="icon === 'text'">
        <path d="M3 6h13M3 10.5h18M3 15h9" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
        <path d="M3 19h6" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-dasharray="2 2" />
      </template>

      <!-- 错了不知道错在哪：一堆格子里某一个错了，但指不出来 -->
      <template v-else>
        <g fill="none" stroke="currentColor" stroke-width="1.5">
          <rect x="3" y="3" width="5" height="5" rx="1" />
          <rect x="10" y="3" width="5" height="5" rx="1" />
          <rect x="3" y="10" width="5" height="5" rx="1" />
          <rect x="10" y="10" width="5" height="5" rx="1" />
        </g>
        <circle cx="17.5" cy="17.5" r="3.5" fill="none" stroke="currentColor" stroke-width="1.5" stroke-dasharray="2 2" />
        <circle cx="17.5" cy="17.5" r="1" fill="currentColor" />
      </template>
    </svg>

    <h3 class="why__title">{{ title }}</h3>
    <p class="why__body">{{ body }}</p>
  </article>
</template>

<script setup lang="ts">
defineProps<{
  icon: 'box' | 'text' | 'pin'
  title: string
  body: string
}>()
</script>

<style scoped>
.why {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  padding: var(--sp-4);
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--card-r);
  background: var(--paper-1);
}

.why__icon {
  color: var(--ink-3);
}

.why__title {
  margin: 0;
  font-family: var(--font-ui);
  font-size: var(--fs-h3);
  font-weight: 600;
  line-height: var(--lh-snug);
  color: var(--ink-1);
}

.why__body {
  margin: 0;
  font-size: var(--fs-ui);
  line-height: var(--lh-body);
  color: var(--ink-2);
}
</style>
