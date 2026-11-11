"""真实 LLM 接入 —— OpenAI 兼容的 /chat/completions 流式接口。

为什么不用各家 SDK：这条链路上唯一需要的东西是「一行一帧的 `data: {...}`」，
而 chat/completions 的流式协议早就统一了。装 SDK 等于把版本升级、代理配置、
异步客户端这些变量一起引进来，出问题时先要排查 SDK 而不是自己的代码。
httpx 只做三件事：POST 一个 JSON、读 SSE 行、超时。

降级是硬要求（答辩现场的网络不可控）：
    未配置 key            → 直接走本地模板，`source=local`
    首字前失败 / 超时 / 429 / 5xx → 重试一次（超时 ×1.5），仍失败再由调用方降级
    已经吐了一部分再断      → 不推倒重来，把断点告诉前端（retryable）
"""

from __future__ import annotations

import json
import logging
import os
import re

import httpx

from services.glossary import OP_LABEL

logger = logging.getLogger("cipherlens.llm")

TIMEOUT_DEFAULT = 20.0
RETRY_FACTOR = 1.5
MAX_TOKENS_DEFAULT = 400
QUESTION_LOG_LIMIT = 80


class LLMUnavailable(Exception):
    """模型不可用。`partial` 为真表示已经发出过内容，不能再从头重放。"""

    def __init__(self, code, message, *, retryable=True, partial=False):
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.partial = partial
        self.audit = None


# ---------------------------------------------------------------- 配置

def _num_env(name, default, cast):
    raw = os.getenv(name, "")
    if not raw.strip():
        return default
    try:
        return cast(raw)
    except ValueError:
        logger.warning("bad env %s ignored", name)
        return default


def config():
    """每次调用现读环境变量：测试和演示都要能在不重启的情况下切 key。"""
    return {
        "base_url": os.getenv("LLM_BASE_URL", "").strip().rstrip("/"),
        "api_key": os.getenv("LLM_API_KEY", "").strip(),
        "model": os.getenv("LLM_MODEL", "").strip(),
        "timeout": _num_env("LLM_TIMEOUT_S", TIMEOUT_DEFAULT, float),
        "max_tokens": _num_env("LLM_MAX_TOKENS", MAX_TOKENS_DEFAULT, int),
    }


def enabled():
    values = config()
    return bool(values["base_url"] and values["api_key"] and values["model"])


def public_status():
    """给 /api/health 用。**不含 base_url 与 key**。"""
    values = config()
    return {
        "enabled": bool(values["base_url"] and values["api_key"] and values["model"]),
        "model": values["model"] or None,
    }


# ---------------------------------------------------------------- 提示词

SYSTEM_PROMPT = """你是 AES 教学助手，面对刚学密码学的大学生。
学生正在看：{label}（整条链路的第 {index} 步，从 0 计）。
规则：
1. 只讲当前这一步，不要扩展到整轮或整个算法。
2. 十六进制数值只能照抄给定的 before / after，禁止自己推算或编造。
3. 用中文口语，全文不超过 220 字。
4. 严格按下面的标题格式输出，标题单独占一行，不加粗、不用代码块：
【结论】
一句话说清这一步做了什么。
【为什么】
- 第一条
- 第二条
【下一步】
一句话说明下一步做什么。
5. 数据里看不出来的地方就说「这一步的数据里看不出」，不要猜。"""


def _hex(values):
    return " ".join(f"{value:02X}" for value in values)


def build_messages(trace, step_index, question):
    """只带当前步（和前后步的 op 名），不带全量 trace。

    全量 trace 有 40 步 × 16 字节，模型读不完也读不准，还费 token；
    讲这一步需要的全部信息就在这一步的 before / after / changed 里。
    """
    steps = trace["steps"]
    step = steps[step_index]
    prev_op = steps[step_index - 1]["op"] if step_index > 0 else None
    next_op = steps[step_index + 1]["op"] if step_index + 1 < len(steps) else None

    system = SYSTEM_PROMPT.format(
        label=step.get("label") or OP_LABEL.get(step["op"], step["op"]),
        index=step_index,
    )
    user = {
        "round": step["round"],
        "op": step["op"],
        "op_label": OP_LABEL.get(step["op"], step["op"]),
        "before": _hex(step["state_before"]),
        "after": _hex(step["state_after"]),
        "changed": list(step["changed"]),
        "prev_op": OP_LABEL.get(prev_op) if prev_op else None,
        "next_op": OP_LABEL.get(next_op) if next_op else None,
        "question": question,
    }
    return [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": json.dumps(user, ensure_ascii=False),
        },
    ]


# ---------------------------------------------------------------- 网络

async def _stream_once(messages, values, timeout):
    """一次请求，逐段吐 delta。错误一律翻译成 LLMUnavailable。"""
    url = f"{values['base_url']}/chat/completions"
    body = {
        "model": values["model"],
        "messages": messages,
        "stream": True,
        "temperature": 0.3,
        "max_tokens": values["max_tokens"],
    }
    headers = {
        "Authorization": f"Bearer {values['api_key']}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(timeout, connect=min(5.0, timeout))
        ) as client:
            async with client.stream("POST", url, json=body, headers=headers) as response:
                if response.status_code != 200:
                    await response.aread()
                    status = response.status_code
                    raise LLMUnavailable(
                        f"llm_http_{status}",
                        f"模型服务返回 {status}",
                        retryable=status in (408, 429) or status >= 500,
                    )

                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line.startswith("data:"):
                        continue
                    chunk = line[5:].strip()
                    if chunk == "[DONE]":
                        return
                    try:
                        payload = json.loads(chunk)
                    except json.JSONDecodeError:
                        # 心跳、注释、厂商自定义帧都会走到这里，跳过即可
                        continue
                    for choice in payload.get("choices") or []:
                        piece = (choice.get("delta") or {}).get("content")
                        if piece:
                            yield piece
    except httpx.TimeoutException as error:
        raise LLMUnavailable("llm_timeout", "模型服务超时", retryable=True) from error
    except httpx.HTTPError as error:
        raise LLMUnavailable("llm_network", "连不上模型服务", retryable=True) from error


# ---------------------------------------------------------------- 文本 → 四块

MARKERS = {"结论": "conclusion", "为什么": "why", "下一步": "next"}

_MARKER_LINE = re.compile(
    r"^[#>*_\s]*[【\[]?(结论|为什么|下一步)[】\]]?[*_]*[：:]?\s*(.*)$"
)
_BULLET = re.compile(r"^[-•·]\s")
_BULLET_PREFIX = re.compile(r"^(?:[-•·*]\s*|\d+[.、)]\s*)")
_HEX_VALUE = re.compile(r"0[xX]([0-9A-Fa-f]{2})(?![0-9A-Fa-f])")


class BlockAssembler:
    """把模型吐的纯文本增量拼成 F09 的四块事件。

    容错取向：**先等第一段文字到了再开「结论」块**，遇到标题再切换。
    模型不按格式来时正文全落在结论块里，一个字都不丢；模型一个字都不吐时，
    调用方还能干净地降级到本地模板（一个空块都没发出去）。
    """

    # 单行太长（模型不换行）时先吐一段，别让读者干等
    FLUSH_AT = 48
    FLUSH_KEEP = 16

    def __init__(self, changed, total):
        self.changed = list(changed)
        self.total = total
        self.buffer = ""
        self.current = None
        self.text = []

    @property
    def started(self):
        return self.current is not None

    def start(self):
        self.current = "conclusion"
        return [("block", {"type": "conclusion", "text": ""})]

    def feed(self, delta):
        self.buffer += delta
        return self._drain()

    def finish(self):
        events = self._drain(final=True)
        events.append(
            (
                "block",
                {
                    "type": "cite",
                    "bytes": self.changed[:3] if self.changed else [0, 1, 2],
                    "total": self.total,
                },
            )
        )
        return events

    # -- 内部

    def _drain(self, final=False):
        events = []
        while True:
            index = self.buffer.find("\n")
            if index < 0:
                break
            line = self.buffer[:index]
            self.buffer = self.buffer[index + 1 :]
            events.extend(self._line(line))
        if final:
            if self.buffer:
                events.extend(self._line(self.buffer))
                self.buffer = ""
            return events
        if len(self.buffer) >= self.FLUSH_AT:
            head = self.buffer[: -self.FLUSH_KEEP]
            self.buffer = self.buffer[-self.FLUSH_KEEP :]
            events.extend(self._text(head))
        return events

    def _line(self, line):
        stripped = line.strip()
        if not stripped:
            return []
        if not _BULLET.match(stripped):
            match = _MARKER_LINE.match(stripped)
            if match:
                return self._switch(MARKERS[match.group(1)], match.group(2).strip())
        if self.current == "why":
            item = _BULLET_PREFIX.sub("", stripped).strip()
            if not item:
                return []
            return self._new_item(item)
        return self._text(stripped if self.current == "conclusion" else line)

    def _switch(self, kind, rest):
        if kind == self.current:
            # 模型把同一个标题写了两遍：当正文续写，别开第二个块
            return self._text(rest) if rest else []
        self.current = kind
        if kind == "why":
            events = [("block", {"type": "why", "items": []})]
        elif kind == "next":
            events = [("block", {"type": "next", "text": ""})]
        else:
            events = [("block", {"type": "conclusion", "text": ""})]
        if rest:
            events.extend(self._text(rest))
        return events

    def _text(self, piece):
        if not piece:
            return []
        self.text.append(piece)
        return [("token", {"t": piece, "text": piece})]

    def _new_item(self, item):
        self.text.append(item)
        return [("token", {"t": item, "text": item, "item": True})]

    # -- 审计

    def hex_outside(self, allowed):
        """模型给出的、当前这一步数据里并不存在的十六进制值。

        不拦（中途打断会毁掉整段可读性），只记账：这是「编数值」的唯一可量化证据。
        """
        allowed = {int(value) for value in allowed}
        found = {int(match, 16) for match in _HEX_VALUE.findall(" ".join(self.text))}
        return sorted(found - allowed)


def allowed_hex(trace, step_index, question):
    """模型**被允许**引用的字节值：本步的 before / after，加上问题里问到的那个。

    刻意不含轮密钥：提示词没给它密钥，它真写出一个密钥字节就是自己算的。
    这条口径与验收「回答里的十六进制值逐个能在当前步 before/after 里找到」一致。
    """
    step = trace["steps"][step_index]
    values = set(step["state_before"]) | set(step["state_after"])
    for match in _HEX_VALUE.findall(question or ""):
        values.add(int(match, 16))
    return values


# ---------------------------------------------------------------- 对外

async def stream_answer(trace, step_index, question):
    """产出 (event, data)：与本地模板完全相同的 block / token 协议。

    最后额外产出一帧 `("audit", {...})`，只给调用方记账用，不发给前端。
    """
    values = config()
    if not (values["base_url"] and values["api_key"] and values["model"]):
        raise LLMUnavailable("llm_disabled", "未配置模型", retryable=False)

    messages = build_messages(trace, step_index, question)
    step = trace["steps"][step_index]
    assembler = BlockAssembler(step["changed"], len(step["changed"]))
    allowed = allowed_hex(trace, step_index, question)

    for attempt in (1, 2):
        timeout = values["timeout"] * (RETRY_FACTOR if attempt == 2 else 1.0)
        try:
            async for piece in _stream_once(messages, values, timeout):
                if not assembler.started:
                    for event in assembler.start():
                        yield event
                for event in assembler.feed(piece):
                    yield event
        except LLMUnavailable as error:
            if assembler.started:
                # 已经吐过字：补上依据块再抛，前端留着已生成的部分
                for event in assembler.finish():
                    yield event
                error.partial = True
                error.audit = {"hex_outside": assembler.hex_outside(allowed)}
                raise error
            if not error.retryable or attempt == 2:
                raise
            logger.warning("llm retry code=%s attempt=%s", error.code, attempt)
            continue

        if not assembler.started:
            raise LLMUnavailable("llm_empty", "模型没有返回内容", retryable=False)

        for event in assembler.finish():
            yield event
        yield "audit", {"hex_outside": assembler.hex_outside(allowed)}
        return
