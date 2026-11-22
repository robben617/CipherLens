# CipherLens 全站 AI 助手（每页独立对话）· 编码任务清单

> 文档编号：CL-GAI-TASKS-v1.0
> 状态：**待评审，未开始编码**
> 输入基线：`docs/specs/global-ai-assistant-v1/requirements.md`、`docs/specs/global-ai-assistant-v1/design.md`
> 规范镜像：`.codeartsdoer/specs/global_ai_assistant_v1/tasks.md`
> 任务总数：**34**（阶段 0：9；阶段 1：8；阶段 2：6；阶段 3：5；阶段 4：6）
> 执行原则：一任务一验收；先契约/测试，后实现；旧证据只追加不删改；未确认决策不得写成已确认
> 本文只拆任务，不写业务源码，不提交，不创建分支，不恢复已删页面

---

## 0. 使用说明与执行门禁

### 0.1 状态图例

| 状态 | 含义 |
|---|---|
| 可执行 | 无外部依赖，可按本文命令验收 |
| 按阶段推进默认 | 需求 D-Gx 未逐条拍板，但用户已明确进入下一阶段；按设计默认实施，改判时回退对应任务 |
| 条件任务（默认不执行） | 设计默认不纳入本轮；仅用户明确纳入后启动 |
| 已完成 | 已实现、已验收、证据已归档 |

### 0.2 阶段推进默认值与任务放行矩阵（D-G1–D-G11）

> 用户已明确「进入下一阶段」，以下视为**按阶段推进默认**，不阻塞开工。任何一项改判，只回退受影响任务，不扩大范围。

| 决策 | 本轮默认 | 受影响任务 | 改判代价 |
|---|---|---|---|
| D-G1 切页时生成中的流 | **A 立即中止**；离开页 `phase=error`、`errorCode='interrupted'`，可重试 | T1-1、T1-2、T1-8 | 改 B 需每页独立后台流与写会话，T1-1 重做 |
| D-G2 工作台入口形态 | **保留 E 区**；设计默认工作台收起态由右下 `AiFab` 承担，E 区右上 44px 按钮不再渲染；展开态保留 E 区关闭按钮；展开时隐藏 `AiFab`；不弹全局面板 | T1-2、T3-1、T3-2、T3-4 | 若严格保留右上按钮：T3-2 改为「不移除按钮 + 工作台隐藏 AiFab」，其余不变 |
| D-G3 通用接口 | **A 新增 `/api/ai/ask`**；工作台继续 `/api/tutor/ask` | T0-6–T0-9、T1-6 | 改 B 需放宽 `TutorRequest`，污染工作台契约并重验 F17，不推荐 |
| D-G4 单轮/多轮 | **A 单轮**；历史只展示，请求不带 messages | T1-1 | 改 B 需另立上下文窗口、成本与隐私评估 |
| D-G5 刷新 | **A 内存、刷新清空**；不用 `sessionStorage/localStorage` 存会话 | T1-1 | 改 B 需每页序列化/反序列化与版本迁移 |
| D-G6 雪崩上传范围 | **A 只传位置与结论数字**；不传 `plaintext_hex/key_hex/input_byte_*` | T0-2、T2-2 | 改 B 需新增敏感字段审计与脱敏 |
| D-G7 通用页审计 | **A 不写 `tutor_logs`**；只写脱敏结构化日志 | T0-8、T0-9 | 改 B 需迁表并复验 F24 |
| D-G8 首页动作 | **采用设计默认：回答内显式动作按钮，但绝不自动路由**；`open-workbench` 仅在用户点击时执行 | T2-5、T1-5 | 若按需求 A，首页按钮降级为文字链接，其余不变 |
| D-G9 已移除页面 | **B 仅文档保留契约**；练习/记录/速查卡不实现 | 无 | 恢复页面需另立需求 |
| D-G10 页面动作能力 | **本轮不做**：S 盒不自动切逆向表；雪崩不自动改字节/重跑 | T2-5 | 需新增动作协议与安全审计 |
| D-G11 主动核对 | **本轮不做**：提示词只要求「不得编造数值」 | T1-6 | 需新增核对规则与 UI 呈现 |

> 放行规则：`T0-1` 只记录「按阶段推进默认/待确认/否决」，不得由实施 Agent 自行写成「已确认」。工作台入口位置（D-G2）在证据文档中必须注明「设计默认：右下 AiFab，右上按钮未渲染」。

### 0.3 首批可执行任务与批次划分

**第一批（可立即开工，互不阻塞）**

1. `T0-1` 冻结口径与工作区保护（文档/台账）。
2. `T0-2` 前端上下文白名单与指纹（先写 spec）。
3. `T0-3` 推荐问题数据（先写 spec）。
4. `T0-4` 6 态流控制器（先写 spec）。
5. `T0-5` 共享消息模型扩展（先写/扩 spec）。
6. `T0-6` 后端请求模型与上下文清洗（可与前端并行）。

**第二批（串行，后端契约闭环）**

`T0-7` → `T0-8` → `T0-9`。

**第三批（通用后端 + 全局面板 + 首页）**

`T1-1` → `T1-2` → `T1-3` → `T1-4` → `T1-5` → `T1-6` → `T1-7` → `T1-8`。

**第四批（S 盒/雪崩）**

`T2-1` 与 `T2-2` 可并行 → `T2-3` → `T2-4` → `T2-5` → `T2-6`。

**第五批（工作台统一入口）**

`T3-1` → `T3-2` → `T3-3` → `T3-4` → `T3-5`。

**第六批（全量回归与证据）**

`T4-1` → `T4-2` → `T4-3` → `T4-4` → `T4-5` → `T4-6`。

### 0.4 通用验收命令与证据规则

**前端**

```bash
cd frontend
npm test
npm run typecheck
npm run build
npx vitest run src/utils/ai-context.spec.ts
npx vitest run src/data/ai-prompts.spec.ts
npx vitest run src/utils/ai-stream.spec.ts
npx vitest run src/utils/tutor-message.spec.ts
npx vitest run src/stores/ai.spec.ts
```

**后端（dev 8000）**

```bash
cd backend
python -m uvicorn main:app --port 8000
python tools/ai_probe.py --self-test
python tools/ai_probe.py 8000
python tools/tutor_probe.py 8000
python tools/disconnect_probe.py
```

**Docker / SSE**

```bash
docker compose up -d --build
curl -N http://127.0.0.1:8080/api/ai/ask \
  -H "Content-Type: application/json" \
  -d "{\"page\":\"sbox\",\"question\":\"0x53 为什么查表得到 0xED？\",\"context\":{\"page\":\"sbox\",\"mode\":\"forward\",\"input\":83,\"output\":237,\"selected_hex\":\"0x53\"},\"conversation_id\":\"conv_probe_sbox\"}"
```

**Playwright（临时安装，不写入 `package.json`）**

```bash
cd frontend
npm install --no-save --no-package-lock @playwright/test@1.55.0
npx playwright test --config=e2e/playwright.config.ts e2e/global-ai.spec.ts
npx playwright test --config=e2e/playwright.config.ts e2e/smoke.spec.ts --grep "载入工作台|提问 SSE"
```

**Lighthouse（新结果不得覆盖旧证据）**

```bash
cd frontend
npm run build
npx vite preview --port 4174 --host 127.0.0.1
# 另开终端执行：
npx --yes lighthouse@13.6.0 http://127.0.0.1:4174/ \
  --preset=desktop --only-categories=performance,accessibility \
  --output=json --output-path=output/GAI-F21-home-lighthouse.json \
  --chrome-flags="--headless=new --disable-gpu --no-sandbox"
npx --yes lighthouse@13.6.0 http://127.0.0.1:4174/workbench \
  --preset=desktop --only-categories=performance,accessibility \
  --output=json --output-path=output/GAI-F21-workbench-lighthouse.json \
  --chrome-flags="--headless=new --disable-gpu --no-sandbox"
```

**证据规则**

- `evidence/acceptance/` 原文件只允许**追加**口径说明，不得删改原文、实测数字、截图引用。
- 本轮新证据使用新文件名：`GAI-home.md`、`GAI-sbox-avalanche.md`、`GAI-workbench.md`、`GAI-build.md`、`GAI-probe.md`、`GAI-playwright.txt`、`GAI-docker-sse.txt`、`GAI-F21-home-lighthouse.json`、`GAI-F21-workbench-lighthouse.json`、`GAI-summary.md`。
- 每条证据写：需求编号 A1–A20、命令、断言、实测值、未达项；未达项保留「未达」，不得改写为通过。
- Playwright 继续使用系统 Chrome；`--no-save --no-package-lock`，不写入 `package.json`。
- 本次不提交、不建分支；「独立验收点」只是建议主题，是否提交由用户决定。

### 0.5 任务依赖图

```text
T0-1 ─┬─> T0-2 ─> T0-3 ─┐
      ├─> T0-4 ─────────┤
      ├─> T0-5 ─────────┤
      └─> T0-6 ─> T0-7 ─> T0-8 ─> T0-9
                                   │
T0-2/T0-3/T0-4/T0-5 ───────────────┴─> T1-1 ─> T1-2 ─> T1-3 ─> T1-4 ─> T1-5 ─> T1-6 ─> T1-7 ─> T1-8
                                                                  │
                                                     T2-1/T2-2 ───┴─> T2-3 ─> T2-4 ─> T2-5 ─> T2-6
                                                                                           │
                                                               T3-1 ─> T3-2 ─> T3-3 ─> T3-4 ─> T3-5
                                                                                           │
                                                                     T4-1 ─> T4-2 ─> T4-3 ─> T4-4 ─> T4-5 ─> T4-6
```

### 0.6 禁止项与不做项（任务级红线）

1. 不恢复练习 `/practice`、记录 `/records`、速查卡 `/cheatsheet` 的路由、视图、导航或后端接入。
2. 不新增任何 npm/Python 依赖与测试框架；Playwright 仍临时安装。
3. 不修改 `backend/routers/tutor.py`、`backend/services/tutor_service.py`、`backend/services/tutor_log.py`、`backend/db.py`、`TutorRequest` 的字段与 `extra="forbid"`。
4. 不改 `TutorPanel` 的 11 态、3s/20s/55s、缓存直出、MORE、chip、`goto-step`/`open-sbox` 语义；只允许新增 `snapshot` 事件。
5. 不改 `AppDrawer`、`useHotkeys`、`useSSE`、`sse.ts`、`useHealth` 的既有行为。
6. 不改字节格几何、`--cell-gap`、七态样式阈值、S 盒网格缩放/选中逻辑、雪崩位图色阶。
7. 不改 Docker / nginx / 桌面环境；通用端点沿用现有 `/api` 不缓冲配置。
8. 不传雪崩完整明文/密钥、S 盒整表、工作台全量 trace；日志不打印问题全文、上下文值、key。
9. 不自动路由、不自动跳转、不自动跑实验、不自动切逆向表；所有跨页/页面动作必须用户显式点击。
10. 不做通用页 `tutor_logs` 写入；不做表结构迁移。
11. 不做多轮上下文、登录、跨设备、多模型、语音、图片、文件问答。
12. 不改 `evidence/acceptance/` 原文；只追加口径说明。
13. 不触碰 `frontend/public/aes-quest/index.html`（工作区既有用户改动）。
14. 不做深色科技风主题切换；不引入 UI 组件库/Tailwind/GSAP；手写 CSS，复用现有 tokens。
15. 不在 `GlobalAiPanel` 复制 F09 四块文案逻辑；只复用 `TutorMessage` 的渲染能力。
16. 不为单页另造阶段名；非工作台只使用 6 态，工作台继续 11 态。

---

## 阶段 0 · 契约与骨架（不改 UI 行为）

> 阶段目标：固化类型、上下文序列化、推荐问题、流控制器、消息模型、后端请求/模板/缓存/路由与探针。页面行为不变，工作台无视觉变化。
> 阶段验收门：`npm test -- ai-context ai-prompts ai-stream tutor-message` 全绿；`python tools/ai_probe.py --self-test` 通过；`npm run build` 通过；工作台手工打开无差异。
> 阶段回滚：删除本阶段新增文件；还原 `backend/models/schemas.py`、`backend/main.py`（若已挂载）；`tutor` 链路未改，无需回滚。

### T0-1 冻结口径、决策台账与工作区保护

- [ ] **状态**：可执行
- **目标**：把 D-G1–D-G11 的按阶段推进默认、四栏目口径、禁止项与工作区保护写成可评审台账，避免实施中擅自扩大范围。
- **涉及文件/模块**：`docs/specs/global-ai-assistant-v1/tasks.md`、`.codeartsdoer/specs/global_ai_assistant_v1/tasks.md`；只读 `requirements.md`、`design.md`、`spec.md`、`design.md`。
- **具体改动点**：
  - 在本文 §0.2 登记 11 项默认值，逐项标注「按阶段推进默认」；不写「已确认」。
  - 记录四栏目口径：`/`、`/workbench`、`/sbox`、`/avalanche`；练习/记录/速查卡不存在、不恢复。
  - 记录工作区既有改动 `frontend/public/aes-quest/index.html` 为**禁止触碰、禁止提交**。
  - 记录证据规则：只追加、不改原文；Playwright 不写入依赖。
  - 记录 D-G2 的实现取舍：工作台收起态入口由右下 `AiFab` 承担，右上 44px 按钮不渲染；若评审要求严格保留右上按钮，按 §0.2 回退 T3-2。
- **测试/证据前置**：否（文档台账）。
- **依赖任务**：无。
- **验收命令/断言**：
  - `git status --short` → 仅出现 `frontend/public/aes-quest/index.html`（既有改动）与本任务新增/修改的 tasks 文档。
  - `rg -n "D-G1|D-G2|D-G8|D-G10|aes-quest" docs/specs/global-ai-assistant-v1/tasks.md` → 台账与禁止项均存在。
  - 未修改任何 `frontend/src`、`backend/` 业务源码。
- **回滚方式**：删除本任务在 §0.2、§0.6 新增的台账段落。
- **独立验收点（建议主题）**：`docs(spec): freeze global AI task defaults`。

### T0-2 前端上下文类型、白名单序列化与指纹

- [ ] **状态**：可执行
- **目标**：把页面状态收敛为白名单 `PageContext`，提供稳定序列化与指纹，保证不泄露明文/密钥、跨页不串缓存。
- **涉及文件/模块**：`frontend/src/utils/ai-context.ts`（新增）、`frontend/src/utils/ai-context.spec.ts`（新增）；只读 `frontend/src/engine/sbox.ts`、`SBoxView.vue`、`AvalancheView.vue`。
- **具体改动点**：
  - 导出类型：`PageKey = 'home' | 'sbox' | 'avalanche' | 'workbench'`；`HomeContext`、`SboxContext`、`AvalancheContext`、`WorkbenchContext`、`PageContext`；`ApiPageContext` 仅含 `home/sbox/avalanche`。
  - `toWireContext(page, raw): ApiPageContext`：只输出 snake_case 白名单；`home` 只输出 `page`；`sbox` 输出 `page/mode/input/output/selected_hex`，`input/output` 必须成对且 0–255；`avalanche` 输出 `page/target/byte_index/bit_index/key_bits`，可选 `changed_bits/total_bits/rate/sweep_mean`，范围分别 0–31、0–7、128/192/256、0–128、0–128、0–1；`workbench` 不进入 wire（由 store 内部保留，调用 `toWireContext('workbench', ...)` 返回 `null` 或抛出明确错误）。
  - 丢弃任何非白名单键，包括 `plaintext_hex`、`key_hex`、`input_byte_before`、`input_byte_after`、整张 S 盒表、完整 trace。
  - `normalizeQuestion(question)`：`NFKC` → `trim` → 连续空白折叠为单个空格；不做大小写转换。
  - `contextFingerprint(page, cleanContext, question): Promise<string>`：固定字段顺序的紧凑 JSON（无多余空格、`ensure_ascii` 等价语义）+ `crypto.subtle.digest('SHA-256')` 取前 16 位十六进制；不含 `client_id`、`conversation_id`、时间戳、消息历史。
  - 辅助函数：`hasSboxContext`、`hasAvalancheResult`、`describeContext(page, context)`（供推荐问题与面板上下文行使用）。
  - 固定样例与后端 T0-6 共用同一字段顺序：`sbox` 为 `page,mode,input,output,selected_hex`；`avalanche` 为 `page,target,byte_index,bit_index,key_bits,changed_bits,total_bits,rate,sweep_mean`。
- **测试/证据前置**：是（先写 `ai-context.spec.ts`）。
- **依赖任务**：无；与 T0-1 可并行。
- **验收命令/断言**：
  - `cd frontend && npx vitest run src/utils/ai-context.spec.ts` → 全绿。
  - 用例覆盖：白名单剔除 `plaintext_hex/key_hex`；S 盒 `input/output` 成对；越界数值丢弃；雪崩无结果只保留位置；指纹对键顺序不敏感、同 page 同值同问题稳定、不同 page/值不同；指纹不含 client/conversation/时间。
  - `npm run typecheck` → 0 error。
- **回滚方式**：删除 `ai-context.ts` 与 `ai-context.spec.ts`。
- **独立验收点（建议主题）**：`feat(ai-context): add page context whitelist and fingerprint`。

### T0-3 推荐问题数据（随页面与上下文变化）

- [ ] **状态**：可执行
- **目标**：提供纯函数 `promptsFor(page, context)`，为首页/S 盒/雪崩各生成 3 条序号化问题；工作台沿用 `QuickAsk`，不改。
- **涉及文件/模块**：`frontend/src/data/ai-prompts.ts`（新增）、`frontend/src/data/ai-prompts.spec.ts`（新增）。
- **具体改动点**：
  - `home` 恒定 3 条：「AES 是什么？」「为什么按 16 字节分组？」「密钥和加密结果是什么关系？」。
  - `sbox` 有上下文：`0x{input} 为什么查表得到 0x{output}？`、`逆 S 盒为什么能还原？`、`为什么 S 盒不是随机的？`；`input/output` 用大写两位十六进制；无上下文：「先在网格里选中一个字节，再问我」「正向和逆向 S 盒有什么区别？」「为什么 S 盒能反查？」。
  - `avalanche` 有结果：「为什么改 1 位会变一半？」`为什么不是正好 {totalBits/2} 位？`「连做平均说明了什么？」；无结果：「先跑一次实验，才能引用真实数字」「为什么改 1 位会变一半？」「雪崩效应和扩散有什么关系？」。
  - `workbench` 返回空数组（由 `QuickAsk` 负责）；函数不读取历史、不发请求、不改变页面状态。
  - 序号由 `GlobalAiPrompts` 渲染，数据层只返回文本。
- **测试/证据前置**：是（先写 spec）。
- **依赖任务**：T0-2（类型与上下文判定）。
- **验收命令/断言**：
  - `cd frontend && npx vitest run src/data/ai-prompts.spec.ts` → 全绿。
  - 断言：每个非工作台页面返回 3 条；序号不写入文本；无上下文文案出现；不出现明文/密钥；雪崩 `total_bits=128` 时出现「64 位」。
- **回滚方式**：删除 `ai-prompts.ts` 与 `ai-prompts.spec.ts`。
- **独立验收点（建议主题）**：`feat(ai-prompts): add page-aware suggested questions`。

### T0-4 前端 6 态流控制器（可中止、可单测）

- [ ] **状态**：可执行
- **目标**：给 store 提供一个不依赖组件生命周期、可显式中止、30s 无 token 只报一次的 SSE 流控制器；工作台继续用 `useSSE`。
- **涉及文件/模块**：`frontend/src/utils/ai-stream.ts`（新增）、`frontend/src/utils/ai-stream.spec.ts`（新增）；只读 `frontend/src/utils/sse.ts`、`frontend/src/composables/useSSE.ts`。
- **具体改动点**：
  - `startAiStream({ url, payload, handlers, tokenTimeoutMs = 30000 })` 返回 `{ abort(reason?), promise, settled }`。
  - 内部使用 `fetch` + `consumeSSE`，自建 `AbortController`；不调用 `useSSE`，不依赖 `onScopeDispose`。
  - `meta/block/token` 均重置 30s 计时；`done`/`error` settle 一次；`abort()` 幂等，且不触发 `onError`。
  - 网络错误映射 `network_error`；超时只报一次 `timeout`；HTTP 非 2xx 映射 `network_error`。
  - 不修改 `useSSE.ts` 与 `sse.ts`。
- **测试/证据前置**：是（先写 spec，mock `fetch` 与 `ReadableStream`）。
- **依赖任务**：无；与 T0-2/T0-3 可并行。
- **验收命令/断言**：
  - `cd frontend && npx vitest run src/utils/ai-stream.spec.ts` → 全绿。
  - 用例：`meta→block→token→done` 正常；只发 `meta` 后 30s 触发一次 `onError('timeout')`；`abort()` 后不再写 token、不触发 `onError`；`error` 不重复。
  - `npx vitest run src/composables/useSSE.spec.ts` → 仍全绿（未受影响）。
- **回滚方式**：删除 `ai-stream.ts` 与 `ai-stream.spec.ts`。
- **独立验收点（建议主题）**：`feat(ai-stream): add abortable SSE stream for global panel`。

### T0-5 共享消息模型扩展 cite refs 与页面动作类型

- [ ] **状态**：可执行
- **目标**：在 `TutorBlock` 上扩展只读 `refs` 与页面动作类型，让非工作台引用 `0x53→0xED`、位置、比例可渲染；工作台 `bytes` 语义不变。
- **涉及文件/模块**：`frontend/src/utils/tutor-message.ts`（修改）、`frontend/src/utils/tutor-message.spec.ts`（扩展）。
- **具体改动点**：
  - `TutorAction.kind` 扩展为 `'goto-step' | 'open-sbox' | 'open-workbench' | 'focus-sbox-byte' | 'focus-avalanche-byte'`；`normalizeAction` 按白名单解析，未知 kind 回退 `goto-step` 的现有行为或丢弃（任务实现时以「未知丢弃」为准，避免误动作）。
  - 新增 `AiCiteRef { label: string; value: string; kind: 'byte' | 'position' | 'stat' }`。
  - `cite` 块类型改为 `{ type: 'cite'; bytes: number[]; refs?: AiCiteRef[]; total?: number }`；`bytes` 仍只接受 0–15 整数，工作台行为不变。
  - `appendBlock` 解析 `refs`：`label/value` 转字符串，`kind` 白名单过滤，最多 6 条；非法项丢弃，不抛错。
  - `blocksToText` 在 cite 分支加入 `refs` 的 `label value`，供 live region 与摘要使用。
  - 本任务**不改** `TutorMessage.vue` 渲染（T1-4 做），保证阶段 0 无 UI 变化。
- **测试/证据前置**：是（先扩展 spec）。
- **依赖任务**：无；与 T0-2/T0-3/T0-4 可并行。
- **验收命令/断言**：
  - `cd frontend && npx vitest run src/utils/tutor-message.spec.ts` → 全绿。
  - 用例：工作台 `bytes` 过滤与 `total` 行为不变；`refs` 正常拼装；未知 `kind` 丢弃；`blocksToText` 含 `输入 0x53`、`输出 0xED`；`action.kind` 新值可解析。
- **回滚方式**：还原 `tutor-message.ts` 与 spec。
- **独立验收点（建议主题）**：`feat(tutor-message): extend cite refs and page actions`。

### T0-6 后端请求模型、上下文清洗与指纹

- [ ] **状态**：可执行
- **目标**：新增 `AiAskRequest` 与 `sanitize_context`，在服务端再做一次白名单/类型/范围校验；未知字段忽略，不 500；工作台 `TutorRequest` 不动。
- **涉及文件/模块**：`backend/models/schemas.py`（扩展）、`backend/services/ai_service.py`（新增）、`backend/tools/ai_probe.py`（新增，先 `--self-test`）。
- **具体改动点**：
  - `AiAskRequest`：`model_config = ConfigDict(extra="ignore")`；`page: Literal["home","sbox","avalanche"]`；`question: str = Field(min_length=1, max_length=500)` 且 `field_validator` 校验 trim 后非空；`context: dict = Field(default_factory=dict)`；`conversation_id: str = Field(min_length=1, max_length=128)`；`client_id: str | None = None`。
  - 不修改 `TutorRequest` 的 `extra="forbid"`、字段与 `client` 预留位。
  - `sanitize_context(page, raw) -> (clean: dict, missing: list[str], ignored: list[str])`：
    - `home`：只保留 `page`，`missing=[]`，`ignored` 列出其他键。
    - `sbox`：`mode` ∈ `forward/inverse`；`input/output` 0–255 且成对；`selected_hex` 可选且匹配 `0xNN`；缺一记 missing。
    - `avalanche`：`target` ∈ `plaintext/key`；`byte_index` 0–31；`bit_index` 0–7；`key_bits` ∈ 128/192/256；可选结论字段 `changed_bits` 0–128、`total_bits` 0–128、`rate` 0–1、`sweep_mean` 0–128；类型/范围错误丢弃并记 missing。
    - 未知字段只进 `ignored`，不报错、不回显值。
  - `normalize_question`：`unicodedata.normalize('NFKC', question).strip()` + 连续空白折叠；`context_fingerprint(page, clean)` 使用固定字段顺序紧凑 JSON + `hashlib.sha256` 前 16 位；`ai_cache_key(page, fingerprint, normalized_question)`。
  - `ai_probe.py --self-test`：直接 import `ai_service`，断言白名单、成对、越界、未知字段、固定样例指纹、跨页键不同；不启服务、不读数据库。
- **测试/证据前置**：是（`--self-test` 先写断言）。
- **依赖任务**：无；可与前端第一批并行。
- **验收命令/断言**：
  - `cd backend && python tools/ai_probe.py --self-test` → 全 PASS。
  - `python -m compileall -q .` → 通过。
  - `git diff -- backend/models/schemas.py` → 仅新增 `AiAskRequest`，`TutorRequest` 无改动。
  - `git diff -- backend/routers/tutor.py` → 为空。
- **回滚方式**：删除 `ai_service.py` 与 `ai_probe.py`；还原 `schemas.py`。
- **独立验收点（建议主题）**：`feat(api): add AI ask request model and context sanitizer`。

### T0-7 后端页面本地模板、LRU 缓存与事件迭代

- [ ] **状态**：可执行
- **目标**：无 key 时四栏目都有可用本地四块；缓存键含 page + 上下文指纹 + 规范化问题；跨页不串。
- **涉及文件/模块**：`backend/services/ai_service.py`（扩展）、`backend/tools/ai_probe.py`（扩展 self-test）；只读 `backend/services/tutor_service.py`、`backend/services/glossary.py`。
- **具体改动点**：
  - `build_local_blocks(page, clean, question)` 返回四块：
    - `home`：AES 是 16 字节分组、密钥控制轮密钥；不出现 `0xNN` 具体字节；cite `refs` 为「通用讲解」「无数据上下文」。
    - `sbox` 有上下文：当前方向 `input → output`、行/列查表、逆表反查、双射；cite `refs` 为「输入 0xNN」「输出 0xNN」「方向 正向/逆向」；无上下文提示先选中字节。
    - `avalanche` 有结果：`target` 第 `byte_index` 字节第 `bit_index` 位，`changed_bits/total_bits`、`rate` 百分比；cite `refs` 为「变化位数」「总位数」「比例」「位置」；无结果提示先跑一次实验。
  - `quotes_values` 由模板实际引用的 context 数值决定，不由 page 决定；`home` 固定 false。
  - `iter_ai_events(page, clean, question)`：`block` 开块 + 2 字/帧 `token`；`why` 首项带 `item:true`；cite 直接发完整块。
  - 独立的 `_ai_cache = OrderedDict()`，`MAX_CACHE = 128`；`get_cached` 命中 `move_to_end`；`put_cached` 淘汰最旧；只缓存 `source=local` 的完整块；不缓存 LLM。
  - 不修改 `tutor_service.py` 的 `_cache` / `cache_key` / `build_local_blocks`。
- **测试/证据前置**：是（扩展 `--self-test`）。
- **依赖任务**：T0-6。
- **验收命令/断言**：
  - `cd backend && python tools/ai_probe.py --self-test` → 全 PASS。
  - 用例：home 不含 `0x[0-9A-Fa-f]{2}`；sbox 含 `0x53`/`0xED`；avalanche 含 `62/128` 与比例；无结果含「先跑一次实验」；同页同上下文同问题第二次命中缓存；sbox 与 avalanche 同问题键不同；工作台 `cache_key` 未变。
- **回滚方式**：将 `ai_service.py` 还原到 T0-6 版本；删除 T0-7 新增 self-test 段。
- **独立验收点（建议主题）**：`feat(api): add page-level local templates and AI LRU cache`。

### T0-8 后端 `POST /api/ai/ask` 路由骨架（先只走本地）

- [ ] **状态**：可执行
- **目标**：新增不要求 `trace_id` 的通用 SSE 端点，事件协议与工作台一致；工作台 `/api/tutor/ask` 完全不动；不写 `tutor_logs`。
- **涉及文件/模块**：`backend/routers/ai.py`（新增）、`backend/main.py`（修改）；只读 `backend/routers/tutor.py`。
- **具体改动点**：
  - `APIRouter(prefix="/api/ai", tags=["AI 问答"])`；`POST /ask` 接收 `AiAskRequest`，返回 `StreamingResponse`，`media_type="text/event-stream"`。
  - SSE headers：`Cache-Control: no-cache`、`Connection: keep-alive`、`X-Accel-Buffering: no`（与 tutor 同值，单独定义，不跨路由导入）。
  - `_event_stream`：
    1. `sanitize_context` → 计算 `context_valid`、`context_missing`、`context_ignored`；
    2. 发 `meta`：`page/source/quotes_values/cache/conversation_id/model/context_valid/context_missing/context_ignored/structured=true`；
    3. 命中缓存：逐个 `block` 完整块 → `done`；
    4. 未命中：`iter_ai_events` 逐帧 → `done(finish=stop)`；
    5. 20s 本地 deadline：超时发 `done(finish=timeout, degraded=true)`，不额外发 `error`；
    6. 内部异常：生成器内转 `error(code='internal_error')`，记录 `logger.exception`（不含问题原文）。
  - 客户端断开：`await request.is_disconnected()`，检测到即 return，不写缓存。
  - 日志：`ai ask page=%s source=%s cache=%s context_valid=%s missing=%s qlen=%s qhash=%s`；`qhash=sha256(question)[:8]`；不打印问题全文、context 值、key、明文。
  - 不调用 `tutor_log.record()`；不新增表字段。
  - `main.py` 挂载 `ai_router`；不修改 tutor 路由、中间件与校验处理器。
- **测试/证据前置**：否（由 T0-9 探针覆盖）；先手工 `curl` 验证帧序。
- **依赖任务**：T0-6、T0-7。
- **验收命令/断言**：
  - 启动：`cd backend && python -m uvicorn main:app --port 8000`。
  - `curl -N http://127.0.0.1:8000/api/ai/ask -H "Content-Type: application/json" -d "{\"page\":\"home\",\"question\":\"AES 是什么？\",\"context\":{\"page\":\"home\"},\"conversation_id\":\"conv_probe_home\"}"` → 帧序 `meta → block/token × N → done`；`meta.source=local`、`quotes_values=false`。
  - `curl -s -o /dev/null -w "%{http_code}" ... -d "{\"page\":\"workbench\",...}"` → 400。
  - `git diff -- backend/routers/tutor.py backend/services/tutor_service.py` → 为空。
- **回滚方式**：删除 `routers/ai.py`；还原 `main.py` 的 import 与 `include_router`。
- **独立验收点（建议主题）**：`feat(api): add /api/ai/ask local SSE endpoint`。

### T0-9 `ai_probe.py` 全场景 HTTP 探针

- [ ] **状态**：可执行
- **目标**：用标准库 HTTP 客户端覆盖通用端点全部验收场景，成为阶段 0–4 的固定探针；不新增测试框架。
- **涉及文件/模块**：`backend/tools/ai_probe.py`（扩展）。
- **具体改动点**：
  - 支持两种模式：`--self-test`（纯函数）与 `python tools/ai_probe.py 8000`（HTTP）。
  - HTTP 场景：
    1. 无 key、`page=home`：`meta.source=local`、`quotes_values=false`、回答不含 `0xNN` 具体字节；
    2. `page=sbox`、0x53→0xED：回答含 `0x53`/`0xED`、`quotes_values=true`；
    3. `page=sbox` 无上下文：不 500，提示先选中；
    4. `page=avalanche` 有结果：`changed_bits=62,total_bits=128,rate=0.484375`，回答含 `62/128` 与 `48.4%`；
    5. `page=avalanche` 无结果：只传位置，`quotes_values=false`，提示先跑实验；
    6. 缓存：同请求连续两次，第二次 `meta.cache=true`、总耗时 ≤100ms、无逐字 token（或 token 数 0）；
    7. 白名单：`context` 含 `plaintext_hex/key_hex` → 200、`meta.context_ignored` 含字段名、回答不出现这些值；
    8. 顶层未知字段 → 200，行为不变；
    9. 非法 `page=practice` → 400 `validation_error`；
    10. 501 字 `question` → 400；空白 `question` → 400；
    11. `tutor_logs` 行数前后不变（dev 模式读 `backend/data/cipherlens.db`；读不到时打印 SKIP，不判失败）；
    12. 日志脱敏：配合 `output/GAI-backend.log` 检查，不含问题全文、`plaintext_hex` 值、key（探针只打印检查结果）。
  - 输出 PASS/FAIL 与关键字段；任一 FAIL 退出码非 0；不写入任何业务表。
- **测试/证据前置**：是（探针本身即测试）。
- **依赖任务**：T0-8。
- **验收命令/断言**：
  - `cd backend && python tools/ai_probe.py 8000` → 全 PASS。
  - `python tools/tutor_probe.py 8000` → 仍 PASS（工作台零回归）。
- **回滚方式**：删除 `ai_probe.py` 或还原到 T0-6 版本；不影响业务代码。
- **独立验收点（建议主题）**：`test(api): add AI ask probe`。

---

## 阶段 1 · 通用后端 + 全局面板 + 首页

> 阶段目标：非工作台入口不跳转；首页可用；无 key/断网/缓存/降级可用；工作台不改。
> 阶段验收门：`npm run build`、`npm test` 全绿；`python tools/ai_probe.py 8000` 全 PASS；Playwright 首页 3 条通过；工作台 `smoke` 两条不受影响。
> 阶段回滚：还原 `App.vue`、`AppShell.vue`、`HomeView.vue`、`TutorMessage.vue`、`utils/tutor-message.ts`；删除 `components/global-ai/*`、`composables/useDialogFocusTrap.ts`、`utils/ai-local-fallback.ts`、`stores/ai.ts`；后端端点可保留但不被调用。

### T1-1 `stores/ai.ts` 四页独立会话与 6 态状态机

- [ ] **状态**：可执行
- **目标**：用 Pinia 按 `home/sbox/avalanche/workbench` 维护独立会话；切页保留历史、中止活动流；刷新清空；单轮问答；工作台 11 态只读投影。
- **涉及文件/模块**：`frontend/src/stores/ai.ts`（新增）、`frontend/src/stores/ai.spec.ts`（新增）；依赖 `ai-context.ts`、`ai-prompts.ts`、`ai-stream.ts`、`useHealth.ts`。
- **具体改动点**：
  - `AiPhase = 'idle' | 'waiting' | 'streaming' | 'done' | 'error' | 'offline'`；`AiConversation` 字段：`page/conversationId/messages/draft/phase/errorCode/errorMessage/degraded/cacheHit/quotesValues/context/lastContext/announcement/updatedAt`。
  - `conversations` 用 `reactive<Record<PageKey, AiConversation>>`，首次访问懒创建；`conversationId = conv_<page>_<16hex>`，清空/刷新重建。
  - 状态：`panelOpen`、`workbenchTutorOpen`、`activePage`、`activeAbort`（非 reactive）、`health`（读 `useHealth` 单例，不复制）。
  - 动作：`openPanel(page)`（仅非 workbench）、`closePanel()`、`togglePanel(page)`、`openWorkbenchTutor()`、`closeWorkbenchTutor()`、`setContext(page, context)`、`submit(page, question, context)`、`abort(page, reason)`、`retry(page)`、`clear(page)`、`syncWorkbench(snapshot)`。
  - `submit`：trim + 1–500 校验；同页旧流 `abort('replaced')`；冻结 `lastContext`；计算指纹（仅本地兜底缓存/调试，不作为请求字段）；写 user 消息；`phase=waiting`；3s 后仍 waiting 则设置 `slowHint` 辅助文案（不作为 phase）；按 `health.llm` 选择 20s/55s 总阈值；调用 `startAiStream('/api/ai/ask', {page, question, context: toWireContext(...), conversation_id, client_id})`；回调按 page 闭包写入。
  - `onMeta`：`cacheHit/cache`、`quotesValues`、`source/model` 写入消息；缓存命中仍归 `done`，用 `cacheHit` 徽标；`quotes_values=false` 仍归 `done`，用 `quotesValues` 徽标。
  - `onDone`：写完整 assistant 消息、`phase=done`、live region 文案一次；`onError`：`llm_unavailable` 且已有内容 → `done` + `degraded`；`timeout/network_error` → `error`；`abort('interrupted')` → `error` + `errorCode='interrupted'`，不覆盖已写消息。
  - `retry`：复用同一条 user 消息，删除上一条 assistant 消息，重新冻结上下文；不重复写 user。
  - `clear(page)`：只清当前页；`abort(page,'cleared')`；清 messages/draft/error/degraded/lastContext；重建 `conversationId`。
  - `syncWorkbench(snapshot)`：按 design §1.3 表映射 11→6；只读投影，不回写 `TutorPanel`；workbench 消息保留一对 user/assistant。
  - 刷新：Pinia 内存自然清空；不写 `sessionStorage/localStorage`；`client_id` 仍走 `clientId.ts`。
- **测试/证据前置**：是（先写 `ai.spec.ts`）。
- **依赖任务**：T0-2、T0-3、T0-4、T0-5。
- **验收命令/断言**：
  - `cd frontend && npx vitest run src/stores/ai.spec.ts` → 全绿。
  - 用例：四页消息隔离；A 页 `streaming` 时 `abort('interrupted')` 后 A=`error/interrupted`、B=`idle`；清空 S 盒不影响首页；四页 `conversationId` 互不相同且不含 client；`new Pinia` 后四页空；请求体不含 `messages`；工作台 `cache→done`、`generic→done`、`interrupted→error`、`collapsed→done` 映射正确。
- **回滚方式**：删除 `stores/ai.ts` 与 `ai.spec.ts`。
- **独立验收点（建议主题）**：`feat(ai-store): add per-page conversations and six-phase state`。

### T1-2 全局宿主、四页常驻入口与应用壳去跳转

- [ ] **状态**：可执行
- **目标**：把入口提升到 `App.vue` 全局宿主，四页常驻 44×44；点击不再 `router.push('/workbench?ai=1')`；非工作台就地打开面板，工作台展开 E 区。
- **涉及文件/模块**：`frontend/src/App.vue`（修改）、`frontend/src/components/layout/AppShell.vue`（修改）、`frontend/src/components/global-ai/GlobalAiHost.vue`（新增）、`frontend/src/components/global-ai/GlobalAiLauncher.vue`（新增）；只读 `AiFab.vue`、`router/index.ts`。
- **具体改动点**：
  - `App.vue` 在 `RouterView`/`AppShell` 同级挂 `<GlobalAiHost />`；`bare` 与 `density` 逻辑不变。
  - `AppShell.vue` 移除 `<AiFab @open="openAi" />`、`openAi()` 与 `useRouter`；保留顶栏、导航、移动端菜单；`onKeydown` 增加 `if (aiStore.panelOpen) return`（面板自己处理 Esc）。
  - `GlobalAiLauncher.vue`：44×44、右下、`z-index: 40`、390 下 `right/bottom: var(--sp-3)`；`aria-label="打开 AI 助手（<页面名>）"`、`aria-haspopup="dialog"`、`aria-expanded`、`aria-controls="global-ai-panel"`；点击按 `route.name` 分派：`workbench` → `aiStore.openWorkbenchTutor()`；其余 → `aiStore.openPanel(pageKey)`。
  - `GlobalAiHost.vue`：计算当前 `pageKey`（`home/sbox/avalanche/workbench`）；记录触发元素 `lastTrigger`；`router.beforeEach/afterEach` 记录并 `abort(previousPage,'interrupted')`；Launcher 渲染条件 `!panelOpen && !(route.name==='workbench' && workbenchTutorOpen)`；`<Teleport to="body"><GlobalAiPanel v-if="panelOpen && route.name!=='workbench'" ... /></Teleport>`（面板本体由 T1-3 完成，本任务先搭壳）。
  - 不删除 `AiFab.vue`（保留文件，仅 AppShell 不再引用），避免影响历史证据与引用检索。
- **测试/证据前置**：否；T1-8 的 E2E 覆盖。
- **依赖任务**：T1-1。
- **验收命令/断言**：
  - `cd frontend && npm run build` → 通过。
  - `rg -n "router.push.*workbench.*ai" frontend/src` → 0。
  - 手工在 `/`、`/sbox`、`/avalanche` 点击入口：`location.pathname` 不变、`history.length` 不变、面板出现；工作台点击后 E 区展开（T3-1 完成后最终生效，本任务先不验证工作台）。
- **回滚方式**：还原 `App.vue`、`AppShell.vue`；删除 `GlobalAiHost.vue`、`GlobalAiLauncher.vue`。
- **独立验收点（建议主题）**：`feat(global-ai): mount global host and remove workbench redirect`。

### T1-3 `GlobalAiPanel` 家族、焦点陷阱与极简 UI

- [ ] **状态**：可执行
- **目标**：非工作台模态抽屉：标题 + 序号化推荐 + 空输入；消息复用 `TutorMessage`；错误/降级行内条；Esc/焦点归还/live region/390 全宽。
- **涉及文件/模块**：`frontend/src/components/global-ai/GlobalAiPanel.vue`、`GlobalAiMessage.vue`、`GlobalAiPrompts.vue`（新增）；`frontend/src/composables/useDialogFocusTrap.ts`（新增）；`frontend/src/styles/tokens.css`（仅追加布局变量）。
- **具体改动点**：
  - `GlobalAiPanel` props：`open/page/conversation/prompts/contextLine/reducedMotion`；emits：`close/submit/retry/clear/action`。
  - 结构：`h2#global-ai-title` 标题「AI 助手 · 页面短名」+ 唯一关闭按钮 `aria-label="关闭 AI 助手"`+ 一行上下文；消息区（用户问题行 + `GlobalAiMessage`）；推荐列表；错误/降级条；`textarea rows=2` 默认空；生成中「停止」；发送；底部次级「清空本页对话」。
  - `role="dialog"`、`aria-modal="true"`、`aria-labelledby="global-ai-title"`、`tabindex="-1"`；打开聚焦关闭按钮，有草稿时聚焦 textarea；Tab/Shift+Tab 循环（`useDialogFocusTrap`）；Esc `preventDefault + stopPropagation` 只关面板。
  - 遮罩：`z-index: 55`、面板 `60`、Launcher `40`；点击遮罩关闭；面板打开时 `document.body` 记录并 `overflow: hidden`，关闭恢复（在 Host 做）。
  - live region：`<p class="sr-only" aria-live="polite" aria-atomic="true">`；`done`/`error`/`offline` 各写一次，token 不写；文案：回答完成/回答失败可重试/已切换本地讲解/上次生成已中断。
  - 错误码转人话：新增面板内 `ERROR_TEXT` 同口径（不修改 `TutorPanel`）；提供「重试」。
  - 390：`width:100vw`、`max-width:100vw`、`height:100dvh`、`top:0`；所有行 `min-width:0` + `overflow-wrap:anywhere`；推荐/chip/动作 `flex-wrap:wrap`；输入 `font-size:16px`；发送/停止 44×44；底部 `env(safe-area-inset-bottom)`。
  - 视觉：手写 CSS，复用 `--paper/--ink/--line/--accent/--sp/--r-control/--shadow`；仅追加 `--z-ai-scrim:55`、`--z-ai-panel:60`、`--ai-panel-w:420px` 三个布局变量；不改现有 token 值。
  - `GlobalAiPrompts`：序号 + 文本；点击即 `submit`，不填充输入框；最多 3 条。
  - `GlobalAiMessage`：用户问题行 + `TutorMessage`；历史只读，最后一条可流式光标。
- **测试/证据前置**：否（组件行为由 T1-8 E2E 覆盖）；先 `npm run build`。
- **依赖任务**：T1-1、T1-2、T0-5。
- **验收命令/断言**：
  - `cd frontend && npm run build` → 通过。
  - `rg -n "role=\"dialog\"" frontend/src/components/global-ai` → 仅 `GlobalAiPanel` 一处。
  - 手工：390×844 打开面板无横向滚动；`document.documentElement.scrollWidth <= 390`；关闭按钮可点；Esc 只关面板；关闭后焦点回 Launcher。
- **回滚方式**：删除 4 个新增文件；删除 `tokens.css` 追加的 3 个变量。
- **独立验收点（建议主题）**：`feat(global-ai): add modal panel with focus trap and live region`。

### T1-4 `TutorMessage` 的 `refs` 渲染（工作台 bytes 分支不变）

- [ ] **状态**：可执行
- **目标**：让非工作台引用以只读/可定位 chip 呈现，同时不复制 F09 四块语义，不改工作台 `#N` chip 行为。
- **涉及文件/模块**：`frontend/src/components/region-e/TutorMessage.vue`（修改）；依赖 `utils/tutor-message.ts`。
- **具体改动点**：
  - 模板把 `v-else` 改为显式 `v-else-if="block.type === 'cite'"`；`block.bytes` 非空时保持现有 `#N` 可点击 chip + `共 N 格` + `cite` 事件。
  - `block.refs` 存在时渲染只读 chip：`输入 0x53`、`输出 0xED`、`变化 62/128`、`比例 48.4%`；`kind` 为 `byte/position` 且页面可定位时渲染为按钮 `data-action="ai-cite-ref"`，点击 `emit('action', {label, kind, value})`，**不自动执行**。
  - `moreCount` 只对 `bytes` 生效；`refs` 的 `total` 仅用于文案。
  - 不新增第二套四块模板；`conclusion/why/next` 保持原样；来源徽标、流式光标、`prefers-reduced-motion` 不变。
- **测试/证据前置**：是（`tutor-message.spec.ts` 已在 T0-5 覆盖数据层；本任务用 build + 阶段 2 E2E）。
- **依赖任务**：T0-5、T1-3。
- **验收命令/断言**：
  - `cd frontend && npm run build` → 通过。
  - `npx vitest run src/utils/tutor-message.spec.ts` → 仍全绿。
  - 手工工作台：第 1 步提问，`#N` chip 仍可点开字节抽屉；`共 N 格` 正常。
- **回滚方式**：还原 `TutorMessage.vue`。
- **独立验收点（建议主题）**：`feat(tutor-message): render cite refs without changing workbench chips`。

### T1-5 首页写空上下文与「通用讲解」标识

- [ ] **状态**：可执行
- **目标**：首页明确「无数据上下文」，回答不得编造字节；入口仍由全局 Launcher 承担。
- **涉及文件/模块**：`frontend/src/views/HomeView.vue`（修改）；依赖 `stores/ai.ts`。
- **具体改动点**：
  - `onMounted` 调用 `aiStore.setContext('home', { page: 'home' })`；不自动打开面板、不自动提问。
  - 不新增页面内 AI 按钮；不改变现有 CTA 与 `HeroMatrix`。
  - 面板上下文行由 `describeContext('home', ...)` 显示「通用讲解 · 未引用本页数值」（T1-3 已支持）。
- **测试/证据前置**：否；T1-8 E2E 覆盖。
- **依赖任务**：T1-1、T1-3。
- **验收命令/断言**：
  - `cd frontend && npm run build` → 通过。
  - 首页打开面板：标题「AI 助手 · 首页」；上下文行含「通用讲解」；提问回答不含 `0xNN` 具体字节（`ai_probe` 同步验证）。
- **回滚方式**：还原 `HomeView.vue`。
- **独立验收点（建议主题）**：`feat(home): register empty AI context`。

### T1-6 后端通用 LLM 提示词与降级流

- [ ] **状态**：可执行
- **目标**：有 key 时通用页可走模型；无 key/失败时保持同一事件协议并降级本地；不修改工作台 LLM 路径。
- **涉及文件/模块**：`backend/services/llm_service.py`（扩展）、`backend/routers/ai.py`（扩展）；只读 `backend/services/tutor_service.py`。
- **具体改动点**：
  - 新增 `GENERAL_SYSTEM_PROMPT`：角色「AES 教学助手」；只讲当前页面；只允许引用 context 数值；禁止编造；中文；输出【结论】【为什么】【下一步】；不超过 220 字；home 不得出现具体字节值；不主动做数值合理性核对（D-G11）。
  - `build_general_messages(page, context, question)`：system + user JSON（page/context/question，context 已清洗）。
  - `general_allowed_values(context, question)`：收集 context 中所有数值 + 问题中显式 `0xNN`；用于 `BlockAssembler.hex_outside` 审计，只记账不中断。
  - `stream_general_answer(page, context, question, cite_block)`：复用 `BlockAssembler`；cite 由 `ai_service.build_local_blocks` 提供的 `refs` 块补发，避免误显示字节格；不改 `BlockAssembler` 默认 bytes 行为（必要时新增可选参数，默认保持现状）。
  - 降级：`enabled=false` 直接本地（不发网络）；首字前失败重试一次（`RETRY_FACTOR`）；仍失败且无内容 → 本地 + `degraded=true`；已有内容 → 保留部分 + `error.llm_unavailable(partial=true)`；LLM 45s / 本地 20s，沿用 tutor 常量。
  - 不修改 `SYSTEM_PROMPT`、`build_messages`、`stream_answer`、`allowed_hex` 的现有语义。
  - `routers/ai.py` 按 `llm_service.enabled()` 选择路径；`meta.source` 与实际来源一致；`meta.model` 不泄露 key。
- **测试/证据前置**：是（`ai_probe` 增加有 key 时的可选场景；无 key 环境记录「未配置，跳过网络路径」）。
- **依赖任务**：T0-7、T0-8。
- **验收命令/断言**：
  - 无 key：`cd backend && python tools/ai_probe.py 8000` → 全 PASS，`meta.source=local`。
  - 有 key（可选）：同一探针 → `meta.source=llm`，事件仍仅 `meta/block/token/done/error`；`llm_probe.py` 工作台仍 PASS。
  - `git diff -- backend/services/tutor_service.py` → 为空。
- **回滚方式**：还原 `llm_service.py`、`routers/ai.py` 到 T0-8 版本。
- **独立验收点（建议主题）**：`feat(llm): add general page prompt and fallback stream`。

### T1-7 前端页面级本地兜底（后端不可达不空白）

- [ ] **状态**：可执行
- **目标**：后端 500/断网时，四页仍能就地显示最小四块本地讲解，不跳转、不空白。
- **涉及文件/模块**：`frontend/src/utils/ai-local-fallback.ts`（新增）、`frontend/src/utils/ai-local-fallback.spec.ts`（新增）、`frontend/src/stores/ai.ts`（修改）。
- **具体改动点**：
  - `buildLocalFallback(page, lastContext, question)` 返回四块：结论/为什么/下一步/cite refs；`source='local'`、`degraded=true`、`errorCode='network_error'`。
  - home 不出现具体字节；sbox 有上下文时引用 input/output；avalanche 有结果时引用位置/变化位数/比例；无上下文时提示先操作页面。
  - store 在 `network_error`（fetch 失败/非 2xx）时调用该兜底，不再次请求 `/api/ai/ask`；`onDone` 不自动执行动作。
  - 不改 `TutorPanel` 的 `fallbackBlocks`；工作台仍走自己的本地兜底。
- **测试/证据前置**：是（先写 spec）。
- **依赖任务**：T1-1、T0-3、T0-5。
- **验收命令/断言**：
  - `cd frontend && npx vitest run src/utils/ai-local-fallback.spec.ts` → 全绿。
  - 用例：home 无 `0xNN`；sbox 引用 0x53/0xED；avalanche 引用 62/128/48.4%；四块齐全；不依赖后端。
  - 停后端手工打开面板提问：出现「本地讲解」，无空白、无跳转（阶段 4 复验）。
- **回滚方式**：删除兜底文件；还原 `stores/ai.ts` 的调用点。
- **独立验收点（建议主题）**：`feat(ai-store): add page-level local fallback`。

### T1-8 首页闭环验收（不跳转 / 焦点 / Esc / 播报）

- [ ] **状态**：可执行
- **目标**：把阶段 1 的首页链路固化为 E2E 与证据，作为后续阶段的回归基线。
- **涉及文件/模块**：`frontend/e2e/global-ai.spec.ts`（新增，先写 #1/#2/#14）、`evidence/acceptance/GAI-home.md`（新增）。
- **具体改动点**：
  - E2E #1：`/` 点 Launcher → URL 仍 `/`、`history.length` 不变、`[role=dialog]` 可见、焦点在关闭按钮。
  - E2E #2：Esc → 面板关闭、焦点回 Launcher、URL/history 不变。
  - E2E #14：完成/错误各 1 条 live region 文本；token 阶段不新增。
  - 证据写：A1/A2/A9/A15/A16/A17 覆盖、命令、实测值、未达项。
- **测试/证据前置**：是（E2E 先写）。
- **依赖任务**：T1-1–T1-7。
- **验收命令/断言**：
  - `cd frontend && npm run build` → 通过。
  - `npx playwright test --config=e2e/playwright.config.ts e2e/global-ai.spec.ts --grep "首页"` → 3/3。
  - `python tools/ai_probe.py 8000` → home 场景 PASS。
- **回滚方式**：删除 E2E 用例与 `GAI-home.md`；不影响业务代码。
- **独立验收点（建议主题）**：`test(e2e): cover home global AI loop`。

---

## 阶段 2 · S 盒 / 雪崩接入

> 阶段目标：两页上下文、推荐问题、显式动作、无结果提示；不自动跳转、不自动跑实验、不自动切逆向表。
> 阶段验收门：`ai_probe` sbox/avalanche 全场景 PASS；E2E #3/#4/#7/#8 通过；跨页缓存 A14 通过；`npm run build` 通过。
> 阶段回滚：还原 `SBoxView.vue`、`AvalancheView.vue`；删除 `ai-prompts.ts` 页面分支、动作按钮与事件监听；首页/全局面板保留。

### T2-1 S 盒上下文采集与页内定位

- [ ] **状态**：可执行
- **目标**：S 盒实时上下文（方向、输入、输出、选中值）写入 store；回答引用当前字节；页内定位只改选中，不改 URL。
- **涉及文件/模块**：`frontend/src/views/SBoxView.vue`（修改）；只读 `frontend/src/engine/sbox.ts`、`components/sbox/SBoxDetail.vue`。
- **具体改动点**：
  - `watch([inverse, selected], () => aiStore.setContext('sbox', snapshot), { immediate: true })`；`output = inverse ? INV_SBOX[selected] : SBOX[selected]`；`selected_hex` 大写两位。
  - 不自动打开面板、不自动提问、不改变 URL；`?b=` 逻辑与 `setMode` 保持同一对字节的行为不变。
  - 监听 `window` 自定义事件 `cipherlens:ai-focus-sbox-byte`（detail: number），设置 `selected` 并滚动到对应格子；仅由用户点击 AI 动作按钮触发。
  - 不改网格几何、缩放、`SBoxDetail` 的显示逻辑。
- **测试/证据前置**：否；T2-6 E2E/探针覆盖。
- **依赖任务**：T1-1。
- **验收命令/断言**：
  - `cd frontend && npm run build` → 通过。
  - 手工：选中 0x53 → 打开面板 → 上下文行「当前：0x53 → 0xED · 正向」；切逆向 → 保持同一对字节并更新上下文。
  - `page.url()` 不因选中/切方向改变。
- **回滚方式**：还原 `SBoxView.vue`。
- **独立验收点（建议主题）**：`feat(sbox): publish AI page context`。

### T2-2 雪崩上下文采集与页内定位

- [ ] **状态**：可执行
- **目标**：雪崩实时上下文（目标、字节、位、密钥位数、变化位数/比例/连做均值）写入 store；无结果只传位置；不传明文/密钥；不自动跑。
- **涉及文件/模块**：`frontend/src/views/AvalancheView.vue`（修改）。
- **具体改动点**：
  - `watch([target, byteIndex, keyBits, result, sweep], () => aiStore.setContext('avalanche', snapshot), { immediate: true })`。
  - `key_bits = keyHex.length * 4`（16/24/32 字节 → 128/192/256）；`bit_index` 当前固定 0（沿用页面现状）。
  - 有 `result` 时传 `changed_bits/total_bits/rate`；有 `sweep` 时传 `sweep_mean`；无结果只传位置字段，不传 `plaintext_hex/key_hex/input_byte_before/input_byte_after`。
  - 输入变化只更新上下文，不自动打开面板、不自动提问、不自动切换 target/byte、不自动重跑。
  - 监听 `cipherlens:ai-focus-avalanche-byte`（detail: number），设置 `byteIndex`（触发既有 220ms 防抖重算，属于用户点击动作）。
  - 不改位图色阶、结果区布局、输入校验。
- **测试/证据前置**：否；T2-6 覆盖。
- **依赖任务**：T1-1。
- **验收命令/断言**：
  - `cd frontend && npm run build` → 通过。
  - 手工：跑一次实验（第 3 字节）→ 上下文行含「第 3 字节 · 62/128 位 · 48.4%」；清空/非法输入 → 上下文行「先跑一次实验」。
  - 网络面板：`/api/ai/ask` 请求体不含 `plaintext_hex/key_hex/input_byte_*`。
- **回滚方式**：还原 `AvalancheView.vue`。
- **独立验收点（建议主题）**：`feat(avalanche): publish AI page context`。

### T2-3 推荐问题随上下文接入面板

- [ ] **状态**：可执行
- **目标**：S 盒/雪崩的推荐问题随当前上下文变化；点击即提交，输入区保持空。
- **涉及文件/模块**：`frontend/src/components/global-ai/GlobalAiPrompts.vue`（修改）、`GlobalAiPanel.vue`（修改）；依赖 `data/ai-prompts.ts`。
- **具体改动点**：
  - 面板用 `promptsFor(page, conversation.context)` 计算推荐；无消息时显示在消息区顶部，有消息时固定在输入区上方，最多 3 条。
  - 点击推荐 → `emit('submit', question)`；不填充 textarea；不自动发送第二条。
  - `sbox` 的 `0xNN` 与页面显示一致（大写两位）；`avalanche` 无结果时显示「先跑一次实验」。
  - `workbench` 返回空数组，不渲染（工作台沿用 `QuickAsk`）。
- **测试/证据前置**：否；`ai-prompts.spec.ts` 已在 T0-3 覆盖数据层。
- **依赖任务**：T0-3、T1-3、T2-1、T2-2。
- **验收命令/断言**：
  - `cd frontend && npm run build` → 通过。
  - 手工：S 盒选中 0x53 → 推荐第 1 条含 `0x53`/`0xED`；雪崩无结果 → 第 1 条含「先跑一次实验」；输入框仍为空。
- **回滚方式**：还原 `GlobalAiPrompts.vue`、`GlobalAiPanel.vue` 的推荐接线。
- **独立验收点（建议主题）**：`feat(global-ai): wire context-aware prompts`。

### T2-4 面板上下文行与无上下文提示

- [ ] **状态**：可执行
- **目标**：面板只显示一行上下文；无上下文时给可读提示，不堆说明。
- **涉及文件/模块**：`frontend/src/components/global-ai/GlobalAiPanel.vue`（修改）；依赖 `utils/ai-context.ts` 的 `describeContext`。
- **具体改动点**：
  - `home`：「通用讲解 · 未引用本页数值」。
  - `sbox` 有上下文：「当前：0x53 → 0xED · 正向/逆向」；无上下文：「先在 S 盒里选中一个字节」。
  - `avalanche` 有结果：「当前：明文/密钥第 N 字节 · 62/128 位 · 48.4%」；无结果：「先跑一次实验，才能引用真实数字」。
  - 仅一行；不在输入区上方堆多行说明；不显示工作台步进/播放/诊断。
- **测试/证据前置**：否；E2E #3/#7 覆盖。
- **依赖任务**：T1-3、T2-1、T2-2。
- **验收命令/断言**：
  - `npm run build` → 通过。
  - 手工四态：home/sbox 有/sbox 无/avalanche 有/无；上下文行均不超过一行。
- **回滚方式**：还原 `GlobalAiPanel.vue` 的上下文行。
- **独立验收点（建议主题）**：`feat(global-ai): add one-line context summary`。

### T2-5 显式动作按钮（绝不自动路由）

- [ ] **状态**：可执行
- **目标**：回答内动作只以按钮出现；S 盒/雪崩页内定位不改 URL；首页跨页动作只在用户点击时执行；`onDone` 不自动执行。
- **涉及文件/模块**：`frontend/src/components/region-e/TutorMessage.vue`（修改）、`frontend/src/components/global-ai/GlobalAiPanel.vue`（修改）、`GlobalAiHost.vue`（修改）、`SBoxView.vue`/`AvalancheView.vue`（动作监听）。
- **具体改动点**：
  - `focus-sbox-byte`：用户点击 → `window.dispatchEvent(new CustomEvent('cipherlens:ai-focus-sbox-byte', { detail: value }))`；S 盒设置 `selected`，不改变 URL。
  - `focus-avalanche-byte`：用户点击 → `window.dispatchEvent(new CustomEvent('cipherlens:ai-focus-avalanche-byte', { detail: value }))`；雪崩设置 `byteIndex`，不改变 URL。
  - `open-workbench`：仅首页动作；用户点击 → `router.push('/workbench?step=N')`；不自动执行。
  - `open-sbox`/`goto-step`：工作台既有语义不变（不在本任务改动）。
  - **不做** D-G10 动作：S 盒不自动切逆向表；雪崩不自动改 target/bit、不自动重跑。
  - `onDone` 只写消息与播报，不遍历动作执行。
- **测试/证据前置**：否；T2-6 E2E 覆盖"点击前 URL 不变、点击后才变化"。
- **依赖任务**：T0-5、T1-4、T2-1、T2-2、T2-4。
- **验收命令/断言**：
  - `npm run build` → 通过。
  - 手工：S 盒回答出现「定位 0x53」按钮；点击后 URL 不变、格子选中；未点击时无任何跳转。
  - 首页回答出现「去工作台看一次」按钮；未点击前 URL 不变；点击后才跳转。
- **回滚方式**：还原 `TutorMessage.vue`、`GlobalAiPanel.vue`、`GlobalAiHost.vue`、两个 View 的监听。
- **独立验收点（建议主题）**：`feat(global-ai): add explicit page action buttons`。

### T2-6 阶段 2 验收门（S 盒 / 雪崩 + 跨页缓存）

- [ ] **状态**：可执行
- **目标**：固化两页上下文、无结果提示、动作不自动执行、跨页缓存不串的证据。
- **涉及文件/模块**：`frontend/e2e/global-ai.spec.ts`（追加 #3/#4/#7/#8）、`evidence/acceptance/GAI-sbox-avalanche.md`（新增）。
- **具体改动点**：
  - E2E #3：`/sbox` 点 Launcher → URL 仍 `/sbox`、标题「AI 助手 · S 盒」、上下文行含 `0x53 → 0xED`。
  - E2E #4：S 盒提问 → 回答含 `0x53`/`0xED`、来源徽标「本地讲解」或「AI」、不自动跳转。
  - E2E #7：雪崩无结果 → 面板先显示「先跑一次实验」；不自动跑实验。
  - E2E #8：雪崩跑一次后打开面板 → 上下文行含变化位数/比例；提问回答含数字。
  - 证据写 A7/A8/A14、命令、实测值、未达项。
- **测试/证据前置**：是（E2E 先写）。
- **依赖任务**：T2-1–T2-5。
- **验收命令/断言**：
  - `cd backend && python tools/ai_probe.py 8000` → sbox/avalanche 全 PASS；跨页同问题不互为缓存（A14）。
  - `cd frontend && npx playwright test --config=e2e/playwright.config.ts e2e/global-ai.spec.ts --grep "S 盒|雪崩"` → 4/4。
  - `npm run build` → 通过。
- **回滚方式**：删除本阶段 E2E 段与证据文件；代码回滚按各任务。
- **独立验收点（建议主题）**：`test(e2e): cover sbox and avalanche AI context`。

---

## 阶段 3 · 工作台统一入口与回归

> 阶段目标：工作台右下 `AiFab` 展开 E 区；收起态单入口；`?ai=1`/F 键/第 0 步禁用不变；不弹全局面板；无双面板/双输入框。
> 阶段验收门：E2E #9/#10/#11 通过；`smoke` 工作台两条通过；F17 关键态抽查（waiting/streaming/done/cache/offline/error）；`tutor_probe` 通过。
> 阶段回滚：还原 `WorkbenchView.vue`、`WorkbenchLayout.vue`、`TutorPanel.vue`；`GlobalAiLauncher` 工作台分支改回隐藏；全局三页入口保留。

### T3-1 工作台入口状态同步（`tutorCollapsed` ↔ store）

- [ ] **状态**：可执行
- **目标**：工作台点击全局 Launcher 展开 E 区并聚焦输入框；`?ai=1`、F 键、A 键行为不变；不弹全局面板。
- **涉及文件/模块**：`frontend/src/views/WorkbenchView.vue`（修改）、`frontend/src/stores/ai.ts`（修改）。
- **具体改动点**：
  - `watch(() => aiStore.workbenchTutorOpen, open => { tutorCollapsed.value = !open })`；`watch(tutorCollapsed, collapsed => aiStore.setWorkbenchTutorOpen(!collapsed))`；用一个 `syncing` 标志避免循环写入。
  - `toggleTutor()` 改为写 `aiStore.toggleWorkbenchTutor()`，并保留 `announcement` 文案。
  - `?ai=1`：保持 `router.replace` 删除 `ai`，同时调用 `aiStore.openWorkbenchTutor()`；不是入口跳转。
  - `focusAsk()`：若 E 区收起先展开；`nextTick` 后聚焦 `textarea[aria-label="向 AI 提问"]`；第 0 步/`askDisabled` 时改为聚焦 E 区关闭按钮（不强行聚焦 disabled textarea）。
  - `onToggleAi`（F 键）沿用 `toggleTutor()`；`onEscape` 优先级不变。
- **测试/证据前置**：否；E2E #9/#11 覆盖。
- **依赖任务**：T1-2、T1-3。
- **验收命令/断言**：
  - `cd frontend && npm run build` → 通过。
  - 手工 `/workbench` 点 Launcher → E 区展开、`textarea` 聚焦；再点 × 收起；`[role=dialog]` 数量 0。
  - 手工 `/workbench?ai=1` → E 区展开、URL 中 `ai` 被移除；无跳转。
  - 第 0 步按 A → 聚焦关闭按钮，不报错。
- **回滚方式**：还原 `WorkbenchView.vue`；删除 `stores/ai.ts` 的工作台动作（若 T1-1 已含则只还原调用）。
- **独立验收点（建议主题）**：`feat(workbench): sync E-region with global AI entry`。

### T3-2 `WorkbenchLayout` 收起态入口移除、展开态关闭按钮保留

- [ ] **状态**：可执行（按 D-G2 设计默认）
- **目标**：工作台只保留一个入口：收起态由右下 `AiFab` 承担；展开态保留 E 区头部 `×`；不出现右上/右下双入口。
- **涉及文件/模块**：`frontend/src/components/layout/WorkbenchLayout.vue`（修改）。
- **具体改动点**：
  - `v-if="tutorCollapsed"` 分支不再渲染 44px `AI` 按钮（保留 E 区头部容器，不显示按钮）。
  - `v-else` 分支保留标题与 `data-action="toggle-tutor"` 的关闭按钮，`aria-controls="ai-panel-body"`、`aria-expanded="true"` 不变。
  - `data-ai-state`、E 区容器、五区布局、`RoundSummary` 浮层逻辑不变。
  - 不删除 E 区、不修改 `TutorPanel`。
- **测试/证据前置**：否；E2E #9 + 手工 F17 锚点。
- **依赖任务**：T3-1。
- **验收命令/断言**：
  - `npm run build` → 通过。
  - 手工 `/workbench` 收起态：页面内无 44px `AI` 按钮；右下 Launcher 可见；点击展开后 Launcher 隐藏、E 区 `×` 可见。
  - `document.querySelectorAll('[data-action="toggle-tutor"]').length` 展开态为 1。
- **回滚方式**：还原 `WorkbenchLayout.vue`（恢复右上按钮）。
- **独立验收点（建议主题）**：`feat(workbench): unify E-region entry through global launcher`。

### T3-3 `TutorPanel` 只读快照投影（不改 11 态）

- [ ] **状态**：可执行
- **目标**：把工作台阶段/消息投影到 store 的 workbench 会话，供统一会话模型展示；`TutorPanel` 仍是唯一事实源。
- **涉及文件/模块**：`frontend/src/components/region-e/TutorPanel.vue`（修改，仅新增 emit）、`WorkbenchLayout.vue`（透传）、`WorkbenchView.vue`（接收）、`stores/ai.ts`（消费）。
- **具体改动点**：
  - `TutorPanel` 新增 `emit('snapshot', { phase, question, blocks, source, model, errorCode, errorMessage, degraded })`；在 `phase`、`blocks`、`source/model`、`error`、`degraded` 变化时 `watch` 触发；不改变任何状态机逻辑。
  - `WorkbenchLayout` 增加 `@snapshot="$emit('snapshot', $event)"`。
  - `WorkbenchView` 接收 `@snapshot="aiStore.syncWorkbench($event)"`。
  - `stores/ai.ts` 按 design §1.3 映射 11→6；workbench 会话消息保留一对 user/assistant；`collapsed` 映射 `done` 并保留 `collapsed` 标记；`cache/generic` 映射 `done` 并保留 `cacheHit/quotesValues`。
  - store 不回写 `TutorPanel`；不改变 11 态、3s/20s/55s、缓存直出、MORE、chip、动作。
- **测试/证据前置**：是（`ai.spec.ts` 增加投影用例）。
- **依赖任务**：T1-1、T3-1。
- **验收命令/断言**：
  - `npx vitest run src/stores/ai.spec.ts` → 投影用例全绿。
  - `npm run build` → 通过。
  - 手工工作台：提问 → `data-phase` 从 waiting/streaming 到 done；store 投影为 `done`；切步 → `collapsed` 投影为 `done + collapsed`。
- **回滚方式**：删除 `TutorPanel` 的 emit 与三个消费点。
- **独立验收点（建议主题）**：`feat(workbench): project tutor snapshots into AI store`。

### T3-4 双面板/双输入框防护与 Esc 优先级

- [ ] **状态**：可执行
- **目标**：任意时刻最多一个 AI 面板/一个提问输入框；面板打开时 Esc 只关面板；工作台 Space/→ 不被面板拦截。
- **涉及文件/模块**：`frontend/src/components/global-ai/GlobalAiHost.vue`、`GlobalAiPanel.vue`、`AppShell.vue`、`WorkbenchView.vue`（修改）。
- **具体改动点**：
  - `aiStore.panelOpen` 与 `aiStore.workbenchTutorOpen` 互斥：`openPanel` 仅在 `page !== 'workbench'` 时置 `panelOpen=true`；`openWorkbenchTutor` 仅在 `route.name==='workbench'` 时置 `workbenchTutorOpen=true` 并确保 `panelOpen=false`。
  - `GlobalAiPanel` 渲染条件加 `route.name !== 'workbench'`；Launcher 条件 `!panelOpen && !(route.name==='workbench' && workbenchTutorOpen)`。
  - `AppShell` 的 window `keydown` 在 `aiStore.panelOpen` 时直接 return；面板内 Esc `preventDefault + stopPropagation`。
  - 工作台 E 区不是模态：不阻止 Space/→；`onEscape` 既有优先级不变（引导 > 小结 > 帮助 > 密钥抽屉 > 字节抽屉 > AI 生成 > 批注 > 演示 > 播放）。
  - 面板打开时 `document.body` 滚动锁定与关闭恢复（在 Host 做）。
- **测试/证据前置**：否；E2E #9/#13 + 手工。
- **依赖任务**：T1-2、T3-1、T3-2。
- **验收命令/断言**：
  - `npm run build` → 通过。
  - 手工/Playwright：任意时刻 `document.querySelectorAll('[role="dialog"]').length <= 1`；`textarea[aria-label="向 AI 提问"]` 数量 ≤1。
  - 非工作台面板打开按 Space/→：页面无播放/步进副作用；Esc 只关面板。
  - 工作台 E 区展开按 Space：播放仍响应（回归项）。
- **回滚方式**：还原 Host/Panel/AppShell 的条件与 Esc 处理；工作台逻辑未改则无需回滚。
- **独立验收点（建议主题）**：`fix(global-ai): guard against dual panels and Esc conflicts`。

### T3-5 阶段 3 验收门（工作台入口 + F17 回归）

- [ ] **状态**：可执行
- **目标**：固化工作台单入口、E 区 11 态、`?ai=1`、无全局抽屉的证据。
- **涉及文件/模块**：`frontend/e2e/global-ai.spec.ts`（追加 #9/#10/#11）、`evidence/acceptance/GAI-workbench.md`（新增）。
- **具体改动点**：
  - E2E #9：`/workbench` 点 Launcher → E 区展开；`[role=dialog]` 数量 0；`textarea[aria-label="向 AI 提问"]` 数量 1；Launcher 隐藏。
  - E2E #10：第 1 步提问 → `data-phase` 出现 `streaming` 后到 `done/cache`；`#N` chip 可点开抽屉；`goto-step` 可用。
  - E2E #11：直接访问 `/workbench?ai=1` → E 区展开；URL 中 `ai` 被移除；无跳转。
  - 证据写 A2/A6/A15/A19、命令、实测值、未达项；注明「F17 11 态未逐态重跑，只抽查 6 态」。
- **测试/证据前置**：是（E2E 先写）。
- **依赖任务**：T3-1–T3-4。
- **验收命令/断言**：
  - `npx playwright test --config=e2e/playwright.config.ts e2e/global-ai.spec.ts --grep "工作台"` → 3/3。
  - `npx playwright test --config=e2e/playwright.config.ts e2e/smoke.spec.ts --grep "载入工作台|提问 SSE"` → 2/2。
  - `python tools/tutor_probe.py 8000` → PASS。
  - F17 抽查：`?debug=tutor` 切换 waiting/streaming/done/cache/offline/error，阶段名与文案不变。
- **回滚方式**：删除本阶段 E2E 段与证据文件；代码回滚按 T3-1–T3-4。
- **独立验收点（建议主题）**：`test(e2e): cover workbench unified AI entry`。

---

## 阶段 4 · 全量回归与证据

> 阶段目标：构建、单测、探针、E2E、Docker SSE、Lighthouse；只追加证据；明确不重跑项与已知边界。
> 阶段验收门：`npm run typecheck`、`npm test`、`npm run build`；`ai_probe`/`tutor_probe`；Playwright 全量；Docker SSE；Lighthouse；证据文件齐全。
> 阶段回滚：不回滚代码；指标不达记录为已知边界，并回滚对应阶段（1/2/3）。

### T4-1 工程回归（类型、单测、构建、依赖数）

- [ ] **状态**：可执行
- **目标**：证明 `vue-tsc` 0 error、单测全绿、构建通过、依赖数不变。
- **涉及文件/模块**：无业务源码；`evidence/acceptance/GAI-build.md`（新增）。
- **具体改动点**：
  - 记录 `npm run typecheck`、`npm test`、`npm run build` 输出。
  - 依赖数对比：`git diff -- frontend/package.json frontend/package-lock.json` 为空；`npm ls --depth=0` 与基线一致。
  - 记录新增测试数量与全量通过数。
- **测试/证据前置**：是（证据文件）。
- **依赖任务**：T1-8、T2-6、T3-5。
- **验收命令/断言**：
  - `cd frontend && npm run typecheck && npm test && npm run build` → 全部通过。
  - `git diff -- frontend/package.json frontend/package-lock.json` → 无改动。
- **回滚方式**：无代码回滚；失败项回到对应任务修复。
- **独立验收点（建议主题）**：`test: run full frontend verification`。

### T4-2 后端探针回归（通用 + 工作台 + 断开）

- [ ] **状态**：可执行
- **目标**：证明通用端点全场景通过、工作台端点零回归、客户端断开不写缓存/不报错。
- **涉及文件/模块**：无业务源码；`evidence/acceptance/GAI-probe.md`（新增）。
- **具体改动点**：
  - 启动 dev 后端，运行 `ai_probe.py 8000`、`tutor_probe.py 8000`、`disconnect_probe.py`。
  - 记录帧序、首 token、总耗时、缓存命中、`tutor_logs` 行数、日志脱敏检查。
  - 无 key 环境记录「模型路径未启用」；有 key 环境补一条 `source=llm`。
- **测试/证据前置**：是。
- **依赖任务**：T4-1（或与 T4-1 并行，仅后端）。
- **验收命令/断言**：
  - `cd backend && python tools/ai_probe.py 8000 && python tools/tutor_probe.py 8000 && python tools/disconnect_probe.py` → 全 PASS。
  - `output/GAI-backend.log` 不含问题全文、`plaintext_hex` 值、key。
- **回滚方式**：无代码回滚；失败项回到 T0/T1 修复。
- **独立验收点（建议主题）**：`test: run backend AI and tutor probes`。

### T4-3 浏览器回归（新增全量 + 工作台两条；不重跑已验收项）

- [ ] **状态**：可执行
- **目标**：跑完 `global-ai.spec.ts` 14 条与工作台 `smoke` 两条；明确不重跑练习页与 F09/F10/F17/F22 已验收浏览器项。
- **涉及文件/模块**：`frontend/e2e/global-ai.spec.ts`（全量）、`evidence/acceptance/GAI-playwright.txt`（新增）。
- **具体改动点**：
  - 全量运行 `global-ai.spec.ts`：首页/S 盒/雪崩不改变 URL、四页互不串、切页不串流、工作台 E 区/单入口/Esc/焦点、`?ai=1`、390 无横向滚动、播报。
  - 运行 `smoke.spec.ts` 中工作台两条（`--grep "载入工作台|提问 SSE"`）；**不运行** `/practice` 用例（页面已删除，证据只增不改）。
  - 证据写 A1–A5、A10–A18 的覆盖与实测值；未达项保留。
- **测试/证据前置**：是。
- **依赖任务**：T4-1、T4-2。
- **验收命令/断言**：
  - `cd frontend && npx playwright test --config=e2e/playwright.config.ts e2e/global-ai.spec.ts` → 14/14（若因本地流过快导致 #6 放宽，记录原因与断言）。
  - `npx playwright test --config=e2e/playwright.config.ts e2e/smoke.spec.ts --grep "载入工作台|提问 SSE"` → 2/2。
- **回滚方式**：无代码回滚；失败项回到对应阶段修复。
- **独立验收点（建议主题）**：`test(e2e): run global AI suite`。

### T4-4 Docker / SSE 不缓冲 / Lighthouse

- [ ] **状态**：可执行
- **目标**：证明通用端点在容器内逐帧、不缓冲；面板关闭时性能/可访问性不回归。
- **涉及文件/模块**：`docker-compose.yml`、`docker/nginx.conf`（只读，不改）；`evidence/acceptance/GAI-docker-sse.txt`、`GAI-F21-home-lighthouse.json`、`GAI-F21-workbench-lighthouse.json`（新增）。
- **具体改动点**：
  - `docker compose up -d --build`；`docker compose ps` 看 backend/frontend healthy。
  - `curl -N` 打 `/api/ai/ask`，记录 `Content-Type: text/event-stream`、逐帧、无 gzip；工作台 `/api/tutor/ask` 旧探针仍通过。
  - Lighthouse 在面板关闭态跑 `/` 与 `/workbench`；如需，另跑 `/sbox` 面板打开态 accessibility 一次。
  - 不修改 `docker-compose.yml` / `nginx.conf`。
- **测试/证据前置**：是。
- **依赖任务**：T4-1。
- **验收命令/断言**：
  - `docker compose up -d --build` → healthy。
  - `curl -N ...` → 帧序正确、无 `Content-Encoding: gzip`。
  - Lighthouse：Accessibility ≥95；Performance 不低于基线；记录 FCP/LCP/TBT/CLS。
- **回滚方式**：无代码回滚；若指标不达，记录为已知边界并回滚对应阶段。
- **独立验收点（建议主题）**：`test: run docker SSE and lighthouse regression`。

### T4-5 证据归档与已知边界

- [ ] **状态**：可执行
- **目标**：把 A1–A20 的覆盖、命令、实测值、未达项汇总为可评审证据；只追加不改原文。
- **涉及文件/模块**：`evidence/acceptance/GAI-summary.md`（新增）；只读 `F09/F10/F17/F22/F24` 原文。
- **具体改动点**：
  - 汇总各阶段证据文件；按 A1–A20 列表写「通过/未达/不适用」。
  - 明确不重跑项：F09 四块/chip、F10 状态点、F17 逐态截图、F22 键盘链路、F24 Docker 基线、练习页用例。
  - 明确按阶段推进默认值：D-G2 入口位置、D-G8 动作按钮、D-G10 不做页面动作、D-G5 刷新清空。
  - 记录遗留问题与已知边界（如本地流过快导致切页中断用例放宽、Docker 引擎不可用时的替代口径）。
- **测试/证据前置**：是。
- **依赖任务**：T4-1–T4-4。
- **验收命令/断言**：
  - `ls evidence/acceptance/GAI-*` → 文件齐全。
  - `git diff -- evidence/acceptance/F09.md F10.md F17.md F22.md F24.md` → 为空（未改原文）。
  - A1–A20 每项都有结论，未达项未标为通过。
- **回滚方式**：删除新增证据文件；不改原文。
- **独立验收点（建议主题）**：`docs(evidence): archive global AI acceptance summary`。

### T4-6 交付说明与评审留痕（不开始编码）

- [ ] **状态**：可执行
- **目标**：按用户偏好给出结构化实现说明：改了什么、与设计的偏差及原因、实测数据、需要知道的事、遗留问题；任务文档勾选完成状态。
- **涉及文件/模块**：`docs/specs/global-ai-assistant-v1/tasks.md`、`.codeartsdoer/specs/global_ai_assistant_v1/tasks.md`、`evidence/acceptance/GAI-summary.md`（追加交付说明）。
- **具体改动点**：
  - 勾选各任务 `- [x]`，未完成项保持未勾选并说明原因。
  - 交付说明列出：入口/会话/上下文/后端/UI/测试六块；D-G2/D-G8 的偏差；实测视口/步数/耗时；测试结果；需要用户知道的事项；遗留问题。
  - 不提交、不建分支；是否提交由用户决定。
- **测试/证据前置**：否（文档）。
- **依赖任务**：T4-5。
- **验收命令/断言**：
  - 交付说明包含「改了什么 / 与设计偏差 / 实测数据 / 需要你知道的事 / 遗留问题」五个小节。
  - 任务勾选与证据文件一致。
- **回滚方式**：无代码回滚；删除交付说明段落。
- **独立验收点（建议主题）**：`docs: add global AI delivery notes`。

---

## 附录 A · 需求覆盖矩阵（A1–A20 → 任务）

| 验收项 | 覆盖任务 |
|---|---|
| A1 不跳转 | T1-2、T1-8、T2-6、T3-5 |
| A2 四栏目入口 | T1-2、T3-2、T3-5 |
| A3 会话隔离 | T1-1、T1-8、T2-6 |
| A4 切页不串流 | T1-1、T1-2、T1-8 |
| A5 刷新口径 | T1-1 |
| A6 工作台上下文 | T3-3、T3-5 |
| A7 S 盒上下文 | T2-1、T2-6 |
| A8 雪崩上下文 | T2-2、T2-6 |
| A9 首页无上下文 | T0-7、T1-5、T1-8 |
| A10 SSE 协议 | T0-8、T0-9、T1-6 |
| A11 降级 | T0-7、T1-6、T1-7、T4-2 |
| A12 超时 | T0-4、T1-1 |
| A13 缓存 | T0-7、T0-9 |
| A14 缓存不串 | T0-6、T0-9、T1-6、T2-6 |
| A15 快捷键 | T1-3、T3-4、T1-8 |
| A16 焦点 | T1-3、T1-8 |
| A17 播报 | T1-3、T1-8 |
| A18 移动端 | T1-3、T1-8 |
| A19 回归 | T1-4、T3-5、T4-3 |
| A20 工程 | T4-1 |

## 附录 B · 文件改动清单

**新增**

- `frontend/src/utils/ai-context.ts` / `ai-context.spec.ts`
- `frontend/src/data/ai-prompts.ts` / `ai-prompts.spec.ts`
- `frontend/src/utils/ai-stream.ts` / `ai-stream.spec.ts`
- `frontend/src/utils/ai-local-fallback.ts` / `ai-local-fallback.spec.ts`
- `frontend/src/stores/ai.ts` / `ai.spec.ts`
- `frontend/src/composables/useDialogFocusTrap.ts`
- `frontend/src/components/global-ai/GlobalAiHost.vue`
- `frontend/src/components/global-ai/GlobalAiLauncher.vue`
- `frontend/src/components/global-ai/GlobalAiPanel.vue`
- `frontend/src/components/global-ai/GlobalAiMessage.vue`
- `frontend/src/components/global-ai/GlobalAiPrompts.vue`
- `frontend/e2e/global-ai.spec.ts`
- `backend/services/ai_service.py`
- `backend/routers/ai.py`
- `backend/tools/ai_probe.py`
- `evidence/acceptance/GAI-*.md` / `GAI-playwright.txt` / `GAI-docker-sse.txt` / `GAI-F21-*.json`

**修改**

- `frontend/src/App.vue`
- `frontend/src/components/layout/AppShell.vue`
- `frontend/src/components/layout/WorkbenchLayout.vue`
- `frontend/src/components/region-e/TutorPanel.vue`（仅新增 `snapshot` emit）
- `frontend/src/components/region-e/TutorMessage.vue`
- `frontend/src/views/HomeView.vue`
- `frontend/src/views/SBoxView.vue`
- `frontend/src/views/AvalancheView.vue`
- `frontend/src/views/WorkbenchView.vue`
- `frontend/src/utils/tutor-message.ts`
- `frontend/src/utils/tutor-message.spec.ts`
- `frontend/src/styles/tokens.css`（仅追加 3 个布局变量）
- `backend/models/schemas.py`（仅新增 `AiAskRequest`）
- `backend/main.py`（仅挂载 `ai_router`）
- `backend/services/llm_service.py`（仅新增通用函数）

**只读/禁止修改**

- `frontend/src/composables/useSSE.ts`、`utils/sse.ts`、`composables/useHealth.ts`
- `frontend/src/components/shared/AppDrawer.vue`、`composables/useHotkeys.ts`
- `frontend/src/components/shared/AiFab.vue`（保留，不再由 AppShell 引用）
- `backend/routers/tutor.py`、`services/tutor_service.py`、`services/tutor_log.py`、`db.py`
- `docker-compose.yml`、`docker/nginx.conf`
- `frontend/public/aes-quest/index.html`
- `evidence/acceptance/` 既有原文

## 附录 C · 阶段回滚点与独立验收

| 阶段 | 独立验收 | 回滚点 |
|---|---|---|
| 0 契约/骨架 | 单测 + `ai_probe --self-test` + build；工作台无视觉变化 | 删除新增文件；还原 `schemas.py`、`main.py` |
| 1 通用+首页 | E2E #1/#2/#14；首页探针；build；`smoke` 不受影响 | 还原 `App/AppShell/Home/TutorMessage/tutor-message.ts`；删除 `global-ai/*`、`useDialogFocusTrap`、`ai-local-fallback`、`stores/ai` |
| 2 S 盒/雪崩 | E2E #3/#4/#7/#8；`ai_probe` 两页；A14 | 还原 `SBoxView/AvalancheView`；删除页面分支/动作监听 |
| 3 工作台 | E2E #9/#10/#11；`smoke` 两条；F17 抽查；`tutor_probe` | 还原 `WorkbenchView/WorkbenchLayout/TutorPanel`；Launcher 工作台分支隐藏 |
| 4 全量 | `typecheck/test/build`；`ai_probe/tutor_probe`；Playwright；Docker SSE；Lighthouse | 不回滚代码；指标不达记录并回滚对应阶段（1/2/3） |

---

**任务清单结束。本文不含业务源码，不构成提交。**