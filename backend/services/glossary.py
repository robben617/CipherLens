"""术语表 —— 与 frontend/src/data/glossary.ts 一一对应（12 条）。

分工：
- 后端只保留 key / name / en / layer，用于拼句子、生成错因标签、`GET /api/glossary`。
- 长文案（做什么 / 类比 / 常见误解）只在前端维护，因为它们是界面渲染内容，
  后端不参与渲染，抄一份只会制造漂移。

约束：两边 key 集合必须完全一致。由 scripts/check-glossary.mjs 校验，
不一致时脚本退出码非 0，可挂到 CI 或 pre-commit。
"""

from __future__ import annotations

TERMS: tuple[dict[str, str], ...] = (
    {"key": "state", "name": "状态矩阵", "en": "State", "layer": "L1"},
    {"key": "round", "name": "轮", "en": "Round", "layer": "L1"},
    {"key": "sub_bytes", "name": "字节代换", "en": "SubBytes", "layer": "L1"},
    {"key": "shift_rows", "name": "行移位", "en": "ShiftRows", "layer": "L1"},
    {"key": "mix_columns", "name": "列混合", "en": "MixColumns", "layer": "L1"},
    {"key": "add_round_key", "name": "轮密钥加", "en": "AddRoundKey", "layer": "L1"},
    {"key": "sbox", "name": "S 盒", "en": "S-Box", "layer": "L1"},
    {"key": "key_expansion", "name": "密钥扩展", "en": "Key Expansion", "layer": "L1"},
    {"key": "round_key", "name": "轮密钥", "en": "Round Key", "layer": "L1"},
    {"key": "confusion", "name": "混淆", "en": "Confusion", "layer": "L2"},
    {"key": "diffusion", "name": "扩散", "en": "Diffusion", "layer": "L2"},
    {"key": "gf_xor", "name": "GF(2⁸) 与异或", "en": "Galois Field / XOR", "layer": "L2"},
)

GLOSSARY: dict[str, dict[str, str]] = {term["key"]: term for term in TERMS}

# 四步的中文名 —— 全后端唯一来源。
# 原先 aes_impl / tutor_service / records_service 各写一份，措辞一改就会
# 出现「第 2 轮 列混合」和「第 2 轮 列混淆」两种说法，教学产品上这是致命的。
_OP_KEYS = ("sub_bytes", "shift_rows", "mix_columns", "add_round_key")

OP_LABEL: dict[str, str] = {key: GLOSSARY[key]["name"] for key in _OP_KEYS}


def label_of(op: str) -> str:
    """取步骤中文名，未知 op 原样返回，避免上游 KeyError。"""
    return OP_LABEL.get(op, op)
