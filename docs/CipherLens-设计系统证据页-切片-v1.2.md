# CipherLens · 密码透镜 — 设计系统证据页（切片 v1.2 / r5）

> **本文件是 `CipherLens-视觉设计规范-v1.2.md` 的切片，不是独立文档。**
> 用途：打包成 Word / PDF 时，作为"设计系统"的三页证据。全文不进 Word，其余章节只做目录索引。
> 切片内容：① §2.3 七态字节色板（含 §2.4 语义色 token 定义）② §9 六个组件 DOM 伪结构 ③ §10 CSS 变量清单（常规 / 压缩 / 演示三块）。
> 三样东西的分工：**§2.3 证明"每个状态都有非颜色通道"**，**§10 证明"这不是随手调的色，是有 token 体系的"**，**§9 证明"它能被前端直接实现"**。
> 权威处声明：色值与视觉参数以全文为准；本切片如与全文冲突，以全文为权威。

---

## 2. 色彩系统（节选：§2.3 七态字节色板 / §2.4 语义色 token）

### 2.3 七态字节色板（核心交付）

**设计原则：颜色是第 7 通道，前 6 通道优先。** 每个状态由「底色 → 纹理 → 边框 → 角标 → 文字 → 墨量」六层叠加表达；纹理与角标是**独立叠加层**，可与底色共存（例如"轮密钥加"这一步里每个格子既"本步变化"又"密钥参与"）。

#### 2.3.1 常规态

| # | 状态 | 底色（通道1） | 纹理（通道2） | 边框 / 角标（通道3–4） | 文字（通道5） |
|---|---|---|---|---|---|
| A | 普通 `idle` | 无填充（纸） | 无 | 1px `--line-default` | `--ink-1` 500 |
| B | 本步变化 `changed` | 满涂 `--st-changed` `oklch(0.855 0.145 82)` | 无 | 顶部 `inset 0 2px 0 --st-changed-bar` `oklch(0.740 0.160 78)`；右上角 3px 实心琥珀角标 | `--ink-1` 600 |
| C | 选中 `selected` | `--paper-0` | 无 | **`border-color: --accent`（宽度仍 1px）+ `inset 0 0 0 1px --accent`（合起来 2px 观感，但不改 border 宽度、不位移 hex）+ 外 3px `--accent-ring`**（判分上下文中环色改 `--ink-1`，见 §9.1）。**不再用四角刻线**——理由见下方"为什么选中态不用四角刻线" | `--accent-strong` 600 |
| D | 错误 `error` | `--st-error-fill`（红 10%） | 无 | **右下角 6px 红色实心折角三角** + 底部 `inset 0 -2px 0 --st-error` + 右上格外 2px `≠` 上标 | `--st-error` 600 |
| E | 密钥参与 `key` | 石墨 6% | **45° 斜纹 hatch** | 左侧 3px `--st-key-ink` 竖条 + 右上角 4px 实心石墨方块 | `--ink-1` 500 |
| F | 已完成 `done` | 无填充（纸） | **无纹理**（去点阵） | **1px 实线 `--line-default` + 左下角 5px 缺口**（由 `__corner[data-corner="bl"]` 压一块 `--paper-0` 方块实现，**不用 `border` 断边**——断边会随 `border-color` 变化失效） | `--ink-3` 400（视觉权重约 60%） |
| **G** | **受污染 `downstream`** | **`--surface-inset`（底色内缩一档）** | **无纹理** | **1px `--line-hairline`（唯一允许的动作：降一级）**；无角标、无折角、无 `≠`、不换线型 | `--ink-3` 400 |

**为什么选中态不用四角刻线（r5 撤除，原先用了四版）**

`selected` 原来用"四角 6px L 形刻线"作非颜色第二通道，撤除它是因为**它在同一个像素位置上和 `error` 抢语义**：

1. **同位置、同尺寸、不同含义。** `error` 的身份通道是**右下 6px 折角三角**，而四角刻线里正好有**右下那条 6px 臂**。`error + selected` 不是边角情形——判错后点开那个错字节看明细，是练习流程里**必然发生**的动作。两者叠加时看起来像"一条画歪的线"，学生读不出这是两个语义在争用。
2. **四角是角标通道，且已满。** 角标通道的四个位置已按 §6.1.1 分配完（左上 reverse / 右上 changed / 右下 error / 左下 done），规则是"每格 ≤2 个、不得覆盖既有角"。再塞一套刻线进来，等于**同一个通道有了第二个 owner**，直接违反"一个通道一个 owner"。
3. **撤掉之后，单格级别不再有任何 L 形符号**，同屏只剩"容器活动区刻线 vs 范围角括"这一对（§6.7），需要校的组合从三种降到一种。

**第二通道改由外环承担**（不能只删刻线就完事，否则 `selected` 退化为纯颜色信号）：

- 必须是**环**（`outline` / `box-shadow`），离格边留 2px 空隙；**不能退化成"把边框加粗"**——加粗只是量变，环是另一种形状；
- `selected` 的完整表达是**三件套全落在边缘通道**：`border-color` + `inset 0 0 0 1px` + 外 3px 环。它与角标通道**正交**，所以永远不会和 `error` / `done` / `key` 抢位置；
- **判分上下文中环色改 `--ink-1`（近黑）**：红底 + accent 环在红色盲下会并成一团，近黑环才稳（详见 §9.1）。**作用域是整个 `[data-ctx="graded"]`，不是"仅 `error` 格"**——否则同一个选中态会因为底下那格是不是错格而换色，**同屏两种环色比一种更难读**。

**环宽不是一个可以随手调厚的数，它受格间距约束**（fe 的 §3.1 与 ux 的口径表都直接用这个式子）：

```
环宽 + 环离格边的偏移 ≤ --cell-gap − 1px
```

| 档 | `--cell-gap` | 环宽 | 偏移 | 外扩合计 | 余量 |
|---|---|---|---|---|---|
| 常规 | 6px | 3px | 2px | 5px | **1px** |
| 演示 | 10px | 5px | 2px | 7px | 3px |

- **常规档只剩 1px 余量**：把常规环从 3px 加到 4px，环就会碰到相邻格的边框——16 格矩阵里相邻两条边贴在一起，会读成"两格连成一块"，正好毁掉 6px gap 的 chip 语言。
- **留 1px 而不是 0**：0 余量在 125% / 150% 系统缩放下会因亚像素取整而接触，肉眼是"偶尔粘一次"的间歇性缺陷，最难查。
- **想加厚时先看式子，不要直接改数**；要突破就得同时改 `--cell-gap`，而 `--cell-gap` 一变，`downstream` 边框"降一级不移除"的判据也要重算——**这条链是连着的，不要只改一头**。

**注意适用范围**：本条只管**字节格**。`--corner-tick` 这个语言在别处仍然合法——矩阵容器的"当前活动区"刻线（§6.2）与 B 区输入框的 focus 刻线（§6.8）都保留，因为那两个组件里**没有角标通道**，不存在争用。撤的是"字节格里再出现 L 形"这一件事，不是这个语言本身。

**这条能被推翻，但推翻它不只靠"看得见"**：如果将来有投影实测证明"6px 臂 × 1px 线宽在 1080p + 3m 距离下仍清楚可辨"，刻线可以回来——**但那时必须同时把 `error` 的折角挪到别的角位**，否则右下角仍然是"同位置、同尺寸、两个语义"。**判据是两个条件同时成立：看得见，且不撞角位。** 只满足前一个就恢复，等于把 r4 那个补丁又装回去。

**第 7 态 `downstream`（受首错污染的字节）的完整语义与规格**

它不是"另一个错误标记"，而是**"安静下去"**。数据来源：`POST /api/quiz/submit` 返回的 `propagated: number[]`。

| 项 | 规定 |
|---|---|
| 视觉目标 | **减墨**，不是**加标记**。它不需要被看见，它需要的是"和那 1 个错误字节形成对比" |
| **边框降一级，不是移除** | `--line-default`（L 0.845）→ `--line-hairline`（L 0.885）。**这是唯一允许的边框动作**，理由见下方"为什么去掉边框不成立" |
| **为什么不能移除边框** | 早期 v1.1 主张"去掉边框"，已否决：矩阵是 6px 间隙的独立 chip，**每一格的外框是它自己的完整矩形**，抽掉一格的框不会被读成"安静"，会被读成"这格没画完"——在一群自带完整外框的方块里，缺一个框比浅一个框显眼得多 |
| **也不许换线型或加粗** | 不得用虚线（虚线专义是"未生效/待定/禁用"，见 §2.6），不得用点划线（本规范已无该用例，r4 删除，见 §2.6），不得加角标、不得加粗。**降一级是全部动作** |
| 底色 | `--surface-inset`（比纸深一档，ΔL 0.036）——**"退后"而不是"突出"** |
| 禁止 | **不得复用 `error` 的任何通道**：不要红、不要折角三角、不要底部 inset 红条、不要 `≠` 上标、不要 `--st-error-fill` |
| 选择器隔离 | 前端单独挂 `is-downstream`；CSS 中 **`is-error` 与 `is-downstream` 互斥**（JS 保证），且**所有承载 `error` 特征的节点**（`__corner[data-corner="br"]` 的折角、底边 `inset` 条、`__sup--neq` 上标）的显示规则必须写成 `:not(.is-downstream)` 保护 |
| 可叠加 | `is-downstream` + `is-selected` 合法（学生点开一个受牵连字节查看来源链）；`is-downstream` + `is-changed` **在判分期不叠加**（见 §9.1 上下文覆盖规则） |
| 与 F 态 `done` 的区别 | 两者都保留边框（**都不能不要**），区别在边框之外的通道：`done` = 边框满值 + **左下角 5px 缺口**（形状通道）；`downstream` = **边框降一级** + 底色内缩 + 墨量降级（"这一片先别看"）。**`done` 用形状，`downstream` 用色阶，两者不共用通道，不会互相误读** |
| 灰度可辨性 | `ink-1`（L 0.255）/ `ink-3`（L 0.545）**ΔL 0.29** —— 墨量这一档在灰度下清晰成立。底色档 `--surface-inset` 与纸只有 **ΔL 0.036**，**这一档在灰度与投影下都不可靠，不承担区分职责**，只承担"退后"的氛围。灰度下"错的 1 个（折角形状）→ 受牵连的（无形状、最淡的墨）→ 正常的（中等墨量）"三者靠**形状 + 墨量**可分，不依赖底色 |

**为什么"去掉边框"这条路在本设计里从根上不成立（这条我推翻过两版，结论留档）**

矩阵是 **`display:grid; gap:6px` 的 16 个独立 chip**（§6.2），不是连续表格：

- 每格四周都有 **6px 纸色间隙**，"外框"是这一格自己的完整矩形
- **格与格之间没有共享边**，所以不存在"抽掉一条线只影响一半"的情况——**抽掉一格的边框，那一格就与周围所有自带完整边框的格子明显不同**

这就是为什么"减墨"在本设计里只能**降级**、不能**移除**：在一群各自有完整外框的方块里，少一个外框不会被读成"安静"，会被读成**"这格没画完"**。6px 间隙是保护（画面透气），也是约束（**边框是每格的身份证**）。

由此得到 `downstream` 的唯一定义方式：

> **边框保留，只降一级（`--line-default` → `--line-hairline`）。不可移除、不可换线型、不可加粗。**

**一个已被否决的替代方案（记下来防止再被提出）**：曾考虑"把格线改为由矩阵容器统一绘制（`gap:1px` + 容器底色），格子不写 border"。它在**本设计里不成立**，且有两个独立的否决理由：

1. **与既有构图冲突**：矩阵是 `--cell-gap: 6px`（§6.2 / §7.1）。容器底色方案会在 16 格之间填出 **6px 粗的实色条带**，不是 1px 细线；若把间隙压到 1px，"16 个独立格 + 透气"的读法与 §6.2 的列括线设计同时失效。
2. **它解决的是一个不存在的问题**：该方案原本是为了消除"相邻格共享边 → 两条 1px 叠成 2px、且两格状态不同时那条边颜色一半一半"。但 **6px 间隙下每格边框完全独立，既无共享边、也无双线**。也就是说，这个方案治的病在本设计里没有。

> **教训**：判定"某条 CSS 结构有问题"之前，先查这张表自己的 `--cell-gap`。我提出这个方案时没有核对 §6.2 的 6px，直接假设了连续表格——**跟 fe 定的那条纪律是同一类错误：引用数值时不回原文核对**。

**边框宽度必须恒定 1px，位移问题用 `border-color` 而不是 `border-width` 解决**：七态之间只改 `border-color`，不改宽度，因此 `box-sizing` 怎么算都不会让 hex 位移。需要"加粗感"的状态（`selected`）用**叠加 `box-shadow: inset`** 而不是把 border 改宽——inset 画在格内，不动盒模型。

#### 2.3.2 演示态（投屏）——不透明、零纹理、零 alpha

投影仪会吃掉所有低对比细节与半透明叠加，因此演示态**换一套通道**，不换语义：

| 状态 | 演示态表达 | 承载对比度 |
|---|---|---|
| 普通 | 实心 `--paper-0` + **2px `var(--rule-region-ink)`** = `oklch(0.545 0.012 258)` 边框 | 4.6:1 ✅ |
| 本步变化 | 同常规（黄底已不透明）；顶条加粗到 **3px**，hex 字重 **700** | 顶条 4.9:1 ✅ |
| 选中 | **3px `--accent`** + 外 **5px 实心** `oklch(0.925 0.026 205)` 环（r5 补厚 1px 替代原刻线：投影下环必须够宽才看得出"双层"） | 3.4:1（由线宽 + **环的双层结构**补足，不靠刻线） |
| 错误 | **实心 `oklch(0.905 0.055 28)`** + 3px 红边 + 10px 折角 + 14px `≠` | 红边 4.8:1 ✅ |
| 密钥参与 | **实心 `oklch(0.895 0.004 258)`** + 左 **6px** 石墨条 + 右上 **5px** 实心方块 | 石墨条 9.1:1 ✅ |
| 已完成 | 无纹理；**2px `var(--rule-region-ink)` + 左下角 6px 缺口（纸色方块压上去）** + 文字 `--ink-3` | 边框 4.6:1 ✅（r5 补正：原为 0.760 / 2.9:1，投影下会被读成"没画完"）；缺口形状仍承担身份通道 |
| **受污染 `downstream`** | **边框不降级**——`border-color` 引用 `--st-downstream-border`，其演示值 = **`var(--rule-region-ink)`**，与同屏其他格**同一个值**（0.545，4.6:1）；安静感改由三样东西同时承担：底色加深到 `oklch(0.905 0.004 258)`（比纸深 **ΔL 0.06**，常规档的两倍）+ 文字 `--ink-3`=`oklch(0.415 0.012 258)`（**8.4:1** ✅）+ **字重 400**（同屏其他态均为 700） | 文字 8.4:1 ✅。**这是"演示态换一套通道、不换语义"的直接应用**：常规档用"边框浅一级"表达"退后"，投影会把浅一级的线抹平成纸色（抹平后读作"这格没画完"，比不降更糟），所以演示档把"退后"整体挪到底色与字重上承担。**引用 token 而不是硬写值**，是为了让"不降级"成为结构事实——日后改演示线色时它自动跟随 |
| 判错（整段错 / 首步即错） | **四角括（corner brackets）**：四角各一个 L 形，**实线 2px** `oklch(0.545)`，长臂 **28px** / 短臂 **28px**，内缩 6px；配骑在顶边上的标签「影响范围：16 字节」（13px） | 4.6:1；**没有完整外框、没有虚线、没有琥珀** |

**演示态为什么让"格子边框"与"区域分隔线"同色（都取 `--rule-region-ink` 0.545），层级改由别处承担**

常规态靠明度分层级（格子 `--line-default` 0.845 / 区域 `--line-strong` 0.720，区域更深）。**演示态不能这么分**：投影会把所有"浅一级"的线抹平成纸色，0.760 的格子边框在 1080p 投影上只剩 **2.9:1**，被读成"格子没画完"，而不是"格子比区域次要"。所以演示态**把可视线一律抬到 ≥4.5:1**，层级改由三样重建：

1. **留白**：区域之间 16px 起，格间只有 6px（演示 10px）；
2. **标签**：区域带图号式标签（`STATE MATRIX` / `DIAGNOSTIC`），格子没有；
3. **位置**：区域分隔只出现在两区之间，从不与格子相邻——两者在屏幕上永远不相邻，本来就不需要靠色差区分。

**"靠更淡来分层级"在投影上等于"没有层级"**——这条和 `downstream` 在演示态不降级、`done` 从 0.760 抬到 0.545，是同一条道理的三次应用。

#### 2.3.3 色盲友好论证（评审会追问，必须能背）

1. **明度是主通道**：B 态 L=0.855（填充）/ D 态 0.545 / C 态 0.500 / E 态 0.360，相邻状态 **ΔL ≥ 0.10**。红绿色盲（deutan / protan，占人群约 8%）会丢失 h82–h27 的色相差，但拿到明度差后 B≈浅、D≈中、C≈中深、E≈深，仍然可分。
2. **形状通道**：C 有**外环**（唯一有双层环的状态——环是形状，不是颜色）、D 有折角三角（唯一有角标的状态）、E 有斜纹 + 方块、F 有左下缺口（唯一有缺口的）、B 有实心色块 + 顶部厚条、G 的唯一动作是**三档同时减**（边框降一级 + 底色退一档 + 墨量降一档），**形状零新增**。通道互不重复；演示态下改为形状互不重复。
3. **位置通道**：E 的标识固定左边缘 + 右上角，D 固定右下角 + 底部，B 固定顶部。整格变灰后位置仍在。
4. **文本通道兜底**：凡"行为语义"差异（播放中 vs 暂停、缓存命中 vs 流式、输入不一致 vs 判错），一律给文本或图标，**不给颜色**。
5. **不给"正确"任何颜色**：判分正确 = 无标记（即 A 态）。少一种颜色，就少一次与 accent 青 / 成功绿混淆的机会。
6. **"受牵连"用减墨，而不是用标记**：G 态只有三个动作——文字墨量降一档、底色后退一档、边框降一级（`--line-default` → `--line-hairline`），**形状零新增、角标零新增**。学生的眼睛会自动跳到唯一有形状的那一格（D），而不会把注意力分散到 15 个同样安静的格子上。这是"安静"作为设计手段的唯一正解：**安静 = 拿掉东西，不是换成另一种颜色，也不是换成另一种线型**。
7. **七态不共时**：A/B/C/E/F 属于"播放与浏览"（工作台），D/G 属于"判分与定位"（练习）。D 与 G 严格互斥，B 与 D 也不同时出现。真正需要同时分辨的最多 4 态，这保证了灰度下的可辨性有余量。
8. **验收标准（写进测试用例，已脚本化）**：对工作台截图加 `filter: grayscale(1)`，必须仍能在 3 秒内指出"哪几个字节变了 / 哪个选错了 / 哪些是密钥字节 / 哪些是受牵连的"。做不到就调**明度**，不调**色相**。

### 2.4 语义色补充

- `--st-changed: oklch(0.855 0.145 82)`、`--st-changed-bar: oklch(0.740 0.160 78)`
- `--st-error: oklch(0.545 0.195 27)`（对纸底 5.7:1）、`--st-error-fill: oklch(0.545 0.195 27 / 0.10)`
- `--st-key-ink: oklch(0.360 0.012 258)`
- `--st-downstream-fill: var(--surface-inset)`、`--st-downstream-ink: var(--ink-3)`、`--st-downstream-border: var(--line-hairline)`（**边框保留、只降一级**——本态排在边框通道末位）。**演示态覆盖为 `var(--rule-region-ink)`**，不是 `var(--line-default)`：演示态格子边框本身取 0.545，若此态取 0.760 就比邻居更浅，"不降"在数值上不成立
- `--rule-scope-w: 2px`、`--rule-scope-ink: var(--line-strong)`（演示态 `oklch(0.545 0.012 258)`）—— **区域级"四角括"专用，实线、中性色、永不带红、永不带琥珀**
- `--rule-scope-arm: 28px`、`--rule-scope-inset: 6px`（四角括的长臂与内缩）
- `--warn: oklch(0.660 0.140 62)`（仅用于服务异常，**不用于教学语义**）
- **不设 `--success`**（正确 = 无标记，见 §2.3.3 第 5 条）

---

## 9. 六个关键组件的 DOM 伪结构

类名约定：`c-` 前缀 = component，`is-` 前缀 = 状态，`__` = 元素（BEM 元素层）。**状态一律写在根元素上，禁止写在子元素上**（避免 `is-` 散落导致 CSS 选择器不可穷举）。

### 9.1 字节格 `c-byte`

```
<div class="c-byte"                          ← 状态全部挂这里
     role="gridcell"
     tabindex="-1"
     aria-label="第 2 行第 2 列，值 63，本步已变化"
     data-row="1" data-col="1">
  <span class="c-byte__stage">               ← overflow:hidden，裁剪滚动替换
    <span class="c-byte__val is-current">63</span>
    <span class="c-byte__val is-incoming" aria-hidden="true">7C</span>
  </span>
  <span class="c-byte__corner" data-corner="tr" aria-hidden="true"></span>  ← 角位元素 ①：左上 reverse / 右上 changed / 右下 error / 左下 done，由 data-corner 驱动
  <span class="c-byte__corner" data-corner="br" aria-hidden="true"></span>  ← 角位元素 ②：同格最多 2 个角标，所以 DOM 只要 2 个
  <span class="c-byte__sup"   aria-hidden="true">≠</span>  ← 错误上标（格外 2px，不进格心）
  <span class="c-byte__sup"   aria-hidden="true">⊕</span>  ← is-xor（reduced-motion 下的密钥加替代）
  <span class="c-byte__hint"  aria-hidden="true">←1</span> ← reduced-motion 下的行移位旋转量
</div>
```

**角位元素只有 2 个，这是配"同格 ≤2 个角标"的上限，不是偷懒**：另两个角永远不会同时出现，多建节点等于给未来留出错余地。`data-corner` 取 `tl` / `tr` / `br` / `bl`，形状与尺寸按 §6.1.1 那张表查，不在 DOM 里硬编码。**`is-done` 的缺口也走 `data-corner="bl"`**——压一块 `--paper-0` 方块，与 `border-color` 解耦。

**根元素可用状态（7 + 4 个行为态）**：`is-changed` `is-selected` `is-error` `is-key` `is-done` `is-downstream` `is-ghost`（空 / 未输入）| `is-reverse` `is-xor` `is-disabled` `is-dragging`

**状态的 CSS 优先级顺序（实现必须按这个 order 写，fe 直接按此写 `classList`）**

所有状态规则同为 `.c-byte.is-x`（特异度 0,2,0），**靠源码顺序决定胜负**。从低到高：

| 序 | 状态 | 影响层 | 说明 |
|---|---|---|---|
| 1 | `.is-done` | 边框 + 左下缺口 + 文字墨量（**无纹理**） | 最弱的底层语义，"有内容的旧值" |
| 2 | `.is-downstream` | 边框 `border-color` 降一级 + 文字墨量（**只降不改：不加粗、不移除、不换线型**） | 覆盖 done |
| 3 | `.is-key` | 左竖条 + 右上方块 + 斜纹（**不改底色**） | 叠加层，永远不抢底色 |
| 4 | `.is-changed` | 底色 + 顶部厚条 + 右上角标 | 底色层最高 |
| 5 | `.is-reverse` / `.is-xor` | 角标 / 上标（图形层） | 只加图形，不改色 |
| 6 | `.is-selected` | 边框（`border-color` + `inset`）+ **外环**（判分上下文改近黑） | 边框层最高；**不占角标通道** |
| 7 | `.is-error` | 折角 + 底部条 + `≠` + 底色 | 图形层最高 |
| 8 | `.is-ghost` / `.is-disabled` | 整体降级 | 覆盖一切，**必须带 `:not()` 保护或 `!important`** |

**合法叠加**（JS 可同时挂，视觉按上表叠加）：
`is-changed + is-key`（轮密钥加）、`is-changed + is-selected`、`is-error + is-selected`、`is-downstream + is-selected`

**互斥（JS 必须保证不同时挂）**：
`is-error` ✕ `is-downstream`、`is-ghost` ✕ 其余全部、`is-disabled` ✕ 其余全部

**唯一需要"同时表达"的组合态是 `is-error + is-selected`**（判错后学生点开那个错字节看明细）。两态的通道本来就不抢：

| 通道 | `is-error` 占 | `is-selected` 占 |
|---|---|---|
| 底色 | `--st-error-fill` | —（不改底色） |
| 右下角 | **6px 折角三角 + `≠` 上标** | — |
| 底部 | `inset 0 -2px 0 --st-error` | — |
| 边框 | —（宽度仍 1px，颜色不变） | **`border-color: --accent`** + `inset 0 0 0 1px --accent` |
| 外环 | — | **外 3px 环，颜色改 `--ink-1`（近黑）** |
| 四角（角标通道） | **右下 6px 折角三角**（唯一占用者） | **不占用** |

**现在没有冲突了，而且这不是"凑巧"**：`selected` 的全部表达落在**边缘通道**（`border-color` + `inset` + 外环），`error` 的全部表达落在**角标通道 + 底色 + 底边条**。两个通道**正交**，所以组合时既不需要让位规则、也不需要判断谁优先——**这才是 r5 撤掉 `selected` 四角刻线的真正收益**。

> r4 里我写过一条补救规则："折角赢，`selected` 在 `is-error` 时整体不画刻线"。那是**补丁**：冲突本身是刻线带来的（刻线的右下那条臂与折角的折角三角同位置同尺寸），补丁只能让它不显眼，不能让它不存在。**r5 把冲突从源头去掉**，那条让位规则随之作废。

**判分上下文里外环必须换色**（这条不能省）：`--st-error-fill` 是红底，`--accent` 环是青，在红色盲（deutan / protan，约人群 8%）下两者明度接近、并成一团。改用 `--ink-1`（对红底 12:1）后，"这一格被选中"在任何色觉下都成立。

```css
.c-matrix[data-ctx="graded"] .c-byte.is-selected { --accent-ring: var(--ink-1); }
/* 只换环色，不动 border-color：accent 边对红底仍有 3.4:1，且它是"选中"的第二重确认 */
```

**上下文覆盖规则（判分结果展示期间）**：进入"判分结果"上下文后，**`is-error` / `is-downstream` 覆盖 `is-changed`**。

- 理由：判分那一刻用户关注的是**对错**，不是**变化**。此时 16 个格子里 `is-changed` 全都为真（AES 雪崩性），如果它继续占着底色，`error` 与 `downstream` 就都读不出来。
- 实现：`.c-matrix[data-ctx="graded"] .c-byte.is-changed:not(.is-error):not(.is-downstream) { /* changed 样式静音 */ }` —— **用上下文属性克制，不要用 `!important`，也不要让 JS 摘 class**（摘 class 会让"退出判分后恢复变化高亮"变成一次状态重建，成本高且易错）。
- 退出判分上下文（`data-ctx` 回到 `play`）后，`is-changed` 自动恢复，无需重算。

**选择器隔离硬要求**：**所有承载 `error` 特征的节点**——右下折角（`.c-byte__corner[data-corner="br"]`）、底边 `inset` 条、`≠` 上标——的显示规则必须带 `:not(.is-downstream)`：

```css
.c-byte.is-error:not(.is-downstream) .c-byte__corner[data-corner="br"] { /* 折角 */ }
.c-byte.is-error:not(.is-downstream) .c-byte__sup--neq { /* 上标 */ }
```

否则一旦状态机出错，受污染的 15 个格子会同时长出红折角，正好触发红线 1 要防的"满屏红"。**注意：闸门挂在"触发条件"上，不挂在"伪元素"上**——折角已经移进 `__corner` 元素，只护旧写法的 `::before` 会漏掉真正渲染的那个节点。

**禁止**：不要为每种状态写独立选择器树；全部走 `.c-byte.is-x .c-byte__y`。

### 9.2 状态矩阵容器 `c-matrix`

```
<section class="c-matrix" data-step="13" data-round="3">
  <header class="c-matrix__head">
    <span class="c-sheet-label">STATE MATRIX</span>          ← 图号式标签（11px mono uppercase）
    <span class="c-sheet-label__cn">状态矩阵</span>
    <span class="c-matrix__round">ROUND 3 / 10</span>
  </header>

  <div class="c-matrix__body">                              ← position:relative，图层锚点
    <div class="c-matrix__colheads" aria-hidden="true">      ← c0 c1 c2 c3
      <span>c0</span><span>c1</span><span>c2</span><span>c3</span>
    </div>
    <div class="c-matrix__rowheads" aria-hidden="true">      ← r0 r1 r2 r3（竖向）
      <span>r0</span><span>r1</span><span>r2</span><span>r3</span>
    </div>

    <canvas class="c-matrix__fx" aria-hidden="true"></canvas>            ← z0：扫描线 / 行移位
    <svg class="c-matrix__brackets" aria-hidden="true"></svg>            ← z1：4 条列括线
    <svg class="c-matrix__ticks" aria-hidden="true"></svg>               ← z1：顶部 4 刻度

    <div class="c-matrix__grid"                                          ← z2
         role="grid" aria-rowcount="4" aria-colcount="4" aria-label="状态矩阵">
      <!-- 16 × .c-byte，DOM 顺序 = 列优先，用 grid-auto-flow: column 排列 -->
    </div>

    <span class="c-matrix__corner" aria-hidden="true"></span> × 4           ← z3：四角刻线
  </div>

  <p class="c-matrix__summary">
    本步 16 个字节中 4 个被替换：下标 0、5、10、15
    <button class="c-matrix__expand is-collapsed">逐字节 ▸</button>
  </p>
</section>
```

**根元素可用状态**：`is-empty` `is-computing` `is-ready` `is-playing` `is-paused` `is-browsing`（拖拽中）`is-error` `is-offline`
**关键实现点**：`.c-matrix__grid` 的 16 个子元素 **DOM 顺序按列优先**（col0r0, col0r1, col0r2, col0r3, col1r0 …），配合 `grid-auto-flow: column` —— 这样 `Tab` 顺序、"列优先"的语义、以及 Canvas 的索引计算三者自动一致，**不需要额外映射表**。

### 9.3 Transport 栏 `c-transport`

```
<footer class="c-transport" data-mode="normal">   ← is-empty / is-dragging / is-at-end / is-at-start / is-focused

  <div class="c-transport__controls">             ← 控制行 40px
    <div class="c-transport__btns">
      <button class="c-btn c-btn--icon" aria-label="回到开头">⏮</button>
      <button class="c-btn c-btn--icon" aria-label="上一步">◀</button>
      <button class="c-btn c-btn--icon is-primary" aria-label="播放">▶</button>
      <button class="c-btn c-btn--icon" aria-label="下一步">▶|</button>
      <button class="c-btn c-btn--icon" aria-label="跳到下一轮">⏭</button>
    </div>
    <span class="c-transport__counter">第 13 步 / 24</span>
    <button class="c-toggle is-on">跟随当前步</button>
    <div class="c-transport__spacer"></div>
    <div class="c-transport__hint" aria-live="off">      ← §6.3.4 共享槽位（二者互斥，永不同时出现）
      <!-- 态 A：有标记或曾展开过 -->
      <div class="c-legend" id="tl-legend">                ← 时间轴 aria-describedby 的目标：任何状态都不许 display:none
        <span class="c-legend__item">
          <i class="c-mark__shape" data-kind="diag" aria-hidden="true"></i>系统推测
        </span>
        <span class="c-legend__item">
          <i class="c-mark__shape" data-kind="ask"  aria-hidden="true"></i>我的提问
        </span>
      </div>
      <!-- 态 B：无标记 -->
      <button class="c-legend__toggle" aria-label="时间轴标记图例">?</button>
      <!-- 态 C：时间轴聚焦中（替换整个槽位内容） -->
      <p class="c-legend__keys">← → 单步，PgUp/PgDn 跳轮</p>
    </div>
  </div>

  <div class="c-timeline"
       role="slider" tabindex="0"
       aria-describedby="tl-legend"
       aria-valuemin="0" aria-valuemax="23" aria-valuenow="13"
       aria-valuetext="第 13 步，共 24 步，第 2 轮 列混合，1 条系统推测、2 次提问">

    <div class="c-timeline__rounds" aria-hidden="true">        ← 轨道①
      <span class="c-timeline__round" style="--span:1">INIT</span>
      <span class="c-timeline__round is-alt" style="--span:4">R1</span>
      <span class="c-timeline__round" style="--span:4">R2</span>
      <!-- … -->
    </div>

    <div class="c-timeline__ticks" aria-hidden="true"></div>   ← 轨道②

    <div class="c-timeline__marks" role="group" aria-label="学习足迹标记">   ← 轨道③
      <!-- 一步 = 一个 button。圆与方是它内部的 <i> 图形，不是两个 button。
           两枚 <i> **永远常驻**（不用 v-if）——"哪一枚显形"交给 CSS 闸门，
           见 §9.3 的 .c-mark__shape 闸门。理由：学生每做一步就多一类标记，
           若用 v-if 增删子节点，24 步列表里每次追加都是一次子节点重建；
           而 <i> 的引用一旦脱离文档，写值不报错也不显示，只在真机偶发。
           仍只有一个热区、一个 Tab 停靠点。
           roving tabindex：整组仅最近的 1 个为 0，其余 -1 -->
      <button class="c-mark" style="--i:3" data-kinds="diag ask"
              tabindex="0"
              aria-label="第 3 轮列混合，1 条系统推测、2 次提问，按回车打开标记详情">
        <i class="c-mark__shape" data-kind="diag" aria-hidden="true"></i>
        <i class="c-mark__shape" data-kind="ask"  aria-hidden="true"></i>
      </button>
      <button class="c-mark" style="--i:7" data-kinds="ask"
              tabindex="-1"
              aria-label="第 3 轮列混合，2 次提问，按回车打开标记详情">
        <i class="c-mark__shape" data-kind="diag" aria-hidden="true"></i>   ← 常驻，但被闸门藏起
        <i class="c-mark__shape" data-kind="ask"  aria-hidden="true"></i>
      </button>
      <!-- 只有提问时，方仍贴下沿——位置通道不变，只是上沿那枚不可见 -->
    </div>

    <div class="c-timeline__cursor" style="--i:13" aria-hidden="true">   ← 轨道④
      <span class="c-timeline__cap"></span>                     ← 末步时出现的 4px 短横帽
      <span class="c-timeline__pos">13 / 24</span>
    </div>

    <span class="c-timeline__browse-flag" hidden>浏览中</span>
    <span class="c-timeline__empty-msg">生成后显示 24 步</span>
  </div>
</footer>
```

**根元素可用状态**：`is-empty` `is-playing` `is-dragging` `is-at-start` `is-at-end` `is-focused`
**关键实现点**：
- `--i`（步下标）与 `--span`（该轮步数）是**唯一的数据接口**，所有 x 坐标由 CSS `calc()` 从这两个变量算出。前端只改 `--i`，不改 DOM 结构。
- `.c-mark__shape[data-kind="diag"]` 画 **5px 实心圆**（上沿），`[data-kind="ask"]` 画 **5px 实心方**（下沿）。**形状由 `<i>` 子元素承担，不用伪元素**——伪元素无法被图例"原样复用"，图例那边还要一个宿主元素，多一层间接就多一处对不齐。`::after` / `::before` 不用于扩热区（热区由元素自身尺寸承担，见下条）。
- **图例与轨道共用同一个 `<i class="c-mark__shape" data-kind="…">`**（见 §6.3.4）：图例里不放独立样式、不放独立尺寸，直接用同一个元素。**这是"图例与轨道形状尺寸完全一致"这条验收唯一能过的实现方式。**

**"哪一枚显形"的闸门（r5 补正：两枚常驻，不用 `v-if`）**：

```css
/* 形状与位置只写在 <i> 自己身上，完全不依赖父级 data-kinds。
   图例里的同一枚 <i> 没有 .c-mark 父级，照样按这段渲染 —— 这就是"像素级一致"的机制。 */
.c-mark__shape { position: absolute; left: 50%; transform: translateX(-50%);
                 width: 5px; height: 5px; background: var(--ink-2); }
.c-mark__shape[data-kind="diag"] { top: 0;    border-radius: 50%; }
.c-mark__shape[data-kind="ask"]  { bottom: 0; border-radius: 0; }

/* 闸门只藏"另一类"：两个都有时两条规则都不命中，两枚同时显形 */
.c-mark[data-kinds~="diag"]:not([data-kinds~="ask"]) .c-mark__shape[data-kind="ask"],
.c-mark[data-kinds~="ask"]:not([data-kinds~="diag"]) .c-mark__shape[data-kind="diag"] { opacity: 0; }
```

- **为什么"藏"而不是"不渲染"**：标记是**追加**的（学生每做一步才多一类），用 `v-if` 意味着每次追加都在 24 步列表里重建一次子节点；而 `<i>` 的引用一旦脱离文档，`el.style.xxx = …` **不报错也不显示**，只在真机偶发（同 §9.7.1 的 `isConnected` 那条）。
- **为什么用 `opacity` 不用 `display:none`**：`display:none` 会把元素从渲染树摘掉，DevTools 里量不到尺寸——**"形状尺寸完全一致"这条验收从此只能靠肉眼**。`opacity: 0` 保留盒，隐藏的那枚仍能量出 5×5。
- **`data-kinds` 是单值枚举 + `~=`**：只允许 `diag` / `ask` / `diag ask` 三种，**不做第三类**。新增标记类型前先问：它是"系统推测"还是"我的提问"？都不是，就说明它该进 E 区卡，而不是轨道。
- **热区 = 整列宽 × 标记轨全高，一步一个**：`.c-mark { width: 100%; height: var(--tl-mark-band); background: transparent }`，宽取该步**列容器的 100%**（列容器由 `--i` + `--step-w` 定位），**绝不写死像素**——58 步下列宽约 10px，写死 12px 会跨到相邻步。可视图形只占其中 5–6px，**视觉大小与靶子大小不一致是有意的**。
- **两个图形是两个 `<i aria-hidden>` 子元素，不是伪元素**（r5 补正）：`<i class="c-mark__shape" data-kind="diag">` 贴上沿、`data-kind="ask"` 贴下沿。**为什么不用 `::before`/`::after`**：图例要"像素级一致地复用同一个符号"，而 `<i>` 可以让轨道的图形与图例的图形用**同一个元素、同一个 class、同一段 CSS**；伪元素方案只能复用"伪元素规则"，图例那边仍要一个宿主元素，多一层间接就多一处可能对不齐。**不要拆成两个 `<button>`**——两个整列宽的热区会完全重合（点不到）或各让一半（两个都不满足 24px 间距），详见 §6.3.3。
- **图例与轨道共用同一个 `<i class="c-mark__shape" data-kind="…">`**——同一个元素、同一段 CSS，验收的"像素级一致"因此是**结构上天然成立**，而不是靠两处写一样的值去凑。
- `.c-mark` 在标记轨内 **z-index: 3，高于游标**（游标 z=2）；不要做"游标压住标记时标记偏移"的处理（2px 压 5px 只露 1px，等于没露）。
- `.c-mark` 必须是可真聚焦元素（`<button>` + roving tabindex），键盘规格见 §6.3.5。
- `.c-timeline` 的 `role="slider"` 必须支持 `←/→`（执行语义）与 `PageUp/PageDown`（跳转语义）、`Home/End`；标记组不在此滑块内，避免嵌套控件冲突。

### 9.4 AI 消息块 `c-msg`

```
<article class="c-msg is-ai"
         data-state="streaming|cached|generic|degraded|error|stopped|collapsed">
  <header class="c-msg__meta">
    <span class="c-msg__ctx">R3 · MixColumns · C[1]</span>
    <span class="c-msg__tag is-muted">来自常见问题</span>     ← 可选：cached / generic / degraded / stopped
  </header>

  <div class="c-msg__body" aria-live="polite" aria-busy="true">
    <p>…这一步 4 个字节都变了，因为 …</p>
    <span class="c-ref" role="button" tabindex="0">63</span>   ← 内联数值，可点击跳字节抽屉
    <ul><li>…</li></ul>
    <span class="c-msg__caret" aria-hidden="true"></span>      ← 2px 方块光标，仅 streaming
    <span class="c-msg__seal"  aria-hidden="true"></span>      ← 16px 1px 封口线
  </div>

  <footer class="c-msg__foot">
    <button class="c-msg__act">这对你有帮助吗</button>
  </footer>
</article>

<article class="c-msg is-user">
  <p>为什么这一步只改了 4 个字节？</p>
</article>
```

**关键实现点**：
- `data-state` 用属性而不是多个 `is-` 类，因为 `cached / generic / degraded / error / stopped` 是**互斥**的（用类会让"同时 is-error is-cached"这种非法组合变得可能）。
- `is-ai` / `is-user` 用类，因为它是**结构差异**而非状态。
- `.c-msg__caret` 只在 `data-state="streaming"` 时渲染；`cached` 状态必须**不渲染**（否则就变成假流式）。
- `aria-busy` 在流式期间为 `true`，结束置 `false`。

### 9.5 红线批注 `c-annotation`

```
<!-- ① 常驻槽位：E 区顶部 40px（演示 56px），任何时刻都存在，高度不变 -->
<div class="c-diagslot" aria-live="polite">

  <!-- ② 无提示时的占位（不是隐藏，是显示占位内容） -->
  <p class="c-diagslot__idle">DIAGNOSTIC —</p>

  <!-- ③ 有提示时替换为批注本体 -->
  <aside class="c-annotation"
         role="note"
         data-state="expanded"
         style="--tick-y:168px">                  ← 刻痕在 E 区左分隔线上的 y 偏移
    <span class="c-annotation__bar" aria-hidden="true"></span>     ← 2px 红竖条，静止

    <svg class="c-annotation__bracket" aria-hidden="true" viewBox="0 0 10 26">
      <path d="M9 1 L2 1 L2 25 L9 25"/>
    </svg>

    <div class="c-annotation__text">
      <p class="c-annotation__q">
        这一步 4 个字节都变了，你觉得是哪一个先算出来的？
      </p>
      <p class="c-annotation__disclaimer">这是系统的推测，不是判错</p>   ← 仅首访
    </div>

    <div class="c-annotation__acts">
      <button class="c-annotation__act">是</button>
      <button class="c-annotation__act">不是</button>
      <button class="c-annotation__act">这提示不对</button>
    </div>

    <span class="c-annotation__count" aria-hidden="true">1</span>
    <button class="c-annotation__close" aria-label="关闭提示">×</button>
    <span class="c-annotation__tick" aria-hidden="true"></span>   ← 12×2px 红刻痕，坐标由 --tick-y 驱动
  </aside>

</div>
```

**三个元素的关系（fe 问的正是这个）**：

| 元素 | 职责 | 生命周期 |
|---|---|---|
| `.c-diagslot` | **常驻槽位**。锁死 `height: var(--diag-row-h)`，内容变化时高度不变 | 页面存活期间永不卸载 |
| `.c-diagslot__idle` | 空态占位文本 `DIAGNOSTIC —`（11px `--ink-4`） | 有提示时 `display:none` |
| `.c-annotation` | 批注本体（`DiagnosisCard`） | 按三条克制条款挂载 / 卸载，**只在槽位内** |

**关键实现点**：
- `.c-annotation` 是 `.c-diagslot` 的**唯一子元素**（`__idle` 除外），**绝不 `position: fixed`** —— 它是行内块，不是浮层。
- 槽位高度锁死 `var(--diag-row-h)`，任何状态下都不变；批注出场只动 `opacity` 与 `translateY(2px→0)`，**不动高度**（否则槽位被撑高，对话流位移）。
- 若将来批注内容变长（比如引用了 4 个数值），走 `max-height` 展开 + 槽位内部滚动，**仍然不许撑高槽位**。
- `--tick-y` 由 JS 从"目标字节格的 `getBoundingClientRect().top` − 舞台顶"算出，写成 CSS 变量；**不要用 JS 直接改 `top` 样式**（会触发 layout），因为批注出场时恰好有 16 个格子在动描边动画。
- `.c-annotation__tick` 必须 `position: absolute; left: -1px`（压在 E 区左分隔线上），**不得进入 C 区**。
- 三条克制条款（一次最多 1 条 / 间隔 45s / 空闲 20s）由状态机保证，不由 CSS 保证；CSS 只负责"不许有循环动画"。
- `aria-live="polite"` 挂在槽位而非批注上：批注被卸载时读屏仍能播报最后一次内容。

### 9.6 S 盒表 `c-sbox`

```
<div class="c-sbox" data-state="idle|query|noresult">
  <header class="c-sbox__head">
    <div class="c-tabs" role="tablist">
      <button class="c-tab is-on" role="tab" aria-selected="true">S-BOX</button>
      <button class="c-tab" role="tab" aria-selected="false">INV S-BOX</button>
    </div>
    <div class="c-sbox__search">
      <input class="c-input is-mono" placeholder="输入 0x53 或 83" aria-label="查询字节">
    </div>
  </header>

  <div class="c-sbox__scroll">
    <table class="c-sbox__table">
      <thead>
        <tr><th class="c-sbox__corner"></th><th>0</th>…<th>F</th></tr>
      </thead>
      <tbody>
        <tr><th>0</th>
            <td class="c-sbox__cell" data-x="0" data-y="0">63</td>
            …
        </tr>
      </tbody>
    </table>
    <div class="c-sbox__rowhl" aria-hidden="true"></div>   ← 1px 整行线（transform: translateY）
    <div class="c-sbox__colhl" aria-hidden="true"></div>   ← 1px 整列线（transform: translateX）
  </div>

  <footer class="c-sbox__inspect">
    <span class="c-sbox__expr">S[0x3F] = 0x75</span>
  </footer>
</div>
```

**关键实现点**：
- 4×4 分组线**不用额外 DOM**：用 `td:nth-child(4n+1) { border-left: 1px solid … }` + `tr:nth-child(4n+1) { border-top: … }`。
- 行列高亮线是**两个绝对定位的 div**，只改 `transform` —— 不要给 16 个 `<td>` 加 `is-hl` 类（256 格加类会触发 256 次样式重算）。
- 交叉格的高亮用 `.c-sbox__cell.is-cross`（单格，1 个类切换）。
- 行 / 列头 `position: sticky`；`z-index` 顺序：表头 2 > 高亮线 1 > 单元格 0。
- **密度归属**：`.c-sbox` 根挂 `data-density="roomy"`（外壳），`.c-sbox__table` 容器挂 `data-density="compact"` —— 256 格在 roomy 的 16/24px 间距下会超出 1280×720，必须收紧（见 §4.2 密度归属规则）。
- 256 格**不做虚拟滚动**：28×22px × 256 = 单表约 7.5KB 的渲染量，一次性渲染 + `content-visibility: auto` 足够；虚拟滚动会破坏 sticky 表头与整行/整列高亮线的对齐。

---

### 9.7 三个组件的 Vue SFC 骨架（fe 明确要求，只给这三个）

**先立一条硬规则，三个组件全部适用：**

> **`<template>` 里禁止出现 `v-if` / `v-else` / `<template v-if>` 来控制状态子元素。**
> 一律**常驻 DOM**，用 `data-state` / `is-*` 类切可见性（`display:none`、`visibility:hidden`、`opacity:0` 都行——它们都不销毁节点）。
> 理由：`useMatrixWriter` 与 `useByteRefs` 都是**按索引缓存节点引用**的（16 格 × 每次动画取一次 `el`），`v-if` 会在状态切换时销毁并重建节点，缓存里的旧引用变成游离节点，写进去的值不报错但也不显示——**这类 bug 只在真机上偶发，最难查**。

#### 9.7.1 `c-byte`（`ByteCell.vue`）

```vue
<template>
  <div
    class="c-byte"
    :class="[stateClasses, { 'is-ghost': ghost }]"
    role="gridcell"
    :tabindex="-1"
    :aria-label="label"
    :data-row="row" :data-col="col"
    @click="$emit('select', index)"
  >
    <!-- ① 值区：两个 .c-byte__val 永远都在，靠 is-current / is-incoming 决定谁在上层 -->
    <span class="c-byte__stage">
      <span class="c-byte__val is-current" ref="valCur">{{ value }}</span>
      <span class="c-byte__val is-incoming" aria-hidden="true" ref="valNext">{{ nextValue }}</span>
    </span>

    <!-- ② 以下 5 个装饰节点全部常驻，永不 v-if；显隐只由根元素的类 / data-corner 决定
         2 个角位元素 + 2 个上标 + 1 个 reduced-motion 提示 = 5 个，不是 6 个 -->
    <span class="c-byte__corner" data-corner="tr" aria-hidden="true"></span>  <!-- 角位①：tr=changed 琥珀 3px / tl=reverse ◀ -->
    <span class="c-byte__corner" data-corner="br" aria-hidden="true"></span>  <!-- 角位②：br=error 6px 折角 / bl=done 5px 缺口（纸色方块） -->
    <span class="c-byte__sup c-byte__sup--neq" aria-hidden="true">≠</span>  <!-- error 上标 -->
    <span class="c-byte__sup c-byte__sup--xor" aria-hidden="true">⊕</span>  <!-- 密钥加 / reduced-motion 替代 -->
    <span class="c-byte__hint" aria-hidden="true">←1</span>              <!-- reduced-motion 下行移位旋转量 -->
  </div>
</template>

<script setup>
// 状态由 props 算成类，全部挂在根元素上（§9.1 规定状态不写子元素）
// 优先级不在这里排序：CSS 靠 §9.1 的源码顺序表决定，JS 只负责"该挂的都挂上"
const props = defineProps({
  index: Number, row: Number, col: Number,
  value: String, nextValue: String, label: String,
  changed: Boolean, selected: Boolean, error: Boolean,
  key: Boolean, done: Boolean, downstream: Boolean,
  reverse: Boolean, xor: Boolean, ghost: Boolean, disabled: Boolean,
})
const stateClasses = computed(() => props)           // 见下"状态类映射"

// 模板 ref：必须在 <script setup> 顶层声明，defineExpose 才有东西可暴露
const valCur  = ref(null)
const valNext = ref(null)
defineExpose({ valCur, valNext })                    // 供 useMatrixWriter 缓存引用
</script>
```

**给 `useMatrixWriter` 的接口约定（这条比样式重要）**：

| | 约定 |
|---|---|
| 节点引用 | 只允许缓存 `valCur` / `valNext` 两个节点，**且必须校验 `el.isConnected`** 再写（判分上下文切换时组件可能被 `v-for` 的 key 变化整体重建） |
| 写值 | 写 `textContent`，**不写 `innerHTML`**（避免每次创建文本节点，16 格 × 24 步会留下大量待回收对象） |
| 触发动画 | 只切 `is-current` / `is-incoming` 两个类，**不直接改 `transform` 内联样式**——内联样式会盖掉 `[data-motion="reduced"]` 的归零规则 |
| 状态互斥 | `error` 与 `downstream` 由 JS 保证不同时挂；CSS 再挂一层 `:not(.is-downstream)` 闸门（§9.1） |

**状态类映射（顺序无关，只是拼类名）**：`is-changed` `is-selected` `is-error` `is-key` `is-done` `is-downstream` `is-ghost` `is-reverse` `is-xor` `is-disabled`。

#### 9.7.2 `c-transport` + `c-mark`（`Transport.vue` / `TimelineMark.vue`）

```vue
<!-- TimelineMark.vue：**一步一个**，不是"一标记一个"。
     圆与方是它的两枚 <i class="c-mark__shape"> 子元素，**不是伪元素** ——
     伪元素只能被"规则"复用，图例那边仍要一个宿主元素，多一层间接就多一处对不齐（§6.3.4）。
     两枚**永远常驻**，显不显由 data-kinds 交给 CSS 闸门，不用 v-if（§9.3）。 -->
<template>
  <button
    class="c-mark"
    :data-kinds="kinds"            <!-- 'diag' | 'ask' | 'diag ask' —— 只驱动闸门，不决定子节点数 -->
    :style="{ '--i': step }"
    :tabindex="active ? 0 : -1"
    :aria-label="ariaLabel"        <!-- 两类计数合并成一条播报 -->
    @click="$emit('jump', step)"
    @keydown.enter="$emit('open-detail', step)"
  >
    <i class="c-mark__shape" data-kind="diag" aria-hidden="true"></i>
    <i class="c-mark__shape" data-kind="ask"  aria-hidden="true"></i>
  </button>
</template>

<script setup>
const props = defineProps({ step: Number, kinds: String, active: Boolean })
const ariaLabel = computed(() => {
  const parts = []
  if (props.kinds.includes('diag')) parts.push('1 条系统推测')
  if (props.kinds.includes('ask'))  parts.push(`${askCount} 次提问`)
  return `第 ${round} 轮 ${op}，${parts.join('、')}，按回车打开标记详情`
})
</script>
```

**`c-mark` 的三层分工（fe 问的"谁撑热区"——答案：元素自身，两个图形是子元素）**：

| 层 | 由谁承担 | 尺寸 | 说明 |
|---|---|---|---|
| **热区** | **元素自身**（`width: 100%`、`height: var(--tl-mark-band)`、`background: transparent`） | 整列宽 × 20px（演示 24px） | 宽取**该步列容器的 100%**，**绝不写死像素**（58 步下列宽约 10px，写死 12px 会跨到相邻步）。绝不用伪元素扩热区——伪元素扩出的区域**不在元素的命中测试父链上**，`@click` 绑在元素上时点在伪元素上有时不触发 |
| **诊断圆** | `<i class="c-mark__shape" data-kind="diag">` | 5×5px（演示 6×6） | 贴上沿；`border-radius: 50%` |
| **提问方** | `<i class="c-mark__shape" data-kind="ask">` | 5×5px（演示 6×6） | 贴下沿；`border-radius: 0` |

**两个图形是 `<i>` 子元素而不是伪元素**——这解决了一个原来被伪元素绑死的限制：`::before` 只能画一个形状，而一步要能同时有两个标记；同时图例要"像素级一致地复用"，`<i>` 可以让两处用**同一个元素、同一段 CSS**。**圆在上、方在下是位置通道，两个 `<i>` 互不干扰。**

**`--i` / `--span` 的唯一数据接口**：

```css
/* --step-count 由 JS 写入（trace 长度），--step-w 是派生量。
   两者都不进 §10 的 token 表：它们不是设计参数，是布局计算。 */
.c-timeline { --step-count: 24; --step-w: calc(100% / var(--step-count)); }

.c-mark,
.c-timeline__cursor {
  left: calc(var(--i) * var(--step-w) + var(--step-w) / 2);
  transform: translateX(-50%);
}
.c-timeline__round { width: calc(var(--span) * var(--step-w)); flex: none; }
```

- `--i` 由**每个标记自己**带（`style="--i: 3"`），`--span` 只给轮号带用。
- 前端只改 `--i` 的数值，**不改 DOM 结构、不改 left 内联值**。这样 `[` / `]` 跳转、roving tabindex、`aria-label` 三者都不需要重算布局。
- `--step-w` 由容器 `calc(100% / var(--step-count))` 算出，`--step-count` 来自 trace 长度——**这是 24 步与 58 步唯一的差别**，不需要第二套布局。

**父组件 `Transport.vue` 负责**：`aria-describedby="tl-legend"` 挂在 `.c-timeline`；`.c-legend` 节点常驻（收起时换 `.sr-only`，见 §6.3.4）；`role="slider"` 与标记组是**兄弟关系，绝不嵌套**。

#### 9.7.3 `c-annotation`（`DiagnosisCard.vue`）

```vue
<template>
  <!-- 槽位常驻、高度锁死；批注本体按克制条款挂载/卸载，但卸载是"整个组件 v-if" -->
  <div class="c-diagslot" aria-live="polite">          <!-- ① live 区挂在槽位，不挂批注 -->
    <p class="c-diagslot__idle" :class="{ 'is-hidden': hasNote }">DIAGNOSTIC —</p>

    <aside
      class="c-annotation"
      :class="{ 'is-answered': answered }"
      role="note"
      :data-state="state"                              <!-- expanded | collapsed | answered -->
      :style="{ '--tick-y': tickY + 'px' }"
    >
      <span class="c-annotation__bar" aria-hidden="true"></span>
      <svg class="c-annotation__bracket" aria-hidden="true" viewBox="0 0 10 26">
        <path d="M9 1 L2 1 L2 25 L9 25"/>
      </svg>

      <div class="c-annotation__text">
        <p class="c-annotation__q">{{ question }}</p>
        <p class="c-annotation__disclaimer">这是系统的推测，不是判错</p>
      </div>

      <div class="c-annotation__acts">
        <button class="c-annotation__act" @click="answer('yes')">是</button>
        <button class="c-annotation__act" @click="answer('no')">不是</button>
        <button class="c-annotation__act" @click="answer('bad')">这提示不对</button>
      </div>

      <span class="c-annotation__count" aria-hidden="true">{{ count }}</span>
      <button class="c-annotation__close" aria-label="关闭提示" @click="$emit('dismiss')">×</button>
      <span class="c-annotation__tick" aria-hidden="true"></span>
    </aside>
  </div>
</template>
```

**`data-state` 三态下哪些子元素保留（fe 的原问题，逐条答）**：

| 子元素 | `expanded` | `collapsed`（用户手动收起） | `answered`（点了"是/不是"） |
|---|---|---|---|
| `__bar` 2px 红竖条 | 显示 | **显示**（收起后仍要能看见"这里有一条批注"） | 显示 |
| `__bracket` | 显示 | 显示 | 显示 |
| `__q` | 完整 | **`overflow:hidden` 截到 1 行**（不是 `display:none`——截断仍留可读片段） | 保留原文（用户要能回看"系统当时猜的是什么"） |
| `__disclaimer` | 首访才显示 | 隐藏（`display:none`，它是可有可无的说明） | 隐藏 |
| `__acts` 三个按钮 | 显示 | 隐藏 | **整组换成一行文本 `已记录`**（`__acts` 节点仍在，内容替换） |
| `__count` 剩余条数 | 显示（>1 时） | 显示 | 显示 |
| `__close` | 显示 | 显示 | 显示 |
| `__tick` 12×2 红刻痕 | 显示 | **显示**（它是"批注 ↔ 矩阵"唯一的位置索引，任何状态都不能丢） | 显示 |

- **高度不变是硬要求，且不是靠 CSS 猜出来的**：`.c-diagslot` 锁死 `height: var(--diag-row-h)`，`.c-annotation` 与 `__text` 都 `overflow: hidden`。三态**只改内部可见性与行数**，不改槽位盒模型。**不要用 `max-height` 过渡来"折叠"**——那会让槽位高度参与过渡。
- `answered` 态**不清空批注**：学生选了"不是"，还要能看见系统原来猜的是什么；清空会让他无法确认"我刚才否掉的是哪一句"。
- 关闭 / 换提示 = **整个 `.c-annotation` 卸载**（这是唯一允许的 `v-if`，因为它挂在槽位内部，不涉及 `c-byte` 的引用缓存）。

---

---

## 10. CSS 变量清单（可直接粘贴到 `:root`）

```css
:root {
  /* ============ 字体 ============ */
  --font-display: "Archivo", "Noto Serif SC", "Songti SC", "SimSun", Georgia, serif;
  --font-ui:      "Archivo", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", system-ui, sans-serif;
  --font-mono:    "IBM Plex Mono", "JetBrains Mono", ui-monospace, "SFMono-Regular", Consolas, monospace;

  /* ============ 字号阶梯 ============ */
  --fs-display: clamp(1.75rem, 1.1rem + 2.2vw, 2.875rem);
  --fs-h1:      clamp(1.375rem, 1.05rem + 1.1vw, 1.75rem);
  --fs-h2:      1.25rem;
  --fs-h3:      1rem;
  --fs-body:    0.9375rem;
  --fs-ui:      0.875rem;
  --fs-label:   0.75rem;
  --fs-micro:   0.6875rem;
  --fs-byte:    1rem;
  --fs-byte-lg: 1.5rem;
  --fs-sbox:    0.75rem;

  --lh-tight: 1.15;
  --lh-snug:  1.40;
  --lh-body:  1.65;
  --lh-mono:  1.20;

  --ls-label:    0.08em;
  --ls-hex-cell: 0.06em;
  --ls-hex-long: 0.02em;

  /* ============ 中性 / 表面（无纯黑纯白） ============ */
  --paper-0:        oklch(0.981 0.0025 250);
  --paper-1:        oklch(0.962 0.0035 250);
  --surface-inset:  oklch(0.945 0.0040 250);
  --surface-raised: oklch(0.995 0.0015 250);
  --line-hairline:  oklch(0.885 0.0060 250);
  --line-default:   oklch(0.845 0.0080 250);
  --line-strong:    oklch(0.720 0.0120 250);
  --ink-1:          oklch(0.255 0.0180 258);
  --ink-2:          oklch(0.440 0.0140 258);
  --ink-3:          oklch(0.545 0.0120 258);
  --ink-4:          oklch(0.700 0.0080 258);

  /* ============ 强调色（深青墨，C≤0.09 刻意不发光） ============ */
  --accent:        oklch(0.500 0.0880 205);
  --accent-strong: oklch(0.415 0.0820 205);
  --accent-soft:   oklch(0.925 0.0260 205);
  --accent-ring:   oklch(0.500 0.0880 205 / 0.20);

  /* ============ 七态字节色板（常规态） ============ */
  --st-idle-fill:   transparent;
  --st-idle-border: var(--line-default);
  --st-idle-ink:    var(--ink-1);

  --st-changed:     oklch(0.855 0.1450 82);
  --st-changed-bar: oklch(0.740 0.1600 78);

  --st-selected:      var(--accent);
  --st-selected-ring: var(--accent-ring);

  --st-error:      oklch(0.545 0.1950 27);
  --st-error-fill: oklch(0.545 0.1950 27 / 0.10);

  --st-key-ink:   oklch(0.360 0.0120 258);
  --st-key-fill:  oklch(0.360 0.0120 258 / 0.06);
  --st-key-hatch: repeating-linear-gradient(135deg,
                    oklch(0.360 0.0120 258 / 0.14) 0 1px,
                    transparent 1px 5px);

  --st-done-ink:    var(--ink-3);
  --st-done-border: var(--line-default);      /* r3：改实线（不再用虚线框）；左下缺口是它的身份通道 */
  --st-done-dots:   none;                     /* r3 去点阵：纹理通道腾出来，避免"一个通道足够却被用两次"。**token 保留、值置 none**——删掉 token 会让旧代码引用到 undefined，改值才有机会在 review 里被发现 */

  /* 第 7 态：受首错污染（只降不改——边框降一级、底色退一档、墨量降一档；与 --st-error 完全隔离） */
  --st-downstream-fill:   var(--surface-inset);
  --st-downstream-ink:    var(--ink-3);
  --st-downstream-border: var(--line-hairline);

  --warn: oklch(0.660 0.1400 62);

  /* ============ 间距（8 个值，两套密度覆盖） ============ */
  --sp-1: 4px;  --sp-2: 8px;  --sp-3: 12px;  --sp-4: 16px;
  --sp-6: 24px; --sp-8: 32px; --sp-12: 48px; --sp-16: 64px;

  /* ============ 尺寸 ============ */
  --cell-size:   62px;          /* 离散桶，容器查询覆盖 */
  --cell-gap:    6px;
  --r-cell:      2px;
  --r-control:   2px;
  --r-float:     3px;           /* 上限，禁止 >4px */

  --topbar-h:    56px;           /* A 上下文条 */
  --transport-h: 104px;          /* D 区：控制行 40 + 时间轴 64 */
  --diag-row-h:  40px;           /* E 区顶部诊断批注位（常驻占位） */
  --ai-col:      360px;          /* [data-ai="collapsed"] → 48px */
  --input-col:   268px;          /* B 区，折叠为 44px */

  /* 时间轴四轨道（常规档；压缩档与演示档见 §6.3.2 坐标表） */
  --tl-round-band:  16px;
  --tl-tick-band:   10px;
  --tl-mark-band:   20px;
  --tl-cursor-band: 14px;
  --tl-cursor-h:    46px;         /* 游标纵向贯穿 ①–③ */
  --tl-round-alt:   var(--surface-inset);
  --tl-mark-diag:   5px;          /* 诊断：5px 实心圆（一个时刻） */
  --tl-mark-ask:    5px;          /* 提问：5px 实心方（一次关注） */
  --tl-mark-z:      3;            /* 标记在标记轨内高于游标 z=2 */
  --tl-hint-slot:   188px;        /* 控制行右端共享槽位：图例 / 键盘提示，二者互斥 */

  /* 结构线分级 */
  --rule-region-w:   1px;
  --rule-region-ink: var(--line-default);
  /* 区域级"四角括"：只表达范围，永不带红、永不带琥珀（§1.4 红线 1） */
  --rule-scope-w:     2px;
  --rule-scope-ink:   var(--line-strong);
  --rule-scope-arm:   28px;
  --rule-scope-inset: 6px;

  /* 角标尺寸：不随格径等比，钳位在 3–4px（§6.1.1） */
  --flag-size: clamp(3px, calc(var(--cell-size) * 0.045), 4px);

  /* ============ 阴影（全站仅 2 处浮层可用 shadow-float） ============ */
  --shadow-1:     0 1px 0 var(--line-default);
  --shadow-float: 0 1px 0 var(--line-hairline), 0 1px 8px oklch(0.255 0.0180 258 / 0.06);

  /* ============ 动效 ============ */
  --e-out-quart:    cubic-bezier(0.16, 1, 0.30, 1);
  --e-out-quint:    cubic-bezier(0.22, 1, 0.36, 1);
  --e-in-out-cubic: cubic-bezier(0.65, 0, 0.35, 1);
  --e-step-4:       steps(4, end);
  --e-linear:       linear;

  --d-1: 80ms;
  --d-2: 160ms;
  --d-3: 280ms;
  --d-4: 420ms;
  --d-linger: 1200ms;
  --d-fade-linger: 600ms;

  --d-stagger-cell: 20ms;   /* SubBytes 列优先 */
  --d-stagger-row:  40ms;   /* ShiftRows 行序 */
  --d-stagger-col:  60ms;   /* MixColumns 列序 */

  /* 播放节奏，与动画时长解耦（动效归零时不变） */
  --step-interval: 800ms;   /* 0.5×:1600 / 2×:400 */

  /* ============ 焦点 ============ */
  --focus-ring-w:      2px;
  --focus-ring-color:  var(--accent);
  --focus-ring-offset: 2px;
  --focus-halo:        4px var(--paper-0);

  /* ============ 层级 ============ */
  --z-canvas: 0;
  --z-cells: 1;
  --z-svg-overlay: 2;
  --z-corner: 3;
  --z-transport: 20;
  --z-inspector: 40;
  --z-annotation: 50;
}

/* ================================================================
   密度 A：工作台（五区挤一屏）  →  <main data-density="compact">
   ================================================================ */
[data-density="compact"] {
  --sp-1: 4px;  --sp-2: 8px;  --sp-3: 12px;  --sp-4: 16px;
  --sp-6: 24px; --sp-8: 32px; --sp-12: 48px; --sp-16: 64px;
  --fs-body: 0.9375rem;
  --lh-body: 1.65;
  --measure: none;
  --r-control: 2px;
}

/* ================================================================
   密度 B：首页 / 练习 / 记录 / S 盒全屏  →  data-density="roomy"
   ================================================================ */
[data-density="roomy"] {
  --sp-1: 4px;  --sp-2: 8px;  --sp-3: 16px;  --sp-4: 24px;
  --sp-6: 32px; --sp-8: 48px; --sp-12: 64px; --sp-16: 96px;
  --fs-body: 1rem;
  --lh-body: 1.75;
  --measure: 68ch;
  --r-control: 3px;
}

/* ================================================================
   常规·压缩档：视口高度 ≤780px（1280×720 极限场景）
   只压高度，绝不减少轨道条数（§6.3.1）
   ================================================================ */
@media (max-height: 780px) {
  :root {
    --topbar-h:    52px;
    --transport-h: 92px;          /* 控制行 36 + 时间轴 56 */
    --tl-round-band:  14px;
    --tl-tick-band:   8px;
    --tl-mark-band:   18px;
    --tl-cursor-band: 12px;
    --tl-cursor-h:    40px;
    --sp-6: 20px;
    --sp-8: 28px;
  }
}

/* ================================================================
   演示态（投屏）：放大 + 提对比 + 删次要 + 去纹理
   与 [data-density] 正交，可叠加
   ================================================================ */
[data-mode="present"] {
  /* 字号 */
  --fs-body:  1.125rem;   /* 18 */
  --fs-ui:    1rem;       /* 16 */
  --fs-label: 0.875rem;   /* 14 */
  --fs-micro: 0.8125rem;  /* 13 */
  --fs-byte:  1.5rem;     /* 24 */
  --fs-sbox:  0.8125rem;  /* 13 */
  --lh-body:  1.50;

  /* 尺寸 */
  --cell-size: 88px;
  --cell-gap:  10px;
  --r-cell:    3px;
  --topbar-h:    72px;
  --transport-h: 136px;
  --diag-row-h:  56px;
  --ai-col:      48px;      /* 默认折叠，可展开到 420px */
  --tl-round-band:  18px;
  --tl-tick-band:   10px;
  --tl-mark-band:   24px;
  --tl-cursor-band: 18px;
  --tl-cursor-h:    54px;
  --tl-round-alt:   oklch(0.900 0.0040 250);   /* 交替底 ΔL 0.10 */
  --sp-4: 20px;
  --sp-6: 32px;

  /* 结构线：不得依赖 1px（UX-V2） */
  --rule-region-w:   2px;
  --rule-region-ink: oklch(0.545 0.0120 258);  /* 对纸底 4.6:1 */
  --rule-scope-w:    2px;
  --rule-scope-ink:  oklch(0.545 0.0120 258);
  --line-hairline:   oklch(0.820 0.0060 250);  /* 仅非结构信息 */
  --line-default:    oklch(0.760 0.0080 250);

  /* 文字对比：正文 ≥7:1、标签 ≥4.5:1（UX-V2） */
  --ink-1: oklch(0.190 0.0180 258);            /* 17.2:1 */
  --ink-2: oklch(0.340 0.0140 258);
  --ink-3: oklch(0.415 0.0120 258);            /* 8.4:1 */
  --ink-4: oklch(0.560 0.0080 258);

  /* 状态色：禁半透明、禁纹理，全部换实心 + 形状（UX-V2） */
  --st-changed:     oklch(0.870 0.1700 78);
  --st-changed-bar: oklch(0.700 0.1900 76);
  --st-error:       oklch(0.520 0.2150 27);
  --st-error-fill:  oklch(0.905 0.0550 28);            /* 不透明 */
  --st-key-fill:    oklch(0.895 0.0040 258);           /* 不透明 */
  --st-key-hatch:   none;                              /* 禁纹理 */
  --st-done-dots:   none;                              /* 禁纹理 */
  --st-downstream-fill:   oklch(0.905 0.0040 258);     /* 比纸深 ΔL 0.06（常规档的两倍），不透明 */
  --st-downstream-ink:    var(--ink-3);                /* 0.415 → 8.4:1 */
  --st-downstream-border: var(--rule-region-ink);      /* 不降级 = 与"格子边框本身"同值（0.545），**不是** --line-default（0.760）——否则比邻居更浅，"不降"在数值上是假的 */
  --accent-ring:    oklch(0.925 0.0260 205);           /* 不透明环 */

  /* 时间轴标记放大 */
  --tl-mark-diag: 6px;
  --tl-mark-ask:  6px;

  /* 焦点环：双层（内近黑 12:1 / 外黄高识别） */
  --focus-ring-w:      3px;
  --focus-ring-color:  oklch(0.200 0.0180 258);
  --focus-ring-offset: 3px;
  --focus-halo:        4px oklch(0.870 0.1700 92);

  /* 动效：投影有拖影，略慢但不超过 400ms */
  --d-3: 340ms;
}

/* ================================================================
   动效归零：系统偏好 + 页内开关，走同一段 override
   注意：--step-interval 故意不动，节奏必须保留（UX-V4）
   ================================================================ */
@media (prefers-reduced-motion: reduce) {
  :root {
    --d-1: 0ms; --d-2: 0ms; --d-3: 0ms; --d-4: 0ms;
    --d-linger: 0ms; --d-fade-linger: 0ms;
  }
}
[data-motion="reduced"] {
  --d-1: 0ms; --d-2: 0ms; --d-3: 0ms; --d-4: 0ms;
  --d-linger: 0ms; --d-fade-linger: 0ms;
}
```

---
