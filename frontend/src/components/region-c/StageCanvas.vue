<template>
  <canvas ref="canvasEl" class="c-matrix__fx" aria-hidden="true"></canvas>
</template>

<script setup lang="ts">
import { onMounted, onScopeDispose, ref } from 'vue'

const canvasEl = ref<HTMLCanvasElement | null>(null)
let ctx: CanvasRenderingContext2D | null = null
let rafId = 0
let width = 0
let height = 0

onMounted(() => {
  const canvas = canvasEl.value
  const parent = canvas?.parentElement
  if (!canvas || !parent) return

  const dpr = window.devicePixelRatio || 1
  width = parent.clientWidth
  height = parent.clientHeight
  canvas.width = Math.round(width * dpr)
  canvas.height = Math.round(height * dpr)
  ctx = canvas.getContext('2d')
  ctx?.setTransform(dpr, 0, 0, dpr, 0, 0)
  canvas.style.visibility = 'hidden'
})

function flashRow(row: number): void {
  const canvas = canvasEl.value
  const parent = canvas?.parentElement
  if (!canvas || !ctx || !parent) return
  const context = ctx

  const cell = Number.parseFloat(getComputedStyle(parent).getPropertyValue('--cell-size')) || 62
  const gap = Number.parseFloat(getComputedStyle(parent).gap) || 6
  const accent = getComputedStyle(document.documentElement).getPropertyValue('--accent').trim()
  const start = performance.now()

  canvas.style.visibility = 'visible'
  cancelAnimationFrame(rafId)

  const tick = (): void => {
    const progress = Math.min((performance.now() - start) / 60, 1)
    context.clearRect(0, 0, width, height)
    context.globalAlpha = 1 - progress
    context.strokeStyle = accent
    context.lineWidth = 1

    const y = row * (cell + gap)
    for (let col = 0; col < 4; col++) {
      const x = col * (cell + gap)
      context.strokeRect(x + 0.5, y + 0.5, cell - 1, cell - 1)
    }

    if (progress < 1) {
      rafId = requestAnimationFrame(tick)
    } else {
      context.globalAlpha = 1
      canvas.style.visibility = 'hidden'
    }
  }

  rafId = requestAnimationFrame(tick)
}

onScopeDispose(() => {
  cancelAnimationFrame(rafId)
})

defineExpose({ flashRow })
</script>

<style scoped>
.c-matrix__fx {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}
</style>