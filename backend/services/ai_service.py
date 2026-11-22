"""通用 AI 问答的服务端契约：上下文白名单、问题规范化、指纹与缓存键。

工作台继续走 tutor_service；这里只服务首页 / S 盒 / 雪崩三个页面。
上下文在服务端再做一次白名单，避免客户端误传明文、密钥或整张表。
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import OrderedDict

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

MAX_AI_CACHE = 128
_ai_cache: "OrderedDict[str, list[dict]]" = OrderedDict()


def get_cached(key: str):
    blocks = _ai_cache.get(key)
    if blocks is None:
        return None
    _ai_cache.move_to_end(key)
    return [dict(block) for block in blocks]


def put_cached(key: str, blocks: list[dict]) -> None:
    _ai_cache[key] = [dict(block) for block in blocks]
    _ai_cache.move_to_end(key)
    while len(_ai_cache) > MAX_AI_CACHE:
        _ai_cache.popitem(last=False)


def quotes_values(page: str, clean: dict) -> bool:
    if page == "home":
        return False
    if page == "sbox":
        return "input" in clean and "output" in clean
    return all(name in clean for name in ("changed_bits", "total_bits", "rate"))


def _hex(value: int) -> str:
    return f"0x{value:02X}"


def build_local_blocks(page: str, clean: dict, question: str) -> list[dict]:
    if page == "home":
        return [
            {
                "type": "conclusion",
                "text": "AES 是 16 字节分组的对称加密：同一把密钥把一块数据经过多轮替换、移位、混合和轮密钥加，最后得到同样 16 字节的密文。",
            },
            {
                "type": "why",
                "items": [
                    "分组固定 16 字节，是为了让每一步都在同样大的 4×4 状态矩阵上计算。",
                    "密钥决定每一轮的轮密钥；128/192/256 位对应 10/12/14 轮。",
                    "四步变换各管一件事：S 盒做非线性替换，行移位打散位置，列混合扩散到整列，轮密钥加引入密钥。",
                ],
            },
            {
                "type": "next",
                "text": "想逐步看某一块数据怎么变，去工作台按播放，或用方向键一步一步走。",
            },
            {
                "type": "cite",
                "bytes": [],
                "refs": [
                    {"label": "通用讲解", "value": "未引用本页数值", "kind": "stat"}
                ],
            },
        ]

    if page == "sbox":
        if "input" in clean and "output" in clean:
            input_hex = _hex(clean["input"])
            output_hex = _hex(clean["output"])
            mode_label = "逆向" if clean.get("mode") == "inverse" else "正向"
            return [
                {
                    "type": "conclusion",
                    "text": f"{input_hex} 查 S 盒得到 {output_hex}：S 盒是一张固定的 256 项替换表，正向查一次，逆向查反表。",
                },
                {
                    "type": "why",
                    "items": [
                        f"把 {input_hex} 拆成高 4 位和低 4 位，分别当作行号和列号，在 16×16 表里找到对应格。",
                        f"当前是{mode_label}模式：{input_hex} → {output_hex}；逆表把 {output_hex} 反查回 {input_hex}。",
                        "S 盒不是随机的：它由 GF(2⁸) 求逆和固定仿射变换构造，256 个输入一一对应 256 个输出。",
                    ],
                },
                {
                    "type": "next",
                    "text": "想把这个字节放回 AES 的某一步看，去工作台找到对应的字节步。",
                },
                {
                    "type": "cite",
                    "bytes": [],
                    "refs": [
                        {"label": "输入", "value": input_hex, "kind": "byte"},
                        {"label": "输出", "value": output_hex, "kind": "byte"},
                        {"label": "方向", "value": mode_label, "kind": "stat"},
                    ],
                },
            ]
        return [
            {
                "type": "conclusion",
                "text": "先在 16×16 网格里选中一个字节，我才能引用真实的输入和输出；现在没有本页数值。",
            },
            {
                "type": "why",
                "items": [
                    "S 盒是 256 项固定替换表，正向和逆向各一张。",
                    "选中字节后，行号和列号由高 4 位、低 4 位决定。",
                    "没有选中值时，我不会编造 0xNN 这样的具体结果。",
                ],
            },
            {
                "type": "next",
                "text": "点网格里的任意一格，再问我这一格为什么变成另一个值。",
            },
            {
                "type": "cite",
                "bytes": [],
                "refs": [
                    {"label": "上下文", "value": "未选中字节", "kind": "stat"}
                ],
            },
        ]

    if all(name in clean for name in ("changed_bits", "total_bits", "rate")):
        target = clean.get("target", "plaintext")
        target_label = "密钥" if target == "key" else "明文"
        position = (
            f"{target_label}第 {clean.get('byte_index')} 字节"
            f"第 {clean.get('bit_index')} 位"
        )
        percent = f"{float(clean['rate']) * 100:.1f}%"
        return [
            {
                "type": "conclusion",
                "text": f"改 1 位后，密文变化了 {clean['changed_bits']}/{clean['total_bits']} 位（{percent}），接近一半，这就是雪崩效应。",
            },
            {
                "type": "why",
                "items": [
                    "AES 的四步变换会把一个字节的改动扩散到整行、整列，再到多轮后的全部字节。",
                    "理想情况下每一位输出对每一位输入都有约 50% 的翻转概率，所以通常会接近一半，而不是每次都正好一半。",
                    f"这次改的是{position}；连续做多次取平均，比单次结果更能看出扩散是否充分。",
                ],
            },
            {
                "type": "next",
                "text": "可以再换一个位置或位重复实验，观察变化位数是否仍围绕一半波动。",
            },
            {
                "type": "cite",
                "bytes": [],
                "refs": [
                    {"label": "变化位数", "value": str(clean["changed_bits"]), "kind": "stat"},
                    {"label": "总位数", "value": str(clean["total_bits"]), "kind": "stat"},
                    {"label": "比例", "value": percent, "kind": "stat"},
                    {"label": "位置", "value": position, "kind": "position"},
                ],
            },
        ]

    return [
        {
            "type": "conclusion",
            "text": "先跑一次实验，我才能引用这次真实的位数变化；现在没有实验结论。",
        },
        {
            "type": "why",
            "items": [
                "雪崩效应看的是输入改 1 位后，输出有多少位跟着翻转。",
                "目标通常接近总位数的一半，但单次会有波动。",
                "没有实验结果时，我不会编造 62/128 这类具体数字。",
            ],
        },
        {
            "type": "next",
            "text": "先点「开始演示」跑一次，再回来问为什么是这个比例。",
        },
        {
            "type": "cite",
            "bytes": [],
            "refs": [
                {"label": "上下文", "value": "无实验结论", "kind": "stat"}
            ],
        },
    ]


def _chunks(text: str, size: int = 2):
    for start in range(0, len(text), size):
        yield text[start : start + size]


def iter_ai_events(page: str, clean: dict, question: str):
    for block in build_local_blocks(page, clean, question):
        kind = block["type"]
        if kind == "conclusion":
            yield "block", {"type": "conclusion", "text": ""}
            for piece in _chunks(block["text"]):
                yield "token", {"t": piece, "text": piece}
        elif kind == "why":
            yield "block", {"type": "why", "items": []}
            for item in block["items"]:
                first = True
                for piece in _chunks(item):
                    payload = {"t": piece, "text": piece}
                    if first:
                        payload["item"] = True
                        first = False
                    yield "token", payload
        elif kind == "next":
            yield "block", {
                "type": "next",
                "text": "",
                **({"action": block["action"]} if "action" in block else {}),
            }
            for piece in _chunks(block["text"]):
                yield "token", {"t": piece, "text": piece}
        elif kind == "cite":
            yield "block", dict(block)
