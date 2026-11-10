# F24-opt1 · Docker 与 E2E 回归（含环境阻塞）

- 日期：2026-11-10
- 旧 F24 证据保留：Docker 全栈曾验证 SSE 逐帧、SQLite volume 重启、Playwright 4/4。

## 本轮结果（dev 8080 等效通道）

Docker Desktop 引擎在本轮多次掉线（`npipe ... dockerDesktopLinuxEngine`），按既定口径改用 **Vite dev 8080 + FastAPI 8000**：

| 项 | 实测 |
|---|---|
| 无头 `/api/records/summary` | **200 / total=0 / scope=none** |
| SSE | `meta → token×7 → done`；首 token **0.05ms**、总 **222.15ms**、间隔 **30.0–35.7ms** |
| Playwright 全量 | **12/12 passed（13.0s）** |
| 单测 | **40/40** |
| 构建 | 通过 |

Playwright 12 条：A/B 隔离、一致性/离线、设计意图、选题、source/legacy、4 条 F24 冒烟。
原始输出：`F24-opt1-playwright.txt`。

## 未完成（环境阻塞）

- `docker compose up -d --build` 与 Docker volume 重启回归**未能在本轮执行**；引擎启动后随即再次掉线。
- 该项留到下次 Docker 引擎稳定时补跑；不得把引擎故障当作代码失败。
- 旧 F24 的 Docker/SSE/volume 证据仍有效，未被改写。