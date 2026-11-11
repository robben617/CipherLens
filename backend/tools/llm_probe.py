"""F10 的离线联调工具。

真实 key 不是随时都有，但「模型吐字 → 四块解析 → 降级」这条链路必须能验。
所以这里自带一个假的 OpenAI 兼容服务：它照着请求里的 before/after 编一段
格式正确的回答，用来验证解析、状态点、依据块；另开两条坏路径验证降级。

    py tools/llm_probe.py selfcheck          # 纯本地：解析器 + 降级链自检
    py tools/llm_probe.py mock 8099          # 假模型服务（/v1 正常 /bad 500 /slow 慢）
    py tools/llm_probe.py ask 8000           # 打一次 SSE，打印 meta / 分块 / done

用法顺序（演示 LLM 路径，不需要真 key）：
    1. py tools/llm_probe.py mock 8099
    2. LLM_BASE_URL=http://127.0.0.1:8099/v1 LLM_API_KEY=fake LLM_MODEL=mock \\
       py -m uvicorn main:app --port 8000
    3. py tools/llm_probe.py ask 8000
"""

import http.client
import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# 从 tools/ 直接跑时要能 import services.*
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PLAINTEXT = "00112233445566778899aabbccddeeff"
KEY = "000102030405060708090a0b0c0d0e0f"
STEP = 13

REPLY_LINES = [
    "【结论】",
    "这一步把这一列 4 个格当成一个整体做 GF(2⁸) 乘法，所以改一格整列都变。\n",
    "【为什么】\n",
    "- 每列乘的是同一个固定矩阵，四行只是把它旋转了一下。\n",
    "- 以第 {index} 格为例：{before} 变成了 {after}，同列另外三格也跟着动。\n",
    "- 乘 2 不是普通乘法，溢出要按 0x11B 约简，正因为它可逆，解密才还原得回来。\n",
    "【下一步】\n",
    "下一步把这列的结果和轮密钥逐字节异或。\n",
]


def merge(events):
    """像前端那样把 block + token 拼成完整块。

    服务端发的是「空壳块 + 增量」，**服务端自己不留拼好的副本**；
    所以任何想验内容的地方都得在这儿拼一次，否则看到的永远是空 items。
    """
    blocks = []
    for event, data in events:
        if event == "block":
            blocks.append(dict(data))
        elif event == "token" and blocks:
            last = blocks[-1]
            text = data.get("t", "")
            if last["type"] in ("conclusion", "next"):
                last["text"] = last.get("text", "") + text
            elif last["type"] == "why":
                if data.get("item") or not last["items"]:
                    last["items"].append(text)
                else:
                    last["items"][-1] += text
    return blocks


# ---------------------------------------------------------------- 假模型

def _reply_text(user_payload, lie=False):
    step = user_payload or {}
    before = (step.get("before") or "").split()
    after = (step.get("after") or "").split()
    changed = step.get("changed") or []
    index = changed[0] if changed else 0
    values = {
        "index": index,
        "before": f"0x{before[index]}" if index < len(before) else "0x00",
        "after": f"0x{after[index]}" if index < len(after) else "0x00",
    }
    text = "".join(line.format(**values) for line in REPLY_LINES)
    if lie:
        # 挑一个本步 before/after 里确实没有的字节，才叫「编造」
        used = {int(value, 16) for value in before + after}
        fake = next((value for value in range(0xF0, 0x100) if value not in used), 0xFF)
        text = text.replace("【下一步】", f"- 顺便说，0x{fake:02X} 也跟着变了。\n【下一步】")
    return text


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_args):  # 安静点，别把 probe 输出冲掉
        pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            body = {}

        if self.path.startswith("/bad"):
            self.send_response(500)
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b"{}")
            return

        user = ""
        for message in body.get("messages") or []:
            if message.get("role") == "user":
                user = message.get("content") or ""
        try:
            user_payload = json.loads(user)
        except json.JSONDecodeError:
            user_payload = {}

        text = _reply_text(user_payload, lie=self.path.startswith("/liar"))
        if self.path.startswith("/slow"):
            time.sleep(1.0)

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()

        # 4 个字一段，模拟真实的逐字节奏
        for start in range(0, len(text), 4):
            chunk = {
                "choices": [{"delta": {"content": text[start : start + 4]}}],
            }
            frame = f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n".encode("utf-8")
            self._write_chunk(frame)
            time.sleep(0.02)
        self._write_chunk(b"data: [DONE]\n\n")
        self._write_chunk(b"")

    def _write_chunk(self, data):
        self.wfile.write(f"{len(data):X}\r\n".encode("ascii"))
        self.wfile.write(data)
        self.wfile.write(b"\r\n")
        self.wfile.flush()


def serve_mock(port):
    server = ThreadingHTTPServer(("127.0.0.1", port), _Handler)
    print(f"mock llm listening on http://127.0.0.1:{port}")
    print("  POST /v1/chat/completions   正常流式")
    print("  POST /bad/chat/completions  500")
    print("  POST /slow/chat/completions 先睡 1 秒")
    print("  POST /liar/chat/completions 编一个不存在的字节 0xAB")
    server.serve_forever()


# ---------------------------------------------------------------- 解析器自检

def selfcheck():
    from services.llm_service import BlockAssembler, allowed_hex

    checks = []

    def check(name, condition, detail=""):
        checks.append((name, bool(condition), detail))

    text = "".join(line.format(index=4, before="0x02", after="0x8E") for line in REPLY_LINES)
    asm = BlockAssembler([4, 5, 6, 7], 4)
    events = asm.start()
    for start in range(0, len(text), 5):
        events.extend(asm.feed(text[start : start + 5]))
    events.extend(asm.finish())

    blocks = merge(events)
    kinds = [block["type"] for block in blocks]
    check("四块齐", kinds == ["conclusion", "why", "next", "cite"], str(kinds))

    why = next(block for block in blocks if block["type"] == "why")
    check("为什么三条", len(why["items"]) == 3, str(len(why["items"])))
    check("条目不带列表符号", not why["items"][0].startswith("-"), why["items"][0][:12])
    check("条目是整句", why["items"][1].endswith("。"), why["items"][1][-6:])

    tokens = [data for event, data in events if event == "token"]
    items = [token for token in tokens if token.get("item")]
    check("每条 item 只标一次", len(items) == 3, str(len(items)))

    conc = next(block for block in blocks if block["type"] == "conclusion")["text"]
    check("结论没把标题吞进去", "【结论】" not in conc, conc[:20])

    # 模型不按格式来：整段都该落进结论块，一个字不丢
    asm2 = BlockAssembler([1], 1)
    asm2.start()
    plain = "这一步就是查表，查完就过去了。"
    for start in range(0, len(plain), 3):
        asm2.feed(plain[start : start + 3])
    body = "".join(data["t"] for event, data in asm2.finish() if event == "token")
    check("无格式不丢字", body == plain, body[:20])

    # 单行超过 48 字还没换行也要先吐，别让读者干等
    asm3 = BlockAssembler([1], 1)
    asm3.start()
    early = asm3.feed("字" * 60)
    check("长行提前吐字", len(early) >= 1, str(len(early)))

    # 编造的十六进制能被抓出来
    asm4 = BlockAssembler([2], 1)
    asm4.start()
    asm4.feed("这里是 0xAB，那里是 0x02。\n")
    outside = asm4.hex_outside({2, 3})
    check("抓编造值", outside == [0xAB], str([hex(v) for v in outside]))

    # 0x11B 是约简多项式，不是「0x11」这个字节
    asm5 = BlockAssembler([2], 1)
    asm5.start()
    asm5.feed("溢出要按 0x11B 约简。\n")
    check("多项式不算字节", asm5.hex_outside({2}) == [], str(asm5.hex_outside({2})))

    allowed = allowed_hex({"steps": [{"state_before": [0, 1], "state_after": [2, 3]}]}, 0, "0x7F 呢")
    check("允许集合含问题里的值", {0x7F, 0, 1, 2, 3} <= allowed, str(sorted(allowed)))

    failed = [name for name, ok, _ in checks if not ok]
    for name, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'} {name}" + (f"  ({detail})" if not ok else ""))
    print(f"selfcheck: {len(checks) - len(failed)}/{len(checks)} passed")
    if failed:
        raise SystemExit(1)


# ---------------------------------------------------------------- 打一次 SSE

def post_json(port, path, payload):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    connection.request(
        "POST",
        path,
        body=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    response = connection.getresponse()
    data = response.read().decode("utf-8")
    connection.close()
    if response.status >= 400:
        raise RuntimeError(f"{path} HTTP {response.status}: {data}")
    return json.loads(data)


def ask(port):
    trace = post_json(
        port,
        "/api/aes/trace",
        {
            "plaintext_hex": PLAINTEXT,
            "key_hex": KEY,
            "key_bits": 128,
            "direction": "encrypt",
        },
    )
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=60)
    body = json.dumps(
        {"trace_id": trace["trace_id"], "step_index": STEP, "question": "这几格为什么一起变？"},
        ensure_ascii=False,
    ).encode("utf-8")
    connection.request(
        "POST",
        "/api/tutor/ask",
        body=body,
        headers={"Content-Type": "application/json; charset=utf-8", "Accept": "text/event-stream"},
    )
    response = connection.getresponse()
    start = time.perf_counter()
    meta = None
    events = []
    errors = []
    done = None
    first_token_ms = None
    event = None

    while True:
        line = response.readline()
        if not line:
            break
        text = line.decode("utf-8").rstrip("\r\n")
        if text.startswith("event: "):
            event = text[7:]
        elif text.startswith("data: "):
            data = json.loads(text[6:])
            if event == "meta":
                meta = data
            elif event in ("block", "token"):
                events.append((event, data))
            elif event == "error":
                errors.append(data)
            elif event == "done":
                done = data
            if event == "token" and first_token_ms is None:
                first_token_ms = round((time.perf_counter() - start) * 1000, 1)
        elif text == "":
            event = None
    connection.close()

    blocks = merge(events)

    total_ms = round((time.perf_counter() - start) * 1000, 1)
    kinds = [block["type"] for block in blocks]
    print(f"meta.source={meta.get('source')} model={meta.get('model')} cache={meta.get('cache')}")
    print(f"blocks={kinds}")
    print(f"first_token_ms={first_token_ms} total_ms={total_ms}")
    print(f"errors={errors}")
    print(f"done={done}")
    for block in blocks:
        if block["type"] == "why":
            for item in block["items"]:
                print(f"  why: {item}")
        elif block["type"] == "next":
            print(f"  next: {block['text']}")
        elif block["type"] == "cite":
            print(f"  cite: {block['bytes']} / 共 {block.get('total')}")
    return meta, kinds, errors


def main(argv):
    command = argv[1] if len(argv) > 1 else "selfcheck"
    if command == "selfcheck":
        selfcheck()
    elif command == "mock":
        serve_mock(int(argv[2]) if len(argv) > 2 else 8099)
    elif command == "ask":
        ask(int(argv[2]) if len(argv) > 2 else 8000)
    else:
        print(__doc__)
        raise SystemExit(2)


if __name__ == "__main__":
    main(sys.argv)
