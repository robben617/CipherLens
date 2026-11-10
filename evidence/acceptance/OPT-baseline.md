# OPT 基线快照（2026-11-10）

- 基线提交：`d3c0870`（T1-8 完成后、阶段 0 证据追记前）
- 日期：2026-11-10
- Node：v24.15.0；Python：3.12.9；Docker CLI：29.7.2
- Docker 引擎：**不可用**（`npipe:////./pipe/dockerDesktopLinuxEngine` 不存在），Docker 回归延后

## 命令与结果

| 命令 | 结果 |
|---|---|
| `npm test`（frontend） | **40/40**，5 个测试文件 |
| `npm run build` | 通过；入口 JS gzip **40.26KB**，WorkbenchView gzip **21.92KB** |
| `python backend/tools/compare_trace.py` | C.1/C.2/C.3 三组 **differences=0** |
| `python backend/tools/quiz_probe.py 8000` | wrong/bad_plaintext/bad_key 均 200；events 204 |
| `python backend/tools/records_probe.py --summary` | `total=5, correct=2, accuracy=0.4`（含历史测试数据） |
| `docker compose ps` | 失败：Docker 引擎不可用 |

## 现有验收值（回归对照）

- B1：C.1 密文 `69c4e0d8…c55a`，40 步，前后端 trace 0 差异。
- B3：`propagated=[8..15]`，first_diff byte 7；旧口径保留。
- F19：`.is-error=1`、`.is-downstream=8`；T2-3 后才改为 4。
- F20：三态门槛 3；真实错误当前 `key_timing`；T2-1 后改 `unattributed`。
- F21：p95 29.4ms、0 长帧、写批次全 1、播放 40 步 0 longtask、合成层 4；每步 Layout **2.47 未达**。
- F24：SSE 7 token 间隔约 30ms；SQLite volume 重启后保留；Playwright 4/4（Docker 引擎不可用时用 dev 8080）。

## 回滚

删除本文件；不影响运行时。Docker 回归在 T3-4/T5-3 重跑。