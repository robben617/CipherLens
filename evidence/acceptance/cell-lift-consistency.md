# 全站小正方形格子立体效果验收证据

- 范围：只改视觉表现，不改功能、交互、主题色、格子几何
- 验收时间：2026-11-24

## 1. 全站扫描命中位置

### 大格（完整版凸起）

| 位置 | 说明 |
|---|---|
| `components/region-c/ByteCell.vue` | 工作台字节矩阵，16 格、七态 |
| `components/region-c/MatrixStage.vue` | 工作台 4×4 整体视图矩阵容器 |
| `components/region-c/StepCompare.vue` | 单步前后对照矩阵（前后各 16 格） |
| `components/home/HeroMatrix.vue` | 首页活体演示 4×4 矩阵 |
| `components/sbox/SBoxIntroAnimation.vue` | S 盒介绍动画 4×4 示意格 |
| `views/AvalancheView.vue` | 雪崩实验 16 格密文块 |

### 密集网格（压紧版凸起）

| 位置 | 说明 |
|---|---|
| `views/AvalancheView.vue` 16×8 位图格 | 边长 18×6，行列间距 2px |
| `components/sbox/SBoxGrid.vue` 16×16 查表 | 256 格，间距 2px |

范围外：长条形按钮、标签、进度块、步骤 chip，未改动。

## 2. 改动文件

- `frontend/src/styles/tokens.css`
  - `--cell-lift-edge`: `oklch(0.790 …)` → `oklch(0.600 0.0100 250)`（厚度边加深，看得见）
  - `--cell-lift-soft`: `0 3px 5px rgba(…,.10)` → `0 3px 6px rgba(…,.18)`
  - `--cell-lift-soft-tight`: `0 1px 2px` → `0 1px 1px`（密集网格外扩 ≤1px）
  - 演示态：edge `0.650` → `0.560`，soft `16%` → `20%`（实色边，不依赖软阴影）
- `frontend/src/components/region-c/ByteCell.vue`
  - selected / 刚写入外环：`2px solid var(--accent-ring)` → `2px solid var(--st-selected)`
- `frontend/src/components/region-c/MatrixStage.vue`
  - `.c-row` 从 `overflow: hidden` 改为 `overflow-x: clip; overflow-y: visible`：只裁行平移露出的鬼格，保留格子的 2px 厚度与 6px 投影
- `frontend/src/styles/base.css`
  - 打印时隐藏当前顶栏 `.shellbar`（原 `.shell__bar` 已过时）

## 3. 实测（1440×900，CDP 计算样式）

| 项 | 结果 |
|---|---|
| 完整版 idle | `inset 0 1px 0 #fff/.95` + `inset 1px 0 0 #fff/.55` + `0 2px 0 oklch(.600)` + `0 3px 6px rgba(.18)` |
| 托盘 | `--cell-lift-tray = paper-1`（`oklch(0.962 0.0035 250)`），格间 6px 露出 |
| changed | 填充 `--st-changed`，厚度边 `--st-changed-bar`，无外圈 |
| selected / 刚写入 | `outline: 2px solid var(--st-selected)`，凸起不变 |
| key | 斜纹 + 左竖条 + 完整凸起 |
| downstream | 厚度 1px，软影 `0 2px 3px rgba(.06)`，凸起仍在 |
| error | 红填充 + 红色厚度边 |
| done | 去纹理，凸起保留 |
| 几何 | 七态 width/height 140×140、border 1px 全部不变 |
| 密集网格 | `inset top + 0 1px 0 edge + 0 1px 1px rgba(.10)`，外扩 1px |
| 打印 | `0 1px 0 edge, 0 0 0 1px edge` 实线 + `print-color-adjust: exact`，shellbar 隐藏 |
| 演示态 | depth 3px、edge `oklch(0.560)`、soft 20% |
| reduced-motion | S 盒格 `transition: none`；字节格无显式过渡 |
| 行位移动画 | `overflow-x: clip` / `overflow-y: visible`；页面 `scrollWidth=clientWidth`，16 实格正常 |

## 4. 回归

- Playwright 全量 21/21
- vitest 149/149
- `vue-tsc`、`vite build` 通过
- 截图：`output/cell-lift-final/{workbench-matrix-strong,matrix-clip,workbench-compare,home,sbox-grid,avalanche,shiftrows-anim}.png`

## 5. 已知边界

- 托盘 `paper-1` 与格子 `paper-0` 的色差很小，立体感主要由 2px 实色厚度边与软投影承担；未改动主题令牌。
- 密集网格只用 1px 厚度与 1px 短影，避免相邻投影叠灰。
- 未改 `border-width`、`padding`、`width`、`height`、`--cell-size`、`--cell-gap`，未改任何交互逻辑。