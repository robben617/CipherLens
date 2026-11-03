import json
from collections import OrderedDict

MAX_CACHE = 128

_cache = OrderedDict()

OP_LABEL = {
    "sub_bytes": "字节代换",
    "shift_rows": "行移位",
    "mix_columns": "列混合",
    "add_round_key": "轮密钥加",
}


def _hex(values):
    return " ".join(f"{value:02X}" for value in values)


def step_label(step):
    return f"R{step['round']} · {OP_LABEL[step['op']]} · 变化 {len(step['changed'])} 格"


def cache_key(trace_id, step_index, question):
    return (trace_id, step_index, question.strip())


def get_cached(key):
    value = _cache.get(key)
    if value is not None:
        _cache.move_to_end(key)
    return value


def put_cached(key, chunks, label):
    _cache[key] = {"chunks": list(chunks), "step_label": label}
    _cache.move_to_end(key)
    while len(_cache) > MAX_CACHE:
        _cache.popitem(last=False)


def iter_answer_chunks(trace, step_index, question):
    """按子句增量产出；不先拼完整段，再一次性发。"""
    step = trace["steps"][step_index]
    before = _hex(step["state_before"])
    after = _hex(step["state_after"])
    changed = step["changed"]

    yield f"这一步是第 {step['round']} 轮 {OP_LABEL[step['op']]}。"
    yield f"这一步的输入状态是：{before}。"
    yield f"这一步的输出状态是：{after}。"
    if changed:
        yield f"发生变化的字节下标是：{', '.join(str(index) for index in changed)}。"
    else:
        yield "这一步没有字节发生变化。"

    if step["op"] == "mix_columns":
        yield "列混合对每一列做 GF(2^8) 上的矩阵乘法，同列四格必须一起看。"
    elif step["op"] == "shift_rows":
        yield "行移位按行循环左移：第 1 行移 1 格，第 2 行移 2 格，第 3 行移 3 格。"
    elif step["op"] == "sub_bytes":
        yield "字节代换逐格查 FIPS-197 S 盒；这里的输出值就是查表结果。"
    else:
        yield "轮密钥加把当前状态与轮密钥逐字节异或。"

    yield f"你的问题是：“{question.strip()}”。"
    yield "以上数值来自服务端 trace，与当前步的 state 一致；可以对照矩阵逐格核对。"


def sse(event, data):
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"