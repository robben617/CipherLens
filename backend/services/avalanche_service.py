"""雪崩实验：改 1 位，看密文变多少位。

AES 的四步里只有两步真正制造「扩散」：列混合让 1 个字节扩散到整列，
行移位再把这一列摊到四列上。叠 10 轮之后，明文改 1 位，输出应该看起来
完全无关 —— 也就是 128 位里约一半翻转。

这个数字不该让学生背，应该让他自己算出来。所以本模块只做一件事：
把「改 1 位」前后的两块密文摆在一起，数差异，交给前端画。
"""

from services.aes_impl import AesInputError, _parse_hex, encrypt_block

TOTAL_BITS = 128
TOTAL_BYTES = 16
IDEAL_BITS = 64  # 理想的扩散结果：128 位里一半翻转


def _parse_inputs(plaintext_hex, key_hex):
    """与 /api/aes/trace 同一套解析口径，报错字段名也一致（plaintext / key）。"""
    plaintext = _parse_hex(plaintext_hex, "plaintext", TOTAL_BYTES)
    key = _parse_hex(key_hex, "key")
    if len(key) * 8 not in (128, 192, 256):
        raise AesInputError("invalid_key", "key must be 16, 24 or 32 bytes", "key")
    return plaintext, key


def _flipped(base, byte_index, bit_index):
    mutated = base[:]
    mutated[byte_index] ^= 1 << bit_index
    return mutated


def _bit_flags(before, after):
    """128 个位是否变化，顺序与十六进制书写一致：字节 0 的 bit7 → bit0，再字节 1 ……

    这个顺序是刻意的：前端把 16 个字节排成一行时，每个字节下面的 8 格
    正好对应它的两位十六进制数字，用户能直接对着 hex 数。
    """
    flags = []
    for index in range(TOTAL_BYTES):
        diff = before[index] ^ after[index]
        for shift in range(7, -1, -1):
            flags.append(bool((diff >> shift) & 1))
    return flags


def _byte_bits(before, after):
    return [(before[index] ^ after[index]).bit_count() for index in range(TOTAL_BYTES)]


def _validate_target(target):
    if target not in ("plaintext", "key"):
        raise AesInputError("invalid_target", "target must be 'plaintext' or 'key'", None)


def compare(plaintext_hex, key_hex, target="plaintext", byte_index=0, bit_index=0):
    plaintext, key = _parse_inputs(plaintext_hex, key_hex)
    _validate_target(target)
    base = plaintext if target == "plaintext" else key

    if not 0 <= byte_index < len(base):
        raise AesInputError(
            "invalid_byte_index",
            f"byte_index must be 0..{len(base) - 1}",
            "byte_index",
        )
    if not 0 <= bit_index <= 7:
        raise AesInputError("invalid_bit_index", "bit_index must be 0..7", "bit_index")

    mutated = _flipped(base, byte_index, bit_index)

    if target == "plaintext":
        before_cipher = encrypt_block(plaintext, key)
        after_cipher = encrypt_block(mutated, key)
    else:
        before_cipher = encrypt_block(plaintext, key)
        after_cipher = encrypt_block(plaintext, mutated)

    flags = _bit_flags(before_cipher, after_cipher)
    per_byte = _byte_bits(before_cipher, after_cipher)
    changed_bits = sum(flags)

    return {
        "target": target,
        "byte_index": byte_index,
        "bit_index": bit_index,
        "key_bits": len(key) * 8,
        # 改的是哪一块输入、改成了什么 —— 前端要原样念给用户听
        "input_before_hex": bytes(base).hex(),
        "input_after_hex": bytes(mutated).hex(),
        "input_byte_before": base[byte_index],
        "input_byte_after": mutated[byte_index],
        "before": {"cipher_hex": bytes(before_cipher).hex(), "cells": before_cipher},
        "after": {"cipher_hex": bytes(after_cipher).hex(), "cells": after_cipher},
        "changed_bits": changed_bits,
        "changed_bytes": sum(1 for count in per_byte if count),
        "total_bits": TOTAL_BITS,
        "total_bytes": TOTAL_BYTES,
        "ideal_bits": IDEAL_BITS,
        "rate": round(changed_bits / TOTAL_BITS, 4),
        "bit_flags": flags,
        "byte_bits": per_byte,
    }


def sweep(plaintext_hex, key_hex, target="plaintext", bit_index=0):
    """把每个字节的最低位各翻一次，统计变化位数分布。

    单次实验容易碰上「刚好变了 58 位」这类数字，看起来像巧合。
    连做 16（或 24 / 32）次、平均下来贴着 64 位，才是「设计如此」的证据。
    """
    plaintext, key = _parse_inputs(plaintext_hex, key_hex)
    _validate_target(target)
    base = plaintext if target == "plaintext" else key

    if not 0 <= bit_index <= 7:
        raise AesInputError("invalid_bit_index", "bit_index must be 0..7", "bit_index")

    before_cipher = encrypt_block(plaintext, key)
    samples = []
    for byte_index in range(len(base)):
        mutated = _flipped(base, byte_index, bit_index)
        after_cipher = (
            encrypt_block(mutated, key) if target == "plaintext" else encrypt_block(plaintext, mutated)
        )
        samples.append(
            {
                "byte_index": byte_index,
                "byte_before": base[byte_index],
                "byte_after": mutated[byte_index],
                "changed_bits": _bit_flags(before_cipher, after_cipher).count(True),
            }
        )

    counts = [sample["changed_bits"] for sample in samples]
    return {
        "target": target,
        "bit_index": bit_index,
        "key_bits": len(key) * 8,
        "trials": len(samples),
        "total_bits": TOTAL_BITS,
        "ideal_bits": IDEAL_BITS,
        "mean": round(sum(counts) / len(counts), 2),
        "min_bits": min(counts),
        "max_bits": max(counts),
        "samples": samples,
    }
