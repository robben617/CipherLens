# B1-opt1 · 数据库迁移与加固

- 日期：2026-11-10
- 基线：B1 建表 7 张表、C.1 40 步 trace 0 差异（原文未删）

## 迁移实测

| 项 | 实测 |
|---|---|
| `PRAGMA journal_mode` | **wal** |
| `PRAGMA user_version` | **1**（重复启动仍为 1） |
| `practice_attempts` 列 | 含 `client_id`、`design_tag` |
| 行数 | 迁移前 **2** → 迁移后 **2** |
| 备份 | `cipherlens.db.bak-v0-20261110T011531Z`（保留最近 2 份） |
| 幂等 | 第二次 `init_db()` 未新增备份 |
| 索引 | `EXPLAIN QUERY PLAN` 命中 `idx_practice_client`，无 `SCAN practice_attempts` |
| 并发写 | 2 线程同时插入，**0 错误** |

## 说明

- 新库 `SCHEMA` 直接含新列；旧库只 `ALTER TABLE ADD COLUMN`，未删列/重建表。
- 迁移失败会 `ROLLBACK` 并抛启动错误；本轮未人为破坏迁移（避免损坏本地数据），失败路径由代码审查确认。
- `client_id` 默认 `legacy-default`，旧记录无需重写。
- `backend/data/*` 仍被 `.gitignore` 忽略，备份不入库。