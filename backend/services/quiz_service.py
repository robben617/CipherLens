from services.aes_impl import AesInputError, build_trace

HEX_CHARS = set("0123456789abcdefABCDEF")


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
    mismatch = _input_mismatch(payload.plaintext_hex, payload.key_hex)
    if mismatch is not None:
        return {
            "summary": {"total_bytes": 0, "wrong_count": 0},
            "first_diff": None,
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

    if not wrong:
        first_diff = None
        propagated = []
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
        # 请求只有最终密文，没有学生中间态；按契约示例采用“首个差异之后的下标”
        # 作为受污染下游字节的可观测口径。
        propagated = list(range(first + 1, 16))

    return {
        "summary": {"total_bytes": 16, "wrong_count": len(wrong)},
        "first_diff": first_diff,
        "propagated": propagated,
        "input_mismatch": None,
        "expected_ciphertext": expected_ciphertext,
    }


def assert_answer_length(answer_hex):
    if len(answer_hex) != 32:
        raise AesInputError(
            "invalid_answer",
            "answer_hex must be 32 hex characters",
            None,
        )