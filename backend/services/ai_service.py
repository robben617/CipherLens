"""通用 AI 问答的服务端契约：上下文白名单、问题规范化、指纹与缓存键。

工作台继续走 tutor_service；这里只服务首页 / S 盒 / 雪崩三个页面。
上下文在服务端再做一次白名单，避免客户端误传明文、密钥或整张表。
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata

SBOX_FIELDS = {"page", "mode", "input", "output", "selected_hex"}
AVALANCHE_FIELDS = {
    "page",
    "target",
    "byte_index",
    "bit_index",
    "key_bits",
    "changed_bits",
    "total_bits",
    "rate",
    "sweep_mean",
}
SELECTED_HEX_RE = re.compile(r"^0x[0-9A-Fa-f]{2}$")


def _is_int(value, minimum: int, maximum: int) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and minimum <= value <= maximum
    )


def _is_number(value, minimum: float, maximum: float) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and minimum <= float(value) <= maximum
    )


def normalize_question(question: str) -> str:
    normalized = unicodedata.normalize("NFKC", question).strip()
    return " ".join(normalized.split())


def sanitize_context(page: str, raw: dict | None) -> tuple[dict, list[str], list[str]]:
    """返回 (clean, missing, ignored)。

    clean 只含该页白名单字段；missing 是必填/可选字段的类型或范围错误；
    ignored 是未知字段名，不回显其值。
    """
    if not isinstance(raw, dict):
        raw = {}
    if page == "home":
        ignored = sorted(str(key) for key in raw if key != "page")
        return {"page": "home"}, [], ignored

    if page == "sbox":
        clean = {"page": "sbox"}
        missing: list[str] = []
        ignored = sorted(str(key) for key in raw if key not in SBOX_FIELDS)

        mode = raw.get("mode")
        if mode in ("forward", "inverse"):
            clean["mode"] = mode
        elif mode is not None:
            missing.append("mode")

        input_value = raw.get("input")
        output_value = raw.get("output")
        input_ok = _is_int(input_value, 0, 255)
        output_ok = _is_int(output_value, 0, 255)
        if input_ok and output_ok:
            clean["input"] = input_value
            clean["output"] = output_value
        else:
            if not input_ok:
                missing.append("input")
            if not output_ok:
                missing.append("output")

        selected = raw.get("selected_hex")
        if isinstance(selected, str) and SELECTED_HEX_RE.fullmatch(selected):
            clean["selected_hex"] = selected
        elif selected is not None:
            missing.append("selected_hex")

        return clean, missing, ignored

    if page == "avalanche":
        clean = {"page": "avalanche"}
        missing: list[str] = []
        ignored = sorted(str(key) for key in raw if key not in AVALANCHE_FIELDS)

        target = raw.get("target")
        if target in ("plaintext", "key"):
            clean["target"] = target
        else:
            missing.append("target")

        byte_index = raw.get("byte_index")
        if _is_int(byte_index, 0, 31):
            clean["byte_index"] = byte_index
        else:
            missing.append("byte_index")

        bit_index = raw.get("bit_index")
        if _is_int(bit_index, 0, 7):
            clean["bit_index"] = bit_index
        else:
            missing.append("bit_index")

        key_bits = raw.get("key_bits")
        if key_bits in (128, 192, 256):
            clean["key_bits"] = key_bits
        else:
            missing.append("key_bits")

        optional = (
            ("changed_bits", 0, 128, _is_int),
            ("total_bits", 0, 128, _is_int),
            ("rate", 0.0, 1.0, _is_number),
            ("sweep_mean", 0.0, 128.0, _is_number),
        )
        for name, minimum, maximum, checker in optional:
            if name not in raw:
                continue
            value = raw.get(name)
            if checker(value, minimum, maximum):
                clean[name] = value
            else:
                missing.append(name)

        return clean, missing, ignored

    raise ValueError(f"unsupported page: {page}")


def context_fingerprint(page: str, clean: dict) -> str:
    if page == "home":
        ordered = {"page": "home"}
    elif page == "sbox":
        ordered = {
            "page": "sbox",
            "mode": clean.get("mode", ""),
            "input": clean.get("input"),
            "output": clean.get("output"),
            "selected_hex": clean.get("selected_hex", ""),
        }
    elif page == "avalanche":
        ordered = {
            "page": "avalanche",
            "target": clean.get("target", ""),
            "byte_index": clean.get("byte_index"),
            "bit_index": clean.get("bit_index"),
            "key_bits": clean.get("key_bits"),
            "changed_bits": clean.get("changed_bits"),
            "total_bits": clean.get("total_bits"),
            "rate": clean.get("rate"),
            "sweep_mean": clean.get("sweep_mean"),
        }
    else:
        raise ValueError(f"unsupported page: {page}")

    payload = json.dumps(ordered, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def ai_cache_key(page: str, fingerprint: str, normalized_question: str) -> str:
    question_hash = hashlib.sha256(normalized_question.encode("utf-8")).hexdigest()[:16]
    return f"{page}:{fingerprint}:{question_hash}"