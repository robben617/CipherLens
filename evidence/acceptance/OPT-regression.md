# OPT 全量回归报告（2026-11-10）

- 本轮基线：`f4bbd27` 之后继续至 T3/T5；当前分支 `main`
- 单测：**40/40**（5 文件）
- 生产构建：通过；入口 gzip **40.28KB**、WorkbenchView **21.94KB**、quiz **3.56KB**
- Lighthouse Desktop：Performance **100**、Accessibility **100**；FCP=LCP **416.06ms**、TBT **1ms**、CLS **0**（`F21-opt1-lighthouse.json`）
- Playwright：**12/12**（`F24-opt1-playwright.txt`）
- 三向量对账：C.1/C.2/C.3 **differences=0**
- 后端探针：quiz 五路径、records、tutor 冷/热均通过（`scripts/verify.sh` 退出 0）

## RG-01–RG-13

| 编号 | 回归项 | 结果 |
|---|---|---|
| RG-01 | B1 三向量契约 | 通过（0 差异） |
| RG-02 | B2 SSE | 通过（7 token，30–35ms 间隔） |
| RG-03 | B3 判分三分支 | 通过；新增 diff/source 字段，旧字段保留 |
| RG-04 | F19 判分/跳转/组合态 | 通过；downstream 8→4，legacy 回退 8 |
| RG-05 | F20 三态/错误分布 | 通过；新增未归类第 4 桶与客户端隔离 |
| RG-06 | F21 性能/Lighthouse | Lighthouse 双 100；**每步 Layout 2.47 仍未达**（保留原记录） |
| RG-07 | F22 键盘/live region | 冒烟用例通过；代码未改 |
| RG-08 | F23 URL/错误边界 | 旧证据保留；一致性/离线新用例通过 |
| RG-09 | F24 Docker/SSE/E2E | dev 8080 12/12；**Docker 引擎阻塞，volume 重启未执行** |
| RG-10 | F7/F15 视觉 | 未改七态/演示令牌；按原证据保留 |
| RG-11 | F5/F10/F13 动画 | 未改通道时序/写值路径；Layout 口径不变 |
| RG-12 | 输入合法性/错误结构 | 31 位 400、非法客户端 400、OpenAPI 400/500 已声明 |
| RG-13 | 工程收口 | `.env.example`、meta/favicon、Vite base/target、本地 verify 脚本 |

## 未达/未执行（透明记录）

1. **F21 每步 Layout ≤1 未达**：实测 2.47/步；原因与 F21 相同（步头文本 + 矩阵写值；MixColumns 4 列写）。未改阈值、未删动画。
2. **Docker volume 重启回归未执行**：Docker Desktop 引擎反复掉线；T3-4/T5-3 的 Docker 部分留待下次引擎稳定。
3. **T3-5 埋点落库、T4 真实 LLM/单一真相源、T5-2 平台 CI**：按 D-05/D-01/D-03/D-07 默认不执行，未伪造通过。
4. **F23 `cdp-f23.mjs` 未重跑**：避免覆盖旧截图；以 T1-5 新用例和旧证据作回归。

## 禁止项核对

- 未新增 pytest/httpx/图表/UI/动画依赖；
- `PracticeView`/`quiz.ts` 无 `engine` 引用；
- 未修改判分阈值、`--cell-gap`、七态边框/格子几何；
- 旧 evidence 原文未删除，只追加“口径变更说明”；
- 无源码为通过回归而被删/隐藏。
## Docker 补跑（2026-11-10，解除环境阻塞）

- `docker compose ps`：backend/frontend 均 **healthy**（8080→80）。
- 无头 summary：**200 / total=0 / scope=none**。
- A/B 隔离：A **+2**、B **+3**，互不可见。
- volume：C 0 → 提交后 1 → `docker compose restart backend` 后仍 **1**；容器内 SQL 为 `unattributed + key_timing`。
- SSE：7 token，首 **0.23ms**、总 **215.36ms**、间隔 **30.4–31.1ms**，`chunked` 且无 gzip。
- Playwright 冒烟：**4/4 passed**。
- Lighthouse：Performance/Accessibility **双 100**，FCP=LCP **447.54ms**、TBT 4ms、CLS 0。

RG-09 由“Docker 未执行”更新为 **Docker 通过**。F21 每步 Layout **2.47 仍未达**，保持原记录。全量 12 条 Playwright 中 2 条 `?debug=quiz` 用例仅 DEV 可用，生产镜像不暴露 `window.__quiz`，故 Docker 口径以 4 条冒烟 + 非调试用例为准；dev 8080 全量仍 12/12。
