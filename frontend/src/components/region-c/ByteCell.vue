<template>
  <div
    class="c-byte"
    :role="ghost ? 'presentation' : 'gridcell'"
    :tabindex="ghost ? -1 : active ? 0 : -1"
    :aria-label="ghost ? undefined : initialLabel"
    :aria-hidden="ghost ? 'true' : undefined"
    :data-row="row"
    :data-col="col"
    :data-index="ghost ? undefined : index"
    :data-ghost="ghost ? 'true' : undefined"
    data-bd="idle"
    data-txr="none"
  >
    <span class="c-byte__stage">
      <span class="c-byte__val is-current">—</span>
      <span class="c-byte__val is-incoming" aria-hidden="true">—</span>
</span>
    <span class="c-byte__key" aria-hidden="true"></span>
    <span class="c-byte__corner" data-corner="" aria-hidden="true"></span>
    <span class="c-byte__corner" data-corner="" aria-hidden="true"></span>
    <span class="c-byte__sup c-byte__sup--neq" data-active="false" aria-hidden="true">≠</span>
    <span class="c-byte__sup c-byte__sup--xor" data-active="false" aria-hidden="true">⊕</span>
    <span class="c-byte__hint" aria-hidden="true">←1</span>
  </div>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  index: number
  row: number
  col: number
  active: boolean
  ghost?: boolean
}>(), {
  ghost: false,
})

const initialLabel = props.ghost
  ? ''
  : `第 ${props.row + 1} 行第 ${props.col + 1} 列，字节 ${props.index}，值 —`
</script>

<!-- 字节格类名是视觉规范的全局语汇（.c-byte / .c-byte__x / .is-x），
     七态样式必须能被 useMatrixWriter 写的 className 直接命中，因此不 scoped。 -->
<style>
.c-byte {
  --key-bar-w: 3px;
  --changed-bar-h: 2px;
  --error-bar-h: 2px;

  position: relative;
  box-sizing: border-box;
  width: var(--cell-size);
  height: var(--cell-size);
  display: flex;
  align-items: center;
  justify-content: center;
  border: var(--rule-region-w) solid var(--rule-region-ink);
  border-radius: var(--r-cell);
  background-color: var(--st-idle-fill);
  color: var(--ink-1);
  font-family: var(--font-mono);
  font-size: var(--fs-byte);
  font-weight: 500;
  letter-spacing: var(--ls-hex-cell);
  font-variant-numeric: tabular-nums;
}

.c-byte__stage {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.c-byte__val {
  position: absolute;
  line-height: 1;
}

.c-byte__val.is-incoming {
  opacity: 0;
}

.c-byte__corner,
.c-byte__sup {
  display: none;
  position: absolute;
}

.c-byte__hint {
  display: none;
}

/* reduced-motion 静态信息补偿：仍在格内绝对定位，不新增布局。 */
.c-byte.is-cue .c-byte__hint {
  display: block;
  position: absolute;
  right: 2px;
  bottom: 2px;
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  line-height: 1;
  color: var(--ink-2);
}

.c-byte.is-cue-xor .c-byte__sup--xor {
  display: block;
  position: absolute;
  top: calc(-1 * var(--sp-1) / 2);
  right: calc(-1 * var(--sp-1) / 2);
  font-family: var(--font-ui);
  font-size: var(--fs-micro);
  line-height: 1;
  color: var(--accent);
}

.c-byte__key {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  pointer-events: none;
  font-family: var(--font-mono);
  font-size: var(--fs-label);
  letter-spacing: var(--ls-hex-cell);
  color: var(--ink-2);
}

/* AddRoundKey：密钥层 0→0.6 120ms → 保持 → 0.6→0 120ms；
   底色纸→石墨 160ms；数值 steps(4) 80ms 离散跳变。总 480ms。 */
@keyframes c-key-layer {
  0% { opacity: 0; }
  25% { opacity: 0.6; }
  75% { opacity: 0.6; }
  100% { opacity: 0; }
}

@keyframes c-add-round-fill {
  0%, 24% {
    background-color: var(--st-idle-fill);
    background-image: none;
  }
  58%, 100% {
    background-color: var(--st-key-fill);
    background-image: var(--st-key-hatch);
  }
}

@keyframes c-value-step {
  from {
    transform: translateY(0.35em);
    opacity: 0.35;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.c-byte.is-add-round {
  animation: c-add-round-fill 480ms linear both;
}

.c-byte.is-add-round .c-byte__key {
  animation: c-key-layer 480ms linear both;
}

.c-byte.is-add-round .c-byte__val.is-current {
  animation: c-value-step 80ms steps(4, end) 280ms forwards;
}

@media (prefers-reduced-motion: reduce) {
  .c-byte.is-add-round,
  .c-byte.is-add-round .c-byte__key,
  .c-byte.is-add-round .c-byte__val.is-current {
    animation: none;
  }
}

[data-motion="reduced"] .c-byte.is-add-round,
[data-motion="reduced"] .c-byte.is-add-round .c-byte__key,
[data-motion="reduced"] .c-byte.is-add-round .c-byte__val.is-current {
  animation: none;
}

/* changed：黄底 + 顶部厚条 + 右上琥珀角标 */
.c-byte.is-changed {
  background-color: var(--st-changed);
  box-shadow: inset 0 var(--changed-bar-h) 0 var(--st-changed-bar);
  font-weight: 600;
}

.c-byte.is-changed .c-byte__corner[data-corner="tr"] {
  display: block;
  top: 0;
  right: 0;
  width: var(--flag-size);
  height: var(--flag-size);
  background-color: var(--st-changed-bar);
}

/* 诊断批注目标：1.5px 红线描边，静止后常驻，不动布局 */
.c-byte.is-diag-target {
  outline: 1.5px solid var(--st-error);
  outline-offset: 3px;
  animation: c-diag-trace 120ms var(--e-out-quart) both;
}

@keyframes c-diag-trace {
  from {
    outline-color: transparent;
  }
  to {
    outline-color: var(--st-error);
  }
}

@media (prefers-reduced-motion: reduce) {
  .c-byte.is-diag-target {
    animation: none;
  }
}

[data-motion="reduced"] .c-byte.is-diag-target {
  animation: none;
}

/* selected：边框改 accent + 内 1px inset + 外 3px 环；不用四角刻线 */
.c-byte.is-selected {
  border-color: var(--accent);
  outline: 3px solid var(--accent-ring);
  outline-offset: 2px;
  box-shadow: inset 0 0 0 1px var(--accent);
  color: var(--accent-strong);
  font-weight: 600;
}

.c-byte.is-changed.is-selected {
  box-shadow:
    inset 0 var(--changed-bar-h) 0 var(--st-changed-bar),
    inset 0 0 0 1px var(--accent);
}

/* error：红底 + 红边 + 右下折角 + 底条 + ≠ 上标 */
.c-byte.is-error {
  border-color: var(--st-error);
  background-color: var(--st-error-fill);
  box-shadow: inset 0 calc(-1 * var(--error-bar-h)) 0 var(--st-error);
  color: var(--st-error);
  font-weight: 600;
}

.c-byte.is-error:not(.is-downstream) .c-byte__corner[data-corner="br"] {
  display: block;
  right: 0;
  bottom: 0;
  width: calc(var(--flag-size) * 2);
  height: calc(var(--flag-size) * 2);
  background-color: var(--st-error);
  clip-path: polygon(100% 0, 100% 100%, 0 100%);
}

.c-byte.is-error:not(.is-downstream) .c-byte__sup--neq {
  display: block;
  top: calc(-1 * var(--sp-1) / 2);
  right: calc(-1 * var(--sp-1) / 2);
  font-family: var(--font-ui);
  font-size: var(--fs-micro);
  line-height: 1;
  color: var(--st-error);
}

/* error + selected：红底红边 + 近黑外环；外环与右下折角不重叠 */
.c-byte.is-error.is-selected {
  border-color: var(--st-error);
  outline-color: var(--ink-1);
  box-shadow:
    inset 0 calc(-1 * var(--error-bar-h)) 0 var(--st-error),
    inset 0 0 0 1px var(--accent);
  color: var(--st-error);
}

/* downstream：只降不改；边框走 --st-downstream-border 一层令牌，演示态自动不降 */
.c-byte.is-downstream {
  border-color: var(--st-downstream-border);
  background-color: var(--st-downstream-fill);
  color: var(--st-downstream-ink);
  font-weight: 400;
}

/* key：石墨底 + 45° 斜纹 + 左侧竖条；不改边框 */
.c-byte.is-key {
  background-color: var(--st-key-fill);
  background-image: var(--st-key-hatch);
  box-shadow: inset var(--key-bar-w) 0 0 var(--st-key-ink);
}

/* changed + key：黄底保留，斜纹保留，左竖条保留 */
.c-byte.is-changed.is-key {
  background-color: var(--st-changed);
  background-image: var(--st-key-hatch);
  box-shadow:
    inset 0 var(--changed-bar-h) 0 var(--st-changed-bar),
    inset var(--key-bar-w) 0 0 var(--st-key-ink);
}

/* done：无纹理、实线 + 左下缺口（纸色方块压上去，不断 border） */
.c-byte.is-done {
  color: var(--ink-3);
  font-weight: 400;
}

.c-byte.is-done .c-byte__corner[data-corner="bl"] {
  display: block;
  left: 0;
  bottom: 0;
  width: calc(var(--flag-size) * 2);
  height: calc(var(--flag-size) * 2);
  background-color: var(--paper-0);
}

/* 演示态：只放大承载厚度的通道，不换语义 */
[data-mode="present"] .c-byte {
  --key-bar-w: 6px;
  --changed-bar-h: 3px;
  --error-bar-h: 3px;
}

[data-mode="present"] .c-byte.is-selected {
  outline-width: 5px;
}

[data-mode="present"] .c-byte.is-error:not(.is-downstream) .c-byte__corner[data-corner="br"] {
  width: calc(var(--flag-size) * 2.5);
  height: calc(var(--flag-size) * 2.5);
}
</style>