# CipherLens 代码审查与优化建议 · v1.0

> 审查日期：2026-11-09
> 审查范围：`D:\project\CipherLens` 全部源码（前端 7765 行 / 后端 1494 行 / Docker 与配置）
> 审查方式：逐文件通读 + 跨层调用链追踪（前端调用点 ↔ 后端路由 ↔ 服务层 ↔ 数据表）
> 结论口径：只写"能指出具体文件行号、能说明为什么值得改"的条目；纯风格偏好不收录

---

## 0. 一句话结论

架构骨架是对的（五区分层、单值 `data-bd`、判分放后端、SSE 代理配置正确），**真正的问题不在代码写得好不好，而在三处"承诺与实现不一致"**：

1. AI 辅导**没有接大模型**，是本地模板拼接 + `sleep` 假装流式；
2. "受污染字节"的算法在教学上是**错的**，会把 15 个正确字节标成"被牵连"；
3. 前端渲染与 AI 回答**用两套独立算出的 AES**，只靠 `trace_id` 对齐，没有任何一致性校验。

前两条评委或老师现场一问就会露，第三条会在后续迭代里静默分叉。这三条是 P0，其余按收益排序。

---

## 1. P0：必须先修的四条

### P0-1　AI 辅导没有接大模型

**证据**

| 位置 | 内容 |
|---|---|
| `backend/services/tutor_service.py:42-67` | `iter_answer_chunks()` 逐句 `yield` 固定模板：「这一步是第 N 轮 XX。」「输入状态是：…」「输出状态是：…」「你的问题是：…」 |
| `backend/routers/tutor.py:120` | `await asyncio.sleep(0.03)` —— 流式的"打字感"是人为 `sleep` 出来的 |
| `backend/routers/tutor.py:66,88` | SSE `meta` 事件里写死 `source: "local"` |
| `backend/requirements.txt` | 只有 fastapi / uvicorn / pydantic，无任何 LLM SDK |
| 全项目 | 无 `.env.example`、无 API Key 读取、无模型调用 |

**影响**

- 大赛评分点 H4 是「AI Agent 能力」。评委问一句"你调的是哪个模型、提示词长什么样、怎么防幻觉"，当前代码答不上来。
- 产品叙事「在卡住的那一刻开口」实际是「把 trace 数字翻译成中文句子」，**没有诊断、没有推理、没有多轮记忆**。学生问「为什么第 5 号字节变了」，回答里只会复述 16 个字节，不会解释原因。
- `TutorPanel.vue` 里精心实现的 11 态降级、`quotes_values` 通用话术分支，全部服务的是一个不存在的模型。

**建议改法（按最小可行顺序）**

1. 新增 `backend/services/llm_client.py`：读 `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL` 三个环境变量，走 OpenAI 兼容协议（这样云端 API 与本地 vLLM / Ollama 可互换，答辩现场断网可切本地）。
2. `tutor_service` 拆成两段：`build_context(trace, step_index, question)` 产出结构化上下文（当前步的 `state_before/after`、`changed`、该步 `key_words` 对应的 4 个轮密钥字节、上一轮同类操作的值），`stream_answer(context)` 才调模型。
3. 提示词里**禁止模型自己算数**：把 32 个十六进制值作为事实传入，要求"只允许引用给定数值，不得自行推导新数值"。这一条同时是 AI 幻觉的防线，也是最容易在答辩里讲出彩的点。
4. 保留现有 `iter_answer_chunks` 作为 `LLM 不可用时的兜底`（改名 `template_answer_chunks`），`meta.source` 改为 `"llm"` / `"fallback"`。**这样 11 态降级立刻变成真功能，而不是模拟**。

**工作量**：1 天（含本地 Ollama 跑通）。**收益**：把"AI 辅导"从演示级变成真功能，是整份报告里性价比最高的一条。

---

### P0-2　"受污染字节"是错的教学口径

**证据**

```python
# backend/services/quiz_service.py:88-90
# 请求只有最终密文，没有学生中间态；按契约示例采用"首个差异之后的下标"
# 作为受污染下游字节的可观测口径。
propagated = list(range(first + 1, 16))
```

这段被 `stores/quiz.ts:28` 接收，再由 `MatrixStage.vue:312` 渲染成矩阵上的 `downstream` 降级态。

**为什么是错的**

AES 最后一轮**没有 MixColumns**，只有 SubBytes → ShiftRows → AddRoundKey。这意味着：

```
密文[c][r] = state_after_shiftrows[c][r] XOR roundkey_last[c][r]
state_after_shiftrows[c][r] = state_before_shiftrows[(c+r) mod 4][r]
```

即：**密文里任意一个字节，只可能由上一状态的一个字节决定**（`ShiftRows` 是纯置换，`AddRoundKey` 是逐字节异或）。所以「第 3 字节错了 → 第 4~15 字节都被污染」在密码学上不成立，那 12 个字节与它没有任何因果关系。

（复核更正：`propagated` **只被前端** `stores/quiz.ts:28` → `MatrixStage.vue:312` 用于渲染，后端统计走的是 `first_diff_byte`，两者不共享。所以这个错误的影响范围是**界面显示**，不是统计数据。但界面恰恰是学生看的地方，优先级不变。）

**建议改法**

1. 新增 `source_bytes`：由差异位置 `(c, r)` 反查 `((c + r) % 4, r)`，得到"唯一可能的来源字节"，最多 4 个（当 4 个差异字节同列时）。这是**真实且可验证**的定位。
2. 现有 `propagated` 改名 `diff_bytes`，语义就是"密文里有差异的字节"，UI 文案从「受污染」改为「差异字节」。
3. 若确实要讲"污染传播"（教学上有价值），必须改成**正向**口径：从某个中间步的错字节出发，用 MixColumns 的列扩散算"它会影响最后哪些字节"，并且需要学生提供中间态 —— 这才是三层反馈里"区域层"的本义。
4. `MatrixStage` 的 `downstream` 七态样式保留，但只挂在 `source_bytes` 上，且必须带标签（否则学生会读成"这些都是错的"）。

**工作量**：半天（算法 20 行 + UI 文案 + 一处验收）。**收益**：这是唯一一条"现在教的是错知识"的问题，优先级等同 P0-1。

---

### P0-3　前后端两套 AES，无一致性校验

**证据**

| 位置 | 说明 |
|---|---|
| `frontend/src/engine/aes.ts`（142 行）+ `trace.ts`（175 行） | 前端完整实现 AES 与 trace 生成 |
| `backend/services/aes_impl.py`（239 行） | 后端完整实现同一套 |
| `WorkbenchView.vue:118-120` | 矩阵数据来自**前端本地** `buildTrace()` |
| `WorkbenchView.vue:199-215` | 后端 `/api/aes/trace` **只用来取 `trace_id`**，返回值只取了 `data.trace_id` |
| `TutorPanel.vue:279` | 提问时把 `trace_id` 发给后端，后端从自己的内存 store 取**另一份** trace 来组织回答 |
| `trace.ts:72-84` / `aes_impl.py:128-134` | 两边各自实现 FNV-1a 生成 `trace_id`，算法相同但**没有任何测试保证它们会一直相同** |

**影响**

- 学生看到的是前端算的矩阵，AI 引用的是后端算的数值。**一旦某一边改动（比如加解密方向、改 MixColumns 写法），画面对与 AI 说错同时存在，且没有任何报错**。
- 前端离线时（`WorkbenchView.vue:216-219`）保留本地 `trace_id`，后端 `trace_store` 里根本没有这条，提问必回 `trace_id 不存在或已过期`。`offlineMode` 只传给了布局组件做视觉提示，**没有禁用提问按钮**。
- 后端 `trace_store` 是进程内 `OrderedDict`，`MAX_TRACES = 64`（`trace_store.py:3-13`）。后端重启、或多个 worker、或换实例，历史 `trace_id` 全部失效。

**建议改法（二选一，推荐 A）**

**A. 后端做唯一真相源**
`buildTrace` 只保留给单测与离线兜底；`WorkbenchView` 直接使用 `/api/aes/trace` 返回的完整 trace（响应体本来就包含 `steps` 全量）。前端本地引擎降级为"后端不可用"分支，并在 UI 上明确标"离线模式：数值由本地引擎生成"。

**B. 前端做唯一真相源（更省服务器）**
每次提问时把当前 step 的 `state_before / state_after / changed / key_words` 一起 POST 给后端，后端只做校验与上下文组装，不查 store。代价是请求体变大（约 200 字节），但**彻底消掉 `trace_store` 这个状态源**。

无论选哪个，都要加一条 CI 断言：
```python
# backend/tools/compare_trace.py 已存在，把它变成 pytest 用例
# 对 3 组 FIPS-197 向量，比对后端 trace 与前端 dump 的 steps 全量 JSON
```
`backend/tools/dump_frontend_trace.mjs` 已经在仓库里，说明这个比对做了一半，只是没接进测试。

**工作量**：A 方案 1 天，B 方案半天。**收益**：消掉本轮所有事故的通因——"同一参数两处各存一份"。

---

### P0-4　学习记录的错因分类永远只有一类有值

**证据**

```python
# backend/services/quiz_service.py:79-86
last_step = trace["steps"][-1]          # 永远是最后一轮的 add_round_key
first_diff = {"step": last_step["op"], ...}
```
```python
# backend/services/records_service.py:17-24
def misconception_for(step):
    if step == "add_round_key": return "key_timing"
    ...
```

`build_trace()` 的循环最后一句固定是 `add_round_key`（`aes_impl.py:226`），所以 `first_diff.step` **恒为 `add_round_key`**，`misconception` **恒为 `key_timing`**。

**影响**

- 「学习记录」页的三类错因分布（轮密钥时机 / 列混合系数 / 密钥扩展方向）**永远只有第一类有数**，另外两个桶恒为 0。
- 答辩展示"错因分布"时会看到一个 100%/0%/0% 的图，等于自证诊断没生效。
- 这不是显示 bug，是归因逻辑本身没有区分度。

**建议改法**

1. 短期（1 小时）：把 `misconception` 改为**按 `source_bytes` 落在哪一轮的哪类操作上归因**（配合 P0-2 的 `source_bytes`）。若无法归因，写 `"unattributed"` 而不是硬塞 `key_timing` —— **宁可显示"未归类"，不要显示一个假的分类**。
2. 中期（半天）：练习模式允许提交**中间态**（哪怕只提交某一轮的 16 字节）。有了中间态，"错在第几步"才可判定，认知诊断才成立。这也是 PRD 里"三层反馈"中认知层的技术前提。
3. `records_service.py:104-115` 的 `most_stuck` 统计依赖 `first_diff_byte`，在 P0-2 修好之前它的输出同样不可信，建议同批修。

---

## 2. 后端：P1 与 P2

### P1-1　埋点接口不落库，`step_events` 表永远是空的

```python
# backend/routers/events.py:12-20
@router.post("/events", status_code=204)
def ingest_events(payload: EventsRequest):
    logger.info("events received session_id=%s count=%s", ...)
    return Response(status_code=204)
```

前端 `step_events` 的每一步停留时长、翻步行为上报后**只打了行日志就丢弃**。后果：

- 认知诊断的触发规则（`stores/diagnosis.ts` 的 7 步滑窗）只在内存里跑，**关掉页面就没有任何证据**；
- 大赛「数据驱动」与「AI 发现学生卡住」这两条叙事，拿不出任何数据支撑。

**更强的证据**：全后端 `grep "INSERT INTO"` 只有两处命中，且都写同一张表 —— `services/records_service.py:42` 与 `tools/records_probe.py:43`（后者是探针脚本），写入 `practice_attempts`。

也就是说 `db.py` 建了 **8 张表，7 张从未被写入**：

| 表 | 状态 |
|---|---|
| `users` / `sessions` | 从未 INSERT（所以无登录、无会话） |
| `step_events` | 从未 INSERT（埋点全丢） |
| `diagnoses` | 从未 INSERT（认知诊断没落库） |
| `quiz_items` | 从未 INSERT（题库硬编码在 `frontend/src/data/quizBank.ts`） |
| `attempts` | 从未 INSERT（判分写的是 `practice_attempts`，`attempts` 是重复设计） |
| `tutor_logs` | 从未 INSERT（LLM 调用无审计，本来该记 prompt 版本与延迟） |
| `practice_attempts` | 唯一在用的表 |

**改法**：`session_id` 是字符串（如 `s_9c21`），与 `sessions.id` 整数主键的映射需要先建会话。最小可行：`POST /api/sessions` 建会话返回 id，`events` 落 `step_events`，`DiagnosisCard` 触发时调 `POST /api/diagnoses` 落 `diagnoses`。约 80 行。

### P1-2　零鉴权，学习记录是全库共享的

- `routers/records.py:8` 直接 `return summary()`，无任何用户维度；
- `db.py` 里 `users`、`sessions.user_id`、`attempts.user_id` 都设计了，但**没有一条 INSERT 进 users**，也没有登录路由；
- PRD 的 PG-9「登录注册」在实现里不存在（`router/index.ts` 只有 5 条路由，无 `/login`）。

**影响**：多人演示时 A 的学习记录会被 B 看到；答辩现场如果两个评委各试一次，记录会混在一起。此外无鉴权意味着 `/api/records/summary` 可被任意爬取。

**改法（按投入选）**

| 方案 | 工作量 | 说明 |
|---|---|---|
| A. 匿名会话 + 本地存储 id | 2 小时 | 前端生成 `client_id` 存 localStorage，请求带上，后端按 `client_id` 分组。够答辩用，不算真鉴权 |
| B. 真登录（bcrypt + JWT） | 1 天 | 需要加 `passlib[bcrypt]`、`python-jose`，`users` 表启用。对应 PRD 的 PG-9 |

建议 A 先做（保证演示不串），B 作为 W4 加分项。

### P1-3　数据库层三处隐患

| 问题 | 位置 | 说明 |
|---|---|---|
| 每次请求新建连接 | `db.py:91-96` | 无连接池；SQLite 每次 `connect()` 开销小但 `PRAGMA foreign_keys` 每连接重设，且未设 `check_same_thread` |
| 未开 WAL | `db.py` | 并发写会 `database is locked`。加 `PRAGMA journal_mode=WAL` 一行即可 |
| 无索引 | `db.py:26-87` | `step_events.session_id`、`practice_attempts.item_id`、`attempts.item_id` 全无索引。数据量一上来，`records_service.summary()` 的 `SELECT *` 全表扫描 + 内存聚合会明显变慢 |
| 无迁移机制 | `db.py` | `CREATE TABLE IF NOT EXISTS` 只能建新表，**加字段不会生效**。要么引入 Alembic，要么写一个 `PRAGMA user_version` 手写迁移 |

### P2 级（不影响演示，但影响长期）

| 编号 | 问题 | 位置 | 建议 |
|---|---|---|---|
| P2-1 | 全局 `Exception` handler 吞掉异常不打日志 | `main.py:76-86`（`_exc` 参数未使用） | `logger.exception(...)` 后再返回 500，否则线上排查零线索 |
| P2-2 | `assert_answer_length()` 是死代码 | `quiz_service.py:101-106` | 删除或接入调用（当前靠 pydantic 长度约束） |
| P2-3 | `_input_mismatch` 的 `both` 分支 `char_index` 取的是 key 的下标 | `quiz_service.py:19-24` | `field="both"` 时返回两个下标，或拆成两条 |
| P2-4 | `direction` 只支持 `encrypt` | `aes_impl.py:177-182` | PRD 若承诺解密视图，需补 `inv_sub_bytes / inv_shift_rows / inv_mix_columns`；若不承诺，把错误信息从 `B1 only supports encrypt trace` 改成面向用户的话术 |
| P2-5 | 无任何测试 | 全后端（1494 行，0 个测试文件） | `requirements.txt` 加 `pytest` + `httpx`，至少覆盖：FIPS 三组向量、`_expand_key` 边界、`grade()` 三种分支、`_parse_hex` 异常。**判分和引擎是纯函数，最该测也最好测** |
| P2-6 | 错误响应格式统一但没有文档 | `main.py:51-86` | 在 `docs` 或 OpenAPI `responses=` 里写明 `{"error":{code,message,field}}`，前端才好按 code 分支 |
| P2-7 | 容器以 root 运行 | `backend/Dockerfile` | 加 `RUN useradd -m app && USER app`，安全合规项打分常看这个 |
| P2-8 | 无 `.env.example` | 仓库根 | 接入 LLM 后必需（`LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL` / `DB_PATH`） |
| P2-9 | 依赖 pin 死但缺开发依赖 | `requirements.txt` | 拆 `requirements-dev.txt`（pytest、httpx、ruff、mypy） |

---

## 3. 前端：P1 与 P2

### P1-4　题库只有 1 道题

```ts
// frontend/src/data/quizBank.ts
export const QUIZ_ITEMS: readonly QuizItem[] = [ { id: 'q_042', ... } ]
```

全文件只有一个 `q_042`。后果：

- 练习模式做第二次就是同一道题，**学习记录页的趋势图只有 1~2 个点**；
- 「错因分布」即使修好 P0-4，样本量也不足以显示任何分布；
- 答辩如果安排两位评委先后试用，第二位会看到和第一位完全一样的题。

**改法**：补到 8~12 道，覆盖 AES-128/192/256 各 2 道 + 列混合单独考查 2 道 + 轮密钥单独考查 2 道，每题带 `misconception_tag`（题库表里已设计该字段，`db.py:48`）。纯数据工作，2 小时。**这是投入产出比最高的内容补强。**

### P1-5　SSE 客户端有三处不符合规范，且存在跨组件互相中断

```ts
// frontend/src/utils/sse.ts:13
else if (line.startsWith('data: ')) data += line.slice(6)
```
| 问题 | 后果 |
|---|---|
| `data:` 后**不跟空格**时不匹配（规范允许 `data:{"t":"x"}`） | 换一个后端实现就整条流失效，且不报错 |
| 多行 `data:` 应**以 `\n` 连接**，现在是直接字符串拼接 | 多行 data 会被粘成一行 |
| 循环结束后 `buffer` 里的残留不 dispatch | 最后一帧若没有 `\n\n` 结尾就丢失（当前后端总是带 `\n\n`，属"靠对方配合"） |
| 无超时、无重连 | 后端挂起时前端永远停在 `waiting`，只能靠用户点停止 |

```ts
// frontend/src/composables/useSSE.ts:3-4, 59
const controllers = new Set<AbortController>()   // 模块级单例
onScopeDispose(abort)                             // 任一组件卸载 -> abort 全部
```

`controllers` 是模块级集合，`onScopeDispose(abort)` 会在**任意一个**使用 `useSSE` 的组件卸载时清空**所有**流。当前只有 `TutorPanel` 用，所以没暴露；一旦练习页也用 SSE，就会出现"关掉面板把别处的回答也掐了"。

**改法**：`controllers` 改为 `useSSE()` 内的局部 `Set`（每个调用方各管各的）；`consumeSSE` 补 `data:` 正则（`/^data:\s?/`）、多行用 `\n` 连接、结束后 flush 残留；加 30s 无 token 超时 → 触发 `onError('timeout')`。

### P1-6　"尚未开始"与"第 0 步"语义被 `Math.max` 抹平

```ts
// TutorPanel.vue:157
const traceStepIndex = computed(() => Math.max(0, props.stepIndex - 1))
```

`playback.currentStep = 0` 表示"一步都还没走"，但 `Math.max(0, -1) = 0` 会让 AI 去讲第 0 步（初始轮密钥加）。学生还没开始就收到"这一步是第 0 轮…"，属于语义错位。

**改法**：`currentStep === 0` 时禁用提问输入，提示"先走一步，我才能讲你看到的东西"。一行判断，同时让产品的"陪伴感"更真实。

### P2 级前端

| 编号 | 问题 | 位置 | 建议 |
|---|---|---|---|
| P2-10 | `tokens.css` 里留着「待用户批准」注释，共 3 处 | `tokens.css:50, 69` | 要么批准（删注释），要么写进视觉规范 §10。**交付物里出现"待批准"字样是硬伤** |
| P2-11 | `index.html` 无 description / OG / theme-color，favicon 是 `data:,` 空占位 | `frontend/index.html` | 补 5 行 meta + 一个真图标。大赛分享链接时会渲染预览卡 |
| P2-12 | 无 ESLint / Prettier / ruff 配置 | 仓库根 | 多人协作无格式闸门，CodeArts 评审时"风格 diff"会淹没真实改动 |
| P2-13 | 组件偏大 | `TutorPanel.vue` 637 行、`WorkbenchView.vue` 611 行、`Timeline.vue` 497 行 | `TutorPanel` 的 11 态可抽成 `useTutorPhase()` composable（状态机与视图分离），至少减 150 行 |
| P2-14 | 无 bundle 分析、无 `manualChunks` | `vite.config.ts` | 加 `build.rollupOptions.output.manualChunks` 拆 vue 全家桶；配 `rollup-plugin-visualizer` 看一眼首屏 |
| P2-15 | 无 skip link | `WorkbenchLayout.vue` | 键盘用户无法跳过导航直达矩阵，无障碍验收项 |
| P2-16 | `vite.config.ts` 无 `build.target` / `base` | 同上 | 部署到子路径时 `base` 必须可配，当前写死默认值 |

---

## 4. 工程与交付

| 编号 | 问题 | 影响 | 建议 |
|---|---|---|---|
| P1-7 | 仓库内**无 CI 配置**（`.github/workflows` 不存在，`.codeartsdoer` 只有平台侧 agent 配置） | 大赛「全流程留痕」要求流水线证据，目前只有本地 `git log`。任何一次误提交都要人工发现 | 加一份最小 workflow：`npm ci && npm run build && npm test` + `pip install -r requirements.txt && pytest`。同时把 CodeArts 流水线的 yaml 也存进仓库（`ci/codearts.yaml`），双平台都有证据 |
| P2-17 | 无一键启动脚本 | 现在要开两个终端分别 `npm run dev` 和 `uvicorn` | 加 `Makefile` 或 `scripts/dev.sh`；`docker compose up` 已可用，写进 README 第一屏 |
| P2-18 | `docker-compose.yml` 无 `restart: unless-stopped`、无资源限制、backend 未映射端口 | 演示机重启后容器不自起；想看 `/docs` 调接口还得进容器 | 补 restart policy + `ports: "8000:8000"`（仅调试用） |
| P2-19 | 无 LICENSE 说明段（有 MIT 文件但 README 未提） | 简历/开源形象 | README 末尾加三行 |
| P2-20 | `evidence/` 3.4 MB / 116 文件已入库 | 合理（大赛要留痕），但仓库会持续变大 | 保持现状；若超过 50 MB 再考虑 Git LFS |

**做得好的地方（不建议改）**

- `docker/nginx.conf` 的 SSE 配置是**正确且罕见**的：`proxy_buffering off` + 该 location `gzip off` + `proxy_read_timeout 60s`。很多人栽在 SSE 被 nginx 攒批，这里处理对了。
- `useMatrixWriter.ts` 的"一个 rAF 内批量写 DOM + 鬼格复制行值"是正确的性能路线，比 `v-for` 绑 32 个响应式对象快一个量级。
- `TraceStep` 全字段 `readonly`、`trace 只生成一次`，这个不可变约定避免了整类"渲染时改数据"的 bug。
- 统一错误格式 `{"error":{code,message,field}}` + `field` 能定位到 `plaintext`/`key`，前后端契约清楚。
- 依赖 pin 到补丁版本、`engines.node >= 20`，可复现性好。

---

## 5. 优先级总表

按「答辩收益 ÷ 改动量」排序，前六条建议在 W3 内做完。

| 顺位 | 编号 | 事项 | 工作量 | 答辩收益 | 风险 |
|---|---|---|---|---|---|
| 1 | P0-1 | AI 接真模型（含本地兜底） | 1 天 | 极高（H4 评分点） | 中（需选型 + Key） |
| 2 | P0-2 | 修"受污染字节"为 `source_bytes` | 半天 | 极高（教学正确性） | 低 |
| 3 | P1-4 | 题库补到 8~12 道 | 2 小时 | 高（练习模式可用） | 极低 |
| 4 | P0-4 | 错因归因改为按来源字节判定 | 1 小时（短期方案） | 高（记录页有数据） | 低 |
| 5 | P0-3 | 消掉双引擎（选 A 或 B） | 半天~1 天 | 中高（架构可信度） | 中 |
| 6 | P1-6 | "尚未开始"禁用提问 | 10 分钟 | 中（体验细节） | 无 |
| 7 | P1-1 | 埋点落库 | 80 行 | 中（数据叙事） | 低 |
| 8 | P1-5 | SSE 客户端修规范 + 作用域 | 2 小时 | 中（健壮性） | 低 |
| 9 | P1-2 | 匿名 client_id 隔离记录 | 2 小时 | 中（演示不串） | 低 |
| 10 | P1-7 | 最小 CI | 2 小时 | 中（留痕证据） | 低 |
| 11 | P2-5 | 后端 pytest（引擎 + 判分） | 半天 | 中（L14 验收） | 低 |
| 12 | P1-3 | DB WAL + 索引 + 迁移 | 2 小时 | 低 | 低 |
| 13 | P2-10/11 | 清理"待批准"注释 + 补 meta | 30 分钟 | 低但显眼 | 无 |

---

## 6. 建议的三天施工顺序

**Day 1 —— 把"教学正确性"修对（P0-2 → P0-4 → P1-4）**

先改判分口径（`source_bytes`），再改归因，再补题库。这三件是同一件事的三个面：**没有正确的差异定位，练习模式就只是个对答案机**。做完当天就能录一段"答错 → 只红一个字节 → 指出它来自哪一轮"的演示。

**Day 2 —— 把 AI 变成真 AI（P0-1）**

上午接 LLM 客户端 + 上下文组装，下午做提示词与兜底切换。验收标准：拔掉网线能在 1 秒内切到模板兜底且 UI 有明确提示；恢复网络后重问能正常流式返回。这一天产出的对话截图是大赛最值钱的证据。

**Day 3 —— 收口（P0-3 + P1-1 + P1-5 + P1-2）**

消双引擎、埋点落库、SSE 规范化、记录隔离。这四项都不改变产品外观，但决定了"这个项目能不能被别人接手"。

---

## 7. 明确不建议做的事

写在这里是为了防止下一轮有人"顺手加上"：

| 不建议 | 原因 |
|---|---|
| 引入 Tailwind / Element Plus / Naive UI | 全站视觉由 `tokens.css` 的 oklch 令牌与七态规则驱动，混入组件库会立刻产生两套间距与色阶，且破坏 `--cell-gap: 6px` 的 chip 语言 |
| 引入 GSAP / anime.js | 动效是"通道化"的（四步各走各的通道，`reduced-motion` 有降级），第三方时间线会接管时序，`F12/F13` 的播放节奏口径会失效 |
| 改 `--cell-gap` 或给格子加位移/缩放 | 这是项目五条硬约束里的两条，历史上已经因此返工过四轮 |
| 前端复算判分结果 | 判分必须单一来源在后端。前端本地引擎只允许出现在"后端不可用"分支，且 UI 必须标注 |
| 把 `propagated` 换个名字继续用 | 语义错了就是错了，`list(range(first+1, 16))` 无论叫什么都不是"受污染" |
| 给 16 个字节格各加一个 Vue 响应式对象做动画 | `useMatrixWriter` 的 rAF 批量写就是为了避开这条，加了会掉帧 |

---

## 8. 一句话交接

代码质量本身不差——**可读、分层清楚、约定被遵守**（`readonly` trace、单值 `data-bd`、rAF 写 DOM 都执行到位了）。真正拖后腿的是三处"文档承诺了、实现没跟上"：AI 没接模型、污染口径算错、双引擎无对账。

修好这三处，这个项目从"设计很好的课程作业"变成"能拿出去讲的产品"；不修，它在答辩现场经不起两个追问。
