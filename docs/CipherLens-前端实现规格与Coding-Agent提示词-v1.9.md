# CipherLens · 密码透镜 — 前端实现规格与分阶段 Coding Agent 提示词 v1.9

| 项 | 内容 |
|---|---|
| 文档类型 | 前端实现规格（可直接交给 Coding Agent 执行） |
| 编制日期 | 2026-11-02 |
| 版本 | v1.9（r5） —— **容器画线整条撤回**（`--cell-gap: 6px` 下 16 格是独立 chip，无共享边无双线），格线回到每格自带 `1px border`（**结构线走 `border` 不走 `inset shadow`，择一**），**宽度恒定、七态只改 `border-color`，加粗一律 `box-shadow: inset`**；**六通道 owner 表**（fill / bd / txr / corner / text / **bar**）+ `data-bd`/`data-txr` 单值属性；补 `error + selected` 组合态出口（**判分上下文环色近黑**）与「判分叠加绑定 `step_index`」；`selected` **停用四角刻线**（与 error 折角同位）；`is-key` 修回输出侧；`done` 去点阵、缺口改「压纸色方块（边长取 `calc(var(--flag-size)*2)`，不许写死）」；角位截断序 `br > tl > tr > bl`；**禁止尺寸内缩**；**r5：格边框基线改 `--rule-region-ink`（常规 0.845 / 演示 0.545 4.6:1，七态一律含 `done`），`--st-downstream-border` 演示值同步，`--line-default` 0.760 退回"非格子结构线"专用；时间轴标记改"一步一个 button + 2 个 `<i class="c-mark__shape">` 子元素"，图例复用同一元素**。**无阻塞性遗留** |
| 上游依赖 | 《视觉设计规范》（token / **七态** / 四操作四通道 / 10 条实现要点）、《信息架构与交互规格 v1.0》（区域 / 状态 / 键位 / 无障碍） |
| 下游消费 | W1–W4 阶段 Coding Agent |
| 技术栈（锁定） | Vue 3.5 + Vite 5 + TypeScript + Pinia 2 + Canvas 2D + SVG + FastAPI(REST/SSE) + SQLite + Docker |
| 工期 | 单人前端 10 个有效工作日（W1–W4） |
| 文档状态 | 可执行 |

---

## 0. 一页速览：本项目的 6 个技术判断

| # | 判断 | 理由（一句话） |
|---|---|---|
| J1 | **16 个字节格不参与 Vue 响应式渲染**，用 `shallowRef` 存 trace + 命令式 `useMatrixWriter` 单 rAF 批量写 DOM | 每步 16 格各自跑 transition = 16 个调度任务 + 16 次 patch，24 步/秒必掉帧；这是本项目最大陷阱 |
| J2 | **`usePlaybackStore` 与 `useEngineStore` 不合并** | `currentStep` 在拖拽时 60 次/秒变化，trace 是不可变大对象；混在一个 store 会让高频标量污染低频大数据的 effect scope |
| J3 | **Canvas 只开 1 个**，用"绘制程序"（pass）切换而非多 canvas | 单活动焦点原则保证行移位与列混合永不同时发生，多 canvas = 多合成层 + 多份内存。**这是纪律的推论不是架构约束，代码须能降级为双 canvas** |
| J4 | **内容位移归 DOM，瞬时几何归 Canvas**：行移位由 DOM 行轨道 `translateX` 承载（每行 4 实 + 4 鬼格），Canvas 只画回绕 1px 描边与行列交界 | "禁止把 hex 画进 Canvas"是硬规定，内容位移只能在 DOM |
| J5 | **网格 1px 基线用 DOM 而非 Canvas**（对视觉规范的工程修正） | dpr≥1 时浏览器像素对齐比 Canvas 0.5px 偏移稳；静帧零重绘、少一个 pass |
| J6 | **判分完全在后端**，前端只渲染三层反馈，不做 engine 复算 | 双实现 = 双倍"列优先写反"风险（PRD 唯一概率4×影响5项）；且 `propagated`（受污染下游字节）前端算不出来，必须靠后端全量中间态 |
| J4 | **行移位的内容位移由 DOM 行轨道 `translateX` 完成，Canvas 只画回绕描边闪** | "禁止把 hex 画进 Canvas"是硬规定；Canvas 只承担瞬时几何 |
| J5 | **SSE 用 `fetch` + `ReadableStream` 手写 60 行，不用 `EventSource`** | `EventSource` 只支持 GET 且不能带 body，无法传 16 字节上下文；手写可用 `AbortController` 精确中断 |

---

## 1. 目录结构与组件树

### 1.1 目录

```
cipherlens/
├─ index.html
├─ vite.config.ts            # 手动 chunk：engine / vendor 分离
├─ .env.example              # VITE_API_BASE
├─ docker/{Dockerfile,nginx.conf}
└─ src/
   ├─ main.ts
   ├─ App.vue
   ├─ router/index.ts
   ├─ styles/
   │   ├─ tokens.css         # ★ 视觉规范的唯一落地处（CSS 变量全集）
   │   ├─ base.css           # reset / 字体 / 焦点环 / 1px 发丝线工具类
   │   ├─ motion.css         # 全部 @keyframes；.is-playing/.is-dragging 的 will-change
   │   └─ reduced-motion.css # 双通道归零（媒体查询 + `[data-motion="reduced"]`）
   ├─ types/
   │   ├─ trace.ts           # TraceStep / ByteState / OpKind / KeyWord
   │   └─ api.ts             # 请求响应 DTO，与后端 OpenAPI 对齐
   ├─ engine/                # 纯函数，零 Vue 依赖，可在 Worker / 单测中直接跑
   │   ├─ aes.ts             # keyExpansion / subBytes / shiftRows / mixColumns / addRoundKey
   │   ├─ trace.ts           # 仅离线演示内置向量用；**不进判分路径**
   │   ├─ diff.ts            # prev/next → { changed[], keyUsed[], wrapped[] }
   │   └─ sbox.ts            # 正逆 S 盒 + Rcon
   ├─ stores/
   │   ├─ engine.ts          # useEngineStore
   │   ├─ playback.ts        # usePlaybackStore
   │   ├─ tutor.ts           # useTutorStore
   │   ├─ diagnosis.ts       # useDiagnosisStore
   │   ├─ quiz.ts            # useQuizStore
   │   └─ ui.ts              # useUiStore（activeChannel / 折叠态 / 减少动效 / 演示模式）
   ├─ composables/
   │   ├─ useMatrixWriter.ts # ★ 16 格单 rAF 批量写入
   │   ├─ useStageMetrics.ts # ★ 三层共享坐标系
   │   ├─ useRafLoop.ts
   │   ├─ useSSE.ts          # ★ fetch stream + AbortController
   │   ├─ useHotkeys.ts      # 22 键 + 可编辑元素守卫
   │   ├─ useRovingGrid.ts   # 16 格单一 Tab 位
   │   ├─ useDrawerFocus.ts  # 焦点陷阱 + 焦点归还
   │   ├─ useUrlState.ts     # 折叠态 / 步号 / 参数入 URL
   │   ├─ usePerfProbe.ts    # 埋帧率采样与 step 耗时
   │   └─ useReducedMotion.ts
   ├─ canvas/
   │   ├─ StageCanvas.vue    # 唯一 canvas
   │   ├─ drawRowShift.ts    # 回绕描边闪
   │   ├─ drawMixScan.ts     # 列混合计算线
   │   └─ palette.ts         # CSS 变量 → Canvas 色值（含 oklch 解析兜底）
   ├─ svg/
   │   ├─ BracketLayer.vue   # 列括线（静态）
   │   ├─ CornersLayer.vue   # 四角 L 形刻线（仅活动区/容器级，**选中格不用**）
   │   ├─ CrosshairLayer.vue # S 盒十字准星
   │   └─ AnnotationLayer.vue# 红线批注折线 + 方括号
   ├─ components/
   │   ├─ layout/{AppBar.vue, WorkbenchLayout.vue}
   │   ├─ region-a/ContextBar.vue
   │   ├─ region-b/{InputPanel.vue, ParamsRow.vue, FieldHint.vue}
   │   ├─ region-c/{StageHeader.vue, SummarySentence.vue, MatrixStage.vue,
   │   │            ByteCell.vue, KeyTrack.vue, TableView.vue, DirectionMark.vue}
   │   ├─ region-d/{TransportBar.vue, Timeline.vue, TimelineSegment.vue}
   │   ├─ region-e/{TutorPanel.vue, ContextHeader.vue, ChipRow.vue,
   │   │            MessageList.vue, MessageItem.vue, Composer.vue, DiagnosisCard.vue}
   │   ├─ drawers/{ByteDrawer.vue, KeyExpansionDrawer.vue}
   │   └─ shared/{AppDrawer.vue, CollapsibleRow.vue, LiveRegion.vue,
   │              IconMark.vue, HexInput.vue, SegmentedTabs.vue}
   └─ views/
       ├─ HomeView.vue  WorkbenchView.vue  SBoxView.vue
       ├─ PracticeView.vue  StepDrillView.vue  RecordsView.vue
       └─ AuthView.vue  AboutView.vue  KeyExpansionView.vue
```

**分层理由**：`engine/` 必须零 Vue 依赖 —— 它要同时被 W3 练习判分、离线降级、单元测试三方复用；一旦 import 了 `vue`，Node 端单测就要拖 jsdom。

### 1.2 组件树（★ = 连 store，○ = 哑组件）

```
App.vue ★ui
├─ AppBar ○                                   [全局] 导航 / 演示模式 / ?
├─ router-view
│  └─ WorkbenchView ★engine ★playback ★ui      [PG-2 主场景]
│     ├─ ContextBar ★engine ○                  [A] 数据集名·长度·方向·离线标·导出
│     ├─ InputPanel ★engine ── FieldHint ○     [B] 明文/密钥/长度/载入向量/生成
│     ├─ StageArea
│     │  ├─ StageHeader ○                      [C1] "第 N 轮 · 列混合"
│     │  ├─ SummarySentence ★playback ★engine  [C2] 一句话摘要 + 展开逐字节映射
│     │  ├─ MatrixStage ★engine ★playback ★ui  [C3] 舞台容器：三层对齐 + 事件
│     │  │  ├─ StageCanvas     (canvas/)       [C3] 唯一 canvas：回绕描边 / 扫描线
│     │  │  ├─ ByteCell ×16  ○                 [C3] 单格 DOM：两个 span 叠放 + 七态 class
│     │  │  ├─ BracketLayer    (svg/)          [C3] 列括线
│     │  │  ├─ CornersLayer    (svg/)          [C3] 四角刻线（活动区容器级）
│     │  │  └─ AnnotationLayer (svg/)  ★diagn  [C3] 红线批注（唯一非哑 SVG）
│     │  ├─ KeyTrack ★engine ○                 [C5] 本轮 4 字 + 展开来源箭头
│     │  └─ TableView ○                        [C3-alt] 读屏深挖通道（<table>）
│     ├─ TransportBar ★playback ★ui            [D] 播放/单步/步计数/跟随
│     ├─ Timeline ★playback ★diagnosis ○       [D] 按轮分段 + 诊断/提问标记 + 拖拽
│     ├─ TutorPanel ★tutor ★playback ★ui       [E] 360–400px，可收 48px
│     │  ├─ ContextHeader ○                    [E] CTX: R3 · MixColumns · C[1]
│     │  ├─ ChipRow ○                          [E] 3 个本地预设问题（不调模型）
│     │  ├─ DiagnosisCard ★diagnosis ○         [E] 红线批注的反问卡（行内，非浮层）
│     │  ├─ MessageList ★tutor ─ MessageItem ○ [E] 流式正文 + 引用数值 + 停止生成
│     │  └─ Composer ○                         [E] 输入框 + 发送
│     ├─ ByteDrawer ★engine ★ui ○              [F1] 覆盖 E 不覆盖 C
│     └─ KeyExpansionDrawer ★engine ★ui ○      [F2] 44/52/60 字条带
├─ SBoxView ★engine ★ui                        [PG-3]
├─ PracticeView ★quiz ★engine ★ui              [PG-6]
├─ StepDrillView ★quiz ★playback               [PG-7]
├─ RecordsView ★quiz ★diagnosis                [PG-8]
└─ KeyExpansionView ★engine                    [PG-4 全屏态，复用 F2 组件]
```

**哑组件的判定线**：凡是"一个 prop 进去、一个事件出来、不需要知道 step 是第几步"的组件，一律哑。`ByteCell` 必须哑 —— 它被 `useMatrixWriter` 命令式操作，若它连 store，`currentStep` 变化会触发 16 次 patch，J1 直接失效。

---

## 2. Pinia store 设计

### 2.1 `useEngineStore`（低频 / 大数据 / 不可变）

| 字段 | 类型 | 含义 |
|---|---|---|
| `trace` | `ShallowRef<TraceStep[]>` | 全部快照。**`shallowRef`，绝不 `ref`** |
| `keySchedule` | `ShallowRef<KeyWord[]>` | 44/52/60 个字，每字 4 字节 |
| `params` | `Reactive<{ keyBits: 128\|192\|256; direction: 'enc'\|'dec'; plaintextHex: string; keyHex: string }>` | 输入参数，需响应式（表单绑定） |
| `status` | `Ref<'idle'\|'computing'\|'ready'\|'error'\|'offline'>` | 生成状态机 |
| `error` | `Ref<{ code, message, field: 'plaintext'\|'key'\|null } \| null>` | 行内错误（不弹窗） |
| `vectorName` | `Ref<string \| null>` | `'FIPS-197 A.1'`；未载入则 `null` |
| `isStale` | `Ref<boolean>` | 参数已改但 trace 未重算 → 触发二次确认 |
| `stepCount` | `Ref<number>` | **不再由前端推导**（v1.3）：直接取 `/api/aes/trace` 响应的 `step_count` / `rounds`；未生成时为 0。理由：128/192/256 步数不同，前端推导等于第二份真相源（见 §11.2） |

Actions：`generate()`（`POST /api/aes/trace`，超时 8s 回落本地 `engine/trace.ts`）、`loadVector()`、`setKeyBits()`（带二次确认）、`reset()`。

### 2.2 `usePlaybackStore`（高频 / 小标量）

| 字段 | 类型 | 含义 |
|---|---|---|
| `currentStep` | `Ref<number>` | 0..stepCount-1，**"我在哪"的唯一真相源** |
| `mode` | `Ref<'idle'\|'playing'\|'paused'\|'scrubbing'\|'stepping'>` | 播放态机 |
| `direction` | `Ref<1 \| -1>` | 反向单步用（显示上一步 `state_before`） |
| `speed` | `Ref<0.5\|1\|2\|4>` | 播放倍速，**只改步间隔不改动画时长**：`--step-interval` 800ms × {2, 1, 0.5, 0.25} = 1600 / 800 / 400 / 200ms |
| `follow` | `Ref<boolean>` | AI 栏是否跟随当前步 |
| `stepLockUntil` | `Ref<number>` | 单步锁（动画期间禁止再进），= `now + totalDuration` |
| `lastStepMs` | `number`（非响应式） | 上一步实测耗时，供 `usePerfProbe` 读 |

Getters：`canPrev / canNext / progressPct / isAnimating`。
Actions：`next() / prev() / play() / pause() / beginScrub() / updateScrub(i) / commitScrub() / setStep(i) / jumpRound(n)`。

**为什么与 engine 分开**：`currentStep` 在拖拽时每帧变；若与 `trace` 同库，Pinia devtools 的 `$subscribe` 每次变更都会序列化整个 trace 数组（上千快照 × 16 字节），dev 环境直接卡死；且两者更新频率差三个数量级，放一起会让"只改步号"进入大数据的 effect scope。**代价**是 `MatrixStage` 要显式订阅两个 store —— 这是好事，依赖可见、可测。

### 2.3 `useTutorStore`

| 字段 | 类型 | 含义 |
|---|---|---|
| `messages` | `Ref<TutorMessage[]>` | 每条 message 是 `markRaw` 的 plain object |
| `ctxStep` | `Ref<number>` | 锁定的步（`follow=false` 时与 `currentStep` 脱钩） |
| `ctxLabel` | `Computed<string>` | `CTX: R3 · MixColumns · C[1]`（切步只更新这个 + chip，不生成正文） |
| `phase` | `Ref<'idle'\|'waiting-first'\|'streaming'\|'done'\|'aborted'\|'error'>` | 流式状态机 |
| `timings` | `{ startedAt, firstTokenAt, endedAt }` | 用于 3s / 20s 双阈值判定 |
| `degraded` | `Ref<'none'\|'slow'\|'timeout'\|'offline-template'>` | 降级态，渲染顶部一行标识 |
| `cacheHit` | `Ref<boolean>` | 命中 → 整段直出，**不做假打字机** |
| `quotesValues` | `Ref<boolean>` | 回答是否引用了本步数值 |
| `abortCtrl` | 模块内 `AbortController \| null` | **非响应式**，不要放 state |

Actions：`ask(q)`、`abort()`、`appendToken(t)`、`markFirstToken()`、`switchContext(step)`、`retry()`。
双阈值：`firstTokenAt` 超过 3000ms → `degraded='slow'` 并露出"先看本地要点"；总时长超 20000ms → `abort()` + 用 `templates.ts` 本地模板。

### 2.4 `useDiagnosisStore`

| 字段 | 类型 | 含义 |
|---|---|---|
| `rules` | `Record<Misconception, { hits: number; dismissed: boolean; lastFiredAt: number }>` | 三类误解各自冷却 |
| `active` | `Ref<Annotation \| null>` | 当前批注（**同时最多 1 条**） |
| `idleSince` | `Ref<number>` | 最后一次有效操作时间戳 |
| `cooldownUntil` | `Ref<number>` | `lastFiredAt + 45000` |
| `history` | `Ref<Annotation[]>` | 上报 `/api/events`，也是时间轴**双轨标记**的数据源：`{ stepIndex, kind: 'diagnosis'\|'ask', count }`，同一 step 可有两条 |

判定（修正后）：`now - idleSince >= 20000 && active === null && now >= cooldownUntil && 该类型未 dismissed`。
Actions：`onEffectiveAction()`（重置 `idleSince`）、`onRevert()`（仅当回退后 3s 内无有效操作才 +1 hit）、`tryFire()`、`accept() / deny() / flagWrong()`、`forceFire(type)`（仅 `?debug=diagnosis` 下暴露到 `window.__diag`）。

### 2.5 `useQuizStore`

| 字段 | 类型 | 含义 |
|---|---|---|
| `items` | `Ref<QuizItem[]>` | 题目（含 `expected`，不渲染到 DOM） |
| `cursor` | `Ref<number>` | 当前题 |
| `answers` | `Ref<Record<string, { value: string; at: number }>>` | 作答 |
| `phase` | `Ref<'idle'\|'answering'\|'submitting'\|'graded'\|'reviewing'>` | `submitting` 期间禁用提交按钮、矩阵不播 diff |
| `errorLoc` | `Ref<{ round: number; step: string; byteIndex: number } \| null>` | 来自后端 `first_diff` |
| `errorBytes` | `Ref<Set<number>>` | 由 `first_diff.byte_index` 构造（**通常只 1 个**） |
| `propagated` | `Ref<Set<number>>` | 由后端 `propagated[]` 构造，驱动 `is-downstream` |
| `inputMismatch` | `Ref<{ field: 'plaintext' | 'key' | 'both'; char_index: number; expected: string } | null>` | 后端 `input_mismatch`，**可空对象不是 boolean**；非 null 时不计入错误统计并渲染字段级提示。前端用自己的输入按 `char_index` 切片即可说出「你写的是 X」，无需后端回传原字符 |
| `stats` | `Ref<{ done; correct; byStep: Record<string, number> }>` | 记录页 |

**接口契约 `POST /api/quiz/submit`**（判分全部在后端，前端零复算）：
```jsonc
{ "summary": { "total_bytes": 12, "wrong_count": 3 },
  "first_diff": { "round": 4, "step": "mix_columns", "byte_index": 7 },
  "propagated": [8,9,10,11,12,13,14,15],   // 因首错被污染的下游字节，驱动 is-downstream
  "input_mismatch": null,                   // 非 null = 学生录入与题目不一致 → 不计错误统计
  "expected_ciphertext": "…" }
```
Actions：`submit()`（POST 上述接口，只存结果不重算）、`grade(反馈)`、`jumpToWorkbench()`（跳到 `first_diff` 对应步并高亮 `byte_index`）。

### 2.6 `useUiStore`（跨区协调，必须有）

`activeChannel: 'idle'|'playback'|'tutor'|'diagnosis'`（密度纪律 1 的落地）、`tutorCollapsed`、`inputCollapsed`、`drawer: null|'byte'|'key'`、`reducedMotion: 'system'|'on'|'off'`、`density: 'compact'|'roomy'`、`mode: 'normal'|'present'`（**落到 DOM 的 `data-mode`，不是 `presentation` 布尔**）、`tableView: boolean`。全部写进 URL（`useUrlState` 节流 300ms `router.replace`）。

### 2.7 ★ 16 个字节格如何订阅状态而不引发 16 次重渲染

**推荐方案：`shallowRef` 存 trace + 命令式 `useMatrixWriter` 在单个 rAF 内批量写 DOM。**

```ts
// composables/useMatrixWriter.ts（核心架构，非最终代码）
export function useMatrixWriter(getRoot: () => HTMLElement | null) {
  // 三份引用在 ensure() 里一次性缓存：根节点 / 值节点 / 新值节点
  let roots: HTMLElement[] = [], curVals: HTMLElement[] = [], nextVals: HTMLElement[] = []
  let rafId = 0, batches = 0, lastValues = new Uint8Array(16)
  const pending = Array.from({ length: 16 }, () => EMPTY_PAINT)

  function ensure() {
    if (roots.length === 16) return
    roots = [...(getRoot()?.querySelectorAll<HTMLElement>('.c-byte') ?? [])]
    // DOM 顺序 = 列优先，故下标 i 直接就是 AES 字节号，无需映射表
    curVals  = roots.map(r => r.querySelector<HTMLElement>('.c-byte__val.is-current')!)
    nextVals = roots.map(r => r.querySelector<HTMLElement>('.c-byte__val.is-incoming')!)
  }

  function flush() {
    rafId = 0; ensure()
    const t0 = performance.now()
    for (let i = 0; i < 16; i++) {                      // ← 唯一一次写窗口
      const p = pending[i]!, root = roots[i]
      if (!root) continue
      // 判分上下文切换 / 路由往返时节点可能整体重建：引用会变成游离节点，
      // 此时写 textContent 不报错也不显示（只在真机上偶发），必须校验后再写
      if (!root.isConnected) { roots = []; ensure(); if (!roots[i]) continue }
      curVals[i]!.textContent  = HEX[lastValues[i]!]     // 旧值留在上层
      nextVals[i]!.textContent = HEX[p.v]                // 新值从下方滚入
      if (p.cls !== root.className) root.className = p.cls  // 整串替换，比多次 toggle 少写
      const ds = root.dataset                            // 单值通道走属性，只在变化时写
      if (ds.bd  !== p.bd)  ds.bd  = p.bd
      if (ds.txr !== p.txr) ds.txr = p.txr
      const aria = ARIA(i, lastValues[i]!, p.v, p.changed)
      if (root.getAttribute('aria-label') !== aria) root.setAttribute('aria-label', aria)
      lastValues[i] = p.v
    }
    if (import.meta.env.DEV && batches > 0) console.error('[MULTI-BATCH] %d', batches)
    recordBatch(performance.now() - t0); batches = 0
  }

  function write(values: Uint8Array, paints: BytePaint[]) {
    for (let i = 0; i < 16; i++) pending[i] = { ...paints[i]!, v: values[i]!, changed: false }
    batches++; if (!rafId) rafId = requestAnimationFrame(flush)
  }
  onScopeDispose(() => { if (rafId) cancelAnimationFrame(rafId) })
  return { write }
}
```
> 三个易错点：① `batches++` 在 `write()` 里、`batches = 0` 在 `flush()` 末尾，所以"一帧内被调两次"能被抓到；② `classList.toggle` 连写 5 次会产生 5 次 mutation，**整串赋 `className` 一次**更省（16 格 × 5 次 = 80 次降到 16 次）；③ `dataset` 写入**先比对再写**——属性写入会触发该元素的样式重算，无条件写等于每帧 16 次无效重算。
>
> 八个写操作/格（`curVals.textContent` / `nextVals.textContent` / `className` / `dataset.bd` / `dataset.txr` / `aria-label` / 2 个 `dataset.corner`），且 `className`、`dataset.*`、`aria-label` 全部**先比对后写**。在单次 `for` 循环内完成，16 格合计 ≤128 次 mutation，**实测 <0.6ms**（§5 有探针）。这是"一帧一个写窗口"能成立的前提。

**为什么不用其他三种**：

| 备选 | 为什么弃 |
|---|---|
| 16 个 `computed(() => trace[i])` | 每步产生 16 个 patch 任务 → 16 次 mutation → 16 次重排。拖拽时 60fps × 16 = 960 次/秒。**这正是规范禁止的写法** |
| `watch(currentStep)` + 模板绑定 | 模板绑定意味着 `ByteCell` 必须 `:value="..."`，等于把 16 格重新交回响应式系统 |
| `v-for` + `:key="step"` 整体重建 | 每秒重建 24 次 × 16 节点 = 每次 16 个新元素 + 16 次 GC，且选中态/焦点全部丢失 |

**关键补充**：`ByteCell` 模板里 hex 写死为占位 `<span>—</span>`，**不绑定任何表达式**。`useMatrixWriter` 在 `onMounted` 后首次写入真实值。这样 Vue 永远不会为这 16 个格子创建 effect。

**配套的三条硬规则（缺一条，J1 的收益就会被吃掉）**：
1. **`<template>` 里禁止用 `v-if` 控制字节格内的任何状态子元素**（值区、角位、上标、纹理）。一律常驻 DOM，用 `is-*` / `data-*` 切可见性（`display:none` / `visibility:hidden` / `opacity:0` 都可）。`v-if` 会销毁重建节点 → 缓存的引用变游离节点 → **写值不报错也不显示，这类 bug 只在真机偶发**。
2. **只写 `textContent`，不写 `innerHTML`**（`innerHTML` 会重建子树，同时把刚才缓存的 `curVals` / `nextVals` 全部作废）。
3. **写之前校验 `el.isConnected`**（见 `flush()` 里那行）—— 判分上下文切换、路由往返、`v-for` 的 `:key` 变化都可能让整批节点重建。

---

## 3. 渲染分层实现方案

### 3.1 DOM 层（字节数值与交互）

**节点结构**：**完全照抄视觉规范 v1.1 §9.1/§9.2，不要自己发明类名**。

```html
<section class="c-matrix" data-step="13" data-round="3" data-ctx="playing|graded">
  <div class="c-matrix__body">                          <!-- position:relative，三层锚点 -->
    <canvas class="c-matrix__fx" aria-hidden="true"></canvas>       <!-- z0 扫描线/行移位 -->
    <svg class="c-matrix__brackets" aria-hidden="true"></svg>       <!-- z1 列括线 -->
    <div class="c-matrix__grid" role="grid"
         aria-rowcount="4" aria-colcount="4" aria-label="状态矩阵">
      <!-- 16 × .c-byte，DOM 顺序 = 列优先（col0r0,col0r1,col0r2,col0r3,col1r0…）
           配合 grid-auto-flow: column -->
      <div class="c-byte" role="gridcell" tabindex="-1" data-row="0" data-col="0"
           data-bd="idle" data-txr="none"
           aria-label="第 1 行第 1 列，字节 0，值 0x32，十进制 50，本步已变化，原值 0x9A">
        <span class="c-byte__stage">                    <!-- overflow:hidden -->
          <span class="c-byte__val is-current">32</span>          <!-- 旧值 -->
          <span class="c-byte__val is-incoming" aria-hidden="true">B8</span> <!-- 新值 -->
        </span>
        <!-- corner 通道：固定 2 个通用角元素（同格最多 2 个角标），位置/形状/颜色全由 data-corner 驱动 -->
        <span class="c-byte__corner" data-corner="" aria-hidden="true"></span>
        <span class="c-byte__corner" data-corner="" aria-hidden="true"></span>
        <!-- sup 通道：双上标常驻，用 data-active 切换（不用 v-if，也不依赖 UA 的 [hidden] 样式） -->
        <span class="c-byte__sup" data-kind="neq" data-active="false" aria-hidden="true">≠</span>
        <span class="c-byte__sup" data-kind="xor" data-active="false" aria-hidden="true">⊕</span>
        <span class="c-byte__hint" aria-hidden="true">←1</span><!-- 仅 reduced-motion 行移位 -->
      </div>
    </div>
  </div>
</section>
```

- **DOM 子元素顺序按列优先**（视觉 §9.2 的硬要求）。这样三件事自动一致：`Tab`/方向键顺序、AES 的列优先语义、Canvas 的索引计算 —— **不需要映射表**。附带一个极好的性质：**DOM 下标 === AES 字节下标**（AES 状态 `s[r][c] = in[r+4c]`），所以 `useMatrixWriter` 的 `i` 既是 DOM 序号也是字节号，`step.changed[i]` 可直接用，不必换算。**若按行优先渲染，会同时产生三个 bug：方向键顺序错、Canvas 索引错、学生的空间记忆错。**
- **数值滚动**：`c-byte__val` 两个 `span` 绝对定位叠放（`is-current` / `is-incoming`），**不写内联 style 位移**，用 `@keyframes` 驱动。`useMatrixWriter` 只切 class 与 `textContent`，位移交给 CSS —— 16 格动画由合成线程并行跑，主线程只发 1 次指令。
- **roving tabindex**（`useRovingGrid.ts`）：容器 `@keydown` 捕获方向键，维护 `activeIndex`；只改两个节点的 `tabindex`（旧 `-1`、新 `0`）并 `focus({ preventScroll: true })`。**到边界不跨行**。`Enter` 开 F1，`Esc` 交还焦点给容器。
- **`aria-label` 必须 hex + 十进制双写**（ux 的 A4：教材两种写法都有，读屏用户常需十进制心算）。写一次模板，由 `useMatrixWriter` 在写入值的同一帧用 `setAttribute` 更新；不要在模板里绑定表达式。
- **类名约定（照抄视觉，别改）**：`c-` = 组件、`__` = 元素、`is-` = 状态；**状态一律挂组件根元素，禁止挂子元素**（否则选择器不可穷举）；互斥状态走 `data-state="streaming|cached|error|…"` 属性，**不用多个 `is-` 叠着表达互斥**。
- **状态编码**：用**互相独立**的 `is-` class 而非 1 个枚举，因为叠加态要同时显示。但"独立"只指**声明层**：每个 class 声明一种状态，**每个视觉通道的值仍然只由一个 owner 提供**（见下方 owner 表），否则就会退化成靠特异性打架。类名对齐视觉 §9.1：

| class | 语义 | 来源 |
|---|---|---|
| `is-changed` | 本步值发生变化 | `step.changed[i]` |
| `is-selected` | 当前选中格（**外 3px 环** + `border-color` + `inset` 1px；**不用四角刻线**，见下方改判；底色只在它是 fill owner 时才归它） | roving tabindex 的 `activeIndex` |
| `is-error` | **学生真正答错的那些字节** | `/api/quiz/submit` 的 `first_diff` |
| `is-downstream` | **受首错牵连的下游字节**（第 7 态，**不占角标/纹理/`≠`**）：常规 = 底色 `--surface-inset` + `--ink-3` 400 + `data-bd="downstream"`（边框降一级）；演示 = 底色 `oklch(0.905 0.004 258)`（ΔL 0.06）+ `oklch(0.415 0.012 258)`（8.4:1）+ 400 + **边框不降** | `/api/quiz/submit` 的 `propagated[]` |
| `is-key` | 密钥参与（45° hatch + 左 3px 竖条；**语义身份由竖条承载**，见 §3.1 判分例外） | `step.key_indices` |
| `is-done` | 已完成（**1px 实线 + 左下 5px 缺口**；**无点阵**、不用虚线 —— 视觉 v1.2 已去掉 `txr-dots`） | 播放进度 |
| `is-ghost` | 空/未输入占位（值显示 `—`，不给假数值） | `status==='idle'` |
| `is-reverse` | 反向单步（角位 `tl` 的 `◀`） | `playback.direction === -1` |
| `is-xor` | 轮密钥加语义（`⊕` 上标；reduced-motion 下的替代） | `op==='AddRoundKey'` |
| `is-disabled` | 计算中（格禁用但 Tab 可达并说明原因） | `status==='computing'` |
| （idle） | 无标记 | 默认 |

**元素名对齐（一次性说清，之后不再改名）**：视觉 §9.1 的 `__flag`（右上）/ `__fold`（右下）/ `__notch`（左下）**是同一批"角位"的三个专用元素**，实现层合并为 **2 个通用 `__corner`**（几何/形状/颜色照搬，只是位置由 `data-corner` 驱动）。理由见下方"四角与双上标的 DOM 契约"。合并后 `done` 的左下 5px 缺口**由 `data-corner="bl"` 的那个元素承载** —— 它的做法是**压一块纸色方块盖住边框**，**不是把 `border` 断开一段**。
> 为什么不许断 `border`：`border` 是四个状态共用的通道（`downstream` 降级改 `border-color`、`selected` 改 `border-color`、判分上下文换环色也会碰边框），**断边会随 `border-color` 变化而失效** —— 缺口在某个状态下会莫名消失或变成一条黑缝。**用形状去改另一个通道，是这套规则里最典型的一类错法。**
> **角位尺寸一律取 `calc(var(--flag-size) * 2)`，不许在 CSS/DOM 里写死 5px 或 6px。** 视觉 §6.1.1 把它绑在 `--flag-size` 上（随 `--cell-size` 与模式变），本节表格里的"5px 缺口 / 6px 折角"是**取值简写**，不是可抄的常量：88px 档会变成 8px，演示态缺口是 6px。写死的结果是"某一档下缺口盖不住边框"，而它只在那个档才看得出来。

视觉 §9.1 声明的**合法叠加**：`is-changed + is-key`（轮密钥加）、`is-changed + is-selected`、`is-error + is-selected`。
**`is-downstream` 已进视觉 v1.2 §2.3.1 的状态清单**（此前只有 6 态，见 §10.6 闭合记录）。本节与视觉冲突时以本节为准，因为 owner 表与 `data-bd` 口径只在这里维护。

**状态判定：按「视觉属性通道」分配 owner，不靠 class 顺序**

> 「7 个 class 谁盖谁」这个提法本身有风险：如果叠加结果依赖 class 的书写顺序，那么 `classList` 的真实顺序不可控（`add`/`remove` 交错后顺序由引擎内部决定），靠顺序赢就是靠运气。**正解不是排顺序，是让顺序无关** —— 每个视觉属性通道，同一时刻只有一个 owner。

| 通道 | 承载 | 单值域 | owner 优先级（左高右低） |
|---|---|---|---|
| **底色 fill** | `is-*` class（**单值**） | 6 值 | `error` > `selected` > `changed` > `downstream` > `done` > `idle`（**判分期去掉 `changed`**） |
| **边框色 bd** | `data-bd`（**单值属性**） | 4 值 | `error` > `selected` > `downstream` > `idle` |
| **纹理 txr** | `data-txr`（**单值属性**） | 3 值 | `fold`(error) > `hatch`(key) > `none` |
| **角位 corner** | 2 个 `data-corner` 元素 | 4 值取前 2 | `br`(error) > `tl`(reverse) > `tr`(changed) > `bl`(done) |
| **边条 bar** | `is-key`（与 `txr` 同源、**不同通道**） | 2 值 `key \| idle` | **无竞争**：只有 `key` 一个候选，不进优先级链、不进角位截断 |
| **文字/墨量 text** | CSS（**由 fill 推导，不独立求值**） | 4 档 | error/selected → 600 / changed·key → 600·500 / downstream·done → `--ink-3` 400 / idle → `--ink-1` 500 |

**为什么必须把 `bar` 单列成一条通道**（ux 提的，采纳）：`key` 的左边缘 3px 竖条**不属于上面任何一条**——不是 fill（`is-key` 不许带底色，否则轮密钥加 16 格的 `is-changed` 黄底全丢）、不是 bd、不是 txr（纹理已给 `fold`/`hatch`）、不是 corner、也不是 text。若不单列，下一个想给 `key` 加点东西的人会发现"五条通道都占满了"，然后顺手塞进 fill —— **那正是本项目的第一次事故原因**。显式写一条"只有一个候选、永不竞争"的通道，成本是一行表格，收益是堵住这条路。
> 它不是"优先级最低的第七态"，而是**一条只有 0 或 1 个候选的通道**：`key` 出现就画，不出现就没有，与 fill/bd 的取值完全无关。`is-key` 因此天然**不受判分叠加影响**（`key` 是输入条件，判分恰恰需要，见"判分展示期间的三条例外"）。

**为什么 `data-bd` / `data-txr` 用属性而不是 class 前缀**：`bd-error` 和 `bd-key` 同时写在 `class` 里是**语法上合法**的，能不能只出现一个还得靠人不写错；**属性是单值的，平台层面就保证了一个 owner**，比"我承诺只写一个 class"强一档。代价只有选择器写成 `[data-bd="error"]`，一次性成本。`is-*` 全部留给"整格状态"，视觉已有的 `.c-byte.is-x` 选择器**一行都不用改**。

**为什么 `changed` / `key` / `done` 不在边框色链里**：视觉 §2.3.1 这三行的边框列分别只写"顶部 2px 顶条 / 左侧 3px 竖条 / 左下 5px 缺口"，**都没有改 `border-color`**。把它们塞进边框链，等于让三个"其实不改边框色"的态占着 owner 位，将来必然有人问"`changed` 到底该不该红边"。**只有真的改边框色的态才进这条链** —— 这是 owner 表的准入条件。

**四条互斥 / 组合规则**：
1. `error` ⊥ `downstream`（不可能既错又被污染）→ 同时命中以 `error` 为准，并 `console.warn` 标记契约漂移（**这正好能帮你抓到后端 `propagated` 与 `first_diff` 不一致的 bug**）。
2. `done` ⊥ `changed`（`done` 只在复习视图，播放态不出现）→ `done` 让位。
3. `idle` 永不与其他共存，命中即清空其余。
4. **`error + selected` 是唯一的组合态，必须有独立出口**。team-lead 的链路是 `error + selected > error > selected > changed > done > idle` —— 也就是说它**是一个独立状态，不是"谁赢"**。落地是一条**两类选择器规则**（特异性 0,2,0，与书写顺序无关，不需要 `!important`）：

```css
/* error 占底色与边框；selected 的「外 3px 环」来自 .is-selected，不被这条覆盖 */
.c-byte.is-error.is-selected {
  background: var(--st-error-fill);   /* 底色归 error */
  border-color: var(--st-error);      /* 边框归 error */
}
/* 判分上下文（data-ctx="graded"）里选中环一律换近黑：红底 + accent 环在红色偏弱的
   视觉下会并成一团。**只换环色，不动 border-color** —— accent 边对红底仍有 3.4:1，
   是"选中"的第二重确认。 */
.c-matrix[data-ctx="graded"] .c-byte.is-selected { --accent-ring: var(--ink-1); }
```
这样 `error + selected` = 红底 + 右下折角（error）＋ 红边 + `inset`（error）＋ **近黑外环**（selected），三个通道正交、互不遮挡。注意环色的作用域是**整个判分上下文**、不是"仅 error 格"—— 否则同样的选中态会因为底下的格子是不是错格而换色，同屏两种环色比一种更难读。
不加这条的后果很具体：学生答错后点开那个字节看明细，屏幕上没有任何"我选中了它"的反馈 —— **他会以为自己没点上**。

**`selected` 不用四角刻线（ux v1.3 改判，会动 4 处，已全改）**：原设计是"四角 6px L 形刻线 + 外 3px 环"。刻线这一半**停用**，两条理由：

1. `error` 的标识是**右下 6px 折角**，而四角刻线里正好有**右下那条 6px 臂** —— 同位置、同尺寸、不同语义。`error + selected`（判错后点开那个错字节，这是必然动作）下两者直接叠死，看起来像一条画歪的线。
2. 四角是**角标通道**（左上 reverse / 右上 changed / 右下 error / 左下 done），规则是"每格最多 2 个"。再塞一套四角刻线 = 同一通道进第二个 owner，直接破上面那张 owner 表。

**但刻线不能只删不补**：光改 `border-color` + `inset` 是纯颜色信号。接它的是**外环**，两条约束 —— ① 必须是**环**（`outline` 与格边留 2px 空隙），不能退化成"加粗边框"：加粗是量变，环是另一种形状；② **判分上下文里环色改近黑 `--ink-1`**（见上）。

**撤的范围要说清**：`CornersLayer` 只停用"字节格里的选中格"这一个用法；**矩阵容器活动区的四角刻线、B 区输入框 focus 时的四角刻线都保留** —— 那两个位置没有角标通道，不存在争用。别把"撤刻线"读成"全站不用刻线"。

**判分展示期间的三条例外（都不是"谁赢"，是语义不同）**
- **`changed` 整体让位**（fill 与 corner 都不占，不是逐通道例外）：判分要回答的是"哪个错、哪些被带偏"，不是"本步 diff 了哪些字节"；逐通道让位会产生"corner 撤了但 fill 还在"的半让位怪状态，说不清也测不清。副产品：琥珀角标 + 红折角 + `≠` 三重叠加**根本不会同时存在**。
- **`key` 不让位**：`changed` 是 **diff 信息**（判分不需要），`key` 是 **输入条件**（判分恰恰需要）。若首次差异发生在轮密钥加，学生必须看到"参与异或的是哪 8 个密钥字节"，否则他已经知道错了，却不知道错在哪一半。`key` 的身份由**左边缘 3px 竖条**承载 —— 该通道只有 `key` 使用、永不竞争，所以无论 fill / txr 被谁占用，它都仍然可读。
- **判分叠加整体绑定 `step_index`**：`errorSet` / `downstreamSet` 是为**某一步**算出来的；学生单步或跳到别的步之后，这些下标指的是另一批字节位置，继续画就是错的。因此它们与 `step_index` **同生命周期**，离开该步即整体撤场。这条一加，"判分 + 反向单步"变成不可能组合，`is-reverse` 的 `tl` 角位**不需要任何门控** —— 而且它顺手堵掉一个更容易出的 bug：判分结果画在了非锚点步上。

**★ 格线就在格子上，`border-width` 恒定（v1.9 定稿，撤回 v1.7 的"容器画线"）**

v1.7 曾提出"格线改由矩阵容器画、`.c-byte` 不写 `border`"。**该方案整条作废**，两个理由：

1. 矩阵是 `--cell-gap: 6px` 的 16 个独立 chip（视觉规范 §6.2）。容器底色方案会在格子之间填出 **6px 实色条带**，不是 1px 细线；若把间隙压到 1px，矩阵的呼吸感与"16 个独立格"的读法同时失效。
2. 它要治的病**不存在**：6px 间隙下每格边框互不接触，**既没有共享边、也不会"两条 1px 叠成 2px"**。

所以：**格线 = 每格自己的 `border: 1px solid`，留在 `.c-byte` 上。**

```css
.c-byte {
  /* 格子边框属"区域结构线族"：常规块 0.845 / 演示块 0.545（4.6:1）。
     引用 token 名，不引用数值 —— 两个块的同名 token 值不同，写死数值必错一个。 */
  --bd-color: var(--rule-region-ink);
  border: 1px solid var(--bd-color);   /* ★ 结构线走 border，不走 box-shadow —— 见下方说明 */
  box-sizing: border-box;              /* 必写：内容盒尺寸与 border-width 解耦 */
}
[data-mode="present"] .c-byte {
  border-width: 2px;                   /* 演示态恒 2px（只改宽度；色由 --rule-region-ink 自己给出，不覆盖） */
}

/* 七态只改 color，永不改 width —— 改 width 会让 hex 位移 1px，
   而矩阵里位移 1px 会被读成"这个数值变了" */
[data-bd="error"]      { border-color: var(--st-error); }
[data-bd="selected"]   { border-color: var(--accent); }
/* 常规 = --line-hairline（比 0.845 降一级）；演示 = --rule-region-ink（0.545，与同屏其他格同值）。
   两个档由 --st-downstream-border 一个 token 表达，组件里不写 if (mode === 'present')。 */
[data-bd="downstream"] { border-color: var(--st-downstream-border); }
```

> **为什么不是 `--line-default`**（上一版写错的地方，值不值得记一笔）：`--line-default` 在常规块是 0.845，**恰好与 `--rule-region-ink` 相等**，所以常规态看不出问题；到演示块两者分叉（0.760 / 0.545）才暴露。一旦格线取 0.760，16 格对纸底只有 **2.9:1**，整张矩阵在投影上发灰、被读成"没画完"。
> **`--line-default` 0.760 只服务非格子结构线**（控件边、表头框、分区里的细线）——那里是单条线、有周边留白托着，2.9:1 够用；格子是 16 个并列的闭合框，密度完全不同，不能共用一档。
> 顺带记住 team-lead 那句口径：**「与其他态同值」这个说法在常规态成立、在演示态是陷阱** —— 常规态两个 token 恰好相等，会让人误以为它们永远相等。**凡是要靠"同值"的推断，一律引 token 名，不引数值。**

> **结构线走 `border`，不走 `inset box-shadow` —— 二选一，不许两个都留。**
> 两个都留 = 每格 2px（1px 边框 + 1px 阴影叠在一起），而这不是最坏的情况：**最坏的是有人把线改成 `box-shadow` 之后，`data-bd` 仍在改 `border-color`** —— 它会静默失效（不报错、不生效），属于最难查的一类。既然 `data-bd` 消费的是 `border-color`，结构线就必须是 `border`。
> `inset` 在这套规则里只有一个用途：**加厚**（`selected` +1px、`error` +2px）。它不画结构线。

需要"2px / 3px 厚度"的状态（`selected`、`error` 的红边）**一律用 `box-shadow: inset` 叠加**，不动 `border-width`。`inset` 画在格内、不占布局、不碰格线。

> **另外三个已写死的禁令**（起因都真实发生过）：
> 1. **不许 `border: none`，不许把 `border-color` 设成 `transparent` 或纸色** —— 6px 间隙下每格边框就是它的身份证，缺一条那格读作"没画完"，15 格会一起塌成洞。
> 2. **不许引用没核过的 token**：`border-color: var(--不存在的变量)` **不报错**，会静默回落到 `currentColor`（= 文字色），那一格的框会比谁都黑。W1 加一条 DEV 断言就够：`getComputedStyle(cell).borderTopColor !== getComputedStyle(cell).color`，跑一次、成本 0。
> 3. **不许"尺寸内缩"**（见下）。

**为什么宽度必须恒定（V15 的唯一正解）**

| 态 | `border-width` | `border-color` | `box-shadow: inset` | 观感 |
|---|---|---|---|---|
| `idle` / `changed` / `key` / `done` | 1px | `--rule-region-ink` | 各自装饰（顶条 / 左竖条 / 无） | 1px |
| `selected` | 1px | `--accent` | `0 0 0 1px var(--accent)` | 2px |
| `error` | 1px | `--st-error` | `0 0 0 2px var(--st-error)` + 底 2px | 3px |
| `error + selected` | 1px | `--st-error` | 2px 红 + 外环 `outline 3px` | 3px 红 + 环 |
| `downstream` | 1px | `--line-hairline` | — | 1px |

演示态同一张表，`border-width` 一律 2px，`inset` 数值按视觉 §2.3.2 的加粗档（顶条 3px、选中 +1px、错误 +2px）。**模式切换（1px ↔ 2px）会引起一次 1px 位移，这是允许的**（它由 `data-mode` 驱动、一次布局切换，不是状态切换）；**七态之间绝不能改宽度**。

**`downstream` 的最终形态（终稿，四个通道逐格对齐，不再改）**

| 通道 | 常规态 | 演示态 |
|---|---|---|
| 边框 | `--st-downstream-border` = `--line-hairline`（**降一级**，宽度仍 1px、线型仍实线） | **不降**：`--st-downstream-border` 的演示覆盖 = `var(--rule-region-ink)`（0.545 / 4.6:1），与同屏其他格**同值**（2px） |
| 底色 | `--surface-inset`（ΔL 0.036） | `oklch(0.905 0.004 258)`（ΔL 0.06，常规档的两倍） |
| 文字 | `--ink-3` / **400** | `oklch(0.415 0.012 258)` / **8.4:1** / **400**（同屏其他态均 700，字重本身是通道） |
| 角标 / 纹理 / `≠` | 全无 | 全无 |
| 尺寸 | **不变** | **不变** |

**四个通道叠加的结果**：边框浅一级、底色退一档、墨量降一级、（演示态）字重降一级。**四者都是"轻"，没有一个是"小"。**

**演示态为什么不降边框**：演示块里**所有**字节格都是 `--rule-region-ink` 0.545。`downstream` 若在这条通道上再降一级，唯一可落的值就是 `--line-default` 的演示值 0.760 —— **比邻居更浅**。那不是"轻一点"，在 6px 间隙里那是"这一格的框没画完"：同一张矩阵里出现一个更浅的闭合框，读者只会读成缺墨，不会读成"先别看"。所以演示态**放弃边框通道**，安静感完全交给"底色 ΔL 0.06 + 字重 400 对 700"。这就是"淡框在投影下等于没有"那条结论的正确用法：**不去找一条更淡的线，而是让它根本不靠线。**
> 注意这里没有"降不降都行"的余地：**降 = 比邻居浅 = 读作没画完；不降 = 与邻居同值 = 读作正常一格，靠底色和字重说话。** 前者是错误，后者是取舍。

**常规态为什么又"能"降一级**：常规态是**笔记本屏幕**（课后自习 1366×768），不是投影。近距屏幕上看 `--line-hairline`（L 0.885）是**能看见的浅灰线**，只是不抢。同一档色值在两个场景里一个是"可辨的轻"、一个是"看不见"，这不是谁判断错，是**场景不同**——所以两档必须分开写，不能用一个值覆盖两个场景。**但两档的"降"都必须是相对同屏邻居的"更浅"，不能是相对另一个模式基准值的"更深"。**

**为什么不能用"尺寸内缩 1.5px"替代**（这条与 V15 同族，必须一起守）：内缩会让那一格的可视矩形**比邻居小一圈**。16 格的"方块感"建立在尺寸完全一致上，在 6px 间隙下一格小一圈一眼就能看出来，而"大小不一致"在读者眼里只有两种解释——"这格更重要/更轻"或"这格异常"，**两种都不是"安静"**。

> **位移是位置跳，内缩是尺寸跳，都是几何变化。** 任何靠改几何来表达状态的做法，都会被误读成"这一格有毛病"。要表达"退后"，只能用**变淡**（色阶 + 墨量），不能用变形。这条是"格子绝不位移、绝不缩放"那条视觉红线的另一半。

**一句话区分三个容易混的态**：`done` 用**形状**（左下 5px 缺口）说"已结束"；`downstream` 用**色阶 + 墨量**说"先别看"；`error` 用**红折角 + 红边 + `≠`** 说"这里错了"。三者不共用任何一条通道。

**禁止用 `!important` 兜底**（`hidden` 那条除外，见 §3.5）：它会制造"三态同时生效"这种不可调试的结果，上面这张表不需要它。

**网格容器只负责排布，不画线**

```css
.c-matrix__grid { display: grid; gap: var(--cell-gap); }   /* 6px，不动 */
.c-byte         { border: 1px solid var(--bd-color); background-clip: padding-box; }
```
不要写容器底色 + `gap:1px`（会把 6px 留白塌成 1px、矩阵总宽从 `4×72+3×6=306px` 变 `291px`，摘要句与轮密钥轨的相对位置全要重排），也不要插 6 个绝对定位的线节点（多 6 个节点只为解决一个不存在的问题）。`background-clip: padding-box` 是为了让 `is-changed` 的满涂底色不糊到自己的边框上。

**实现写法**：`useMatrixWriter` 里不要 join 一堆 class 让 CSS 去打架，而是**按通道各算一个值**（六个通道 → 六个确定的值，顺序无关）——

```ts
// 单值通道 → 一个字节格最多 6 个 owner，永不存在"两个 owner 同时命中"
type Fill   = 'error'|'selected'|'changed'|'downstream'|'done'|'idle'
type Bd     = 'error'|'selected'|'downstream'|'idle'   // 只有这 4 态改边框色（视觉 §2.3.1）
type Txr    = 'fold'|'hatch'|'none'
type Corner = 'br'|'tl'|'tr'|'bl'

const FILL_CLS: Record<Fill, string> = {
  // ⚠️ selected 在这里是空串：`is-selected` **只从下面那个布尔出来**（单一来源）。
  //    两个来源出同一个 class，等以后有人改这张表，就会变成双份或漏份。
  error: 'is-error', selected: '', changed: 'is-changed',
  downstream: 'is-downstream', done: 'is-done', idle: '',
}

function paintFor(i: number): BytePaint {
  const isErr = errorSet.has(i), isSel = selectedIdx === i
  const keyed = keySet.has(i)                    // 判分期不让位：key 是输入条件，不是 diff 信息
  const isDn  = !isErr && downstreamSet.has(i)   // error ⊥ downstream
  const showChanged = changed[i] && !grading     // 判分期 changed 整体让位

  // ① 底色：单值。唯一例外是 error+selected，由 §3.1 那条两类选择器规则补出口
  const fill: Fill = isErr ? 'error' : isSel ? 'selected'
    : showChanged ? 'changed' : isDn ? 'downstream'
    : doneSet.has(i) ? 'done' : 'idle'

  // ② 边框色：单值，写入 data-bd
  const bd: Bd = isErr ? 'error' : isSel ? 'selected' : isDn ? 'downstream' : 'idle'

  // ③ 纹理：单值，写入 data-txr（error 折角 > key 斜纹：折角是"错了"的唯一形状）
  const txr: Txr = isErr ? 'fold' : keyed ? 'hatch' : 'none'

  // ④ 角位：按 br > tl > tr > bl 取前 2（错误 > 反向 > 变化 > 完成）
  const cand: Corner[] = []
  if (isErr) cand.push('br')
  if (reverse) cand.push('tl')
  if (showChanged) cand.push('tr')
  if (doneSet.has(i)) cand.push('bl')

  return {
    v: values[i]!,
    // ★ is-key 必须在这里出现：它承载的不是纹理，而是「左边缘 3px 竖条」这条
    //   只有 key 使用、永不竞争的通道。判分期 txr 被 error 的 fold 占掉时，
    //   竖条是学生唯一还能看出"这 8 个字节参与异或"的东西。
    cls: ['c-byte', FILL_CLS[fill], isSel ? 'is-selected' : '', keyed ? 'is-key' : '']
           .filter(Boolean).join(' '),
    bd, txr,
    corners: [cand[0] ?? '', cand[1] ?? ''],
  }
}
```

> **四点说明**：
> ① **每个通道只算一次、只出现一次**，所以"谁盖谁"这个问题根本不存在，也就不需要 `!important`。
> ② `fill` 是单值输出，末尾**不再补 push** `is-downstream` / `is-error`（同一个 class 出现两次会让"谁是 fill 的 owner"说不清）。
> ③ 角位截断顺序必须是 `br > tl > tr > bl` —— 写反了会在 `error + reverse` 时正好丢掉高优的那个，防御代码写错方向，出事时正好错在最不该错的地方。
> ④ **`is-key` 同时输出两条通道**：`txr=hatch`（纹理）与 `bar`（左竖条）。后者是**只有 `key` 一个候选的通道**，没有优先级、不进角位截断，所以 `is-key` 永远输出、不受判分叠加影响。反过来说：`is-key` 在实现层**只输出「纹理 + 左竖条」，绝不输出底色** —— 底色归 fill。否则轮密钥加那一步 16 格全是 key，16 格的 `is-changed` 黄底会全被石墨 6% 盖掉，"本步变化"这个最常看的信号当场消失。

**三条实现陷阱（都会真的踩到）**

1. **`is-key` 的斜纹必须叠在不透明底色之上**。只给 `background-image` 不给 `background-color`，条纹会直接压在纸色上，密度看起来比别的格稀，而且和 `--surface-inset` 的 downstream 混在一起分不清。
2. **`selected` 的"外 3px 环"不能用 `inset`**（inset 画在格内，环必须在格外）。外环用 **`outline: 3px solid var(--accent-ring); outline-offset: 2px`** —— 不占布局、不受 `gap` 影响、不会被相邻格裁剪。内圈那 1px 加厚用 `inset`，两者叠加即规范里的"内 2px + 外 3px 环"。`outline` 与 `border` 是两个独立通道，这也是"`error + selected` 能同时表达"的物理基础。
3. **`border-width` 七态恒定 1px（演示态恒 2px），只改 `border-color`**。切状态时改 `border-width` 会改内容盒，让 hex 文字位移 1–3px —— 而本项目第一条视觉红线是"格子绝不位移、绝不缩放"。需要更厚就用 `box-shadow: inset` 叠加，它画在 padding box 内侧，不动盒模型。

**四角与双上标的 DOM 契约（ux 定稿，元素数按"上限"而不是"总数"配）**

角标元素数 = **同格最多角标数（2）**，不是四角总数（4）。规则上限 2 决定了 DOM 上限 2，另外两个角永远不会出现，不必预留节点 —— 也不要用 4 个通用元素（32 个额外节点纯属浪费）。

```html
<!-- 每个 c-byte 内固定 2 个通用角元素，位置/形状/颜色全由 data-corner 驱动；空闲时 data-corner="" -->
<span class="c-byte__corner" data-corner="" aria-hidden="true"></span>
<span class="c-byte__corner" data-corner="" aria-hidden="true"></span>
<!-- 双上标常驻，用 data-active 切换，不用 v-if、也不依赖 UA 的 [hidden] 样式 -->
<span class="c-byte__sup" data-kind="neq" data-active="false" aria-hidden="true">≠</span>
<span class="c-byte__sup" data-kind="xor" data-active="false" aria-hidden="true">⊕</span>
```
- `data-corner` ∈ `tl | tr | br | bl | ""`（空串 = 该槽空闲）；**基类 `.c-byte__corner` 不带任何几何**（没有默认位置、没有默认颜色），全部由 `data-corner` 驱动。理由：不要复用一个叫 `__flag`、基础样式绑死在"右上+琥珀"上的元素去改定位——那等于让样式完全由修饰符驱动，后续谁加一个未覆盖的修饰符就露馅。
- **截断顺序（防御性代码，必须与优先级同向）：`br`(error) > `tl`(reverse) > `tr`(changed) > `bl`(done)**，按序取前 2 个填入两个槽。写成 `[br, tr, tl, bl]` 这类顺序是错的：`error + reverse` 同时出现时会截掉 `tl` 保留 `tr`，正好把高优先级那个丢掉。虽然实际最多同时 2 个（`changed` 在判分期让位、`done` 与 `changed` 互斥），但防御代码错方向，出事时必然错在最不该错的地方。
- 视觉 §9.1 的 `__flag` / `__fold` / `__notch` **不是额外节点**，它们就是这三个角位的旧命名：`__flag`→`tr`、`__fold`→`br`、`__notch`→`bl`。实现只留 2 个通用 `__corner`，几何/形状/颜色照搬。**同一个角绝不允许多个元素同时渲染**（这条写进 corner 通道的准入）。
- 2 × 16 = 32 个新增节点，对单 rAF 批处理**无影响**（`useMatrixWriter` 只改属性不改结构），但**必须常驻** —— 用 `v-if` 会在状态切换时销毁重建，引用缓存失效。

**`hidden` 的坑（必须避开）**：`hidden` 属性是靠 UA 样式 `[hidden]{display:none}` 生效的，**特异性极低、可被覆盖**。如果 `.c-byte__sup` 上有 `display:inline-block` 之类规则，`hidden` 会失效，两个上标同时显示。**不要依赖 UA 样式**，二选一：
```css
/* 方案 A：显式提权（唯一允许用 !important 的地方） */
[hidden] { display: none !important }
/* 方案 B（推荐）：自控，不碰 hidden 属性 */
.c-byte__sup[data-active="false"] { display: none }
```
两个 `sup` 都保持 `aria-hidden="true"`，读屏信息只走根元素的 `aria-label`（已经在做）。`display:none` 的 sup 不占位、不计入角区几何。

**区域级原则（两条，都是样式硬约束）**

1. **大面积/区域级的视觉通道只能表达「范围」或「程度」，不能表达「对错」**。判分条可以红，矩阵不能整块红。
2. **整段错时矩阵不画外框**，只画**实线四角括 + 文本「影响范围：16 字节」**。三条排除理由：完整外框（哪怕是中性 2px 实线）也带「围起来 = 这块有问题」的语气；**虚线不行**（线型有专义）；**琥珀不行**（琥珀是 `changed` 的色，是学生看得最多的颜色，一旦兼职表达「有问题」，`changed` 的语义就废了）。

**整段错的派生规则（不需要新字段）**：
```
first_diff.step === 0 && propagated.length === 16  →  整段错版式
  = 1 格 is-error + 15 格 is-downstream + 四角括 + 标签「影响范围：16 字节」
否则                                              →  常规定位版式（只高亮首个差异字节 + 其余 propagated 灰化）
```

**线型语汇（三行定稿，全站唯一解释，不得借用）**

| 线型 | 唯一含义 |
|---|---|
| 虚线 | 未生效 / 待定 / 禁用（全规格已用 11 处） |
| 实线 | 已生效 / 确定 |
| 点划线 | 仅演示态，替代纹理 |

**准入规则（比表本身更重要）**：新增线型用法先找它属于哪一行，**找不到就说明这个状态需要的不是线型**。

`downstream` 就是那个"找不到"的案例 —— 它需要的不是"一条语义特殊的线"，而是**"线不参与表意"**。所以：

- **常规态**：边框**只降一级色**（`--rule-region-ink` → `--line-hairline`），线型仍是实线、宽度仍是 1px。**这是减噪，不是表意** —— 语义完全由「底色内缩一档 + 墨量降到 400 + 同屏其他态都是 700」承担。
- **演示态**：**边框不降**，直接等于其他态。因为投影会把任何"降一级"抹平，降了也读不出来，不如干脆不靠它。
- 因此 `downstream` **没有专属线型**，也**不需要**在表里新增一行。

> **两条已撤回的错误语汇，不要再加回来**：
> - 「无边框 = 不强调」—— 这是把结构承载和语义承载混为一谈；6px 间隙下每格的外框是它自己的完整矩形，抽掉一根会被读成"这格没画完"，不会被读成"安静"。
> - 「极淡实线 = 存在但不强调」—— 淡框在 1280 投影下约 1.1:1 等于没有。**撤回的不是"边框可以降级"，撤回的是"用一条看不见的线去表达不强调"这个做法**：`downstream` 的语义一律不落在线上，只落在底色与墨量上。

**产品级红线：`is-error` 的装饰必须带 `:not(.is-downstream)` 保护（visual §9.1 指定，必须加）**

```css
/* ★ 闸门的粒度必须下沉到"真正渲染的那个元素"。
   挂在 .c-byte::after 上只护得住伪元素 —— 折角已经是真元素，会漏掉。 */
.c-byte.is-error:not(.is-downstream) .c-byte__corner[data-corner="br"],  /* 折角 */
.c-byte.is-error:not(.is-downstream) .c-byte__stage::after,              /* 底部条 2px */
.c-byte.is-error:not(.is-downstream) .c-byte__sup[data-kind="neq"] {    /* ≠ */
  /* 三条装饰的规则体 */
}
```

> **这一条被改过一次，值得记住原因**：`is-error` 的折角原来是 `.c-byte::after` 画的，所以闸门写 `.c-byte.is-error:not(.is-downstream)::after` 是对的；折角改成真元素 `__corner` 之后，**闸门挂在旧位置上就变成"保护了一个已经不存在的渲染者"** —— 而新元素照样会渲染，且**不报错**。这类"选择器指向的对象被换掉、选择器本身语法完全合法"的失效，是重构里最难发现的一类。**改元素的承载方式时，必须同时搜一遍挂在这个元素上的闸门/条件选择器。**
> 另一条纪律：**闸门也要收窄到具体值**（`[data-corner="br"]`、`[data-kind="neq"]`），不要写 `.c-byte__sup` 一锅端 —— 否则将来 `⊕`（xor，轮密钥加语义）也会被这条错误闸门顺手关掉，而那是一个**必须**在出错的轮密钥加步骤里显示的上标。

理由不是 CSS 洁癖：**万一状态机出错、让 15 个受污染格同时命中 `is-error`，它们会同时长出红折角，正好触发"满屏红 = 我全错了"这个归因错误** —— 而 F5 第三层存在的全部意义就是防这件事。这层 `:not()` 是第二道闸，第一道闸是 §3.1 的 owner 表（`error` ⊥ `downstream` 由 `useMatrixWriter` 保证）。

### 3.2 Canvas 层（只画会动的几何）

- **1 个 canvas** `<canvas class="c-matrix__fx">`，`position:absolute; inset:0; pointer-events:none`。
- **dpr**：`canvas.width = Math.round(w * dpr)`，`ctx.setTransform(dpr,0,0,dpr,0,0)`，之后所有坐标用 CSS px。`dpr` 从 `window.devicePixelRatio` 取，并监听 `matchMedia('(resolution: …dppx)')` 变化（跨屏拖动窗口时 dpr 会变，只监听 resize 不够）。
- **两个 pass**，由 `activeOp` 选择，同一时刻只跑一个：
  - `drawRowShift(ctx, m, rowIndex, t)`：画 4 条回归线（1px `strokeRect`，`alpha = 1 - t`，仅回绕格 + 行列交界处）。**不画字节**。
  - `drawMixScan(ctx, m, colIndex, t)`：1px 竖线 `y = padTop + t * matrixH`，尾部 40px 渐隐（用 `createLinearGradient` 的 alpha，非 blur）。
- **重绘策略**：动画期间每帧全量 `clearRect` + 重画（元素数 ≤ 6，实测 <0.4ms，脏矩形收益为负）。**静帧时 canvas 置 `visibility:hidden`**，不给合成器留脏层。
- **网格基线用 DOM，不用 Canvas**（team-lead 裁决，覆盖视觉规范原文，已通知视觉改规范）。1px 线由**每格自己的 `border: 1px solid var(--bd-color)`** + `--cell-gap: 6px` 承载（v1.9 定稿；不写 `inset box-shadow` 画格线、也不由容器统一画）。理由不只是"更稳"：**dpr=1 或 125%/150% 系统缩放时，Canvas 的 1px 会落在 0.5px 上，渲染成 1.5–2px 灰线且各缩放下粗细不一** —— 这会让"发丝线"这个主分区语言在别人电脑上直接失效。**因此 Canvas 只剩 2 个 pass**（回绕描边 / 列混合扫描线）。**四角刻线与列括线在 SVG**（注意：四角刻线只用容器级用途，**选中格不画刻线** —— 与 `error` 右下折角同位置同尺寸，会叠死，见 §3.1）。
  - **不留兜底开关**：不写 `drawBaseline`、不做"A/B 切换"。兜底开关等于把决策推迟到出问题时，那时更没时间判断。
- **单 canvas 是"当前纪律的推论"，不是架构约束**：因为单活动焦点原则保证行移位与列混合永不同时，1 个 canvas 够用。**若未来出现并发动效需求，`StageCanvas.vue` 必须能降级为两个 canvas 叠放** —— 请在 `StageCanvas.vue` 顶部写这段注释，不要让它被读成"只能有一个 canvas"。

### 3.3 SVG 层（静态结构与连线）

- 一个 `<svg class="stage-svg" viewBox="0 0 {w} {h}" preserveAspectRatio="none">`，**viewBox 用像素而非格数** —— 这样 `stroke-width="1"` 恒为 1 物理 CSS px，不随缩放变粗。
- 子层：`<g id="brackets">`（列括线，静态，随 metrics 重算 `d`）、`<g id="corners">`（**仅活动区/容器级四角刻线**，选中格的刻线已停用 —— 它与 `error` 的右下折角同位置同尺寸，见 §3.1）、`<g id="crosshair">`（S 盒准星，2 条 `line`）、`<g id="annot">`（红线批注 `path`，`stroke-dasharray` 驱动）。**选中格的形状信号是 DOM 层的 `outline` 环，不在 SVG 里。**
- 所有线 `shape-rendering="crispEdges"`，坐标 `+0.5` 偏移对齐像素栅格。
- 理由：SVG 承载"数量固定、跟随坐标但自身不逐帧变化"的东西；逐帧变化的一律进 Canvas。

### 3.4 三层如何对齐

**唯一坐标系 `useStageMetrics`**：

```ts
// 输入：stage 容器 ResizeObserver（不是 window.resize —— 收 AI 栏也会变宽）
// 输出：{ cell, gap, padX, padY, w, h, dpr }
// 实现：RO 回调里只做一次 layout 读（getComputedStyle 拿 --cell-size/--cell-gap、
//      getBoundingClientRect 拿容器宽），然后写一个 rAF 批量提交给 metrics（reactive）
```

- **`--cell-size` 用离散桶 + 容器查询，不用连续 `clamp()`**（v1.1 修订，取代 v1.0 的 `clamp(48px,4.6vw,64px)`）。理由：连续 clamp 在跨越断点的那一帧会算出十几档中间尺寸，16 格同时重排；离散桶只在换档时重排**一帧**。
  **88px 档只在演示模式可达，普通模式上界锁 72px**（team-lead 裁决：1366×768 下 `4×72 + 3×6 = 306px` 已是矩阵区可承受上限，再大要挤掉轮密钥轨）。
  ```css
  .stage { container-type: inline-size; }
  .c-matrix { --cell-size: 44px; }
  @container (min-width: 640px) { .c-matrix { --cell-size: 52px } }
  @container (min-width: 780px) { .c-matrix { --cell-size: 62px } }
  @container (min-width: 920px) { .c-matrix { --cell-size: 72px } }   /* 普通模式封顶 */
  /* 88px 只对演示模式开门，且要求 ≥1120px（4×88 在 1024 视口溢出） */
  /* 88px 主档：阈值是「stage 容器宽」不是视口宽（visual §6 定稿 720px 容器） */
  @container (min-width: 720px) { [data-mode="present"] .c-matrix__grid { --cell-size: 88px } }
  ```
  **注意选择器特异性**：`[data-mode="present"]` 写在 `html` 上，`.c-matrix` 在其内部，所以上面这条是"祖先属性 + 后代类"，特异性高于第三档，能正确覆盖。**不要**写成 `.c-matrix[data-mode="present"]`（属性不在矩阵上，永远不命中，是最常见的静默失效写法）。
- DOM 用 `--cell-size` / `--cell-gap` 自排布，**不读 metrics 布局**；容器查询换档 → ResizeObserver 触发 → metrics 更新 → Canvas/SVG 跟上（走 §3.4 的 5 步顺序）。**换档本身不做过渡动画**（宽度变化不可能 60fps，见 M26 的两段 opacity 遮罩）。
- Canvas 与 SVG **只用 metrics 的像素值**，因此天然与 DOM 一致（前提：三者共用同一 `padX/padY`，由 `matrix` 的 padding 决定，写进 metrics）。
- resize 同步顺序（单 rAF 内）：① 写 CSS 变量 → ② 读一次 `getBoundingClientRect`（唯一一次强制布局）→ ③ 写 metrics → ④ canvas 改 backing store + 重绘 → ⑤ svg 改 viewBox。**顺序不可交换**，否则 read-after-write 触发二次布局。

### 3.5 三个"数据接口是 CSS 变量"的组件（照视觉 §9 实现）

这三个组件的坐标一律**由 CSS 变量驱动、只改变量不改 DOM 结构/内联 top**，否则每次更新都触发一次布局，而在播放/批注动效期间布局抖动会非常显眼。

| 组件 | 唯一数据接口 | 写法 | 禁止 |
|---|---|---|---|
| `c-timeline` | `--i`（步下标）、`--span`（该轮步数） | 所有 x 坐标由 CSS `calc()` 从这两个变量算；播放时每帧只写 1 个 CSS 变量，**零组件重渲染** | 禁止改 DOM 结构、禁止给每步单独 `left`、禁止用 Vue 列表更新来挪游标 |
| `c-annotation` | `--tick-y` | JS 从"目标格 `getBoundingClientRect().top` − 舞台顶"算出，写成 CSS 变量；刻痕 `position:absolute; left:-1px` 压在 E 区左分隔线上 | **禁止直接改 `style.top`**（批注出场时 16 格正在动，layout 抖动显眼）；禁止刻痕进入 C 区 |
| `c-diagslot` | 无（常量高度） | E 区顶部**常驻槽**：`height: var(--diag-row-h)` **锁死**，`aria-live="polite"` **挂在槽位上**（不是挂在批注上 —— 批注卸载后读屏仍能播报最后一次内容）；无提示时显示 `__idle` 占位 `DIAGNOSTIC —` | **批注绝不用 `position: fixed`**（它是行内块不是浮层）；**槽位高度任何状态都不变**，内容变长走槽内滚动；批注出场只动 `opacity` 与 `translateY(2px→0)` |
| `c-sbox` | `--hl-row` / `--hl-col` | 行列高亮线是**两个绝对定位 div**，只改 `transform: translateY/translateX`；4×4 分组线用 `td:nth-child(4n+1){border-left}` + `tr:nth-child(4n+1){border-top}`，**不加 DOM** | 禁止给 256 个 `<td>` 批量加 `is-hl`（256 次样式重算）；交叉格只切单格 `is-cross` |

**时间轴结构要点**（视觉 §9.3）：`.c-timeline` 是 `role="slider"` + `aria-valuemin/max/now/valuetext`；4 条轨道 `.c-timeline__rounds / __ticks / __marks / __cursor`；`.c-timeline__marks` 是 `role="group" aria-label="学习足迹标记"`。
**标记是 `<button class="c-mark">`：一步一个按钮，不是两个。**

热区 = **该步整列宽（`width:100%`）× 标记轨全高 `--tl-mark-band`（常规 20 / 演示 24 / 压缩 18）**，元素自身撑满热区；一个 `<button>` 同时承载该步的诊断与提问。**圆与方是它的两个 `<i>` 子元素，不是两个 button、也不是伪元素**（visual r5 改判，理由见下）：

```html
<button class="c-mark" style="--i:3" data-kinds="diag ask" tabindex="0"
        aria-label="第 3 轮列混合，1 条系统推测、2 次提问，按回车打开标记详情">
  <i class="c-mark__shape" data-kind="diag" aria-hidden="true"></i>
  <i class="c-mark__shape" data-kind="ask"  aria-hidden="true"></i>
</button>
```
```css
/* ① 宿主：轨道上的按钮 与 图例里的定高盒，共用同一条"定位上下文"规则。
   图例项必须是 position: relative —— 否则形状会相对更远的祖先定位（见要点 3）。 */
.c-mark,
.c-transport__legend-item { position: relative; height: var(--tl-mark-band); }

.c-mark {
  width: 100%;                      /* 取该步列容器的 100%，**绝不写死像素** */
  background: transparent;
}

/* ② 形状原子：尺寸 + 形状 + 上下贴边。尺寸走 token（常规 5px / 演示 6px），不写死 */
.c-mark__shape { display: block; position: absolute; left: 50%; transform: translateX(-50%); }
.c-mark__shape[data-kind="diag"] {
  width: var(--tl-mark-diag); height: var(--tl-mark-diag);
  border-radius: 50%;
  background: oklch(0.545 0.195 27);   /* 视觉 §6.3.3 ③；该色暂无 token → W1 补 --tl-mark-diag-ink */
  top: 0;                              /* 贴上沿 y30–35 */
}
.c-mark__shape[data-kind="ask"] {
  width: var(--tl-mark-ask); height: var(--tl-mark-ask);
  border-radius: 0;
  background: var(--accent);           /* 视觉 §6.3.3 ③ */
  bottom: 0;                           /* 贴下沿 y41–46 */
}
```

> **颜色这条要单独说一句**：诊断色在视觉 §6.3.3 里是**字面量 `oklch(0.545 0.195 27)`，没有 token**（提问色有，是 `--accent`）。本项目口径第 ⑤ 条要求"只引 token 名、不引色值"，所以这里**照抄一次是债，不是范例**：W1 开工时补一个 `--tl-mark-diag-ink` 收掉它，之后本节只留 token 名。**一条没有 token 的颜色，就是下一个"只在某个模式里改对了一处"的源头。**

三处必须照做，缺一处就是不同实现：

1. **`data-kinds` 仍然是空格分隔的多值**，`~=` 匹配；同一步可以同时有圆和方（硬规定）。**两个形状用两个独立 `<i>`**：`::before` 只有一个，本来就画不了两个。
2. **宽度绝不写死**：24 步列宽 ≈ 25px、58 步 ≈ 10px，写死 12px 会出现"点第 13 步落到第 14 步"—— 这与当初否决"8px 横条"是同一个病。**形状自身的 5px / 6px 也不许写死**，取 `--tl-mark-diag` / `--tl-mark-ask`（演示档是 6px，写死 5px 会让演示态标记偏小、与图例对不上）。
3. **`position: absolute` 只能落在形状上、且两个宿主都必须 `position: relative`**。图例复用的是同一个 `<i>`（见 §10.2 图例条），**不许为图例写 `[data-ctx="legend"]` 之类的定位覆盖** —— 那等于放弃"像素级一致"这条验收。**"同一个元素、两处复用"的前提是：形状归原子，定位上下文归宿主。**

**为什么从伪元素改成 `<i>`**：
- 图例要"与轨道形状尺寸完全一致"，而这个验收只有**复用同一个元素**才能在结构上天然成立；伪元素方案只能复用规则，图例仍需一个宿主元素，多一层间接就多一处对不齐。
- 两个伪元素被形状占满后，这个元素就永久失去了装饰额度 —— 以后任何 hover 环、focus 刻线、纹理都得绕。换成 `<i>` 后额度重新打开（但**仍不要滥用**：`.c-mark` 内只允许这 2 个 `<i>`，见 §3.5 末条）。

**为什么不是"上下两个半区各 10px"**：两个 10px 目标上下直接相接，以任一目标为圆心画 24px 判定圆，必然与另一个相交——**两个都不达标，不是各让一半**。而且学生在这一层的意图是"这一步有标记"，不是"我要精确点到那个圆"。

**精确选择放在 E 区的标记卡里**：卡内按类型分组列出，每条行高 28px 独立可点。**"一步一个按钮"+ 卡内分组 = 用达标的大目标做粗选、用达标的中目标做精选**，两处都满足 24px，没有一处需要例外。

- `aria-label` 同时播报两类计数（见上例），不能只播一种。
- **Tab 序列只放"有标记的步"**，否则 AES-256 的 58 步会变成 58 个 Tab 站。
- 热区只服务鼠标，不能作为唯一路径（`[` / `]` 跳转、滑块方向键、卡内条目三条等价路径必须都实现）。roving tabindex：整组仅最近的 1 个为 `0`，其余 `-1`。
**标记轨内 z：标记 3 > 游标 2**（原"游标压标记、标记左偏 1px"方案已撤销：2px 游标压 5px 标记只露 1px，等于没露）。
**Transport 高度是三档，不是两档**：常规 **104**（控制行 40 + 时间轴 64）／**压缩 92**（`@media (max-height: 780px)`，覆盖 1280×720 场景）／演示 **136**。压缩档**只压高度、四轨仍全在**（16→14 / 10→8 / 20→18 / 14→12）。
**若已写了 104 硬编码，必须补这一档** —— 1280×720 是验收基线分辨率之一，漏了会在该分辨率下挤掉矩阵。
四轨 y 坐标三档精确表见视觉规范 §6.3.2，**不要在实现里硬编码一套新数字**。
- 100ms 防抖只用于"非拖拽中"；拖拽/动画进行时 resize 也要走同一路径，靠"单 rAF 内只读一次"控制成本。

---

## 4. 动效实现参数表

> 通用：所有时长/缓动只能取 `--d-1..--d-4` / `--e-out-quart`。
>
> **reduced-motion 归零公式（三段，缺一不可）**：
> 1. `--d-1..--d-4`、`--d-linger` **置 `0.01ms`**（不是 `0`：`0ms` 会导致 `transitionend` 永不派发，抽屉的 `@after-leave` 挂死）；
> 2. 所有描边/位移类动画 `animation: none`；
> 3. `el.getAnimations().forEach(a => a.cancel())` —— **光把时长设 0 不够**：`stroke-dashoffset` 动画在 `transition-duration: 0` 下会停在中间值，红线批注会留半截。
>
> **配一条硬规则保证 `cancel()` 安全**：所有"描边/位移"类动画的**静止态必须是终态**，动画从 0 正向播到终态。这样 `cancel()` 只会回到"完整可见"，而不是"未绘制"。若把静止态写成"不可见"，`cancel()` 会让元素消失 —— 这是本项目最容易出的归零事故。
>
> **`--step-interval` 故意不归零**：播放节奏与动画时长解耦，归零后仍能按 800ms 步进。
>
> **归零后的静态替代（信息不能丢，4 条必须全做）**：
> - 变化字节：直接换终值 + 右上角 **3px 实心琥珀角标常驻**（不是 1200ms 后淡出）
> - 行移位：不位移，行右端显示文本旋转量 `←1 / ←2 / ←3`，内容按移位后顺序呈现
> - 列混合：不扫描，列括线变 2px accent + 列顶文本标签 `MIX`
> - 轮密钥加：不跳变，格内出现 `⊕` 上标 + 密钥轨对应字同高亮

| # | 名称 | 实现方式 | 目标属性 | 时长 | 缓动 | stagger | 触发时机 | reduced-motion 归零 |
|---|---|---|---|---|---|---|---|---|
| M1 | 字节值滚动替换 | CSS `@keyframes`（两个 span 叠放） | `transform: translateY` | 280 | `--e-out-quart` | 0 | `step` 进入且 `changed[i]` | 归 0，直接换 `textContent` |
| M2 | 荧光底横扫 | `::before` 层 `transform: scaleX`，`transform-origin: left` | `transform` | 280 | `--e-out-quart` | 0 | 同 M1 | 归 0，静态满涂 |
| M3 | 顶条淡入 | `::after` 2px 高条 `opacity`（**不用 `box-shadow`**） | `opacity` | 160 | linear | 0 | 同 M1 | 归 0，静态可见 |
| M4 | linger 后回落 | class 移除后过渡到普通态 | `opacity` | 600 | `--e-out-quart` | 0 | M1 后 1200ms | 立即回落，保留 1px 描边 |
| ~~M5~~ | ~~字重 500→600→500~~ | **已删除，不进动效序列**。字重是**瞬时切换**（0ms），与 M1 数值滚动同时发生，无过渡、无时序。理由见 §10.3 Q2 裁决：等宽静态字体为一次 16px 数字换字体栈不值得，280ms 字重插值在 16px 下人眼不可辨 | — | — | — | — | — | 不变 |
| M6 | 字节替代 scaleY | `transform: scaleY(0.94→1)`，`transform-origin: center` | `transform` | 60 | `--e-out-quart` | **列优先 20ms/列** | `op=SubBytes` 步进入 | 取消 |
| M7 | S 盒十字准星 | SVG `line` 的 `x1/y1` 属性 + `opacity` | 位置 + `opacity` | 入 0 / 出 120 | linear | 同步 M6 列 delay | 同 M6 | 仅 120ms opacity，无位移 |
| M8 | 行移位（横向位移） | DOM **行轨道** `transform: translateX(-cellW)`，每行 8 格（4 实 + 4 鬼）`overflow:hidden` | `transform` | 280 | `in-out-cubic` | **行序 40ms** | `op=ShiftRows` 步进入 | 归 0，直接写终态 |
| M9 | 回绕描边闪 | Canvas `strokeRect` 1px | `strokeStyle.alpha` | 60 | linear | 0 | M8 该行结束时 | 取消，改静态角标 |
| M10 | 列混合计算线 | Canvas 竖线，`y` 线性推进 | 位置 | 280 | **linear** | **列序 60ms（总 460ms）** | `op=MixColumns` 步进入 | 取消 |
| M11 | 列 accent-soft 叠加 | DOM `::before` `opacity 0.12→0` | `opacity` | 600 | linear | 列序 60ms | M10 该列扫完 | 归 0，静态 8% 保留 |
| M12 | 列混合同列同步 | **零 stagger**（同列 4 格共用同一 delay） | — | — | — | 0（刻意的） | 同 M10 | — |
| M13 | 轮密钥加 · 密钥层淡入 | `opacity 0→0.6` | `opacity` | 120 | linear | 0 | `op=AddRoundKey` 步进入 | 归 0，直接可见 |
| M14 | 轮密钥加 · 底色石墨化 | `background-color` 过渡 | `background-color` | 160 | linear | 0 | M13 结束 | 归 0 |
| M15 | 轮密钥加 · 数值离散跳变 | **`transition-timing-function: steps(4, end)`** on `transform` | `transform` | 80 | `steps(4)` | 0 | M14 结束 | 归 0，直接换值 |
| M16 | 轮密钥加 · 密钥层淡出 | `opacity 0.6→0` | `opacity` | 120 | linear | 0 | M15 结束 | 归 0 |
| M17 | 红线批注折线 | SVG `path` + `stroke-dasharray/dashoffset` 三段串联；刻痕 y 由 **`--tick-y` CSS 变量**驱动（**禁止改 `style.top`**，会触发 layout） | `stroke-dashoffset` / `transform` | 420 总（140+160+120） | `ease-out` | 段间 0 | 诊断触发 / `?debug=diagnosis` | 归 0 且 `getAnimations().cancel()`，直接显示 |
| M18 | 批注方括号 + 反问 | `opacity` + `translateX(-4px→0)` | `opacity/transform` | 160 | `--e-out-quart` | 在 M17 后 40ms | 同 M17 | 归 0，静态显示 |
| M19 | 抽屉滑出 | `transform: translateX(100%→0)` | `transform` | 280 | `--e-out-quart` | 0 | 打开 F1/F2 | 归 0，直接出现 |
| M20 | 摘要句展开（L1） | `grid-template-rows: 0fr→1fr` + `opacity` | 布局（可接受，单次点击非 60fps 路径） | 280 | `--e-out-quart` | 0 | 点击展开器 | 归 0 |
| M21 | 时间轴游标 | `transform: translateX()`，**不用 `left`**；常态实心，**拖拽态改空心**（预览 vs 执行的双通道） | `transform` + `border-style` | 0（跟手） | — | 0 | 拖拽 / 播放 | 功能保留，空心更明显 |
| M22 | 流式光标 | `opacity` 闪烁 `steps(1)` 1s infinite | `opacity` | 1000 | `steps(1)` | — | `phase='streaming'` | **禁止**，改静态 `▍` |
| M23 | 错误折角出现 | 静态 6px `clip-path` 三角 + `opacity`。**只挂 `is-error`，`is-downstream` 绝不带折角** | `opacity` | 120 | linear | 0 | 判分返回且 `errorBytes.has(i)` | 归 0 |
| M23b | 下游污染灰化 | `is-downstream`：**无纹理无角标** + 底色 `--surface-inset` + `--ink-3` 400 + 边框**只降一级色**（`data-bd="downstream"` → `--line-hairline`；演示态不降）。**无动画**（判分展示期间只允许 M23 一处动效，避免"满屏在动") | — | — | — | — | 判分返回且 `propagated.has(i)` | 不变 |
| M24 | 焦点环（常规） | `outline: 2px solid var(--accent)` + `outline-offset: 2px` + **静态** `box-shadow: 0 0 0 4px var(--paper-0)` 隔离带 | `outline` + 静态 spread shadow | 0 | — | — | `:focus-visible` | 不变（无障碍不归零） |
| M25 | 焦点环（演示） | 内层 3px 近黑 `outline` + 外层 `var(--st-changed)` 双环 + 左外侧 8px `▸` 三角（`::before`，`transform: translateX`） | `outline` + 伪元素 | 0 | — | — | `[data-mode="present"] :focus-visible` | 不变 |
| M26 | AI 栏收起/展开（宽度变化） | **禁止 animate `width` / `grid-template-columns`**。三段：`C 区 opacity 1→0`(120ms) → **下一帧换栅格**（`--ai-col: 360px ↔ 48px`，无过渡） → `C 区 opacity 0→1`(120ms) | `opacity`（非宽度） | 120+0+120 | linear | 0 | 按 `F` / 点收起 | 归 0，直接换栅格 |
| M27 | 栅格换档遮罩 | 同 M26 的 opacity 遮罩兼任：`--cell-size` 离散桶换档那一帧，16 格在 `opacity:0` 期间完成重排 | `opacity` | 复用 M26 | linear | 0 | 容器跨断点 | 同上 |
| M28 | 诊断行占位 | 常量占位，无动画：`--diag-row-h: 40px`（演示 56px），无提示时显示 11px `DIAGNOSTIC —` | — | — | — | — | 始终 | 不变 |
| M29 | will-change 挂载 | `.is-playing, .is-dragging` 选择器内声明，**结束即移除** | `will-change: transform` | — | — | — | 进入播放/拖拽 | 移除 |
| M30 | C2 摘要句文字切换 | `opacity 1→0→1` 交叉淡入，**只在 1× / 0.5× 档启用**；2×（400ms）与 4×（200ms）档**直接换文本、零过渡** | `opacity` | 120 | linear | 0 | `currentStep` 变化 | 归 0 |

**两条容易做错的归零**：
1. **M15 的 `steps(4)` 在 reduced-motion 下必须换成"直接写终值"**，否则会看到 4 次闪烁 —— `steps()` 不是"位移"，媒体查询不会自动帮你干掉它。
2. **M8 反向后 `translateX(+cellW)`**，鬼格要放在左侧；`@keyframes` 必须写成两套（`shift-left` / `shift-right`），不能靠 `animation-direction: reverse`（reverse 会连 stagger 顺序一起反，视觉上像倒放而不是"反向执行"）。

---

## 5. 性能预算与检测方法

### 5.1 预算

| 指标 | 预算 | 判定口径 |
|---|---|---|
| 首屏 FCP | ≤ 1200ms | `vite preview`，本地，桌面 Chrome，无节流 |
| 首屏 LCP | ≤ 2000ms | 同上，LCP 元素应为矩阵首格 |
| TBT | ≤ 150ms | Lighthouse |
| 初始路由 JS（gzip） | ≤ 150KB | `rollup-plugin-visualizer` |
| 全量 JS（gzip） | ≤ 260KB | 工作台路由 ≤ 220KB（含 engine） |
| 单步切换（keydown→写完 DOM） | p95 ≤ 100ms | `performance.mark/measure` |
| 动画帧耗时 | p95 ≤ 12ms，**0 帧 > 20ms** | 自埋 rAF 采样 |
| 每步 Layout 次数 | ≤ 1 | Performance 面板计数 |
| 每步写批次 | **恰好 1** | `useMatrixWriter` 的 `batches` 断言 |
| Canvas 单帧重绘 | ≤ 2ms | `drawX` 前后 `performance.now()` |
| 前端生成 trace（离线降级） | ≤ 8ms（AES-256，32 步） | 单测 benchmark |
| CLS | ≤ 0.02 | `PerformanceObserver('layout-shift')` |
| 合成层数 | ≤ 4（矩阵 / canvas / 抽屉 / 侧栏） | DevTools Layers 面板 |
| 长任务（播放中） | 0 个 > 50ms | `PerformanceObserver('longtask')` |
| 单帧同时动画元素 | ≤ 64 | `document.getAnimations().length` 采样 |
| `background-position` 动画 | 只允许出现在 ≤24px 的字节格内；**矩阵/时间轴/背景层一律禁止** | 代码审查 + Performance 面板 Paint 计数 |
| 骨架尺寸 | `--transport-h` **三档 104/92/136**（92 用于 `max-height: 780px`）、`--diag-row-h: 40px`（演示 56px，**槽位高度锁死**）、`--ai-col: 360–400px ↔ 48px` | tokens.css |

### 5.2 检测方法（可直接照做）

**① 首屏**
```bash
npm run build && npx vite preview --port 4173
# Chrome DevTools → Lighthouse（Desktop）→ 看 FCP/LCP/TBT
npx vite-bundle-visualizer   # 看 engine/ 是否被错误打进入口 chunk
```
目标：`vendor-vue` ≤ 55KB gz、`engine` 独立 chunk 且**仅工作台路由按需加载**（首屏不该加载 AES 引擎）。

**② 单步切换耗时（代码埋点）**
```ts
// usePerfProbe.ts
const ring: number[] = []
export function markStepStart() { performance.mark('step:s') }
export function markStepEnd() {
  performance.mark('step:e')
  const m = performance.measure('step', 'step:s', 'step:e')
  ring.push(m.duration); if (ring.length > 200) ring.shift()
}
export const stats = () => ({
  p50: pct(ring, .5), p95: pct(ring, .95), max: Math.max(...ring)
})
```
`markStepEnd` 放在 `useMatrixWriter.flush()` 的**最后一行**（不是 `write()` 里），否则测的是"派发"不是"落地"。
验收：连按 30 次 `→`，`window.__perf.stats().p95 < 100`。

**③ 帧率**
```ts
// useRafLoop 的采样旁路（只在 ?perf=1 开启）
let prev = 0, long: number[] = []
const tick = (ts: number) => {
  if (prev && ts - prev > 20) long.push(ts - prev)
  prev = ts; raf = requestAnimationFrame(tick)
}
```
播放 24 步结束后 `window.__perf.frames()` 必须 `long.length === 0`。
**Performance 面板看什么**：录制 → 勾 "Screenshots" 与 "Web Vitals" → 按下 `→` 单步 → Frames 轨道**不得出现红色斜纹帧**；Main 轨道一次单步应只有 `keydown → rAF → Function Call → Layout(×1) → Paint`，若出现 16 次 `Function Call` 说明 J1 方案被破坏。

**④ 16 格同帧写入（防回归，dev 强制断言）**
```ts
if (import.meta.env.DEV && batches > 1)
  console.error('[MULTI-BATCH] 一帧内写了 %d 次，检查是否有组件自行绑定 hex 值', batches)
```
再配一条 ESLint 自定义规则：`components/region-c/**` 内禁止出现 `trace[`、`values[`、`:value=` 与模板插值中的 `hex`。

**⑤ Layout thrashing**
- Performance 面板 `Layout` 条目时长应 < 1ms 且每步 ≤ 1 次；若 > 3ms 说明有同步强制布局。
- 代码层：`Grep` 检查 `useMatrixWriter` / `useStageMetrics` 的写循环内是否出现 `offsetTop|offsetWidth|getBoundingClientRect|getComputedStyle|scrollTop` —— **写后读**是 thrashing 唯一成因。
- 用 `PerformanceObserver` 的 `longtask` 兜底：播放中任何 >50ms 任务都要定位。

**⑥ Canvas 与合成**
- DevTools → Rendering → 勾 "Paint flashing"：静帧时不应有绿框闪烁（证明 canvas 该隐藏时已隐藏）。
- Layers 面板：确认 canvas 与矩阵是同一层或 ≤4 层，抽屉在独立层。
- dpr 验证：DevTools 设备模拟切到 DPR=2 再切回 1，canvas 不得模糊（模糊 = 忘了重算 backing store）。

**⑦ 灰度回归（视觉侧指定，比任何视觉描述更能挡住回归）**

对工作台截图加 `filter: grayscale(1)`，**3 秒内必须能指出三件事**：哪几个字节变了 / 哪个选错了 / 哪些是密钥字节。做不到就调**明度**，不调色相。
落地为脚本（W4 验收必跑）：

```js
// e2e/grayscale.spec.ts
await page.locator('.c-matrix').screenshot({ path: 'matrix-color.png' })
await page.addStyleTag({ content: '.c-matrix{filter:grayscale(1)}' })
await page.locator('.c-matrix').screenshot({ path: 'matrix-gray.png' })
// 断言：is-changed 格的平均亮度与普通格差值 ≥14（明度通道确实承载了信息）
```
理由：这一条同时覆盖色盲、投影仪 gamma 失真、以及"高亮只靠色相"三类失败，且是机器可判的。

**⑧ 演示态硬检查（视觉指定，上线前跑）**

演示态截图必须满足：**所有结构分隔线 ≥2px；全站零 `alpha` 叠加；零 `pattern`**（斜纹 / 点阵在演示态必须是 `background-image: none`）。
落地为断言：

```js
await page.emulateMedia({ colorScheme: 'light' })
await page.locator('html').evaluate(el => el.dataset.mode = 'present')
const alpha = await page.evaluate(() => {
  const bad = []
  for (const el of document.querySelectorAll('*')) {
    const cs = getComputedStyle(el)
    if (/rgba\(/.test(cs.backgroundColor) || /rgba\(/.test(cs.borderTopColor)) {
      const m = cs.backgroundColor.match(/[\d.]+\)$/)
      if (m && parseFloat(m[0]) < 1) bad.push(el.className)
    }
    if (cs.backgroundImage.includes('gradient') && el.classList.contains('c-byte')) bad.push(el.className)
  }
  return bad
})
// 断言 alpha.length === 0
```
理由：投影仪 gamma 会把半透明图层糊成一片、把 1px 线吃掉、把斜纹看成脏点 —— 这三类失败在显示器上永远看不到，只有到教室才发现。

---

## 6. 分阶段实现顺序（4 周 / 10 有效日）

| 阶段 | 天 | 目标 | 产出物 | 可演示成果 | 接口依赖 | 本阶段风险 |
|---|---|---|---|---|---|---|
| **W1** 引擎与骨架 | D1–D2 | 可跑的壳 + 正确的 AES + 三层坐标系 | 路由、五区布局、`tokens.css`、`engine/*` + 单测、`MatrixStage` 静态 16 格、`useMatrixWriter`、`useStageMetrics`、`useRovingGrid`、5 个快捷键 | 载入 FIPS-197 向量，按 10 次 `→`，16 格数值瞬变且与标准逐字节一致 | `POST /api/aes/trace`（可先用本地 `engine/trace.ts` 顶着） | 三层坐标系对齐跑偏，后期全盘返工；AES 逆序（解密）实现错误 |
| **W2** 矩阵与动效 | D3–D5 | **七态** + 四操作四通道 + 时间轴 | `ByteCell` 七态、`useMatrixWriter` 的 class 编排、`StageCanvas` 两个 pass、`svg/*`、`Timeline` 四轨双形状标记、`TransportBar`、`tokens` 的 reduced-motion 双通道 | 完整播放 24 步：四步各走各的通道且一秒可辨；拖拽不触发动效；`prefers-reduced-motion` 下信息不丢 | 无新增 | 16 格动效编排失控（多写批次）；行移位回绕的 8 格鬼节点漏写；`steps(4)` 在 reduced-motion 下闪烁 |
| **W3** AI 与练习 | D6–D8 | 讲得清 + 知道你哪不懂 | `useSSE`、`TutorPanel` 全态、降级模板、`useDiagnosisStore` 规则与红线批注、`PracticeView` + `useQuizStore` **渲染后端三层反馈**、`RecordsView`、`?debug=diagnosis` | 选中第 13 步提问，流式回答引用该步真实数值；`?debug=diagnosis` 一键拉出红线批注；答错后**只 1 格红、其余灰化**并定位到"第 4 轮 列混合 字节 7" | `POST /api/tutor/ask`（SSE）、**`POST /api/quiz/submit`（返回 `summary`/`first_diff`/`propagated`/`input_mismatch`）**、`POST /api/events` | SSE 在组件卸载时泄漏；诊断规则在 `activeChannel='tutor'` 时误触发；`is-downstream` 被 `is-error` 选择器连坐 |
| **W4** 打磨与部署 | D9–D10 | 60fps + 无障碍 + 可交付 | 性能修到预算内、roving tabindex + 表格视图 + live region、**22 键全量**、URL 状态、演示模式、Docker + nginx、错误边界、E2E 冒烟 | 三项性能预算全绿；纯键盘完成"载入→播放→提问→关批注→`[` 跳上一个标记"；`docker compose up` 一条命令起全栈 | 全量联调 | 最后两天才发现性能不达标（W2 就必须埋 `usePerfProbe`，不能拖到 W4） |

**里程碑卡点（不达标不许进下一阶段）**：
- W1 末：`step p95 < 120ms`（宽松版），Layout/步 ≤ 1，**每步写批次恰好 1（dev 断言零触发）**。
- W2 末：`step p95 < 100ms`，长帧 0，reduced-motion 全表通过。
- W3 末：SSE 中断后 0 个未清理的 `AbortController`（`window.__sse.active === 0`）；判分结果与后端三层反馈逐字段一致（前端无任何复算）。
- W4 末：三项预算全绿 + Lighthouse 无障碍 ≥ 95 + 灰度回归通过。

---

## 7. 分阶段 Coding Agent 提示词（可直接粘贴）

### 7.1 W1 · 引擎与骨架

```text
【角色】你是 CipherLens 的前端实现 Agent。技术栈已锁定：Vue 3.5 + Vite 5 + TypeScript + Pinia 2 + Vue Router 4。
禁止引入 React/Next/Nuxt/Element Plus/Ant Design/Naive/Tailwind/GSAP/任何 UI 或动画库。CSS 手写，动画只用 CSS transition/keyframes 与 rAF。

【本阶段目标 W1】交付「能跑起来、AES 算得对、三层坐标系对齐」的最小骨架。
做：路由壳（Home/Workbench/SBox/Practice/Records 五条路由，后三条给空占位）；五区静态布局（A 上下文条 / B 输入区 / C 舞台 / D 时间轴 / E AI 栏占位，宽度按 280 / flex / 380）；src/styles/tokens.css 落地全部视觉 token；engine/ 下的 aes.ts、sbox.ts、trace.ts、diff.ts（零 Vue 依赖，可在 node 里跑）；MatrixStage 静态渲染 16 个 ByteCell；useMatrixWriter、useStageMetrics、useRovingGrid；useHotkeys 先接通 Space / ArrowLeft / ArrowRight / Home / End。
不做：任何动效（七态只有静态样式）、Canvas 绘制、SVG 装饰、AI 真实请求、诊断、练习判分、抽屉。

【硬约束】
1. 所有颜色/间距/时长/缓动只能来自 tokens.css 的 CSS 变量。组件内出现 #rrggbb 或写死 ms 数值一律视为不合格。
2. trace 用 shallowRef 存，禁止 ref()/reactive() 包裹 steps 与 keySchedule。
3. 16 个格子的 hex 值禁止在模板里绑定表达式，也禁止每格建 computed。数值只能由 useMatrixWriter 在单个 rAF 内写入 textContent 与 aria-label。
4. **useMatrixWriter 必须内置写批次断言（W1 验收硬项，不可选做）**：每次 flush 前 `batches = 0`，flush 结束 `batches++`；`if (import.meta.env.DEV && batches > 1) console.error('[MULTI-BATCH] 一帧内写了 %d 次', batches)`。这条断言要一直留到 W4，用于防"后来的人顺手把 16 格改回响应式绑定"。
5. 矩阵只占 1 个 Tab 位：role="grid" + roving tabindex，非活动格 tabindex="-1"。
6. 圆角 ≤ 3px；零渐变；零毛玻璃；分区只用 1px 发丝线；阴影只允许浮层用 2 个。
7. **网格 1px 基线用 DOM（`inset box-shadow: 0 0 0 1px`），不要用 Canvas 画**，也**不要留 Canvas 兜底开关**。这是 team-lead 对视觉规范的裁决，理由与作者注写在文档 §3.2。
8. **类名照抄视觉 v1.1 §9**：`c-byte` / `c-byte__stage` / `c-byte__val`（`is-current` / `is-incoming`）/ `c-byte__corner`（2 个通用角位，视觉里的 `__flag`/`__fold`/`__notch` 是同一批角位的旧命名，见 §3.1）/ `c-byte__sup` / `c-byte__hint`；矩阵 `c-matrix` / `c-matrix__body` / `__grid` / `__fx`（canvas）/ `__brackets`（svg）。**16 格 DOM 顺序必须列优先**（col0r0,col0r1,col0r2,col0r3,col1r0…）+ `grid-auto-flow: column`，这样 DOM 下标 === AES 字节下标，`useMatrixWriter` 不需要映射表。每格额外两个单值属性 `data-bd` / `data-txr`（§3.1 owner 表）。
9. `aria-label` 必须 **hex + 十进制双写**（如「第 2 行第 2 列，字节 5，值 0x63，十进制 99，本步已变化，原值 0x53」），由 `useMatrixWriter` 在写值的同一帧 `setAttribute` 更新，模板里不绑表达式。

【输入】①《视觉设计规范》tokens 与七态定义；②《信息架构与交互规格 v1.0》2.1–2.6 节；③ FIPS-197 标准（S 盒、Rcon、密钥扩展、列混合的 xtime）；④ 本文档 §0 的 J1–J6。

【验收（逐条自查，并在报告里给证据）】
1. npm run build 通过，无 TS error，初始路由 JS gzip < 150KB。
2. 载入 FIPS-197 附录 C.1 的 AES-128 向量，按 10 次 → 后，矩阵 16 格与标准的「第 1 轮列混合后状态」逐字节相等；贴出 4×4 对照表。
3. **连按 30 次 →，控制台零 `[MULTI-BATCH]` 输出**，并贴出 batches 计数（每步必须恰好 1）。
3. engine 单测覆盖 subBytes / invSubBytes / shiftRows / invShiftRows / mixColumns / invMixColumns / addRoundKey / keyExpansion(128,192,256)，全部通过，覆盖 128 位明文跨 4 列的场景。
4. Performance 录制一次「按 →」：Layout ≤1 次、Recalculate Style ≤1 次、无 >20ms 帧。
5. 矩阵按一次 Tab 进入，方向键 4×4 内移动且到边界不跨行，再按 Tab 离开只一次。
6. 在 DPR=2 与 DPR=1 下截图，矩阵 1px 边框无模糊、无 2px 粗边。

【禁止】
- 禁止 v-for 的 :key 用随机值或 index 拼时间戳；16 格固定 :key 0..15。
- 禁止在 engine/ 内 import 'vue'（engine 必须能在 node 单测里裸跑）。
- 禁止用 structuredClone / JSON.parse(JSON.stringify()) 复制 trace 做 diff。
- 禁止为「以后可能用到」预建空组件、空 store、空 composable。
- 禁止把 hex 拆成单字符 span（W2 才做，且必须两个 span 叠放，不是每字符一个）。
- 禁止 window.addEventListener('resize') 监听矩阵尺寸，必须用 ResizeObserver 监听容器。

【产出文件】src/styles/{tokens,base}.css；src/engine/{aes,sbox,trace,diff}.ts 及 *.spec.ts；src/types/{trace,api}.ts；src/stores/{engine,playback,ui}.ts；src/composables/{useMatrixWriter,useStageMetrics,useRovingGrid,useHotkeys}.ts；src/components/region-c/{MatrixStage,ByteCell}.vue；src/views/{Home,Workbench}View.vue；src/router/index.ts。最后给一份「W1 验收证据」清单，逐条对应上面 6 项。
```

### 7.2 W2 · 矩阵与动效

```text
【角色】承接 W1 的 CipherLens 前端 Agent。W1 已交付：tokens.css、engine/、MatrixStage 静态 16 格、useMatrixWriter（单 rAF 写入 textContent + aria-label）、useStageMetrics、useRovingGrid。

【本阶段目标 W2】让「一步到底改了什么」这件事在视觉上一秒可辨。
做：ByteCell **七态**（变化/选中/错误/**下游污染/错误**/密钥参与/已完成/正确 —— 共 7 个独立 class，`is-downstream` 的样式在 W2 就要写完，W3 只负责接数据，不许在 W3 回头改 W2 组件）；M1–M4 单字节变更动效链；四个操作各走独立通道（字节替代=逐格 scaleY + 列优先 20ms + SVG S盒十字准星；行移位=DOM 行轨道 translateX 280ms + 行序 40ms + 8 格鬼节点回绕 + Canvas 1px 描边闪 60ms；列混合=同列零 stagger + Canvas 计算线 280ms linear + 列序 60ms 总 460ms + accent-soft 12%→0 淡出 600ms；轮密钥加=密钥层 0→0.6 120ms → 底色石墨 160ms → values steps(4) 80ms → 密钥层淡出 120ms）；Timeline 四轨（游标/标记/刻度/轮号）+ 标记双形状（诊断 = 5px 圆点上沿、提问 = 5px 方块下沿，**都不是横条**）+ 拖拽；TransportBar；reduced-motion 双通道（媒体查询 + `[data-motion="reduced"]`）。
不做：AI 栏真实请求、诊断批注、练习、密钥扩展抽屉内容。

【硬约束】
1. 动画只能改 transform / opacity / background-color / outline。禁止改 width/height/top/left/margin。禁止动画 box-shadow 模糊半径，禁止 filter: blur / backdrop-filter。
2. will-change 只在 .is-playing / .is-dragging 期间存在，选择器内声明，禁止写进基础类。
3. 16 格的 class 编排必须在 useMatrixWriter.flush() 的同一次循环内完成，且该函数一次 step 只允许被调用 1 次。
4. 行移位的位移只能由 DOM 行轨道 translateX 完成。Canvas 只画回绕描边闪与列混合计算线。任何情况下不得把 hex 画进 Canvas。
5. 缓动只允许 --e-out-quart 与 in-out-cubic / linear，禁止任何过冲（back/elastic/bounce）。
6. 列混合同列 4 格必须零 stagger（刻意的同步感），列间 60ms。
7. reduced-motion 归零是三段：`--d-*` 置 `0.01ms` + 该动画 `animation: none` + `el.getAnimations().forEach(a => a.cancel())`。光设时长 0ms 会让 stroke-dashoffset 停在半截。且所有描边/位移动画的**静止态必须是终态**（从 0 正向播到终态），这样 cancel() 才安全。
8. 反向单步用独立的 shift-right keyframes，禁止用 animation-direction: reverse（会把 stagger 顺序一起反）。
9. **播放节奏与动画时长必须解耦**：新增 `--step-interval: 800ms`（0.5×/1×/2×/4× = 1600/800/400/200ms），**单步动效固定 280ms 不随倍速变**。禁止把 transition-duration 乘以倍速——低帧率投影上会累积抖动，且"慢动作"反而看不清哪一步在动。
10. **`--cell-size` 用离散桶 + 容器查询**（44/52/62/72/88），禁止连续 `clamp()`；换档不做宽度过渡，用 M26 的两段 opacity 遮罩遮住那一帧。演示模式下窗口 <1120px 回落 72px 档。
11. **格线 = 每格自己的 `border: 1px solid var(--rule-region-ink)`**（`--cell-gap` 保持 6px；**不许取 `--line-default`** —— 它在演示块是 0.760、比格子基线 0.545 还浅，见 §3.1）。**`border-width` 七态恒定 1px（演示态恒 2px），七态只改 `border-color`**；2px / 3px 的加粗观感一律用 `box-shadow: inset 0 0 0 Npx <color>` 叠在格内。**禁止把格线改成由容器画**（`gap:1px` + 容器底色 / 6 个绝对定位线节点 / `repeating-linear-gradient`）—— 6px 间隙下没有共享边、没有双线，这个方案治的病不存在。`is-downstream` 必须是独立选择器（禁 `[class*="error"]` / `[data-state^="err"]` / 与 `is-error` 同组复合），走 `data-bd="downstream"`：常规 = 边框降一级色 `--line-hairline` + 底色 `--surface-inset` + `--ink-3` 400；演示 = 边框**不降**（`--st-downstream-border` 的演示值 = `var(--rule-region-ink)`，与邻居同值）+ 底色 `oklch(0.905 0.004 258)` + 文字 `oklch(0.415 0.012 258)` 8.4:1。**不许用虚线**（专表未生效/待定/禁用，已用 11 处）。`is-done` 也不用虚线，改 1px 实线 + 左下缺口（**压一块 `calc(var(--flag-size)*2)` 见方的 `--paper-0` 方块，不许写死 5px**，不断 `border`）、**无点阵**。
12. **字重不做过渡**（M5 已删）：字重是瞬时切换（0ms），与数值滚动同时发生，不要给它写 transition。
13. **七态叠加按「视觉属性通道」分配 owner，不靠 class 顺序**：**六个**通道（fill / bd / txr / corner / text / bar）各自独立求值（§3.1 有表）；`bd` 与 `txr` 的值写进 **`data-bd` / `data-txr` 单值属性**（属性单值 → 平台保证一个 owner），其余走单值 `is-*`；`bar` 只有 `key` 一个候选、无竞争。`classList` 真实顺序不可控，靠顺序赢就是靠运气。**禁止 `!important`**。角位按 `br`(error) > `tl`(reverse) > `tr`(changed) > `bl`(done) 截断取前 2，不得进格心。`error + selected` 必须走组合规则（红底红边归 error，**近黑外环**归 selected，环色 `--ink-1`），不允许一方静默吃掉另一方。
14. **时间轴标记是 5px 圆点（诊断）与 5px 无圆角方块（提问）**，不是横条 —— 横条宽度数据驱动（24 步≈28px / 58 步≈10px / 容器变宽还会变），图例永远做不到"与轨道完全一致"，且 58 步时 10×2px 会与刻度轨竖刻度混成"又一种刻度"。**图例复用同一个元素 `.c-mark__shape`（只换宿主、不改尺寸/形状/颜色）**，不许另画图标、不许用 `▪`/`●` 字符。
15. **类名与 DOM 结构照抄视觉 v1.1 §9**：`c-` / `__` / `is-`，状态只挂组件根元素；16 格 **DOM 顺序按列优先** + `grid-auto-flow: column`；时间轴只改 `--i` / `--span`，批注只改 `--tick-y`，S 盒行列高亮用 2 个绝对定位 div。详见本文档 §3.1 / §3.5。
16. **88px 档只在 `[data-mode="present"]` 且 stage 容器 ≥720px 时可达**（`@container`，不是视口宽），普通模式上界锁 72px；选择器写成 `[data-mode="present"] .c-matrix`，**不要写成 `.c-matrix[data-mode="present"]`**（属性不在矩阵上，永远不命中）。

【输入】W1 的产出；《视觉设计规范》**七态**与四操作四通道；本文档第 4 节动效参数表（M1–M29 全表照做，**M5 已删除不要实现**）；视觉侧 10 条实现要点 + 体验侧 6 项增补（本文档第 10 节）。

【验收（逐条自查并给证据）】
1. 播放 AES-128 全 24 步，四个操作各自的通道一眼可辨；贴 4 张步中截图（SubBytes / ShiftRows / MixColumns / AddRoundKey）。
2. 连按 30 次 →，window.__perf.stats() 的 p95 < 100ms，长帧 0。
3. 拖拽时间轴全程：idle 状态无任何 is-changed 动画（用 Performance 面板确认拖拽期间无 Animation 轨道条目），松手后该步只重播一次；且拖拽期间**无 AI 请求发出、无诊断历史写入**（Network 面板 + store 快照证明）。
4. OS 开启「减少动效」+ 页内开关分别单测：位移时长 0、信息不丢（摘要句仍完整、变化字节仍有常驻琥珀角标、行移位有 `←1` 文本旋转量、列混合有 `MIX` 标签、轮密钥加有 `⊕` 上标）。
5. `document.getAnimations().length` 在任意单帧 ≤ 64；DevTools Layers 合成层 ≤ 4；静帧 Paint flashing 无闪烁。
6. 行移位在 4 个方向（左/右 × 正/反）都正确回绕，鬼节点文本与终态一致。
7. 按 F 收 AI 栏：全程无 `width`/`grid-template-columns` 过渡（Performance 面板该 240ms 内 Layout ≤1 次），矩阵在 opacity 遮罩下完成换档。
8. **七态隔离测试**：手动构造 `is-error` 与 `is-downstream` 相邻格，用 DevTools 检查 `is-downstream` 格**没有**折角三角、**没有** `≠`、`data-bd === 'downstream'`（computed `border-color` 是 `--line-hairline`，不是 `--st-error`）；再用 `document.querySelectorAll('.is-error')` 确认它**没有**把 downstream 格算进去。再补一条组合态检查：给同一格加 `is-error` + `is-selected`，确认**红底红边与近黑外环同时可见，且外环与右下折角不重叠**（外环离格边 2px，折角在格内）。
9. 时间轴标记双形状：诊断 = **5px 圆点**贴上沿（y30–35）、提问 = **5px 无圆角方块**贴下沿（y41–46）；同一 x 上两者并存可见；标记不被游标遮挡；**图例复用同一个 `.c-mark__shape` 元素（不是另画图标）**，图例里标记与轨道上像素级一致（贴两张截图叠图对比）。
10. **格线颜色双断言**（DevTools Console 一条跑完）：① 任一 `.c-byte` 的 `getComputedStyle(el).borderTopColor !== getComputedStyle(el).color`（挡住"引用了不存在的 token → 静默回落 `currentColor`"）；② 切到演示态后，`.c-byte` 的 computed `border-top-color` 与 `downstream` 格**完全相等**，且对纸底对比度 ≥4.5:1（用 DevTools 取色器核，期望 `oklch(0.545 …)`）。两条任一失败即打回 —— **它们都是静默失效，不看断言看不出来**。

【禁止】
- 禁止用 v-for + :key="currentStep" 重建 16 格。
- 禁止在 @click 里直接改 DOM 再改 store（必须 store 驱动）。
- 禁止用 setTimeout 串联多段动效，必须用 animation-delay 或 transitionend（且 reduced-motion 下 transitionend 可能不触发，须有兜底定时器）。
- 禁止为 16 格各写一个 <transition-group>。
- 禁止把 SVG 的 stroke-dashoffset 动效做在矩阵以外的 SVG 上又让它在 reduced-motion 下不归零。
- 禁止自己发明类名：必须照抄视觉 v1.1 §9 的 `c-` / `__` / `is-` 约定，状态只挂组件根元素。
- 禁止按行优先渲染 16 格（必须列优先 DOM 顺序 + `grid-auto-flow: column`，否则方向键顺序、Canvas 索引、学生空间记忆三处同时错）。
- 禁止用 JS 改 `style.top` 挪时间轴游标或批注刻痕（必须写 CSS 变量 `--i` / `--tick-y`）。
- 禁止给 S 盒 256 个 `<td>` 批量加高亮类（用 2 个绝对定位 div 做行列线）。
- **禁止在七态之间改 `border-width`**：`.c-byte` 的 `border` 恒为 1px（演示态恒 2px），七态**只改 `border-color`**；需要 2px / 3px 观感一律用 `box-shadow: inset` 叠在格内。改宽度会改内容盒，让 hex 横向位移 1–3px —— 撞「格子绝不位移」这条视觉红线。
- **禁止把 `.c-byte` 的基线色写成 `--line-default`**：格子边框属区域结构线族，基线只能是 `--rule-region-ink`（常规 0.845 / 演示 **0.545，4.6:1**）。`--line-default` 的演示值 0.760 只服务**非格子**结构线（控件边 / 表头框 / 分区细线）；一旦格线取它，16 格在投影上对纸底只有 2.9:1，整张矩阵发灰、被读成"没画完"。**演示态不需要任何 `border-color` / `--bd-color` 覆盖**（`--rule-region-ink` 在演示块自己就是 0.545），写了反而多一层会忘掉的分支。
- **禁止在演示态只给 `downstream` 单独改边框色**：`--st-downstream-border` 的演示覆盖必须是 `var(--rule-region-ink)`（与邻居同值）。若指向 `--line-default`，普通格 0.545、`downstream` 0.760 —— **它比邻居更浅**，在 6px 间隙里只有一个读法：这格没画完。
- **禁止把格线改成由容器画**（`gap:1px` + 容器底色 / 6 个绝对定位线节点）：矩阵是 `--cell-gap: 6px` 的 16 个独立 chip，无共享边、无双线，这个方案治的病不存在，且会把 6px 留白塌成 1px（矩阵总宽 306px → 291px，摘要句与密钥轨全要重排）。
- **禁止用 `inset box-shadow` 画结构线**（它与 `border` 二选一，且 `data-bd` 消费的是 `border-color`）：两个都留 = 每格 2px；更坏的是线改成 shadow 之后 `data-bd` **静默失效**，状态色不生效且不报错。
- **禁止用"尺寸内缩"表达任何状态**（`downstream` 尤其）：位移是位置跳、内缩是尺寸跳，都是几何变化；一格小一圈只会被读成"这格有毛病"。要"退后"只能变淡（色阶 + 墨量）。
- **禁止给选中格画四角刻线**：它与 `error` 的右下 6px 折角同位置同尺寸，`error + selected` 会叠成一条画歪的线；四角是角标通道，已有 4 个 owner、每格最多 2 个。选中格的形状通道是**外 3px 环**（叠加态环色转 `--ink-1`）。
- 禁止给 `is-downstream` 加角标、纹理、`≠`，也禁止复用 `error` 的任何通道（红 / 折角 / 底条 / `--st-error-fill`）。它的全部动作是**三档同时减**：边框降一级色（演示态不降）、底色内缩一档、墨量降到 400。
- **禁止给 `is-downstream` 或 `is-done` 加虚线框**：虚线在本规格专表「未生效/待定/禁用」（已用 11 处），借用即语义污染。downstream = 实线 + 降一级色 + `--surface-inset` + `--ink-3` 400（演示与邻居同值 + 底色 ΔL 0.06 + 400）；done = 1px 实线 + 左下 5px 缺口，**无点阵**。
- **禁止用"断开 `border` 一段"来做 `done` 的缺口**：缺口由 `data-corner="bl"` 的元素**压一块 `--paper-0` 方块**实现（边长 `calc(var(--flag-size)*2)`，**不许写死 5px**）。断边会随 `border-color` 变化而失效（`downstream` 降级、判分上下文换环色都会碰边框），缺口在某个状态下会莫名消失或变成一条黑缝 —— **用形状去改另一个通道，是本项目最典型的一类错法**。
- **禁止把 `is-downstream` 改成无边框**：6px 间隙下每格的外框是它自己的完整矩形，抽掉一根会被读成「这格没画完」，不会被读成「安静」。
- **禁止用 `!important` 处理七态叠加**，也禁止让叠加结果依赖 class 书写顺序。必须按 **fill / bd / txr / corner / text / bar 六个通道**各自求值（§3.1 有表）；`bd` 与 `txr` 的值写进 **`data-bd` / `data-txr` 单值属性**，其余走单值 `is-*`。
- **禁止漏掉 `error + selected` 组合态**：判错后选中那个字节，必须同时看到红（底色 / 边框，归 `error`）与**近黑外环**（归 `selected`）。一方吃掉另一方 = 学生以为自己没点上。
- **禁止让角位截断顺序偏离 `br > tl > tr > bl`**（错误 > 反向 > 变化 > 完成）。
- **禁止把时间轴标记画成横条**（宽度数据驱动，图例无法与轨道像素一致）；**禁止图例另画图标或用 `▪`/`●` 字符**，必须复用轨道标记同一个 `.c-mark__shape` 元素。

【风险与预设扣减（提前写死，出事当天不讨论）】
本阶段是排期瓶颈（PRD 的 RK-2：W2 动画工作量超预期，概率 4 × 影响 5）。**W2 第 5 个工作日结束时，若四个操作的可视化未全部跑通**，立即按以下顺序砍，不申请、不改期、不临时评估：

1. **砍 ECB/CBC 对比（F8）** —— 整块移除，含入口与路由；
2. **砍 PNG 导出** —— 只保留 CSV / JSON 导出（这两种是纯文本，无 canvas 光栅化依赖）；
3. **砍 S 盒投屏放大镜窗口** —— 只保留常规 16×16 表与行列高亮线（放大镜是 `c-sbox` 的衍生态，删它不动主结构）。

砍完后四步可视化必须仍然全通。**若砍完仍不通，说明问题在 J1（16 格被改回响应式绑定），回去修 `useMatrixWriter`，不要再砍功能。**

【产出文件】src/styles/{motion,reduced-motion}.css；src/components/region-c/{ByteCell,MatrixStage,StageHeader,SummarySentence,KeyTrack}.vue；src/components/region-d/{TransportBar,Timeline,TimelineSegment}.vue；src/canvas/{StageCanvas.vue,drawRowShift.ts,drawMixScan.ts,palette.ts}；src/svg/{BracketLayer,CornersLayer,CrosshairLayer}.vue；src/composables/{usePerfProbe,useReducedMotion}.ts；src/stores/playback.ts 全量。附「W2 验收证据」。
```

### 7.3 W3 · AI 与练习

```text
【角色】承接 W1/W2 的 CipherLens 前端 Agent。矩阵三层、动效、时间轴已完成。activeChannel 单活动焦点纪律已在 useUiStore 中定义。

【本阶段目标 W3】把「讲得清」和「知道你哪不懂」两层真正跑通。
做：useSSE（fetch + ReadableStream + AbortController，60 行内，禁止 EventSource，对接 `POST /api/tutor/ask`）；TutorPanel 全部 11 个状态（空闲/等待首字/首字慢/流式/完成/缓存命中/通用讲解/超时降级/错误/中断/切步折叠）；双阈值（首字 3s → "先看本地要点"；总 20s → 中断并换本地模板）；切步只更新 CTX 头与 chip，正文必须点击才生成（预取不预显）；DiagnosisCard + 红线批注（SVG 折线 420ms，同一时刻最多 1 条，间隔 ≥45s，仅空闲 20s 后可出现，activeChannel 必须是 idle）；?debug=diagnosis 暴露 window.__diag.forceFire(type)；PracticeView + useQuizStore **调用后端判分并渲染三层反馈**（summary / first_diff / propagated）；RecordsView 三态（空/有数据/数据不足 <3 道不出结论）。
不做：**任何算法判分逻辑**（判分全在后端）、教师端看板、登录合并记录、演示模式参数集、修改 W2 的 ByteCell 组件（七态样式 W2 已写完）。

【硬约束】
1. SSE 必须在 onScopeDispose / onUnmounted 中 abort()，并置 window.__sse.active。组件卸载后 __sse.active 必须为 0。
2. 流式正文禁止进 aria-live；live region 只在生成结束后一次性播报，或提供「朗读回答」按钮。
3. 流式期间 activeChannel = 'tutor'，此时时间轴与矩阵不得播放任何动效、不得弹诊断。
4. 缓存命中必须整段直出，禁止模拟打字机。
5. 诊断提示不得移动焦点、不得居中、不得 toast、不得覆盖矩阵与时间轴。只能出现在 E 区顶部行内。
6. 诊断判定用「空闲 20s + 无有效操作」，禁止用「停留 8 秒」；反复回退仅在回退后 3s 内无有效操作才计入。
7. 所有 AI 数值 token 可点击且带「引用本步数值」文本标签（不能只靠底纹色）。
8. **判分完全在后端，前端零复算**。调用 `POST /api/quiz/submit`，只做三件事：① 用 `first_diff` 定 `is-error`（通常仅 1 格）；② 用 `propagated[]` 定 `is-downstream`（Set，按字节下标判定）；③ 用 `input_mismatch` 决定是否计入统计（**非 null 则不计入**，并渲染「哪个字段、第几个字符」的字段级提示 —— 学生录错明文/密钥不是算法错）。**禁止**用前端 engine 重新算一遍再跟后端对账——双实现会让"列优先写反"变成必然事件，且 `propagated` 前端根本算不出来（它要全量中间态）。`engine/` 只允许用于离线演示内置向量，不许进判分路径。
9. 判分展示期间，通道优先级：`is-error` / `is-downstream` **覆盖** `is-changed`（此时用户关注对错不是变化），但 **`key` 不让位**（它是输入条件，不是 diff 信息 —— 学生必须看到哪 8 个密钥字节参与异或）。**判分叠加必须绑定 `step_index`**：`errorSet` / `downstreamSet` 与锚点步同生命周期，学生单步或跳步即整体撤场，否则会把某一步的错画到另一步上。这段逻辑写在 `useMatrixWriter` 的 `paintFor()` 里，不要在 W3 新建第二套写入通道。

【输入】W1/W2 产出；《信息架构与交互规格》3.2 / 3.3 / 4.3 / 4.5 / 6.a / 6.b / 6.i / 6.j / 7.4 / 7.6；**接口契约一律以本文档 §11 为准**（`POST /api/tutor/ask` SSE 事件 `meta`/`token`/`done`/`error`；`POST /api/quiz/submit` 返回 `summary`/`first_diff`/`propagated`/`input_mismatch`/`expected_ciphertext`；`POST /api/events` 批量）。请求 `ask` 时**只传 `trace_id + step_index + question`，不要把 16 字节数值再传一遍**（会造成两处数值不一致的新风险）。

【验收（逐条自查并给证据）】
1. 选中第 13 步提问「这一步为什么这么做」，回答里出现该步真实字节值（贴截图 + 后端返回的原始 SSE 帧）。
2. 断网重试：首字 3s 未到出现「先看本地要点」，20s 出现本地模板与「离线讲解」标识，用户问题不被清空。
3. 提问中途切步：旧回答折叠为一行可展开，CTX 头更新，且未自动发起新请求（Network 面板确认无新请求）。
4. 提问中途按 Esc 或点停止：内容保留 + 「已停止」+ 「继续生成」；__sse.active === 0。
5. ?debug=diagnosis 一键拉出红线批注，420ms 折线到具体字节，且不遮矩阵；连续触发第二条被 45s 冷却拦掉。
6. 流式期间矩阵不动（Performance 面板无 Animation 条目）。
7. 练习题答错：页面显示**只 1 格红（is-error）+ 其余受污染格灰化（is-downstream）**，矩阵**不画外框**、只画实线四角括 + 文本「影响范围：16 字节」，并定位到「第 4 轮 列混合 字节 7」、可一键跳工作台该步。
   - 附 DevTools 证据：`document.querySelectorAll('.is-error').length === 1`，`document.querySelectorAll('.is-downstream').length === propagated.length`。
8. `input_mismatch` 非 null 时，该题**不进入** `stats.done / stats.correct` 的分母；文案必须说出**哪个字段、第几个字符**（例：「你的密钥第 7 个字符不是十六进制数。这不算算错，改一下输入重判就行」）。贴记录页前后对比。
9. 后端返回非法/缺失 `propagated` 时前端不崩：按空数组降级（只标 error，不标 downstream），并在 console.warn 标记契约漂移。
10. 读屏（NVDA 或 VoiceOver）逐条走：流式期间不逐字播报，结束后整段可读。

【禁止】
- 禁止用 EventSource。
- 禁止把 AbortController 放进 Pinia state（会被 devtools 序列化）。
- 禁止在 watch(phase) 里发请求（会造成重入）。
- 禁止用 v-html 渲染 AI 回答；数值高亮用 markdown token 解析 + 组件渲染。
- 禁止诊断提示出现在 E 区以外任何位置。
- 禁止把「停止生成」按钮放在回答内容之后（Tab 顺序必须在之前）。
- **禁止在前端复算判分**（含"算一遍再跟后端比对"这种"更保险"的写法）；禁止从 `engine/` import 任何东西进 `PracticeView` / `useQuizStore`。
- 禁止用 `is-error` 表示 downstream（那是两态，混淆等于功能没做）。
- 禁止在 W3 新建第二套矩阵写入通道；判分优先级必须改在 `useMatrixWriter` 的 class 计算里。

【产出文件】src/composables/{useSSE,useDrawerFocus}.ts；src/stores/{tutor,diagnosis,quiz}.ts；src/components/region-e/{TutorPanel,ContextHeader,ChipRow,MessageList,MessageItem,Composer,DiagnosisCard}.vue；src/svg/AnnotationLayer.vue；src/views/{Practice,Records}View.vue；src/data/{tutorTemplates,quizBank}.ts；src/types/api.ts 补 `QuizSubmitResponse`。附「W3 验收证据」。
```

### 7.4 W4 · 打磨与部署

```text
【角色】承接 W1–W3 的 CipherLens 前端 Agent。功能已闭环，本阶段只做非功能项，禁止新增功能。

【本阶段目标 W4】把三项性能预算做实、把无障碍补齐、把部署跑通。
做：性能修到预算内；roving tabindex 收尾 + 表格视图切换（真 `<table>`）+ live region 摘要句；全部状态编码进 URL（参数/步号/折叠态/表格视图，router.replace 节流 300ms）；**22 个快捷键全量**（含新增 `[` / `]` 跳上一个/下一个时间轴标记）+ 输入框聚焦守卫；**时间轴标记键盘可达**（**一步一个 `<button class="c-mark">`**、只有"有标记的步"进 roving、`aria-label`、热区 = 整列宽 × 20px、聚焦播报"第 13 步，1 条诊断提示，2 次提问"）；演示模式参数集（去纹理、去半透明、更高对比、更大焦点环，与埋点 mode 分离）；抽屉焦点陷阱与焦点归还；错误边界 + 离线降级（内置向量，engine 本地算 —— **仅演示路径，不进判分**）；Docker（多阶段构建 + nginx 承载静态 + /api 反代）+ docker-compose（前端 + FastAPI + volume 挂 SQLite）；E2E 冒烟（Playwright，4 条主路径）。
不做：任何新交互、新页面、新动效。发现 W1–W3 的设计缺陷只记录，不改设计。

【硬约束】
1. 性能不达标时，优先怀疑 J1 被破坏（16 格重新绑定响应式），而不是去调动画时长。
2. URL 同步必须 router.replace 且节流 300ms，禁止 push（会污染历史栈）。
3. 表格视图与 grid 视图共用同一份 trace 数据，禁止两套数据源。
4. 演示模式与间距只允许改 tokens 的 CSS 变量作用域，且**只在 3 个挂载点写 data 属性**：`[data-density="compact"]`（工作台 PG-2）、`[data-density="roomy"]`（练习/记录/首页/S 盒全屏）、`[data-mode="present"]`（与 density 正交，可叠加）。token 名不变（`--sp-1..--sp-16` 仍是 8 个），只换值。**组件内禁止出现 `if (mode === 'present')` 这类分支改间距**。
5. 焦点归还必须还给触发元素（矩阵格），禁止还给 body。
6. nginx 必须为 /api 关闭代理缓冲（SSE 需要），并设置 proxy_read_timeout 60s。
7. 全部快捷键在输入框/文本域/contenteditable 聚焦时失效，Esc 例外。

【输入】W1–W3 产出；本文档第 5 节预算表与检测方法；《信息架构与交互规格》2.5 / 2.6 / 5.2 / 5.5 / 8.2（FE-1~FE-8）。

【验收（逐条给数字，不接受「感觉快了」）】
1. Lighthouse（Desktop，本地 vite preview）：FCP ≤1200ms，LCP ≤2000ms，TBT ≤150ms，无障碍 ≥95。
2. 初始路由 gzip JS ≤150KB；工作台路由 ≤220KB（visualizer 截图）。
3. 连按 30 次 →：step p95 <100ms，长帧 0，每步 Layout ≤1，每步写批次恰好 1。
4. 播放 24 步全程：longtask 数量 0，合成层 ≤4。
5. reduced-motion（系统 + 页内开关）分别通关：位移归零、steps(4) 不闪、摘要句完整、变化字节有静态角标。
6. **纯键盘**完成「载入向量 → 播放 → 暂停 → 提问 → 停止 → 关批注 → 开抽屉 → 关抽屉 → `[` 跳到上一个标记 → `Enter` 打开详情」全链路，**中途不出现焦点丢失、焦点跳进不可见区域、或焦点落到 body**。
7. 刷新页面恢复上次参数、步号、折叠态、表格视图。
8. docker compose up 后 localhost 可访问，SSE 正常流式（不是一次性返回），SQLite 落盘到 volume。
9. Playwright 4 条冒烟全绿：载入播放 / 提问流式 / 练习判分（含 downstream 灰化断言）/ 纯键盘标记跳转。
10. **灰度回归**：对 `.c-matrix` 加 `filter: grayscale(1)`，截图后必须仍能在 3 秒内指出「哪几个字节变了 / 哪个选错了 / 哪些是密钥字节」。脚本化为 e2e/grayscale.spec.ts，断言变化格与普通格的平均亮度差 ≥14。做不到就调明度，不调色相。
11. **演示模式降档**：窗口缩到 1024 宽时矩阵回落到 72px 档、4×72 不溢出（`scrollWidth === clientWidth`）；1120px 以上且 `[data-mode="present"]` 时才允许 88px。
12. **演示态硬检查**（§5.2 ⑧）：结构分隔线 ≥2px、零 `alpha` 叠加、零 `pattern`；脚本断言 `bad.length === 0`。

【禁止】
- 禁止为了让 Lighthouse 好看而删功能或延迟挂载 L0 元素（矩阵/时间轴/播放/AI 输入框必须首屏可用）。
- 禁止用 will-change 常驻来"提升性能"。
- 禁止用 transform: translateZ(0) 给 16 格各自升层（会产生 16 个合成层）。
- 禁止在 nginx 层给 SSE 开 gzip（会缓冲）。
- 禁止把 engine 打进主 chunk。
- 禁止提交未删的 console.log（除 usePerfProbe 的 DEV 分支）。

【产出文件】src/components/shared/{TableView,AppDrawer,CollapsibleRow,LiveRegion}.vue；src/composables/{useHotkeys 全量,useUrlState}.ts；src/styles/presentation.css；src/data/vectors.ts；Dockerfile、docker-compose.yml、docker/nginx.conf；e2e/*.spec.ts；一份「W4 预算达标报告」（每条指标：预算 / 实测 / 截图或数值）。
```

---

## 8. Vue 特有坑清单

| # | 现象 | 原因 | 规避写法 |
|---|---|---|---|
| **V1** | 载入 32 步 trace 后页面卡死 3 秒，拖动时每帧 200ms | `ref([])` / `reactive()` 会深度代理每个快照的每个字节；Pinia devtools 还额外序列化 | `shallowRef<TraceStep[]>` + 内部字节用 `Uint8Array`；需要改时整体换引用 `trace.value = next`；devtools 里加 `markRaw` 到单个 step |
| **V2** | 矩阵 dpr=2 时笔画糊，或 DPR 切换后突然变糊 | 只设了 `canvas.width` 没设 `style.width`；只监听 `resize` 没监听 dpr 变化 | `w*devicePixelRatio` 作 backing store + CSS 尺寸固定为 CSS px；额外监听 `matchMedia('(resolution: 1dppx)')` 的 change；`ctx.setTransform(dpr,0,0,dpr,0,0)` 后按 CSS px 坐标画 |
| **V3** | 提问中途切到练习页再回来，发现后端还在跑、token 还在消耗、控制台报 `set on unmounted component` | `fetch` 的 `ReadableStream` 读取循环没人取消；只 `abort` 了 controller 但循环里还在 `getReader().read()` | `useSSE` 内 `onScopeDispose(() => ctrl.abort())`；读取循环每轮检查 `if (ctrl.signal.aborted) return`；路由离开用 `onBeforeRouteLeave` 提前中断；对外暴露 `__sse.active` 计数用于验收 |
| **V4** | 单步一次触发两次 diff 动画 | `watch([currentStep, trace])` 在 trace 刚落库时同时变更两个依赖 → 回调触发 2 次；或 `watch(obj, cb)` 未加 `deep: false` 而对象每帧新建 | 只 `watch(() => playback.currentStep, cb, { flush: 'post' })`；trace 用 `watch(() => engine.trace, ...)` 且 `{ deep: false }`；回调首行做 `if (isEqualStep(prev, cur)) return` 幂等保护 |
| **V5** | Canvas 画出来的颜色和 CSS 里的 accent 不一致，或者直接画成黑色 | Canvas 的 `fillStyle` 不认 `var(--accent)`；`oklch()` 在部分 Chrome/Edge 版本的 Canvas2D 里解析失败会静默变 `#000` | `canvas/palette.ts` 维护一份 JS 常量表（hex sRGB，构建时由视觉 token 手抄并加注释对应哪个变量），**并在 dev 启动时用探针校验**：`ctx.fillStyle = 'oklch(...)'; if (ctx.fillStyle === '#000000') useFallback`。禁止在 draw 函数里 `getComputedStyle`（每帧读样式 = 强制样式重算） |
| **V6** | 抽屉关闭后内容"闪一下才消失"，或 `@after-leave` 不触发 | `v-if` 与 `<Transition>` 同帧反转；reduced-motion 下时长归 `0ms` 导致 `transitionend` 永不派发；`0.01ms` 在某些浏览器被当成 `0` | 用 `0.01ms` 而非 `0ms`；`@after-leave` 必须有 `setTimeout(cleanup, duration + 50)` 兜底；抽屉状态走 `useUiStore.drawer`，但 DOM 用 `v-show` + `pointer-events` 而非 `v-if`（避免重建 44 字条带） |
| **V7** | 在明文输入框里敲 `d`，结果切成了解密模式；敲 `space` 播放了 | 全局 `window.addEventListener('keydown')` 不判目标元素 | `useHotkeys` 首行守卫：`const t = e.target as HTMLElement; if (t.isContentEditable \|\| ['INPUT','TEXTAREA','SELECT'].includes(t.tagName)) { if (e.key !== 'Escape') return }`；`Space` 需 `e.preventDefault()` 以免页面滚动；监听挂 `window`、卸载移除（不能挂 `document.body`，会丢 `capture` 顺序） |
| **V8** | 收 AI 栏后矩阵宽度变了但 Canvas 还画在旧位置，SVG 括线错位 | 只监听了 `window.resize`；flex 布局内部尺寸变化不触发 window resize | 一律 `ResizeObserver` 监听**矩阵容器**，回调里不直接算，`requestAnimationFrame` 合并一次；三层的 `padX/padY` 全部从同一个 `useStageMetrics` 出，禁止各自 `getBoundingClientRect` |
| **V9** | `shallowRef` 的数组 `push()` 后视图不更新 | shallow 系列只跟踪 `.value` 引用本身 | 永远整体替换：`trace.value = [...trace.value, step]`；或在 engine 里一次性构造完再赋值（本项目采纳后者，避免 O(n²)） |
| **V10** | 组件里 `getComputedStyle(el).getPropertyValue('--cell-size')` 返回空字符串，或返回 `"62px"` 这类**没法直接参与计算的字符串** | 自定义属性在 computed style 里保持**声明时的原始 token 串**（`62px`、`clamp(...)`、`var(--x)` 都不会被解析成数值）；未 `onMounted` 前元素不在文档流，读到空串 | 用探针法：`document.createElement('div')` 设 `width: var(--cell-size)` 插到容器里读 `offsetWidth` 得到**真实像素**（一次读，放进 `useStageMetrics`）；或直接 `getBoundingClientRect()` 量首格宽度。**禁止** `parseInt(getComputedStyle(...))` 然后假设单位是 px |
| **V11** | 播放时 CPU 占用随停留时间线性上涨，最后掉帧 | `will-change: transform` 写进了基础类，16 格 + canvas + 抽屉全部常驻升层，显存和合成开销爆掉 | `will-change` 只在 `.is-playing` / `.is-dragging` / `.is-open` 选择器内声明；播放停止后 `setTimeout(removeClass, duration + 50)` 清掉 |
| **V12** | Pinia action 里 `usePlaybackStore()` 报 "no active Pinia" | 在 `engine/trace.ts` 或工具函数顶层调了 `useXxxStore()` | store 只允许在 `setup` 作用域或 `router.beforeEach`（已 `app.use(pinia)` 之后）里调用；`engine/` 与 `canvas/` 禁止 import store，参数靠入参传 |

| **V13** | `hidden` 切了但两个上标同时显示 | `hidden` 靠 UA 样式 `[hidden]{display:none}` 生效，**特异性极低**；`.c-byte__sup { display:inline-block }` 会直接盖掉它 | 不用 `hidden` 属性，改 `data-active="true|false"` + `.c-byte__sup[data-active="false"]{display:none}`；若坚持用 `hidden`，必须 `[hidden]{display:none !important}`（全项目唯一允许 `!important` 的地方） |

| **V14** | 某条格线在状态切换后"消失"，或某格看起来"没画完" | 某个状态为了减墨把 `border-color` 设成透明/纸色，或写了 `border: none`；或格线取错 token（取到演示值 0.760，比邻居浅） | **`border-color` 只允许在 `--rule-region-ink` / `--line-hairline` / `--st-downstream-border` / 状态色之间取值**，永远不许 `transparent`、不许 `none`、不许和纸色同值。**基线恒为 `--rule-region-ink`（常规 0.845 / 演示 0.545），`--line-default` 不许出现在 `.c-byte` 上**（它是非格子结构线的档，演示值 0.760 比格子基线浅）。6px 间隙下每格边框就是它的身份证，缺一条就读作"没画完"。`downstream` 取 `--line-hairline`（**降一级，不是空**） |
| **V15** | 切到 `is-error` / `is-selected` 时 hex 文字横向跳 1–3px | `border` 参与盒子模型，加粗边框会压缩内容盒；`box-sizing: border-box` 也救不了"内容盒变窄" | **`border-width` 恒定**（常规 1px / 演示 2px），七态**只改 `border-color`**；加粗观感用 `box-shadow: inset 0 0 0 Npx`（画在 padding box 内侧，**不参与布局**）；外环用 `outline`（同样不参与布局）。本项目第一条视觉红线是"格子绝不位移"，这条是它在 CSS 层的落地 |

**最后一条工程纪律**：W2 起每次提交前跑 `npm run perf`（内部就是"连按 30 次 → + 打印 p95/长帧/批次"）。**性能不是 W4 才做的事，是每一步都要守住的不变量。**

### 8.1 跨角色传递数值的硬规则（这条是本项目**已实际发生过 4 次**的失败模式）

> **任何尺寸 / 色值 / 坐标出现在第二份文档里时，必须连同它所在的原句一起引，不许改写成短语。**

**禁止**：`提问标记 = 8×2` （短语，脱离上下文）
**要求**：`提问标记 = "2px 高 × 8px 宽横条，标记轨下沿"（引自 visual §9.3）` —— 连同单位、维度顺序、所处位置一起原句搬运。

**证据链（同一个形状被改了 4 次，4 次全是转述丢约束，没有一次是判断错）**：

| 次序 | 原文 | 转述后 | 丢了什么 |
|---|---|---|---|
| 1 | team-lead：`8px × 2px 横条` | 我方文档：`2px 短横条` | **丢了 8px 宽度**，只剩"短" |
| 2 | 修订：`5×5px 无圆角方块` | — | — |
| 3 | visual：`2px 高 × 8px 宽固定横条` | 各方讨论中：`横条（宽度数据驱动）` | 把"固定 8px"误读成"横跨整列" |
| 4 | 复裁：`5px 方块冻结` | — | — |

**为什么这条比任何单个 CSS 决定都重要**：数值类约束（尺寸、色值、阈值、坐标）在传递中丢失单位或维度是最廉价的错误，但修复成本最高 —— 它不会让代码报错，只会让代码"按错的规格正确运行"，而且往往到评审或投影现场才暴露。

**落地检查**：本文件里每个引自视觉 / 体验 / team-lead 的数值，都必须在同句或紧邻处标注来源章节；Coding Agent 若发现某个数值没有来源标注，**停下来问，不要自己补一个合理的**。

---

## 9. 交付清单与验收口径

| 交付物 | 位置 | 验收 |
|---|---|---|
| 可运行前端 | `cipherlens/` | `npm run dev` 三秒内起 |
| 生产构建 | `dist/` | gzip JS 达标、engine 独立 chunk |
| Docker 全栈 | `docker compose up` | localhost 可用、SSE 流式、SQLite 落盘 |
| 预算达标报告 | `docs/perf-report.md` | 每条指标：预算 / 实测 / 证据 |
| 无障碍走查 | `docs/a11y-check.md` | 8 条 FE 项逐条勾 |
| E2E 冒烟 | `e2e/` | 3 条路径全绿 |
| 键盘速查 | `docs/shortcuts.md` | **22 键**与 `?` 浮层一致 |

---

## 10. 承接记录（视觉 10 条 + 体验 6 项 + team-lead 裁决）

> 本节是视觉架构师 10 条实现要点的落地记录。**凡与本文件 §1–§9 冲突处，以本节为准**（已就地改过的地方标注了位置）。目的是让 Coding Agent 只需要读这一份文档，不必回头翻两份规格对齐。

### 10.1 逐条承接

| # | 视觉要点 | 我的落地 | 状态 |
|---|---|---|---|
| VF-1 | hex 必须在 DOM，Canvas 只画会动几何 | 已在 J1/J4 与 §3 承接。**补充澄清**：`drawRowShift` 画的是回绕描边与行轨道刻度，**字节内容位移仍由 DOM 行轨道 `translateX` 完成**（8 格：4 实 + 4 鬼）。"行移位位移归 Canvas"若指内容位移会与 VF-1 自相矛盾，按"内容 DOM / 几何 Canvas"切分 | ✅ 已澄清 |
| VF-2 | 性能红线 | 已进 W2 硬约束 1–2 与 §5 预算。**新增两条预算**：单帧同时动画元素 ≤ 64（`document.getAnimations().length` 采样）；`background-position` 动画只允许 ≤24px 字节格内，矩阵/时间轴/背景层一律禁止 | ✅ 已补 |
| VF-3 | reduced-motion 不能只设 0 | §4 表头已改为**三段归零公式**：`--d-*: 0.01ms` + `animation: none` + `getAnimations().cancel()`。并加了配套硬规则：描边/位移动画**静止态必须是终态**，否则 `cancel()` 会让元素消失。4 条静态替代已写进 W2 验收第 4 项 | ✅ 已就地改 |
| VF-4 | `--step-interval: 800ms`，节奏与时长解耦 | §2.2 的 `speed` 已改：800ms × {2,1,.5,.25} = 1600/800/400/200，**单步动效固定 280ms 不随倍速变**。新增 token，且**故意不参与 reduced-motion 归零** | ✅ 已就地改 |
| VF-5 | AI 栏收起不 animate 栅格宽度 | 新增 **M26**：`C 区 opacity 1→0`(120ms) → 下一帧换 `--ai-col`（360↔48，无过渡）→ `opacity 0→1`(120ms)。W2 验收第 7 项卡"该 240ms 内 Layout ≤1" | ✅ 新增 |
| VF-6 | `--cell-size` 离散桶 + 容器查询 | §3.4 已删 `clamp(48px,4.6vw,64px)`，改 5 档桶（44/52/62/72/88）+ `@container`。理由：连续 clamp 跨断点那一帧会算出十几档中间尺寸，16 格同时重排。新增 **M27** 用 M26 的 opacity 遮罩盖住换档帧 | ✅ 已就地改 |
| VF-7 | 诊断行常驻占位 `--diag-row-h` | 新增 **M28**（常量占位，无动画）：40px / 演示 56px，无提示时显示 11px `DIAGNOSTIC —`。**这条很重要**：否则提示出现时会推动对话流位移，违反 UX-V3 的实施意图 | ✅ 新增 |
| VF-8 | 密度/演示用 data 属性，只在 3 个挂载点 | W4 硬约束 4 已改。`[data-density="compact"]` / `[data-density="roomy"]` / `[data-mode="present"]`（正交可叠加）。token 名不变只换值，组件内禁止 `if (mode==='present')` | ✅ 已就地改 |
| VF-9 | 时间轴 4 条水平轨道 | 见 §10.2，已完整落地 | ✅ 新增 |
| VF-10 | 焦点环（含演示双环） | M24/M25 已按视觉给的数值改：常规 `outline 2px accent + offset 2px + 静态 spread shadow 4px paper-0` 隔离带；演示内层 3px 近黑 + 外层黄双环 + 左外侧 8px `▸`。**明确不用 glow 当焦点环**（投影会糊，且是 slop 特征） | ✅ 已就地改 |
| VF-11 | 灰度回归脚本 | §5.2 新增第 ⑦ 项 + W4 验收第 10 项，给了 e2e/grayscale.spec.ts 的断言口径（亮度差 ≥14） | ✅ 新增 |

### 10.2 时间轴规格（VF-9 落地，取代 v1.0 的"固定 72px"）

`--transport-h` **三档：常规 104 / 压缩 92（`max-height:780px`）/ 演示 136**，4 条水平轨道自下而上叠放（括号内为压缩档）：

| 轨 | 高 | 内容 |
|---|---|---|
| 游标行 | 14px（压缩 12） | 当前步游标（**常态实心 / 拖拽态空心**，双通道区分"预览位"与"执行位"） |
| 标记轨 | 20px（压缩 18 / 演示 24） | **两条子轨，形状不同、不合并**：诊断 = 上沿 y30–35 **实心圆点**（`border-radius:50%`，语义「一个时刻」）；提问 = 下沿 y41–46 **无圆角方块**（语义「一次提问」）。同一 x 上两者并存。尺寸取 `--tl-mark-diag` / `--tl-mark-ask`（**常规 5px / 演示 6px，不许写死**）。**图例复用同一个 `.c-mark__shape` 元素**，尺寸与轨道上完全一致 | 
| 刻度轨 | 10px（压缩 8） | 每步一小格，第 0 轮单段 |
| 轮号带 | 16px（压缩 14） | 每段标"轮 n"文本 |

- **标记轨内 z 顺序：标记 > 游标**。不要做"游标压住标记、标记左移 1px 让位"——2px 游标 + 4px 标记左移 1px 只露 1px 边，等于没露；游标位置已由步号文本表达，在标记轨内不必压住标记。
- **标记键盘可达（漏了 = 无障碍验收不过）**：
  - 每个标记是一个可聚焦元素，纳入标记轨的 roving tabindex；`aria-label` 例：`第 3 轮列混合的系统推测，按回车跳转`
  - `[` / `]` = 跳到上一个 / 下一个**有标记的步**（同一步不重复停留；不再有"诊断优先于提问"—— 那是"一标记一热区"旧模型的规则）—— 作为**第 21、22 个快捷键**
  - 聚焦态：非演示 `outline: 2px solid var(--accent); outline-offset: 2px`；演示态走 M25 双层环
  - **热区 = 该步整列宽 × 标记轨全高 20px，一步一个 `<button>`**（不是上下两个半区——两个 10px 目标相接会互相吃掉 24px 判定圈，两个都不达标），热区只服务鼠标，不能作为唯一路径
  - 聚焦播报：`第 13 步，1 条诊断提示，2 次提问`
- **4 条轨道全部数据驱动**：步数、轮数来自 `trace.length` 与 `trace[*].round`，**禁止写死 24 / 40 / 10**（AES-192/256 分别是 28 / 32 步）。
- 轮分段靠「2px 段间分隔线 + 交替明度底 + 轮号文本」，**禁止按轮上色**（8–14 种色相在色盲与投影下不可辨）。
- 点击热区 = **该步整列宽 × 标记轨全高 20px，一步一个按钮**，同时承载该步的诊断与提问；精确选择在 E 区标记卡里做（每条 28px 独立可点）。**两级目标都 ≥24px，没有一处需要例外**。
- 拖拽期间**三禁止**：不触发任何单步 diff 动效、**不发 AI 请求**、**不写诊断历史**。松手停住 ≥300ms 后才允许该步动效重播一次。
- **图例（`c-transport__legend`）复用轨道上的同一个 `i.c-mark__shape`**，只换宿主、不改尺寸、不改形状、不改颜色 —— 即"把同一个元素放到另一个位置"，不是另画一个图标。**排布是"两个条目左右并排"，不是上下叠**：每项 = 一个高 `var(--tl-mark-band)` 的定高盒 + 4px + 11px `--ink-3` 文本，**盒内只放该条目那一枚 `<i>`**，圆贴上沿、方贴下沿。
  ```html
  <div class="c-transport__legend">
    <span class="c-transport__legend-item"><i class="c-mark__shape" data-kind="diag" aria-hidden="true"></i>系统推测</span>
    <span class="c-transport__legend-item"><i class="c-mark__shape" data-kind="ask"  aria-hidden="true"></i>我的提问</span>
  </div>
  ```
  **为什么不能上下叠**：上下叠等于在图例里把"圆在上、方在下"合成一个盒子，学生学到的就变成"两个符号"而不是"圆=时刻在上轨、方=关注在下轨"。**位置本身是通道，图例必须保真位置，只保真形状是不够的。**
  **禁止为图例写 `[data-ctx="legend"]` 之类的定位覆盖** —— 写了就等于宣布"图例是另一套实现"，"像素级一致"这条验收永远过不了。图例盒只需要 `position: relative`（已在 `.c-transport__legend-item` 上），形状原子自己带 `top/bottom`。
  **禁止用 `▪` / `●` 字符**。这也是"图例与轨道像素级一致"这个验收项唯一能通过的做法：图例一旦自己定尺寸，24 步与 58 步两档下都会差 1px，而 1px 差在投影上会被读成"两种不同的标记"。
  > **前提是 `.c-mark__shape` 的定位只相对"宿主"，而两个宿主（`.c-mark` / `.c-transport__legend-item`）都必须是 `position: relative`。** 少给图例盒这一行，形状会相对更远的祖先定位、直接飞出图例 —— 而且不报错。**"同一个元素两处复用"的验收，第一件事是数宿主上的 `position` 有几处。**
- **图例的 `aria-describedby` 目标节点，收起时只能用 `.sr-only`**（`position:absolute` + 1px 裁剪盒），**禁用 `display:none` / `visibility:hidden` / `hidden` 属性 / `aria-hidden`** —— 这四种都会把节点摘出无障碍树，`aria-describedby` **静默失效**（不报错），比不加描述更糟。验收是双断言：`getComputedStyle(el).display !== 'none'` **且** `el.getBoundingClientRect().width > 0`。**坑在"看起来最省事的那种收法"上：`display:none` 是所有人第一反应。**
- **58 步（AES-256）密度用「整列宽热区 + 图例 + 悬浮详情」解决，不做抽稀**（team-lead 定稿）。理由：**抽稀会让"标记位置 ≠ 数据位置"**，而这是可视化工具最不能错的地方 —— 学生点第 37 步的标记，跳到的必须是第 37 步。58 步时列宽约 10px，5px 方块占 50% 仍可辨；8px 横条占 80% 才会粘连（这也是方块胜出的量化依据）。

### 10.3 已裁决 / 待确认

| # | 问题 | 裁决 | 状态 |
|---|---|---|---|
| Q1 | 网格基线归 Canvas 还是 DOM | **team-lead 裁决：用 DOM**（`inset box-shadow: 0 0 0 1px`），Canvas 只剩 2 个 pass。理由：dpr≥1 像素对齐更稳、静帧零重绘、少一层。已在 §3.2 与本表 J5 落地 | ✅ 已闭环 |
| Q2 | 字重 500→600 能否过渡 | **team-lead 裁决：不引入可变字体，瞬时切换（0ms）**，从动效表删除（见 ~~M5~~）。理由：等宽静态字体（Plex Mono）为一次 16px 数字换字体栈不值得；280ms 插值在 16px 下人眼不可辨 | ✅ 已闭环 |
| Q3 | 桶值 44/52/62/72/88 的 88px 上界是否破坏构图；且**缺窄视口降档** | 按离散桶执行；新增规则：**演示模式下窗口 <1120px 时矩阵回落到 72px 档**（4×88 在 1024 视口会溢出）。若视觉认为 88 破坏构图，只改 `@container` 断点值，代码结构不变 | ⚠️ 待 visual 确认桶值与降档阈值 |

### 10.4 体验侧 5 项增补承接（v1.2）

| # | ux 要点 | 落地 |
|---|---|---|
| UX-1 | 第 7 态 `downstream`（受首错污染字节） | 已进 §3.1 七态表 + `useQuizStore.propagated` + W3 提示词。**硬约束**：独立选择器、禁止 `[class*="error"]` 模糊匹配、判分期间 `error`/`downstream` 覆盖 `changed`、视觉上不是红色无折角无 `≠`。矩阵**不画外框**、只画实线四角括 + 文本「影响范围：16 字节」 |
| UX-2 | 时间轴标记双轨两种形状 | 已进 §10.2 定稿：诊断 = 上沿 5px **圆点**（y30–35）；提问 = 下沿 5px **无圆角方块**（y41–46）；**都不用横条** —— 横条宽度是数据驱动的（24 步≈28px、58 步≈10px、容器变宽还会变），图例永远无法做到「与轨道完全一致」；且 58 步时 10×2px 横条会与刻度轨竖刻度混成「又一种刻度」。图例复用同一个 `.c-mark__shape` 元素。标记轨内标记 z 高于游标 |
| UX-3 | 标记的键盘路径 | 已进 §10.2 + W4：**一步一个 `<button class="c-mark">`，只有"有标记的步"进 roving**、`[` / `]` 为第 21/22 快捷键（跳到下一个**有标记的步**，同一步不重复停留）、热区 = 整列宽 × 标记轨全高 20px、聚焦播报「第 13 步，1 条诊断提示，2 次提问」；精确选择在 E 区卡内（每条 28px 独立可点） |
| UX-4 | density 归属规则（不用第三套间距） | 见下表 §10.5。**关键修正**：S 盒 PG-3 = **外壳 roomy + 表格 compact**（16×16=256 格，整页 roomy 必溢出）；练习 PG-6 与单步训练 PG-7 = roomy 外壳 + compact 矩阵 |
| UX-5 | 2× 档（400ms）下 C2 摘要句不得有更新动效 | 新增规则：`SummarySentence` 的文字切换过渡**只在 1× / 0.5× 启用**；400ms 档（2×）与 200ms 档（4×）下直接换文本。理由：每秒变 2.5 次文字，任何过渡都糊成噪点；0.5× 必须保留（读摘要需要时间） |
| UX-6 | 演示模式矩阵格径缺窄视口降档 | 已并入 Q3：<1120px 回落 72px 档 |
| UX-7 | **线型语汇**：虚线专表「未生效/待定/禁用」（全规格已用 11 次），`downstream` **不得用虚线**，`done` 也去虚线改实线 + 左下 5px 缺口 | 已进 §3.1 七态表 + 线型语汇声明 + M23b。**`downstream` 终稿**：`data-bd="downstream"` → `border-color: --line-hairline`（降一级）+ 底色 `--surface-inset` + `--ink-3` 400 + 无角标无纹理；**演示态边框不降**，安静感由底色 `oklch(0.905 0.004 258)` + 字重 400 对 700 承担。**修正记录（共四次）**：① ux 先给「无边框」→ ② 视觉/ux 纠正为「必须有极淡边框」（矩阵结构靠格边框承载，去掉会塌洞）→ ③ team-lead 提出「格线改由容器画」→ **④ 作废**（与 `--cell-gap: 6px` 冲突，且它要治的"共享边/双线"在间隙布局下不存在）。**「极淡实线」不是一种线型，只是实线的一个色阶，因此不进线型语汇表** |
| UX-8 | **七态叠加改为「按视觉属性通道分配 owner」**，不靠 class 顺序 | 已进 §3.1 **六通道** owner 表（fill / bd / txr / corner / text / bar）+ 四条互斥/组合规则 + 代码改法。**owner 唯一性用属性保证**：`data-bd` / `data-txr` 单值 → 两个 owner 同时存在在语法上不可能；`fill` 单值输出（末尾不再补 push）。**`bar` 由 ux 提议补入**：只有 `key` 一个候选、无优先级、不进角位截断（挡住"五通道满了就往 fill 里塞"那条路）。**组合态出口**：`error + selected` 走两类选择器规则（红底红边归 error，**近黑外环**归 selected，`outline-color: --ink-1`）。**生命周期**：判分叠加绑定 `step_index`，离开该步整体撤场 |
| UX-10 | `done` 去点阵（视觉 v1.2）→ `txr-dots` 删除 | 已删。纹理通道只剩 `fold`(error) / `hatch`(key) / `none` 三值；`done` 的形状身份只由左下 5px 缺口承载（一个通道足够，多一个即噪音） |
| UX-11 | 角位截断序 | 已改 `br > tl > tr > bl`（错误 > 反向 > 变化 > 完成）。原写法 `[br, tr, tl, bl]` 会在 `error + reverse` 时丢掉高优的 `tl`，已修正并写进 W2 验收 8 |
| UX-9 | **整段错只画实线四角括，不画完整外框**（"围起来"本身带"这块有问题"的语气）；琥珀也不能兼职表达"有问题"（会废掉 `changed` 的语义） | 已进 §3.1 区域级原则第 2 条 + W3 验收 7 |

**UX 提出、但已改由后端承接的一条**：`⇄` 输入不一致（学生录入的明文/密钥与题目不同）**不能算算法错**，否则学习记录正确率被抄错污染。按 team-lead 裁决判分在后端，该判断**由 `/api/quiz/submit` 返回可空对象 `input_mismatch: { field, char_index, expected } | null`**（不是 boolean —— 文案必须说出「哪个字段、第几个字符」），前端只做「非 null 则不计入统计 + 渲染字段级提示」。**不要在前端复算输入**。

### 10.5 density 归属规则（UX-4 落地）

规则：**density 由页面容器定；嵌入的密集组件可单独覆盖 `--cell-size` 桶与 spacing。** 不引入第三套间距。

| 页面 | 外壳 density | 嵌入组件覆盖 |
|---|---|---|
| 工作台 PG-2 | `compact` | — |
| 练习 PG-6 | `roomy` | 「错因定位」里嵌的小矩阵：**cell 桶走 compact（44/52/62/72），间距走页面级 roomy** |
| S 盒 PG-3 | `roomy` | **16×16 表格走 compact**（256 格，整页 roomy 必溢出） |
| 单步训练 PG-7 | `roomy` | 矩阵走 compact 桶 |
| 记录 / 首页 / 关于 | `roomy` | — |

实现约束：覆盖只写 `--cell-size` 与局部 spacing 变量，**不新增 `[data-density]` 取值**，避免出现第四、第五套间距。

### 10.6 视觉 §9 对齐后仍待 visual 补的一项

视觉 v1.1 §9.1 声明的字节格状态是 `is-changed / is-selected / is-error / is-key / is-done / is-ghost / is-reverse / is-xor / is-disabled`，**尚无 `is-downstream`**（第 7 态是 team-lead 后续裁定的）。已按 team-lead 口径在本文档写死 `is-downstream`，等 visual 补样式与状态清单。**在补之前以本文档 §3.1 为准**，代码照 `is-downstream` 写，不要等。

> **v1.9 更新：此项已闭合。** visual v1.2 §2.3.1 已补第 7 态 `downstream` 与 `is-downstream` 状态清单。**终稿：`border-color` 由 `--rule-region-ink` 降一级到 `--line-hairline`（宽度恒 1px）+ 底色 `--surface-inset` + `--ink-3` 400 + 无角标、无纹理、无 `≠`；演示态边框不降，`--st-downstream-border` 的演示值 = `var(--rule-region-ink)`（0.545），与同屏其他格同值，安静感由底色 ΔL 0.06 + 字重 400 承担。** 边框色通道优先级 `error > selected > downstream > idle`（`changed`/`key`/`done` 不改边框色，故不在链内）。visual 的 `:not(.is-downstream)` 闸门照旧保留。

**现状：格边框这一项已结案，不再是待议项。**

1. **演示态格边框 = `--rule-region-ink` = `oklch(0.545 0.012 258)`，对纸底 4.6:1，七态一律**（含 `done`）。team-lead 终裁、visual v1.2 已同步（§2.3.2「普通」与「已完成」两行都改成 0.545 —— 同一张矩阵里不许两个值，否则 0.760 那行会被读成没画完）。
   > **`--line-default` 0.760 只服务非格子结构线**（控件边、表头框、分区细线）。它在常规块与 `--rule-region-ink` 恰好都是 0.845，所以上一版误以为两者等价；演示块一分叉就露出来。**主从关系：格子基线归 `--rule-region-ink`，`--line-default` 是别的线族的档，不是格子的默认值。**
   > 实现上格线仍收在一个变量 `--bd-color` 里，且**演示态不需要任何 `border-color`/`--bd-color` 覆盖** —— `--rule-region-ink` 在演示块自己就是 0.545。上一版提到的"改一行"的写法反而会多一层需要维护的分支，已删除。
   > 顺带一条口径（team-lead 原话的意思）：**「与其他态同值」在常规态成立、在演示态是陷阱。** 凡要靠"同值"推断，一律引 token 名、不引数值 —— 数值相等是两个 token 的巧合，不是它们的关系。
2. **`__flag` / `__fold` / `__notch` → 2 个通用 `__corner` 的命名合并**：ux 已裁定元素数按"同格最多 2 个"配，几何/形状/颜色全部照搬，只把"位置"由硬编码改成 `data-corner` 驱动。请 visual 在 §9.1 同步元素名，避免 W1 的 Coding Agent 照旧名建 3 个节点。
3. **`selected` 的四角刻线停用**（ux v1.3 改判）：请 visual 在 §2.3.1 的 C 行删掉"四角 6px L 形刻线"，§2.3.3 第 2 条把"C 有角刻线（唯一有角刻线的状态）"改成"**C 有外环（唯一有外环的状态）**"，并把外环写成 `selected` 的形状通道。**色盲论证不受影响** —— 换的是形状载体，不是通道数量。
4. **`--st-downstream-border` 的演示值 = `var(--rule-region-ink)`**（不是 `--line-default`）。常规降一级、演示与邻居同值，**由一个 token 表达两个档，组件里不写 `if (mode === 'present')`** —— 这层间接必须留着：常规态它有值（`--line-hairline`），删掉就得在常规态硬写色值，下次改常规线色又会漏一个。
   > 为什么这条不是"美观问题"：若 downstream 演示值指向 `--line-default`，**普通格 0.545、downstream 0.760 —— 它比邻居更浅**。在 6px 间隙里，"比邻居浅的闭合框"只有一个读法：**这格没画完**。它不是"降一级"，它是反向加深了误读。

### 10.7 提问标记的形状 —— **已冻结（v1.7 结案）**

**定稿：诊断 = 上沿 5px 圆点；提问 = 下沿 5px 方块，直角无圆角。**

team-lead 复裁时把"提问是离散点不是区间"升为主理由，并且**撤回了自己原先的第一条否决理由**（图例与轨道无法一致 —— 那条已被 visual 改成固定 8px 拆掉），保留两条硬约束：

1. **与相邻轨道的语汇冲突**：58 步时单步约 10px，8px 横条占列宽 80%，就是一条短横线；而正上方 6px 处是一排 1×6px 竖刻度。两种"短线段"垂直相邻 6px，投影 1 米外必然混读。
2. **形状类别差异 > 尺寸差异**：5×5 块与 1×6 线是两种图形类别，不靠尺寸区分。

**数据模型的支撑（决定性）**：提问在数据模型里是"**某一步的提问次数**"（`aria-label` 写的就是"你提问过 1 次"），是**离散点**。8px 这个宽度既不对应步宽、也不对应时长、也不对应任何量 —— **一个不表达任何量的长度，会被读成"某种长度单位"**。原来"横条 = 一段关注区间"的语义在数据上根本不存在。

视觉已同步（§6.3.3 / §9.3 / `--tl-mark-diag: 5px` / `--tl-mark-ask: 5px`）。**不再讨论。**

### 10.8 v1.5 承接 visual r2 的另外三项（已落地）

| 项 | 落地 |
|---|---|
| Q1 基线**不留兜底** | 已在 §3.2 删除全部兜底；visual 补充的理由（Canvas 在 125% 缩放下必然遇到"1.25 物理像素"只能取整到 1 或 2）已并入 |
| Q2 静态字重不可插值 | 已确认：**IBM Plex Mono 是静态字重，`transition: font-weight` 写了和不写结果一样**（浏览器找最近可用字重瞬间切换）。M5 删除的决定因此更硬，不是妥协 |
| Q3 88px 降档阈值 | 已改：`[data-mode="present"] .c-matrix__grid` 默认 **72px 兜底**，`@container (min-width: 720px)` 才升 **88px**。**阈值是 stage 容器宽，不是视口宽** —— 我 v1.4 误把 team-lead 的"1120px 视口"直接套在容器查询上，那是错的，会永远不命中 |
| `--transport-h` 三档 | 常规 104 / **压缩 92（`max-height:780px`）** / 演示 136；压缩档只压高度、四轨仍全在（16→14 / 10→8 / 20→18 / 14→12）。已进 §3.5、§10.2、§5 骨架尺寸行 |
| `c-diagslot` 常驻槽 | 已进 §3.5：高度锁死、`aria-live` 挂槽位不挂批注、批注**绝不 `position:fixed`**、出场只动 `opacity` + `translateY(2px→0)` |
| S 盒 `data-density` | §10.5 早已按「外壳 roomy + 表格 compact」写死，与 visual 一致 |

### 10.9 v1.9 —— 格线 owner 第四次改判（终稿）+ ux 契约三改

**这一项前后改了 4 次，全部经过记录在此，不要再翻第 5 次。**

| 次序 | 结论 | 撤回原因 |
|---|---|---|
| 1 | `downstream` 无边框（ux） | 视觉/ux 认为去掉边框那 15 格会塌洞 |
| 2 | `downstream` 极淡实线边框 | 淡框在 1280 投影下约 1.1:1，等于没有 |
| 3 | 格线改由矩阵容器画，`.c-byte` 不写 `border`（team-lead） | **与 `--cell-gap: 6px` 冲突**：容器底色会填出 6px 实色条带；且它要治的"共享边 / 双线"在 6px 间隙下**不存在** |
| **4（终稿）** | **格线回到每格自己的 `1px border`；宽度恒定，七态只改 `border-color`，加粗用 `inset`** | — |

**第 3 次的教训（两边各一条）**：team-lead 提方案时没核对文档里已有的 `--cell-gap`；我实现时明知 `6px` 与 `gap:1px` 互斥，却选择"实现方案 B 绕开"而不是回问一句。**两次都是"引用数值不回原文核对"** —— 与 §8.1 是同一条纪律。**下一回遇到同类冲突，正确动作是停下引用原文，不是设计一个绕开它的方案。**

**ux 本轮三处契约修改（已全部落地）**

| # | 改动 | 落地位置 |
|---|---|---|
| 1 | `txr-dots` 删除：`done` 已无点阵，纹理通道只剩 `fold` / `hatch` / `none` | §3.1 owner 表、七态表 `is-done` 行、M23b |
| 2 | 角位截断序改为 **`br > tl > tr > bl`**（错误 > 反向 > 变化 > 完成）；原 `[br, tr, tl, bl]` 会在 `error + reverse` 时丢掉 `tl` | §3.1 角位契约、`paintFor()`、W2 验收 8 |
| 3 | `is-*` vs `bd-*` 前缀之争 → **用单值属性 `data-bd` / `data-txr`**：`class` 里 `bd-error` + `bd-key` 同时存在语法合法，属性则平台保证唯一 | §3.1 owner 表、`paintFor()`、W2 硬约束 13 |

**ux 三个提问的裁决（记档，理由比结论重要）**

1. **`fill` 单值输出，末尾不再补 push** —— 同一个 class 出现两次会让"谁是 fill 的 owner"说不清。
2. **判分期 `is-key` 保留**（否掉"为了统一而一并让位"）：`changed` 是 **diff 信息**，`key` 是 **输入条件**。学生答错在轮密钥加时，必须看到"参与异或的是哪 8 个密钥字节"，否则他知道错了但不知道错在哪一半。**判分只让 diff 让位，不让输入条件让位。**
3. **`c-tl` 不加门控，改为"判分叠加绑定 `step_index`"** —— 它顺手堵掉一个更容易出的 bug：判分结果画在了非锚点步上。

**ux 指出我漏掉的一处**：`error + selected` 是独立状态。原代码里 `isErr` 直接占了 fill、`is-selected` 被吃掉，结果是判错后点开那个字节看不到任何"我选中了"的反馈。已加两类选择器组合规则（红底红边归 error，**近黑外环**归 selected），这是 owner 表里**唯一允许"两个通道各有 owner"**的情形。**另：`selected` 的四角刻线已停用**（与 `error` 右下折角同位置同尺寸），形状通道由外环单独承担。

### 10.10 v1.9 r2 —— 三条跨角色纠正（每条都是我先写错、别人指出）

| # | 我写错的 | 纠正 | 为什么值得单独记 |
|---|---|---|---|
| 1 | `paintFor()` 的 `cls` 只输出 `FILL_CLS[fill]` 和补一次的 `is-selected`，**`is-key` 从来没被挂上去** | `cls` 增加 `keyed ? 'is-key' : ''`；同时 `FILL_CLS.selected` 改成 `''`，`is-selected` **只从布尔出来**（单一来源） | 我在同一封信里论证"`key` 的身份挂在左竖条这条永不竞争的通道上，所以判分期仍然可读"——**而代码里那个 class 根本不存在**。判分期 `txr` 被 `error` 的 `fold` 占掉时，key 会一点痕迹不剩，正好是我说要避免的场景。**文档里的结构性保证必须有输出侧对应物，否则它只存在于文档里。** |
| 2 | `selected` 用"四角 6px L 形刻线 + 外 3px 环" | **刻线停用**，只留外环（且叠加态环色转 `--ink-1`） | `error` 的右下折角与刻线的右下臂**同位置、同尺寸、不同语义**，`error + selected`（判错后点开那个字节，必然动作）会叠成一条画歪的线；而且四角是角标通道、已满 4 个 owner。**"两个形状恰好落在同一位置"这类冲突，看单态截图永远发现不了，只有想到组合态才会撞见。** |
| 3 | 结构线在两处分别写成 `border` 与 `inset box-shadow` | **择一：`border`**。因为 `data-bd` 消费 `border-color`，线改 `box-shadow` 会让它**静默失效** | 两处都留不是"2px"那么简单：更坏的是改完线之后状态色不再生效，**不报错**。凡是"读一处对、读两处矛盾"的规格，Coding Agent 一定挑省事的那处实现。 |

**第 4 条（team-lead 拦下的，我原本只写了"不该这么做"，没写成禁令）**：`downstream` **禁止尺寸内缩**。位移是位置跳、内缩是尺寸跳，**都是几何变化**；16 格的方块感建立在尺寸完全一致上，一格小一圈只会被读成"这格有毛病"或"这格更重要"。要表达"退后"只能用**变淡**（色阶 + 墨量），不能用变形。这条已和"禁止改 `border-width`"并列写进 §3.1 与 W2 禁止项。

### 10.11 v1.9 r3 —— visual 的两处 DOM 结构级变更（都会影响 W2 / W4 的写法）

| # | 变更 | 落地 |
|---|---|---|
| 1 | `c-mark` 从"一标记一个 button"（两个 10px 半区）改成 **"一步一个 button"**（整列宽 × 20px）。形状载体先在 `::before` / `::after`（r3），**r5 又改为 2 个 `<i class="c-mark__shape">` 子元素**（见 §10.12） | §3.5 结构要点：`<button class="c-mark" data-kinds="diag ask">` 内部固定 2 个 `<i class="c-mark__shape" data-kind>`（`aria-hidden`）；`[` / `]` 改为"跳到下一个有标记的步、同一步不重复停留"（取消"诊断优先于提问"）；W4 验收话术同步 |
| 2 | `selected` 撤四角刻线，环色在判分上下文换近黑，作用域是**整个 `data-ctx="graded"`** 而不是"仅 error 格" | §3.1：`.c-matrix[data-ctx="graded"] .c-byte.is-selected { --accent-ring: var(--ink-1) }`；`.c-matrix` 根节点加 `data-ctx`；撤的范围写明"只停用字节格里的选中格，容器活动区刻线与 B 区输入框 focus 刻线保留" |

**这两条为什么必须写进"承接记录"而不是直接改正文**：它们是**结构级**的（DOM 节点数、伪元素额度、快捷键语义），不是换色值。结构级变更一旦只改一处、漏一处，症状是"某个状态下标记消失"或"点第 13 步跳到第 14 步"，都属于要等到演示现场才发现的那类。

**记两条从这轮提炼出来的通用判断**：

1. **`::before` / `::after` 是会被占满的资源，所以别把"内容"放进去**。r3 为了让"一步只用一个 button"成立，把圆和方都塞进伪元素，代价是这个元素永久失去装饰额度（hover 环、focus 刻线、纹理都得绕）；r5 换成 `<i>` 子元素后额度重新打开。通用判断：**伪元素适合放"可有可无的装饰"，不适合放"必须在图例里被复用的形状"** —— 因为伪元素没有 DOM 节点，别处复用不了。
   > 但换成子元素不等于可以随便加：`.c-mark` 内**只允许这 2 个 `<i>`**，且它们的位置只由 `data-kind` 决定。多一个节点就多一处能和轨道对不齐的地方。
2. **热区尺寸的"合格线"是判定圈，不是矩形面积**。两个 10px 高的相邻热区，面积加起来等于一个 20px 的，但以各自主中心画 24px 判定圈会互相覆盖 —— **两个都不达标**。"合起来够大"和"各自够大"不是一回事，这条对今后任何"拆半区"的方案都成立。

### 10.12 v1.9 r5 —— 演示态格边框主从修正 + 七处连带（已全部落地）

这一轮的起点是我报给 visual 的三个问题，结论是**两处真错 + 一处规范缺口 + 一处设计不完备**，落下来牵动 8 条。逐条留档，因为每一条都会影响 W1/W2/W4 的验收。

| # | 事项 | 终稿 | 落地位置 |
|---|---|---|---|
| 1 | **演示态格边框色** | `--bd-color` 取 **`--rule-region-ink`**（演示 0.545 / 4.6:1），**七态一律含 `done`**。`--line-default` 0.760 只服务非格子结构线（控件边 / 表头框 / 分区细线） | §3.1 代码块 + 七态表；V14 允许取值集合；§10.6 第 1 条 |
| 2 | **`downstream` 演示值** | `--st-downstream-border` 的演示覆盖 = `var(--rule-region-ink)`（0.545）。**若指向 0.760，它会比邻居更浅 —— 那正是"没画完"的读法** | §3.1 `downstream` 四通道表 + 演示态说明；§10.6 第 4 条 |
| 3 | **`done` 的左下缺口机制** | 用 `data-corner="bl"` 那个元素**压一块 `--paper-0` 方块**（边长 `calc(var(--flag-size)*2)`，**不许写死 5px**），**不许断 `border`** —— 断边会随 `border-color` 变化而失效（`downstream` 降级、判分上下文换环色都会碰边框），缺口会莫名消失 | §3.1 元素名对齐 + §7.2 W2 禁止项 |
| 4 | **`c-mark` 形状载体** | 2 个 `<i class="c-mark__shape" data-kind="diag\|ask" aria-hidden>` 子元素；`.c-mark` 自身撑热区（`width:100%` × `--tl-mark-band`）。**定位只写在 `.c-mark > .c-mark__shape`，基类不带 `position`** | §3.5 HTML/CSS + 三条要点；§10.2 图例条 |
| 5 | **图例复用同一元素** | 图例里写 `<i class="c-mark__shape" data-kind="diag">`，与轨道上完全同一个元素 —— "像素级一致"从**两处写一样**升级成**结构上天然只有一个来源** | §10.2 图例条 |
| 6 | **DEV 断言（visual 收进正文）** | `getComputedStyle(cell).borderTopColor !== getComputedStyle(cell).color` —— **`border-color` 拿到不存在的 token 不报错，会静默回落到 `currentColor`**，那一格反而最黑。这条挡的是"token 改名后某处没跟上"，本轮 `--st-downstream-border` 就差点是这种事故 | §3.1 禁令第 2 条（W1 落地） |
| 7 | **`is-error` 闸门跟随承载者** | 折角从 `.c-byte::after` 变成真元素 `__corner` 后，闸门必须改成 `.c-byte.is-error:not(.is-downstream) .c-byte__corner[data-corner="br"]`；`≠` 收窄到 `[data-kind="neq"]`。**闸门挂在旧的伪元素上不会报错，只会静默放过整个错误态** | §3.1 产品级红线代码块 |
| 8 | **第六通道 `bar`（ux 提议，采纳）** | 左边缘 3px 竖条单列为一条通道：2 值 `key \| idle`、**只有 `key` 一个候选、无优先级、不进角位截断**。理由：它不属于 fill/bd/txr/corner/text 任何一条；不单列的话，下一个要给 `key` 加东西的人会"发现通道满了"然后塞进 fill | §3.1 六通道 owner 表 + §7.2 第 13 条 + §10.3 UX-8 |

**这一轮真正的教训（写给下一个人，也写给下一个人看的那份 token 表）**：

> **数值相等是两个 token 的巧合，不是它们的关系。** `--line-default` 与 `--rule-region-ink` 在常规块都是 0.845，于是"格线取哪个都一样"看起来成立；演示块一分叉（0.760 / 0.545），错误立刻变成视觉缺陷，但**代码里没有一个字变了**。所以：**凡是要靠"同值"做的推断，引 token 名，不引数值。** 这条与 §8.1 引用纪律同源 —— 前者约束"引用什么"，后者约束"怎么引用"。

**层级不能靠变淡（补一条视觉给的定性）**：格子与区域分隔线现在演示态同色同宽了，层级改由**留白（区域 16px vs 格间 6/10px）+ 标签 + 位置**承担。一句话：**"靠更淡来分层级"在投影上等于"没有层级"。**

**第三条教训（本轮第 7 条带出来的）：改元素的承载方式，必须搜一遍挂在它身上的选择器。** 折角从 `::after` 搬到真元素，CSS 语法一字未错、构建不报错、DevTools 里那个元素也确实渲染了 —— 只是**闸门保护的是一个已经不存在的渲染者**。这类失效的共同特征：**选择器合法、目标存在、效果为零**。它和"引用了不存在的 token 静默回落 `currentColor`"是同一个家族：
> **CSS 的失效几乎都是静默的。** 所以本项目每加一条"为了兜住某个事故"的防御规则，都要顺手写一句**"如果这条失效，症状是什么"** —— 症状能被看见，规则才算真的生效。V14 与 §3.1 的 DEV 断言就是按这条要求写的，它们能存在，靠的不是纪律，是断言。

---

## 11. 接口契约附录（后端照此实现）

> 本节是**唯一**的接口口径来源，正文其他位置的路径若与此处不一致，以本节为准。前端按此实现，**不做任何算法复算**。

### 11.1 通用约定

| 项 | 约定 |
|---|---|
| Base path | 全部 `/api/*`，nginx 反代时 **关闭代理缓冲**（SSE 必需），`proxy_read_timeout 60s` |
| 内容类型 | 请求/响应 `application/json; charset=utf-8`；SSE 为 `text/event-stream` |
| 字节表示 | 数组元素为 `0..255` 整数（**不是 hex 字符串**，避免解析开销与大小写不一致）；16 元素数组一律**列优先**（`arr[r+4c]`） |
| hex 字符串 | 仅用于用户输入/导出，统一小写、无 `0x`、无空格 |
| 错误模型 | 非 2xx 一律 `{ "error": { "code": "…", "message": "…", "field": "plaintext\|key\|null" } }` |
| 幂等 | `POST /api/aes/trace`、`POST /api/quiz/submit` 幂等（同样入参返回同样结果，便于重试） |

### 11.2 `POST /api/aes/trace` —— 生成全量 trace

**请求**
```jsonc
{ "plaintext_hex": "3243f6a8885a308d313198a2e0370734",
  "key_hex":       "2b7e151628aed2a6abf7158809cf4f3c",
  "key_bits": 128,              // 128 | 192 | 256
  "direction": "encrypt" }      // encrypt | decrypt
```
**响应 200**
```jsonc
{ "trace_id": "t_7f3a91",        // 前端后续 tutor/quiz 都带它，避免重复传上下文
  "key_bits": 128, "direction": "encrypt",
  "rounds": 10, "step_count": 24,
  "key_schedule": [[43,126,21,22], [40,174,210,166], /* … 共 44 词（192→52，256→60） */],
  "steps": [
    { "index": 0, "round": 0, "op": "add_round_key",
      "state_before": [50,136,49,224, /*16*/],
      "state_after":  [25,159,61,78, /*16*/],
      "changed": [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15],
      "key_indices": [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15],
      "key_words": [0,1,2,3] },
    { "index": 1, "round": 1, "op": "sub_bytes",
      "state_before": [/*16*/], "state_after": [/*16*/],
      "changed": [0,5,10,15], "key_indices": [], "key_words": [] },
    { "index": 2, "round": 1, "op": "shift_rows",  "…": "…" },
    { "index": 3, "round": 1, "op": "mix_columns", "…": "…" },
    { "index": 4, "round": 1, "op": "add_round_key","…": "…" }
    /* … 末轮无 mix_columns，故 128 位共 1 + 9×4 + 3 = 40? 否：24 = 1+9*4+1+... 
       以 step_count 为准，前端不推导 */
  ]
}
```
**字段与前端映射（实现依据）**

| 字段 | 前端落点 |
|---|---|
| `trace_id` | `useEngineStore.traceId`，后续 `ask` / `submit` 必带 |
| `key_schedule` | `useEngineStore.keySchedule`（`shallowRef`，不深代理） |
| `steps[]` | `useEngineStore.trace`（`shallowRef`） |
| `step.changed` | `is-changed` 判定 / C2 摘要句 / 列混合列号推导 |
| `step.key_indices` + `key_words` | `is-key` 判定 + C5 轮密钥轨 |
| `step.state_after` | `useMatrixWriter.write(values, changed)` 的 `values` |
| `step.round` + `op` | C1 步标题、时间轴轮分段（**由数据驱动，禁止写死 24/10**） |

**超时与降级**：8s 未返回 → `status='offline'`，前端用内置 `engine/trace.ts` 只算**内置标准向量**（离线演示专用，**不进判分**）。

### 11.3 `POST /api/tutor/ask` —— SSE 流式辅导

**请求**
```jsonc
{ "trace_id": "t_7f3a91",
  "step_index": 13,
  "question": "这一步为什么这么做？",
  "client": { "follow": true } }
```
> **设计要点**：请求只带 `trace_id + step_index`，**不把 16 个字节值再传一遍**。后端已有 trace，天然一致；若前端把数值也传一遍，就出现了"两处数值可能不一致"的新风险。离线无 `trace_id` 时才允许带 `context` 内联（后端按无状态处理）。

**响应 `text/event-stream`**，四种事件：

```
event: meta
data: {"quotes_values":true,"source":"model","cache":false,"step_label":"R2 · MixColumns · C[1]"}

event: token
data: {"t":"这一步对每一列"}

event: token
data: {"t":"做了 GF(2^8) 上的矩阵乘法，"}

event: done
data: {"finish":"stop","tokens":238}
```
```
event: error
data: {"code":"upstream_timeout","message":"模型超时"}
```

| 事件 | 前端行为 |
|---|---|
| `meta` | 写 `quotesValues` / `cacheHit` / `source`；带 `quotes_values:false` 时渲染「通用讲解（未引用当前数值）」+「带上这一步的数据重问」按钮 |
| `token` | `appendToken()`，**不进 aria-live**（A7），光标闪烁 |
| `done` | `phase='done'`，整段一次性进 live region；`cacheHit` 时**必须整段直出不做打字机** |
| `error` | 保留用户问题、显示一句原因 + 重试；不弹窗 |

**双阈值**：首字 3s 未到 → 本地立即显示「先看本地要点」；总 20s → `abort()` + 换本地模板 + 标「离线讲解」。客户端超时用 `AbortController`，**不用后端超时**（后端超时无法保证前端在 20s 收到信号）。

### 11.4 `POST /api/quiz/submit` —— 判分（**唯一判分入口**）

**请求**
```jsonc
{ "item_id": "q_042",
  "answer_hex": "3925841d02dc09fbdc118597196a0b32",
  "plaintext_hex": "3243f6a8885a308d313198a2e0370734",
  "key_hex": "2b7e151628aed2a6abf7158809cf4f3c",
  "key_bits": 128 }
```
**响应 200**
```jsonc
{ "summary":  { "total_bytes": 12, "wrong_count": 3 },
  "first_diff": { "round": 4, "step": "mix_columns", "byte_index": 7 },
  "propagated": [8, 9, 10, 11, 12, 13, 14, 15],
  "input_mismatch": null,
  "expected_ciphertext": "3925841d02dc09fbdc118597196a0b32" }
```
**`input_mismatch` 非空时的形状**（可空对象，**不是 boolean**）：
```jsonc
"input_mismatch": { "field": "key", "char_index": 6, "expected": "hex" }
```
- `field` ∈ `'plaintext' | 'key' | 'both'`；`char_index` 是**从 0 开始的字符下标**（不是字节下标）；`expected` 目前只有 `'hex'`，将来可扩成具体字符。
- **正常时必须是 `null`，不是 `false`、也不能省略** —— 这样前端只有一种判定写法 `if (resp.input_mismatch) {...}`，不会出现 `undefined / false / null` 三种空值混用。
- `field === 'both'` 时前端两个输入框同时标红，`char_index` 只对 **key** 有效；**明文字段由前端按同一规则（首个非 hex 字符的位置）自行定位**，不必后端再算一遍。这条要写进 `HexInput` 组件的注释，否则后面会有人以为明文没有定位能力。
- **前端不需要后端回传"你写的是什么字符"**：拿到 `char_index` 后切片本地输入即可，文案就能写成「你的密钥第 7 个字符不是十六进制数」。

| 字段 | 前端落点 | 说明 |
|---|---|---|
| `summary.total_bytes / wrong_count` | 判分条文案「16 个字节中 3 个不符」 | — |
| `first_diff.{round,step,byte_index}` | `useQuizStore.errorLoc` + `is-error`（**通常只 1 格**） | 步名用 `sub_bytes/shift_rows/mix_columns/add_round_key`，前端映射成人话 |
| **`propagated[]`** | `useQuizStore.propagated`（Set）→ `is-downstream` | **前端算不出来**：判断"哪些字节受这个错误影响"必须知道全量中间态。这是第 7 态的唯一数据源 |
| **`propagated[]` 派生** | `first_diff.step === 0 && propagated.length === 16` → **整段错版式**（1 格 error + 15 格 downstream + 四角括 + 标签），否则常规定位版式 | **不需要新字段**，不要为此让后端加 `whole_block_wrong` 之类的布尔量 |
| `input_mismatch` | 非 `null` 时**该题不计入** `stats.done / stats.correct` 分母，并渲染字段级提示 | 学生录错明文/密钥不是算法错，否则正确率被污染 |
| `expected_ciphertext` | 「查看正确答案」按需展示 | 默认不显，避免直接给答案 |

**边界约定（前端必须能扛）**：`propagated` 缺失或非数组 → 按 `[]` 降级（只标 `is-error`，不标 downstream）+ `console.warn`；`first_diff` 为 `null`（全对）→ 不进入错误分支。**前端不复算、不校验、不对账**——单实现时判分与矩阵天然一致，双实现才会出现"两边不一样"。

### 11.5 `POST /api/events` —— 埋点批量上报

```jsonc
{ "session_id": "s_9c21",
  "items": [
    { "type": "step_revert",   "step_index": 11, "at": 1762012345678 },
    { "type": "tutor_ask",     "step_index": 13, "at": 1762012355120, "payload": { "cached": false } },
    { "type": "diag_accepted", "step_index": 15, "at": 1762012360000, "payload": { "kind": "misread_priority" } }
  ] }
```
批量策略：≥10 条或 ≥10s 触发；`visibilitychange=hidden` 与 `beforeunload` 强制 flush（`sendBeacon`）。**诊断历史与时间轴标记由本地 `useDiagnosisStore.history` 驱动**，不依赖上报成功。

### 11.6 前端禁止事项（接口层面）

- 禁止在前端做任何 AES 计算用于判分或校验（`engine/` 仅限离线演示内置向量）。
- 禁止把 16 字节数值随 `ask` 请求再传一遍（一致性风险）。
- 禁止用后端返回的 `correct` 之类的布尔量代替 `first_diff + propagated`（三层反馈会退化成一层）。
- 禁止前端推导 `step_count` 或轮数（AES-128/192/256 不同，一律读响应）。

