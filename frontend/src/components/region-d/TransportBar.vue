<template>
  <div class="c-transport">
    <div class="c-transport__controls">
      <button class="c-transport__btn" data-action="first" type="button" aria-label="首步" @click="playback.first()">
        |&lt;
      </button>
      <button class="c-transport__btn" data-action="prev" type="button" aria-label="上一步" @click="stepPrev">
        &lt;
      </button>
      <button
        class="c-transport__btn c-transport__btn--play"
        data-action="play"
        type="button"
        :aria-label="playback.isPlaying ? '暂停' : '播放'"
        :aria-pressed="playback.isPlaying"
        @click="playback.toggle()"
      >
        {{ playback.isPlaying ? '暂停' : '播放' }}
      </button>
      <button class="c-transport__btn" data-action="next" type="button" aria-label="下一步" @click="stepNext">
        &gt;
      </button>
      <button class="c-transport__btn" data-action="last" type="button" aria-label="末步" @click="playback.last()">
        &gt;|
      </button>
      <button class="c-transport__btn" data-action="replay" type="button" aria-label="重播" @click="replay">
        ↻
      </button>
    </div>

    <div class="c-transport__stepno">
      {{ playback.currentStep }} / {{ stepCount }}
    </div>

    <div class="c-transport__spacer"></div>

    <button
      class="c-transport__motion"
      data-action="motion"
      type="button"
      :aria-pressed="reduced"
      :aria-label="reduced ? '恢复动效' : '减少动效'"
      @click="toggleReduced"
    >
      动效
    </button>

    <label class="c-transport__speed">
      <span class="sr-only">播放倍速</span>
      <select :value="String(playback.speed)" @change="onSpeedChange">
        <option value="0.5">0.5×</option>
        <option value="1">1×</option>
        <option value="2">2×</option>
        <option value="4">4×</option>
      </select>
    </label>

    <div id="timeline-legend" class="c-transport__legend">
      <span class="c-legend__item">
        <span class="c-legend__box">
          <i class="c-mark__shape" data-kind="diag" aria-hidden="true"></i>
        </span>
        <span class="c-legend__text">系统推测</span>
      </span>
      <span class="c-legend__item">
        <span class="c-legend__box">
          <i class="c-mark__shape" data-kind="ask" aria-hidden="true"></i>
        </span>
        <span class="c-legend__text">我的提问</span>
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { usePlaybackStore, type PlaybackSpeed } from '../../stores/playback'
import { useReducedMotion } from '../../composables/useReducedMotion'

defineProps<{
  stepCount: number
}>()

const playback = usePlaybackStore()
const { reduced, toggle: toggleReduced } = useReducedMotion()

function stepPrev(): void {
  playback.pause()
  playback.prev()
}

function stepNext(): void {
  playback.pause()
  playback.next()
}

function replay(): void {
  playback.pause()
  playback.setStep(0)
  playback.play()
}

function onSpeedChange(event: Event): void {
  const value = Number((event.target as HTMLSelectElement).value) as PlaybackSpeed
  playback.setSpeed(value)
}
</script>

<style scoped>
.c-transport {
  height: 40px;
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: 0 12px;
  box-sizing: border-box;
}

.c-transport__controls {
  display: flex;
  align-items: center;
  gap: var(--sp-1);
}

.c-transport__btn {
  min-width: 28px;
  height: 26px;
  padding: 0 var(--sp-1);
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  background: transparent;
  font-family: var(--font-mono);
  font-size: var(--fs-label);
  color: var(--ink-2);
  cursor: pointer;
}

.c-transport__btn--play {
  min-width: 48px;
  color: var(--accent-strong);
  border-color: var(--accent);
}

.c-transport__stepno {
  min-width: 64px;
  font-family: var(--font-mono);
  font-size: var(--fs-label);
  font-variant-numeric: tabular-nums;
  color: var(--ink-2);
}

.c-transport__spacer {
  flex: 1;
}

.c-transport__motion {
  height: 26px;
  padding: 0 var(--sp-2);
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  background: transparent;
  font-family: var(--font-ui);
  font-size: var(--fs-label);
  color: var(--ink-2);
  cursor: pointer;
}

.c-transport__motion[aria-pressed="true"] {
  border-color: var(--accent);
  color: var(--accent-strong);
}

.c-transport__speed select {
  height: 26px;
  border: var(--rule-region-w) solid var(--line-hairline);
  border-radius: var(--r-control);
  background: var(--paper-0);
  font-family: var(--font-ui);
  font-size: var(--fs-label);
  color: var(--ink-2);
}

.c-transport__legend {
  min-width: var(--tl-hint-slot);
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 16px;
}

.c-legend__item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 4px;
  height: var(--tl-mark-band);
}

.c-legend__box {
  position: relative;
  width: 20px;
  height: var(--tl-mark-band);
}

.c-legend__text {
  font-family: var(--font-ui);
  font-size: var(--fs-micro);
  color: var(--ink-3);
  white-space: nowrap;
}

@media (max-height: 780px) {
  .c-transport {
    height: 36px;
  }
}

[data-mode="present"] .c-transport {
  height: 52px;
}
</style>