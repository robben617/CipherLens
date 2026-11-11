import json
import re
from collections import OrderedDict

from services.glossary import OP_LABEL

MAX_CACHE = 128

_cache = OrderedDict()

# 逐字流式的切片粒度：2 字一帧，中文读起来接近「逐词出现」，
# 一帧 1 字会让 100 字的解释拖到 5 秒以上。
CHUNK_SIZE = 2


def _hex(values):
    return " ".join(f"{value:02X}" for value in values)


def _b(value):
    return f"0x{value:02X}"


def step_label(step, direction="encrypt"):
    """四步中文名 + 方向。解密时补「逆」字（轮密钥加除外，它是自己的逆操作）。"""
    name = OP_LABEL[step["op"]]
    if direction == "decrypt" and step["op"] != "add_round_key":
        name = f"逆{name}"
    return f"R{step['round']} · {name} · 变化 {len(step['changed'])} 格"


def cache_key(trace_id, step_index, question):
    return (trace_id, step_index, question.strip())


def get_cached(key):
    value = _cache.get(key)
    if value is not None:
        _cache.move_to_end(key)
    return value


def put_cached(key, blocks, label):
    _cache[key] = {"blocks": [dict(block) for block in blocks], "step_label": label}
    _cache.move_to_end(key)
    while len(_cache) > MAX_CACHE:
        _cache.popitem(last=False)


# ---------------------------------------------------------------- 举例字节

_HEX_IN_QUESTION = re.compile(r"0x([0-9A-Fa-f]{2})")


def pick_example(before, after, changed, question):
    """挑一格讲。

    优先顺着用户问题里写到的 `0xNN` 去找 —— 问「0x63 是怎么来的」时，
    讲的就是 0x63 那一格，而不是随便第一格。找不到再退回第一个变化字节。
    """
    changed = list(changed)
    pool = changed or list(range(len(before)))

    match = _HEX_IN_QUESTION.search(question or "")
    if match:
        target = int(match.group(1), 16)
        for index in pool:
            if before[index] == target or after[index] == target:
                return index
        for index in range(len(before)):
            if before[index] == target or after[index] == target:
                return index

    return pool[0]


# ---------------------------------------------------------------- 四块正文

NEXT_LEAD = {
    "sub_bytes": "下一步是字节代换：16 个字节逐个查 S 盒。",
    "shift_rows": "下一步是行移位：同一行的字节整体循环左移。",
    "mix_columns": "下一步是列混合：4 个字节按 GF(2⁸) 矩阵乘成一列。",
    "add_round_key": "下一步是轮密钥加：当前状态和下一组轮密钥逐字节异或。",
}

NEXT_LEAD_INV = {
    "sub_bytes": "下一步是逆字节代换：16 个字节逐个查逆 S 盒。",
    "shift_rows": "下一步是逆行移位：同一行的字节整体循环右移。",
    "mix_columns": "下一步是逆列混合：4 个字节按逆矩阵乘回一列。",
    "add_round_key": "下一步是轮密钥加：当前状态和上一组轮密钥逐字节异或。",
}


def _conclusion(step, changed, is_first, direction="encrypt"):
    op = step["op"]
    count = len(changed)
    decrypt = direction == "decrypt"
    if op == "sub_bytes":
        table = "逆 S 盒" if decrypt else "S 盒"
        return f"这一步把 16 个字节逐个换成{table}里的新值，本步有 {count} 格变了。"
    if op == "shift_rows":
        way = "右移" if decrypt else "左移"
        return f"这一步行内循环{way}：第 1 行移 1 格、第 2 行移 2 格、第 3 行移 3 格，第 0 行不动。"
    if op == "mix_columns":
        matrix = "逆矩阵" if decrypt else "矩阵"
        return f"这一列 4 个字节被当成一个整体做 GF(2⁸) 乘法（乘{matrix}），本步有 {count} 格变了。"
    if is_first:
        if decrypt:
            return (
                f"开始解密：密文先和第 {step['round']} 组轮密钥逐字节异或，"
                f"本步有 {count} 格变了。"
            )
        return f"开始加密：明文先和第 0 组轮密钥逐字节异或，本步有 {count} 格变了。"
    return f"当前状态和本轮轮密钥逐字节异或，本步有 {count} 格变了。"


def _why(step, before, after, example, changed, direction="encrypt"):
    op = step["op"]
    index = example
    b, a = before[index], after[index]
    slot = f"第 {index} 格（第 {index % 4 + 1} 行第 {index // 4 + 1} 列）"
    decrypt = direction == "decrypt"

    if op == "sub_bytes":
        if decrypt:
            return [
                "逆 S 盒是正 S 盒的反查表：S⁻¹(S(x)) = x。256 个值在正表里各出现一次，所以能从结果倒查回输入。",
                f"以{slot}为例：{_b(b)} 查逆表得 {_b(a)}；同一个输入永远得到同一个输出。",
                "它把加密时打乱的非线性关系原样撤掉，不然剩下的步骤都能用代数化简还原。",
            ]
        return [
            "S 盒是一张 256 项的固定表：取高 4 位当行、低 4 位当列，查到的就是结果。",
            f"以{slot}为例：{_b(b)} 查表得 {_b(a)}；同一个输入永远得到同一个输出。",
            "它图的是「非线性」：输入与输出之间没有简单的加减乘关系，否则整轮都能被代数化简。",
        ]
    if op == "shift_rows":
        way = "右移" if decrypt else "左移"
        where = "同一行后面的字节顶过来" if not decrypt else "同一行前面的字节退回来"
        return [
            f"矩阵按列存放，所以「行{way}」实际是把这一列里的字节换到了另一列。",
            f"以{slot}为例：{_b(b)} 变成 {_b(a)}，它是被{where}的。",
            "它负责扩散：列混合只在列内混，行移位把混好的结果搬到别的列去。",
        ]
    if op == "mix_columns":
        if decrypt:
            return [
                "逆列混合乘的是 [14 11 13 9] 那一组系数：它和加密矩阵相乘得到单位矩阵。",
                f"以{slot}为例：{_b(b)} 变成 {_b(a)}；同一列另外 3 格也一起变。",
                "GF(2⁸) 里没有除法，14 / 11 / 13 / 9 都是靠 xtime 叠乘算出来的，所以逆矩阵能精确还原。",
            ]
        return [
            "每列乘一个固定矩阵：输出 = 2·a0 ⊕ 3·a1 ⊕ a2 ⊕ a3，后三行只是把这一行旋转一下。",
            f"以{slot}为例：{_b(b)} 变成 {_b(a)}；同一列另外 3 格也一起变了。",
            "这里的乘 2 不是普通乘法：溢出要按 0x11B 约简，正因为它可逆，解密才能把这一步还原。",
        ]

    key = b ^ a
    lines = [
        "异或自带自反性：a ⊕ k ⊕ k 又回到 a，所以同一个操作既是加密的一步，也是解密的一步。",
        f"以{slot}为例：{_b(b)} ⊕ 轮密钥 {_b(key)} = {_b(a)}。",
        "这是整轮里唯一把密钥真正掺进数据的一步；没有它，前面几步都是公开的固定置换。",
    ]
    if not changed:
        lines[1] = f"本步一格都没变，说明这一格对应的轮密钥位正好是 {_b(0)}。"
    return lines


def build_local_blocks(trace, step_index, question):
    """把「这一步发生了什么」拆成结论 / 为什么 / 下一步 / 依据四块。

    原则：不 dump 整行十六进制。要举例只举一格，并说清它为什么变。
    """
    step = trace["steps"][step_index]
    before = list(step["state_before"])
    after = list(step["state_after"])
    changed = list(step["changed"])
    total = trace["step_count"]
    direction = trace.get("direction", "encrypt")

    example = pick_example(before, after, changed, question)
    cite = changed[:3] if changed else [0, 1, 2]

    blocks = [
        {
            "type": "conclusion",
            "text": _conclusion(step, changed, step_index == 0, direction),
        },
        {"type": "why", "items": _why(step, before, after, example, changed, direction)},
    ]

    if step_index + 1 < total:
        next_op = trace["steps"][step_index + 1]["op"]
        leads = NEXT_LEAD_INV if direction == "decrypt" else NEXT_LEAD
        blocks.append(
            {
                "type": "next",
                "text": leads.get(next_op, "继续下一步。"),
                "action": {
                    "label": f"看第 {step_index + 2} 步",
                    "kind": "goto-step",
                    "value": step_index + 2,
                },
            }
        )
    else:
        ending = "明文已经还原" if direction == "decrypt" else "密文已经生成"
        blocks.append(
            {
                "type": "next",
                "text": f"这是第 {total} 步，{ending}。可以回第 0 步再看一遍整轮。",
                "action": {"label": "回第 0 步", "kind": "goto-step", "value": 0},
            }
        )

    blocks.append({"type": "cite", "bytes": cite, "total": len(changed)})
    return blocks


def _chunks(text, size=CHUNK_SIZE):
    for start in range(0, len(text), size):
        yield text[start : start + size]


def iter_block_events(trace, step_index, question):
    """产出 (event, data)：block 开块（文本为空壳），token 出增量。

    缓存命中时直接发完整块，不走这个生成器。
    """
    for block in build_local_blocks(trace, step_index, question):
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
            yield "block", {"type": "next", "text": "", "action": block.get("action")}
            for piece in _chunks(block["text"]):
                yield "token", {"t": piece, "text": piece}

        elif kind == "cite":
            yield "block", dict(block)


def iter_answer_chunks(trace, step_index, question):
    """旧接口：纯文本流。保留给「只想要一段话」的调用方与回归测试。"""
    for block in build_local_blocks(trace, step_index, question):
        if block["type"] == "conclusion":
            yield block["text"]
        elif block["type"] == "why":
            for item in block["items"]:
                yield item
        elif block["type"] == "next":
            yield block["text"]
        elif block["type"] == "cite":
            yield "依据：" + " ".join(f"字节 {index}" for index in block["bytes"]) + "。"


def sse(event, data):
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
