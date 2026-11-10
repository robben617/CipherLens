# F23-opt1 · URL / 错误边界回归说明

- 日期：2026-11-10
- F23 原验收（`57f8a65`）保留：step/view/present 同步、刷新恢复、history 不变、错误边界、离线标识。
- 本轮 T1-5 只改“trace 校验/离线提示”：
  - `consistency` 区分 `checking/ok/offline/mismatch`；
  - `checking/offline/mismatch` 禁用提问；`ok` 才使用后端 `trace_id`；
  - A 区新增「重新校验」；`online` 事件重试。
- 未改 F23 的 URL 同步与 `ErrorBoundary` 代码。

## 回归

| 用例 | 结果 |
|---|---|
| 前后端不一致 → 禁问 | Playwright 通过；`.is-mismatch` 消失后恢复 |
| 离线 → 保留矩阵/播放、禁问 | Playwright 通过 |
| F23 旧证据 | 原文未删；旧截图仍可查 |

> F23 的 `cdp-f23.mjs` 未重跑：重跑会覆盖旧截图；本轮以 T1-5 的两条 Playwright 用例与代码边界说明作回归证据。