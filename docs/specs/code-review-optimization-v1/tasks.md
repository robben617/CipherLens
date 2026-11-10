# CipherLens 代码审查优化 · 编码任务清单

> 文档编号：CL-OPT-TASKS-v1.0
> 状态：**待评审，未开始编码**
> 输入基线：`docs/specs/code-review-optimization-v1/requirements.md`、`docs/specs/code-review-optimization-v1/design.md`
> 规范镜像：`.codeartsdoer/specs/code_review_opt_v1/tasks.md`
> 任务总数：**34**（阶段 0：6；阶段 1：12；阶段 2：6；阶段 3：5；阶段 4：2；阶段 5：3）
> 执行原则：一任务一提交一验收；先证据/文档、后代码；旧证据只追加不删改；决策未确认不得写成已确认
> 本文只拆任务，不写业务源码，不提交，不创建分支

---

## 0. 使用说明与执行门禁

### 0.1 状态图例

| 状态 | 含义 |
|---|---|
| 可执行 | 无外部依赖、无未决决策，可按本文验收 |
| 待决策（D-xx） | 必须先拿到用户对 D-xx 的明确选择，否则不启动 |
| 条件任务（默认不执行） | 设计默认不纳入本轮；仅在用户明确纳入后启动 |
| 已完成 | 已提交、已验收、证据已归档 |

### 0.2 决策门 D-01–D-08 与任务放行矩阵

| 决策 | 设计假设（**均未确认**） | 受影响任务 | 放行条件 | 未确认时的处理 |
|---|---|---|---|---|
| D-01 真实 LLM | B：本轮不接，保留本地模板 | T4-1 | 用户明确选 A/C | T4-1 不启动；T1-9 只写“预留，未启用”占位 |
| D-02 口径/字段 | A：先追记证据，再新增 `diff_bytes/source_bytes`，`propagated` 保留一版 | T2-2、T2-3 | 用户确认 A；T0-2 已完成 | 只做 T0-2 文档追记，不改字段/UI |
| D-03 真相源 | C：双引擎 + 对账，不改工作台数据源 | T1-4、T1-5 可先行；T4-2 待决策 | T1-4/T1-5 仅做 C；T4-2 需明确 A/B | 不启动 T4-2；不把后端或前端改成唯一真相源 |
| D-04 标签来源 | A+B：真实归因 `unattributed`；后端 `item_id→design_tag` | T2-1（A）、T2-6（B） | A、B 分别确认 | T2-1/T2-6 暂停；T2-4/T2-5 不写结构化标签可先行 |
| D-05 埋点会话 | A 条件纳入；默认不纳入 | T3-5 | 用户明确纳入并选 A/B | T3-5 不启动；`/api/events` 保持 204 |
| D-06 匿名 vs 登录 | A：匿名 `client_id`，不做登录 | T3-2、T3-3、T3-4（完整） | 用户确认 A | T3-1 只加列/索引，不改读写作用域；T3-2/T3-3 不启动 |
| D-07 CI | A：本地脚本 + 文档，不接平台 | T5-1（A）、T5-2（B/C） | T5-1 需 A；T5-2 需 B/C | T5-1/T5-2 不启动；已有命令仍可手工执行 |
| D-08 P2 范围 | 只做已列 REQ-17/18/19/20/21/22 | T1-6–T1-12 | 用户确认只做已列项 | 任何额外 P2 项不排任务、不“顺手做” |

> 放行规则：`T0-5` 只记录“待确认/按建议执行/否决”，不得由实施 Agent 自行填写“已确认”。用户回复“按建议执行”才视为对应决策放行；未逐项回复的，保持“待确认”。

### 0.3 可先行任务（不污染未确认项）

- 证据/文档类：T0-1、T0-2、T0-4、T0-6。
- 无决策依赖的代码类：T1-1、T1-2、T1-3、T1-4、T1-5、T1-6、T1-7、T1-8、T1-9、T1-10、T1-11、T1-12。
- 数据稳定性类：T3-1（只加 `client_id/design_tag` 列与索引，不改变读写作用域，不宣称已实现隔离）。
- 题库数据类：T2-4、T2-5（不含结构化 `design_tag`，不触发 D-04 B）。

### 0.4 建议首批可执行任务（文档审阅通过后）

1. **第一批（无决策、先证据/基线）**：T0-1、T0-2、T0-4、T0-6；同步建立 T0-5 台账，D-01–D-08 全部保持“待确认”。
2. **第二批（可并行、独立提交）**：T1-1 → T1-2；T1-3；T1-4；T1-6；T1-7。
3. **第三批**：T1-5（依赖 T1-3/T1-4）；T1-8、T1-9、T1-10、T1-11、T1-12。
4. **之后按决策放行**：T2-4/T2-5 可先做；T2-1 等 D-04=A；T2-2/T2-3 等 D-02；T3-1 可先做；T3-2/T3-3 等 D-06=A。

### 0.5 通用验收命令与证据规则

**前端**
```bash
cd frontend
npm test
npm run build
npx vitest run src/utils/sse.spec.ts
npx vitest run src/composables/useSSE.spec.ts
```

**后端**
```bash
cd backend
python -m uvicorn main:app --port 8000
python tools/quiz_probe.py 8000
python tools/records_probe.py --summary
python tools/compare_trace.py
python tools/tutor_probe.py 8000
python tools/disconnect_probe.py
```

**Docker / E2E**
```bash
docker compose up -d --build
curl -i http://127.0.0.1:8080/api/records/summary
cd frontend
npm install --no-save --no-package-lock @playwright/test@1.55.0
npx playwright test --config=e2e/playwright.config.ts
```

**Lighthouse（新结果不得覆盖旧证据）**
```bash
cd frontend
npm run build
npx vite preview --port 4174 --host 127.0.0.1
npx --yes lighthouse@13.6.0 http://127.0.0.1:4174/workbench \
  --preset=desktop --only-categories=performance,accessibility \
  --output=json --output-path=output/F21-opt1-lighthouse.json \
  --chrome-flags="--headless=new --disable-gpu --no-sandbox"
```

**证据规则**
- `evidence/acceptance/` 原文件只允许**追加**“口径变更说明”，不得删改原文、实测数字、截图引用。
- 新证据使用新文件名：`OPT-baseline.md`、`B1-opt1.md`、`B3-opt1.md`、`F19-opt1.md`、`F20-opt1.md`、`F21-opt1-lighthouse.json`、`F23-opt1.md`、`F24-opt1.md`、`F24-opt1-playwright.txt`。
- 每条新证据写：需求编号、改动前口径、改动后口径、命令/断言、回归结果；未达项保留“未达”记录（尤其 F21 每步 Layout 2.47）。
- Playwright 继续使用系统 Chrome，`npm install --no-save --no-package-lock`，**不写入 `package.json`**。

---

## 阶段 0 · 口径冻结与证据追记（无代码）

### T0-1 术语冻结与禁词基线

- [ ] **状态**：可执行（无代码、无文件变更）
- **目标**：冻结“差异字节 / 来源字节 / 首错位置 / 未归类 / 题目设计意图 / 兼容字段 `propagated`”，明确学生可见文案不得使用“受污染”“受影响的下游字节”。
- **涉及文件/模块**：`docs/specs/code-review-optimization-v1/design.md` §0.3、§9.3（只读引用）；`frontend/src/views/`、`frontend/src/components/`（只检索，不改）。
- **具体改动点**：
  - 以 design §0.3 为唯一术语表，后续新增文案只允许使用“差异字节”“来源候选字节”。
  - 记录当前基线：`frontend/src/views`、`frontend/src/components` 中学生可见文案“受污染”命中为 0；`backend/services/quiz_service.py:89` 与 `frontend/src/styles/tokens.css:50,69,72` 的注释属于非渲染文本，分别在 T2-2、T1-10 清理。
  - 在 T0-5 台账登记“`propagated` 为兼容字段，不驱动新文案”。
- **文档/证据前置**：是（术语冻结记录；本任务不写证据原文）。
- **依赖任务**：无；为 T2-2/T2-3 的前置。
- **验收命令/断言**：
  - `rg -n "受污染|受影响的下游" frontend/src/views frontend/src/components` → 0。
  - `rg -n "propagated" docs/specs/code-review-optimization-v1/design.md` 能看到“兼容/deprecated”说明。
  - 不修改任何源码文件，`git status` 仅允许 T0 文档/证据变更。
- **回滚方式**：无代码回滚；仅删除 T0-5 中对应台账行。

### T0-2 P0-2/P0-4 口径变更说明（B3/F19/F20 只追加）

- [ ] **状态**：可执行（证据追记）
- **目标**：在旧证据末尾追加“口径变更说明（2026-11-09）”，记录旧口径、新口径、生效日期、影响字段，确保 P0-2 的 downstream 8→4 与 P0-4 的 `unattributed` 有据可查。
- **涉及文件/模块**：`evidence/acceptance/B3.md`、`evidence/acceptance/F19.md`、`evidence/acceptance/F20.md`（仅在文件末尾追加）。
- **具体改动点**：
  - B3：说明 `propagated` 旧口径“首个差异之后的下标”仍保留一版；新字段 `diff_bytes/source_bytes` 将加入；`propagated` 不再驱动文案。
  - F19：说明 `.is-downstream` 旧值 8 是历史可实现口径；T2-3 后将改为 `source_bytes.length=4`；`.is-error` 仍为 1；旧截图与旧断言保留可查。
  - F20：说明真实错误路径将从 `key_timing` 改为 `unattributed`；探针合成的 4/1/1 仍是历史演示数据；三态门槛 3 不变。
  - 明确“旧口径是当时的可观测实现，新口径是教学修正”，不写“旧结论作废/造假”。
- **文档/证据前置**：是（本任务就是前置；T2-1、T2-2、T2-3 未完成前不得改对应代码）。
- **依赖任务**：无；阻塞 T2-1、T2-2、T2-3。
- **验收命令/断言**：
  - `git diff --numstat -- evidence/acceptance/B3.md evidence/acceptance/F19.md evidence/acceptance/F20.md` 仅显示新增行，无删除行。
  - 旧实测字符串仍存在：`propagated": [8, 9, 10, 11, 12, 13, 14, 15]`、`.is-downstream` 8、`key_timing=1`。
  - 追加段落含“口径变更说明（2026-11-09）”、旧值、新值、影响字段、生效条件。
- **回滚方式**：删除追加段落；原文不动，不需要恢复旧文件。

### T0-3 P1-2 记录页隔离与 healthcheck 变更口径登记（待 D-06）

- [ ] **状态**：可执行（仅登记，不宣称生效）
- **目标**：在决策台账记录 P1-2 的拟变更口径，确保 T3-2/T3-3 实施前先明确“无头返回空汇总、写路径默认 `legacy-default`、healthcheck 仍 200”。
- **涉及文件/模块**：`docs/specs/code-review-optimization-v1/tasks.md` 的 T0-5 台账；不修改 `F20.md`/`F24.md` 原文。
- **具体改动点**：
  - 记录读路径规则：有合法 `X-Client-Id` → 该客户端；无头且无 `scope=legacy` → `total=0`、`scope="none"`、HTTP 200；`scope=legacy` → `legacy-default`；非法头 → 400 `invalid_client_id`。
  - 记录写路径规则：缺省 `X-Client-Id` → `legacy-default`，保证旧探针可写。
  - 明确“未确认 D-06=A 前，不写 F20/F24 生效说明，不改接口行为”。
- **文档/证据前置**：是（仅台账；不是生效证据）。
- **依赖任务**：D-06；阻塞 T3-2、T3-3。
- **验收命令/断言**：
  - T0-5 台账存在 P1-2 行，状态为“待确认（D-06）”。
  - `git diff -- evidence/acceptance/F20.md evidence/acceptance/F24.md` 为空。
  - 文档中不出现“已隔离/已解决鉴权”等既成事实表述。
- **回滚方式**：删除台账行；不涉及证据。

### T0-4 P1-3 迁移前证据说明（B1/F20/F24 只追加）

- [ ] **状态**：可执行（证据追记）
- **目标**：在数据库加固前记录迁移目标、备份路径与版本口径，避免“代码已迁移、证据仍是旧版本”的空窗。
- **涉及文件/模块**：`evidence/acceptance/B1.md`、`evidence/acceptance/F20.md`、`evidence/acceptance/F24.md`（仅在末尾追加）。
- **具体改动点**：
  - 记录目标 `PRAGMA user_version=1`、WAL、`busy_timeout=5000`、新增 `practice_attempts.client_id/design_tag`、索引清单。
  - 记录迁移前备份：`backend/data/cipherlens.db.bak-v0-<UTC>`，保留最近 2 份；`backend/data/` 已被 `.gitignore` 忽略。
  - 明确旧建表输出、旧记录页数据、旧 volume 重启证据仍有效；迁移后新增说明，不删旧段落。
- **文档/证据前置**：是（阻塞 T3-1）。
- **依赖任务**：无；阻塞 T3-1。
- **验收命令/断言**：
  - `git diff --numstat` 仅新增行；旧 B1 建表输出、F20 total/correct、F24 volume 结果仍在。
  - 追加段含版本号、备份路径、失败拒绝启动规则。
- **回滚方式**：删除追加段落；旧证据不动。

### T0-5 决策台账 D-01–D-08 与任务放行

- [ ] **状态**：可执行（等待用户勾选；不得自行确认）
- **目标**：建立 D-01–D-08 的唯一决策台账，把每个决策映射到任务，防止“待确认项被写成已确认”。
- **涉及文件/模块**：`docs/specs/code-review-optimization-v1/tasks.md` 的决策表；`.codeartsdoer/specs/code_review_opt_v1/tasks.md` 镜像。
- **具体改动点**：
  - 8 行决策，每行记录：当前状态（默认“待确认”）、用户选择、确认日期、放行任务、未放行任务。
  - 用户回复“按建议执行”时逐项记录；未逐项回复的保持“待确认”。
  - 在任务标题下保留“待决策（D-xx）”状态，不改成“可执行”。
- **文档/证据前置**：是（决策记录本身）。
- **依赖任务**：无；所有待决策任务以本台账为准。
- **验收命令/断言**：
  - 8 行齐全；无未经用户确认的“已确认”。
  - `rg -n "待决策（D-0" docs/specs/code-review-optimization-v1/tasks.md` 能列出阻塞任务。
  - 台账与 0.2 表一致，无“推测已同意”。
- **回滚方式**：状态回退为“待确认”，保留历史记录；不删除用户已确认项。

### T0-6 基线快照与回滚点

- [ ] **状态**：可执行
- **目标**：在改动前记录可复现基线，作为后续“是否回归”的对照。
- **涉及文件/模块**：新增 `evidence/acceptance/OPT-baseline.md`；不修改源码与旧证据。
- **具体改动点**：
  - 记录 `git rev-parse HEAD`、日期、Node/Python/Docker 版本。
  - 运行并记录：`npm test`、`npm run build`、`python backend/tools/compare_trace.py`、`python backend/tools/quiz_probe.py 8000`、`python backend/tools/records_probe.py --summary`、`docker compose ps`。
  - 记录当前入口/工作台 gzip 体积、Lighthouse 旧结果引用、F19/F20/F24 现有断言值。
- **文档/证据前置**：是（新增基线证据，不改旧证据）。
- **依赖任务**：无；建议在 T1 任何代码任务之前完成。
- **验收命令/断言**：
  - 新文件存在，含上述命令与原始输出摘要。
  - 当前基线：`npm test` 28/28、`compare_trace.py` `differences=0`、Docker 服务 healthy。
  - 文件不含密钥、完整明文、真实 Token。
- **回滚方式**：删除 `OPT-baseline.md`；不影响运行时。

---

## 阶段 1 · 无外部依赖的独立修正

### T1-1 SSE 帧解析规范化

- [ ] **状态**：可执行（无决策依赖）
- **目标**：让 `data:` 无空格、多行 `data:`、残留帧、CRLF 跨 chunk 均按 SSE 规范解析，且不改变现有 `meta/token/done/error` 行为。
- **涉及文件/模块**：`frontend/src/utils/sse.ts`；新增 `frontend/src/utils/sse.spec.ts`。
- **具体改动点**：
  - `data:` 使用 `startsWith('data:')`，去掉一个可选前导空格；多行值用 `\n` 连接，不直接拼接。
  - 帧分隔同时支持 `\n\n` 与 `\r\n\r\n`，跨 chunk 的 CRLF 不误判；流结束 flush `TextDecoder`，缓冲区非空时派发最后一帧。
  - 忽略 `:` 开头注释行；未知事件、空事件忽略；JSON 解析失败保持“忽略该帧、不崩溃”。
  - 保留 `meta/token/done/error` 分派与 `onToken(text)` 语义。
- **文档/证据前置**：否。
- **依赖任务**：无；T1-2 依赖本任务。
- **验收命令/断言**：
  - `npx vitest run src/utils/sse.spec.ts` 覆盖 I1–I4：`data:{"t":"x"}`、两行 `data:` → `a\nb`、末尾无空行、CRLF 跨 chunk、现有四事件。
  - `npm test` 全绿；`npm run build` 零 TS error。
- **回滚方式**：单文件 + 新 spec 回退；旧实现保留在 git 历史。

### T1-2 useSSE 作用域隔离与 30s 超时

- [ ] **状态**：可执行（无决策依赖）
- **目标**：每个调用方独立管理 AbortController；30s 无 token 只报一次 `timeout`；主动中止/卸载不报 timeout；`window.__sse.active` 计数准确。
- **涉及文件/模块**：`frontend/src/composables/useSSE.ts`；新增 `frontend/src/composables/useSSE.spec.ts`。
- **具体改动点**：
  - `useSSE()` 内创建独立 `Set<AbortController>`，`abort()` 只清本作用域；`start()` 先中止本作用域上一次流，不触碰其他作用域。
  - 全局 `activeCount` 保留，每条流用 `settled` 标记只减一次；`onScopeDispose(abort)` 只清自己的流。
  - `start(url, payload, handlers, options?)` 增加 `tokenTimeoutMs` 默认 30000；请求开始启动计时，`token` 重置，`meta` 不重置，`done/error` 清理。
  - 超时：标记 `timedOut` → abort → 单次 `onError('timeout', ...)`；主动 abort 不回调错误；TutorPanel 20s 降级调用 `abort()` 后不得再报 timeout。
- **文档/证据前置**：否。
- **依赖任务**：T1-1。
- **验收命令/断言**：
  - `npx vitest run src/composables/useSSE.spec.ts` 覆盖 J1–J4、K1–K4：两个作用域卸载 A 不影响 B；重复 start 只中止本作用域；30s 超时一次；主动中止无 timeout；计数归零。
  - 使用 fake fetch/ReadableStream + `vi.useFakeTimers`，不引入 jsdom。
  - `npm test` 全绿；`npm run build` 通过。
- **回滚方式**：回退 `useSSE.ts` 与新 spec；T1-1 解析器可独立保留。

### T1-3 第 0 步禁用提问

- [ ] **状态**：可执行（无决策依赖）
- **目标**：当前步为 0 时不允许发起 `/api/tutor/ask`，并显示“先走一步”提示；步 1 起恢复，`Math.max(0, stepIndex-1)` 映射不变。
- **涉及文件/模块**：`frontend/src/components/region-e/TutorPanel.vue`、`frontend/src/components/layout/WorkbenchLayout.vue`、`frontend/src/views/WorkbenchView.vue`、`frontend/e2e/smoke.spec.ts`（仅提问用例前置步进）。
- **具体改动点**：
  - `TutorPanel` 增加 `askDisabled`、`disabledReason` props；`stepZero = props.stepIndex === 0`；`askDisabled = props.askDisabled || stepZero`。
  - 步 0：textarea `disabled`、发送按钮 `disabled`、提示“先走一步，我才能讲你看到的东西”；`send()` 首行 guard，不发请求。
  - `disabledReason` 优先级：数值不一致 > 离线 > 步 0（数值/离线由 T1-5 传入）。
  - `WorkbenchLayout` 透传 props；`WorkbenchView` 在 T1-5 前先传默认值。
  - Playwright 提问用例先按 `ArrowRight` 到步 1，再填写发送。
- **文档/证据前置**：否；F24-opt1 在 T3-4/T5-3 补记。
- **依赖任务**：无；T1-5 依赖本任务的 props。
- **验收命令/断言**：
  - 步 0：textarea/发送按钮 disabled；点击/Enter 无 `/api/tutor/ask` 请求。
  - 步 1：可提问，回答引用第 1 步数值；F16/F17 原有断言可复现。
  - `docker compose up -d --build` 后 `npx playwright test --config=e2e/playwright.config.ts -g "提问"` 通过；`npm run build` 通过。
- **回滚方式**：回退 TutorPanel/WorkbenchLayout/WorkbenchView 的 props 与 `send()` guard；回退 e2e 前置步进两行。

### T1-4 三组向量引擎对账

- [ ] **状态**：可执行（D-03=C 兼容，不改变真相源）
- **目标**：把 `compare_trace.py` 从 C.1 单向量扩到 C.1/C.2/C.3 三组，逐字段比较，任一差异非零退出并打印定位。
- **涉及文件/模块**：`backend/tools/compare_trace.py`、`backend/tools/dump_frontend_trace.mjs`。
- **具体改动点**：
  - 向量表：C.1 128/40 步、C.2 192/48 步、C.3 256/56 步；`key_bits` 由 key 长度推导并显式传给 `build_trace`。
  - `step_count` 按响应/前端 dump 读取，不写死 40。
  - 循环三组，保留 B1 字段范围：`trace_id/ciphertext/key_bits/direction/rounds/step_count/key_schedule` 与每步 `index/round/op/state_before/state_after/changed/key_indices/key_words/label`。
  - 任一差异打印“向量 + 字段 + 下标 + 双方值”，退出码非 0；正常退出 0。
- **文档/证据前置**：否。
- **依赖任务**：无；T1-5、T2-2 可复用其输出。
- **验收命令/断言**：
  - `python backend/tools/compare_trace.py`：三组 `differences=0`，退出码 0。
  - 人为临时改后端某一步 `label`：退出码非 0，打印该字段/下标/双方值；恢复后重新 0。
  - `requirements.txt` / `package.json` 无新增测试依赖。
- **回滚方式**：回退两个工具文件；对账能力回到 C.1 单向量。

### T1-5 工作台运行时一致性校验与离线禁问

- [ ] **状态**：可执行（仅 D-03=C 的对账层，不改真相源）
- **目标**：页面加载时比较后端 `trace_id`/`ciphertext` 与本地 trace；网络失败与内容不一致分开提示；`checking/offline/mismatch` 均禁用提问；不扰动播放/步号/URL。
- **涉及文件/模块**：`frontend/src/views/WorkbenchView.vue`、`frontend/src/components/layout/WorkbenchLayout.vue`、`frontend/src/components/region-e/TutorPanel.vue`。
- **具体改动点**：
  - 新增 `consistency: 'checking'|'ok'|'offline'|'mismatch'`；页面加载为 `checking`；2xx 且两字段均一致 → `ok`；2xx 但字段缺失/不一致 → `mismatch`；fetch 异常/非 2xx → `offline`。
  - 只比较 `trace_id` 与 `ciphertext`，不比较 40 步、不复算判分；`ok` 时才把 `traceId` 更新为后端值。
  - A 区提供“重新校验”按钮；监听 `online` 事件再次校验；`checking/offline/mismatch` 传 `askDisabled=true` 与对应 `disabledReason`。
  - 校验不改变 `currentStep`、`isPlaying`、URL；离线仍用本地 engine 渲染矩阵与播放；禁止本地 engine 判分。
- **文档/证据前置**：否；F23-opt1 在 T5-3 补记。
- **依赖任务**：T1-3（禁用 props）、T1-4（保证正常路径一致）。
- **验收命令/断言**：
  - 正常：无提示，步 1 起可提问，矩阵 40 步。
  - 不一致：临时 Playwright/CDP 脚本拦截 `/api/aes/trace` 改一位 `ciphertext`，出现“前后端数值不一致”，输入/发送 disabled，点击发送无 `/api/tutor/ask`；`aria-valuenow` 不变。
  - 离线：`vite preview` 无 `/api`，出现离线标识，提问禁用，矩阵首格 00、40 步可播放。
  - 恢复：点击“重新校验”后提示消失、提问解禁；F23 URL/错误边界回归通过。
- **回滚方式**：回退 WorkbenchView/Layout/TutorPanel 的 consistency 与 props；本地 trace 渲染不受影响。

### T1-6 全局未捕获异常日志

- [ ] **状态**：可执行（D-08 已列项）
- **目标**：500 时记录路径/方法/异常堆栈，响应体仍为统一结构，不记录密钥/完整明文。
- **涉及文件/模块**：`backend/main.py`。
- **具体改动点**：
  - `handle_unexpected_error` 中 `logger.exception("unhandled error path=%s method=%s", request.url.path, request.method)`。
  - 不记录请求体、`key_hex`、`plaintext_hex`；响应保持 `{error:{code:"internal_error",message:"internal server error",field:null}}`。
- **文档/证据前置**：否。
- **依赖任务**：无。
- **验收命令/断言**：
  - 临时注入一次异常（不提交注入代码）：日志含 `Traceback`/异常类型；HTTP 500 响应体与旧结构逐字段一致。
  - 日志中检索 `key_hex`、`plaintext_hex`、完整 32 位明文/密钥 → 0。
  - `python backend/tools/quiz_probe.py 8000` 正常分支不变。
- **回滚方式**：回退 `main.py` 一行日志；响应逻辑未改。

### T1-7 删除 `assert_answer_length` 死代码

- [ ] **状态**：可执行（D-08 已列项）
- **目标**：删除未被调用的答案长度校验函数，保留 pydantic 的 32 位长度约束。
- **涉及文件/模块**：`backend/services/quiz_service.py`。
- **具体改动点**：
  - 删除 `assert_answer_length` 定义与相关未使用导入；不改 `QuizRequest` 的 `min_length/max_length=32`。
- **文档/证据前置**：否。
- **依赖任务**：无。
- **验收命令/断言**：
  - `rg -n "assert_answer_length" backend` → 0。
  - 31 位答案请求 → 400 `validation_error`（field 按现有规则）；`quiz_probe.py` 三分支不变。
  - `python -m compileall backend` 通过。
- **回滚方式**：恢复单函数；无数据/契约影响。

### T1-8 统一错误响应 OpenAPI 文档化

- [ ] **状态**：可执行（D-08 已列项）
- **目标**：在 OpenAPI 中声明 400/500 的统一错误结构，实际响应形状不变。
- **涉及文件/模块**：`backend/models/schemas.py`、`backend/routers/aes.py`、`quiz.py`、`records.py`、`tutor.py`（按需）、`backend/main.py`。
- **具体改动点**：
  - 新增 `ErrorDetail`、`ErrorResponse` 模型（`code/message/field`）。
  - 在相关路由 `responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}`；只为文档声明，不改返回逻辑。
- **文档/证据前置**：否。
- **依赖任务**：无。
- **验收命令/断言**：
  - `curl -s http://127.0.0.1:8000/openapi.json` 中相关接口含 `ErrorResponse` 400/500。
  - `/docs` 可打开；一次真实 `invalid_key` 响应字段与文档一致。
  - 不新增依赖；`quiz_probe.py` 通过。
- **回滚方式**：回退模型与 `responses` 声明；响应逻辑未动。

### T1-9 `.env.example` 环境变量样例

- [ ] **状态**：可执行（D-01 默认 B，不宣称 LLM 已接入）
- **目标**：提供变量名、用途、默认值样例，明确“预留，未启用”，不含真实 Key。
- **涉及文件/模块**：仓库根 `.env.example`。
- **具体改动点**：
  - 列出数据库路径/备份开关、`LLM_BASE_URL`/`LLM_API_KEY`/`LLM_MODEL` 占位（注释“预留，未启用，无 Key 时走本地模板”）。
  - 列出 `VITE_BASE`、`VITE_BUILD_TARGET`，与 T1-12 保持一致。
- **文档/证据前置**：否。
- **依赖任务**：无；T1-12 可引用。
- **验收命令/断言**：
  - 文件存在；`git check-ignore .env.example` 不忽略（`.gitignore` 有 `!.env.example`）。
  - `rg -n "(sk-|Bearer |api[_-]?key\\s*=\\s*[A-Za-z0-9]{20,})" .env.example` → 0。
  - 变量注释含“预留，未启用”。
- **回滚方式**：删除文件；无运行时影响。

### T1-10 清理“待用户批准”注释

- [ ] **状态**：可执行（D-08 已列项）
- **目标**：把 `tokens.css` 两处占位注释改为正式依据说明，不改任何 token 值。
- **涉及文件/模块**：`frontend/src/styles/tokens.css` 第 50、69 行。
- **具体改动点**：
  - 注释改为“依据见 specs/code-review-optimization-v1/design.md §9.3”；保留原有依据文字，删除“待用户批准”。
  - 不修改 `--st-idle-border` / `--st-done-border` 的值。
- **文档/证据前置**：否；design §9.3 已是正式登记处。
- **依赖任务**：无。
- **验收命令/断言**：
  - `rg -n "待用户批准|待批准" frontend` → 0。
  - `git diff` 仅注释变化；七态 border 1px、`--cell-gap` 6px 不变。
  - `npm run build` 通过；F7/F15 视觉回归。
- **回滚方式**：回退注释；token 值未动。

### T1-11 页面元信息与 favicon

- [ ] **状态**：可执行（D-08 已列项）
- **目标**：补齐 `description`、`og:title`、`og:description`、`theme-color` 与非空 favicon。
- **涉及文件/模块**：`frontend/index.html`；新增 `frontend/public/favicon.svg`。
- **具体改动点**：
  - 4 项 meta；`<link rel="icon" href="/favicon.svg" type="image/svg+xml" />`。
  - favicon 手写 SVG，不引入图标库；保持项目视觉语言。
- **文档/证据前置**：否。
- **依赖任务**：无。
- **验收命令/断言**：
  - `rg -n "name=\"description\"|property=\"og:title\"|property=\"og:description\"|name=\"theme-color\"" frontend/index.html` → 4 项。
  - `favicon.svg` 文件大小 > 0；构建产物包含 `/favicon.svg`。
  - `npm run build` 通过；Lighthouse Accessibility/Performance 不退化。
- **回滚方式**：回退 `index.html`，删除新 favicon。

### T1-12 Vite `base` / `build.target` 可配置

- [ ] **状态**：可执行（D-08 已列项）
- **目标**：支持 `VITE_BASE` 与 `VITE_BUILD_TARGET`，未设置时保持现有默认行为与产物大小。
- **涉及文件/模块**：`frontend/vite.config.ts`；`.env.example`（T1-9 已列变量）。
- **具体改动点**：
  - `loadEnv(mode, process.cwd(), '')`；`base: env.VITE_BASE || '/'`。
  - `build.target` 仅在 `VITE_BUILD_TARGET` 设置时覆盖；开发态不变。
- **文档/证据前置**：否。
- **依赖任务**：T1-9（变量文档）可选；无强制依赖。
- **验收命令/断言**：
  - 默认 `npm run build`：入口 ≤150KB、工作台 ≤220KB gzip；路径与 F21/F24 一致。
  - `VITE_BASE=/cipherlens/ npm run build`：`dist/index.html` 资源路径带 `/cipherlens/`。
  - TS error 0；Docker 默认构建仍可用。
- **回滚方式**：回退 `vite.config.ts`；默认产物恢复原状。

---

## 阶段 2 · 教学正确性与题库

### T2-1 不可归因时写入“未归类”

- [ ] **状态**：待决策（D-04=A）；D-04 未确认前不启动
- **目标**：真实判分无法归因时写 `unattributed`，不再默认 `key_timing`；记录页展示第四桶，旧记录不重写，三态门槛不变。
- **涉及文件/模块**：`backend/services/records_service.py`、`frontend/src/types/api.ts`、`frontend/src/views/RecordsView.vue`、`backend/tools/records_probe.py`、`backend/tools/quiz_probe.py`、新增 `evidence/acceptance/F20-opt1.md`。
- **具体改动点**：
  - `record_attempt` 真实路径写 `misconception='unattributed'`；`misconception_for` 仅保留给 `records_probe.py` 合成 0/2/10 数据。
  - `summary()` 固定 4 桶：`key_timing/mix_coefficient/key_schedule/unattributed`；未归类不增加前三类计数。
  - `RecordsView` 标题改“错因分布（含未归类）”；新增第四桶；三态 `0/<3/≥3` 与 `sample_threshold=3` 不变。
  - 旧记录 `misconception` 原值保留；不迁移重写。
- **文档/证据前置**：是（T0-2 已写 F20/B3 口径说明；本任务新增 F20-opt1）。
- **依赖任务**：D-04=A、T0-2、T0-6。
- **验收命令/断言**：
  - 清空记录后真实答错：SQL `SELECT misconception FROM practice_attempts` → `unattributed`，不是 `key_timing`。
  - `python backend/tools/records_probe.py --seed 10 --summary`：前三桶 4/1/1、`unattributed=0`。
  - 记录页 0/2/10 三态通过；未归类错误不增加前三桶；旧记录标签不变。
  - F20 原有截图/断言可复现；新增 F20-opt1 记录新旧口径。
- **回滚方式**：真实路径单点改回 `misconception_for`；移除第四桶 UI；探针 seed 保留。

### T2-2 后端差异字节与来源字节

- [ ] **状态**：待决策（D-02=A）；D-02 未确认前不启动
- **目标**：响应新增 `diff_bytes`、`source_bytes` 及来源定位字段，保留 `propagated` 兼容；来源由首错下标经末轮逆置换推导 4 个候选列。
- **涉及文件/模块**：`backend/services/quiz_service.py`、`backend/tools/quiz_probe.py`（扩展断言输出）；不删旧字段。
- **具体改动点**：
  - `diff_bytes` = 所有不符下标升序；全对 `[]`，输入错误 `[]`。
  - `source_bytes`：`row=i%4`、`col=i//4`、`source_col=(col-row)%4`，下标 `source_col*4+r`（r=0..3）。
  - `source_step_index = 1+(rounds-2)*4+2`（128→35、192→43、256→51）；`source_round=rounds-1`；`source_step="mix_columns"`。
  - 多差异只对首错给 4 个来源；其余差异不标 `sources`；全对来源字段 `null`。
  - `propagated` 原值保留；`first_diff` 仍为末步 `add_round_key`。
- **文档/证据前置**：是（T0-2 必须先完成；F19-opt1 在 T2-3 产出）。
- **依赖任务**：D-02=A、T0-2、T1-4（三向量验证）。
- **验收命令/断言**：
  - C.1 单错：`diff_bytes=[7]`、`source_bytes=[8,9,10,11]`、`source_step_index=35`、`source_round=9`。
  - C.2/C.3 各一次单错：来源步 43/51，来源数量 1–4。
  - 多字节错：`diff_bytes` 等于实际不符集合；`source_bytes` 仍 4 个；全对/输入非法分支符合设计。
  - `python backend/tools/compare_trace.py` 仍三组 `differences=0`；`quiz_probe.py` 通过。
- **回滚方式**：回退 `quiz_service.py` 新增字段与推导；`propagated` 与旧响应保持可用；T2-3 未启动时无前端影响。

### T2-3 前端差异/来源渲染与 Playwright 8→4

- [ ] **状态**：待决策（D-02=A）；依赖 T2-2
- **目标**：前端优先使用 `source_bytes`/`diff_bytes`，只 1 格 `is-error`、4 格 `is-downstream`；其余差异用文字说明；旧后端缺失新字段时回退 `propagated`。
- **涉及文件/模块**：`frontend/src/stores/quiz.ts`、`frontend/src/views/PracticeView.vue`、`frontend/src/components/region-c/QuizMatrix.vue`、`frontend/src/components/region-c/MatrixStage.vue`、`frontend/src/types/api.ts`、`frontend/e2e/smoke.spec.ts`、新增 `evidence/acceptance/F19-opt1.md`。
- **具体改动点**：
  - `quiz.ts` 新增 `diffBytes`、`sourceBytes` computed；`sourceBytes` 优先 `source_bytes`，缺失时回退 `propagated` 并 `console.warn` 一次；`errorBytes` 只含首错；`designTag` 预留给 T2-6。
  - `PracticeView` 的 `matrixDownstream` 改用 `sourceBytes`；文案改为“差异字节”“来源候选字节”；多差异显示“还有 N 个差异字节”。
  - `MatrixStage` 判分叠加的 `downstream` 改用 `quiz.sourceBytes`；不改边框宽度、`--cell-gap`、格子几何。
  - Playwright 判分用例 `.is-downstream` 断言 8 → 4；`.is-error` 仍 1；新增 F19-opt1 记录旧值/新值/原因。
- **文档/证据前置**：是（T0-2 已追记 downstream 8→4；本任务新增 F19-opt1）。
- **依赖任务**：D-02=A、T0-2、T2-2。
- **验收命令/断言**：
  - C.1 单错：`window.__quiz.state()` 中 `sourceBytes=[8,9,10,11]`、`errorBytes=[7]`。
  - Playwright：`.is-error=1`、`.is-downstream=4`；其余差异有文字说明，未标 error/downstream。
  - 旧后端 fixture 缺 `source_bytes`：回退 `propagated`，不崩溃、控制台 warn 1 次。
  - F19 跳转、组合态（error+key、downstream+key）、切步撤场通过；`npm test`/`npm run build` 通过。
- **回滚方式**：前端回退到 `propagated` 驱动；后端新字段保留但无消费者；删除 F19-opt1 中新增段落。

### T2-4 题库扩充到 8 题（不含结构化标签）

- [ ] **状态**：可执行（不触发 D-04 B）
- **目标**：题库从 1 题扩到 8 题，覆盖 128/192/256 与两类专项题干；前端不含 `expected_ciphertext`。
- **涉及文件/模块**：`frontend/src/data/quizBank.ts`。
- **具体改动点**：
  - 按 design §2.4.6 的 8 行数据新增：`q_042`–`q_049`；`q_042` 保持默认。
  - 128 位 3 题、192 位 3 题、256 位 2 题；列混合专项、轮密钥专项各 ≥2，专项仅在题干文字标注。
  - 不新增 `expected_ciphertext`；不新增结构化 `design_tag`/`tag_label`（留给 T2-6，D-04=B）。
- **文档/证据前置**：否；三组对账见 T1-4。
- **依赖任务**：T1-4（新增题向量验证）。
- **验收命令/断言**：
  - `QUIZ_ITEMS.length === 8`；按 `key_bits` 统计 128/192/256 各 ≥2；专项题干各 ≥2。
  - `rg -n "expected_ciphertext" frontend/src/data` → 0。
  - 逐题调用 `POST /api/aes/trace`，`ciphertext` 与 design §2.4.6 表一致；`compare_trace.py` 三组仍 0。
- **回滚方式**：保留 `q_042`，回退数组其余项；判分接口不受影响。

### T2-5 练习页选题、动态页头与切题清场

- [ ] **状态**：可执行（不含设计标签）
- **目标**：可切换 8 题；页头/明文/密钥/密钥长度标识随题更新；切题清空旧判分叠加；提交仍只走后端。
- **涉及文件/模块**：`frontend/src/views/PracticeView.vue`、`frontend/src/stores/quiz.ts`、`frontend/src/types/api.ts`、`frontend/e2e/smoke.spec.ts`（如需）、追加 `evidence/acceptance/F19-opt1.md`。
- **具体改动点**：
  - 从 `?item=` 读取选题，默认 `q_042`；选择器手写 CSS、键盘可达、`aria-label` 明确；选中后用 `router.replace` 写 `?item=`，不新增历史栈。
  - 页头动态 `AES-128/192/256 · 16 字节`；密钥输入标签动态 `32/48/64 位十六进制`；明文始终 32 位。
  - 切题：`quiz.clear()`、清空答案/展示答案/`formError`/`showExpected`、重新 `POST /api/aes/trace`；`QuizMatrix` 用 `:key="item.id + ':' + (first_diff?.step_index ?? 'none')"` 重挂，杜绝残留 `.is-error`。
  - `stats` 跨题保留；`response` 切题清空；`PracticeView`/`quiz.ts` 不得引用 `engine/`。
- **文档/证据前置**：是（追加 F19-opt1 切题证据；T0-2 已在前）。
- **依赖任务**：T2-4、T2-3（矩阵重挂与 F19-opt1）。
- **验收命令/断言**：
  - 切到 `q_044`：页头 AES-192、密钥标签 48 位；切到 `q_046`：AES-256、64 位；明文/题目同步更新。
  - 上一题有 `.is-error` 时切题：新题 `.is-error=0`，无旧叠加。
  - 连续做 3 道不同题：记录页趋势 ≥3 点（F20）。
  - `rg -n "engine" frontend/src/views/PracticeView.vue frontend/src/stores/quiz.ts` → 0；题库无 `expected_ciphertext`。
  - `npm run build` 通过。
- **回滚方式**：恢复 `QUIZ_ITEMS[0]` 与静态页头/密钥标签；保留题库文件或一并回退。

### T2-6 题目设计意图标签与记录页分栏

- [ ] **状态**：待决策（D-04=B）；且依赖 T3-1 的 `design_tag` 列
- **目标**：后端按 `item_id` 常量映射 `design_tag`，与 `misconception` 分开存储/展示；记录页出现“题目设计意图（不是算法诊断）”，不冒充算法诊断。
- **涉及文件/模块**：`backend/services/records_service.py`、`backend/services/quiz_service.py`、`backend/routers/quiz.py`、`backend/db.py`（仅使用 T3-1 已加列）、`frontend/src/data/quizBank.ts`、`frontend/src/types/api.ts`、`frontend/src/views/RecordsView.vue`、`backend/tools/records_probe.py`、追加 `evidence/acceptance/F20-opt1.md`。
- **具体改动点**：
  - 后端常量 `QUIZ_ITEM_META: item_id → design_tag`；判分响应加 `design_tag`；未知题为 `null`。
  - `record_attempt` 接收并写入 `design_tag`；真实归因仍 `unattributed`，标签不替代证据。
  - `summary()` 新增 `design_tags` 计数（仅非空标签）；`misconceptions` 仍固定 4 桶。
  - 前端题库加 `design_tag`/`tag_label`；记录页新增独立面板“题目设计意图（不是算法诊断）”，仅在 `design_tags` 非空时显示；不出现“你的错因是 X”。
- **文档/证据前置**：是（T0-2 已追记；F20-opt1 追加标签分栏证据）。
- **依赖任务**：D-04=B、T2-1、T2-4、T2-5、T3-1。
- **验收命令/断言**：
  - 真实答错 `q_042`：SQL `misconception='unattributed'`、`design_tag='key_timing'`。
  - 记录页同时出现“未归类”桶与“题目设计意图”面板；三类桶计数不因标签增加。
  - 未知 `item_id`：`design_tag=null`，不默认成某类。
  - F20 0/2/10 三态、正确率、趋势、错题跳转通过；`records_probe --seed` 仍可合成旧分布。
- **回滚方式**：删除设计意图面板与 `design_tags` 聚合；保留 `design_tag` 列（可空）与历史值；`misconception` 不受影响。

---

## 阶段 3 · 数据与匿名隔离

### T3-1 数据库 WAL、索引与幂等迁移

- [ ] **状态**：可执行（仅结构加固；不改变读写作用域）
- **目标**：启用 WAL/`busy_timeout`，以 `PRAGMA user_version=1` 幂等迁移，新增 `client_id/design_tag` 列与常用索引；迁移失败拒绝启动，数据不丢。
- **涉及文件/模块**：`backend/db.py`、`backend/main.py`、`backend/services/records_service.py`（查询列兼容）、新增 `evidence/acceptance/B1-opt1.md`。
- **具体改动点**：
  - `connect()`：`foreign_keys=ON`、`busy_timeout=5000`。
  - `init_db()`：读取 `user_version`；若低于 1：一致性备份到 `backend/data/cipherlens.db.bak-v0-<UTC>`（保留最近 2 份）；事务外 `PRAGMA journal_mode=WAL` + `synchronous=NORMAL`；`BEGIN IMMEDIATE`；`PRAGMA table_info` 检查后补 `client_id TEXT NOT NULL DEFAULT 'legacy-default'`、`design_tag TEXT`；`CREATE INDEX IF NOT EXISTS`（`idx_practice_client`、`idx_practice_item`、`idx_step_events_session`、`idx_diagnoses_session`、`idx_attempts_item`）；校验行数；`PRAGMA user_version=1`；提交。
  - 新鲜库 `SCHEMA` 直接含新列；旧库先 `CREATE TABLE IF NOT EXISTS` 再补列；禁止 `DROP TABLE`/重建表/删除旧列。
  - 任一步失败：回滚、记录版本/步骤/原因、抛启动错误；不得半迁移继续服务。
- **文档/证据前置**：是（T0-4 必须先完成；本任务新增 B1-opt1）。
- **依赖任务**：T0-4、T0-6；T3-2/T2-6 依赖本任务。
- **验收命令/断言**：
  - `PRAGMA journal_mode` → `wal`；重复启动 `PRAGMA user_version` 恒为 1。
  - 迁移前后 `SELECT COUNT(*) FROM practice_attempts` 一致；`PRAGMA table_info(practice_attempts)` 含 `client_id/design_tag`。
  - `EXPLAIN QUERY PLAN SELECT * FROM practice_attempts WHERE client_id=? ORDER BY id` 命中 `idx_practice_client`，不出现 `SCAN practice_attempts`。
  - 两个并发写入无用户可见 500；人为制造迁移错误时启动失败，日志含版本/步骤/原因。
  - Docker volume 重启后记录仍在；`git status` 不跟踪 `backend/data/*`。
- **回滚方式**：停服 → 用 `cipherlens.db.bak-v0-*` 替换 → 重启；迁移代码可保留但版本回 0；不删列。

### T3-2 记录摘要按匿名客户端作用域（后端）

- [ ] **状态**：待决策（D-06=A）；D-06 未确认前不启动
- **目标**：`GET /api/records/summary` 按 `X-Client-Id` 过滤；无头返回空汇总而非全库；写路径缺省归 `legacy-default`；healthcheck 仍 200。
- **涉及文件/模块**：`backend/routers/records.py`、`backend/services/records_service.py`、`backend/routers/quiz.py`、追加 `evidence/acceptance/F20-opt1.md`、追加 `evidence/acceptance/F24-opt1.md`。
- **具体改动点**：
  - `records.py` 读取 `Header(None, alias="X-Client-Id")` 与 `scope` query；校验 `c_<32 位小写 hex>`；非法 → 400 `invalid_client_id`。
  - `summary(client_id, scope)`：有合法头 → 该客户端；`scope=legacy` → `legacy-default`；无头且无 legacy → `total=0`、`scope="none"`、HTTP 200，禁止全库聚合。
  - `quiz.py` 读取 `X-Client-Id`，传给 `record_attempt(..., client_id)`；缺省写 `legacy-default`，兼容旧探针。
  - 响应新增 `scope`；旧字段形状保留；`sample_threshold=3` 不变。
- **文档/证据前置**：是（T0-3 登记；本任务先追加 F20/F24 说明，再改代码）。
- **依赖任务**：D-06=A、T3-1、T0-3。
- **验收命令/断言**：
  - 无头 `curl -i /api/records/summary` → 200、`total=0`、`scope="none"`；Docker healthcheck healthy。
  - 客户端 A 做 2 题、B 做 3 题：A `total=2`、B `total=3`；无头不是 5。
  - `scope=legacy` 只返回 `legacy-default`；非法头 400；F20 三态/正确率/趋势/错题跳转仍可用。
- **回滚方式**：回退 router/service 提交；保留 `client_id` 列与数据；接口恢复全库聚合（仅作为旧行为回退，不作为推荐运行态）。

### T3-3 前端匿名标识与记录页隔离

- [ ] **状态**：待决策（D-06=A）；依赖 T3-2
- **目标**：首次访问生成并持久化 `c_<32 位小写 hex>`，记录/提交请求带 `X-Client-Id`；刷新不变；记录页提供 `scope=legacy` 入口；不做登录。
- **涉及文件/模块**：新增 `frontend/src/utils/clientId.ts`、`frontend/src/stores/quiz.ts`、`frontend/src/views/RecordsView.vue`、`frontend/src/types/api.ts`、`frontend/e2e/smoke.spec.ts`（记录页场景按需）、追加 `evidence/acceptance/F20-opt1.md`。
- **具体改动点**：
  - `localStorage['cipherlens.client_id']`；`crypto.getRandomValues` 优先，无则时间戳+随机数；读取已有值不重新生成。
  - `quiz.submit` 请求头 `X-Client-Id`；请求体不变（保持 `extra="forbid"`）。
  - `RecordsView` 请求头 `X-Client-Id`；默认 `scope=client`；无记录空态提供“查看迁移前记录”链接；`scope=legacy` 显示只读提示；400 显示错误+重试，不自动改 id。
  - 不新增 `/login`、用户名/密码/JWT/bcrypt。
- **文档/证据前置**：是（T0-3 登记；本任务追加 F20-opt1 隔离证据）。
- **依赖任务**：D-06=A、T3-2、T2-5（记录页现状）。
- **验收命令/断言**：
  - 刷新后 `localStorage` 值不变；格式匹配 `c_[0-9a-f]{32}`。
  - 两个浏览器上下文 A/B：A=2、B=3；互相不可见；无头 `total=0`。
  - F20 三态、正确率、趋势、错题回看正常；`scope=legacy` 只显示迁移前数据。
  - `rg -n "/login|bcrypt|jsonwebtoken|jwt" frontend/package.json frontend/src` → 0。
- **回滚方式**：回退 fetch 头与 RecordsView scope 逻辑；`clientId.ts` 可保留但不使用；DB 列与数据不删。

### T3-4 Docker、healthcheck 与记录隔离回归

- [ ] **状态**：完整执行需待决策（D-06=A）；未确认时只执行 DB/healthcheck 子集
- **目标**：在 Docker 全栈环境验证 healthcheck、volume 重启、SSE 不缓冲、记录隔离与 Playwright 4/4。
- **涉及文件/模块**：不改源码；新增 `evidence/acceptance/F24-opt1.md`、`F24-opt1-playwright.txt`。
- **具体改动点**：
  - `docker compose up -d --build`；`docker compose ps` 两个服务 healthy。
  - 无头 `curl -i /api/records/summary` → 200 空汇总，healthcheck 不失败。
  - 带客户端提交后重启 backend，记录仍保留；`docker compose exec -T backend python tools/records_probe.py --sql` 核对。
  - SSE `/api/tutor/ask` 帧序列 `meta → token×N → done`，首 token <3s、总时长 <20s。
  - Playwright 4/4；提问用例先步进到 1；判分用例 `.is-downstream=4`（T2-3 后）。
- **文档/证据前置**：是（T0-3；本任务新增 F24-opt1；不覆盖旧 F24-playwright.txt）。
- **依赖任务**：T3-1、T3-2、T3-3、T1-3、T2-3。
- **验收命令/断言**：
  - `docker compose ps` 无 unhealthy；volume 重启后 `total` 不变。
  - 无头 summary 200 且 `total=0`；带 A/B 头隔离正确。
  - SSE 原始帧逐条到达，`Content-Encoding` 无 gzip。
  - Playwright 4/4；Lighthouse 不退化；旧证据未被改写。
- **回滚方式**：仅证据文件可删；无源码回滚。

### T3-5 埋点落库与诊断持久化（条件任务）

- [ ] **状态**：条件任务（默认不执行）；需 D-05=A
- **目标**：仅在用户明确纳入时，建立 `sessions` 整数会话、批量事件落库、诊断接受/拒绝更新；失败不阻塞主链路。
- **涉及文件/模块**：`backend/routers/events.py`、新增 sessions 路由、`backend/db.py`（v2 迁移）、`frontend/src/composables/`（事件队列）、`frontend/src/stores/diagnosis.ts`；新增条件证据。
- **具体改动点**：
  - `POST /api/sessions` 返回整数 `session_id`；`POST /api/events` 事务写 `step_events`；诊断更新 `diagnoses.responded`。
  - 前端 10 条/10 秒批量；`visibilitychange=hidden`/`beforeunload` 用 `sendBeacon`；失败只 `console.warn`。
  - `user_version=2`：`sessions.client_id`、事件/诊断索引；不改主链路。
- **文档/证据前置**：是（D-05 记录；新增条件证据，不改 F18/F20/F21 旧证据）。
- **依赖任务**：D-05=A、T3-1、T3-2。
- **验收命令/断言**：
  - Network 出现 `/api/events`；10 条/10 秒批量；关闭页面事件不丢。
  - DB 事件行数增加，同会话按时间可查；诊断响应字段更新。
  - 后端 500 时页面可继续操作，控制台 warn；F21 p95/长帧/写批次不退化；F18/F20/F24 回归。
- **回滚方式**：事件写入降级为日志；删除 v2 迁移与前端队列；不影响判分/记录主链路。

---

## 阶段 4 · 架构选型与外部依赖（本轮默认不进入）

### T4-1 真实 LLM 适配（条件立项）

- [ ] **状态**：待决策（D-01）；默认 B，不启动
- **目标**：仅在用户明确选择 A/C 时，设计并实现可插拔 LLM 适配器与降级；不谎称已接模型。
- **涉及文件/模块**：`backend/services/tutor_service.py`、新增适配器模块、`.env.example`、B2/F16/F17 证据。
- **具体改动点**：
  - A：OpenAI 兼容适配器，读 `LLM_BASE_URL/LLM_API_KEY/LLM_MODEL`；模板保留 fallback；`meta.source` 区分 `llm/fallback/local`。
  - C：只做适配层 + 环境变量，默认关闭；本地 mock 验证 fallback。
  - 新增依赖必须先取得用户明确同意；本轮默认不引入 SDK。
- **文档/证据前置**：是（D-01 决策；B2 需重录）。
- **依赖任务**：D-01。
- **验收命令/断言**：
  - 无 Key/断网：1s 内切本地模板；恢复后重问可流式；`meta.source` 不谎称 `model`。
  - B2 帧序列、F16/F17 11 态、F24 SSE 回归；成本/网络可复现。
- **回滚方式**：适配器默认关闭；`meta.source="local"`；删除新增适配器与依赖。

### T4-2 单一真相源改造（条件立项）

- [ ] **状态**：待决策（D-03 A/B）；本轮默认 C，不启动
- **目标**：仅在用户明确选择 A/B 时，改造工作台数据源；本轮不把本地 engine 接入判分。
- **涉及文件/模块**：`frontend/src/views/WorkbenchView.vue`、`frontend/src/engine/`、`backend/services/trace_store.py`、B1/B2/F13/F21/F23 证据。
- **具体改动点**：
  - A 后端唯一真相源：工作台使用 `/api/aes/trace` 完整 trace；本地 engine 仅离线兜底并标注。
  - B 前端唯一真相源：提问时 POST 当前步上下文；需处理 B2“不重复传 16 字节”契约变更。
  - 明确 `trace_store` 进程内/上限 64/重启失效为已知边界。
- **文档/证据前置**：是（D-03 决策；B1/B2 重录）。
- **依赖任务**：D-03、T1-4（对账基线）。
- **验收命令/断言**：
  - A：工作台 trace 来自后端；离线只兜底；F13/F21/F23 回归。
  - B：提问上下文完整；请求体大小/契约变更已批准；F16/F17 回归。
  - 判分仍只走后端；`engine` 不进入判分。
- **回滚方式**：恢复本地 trace 渲染；适配器/上下文开关默认关闭。

---

## 阶段 5 · CI 与工程收口

### T5-1 本地验证入口脚本

- [ ] **状态**：待决策（D-07=A）；未确认前不启动
- **目标**：提供不依赖平台的本地验证脚本，串联 build/test/对账/探针，失败非零退出。
- **涉及文件/模块**：新增 `scripts/verify.sh`（Git Bash / Windows 可用）；不新增依赖。
- **具体改动点**：
  - 顺序：`cd frontend && npm test && npm run build`；`python backend/tools/compare_trace.py`；启动后端后运行 `quiz_probe/records_probe/tutor_probe`；可选 Docker。
  - 支持传入 base URL/端口；失败立即非零退出；输出可归档。
- **文档/证据前置**：是（D-07=A 决策）。
- **依赖任务**：D-07=A、T1-4、T1-1/T1-2、T3-1。
- **验收命令/断言**：
  - `bash scripts/verify.sh` 退出 0；人为破坏一处 → 非零退出。
  - `package.json`/`requirements.txt` 无 pytest/httpx 等新增；本地输出与手工命令一致。
- **回滚方式**：删除脚本；不影响运行时。

### T5-2 平台 CI 流水线（条件任务）

- [ ] **状态**：条件任务（默认不执行）；需 D-07=B/C
- **目标**：仅在用户选择 GitHub Actions 或 CodeArts 时，建立最小流水线；不新增测试依赖。
- **涉及文件/模块**：`.github/workflows/ci.yml` 或 CodeArts 流水线 YAML。
- **具体改动点**：
  - 步骤：Node 安装、`npm ci && npm run build && npm test`、Python 探针/对账、失败阻断。
  - 不引入 pytest/httpx；不改变本地命令。
- **文档/证据前置**：是（D-07 B/C + 平台凭证）。
- **依赖任务**：D-07 B/C、T5-1。
- **验收命令/断言**：
  - 流水线运行通过；人为破坏失败可见；本地与 CI 结果一致；运行日志可归档。
- **回滚方式**：删除 workflow 文件；不影响运行时。

### T5-3 全量回归与证据归档

- [ ] **状态**：可执行（在已完成任务范围内执行）
- **目标**：按 RG-01–RG-13 复现存量验收，记录旧值/新值/未达项，确认没有以改阈值/删功能通过审查。
- **涉及文件/模块**：新增/整理 `B1-opt1.md`、`B3-opt1.md`、`F19-opt1.md`、`F20-opt1.md`、`F23-opt1.md`、`F24-opt1.md`、`F21-opt1-lighthouse.json`、`F24-opt1-playwright.txt`；不改源码。
- **具体改动点**：
  - 逐项执行第 6 节回归清单；每项写命令、输出摘要、截图/JSON 引用。
  - 明确 F21 每步 Layout 2.47 仍“未达”，原因沿用 F21 记录；不以新指标替换。
  - 记录依赖清单、`engine` 引用、视觉几何、旧证据未被删改。
  - 若某决策未确认，标注“未纳入/未启动”，不伪造通过。
- **文档/证据前置**：是（新增/整理 opt1 证据；旧文件只追加）。
- **依赖任务**：阶段 0/1/2/3 已执行任务；T3-4；T5-1（若已放行）。
- **验收命令/断言**：
  - RG-01–RG-13 全绿或有明确“未达”记录；无阈值修改、无功能删除。
  - `npm test`、`npm run build`、`compare_trace.py`、Docker、Playwright、Lighthouse 结果归档。
  - `rg` 检索：`待用户批准` 0、学生可见“受污染”0、`PracticeView`/`quiz.ts` 的 `engine` 引用 0、未批准依赖 0。
  - `git status` 本任务只新增/追加证据，不改源码。
- **回滚方式**：删除新增证据文件/追加段落；源码未动。

---

## 6. 回归清单（RG-01–RG-13）

| 编号 | 回归对象 | 必须复现 | 本轮触发 |
|---|---|---|---|
| RG-01 | B1 引擎契约 | C.1 `trace_id=t_b8f9cffc`、`ciphertext=69c4…c55a`、`step_count=40`；C.1/C.2/C.3 `differences=0` | T1-4、T3-1 |
| RG-02 | B2 SSE 契约 | `meta → token×N → done`；断连取消；缓存首字 <100ms | T1-1、T1-2 |
| RG-03 | B3 判分 | 全对/单错/输入非法三分支；`first_diff` 1 格；`propagated` 不返回 null；`input_mismatch` 不计入 | T2-2、T2-3 |
| RG-04 | F16 提问主链路 | 第 13 步回答引用真实字节；卸载后 `window.__sse.active=0` | T1-2、T1-3 |
| RG-05 | F17 11 态 | `idle/waiting/slow/streaming/done/cache/generic/offline/error/interrupted/collapsed`；3s 慢提示；20s 降级；降级后问题不清空 | T1-2、T1-3 |
| RG-06 | F19 判分/跳转/组合态 | `.is-error=1`；`.is-downstream=4`（来源候选）；error+key / downstream+key 组合态；切步撤场；跳转 `?step&byte` | T2-3、T2-5 |
| RG-07 | F20 记录页 | 0/2/10 三态；正确率与 DB 一致；三类 + 未归类；错题跳转；`scope=legacy` | T2-1、T2-6、T3-2、T3-3 |
| RG-08 | F21 性能/Lighthouse | step p95 <100ms；长帧 0；写批次 1；入口 gzip ≤150KB；工作台 ≤220KB；Lighthouse Perf/A11y 不退化；每步 Layout 2.47 仍记“未达” | T1-11、T1-12、T5-3 |
| RG-09 | F22 键盘/live region | 纯键盘链路无焦点丢失；抽屉焦点归还；每步 live region 一次；表格视图 16/16 | T1-3、T1-5、T5-3 |
| RG-10 | F23 URL/错误边界 | `router.replace` 不增历史；`step/view/present/vector` 刷新恢复；错误边界可恢复；离线标识 + 提问禁用 | T1-5、T5-3 |
| RG-11 | F24 Docker/SSE/Playwright | `docker compose up` healthy；SSE 不缓冲；volume 重启保留；Playwright 4/4（提问先步进到 1、判分 downstream=4） | T3-4、T5-3 |
| RG-12 | F7/F15 视觉 | 七态 border 1px（演示 2px）；`--cell-gap` 6px/10px；downstream 与普通格边框同色；格子不位移 | T1-10、T2-3、T2-5 |
| RG-13 | F5/F10/F13 动画通道 | 单 rAF 写；MixColumns 零 stagger、列间 60ms；倍速不改动效时长；合成层 ≤4 | T2-3、T5-3 |

---

## 7. 明确不做项与禁止项

### 7.1 明确不做

- P0-1 真实 LLM 调用（除非 D-01 选 A/C）。
- P1-2 真登录（bcrypt/JWT/注册/跨设备同步）。
- P1-1 埋点落库（默认；仅 D-05 确认 A 后 T3-5）。
- P1-7 平台 CI（默认；仅 D-07 确认 B/C 后 T5-2）。
- P2-3 `both` 分支契约变更。
- P2-4 解密方向算法（`inv_sub_bytes/inv_shift_rows/inv_mix_columns`）。
- P2-5 pytest/httpx/ruff/mypy。
- P2-7 容器非 root。
- P2-9 开发依赖拆分。
- P2-12 ESLint/Prettier/ruff。
- P2-13 组件拆分（`TutorPanel/WorkbenchView/Timeline`）。
- P2-14 bundle 分析与新插件。
- P2-15 skip link。
- P2-17 一键启动脚本。
- P2-18 compose restart/资源限制/端口改造。
- P2-19 README LICENSE。
- P2-20 evidence LFS/体积治理。
- P0-3 A/B 真相源改造（本轮只做 C 对账）。
- P1-4 C/D（题库迁后端、中间态提交）。

### 7.2 禁止项

- 禁止新增 Tailwind、Element Plus、Naive UI、Ant Design、GSAP、anime.js、axios、图表库。
- 禁止为通过审查引入 pytest、httpx、ruff、mypy、ESLint、Prettier、`rollup-plugin-visualizer`。
- 禁止修改 `--cell-gap`（6px / 演示 10px）、七态 `border-width`（1px / 演示 2px）、格子几何。
- 禁止用 `!important` 解决样式冲突；禁止把 downstream 改成虚线、角标、`≠` 或删除边框。
- 禁止前端复算判分、把本地 `engine/` 接入判分路径。
- 禁止为“通过”修改验收阈值、隐藏失败项、删除已验收功能。
- 禁止删除或改写 `evidence/acceptance/` 历史证据原文；只允许追加。
- 禁止把 `propagated` 换个名字继续当“受污染”使用；禁止无法归因时默认写 `key_timing`。
- 禁止修改用户桌面 dify/Docker 环境；项目内 Docker 只验证，不改 compose。
- 禁止写入真实 API Key、Token、密码；禁止提交未清理的 `console.log`（DEV 断言分支除外）。
- 禁止用 `push` 改 URL 历史栈；F23 仍用 `replace`。
- 禁止把 D-01–D-08 的“设计假设”写成“已确认”；禁止把条件任务默认执行。

---

## 8. 完成定义（Definition of Done）

一个任务只有同时满足以下条件才可标记完成：

- [ ] 只改本任务列出的文件/模块，未顺手扩大范围。
- [ ] 对应验收命令全部执行，输出可复现；证据按规则归档。
- [ ] 旧证据原文未删改；新增说明含需求编号、旧值/新值、日期、影响字段。
- [ ] 未引入未批准依赖；未改判分阈值/视觉几何；未把本地 engine 接入判分。
- [ ] 单任务可独立 `git revert`；回滚步骤已记录。
- [ ] 任务涉及的决策门已由用户放行；未放行的保持“待决策”。

---

## 9. 变更记录

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-11-09 | v1.0 | 首次生成；按 design 阶段 0–5 拆分 34 个任务；D-01–D-08 作为决策门 |