<template>
  <canvas ref="canvasEl" class="c-matrix__fx" aria-hidden="true"></canvas>
</template>

<script setup lang="ts">
import { onMounted, onScopeDispose, ref } from 'vue'

const canvasEl = ref<HTMLCanvasElement | null>(null)
let ctx: CanvasRenderingContext2D | null = null
let rafId = 0
let scanRafId = 0
let width = 0
let height = 0
let scans: { column: number; start: number }[] = []

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

function scanColumn(column: number, delay = 0): void {
  const canvas = canvasEl.value
  const parent = canvas?.parentElement
  if (!canvas || !ctx || !parent) return
  const context = ctx

  const cell = Number.parseFloat(getComputedStyle(parent).getPropertyValue('--cell-size')) || 62
  const gap = Number.parseFloat(getComputedStyle(parent).gap) || 6
  const accent = getComputedStyle(document.documentElement).getPropertyValue('--accent').trim()
  const accentSoft = getComputedStyle(document.documentElement).getPropertyValue('--accent-soft').trim()
  const start = performance.now() + delay

  canvas.style.visibility = 'visible'
  scans.push({ column, start })
  if (scanRafId) return

  const tick = (): void => {
    const now = performance.now()
    context.clearRect(0, 0, width, height)
    scans = scans.filter((scan) => now < scan.start + 280 + 600)

    for (const scan of scans) {
      const scanProgress = Math.min(Math.max((now - scan.start) / 280, 0), 1)
      const fadeProgress = Math.min(Math.max((now - scan.start - 280) / 600, 0), 1)
      const columnX = scan.column * (cell + gap)

      if (scanProgress < 1) {
        context.globalAlpha = 1
        context.strokeStyle = accent
        context.lineWidth = 1
        context.beginPath()
        context.moveTo(columnX + cell / 2 + 0.5, 0)
        context.lineTo(columnX + cell / 2 + 0.5, scanProgress * height)
        context.stroke()
      }

      if (scanProgress >= 1 && fadeProgress < 1) {
        context.globalAlpha = 0.12 * (1 - fadeProgress)
        context.fillStyle = accentSoft
        for (let row = 0; row < 4; row++) {
          context.fillRect(columnX, row * (cell + gap), cell, cell)
        }
      }
    }

    context.globalAlpha = 1

    if (scans.length > 0) {
      scanRafId = requestAnimationFrame(tick)
    } else {
      scanRafId = 0
      canvas.style.visibility = 'hidden'
    }
  }

  scanRafId = requestAnimationFrame(tick)
}

function clear(): void {
  cancelAnimationFrame(rafId)
  cancelAnimationFrame(scanRafId)
  rafId = 0
  scanRafId = 0
  scans = []
  ctx?.clearRect(0, 0, width, height)
  if (canvasEl.value) canvasEl.value.style.visibility = 'hidden'
}

onScopeDispose(() => {
  cancelAnimationFrame(rafId)
  cancelAnimationFrame(scanRafId)
})

defineExpose({ flashRow, scanColumn, clear })
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