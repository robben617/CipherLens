"""AI 智能体确定性工具：白名单注册、参数校验、本地意图路由。

设计口径：
- 工具只做「查表 / 读轨迹 / 现算 / 读轮密钥」四件事，全部来自现有服务，
  模型不能执行任意代码，也不联网。
- 每个参数都做 JSON Schema + 范围校验；越界一律 ToolError，不把 traceback 交给模型。
- 返回值里同时给出 summary（给人读）与 hex_values（审计白名单）。
"""

from __future__ import annotations

import re

from services import aes_impl, avalanche_service
from services.glossary import OP_LABEL
from services.trace_store import get_trace

MAX_TOOL_ROUNDS = 2


class ToolError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


# ---------------------------------------------------------------- 参数校验


def _int_arg(params, name, minimum, maximum):
    value = params.get(name)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ToolError(f"invalid_{name}", f"{name} 必须是整数")
    if not minimum <= value <= maximum:
        raise ToolError(f"invalid_{name}", f"{name} 必须在 {minimum}..{maximum} 之间")
    return value


def _hex_arg(params, name, lengths, required=False):
    raw = params.get(name)
    if raw is None:
        if required:
            raise ToolError(f"missing_{name}", f"缺少 {name}")
        return None
    if not isinstance(raw, str):
        raise ToolError(f"invalid_{name}", f"{name} 必须是十六进制字符串")
    text = raw.strip().lower()
    if text.startswith("0x"):
        text = text[2:]
    if len(text) not in lengths or not re.fullmatch(r"[0-9a-f]+", text):
        allowed = " / ".join(str(length) for length in lengths)
        raise ToolError(f"invalid_{name}", f"{name} 需要 {allowed} 个十六进制字符")
    return text


def _trace_arg(params):
    trace_id = params.get("trace_id")
    if not isinstance(trace_id, str) or not trace_id.strip():
        raise ToolError("invalid_trace_id", "缺少 trace_id")
    trace = get_trace(trace_id.strip())
    if trace is None:
        raise ToolError("trace_not_found", "trace_id 不存在或已过期，请先在页面生成一次演示")
    return trace


def _key_from_trace(trace):
    """key_schedule 的前 4/6/8 个词就是原始密钥（每词 4 字节）。"""
    key_words = trace["rounds"] - 6
    words = trace.get("key_schedule") or []
    flat = []
    for word in words[:key_words]:
        flat.extend(word)
    return bytes(flat).hex()


def _initial_state_hex(trace):
    steps = trace.get("steps") or []
    if not steps:
        raise ToolError("trace_empty", "trace 里没有步骤")
    return bytes(steps[0]["state_before"]).hex()


# ---------------------------------------------------------------- 工具实现


def _tool_lookup_sbox(params):
    byte = _int_arg(params, "byte", 0, 255)
    inverse = params.get("inverse", False)
    if not isinstance(inverse, bool):
        raise ToolError("invalid_inverse", "inverse 必须是布尔值")

    table = aes_impl.INV_SBOX if inverse else aes_impl.SBOX
    output = table[byte]
    row = byte >> 4
    col = byte & 15
    label = "逆 S 盒" if inverse else "S 盒"
    return {
        "name": "lookup_sbox",
        "ok": True,
        "summary": (
            f"{label}：输入 0x{byte:02X} 在第 {row} 行第 {col} 列，"
            f"输出 0x{output:02X}"
        ),
        "result": {
            "input": byte,
            "output": output,
            "inverse": inverse,
            "row": row,
            "col": col,
            "input_hex": f"{byte:02X}",
            "output_hex": f"{output:02X}",
            "row_hex": f"{row:X}",
            "col_hex": f"{col:X}",
        },
        "hex_values": [byte, output],
        "action": {"kind": "open-sbox", "label": f"去 S 盒页看 0x{byte:02X}", "value": byte},
    }


def _tool_get_trace_step(params):
    trace = _trace_arg(params)
    step_index = _int_arg(params, "step_index", 0, trace["step_count"] - 1)
    step = trace["steps"][step_index]
    label = step.get("label") or OP_LABEL.get(step["op"], step["op"])
    before = [f"{value:02X}" for value in step["state_before"]]
    after = [f"{value:02X}" for value in step["state_after"]]
    changed = list(step["changed"])
    return {
        "name": "get_trace_step",
        "ok": True,
        "summary": (
            f"第 {step_index} 步（R{step['round']} · {label}）：变化 {len(changed)} 格"
        ),
        "result": {
            "trace_id": trace["trace_id"],
            "step_index": step_index,
            "round": step["round"],
            "op": step["op"],
            "label": label,
            "before": before,
            "after": after,
            "changed": changed,
            "key_indices": list(step.get("key_indices") or []),
            "direction": trace.get("direction", "encrypt"),
        },
        "hex_values": list(step["state_before"]) + list(step["state_after"]),
        "action": {
            "kind": "goto-step",
            "label": f"看第 {step_index + 1} 步",
            "value": step_index,
        },
    }


def _tool_compute_avalanche(params):
    plaintext_hex = _hex_arg(params, "plaintext_hex", (32,))
    key_hex = _hex_arg(params, "key_hex", (32, 48, 64))
    target = params.get("target", "plaintext")
    if target not in ("plaintext", "key"):
        raise ToolError("invalid_target", "target 只能是 plaintext 或 key")
    byte_index = _int_arg(params, "byte_index", 0, 31)
    bit_index = _int_arg(params, "bit_index", 0, 7)

    trace = None
    if plaintext_hex is None or key_hex is None:
        trace = _trace_arg(params)
        plaintext_hex = plaintext_hex or _initial_state_hex(trace)
        key_hex = key_hex or _key_from_trace(trace)

    if target == "key" and byte_index >= len(key_hex) // 2:
        raise ToolError(
            "invalid_byte_index",
            f"改密钥时 byte_index 必须在 0..{len(key_hex) // 2 - 1}",
        )

    result = avalanche_service.compare(
        plaintext_hex,
        key_hex,
        target=target,
        byte_index=byte_index,
        bit_index=bit_index,
    )
    before_hex = result["before"]["cipher_hex"].upper()
    after_hex = result["after"]["cipher_hex"].upper()
    return {
        "name": "compute_avalanche",
        "ok": True,
        "summary": (
            f"改 1 位后密文变化 {result['changed_bits']} / {result['total_bits']} 位"
            f"（{result['changed_bytes']} 个字节）"
        ),
        "result": {
            "target": result["target"],
            "byte_index": result["byte_index"],
            "bit_index": result["bit_index"],
            "changed_bits": result["changed_bits"],
            "changed_bytes": result["changed_bytes"],
            "total_bits": result["total_bits"],
            "ideal_bits": result["ideal_bits"],
            "rate": result["rate"],
            "before_cipher_hex": before_hex,
            "after_cipher_hex": after_hex,
            "input_before_hex": result["input_before_hex"].upper(),
            "input_after_hex": result["input_after_hex"].upper(),
            "input_byte_before": result["input_byte_before"],
            "input_byte_after": result["input_byte_after"],
        },
        "hex_values": (
            list(result["before"]["cells"])
            + list(result["after"]["cells"])
            + [result["input_byte_before"], result["input_byte_after"]]
        ),
        "action": None,
    }


def _tool_get_round_key(params):
    trace = _trace_arg(params)
    round_index = _int_arg(params, "round", 0, trace["rounds"])
    words = trace.get("key_schedule") or []
    start = round_index * 4
    chunk = words[start : start + 4]
    if len(chunk) != 4:
        raise ToolError("round_out_of_range", "这一轮的轮密钥不在当前 trace 里")
    flat = [byte for word in chunk for byte in word]
    label = f"第 {round_index} 轮轮密钥"
    return {
        "name": "get_round_key",
        "ok": True,
        "summary": f"{label}：" + " ".join(f"{byte:02X}" for byte in flat),
        "result": {
            "trace_id": trace["trace_id"],
            "round": round_index,
            "key_hex": "".join(f"{byte:02X}" for byte in flat),
            "words": [list(word) for word in chunk],
        },
        "hex_values": flat,
        "action": {
            "kind": "goto-step",
            "label": f"看第 {round_index + 1} 步",
            "value": min(len(trace.get("steps") or []) - 1, round_index),
        },
    }


# ---------------------------------------------------------------- 注册表


TOOL_REGISTRY = {
    "lookup_sbox": {
        "handler": _tool_lookup_sbox,
        "label": "S 盒",
        "description": "按输入字节查正向或逆向 S 盒，返回结果与行号列号定位。",
        "parameters": {
            "type": "object",
            "properties": {
                "byte": {"type": "integer", "minimum": 0, "maximum": 255},
                "inverse": {"type": "boolean"},
            },
            "required": ["byte"],
            "additionalProperties": False,
        },
    },
    "get_trace_step": {
        "handler": _tool_get_trace_step,
        "label": "当前步轨迹",
        "description": "读取当前 trace 指定步的真实 16 字节状态、操作名与变化格。",
        "parameters": {
            "type": "object",
            "properties": {
                "trace_id": {"type": "string"},
                "step_index": {"type": "integer", "minimum": 0, "maximum": 63},
            },
            "required": ["trace_id", "step_index"],
            "additionalProperties": False,
        },
    },
    "compute_avalanche": {
        "handler": _tool_compute_avalanche,
        "label": "雪崩现算",
        "description": "现场加密两次并统计改 1 位后密文变化了多少位。",
        "parameters": {
            "type": "object",
            "properties": {
                "plaintext_hex": {"type": "string"},
                "key_hex": {"type": "string"},
                "target": {"type": "string", "enum": ["plaintext", "key"]},
                "byte_index": {"type": "integer", "minimum": 0, "maximum": 31},
                "bit_index": {"type": "integer", "minimum": 0, "maximum": 7},
                "trace_id": {"type": "string"},
            },
            "required": ["byte_index", "bit_index"],
            "additionalProperties": False,
        },
    },
    "get_round_key": {
        "handler": _tool_get_round_key,
        "label": "轮密钥",
        "description": "读取当前 trace 指定轮的 16 字节轮密钥。",
        "parameters": {
            "type": "object",
            "properties": {
                "trace_id": {"type": "string"},
                "round": {"type": "integer", "minimum": 0, "maximum": 14},
            },
            "required": ["trace_id", "round"],
            "additionalProperties": False,
        },
    },
}

TOOL_LABELS = {name: meta["label"] for name, meta in TOOL_REGISTRY.items()}


def tool_definitions():
    """OpenAI tools 格式；模型只能从注册表里选。"""
    return [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": meta["description"],
                "parameters": meta["parameters"],
            },
        }
        for name, meta in TOOL_REGISTRY.items()
    ]


PAGE_TOOL_NAMES = ("lookup_sbox", "compute_avalanche")


def page_tool_definitions():
    """栏目页（无 trace）可用工具子集：只保留不需要轨迹的两个。"""
    return [
        definition
        for definition in tool_definitions()
        if definition["function"]["name"] in PAGE_TOOL_NAMES
    ]


def execute_tool(name, params):
    meta = TOOL_REGISTRY.get(name)
    if meta is None:
        raise ToolError("unknown_tool", f"工具 {name} 不在白名单里")
    if not isinstance(params, dict):
        raise ToolError("invalid_params", "工具参数必须是 JSON 对象")
    return meta["handler"](params)


# ---------------------------------------------------------------- 本地意图


_HEX0X_TOKEN = re.compile(r"0[xX]([0-9a-fA-F]{2})(?![0-9a-fA-F])")
_HEX2_TOKEN = re.compile(r"(?<![0-9a-fA-F])([0-9a-fA-F]{2})(?![0-9a-fA-F])")
_HEX_BLOCK = re.compile(r"\b(?:0x)?([0-9a-fA-F]{32}|[0-9a-fA-F]{48}|[0-9a-fA-F]{64})\b")
_STEP_NO = re.compile(r"第\s*(\d+)\s*步")
_ROUND_NO = re.compile(r"第\s*(\d+)\s*轮")
_BYTE_NO = re.compile(r"第\s*(\d+)\s*(?:个)?字节")

PRACTICE_HINTS = ("正确答案", "判分", "得分", "对了几题", "练习答案", "标准答案")


def _first_hex2(question):
    match = _HEX0X_TOKEN.search(question) or _HEX2_TOKEN.search(question)
    return int(match.group(1), 16) if match else None


def detect_tool_call(question, trace=None, step_index=0):
    """轻量意图识别：返回 {name, arguments} 或 None。

    只覆盖校园问答里最常见的几种说法；识别不到就交给模型或本地模板，
    绝不因为「看起来像」而强行调用错误工具。
    """
    question = question or ""
    lowered = question.lower()

    if any(hint in question for hint in PRACTICE_HINTS):
        return None

    has_trace = trace is not None

    if "雪崩" in question or ("改" in question and "位" in question) or "变一半" in question:
        blocks = _HEX_BLOCK.findall(question)
        arguments = {"target": "plaintext", "byte_index": 0, "bit_index": 0}
        if len(blocks) >= 2:
            arguments["plaintext_hex"] = blocks[0]
            arguments["key_hex"] = blocks[1]
        elif len(blocks) == 1:
            arguments["plaintext_hex"] = blocks[0]
        if has_trace:
            arguments["trace_id"] = trace["trace_id"]
        byte_match = _BYTE_NO.search(question)
        if byte_match:
            arguments["byte_index"] = max(0, min(31, int(byte_match.group(1)) - 1))
        if "密钥" in question and "改" in question:
            arguments["target"] = "key"
        return {"name": "compute_avalanche", "arguments": arguments}

    if "s盒" in lowered or "s 盒" in lowered or "查表" in question or "代换" in question:
        byte = _first_hex2(question)
        if byte is not None:
            return {
                "name": "lookup_sbox",
                "arguments": {"byte": byte, "inverse": "逆" in question or "解密" in question},
            }
        return None

    if has_trace and ("轮密钥" in question or "密钥扩展" in question):
        round_match = _ROUND_NO.search(question)
        args = {"trace_id": trace["trace_id"], "round": int(round_match.group(1)) if round_match else trace["steps"][step_index]["round"]}
        return {"name": "get_round_key", "arguments": args}

    if has_trace and (
        "这一步的数据" in question
        or "当前步的数据" in question
        or "这一步的状态" in question
        or "当前步的状态" in question
        or "变了几格" in question
        or "哪几格" in question
        or "哪些格" in question
    ):
        return {
            "name": "get_trace_step",
            "arguments": {"trace_id": trace["trace_id"], "step_index": step_index},
        }

    if has_trace:
        step_match = _STEP_NO.search(question)
        if step_match:
            index = max(0, min(trace["step_count"] - 1, int(step_match.group(1)) - 1))
            return {
                "name": "get_trace_step",
                "arguments": {"trace_id": trace["trace_id"], "step_index": index},
            }

    return None


# ---------------------------------------------------------------- 本地回答


def _hex_list(values):
    return " ".join(f"{value:02X}" for value in values)


def build_tool_local_blocks(tool_result, trace=None, step_index=0, question=""):
    """工具结果 → 四块讲解；无 key/断网时也完整可用。"""
    name = tool_result["name"]
    result = tool_result["result"]
    blocks = []

    if name == "lookup_sbox":
        inverse = result["inverse"]
        label = "逆 S 盒" if inverse else "S 盒"
        blocks.append(
            {
                "type": "conclusion",
                "text": f"{label}查表：0x{result['input_hex']} → 0x{result['output_hex']}。",
            }
        )
        blocks.append(
            {
                "type": "why",
                "items": [
                    f"一个字节拆成高 4 位和低 4 位：0x{result['input_hex']} 的高 4 位是 {result['row_hex']}，低 4 位是 {result['col_hex']}。",
                    f"所以它在第 {result['row']} 行、第 {result['col']} 列；交叉处的值就是 0x{result['output_hex']}。",
                    "加密查正向 S 盒，解密查逆向 S 盒；同一张表，行列的读法完全一样。",
                ],
            }
        )
        blocks.append(
            {
                "type": "next",
                "text": "去 S 盒页对照这一格，确认行列位置和输出值。",
                "action": tool_result.get("action"),
            }
        )
        return blocks

    if name == "get_trace_step":
        changed = result["changed"]
        blocks.append(
            {
                "type": "conclusion",
                "text": (
                    f"第 {result['step_index']} 步是 R{result['round']} · {result['label']}，"
                    f"这 16 格里变了 {len(changed)} 格。"
                ),
            }
        )
        blocks.append(
            {
                "type": "why",
                "items": [
                    f"本步前：{_hex_list([int(value, 16) for value in result['before']])}。",
                    f"本步后：{_hex_list([int(value, 16) for value in result['after']])}。",
                    "这些值来自当前 trace 的真实轨迹，不是模型凭记忆写的。",
                ],
            }
        )
        blocks.append(
            {
                "type": "next",
                "text": "停在当前步对照矩阵；也可以继续下一步观察变化。",
                "action": tool_result.get("action"),
            }
        )
        if trace is not None:
            blocks.append({"type": "cite", "bytes": changed[:3], "total": len(changed)})
        return blocks

    if name == "compute_avalanche":
        blocks.append(
            {
                "type": "conclusion",
                "text": (
                    f"改 1 位后，密文变化 {result['changed_bits']} / {result['total_bits']} 位，"
                    f"涉及 {result['changed_bytes']} 个字节。"
                ),
            }
        )
        blocks.append(
            {
                "type": "why",
                "items": [
                    (
                        f"改动的是第 {result['byte_index']} 字节（索引从 0 计）的第 "
                        f"{result['bit_index']} 位：0x{result['input_byte_before']:02X} → "
                        f"0x{result['input_byte_after']:02X}。"
                    ),
                    f"原密文：{result['before_cipher_hex']}。",
                    f"新密文：{result['after_cipher_hex']}。",
                    "一轮里字节代换、行移位、列混合把差异迅速扩散，所以大约一半位会翻转。",
                ],
            }
        )
        blocks.append(
            {
                "type": "next",
                "text": "到雪崩实验页用同一组明文、密钥和字节复算，页面结果会与这里一致。",
            }
        )
        return blocks

    if name == "get_round_key":
        blocks.append(
            {
                "type": "conclusion",
                "text": f"第 {result['round']} 轮轮密钥是 {result['key_hex']}。",
            }
        )
        words = result["words"]
        blocks.append(
            {
                "type": "why",
                "items": [
                    f"这一轮用到 4 个词，每个词 4 字节：w{result['round'] * 4} 到 w{result['round'] * 4 + 3}。",
                    "密钥扩展每条新词都由上一条词与更早的词异或推出；轮密钥加时逐字节与状态异或。",
                ],
            }
        )
        blocks.append(
            {
                "type": "next",
                "text": "打开左上角的「密钥扩展」抽屉，可以逐词核对这一轮。",
                "action": tool_result.get("action"),
            }
        )
        return blocks

    return blocks


PRACTICE_REFUSAL = {
    "type": "conclusion",
    "text": "练习场景只给分步提示，不直接给答案或判分结果。",
}


def practice_blocks(question):
    return [
        PRACTICE_REFUSAL,
        {
            "type": "why",
            "items": [
                "先写出这一步应该用到的变换，再逐字节核对输入与输出。",
                "卡住时问「这一步为什么变」，而不是问最终答案。",
            ],
        },
        {"type": "next", "text": "回到当前步，把思路写成一行再继续。"},
    ]