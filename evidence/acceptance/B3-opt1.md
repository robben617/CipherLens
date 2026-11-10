# B3-opt1 · 判分字段扩展

- 日期：2026-11-10
- 旧口径保留：`propagated` 仍为“首错之后后缀”，旧 F19/F24 证据未改。

## 新字段实测

| 向量 | diff_bytes | source_bytes | source_step_index | source_round |
|---|---|---|---|---|
| C.1（128） | `[7]` | `[8,9,10,11]` | **35** | 9 |
| C.2（192） | `[7]` | `[8,9,10,11]` | **43** | 11 |
| C.3（256） | `[7]` | `[8,9,10,11]` | **51** | 13 |

- 全对：`diff_bytes=[]`、`source_bytes=[]`、来源字段 `null`。
- `input_mismatch`：`diff_bytes=[]`、来源字段 `null`，不计错误。
- 多字节错：`diff_bytes` 返回全部不符下标；`source_bytes` 仍只为首错回溯 4 个候选。
- 判分响应新增 `design_tag/design_tag_label`（T2-6）。
- 回归：三组 trace `differences=0`，`quiz_probe.py` 五条路径通过，旧字段形状不变。