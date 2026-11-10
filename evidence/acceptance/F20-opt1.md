# F20-opt1 · 未归类错因、匿名隔离与设计意图

- 日期：2026-11-10

## 实测

| 项 | 结果 |
|---|---|
| 真实答错 q_042 | SQL `misconception='unattributed'`、`design_tag='key_timing'` |
| 四桶 | `key_timing=0, mix_coefficient=0, key_schedule=0, unattributed=1`（真实路径） |
| seed 10 | 前三桶 4/1/1、`unattributed=0`（历史合成数据） |
| 记录页标题 | 「错因分布（含未归类）」 |
| 无头 summary | 200、`total=0`、`scope=none`（healthcheck 不失败） |
| 客户端 A / B | A=2、B=3，互不可见；无头不是 5 |
| legacy | `scope=legacy` 只返回 `legacy-default`；非法头 400 `invalid_client_id` |
| 设计意图 | 独立面板「题目设计意图（不是算法诊断）」，与未归类桶分开 |
| 前端 ID | `c_<32 lowercase hex>`；刷新不变 |

## 证据

- `client-scope.spec.ts`：A/B 隔离、刷新不变、legacy 入口。
- `design-tag.spec.ts`：未归类 3 次 + 设计意图「轮密钥时机 · 3 次」。
- 三态门槛 `0/<3/≥3` 不变；旧 0/2/10 截图保留。