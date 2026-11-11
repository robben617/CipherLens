from services import quiz_store
from services.aes_impl import AesInputError, build_trace

HEX_CHARS = set("0123456789abcdefABCDEF")


def first_non_hex(value):
    for index, char in enumerate(value):
        if char not in HEX_CHARS:
            return index
    return None


def _empty_result(mismatch, design_tag, design_tag_label, design_tag_hint):
    return {
        "summary": {"total_bytes": 0, "wrong_count": 0},
        "first_diff": None,
        "diff_bytes": [],
        "source_bytes": [],
        "design_tag": design_tag,
        "design_tag_label": design_tag_label,
        "design_tag_hint": design_tag_hint,
        "source_step_index": None,
        "source_round": None,
        "source_step": None,
        "propagated": [],
        "input_mismatch": mismatch,
        "expected_ciphertext": "",
    }


def _input_mismatch(plaintext_hex, key_hex):
    plaintext_bad = first_non_hex(plaintext_hex)
    key_bad = first_non_hex(key_hex)
    if plaintext_bad is None and key_bad is None:
        return None

    if plaintext_bad is not None and key_bad is not None:
        field = "both"
        char_index = key_bad
    elif plaintext_bad is not None:
        field = "plaintext"
        char_index = plaintext_bad
    else:
        field = "key"
        char_index = key_bad

    return {"field": field, "char_index": char_index, "expected": "hex"}


def _item_mismatch(payload, item):
    """提交的明文/密钥必须和题库里这道题给的一致。

    以前题目硬编码在前端，改两个输入框就能把「这道题」换成任意一道；
    题库落库之后以库为准，改过输入就明确告诉用户本题不计入。
    """
    pairs = (("plaintext", payload.plaintext_hex, item["plaintext_hex"]),
             ("key", payload.key_hex, item["key_hex"]))
    bad = [
        (field, submitted, expected)
        for field, submitted, expected in pairs
        if expected and submitted.lower() != expected.lower()
    ]
    if not bad:
        return None

    field, submitted, expected = bad[0]
    index = 0
    for position, (left, right) in enumerate(zip(submitted.lower(), expected.lower())):
        if left != right:
            index = position
            break
    else:
        index = min(len(submitted), len(expected))

    return {
        "field": "both" if len(bad) > 1 else field,
        "char_index": index,
        "expected": "item",
    }


def grade(payload):
    item = quiz_store.meta_for(payload.item_id)
    design_tag = item["design_tag"]
    design_tag_label = item["design_tag_label"]
    design_tag_hint = item["design_tag_hint"]

    if len(payload.key_hex) not in (32, 48, 64):
        raise AesInputError(
            "invalid_key",
            "key must be 32, 48 or 64 hex characters",
            "key",
        )

    if len(payload.key_hex) * 4 != payload.key_bits:
        raise AesInputError(
            "invalid_key",
            f"key_bits={payload.key_bits} 与密钥长度 {len(payload.key_hex) * 4} 位不符",
            "key",
        )

    mismatch = _input_mismatch(payload.plaintext_hex, payload.key_hex)
    if mismatch is not None:
        return _empty_result(mismatch, design_tag, design_tag_label, design_tag_hint)

    mismatch = _item_mismatch(payload, item)
    if mismatch is not None:
        return _empty_result(mismatch, design_tag, design_tag_label, design_tag_hint)

    if first_non_hex(payload.answer_hex) is not None:
        raise AesInputError(
            "invalid_answer_hex",
            "answer_hex must contain only hex characters",
            None,
        )

    trace = build_trace(
        payload.plaintext_hex,
        payload.key_hex,
        payload.key_bits,
        "encrypt",
    )

    expected_ciphertext = trace["output"] or trace["ciphertext"]
    expected_bytes = bytes.fromhex(expected_ciphertext)
    answer_bytes = bytes.fromhex(payload.answer_hex)

    wrong = [
        index
        for index in range(16)
        if answer_bytes[index] != expected_bytes[index]
    ]

    diff_bytes = list(wrong)
    if not wrong:
        first_diff = None
        propagated = []
        source_bytes = []
        source_step_index = None
        source_round = None
        source_step = None
    else:
        first = wrong[0]
        last_step = trace["steps"][-1]
        first_diff = {
            "step_index": last_step["index"],
            "round": last_step["round"],
            "step": last_step["op"],
            "byte_index": first,
            "expected": expected_bytes[first],
            "actual": answer_bytes[first],
        }
        # 兼容字段：仍保留 B3 的“首错之后后缀”，新文案不再使用。
        propagated = list(range(first + 1, 16))
        # 首错下标回溯到上一轮列混合的 4 个来源候选（列优先）。
        row = first % 4
        col = first // 4
        source_col = (col - row) % 4
        source_bytes = [source_col * 4 + r for r in range(4)]
        rounds = trace["rounds"]
        source_step_index = 1 + (rounds - 2) * 4 + 2
        source_round = rounds - 1
        source_step = "mix_columns"

    return {
        "summary": {"total_bytes": 16, "wrong_count": len(wrong)},
        "first_diff": first_diff,
        "diff_bytes": diff_bytes,
        "source_bytes": source_bytes,
        "design_tag": design_tag,
        "design_tag_label": design_tag_label,
        "design_tag_hint": design_tag_hint,
        "source_step_index": source_step_index,
        "source_round": source_round,
        "source_step": source_step,
        "propagated": propagated,
        "input_mismatch": None,
        "expected_ciphertext": expected_ciphertext,
    }
