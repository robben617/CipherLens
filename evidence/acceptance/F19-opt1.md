# F19-opt1 · 差异/来源字节与题库

- 日期：2026-11-10
- 旧值：`.is-downstream=8`、`propagated=[8..15]`（原 F19 证据保留）。
- 新值：`.is-downstream=4`、`source_bytes=[8,9,10,11]`；`.is-error=1` 不变。

## 实测

| 用例 | 结果 |
|---|---|
| `source_bytes` 契约样例 | error 1 / downstream **4**；额外差异文案「还有 2 个差异字节」 |
| 旧响应缺 `source_bytes` | 回退 `propagated`，downstream **8**，`source_bytes 缺失` warn **1 次** |
| 真实判分 q_043 | error 1 / downstream 4（Playwright 冒烟） |
| 题库 | **8 题**：128×3、192×3、256×2；专项 5 题；无 `expected_ciphertext` |
| 选题 | q_044 AES-192/48 位；q_046 AES-256/64 位；切题 `.is-error` 归零 |
| 回归 | 跳转高亮、组合态、切步撤场沿用 F19 断言；构建通过 |

## 说明

- `propagated` 保留兼容一版，前端新文案不再使用它。
- 旧截图与 8/1 断言不删除，只在 F19 原文末尾追记口径说明。