# CipherLens · 华为 CodeArts（码道）分功能开发提示词手册

> 配套文档：`docs/` 下 8 份设计规格。本手册**不重复**设计内容，只负责「怎么跟平台说话」。
> 版本 v1.0 · 2026-11-02

---

## §0 怎么用（三条铁律，违反任何一条都会返工）

**铁律一：一次只开一个功能点。**
本手册把 4 周工作量拆成 **24 个功能点**。每个功能点 = 一次对话 = 一条提交 = 一次推送。**不要把 F1 和 F2 粘在一条消息里**——平台 Agent 在长任务里会自己发明结构，改起来比重新写贵。

**铁律二：每条提示词开头先粘「A 上下文卡」。**
CodeArts 的会话是长上下文，但记忆会稀释。每开一个新功能点，先粘 §1 的上下文卡（30 行），再粘功能点提示词。这比一次粘 8000 行规范有效得多——**它只需要知道去哪查，不需要把所有内容记住**。

**铁律三：不合规就停下，不要让它"顺手修一下"。**
一旦你看到它开始 `npm install axios` / 引入 UI 库 / 改 `border-width` / 在前端写判分逻辑，立刻打断，用 §10 的纠偏提示词拉回。放任它"顺手"一次，后面要花三倍时间拆。

---

## §1 提示词 A · 上下文卡（每个功能点前都粘一次）

```text
【身份】你是 CipherLens 的唯一实现 Agent，在华为云 CodeArts 里工作。本项目同时是高校实训交付物与华为云开发者大赛参赛作品，所有对话与提交都会作为评审留痕。所以：代码要能跑、能复现、能被别人读懂，不要炫技。

【仓库】D:\project\CipherLens。规格文档在 docs/ 下，只读，不要修改。
查东西按这个顺序，不要全文通读：
- 目录结构 / 组件树 / store → docs/CipherLens-前端实现规格与Coding-Agent提示词-v1.9.md §1 §2
- 字节格 DOM 与七态判定 → 同上 §3.1
- 动效参数（M1–M29）→ 同上 §4
- 性能预算与检测方法 → 同上 §5
- 接口契约 → 同上 §11
- 七态各自长什么样 → docs/CipherLens-视觉设计规范-v1.2.md §2.3
- 设计令牌（颜色/间距/时长）→ 同上 §10
- 交互阈值与 19 条口径 → docs/CipherLens-信息架构与交互规格-v1.3.md §8.4
- 五条冻结口径与 7 条验收 → docs/CipherLens-视觉设计流程与Coding-Agent提示词-v1.0.md §4.6 §7.1

【技术栈已锁定，不可替换】
Vue 3.5 + Vite 5 + TypeScript + Pinia 2 + Vue Router 4；后端 FastAPI + SQLite。
禁止引入：React / Next / Nuxt / Element Plus / Ant Design / Naive UI / Tailwind / GSAP / axios / 任何 UI 组件库或动画库。CSS 手写，动画只用 CSS transition / keyframes 与 rAF。HTTP 用原生 fetch。

【五条硬约束（违反任一条都要推倒重来）】
1. 字节格 border-width 七态恒定 1px（演示态恒 2px），只改 border-color；加粗一律 box-shadow: inset。
2. 字节格边框取 var(--rule-region-ink)，永不取 --line-default（两者常规档都是 0.845 看不出差别，演示档分叉成 0.545 / 0.760，取错就在投影上掉到 2.9:1）。
3. 矩阵 --cell-gap: 6px（演示 10px）是底线。每格边框是它自己的完整矩形，禁止改成容器统一画线。
4. 格子绝不位移、绝不缩放、绝不内缩。状态只改颜色、纹理、描边、角标。
5. 判分在后端，前端只渲染。禁止前端复算判分、禁止前端推导步数。

【工作方式】
- 我说「开始 F<N>」你再动手。之前只读、只回答，不写代码。
- 一次只做一个功能点，不预建"以后可能用到"的文件、空组件、空 store。
- 每完成一个功能点：先自检、再提交、再推送，然后停下等下一句。
- 不确定的地方先问我，不要"合理推测"后直接实现。

【禁止】
- 禁止修改 docs/ 下任何文件。
- 禁止为了让验收好看而削弱功能（如延迟挂载矩阵、隐藏时间轴）。
- 禁止用 !important 解决样式冲突。
- 禁止提交未删除的 console.log（DEV 断言分支除外）。

收到请只回一行：「上下文已就绪，等待 F<N>」，不要展开。
```

---

## §2 提示词 B · 固定收尾（每个功能点做完都粘一次）

```text
【收尾：自检 → 提交 → 推送】

第一步 · 自检。逐条跑下面这些验收项，把结果列成表：
| 验收项 | 结果 | 证据 |
证据要能核：数字、文件路径、或在页面上看得到的东西。不接受「已实现」「正常」。

第二步 · 有失败项就不要提交。先修；修不动就停下，说明卡在哪一条、你试过什么。

第三步 · 全部通过后执行（在 D:\project\CipherLens 下）：

  git add -A
  git commit -m "<按 §11 的提交信息规范写>"
  unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
  git push origin main

提交信息格式：<type>(<scope>): <做了什么> —— 通过 F<N> 验收 <编号列表>
例：feat(engine): 实现 AES 四步变换与密钥扩展 —— 通过 F2 验收 1/2/3

第四步 · 回报四行：
1. commit hash（前 7 位）
2. 改动文件数与新增行数
3. 有没有留下 TODO / 已知缺陷（有就直说）
4. 下一个功能点建议做什么、为什么

推送失败时不要重试超过一次，把完整报错贴给我。
```

---

## §3 功能点清单（24 个，按依赖排序）

| # | 功能点 | 依赖 | scope | 验收要点 |
|---|---|---|---|---|
| F0 | 脚手架与令牌落地 | — | chore | build 通过、五区空壳可见 |
| F1 | S 盒与逆 S 盒 | F0 | engine | 256 项对 FIPS-197 表 |
| F2 | AES 四步 + 密钥扩展 | F1 | engine | 128/192/256 全通 |
| F3 | 全量 trace 生成 | F2 | engine | C.1 向量逐字节对 |
| F4 | 路由壳 + 五区静态布局 | F0 | layout | 五区尺寸对 |
| F5 | MatrixStage + ByteCell 静态 16 格 | F3 F4 | matrix | 列优先、单 rAF 写 |
| F6 | 键盘骨架（roving + 5 键） | F5 | a11y | 一个 Tab 位 |
| F7 | ByteCell 七态静态样式 | F5 | matrix | 七态可手动切换 |
| F8 | SubBytes 动效通道 | F7 | motion | 一秒可辨 |
| F9 | ShiftRows 动效通道 | F8 | motion | 四向回绕正确 |
| F10 | MixColumns 动效通道 | F9 | motion | 同列零 stagger |
| F11 | AddRoundKey 动效通道 | F10 | motion | 密钥层时序 |
| F12 | Timeline 四轨 + 双形状标记 | F7 | timeline | 圆/方不混 |
| F13 | TransportBar + 播放节奏 | F12 | playback | 倍速不改动效时长 |
| F14 | reduced-motion + 灰度回归 | F8–F13 | a11y | 信息不丢 |
| F15 | 演示态参数集 | F14 | theme | 格线 0.545 |
| B1 | FastAPI 骨架 + trace 接口 | F3 | api | 与 engine 同结果 |
| B2 | SSE 辅导接口 | B1 | api | 流式 + 可中断 |
| B3 | 判分接口 + 埋点 | B2 | api | 三层反馈字段 |
| F16 | useSSE + 辅导面板主链路 | B2 | tutor | 引用真实步值 |
| F17 | 辅导 11 态 + 降级 | F16 | tutor | 断网有兜底 |
| F18 | 认知诊断批注 | F17 | diagnosis | 20s 阈值 |
| F19 | 练习页 + 三层反馈渲染 | B3 F11 | quiz | 只 1 格红 |
| F20 | 记录页三态 | F19 | records | <3 题不出结论 |
| F21 | 性能预算达标 | F20 | perf | 三项预算全绿 |
| F22 | 无障碍收尾（22 键 + 表格视图） | F21 | a11y | 纯键盘全链路 |
| F23 | URL 状态 + 错误边界 | F22 | ux | 刷新可恢复 |
| F24 | Docker 部署 + E2E 冒烟 | F23 | deploy | 一条命令起全栈 |

---

## §4 阶段 0 · 脚手架

### F0 · 脚手架与设计令牌落地

```text
【本功能点】搭出能跑的空壳，并把视觉令牌落成 CSS 变量。只做骨架，不做任何业务。

【必读】前端规格 §1.1（目录）、§1.2（组件树）；视觉规范 §10（令牌清单）。

【做】
1. Vite + Vue3 + TS 初始化（npm create vite@latest . -- --template vue-ts），删掉模板自带样式与 HelloWorld 组件。
2. 装 pinia、vue-router，配好 src/router/index.ts 五条路由（Home / Workbench / SBox / Practice / Records），后三条先给只有标题的空视图。
3. 按 §1.1 建目录（components/region-a..e、composables、stores、engine、types、canvas、svg、views、styles、data）。
4. 把视觉规范 §10 的全部令牌写进 src/styles/tokens.css，分三块：:root（常规）、[data-density="compact"]、[data-mode="present"]。**令牌名一个字都不能改**，值照抄。
5. src/styles/base.css：reset、字体栈、tabular-nums、.sr-only、[data-motion="reduced"] 占位。
6. WorkbenchView 搭五区静态布局（A 上下文条 56px / B 输入区 280px / C 舞台 flex / D 时间轴 104px / E AI 栏 380px），每区只放一个带区名的占位块，纯 CSS Grid。

【硬约束】
- 令牌只能用 CSS 变量，组件内出现 #rrggbb 或写死 px 间距即不合格。
- 圆角 ≤ 3px，零渐变，零毛玻璃，分区只用 1px 发丝线，阴影只允许浮层用 2 个。
- 不要装任何 UI 库、图标库、CSS 框架。

【验收】
1. npm run build 通过，零 TS error，初始路由 JS gzip < 150KB（贴 dist 产物大小）。
2. npm run dev 打开 Workbench，五区可见、尺寸与设定一致（贴截图 + 每区实测宽度）。
3. tokens.css 与视觉规范 §10 逐条对照，列出「规范里有 / 我写了」的对账表，缺一不可。
4. 把 document.documentElement 的 --paper-0 打印出来，确认是规范里的值。

【禁止】预建空 store、空 composable、空组件；复制模板自带的 logo 与样式。
```

---

## §5 W1 · 引擎与骨架

### F1 · S 盒与逆 S 盒

```text
【本功能点】实现 S 盒、逆 S 盒及其查表函数，并用 FIPS-197 原表校验。纯函数，零 Vue 依赖。

【必读】前端规格 §7.1 硬约束 2（engine 内禁止 import 'vue'）。

【做】src/engine/sbox.ts，导出 SBOX（256）、INV_SBOX（256）、subBytes(bytes)、invSubBytes(bytes)。
S 盒用 FIPS-197 Figure 7/14 的原始表，**不要用代码现算**（现算容易在仿射变换那一步写错且难查）。
逆 S 盒必须由 S 盒程序生成并断言互逆，不要手抄第二张表。

【硬约束】
- engine/ 下任何文件禁止 import 'vue' —— 它要能在 node 里裸跑单测。
- 用 Uint8Array，不用 number[]。
- 不要做缓存/记忆化，256 项查表已经够快。

【验收】
1. SBOX[0x00] === 0x63，SBOX[0x53] === 0xed，INV_SBOX[0x63] === 0x00（贴运行结果）。
2. 遍历 0..255：INV_SBOX[SBOX[i]] === i 全部成立（贴断言通过的输出）。
3. 单测文件 src/engine/sbox.spec.ts，vitest run 全绿（贴输出）。
4. subBytes 对 16 字节输入返回新 Uint8Array，不修改入参（贴一条深比较断言）。

【禁止】把 S 盒写成二维数组再展平；在 engine 里引入任何第三方库。
```

### F2 · AES 四步变换与密钥扩展

```text
【本功能点】实现 AES 一轮的四个步骤与密钥扩展，支持 128/192/256。

【必读】前端规格 §7.1 硬约束 2；AES 标准 FIPS-197 §5。

【做】src/engine/aes.ts：
- addRoundKey(state, roundKey)：异或。
- shiftRows(state) / invShiftRows(state)：**按列优先存储**的 16 字节状态，row r 左移 r 位。
- mixColumns(state) / invMixColumns(state)：GF(2^8)，xtime 实现乘 2，乘 3 = xtime(x)^x。
- keyExpansion(key)：返回 w[4*(Nr+1)]，含 RotWord / SubWord / Rcon。
- 常量：AES-128 Nr=10/44 字，AES-192 Nr=12/52 字，AES-256 Nr=14/60 字，Rcon 到 10 项。

【硬约束】
- 状态矩阵一律用「长度 16 的 Uint8Array，列优先」：index = col*4 + row。这个约定写进文件头注释，后面三个月的每次调用都靠它。
- 所有变换返回新数组，不原地改。
- 不要引入任何加密库（crypto-js / node:crypto 都不行，这是教学项目，算法必须是自己的）。

【验收】
1. 贴出 FIPS-197 附录 B 的密钥扩展示例：AES-128 密钥 2b7e151628aed2a6abf7158809cf4f3c，w[4]..w[7] 与标准一致。
2. AES-128/192/256 各跑一次 keyExpansion，字数分别为 44/52/60（贴长度断言）。
3. shiftRows 对 [0..15] 列优先输入，输出贴出来，逐位置说明谁移到哪。
4. mixColumns 对 [0xdb,0x13,0x53,0x45] 算出 [0x8e,0x4d,0xa1,0xbc]（贴结果）。
5. vitest run 全绿，覆盖 128/192/256 三档密钥扩展 + 四步正反变换。

【禁止】用查表代替 xtime（乘 2 必须是位运算，这是教学要展示的）；把行/列顺序搞混后靠转置打补丁。
```

### F3 · 全量 trace 生成

```text
【本功能点】把「一次加密的每一步中间态」生成成结构化 trace，供前端播放器消费。这是整个项目的数据底座。

【必读】前端规格 §11.2（trace 结构契约）§7.1 硬约束 2。

【做】
src/engine/trace.ts：buildTrace({ plaintext, key, mode }) 返回：
{ trace_id, ciphertext, steps: Step[], keySchedule: Uint8Array[], meta }
Step 至少含：step_index、round、op（subBytes/shiftRows/mixColumns/addRoundKey/keyExpansion）、state_before(16)、state_after(16)、changed_idx(number[])、round_key_idx(number[])、label（人类可读，如「第 2 轮 列混合」）。
共 1(初始 addRoundKey) + 9*(4步) + 1(末轮3步) = 38 个 step（AES-128），末轮无 mixColumns。

src/engine/diff.ts：diffState(before, after) 返回 { changed: number[], unchanged: number[] }。
src/engine/vectors.ts：内置 FIPS-197 附录 C.1/C.2/C.3 三组向量。

【硬约束】
- trace 只生成一次，不可变；后续任何地方都不得再改它（前端用 shallowRef 存）。
- changed_idx 必须由 diff 算，不要手写。
- trace_id 用内容哈希（plaintext+key+mode），保证同样输入出同样 id，便于缓存。

【验收】
1. 载入 C.1 向量（key=000102...0f，plaintext=00112233...ff），ciphertext 必须等于 69c4e0d86a7b0430d8cdb78070b4c55a（贴实际输出）。
2. steps 数量与每步 op 序列贴出来，与实际轮结构一致（第 10 轮不得出现 mixColumns）。
3. 任取第 13 步，changed_idx 与 state_before/after 逐字节手算核对 3 个位置（贴过程）。
4. 三组向量全过，vitest 全绿。
5. 同一输入连续生成两次，trace_id 相同（贴两次的 id）。

【禁止】把 trace 做成 class 实例（要能 JSON 序列化，接口要传它）；用 JSON.parse(JSON.stringify()) 做 diff。
```

### F4 · 五区静态布局

```text
【本功能点】把 F0 的占位块换成真实分区结构（先不填内容），并让 A/B/C/D/E 的尺寸、分隔线、滚动行为正确。

【必读】交互规格 §2.1–2.6（五区职责）；视觉规范 §10（间距令牌）。

【做】
- App.vue 挂 data-density / data-mode 到 html 或 #app。
- WorkbenchView：CSS Grid 五区（A 顶栏 56px / B 左 280px / C 中 flex / D 底 104px = 控制行 40 + 时间轴 64 / E 右 360px）。
- 分区边界只用 1px --line-hairline，不用背景色差分区。
- C 区必须 min-width: 0（否则 flex 子项会被内容撑破，16 格矩阵溢出）。
- 窗口 < 1120px 时 E 区折叠为 48px（[data-ai="collapsed"]），只留图标条。

【硬约束】
- 禁止用 position: fixed 布局五区（后续抽屉与浮层会打架）。
- 禁止给 C 区设固定宽高，它必须能跟着窗口缩放并保持正方形比例。
- 折叠不带过渡动画（W4 才处理），这一版是瞬时的。

【验收】
1. 1920 / 1440 / 1120 / 1024 四个宽度各截一张图，五区不重叠、不溢出（贴 scrollWidth === clientWidth 的断言）。
2. C 区在 1024 宽下矩阵容器仍是正方形（贴 offsetWidth/offsetHeight）。
3. 分区线颜色实测是 --line-hairline（贴 computed value）。
4. 全局不出现横向滚动条（document.body.scrollWidth === clientWidth）。

【禁止】用 JS 监听 resize 算尺寸（W1 后续用 ResizeObserver，这里先用纯 CSS）。
```

### F5 · MatrixStage + ByteCell 静态 16 格

```text
【本功能点】渲染 4×4 字节矩阵，接 trace 数据，用单次 rAF 写入数值。这是全项目最核心的一个组件，做错要重来。

【必读】前端规格 §3.1（字节格 DOM 与七态判定，含 owner 表）、§2.7（16 格如何订阅而不重渲染）。

【做】
- MatrixStage.vue：role="grid"、aria-label、.c-matrix__body > .c-matrix__grid > 16 个 ByteCell。
- **16 个格子 DOM 顺序必须列优先**（c0r0,c0r1,c0r2,c0r3,c1r0…），配 grid-auto-flow: column。这样 DOM 下标 === AES 字节下标，不需要映射表。
- ByteCell.vue：单个格子，显示 hex 值 + 十进制上标 + 行列表角标位。用 data-bd / data-txr 两个单值属性承载状态（W2 才用，现在先留好）。
- useMatrixWriter.ts：唯一的写值通道。ref 一个 pending，在 1 个 rAF 内遍历 16 格，写 textContent 与 aria-label。
- **必须内置写批次断言**：flush 前 batches=0，结束时 batches++；DEV 下 if (batches > 1) console.error('[MULTI-BATCH] 一帧内写了 %d 次')。这条断言留到 W4，用来防"后来的人顺手改回响应式绑定"。
- aria-label 双写：如「第 2 行第 2 列，字节 5，值 0x63，十进制 99」。

【硬约束】
- trace 用 shallowRef 存，禁止 ref()/reactive() 包裹 steps 与 keySchedule。
- 16 格的 hex 值**禁止在模板里绑表达式**，禁止每格建 computed。
- 格子 border: 1px solid var(--rule-region-ink)，box-sizing: border-box，--cell-gap: 6px。
- 禁止 v-for 的 :key 用 index 拼时间戳，固定 :key 0..15。

【验收】
1. 载入 C.1 向量，矩阵 16 格显示的 initial state 与标准一致（贴 4×4 对照表）。
2. 连按 30 次 →（先临时加一个调试按钮），控制台**零** [MULTI-BATCH] 输出，并贴 batches 计数（每步必须恰好 1）。
3. 人为把 useMatrixWriter 里的循环改成两次 flush，确认断言会报错（证明断言真的有效），然后改回来。
4. 按一次 Tab 进入矩阵，焦点落在第 1 格（贴 activeElement 的 aria-label）。
5. DPR=2 与 DPR=1 各截图，1px 边框无模糊、无 2px 粗边。
6. 16 格的 DOM 顺序打印出来，确认是列优先。

【禁止】把 hex 拆成单字符 span（W2 才做）；用 v-for + :key="currentStep" 重建 16 格；在 @click 里直接改 DOM 再改 store。
```

### F6 · 键盘骨架（roving tabindex + 5 键）

```text
【本功能点】让矩阵只占 1 个 Tab 位，方向键在 4×4 内移动，边界不跨行。

【必读】交互规格 §8.4 口径表；前端规格 §7.1 硬约束 5。

【做】
- useRovingGrid.ts：维护 activeIndex(0..15)，DOM 顺序即列优先。
- 只有 activeIndex 那格 tabindex="0"，其余 tabindex="-1"。
- 方向键：上 = index-1，下 = index+1，左 = index-4，右 = index+4（因为列优先）。边界处不环绕、不跨行。
- useHotkeys.ts：先接 Space（播放/暂停占位）、ArrowLeft/Right（上一步/下一步占位）、Home/End（首/末步占位）。输入框聚焦时全部失效。

【硬约束】
- 方向键的语义必须和视觉方向一致（按「左」焦点真的往左走），不是按数组下标加减。
- roving 不改变选中态（is-selected 是另一件事，W2 再做）。
- 焦点移动不得滚动页面（scrollIntoView 用 block:'nearest'，或干脆不滚）。

【验收】
1. 按一次 Tab 从页首进入矩阵，再按一次 Tab 离开矩阵到下一个可聚焦元素（全程只停 1 次，贴 Tab 序列）。
2. 在角落四格各按一次朝外的方向键，焦点不动（贴 4 次 activeElement 对比）。
3. 从 c0r0 按「右」4 次，焦点到 c3r0（列优先下 +4 是换列），确认视觉上确实是往右（截图标注）。
4. 在输入框里按方向键，焦点不跳（贴 activeElement）。

【禁止】给 16 格都写 tabindex="0"；用 document.activeElement 手动 blur 来"实现"Tab 位。
```

---

## §6 W2 · 矩阵与动效（最容易超期的阶段）

> 本阶段 8 个功能点，按 F8→F11 顺序做，**每完成一个通道就推送一次**。如果 F8 就做不动，说明 F5 的写值通道有问题，回去修 F5，不要继续。

### F7 · ByteCell 七态静态样式

```text
【本功能点】把七种状态各自的静态样式写完（不动效）。七态样式必须在 W2 全部写完，W3 只接数据，不许回头改这个组件。

【必读】视觉规范 §2.3.1（七态表）、§2.3.2（演示态）、§10（令牌）；前端规格 §3.1（owner 表）。

【做】src/components/region-c/ByteCell.vue 的样式部分 + 一个 ?debug=states 调试路由（临时，W4 删）：
七态：idle / changed / selected / error / downstream / key / done。
- idle：1px var(--rule-region-ink)。
- changed：底色 --st-changed-fill 满涂 + 顶部 2px 顶条 + 右上琥珀角标。
- selected：border-color: --accent + inset 0 0 0 1px + 外 3px outline（offset 2px）。**不用四角刻线**（与 error 右下折角同位置同尺寸）。
- error：红底 + 右下 6px 折角三角 + 底条 + ≠ 上标。
- downstream：边框降到 --line-hairline（宽度仍 1px）+ 底色 --surface-inset + 文字 --ink-3 400。演示态边框不降（--st-downstream-border 的演示值 = --rule-region-ink）。**不许虚线**。
- key：石墨底 + 45° 斜纹 + 左侧 3px 竖条。
- done：无纹理 + 1px 实线 + 左下缺口（用 __corner[data-corner="bl"] 压一块 --paper-0 方块实现，**不许断 border**）。

【硬约束】
- border-width 七态恒定 1px（演示态 2px），只改 border-color。
- data-bd / data-txr 用单值属性承载（属性单值 → 保证一个 owner）；其余状态用 is-*。
- 角位按 br(error) > tl(reverse) > tr(changed) > bl(done) 截断取前 2。
- 禁止 !important，禁止靠 class 书写顺序决定叠加结果。

【验收】
1. 打开 ?debug=states，七态同时铺开截图，每态标注对应 class。
2. 逐个量 computed border-width，全部 1px（演示态 2px），贴 7 行输出。
3. 切到演示态（html[data-mode="present"]），逐个量 border-color：普通格与 downstream 格**必须完全相等**，且对纸底 ≥4.5:1。贴取色器结果。
4. error + selected 同格：红底红边 + 近黑外环同时可见，外环与右下折角不重叠（截图）。
5. 一格里同时有 changed+key：确认 key 的斜纹还在、changed 的黄底也没被吃掉。

【禁止】用尺寸内缩表达任何状态；给 downstream 加角标/纹理/≠；给 done 加点阵。
```

### F8–F11 · 四个操作通道（按此顺序，一次一个）

```text
【本功能点】实现 <操作名> 的动效通道。只做这一种操作，其他三种的动效保持没有。

【必读】前端规格 §4（动效参数表 M1–M29，找到本操作对应行）、§3.2（Canvas 只画会动的几何）。

【做】
- SubBytes：逐格 scaleY 0→1（列优先 20ms stagger）+ S 盒十字准星 SVG。
- ShiftRows：DOM 行轨道 translateX 280ms + 行序 40ms stagger + 8 格鬼节点回绕 + Canvas 1px 描边闪 60ms。
- MixColumns：同列 4 格**零 stagger**（刻意的同步感）+ Canvas 计算线 280ms linear + 列间 60ms + accent-soft 12%→0 淡出 600ms。
- AddRoundKey：密钥层 0→0.6 透明度 120ms → 底色转石墨 160ms → values steps(4) 80ms → 密钥层淡出 120ms。

【硬约束】
- 动画只能改 transform / opacity / background-color / outline。禁止改 width/height/top/left/margin。
- 禁止动画 box-shadow 模糊半径，禁止 filter: blur / backdrop-filter。
- will-change 只在 .is-playing / .is-dragging 期间存在，写进选择器，不进基础类。
- 缓动只用 --e-out-quart 与 linear / in-out-cubic，禁止过冲（back/elastic/bounce）。
- 单步动效固定 280ms，不随倍速变（播放节奏由 --step-interval 控制，两者解耦）。

【验收】
1. 播放到本操作的步骤，贴 3 张步中截图（起、中、末）。
2. 用 Performance 录制这一段：Layout ≤1 次、无 >20ms 长帧、合成层 ≤4（贴数值）。
3. 关闭本操作动效（把它注释掉），确认其他三种操作看起来仍然正常 —— 证明四条通道互不依赖。
4. 本操作的通道特征与其他三种并列截图：不加文字标注也能一眼分辨是哪一种。

【禁止】用 setTimeout 串联多段动效（必须 animation-delay 或 transitionend，且要有兜底定时器）；把 hex 画进 Canvas。
```

### F12 · 时间轴四轨与双形状标记

```text
【本功能点】四轨时间轴 + 可拖拽游标 + 两种标记形状。

【必读】视觉规范 §6.3.2（四轨 y 坐标）、§6.3.4（图例）；前端规格 §3.5。

【做】
- Timeline.vue：四轨（轮号带 / 刻度轨 / 标记轨 / 游标）。只改 CSS 变量 --i / --span 定位，不写 style.top。
- 标记：诊断 = 5px 实心圆贴上沿（y30–35）；提问 = 5px 无圆角实心方贴下沿（y41–46）。**都不是横条**。
- 一步一个 <button class="c-mark">，整列宽 × 标记轨全高，内部两枚 <i class="c-mark__shape" data-kind="diag|ask"> 常驻，data-kinds 只驱动 CSS 闸门。**不用伪元素**（伪元素无法被图例原样复用）。
- 图例复用同一个 .c-mark__shape 元素，左右并排，圆贴上沿、方贴下沿，不许用 ● / ▪ 字符。
- 拖拽：pointerdown/move/up，拖拽期间不触发任何动效。

【硬约束】
- 标记与图例必须像素级一致（同一个元素、同一段 CSS）。
- 两个伪元素已被形状占满，这个 button 以后不许再加任何伪元素装饰（hover/focus 用 outline 或子元素）。
- 拖拽期间不写入诊断历史、不发 AI 请求。

【验收】
1. 24 步与 58 步各截图：标记不被游标遮挡，圆方同 x 并存可见。
2. 图例与轨道标记叠图对比，像素级一致（贴两张局部放大图）。
3. 拖拽全程 Performance 面板无 Animation 轨道条目（贴截图）。
4. 松手后该步只重播一次动效。
5. 键盘：Tab 到标记按钮，聚焦播报「第 13 步，1 条诊断提示，2 次提问」（贴 aria-label）。

【禁止】用 JS 改 style.top 挪游标；把标记画成横条；图例另画图标。
```

### F13 · TransportBar 与播放节奏

```text
【本功能点】播放控制条：播放/暂停/上一步/下一步/首末/倍速，并让播放节奏与动画时长解耦。

【必读】前端规格 §4（--step-interval）；交互规格 §2.4（控制行）。

【做】
- TransportBar.vue：6 个按钮 + 倍速选择（0.5× / 1× / 2× / 4×）+ 步骤指示「13 / 38」。
- usePlaybackStore：isPlaying、currentStep、speed。用 rAF 或 setInterval 驱动，间隔 = --step-interval。
- **倍速只改间隔（1600/800/400/200ms），单步动效固定 280ms 不变**。禁止把 transition-duration 乘以倍速。
- 播放到末尾自动停，不循环。

【硬约束】
- 暂停必须"停在这一步的终态"，不是停在动画中间（暂停时把动画 cancel 到终态）。
- 改倍速不打断当前正在播放的那一步。

【验收】
1. 4 档倍速各播放 8 步，贴实测总耗时（应分别约 12.8s / 6.4s / 3.2s / 1.6s）。
2. 4× 倍速下截图：单步动效仍完整发生（不是瞬间跳变）——贴两帧连续截图。
3. 播到第 38 步自动停止，isPlaying === false（贴 store 快照）。
4. 播放中途按暂停，矩阵停在该步终态（贴 state 与 trace 第 N 步的 state_after 一致）。

【禁止】用 CSS animation-iteration-count 数组一次性播完 38 步；让倍速影响缓动曲线。
```

### F14 · reduced-motion 与灰度回归

```text
【本功能点】让关闭动效后信息一点不丢，并做灰度检验。

【必读】前端规格 §7.2 硬约束 7（三段归零）；交互规格 §8.2。

【做】
- useReducedMotion.ts：媒体查询 prefers-reduced-motion + 页内开关，合并成一个布尔。
- 归零三段：--d-* 置 0.01ms + 该动画 animation: none + el.getAnimations().forEach(a => a.cancel())。**光设时长 0ms 会让 stroke-dashoffset 停在半截**。
- 所有描边/位移动画的静止态必须是终态（从 0 正向播到终态），这样 cancel() 才安全。
- 信息补偿：变化字节留常驻琥珀角标；行移位有「←1」文本；列混合有「MIX」标签；轮密钥加有「⊕」上标。
- e2e/grayscale.spec.ts：对 .c-matrix 加 filter: grayscale(1)，断言变化格与普通格平均亮度差 ≥14。

【硬约束】
- reduced-motion 下不许有任何"为了补偿"的新布局（不加新元素，只加已有元素的常驻态）。
- 灰度断言失败时调明度，不调色相。

【验收】
1. OS 开启「减少动效」+ 页内开关，各截图一张：界面完整、无半截描边。
2. 关闭动效后，不看颜色也能说出「哪几个字节变了」（贴截图 + 你的描述）。
3. document.getAnimations().length === 0（贴断言）。
4. 灰度断言通过，贴亮度差数值。

【禁止】用 display:none 隐藏动效元素（会连带隐藏信息）；在 reduced-motion 下改变 DOM 结构。
```

### F15 · 演示态参数集

```text
【本功能点】课堂投影专用的一套参数，与常规态正交。

【必读】视觉规范 §2.3.2（演示态为什么让格子边框与区域线同色）、§10 演示块。

【做】
- html[data-mode="present"] 下的令牌覆盖（视觉规范 §10 演示块，值照抄）：去纹理、去半透明、更高对比、更大焦点环、--cell-gap: 10px、border-width: 2px、--cell-size 上限 88px。
- C 区容器 ≥720px 且 present 时才可达 88px 档（@container，不是视口宽）。选择器写 [data-mode="present"] .c-matrix，**不要写 .c-matrix[data-mode="present"]**（属性不在矩阵上，永远不命中）。
- 顶部加一个演示模式开关（临时放 A 区右端，W4 收进菜单）。

【硬约束】
- 演示态**不需要任何 border-color 覆盖**：--rule-region-ink 在演示块自己就是 0.545。写了反而多一层会忘掉的分支。
- 禁止在组件里写 if (mode === 'present') 分支改间距，只能改令牌。

【验收】
1. 切到演示态，量 .c-byte 的 border-top-color = oklch(0.545 …)，与 downstream 格**完全相等**（贴两个 computed value）。
2. 对纸底对比度 ≥4.5:1（DevTools 取色器，贴数值）。
3. 窗口缩到 1024 宽：矩阵回落到 72px 档，4×72 不溢出（scrollWidth === clientWidth）。
4. 1120 以上且 present：可达 88px（贴 offsetWidth）。
5. 演示态截图与常规态并列，投影下差异明显（贴两张）。

【禁止】演示态只给 downstream 单独改边框色（会让它比邻居更浅）；用 @media 视口宽判断档位（必须 @container）。
```

---

## §7 后端（B1–B3）

> 前端 W2 完成后再做后端。W1–W2 期间前端用本地 engine 顶着。

### B1 · FastAPI 骨架与 trace 接口

```text
【本功能点】起一个能跑的后端，提供 /api/aes/trace。

【必读】前端规格 §11.1（通用约定）、§11.2（trace 契约）。

【做】
- backend/：FastAPI + uvicorn，main.py、routers/aes.py、services/aes_impl.py、models/schemas.py、db.py（SQLite，先只建表不写数据）。
- POST /api/aes/trace：入参 { plaintext, key, mode }，出参与前端 engine/trace.ts 完全同构（字段名一个字都不能差）。
- 算法用 Python 重写一遍（pysmx 之类都不许用），**结果必须与前端 engine 逐字节一致**。
- CORS 允许 localhost:5173。

【硬约束】
- 字段命名 snake_case，与 §11 一致。
- 错误返回 { error: { code, message } }，不要裸 500。
- 不用 ORM，先手写 sqlite3。

【验收】
1. curl 一组 FIPS-197 C.1 向量，ciphertext 正确（贴命令与响应）。
2. 同一组输入，后端与前端 engine 的 steps 逐字段对比脚本跑通，0 处差异（贴脚本输出）。
3. /docs 可打开（贴截图）。
4. 非法入参（key 长度 15）返回 400 + 结构化错误（贴响应）。

【禁止】引入 pydantic 之外的重型依赖；把 trace 存进数据库（它是纯计算）。
```

### B2 · SSE 辅导接口

```text
【本功能点】流式 AI 辅导接口，用 SSE。

【必读】前端规格 §11.3（SSE 事件契约）。

【做】POST /api/tutor/ask：
- 入参只收 { trace_id, step_index, question } —— **不要把 16 字节数值再传一遍**（会造成两处数值不一致）。
- 事件序列：meta（含 trace_id/step_index）→ token（多次）→ done 或 error。
- 后端自己按 trace_id 取那一步的真实 state，拼进 prompt，模型回答里的数值来自这里。
- 超时 20s 主动结束并下发 done 带 degraded: true。
- 缓存：同一 (trace_id, step, question) 命中直接回放整段，不重新生成。

【硬约束】
- SSE 帧格式严格按 §11.3，前端已经照它写了。
- 不许把整段答案一次发完再拆包（假流式，评审一眼能看出来）。
- 断连必须停止生成（检测 request.is_disconnected）。

【验收】
1. curl -N 观察，逐 token 到达（贴前 5 帧与耗时）。
2. 回答里出现的字节值，与 trace 第 N 步 state 完全一致（贴对比）。
3. 中途 Ctrl+C 断开，后端日志显示生成已取消（贴日志）。
4. 同一问题第二次请求命中缓存，首字 <100ms（贴两次耗时）。

【禁止】把 API Key 写进代码或前端；用假流式（先算完再逐字符发）。
```

### B3 · 判分接口与埋点

```text
【本功能点】唯一的判分入口 + 批量埋点。判分逻辑只在这里存在。

【必读】前端规格 §11.4（判分契约）、§11.6（前端禁止事项）。

【做】POST /api/quiz/submit：
返回 { summary, first_diff, propagated[], input_mismatch, expected_ciphertext }。
- first_diff：{ step_index, byte_index, expected, actual }，**只标 1 格**（首个差异）。
- propagated：受污染字节下标数组 —— 由首个错误之后的全量中间态推出来，**前端算不出这个，所以只能后端给**。
- input_mismatch：可空对象 { field, char_index, expected } —— 学生录错明文/密钥不算算法错，不计入统计。
POST /api/events：批量埋点，返回 204。

【硬约束】
- 判分只此一处，任何其他接口不得复算。
- input_mismatch 非 null 时，summary 里的统计分母不含本题。
- propagated 为空数组时前端按"只标 error"降级，不许返回 null。

【验收】
1. 故意答错 1 个字节，first_diff 只返回那 1 个下标（贴响应）。
2. propagated 长度与该错实际影响的字节数一致（贴手算过程对照）。
3. 输入非法字符，input_mismatch 指出 field 与 char_index（贴响应）。
4. 前端复算路径不存在：在 PracticeView 里 grep engine 引用，结果为空（贴 grep 输出）。
```

---

## §8 W3 · AI 与练习

### F16 · useSSE 与辅导主链路

```text
【本功能点】能提问、能流式回答、回答引用当前步真实数值。

【必读】前端规格 §7.3；交互规格 §4.3 / §4.5。

【做】
- useSSE.ts：fetch + ReadableStream + AbortController，60 行内，**禁止 EventSource**（它不支持 POST 与自定义头）。
- TutorPanel 主链路：输入框 → 发送 → 流式渲染 → 完成。
- 请求只传 { trace_id, step_index, question }。
- 数值高亮：回答中的 hex / 十进制数值可点击，带「引用本步数值」文本标签（不能只靠底纹色）。

【硬约束】
- onScopeDispose / onUnmounted 中 abort()，并维护 window.__sse.active 计数。
- 流式正文禁止进 aria-live；结束后一次性播报或提供「朗读回答」按钮。
- 流式期间 activeChannel = 'tutor'，矩阵与时间轴不得播动效、不得弹诊断。

【验收】
1. 选中第 13 步问「这一步为什么这么做」，回答里出现该步真实字节值（贴截图 + 后端原始 SSE 帧）。
2. 提问中途切步：旧回答折叠为一行，CTX 头更新，且**没有自动发起新请求**（Network 面板确认）。
3. 组件卸载后 window.__sse.active === 0（贴断言）。
4. 流式期间 Performance 面板无 Animation 条目（贴截图）。

【禁止】把 AbortController 放进 Pinia state（会被 devtools 序列化）；用 v-html 渲染回答；在 watch(phase) 里发请求（会重入）。
```

### F17 · 辅导 11 态与降级

```text
【本功能点】把辅导面板的 11 个状态补全，断网也不崩。

【做】空闲 / 等待首字 / 首字慢 / 流式 / 完成 / 缓存命中 / 通用讲解 / 超时降级 / 错误 / 中断 / 切步折叠。
- 双阈值：首字 3s 未到 → 显示「先看本地要点」；总 20s → 中断并切本地模板，标「离线讲解」。
- 用户问题在降级后**不得清空**。
- 缓存命中整段直出，不许模拟打字机。

【验收】
1. 断网重试：3s 出本地要点、20s 出本地模板与「离线讲解」标识（贴三个时间点截图）。
2. 降级后输入框内容仍在（贴截图）。
3. 缓存命中：首字到整段完成 <100ms，且逐字动画不存在（贴时间）。
4. 11 个状态用一个调试开关逐个走一遍，各截一张图。

【禁止】用 toast 承载错误态（必须行内）；把降级文案写成"AI 暂时不可用"这种没有信息量的句子。
```

### F18 · 认知诊断批注

```text
【本功能点】在 E 区顶部出现红线批注，指向具体字节。

【做】
- useDiagnosisStore：规则 = 空闲 ≥20s 且无有效操作，或同一 1–2 步窗口往返 ≥3 次且单次停留不足 3 秒。
- **禁止用「停留 8 秒」**（8 秒读不完一段 AI 回答，误判代价远高于漏判）。
- 同屏最多 1 条，间隔 ≥45 秒；activeChannel 必须是 idle 才允许出现。
- DiagnosisCard + SVG 折线 420ms 指向矩阵具体格。
- ?debug=diagnosis 暴露 window.__diag.forceFire(type)。

【验收】
1. ?debug=diagnosis 一键拉出批注，420ms 折线到具体字节，不遮矩阵（贴截图 + 录屏时长）。
2. 连续触发第二条被 45s 冷却拦掉（贴两次时间戳）。
3. 提问期间（activeChannel='tutor'）强制触发，不出现（贴截图）。
4. 快速来回翻步 3 次（每次不足 3 秒）后静止 20 秒，批注出现（贴时间线）。

【禁止】诊断提示出现在 E 区以外；移动焦点、居中、toast；覆盖矩阵与时间轴。
```

### F19 · 练习页与三层反馈

```text
【本功能点】答题 → 后端判分 → 只标 1 格红、其余灰化、并说出错在哪一步。

【做】
- PracticeView + useQuizStore：调 POST /api/quiz/submit，**前端零复算**。
- 渲染三层：summary（一句结论）/ first_diff（1 格 is-error）/ propagated（Set → is-downstream）。
- 通道优先级：error / downstream 覆盖 changed，但 **key 不让位**（学生必须看到哪 8 个密钥字节参与异或）。
- 判分叠加绑定 step_index：切步即整体撤场，不许把某一步的错画到另一步。
- input_mismatch 非 null：不计入统计，文案说出「哪个字段、第几个字符」。

【硬约束】
- 禁止从 engine/ import 任何东西进 PracticeView / useQuizStore。
- 不许新建第二套矩阵写入通道，判分优先级写进 useMatrixWriter 的 paintFor()。
- 矩阵不许画外框，只画实线四角括 + 文本「影响范围：16 字节」。

【验收】
1. 答错后：document.querySelectorAll('.is-error').length === 1，.is-downstream 数 === propagated.length（贴断言）。
2. 定位文案到「第 4 轮 列混合 字节 7」，一键跳工作台该步（贴截图）。
3. key 的 8 个字节在判分期仍有左竖条（贴截图 + 断言）。
4. 输入非法字符：不计入分母，文案说出字段与位置（贴记录页前后对比）。
5. 后端返回缺失 propagated：前端不崩，按空数组降级并 console.warn（贴构造的异常响应）。

【禁止】前端复算判分（含"算一遍再比对"这种更保险的写法）；用 is-error 表示 downstream。
```

### F20 · 记录页三态

```text
【本功能点】学习记录页：空 / 有数据 / 数据不足。

【做】RecordsView：三类误解分布、正确率趋势、错题回看。
- 数据不足（<3 道）时不出结论，显示「再做 2 道就能看到你的薄弱点」。
- 误解分布只展示三类可枚举的规则命中，不做自由文本聚类。

【验收】
1. 0 题 / 2 题 / 10 题各截图一张，三态正确。
2. 正确率数字与数据库手查一致（贴 SQL 与页面数字）。
3. 点错题能回到那一步（贴跳转前后 URL）。

【禁止】用图表库（手写 SVG 折线/CSS 柱状即可）；对 <3 道的数据做百分比解读。
```

---

## §9 W4 · 打磨与部署

### F21 · 性能预算达标

```text
【本功能点】三项性能预算做实。功能一个都不许删。

【做法】先测再改。usePerfProbe 已在 W2 埋好，读它的数。
性能不达标时优先怀疑 J1 被破坏（16 格重新绑定了响应式），而不是去调动画时长。

【验收（要数字，不接受"感觉快了"）】
1. 连按 30 次 →：step p95 <100ms，长帧 0，每步 Layout ≤1，每步写批次恰好 1（贴 window.__perf.stats()）。
2. 初始路由 gzip JS ≤150KB，工作台路由 ≤220KB（贴 dist 产物）。
3. Lighthouse Desktop：FCP ≤1200ms、LCP ≤2000ms、TBT ≤150ms、无障碍 ≥95（贴报告截图）。
4. 播放 24 步全程 longtask 0，合成层 ≤4。

【禁止】为 Lighthouse 好看而延迟挂载矩阵/时间轴/播放/AI 输入框；用 will-change 常驻"提升性能"；给 16 格各升一个合成层。
```

### F22 · 无障碍收尾与表格视图

```text
【本功能点】纯键盘能走完整条链路，并提供表格视图。

【做】
- 22 个快捷键全量（含 [ / ] 跳上一个/下一个标记）；输入框聚焦时全部失效，Esc 例外。
- 表格视图：真 <table>，与 grid 共用同一份 trace，不是第二套数据。
- live region 摘要句：每次步进播报一句「第 13 步，2 轮列混合，9 个字节变化」。
- 焦点归还还给触发元素（矩阵格），不许还给 body。

【验收】
1. 纯键盘走完：载入 → 播放 → 暂停 → 提问 → 停止 → 关批注 → 开抽屉 → 关抽屉 → [ 跳上一个标记 → Enter 打开详情。全程无焦点丢失、无焦点进不可见区（贴 Tab 序列）。
2. 表格视图与 grid 的数值逐格一致（贴脚本对比）。
3. 每次步进 live region 播报一次，不重复不遗漏（贴 aria-live 内容序列）。
4. Lighthouse 无障碍 ≥95（贴报告）。

【禁止】给 16 格都写 tabindex="0"；表格视图另建一份数据。
```

### F23 · URL 状态与错误边界

```text
【本功能点】刷新能恢复现场，出错不白屏。

【做】
- 参数 / 步号 / 折叠态 / 表格视图 全进 URL，router.replace + 节流 300ms（**禁 push**，会污染历史栈）。
- 错误边界：组件报错显示可读提示 + "回到第一步"，不白屏。
- 离线降级：内置向量 + engine 本地算（**仅演示路径，绝不进判分**）。

【验收】
1. 刷新后参数、步号、折叠态、视图全部恢复（贴刷新前后截图）。
2. URL 历史栈只有一条（贴 history.length 前后）。
3. 人为让一个组件抛错，显示错误边界（贴截图）。

【禁止】用 push 同步 URL；把离线降级路径接进判分。
```

### F24 · Docker 部署与 E2E 冒烟

```text
【本功能点】一条命令起全栈，并跑通 4 条冒烟。

【做】
- 前端多阶段构建 + nginx 承载静态 + /api 反代；docker-compose 起 前端 + FastAPI + volume 挂 SQLite。
- **nginx 必须为 /api 关闭代理缓冲**（SSE 需要），proxy_read_timeout 60s。
- Playwright 4 条：载入播放 / 提问流式 / 练习判分（含 downstream 灰化断言）/ 纯键盘标记跳转。

【验收】
1. docker compose up 后 localhost 可访问，SSE 正常逐字流式（不是一次性返回，贴抓包或录屏）。
2. SQLite 落盘到 volume，重启容器后数据还在（贴两次查询）。
3. Playwright 4 条全绿（贴输出）。
4. 一份「预算达标报告」：每条指标 预算 / 实测 / 证据（截图或数值）。

【禁止】在 nginx 层给 SSE 开 gzip（会缓冲）；把 engine 打进主 chunk。
```

---

## §10 纠偏提示词（发现跑偏立刻粘）

### C1 · 它引入了不该有的依赖

```text
【停下】你引入了 <包名>，本项目禁止使用。技术栈已锁定：Vue3 + Vite + TS + Pinia + Router，HTTP 用原生 fetch，样式纯手写。
请：① 卸载该依赖；② 把用到它的地方改成原生实现；③ 说明你原本想解决什么问题，我们用已有手段怎么解决。
以后凡是需要新依赖，先问我，不要直接装。
```

### C2 · 它一次改太多

```text
【停下】你这一轮改动了 <N> 个功能点的内容，超出本轮的边界。
请：① 用 git diff --stat 列出你改的全部文件；② 把不属于「<当前功能点>」的改动全部 revert；③ 只保留本轮该做的那部分。
原则：一个功能点 = 一次提交。混在一起以后就查不出是哪一步引入的 bug。
```

### C3 · 它写死了色值/尺寸

```text
【停下】<文件>:<行> 出现了写死的色值/尺寸 <具体值>。本项目所有视觉值只能来自 tokens.css 的 CSS 变量。
请把它改成对应的 var(--xxx)，并告诉我你用的是哪个令牌、依据是视觉规范 §10 的哪一行。
如果 tokens 里没有合适的令牌，不要自己造，先问我。
```

### C4 · 它动了不该动的通道

```text
【停下】你改了 <border-width / 尺寸 / 位置>，这违反「格子绝不位移、绝不缩放、绝不内缩」。
需要更强的观感时，只能用 box-shadow: inset 叠加（它画在 padding box 内侧，不动盒模型）。
请回退这次改动，并说明你原本想达到什么视觉效果，我们换一种不改变几何的做法。
```

### C5 · 它在前端复算了判分

```text
【停下】你在前端重新算了一遍正确答案，这违反「判分只存在于后端」。
双实现会让"列优先写反"这类问题变成必然事件，而且 propagated（受污染字节）前端根本算不出来 —— 它需要全量中间态。
请：① 删掉前端算分代码；② 改为只消费 POST /api/quiz/submit 返回的 summary / first_diff / propagated / input_mismatch；③ 在 PracticeView 里确认没有 import engine/ 的任何东西。
```

### C6 · 它自己发明了结构

```text
【停下】你新建了 <文件/目录/组件>，规格里没有这个。
本项目禁止为「以后可能用到」预建空组件、空 store、空 composable。
请说明：① 它是哪个功能点要求的；② 如果规格里确有，指出文档与章节号；③ 如果没有，删掉它。
```

---

## §11 提交信息规范与留痕清单

### 提交信息

```
<type>(<scope>): <做了什么> —— 通过 F<N> 验收 <编号>

type:  feat / fix / style / perf / refactor / test / chore / docs
scope: engine / matrix / motion / timeline / playback / tutor / diagnosis / quiz / records / api / a11y / theme / perf / deploy / layout
```

例：
```
feat(engine): 实现 AES 四步变换与密钥扩展 —— 通过 F2 验收 1/2/3/4/5
feat(motion): SubBytes 逐格 scaleY + 列优先 20ms stagger —— 通过 F8 验收 1/2/3/4
fix(matrix): 16 格改回响应式绑定导致多批次写入 —— 修复 F5 断言 [MULTI-BATCH]
```

**为什么这么写**：评审看提交历史时，看到的是"每个功能点都通过了哪几条验收"，而不是"改了哪些文件"。前者证明过程，后者只是流水账。

### 大赛五件套（留痕清单，边做边攒）

| # | 要交什么 | 什么时候攒 | 存在哪 |
|---|---|---|---|
| 1 | CodeArts 对话记录（关键决策截图） | 每个功能点做完截一次，标上 F 编号 | `evidence/dialogue/F<N>-*.png` |
| 2 | 代码仓库与提交历史 | 自动（每次 push） | GitHub + CodeArts |
| 3 | 验收证据（截图/数字/断言输出） | 每个功能点的「验收证据」直接存 | `evidence/acceptance/F<N>.md` |
| 4 | 设计文档 | 已有 | `docs/` |
| 5 | 演示视频 / 答辩材料 | W4 后 | `evidence/demo/` |

`evidence/` 不要进 .gitignore（它就是要被看到的），但单张截图压到 500KB 以内。

---

## §12 一句话提醒

**这个项目最大的风险不是写不出来，是"写出来了但和设计不是同一个东西"。**

规格写了 8000 行，平台 Agent 不会全读。所以每一轮你只需要保证三件事：它读对了要读的那一节、它没越过这一轮的边界、它做完真的跑了验收。这三件事做完，20 个功能点自然拼成一份能答辩的作品。
