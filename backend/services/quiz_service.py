from services.aes_impl import AesInputError, build_trace

HEX_CHARS = set("0123456789abcdefABCDEF")

QUIZ_ITEM_META = {
    "q_042": ("key_timing", "轮密钥时机"),
    "q_043": ("mix_coefficient", "列混合系数"),
    "q_044": (None, None),
    "q_045": ("mix_coefficient", "列混合系数"),
    "q_046": ("key_timing", "轮密钥时机"),
    "q_047": (None, None),
    "q_048": ("mix_coefficient", "列混合系数"),
    "q_049": (None, None),
}


def first_non_hex(value):
    for index, char in enumerate(value):
        if char not in HEX_CHARS:
            return index
    return None


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


def grade(payload):
    design_tag, design_tag_label = QUIZ_ITEM_META.get(payload.item_id, (None, None))
    mismatch = _input_mismatch(payload.plaintext_hex, payload.key_hex)
    if mismatch is not None:
        return {
            "summary": {"total_bytes": 0, "wrong_count": 0},
            "first_diff": None,
            "diff_bytes": [],
            "source_bytes": [],
            "design_tag": design_tag,
            "design_tag_label": design_tag_label,
            "source_step_index": None,
            "source_round": None,
            "source_step": None,
            "propagated": [],
            "input_mismatch": mismatch,
            "expected_ciphertext": "",
        }

    if first_non_hex(payload.answer_hex) is not None:
        raise AesInputError(
            "invalid_answer_hex",
            "answer_hex must contain only hex characters",
            None,
        )

    if len(payload.key_hex) not in (32, 48, 64):
        raise AesInputError(
            "invalid_key",
            "key must be 32, 48 or 64 hex characters",
            "key",
        )

    trace = build_trace(
        payload.plaintext_hex,
        payload.key_hex,
        payload.key_bits,
        "encrypt",
    )

    expected_ciphertext = trace["ciphertext"]
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
        "source_step_index": source_step_index,
        "source_round": source_round,
        "source_step": source_step,
        "propagated": propagated,
        "input_mismatch": None,
        "expected_ciphertext": expected_ciphertext,
    }
