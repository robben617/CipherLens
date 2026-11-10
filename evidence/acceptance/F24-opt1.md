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
## 2026-11-10 Docker 补跑（通过）

Docker 引擎恢复后按原 T3-4/T5-3 口径补跑，未改任何源码：

| 项 | 实测 |
|---|---|
| `docker compose ps` | backend **healthy**、frontend **healthy**（8080→80） |
| 无头 summary | **200 / total=0 / scope=none** |
| A/B 隔离（增量） | A **+2**、B **+3**，互不可见 |
| volume 重启 | C 提交前 0 → 提交后 1 → `docker compose restart backend` 后仍 **1** |
| 容器内 SQL | `client_id=c_333…`、`misconception=unattributed`、`design_tag=key_timing` |
| SSE | 7 token；首 token **0.23ms**、总 **215.36ms**、间隔 **30.4–31.1ms**；`chunked`、无 `Content-Encoding` |
| Playwright 冒烟 | **4/4 passed（6.4s）** |
| Lighthouse | Performance **100**、Accessibility **100**；FCP=LCP **447.54ms**、TBT 4ms、CLS 0 |

说明：生产镜像不暴露 `?debug=quiz` 的 `window.__quiz`，因此全量套件在 Docker 下为 10 passed + 2 个仅 DEV 调试用例失败；这 2 条在 dev 8080 全量套件中通过（12/12）。Docker 口径以 4 条冒烟 + 非调试用例为准，不把生产不暴露的调试入口判为缺陷。

原始输出：`F24-opt1-playwright-docker.txt`、`F21-opt1-docker-lighthouse.json`。
