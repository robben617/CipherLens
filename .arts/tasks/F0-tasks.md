# CipherLens F0 · 脚手架与设计令牌落地 —— 编码任务清单

| 项 | 内容 |
|---|---|
| 功能点 | F0 · 脚手架与设计令牌落地 |
| 文档类型 | 编码任务清单（tasks.md） |
| 输入 | `.arts/design/F0-design.md`、`README.md`、`docs/` 权威文档 |
| 输出路径 | `.arts/tasks/F0-tasks.md` |
| 本轮边界 | 只产出任务清单；不初始化工程、不写业务代码、不提交、不推送 |
| 任务总数 | 7 个主任务 / 20 个子任务 |
| 验收目标 | F0 验收 1–4 + 工程纪律 5 条 |

> **流程说明**：按 SDD 规范，`tasks.md` 应位于 `.codeartsdoer/specs/<feature>/`，且需 `spec.md` + `design.md`。本仓库实际设计产物在 `.arts/design/F0-design.md`，用户本轮明确指定输出 `.arts/tasks/F0-tasks.md`。本清单按用户指定路径执行，不修改 `docs/` 下任何文件。
>
> **执行方式**：F0 整体作为**一个功能点**。实现 Agent 一次只做一个子任务，完成一个即按“完成判据”自检；全部子任务完成、F0 自检通过后**停止**，等待用户自行提交。不要把 F0 再拆成多个需要用户确认的功能点。

---

## 0. 执行前口径（先读，不改文档）

### 0.1 必读清单

- `.arts/design/F0-design.md` 全文，重点 §2.2.3、§2.3、§2.4、§2.5、§2.8、§2.9、§2.10。
- `README.md`：五条硬约束、目录规划、开发纪律。
- `docs/CipherLens-视觉设计规范-v1.2.md`：§3.1（字体）、§4.1（五区）、§10（令牌全集）。
- `docs/CipherLens-前端实现规格与Coding-Agent提示词-v1.9.md`：§1.1（目录）、§1.2（组件树）、§10（承接记录与禁止项）。
- `docs/CipherLens-信息架构与交互规格-v1.3.md`：§2.1（五区）、§2.2（职责表）。
- `docs/CipherLens-华为CodeArts-分功能开发提示词手册-v1.0.md`：§4 F0。
- `docs/CipherLens-视觉设计流程与Coding-Agent提示词-v1.0.md`：§4.6（冻结口径）、§7.1（可自动化验收）。

### 0.2 固定口径（本轮按此执行）

| 事项 | 取值 | 依据 | 状态 |
|---|---|---|---|
| 前端工程位置 | `frontend/` | README 目录规划 | 已确认 |
| 脚手架方式 | 手写最小工程，锁 Vite 5 | 技术栈锁定；禁止 `npm create vite@latest` | 已确认 |
| B 区宽度 | `var(--input-col)` = 268px | 视觉规范 §4.1/§6.8/§10 | **执行中，待用户复核** |
| E 区宽度 | `var(--ai-col)` = 360px | 视觉规范 §4.1/§10 | **执行中，待用户复核** |
| 五区占位 | 只在 `WorkbenchView.vue` 内放 5 个 `section[data-region]` | 手册 F0 第 6 条；F4 才拆真实组件 | 已确认 |
| 令牌落地 | 完整照抄 §10 的 7 个作用域 | 手册“全部令牌” + 验收“缺一不可” | 已确认 |
| 空目录 | 不创建 | 禁止预建空 store / 空 composable / 空组件 | 已确认 |
| 字体 | 不引入 webfont，先用系统回退 | F0 不验收字体；避免新增依赖 | 已确认 |
| 验收视口 | 1440×900 主，1920×1080 复核 | 避开 `max-height:780px` 压缩档 | 已确认 |

> **宽度口径标注（必须写进验收证据）**：F0 按 268/360 执行，依据《视觉设计规范》§10 令牌；《分功能开发提示词手册》F0/F4 中的 280/380 口径**待用户复核**。**不得自行新增** `--wb-input-col` / `--wb-ai-col` 等派生令牌。

### 0.3 待用户复核项（不阻塞执行，但必须在证据中标注）

1. **P0 宽度**：B/E 取 268/360（推荐）还是 280/380（手册口径）。若改判 280/380，必须另行批准 2 个派生令牌或修改令牌值，**不得由实现 Agent 自行决定**。
2. **P1 令牌偏离**：`--st-idle-border`、`--st-done-border` 是否允许改为 `var(--rule-region-ink)`。本轮按“允许偏离”执行，对账表标“有意偏离 1/2”。
3. **P1 作用域**：`tokens.css` 完整落地 §10 的 7 个作用域（含 roomy、max-height、两处 reduced），不只 `:root` / compact / present 三块。
4. **P2 任务文档提交**：`.arts/tasks/F0-tasks.md` 是否随 F0 提交，由用户决定；默认建议只提交 `frontend/` 与 `evidence/acceptance/`。
5. **P2 流程路径偏离**：本仓库使用 `.arts/design` 与 `.arts/tasks`，不是 `.codeartsdoer/specs/<feature>/`；需在评审时说明。

### 0.4 全局禁止项（F0 全程适用）

- **不碰业务**：AES 引擎、S 盒、密钥扩展、trace、diff、矩阵、字节格、Canvas、SVG 装饰、时间轴四轨、播放控制、动效、演示态、AI 辅导、SSE、判分、记录、抽屉、快捷键、URL 状态、错误边界、后端 FastAPI/SQLite。
- **不建目录**：`src/components/`、`src/composables/`、`src/stores/`、`src/engine/`、`src/types/`、`src/canvas/`、`src/svg/`、`src/data/`、`src/assets/`、`public/`、`scripts/`、`docker/`。
- **不建文件**：`.env.example`、`motion.css`、`reduced-motion.css`、`frontend/.gitignore`、`tsconfig.node.json`、`HelloWorld.vue`、`vue.svg`、`vite.svg`、模板 `style.css`。
- **不装依赖**：任何 UI 组件库、图标库、CSS 框架、Tailwind、GSAP、axios、`@fontsource/*`、ESLint、Prettier、Vitest、Playwright、`@types/node`、Sass/Less。
- **不执行**：`npm create vite@latest`、`git add`、`git commit`、`git push`；不修改 `docs/`、`README.md`、根 `.gitignore`。
- **不写**：`!important`、内联 `style="..."`、`console.log` / `console.error`、`border-width`、硬编码颜色（`#rrggbb` / `oklch()` / `rgb()` / `hsl()`）、硬编码 px 视觉值（`tokens.css` 与 `.sr-only` 白名单除外）、`position: fixed`、F0 布局 `@media`、`ResizeObserver`、`window.resize`。
- **不挂**：`data-mode="present"`、`data-motion="reduced"`（F0 不启用演示/减动效入口）；`WorkbenchView` 根只挂 `data-density="compact"`。
- **不做**：404 路由、导航守卫、`meta.title`、响应式折叠、B/E 折叠、C 区正方形、1120/1024 适配、首页视觉、AppBar。

---

## 1. 建立可运行的最小前端工程

### 1.1 编写工程配置与入口文件

- [ ] 在 `frontend/` 下创建 5 个工程文件，形成可安装的最小 Vite 5 + Vue 3.5 + TS 工程
  - **做什么**：手写 `package.json`、`index.html`、`vite.config.ts`、`tsconfig.json`、`src/env.d.ts`；依赖、脚本、编译选项按设计文档 §2.4.2–§2.4.4、§2.4.6 执行。
  - **文件**：`frontend/package.json`、`frontend/index.html`、`frontend/vite.config.ts`、`frontend/tsconfig.json`、`frontend/src/env.d.ts`。
  - **依赖**：无。
  - **完成判据**：
    - 5 个文件存在；`package.json` 直接依赖**恰好 7 个**：`vue`、`vue-router`、`pinia`、`vite`、`@vitejs/plugin-vue`、`typescript`、`vue-tsc`；主版本锁定 vue 3 / vue-router 4 / pinia 2 / vite 5 / typescript 5 / vue-tsc 2；无 `latest`。
    - scripts 含 `dev`、`build`（`vue-tsc --noEmit && vite build`）、`preview`、`typecheck`；`private: true`、`type: "module"`、`engines.node >=20.0.0`。
    - `index.html` 含 `lang="zh-CN"`、`<meta name="color-scheme" content="light">`、`<title>CipherLens · 密码透镜</title>`、`#app`、`/src/main.ts`。
    - `tsconfig.json` 按 §2.4.4 设置 `strict`、`noUncheckedIndexedAccess`、`noUnusedLocals`、`noUnusedParameters`、`verbatimModuleSyntax`、`noEmit`、`moduleResolution: "Bundler"`；`include` 覆盖 `src` 与 `vite.config.ts`。
    - `vite.config.ts` 只注册 `@vitejs/plugin-vue`；不配 `base`、`server`、`build`、`resolve.alias`。
    - 无模板 logo / HelloWorld / `vue.svg` / `vite.svg` / 模板 `style.css`。
  - **覆盖验收**：1（前置）。
  - **不做**：不执行 `npm create vite@latest`；不建 `tsconfig.node.json`、`.env.example`、`public/`、`assets/`、`components/`、`stores/`、`composables/`、`engine/`、`types/`、`canvas/`、`svg/`、`data/`、`scripts/`。

### 1.2 安装依赖并锁定版本

- [ ] 在 `frontend/` 下执行 `npm install`，生成并保留 `package-lock.json`，实测 Node 24 与 Vite 5 兼容
  - **做什么**：记录 `node -v`、`npm -v`；执行 `npm install`；确认 `vite` 实际版本为 5.x；确认 7 个直接依赖无缺失/多余。
  - **文件**：`frontend/package-lock.json`（生成）、`frontend/node_modules/`（不提交）。
  - **依赖**：1.1。
  - **完成判据**：`npm install` 退出码 0；`package-lock.json` 生成；`npm ls --depth=0` 只显示 7 个直接依赖；`vite` 为 5.x；无 `EBADENGINE` / peer 冲突导致的 error。
  - **失败处理**：停止并贴完整报错；**不**换 pnpm/yarn；**不**升级 Vite 主版本；**不**擅自切 Node 20；由用户裁决。
  - **覆盖验收**：1（前置）。
  - **不做**：不安装任何额外包；不提交 `node_modules/`。

---

## 2. 落地设计令牌 `tokens.css`

### 2.1 写 `:root` 常规令牌

- [ ] 创建 `frontend/src/styles/tokens.css`，先逐字照抄视觉规范 §10 的 `:root` 块
  - **做什么**：按 §10 的分组顺序写入字体、字号、行高、字距、中性/表面、强调、七态、间距、尺寸、时间轴、结构线、角标、阴影、动效、焦点、层级；保留原分组注释；变量名与值一个字不改。
  - **文件**：`frontend/src/styles/tokens.css`。
  - **依赖**：1.2。
  - **完成判据**：
    - `:root` 变量集合与 §10 一致；`--paper-0` 值为 `oklch(0.981 0.0025 250)`。
    - 无组件选择器（文件内只有 `:root` 及注释）；无新增令牌；无改名；无 `!important`。
    - 包含 `--font-*`、`--fs-*`、`--lh-*`、`--ls-*`、`--paper-*`、`--surface-*`、`--line-*`、`--ink-*`、`--accent*`、`--st-*`、`--sp-*`、`--cell-*`、`--r-*`、`--topbar-h`、`--transport-h`、`--diag-row-h`、`--ai-col`、`--input-col`、`--tl-*`、`--rule-*`、`--flag-size`、`--shadow-*`、`--e-*`、`--d-*`、`--step-interval`、`--focus-*`、`--z-*`。
  - **覆盖验收**：3、4。
  - **不做**：不写 compact/roomy/present/max-height/reduced 覆盖块；不写 `body`、`.workbench` 等选择器；不把 §10 的 7 块压成 3 块。

### 2.2 追加 6 个覆盖作用域

- [ ] 在 `:root` 之后按固定顺序追加 6 个覆盖块，形成 §10 的 7 个作用域
  - **做什么**：依次写 `[data-density="compact"]`、`[data-density="roomy"]`、`@media (max-height: 780px)`、`[data-mode="present"]`、`@media (prefers-reduced-motion: reduce)`、`[data-motion="reduced"]`；每块变量名与值逐字照抄 §10。
  - **文件**：`frontend/src/styles/tokens.css`。
  - **依赖**：2.1。
  - **完成判据**：
    - 7 个作用域齐全，**块顺序不可调换**：`:root` → compact → roomy → max-height → present → prefers-reduced-motion → `[data-motion="reduced"]`。
    - compact 含 8 个 `--sp-*`、`--fs-body`、`--lh-body`、`--measure`、`--r-control`；roomy 使用同名变量换值。
    - max-height 覆盖 `--topbar-h`（52）、`--transport-h`（92）、四带、`--tl-cursor-h`、`--sp-6`、`--sp-8`。
    - present 覆盖 §10 全部；重点核对 `--ai-col: 48px`、`--rule-region-ink: oklch(0.545 0.0120 258)`、`--line-default: oklch(0.760 0.0080 250)`、`--st-downstream-border: var(--rule-region-ink)`、`--d-3: 340ms`。
    - 两处 reduced 只把 `--d-1`–`--d-4`、`--d-linger`、`--d-fade-linger` 归零；`--step-interval` 不动。
    - `--measure` 只出现在 compact / roomy，不当作 `:root` 缺失。
  - **覆盖验收**：3。
  - **不做**：不省略 roomy / max-height；不合并两处 reduced；不改 present 块的 0.545 / 0.760 关系；不新增媒体查询。

### 2.3 处理 2 处白名单偏离

- [ ] 将 `--st-idle-border`、`--st-done-border` 改为 `var(--rule-region-ink)`，并在原行注释中标注依据与待批准状态
  - **做什么**：只改这两行；其余令牌保持 §10 字面值；注释写明“有意偏离 §10，依据 README 五条硬约束第 2 条、前端规格 §10.6/§10.12、视觉规范 §7.1；待用户批准”。
  - **文件**：`frontend/src/styles/tokens.css`。
  - **依赖**：2.1；执行顺序在 2.2 之后。
  - **完成判据**：两行值均为 `var(--rule-region-ink)`；注释存在；全文件无第三处偏离；对账表可标记“有意偏离 1/2”。
  - **回退分支**：若用户复核**否决**偏离，改回 `var(--line-default)`，注释改为“F7 开工前必须复查：演示态应取 `--rule-region-ink`”；对账表偏离数改 0，并在 `F0.md` 记录“F7 复查项”。
  - **覆盖验收**：3。
  - **不做**：不顺带改 `--st-downstream-border`（它的常规值是 `var(--line-hairline)`、present 值是 `var(--rule-region-ink)`，不要在 F0 动）；不新增第三个例外。

---

## 3. 落地基础样式 `base.css`

### 3.1 写 reset、字体、可访问性与焦点环基础

- [ ] 创建 `frontend/src/styles/base.css`，只写全局基础样式，不写任何组件/布局视觉
  - **做什么**：最小 reset（`box-sizing`、`margin`/`padding`、媒体元素）；`body` 字体栈、字号、行高、墨色、纸底；`font-variant-numeric: tabular-nums`；`.sr-only`（按无障碍常量写，并注释白名单）；`:focus-visible` 焦点环；`[data-motion="reduced"]` 只留注释占位，指明覆盖在 `tokens.css`。
  - **文件**：`frontend/src/styles/base.css`。
  - **依赖**：2.2（需要完整令牌）。
  - **完成判据**：
    - `body` 背景为 `var(--paper-0)`；字体为 `var(--font-ui)`；字号/行高/墨色均引令牌。
    - `.sr-only` 使用 `1px` / `-1px` 等无障碍常量，并在文件中用注释标明这是白名单，不属于视觉硬编码。
    - 除 `.sr-only` 外，文件内无颜色字面量、无 px 字面量。
    - 无 `!important`；无 `.workbench` / `h1` / 按钮 / 卡片 / 阴影 / 分区线样式；无布局 `@media`。
    - `[data-motion="reduced"]` 没有重复声明 `--d-*`，只留“覆盖见 tokens.css”的注释占位。
  - **覆盖验收**：4（旁证）、6.5（扫描）。
  - **不做**：不引入字体文件；不写 Workbench Grid；不写组件选择器；不写 `position: fixed`。

---

## 4. 搭工作台五区静态空壳

### 4.1 写 `WorkbenchView.vue` 的 Grid 结构

- [ ] 创建 `frontend/src/views/WorkbenchView.vue`，用纯 CSS Grid 搭出 A/B/C/D/E 五区骨架
  - **做什么**：根节点 `<main class="workbench" data-density="compact">`；5 个 `<section data-region="a|b|c|d|e" class="workbench__region">`，DOM 顺序 a → b → c → d → e；3 列 × 3 行；`grid-template-areas` 为 `"a a a"` / `"b c e"` / `"d d d"`；列用 `var(--input-col) minmax(0, 1fr) var(--ai-col)`；行用 `var(--topbar-h) minmax(0, 1fr) var(--transport-h)`；高度先 `100vh` 后 `100dvh`。
  - **文件**：`frontend/src/views/WorkbenchView.vue`。
  - **依赖**：2.2、3.1。
  - **完成判据**：
    - 5 个 `section[data-region]` 存在，值唯一为 a–e；`grid-area` 与 DOM 顺序一致。
    - C 区有 `min-width: 0; min-height: 0`；B/E 有 `min-width: 0; overflow: hidden`；A/D 有 `min-height: 0`。
    - 所有尺寸引令牌；无 px / 颜色字面量；无 `position: fixed`；无 `@media`、`ResizeObserver`、`window.resize`。
    - 根节点只挂 `data-density="compact"`；不挂 `data-mode` / `data-motion`。
    - 无按钮、输入框、链接、图标、`id`、`role`、`tabindex`、`aria-*`。
  - **覆盖验收**：2。
  - **不做**：不拆 `components/region-a..e/`；不建 `components/`；不做折叠、响应式、C 区正方形；不填真实内容。

### 4.2 写分区线与五区占位块

- [ ] 在 `WorkbenchView.vue` 内补 5 个占位 `<p>` 和单向分区线
  - **做什么**：每区只放一个 `<p>`，文字固定为“A · 上下文条”“B · 输入区”“C · 舞台区”“D · 步进与时间轴”“E · AI 辅导栏”；A 只画 `border-bottom`、B 只画 `border-right`、D 只画 `border-top`、E 只画 `border-left`、C 不画；线宽 `var(--rule-region-w)`、颜色 `var(--line-hairline)`；占位文字用 `var(--font-mono)`、`var(--fs-label)`、`var(--ink-3)`、`var(--ls-label)`；区内边距 `var(--sp-3)`。
  - **文件**：`frontend/src/views/WorkbenchView.vue`。
  - **依赖**：4.1。
  - **完成判据**：
    - 5 条占位文字与设计文档 §2.2.3 完全一致；占位块不写尺寸数字。
    - 4 条分区线各只画一条边；C 区无边框；不使用“容器背景色 + `gap: 1px`”画线。
    - 无背景色差、无阴影、无卡片；`<style scoped>`；无按钮/输入/链接/图标。
    - DevTools 查 A 的 `border-bottom`：宽度为 `var(--rule-region-w)` 计算值（常规态 1px），颜色等于 `--line-hairline` 计算值。
  - **覆盖验收**：2（含 §2.8.2 #12 分区线）。
  - **不做**：不给 A/B/C/D/E 添加交互；不加 `aria-label`；不写真实面板内容。

---

## 5. 打通五条路由与入口

### 5.1 创建 Home 与三条旁路视图

- [ ] 创建 4 个最小视图：`HomeView`、`SBoxView`、`PracticeView`、`RecordsView`
  - **做什么**：`HomeView` 只放 `<h1>CipherLens · 密码透镜</h1>` 和一个到 `/workbench` 的 `RouterLink`（文字“进入工作台”，显式导入 `RouterLink`）；`SBoxView` 只放 `<h1>S 盒浏览器</h1>`；`PracticeView` 只放 `<h1>练习模式</h1>`；`RecordsView` 只放 `<h1>学习记录</h1>`；全部使用 `<script setup lang="ts">`。
  - **文件**：`frontend/src/views/HomeView.vue`、`frontend/src/views/SBoxView.vue`、`frontend/src/views/PracticeView.vue`、`frontend/src/views/RecordsView.vue`。
  - **依赖**：1.2；执行顺序在 4.2 之后。
  - **完成判据**：4 个文件存在；Home 只有标题 + 一个链接；三条旁路只有 `h1`；无 store / composable / 组件 import；无样式块；不挂 `data-density`；无业务文案/按钮/表单。
  - **覆盖验收**：2（路由前置）。
  - **不做**：不做首页视觉、导航、AppBar；不加 `meta`、守卫、404；不引入图片/图标。

### 5.2 创建五条路由表

- [ ] 创建 `frontend/src/router/index.ts`，注册 5 条路由并导出 `router`
  - **做什么**：`/` → `HomeView`（静态 import）；`/workbench` → `WorkbenchView`（动态 import）；`/sbox` → `SBoxView`（动态 import）；`/practice` → `PracticeView`（动态 import）；`/records` → `RecordsView`（动态 import）；`createWebHistory(import.meta.env.BASE_URL)`；`routes` 显式标注 `RouteRecordRaw[]`；命名导出 `router`。
  - **文件**：`frontend/src/router/index.ts`。
  - **依赖**：4.2、5.1。
  - **完成判据**：5 条 path/name/component 正确；Home 静态导入，其余动态导入；无 `any`；无守卫、无 `meta.title`、无 404；`router` 为命名导出；无桶文件。
  - **覆盖验收**：2。
  - **不做**：不使用 hash 模式；不写权限/登录；不把 Workbench 改成静态导入。

### 5.3 创建应用入口与根组件

- [ ] 创建 `frontend/src/main.ts` 与 `frontend/src/App.vue`，把样式、Pinia、Router 接起来
  - **做什么**：`main.ts` 引入顺序固定为 `styles/tokens.css` → `styles/base.css` → `createApp` → `createPinia` → `router` → `App.vue` → `mount('#app')`；`App.vue` 显式导入 `RouterView`，模板只放 `<RouterView />`，不引入样式。
  - **文件**：`frontend/src/main.ts`、`frontend/src/App.vue`。
  - **依赖**：5.2。
  - **完成判据**：引入顺序正确；`createPinia()` 已挂载；无 `src/stores/*`；无 HTTP / 业务初始化；`main.ts` 无默认导出；`App.vue` 无样式、无导航、不挂 `data-density` / `data-mode` / `data-motion`。
  - **覆盖验收**：1、2。
  - **不做**：不建 store；不建 composable；不调 API；不写全局导航。

---

## 6. 构建与验收自检

### 6.1 类型检查与生产构建

- [ ] 在 `frontend/` 下执行 `npm run typecheck` 与 `npm run build`，修到零 TS error
  - **做什么**：运行两条命令；记录终端输出与时间；出现错误只改 F0 文件。
  - **文件**：不新增源文件；必要时修正 §1–§5 已建文件。
  - **依赖**：5.3。
  - **完成判据**：两条命令退出码 0；`dist/` 生成；零 TS error；Vite 编译无 error（warning 需记录）。
  - **失败处理**：不改验收数字；修不动停止并报告，不带缺陷进入提交。
  - **覆盖验收**：1。

### 6.2 五区尺寸实测（1440×900 / 1920×1080）

- [ ] 打开 `/workbench`，在两个视口执行设计文档 §2.8.3 的实测脚本并记录结果
  - **做什么**：`npm run dev`（或 `npm run preview`）后打开 `/workbench`；DevTools 设备模式分别设 1440×900、1920×1080；执行 §2.8.3 脚本，记录 A/B/C/D/E 的 `w/h/x/y`、`innerWidth/innerHeight`、`htmlScroll`、`bodyScroll`。
  - **文件**：无新增；结果写入 `evidence/acceptance/F0.md`（6.6 汇总）。
  - **依赖**：6.1。
  - **完成判据**：
    - A 高 56 ± 0.5；D 高 104 ± 0.5；B 宽 268 ± 0.5；E 宽 360 ± 0.5。
    - C 宽 = `innerWidth - B - E`（1440 下 812；1920 下 1292）；C 高 = `innerHeight - A - D`（1440×900 下 740；1920×1080 下 920）。
    - `htmlScroll === 0`、`bodyScroll === 0`；两视口都通过。
    - **不使用** 1366×768 或任何高度 ≤780 的视口，避免触发 `max-height` 压缩档。
  - **覆盖验收**：2。
  - **待复核**：268/360 是当前口径；若用户改判 280/380，期望值同步改，但**令牌需另行批准**，本任务不得自行改。

### 6.3 令牌对账与 `--paper-0` 实测

- [ ] 按设计文档 §2.5.4 生成 §10 与 `tokens.css` 的逐项对账表，并实测 `--paper-0`
  - **做什么**：提取视觉规范 §10 的 7 个作用域块；按选择器切块、提取变量名与值；与 `tokens.css` 逐块比较；统计缺失/多余/偏离；DevTools 执行 `getComputedStyle(document.documentElement).getPropertyValue('--paper-0').trim()`、`CSS.supports('color', 'oklch(0.981 0.0025 250)')`、`getComputedStyle(document.body).backgroundColor`。
  - **文件**：对账表文本（供 6.6 写入 `evidence/acceptance/F0.md`）；临时脚本只放 `output/` 或命令行内联，**执行后删除、不提交、不放进 `frontend/scripts/`**。
  - **依赖**：2.3、6.1。
  - **完成判据**：
    - 7 个作用域逐块对账；缺失 0、多余 0；有意偏离仅 2 处（若用户批准），每处写明依据。
    - `--paper-0` 原始字符串为 `oklch(0.981 0.0025 250)`；`CSS.supports` 为 `true`；`body` 背景不是 `rgb(255, 255, 255)`。
    - 对账表含“变量名 / §10 值 / tokens.css 值 / 块 / 状态”列；状态只用“一致 / 有意偏离 / 缺失 / 多余”。
  - **覆盖验收**：3、4。
  - **不做**：不接受“已全部落地”无表结论；不在 `frontend/` 新增对账脚本或 `scripts/` 目录。

### 6.4 初始路由 JS gzip 预算

- [ ] 测量 `dist/assets/index-*.js` 的 gzip 大小，确认 < 150KB
  - **做什么**：从 `npm run build` 输出读取 gzip；再用 Node 复核 entry chunk；记录文件名、KB、`dist/assets` 文件数。
  - **文件**：无新增；结果写入 `F0.md`。
  - **依赖**：6.1。
  - **完成判据**：初始路由 JS gzip < 150KB；文件名与 KB 数字完整；若超预算，先查是否误把 Workbench 静态导入、是否引入未使用依赖，**不先加 `manualChunks` 掩盖**。
  - **覆盖验收**：1。

### 6.5 禁止依赖与硬编码扫描

- [ ] 执行设计文档 §2.5.5 的四组扫描与 `npm ls --depth=0`，确认命中数为 0
  - **做什么**：扫描颜色字面量、px 字面量、`!important` / 内联 `style` / `console.*`、`border-width`；扫描 `package.json` 禁止依赖；核对 `.sr-only` 白名单行号。
  - **文件**：无新增；扫描结果写入 `evidence/acceptance/F0.md`（6.6 汇总）。
  - **依赖**：6.1。
  - **完成判据**：
    - 颜色字面量命中 0（`tokens.css`、`env.d.ts` 除外）。
    - px 字面量命中 0（`tokens.css` 除外；若命中 `.sr-only`，必须在证据中标注白名单行号）。
    - `!important`、内联 `style="..."`、`console.log`、`console.error` 命中 0。
    - `border-width` 命中 0。
    - `package.json` 无 `axios` / `tailwind` / `gsap` / `element-plus` / `ant-design` / `naive-ui` / `react` / `next` / `nuxt`。
    - `npm ls --depth=0` 只显示 7 个直接依赖。
  - **覆盖验收**：1、3、依赖合规（§2.8.2 #11）。
  - **不做**：不删除白名单代码来“消命中”；不用注释或配置掩盖命中；不新增 lint 工具。

### 6.6 截图与证据归档

- [ ] 生成 1440×900、1920×1080 两张工作台截图，并写 `evidence/acceptance/F0.md`
  - **做什么**：用浏览器 DevTools 设备模式打开 `/workbench`，分别截图保存；按设计文档附录 B 模板写 `F0.md`，汇总 build、五区尺寸、令牌对账、`--paper-0`、gzip、扫描、截图。
  - **文件**：`evidence/acceptance/F0.md`、`evidence/acceptance/F0-workbench-1440x900.png`、`evidence/acceptance/F0-workbench-1920x1080.png`。
  - **依赖**：6.2、6.3、6.4、6.5。
  - **完成判据**：
    - 两张 PNG 存在，单张 ≤ 500KB；文件名与视口一致。
    - `F0.md` 含：前端路径、视口、build 结果与时间、TS error 数、初始 JS gzip 文件名与 KB、五区期望/实测表、令牌对账表与缺失/多余/偏离计数、`--paper-0` 三个实测结果、扫描命中表、截图路径。
    - 所有结论都有数字、路径或命令输出；不接受“正常”“已实现”“已全部落地”。
  - **覆盖验收**：1、2、3、4。
  - **不做**：不伪造截图或数字；若实现环境无法截图，停止并请用户补拍，不能省略证据进入提交。

### 6.7 汇总 F0 完成判据

- [ ] 按附录 A 的 8 条完成判据逐条打勾，记录未通过项
  - **做什么**：把 6.1–6.6 的结果对照附录 A；每条写“通过 / 不通过 / 不适用”；未通过项写明原因、归属功能点、是否阻塞提交。
  - **文件**：`evidence/acceptance/F0.md`（追加完成判据汇总段）。
  - **依赖**：6.6。
  - **完成判据**：8 条全部通过；任一阻塞项未通过则停在本任务，不带缺陷进入第 7 节；非阻塞缺口（如字体回退、E 400/344）写明后续归属。
  - **覆盖验收**：1–4。

---

## 7. 提交前停止点

### 7.1 只读检查并停止

- [ ] 在仓库根执行只读 Git 检查，确认提交范围，然后停止
  - **做什么**：执行 `git status --short`、`git diff --stat`（只读，不 `add`）；确认 `docs/`、`README.md`、根 `.gitignore` 无改动；确认 `node_modules/`、`dist/`、`output/` 未被跟踪；对照附录 D 核对文件清单。
  - **文件**：无新增、无修改。
  - **依赖**：6.7。
  - **完成判据**：
    - `git status --short` 只显示 F0 预期新增/修改（`frontend/`、`evidence/acceptance/`）。
    - 无 `docs/`、`README.md`、`.gitignore` 改动。
    - Agent **未执行** `git add`、`git commit`、`git push`。
    - 未进入 F1，未创建任何 F1 文件。
  - **输出**：向用户报告“F0 哪几条验收通过、证据路径、已知缺口、下一功能点建议（F1）”，然后**停止等待用户**。
  - **覆盖验收**：工程纪律（提交与留痕）。

### 7.2 给出建议提交描述（用户执行）

- [ ] 提供建议提交信息与建议 add 范围，由用户自行提交
  - **做什么**：给出下面的提交信息与 add 范围；说明 Agent 不执行 Git 写操作。
  - **文件**：无。
  - **依赖**：7.1。
  - **完成判据**：提交信息符合手册 §11，写“通过了哪几条验收”，不写文件流水账。
  - **建议提交信息**：

    ```text
    chore(layout): 搭建 Vite5+Vue3.5+TS 脚手架并落地设计令牌与五区空壳 —— 通过 F0 验收 1/2/3/4
    ```

    建议正文 3 行：

    ```text
    - frontend/：Vite 5 + Vue 3.5 + TS，五条路由与五区空壳可运行
    - B/E 宽度按视觉规范 §10 取 268/360；手册 280/380 口径待复核
    - 令牌对账：缺失 0 / 多余 0 / 有意偏离 2
    ```

  - **建议 add 范围**（由用户执行，Agent 不执行）：

    ```bash
    git add frontend evidence/acceptance
    # 可选：若希望任务文档留痕
    git add .arts/tasks/F0-tasks.md
    ```

    **不要**用 `git add -A`，避免把临时对账脚本、截图草稿或其他无关文件带入。
  - **覆盖验收**：工程纪律（提交与留痕）。
  - **不做**：不执行 `git add` / `git commit` / `git push`；不代填 commit hash；不推送。

---

## 附录 A · F0 完成判据总表

| # | 判据 | 通过标准 | 证据 |
|---|---|---|---|
| 1 | 构建 | `npm run build` 零 TS error；`dist/` 生成；初始路由 JS gzip < 150KB | 终端输出、`dist/assets/index-*.js`、gzip KB |
| 2 | 五区 | `/workbench` 五区可见；1440×900：A=56、B=268、C=812×740、D=104、E=360；1920×1080：A=56、B=268、C=1292×920、D=104、E=360；`htmlScroll === 0`、`bodyScroll === 0`。B/E 期望值依据视觉规范 §10 令牌；手册 280/380 口径待用户复核 | §2.8.3 脚本输出 + 两张截图 |
| 3 | 令牌 | §10 的 7 个作用域逐项对账；缺失 0、多余 0；有意偏离 2 处且有依据（若用户否决偏离，则为 0 并记录 F7 复查项） | `F0.md` 对账表 |
| 4 | 纸底 | `--paper-0` 原始字符串为 `oklch(0.981 0.0025 250)`；`CSS.supports` 为 true；`body` 背景非纯白 | 控制台三个结果 |
| 5 | 路由 | `/`、`/workbench`、`/sbox`、`/practice`、`/records` 均渲染；无控制台 error | 5 个 URL + 文字/截图 |
| 6 | 依赖 | 直接依赖恰好 7 个；无 UI/动画/HTTP/字体/lint/测试库 | `npm ls --depth=0` |
| 7 | 扫描 | 颜色、px、`!important`、内联 style、`console.*`、`border-width`、禁止依赖命中 0（白名单除外） | 扫描命令输出 + 白名单行号 |
| 8 | 证据 | `F0.md` + 2 张 PNG 存在；单张 ≤ 500KB；所有结论有数字/路径 | `evidence/acceptance/` |

> **提交门槛**：第 1–8 条全部通过才进入 7.1。任一条不通过，停在该条修复；修不动就停止并报告，不带缺陷提交。

---

## 附录 B · 风险与待用户复核口径

| # | 事项 | 当前执行口径 | 需用户确认 | 影响 / 后续 |
|---|---|---|---|---|
| R1 | B/E 宽度 268/360 vs 280/380 | 268/360（视觉规范 §10） | **请确认是否改判 280/380** | 改判需批准 2 个派生令牌或改令牌值，验收数字同步改 |
| R2 | 2 处令牌偏离（`--st-idle-border` / `--st-done-border`） | 改为 `var(--rule-region-ink)` | **请批准或否决** | 否决则回退字面值，F0.md 偏离数改 0，F7 开工前复查 |
| R3 | 7 个作用域 | 全部落地（含 roomy、max-height、两处 reduced） | 请确认 | 只落三块会导致“全部令牌”验收不成立 |
| R4 | E 区 §4.1 的 400/344 | F0 不落，只取 §10 的 360 | 请确认由 F4 处理 | 1440 下 E=360 与 §4.1 文字存在口径差 |
| R5 | Node 24.15.0 + Vite 5 | 1.2 实测 | 失败时请裁决 | 不擅自升级 Vite 主版本或切换 Node |
| R6 | 字体 | 系统回退，不引入 webfont | 请确认 | 截图字体与设计稿不同，属预期 |
| R7 | 1024 视口横向溢出 | F0 不处理 | 请确认由 F4 处理 | F0 验收只用 1440/1920 |
| R8 | `.arts/tasks/F0-tasks.md` 是否提交 | 建议可选提交 | 请用户决定 | 默认只提交 `frontend/` + `evidence/acceptance/` |
| R9 | 流程路径偏离 | 使用 `.arts/design` / `.arts/tasks` | 评审时说明 | 不是 `.codeartsdoer/specs/<feature>/` |
| R10 | 截图补拍 | 由实现环境或用户完成 | 无法截图时请用户补 | 不伪造证据 |

> **宽度标注必须进证据**：`F0.md` 的五区表头写“B/E 期望值依据视觉规范 §10 令牌；手册 280/380 口径待用户复核”。不要在代码或 UI 文案里写尺寸数字，避免第二次漂移。

---

## 附录 C · 自检命令速查

> 以下命令在 `frontend/` 下执行。Windows / Git Bash 可用；无 `rg` 时用 `grep -rnE` 等价替换，判定标准不变。

```bash
# 1) 类型与构建
npm run typecheck
npm run build

# 2) 初始路由 JS gzip（package.json 为 type=module，必须加 --input-type=commonjs）
node --input-type=commonjs -e "const fs=require('fs'),z=require('zlib');const f=fs.readdirSync('dist/assets').find(x=>/^index-.*\.js$/.test(x));const b=fs.readFileSync('dist/assets/'+f);console.log(f,(z.gzipSync(b).length/1024).toFixed(1)+'KB')"

# 3) 颜色字面量：tokens.css 之外应为 0
rg -n --glob '!src/styles/tokens.css' --glob '!src/env.d.ts' '#[0-9a-fA-F]{3,8}\b|oklch\(|rgba?\(|hsla?\(' src

# 4) px 字面量：tokens.css 之外应为 0（.sr-only 白名单单独看）
rg -n --glob '!src/styles/tokens.css' --glob '!src/env.d.ts' '\b[0-9]+(\.[0-9]+)?px\b' src

# 5) 禁止项
rg -n '!important|style="|console\.' src
rg -n 'border-width' src

# 6) 禁止依赖与直接依赖清单
rg -n 'axios|tailwind|gsap|element-plus|ant-design|naive-ui|react|next|nuxt' package.json
npm ls --depth=0
```

无 `rg` 时用以下等价命令（Git Bash / GNU grep）：

```bash
grep -rnE --exclude=tokens.css --exclude=env.d.ts '#[0-9a-fA-F]{3,8}\b|oklch\(|rgba?\(|hsla?\(' src
grep -rnE --exclude=tokens.css --exclude=env.d.ts '\b[0-9]+(\.[0-9]+)?px\b' src
grep -rnE '!important|style="|console\.' src
grep -rnE 'border-width' src
grep -nE 'axios|tailwind|gsap|element-plus|ant-design|naive-ui|react|next|nuxt' package.json
```

**白名单判定**：

- 颜色/px 字面量只允许出现在 `src/styles/tokens.css`。
- `.sr-only` 的 `1px` / `-1px` 是无障碍技术常量，允许，但必须在 `base.css` 注释中标注，并在 `F0.md` 记录行号。
- `100dvh`、`100vh`、`100%`、`0` 不是 px 视觉值，允许。
- `router/index.ts` 的路径字符串、`env.d.ts` 的类型引用不是视觉值，允许。

---

## 附录 D · F0 文件清单

### D.1 应存在的文件（19 个）

```text
frontend/package.json
frontend/package-lock.json
frontend/index.html
frontend/vite.config.ts
frontend/tsconfig.json
frontend/src/main.ts
frontend/src/App.vue
frontend/src/env.d.ts
frontend/src/router/index.ts
frontend/src/styles/tokens.css
frontend/src/styles/base.css
frontend/src/views/HomeView.vue
frontend/src/views/WorkbenchView.vue
frontend/src/views/SBoxView.vue
frontend/src/views/PracticeView.vue
frontend/src/views/RecordsView.vue
evidence/acceptance/F0.md
evidence/acceptance/F0-workbench-1440x900.png
evidence/acceptance/F0-workbench-1920x1080.png
```

### D.2 不应存在的目录 / 文件

```text
frontend/src/components/
frontend/src/composables/
frontend/src/stores/
frontend/src/engine/
frontend/src/types/
frontend/src/canvas/
frontend/src/svg/
frontend/src/data/
frontend/src/assets/
frontend/public/
frontend/scripts/
frontend/.env.example
frontend/tsconfig.node.json
frontend/src/styles/motion.css
frontend/src/styles/reduced-motion.css
frontend/src/components/HelloWorld.vue
frontend/HelloWorld.vue
frontend/src/assets/vue.svg
frontend/public/vite.svg
```

> 目录只在包含 F0 文件时自然创建（`src/`、`src/router/`、`src/styles/`、`src/views/`）。空目录不进 Git，也会误导后续 Agent，因此不建。

---

## 文档结束

> 本文件只做任务规划，不含实现代码。实现 Agent 完成后必须停在 7.1，等待用户自行提交；提交后由用户决定是否进入 F1。